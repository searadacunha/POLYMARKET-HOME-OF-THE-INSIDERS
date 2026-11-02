#!/usr/bin/env python3
"""Recompute the 198 (EOA-funder de-noised signature set) and list those that bet >=$1000
on a single PM position. Check direct + via relay rout recipients (proxy)."""
import json, os, time, urllib.request, urllib.error, urllib.parse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
OUT=os.path.dirname(os.path.abspath(__file__)); STATE=os.path.join(OUT,"state")
KEY=[l.split('=',1)[1].strip() for l in open(os.path.expanduser('~/Downloads/.env')) if l.startswith('ETHERSCAN_API_KEY=')][0]
ESBASE="https://api.etherscan.io/v2/api"
UA={"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36","Accept":"application/json"}
KNOWN={'0xf70da97812cb96acdf810712aa562db8dfa3dbef','0xb92fe925dc43a0ecde6c8b1a2709c170ec4fff4f','0x4cd00e387622c35bddb9b4c962c136462338bc31','0x555ce236c0220695b68341bc48c68d52210cc35b','0x1205f31718499dbf1fca446663b532ef87481fe1','0x9aa02d4fae7f58b8e8f34c66e756cc734dac7fe4','0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb','0x0000000000000000000000000000000000000000','0x505e71695e9bc45943c58adec1650577bca68fd9','0xeba88149813bec1cccccfdb0dacefaaa5de94cb1'}
def es(p):
    p=dict(p); p['chainid']=1; p['apikey']=KEY
    for a in range(3):
        try: return json.loads(urllib.request.urlopen(ESBASE+'?'+urllib.parse.urlencode(p),timeout=30).read()).get('result')
        except Exception: time.sleep(0.4*(a+1))
    return None
def is_contract(a):
    c=es({'module':'proxy','action':'eth_getCode','address':a,'tag':'latest'})
    return isinstance(c,str) and len(c)>2
def http(u):
    for a in range(3):
        try: return json.loads(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=25).read())
        except urllib.error.HTTPError as e:
            if e.code==429: time.sleep(1.0*(a+1)); continue
            return None
        except Exception: time.sleep(0.4*(a+1))
    return None
def max_position(addr):
    """max cumulative BUY usdcSize on a single conditionId via /activity. Returns (max_usd, market)."""
    best=0.0; bm=None; off=0
    by=defaultdict(float); title={}
    while off<2000:
        a=http(f"https://data-api.polymarket.com/activity?user={addr}&limit=500&offset={off}")
        if not isinstance(a,list) or not a: break
        for e in a:
            if e.get("type")=="TRADE" and e.get("side")=="BUY":
                c=e.get("conditionId");
                if c: by[c]+=float(e.get("usdcSize") or 0); title[c]=e.get("title")
        if len(a)<500: break
        off+=500
    for c,v in by.items():
        if v>best: best=v; bm=title.get(c)
    return best, bm

# recompute 198
rows=[json.loads(l) for l in open(os.path.join(STATE,"sig_phase1.jsonl")) if l.strip()]
f2w=defaultdict(set)
for r in rows:
    if r['capital']=='clean':
        tf=r.get('top_funder')
        if tf and tf not in KNOWN: f2w[tf].add(r['wallet'])
micro={f:ws for f,ws in f2w.items() if 2<=len(ws)<=5}
funders=list(micro)
codes={}
with ThreadPoolExecutor(max_workers=5) as ex:
    for f,c in zip(funders, ex.map(is_contract, funders)): codes[f]=c
eoas=[f for f in funders if not codes[f]]
set198=sorted(set().union(*[micro[f] for f in eoas])) if eoas else []
print(f"198-set (EOA-funder, capital-clean): {len(set198)} wallets")

# rout recipients per wallet (candidate proxies)
rout={r['wallet']:[x for x in (r.get('rout') or []) if x not in KNOWN] for r in rows}

def check(w):
    cands=[w]+rout.get(w,[])
    best=0.0; bm=None; proxy=None
    for c in cands[:4]:
        mp,mk=max_position(c)
        if mp>best: best=mp; bm=mk; proxy=c
    return {"wallet":w,"max_pos_usd":round(best),"market":bm,"proxy":proxy}

results=[]
with ThreadPoolExecutor(max_workers=6) as ex:
    for i,r in enumerate(ex.map(check, set198)):
        results.append(r)
        if i%40==0: print(f"  {i}/{len(set198)}")
qual=[r for r in results if r["max_pos_usd"]>=1000]
qual.sort(key=lambda r:-r["max_pos_usd"])
import csv
with open(os.path.join(STATE,"sig198_pm_1000.csv"),"w",newline="") as f:
    wr=csv.writer(f); wr.writerow(["wallet","max_position_usd","market","pm_proxy"])
    for r in qual: wr.writerow([r["wallet"],r["max_pos_usd"],r["market"],r["proxy"]])
print("="*60)
print(f"198-set: {len(set198)} | avec position PM >= $1000: {len(qual)}")
for r in qual:
    print(f"  {r['wallet']}  ${r['max_pos_usd']:,}  via {str(r['proxy'])[:12]}  {str(r['market'])[:45]}")
print(f"-> state/sig198_pm_1000.csv")
