"""Relay's own record of an order, read from its public API before the keyless endpoint is retired (2026-11-24 00:00 UTC).

Network collector. Two reads, each answer kept verbatim on disk and never fetched twice:
- `hash`: the request that holds one transaction (a solver's fill or a deposit): origin chain, origin transaction,
  depositor (`user`), recipient, referrer (Polymarket's withdrawals carry `funxyz|...`).
- `user`: every request where an address is sender or recipient, paged by continuation.

Targets come from the census files: every Relay fill into a ChangeNOW deposit address that the chain alone did not
tie to an origin, a fixed-seed sample of the fills it did tie (to measure agreement), and optionally wallets.
The endpoint is throttled: the pace adapts to 429 answers and honours Retry-After. Nothing here is a chain fact:
`build.py` uses an answer only after the transactions it names are read on the chain.
"""
import argparse
import hashlib
import json
import os
import sys
import time
import urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "monitoring"))
sys.dont_write_bytecode = True

from phi_monitor import net  # noqa: E402

API = "https://api.relay.link/requests/v2"
SUNSET = 1795478400            # 2026-11-24 00:00:00 UTC, from the endpoint's own deprecation notice


class Pacer:
    def __init__(self, wait=13.0, low=8.0, high=180.0):
        self.wait, self.low, self.high, self.last = wait, low, high, 0.0

    def before(self):
        delay = self.wait - (time.time() - self.last)
        if delay > 0:
            time.sleep(delay)
        self.last = time.time()

    def answer(self, status, retry_after=None):
        if status == 429:
            self.wait = min(self.high, max(self.wait * 2, float(retry_after or 0)))
        elif status == 200:
            self.wait = max(self.low, self.wait * 0.95)


def fetch(url, pacer, tries=6):
    """(status, parsed body or None). A 429 waits and retries; other statuses are returned as they are."""
    for _ in range(tries):
        if time.time() >= SUNSET:
            raise net.SourceError("Relay requests/v2 is past its announced retirement")
        pacer.before()
        status, body = net.fetch(url, timeout=60, tries=2)
        if status == 429:
            pacer.answer(429)
            continue
        pacer.answer(status)
        try:
            return status, json.loads(body)
        except ValueError:
            return status, None
    return 429, None


def save(path, url, status, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(dict(url=url, status=status, fetched_ts=int(time.time()), body=body), separators=(",", ":")))
    os.replace(tmp, path)


def by_hash(raw, tx, pacer):
    path = Path(raw) / "relay_api" / "hash" / f"{tx.lower()}.json"
    if path.exists() and json.loads(path.read_text())["status"] == 200:
        return False
    url = f"{API}?hash={tx}"
    status, body = fetch(url, pacer)
    save(path, url, status, body)
    return True


def by_user(raw, address, pacer, max_pages=20):
    folder = Path(raw) / "relay_api" / "user" / address.lower()
    page, continuation = 0, None
    while page < max_pages:
        path = folder / f"{page:03d}.json"
        if path.exists() and json.loads(path.read_text())["status"] == 200:
            body = json.loads(path.read_text())["body"]
        else:
            url = f"{API}?user={address}&limit=50" + (f"&continuation={urllib.parse.quote(continuation)}" if continuation else "")
            status, body = fetch(url, pacer)
            save(path, url, status, body)
            if status != 200:
                return
        continuation = (body or {}).get("continuation")
        if not continuation or not (body or {}).get("requests"):
            (folder / "COMPLETE").write_text(str(page + 1))
            return
        page += 1


def census_files(raw):
    return sorted(Path(raw).glob("20*-W*/withdrawals-*.json"))


def sampled(tx):
    """A stable sample of the fills the chain tied: about one in eight, decided by the transaction hash alone, so the
    sample does not change when more weeks are read."""
    return int(hashlib.sha256(tx.encode()).hexdigest(), 16) % 8 == 0


def targets(raw):
    """Relay fills into deposit addresses: unresolved ones, then the stable sample of the ones the chain tied."""
    unresolved, tied = set(), set()
    for path in census_files(raw):
        for w in json.loads(path.read_text())["walks"]:
            if w["category"] not in ("RELAY_SOLVER", "RELAY_ROUTER"):
                continue
            if w["status"] != "CONFIRMED":
                unresolved.add(w["start"]["tx"])
            elif sampled(w["start"]["tx"]):
                tied.add(w["start"]["tx"])
    return sorted(unresolved), sorted(tied)


def start_key(start):
    return f"{start['chain']}:{start['tx']}:{start['log_index']}"


def request_for(reqs, start):
    """The request of the record that pays this deposit address in this fill, or None. A fill made inside another call
    can settle several orders, so the first request is not taken by default."""
    found = [r for r in reqs if (r.get("recipient") or "").lower() == start["dst"].lower()
             and (start["chain"], start["tx"].lower()) in [(int(t.get("chainId") or 0), (t.get("hash") or "").lower()) for t in (r.get("data") or {}).get("outTxs") or []]]
    return found[0] if len(found) == 1 else None


def check(raw):
    """Read on chain what Relay's record says about each unresolved fill: the request must pay this deposit address in
    this fill; its origin transaction must exist, succeed and move value out of the request's `user`; that user must
    be a Polymarket trading wallet, an account trading from its own key, or a key owning a wallet.
    Writes relay_api/checked.json: {chain:tx:log_index of the fill: dict(verdict, origin, wallet, value, note)}.
    An answer that is not a 200, or an origin no node serves, gets no verdict and is read again next time.
    Network: receipts, Polygon wallet classification, the activity feed, prices."""
    import census                                            # endpoint lists, batch sizes, strict wallet reads, activity-feed test
    from changenow_weekly import chainio as io, prices
    from changenow_weekly import polymarket as pm
    io.CHAINS[137]["state"] = list(census.POLYGON_STATE)
    out_path = Path(raw) / "relay_api" / "checked.json"
    done = json.loads(out_path.read_text()) if out_path.exists() else {}
    done = {k: v for k, v in done.items() if k.count(":") == 2}             # earlier format keyed by transaction only
    starts, agreement = {}, {}
    for path in census_files(raw):
        w = json.loads(path.read_text())
        for x in w["walks"]:
            if x["category"] in ("RELAY_SOLVER", "RELAY_ROUTER") and x["status"] != "CONFIRMED":
                starts[start_key(x["start"])] = (w["week"], x["start"], w["tokens"], path)
            elif x["category"] == "RELAY_SOLVER" and x["status"] == "CONFIRMED" and sampled(x["start"]["tx"]):
                # the chain tied this fill to an escrow deposit by its order id: does Relay's own record name the same deposit?
                p = Path(raw) / "relay_api" / "hash" / f"{x['start']['tx']}.json"
                origin = [(h["chain"], h["tx"]) for h in x["hops"] if h["kind"] == "RELAY_ORDER"]
                if p.exists() and origin:
                    a = json.loads(p.read_text())
                    if a["status"] != 200:
                        continue
                    r = request_for((a["body"] or {}).get("requests") or [], x["start"])
                    ins = [(int(t.get("chainId") or 0), (t.get("hash") or "").lower()) for t in ((r or {}).get("data") or {}).get("inTxs") or []]
                    agreement[start_key(x["start"])] = dict(chain_origin=list(origin[0]), api_origin=[list(i) for i in ins], request_found=r is not None,
                                                            agree=tuple(origin[0]) in ins, referrer=(r or {}).get("referrer"))
    (Path(raw) / "relay_api").mkdir(parents=True, exist_ok=True)
    tmp = (Path(raw) / "relay_api" / "agreement.json").with_suffix(f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(agreement, indent=1, sort_keys=True))
    os.replace(tmp, Path(raw) / "relay_api" / "agreement.json")
    for k, (week, start, tokens, path) in sorted(starts.items()):
        if k in done:
            continue
        p = Path(raw) / "relay_api" / "hash" / f"{start['tx']}.json"
        if not p.exists():
            continue
        a = json.loads(p.read_text())
        if a["status"] != 200 or a["body"] is None:
            continue                                         # refused or throttled: not an answer, asked again later
        reqs = a["body"].get("requests") or []
        if not reqs:
            done[k] = dict(verdict="NO_RECORD", note="HTTP 200 with no request for this transaction")
            continue
        r = request_for(reqs, start)
        if r is None:
            done[k] = dict(verdict="RECORD_DOES_NOT_NAME_THIS_FILL", note=f"{len(reqs)} request(s), none paying {start['dst']} in this fill")
            continue
        user = (r.get("user") or "").lower()
        ins = (r.get("data") or {}).get("inTxs") or []
        if len(ins) != 1 or int(ins[0].get("chainId") or 0) not in io.CHAINS:
            done[k] = dict(verdict="ORIGIN_NOT_READ", user=user, note=f"origin chain {[t.get('chainId') for t in ins]} not read here")
            continue
        chain, otx = int(ins[0]["chainId"]), ins[0]["hash"].lower()
        try:
            rec = io.receipt(chain, otx)
        except Exception:                                    # no node serves it now: no verdict, read again later
            continue
        moves = [m for m in pm.ff_flows.transfers(rec, chain) if m["source"] == user and m["raw"] > 0] if int(rec.get("status", "0x0"), 16) == 1 else []
        if not moves:
            done[k] = dict(verdict="NO_DEBIT_OF_USER_IN_ORIGIN", user=user, note=f"origin {chain}:{otx}")
            continue
        m = moves[0]
        origin = dict(chain=chain, tx=otx, log_index=m["log_index"], block=int(rec["blockNumber"], 16), ts=None, src=user, dst=m["target"], token=m["token"], raw=str(m["raw"]))
        origin["ts"] = io.block_time(chain, origin["block"])
        wallet, verdict, kind = None, "ORIGIN_NOT_POLYMARKET", ""
        if chain == 137:
            found, _ = pm.trading_wallets([user])
            if user in found:
                wallet, verdict, kind = user, "WALLET_DEBIT_VERIFIED", found[user]["type"]
            elif io.get_codes(137, [user])[user] in ("0x", "0x0") and census.eoa_traders([user]):
                wallet, verdict, kind = user, "WALLET_DEBIT_VERIFIED", "EOA_TRADING_ACCOUNT"
            else:
                owned = pm.owned_wallets([user])
                if owned.get(user):
                    wallet, verdict = "|".join(x["wallet"] for x in owned[user]), "KEY_OF_WALLET"
        value = {}
        if verdict != "ORIGIN_NOT_POLYMARKET":
            book = prices.Book(Path(raw) / week / f"prices-{path.stem.split('-', 1)[1]}.json")
            info = tokens.get(str(start["chain"]), {}).get(start["token"])
            if info:
                try:
                    price, price_ts = book.at(start["chain"], start["token"], start["ts"])
                    amount = int(start["raw"]) / 10 ** info["decimals"]
                    value = dict(symbol=info["symbol"], decimals=info["decimals"], amount=amount, price_usd=price, price_ts=price_ts, usd=round(amount * price, 2))
                except pm.net.SourceError as exc:
                    value = dict(error=str(exc)[:160])
        done[k] = dict(verdict=verdict, user=user, wallet=wallet, wallet_type=kind, origin=origin, referrer=r.get("referrer"), request_id=r.get("id"), value=value,
                       note=f"Relay record {r.get('id')} pays {start['dst']} in this fill and names origin {chain}:{otx}; the origin receipt moves {m['raw']} of {m['token']} out of {user}")
        print(time.strftime("%H:%M:%S"), k, verdict, flush=True)
    tmp = out_path.with_suffix(f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(done, indent=1, sort_keys=True))
    os.replace(tmp, out_path)
    return done


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--raw", required=True)
    p.add_argument("--from-census", action="store_true", help="read targets from <raw>/<week>/withdrawals-<chains>.json")
    p.add_argument("--hash", action="append", default=[])
    p.add_argument("--user", action="append", default=[])
    p.add_argument("--check", action="store_true", help="read on chain the origins named by the answers on disk")
    args = p.parse_args(argv)
    if args.check:
        check(args.raw)
        return 0
    pacer = Pacer()
    hashes = list(args.hash)
    if args.from_census:
        unresolved, sample = targets(args.raw)
        print(f"{len(unresolved)} unresolved fills, {len(sample)} sampled tied fills", flush=True)
        hashes += unresolved + sample
    done = 0
    for tx in hashes:
        if by_hash(args.raw, tx, pacer):
            done += 1
            print(time.strftime("%H:%M:%S"), f"hash {tx} ({done} fetched, pace {pacer.wait:.1f}s)", flush=True)
    for address in args.user:
        by_user(args.raw, address, pacer)
        print(time.strftime("%H:%M:%S"), f"user {address} done", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
