"""Inventaire : wallets preneurs de l'univers p8 (trades >= 100 $), leur activité par split, et recoupements."""
import json, os, csv, collections
P8 = os.path.expanduser("~/Documents/Crypto/enquete_maduro_iran/donnees/brut_p8_p9/p8")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "derived")
u = {m["conditionId"]: m for m in json.load(open(os.path.join(P8, "universe.json")))}
W = collections.defaultdict(lambda: {"n": 0, "n_buy": 0, "usd": 0.0, "first": 9e12, "last": 0, "marches": set(),
                                     "split": collections.Counter()})
lus = trunc = 0
for cid, m in u.items():
    d = json.load(open(os.path.join(P8, "trades", cid + ".json")))
    lus += 1; trunc += bool(d.get("maybe_truncated"))
    for r in d["rows"]:
        w = W[r["proxyWallet"].lower()]
        w["n"] += 1; w["n_buy"] += r["side"] == "BUY"; w["usd"] += r["size"] * r["price"]
        w["first"] = min(w["first"], r["timestamp"]); w["last"] = max(w["last"], r["timestamp"])
        w["marches"].add(cid); w["split"][m["split"]] += 1
with open(os.path.join(OUT, "p8_wallets.csv"), "w", newline="") as f:
    wr = csv.writer(f); wr.writerow(["wallet", "n_trades", "n_buy", "usd", "first_ts", "last_ts", "n_marches", "n_train", "n_valid", "n_test"])
    for k, w in W.items():
        wr.writerow([k, w["n"], w["n_buy"], round(w["usd"], 2), w["first"], w["last"], len(w["marches"]),
                     w["split"]["TRAIN"], w["split"]["VALID"], w["split"]["TEST"]])
n = len(W); tot = sum(w["n"] for w in W.values())
print(f"marchés lus {lus}, tronqués {trunc}, wallets {n}, trades {tot}")
for seuil in (1, 3, 10, 30):
    print(f"  wallets avec >= {seuil} trades : {sum(1 for w in W.values() if w['n'] >= seuil)}")
print("  wallets actifs dans les 3 splits :", sum(1 for w in W.values() if all(w['split'][s] for s in ('TRAIN','VALID','TEST'))))
cn = set()
for r in csv.DictReader(open(os.path.expanduser("~/Documents/Crypto/cn_pm_sakana/state/pm_traders.csv"))):
    cn |= {r[c].lower() for c in ("owner", "proxy", "account") if r.get(c)}
print("  parieurs ChangeNOW (pm_traders.csv) :", len(cn), "présents dans p8 :", len(cn & set(W)))
wf = {r["wallet"].lower(): r for r in csv.DictReader(open(os.path.expanduser("~/Documents/Crypto/enquete_maduro_iran/phase8/wallet_features.csv")))}
print("  wallets phase 8 avec financement :", len(wf), "présents dans p8 :", len(set(wf) & set(W)))
