"""Les comptes Polymarket financés par le financeur commun Nobel 2025 : profil, paris Machado, gains, et destination
de chaque retrait (ordres Relay). Les adresses sont relues dans les sorties précédentes, jamais retapées.

Entrées : resultats/pm_nobel_financeur/{flux.csv,resume.json} (pm_nobel_financeur.py).
Sorties : resultats/pm_nobel_comptes/{comptes.csv,relay.csv,paris.csv,resume.json}.
Sources : gamma-api /public-profile, data-api /v2/trades et /v2/activity, api.relay.link /requests/v2 (archivées).

Usage : python3 scripts/pm_nobel_comptes.py
"""
from __future__ import annotations

import csv
import gzip
import json
from datetime import datetime, timezone

from onchain import ROOT, http_json

CASE = "pm_nobel_c7"
FLUX = ROOT / "resultats/pm_nobel_financeur/flux.csv"
OUT = ROOT / "resultats/pm_nobel_comptes"
USDC = "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359"
ANNONCE = datetime(2025, 10, 10, 9, 0, tzinfo=timezone.utc).timestamp()  # ~09:00 UTC (REPORT.md C7)
CONNUS = {"0xa430506774f9efaf39903ee7e0db1351f66891ca": "6741", "0x234cc49e43dff8b3207bbd3a8a2579f339cb9867": "dirtycup",
          "0x8507124d416dd181ea552e01a0dfed19ab0b1086": "madurowilllose", "0x1973177faa69b94b4afab818e612a7c05b3c01a9": "fmaduro",
          "0x03f8aae7ae1687ef7e2d55e4429e72e9a95d8541": "trumpdeservesit"}


def relay_requests(proxy: str) -> dict:
    """Ordres Relay d'un compte. L'API est bridée (~1 appel/min) : réponse déjà archivée relue, sinon pause de 65 s."""
    url = f"https://api.relay.link/requests/v2?user={proxy}&limit=50"
    idx = ROOT / "sources" / CASE / "INDEX.jsonl"
    for line in (idx.open() if idx.exists() else []):
        r = json.loads(line)
        if r["url"] == url and r["status"] == 200:
            body = r["inline"] if r.get("inline") is not None else gzip.decompress((ROOT / r["file"]).read_bytes())
            return json.loads(body)
    return http_json(CASE, url, pause=65)[0]


def paged(url: str, limit: int = 500, max_pages: int = 20) -> list:
    out, cursor = [], None
    for _ in range(max_pages):
        u = f"{url}&limit={limit}" + (f"&cursor={cursor}" if cursor else "")
        d, _ = http_json(CASE, u, pause=0.2)
        out += d.get("data") or []
        cursor = (d.get("pagination") or {}).get("next_cursor")
        if not cursor:
            return out
    raise RuntimeError(f"pagination non terminée après {max_pages} pages : {url}")  # jamais de troncature silencieuse


def main() -> None:
    rows = list(csv.DictReader(FLUX.open()))
    fund = json.loads((ROOT / "resultats/pm_nobel_financeur/resume.json").read_text())["adresse"]
    funded = {}
    for r in rows:
        if r["from"] == fund and r["asset_contract"] == USDC and r["to_tags"] == "contrat":
            funded.setdefault(r["to"], []).append((r["timestamp"], float(r["amount"]), r["tx"]))
    OUT.mkdir(parents=True, exist_ok=True)
    comptes, relay_rows, paris = [], [], []
    for proxy, fl in sorted(funded.items(), key=lambda x: min(t for t, _, _ in x[1])):
        prof, _ = http_json(CASE, f"https://gamma-api.polymarket.com/public-profile?address={proxy}", pause=0.2)
        trades = paged(f"https://data-api.polymarket.com/v2/trades?user={proxy}")
        acts = paged(f"https://data-api.polymarket.com/v2/activity?user={proxy}")
        rel = relay_requests(proxy)
        reqs = rel.get("requests") or []
        if rel.get("continuation"):
            raise RuntimeError(f"Relay : plus de 50 ordres pour {proxy}, pagination à ajouter")
        nobel = [t for t in trades if "Nobel" in (t.get("title") or "")]
        before = [t for t in nobel if t["timestamp"] < ANNONCE]
        for t in nobel:
            paris.append({"proxy": proxy, "nom": prof.get("name"), "utc": datetime.fromtimestamp(t["timestamp"], timezone.utc).isoformat(),
                          "avant_annonce": t["timestamp"] < ANNONCE, "side": t.get("side"), "outcome": t.get("outcome"),
                          "title": t.get("title"), "size": t.get("size"), "price": t.get("price"),
                          "usdc": round(float(t.get("size") or 0) * float(t.get("price") or 0), 2),
                          "tx": t.get("transaction_hash")})
        redeems = [a for a in acts if a.get("type") == "REDEEM"]
        for q in reqs:
            md = (q.get("data") or {}).get("metadata") or {}
            relay_rows.append({"proxy": proxy, "nom": prof.get("name"), "createdAt": q.get("createdAt"), "status": q.get("status"),
                               "recipient": (q.get("recipient") or "").lower(), "vers_financeur": (q.get("recipient") or "").lower() == fund,
                               "vers_compte_finance": (q.get("recipient") or "").lower() in funded,
                               "montant_sortie": (md.get("currencyOut") or {}).get("amountFormatted"),
                               "chaine_sortie": ((md.get("currencyOut") or {}).get("currency") or {}).get("chainId"),
                               "in_tx": ";".join(t.get("hash") or "" for t in (q.get("data") or {}).get("inTxs") or []),
                               "request_id": q.get("id")})
        comptes.append({"proxy": proxy, "connu_dossier_C7": CONNUS.get(proxy, ""), "nom": prof.get("name"),
                        "profil_cree": prof.get("createdAt"),
                        "premier_financement": min(t for t, _, _ in fl), "finance_usdc": round(sum(a for _, a, _ in fl), 2),
                        "n_paris_nobel_avant": len(before),
                        "cout_nobel_avant": round(sum(float(t["size"]) * float(t["price"]) for t in before if t.get("side") == "BUY"), 2),
                        "marches_nobel": "|".join(sorted({t.get("title", "") for t in nobel}))[:200],
                        "redeem_usdc": round(sum(float(a.get("usdc_size") or 0) for a in redeems), 2),
                        "n_trades_total": len(trades), "n_relay": len(reqs)})
        print(f"{prof.get('name') or '?':<22} {proxy} créé {prof.get('createdAt', '')[:19]} financé {comptes[-1]['finance_usdc']:>10,.2f} "
              f"Nobel avant: {len(before)} ordres, {comptes[-1]['cout_nobel_avant']:>10,.2f} $ | redeem {comptes[-1]['redeem_usdc']:>10,.2f} "
              f"| Relay {len(reqs)}", flush=True)
    for name, data in (("comptes", comptes), ("relay", relay_rows), ("paris", paris)):
        with (OUT / f"{name}.csv").open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(data[0]))
            w.writeheader()
            w.writerows(data)
    back = [r for r in relay_rows if r["vers_financeur"] and r["status"] == "success"]
    inter = [r for r in relay_rows if r["vers_compte_finance"] and r["status"] == "success"]
    resume = {"financeur": fund, "comptes": len(comptes), "finance_total": round(sum(c["finance_usdc"] for c in comptes), 2),
              "cout_nobel_avant_total": round(sum(c["cout_nobel_avant"] for c in comptes), 2),
              "redeem_total": round(sum(c["redeem_usdc"] for c in comptes), 2),
              "relay_vers_financeur": {"n": len(back), "usdc": round(sum(float(r["montant_sortie"] or 0) for r in back), 2)},
              "relay_entre_comptes": {"n": len(inter), "usdc": round(sum(float(r["montant_sortie"] or 0) for r in inter), 2)}}
    (OUT / "resume.json").write_text(json.dumps(resume, indent=1, ensure_ascii=False))
    print(json.dumps(resume, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
