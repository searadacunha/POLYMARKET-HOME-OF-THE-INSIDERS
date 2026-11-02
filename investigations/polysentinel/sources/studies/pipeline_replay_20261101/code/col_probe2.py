"""Second probe: the first legacy test was inconclusive (0 rows on both sides, wrong market)."""
import collections, gzip, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from ledger import appel, compteur, ETUDE
counts = collections.Counter()
rows = []
with gzip.open(ETUDE.parent / 'ballon_2026_20261030/data/trades_minimal.jsonl.gz', 'rt') as f:
    for line in f:
        r = json.loads(line)
        counts[r['condition_id']] += 1
        rows.append((r['condition_id'], r['timestamp'], r['id']))
condition = counts.most_common(1)[0][0]
mine = sorted(t for c, t, _ in rows if c == condition)
start, end = mine[len(mine) // 3], mine[2 * len(mine) // 3]
expected = sum(start <= t <= end for t in mine)
body, recu = appel('https://data-api.polymarket.com/trades', dict(market=condition, start=start, end=end, limit=1000, takerOnly='true'), phase='probe')
got = body if isinstance(body, list) else body.get('data', [])
ts = [int(r['timestamp']) for r in got]
out = dict(local_rows_market=len(mine), expected_in_window=expected, returned=len(got),
           inside=sum(start <= t <= end for t in ts), outside=sum(not start <= t <= end for t in ts),
           requests_used=compteur())
(ETUDE / 'data/api_probe2.json').write_text(json.dumps(out, indent=1))
print(out)
