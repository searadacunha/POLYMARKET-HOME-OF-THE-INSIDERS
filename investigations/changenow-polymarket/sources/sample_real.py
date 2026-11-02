#!/usr/bin/env python3
"""Sample REAL PM wallets and extract their funding features (the negative/noise universe).
Feature per wallet: top stablecoin funder on Polygon + class (BRIDGE/CN/CEX/OTHER),
bridged_share, n_funders, age proxy. Threaded. Writes real_wallets.json."""
import json, os, sys, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chain  # Etherscan V2 (chainid 137)

OUT = os.path.dirname(os.path.abspath(__file__))
H = {"User-Agent": "Mozilla/5.0 AppleWebKit/537.36 Chrome/124.0 Safari/537.36"}

# Bridge solver / router constants (Polygon). MEASURED set; CCTP/Stargate = MISSING (noted).
BRIDGE = {
    "0xf70da97812cb96acdf810712aa562db8dfa3dbef",  # Relay Solver
    "0xb92fe925dc43a0ecde6c8b1a2709c170ec4fff4f",  # Relay Router V3
    "0x4cd00e387622c35bddb9b4c962c136462338bc31",  # Relay Depository
    "0x555ce236c0220695b68341bc48c68d52210cc35b",  # deBridge
}
CN = {
    "0xf2020cbfc13fd5d4cb2da0ff8ae2d2c093c1c423",
    "0x4958f6c329b61404b1cfd0ec8a44600a9486bd0a",
    "0xeba88149813bec1cccccfdb0dacefaaa5de94cb1",
    "0x3a0d24d59af3a3444dc6ef12cdb0c6e38c985288",
}
# A few known CEX Polygon hot wallets (small MEASURED set; not exhaustive)
CEX = {
    "0xe7804c37c13166ff0b37f5ae0bb07a3aebb6e245",  # (seen high-freq; treat as infra/CEX-like)
    "0xf89d7b9c864f589bbf53a82105107622b35eaa40",
}

def get(u):
    for a in range(3):
        try:
            return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=25).read())
        except urllib.error.HTTPError as e:
            if e.code == 429: time.sleep(1.2*(a+1)); continue
            return None
        except Exception:
            time.sleep(0.5*(a+1))
    return None

def collect_wallets(target=700):
    """Distinct PM proxy wallets from recent trades of varied liquid markets."""
    wallets = set()
    mk = get("https://gamma-api.polymarket.com/markets?closed=false&limit=120&order=volume24hr&ascending=false")
    cids = []
    if isinstance(mk, list):
        for m in mk:
            c = m.get("conditionId")
            if c: cids.append(c)
    sys.stderr.write(f"[markets] {len(cids)}\n")
    for c in cids:
        if len(wallets) >= target: break
        tr = get(f"https://data-api.polymarket.com/trades?market={c}&limit=500")
        if isinstance(tr, list):
            for t in tr:
                w = (t.get("proxyWallet") or "").lower()
                if w: wallets.add(w)
        sys.stderr.write(f"[collect] {len(wallets)} wallets\n")
    return list(wallets)[:target]

def classify(w):
    funders = {}
    for tok in ("0x2791bca1f2de4661ed88a30c99a7a9449aa84174",
                "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359",
                "0xc2132d05d31c914a87c6611c10748aeb04b58e8f"):
        rows = chain.tokentx(w, contractaddress=tok, sort="desc", offset=300, page=1)
        for r in rows if isinstance(rows, list) else []:
            if isinstance(r, dict) and r.get("to","").lower()==w:
                f = r.get("from","").lower()
                funders[f] = funders.get(f,0)+int(r.get("value","0"))/1e6
    if not funders:
        return {"wallet": w, "class": "NONE", "bridged_share": 0, "n_funders": 0, "top": None}
    tot = sum(funders.values())
    bridged = sum(v for f,v in funders.items() if f in BRIDGE)
    top = max(funders, key=funders.get)
    cls = ("BRIDGE" if top in BRIDGE else "CN" if top in CN else "CEX" if top in CEX else "OTHER")
    return {"wallet": w, "class": cls, "bridged_share": round(bridged/tot,3) if tot else 0,
            "n_funders": len(funders), "top": top, "top_is_bridge": top in BRIDGE}

def main():
    cache = os.path.join(OUT, "real_wallets.json")
    wl = collect_wallets()
    sys.stderr.write(f"[classify] {len(wl)} wallets...\n")
    out = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        for i, r in enumerate(ex.map(classify, wl)):
            out.append(r)
            if i % 50 == 0: sys.stderr.write(f"  {i}/{len(wl)}\n")
    json.dump(out, open(cache, "w"), indent=1)
    from collections import Counter
    c = Counter(r["class"] for r in out)
    bridged = sum(1 for r in out if r.get("top_is_bridge"))
    print(f"REAL universe sampled: {len(out)} wallets")
    print(f"  funding class: {dict(c)}")
    print(f"  top-funder is a BRIDGE solver: {bridged}/{len(out)} = {100*bridged/len(out):.1f}%  (FP base-rate)")
    print(f"  median bridged_share: {sorted(r['bridged_share'] for r in out)[len(out)//2]:.2f}")

if __name__ == "__main__":
    main()
