"""How the Nobel fixture was made (network needed; the tests themselves run offline).

    python3 -m phi_monitor backtest --db /tmp/nobel.sqlite \
        --token 75406677405586796507165996816755205915219135539748390183994296030461533919844 \
        --start "2025-10-09 12:00" --end "2025-10-10 09:00"
    python3 tests/make_fixtures.py /tmp/nobel.sqlite fixtures/nobel_machado_20251009.json

Only the rows needed to replay the evening of 9 October 2025 are exported: public on-chain fills as served by the data
API (addresses, sizes, prices, transaction hashes), 10-minute prices, the as-of history of the initiator, its funding.
No profile text is read or stored anywhere in this package."""
import json, sqlite3, sys

T0, T1 = 1760043600, 1760052600      # 2025-10-09 21:00 -> 23:30 UTC (tape)
P0, P1 = 1760000400, 1760054400      # 2025-10-09 09:00 -> 2025-10-10 00:00 UTC (prices)


def main(db, out):
    con = sqlite3.connect(db); con.row_factory = sqlite3.Row
    m = dict(con.execute("select * from markets").fetchone())
    fills = [dict(r) for r in con.execute("select tx, log_index, ts, wallet, token_id, side, shares, cash, price from fills where source='api' and ts between ? and ? "
                                          "order by ts, log_index desc", (T0, T1))]
    prices = [list(r) for r in con.execute("select ts, price from prices where token_id=? and ts between ? and ? order by ts", (m["yes_token"], P0, P1))]
    wallets = {f["wallet"] for f in fills}
    base = [dict(r) for r in con.execute("select wallet, as_of, body from baselines") if r["wallet"] in wallets and T0 <= r["as_of"] <= T1]
    fund = [dict(r) for r in con.execute("select * from funding") if r["proxy"] in {b["wallet"] for b in base}]
    m.pop("updated", None)
    json.dump({"note": "Machado market, Nobel Peace Prize 2025; see tests/make_fixtures.py", "market": m, "prices": prices, "fills": fills,
               "baselines": base, "funding": fund}, open(out, "w"), indent=0)
    print("fills", len(fills), "prices", len(prices), "baselines", len(base), "funding", len(fund))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
