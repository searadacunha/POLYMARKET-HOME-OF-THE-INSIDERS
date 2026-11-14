"""feat_05: the DISCOVERY set. Every slug and condition id of the cases already documented in the repository
(two case registries built from repository files on 13 November 2026). No outcome is read."""
import hashlib, json, os

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES = ("case_registry_maduro_iran.json", "case_registry_ballon_c1c7.json")


def main():
    slugs, conds, cases, shas = set(), set(), [], {}
    for name in SOURCES:
        raw = open(os.path.join(ETUDE, "data", name), "rb").read(); shas[name] = hashlib.sha256(raw).hexdigest()
        j = json.loads(raw)
        for c in (j if isinstance(j, list) else j.get("cases") or list(j.values())):
            if not isinstance(c, dict): continue
            cases.append(c.get("case_id"))
            slugs.update(s for s in (c.get("event_slugs") or []) if isinstance(s, str))
            conds.update(x.lower() for x in (c.get("condition_ids") or []) if isinstance(x, str))
    if "nobel-peace-prize-winner-2025" not in slugs: raise SystemExit("the Nobel 2025 event must be in the discovery set")
    out = {"cases": cases, "event_slugs": sorted(slugs), "condition_ids": sorted(conds), "source_sha256": shas}
    json.dump(out, open(os.path.join(ETUDE, "derived", "discovery_events.json"), "w"), indent=1)
    print("cases", len(cases), "slugs", len(slugs), "conditions", len(conds))


if __name__ == "__main__":
    main()
