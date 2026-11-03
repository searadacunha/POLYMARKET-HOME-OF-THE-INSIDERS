"""Markets that cannot be in the holdout, fixed at the freeze. Usage: col_05_seen.py <out.json>. No outcome is read.

The first study's markets, by condition. The catalogue and the Ballon d'Or family, by condition, by event and by words in the slug, so a sibling on the same world fact leaves too. Other questions of the first study stay when they recur: only rows after 2026-09-15 are scored, so those rows are new data.
"""
import gzip
import json
import sys
from pathlib import Path


UNIVERSE = Path.home() / 'Documents/Crypto/enquete_maduro_iran/donnees/brut_p8_p9/p8/universe.json'
CENSUS = Path.home() / 'Projects/PolySentinel-ballon-dor-2026/derived/census_trades.jsonl.gz'
CATALOG = Path('/Volumes/PHI-Data/global-forensics/wip/catalog/markets.json')


def main(out):
    design = json.loads(UNIVERSE.read_text())
    conditions = {m['conditionId'].lower() for m in design}
    catalog = json.loads(CATALOG.read_text())
    events = set()
    for m in catalog:
        conditions.add(m['condition'].lower())
    family = set()
    with gzip.open(CENSUS, 'rt') as f:
        for line in f:
            r = json.loads(line)
            family.add(r['cond'].lower())
            if r.get('eid'):
                events.add(str(r['eid']))
    conditions |= family
    # slugs of the same world facts differ in wording, so these are searched inside the slug, not matched whole
    patterns = ['ballon-dor', 'khamenei', 'maduro', 'machado', 'nobel-peace', 'fauci', 'biden-pardon', 'strikes?-iran', 'iran-strike', 'iran-ceasefire', 'x-iran-ceasefire', 'us-x-iran', 'venezuela']
    Path(out).write_text(json.dumps(dict(conditions=sorted(conditions), slug_patterns=patterns, event_ids=sorted(events), counts=dict(design=len(design), catalogue=len(catalog), ballon_family=len(family)), note='event ids of the Ballon d Or census'), indent=0))
    print(len(conditions), patterns, len(events))


if __name__ == '__main__':
    main(sys.argv[1])
