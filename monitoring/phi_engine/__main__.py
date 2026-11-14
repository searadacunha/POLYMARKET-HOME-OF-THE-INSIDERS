"""Command line of the engine.

  python3 -m phi_engine doctor                      check every source, the decoder and the exchange registry
  python3 -m phi_engine run --db FILE [--minutes N] watch the chain, open entries, evaluate them, raise alerts
  python3 -m phi_engine status --db FILE            position, lag, counts, entries by state, journal integrity
  python3 -m phi_engine alerts --db FILE [--json] [--class NAME] [--last N]
  python3 -m phi_engine journal --db FILE [--kind K]  gaps, unknown exchanges, entries left without an answer
  python3 -m phi_engine replay --db FILE            re-read the stored view of each alert and check that it still fires
  python3 -m phi_engine priority --db FILE --out FILE [--hours N]
                                                    markets with entries in the last hours, in the format the order-book
                                                    collector (livecollect) takes as --markets

One process per database: a lock file next to the database refuses a second `run`."""
import argparse, fcntl, gzip, json, os, sys, time
from phi_monitor import net
from . import asof, contracts, enrich, feed, report, store

SENTINEL_EVERY = 40             # passes between two looks for an exchange the registry does not know


def load_rarity():
    try:
        with gzip.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "reference", "rarity_discovery.json.gz"), "rt") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None             # without the reference population the rarity class is simply not computed


def doctor(_):
    ok = True
    def check(name, fn):
        nonlocal ok
        try:
            print(f"ok    {name}: {fn()}")
        except Exception as e:                           # a failed source is shown, never hidden
            ok = False; print(f"FAIL  {name}: {type(e).__name__} {e}")
    check("polygon head block", feed.head)
    def decoder():
        tip = feed.head() - 5; fills, bad = feed.read_fills(tip - 2, tip)
        by = {}
        for f in fills:
            by[contracts.EXCHANGES[f["exchange"]]] = by.get(contracts.EXCHANGES[f["exchange"]], 0) + 1
        return f"{len(fills)} fills in 3 blocks, {len(bad)} undecodable, by exchange {by}"
    check("fills of the registered exchanges", decoder)
    def emitters():
        tip = feed.head() - 5
        logs = net.rpc("eth_getLogs", [{"fromBlock": hex(tip - 3), "toBlock": hex(tip), "topics": [contracts.ORDER_FILLED]}])
        u = contracts.unknown_emitters(logs)
        if u:
            raise RuntimeError(f"OrderFilled emitted by contracts outside the registry: {u}")
        return f"{len(logs)} OrderFilled logs in 4 blocks, every emitter is registered"
    check("no exchange outside the registry", emitters)
    check("gamma", lambda: len(net.get_json(f"{feed.GAMMA}/events/keyset?closed=false&limit=1")["events"]))
    check("data API activity", lambda: "answers" if "data" in net.get_json(f"{enrich.DATA}/v2/activity?user=0x0000000000000000000000000000000000000001&limit=1") else "no data field")
    check("rarity reference", lambda: "present" if load_rarity() else "absent: class M1 is not computed")
    return 0 if ok else 1


def run(a):
    lock = open(a.db + ".lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("another engine is already running on this database"); return 2
    con = store.connect(a.db); end = time.time() + 60 * a.minutes if a.minutes else None; rarity = load_rarity(); n = 0
    while True:
        n += 1; line = time.strftime("%H:%M:%S")
        try:
            w = feed.watch(con)
            cursor = (store.checkpoint(con, "entries") or {}).get("rowid", 0)
            new, last, c = feed.open_entries(con, cursor)
            with con:
                store.checkpoint(con, "entries", {"rowid": last})
            alerts, counts = enrich.work(con, a.db, rarity=rarity)
            if n % SENTINEL_EVERY == 1:
                unknown = feed.sentinel(con)
                if unknown:
                    print(line, "UNKNOWN EXCHANGE emitting OrderFilled:", unknown, flush=True)
            print(line, f"blocks {w['from']}-{w['to']} behind {w['behind']} fills {w['fills']} kept {w['stored']} large buys {c['large_buys']} new entries {new} "
                        f"evaluated {counts['evaluated']} waiting {counts['not_ready']} alerts {len(alerts)}"
                        + (f" | combos {c['combo']}" if c["combo"] else "") + (f" | tokens unknown to the catalogue {c['unknown_token']}" if c["unknown_token"] else ""), flush=True)
            for b in alerts:
                print(report.render(b), flush=True)
        except net.SourceError as e:                     # checkpoints did not move: the next pass resumes from them
            print(line, "source error:", str(e)[:200], flush=True)
        except Exception as e:                           # anything else is journaled and the engine keeps running
            with con:
                store.journal(con, "pass_error", {"type": type(e).__name__, "detail": str(e)[:300]})
            print(line, "error:", type(e).__name__, str(e)[:200], flush=True)
        if a.once or (end and time.time() >= end):
            return 0
        time.sleep(a.interval)


def status(a):
    con = store.connect(a.db); cp = store.checkpoint(con, "chain")
    print("chain checkpoint:", cp, "| seconds since last block stored:", None if not cp else int(time.time() - cp["t"]))
    for t in ("fills", "tokens", "markets", "entries", "deposits", "addresses", "links", "alerts", "journal"):
        print(f"{t:10}", con.execute(f"select count(*) from {t}").fetchone()[0])
    print("entries by state:", dict(con.execute("select state, count(*) from entries group by state").fetchall()))
    print("alerts by class:", dict(con.execute("select cls, count(*) from alerts group by cls").fetchall()))
    print("fills seen by exchange:", {contracts.EXCHANGES.get(k, k): v for k, v in con.execute("select exchange, sum(fills) from coverage group by exchange")},
          "| rows kept:", con.execute("select count(*) from fills").fetchone()[0])
    lat = [r[0] for r in con.execute("select seen - ts from fills order by rowid desc limit 5000")]
    if lat:
        lat.sort(); print(f"lateness of the last {len(lat)} fills (stored minus block time): median {lat[len(lat) // 2]:.1f} s, p90 {lat[int(0.9 * (len(lat) - 1))]:.1f} s")
    print("journal kinds:", dict(con.execute("select kind, count(*) from journal group by kind").fetchall()))
    n, broken = store.verify_journal(con)
    print("journal:", n, "entries,", "intact" if broken is None else f"BROKEN at seq {broken}")
    return 0 if broken is None else 1


def alerts(a):
    con = store.connect(a.db)
    q, p = "select body from alerts", []
    if a.cls:
        q += " where cls=?"; p.append(a.cls)
    rows = con.execute(q + " order by t_alert", p).fetchall()
    for (body,) in rows[-a.last:] if a.last else rows:
        print(body if a.json else report.render(json.loads(body)))
    return 0


def journal(a):
    con = store.connect(a.db)
    q, p = "select seq, t, kind, body from journal", []
    if a.kind:
        q += " where kind=?"; p.append(a.kind)
    for seq, t, kind, body in con.execute(q + " order by seq", p):
        print(seq, report.utc(t), kind, body)
    return 0


def replay(a):
    """Each alert is re-derived from the wallet rows kept with it: same class, same moment, or it is reported."""
    con = store.connect(a.db); bad = 0; n = 0
    for body, in con.execute("select body from alerts order by t_alert"):
        b = json.loads(body); n += 1
        v = con.execute("select body from views where wallet=? and condition_id=? and oi=?", (b["wallets"]["wallet"], b["market"]["condition_id"],
                        con.execute("select oi from alerts where id=?", (b["id"],)).fetchone()[0])).fetchone()
        kept = json.loads(v[0]) if v else None
        same = bool(kept) and (b["class"][:2] != "C7" or (kept["heavy"] and kept["heavy"]["t"] <= b["t_alert"]))
        bad += not same
        if not same:
            print("NOT REPRODUCED", b["id"], b["class"])
    print(json.dumps({"alerts": n, "not_reproduced": bad})); return 1 if bad else 0


def priority(a):
    con = store.connect(a.db); since = time.time() - 3600 * a.hours; out = []
    for r in con.execute("select m.condition_id, m.title, count(*) n, max(e.t) last from entries e join markets m on m.condition_id=e.condition_id "
                         "where e.t>=? group by m.condition_id order by n desc limit ?", (since, a.limit)):
        toks = {o: t for t, o in con.execute("select token_id, oi from tokens where condition_id=?", (r[0],))}
        out.append({"condition_id": r[0], "question": r[1], "yes_token": toks.get(0), "no_token": toks.get(1), "entries": r[2], "last_entry": r[3]})
    with open(a.out, "w") as f:
        json.dump(out, f, indent=1)
    print(f"{len(out)} markets written to {a.out}"); return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="phi_engine", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd", required=True)
    sp.add_parser("doctor").set_defaults(fn=doctor)
    r = sp.add_parser("run"); r.add_argument("--db", required=True); r.add_argument("--minutes", type=float); r.add_argument("--once", action="store_true")
    r.add_argument("--interval", type=float, default=8.0); r.set_defaults(fn=run)
    for name, fn in (("status", status), ("replay", replay)):
        q = sp.add_parser(name); q.add_argument("--db", required=True); q.set_defaults(fn=fn)
    q = sp.add_parser("alerts"); q.add_argument("--db", required=True); q.add_argument("--json", action="store_true"); q.add_argument("--class", dest="cls")
    q.add_argument("--last", type=int); q.set_defaults(fn=alerts)
    q = sp.add_parser("journal"); q.add_argument("--db", required=True); q.add_argument("--kind"); q.set_defaults(fn=journal)
    q = sp.add_parser("priority"); q.add_argument("--db", required=True); q.add_argument("--out", required=True); q.add_argument("--hours", type=float, default=6.0)
    q.add_argument("--limit", type=int, default=20); q.set_defaults(fn=priority)
    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
