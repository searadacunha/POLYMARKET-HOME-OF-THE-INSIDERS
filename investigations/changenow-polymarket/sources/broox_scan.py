#!/usr/bin/env python3
"""
Broox structure scan, market-first. 3 traits + MANDATORY negative control.
T1 bridged filter -> T2 co-control cluster (shared origin + corroborator, with base-rate
control) -> T3 gas-CN confirmer. Solana-OFF: labels MISSING, address-level clustering OK.
"""
import json, os, sys, time, urllib.request, urllib.error, urllib.parse
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict, Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chain
OUT=os.path.dirname(os.path.abspath(__file__)); STATE=os.path.join(OUT,"state")
ENV=os.path.expanduser("~/Downloads/.env")
HELIUS_RPC=[l.split('=',1)[1].strip() for l in open(ENV) if l.startswith('HELIUS_RPC_URL=')][0]
ZERO="0x0000000000000000000000000000000000000000"
USDC_SOL="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"

BRIDGE_FUNDERS={
 "0xf70da97812cb96acdf810712aa562db8dfa3dbef":"relay","0xb92fe925dc43a0ecde6c8b1a2709c170ec4fff4f":"relay",
 "0x4cd00e387622c35bddb9b4c962c136462338bc31":"relay","0x555ce236c0220695b68341bc48c68d52210cc35b":"debridge",
 "0x1205f31718499dbf1fca446663b532ef87481fe1":"stargate_v1","0x9aa02d4fae7f58b8e8f34c66e756cc734dac7fe4":"stargate_v2",
}
CN_GAS={"0xeba88149813bec1cccccfdb0dacefaaa5de94cb1","0x4958f6c329b61404b1cfd0ec8a44600a9486bd0a",
        "0x3a0d24d59af3a3444dc6ef12cdb0c6e38c985288"}

def _get(u):
    for a in range(3):
        try: return json.loads(urllib.request.urlopen(u,timeout=25).read())
        except urllib.error.HTTPError as e:
            if e.code==429: time.sleep(1.0*(a+1)); continue
            return None
        except Exception: time.sleep(0.5*(a+1))
    return None
def rpc(method,params):
    body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    try: return json.loads(urllib.request.urlopen(urllib.request.Request(HELIUS_RPC,data=body,headers={"Content-Type":"application/json"}),timeout=25).read())
    except Exception: return {}

# ---- T1: classify ----
def classify(rec):
    if not rec["top"]: return {**rec,"klass":"NONE","bridge":None,"top_funder":None}
    top=rec["top"][0]; a=top["addr"]
    if a in BRIDGE_FUNDERS: k="BRIDGED"; b=BRIDGE_FUNDERS[a]
    elif a==ZERO: k="BRIDGED"; b="cctp_mint?"   # mint; CCTP candidate (tx-verify deferred)
    else: k="DIRECT-CEX/other"; b=None
    return {**rec,"klass":k,"bridge":b,"top_funder":a}

# ---- T2: relay origin ----
_relay_cache={}
def relay_origins(wallet):
    if wallet in _relay_cache: return _relay_cache[wallet]
    d=_get("https://api.relay.link/requests/v2?"+urllib.parse.urlencode({"user":wallet,"limit":50}))
    origins=set()
    for rq in (d.get("requests") if isinstance(d,dict) else []) or []:
        md=rq.get("data",{}).get("metadata",{}); ins=(rq.get("data",{}).get("inTxs") or [{}])
        # only inbound (dest=Polygon 137) bridges, origin sender
        outs=(rq.get("data",{}).get("outTxs") or [{}])
        if str(outs[0].get("chainId"))=="137" and md.get("sender"):
            origins.add((md.get("sender"), str(ins[0].get("chainId"))))
    _relay_cache[wallet]=origins; return origins

def origin_fanout(origin):
    """How many distinct Polygon recipients does this origin bridge to (via Relay)? high=service."""
    d=_get("https://api.relay.link/requests/v2?"+urllib.parse.urlencode({"user":origin,"limit":100}))
    recs=set()
    for rq in (d.get("requests") if isinstance(d,dict) else []) or []:
        md=rq.get("data",{}).get("metadata",{})
        if md.get("recipient"): recs.add(md["recipient"].lower())
    return len(recs)

def sol_funder(addr):
    """Label-free: who sent USDC to this Solana origin (top inbound source). Helius RPC."""
    sigs=rpc("getSignaturesForAddress",[addr,{"limit":15}])
    funders=Counter()
    for s in (sigs.get("result") or [])[:15]:
        tx=rpc("getTransaction",[s["signature"],{"encoding":"jsonParsed","maxSupportedTransactionVersion":0}])
        res=tx.get("result") or {}
        meta=res.get("meta") or {}
        pre={b["accountIndex"]:b for b in meta.get("preTokenBalances",[]) if b.get("mint")==USDC_SOL}
        post={b["accountIndex"]:b for b in meta.get("postTokenBalances",[]) if b.get("mint")==USDC_SOL}
        keys=(res.get("transaction",{}).get("message",{}).get("accountKeys",[]))
        # find accounts that DECREASED (senders) and the target increased
        for idx,b in post.items():
            owner=b.get("owner")
            if owner==addr:  # this addr received
                for i2,pb in pre.items():
                    preamt=float(pb.get("uiTokenAmount",{}).get("uiAmount") or 0)
                    postamt=float(post.get(i2,{}).get("uiTokenAmount",{}).get("uiAmount") or 0) if i2 in post else 0
                    if postamt<preamt and pb.get("owner")!=addr:
                        funders[pb.get("owner")]+=preamt-postamt
    return funders.most_common(3)

def main():
    data=json.load(open(os.path.join(STATE,"funding_1000.json")))
    cl=[classify(r) for r in data]
    n=len(cl); bridged=[r for r in cl if r["klass"]=="BRIDGED"]
    direct=[r for r in cl if r["klass"].startswith("DIRECT")]
    print("="*72); print(f"T1 — {n} PM wallets classés"); print("="*72)
    print(f"  BRIDGED: {len(bridged)} ({100*len(bridged)/n:.1f}%) | DIRECT-CEX/other: {len(direct)} | none: {n-len(bridged)-len(direct)}")
    print(f"  bridges: {dict(Counter(r['bridge'] for r in bridged))}")

    # ---- NEGATIVE CONTROL / base rate ----
    print("\n"+"="*72); print("CONTRÔLE NÉGATIF — taux de base de convergence"); print("="*72)
    # weak: same solver
    solver_share=Counter(r["bridge"] for r in bridged)
    print(f"  Convergence FAIBLE (même solver): {dict(solver_share)}")
    print(f"    -> {100*max(solver_share.values())/len(bridged):.0f}% des bridgés partagent le solver dominant = BRUIT (structure normale du bridging)")
    # strong base rate: shared origin
    relay_bridged=[r for r in bridged if r["bridge"]=="relay"]
    print(f"  Décodage origine Relay sur {len(relay_bridged)} wallets relay-bridgés...")
    w2orig={}
    with ThreadPoolExecutor(max_workers=8) as ex:
        for r,origins in zip(relay_bridged, ex.map(lambda x: relay_origins(x["wallet"]), relay_bridged)):
            w2orig[r["wallet"]]=origins
    orig2wallets=defaultdict(set)
    for w,origins in w2orig.items():
        for (o,oc) in origins: orig2wallets[o].add(w)
    decoded=[w for w,o in w2orig.items() if o]
    shared=[o for o,ws in orig2wallets.items() if len(ws)>=2]
    wallets_in_shared=set().union(*[orig2wallets[o] for o in shared]) if shared else set()
    print(f"    origines décodées: {len(decoded)}/{len(relay_bridged)} | origines distinctes: {len(orig2wallets)}")
    base=100*len(wallets_in_shared)/len(decoded) if decoded else 0
    print(f"    TAUX DE BASE origine-partagée: {len(wallets_in_shared)}/{len(decoded)} = {base:.1f}% des wallets relay décodés partagent une origine avec >=1 autre")
    print(f"    {'>15-20% => origine-partagée = STRUCTURE NORMALE, pas un signal' if base>15 else '<15% => origine-partagée RARE => peut etre un signal'}")

    # ---- T2 strong clusters: shared origin + low fanout + corroborator ----
    print("\n"+"="*72); print("CLUSTERS FORTS (origine partagée + faible fan-out + corroborateur)"); print("="*72)
    clusters=[]
    for o in shared:
        members=sorted(orig2wallets[o])
        fan=origin_fanout(o)
        funders=sol_funder(o)
        # gas-CN: any member received gas from CN const (ETH/Polygon)
        gas_cn=False
        for m in members:
            for t in (chain.txlist(m, sort="desc") or [])[:50]:
                if isinstance(t,dict) and t.get("from","").lower() in CN_GAS: gas_cn=True; break
            if gas_cn: break
        clusters.append({"origin":o,"members":members,"n_members":len(members),
                         "origin_fanout":fan,"sol_funders":funders,"gas_cn":gas_cn})
    # rank: low fanout first (service if high)
    clusters.sort(key=lambda c:(c["origin_fanout"], -c["n_members"]))
    SERVICE_FAN=30
    strong=[c for c in clusters if c["origin_fanout"]<SERVICE_FAN]
    services=[c for c in clusters if c["origin_fanout"]>=SERVICE_FAN]
    print(f"  origines partagées: {len(shared)} | dont SERVICES (fanout>={SERVICE_FAN}, bruit): {len(services)} | candidats: {len(strong)}")
    for c in strong:
        corr=[]
        if c["sol_funders"]: corr.append(f"funder-Solana-amont={c['sol_funders'][0][0][:10] if c['sol_funders'] else '?'}")
        if c["gas_cn"]: corr.append("GAS-CN")
        print(f"\n  CLUSTER origin={c['origin'][:16]} fanout={c['origin_fanout']} membres={c['n_members']}")
        for m in c["members"]: print(f"     {m}")
        print(f"     corroborateurs: {corr if corr else 'AUCUN (origine partagée seule)'}")
    json.dump({"clusters":clusters,"base_rate":base,"n_bridged":len(bridged)}, open(os.path.join(STATE,"broox_clusters.json"),"w"), default=list)
    print(f"\n  -> state/broox_clusters.json")

if __name__=="__main__":
    main()
