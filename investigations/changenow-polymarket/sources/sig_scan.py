#!/usr/bin/env python3
"""
Broox signature enumeration, EXACT count over the 7d 0xeba8 gas-recipient set (4780).
Per wallet (label-free): gas-CN (by construction) + capital CN-vs-non-CN + co-control.
Phase1 (resumable JSONL): per-wallet capital class + capital funder + relay profile.
Phase2 (in-memory): co-control via shared low-degree funder / relay edge.
Phase3: counts + CSV. Trace break = ERROR, never "no signature".
"""
import json, os, sys, time, urllib.request, urllib.error, urllib.parse
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict, Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.dirname(os.path.abspath(__file__)); STATE=os.path.join(OUT,"state")
KEY=[l.split('=',1)[1].strip() for l in open(os.path.expanduser('~/Downloads/.env')) if l.startswith('ETHERSCAN_API_KEY=')][0]
HELIUS=[l.split('=',1)[1].strip() for l in open(os.path.expanduser('~/Downloads/.env')) if l.startswith('HELIUS_RPC_URL=')][0]
ESBASE="https://api.etherscan.io/v2/api"
USDC_ETH="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"; USDT_ETH="0xdac17f958d2ee523a2206206994597c13d831ec7"
USDC_SOL="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
ZERO="0x0000000000000000000000000000000000000000"
SOL_CHAIN="792703809"
# CN set (Arkham, user-specified) + labeled extensions
CN_SET={"0xeba88149813bec1cccccfdb0dacefaaa5de94cb1","0x4958f6c329b61404b1cfd0ec8a44600a9486bd0a",
        "0x3a0d24d59af3a3444dc6ef12cdb0c6e38c985288","0x975d9bd9928f398c7e01f6ba236816fa558cd94b",
        "0xa96be652a08d9905f15b7fbe2255708709becd09","0xe2d60cfe3cf8b2079c7df0144c5b28c03469775c"}
CN_SOL={"6ftKUGVx826i7Km5Suk66EzTQz8zX8Pae9hfnKYnkbrK"}
BRIDGE_FUNDERS={"0xf70da97812cb96acdf810712aa562db8dfa3dbef","0xb92fe925dc43a0ecde6c8b1a2709c170ec4fff4f",
        "0x4cd00e387622c35bddb9b4c962c136462338bc31","0x555ce236c0220695b68341bc48c68d52210cc35b",
        "0x1205f31718499dbf1fca446663b532ef87481fe1","0x9aa02d4fae7f58b8e8f34c66e756cc734dac7fe4"}
KNOWN_NODES=BRIDGE_FUNDERS | {"0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb",ZERO,
        "0x505e71695e9bc45943c58adec1650577bca68fd9","0xeba88149813bec1cccccfdb0dacefaaa5de94cb1"}
EBA8="0xeba88149813bec1cccccfdb0dacefaaa5de94cb1"

import threading
_lock=threading.Lock(); _last=[0.0]
def _throttle():
    with _lock:
        dt=time.time()-_last[0]
        if dt<0.21: time.sleep(0.21-dt)
        _last[0]=time.time()
def es(p,chainid=1):
    p=dict(p); p['chainid']=chainid; p['apikey']=KEY
    for a in range(4):
        _throttle()
        try:
            o=json.loads(urllib.request.urlopen(ESBASE+'?'+urllib.parse.urlencode(p),timeout=35).read())
            if o.get('status')=='1': return o.get('result',[])
            m=str(o.get('result',''))
            if 'No transactions' in m or 'No records' in m: return []
            if 'rate' in m.lower() or 'Max' in m: time.sleep(0.8+a); continue
            return []
        except Exception: time.sleep(0.5*(a+1))
    return None  # ERROR
def http(u):
    for a in range(3):
        try: return json.loads(urllib.request.urlopen(u,timeout=25).read())
        except urllib.error.HTTPError as e:
            if e.code==429: time.sleep(1.0*(a+1)); continue
            return None
        except Exception: time.sleep(0.4*(a+1))
    return None
def rpc(m,p):
    b=json.dumps({"jsonrpc":"2.0","id":1,"method":m,"params":p}).encode()
    try: return json.loads(urllib.request.urlopen(urllib.request.Request(HELIUS,data=b,headers={"Content-Type":"application/json"}),timeout=25).read())
    except Exception: return None

def usdc_inbound_funders(w, chainid=1):
    """top USDC inbound funders of w (EVM). USDC first; USDT only if USDC empty (1 call typ.)."""
    agg=defaultdict(float)
    r=es({'module':'account','action':'tokentx','address':w,'contractaddress':USDC_ETH,'sort':'desc','offset':100,'page':1},chainid)
    if r is None: return None
    for t in r:
        if isinstance(t,dict) and t.get('to','').lower()==w.lower():
            agg[t.get('from','').lower()]+=int(t.get('value','0'))/1e6
    if not agg:  # fallback to USDT only when no USDC inbound
        r=es({'module':'account','action':'tokentx','address':w,'contractaddress':USDT_ETH,'sort':'desc','offset':100,'page':1},chainid)
        if r is None: return None
        for t in r:
            if isinstance(t,dict) and t.get('to','').lower()==w.lower():
                agg[t.get('from','').lower()]+=int(t.get('value','0'))/1e6
    return sorted(agg.items(), key=lambda x:-x[1])

def relay_origin_solana(w):
    d=http("https://api.relay.link/requests/v2?"+urllib.parse.urlencode({"user":w,"limit":30}))
    for r in (d.get("requests") if isinstance(d,dict) else []) or []:
        md=r.get("data",{}).get("metadata",{}); ins=(r.get("data",{}).get("inTxs") or [{}])
        if str(ins[0].get("chainId"))==SOL_CHAIN and (md.get("recipient") or "").lower()==w.lower() and md.get("sender"):
            return md["sender"]
    return None

def solana_hits_cn(origin, depth=2, seen=None):
    seen=seen or set()
    if origin in CN_SOL: return True
    if depth<0 or origin in seen: return False
    seen.add(origin)
    sigs=rpc("getSignaturesForAddress",[origin,{"limit":10}])
    if not sigs or "result" not in sigs: return False
    for s in (sigs.get("result") or [])[:10]:
        tx=rpc("getTransaction",[s["signature"],{"encoding":"jsonParsed","maxSupportedTransactionVersion":0}])
        res=(tx or {}).get("result") or {}; meta=res.get("meta") or {}
        for b in meta.get("preTokenBalances",[]):
            o=b.get("owner")
            if o in CN_SOL: return True
    return False

def capital_class(w, depth=2, seen=None, first_funder=None):
    """CN vs clean (non-CN), label-free. Returns ('CN'|'clean'|'NO_CAPITAL'|'ERROR', src, top_funder)."""
    seen=seen or set()
    if depth<0 or w.lower() in seen: return ("clean", w, first_funder)   # exhausted depth w/o CN = clean
    seen.add(w.lower())
    funders=usdc_inbound_funders(w)
    if funders is None: return ("ERROR", None, first_funder)
    funders=[(a,v) for a,v in funders if a!=w.lower()]
    if not funders: return ("NO_CAPITAL", None, first_funder)
    top=funders[0][0]
    if first_funder is None: first_funder=top
    if top in CN_SET: return ("CN", top, first_funder)
    if top in BRIDGE_FUNDERS or top==ZERO:
        o=relay_origin_solana(w)
        if o and solana_hits_cn(o): return ("CN", "solana:"+o[:10], first_funder)
        return ("clean", "bridged", first_funder)
    if top in KNOWN_NODES: return ("clean", top, first_funder)
    return capital_class(top, depth-1, seen, first_funder)

def relay_profile(w):
    d=http("https://api.relay.link/requests/v2?"+urllib.parse.urlencode({"user":w,"limit":40}))
    rout=set(); sin=set()
    for r in (d.get("requests") if isinstance(d,dict) else []) or []:
        md=r.get("data",{}).get("metadata",{}); s=(md.get("sender") or ""); rc=(md.get("recipient") or "")
        if s.lower()==w.lower() and rc and rc.lower() not in KNOWN_NODES: rout.add(rc.lower())
        if rc.lower()==w.lower() and s and s.lower() not in KNOWN_NODES and not s.startswith("0x")==False: sin.add(s.lower())
    return list(rout), list(sin)

def phase1():
    wallets=json.load(open(os.path.join(STATE,"eba8_gas_7d.json")))
    jl=os.path.join(STATE,"sig_phase1.jsonl")
    done=set()
    if os.path.exists(jl):
        for line in open(jl):
            try: done.add(json.loads(line)["wallet"])
            except: pass
    todo=[w for w in wallets if w not in done]
    sys.stderr.write(f"[phase1] {len(todo)} to do ({len(done)} done) of {len(wallets)}\n")
    def work(w):
        cap,src,top_funder=capital_class(w)
        rout,sin=relay_profile(w)
        return {"wallet":w,"capital":cap,"capital_src":src,"top_funder":top_funder,"rout":rout,"sin":sin}
    with open(jl,"a") as f, ThreadPoolExecutor(max_workers=6) as ex:
        for i,r in enumerate(ex.map(work, todo)):
            f.write(json.dumps(r)+"\n"); f.flush()
            if i%100==0: sys.stderr.write(f"  {i}/{len(todo)}\n")
    sys.stderr.write("[phase1 done]\n")

def phase23():
    rows=[json.loads(l) for l in open(os.path.join(STATE,"sig_phase1.jsonl")) if l.strip()]
    by=Counter(r["capital"] for r in rows)
    # co-control: shared low-degree capital funder (excl known nodes / eba8) + relay edge
    funder2w=defaultdict(set)
    for r in rows:
        tf=r.get("top_funder")
        if tf and tf not in KNOWN_NODES and tf!=EBA8: funder2w[tf].add(r["wallet"])
    rout={r["wallet"]:set(r.get("rout") or []) for r in rows}
    sin={r["wallet"]:set(r.get("sin") or []) for r in rows}
    # relay edges A->X->B
    Xdeg=defaultdict(set); edges=set()
    wl=[r["wallet"] for r in rows]
    rout_index=defaultdict(set)
    for w in wl:
        for x in rout[w]: rout_index[x].add(w)
    for B in wl:
        for x in sin[B]:
            for A in rout_index.get(x,()):
                if A!=B: edges.add((A,x,B)); Xdeg[x].add(B)
    def cocontrol(w):
        # shared low-degree funder
        tf=next((r.get("top_funder") for r in rows if r["wallet"]==w),None)
        if tf and tf in funder2w and 2<=len(funder2w[tf])<=5: return ("funder_partagé:"+tf[:10], list(funder2w[tf]-{w})[:3])
        # relay edge with bordered X
        for (A,x,B) in edges:
            if (A==w or B==w) and len(Xdeg[x])<=5: return ("arête:"+x[:10], [A if B==w else B])
        return (None,None)
    out=[]
    gas_only=gas_cap=full=err=0
    for r in rows:
        w=r["wallet"]; cap=r["capital"]
        cc,partners=cocontrol(w)
        clean = cap=="clean"
        if cap=="ERROR": err+=1
        sig = bool(clean and cc)
        if sig: full+=1
        elif clean: gas_cap+=1
        else: gas_only+=1
        out.append({"wallet":w,"capital_source":r.get("capital_src"),"CN_ou_non":("CN" if cap=="CN" else "non-CN" if clean else cap),
                    "co_controle":cc or "non","signature_complete":"oui" if sig else "non"})
    import csv
    with open(os.path.join(STATE,"sig_broox_7d.csv"),"w",newline="") as f:
        wr=csv.writer(f); wr.writerow(["wallet","capital_source","CN_ou_non","co_controle","signature_complete"])
        for o in out: wr.writerow([o["wallet"],o["capital_source"],o["CN_ou_non"],o["co_controle"],o["signature_complete"]])
    print("="*64)
    print(f"SIGNATURE BROOX — 7j, N={len(rows)} gazés CN-ETH (compte EXACT)")
    print("="*64)
    print(f"  capital: {dict(by)}")
    print(f"  --- ventilation ---")
    print(f"  gas-seul (capital CN / no-capital / error): {gas_only}  (dont ERREUR trace: {err})")
    print(f"  gas + capital-clean (sans co-contrôle): {gas_cap}")
    print(f"  *** SIGNATURE COMPLÈTE (gas-CN + capital-clean + co-contrôle): {full} ***")
    print(f"  relay edges A->X->B (bordés <=5): {sum(1 for (A,x,B) in edges if len(Xdeg[x])<=5)}")
    print(f"  -> state/sig_broox_7d.csv")

if __name__=="__main__":
    mode=sys.argv[1] if len(sys.argv)>1 else "all"
    if mode in ("all","p1"): phase1()
    if mode in ("all","p23"): phase23()
