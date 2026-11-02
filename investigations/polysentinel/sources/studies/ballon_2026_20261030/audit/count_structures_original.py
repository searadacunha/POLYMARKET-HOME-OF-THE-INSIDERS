import collections
import gzip
import hashlib
import json
from pathlib import Path
from statistics import median

study = Path('/Users/benjamindacunha/Projects/PolySentinel/studies/ballon_2026_20261030')
lock = json.loads((study / 'PROTOCOL.lock').read_text())
name = 'data/trades_minimal.jsonl.gz'
source = study / name
assert hashlib.sha256(source.read_bytes()).hexdigest() == lock['fichiers'][name]
counts = {key: collections.Counter() for key in ('wallet', 'event_id', 'market_id', 'transaction_hash', 'id')}
rows = 0
with gzip.open(source, 'rt') as stream:
    for line in stream:
        row = json.loads(line)
        rows += 1
        for key, counter in counts.items():
            value = row[key]
            assert value is not None and value != ''
            counter[str(value).lower() if key == 'wallet' else str(value)] += 1
assert rows == sum(counts['wallet'].values())
output = {'scope': 'entire frozen acquisition, no cutoff/outcome/amount/label read into aggregates', 'rows': rows}
for key, counter in counts.items():
    sizes = list(counter.values())
    output[key] = {'unique': len(counter), 'min_rows': min(sizes), 'median_rows': median(sizes), 'max_rows': max(sizes), 'largest_cluster_fraction': max(sizes) / rows}
output['event_cluster_sizes_descending'] = sorted(counts['event_id'].values(), reverse=True)
output['row_id_duplicates'] = rows - len(counts['id'])
print(json.dumps(output, indent=2))
