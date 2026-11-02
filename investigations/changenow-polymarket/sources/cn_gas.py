#!/usr/bin/env python3
"""CN gas recipients, last 30d. Native outbound <= $100 from CN hots. Pure measured list."""
import os, json, csv, time, urllib.request, urllib.parse, sys

ENV = os.path.expanduser("~/Downloads/.env")
def env():
    d={}
    for l in open(ENV, errors="ignore"):
        l=l.strip()
        if "=" in l and not l.startswith("#"):
            k,v=l.split("=",1); d[k.strip()]=v.strip()
    return d
KEY = env().get("ETHERSCAN_API_KEY")
BASE = "https://api.etherscan.io/v2/api"
OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state"); os.makedirs(OUTDIR, exist_ok=True)
CSV = os.path.join(OUTDIR, "cn_gas_recipients_30d.csv")
GAS_MAX_USD = 100.0
NOW = time.time(); CUTOFF = NOW - 30*86400

SOURCES = [
    ("0x4958f6c329b61404b1cfd0ec8a44600a9486bd0a", 137, "MATIC", "0x4958f6c3 (CN hot Polygon)"),
    ("0xeba88149813bec1cccccfdb0dacefaaa5de94cb1", 1,   "ETH",   "0xeba8814 (CN hot ETH)"),
]

def price(ids):
    try:
        u="https://api.coingecko.com/api/v3/simple/price?"+urllib.parse.urlencode({"ids":ids,"vs_currencies":"usd"})
        return json.loads(urllib.request.urlopen(u,timeout=20).read())
    except Exception as e:
        return {"_err":str(e)}
PX = price("ethereum,polygon-ecosystem-token,matic-network")
def native_usd(sym):
    if sym=="ETH": return (PX.get("ethereum") or {}).get("usd")
    p=(PX.get("polygon-ecosystem-token") or {}).get("usd") or (PX.get("matic-network") or {}).get("usd")
    return p

def es(chainid, params, tries=5):
    q=dict(params); q["chainid"]=chainid; q["apikey"]=KEY
    url=BASE+"?"+urllib.parse.urlencode(q)
    last=None
    for a in range(tries):
        try:
            o=json.loads(urllib.request.urlopen(url,timeout=40).read())
            if o.get("status")=="1": return o.get("result",[]), None
            msg=str(o.get("result","")) or o.get("message","")
            if "No transactions" in msg or "No records" in msg: return [], None
            if "rate limit" in msg.lower() or "Max calls" in msg: last=msg; time.sleep(1.0+a); continue
            return None, msg
        except Exception as e:
            last=repr(e); time.sleep(0.8*(a+1))
    return None, "FAIL:"+str(last)

def native_outbound(source, chainid):
    """Paginate txlist desc; collect from==source, value>0, ts>=cutoff. Returns (rows or None, status)."""
    out=[]; page=1
    while True:
        res,err=es(chainid, {"module":"account","action":"txlist","address":source,
                             "startblock":0,"endblock":99999999,"sort":"desc","offset":2000,"page":page})
        if res is None: return None, "MANQUANT("+str(err)+")"
        if not res: break
        stop=False
        for t in res:
            ts=int(t.get("timeStamp","0"))
            if ts<CUTOFF: stop=True; break
            if (t.get("from","").lower()==source.lower() and int(t.get("value","0"))>0
                    and t.get("isError","0")=="0"):
                out.append(t)
        if stop or len(res)<2000: break
        page+=1
        if page>40: break
    return out, "OK"

print(f"window: {time.strftime('%Y-%m-%d',time.gmtime(CUTOFF))} -> {time.strftime('%Y-%m-%d',time.gmtime(NOW))} (30d)")
print(f"prices: {PX if '_err' not in PX else 'PRICE_MISSING:'+PX['_err']}")
print(f"key set: {bool(KEY)}")

allrows=[]; status={}
for src,chainid,sym,label in SOURCES:
    px=native_usd(sym)
    rows,st=native_outbound(src,chainid)
    if rows is None:
        status[label]=st; print(f"[{label}] {st}"); continue
    # filter usd<=100, dedupe by recipient
    rec={}
    for t in rows:
        nat=int(t["value"])/1e18
        usd=(nat*px) if px else None
        if usd is not None and usd>GAS_MAX_USD: continue
        w=t["to"].lower(); ts=int(t["timeStamp"])
        usd_v=(round(usd,4) if usd is not None else "MISSING_PRICE")
        if w not in rec:
            rec[w]={"wallet":w,"chaine":sym,"gaser_source":label,"montant_natif":round(nat,8),
                    "montant_usd":usd_v,"nb_gas_recus":1,"tx_hash_recent":t["hash"],"timestamp":ts}
        else:
            rec[w]["nb_gas_recus"]+=1
            if ts>rec[w]["timestamp"]:
                rec[w].update(timestamp=ts, tx_hash_recent=t["hash"], montant_natif=round(nat,8), montant_usd=usd_v)
    status[label]=f"OK ({'price ok' if px else 'PRICE_MISSING->usd cap not applied'})"
    allrows.extend(rec.values())
    print(f"[{label}] OK: {len(rec)} distinct recipients (native txns scanned: {len(rows)}), price=${px}")

allrows.sort(key=lambda r:-r["timestamp"])
with open(CSV,"w",newline="") as f:
    w=csv.writer(f); w.writerow(["wallet","chaine","gaser_source","montant_natif","montant_usd","nb_gas_recus","tx_hash_recent","timestamp","datetime_utc"])
    for r in allrows:
        w.writerow([r["wallet"],r["chaine"],r["gaser_source"],r["montant_natif"],r["montant_usd"],
                    r["nb_gas_recus"],r["tx_hash_recent"],r["timestamp"],time.strftime('%Y-%m-%d %H:%M',time.gmtime(r["timestamp"]))])

from collections import Counter
bychain=Counter(r["chaine"] for r in allrows)
print("\n"+"="*60)
print(f"TOTAL distinct wallets gazés (30d): {len(allrows)}")
for ch,n in bychain.items(): print(f"  {ch}: {n}")
print("STATUTS sources:")
for k,v in status.items(): print(f"  {k}: {v}")
print(f"CSV -> {CSV}")
