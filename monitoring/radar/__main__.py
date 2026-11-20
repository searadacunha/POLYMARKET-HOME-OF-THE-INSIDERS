"""Radar: seals the alerts of phi_engine with the fields a reviewer needs, evaluates them later, and shows them.

  cd monitoring
  python3 -m radar seal --engine-db ~/phi_engine.sqlite --out ~/radar        # new engine alerts -> radar.alerts.jsonl
  python3 -m radar watch --engine-db ~/phi_engine.sqlite --out ~/radar       # the same every 30 s, while phi_engine runs
  python3 -m radar verify --engine-db ~/phi_engine.sqlite --out ~/radar      # both chains, and every record against its engine line
  python3 -m radar evaluate --out ~/radar --fee 0.0                          # later: prices after 1, 6, 24 h, resolution, shadow trade
  python3 -m radar dashboard --out ~/radar --html ~/radar/index.html
  python3 -m radar anchor --out ~/radar                                      # head hash to publish elsewhere

No key, no account, no order. A record is written once and never changed; evaluations go to their own chain."""
import argparse, hashlib, json, os, sys, time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from radar import chain, dashboard, evaluate, notify, record  # noqa: E402

DAY = 86400


def paths(out):
    os.makedirs(out, exist_ok=True)
    return os.path.join(out, "radar.alerts.jsonl"), os.path.join(out, "radar.evaluations.jsonl")


def seal(engine_db, out, now=time.time, env=None):
    """Seal every engine alert line not sealed yet, in file order, under one lock for the whole pass. Refuses a broken
    engine chain; an engine line still being written (no newline yet) waits for the next pass. Returns new records."""
    src = engine_db + ".alerts.jsonl"
    rows = chain.read(src, partial_tail_ok=True)
    prev = chain.ZERO
    for i, (line, a) in enumerate(rows, 1):
        if a.get("previous_line_sha256") != prev:
            raise SystemExit(f"engine alert file broken at line {i}, nothing sealed")
        prev = hashlib.sha256(line).hexdigest()
    alerts_path, _ = paths(out)
    new = []
    with chain.lock(alerts_path):
        done = {o.get("engine_line_sha256") for _, o in chain.read(alerts_path)}
        for i, (line, a) in enumerate(rows):
            sha = hashlib.sha256(line).hexdigest()
            if sha in done:
                continue
            load = sum(1 for _, b in rows[:i] if b.get("class") == a.get("class") and a.get("t_alert") and b.get("t_alert")
                       and a["t_alert"] - DAY <= b["t_alert"] <= a["t_alert"])
            t = now()
            rec = record.build(a, sha, t, load_24h=load)
            chain.append_locked(alerts_path, rec); done.add(sha); new.append(rec)
            if isinstance(a.get("t_alert"), (int, float)) and t - a["t_alert"] <= 3600:   # no backlog notifications
                for kind, status in notify.send(rec, env):
                    print(f"notify {kind}: {status}", flush=True)
    return new


KEYS = (("class", lambda r: r["risk"]["class"], lambda a: a.get("class")),
        ("condition_id", lambda r: r["market"]["condition_id"], lambda a: (a.get("market") or {}).get("condition_id")),
        ("trigger_t", lambda r: r["trigger_t"], lambda a: a.get("t_alert")),
        ("fills", lambda r: [f.get("tx") for f in r["transactions"]["fills"]], lambda a: [f.get("tx") for f in (a.get("evidence") or {}).get("fills") or []]))


def verify(out, engine_db=None):
    """Both chains and their anchors; with the engine file, every record against the engine line it names, records
    sealed twice, and engine lines not sealed yet."""
    alerts_path, evals_path = paths(out)
    report = {}
    for name, p in (("alerts", alerts_path), ("evaluations", evals_path)):
        n, head, errors = chain.verify(p); report[name] = {"lines": n, "head": head, "errors": errors}
    recs = [o for _, o in chain.read(alerts_path)] if not report["alerts"]["errors"] else []
    seen, dup = set(), []
    for r in recs:
        (dup.append(r["id"]) if r.get("engine_line_sha256") in seen else seen.add(r.get("engine_line_sha256")))
    report["records_sealed_twice"] = dup
    if engine_db:
        engine = {hashlib.sha256(l).hexdigest(): a for l, a in chain.read(engine_db + ".alerts.jsonl", partial_tail_ok=True)}
        report["records_without_engine_line"] = [r["id"] for r in recs if r.get("engine_line_sha256") not in engine]
        report["records_differing_from_engine_line"] = [r["id"] for r in recs if r.get("engine_line_sha256") in engine
                                                        and any(f(r) != g(engine[r["engine_line_sha256"]]) for _, f, g in KEYS)]
        report["engine_lines_not_sealed"] = len(set(engine) - seen)
    return report


def run_evaluate(out, get_json, now=time.time, fee=0.0):
    """One evaluation per sealed record not FINAL yet; a line is written only when the evaluation changed."""
    alerts_path, evals_path = paths(out)
    last = {}
    for _, o in chain.read(evals_path):
        last[o["alert"]] = o
    strip = lambda e: {k: v for k, v in e.items() if k not in ("evaluated_at", "previous_line_sha256")}
    written = 0
    for _, rec in chain.read(alerts_path):
        if (last.get(rec["id"]) or {}).get("status") == "FINAL":
            continue
        try:
            e = evaluate.evaluate(rec, get_json, now(), fee)
        except Exception as err:                  # a source that fails leaves the alert for the next run
            print(f"{rec['id']}: {type(err).__name__} {str(err)[:120]}", flush=True); continue
        if e and (rec["id"] not in last or strip(last[rec["id"]]) != strip(e)):
            chain.append(evals_path, dict(e, evaluated_at=int(now()))); written += 1
    return written


def latest_evaluations(evals_path):
    last = {}
    for _, o in chain.read(evals_path):
        last[o["alert"]] = o
    return list(last.values())


def main(argv=None):
    ap = argparse.ArgumentParser(prog="radar"); sp = ap.add_subparsers(dest="cmd", required=True)
    for name in ("seal", "watch", "verify"):
        p = sp.add_parser(name); p.add_argument("--engine-db", required=(name != "verify")); p.add_argument("--out", required=True)
        if name == "watch":
            p.add_argument("--interval", type=float, default=30.0); p.add_argument("--minutes", type=float)
    p = sp.add_parser("evaluate"); p.add_argument("--out", required=True); p.add_argument("--fee", type=float, default=0.0)
    p = sp.add_parser("dashboard"); p.add_argument("--out", required=True); p.add_argument("--html", required=True)
    p = sp.add_parser("anchor"); p.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if a.cmd == "seal":
        print(f"{len(seal(a.engine_db, a.out))} new records")
    elif a.cmd == "watch":
        end = time.time() + 60 * a.minutes if a.minutes else None
        while True:
            try:
                new = seal(a.engine_db, a.out)
            except (SystemExit, ValueError, OSError) as err:   # journaled on the terminal; the next pass tries again
                print(time.strftime("%H:%M:%S"), "seal failed:", str(err)[:200], flush=True); new = []
            if new:
                print(time.strftime("%H:%M:%S"), f"{len(new)} sealed:", ", ".join(f"{r['risk']['class']} {r['id']}" for r in new), flush=True)
            if end and time.time() >= end:
                return 0
            time.sleep(a.interval)
    elif a.cmd == "verify":
        r = verify(a.out, a.engine_db); print(json.dumps(r, indent=1))
        return 1 if (r["alerts"]["errors"] or r["evaluations"]["errors"] or r["records_sealed_twice"]
                     or r.get("records_without_engine_line") or r.get("records_differing_from_engine_line")) else 0
    elif a.cmd == "evaluate":
        from phi_monitor import net
        print(f"{run_evaluate(a.out, net.get_json, fee=a.fee)} evaluations written")
    elif a.cmd == "dashboard":
        alerts_path, evals_path = paths(a.out)
        with open(a.html, "w") as f:
            f.write(dashboard.render([o for _, o in chain.read(alerts_path)], latest_evaluations(evals_path)))
        print(a.html)
    elif a.cmd == "anchor":
        n, head, errors = chain.verify(paths(a.out)[0])
        if errors:
            print(json.dumps({"intact": False, "errors": errors})); return 1
        print(json.dumps(chain.anchor(paths(a.out)[0])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
