"""Command line of the monitor.

  python3 -m phi_monitor doctor                         check every public source and the on-chain decoder
  python3 -m phi_monitor run --db FILE [--minutes N]    watch the exchanges, open candidates, evaluate, alert
  python3 -m phi_monitor status --db FILE               checkpoints, counts, open candidates, journal integrity
  python3 -m phi_monitor alerts --db FILE [--json]      alerts with their reasons
  python3 -m phi_monitor backtest --db FILE --token ID --start "YYYY-MM-DD HH:MM" --end "YYYY-MM-DD HH:MM"
                                                        chronological replay of one past market (network, as-of reads)
  python3 -m phi_monitor replay --db FILE               re-evaluate every stored market from stored rows only (no network)
  python3 -m phi_monitor prices --db FILE --token ID [--minutes N]
                                                        record the trade prints of one market from the public WebSocket
"""
import argparse, datetime as dt, json, sys, time
from . import chain, collect, detect, net, store


def _ts(s):
    return int(dt.datetime.strptime(s, "%Y-%m-%d %H:%M").replace(tzinfo=dt.timezone.utc).timestamp())


def doctor(_):
    ok = True
    def check(name, fn):
        nonlocal ok
        try:
            print(f"ok    {name}: {fn()}")
        except Exception as e:                            # a failed source is reported, never hidden
            ok = False; print(f"FAIL  {name}: {e}")
    check("polygon head block", chain.head)
    def decoder():
        h = chain.head() - 5; fl = chain.fills(h - 2, h)
        rows = net.get_json(f"{collect.DATA}/v2/trades?limit=1000&taker_only=false&cb={int(time.time() * 1000)}")["data"]
        api = {}
        for r in rows:
            api.setdefault(r["transaction_hash"], []).append((r["proxy_wallet"].lower(), str(r["token_id"]), r["side"], round(float(r["size"]), 4)))
        same = sum(sorted((f["wallet"], f["token_id"], f["side"], round(f["shares"], 4)) for f in fl if f["tx"] == tx) == sorted(api[tx])
                   for tx in {f["tx"] for f in fl} if tx in api)
        seen = len({f["tx"] for f in fl} & set(api))
        if seen and same != seen:
            raise RuntimeError(f"on-chain fills differ from the data API on {seen - same} of {seen} transactions")
        return f"{len(fl)} fills in 3 blocks; {same}/{seen} transactions identical to the data API"
    check("fill decoder against the data API", decoder)
    check("gamma", lambda: len(net.get_json(f"{collect.GAMMA}/events/keyset?closed=false&limit=1")["events"]))
    check("clob prices-history", lambda: "answers" if "history" in net.get_json(
        f"{collect.CLOB}/prices-history?market=75406677405586796507165996816755205915219135539748390183994296030461533919844&startTs=1760040000&endTs=1760050000&fidelity=10") else "no history field")
    check("collateral symbols", lambda: [bytes.fromhex(net.rpc("eth_call", [{"to": a, "data": "0x95d89b41"}, "latest"])[130:]).rstrip(b"\x00").decode() for a in chain.STABLES])
    return 0 if ok else 1


def run(a):
    con = store.connect(a.db); end = time.time() + 60 * a.minutes if a.minutes else None
    while True:
        try:
            w = collect.watch_chain(con)
            new = detect.scan(con)
            print(time.strftime("%H:%M:%S"), f"blocks {w['from']}-{w['to']} fills {w['fills']} triggers {w['triggers']} new alerts {len(new)}", flush=True)
            for b in new:
                print("ALERT", b["level"], b["t_alert_utc"], b["title"], "|", b["side"], "|", "; ".join(b["reasons"][:2]), flush=True)
        except net.SourceError as e:                      # the checkpoint did not move: the next loop resumes from it
            print(time.strftime("%H:%M:%S"), "source error:", str(e)[:200], flush=True)
        if a.once or (end and time.time() >= end):
            return 0
        time.sleep(a.interval)


def status(a):
    con = store.connect(a.db)
    print("checkpoint chain:", store.checkpoint(con, "chain"))
    for t in ("fills", "markets", "prices", "baselines", "funding", "alerts", "journal"):
        print(f"{t:10}", con.execute(f"select count(*) from {t}").fetchone()[0])
    print("candidates:", dict(con.execute("select state, count(*) from candidates group by state").fetchall()))
    n, broken = store.verify_journal(con)
    print("journal:", n, "entries,", "intact" if broken is None else f"BROKEN at seq {broken}")
    print("requests this process:", dict(net.COUNTS))
    return 0 if broken is None else 1


def alerts(a):
    con = store.connect(a.db)
    for (body,) in con.execute("select body from alerts order by t_alert"):
        b = json.loads(body)
        if a.json:
            print(json.dumps(b)); continue
        print(f"\n{b['level']}  {b['t_alert_utc']}  {b['title']}  [{b['side']}]  id {b['id']}")
        for r in b["reasons"]:
            print("  -", r)
        if b["cluster"]:
            print("  - other wallets of this event paid by the same key:", ", ".join(x["wallet"] for x in b["cluster"]))
        print("  evidence:", ", ".join(b["evidence_tx"][:3]))
        print("  other explanations to rule out:", "; ".join(b["competing_explanations"]))
    return 0


def backtest(a):
    con = store.connect(a.db); start, end = _ts(a.start), _ts(a.end)
    m = collect.resolve(con, a.token)
    if m is None:
        print("unknown token or not a Yes/No market"); return 1
    for lo in range(start - 8 * 3600, end, 13 * 86400):  # the endpoint refuses more than about 14 days per call
        collect.fetch_prices(con, m["yes_token"], lo, min(end, lo + 13 * 86400))
    t = collect.fetch_tape(con, m["condition_id"], start - 3600)
    if not t["complete"]:
        print("tape too deep (more than 300 pages): not replayed"); return 1
    res = detect.backtest(con, m["condition_id"], start, end)
    print(json.dumps({"market": m["title"], "tape_rows": t["rows"], "result": res}, indent=1))
    return 0


def replay(a):
    con = store.connect(a.db); out = detect.replay(con)
    stored = {r[0] for r in con.execute("select id from alerts")}
    got = {r["id"] for r in out if r.get("level")}
    print(json.dumps({"replayed_alerts": sorted(got), "journaled_not_reproduced": sorted(stored - got), "new_in_replay": sorted(got - stored)}, indent=1))
    return 0 if stored <= got else 1


def prices(a):
    con = store.connect(a.db); m = collect.resolve(con, a.token)
    if m is None:
        print("unknown token or not a Yes/No market"); return 1
    events = collect.watch_prices(con, [m["yes_token"], m["no_token"]], time.time() + 60 * a.minutes)
    n = con.execute("select count(*) from ws_trades where token_id in (?,?)", (m["yes_token"], m["no_token"])).fetchone()[0]
    print(json.dumps({"market": m["title"], "trade_prints_stored": n, "connection_events": [(round(t), e, str(d)[:80]) for t, e, d in events]}, indent=1))
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="phi_monitor", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd", required=True)
    sp.add_parser("doctor").set_defaults(fn=doctor)
    r = sp.add_parser("run"); r.add_argument("--db", required=True); r.add_argument("--minutes", type=float); r.add_argument("--once", action="store_true")
    r.add_argument("--interval", type=float, default=8.0); r.set_defaults(fn=run)
    for name, fn in (("status", status), ("replay", replay)):
        q = sp.add_parser(name); q.add_argument("--db", required=True); q.set_defaults(fn=fn)
    q = sp.add_parser("alerts"); q.add_argument("--db", required=True); q.add_argument("--json", action="store_true"); q.set_defaults(fn=alerts)
    b = sp.add_parser("backtest"); b.add_argument("--db", required=True); b.add_argument("--token", required=True)
    b.add_argument("--start", required=True); b.add_argument("--end", required=True); b.set_defaults(fn=backtest)
    w = sp.add_parser("prices"); w.add_argument("--db", required=True); w.add_argument("--token", required=True)
    w.add_argument("--minutes", type=float, default=10.0); w.set_defaults(fn=prices)
    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
