#!/usr/bin/env python3
"""Sample test: resolve f2020 recipients -> legacy proxy, probe data-api.
Measures legacy-shape coverage + PM hit rate. Loud on errors."""
import json, os, random, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor
from proxy_resolver import resolve

cfg = {l.split('=',1)[0].strip(): l.split('=',1)[1].strip()
       for l in open(os.path.expanduser('~/Downloads/.env')) if '=' in l and not l.startswith('#')}
KEY = cfg['ETHERSCAN_API_KEY']
UA = {"User-Agent":"Mozilla/5.0","Accept":"application/json"}

def http(u, tries=3):
    last=None
    for a in range(tries):
        try:
            return json.loads(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=25).read())
        except Exception as e:
            last=e
    raise RuntimeError(f"HTTP fail {u[:80]}: {last}")

def has_code(addr):
    u="https://api.etherscan.io/v2/api?"+urllib.parse.urlencode(
        {'chainid':137,'module':'proxy','action':'eth_getCode','address':addr,'tag':'latest','apikey':KEY})
    r=http(u); c=r.get('result',''); return isinstance(c,str) and len(c)>2

def pm_value(addr):
    v=http(f"https://data-api.polymarket.com/value?user={addr}")
    if isinstance(v,list) and v: return float(v[0].get('value') or 0)
    return 0.0

def pm_positions(addr):
    p=http(f"https://data-api.polymarket.com/positions?user={addr}&sizeThreshold=1")
    return p if isinstance(p,list) else []

d=json.load(open("f2020_recipients.json"))
owners=list(d.keys())
random.seed(1); sample=random.sample(owners, 120)

def check(o):
    px=resolve(o)
    try:
        code=has_code(px)
        val=pm_value(px) if code else 0.0
        pos=pm_positions(px) if code else []
        maxpos=max((float(x.get('currentValue') or 0) for x in pos), default=0.0)
        return {"owner":o,"proxy":px,"code":code,"pm_value":round(val,2),
                "n_pos":len(pos),"max_pos_val":round(maxpos,2)}
    except Exception as e:
        return {"owner":o,"proxy":px,"error":str(e)}

res=[]
with ThreadPoolExecutor(max_workers=8) as ex:
    for r in ex.map(check, sample): res.append(r)

errs=[r for r in res if 'error' in r]
ok=[r for r in res if 'error' not in r]
code_yes=[r for r in ok if r['code']]
pm_hit=[r for r in ok if r.get('pm_value',0)>0 or r.get('n_pos',0)>0]
print(f"sample={len(sample)} errors={len(errs)}")
print(f"legacy-addr has code on-chain: {len(code_yes)}/{len(ok)}")
print(f"PM value>0 or positions>0     : {len(pm_hit)}/{len(ok)}")
pm_hit.sort(key=lambda r:-r.get('pm_value',0))
print("top hits by pm_value:")
for r in pm_hit[:15]:
    print(f"  {r['owner'][:10]} -> {r['proxy'][:12]}  val=${r['pm_value']:,}  npos={r['n_pos']}  maxpos=${r['max_pos_val']:,}")
if errs: print("SAMPLE ERROR:", errs[0])
