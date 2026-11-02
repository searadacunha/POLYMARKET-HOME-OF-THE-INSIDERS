"""Third probe: legacy /trades without a market, at the production filter, with a time window."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from ledger import appel, compteur, ETUDE
start, end = 1792000000, 1792003600  # one hour on 2026-10-14, chosen for size, not for content
out = {}
for limit in (1000, 10000):
    body, recu = appel('https://data-api.polymarket.com/trades',
                       dict(start=start, end=end, limit=limit, takerOnly='true', filterType='CASH', filterAmount=1000), phase='probe')
    got = body if isinstance(body, list) else body.get('data', [])
    ts = [int(r['timestamp']) for r in got]
    nominal = [float(r['size']) * float(r['price']) for r in got]
    out[limit] = dict(returned=len(got), inside=sum(start <= t <= end for t in ts), outside=sum(not start <= t <= end for t in ts),
                      newest=max(ts) if ts else None, oldest=min(ts) if ts else None,
                      below_1000=sum(n < 999.999 for n in nominal), bytes=recu['bytes'],
                      keys=sorted(got[0]) if got else [])
out['requests_used'] = compteur()
(ETUDE / 'data/api_probe3.json').write_text(json.dumps(out, indent=1))
print(json.dumps(out)[:1500])
