"""Summary of one run of phi_engine, from its database, for publication: counts, lateness and the alerts raised.
No wallet and no transaction is written: the journal of alerts itself stays next to the database.

    python3 -I scripts/summarize_live_run.py ENGINE.sqlite [ENGINE.log] > data/live_run_YYYYMMDD.json"""
import json, os, re, sqlite3, sys, time

NAMES = {"0xe111180000d2663c0091e4f400237545b87b996b": "CTF Exchange", "0xe2222d279d744050d28e00520010520000310f59": "Neg Risk CTF Exchange",
         "0xe3333700ca9d93003f00f0f71f8515005f6c00aa": "ExchangeV3 (Polymarket Protocol V2)"}


def q(xs, p):
    xs = sorted(xs)
    return round(xs[int(p * (len(xs) - 1))], 1) if xs else None


def main():
    path = sys.argv[1]
    con = sqlite3.connect("file:" + path + "?mode=ro", uri=True); con.row_factory = sqlite3.Row
    utc = lambda t: time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(t)) if t else None
    start = con.execute("select t, body from journal where kind='start' order by seq limit 1").fetchone()
    cp = json.loads(con.execute("select value from checkpoints where key='chain'").fetchone()[0])
    first_block = json.loads(start["body"])["first_block"]
    cover = {NAMES.get(r[0], r[0]): {"fills": r[1], "of_1000_usd_or_more": r[2], "usd": round(r[3])} for r in con.execute(
        "select exchange, sum(fills), sum(large), sum(cash) from coverage group by exchange")}
    late = [r[0] for r in con.execute("select seen - ts from fills")]
    alerts = [json.loads(r[0]) for r in con.execute("select body from alerts order by t_alert")]
    out = {"database": os.path.basename(path), "started_utc": utc(start["t"]), "last_block_stored_utc": utc(cp["t"]), "minutes": round((cp["t"] - start["t"]) / 60, 1),
           "blocks": [first_block, cp["block"]], "blocks_read": cp["block"] - first_block + 1,
           "fills_seen_by_exchange": cover, "fills_seen": sum(v["fills"] for v in cover.values()),
           "rows_kept": con.execute("select count(*) from fills").fetchone()[0],
           "seconds_from_block_to_storage": {"median": q(late, 0.5), "p90": q(late, 0.9), "max": q(late, 1.0), "rows": len(late)},
           "tokens_by_status": dict(con.execute("select status, count(*) from tokens group by status").fetchall()),
           "markets_by_family": dict(con.execute("select family, count(*) from markets group by family").fetchall()),
           "entries_by_state": dict(con.execute("select state, count(*) from entries group by state").fetchall()),
           "entries": con.execute("select count(*) from entries").fetchone()[0],
           "deposits_traced": con.execute("select count(*) from deposits").fetchone()[0], "addresses_described": con.execute("select count(*) from addresses").fetchone()[0],
           "links_to_plain_keys": con.execute("select count(*) from links").fetchone()[0],
           "alerts_by_class": dict(con.execute("select cls, count(*) from alerts group by cls").fetchall()),
           "seconds_from_trade_to_alert": {"median": q([a["seconds_from_trade_to_alert"] for a in alerts], 0.5), "p90": q([a["seconds_from_trade_to_alert"] for a in alerts], 0.9),
                                           "max": q([a["seconds_from_trade_to_alert"] for a in alerts], 1.0)},
           "journal_kinds": dict(con.execute("select kind, count(*) from journal group by kind").fetchall()),
           "database_bytes": os.path.getsize(path),
           "alerts": [{"class": a["class"], "utc": a["t_alert_utc"], "seconds_from_trade_to_alert": a["seconds_from_trade_to_alert"], "market": a["market"]["title"],
                       "side": a["market"]["outcome"], "family": a["market"]["family"], "price": a["market"]["price_at_alert"], "entry_usd": a["wallets"]["entry_usd"],
                       "net_bought_usd": a["wallets"]["net_bought_usd"], "plain_keys_behind_deposits": len(a["wallets"]["plain_keys_behind_deposits"]),
                       "validation": a["validation"].get("status")} for a in alerts]}
    if len(sys.argv) > 2:                                    # the log of the run: passes, source errors, largest lag
        text = open(sys.argv[2]).read()
        behind = [int(x) for x in re.findall(r"behind (\d+)", text)]
        out["log"] = {"passes": len(behind), "passes_behind_the_head": sum(1 for b in behind if b > 0), "largest_lag_blocks": max(behind) if behind else None,
                      "source_errors": len(re.findall(r"source error:", text)), "other_errors": len(re.findall(r" error: ", text))}
    json.dump(out, sys.stdout, indent=1); print()


if __name__ == "__main__":
    main()
