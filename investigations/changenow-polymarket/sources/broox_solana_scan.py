#!/usr/bin/env python3
"""
Broox scan, Solana-bridge-first. Input = Solana->Polygon Relay bridges whose Polygon
recipient is/funds-1-hop a PM wallet. Cluster by shared Solana origin OR bordered A->X->B
intra-cluster bridge edge. Calibrated on INT (capital fan-out=1) -> threshold<=5.
Negative control + P1/P2 non-regression injected.
"""
import json, os, sys, time, urllib.request, urllib.error, urllib.parse
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict, Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chain
OUT=os.path.dirname(os.path.abspath(__file__)); STATE=os.path.join(OUT,"state")
UA={"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36","Accept":"application/json"}
SOL_CHAIN="792703809"; FANOUT_MAX=5
# known nodes that must NEVER be used as the linking intermediary X (rule 3)
KNOWN_NODES={
 "0xf70da97812cb96acdf810712aa562db8dfa3dbef","0xb92fe925dc43a0ecde6c8b1a2709c170ec4fff4f",
 "0x4cd00e387622c35bddb9b4c962c136462338bc31","0x555ce236c0220695b68341bc48c68d52210cc35b",
 "0x1205f31718499dbf1fca446663b532ef87481fe1","0x9aa02d4fae7f58b8e8f34c66e756cc734dac7fe4",
 "0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb",  # pUSD
 "0x0000000000000000000000000000000000000000","0x505e71695e9bc45943c58adec1650577bca68fd9",
}
CN_GAS={"0xeba88149813bec1cccccfdb0dacefaaa5de94cb1","0x4958f6c329b61404b1cfd0ec8a44600a9486bd0a"}

def get(u):
    for a in range(4):
        try: return json.loads(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=30).read())
        except urllib.error.HTTPError as e:
            if e.code==429: time.sleep(1.2*(a+1)); continue
            return None
        except Exception: time.sleep(0.5*(a+1))
    return None

def enum_solana_polygon(max_pages=25):
    """Q1: enumerate Solana->Polygon Relay bridges (paginated via continuation)."""
    bridges=[]; cont=None
    for _ in range(max_pages):
        p={"originChainId":SOL_CHAIN,"destinationChainId":"137","limit":"50"}
        if cont: p["continuation"]=cont
        d=get("https://api.relay.link/requests/v2?"+urllib.parse.urlencode(p))
        if not isinstance(d,dict): break
        reqs=d.get("requests") or []
        for r in reqs:
            md=r.get("data",{}).get("metadata",{})
            if md.get("sender") and md.get("recipient"):
                bridges.append({"origin":md["sender"],"recipient":md["recipient"].lower(),
                                "ts":r.get("createdAt")})
        cont=d.get("continuation")
        if not cont or not reqs: break
    return bridges

def pm_active(w):
    a=get(f"https://data-api.polymarket.com/activity?user={w}&limit=10")
    return isinstance(a,list) and len(a)>0

def relay_profile(wallet):
    """origins (Solana senders to this wallet), R_out (outbound recipients), S_in (inbound senders)."""
    d=get("https://api.relay.link/requests/v2?"+urllib.parse.urlencode({"user":wallet,"limit":50}))
    origins=set(); rout=set(); sin=set()
    for r in (d.get("requests") if isinstance(d,dict) else []) or []:
        md=r.get("data",{}).get("metadata",{}); ins=(r.get("data",{}).get("inTxs") or [{}]); outs=(r.get("data",{}).get("outTxs") or [{}])
        s=(md.get("sender") or ""); rc=(md.get("recipient") or "")
        oc=str(ins[0].get("chainId")); dc=str(outs[0].get("chainId"))
        if s.lower()==wallet.lower():            # wallet is sender -> outbound
            if rc and rc.lower() not in KNOWN_NODES: rout.add(rc.lower())
        if rc.lower()==wallet.lower():            # wallet is recipient -> inbound
            if oc==SOL_CHAIN and s: origins.add(s)         # Solana origin
            elif s and s.lower() not in KNOWN_NODES: sin.add(s.lower())  # EVM intermediary
    return {"wallet":wallet.lower(),"origins":origins,"rout":rout,"sin":sin}

def main():
    print("="*72); print("INPUT — Solana->Polygon Relay bridges (Q1 originChainId)"); print("="*72)
    bridges=enum_solana_polygon()
    recips=sorted({b["recipient"] for b in bridges})
    print(f"  bridges enumerated: {len(bridges)} | distinct Polygon recipients: {len(recips)}")
    # NON-REGRESSION: ensure P1 present (P1 should be a recipient of a Solana bridge)
    P1="0x054ec2f0ccfdae941886a3ed306635068c716639"; P2="0xe56526b27b96f009b31ddb46558a134047bfce48"
    inj=[]
    if P1 not in recips: inj.append(P1)
    # P2 is ETH-origin (not in solana set) but must be reachable via edge -> add as member to test
    for x in [P1,P2]:
        if x not in recips: recips.append(x)
    print(f"  + injected non-regression members P1/P2 (P1_in_solana_set={P1 in {b['recipient'] for b in bridges}})")

    # MEMBER filter: recipient is PM-active OR funds 1-hop a PM-active wallet
    def is_member(w):
        if pm_active(w): return (w,"direct")
        # 1-hop: outbound stables to a PM-active addr
        for tok in ("0x2791bca1f2de4661ed88a30c99a7a9449aa84174","0x3c499c542cef5e3811e1192ce70d8cc03d5c3359"):
            for t in (chain.tokentx(w,contractaddress=tok,sort="desc",offset=30,page=1) or [])[:30]:
                if isinstance(t,dict) and t.get("from","").lower()==w:
                    x=t.get("to","").lower()
                    if x not in KNOWN_NODES and pm_active(x): return (w,"via_proxy:"+x)
        return None
    members={}
    with ThreadPoolExecutor(max_workers=6) as ex:
        for r in ex.map(is_member, recips):
            if r: members[r[0]]=r[1]
    print(f"  MEMBERS (PM-linked recipients): {len(members)} / {len(recips)}")

    # relay profiles
    profs={}
    with ThreadPoolExecutor(max_workers=6) as ex:
        for p in ex.map(relay_profile, list(members)):
            profs[p["wallet"]]=p

    # ---- NEGATIVE CONTROL: base rate of shared Solana origin ----
    print("\n"+"="*72); print("CONTRÔLE NÉGATIF"); print("="*72)
    orig2=defaultdict(set)
    for w,p in profs.items():
        for o in p["origins"]: orig2[o].add(w)
    decoded=[w for w,p in profs.items() if p["origins"]]
    shared_orig=[o for o,ws in orig2.items() if len(ws)>=2]
    in_shared=set().union(*[orig2[o] for o in shared_orig]) if shared_orig else set()
    base=100*len(in_shared)/len(decoded) if decoded else 0
    print(f"  membres avec origine Solana décodée: {len(decoded)} | origines distinctes: {len(orig2)}")
    print(f"  TAUX DE BASE origine-Solana-partagée: {len(in_shared)}/{len(decoded)} = {base:.1f}%")
    # edge base rate
    edges=[]  # (A,X,B)
    Xdeg=defaultdict(set)
    for A,pa in profs.items():
        for B,pb in profs.items():
            if A==B: continue
            common=pa["rout"] & pb["sin"]
            for X in common:
                edges.append((A,X,B)); Xdeg[X].add(B)
    bordered=[(A,X,B) for (A,X,B) in edges if len(Xdeg[X])<=FANOUT_MAX]
    print(f"  arêtes A->X->B brutes: {len(edges)} | intermédiaires distincts: {len(Xdeg)}")
    print(f"  arêtes après bordage (fan-out X intra-scan <= {FANOUT_MAX}): {len(bordered)}")

    # ---- STRONG CLUSTERS ----
    print("\n"+"="*72); print("CLUSTERS FORTS (origine Solana partagée OU arête bordée)"); print("="*72)
    # union-find over shared-origin + bordered edges
    parent={}
    def find(x):
        parent.setdefault(x,x)
        while parent[x]!=x: parent[x]=parent[parent[x]]; x=parent[x]
        return x
    def union(a,b): parent[find(a)]=find(b)
    for o,ws in orig2.items():
        ws=list(ws)
        for w in ws[1:]: union(ws[0],w)
    for (A,X,B) in bordered: union(A,B)
    groups=defaultdict(set)
    for w in profs: groups[find(w)].add(w)
    clusters=[g for g in groups.values() if len(g)>=2]
    print(f"  clusters (>=2 membres): {len(clusters)}")
    out=[]
    for g in clusters:
        g=sorted(g)
        # why: shared origin? bordered edge?
        sh=[o for o in shared_orig if orig2[o] & set(g)]
        eg=[(A,X,B) for (A,X,B) in bordered if A in g and B in g]
        gas_cn=False
        for m in g:
            for t in (chain.txlist(m,sort="desc") or [])[:40]:
                if isinstance(t,dict) and t.get("from","").lower() in CN_GAS: gas_cn=True;break
            if gas_cn: break
        corr=[]
        if sh: corr.append(f"origine_Solana_partagée={[o[:10] for o in sh]}")
        if eg: corr.append(f"arête_bordée={[(A[:8],X[:8],B[:8]) for (A,X,B) in eg]}")
        if gas_cn: corr.append("GAS-CN")
        out.append({"members":g,"markets":None,"corroborators":corr})
        print(f"\n  CLUSTER ({len(g)} membres): corroborateurs={corr}")
        for m in g: print(f"     {m}{'  <-PM' if members.get(m) else ''}")
    # non-regression check
    p1p2 = any(P1 in c["members"] and P2 in c["members"] for c in out)
    print(f"\n  NON-RÉGRESSION P1+P2 liés: {'OUI' if p1p2 else 'NON'}")
    json.dump({"clusters":out,"base_rate_shared_origin":base,"n_members":len(members),
               "n_bridges":len(bridges)}, open(os.path.join(STATE,"broox_solana_clusters.json"),"w"), default=list)
    print(f"  -> state/broox_solana_clusters.json")

if __name__=="__main__":
    main()
