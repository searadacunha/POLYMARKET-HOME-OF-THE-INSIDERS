"""For accounts classified NO-before-YES: was the NO inventory sold before the first YES buy (liquidation + reversal)
or still held (both sides open)? Censored band: pre-band inventory is unknown, so 'net' is band-relative."""
import sys, json, csv
from collections import defaultdict, Counter
pop = {r["proxy"].lower(): r["in_g38"] == "True" for r in csv.DictReader(open(sys.argv[1]))}
rows = defaultdict(list)
for line in sys.stdin:
    if line.strip():
        t = json.loads(line); w = t["proxy_wallet"].lower()
        if w in pop: rows[w].append((int(t["timestamp"]), t["side"], t["outcome"], float(t["size"])))
res = {"cohort": Counter(), "other": Counter()}
for w, rs in rows.items():
    fy = min((ts for ts, s, o, _ in rs if s == "BUY" and o == "Yes"), default=None)
    fn = min((ts for ts, s, o, _ in rs if s == "BUY" and o == "No"), default=None)
    if fy is None or fn is None or not fn < fy: continue
    before = [r for r in rs if r[0] < fy]
    no_bought = sum(z for ts, s, o, z in before if s == "BUY" and o == "No")
    no_sold = sum(z for ts, s, o, z in before if s == "SELL" and o == "No")
    g = "cohort" if pop[w] else "other"
    if no_sold == 0: k = "no_NO_sell_before_first_YES_buy (NO still held)"
    elif no_sold >= 0.95 * no_bought: k = "NO sold >=95% before first YES buy (liquidation then YES)"
    else: k = "NO partly sold before first YES buy"
    res[g][k] += 1
    res[g]["n"] += 1
print(json.dumps({g: dict(c) for g, c in res.items()}, indent=1))
