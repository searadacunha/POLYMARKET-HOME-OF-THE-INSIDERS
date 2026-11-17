#!/usr/bin/env python3
"""Render results/audit/publication_tables.json as two Markdown tables (no recomputation, no outcome re-join).

Usage: python3 scripts/audit/render_tables.py results/audit/publication_tables.json > results/audit/tables.md
"""
import json, sys


def short(x, n=10):
    return x[:n] + "…" if x and len(x) > n else (x or "")


def table(rows):
    head = ("| # | Alert (UTC) | Market | Side | Last fill | Wallets | Shift USD | Won | Result/share at 1 % | "
            "Largest wallet | Its fills (tx) | Tape |\n|---:|---|---|---|---:|---:|---:|---|---:|---|---|---|")
    out = [head]
    for i, r in enumerate(rows, 1):
        txs = " ".join(f"[{short(t, 10)}](https://polygonscan.com/tx/{t})" for t in r["largest_wallet_txs"][:2])
        out.append(
            f'| {i} | {r["alert_ts_utc"]} | [{short(r["event_slug"], 38)}]({r["market_url"]}) | {r["side"]} | '
            f'{r["entry_price_last_fill"]:.3f} | {r["n_wallets"]} ({r["wallets_verified"]}) | '
            f'{r["total_shift_usd"]:,.0f} | {"yes" if r["win"] else "**no**"} | {r["payoff_per_share_1pct"]:+.3f} | '
            f'`{short(r["largest_wallet"], 12)}` | {txs} | [v2]({r["tape_url"]}) |')
    return "\n".join(out)


def main():
    t = json.load(open(sys.argv[1]))
    print("## Best alerts\n")
    print(f'Rule: {t["best_alerts_rule"]}.\n')
    print(table(t["best_alerts"]))
    print("\n## False positives\n")
    print(f'Rule: {t["false_positives_rule"]}.\n')
    print(table(t["false_positives"]))


if __name__ == "__main__":
    main()
