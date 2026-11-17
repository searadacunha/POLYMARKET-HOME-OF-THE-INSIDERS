"""Resolve profile names to proxy wallets by exact, case-insensitive match in archived Gamma public-search answers.
Writes data/resolved_names.csv: name, status (RESOLVED / AMBIGUOUS / NOT_FOUND), proxy, pseudonym, n_exact, n_returned."""
import csv, json, os, sys
from pathlib import Path
RAW = Path(os.environ.get("XLEADS_RAW", Path.home() / "Projects/Polymarket-x-leads-raw-20261106/raw"))
names = [l.split("\t")[0] for l in Path(sys.argv[1]).read_text().splitlines() if l and not l.startswith("#")] + sys.argv[3:]
out = []
for n in names:
    d = json.loads((RAW / "search" / f"{n}.json").read_bytes())
    profs = d.get("profiles") or []
    ex = [p for p in profs if (p.get("name") or "").lower() == n.lower()]
    st = "RESOLVED" if len(ex) == 1 else ("AMBIGUOUS" if ex else "NOT_FOUND")
    if st == "RESOLVED" and len(profs) >= 20:  # answer hit the page limit: other exact homonyms may be hidden
        st = "AMBIGUOUS_TRUNCATED"
    out.append({"name": n, "status": st, "proxy": ex[0]["proxyWallet"].lower() if st == "RESOLVED" else "",
                "pseudonym": ex[0].get("pseudonym", "") if len(ex) == 1 else "", "n_exact": len(ex), "n_returned": len(profs)})
Path(sys.argv[2]).parent.mkdir(parents=True, exist_ok=True)
with open(sys.argv[2], "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
from collections import Counter
print(Counter(r["status"] for r in out))
for r in out:
    if r["status"] != "RESOLVED": print(r)
