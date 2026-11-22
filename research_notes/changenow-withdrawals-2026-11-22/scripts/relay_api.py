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
import json
import os
import random
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
SAMPLE_SEED = 20261122
SAMPLE_SIZE = 60


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


def targets(raw):
    """Relay fills into deposit addresses: unresolved ones, then a fixed sample of the ones the chain tied."""
    unresolved, tied = [], []
    for path in sorted(Path(raw).glob("*/withdrawals.json")):
        for w in json.loads(path.read_text())["walks"]:
            if w["category"] not in ("RELAY_SOLVER", "RELAY_ROUTER"):
                continue
            (tied if w["status"] == "CONFIRMED" else unresolved).append(w["start"]["tx"])
    tied = sorted(set(tied))
    random.Random(SAMPLE_SEED).shuffle(tied)
    return sorted(set(unresolved)), tied[:SAMPLE_SIZE]


def check(raw):
    """Read on chain what Relay's record says about each unresolved fill: the origin transaction must exist, succeed
    and move value out of the record's `user`; that user must be a Polymarket trading wallet (or a key owning one).
    Writes relay_api/checked.json: {fill_tx: dict(verdict, origin, wallet, value, note)}. Network: receipts,
    Polygon wallet classification, prices."""
    from changenow_weekly import chainio as io, prices
    from changenow_weekly import polymarket as pm
    out_path = Path(raw) / "relay_api" / "checked.json"
    done = json.loads(out_path.read_text()) if out_path.exists() else {}
    starts, agreement = {}, {}
    for path in sorted(Path(raw).glob("*/withdrawals.json")):
        w = json.loads(path.read_text())
        for x in w["walks"]:
            if x["category"] in ("RELAY_SOLVER", "RELAY_ROUTER") and x["status"] != "CONFIRMED":
                starts[x["start"]["tx"]] = (w["week"], x["start"], w["tokens"])
            elif x["category"] == "RELAY_SOLVER" and x["status"] == "CONFIRMED":
                # the chain tied this fill to an escrow deposit by its order id: does Relay's own record name the same deposit?
                p = Path(raw) / "relay_api" / "hash" / f"{x['start']['tx']}.json"
                origin = [(h["chain"], h["tx"]) for h in x["hops"] if h["kind"] == "RELAY_ORDER"]
                if p.exists() and origin:
                    a = json.loads(p.read_text())
                    reqs = (a["body"] or {}).get("requests") or [] if a["status"] == 200 else []
                    ins = [(int(t.get("chainId") or 0), (t.get("hash") or "").lower()) for t in ((reqs[0].get("data") or {}).get("inTxs") or [])] if reqs else []
                    agreement[x["start"]["tx"]] = dict(chain_origin=origin[0], api_origin=ins, agree=origin[0] in [tuple(i) for i in ins], referrer=reqs[0].get("referrer") if reqs else None)
    (Path(raw) / "relay_api").mkdir(parents=True, exist_ok=True)
    (Path(raw) / "relay_api" / "agreement.json").write_text(json.dumps(agreement, indent=1, sort_keys=True))
    for tx, (week, start, tokens) in sorted(starts.items()):
        if tx in done:
            continue
        p = Path(raw) / "relay_api" / "hash" / f"{tx}.json"
        if not p.exists():
            continue
        a = json.loads(p.read_text())
        reqs = (a["body"] or {}).get("requests") or []
        if a["status"] != 200 or not reqs:
            done[tx] = dict(verdict="NO_RECORD", note=f"HTTP {a['status']}")
            continue
        r = reqs[0]
        user = (r.get("user") or "").lower()
        ins = (r.get("data") or {}).get("inTxs") or []
        outs = [(int(t.get("chainId") or 0), (t.get("hash") or "").lower()) for t in (r.get("data") or {}).get("outTxs") or []]
        if (start["chain"], tx) not in outs:
            done[tx] = dict(verdict="RECORD_DOES_NOT_NAME_THIS_FILL", user=user, note=f"outTxs {outs}")
            continue
        if len(ins) != 1 or int(ins[0].get("chainId") or 0) not in io.CHAINS:
            done[tx] = dict(verdict="ORIGIN_NOT_READ", user=user, note=f"inTxs {[(t.get('chainId'), t.get('hash')) for t in ins]}")
            continue
        chain, otx = int(ins[0]["chainId"]), ins[0]["hash"].lower()
        try:
            rec = io.receipt(chain, otx)
        except Exception as exc:                      # the record names a transaction no node serves: not a fact
            done[tx] = dict(verdict="ORIGIN_UNREADABLE", user=user, note=str(exc)[:160])
            continue
        moves = [m for m in pm.ff_flows.transfers(rec, chain) if m["source"] == user and m["raw"] > 0] if int(rec.get("status", "0x0"), 16) == 1 else []
        if not moves:
            done[tx] = dict(verdict="NO_DEBIT_OF_USER_IN_ORIGIN", user=user, note=f"origin {chain}:{otx}")
            continue
        m = moves[0]
        origin = dict(chain=chain, tx=otx, log_index=m["log_index"], block=int(rec["blockNumber"], 16), ts=None, src=user, dst=m["target"], token=m["token"], raw=str(m["raw"]))
        origin["ts"] = io.block_time(chain, origin["block"])
        wallet, verdict = None, "ORIGIN_NOT_POLYMARKET"
        if chain == 137:
            found, _ = pm.trading_wallets([user])
            if user in found:
                wallet, verdict = user, "WALLET_DEBIT_VERIFIED"
            else:
                owned = pm.owned_wallets([user])
                if owned.get(user):
                    wallet, verdict = "|".join(x["wallet"] for x in owned[user]), "KEY_OF_WALLET"
        value = {}
        if verdict != "ORIGIN_NOT_POLYMARKET":
            book = prices.Book(Path(raw) / week / "prices.json")
            info = tokens.get(str(start["chain"]), {}).get(start["token"])
            if info:
                price, price_ts = book.at(start["chain"], start["token"], start["ts"])
                amount = int(start["raw"]) / 10 ** info["decimals"]
                value = dict(symbol=info["symbol"], decimals=info["decimals"], amount=amount, price_usd=price, price_ts=price_ts, usd=round(amount * price, 2))
        done[tx] = dict(verdict=verdict, user=user, wallet=wallet, origin=origin, referrer=r.get("referrer"), request_id=r.get("id"), value=value,
                        note=f"Relay record {r.get('id')} names origin {chain}:{otx}; the origin receipt moves {m['raw']} of {m['token']} out of {user}")
        out_path.write_text(json.dumps(done, indent=1, sort_keys=True))
        print(time.strftime("%H:%M:%S"), tx, verdict, flush=True)
    out_path.write_text(json.dumps(done, indent=1, sort_keys=True))
    return done


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--raw", required=True)
    p.add_argument("--from-census", action="store_true", help="read targets from <raw>/*/withdrawals.json")
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
