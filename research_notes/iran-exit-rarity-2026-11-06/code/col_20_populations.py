"""Populations of early Yes buyers for each comparator market. Network, one worker.

python3 -I -B code/col_20_populations.py

For every non-alleged market of data/shocks.json, pages data-api /v2/trades (taker_only=false,
the parameters of the reference tape) from the newest row back past T - WINDOW_S. The endpoint
ignores start and end (checked on 6 November 2026), so the whole tape after the window is read.
Raw pages go to RAW/trades/ with their SHA-256; data/populations/<condition>.json keeps the
window's Yes BUY rows reduced to wallet, size, price, time and hash, the request counters and the
completeness checks.

A population is complete only if (1) the tape passed below the window start, or ended at or below
the oldest row of the 30 September archive, and (2) every Yes taker row of the archive inside the
window is found in the tape (same hash and wallet). A malformed page stops the run.
"""
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DATA, MAX_TRADE_PAGES, MIN_USDC, RAW, fetch, low, write_atomic  # noqa: E402


def collect(m):
    out = DATA / "populations" / f'{m["condition"]}.json'
    if out.exists():
        d = json.loads(out.read_text())
        if d["window"] != m["window"]:
            raise SystemExit(f'{m["condition"]}: stored window differs from shocks.json')
        if d["complete"]:
            return d
    t0, t1 = m["window"]
    cur, n, rows, shas, prev_min, counters = None, 0, [], [], None, {}
    termination = "MAX_PAGES"
    while n < MAX_TRADE_PAGES:
        u = (f'https://data-api.polymarket.com/v2/trades?condition={m["condition"]}&limit=1000&taker_only=false'
             + (f"&cursor={cur}" if cur else ""))
        raw_out = RAW / "trades" / m["condition"] / f"p{n:04d}.json"
        b = fetch(u, raw_out, counters, wait=10)
        shas.append(json.loads(raw_out.with_suffix(".meta.json").read_text())["sha256"]); n += 1
        if not isinstance(b, dict) or not isinstance(b.get("data"), list) or not isinstance(b.get("pagination"), dict):
            raise SystemExit(f'{m["condition"]} page {n - 1}: unexpected shape {str(b)[:200]}')
        data, pg = b["data"], b["pagination"]
        if any(x.get("condition_id", "").lower() != m["condition"] for x in data):
            raise SystemExit(f'{m["condition"]} page {n - 1}: rows of another market')
        if not data and pg.get("has_more"):
            raise SystemExit(f'{m["condition"]} page {n - 1}: empty page that announces more')
        if data:
            ts = [int(x["timestamp"]) for x in data]
            if prev_min is not None and max(ts) > prev_min:
                raise SystemExit(f'{m["condition"]}: page {n - 1} is newer than the previous page')
            prev_min = min(ts)
            rows += [x for x in data if t0 <= int(x["timestamp"]) < t1]
        cur = pg.get("next_cursor")
        if prev_min is not None and prev_min < t0:
            termination = "PASSED_WINDOW"; break
        if not pg.get("has_more") or not cur or not data:
            termination = "END"; break
        time.sleep(0.4)
    seen, buy, first, kept, got = set(), defaultdict(float), {}, [], set()
    for x in rows:  # identical rows counted once, as in the reference population
        k = json.dumps(x, sort_keys=True)
        if k in seen:
            continue
        seen.add(k)
        got.add((x["transaction_hash"].lower(), low(x["proxy_wallet"])))
        if x["token_id"] == m["yes_token"] and x["side"] == "BUY":
            w = low(x["proxy_wallet"])
            buy[w] += float(x["size"]) * float(x["price"])
            first[w] = min(first.get(w, int(x["timestamp"])), int(x["timestamp"]))
            kept.append({"w": w, "size": x["size"], "price": x["price"], "t": int(x["timestamp"]), "tx": x["transaction_hash"]})
    oracle = {tuple(r) for r in m["archive_window_yes_rows"]}
    missing = sorted(oracle - got)
    reached = termination == "PASSED_WINDOW" or (termination == "END" and prev_min is not None and prev_min <= m["archive_oldest_ts"])
    wallets = sorted((w for w, v in buy.items() if v >= MIN_USDC), key=lambda w: (first[w], w))
    res = {"condition": m["condition"], "T": t1, "window": [t0, t1], "pages": n, "termination": termination,
           "oldest_ts_read": prev_min, "archive_oldest_ts": m["archive_oldest_ts"], "reached_window_start": reached,
           "archive_rows_in_window": len(oracle), "archive_rows_missing_from_tape": missing,
           "complete": reached and not missing, "rows_in_window": len(rows), "unique_rows": len(seen),
           "http": counters, "page_sha256": shas, "wallets": wallets, "buy_usdc": {w: round(buy[w], 6) for w in wallets},
           "yes_buy_rows": kept}
    write_atomic(out, json.dumps(res, indent=1).encode())
    return res


def main():
    shocks = json.loads((DATA / "shocks.json").read_text())
    for m in shocks["markets"]:
        if m["alleged"]:
            continue
        r = collect(m)
        print(m["T_utc"], m["condition"][:10], r["termination"], "pages", r["pages"], "wallets", len(r["wallets"]),
              "oracle missing", len(r["archive_rows_missing_from_tape"]), "complete", r["complete"], flush=True)


if __name__ == "__main__":
    main()
