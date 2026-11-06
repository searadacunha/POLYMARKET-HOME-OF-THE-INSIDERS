"""Cash-flow ledger per wallet from archived /v2/activity rows (all pages, DONE marker required).

Per wallet: deposits, withdrawals, buys, sells, redemptions, merges, splits, rebates and rewards (USDC, Decimal).
trading_result = sells + redeems + merges + rebates/rewards - buys - splits. It counts any share still held as 0:
`open_share_tokens` lists tokens with shares bought but not sold, redeemed or merged, so a still-valuable residual
is visible instead of hidden. Withdrawals are never treated as profit.
Per-market lines are kept for markets whose title matches the fixed keyword classes of ANALYSIS_PLAN.md.
Usage: python3 -I ledger.py OUT.json address...
"""
import json, os, re, sys
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

RAW = Path(os.environ.get("XLEADS_RAW", Path.home() / "Projects/Polymarket-x-leads-raw-20261106/raw")) / "polymarket"
CLASSES = {"iran_israel": re.compile(r"iran|israel|khamenei|tehran|hormuz", re.I),
           "venezuela": re.compile(r"venezuela|maduro|caracas", re.I),
           "us_engagement": re.compile(r"us strike|us military|u\.s\. strike|invade", re.I)}


def rows_of(a):
    d = RAW / a
    if not (d / "DONE.json").exists():
        raise SystemExit(f"{a}: activity not complete")
    rows = []
    for p in sorted(d.glob("v2activity_p*.json")):
        if p.name.endswith(".meta.json"):
            continue
        rows += json.loads(p.read_text(), parse_float=Decimal)["data"]
    n = json.loads((d / "DONE.json").read_text())["activity_rows"]
    if len(rows) != n:
        raise SystemExit(f"{a}: {len(rows)} rows read, DONE says {n}")
    return rows


def ledger(a):
    rows = rows_of(a)
    t = defaultdict(Decimal)
    per = defaultdict(lambda: defaultdict(Decimal))
    shares = defaultdict(Decimal)
    for r in rows:
        ty, u = r["type"], Decimal(str(r["usdc_size"]))
        key = r["title"] or ""
        if ty == "TRADE":
            k = "buys" if r["side"] == "BUY" else "sells"
            t[k] += u; per[key][k] += u
            shares[(key, r["outcome"])] += Decimal(str(r["size"])) * (1 if r["side"] == "BUY" else -1)
        elif ty in ("REDEEM", "MERGE", "SPLIT", "DEPOSIT", "WITHDRAWAL", "CONVERSION"):
            k = ty.lower() + "s"
            t[k] += u
            if ty in ("REDEEM", "MERGE", "SPLIT"):
                per[key][k] += u
                if ty == "REDEEM":
                    for o in [x for x in shares if x[0] == key]:
                        shares[o] = Decimal(0)
                if ty == "MERGE":
                    for o in [x for x in shares if x[0] == key]:
                        shares[o] -= Decimal(str(r["size"]))
        else:
            t["other_" + ty.lower()] += u
    other_in = sum((v for k, v in t.items() if k.startswith("other_")), Decimal(0))
    res = t["sells"] + t["redeems"] + t["merges"] + other_in - t["buys"] - t["splits"]
    ts = [r["timestamp"] for r in rows]
    classes = {}
    for c, rx in CLASSES.items():
        m = {k: {kk: str(vv) for kk, vv in v.items()} for k, v in per.items() if rx.search(k)}
        tot = defaultdict(Decimal)
        for v in per.values():
            pass
        for k, v in per.items():
            if rx.search(k):
                for kk, vv in v.items():
                    tot[kk] += vv
        r_c = tot["sells"] + tot["redeems"] + tot["merges"] - tot["buys"] - tot["splits"]
        classes[c] = {"markets": len(m), "result": str(r_c), "totals": {k: str(v) for k, v in tot.items()}, "per_market": m}
    return {"address": a, "rows": len(rows),
            "first_utc": datetime.fromtimestamp(min(ts), timezone.utc).isoformat() if ts else None,
            "last_utc": datetime.fromtimestamp(max(ts), timezone.utc).isoformat() if ts else None,
            "totals": {k: str(v) for k, v in sorted(t.items())}, "trading_result": str(res),
            "withdrawals_minus_deposits": str(t["withdrawals"] - t["deposits"]),
            "open_share_tokens": {f"{k[0]} | {k[1]}": str(v) for k, v in shares.items() if v > Decimal("0.01")},
            "classes": classes}


if __name__ == "__main__":
    out = {a.lower(): ledger(a.lower()) for a in sys.argv[2:]}
    Path(sys.argv[1]).write_text(json.dumps(out, indent=1))
    for a, v in out.items():
        print(a, v["rows"], "result", round(Decimal(v["trading_result"]), 2), "W-D", round(Decimal(v["withdrawals_minus_deposits"]), 2),
              "open", len(v["open_share_tokens"]), {c: round(Decimal(x["result"]), 2) for c, x in v["classes"].items() if x["markets"]})
