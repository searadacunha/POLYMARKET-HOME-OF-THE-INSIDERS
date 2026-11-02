"""Fourth probe: does the legacy global feed honour a deep offset? Size of one page is already known."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from ledger import appel, compteur, ETUDE
out = {}
for offset in (10000, 150000):
    try:
        body, recu = appel('https://data-api.polymarket.com/trades',
                           dict(limit=1000, offset=offset, takerOnly='true', filterType='CASH', filterAmount=1000), phase='probe', tentatives=1)
    except Exception as exc:
        out[offset] = dict(error=str(exc)[:300])
        continue
    got = body if isinstance(body, list) else body.get('data', [])
    ts = [int(r['timestamp']) for r in got]
    out[offset] = dict(returned=len(got), newest=max(ts) if ts else None, oldest=min(ts) if ts else None, bytes=recu['bytes'])
out['requests_used'] = compteur()
(ETUDE / 'data/api_probe4.json').write_text(json.dumps(out, indent=1))
print(json.dumps(out))
