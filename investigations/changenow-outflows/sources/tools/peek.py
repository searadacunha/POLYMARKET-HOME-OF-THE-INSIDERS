"""Offline peek: counterparties of a few consolidation-like addresses, from cached desc-1000 rows, with cached Blockscout tags when any. No network."""
import gzip, hashlib, json, sys, urllib.parse
from collections import Counter
from pathlib import Path
P = Path.home() / 'Projects/PolySentinel-ChangeNOW-proof'
CACHES = [P / 'state/http_cache', Path.home() / 'Projects/PolySentinel-flow-trace/state/http_cache']
tags = json.load(open(P / 'state/p9.json'))
tagmap = {**tags['dep_cp_tags'], **tags['hot3_cp_tags']}
def load(a, action, chain=1):
    u = 'https://api.etherscan.io/v2/api?' + urllib.parse.urlencode(dict(chainid=chain, module='account', action=action, address=a, page=1, offset=1000, sort='desc', startblock=0, endblock=999999999))
    k = hashlib.sha256(u.encode()).hexdigest()
    for c in CACHES:
        f = c / k[:2] / (k + '.json.gz')
        if f.exists():
            return json.load(gzip.open(f, 'rt')).get('result') or []
    return []
for a in sys.argv[1:]:
    for action in ('txlist', 'tokentx'):
        rows = load(a, action)
        ins = Counter(r['from'].lower() for r in rows if (r['to'] or '').lower() == a and int(r['value']) > 0)
        out = Counter((r['to'] or '').lower() for r in rows if r['from'].lower() == a and int(r['value']) > 0)
        print(a[:10], action, len(rows))
        for lab, c in (('IN', ins), ('OUT', out)):
            for x, n in c.most_common(7):
                print('  ', lab, x, n, (tagmap.get(x) or [])[:3])
