"""API capability probes, written before any trade download; every call spends the ledger."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from ledger import appel, compteur, ETUDE

GAMMA = 'https://gamma-api.polymarket.com'
DATA = 'https://data-api.polymarket.com'
LOW, HIGH = 1790176669, 1792768669  # same window as detection_20261030
sortie = {}

# 1. Bare global feed at the production filter: how much time does one page span?
body, recu = appel(DATA + '/v2/trades', dict(limit=1000, taker_only='true', filter_type='CASH', filter_amount=1000), phase='probe')
ts = [r['timestamp'] for r in body['data']]
sortie['global_page'] = dict(rows=len(ts), newest=max(ts), oldest=min(ts), hours=(max(ts) - min(ts)) / 3600,
                             has_more=body['pagination'].get('has_more'), keys=sorted(body['data'][0]))

# 2. Legacy /trades: does it honour start/end on one market? (condition taken from the first stratum row)
import gzip
with gzip.open(ETUDE.parent / 'detection_20261030/data/replay_input.jsonl.gz', 'rt') as f:
    condition = json.loads(f.readline())['condition_id']
start, end = 1792000000, 1792086400
body, recu = appel(DATA + '/trades', dict(market=condition, start=start, end=end, limit=1000, takerOnly='true'), phase='probe')
rows = body if isinstance(body, list) else body.get('data', [])
ts = [int(r['timestamp']) for r in rows]
sortie['legacy_trades'] = dict(rows=len(rows), inside=sum(start <= t <= end for t in ts), outside=sum(not start <= t <= end for t in ts),
                               newest=max(ts) if ts else None, oldest=min(ts) if ts else None,
                               keys=sorted(rows[0]) if rows else [])

# 3. Same market on /v2/trades without bounds, one page, for the row-level comparison of the two sources.
body, recu = appel(DATA + '/v2/trades', dict(condition=condition, limit=1000, taker_only='true'), phase='probe')
ts = [r['timestamp'] for r in body['data']]
sortie['v2_condition'] = dict(rows=len(ts), newest=max(ts), oldest=min(ts), has_more=body['pagination'].get('has_more'),
                              inside=sum(start <= t <= end for t in ts))

# 4. Frame size: Gamma pagination counters for events alive during the window.
window = dict(end_date_min='2026-10-13T00:00:00Z', start_date_max='2026-10-23T15:17:49Z')
for closed in ('true', 'false'):
    body, recu = appel(GAMMA + '/events/pagination', dict(window, limit=1, offset=0, closed=closed), phase='probe')
    sortie['gamma_pagination_closed_' + closed] = body.get('pagination')
    if closed == 'true':
        e = body['data'][0]
        sortie['gamma_event_keys'] = sorted(e)
        sortie['gamma_market_keys'] = sorted(e['markets'][0]) if e.get('markets') else []
sortie['requests_used'] = compteur()
(ETUDE / 'data/api_probe.json').write_text(json.dumps(sortie, indent=1, sort_keys=True))
print(json.dumps(sortie, indent=0)[:3500])
