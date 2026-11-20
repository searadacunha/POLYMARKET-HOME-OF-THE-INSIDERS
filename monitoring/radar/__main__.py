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
    """Seal every engine alert line not sealed yet, in file order. Refuses a broken engine chain. Returns new records."""
    src = engine_db + ".alerts.jsonl"
    n, _, errors = chain.verify(src)
    if errors:
        raise SystemExit(f"engine alert file broken, nothing sealed: {errors[:3]}")
    alerts_path, _ = paths(out)
    done = {o.get("engine_line_sha256") for _, o in chain.read(alerts_path)}
    rows, new = chain.read(src), []
    for i, (line, a) in enumerate(rows):
        sha = hashlib.sha256(line).hexdigest()
        if sha in done:
            continue
        load = sum(1 for _, b in rows[:i] if b.get("class") == a.get("class") and a.get("t_alert") and b.get("t_alert") and a["t_alert"] - DAY <= b["t_alert"] <= a["t_alert"])
        rec = record.build(a, sha, now(), load_24h=load)
        chain.append(alerts_path, rec); new.append(rec)
        for kind, status in notify.send(rec, env):
            print(f"notify {kind}: {status}", flush=True)
    return new


def verify(out, engine_db=None):
    alerts_path, evals_path = paths(out)
    report = {}
    for name, p in (("alerts", alerts_path), ("evaluations", evals_path)):
        n, head, errors = chain.verify(p); report[name] = {"lines": n, "head": head, "errors": errors}
    if engine_db:
        engine = {hashlib.sha256(l).hexdigest() for l, _ in chain.read(engine_db + ".alerts.jsonl")}
        missing = [o["id"] for _, o in chain.read(alerts_path) if o.get("engine_line_sha256") not in engine]
        report["records_without_engine_line"] = missing
    return report


def run_evaluate(out, get_json, now=time.time, fee=0.0):
    alerts_path, evals_path = paths(out)
    final = {o["alert"] for _, o in chain.read(evals_path) if o.get("status") == "FINAL"}
    written = 0
    for _, rec in chain.read(alerts_path):
        if rec["id"] in final:
            continue
        try:
            e = evaluate.evaluate(rec, get_json, now(), fee)
        except Exception as err:                  # a source that fails leaves the alert for the next run
            print(f"{rec['id']}: {type(err).__name__} {str(err)[:120]}", flush=True); continue
        if e:
            chain.append(evals_path, e); written += 1
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
            new = seal(a.engine_db, a.out)
            if new:
                print(time.strftime("%H:%M:%S"), f"{len(new)} sealed:", ", ".join(f"{r['risk']['class']} {r['id']}" for r in new), flush=True)
            if end and time.time() >= end:
                return 0
            time.sleep(a.interval)
    elif a.cmd == "verify":
        r = verify(a.out, a.engine_db); print(json.dumps(r, indent=1))
        return 1 if r["alerts"]["errors"] or r["evaluations"]["errors"] or r.get("records_without_engine_line") else 0
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
        print(json.dumps({"lines": n, "head_sha256": head, "intact": not errors, "utc": record.utc(time.time())}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
