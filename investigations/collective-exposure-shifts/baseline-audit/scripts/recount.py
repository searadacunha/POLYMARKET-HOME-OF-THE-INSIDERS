"""Independent streaming recount of the Feb-28 NO-before-YES contrast.
Reads the tape on stdin line by line; CSV path as argv[1]. Never reads feb28_noyes_descriptive.json counts."""
import sys, json, csv, hashlib
from datetime import datetime, timezone
from collections import Counter

csv_path = sys.argv[1]
pop = {}
with open(csv_path, newline="") as f:
    for r in csv.DictReader(f):
        pop[r["proxy"].lower()] = (r["createdAt"], r["in_g38"] == "True")

first = {}  # wallet -> {"Yes": ts, "No": ts} earliest BUY
tape_wallets = set(); n = 0; ts_min = ts_max = None; sides = Counter(); outs = Counter(); h = hashlib.sha256()
for line in sys.stdin.buffer:
    h.update(line)
    if not line.strip(): continue
    t = json.loads(line); n += 1
    w = t["proxy_wallet"].lower(); ts = int(t["timestamp"])
    tape_wallets.add(w); sides[t["side"]] += 1; outs[t["outcome"]] += 1
    ts_min = ts if ts_min is None else min(ts_min, ts); ts_max = ts if ts_max is None else max(ts_max, ts)
    if t["side"] == "BUY":
        d = first.setdefault(w, {})
        o = t["outcome"]; assert o in ("Yes", "No"), o
        if o not in d or ts < d[o]: d[o] = ts

def cls(w):
    d = first.get(w, {})
    y, no = d.get("Yes"), d.get("No")
    if y is None and no is None: return "no_buy"
    if y is None: return "no_buy_only"
    if no is None: return "yes_buy_only"
    if no < y: return "no_buy_before_yes_buy"
    if y < no: return "yes_buy_before_no_buy"
    return "same_second"  # tie: not 'strictly before' either way

days = {"2026-02-22", "2026-02-23", "2026-02-24", "2026-02-25"}
bad_days = [w for w, (c, _) in pop.items() if c[:10] not in days]
in_tape = [w for w in pop if w in tape_wallets]
groups = {"cohort": Counter(), "other": Counter()}
for w in in_tape:
    groups["cohort" if pop[w][1] else "other"][cls(w)] += 1
iso = lambda s: datetime.fromtimestamp(s, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
out = {
    "tape_sha256": h.hexdigest(), "tape_rows": n, "tape_band_utc": [iso(ts_min), iso(ts_max)],
    "tape_distinct_wallets": len(tape_wallets), "sides": dict(sides), "outcomes": dict(outs),
    "csv_rows": len(pop), "csv_in_g38": sum(g for _, g in pop.values()), "csv_createdAt_outside_22_25": len(bad_days),
    "population_in_tape": len(in_tape), "tape_wallets_without_profile_row": len(tape_wallets - set(pop)),
    "cohort_n": sum(groups["cohort"].values()), "other_n": sum(groups["other"].values()),
    "cohort": dict(groups["cohort"]), "other": dict(groups["other"]),
}
print(json.dumps(out, indent=1))
c, o = out["cohort"], out["other"]
assert c.get("no_buy_before_yes_buy") == 20 and out["cohort_n"] == 36, "cohort mismatch"
assert o.get("no_buy_before_yes_buy") == 16 and out["other_n"] == 733, "other mismatch"
print("SELF-CHECK OK: 20/36 vs 16/733 reproduced independently")
