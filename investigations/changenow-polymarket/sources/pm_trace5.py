#!/usr/bin/env python3
import json, os, urllib.request, urllib.parse
from collections import Counter
from proxy_resolver import resolve
cfg = {l.split('=',1)[0].strip(): l.split('=',1)[1].strip()
       for l in open(os.path.expanduser('~/Downloads/.env')) if '=' in l and not l.startswith('#')}
KEY=cfg['ETHERSCAN_API_KEY']; UA={"User-Agent":"Mozilla/5.0","Accept":"application/json"}
def http(u): return json.loads(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=25).read())
def es(p):
    p=dict(p);p['chainid']=137;p['apikey']=KEY
    return json.loads(urllib.request.urlopen("https://api.etherscan.io/v2/api?"+urllib.parse.urlencode(p),timeout=40).read())
def code(a):
    r=es({'module':'proxy','action':'eth_getCode','address':a,'tag':'latest'}); c=r.get('result',''); return isinstance(c,str) and len(c)>2

d=json.load(open("f2020_recipients.json"))
# top recipients by total_usd
top=sorted(d.values(), key=lambda x:-x['total_usd'])[:40]
picked=[]
for r in top:
    o=r['wallet']; px=resolve(o)
    if code(px): picked.append((o,px,r['total_usd']))
    if len(picked)>=6: break

for o,px,usd in picked:
    print(f"\n===== recipient {o}  (CN payout ${usd:,.0f})  proxy {px}")
    act=http(f"https://data-api.polymarket.com/activity?user={px}&limit=200")
    if isinstance(act,list):
        print("  activity n:", len(act), "types:", dict(Counter(e.get('type') for e in act)))
    val=http(f"https://data-api.polymarket.com/value?user={px}")
    print("  pm value:", val)
    # on-chain: what does the EOA do with USDC? tokentx of the EOA
    tt=es({'module':'account','action':'tokentx','address':o,'page':1,'offset':50,'sort':'asc'})
    if isinstance(tt,list):
        outs=[t for t in tt if t.get('from','').lower()==o.lower()]
        tos=Counter(t.get('to','').lower() for t in outs)
        print("  EOA USDC OUT to (top):")
        for addr,n in tos.most_common(4):
            iscode=code(addr)
            print(f"     {addr}  x{n}  {'CONTRACT' if iscode else 'eoa'}  == proxy? {addr==px.lower()}")
