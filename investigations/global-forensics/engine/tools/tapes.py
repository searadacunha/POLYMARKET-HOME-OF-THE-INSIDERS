"""Pull the taker tape of each catalogue market for its window, and resolve the cited usernames to addresses from the rows themselves. Profile fields stay out of the tape files.

Usage: tapes.py <markets.json> [id ...]. Writes markets/<id>/tape.jsonl.gz and cited.json under the data root.
"""
import gzip
import json
import sys
from datetime import datetime
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gf import env, pm
from gf.net import Net

env.redirect_temp()
ROOT = env.data_root() / 'markets'
SECONDS = lambda s: int(datetime.fromisoformat(s.replace('Z', '+00:00')).timestamp())
net = Net()
markets = json.loads(Path(sys.argv[1]).read_text())
only = set(sys.argv[2:])
for m in markets:
    if only and m['id'] not in only:
        continue
    out = ROOT / m['id']
    out.mkdir(parents=True, exist_ok=True)
    start, event = SECONDS(m['window_start_utc']), SECONDS(m['event_utc'])
    seen, names, coverage = set(), {}, None
    with gzip.open(out / 'tape.tmp.gz', 'wt') as f:
        for r in pm.trades(net, m['condition'], start, event + 6 * 3600, taker_only=True):
            if '_coverage' in r:
                coverage = r['_coverage']
                continue
            key = (r.get('transaction_hash'), r.get('proxy_wallet'), r.get('token_id'), r.get('size'), r.get('price'), r.get('side'))
            if key in seen:
                continue
            seen.add(key)
            names.setdefault(r['proxy_wallet'].lower(), {r.get('name'), r.get('pseudonym')})
            f.write(json.dumps({k: r.get(k) for k in pm.TRADE_KEEP}) + '\n')
    (out / 'tape.tmp.gz').replace(out / 'tape.jsonl.gz')
    cited = {}
    for c in m.get('cited_names', []):
        cited[c] = sorted(w for w, n in names.items() if c in n or any(c.lower() == str(x).lower() for x in n))
    for a in m.get('cited_addresses', []):
        cited[a] = [a.lower()] if a.lower() in names else []
    (out / 'cited.json').write_text(json.dumps(dict(market=m['id'], rows=len(seen), wallets=len(names), cited=cited, read_at=int(__import__('time').time()), window=[start, event + 6 * 3600], coverage=coverage), indent=1))
    print(m['id'], 'rows', len(seen), 'wallets', len(names), 'cited', cited, flush=True)
print('calls', net.calls, 'hits', net.hits)
