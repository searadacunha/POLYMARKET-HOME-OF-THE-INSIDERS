"""Registry step 1: every Blockscout tag whose name carries ChangeNOW, per chain, and its addresses. The tag search ignores its page token (seen in the proof session: 50 tags repeated), so it is queried by name prefix. Writes state/bs_tags.jsonl."""
import json, sys, urllib.parse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import net
BASE = 'https://metadata.services.blockscout.com/api/v1'
OUT = net.ROOT / 'state/bs_tags.jsonl'
CHAINS = (1, 137, 42161, 10, 8453, 56)
PREFIXES = ['changenow'] + [f'changenow{x}' for x in (' ', '-', '_', ':', ' dep', ' 1', ' 2', '_deposit', ': ', ' (', '_deposit_0x0', '_deposit_0x1', '_deposit_0x2', '_deposit_0x3')] + ['change now', 'change-now', 'now wallet', 'nowpayments']
seen = {}
for chain in CHAINS:
    for pre in PREFIXES:
        d = net.get(f'{BASE}/tags:search', dict(chainId=chain, tag_types='name,protocol,generic', name=pre, pageSize=1000, addressLimit=50), pause=.5)
        items = d.get('items') or []
        new = 0
        for it in items:
            t = it.get('tag', it)
            k = (chain, t.get('slug'))
            if k not in seen:
                new += 1
                seen[k] = dict(chain=chain, slug=t.get('slug'), name=t.get('name'), type=t.get('tagType'), meta=t.get('meta'), addresses=[a.lower() if isinstance(a, str) else (a.get('address') or a.get('hash') or '').lower() for a in it.get('addresses') or []])
        print(chain, repr(pre), 'items', len(items), 'new', new, 'error' if d.get('_http_error') else '', flush=True)
for k, v in list(seen.items()):
    if not v['addresses']:
        d = net.get(f'{BASE}/addresses', dict(slug=v['slug'], tagType=v['type'], chainId=k[0], pageSize=100), pause=.5)
        v['addresses'] = [a.lower() for a in d.get('addresses') or []]
        v['more'] = bool((d.get('next_page_params') or {}).get('page_token'))
with OUT.open('w') as f:
    for v in seen.values():
        f.write(json.dumps(v) + '\n')
hit = [v for v in seen.values() if 'change' in (v['name'] or '').lower() or 'now' in (v['slug'] or '').lower()]
print('tags', len(seen), 'changenow-like', len(hit), 'addresses', len({a for v in hit for a in v['addresses']}))
