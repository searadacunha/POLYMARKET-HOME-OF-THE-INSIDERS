#!/usr/bin/env python3
"""For bettor-plausible recipients, trace EOA USDC-out destinations and match
against known Polymarket contracts. Decisive: does their money reach Polymarket?"""
import json, os, time, threading, urllib.request, urllib.parse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from proxy_resolver import resolve
cfg={l.split('=',1)[0].strip():l.split('=',1)[1].strip() for l in open(os.path.expanduser('~/Downloads/.env')) if '=' in l and not l.startswith('#')}
KEY=cfg['ETHERSCAN_API_KEY']; UA={"User-Agent":"Mozilla/5.0","Accept":"application/json"}
def http(u): return json.loads(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=25).read())
_lk=threading.Lock(); _last=[0.0]
def es(p):
    p=dict(p);p['chainid']=137;p['apikey']=KEY
    u="https://api.etherscan.io/v2/api?"+urllib.parse.urlencode(p)
    for a in range(6):
        with _lk:
            dt=time.time()-_last[0]
            if dt<0.25: time.sleep(0.25-dt)
            _last[0]=time.time()
        o=json.loads(urllib.request.urlopen(u,timeout=40).read())
        r=o.get('result')
        if o.get('status')=='1' or o.get('message')=='No transactions found': return r if isinstance(r,list) else []
        if isinstance(r,str) and 'Max calls' in r: time.sleep(0.6*(a+1)); continue
        return r
    return []

PM={ # known Polymarket infra on Polygon (lowercased)
 "0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e":"CTF_Exchange",
 "0xc5d563a36ae78145c45a50134d48a1215220f80a":"NegRisk_Exchange",
 "0xd91e80cf2e7be2e162c6513ced06f1dd0da35296":"NegRisk_Adapter",
 "0x4d97dcd97ec945f40cf65f87097ace5ea0476045":"ConditionalTokens",
 "0xab45c5a4b0c941a2f231c04c3f49182e1a254052":"ClassicProxyFactory",
 "0xaacfeea03eb1561c4e67d661e40682bd20e3541b":"GnosisSafeFactory",
 "0x00000000000fb5c9adea0298d729a0cb3823cc07":"DepositWalletFactory",
 "0x256b1b01021d9e91e9ca4e9e1516d206fad149c8":"DepWalletDeployer",
}
def act_n(addr):
    a=http(f"https://data-api.polymarket.com/activity?user={addr}&limit=100")
    return len(a) if isinstance(a,list) else -1

d=json.load(open("f2020_recipients.json"))
cands=[r for r in d.values() if 300<=r['total_usd']<=20000]
cands.sort(key=lambda r:-r['total_usd'])
sample=cands[:25]
print(f"bettor-plausible recipients ($300-$20k): {len(cands)}; tracing top {len(sample)}")

def trace(r):
    o=r['wallet']
    tt=es({'module':'account','action':'tokentx','address':o,'page':1,'offset':100,'sort':'asc'})
    if not isinstance(tt,list): return {"o":o,"err":str(tt)[:80]}
    outs=[t for t in tt if t['from'].lower()==o.lower()]
    dests=Counter(t['to'].lower() for t in outs)
    pm_touch=[(PM[a],a,n) for a,n in dests.items() if a in PM]
    # also: does resolved deposit wallet have activity?
    dw=resolve(o); dw_act=act_n(dw)
    # does EOA itself have activity?
    eoa_act=act_n(o)
    return {"o":o,"cn":round(r['total_usd']),"n_out":len(outs),
            "pm_touch":pm_touch,"dw":dw,"dw_act":dw_act,"eoa_act":eoa_act,
            "top_dests":dests.most_common(3)}
res=[]
with ThreadPoolExecutor(max_workers=3) as ex:
    for r in ex.map(trace,sample): res.append(r)
for r in res:
    if 'err' in r: print("ERR",r['o'],r['err']); continue
    print(f"\n{r['o']} CN=${r['cn']:,} outs={r['n_out']} eoa_act={r['eoa_act']} dw_act={r['dw_act']}")
    print("  PM touch:", r['pm_touch'] if r['pm_touch'] else "NONE")
    print("  top dests:", r['top_dests'])
