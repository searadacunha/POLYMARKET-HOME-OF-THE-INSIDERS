#!/usr/bin/env python3
"""Collect funding of ~1000 active PM wallets (bridge-agnostic). For each: top USDC funders
on Polygon with amounts + the funding tx hashes (for later Relay/bridge decode)."""
import json, os, sys, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chain
OUT=os.path.dirname(os.path.abspath(__file__)); STATE=os.path.join(OUT,"state"); os.makedirs(STATE,exist_ok=True)
H={"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36","Accept":"application/json"}
STABLES={"USDC.e":"0x2791bca1f2de4661ed88a30c99a7a9449aa84174","USDC":"0x3c499c542cef5e3811e1192ce70d8cc03d5c3359",
         "USDT":"0xc2132d05d31c914a87c6611c10748aeb04b58e8f"}
def get(u):
    for a in range(3):
        try: return json.loads(urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=25).read())
        except urllib.error.HTTPError as e:
            if e.code==429: time.sleep(1.2*(a+1)); continue
            return None
        except Exception: time.sleep(0.5*(a+1))
    return None

def collect_wallets(target=1000):
    ws=set()
    for order in ("volume24hr","liquidity","volume"):
        mk=get(f"https://gamma-api.polymarket.com/markets?closed=false&limit=120&order={order}&ascending=false")
        cids=[m.get("conditionId") for m in mk if isinstance(m,dict) and m.get("conditionId")] if isinstance(mk,list) else []
        for c in cids:
            if len(ws)>=target: break
            tr=get(f"https://data-api.polymarket.com/trades?market={c}&limit=500")
            if isinstance(tr,list):
                for t in tr:
                    w=(t.get("proxyWallet") or "").lower()
                    if w: ws.add(w)
            sys.stderr.write(f"[collect] {len(ws)}\n")
        if len(ws)>=target: break
    return list(ws)[:target]

def funding(w):
    funders={}  # addr -> {usd, txs:[(hash,amt,ts)]}
    for tok in STABLES.values():
        rows=chain.tokentx(w, contractaddress=tok, sort="desc", offset=300, page=1)
        for r in rows if isinstance(rows,list) else []:
            if isinstance(r,dict) and r.get("to","").lower()==w:
                f=r.get("from","").lower(); amt=int(r.get("value","0"))/1e6
                d=funders.setdefault(f,{"usd":0.0,"txs":[]})
                d["usd"]+=amt
                if len(d["txs"])<3: d["txs"].append([r["hash"],round(amt,2),int(r["timeStamp"])])
    tot=sum(d["usd"] for d in funders.values())
    top=sorted(funders.items(), key=lambda x:-x[1]["usd"])[:5]
    return {"wallet":w,"total_in":round(tot,2),"n_funders":len(funders),
            "top":[{"addr":a,"usd":round(d["usd"],2),"txs":d["txs"]} for a,d in top]}

def main():
    cache=os.path.join(STATE,"funding_1000.json")
    wl=collect_wallets(1000)
    sys.stderr.write(f"[wallets] {len(wl)} -> funding...\n")
    out=[]
    with ThreadPoolExecutor(max_workers=5) as ex:
        for i,r in enumerate(ex.map(funding, wl)):
            out.append(r)
            if i%100==0: sys.stderr.write(f"  {i}/{len(wl)}\n")
    json.dump(out, open(cache,"w"))
    print(f"funding collected: {len(out)} wallets -> {cache}")
    print(f"  with >=1 funder: {sum(1 for r in out if r['n_funders']>0)}")

if __name__=="__main__":
    main()
