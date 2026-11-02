#!/usr/bin/env python3
import json, os, random, urllib.request, urllib.parse
from collections import Counter
from proxy_resolver import resolve
cfg={l.split('=',1)[0].strip():l.split('=',1)[1].strip() for l in open(os.path.expanduser('~/Downloads/.env')) if '=' in l and not l.startswith('#')}
KEY=cfg['ETHERSCAN_API_KEY']; UA={"User-Agent":"Mozilla/5.0","Accept":"application/json"}
def http(u): return json.loads(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=25).read())
def es(p):
    p=dict(p);p['chainid']=137;p['apikey']=KEY
    return json.loads(urllib.request.urlopen("https://api.etherscan.io/v2/api?"+urllib.parse.urlencode(p),timeout=40).read())
def code(a):
    r=es({'module':'proxy','action':'eth_getCode','address':a,'tag':'latest'});c=r.get('result','');return isinstance(c,str) and len(c)>2

d=json.load(open("f2020_recipients.json")); owners=list(d.keys())
random.seed(1); sample=random.sample(owners,120)
# find first with code
target=None
for o in sample:
    px=resolve(o)
    if code(px): target=(o,px); break
o,px=target
print("recipient EOA:",o,"CN$=",d[o]['total_usd'])
print("resolved proxy:",px,"has_code=",code(px))
print("\n-- data-api on proxy --")
for ep in ["activity","positions?sizeThreshold=0","value","trades"]:
    sep='&' if '?' in ep else '?'
    r=http(f"https://data-api.polymarket.com/{ep}{sep}user={px}&limit=5" if 'limit' not in ep else f"https://data-api.polymarket.com/{ep}")
    print(f"  {ep.split('?')[0]}:", (len(r) if isinstance(r,list) else r) if not isinstance(r,list) or len(r)==0 else json.dumps(r[0])[:200])
print("\n-- proxy on-chain: who deployed it, what impl --")
cc=es({'module':'contract','action':'getcontractcreation','contractaddresses':px})
print("creation:",json.dumps(cc.get('result'))[:300])
print("\n-- proxy USDC transfers (in/out) --")
tt=es({'module':'account','action':'tokentx','address':px,'page':1,'offset':30,'sort':'asc'})
if isinstance(tt,list):
    print("n token transfers:",len(tt))
    for t in tt[:12]:
        d_=('IN ' if t['to'].lower()==px.lower() else 'OUT')
        print(f"   {d_} {float(t['value'])/10**int(t['tokenDecimal']):>12,.2f} {t['tokenSymbol']:6} {'from' if d_=='IN ' else 'to'} {(t['from'] if d_=='IN ' else t['to'])}")
else:
    print("tokentx:",tt)
print("\n-- EOA on-chain: where does its USDC go? --")
te=es({'module':'account','action':'tokentx','address':o,'page':1,'offset':40,'sort':'asc'})
if isinstance(te,list):
    outs=[t for t in te if t['from'].lower()==o.lower()]
    c=Counter((t['to'].lower()) for t in outs)
    for a,n in c.most_common(6):
        print(f"   OUT to {a} x{n} contract={code(a)} ==resolvedproxy? {a==px.lower()}")
