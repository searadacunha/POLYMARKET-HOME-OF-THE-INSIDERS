#!/usr/bin/env python3
"""Describe confirmed V2 maker-taker event legs, not buyer-seller ownership or profitability."""
import argparse
import json
import re
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

EXCHANGES = {
    "0xe111180000d2663c0091e4f400237545b87b996b",
    "0xe2222d279d744050d28e00520010520000310f59",
}
ADDRESS = re.compile(r"^0x[0-9a-f]{40}$")


def addr(value):
    s = str(value).lower()
    if not ADDRESS.fullmatch(s):
        raise ValueError("Malformed account address")
    return s


def summarize(fills, cutoff=None):
    seen = {}
    edges = defaultdict(lambda: {"fills": 0, "txs": set(), "cash": Decimal(0),
                                 "first_ts": None, "last_ts": None, "maker_buy": 0, "maker_sell": 0})
    ignored_synthetic = 0
    for row in fills:
        exchange = addr(row["exchange"])
        if exchange not in EXCHANGES:
            raise ValueError("Unsupported V2 exchange; verify its event semantics before use")
        maker, taker = addr(row["wallet"]), addr(row["counterparty"])
        ts = int(row["ts"])
        if cutoff is not None and ts > cutoff:
            continue
        if taker == exchange or maker == exchange:
            ignored_synthetic += 1
            continue
        side = row["side"]
        if side not in ("BUY", "SELL"):
            raise ValueError("Invalid order side")
        tx = str(row["tx"]).lower()
        if len(tx) != 66 or not tx.startswith("0x") or any(c not in "0123456789abcdef" for c in tx[2:]):
            raise ValueError("Invalid transaction hash")
        log_index = int(row["log_index"])
        if log_index < 0:
            raise ValueError("Negative log index")
        token = str(row["token_id"])
        if not token.isdecimal():
            raise ValueError("Invalid token ID")
        cash = Decimal(str(row["cash"]))
        if not cash.is_finite() or cash <= 0:
            raise ValueError("Invalid cash amount")
        identity = (exchange, tx, log_index)
        fingerprint = (maker, taker, token, side, str(cash), ts)
        if identity in seen:
            if seen[identity] != fingerprint:
                raise ValueError("Conflicting fill for one log index")
            continue
        seen[identity] = fingerprint
        pair = tuple(sorted((maker, taker)))
        record = edges[(exchange, token, *pair)]
        record["fills"] += 1
        record["txs"].add(tx)
        record["cash"] += cash
        record["first_ts"] = ts if record["first_ts"] is None else min(ts, record["first_ts"])
        record["last_ts"] = ts if record["last_ts"] is None else max(ts, record["last_ts"])
        record["maker_buy" if side == "BUY" else "maker_sell"] += 1
    result = []
    for (exchange, token, a, b), rec in sorted(edges.items()):
        result.append({
            "exchange": exchange, "token_id": token, "counterparties": [a, b],
            "self_match": a == b,
            "fill_legs": rec["fills"], "distinct_transactions": len(rec["txs"]),
            "cash_on_maker_legs": str(rec["cash"]),
            "first_ts": rec["first_ts"], "last_ts": rec["last_ts"],
            "maker_buy_legs": rec["maker_buy"], "maker_sell_legs": rec["maker_sell"],
            "match_type": "UNRESOLVED",
        })
    return {
        "status": "DESCRIPTIVE_EXECUTION_GRAPH_ONLY",
        "ignored_synthetic_legs": ignored_synthetic,
        "unique_maker_legs": len(seen),
        "edges": result,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--cutoff-ts", type=int)
    args = parser.parse_args()
    with args.input.open(encoding="utf-8") as stream:
        out = summarize((json.loads(line) for line in stream if line.strip()), args.cutoff_ts)
    report = json.dumps(out, indent=2) + "\n"
    if args.output:
        args.output.write_text(report, encoding="utf-8")
    else:
        print(report, end="")


if __name__ == "__main__":
    main()
