"""Receipts of every DEPOSIT and WITHDRAWAL of the analysed set S (PLAN_CONTROLS.md cap: 4,000 receipts)."""
import json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import collect  # noqa: E402

pop = json.loads((HERE.parent / "data" / "population.json").read_text())
ctrl = sorted(set(pop["controls"]) | {r["wallet"] for r in pop["population"] if r["role"] == "inca"})
hashes = set()
for w in ctrl:
    d = collect.RAW / "polymarket_dw" / w  # amendment A1
    if not (d / "DONE.json").exists():
        raise SystemExit(f"{w}: activity not complete")
    for p in sorted(d.glob("p*.json")):
        if not p.name.endswith(".meta.json"):
            hashes |= {r["transaction_hash"] for r in json.loads(p.read_text())["data"] if r["type"] in ("DEPOSIT", "WITHDRAWAL")}
print("control receipts", len(hashes))
if len(hashes) > 4000:
    raise SystemExit("cap of 4,000 receipts exceeded: stop and report (PLAN_CONTROLS.md)")
for h in sorted(hashes):
    collect.rcpt(h.lower())
print("done", json.dumps(collect.STATS))
