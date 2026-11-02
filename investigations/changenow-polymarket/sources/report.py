#!/usr/bin/env python3
"""Build the final CN->PM attribution table + summary from wallets_enriched.jsonl."""
import json, os, datetime as dt

OUT = os.path.dirname(os.path.abspath(__file__))

def honest_conf(r):
    """Recalibrated confidence that wallet is CN-funded, given f2020 is a CN payout hub
    (proven by Benjamin's controlled CN test-swap) BUT commingled (only ~25% inbound is
    labeled-CN; 42% from a non-CN settlement contract). So: high, never certain.
    Base 0.75 for PM bettor + direct retail payout; adjust by size/timing; cap 0.85."""
    if r.get("pm_link") is None: return 0.50
    if not r.get("pm_link"):     return 0.15
    p = 0.75
    tot = r.get("total_usd", 0)
    if tot >= 50000:   p -= 0.25   # consolidation-sized => likely infra, not a bettor payout
    elif tot >= 10000: p -= 0.08
    elif tot >= 50:    p += 0.03
    dt_ = r.get("sec_payout_to_pm")
    if dt_ is not None:
        if dt_ < -30*24*3600: p -= 0.10   # heavy PM history long before CN ever paid
        elif dt_ < 0:         p -= 0.04
        elif dt_ <= 7*24*3600:p += 0.05
    if r.get("pm_has_trade"): p += 0.02
    return round(max(0.05, min(0.85, p)), 3)

rows = []
with open(os.path.join(OUT, "wallets_enriched.jsonl")) as f:
    for line in f:
        line = line.strip()
        if line:
            o = json.loads(line)
            o["confidence"] = honest_conf(o)   # recalibrated, overrides pipeline's optimistic score
            rows.append(o)

def iso(ts):
    return dt.datetime.fromtimestamp(ts, dt.UTC).strftime("%Y-%m-%d") if ts else "—"

bettors = [r for r in rows if r.get("pm_link") is True]
nolink  = [r for r in rows if r.get("pm_link") is False]
missing = [r for r in rows if r.get("pm_link") is None]
bettors.sort(key=lambda r: (-r["confidence"], -r["total_usd"]))

tot_cn_to_bettors = sum(r["total_usd"] for r in bettors)

md = []
md.append("# CN → Polymarket — Table d'attribution (rail DIRECT_POLYGON, hub f2020)\n")
md.append(f"_Généré {dt.datetime.now(dt.UTC).strftime('%Y-%m-%d %H:%M UTC')}. "
          f"Méthodo Fugu (fugu-ultra) exécutée sur données Polygon live (Etherscan V2 + PM data-api)._\n")
md.append("## Synthèse\n")
md.append(f"- Destinataires totaux du hub CN **f2020** (USDC.e+USDC+USDT, vie complète 2026-04-14→06-22) : **{len(rows)}**")
md.append(f"- **Wallets PM CN-fundés (MESURÉ)** : **{len(bettors)}** (activité PM vérifiée data-api)")
md.append(f"- Destinataires CN sans lien PM : {len(nolink)} | lookup échoué (MISSING) : {len(missing)}")
md.append(f"- Capital CN→ ces {len(bettors)} wallets PM : **${tot_cn_to_bettors:,.0f}**")
md.append("")
# confidence bands
bands = {"≥0.90":0,"0.80–0.89":0,"0.60–0.79":0,"<0.60":0}
for r in bettors:
    c=r["confidence"]
    bands["≥0.90" if c>=0.90 else "0.80–0.89" if c>=0.80 else "0.60–0.79" if c>=0.60 else "<0.60"]+=1
md.append("Bandes de confiance (wallets PM) : " + " | ".join(f"{k}: {v}" for k,v in bands.items()) + "\n")

md.append("## Table — wallets PM CN-fundés (triés confiance, $)\n")
md.append("| # | wallet_pm | rail | cn_hub | méthode | conf | statut | CN→$ | n | 1er payout | PM trade |")
md.append("|--|--|--|--|--|--:|--|--:|--:|--|--|")
for i, r in enumerate(bettors, 1):
    md.append(f"| {i} | [{r['wallet_pm'][:10]}…](https://polymarket.com/profile/{r['wallet_pm']}) "
              f"| {r['rail']} | {r['cn_hub']} | {r['attribution_method']} | {r['confidence']:.2f} "
              f"| {r['status']} | ${r['total_usd']:,.0f} | {r['n_payouts']} | {iso(r['first_payout_ts'])} "
              f"| {'oui' if r.get('pm_has_trade') else '—'} |")
md.append("")
md.append("## Notes de validité\n")
md.append("- **hub f2020** : payout-hub actif (fan-out 3408 destinataires, médiane ~$27), "
          "corroboré par lien on-chain avec **ChangeNOW 22** (0x4958, *labellisé* PolygonScan). "
          "f2020 lui-même = OSINT 'most likely CN' (pas de label public) → plafond de confiance 0.94, jamais 'certitude'.")
md.append("- **MESURÉ** = payout ERC-20 direct depuis f2020 (on-chain) + activité PM (data-api). "
          "**NO_PM_LINK** = a reçu du CN mais aucune activité PM (hors scope mission). "
          "**MISSING** = lookup data-api échoué.")
md.append("- Faux-négatifs non couverts ici (bornes déclarées) : payouts routés via contrat tiers, "
          "rotation de gasers, rail Solana (B48k/9byY), tokens hors stables, A→B→PM multi-hop.")

with open(os.path.join(OUT, "CN_PM_TABLE.md"), "w") as f:
    f.write("\n".join(md))

# CSV
import csv
with open(os.path.join(OUT, "cn_pm_wallets.csv"), "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["wallet_pm","rail","cn_hub","attribution_method","confidence","status",
                "cn_usd","n_payouts","first_payout","pm_has_trade","pm_n_sample"])
    for r in bettors:
        w.writerow([r["wallet_pm"], r["rail"], r["cn_hub"], r["attribution_method"],
                    r["confidence"], r["status"], r["total_usd"], r["n_payouts"],
                    iso(r["first_payout_ts"]), r.get("pm_has_trade"), r.get("pm_n_activity_sample")])

print(f"PM bettors (MEASURED): {len(bettors)}  |  total recipients: {len(rows)}")
print(f"capital CN->PM bettors: ${tot_cn_to_bettors:,.0f}")
print(f"wrote CN_PM_TABLE.md + cn_pm_wallets.csv")
print("\nTop 15 by confidence/$:")
for r in bettors[:15]:
    print(f"  {r['wallet_pm']} conf={r['confidence']:.2f} ${r['total_usd']:,.0f} n={r['n_payouts']} trade={r.get('pm_has_trade')}")
