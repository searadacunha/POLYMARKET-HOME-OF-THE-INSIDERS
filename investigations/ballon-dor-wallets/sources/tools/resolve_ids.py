"""Try to resolve the unresolved public labels from public endpoints only: profile search and current top holders of each market.
A name returned today documents the current alias, not its continuity on the betting dates."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import net

CAT = Path.home() / 'Projects/PolySentinel/studies/ballon_2026_20261030/data/catalog_refreshed.json'
TARGETS = ('cookedrice', 'zoomman17', 'kraben006', '0x86544e4dfde', '0xdd97e6')
MEN = {'48361', '811116', '811117', '1189431', '1105185', '1218178', '1218179', '1225367', '1225368', '1105364', '1105369', '1105379', '1226675', '1226676'}
out = dict(searches={}, holder_hits=[], markets_read=0, holder_rows=0, errors=[])
for q in TARGETS:
    r = net.get('https://gamma-api.polymarket.com/public-search', dict(q=q, search_profiles='true', limit_per_type=10))
    out['searches'][q] = [dict(name=p.get('name'), pseudonym=p.get('pseudonym'), proxy=p.get('proxyWallet')) for p in (r.get('profiles') or [])]
events = json.loads(CAT.read_text())['events']
for item in events:
    e = item['event']
    if str(e['id']) not in MEN:
        continue
    # Winner and rank events hold many long shots: the most traded markets carry the holders the press screenshot could show.
    markets = sorted(e['markets'], key=lambda m: -float(m.get('volumeNum') or m.get('volume') or 0))[:12]
    for m in markets:
        rows = net.get('https://data-api.polymarket.com/holders', dict(market=m['conditionId'], limit=500))
        if not isinstance(rows, list):
            out['errors'].append(dict(market=m['conditionId'], answer=rows))
            continue
        out['markets_read'] += 1
        for token in rows:
            for h in token.get('holders', []):
                out['holder_rows'] += 1
                names = ' '.join(str(h.get(k) or '') for k in ('name', 'pseudonym', 'proxyWallet', 'displayUsernamePublic')).lower()
                for t in TARGETS:
                    if t in names:
                        out['holder_hits'].append(dict(target=t, wallet=h.get('proxyWallet'), name=h.get('name'), pseudonym=h.get('pseudonym'), amount=h.get('amount'), outcome=h.get('outcomeIndex'), event=e['slug'], question=m.get('question')))
Path('evidence/resolve_ids.json').write_text(json.dumps(out, indent=1, ensure_ascii=False))
print(json.dumps(dict(out, holder_hits=out['holder_hits'][:30]), ensure_ascii=False)[:3500], '\ncalls', net.Stats.calls)
