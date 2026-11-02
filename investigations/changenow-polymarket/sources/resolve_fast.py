#!/usr/bin/env python3
import json, os, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict, Counter

OUT = os.path.dirname(os.path.abspath(__file__))
H = {"User-Agent":"Mozilla/5.0 AppleWebKit/537.36 Chrome/124.0 Safari/537.36"}
RES_CACHE = os.path.join(OUT,"clob_res.json")
res = json.load(open(RES_CACHE)) if os.path.exists(RES_CACHE) else {}

def isud(e):
    s=((e.get('slug') or '')+' '+(e.get('eventSlug') or '')).lower(); t=(e.get('title') or '').lower()
    return 'updown' in s or 'up-or-down' in s or 'up or down' in t

def theme(t):
    t=(t or '').lower()
    if any(k in t for k in [' win',' vs ','nba','nfl','mlb','soccer','ufc','fight','epl','tennis','nhl','match','cup','league','f1','boxing','fc ',' sc ','win on','o/u','spread']): return 'sport'
    if any(k in t for k in ['trump','election','president','senate','governor','poll','vote','democrat','republican','congress','minister','starmer','mayor','blockade','project freedom']): return 'politique/geo'
    if any(k in t for k in ['bitcoin','btc','ethereum','eth ','solana','price','reach','hit $','all-time','ath','s&p','crude oil','microstrategy','dip to','closes above']): return 'macro/crypto'
    return 'autre'

def fetch(cid):
    if cid in res: return
    for a in range(3):
        try:
            d=json.loads(urllib.request.urlopen(urllib.request.Request(f"https://clob.polymarket.com/markets/{cid}",headers=H),timeout=20).read())
            info={"closed":None,"win":None}
            if isinstance(d,dict) and d.get("tokens"):
                info["closed"]=d.get("closed")
                for i,t in enumerate(d["tokens"]):
                    if t.get("winner") is True or t.get("price") in (1,"1",1.0): info["win"]=i;break
            res[cid]=info; return
        except urllib.error.HTTPError as e:
            if e.code==429: time.sleep(1.0*(a+1)); continue
            res[cid]={"closed":None,"win":None}; return
        except Exception: time.sleep(0.4*(a+1))
    res[cid]={"closed":None,"win":None}

# build positions
mk=defaultdict(lambda:{"buy":0.,"sell":0.,"sh":defaultdict(float),"title":""})
for f in os.listdir(os.path.join(OUT,"activity_cache")):
    w=f[:-5]
    for e in json.load(open(os.path.join(OUT,"activity_cache",f))):
        if e.get("type")!="TRADE" or isud(e): continue
        cid=e.get("conditionId");
        if not cid: continue
        d=mk[(w,cid)]; d["title"]=e.get("title") or d["title"]
        usd=float(e.get("usdcSize") or 0); sz=float(e.get("size") or 0)
        if e.get("side")=="BUY": d["buy"]+=usd; d["sh"][e.get("outcomeIndex")]+=sz
        elif e.get("side")=="SELL": d["sell"]+=usd; d["sh"][e.get("outcomeIndex")]-=sz

cids=list({cid for (_,cid) in mk})
todo=[c for c in cids if c not in res]
print(f"resolving {len(todo)}/{len(cids)} cids (threads)...", flush=True)
with ThreadPoolExecutor(max_workers=16) as ex:
    list(ex.map(fetch, todo))
json.dump(res, open(RES_CACHE,"w"))

# per (wallet,market) pnl
rows=[]
for (w,cid),d in mk.items():
    info=res.get(cid,{"closed":None,"win":None})
    red = max(0.,d["sh"].get(info["win"],0.)) if info["win"] is not None else 0.
    pnl=d["sell"]+red-d["buy"]
    rows.append({"wallet":w,"cid":cid,"title":d["title"],"cost":d["buy"],"pnl":pnl,
                 "resolved": info["closed"] is True and info["win"] is not None,"theme":theme(d["title"])})
json.dump(rows, open(os.path.join(OUT,"nonupdown_positions.json"),"w"))

resd=[r for r in rows if r["resolved"]]
tc=sum(r["cost"] for r in resd); tp=sum(r["pnl"] for r in resd); ww=sum(1 for r in resd if r["pnl"]>0)
print("\n"+"="*64)
print(f"NON-UPDOWN — resolved markets: {len(resd)} / positions {len(rows)}")
print(f"pooled WR  = {ww}/{len(resd)} = {100*ww/len(resd):.1f}%" if resd else "n/a")
print(f"pooled ROI = ${tp:+,.0f} / ${tc:,.0f} = {100*tp/tc:+.1f}%" if tc>0 else "n/a")
print("--- by theme (resolved) ---")
for th in ["sport","politique/geo","macro/crypto","autre"]:
    rr=[r for r in resd if r["theme"]==th]
    if not rr: continue
    c=sum(r['cost'] for r in rr); p=sum(r['pnl'] for r in rr); w=sum(1 for r in rr if r['pnl']>0)
    print(f"  {th:14s} markets={len(rr):4d} WR={100*w/len(rr):3.0f}% ROI={100*p/c:+5.0f}% (cost ${c:,.0f})" if c>0 else "")

# per-wallet
W=defaultdict(lambda:{"cost":0.,"pnl":0.,"res":0,"wins":0,"g":[]})
for r in resd:
    d=W[r["wallet"]]; d["cost"]+=r["cost"]; d["pnl"]+=r["pnl"]; d["res"]+=1; d["g"].append(r["pnl"])
    if r["pnl"]>0: d["wins"]+=1
cand=[]
for w,d in W.items():
    if d["cost"]<=0: continue
    g=sorted(d["g"],reverse=True); top1=(g[0]/d["pnl"]) if (d["pnl"]>0 and g) else 0
    cand.append((w,d["res"],d["wins"]/d["res"],d["pnl"]/d["cost"],d["pnl"],d["cost"],top1))
cand.sort(key=lambda x:-x[4])
print("\n--- top 15 wallets by non-updown PnL ---")
print("wallet                                      res  WR   ROI    PnL$   cost$ top1%")
for w,r,wr,roi,pnl,cost,t1 in cand[:15]:
    print(f"{w}  {r:3d} {100*wr:3.0f}% {100*roi:+4.0f}% {pnl:+6.0f} {cost:6.0f} {100*t1:3.0f}%")
winners=[c for c in cand if c[1]>=4 and c[3]>0 and c[2]>=0.5 and c[6]<0.8]
print(f"\n--- CONSISTENT WINNERS (>=4 resolved, ROI>0, WR>=50%, not one-hit): {len(winners)} ---")
for w,r,wr,roi,pnl,cost,t1 in winners:
    print(f"  {w} res={r} WR={100*wr:.0f}% ROI={100*roi:+.0f}% PnL=${pnl:+.0f}")
# coordination
mkw=defaultdict(set)
for r in rows:
    if r["cost"]>0: mkw[r["title"] or r["cid"]].add(r["wallet"])
herd=sorted([(m,w) for m,w in mkw.items() if len(w)>=3],key=lambda x:-len(x[1]))
print(f"\n--- coordination: non-updown markets with >=3 CN wallets: {len(herd)} ---")
for m,w in herd[:10]: print(f"  {len(w)}x  {str(m)[:55]}")
print("\nDONE")
