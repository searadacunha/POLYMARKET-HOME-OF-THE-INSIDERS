#!/usr/bin/env python3
"""Cross the 472 CN-gas recipients with Polymarket activity. List PM-linked ones."""
import csv, json, os, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

OUT=os.path.dirname(os.path.abspath(__file__))
CSV=os.path.join(OUT,"state","cn_gas_recipients_30d.csv")
H={"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36","Accept":"application/json"}

rows=list(csv.DictReader(open(CSV)))
gas={r["wallet"].lower():{"usd":r["montant_usd"],"nb":r["nb_gas_recus"]} for r in rows}
wallets=list(gas.keys())

def pm(w):
    u=f"https://data-api.polymarket.com/activity?user={w}&limit=200"
    for a in range(3):
        try:
            arr=json.loads(urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=25).read())
            if not isinstance(arr,list) or not arr: return None
            vol=sum(float(x.get("usdcSize") or 0) for x in arr)
            trades=[x for x in arr if x.get("type")=="TRADE"]
            mkts={x.get("conditionId") for x in arr if x.get("conditionId")}
            return {"n":len(arr),"vol":vol,"trades":len(trades),"mkts":len(mkts)}
        except urllib.error.HTTPError as e:
            if e.code==429: time.sleep(1.2*(a+1)); continue
            return None
        except Exception: time.sleep(0.5*(a+1))
    return "ERR"

res={}
with ThreadPoolExecutor(max_workers=6) as ex:
    for w,r in zip(wallets, ex.map(pm, wallets)):
        res[w]=r

linked=[(w,r) for w,r in res.items() if isinstance(r,dict)]
err=sum(1 for r in res.values() if r=="ERR")
linked.sort(key=lambda x:-x[1]["vol"])

print(f"472 wallets gazés CN -> PM-liés: {len(linked)} | aucune activité PM: {sum(1 for r in res.values() if r is None)} | lookup err: {err}")
print()
out=[]
for w,r in linked:
    out.append({"wallet":w,"sample_vol":round(r["vol"]),"n_act":r["n"],"trades":r["trades"],
                "mkts":r["mkts"],"gas_usd":gas[w]["usd"],"gas_nb":gas[w]["nb"]})
json.dump(out, open(os.path.join(OUT,"state","cn_gas_pm_linked.json"),"w"), indent=1)
print("rang | wallet | vol(sample $) | n_act | trades | marchés | gas$ | gasx")
for i,o in enumerate(out,1):
    print(f"{i:3d} | {o['wallet']} | {o['sample_vol']:>9,} | {o['n_act']:>4} | {o['trades']:>4} | {o['mkts']:>3} | {o['gas_usd']} | {o['gas_nb']}")
