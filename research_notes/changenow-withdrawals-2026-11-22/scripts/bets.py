"""Bets before each withdrawal: Polymarket's public activity of every wallet found, the markets it traded, and the
wallet's collateral balance just before each debit. Network collector; the accounting is offline in `pnl.py`.

For every wallet of results/changenow_outflows.csv in the chosen classes:
- the complete v2 activity feed, every type, ascending, all pages up to a cap (a capped read is marked, never
  presented as complete); profile fields (name, pseudonym, bio, images) are dropped at read time;
- the Gamma record of every market it traded (outcomes, token ids, resolution), 100 markets a query;
- USDC + USDC.e + pUSD held by the wallet at the end of the block before each of its debits, from archive state.
Comparable traders: for each wallet, small buyers of its largest market, picked by a hash rank that ignores outcome
and later behaviour, read over the same period (`--controls`).
"""
import argparse
import csv
import gzip
import hashlib
import json
import sys
import time
from pathlib import Path
from urllib.parse import urlencode

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "monitoring"))
sys.dont_write_bytecode = True

from changenow_weekly import chainio as io  # noqa: E402
from phi_monitor import net  # noqa: E402

ACTIVITY = "https://data-api.polymarket.com/v2/activity?"
TRADES = "https://data-api.polymarket.com/v2/trades?"
GAMMA = "https://gamma-api.polymarket.com/markets?"
# Fields kept from each activity row: what the accounting reads. Profile fields (name, pseudonym, bio, images) are
# never kept, and neither is anything else not listed here.
ROW_FIELDS = ("proxy_wallet", "timestamp", "type", "side", "size", "usdc_size", "price", "token_id", "condition_id", "outcome", "outcome_index",
              "transaction_hash", "title", "slug", "event_slug")
USDC_E = "0x2791bca1f2de4661ed88a30c99a7a9449aa84174"
USDC = "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359"
PUSD = "0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb"
BALANCE_OF = "70a08231"
ESTABLISHED = ("CONFIRMED_DIRECT", "SUPPORTED_INDIRECT")


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8") as f:
        json.dump(value, f, sort_keys=True, separators=(",", ":"))
    tmp.replace(path)


def load(path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def activity(wallet, max_pages=80, limit=500, start=None, end=None):
    """Every activity row of one trading account, ascending. Raises on ambiguous pagination, rows of another wallet or
    a descending page. Returns dict(rows, pages, complete): complete is False when the page cap stopped the read."""
    wallet = wallet.lower()
    rows, pages, cursor = [], [], None
    while len(pages) < max_pages:
        q = dict(user=wallet, limit=limit, sort_by="TIMESTAMP", sort_direction="ASC", exclude_deposits_withdrawals="false")
        if start:
            q["start"] = start
        if end:
            q["end"] = end
        if cursor:
            q["cursor"] = cursor
        v = net.get_json(ACTIVITY + urlencode(q))
        if not isinstance(v, dict) or "data" not in v:
            raise net.SourceError(f"activity of {wallet}: unexpected answer")
        pg, data = v.get("pagination") or {}, v["data"]
        for r in data:
            if (r.get("proxy_wallet") or "").lower() != wallet:
                raise net.SourceError(f"activity row for another wallet: {r.get('proxy_wallet')}")
            rows.append({k: r.get(k) for k in ROW_FIELDS if k in r})
        pages.append(dict(cursor=cursor, rows=len(data), has_more=pg.get("has_more"), next_cursor=pg.get("next_cursor")))
        if pg.get("has_more") != bool(pg.get("next_cursor")):
            raise net.SourceError(f"activity of {wallet}: ambiguous pagination")
        if not pg.get("has_more"):
            break
        if not data:
            raise net.SourceError(f"activity of {wallet}: empty page with a continuation")
        cursor = pg["next_cursor"]
        time.sleep(0.3)
    ts = [r["timestamp"] for r in rows]
    if ts != sorted(ts):
        raise net.SourceError(f"activity of {wallet} is not ascending")
    complete = not pages[-1]["has_more"]
    if start and end and any(not (start <= t <= end) for t in ts):
        raise net.SourceError(f"activity of {wallet}: the time filter was not honoured")
    return dict(wallet=wallet, captured_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), pages=pages, complete=complete, rows=rows,
                endpoint=ACTIVITY + "user=<wallet>&limit=500&sort_by=TIMESTAMP&sort_direction=ASC&exclude_deposits_withdrawals=false")


MARKET_FIELDS = ("conditionId", "question", "slug", "outcomes", "clobTokenIds", "outcomePrices", "closed", "umaResolutionStatus",
                 "endDate", "closedTime", "umaEndDate", "eventStartTime", "negRisk")


def project(m):
    """The fields the accounting reads, and the event slug; descriptions and images are not kept."""
    out = {k: m.get(k) for k in MARKET_FIELDS}
    out["events"] = [dict(slug=e.get("slug")) for e in (m.get("events") or [])[:1]]
    return out


def gamma(cids, folder):
    """Gamma records of markets, closed ones then open ones, 100 condition ids a query. Missing ones are listed."""
    path = folder / "markets.json.gz"
    have = load(path) if path.exists() else dict(markets={}, missing=[], queries=0)
    todo = sorted(set(cids) - set(have["markets"]) - set(have["missing"]))
    for i in range(0, len(todo), 100):
        part = todo[i:i + 100]
        for closed in ("true", "false"):
            want = [c for c in part if c not in have["markets"]]
            if not want:
                break
            got = net.get_json(GAMMA + f"closed={closed}&limit=500&" + "&".join("condition_ids=" + c for c in want))
            have["queries"] += 1
            for m in got:
                have["markets"][m["conditionId"].lower()] = project(m)
            time.sleep(0.15)
        have["missing"] += [c for c in part if c not in have["markets"]]
        if i % 1000 == 0:
            save(path, have)
            print(time.strftime("%H:%M:%S"), f"gamma {len(have['markets'])} markets, {len(have['missing'])} missing", flush=True)
    save(path, have)
    return have


def balances(debits, folder):
    """USDC + USDC.e + pUSD of a wallet at the end of the block before its debit, one multicall at that block."""
    path = folder / "balances.json.gz"
    have = load(path) if path.exists() else {}
    for wallet, block, tx in sorted(debits):
        k = f"{wallet}@{block}"
        if k in have:
            continue
        calls = [(t, BALANCE_OF + "0" * 24 + wallet[2:]) for t in (USDC, USDC_E, PUSD)]
        res = io.aggregate3(137, calls, block=hex(block - 1))
        if not all(ok and len(data) == 64 for ok, data in res):
            raise net.SourceError(f"balance of {wallet} at block {block - 1}: a call failed")
        have[k] = dict(wallet=wallet, block_before=block - 1, debit_tx=tx, raw={"USDC": str(int(res[0][1], 16)), "USDC.e": str(int(res[1][1], 16)), "pUSD": str(int(res[2][1], 16))})
        save(path, have)
    return have


def market_buyers(cid, max_pages=10):
    """Buy notional per wallet in one market from the public trade feed (maker fills included)."""
    notional, cursor = {}, None
    for _ in range(max_pages):
        q = dict(condition=cid, limit=1000, taker_only="false")
        if cursor:
            q["cursor"] = cursor
        v = net.get_json(TRADES + urlencode(q))
        data = v.get("data") if isinstance(v, dict) else v
        for r in data or []:
            if r.get("side") == "BUY":
                w = (r.get("proxy_wallet") or r.get("proxyWallet") or "").lower()
                notional[w] = notional.get(w, 0.0) + float(r["price"]) * float(r["size"])
        cursor = (v.get("pagination") or {}).get("next_cursor") if isinstance(v, dict) else None
        if not cursor:
            break
        time.sleep(0.2)
    return notional


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--raw", required=True)
    p.add_argument("--outflows", default=str(HERE.parent / "results" / "changenow_outflows.csv"))
    p.add_argument("--classes", default="CONFIRMED_DIRECT,SUPPORTED_INDIRECT,POSSIBLE")
    p.add_argument("--max-pages", type=int, default=80)
    p.add_argument("--controls", type=int, default=0, help="comparable traders per wallet with an established withdrawal")
    args = p.parse_args(argv)
    folder = Path(args.raw) / "bets"
    classes = set(args.classes.split(","))
    with open(args.outflows, newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["evidence_class"] in classes]
    wallets = sorted({w for r in rows for w in r["polymarket_wallet"].split("|") if len(w) == 42})
    print(f"{len(wallets)} wallets", flush=True)
    cids = set()
    for w in wallets:
        path = folder / "activity" / f"{w}.json.gz"
        if not path.exists():
            a = activity(w, args.max_pages)
            save(path, a)
            print(time.strftime("%H:%M:%S"), f"{w} {len(a['rows'])} rows {'complete' if a['complete'] else 'CAPPED'}", flush=True)
        cids |= {(r.get("condition_id") or "").lower() for r in load(path)["rows"] if r.get("condition_id")}
    debits = {(r["polymarket_wallet"], int(r["polymarket_debit_block"]), r["polymarket_debit_tx"]) for r in rows
              if r.get("polymarket_debit_block") and "|" not in r["polymarket_wallet"] and r["evidence_class"] in ESTABLISHED}
    balances(debits, folder)
    if args.controls:
        picked = {}
        cpath = folder / "controls.json.gz"
        have = load(cpath) if cpath.exists() else {}
        for w in sorted({r["polymarket_wallet"] for r in rows if r["evidence_class"] in ESTABLISHED and "|" not in r["polymarket_wallet"]}):
            if w in have:
                continue
            own = load(folder / "activity" / f"{w}.json.gz")["rows"]
            spend = {}
            for r in own:
                if r["type"] == "TRADE" and r.get("side") == "BUY" and r.get("condition_id"):
                    spend[r["condition_id"].lower()] = spend.get(r["condition_id"].lower(), 0.0) + float(r.get("usdc_size") or 0)
            if not spend:
                continue
            cid = max(sorted(spend), key=spend.get)
            buyers = market_buyers(cid)
            lo, hi = spend[cid] / 4, spend[cid] * 4
            pool = sorted((x for x, n in buyers.items() if lo <= n <= hi and x != w and x not in wallets), key=lambda x: hashlib.sha256((cid + x).encode()).hexdigest())
            picked[w] = dict(condition_id=cid, focus_notional=spend[cid], pool=len(pool), controls=pool[:args.controls])
            have[w] = picked[w]
            for c in pool[:args.controls]:
                path = folder / "activity" / f"{c}.json.gz"
                if not path.exists():
                    a = activity(c, min(args.max_pages, 20))          # controls: 10,000 rows at most, a capped read is marked
                    save(path, a)
                    cids |= {(r.get("condition_id") or "").lower() for r in a["rows"] if r.get("condition_id")}
            save(cpath, have)
            print(time.strftime("%H:%M:%S"), f"controls of {w}: {len(pool[:args.controls])} of {len(pool)}", flush=True)
        for c in {c for v in have.values() for c in v["controls"]}:
            path = folder / "activity" / f"{c}.json.gz"
            if path.exists():
                cids |= {(r.get("condition_id") or "").lower() for r in load(path)["rows"] if r.get("condition_id")}
    gamma(sorted(cids - {""}), folder)
    return 0


if __name__ == "__main__":
    sys.exit(main())
