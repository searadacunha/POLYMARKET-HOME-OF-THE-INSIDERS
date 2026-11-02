#!/usr/bin/env python3
"""FULL sweep: for every f2020 (ChangeNOW payout) recipient, detect Polymarket
trading on EITHER the EOA (direct CTF-exchange traders) OR the resolved deposit
wallet (proxy traders). For hits, pull full activity and size the betting.
Checkpointed to state/pm_sweep.jsonl so it can resume. Loud on errors."""
import json, os, sys, time, urllib.request, urllib.error
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from proxy_resolver import resolve

OUT=os.path.dirname(os.path.abspath(__file__)); STATE=os.path.join(OUT,"state")
CKPT=os.path.join(STATE,"pm_sweep.jsonl")
UA={"User-Agent":"Mozilla/5.0","Accept":"application/json"}

def http(u,tries=4):
    last=None
    for a in range(tries):
        try:
            return json.loads(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=25).read())
        except urllib.error.HTTPError as e:
            if e.code==400:   # malformed/unindexed address -> treat as empty
                return []
            if e.code==429:
                time.sleep(0.6*(a+1)); last=e; continue
            last=e; time.sleep(0.3*(a+1))
        except Exception as e:
            last=e; time.sleep(0.3*(a+1))
    raise RuntimeError(f"HTTP fail {u[:120]} :: {last}")

def full_activity(addr,cap=6000):
    out=[]; off=0
    while off<cap:
        a=http(f"https://data-api.polymarket.com/activity?user={addr}&limit=500&offset={off}")
        if not isinstance(a,list) or not a: break
        out+=a
        if len(a)<500: break
        off+=500
    return out

def size_from_activity(act):
    tr=[e for e in act if e.get('type')=='TRADE']
    buys=[e for e in tr if e.get('side')=='BUY']
    vol=sum(float(e.get('usdcSize') or 0) for e in tr)
    by=defaultdict(float); title={}
    for e in buys:
        c=e.get('conditionId'); by[c]+=float(e.get('usdcSize') or 0); title[c]=e.get('title')
    maxmkt=0.0; mktname=None
    for c,v in by.items():
        if v>maxmkt: maxmkt=v; mktname=title.get(c)
    tss=[int(e['timestamp']) for e in tr if e.get('timestamp')]
    return {"n_trades":len(tr),"life_vol":round(vol,2),"max_market":round(maxmkt,2),
            "market":mktname,"first_trade":min(tss) if tss else None,"last_trade":max(tss) if tss else None}

def process(o, meta):
    px=resolve(o)
    # cheap probe: 1 page each
    ea=http(f"https://data-api.polymarket.com/activity?user={o}&limit=100")
    pa=http(f"https://data-api.polymarket.com/activity?user={px}&limit=100")
    n_e=len(ea) if isinstance(ea,list) else 0
    n_p=len(pa) if isinstance(pa,list) else 0
    rec={"owner":o,"proxy":px,"cn_usd":round(meta['total_usd'],2),
         "cn_first":meta.get('first_ts'),"cn_last":meta.get('last_ts'),
         "eoa_act":n_e,"dw_act":n_p,"trader":None}
    if n_e==0 and n_p==0:
        return rec
    # determine trading account(s) and size fully
    best=None
    for label,addr,n in [("EOA",o,n_e),("DW",px,n_p)]:
        if n==0: continue
        act=full_activity(addr)
        s=size_from_activity(act)
        s.update({"account":addr,"account_type":label})
        if best is None or s['life_vol']>best['life_vol']: best=s
    rec["trader"]=best
    return rec

def main():
    d=json.load(open(os.path.join(OUT,"f2020_recipients.json")))
    done=set()
    if os.path.exists(CKPT):
        for l in open(CKPT):
            try: done.add(json.loads(l)['owner'])
            except: pass
    owners=[o for o in d if o not in done]
    print(f"total={len(d)} done={len(done)} todo={len(owners)}",flush=True)
    fh=open(CKPT,"a")
    lock_written=[0]
    def work(o):
        try:
            return process(o,d[o])
        except Exception as e:
            return {"owner":o,"proxy":resolve(o),"cn_usd":round(d[o]['total_usd'],2),
                    "eoa_act":-1,"dw_act":-1,"trader":None,"error":str(e)[:120]}
    from threading import Lock
    wl=Lock()
    with ThreadPoolExecutor(max_workers=12) as ex:
        for i,rec in enumerate(ex.map(work,owners)):
            with wl:
                fh.write(json.dumps(rec)+"\n"); fh.flush()
            if i%200==0:
                print(f"  {i}/{len(owners)}",flush=True)
    fh.close()
    print("DONE",flush=True)

if __name__=="__main__":
    main()
