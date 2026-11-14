"""Recompute the published results of this note from the files of the repository alone. No network.

    python3 -I research_notes/realtime-intelligence-2026-11-14/verify.py

Checks
  1. the archived study files have the sha256 recorded in the freeze (PROTOCOL.lock);
  2. the exact test of every class and population is recomputed from data/study_export/alerts.jsonl;
  3. the difference to the control entries is recomputed from the base and class cells;
  4. every verdict is recomputed from those results and from the registry count of comparisons;
  5. the code the live engine shares with the study is the frozen code, byte for byte;
  6. SIGNALS_REGISTER.md is the rendering of its data file, and the tables of RESULTS.md of the study outputs;
  7. every full address or transaction hash written in the pages of this note exists in its data files.
The analytic table itself holds wallet addresses and is not published: its sha256 is in the lock."""
import hashlib, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
STUDY = os.path.join(HERE, "study")
sys.path.insert(0, os.path.join(STUDY, "code"))
import stats, tests_lib as T          # noqa: E402  (the frozen code)

ok, bad = 0, []


def check(name, cond, detail=""):
    global ok
    if cond:
        ok += 1
    else:
        bad.append(f"{name} {detail}")


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def rows(path):
    with open(path) as f:
        return [json.loads(l) for l in f if l.strip()]


def close(a, b, tol=1e-9):
    return (a is None and b is None) or (a is not None and b is not None and abs(a - b) <= tol * max(1.0, abs(a), abs(b)))


if sys.argv[1:] == ["--write-manifest"]:      # the data files and scripts of this note, written once they are final
    files = {}
    for sub in ("data", "scripts"):
        for root, _, names in os.walk(os.path.join(HERE, sub)):
            for name in sorted(names):
                rel = os.path.relpath(os.path.join(root, name), HERE)
                if rel != os.path.join("data", "MANIFEST.json") and "__pycache__" not in rel:
                    files[rel] = sha(os.path.join(HERE, rel))
    json.dump({"what": "sha256 of every data file and script of this note, checked by verify.py", "files": dict(sorted(files.items()))},
              open(os.path.join(HERE, "data", "MANIFEST.json"), "w"), indent=1)
    print(f"manifest written, {len(files)} files"); sys.exit(0)

# 1. freeze
lock = json.load(open(os.path.join(STUDY, "PROTOCOL.lock")))
published = missing = 0
for rel, digest in lock["fichiers"].items():
    path = os.path.join(STUDY, rel)
    if os.path.exists(path):
        published += 1; check("frozen file " + rel, sha(path) == digest, "differs from the freeze")
    else:
        missing += 1
check("frozen files published", published >= 20, f"only {published}")
for add in lock.get("ajouts", []):          # files added after the freeze: listed by name, their sha256 is in "fichiers"
    for rel in add.get("fichiers") or []:
        check("added file " + rel, rel in lock["fichiers"] and os.path.exists(os.path.join(STUDY, rel)), "not in the lock or not published")

# 2 and 3. tests
res = json.load(open(os.path.join(STUDY, "derived", "results_tests.json")))
alerts = rows(os.path.join(HERE, "data", "study_export", "alerts.jsonl"))
base = rows(os.path.join(HERE, "data", "study_export", "base_cells.jsonl"))
cells = rows(os.path.join(HERE, "data", "study_export", "class_cells.jsonl"))
part = {"validation_info": "primary", "validation_public_process": "negative_control", "discovery_info": "discovery"}
by = {}
for a in alerts:
    by.setdefault((a["population"], a["class"]), []).append(a)
for pop, key in part.items():
    for cls, r in res[key].items():
        mine = by.get((pop, cls), [])
        t1 = stats.t1([{"event": a["event"], "t": a["t"], "price": a["price"], "win": a["win"]} for a in mine])
        for f in ("n", "wins"):
            check(f"T1 {pop} {cls} {f}", t1[f] == r["t1"][f], f"{t1[f]} against {r['t1'][f]}")
        for f in ("excess", "p", "expected"):
            check(f"T1 {pop} {cls} {f}", close(t1[f], r["t1"][f], 1e-6), f"{t1[f]} against {r['t1'][f]}")
taken = {}
# class cells (alerts and refused alerts, ana_95) and excluded cells (entries kept out of the controls, ana_98, amendment 001)
for c in cells + rows(os.path.join(HERE, "data", "study_export", "excluded_cells.jsonl")):
    k = (c["class"], c["event"], c["price_band"], c["horizon_band"]); n0, t0 = taken.get(k, (0, 0.0))
    taken[k] = (n0 + c["n"], t0 + c["sum_excess"])
for cls, r in res["primary"].items():
    if not r.get("t2") or r["t2"].get("diff") is None:
        continue
    ev = {}
    for a in by.get(("validation_info", cls), []):
        ev.setdefault(a["event"], [None, {}])[0] = (stats.stratum(a["price"], a["hours_to_end"]), a["win"] - a["price"])
    for b in base:
        n, tot = taken.get((cls, b["event"], b["price_band"], b["horizon_band"]), (0, 0.0))
        if b["n"] - n > 0:
            ev.setdefault(b["event"], [None, {}])[1][(b["price_band"], b["horizon_band"])] = [b["n"] - n, b["sum_excess"] - tot]
    d = stats._diff(list(ev.values()))
    check(f"T2 difference {cls}", close(d, r["t2"]["diff"], 1e-5), f"{d} against {r['t2']['diff']}")

# 4. verdicts
verdict = json.load(open(os.path.join(STUDY, "derived", "verdict.json")))
n_cmp = sum(int(x.get("n_comparaisons") or 1) for x in rows(os.path.join(STUDY, "registre", "tests.jsonl")) if x.get("donnees") == "reelles")
check("comparisons on real data", n_cmp == verdict["comparisons_on_real_data"], f"{n_cmp} against {verdict['comparisons_on_real_data']}")
alpha = 0.05 / n_cmp
for cls, r in res["primary"].items():
    nc = (res["negative_control"].get(cls) or {}).get("t1", {}).get("p")
    check(f"verdict {cls}", T.verdict(r, alpha, nc_p=nc) == verdict["classes"][cls]["verdict"], f"{T.verdict(r, alpha, nc_p=nc)} against {verdict['classes'][cls]['verdict']}")

# 5. shared code
for name in ("asof.py", "chainfund.py", "models.py"):
    check("engine code " + name, sha(os.path.join(REPO, "monitoring", "phi_engine", name)) == sha(os.path.join(STUDY, "code", name)), "differs from the frozen code")

# 6. register
r = subprocess.run([sys.executable, "-I", os.path.join(HERE, "scripts", "render_signals_register.py"), "--check"], capture_output=True, text=True)
check("signals register", r.returncode == 0, r.stdout.strip())

# 6b. the tables of RESULTS.md are the rendering of the study outputs
r = subprocess.run([sys.executable, "-I", os.path.join(HERE, "scripts", "render_results.py"), "--check"], capture_output=True, text=True)
check("RESULTS.md tables rendered from study/derived", r.returncode == 0, r.stderr[-300:])

# 7. no invented address or hash
data_text = ""
for root, _, files in os.walk(os.path.join(HERE, "data")):
    for f in files:
        if f.endswith((".json", ".jsonl", ".csv")):
            with open(os.path.join(root, f)) as fh:
                data_text += fh.read().lower()
known = set(re.findall(r"0x[0-9a-f]{64}|0x[0-9a-f]{40}", data_text))
for page in sorted(f for f in os.listdir(HERE) if f.endswith(".md")):
    with open(os.path.join(HERE, page)) as fh:
        for ref in set(re.findall(r"0x[0-9a-fA-F]{64}|0x[0-9a-fA-F]{40}(?![0-9a-fA-F])", fh.read())):
            check(f"reference in {page}", ref.lower() in known, f"{ref} is in no data file")

# 8. amendment 002: the lock of the study folder after it follows the published lock, and the export of every transfer
#    agrees with the first-transfer export and with the receipts read on chain
m2 = json.load(open(os.path.join(HERE, "data", "amendment_002_manifest.json")))
check("amendment 002 follows the published lock", m2["addition"]["lock_sha_avant"] == m2["published_study_lock_sha256"] == sha(os.path.join(STUDY, "PROTOCOL.lock")))
check("amendment 002 keeps every earlier frozen hash", m2["frozen_hashes_before_002_unchanged"] == len(lock["fichiers"]))
for rel, digest in list(m2["files"].items()) + list(m2["published_outputs"].items()):
    check("amendment 002 file " + rel, sha(os.path.join(HERE, rel)) == digest, "differs from its manifest")
import csv  # noqa: E402
first = list(csv.DictReader(open(os.path.join(HERE, "data", "study_export", "financial_links.csv"))))
every = list(csv.DictReader(open(os.path.join(HERE, "data", "study_export", "financial_links_transfers.csv"))))
for r in first:
    mine = [x for x in every if (x["wallet"], x["deposit_tx"], x["entry_utc"]) == (r["wallet"], r["deposit_tx"], r["entry_utc"])]
    top = [x for x in mine if x["transfer_rank"] == "1"]
    check(f"first transfer of {r['wallet'][:10]} {r['entry_utc']}", len(top) == 1 and (top[0]["funding_tx"], float(top[0]["funding_usd"])) == (r["funding_tx"], float(r["funding_usd"])))
distinct = {}
for x in every:
    distinct.setdefault(x["wallet"], {})[x["funding_tx"]] = float(x["funding_usd"])
onchain = json.load(open(os.path.join(HERE, "data", "links_transfers.json")))
for l in onchain["links"]:
    check(f"every transfer to {l['wallet'][:10]}", close(sum(distinct.get(l["wallet"], {}).values()), l["usd"], 1e-9), f"{distinct.get(l['wallet'])} against {l['usd']}")
v2 = json.load(open(os.path.join(HERE, "data", "links_transfers_v2_recheck.json")))
check("receipts of amendment 002", v2["by_receipt"]["confirmed"] == v2["distinct_transfers"] and v2["distinct_transfers"] > 0, str(v2["by_receipt"]))

# 9. the audit after the results and the independent recomputation
for args in (["audit_after_results.py", "offline", "--check"], ["audit_after_results.py", "render", "--check"], ["independent_recompute.py", "--check"]):
    r = subprocess.run([sys.executable, "-I", os.path.join(HERE, "scripts", args[0])] + args[1:], capture_output=True, text=True)
    check(" ".join(args), r.returncode == 0, (r.stdout + r.stderr)[-300:])

# 10. manifest of the published files of this note
man = json.load(open(os.path.join(HERE, "data", "MANIFEST.json")))
for rel, digest in man["files"].items():
    check("manifest " + rel, os.path.exists(os.path.join(HERE, rel)) and sha(os.path.join(HERE, rel)) == digest, "missing or changed")

print(f"{ok} checks passed, {len(bad)} failed" + (f", {missing} frozen files not published (the analytic table)" if missing else ""))
for b in bad:
    print("FAILED", b)
sys.exit(1 if bad else 0)
