#!/usr/bin/env python3
"""Sample: resolve recipient -> proxy, measure LIFETIME PM betting (TRADE volume,
max single-market cumulative BUY). Loud on errors."""
import json, os, random, urllib.request, urllib.parse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from proxy_resolver import resolve
cfg = {l.split('=',1)[0].strip(): l.split('=',1)[1].strip()
       for l in open(os.path.expanduser('~/Downloads/.env')) if '=' in l and not l.startswith('#')}
KEY=cfg['ETHERSCAN_API_KEY']; UA={"User-Agent":"Mozilla/5.0","Accept":"application/json"}
def http(u,tries=3):
    last=None
    for _ in range(tries):
        try: return json.loads(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=25).read())
        except Exception as e: last=e
    raise RuntimeError(f"HTTP {u[:70]} {last}")
def activity(addr):
    out=[]; off=0
    while off<3000:
        a=http(f"https://data-api.polymarket.com/activity?user={addr}&limit=500&offset={off}")
        if not isinstance(a,list) or not a: break
        out+=a
        if len(a)<500: break
        off+=500
    return out

d=json.load(open("f2020_recipients.json"))
owners=list(d.keys())
random.seed(1); sample=random.sample(owners,120)
def check(o):
    px=resolve(o)
    try:
        act=activity(px)
        tr=[e for e in act if e.get('type')=='TRADE']
        buys=[e for e in tr if e.get('side')=='BUY']
        vol=sum(float(e.get('usdcSize') or 0) for e in tr)
        by=defaultdict(float)
        for e in buys: by[e.get('conditionId')]+=float(e.get('usdcSize') or 0)
        maxmkt=max(by.values(), default=0.0)
        return {"owner":o,"proxy":px,"cn_usd":round(d[o]['total_usd'],2),
                "n_trades":len(tr),"life_vol":round(vol,2),"max_market":round(maxmkt,2)}
    except Exception as e:
        return {"owner":o,"proxy":px,"error":str(e)}
res=[]
with ThreadPoolExecutor(max_workers=8) as ex:
    for r in ex.map(check,sample): res.append(r)
errs=[r for r in res if 'error' in r]; ok=[r for r in res if 'error' not in r]
traders=[r for r in ok if r['n_trades']>0]
print(f"sample={len(sample)} errors={len(errs)}")
print(f"PM traders (>=1 trade): {len(traders)}/{len(ok)}")
print(f"  with life_vol>=$1000 : {len([r for r in traders if r['life_vol']>=1000])}")
print(f"  with max_market>=$1000: {len([r for r in traders if r['max_market']>=1000])}")
traders.sort(key=lambda r:-r['life_vol'])
print("top traders by lifetime volume:")
for r in traders[:15]:
    print(f"  {r['owner'][:10]} CN=${r['cn_usd']:>9,.0f}  trades={r['n_trades']:>4}  vol=${r['life_vol']:>10,.0f}  maxmkt=${r['max_market']:>9,.0f}")
if errs: print("ERR sample:", errs[0])
