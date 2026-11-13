"""Amont et aval du financeur commun Nobel 2025 : d'où viennent ses fonds, où partent ses sorties après l'annonce.

Adresses et transactions relues dans resultats/pm_nobel_financeur/flux.csv (jamais retapées).
Sorties : resultats/pm_nobel_amont_aval/resume.json.

Usage : python3 scripts/pm_nobel_amont_aval.py
"""
from __future__ import annotations

import csv
import json

from onchain import ROOT, http_json

CASE = "pm_nobel_c7"
HOST = "polygon.blockscout.com"
USDC = "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359"
OUT = ROOT / "resultats/pm_nobel_amont_aval"


def tags(o: dict) -> list:
    return ([o.get("name")] if o.get("name") else []) + [t.get("name") for t in ((o.get("metadata") or {}).get("tags") or [])] \
        + [t.get("label") for t in (o.get("public_tags") or [])]


def profile(a: str) -> dict:
    d, _ = http_json(CASE, f"https://{HOST}/api/v2/addresses/{a}", pause=0.25)
    c, _ = http_json(CASE, f"https://{HOST}/api/v2/addresses/{a}/counters", pause=0.25)
    tt, _ = http_json(CASE, f"https://{HOST}/api/v2/addresses/{a}/token-transfers?type=ERC-20", pause=0.25)
    items = [it for it in (tt.get("items") or []) if ((it.get("token") or {}).get("address_hash") or "").lower() == USDC]
    return {"adresse": a, "contrat": d.get("is_contract"), "tags": tags(d), "tx_envoyees": c.get("transactions_count"),
            "transferts_jetons": c.get("token_transfers_count"),
            "usdc_recents": [{"utc": it.get("timestamp"), "de": it["from"]["hash"], "de_tags": tags(it["from"]),
                              "vers": it["to"]["hash"], "vers_tags": tags(it["to"]),
                              "usdc": int(it["total"]["value"]) / 1e6, "tx": it.get("transaction_hash")} for it in items[:25]]}


def main() -> None:
    rows = list(csv.DictReader((ROOT / "resultats/pm_nobel_financeur/flux.csv").open()))
    fund = json.loads((ROOT / "resultats/pm_nobel_financeur/resume.json").read_text())["adresse"]
    usdc = [r for r in rows if r["asset_contract"] == USDC and float(r["amount"]) > 0]
    capital = max((r for r in usdc if r["to"] == fund), key=lambda r: float(r["amount"]))  # entrée principale
    sorties = sorted((r for r in usdc if r["from"] == fund and r["timestamp"] > "2025-10-10T09"), key=lambda r: -float(r["amount"]))
    OUT.mkdir(parents=True, exist_ok=True)
    res = {"financeur": fund, "capital": {k: capital[k] for k in ("timestamp", "from", "amount", "tx")},
           "amont": profile(capital["from"]), "aval": []}
    for s in sorties:
        item = {k: s[k] for k in ("timestamp", "to", "to_tags", "amount", "tx")}
        if "Across" in s["to_tags"]:
            try:  # statut public d'un dépôt Across (chaîne et destinataire de sortie)
                item["across"], _ = http_json(CASE, "https://app.across.to/api/deposit/status?originChainId=137"
                                              f"&depositTxHash={s['tx']}", retries=2)
            except Exception as exc:
                item["across_erreur"] = str(exc)[:200]
        else:
            item["profil"] = profile(s["to"])
        res["aval"].append(item)
    (OUT / "resume.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print(json.dumps(res, indent=1, ensure_ascii=False)[:7000])


if __name__ == "__main__":
    main()
