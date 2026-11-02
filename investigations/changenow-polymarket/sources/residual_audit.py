#!/usr/bin/env python3
"""Residual audit: among NON-traders with meaningful CN$, does their USDC ever
reach a Polymarket contract (hidden classic-proxy class)? Closes the gap left by
only checking EOA + deposit-wallet."""
import json, os, time, threading, urllib.request, urllib.parse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
cfg={l.split('=',1)[0].strip():l.split('=',1)[1].strip() for l in open(os.path.expanduser('~/Downloads/.env')) if '=' in l and not l.startswith('#')}
KEY=cfg['ETHERSCAN_API_KEY']; UA={"User-Agent":"Mozilla/5.0","Accept":"application/json"}
_lk=threading.Lock(); _last=[0.0]
def es(p):
    p=dict(p);p['chainid']=137;p['apikey']=KEY
    u="https://api.etherscan.io/v2/api?"+urllib.parse.urlencode(p)
    for a in range(6):
        with _lk:
            dt=time.time()-_last[0]
            if dt<0.22: time.sleep(0.22-dt)
            _last[0]=time.time()
        o=json.loads(urllib.request.urlopen(u,timeout=40).read())
        r=o.get('result')
        if o.get('status')=='1' or o.get('message')=='No transactions found': return r if isinstance(r,list) else []
        if isinstance(r,str) and 'Max calls' in r: time.sleep(0.6*(a+1)); continue
        return []
    return []
def http(u):
    try: return json.loads(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=25).read())
    except: return []
PM={ "0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e":"CTF_Exchange",
 "0xc5d563a36ae78145c45a50134d48a1215220f80a":"NegRisk_Exchange",
 "0xd91e80cf2e7be2e162c6513ced06f1dd0da35296":"NegRisk_Adapter",
 "0x4d97dcd97ec945f40cf65f87097ace5ea0476045":"ConditionalTokens",
 "0xab45c5a4b0c941a2f231c04c3f49182e1a254052":"ClassicProxyFactory",
 "0xaacfeea03eb1561c4e67d661e40682bd20e3541b":"GnosisSafeFactory",
 "0x56c79347e95530c01a2fc76e732f9566da16e113":"CTF_ExchangeV2?"}
rows=[json.loads(l) for l in open("state/pm_sweep.jsonl") if l.strip()]
non=[r for r in rows if not r.get('trader') and not r.get('error')]
THRESH=2000
cohort=[r for r in non if r['cn_usd']>=THRESH]
cohort.sort(key=lambda r:-r['cn_usd'])
print(f"non-trader recipients with CN$>= ${THRESH}: {len(cohort)}")
def audit(r):
    o=r['owner']
    tt=es({'module':'account','action':'tokentx','address':o,'page':1,'offset':200,'sort':'asc'})
    outs=[t for t in tt if t.get('from','').lower()==o.lower()]
    dests=Counter(t['to'].lower() for t in outs)
    pm=[(PM[a],n) for a,n in dests.items() if a in PM]
    # for each distinct dest, is it a hidden PM account? probe data-api for the 3 top dests
    hidden=[]
    for a,n in dests.most_common(4):
        act=http(f"https://data-api.polymarket.com/activity?user={a}&limit=20")
        if isinstance(act,list) and len(act)>0:
            hidden.append((a,n,len(act)))
    return {"o":o,"cn":round(r['cn_usd']),"n_out":len(outs),"pm_touch":pm,"hidden_pm_dests":hidden}
res=[]
with ThreadPoolExecutor(max_workers=3) as ex:
    for x in ex.map(audit,cohort): res.append(x)
touched=[x for x in res if x['pm_touch'] or x['hidden_pm_dests']]
print(f"non-traders whose USDC reaches a PM contract or a PM-active address: {len(touched)}/{len(res)}")
for x in touched:
    print(f"  {x['o'][:12]} CN=${x['cn']:,} pm_touch={x['pm_touch']} hidden={x['hidden_pm_dests']}")
if not touched:
    print("  => NONE. No hidden classic-proxy PM class among big-CN non-traders.")
