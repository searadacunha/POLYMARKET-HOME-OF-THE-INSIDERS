"""Historique complet du financeur commun des comptes Nobel 2025 trouvé par pm_nobel_c7.py (Polygon, Blockscout).

L'adresse est relue dans resultats/pm_nobel_c7/financeurs_avant_annonce.csv (financeur sans étiquette commun aux 5
proxies), jamais retapée. Sorties : resultats/pm_nobel_financeur/{flux.csv,resume.json}.

Usage : python3 scripts/pm_nobel_financeur.py
"""
from __future__ import annotations

import csv
import json
import urllib.parse
from collections import Counter, defaultdict

from onchain import ROOT, http_json

CASE = "pm_nobel_c7"
HOST = "polygon.blockscout.com"
OUT = ROOT / "resultats" / "pm_nobel_financeur"
FUND = ROOT / "resultats" / "pm_nobel_c7" / "financeurs_avant_annonce.csv"
PROXIES = {"0xa430506774f9efaf39903ee7e0db1351f66891ca": "6741", "0x234cc49e43dff8b3207bbd3a8a2579f339cb9867": "dirtycup",
           "0x8507124d416dd181ea552e01a0dfed19ab0b1086": "madurowilllose", "0x1973177faa69b94b4afab818e612a7c05b3c01a9": "fmaduro",
           "0x03f8aae7ae1687ef7e2d55e4429e72e9a95d8541": "trumpdeservesit"}


def all_pages(path: str, max_pages: int = 30) -> tuple[list, bool]:
    items, params = [], {}
    for _ in range(max_pages):
        q = ("?" + urllib.parse.urlencode(params)) if params else ""
        data, _ = http_json(CASE, f"https://{HOST}/api/v2/{path}{q}", pause=0.25)
        items += data.get("items") or []
        params = data.get("next_page_params") or {}
        if not params:
            return items, False
    return items, True


def tags(o: dict) -> str:
    names = ([o.get("name") or ""] + [t.get("name", "") for t in ((o.get("metadata") or {}).get("tags") or [])]
             + [t.get("label", "") for t in (o.get("public_tags") or [])])
    return "; ".join(x for x in (["contrat"] if o.get("is_contract") else []) + names if x)


def main() -> None:
    a = next(r["financeur"] for r in csv.DictReader(FUND.open()) if not r["tags"] and int(r["n_comptes"]) >= 2)
    OUT.mkdir(parents=True, exist_ok=True)
    rows, trunc = [], {}
    for ep in ("token-transfers", "transactions", "internal-transactions"):
        items, trunc[ep] = all_pages(f"addresses/{a}/{ep}")
        for it in items:
            f, t = it.get("from") or {}, it.get("to") or {}
            tok = it.get("token") or {}
            if ep == "token-transfers":
                dec = int((it.get("total") or {}).get("decimals") or tok.get("decimals") or 0)
                amount, asset = int((it.get("total") or {}).get("value") or 0) / 10 ** dec, tok.get("symbol")
                asset_addr = (tok.get("address_hash") or "").lower()
            else:
                amount, asset, asset_addr = int(it.get("value") or 0) / 1e18, "POL", ""
            rows.append({"source": ep, "timestamp": it.get("timestamp"), "block": it.get("block_number"),
                         "tx": it.get("transaction_hash") or it.get("hash"), "from": (f.get("hash") or "").lower(),
                         "to": (t.get("hash") or "").lower(), "asset": asset, "asset_contract": asset_addr,
                         "amount": amount, "method": it.get("method") or "", "from_tags": tags(f), "to_tags": tags(t),
                         "to_label": PROXIES.get((t.get("hash") or "").lower(), ""),
                         "from_label": PROXIES.get((f.get("hash") or "").lower(), "")})
    rows.sort(key=lambda r: r["timestamp"] or "")
    with (OUT / "flux.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    inn, out = defaultdict(float), defaultdict(float)
    for r in rows:
        if r["to"] == a and r["amount"] > 0:
            inn[(r["from"], r["asset"], r["from_tags"])] += r["amount"]
        if r["from"] == a and r["amount"] > 0:
            out[(r["to"], r["asset"], r["to_tags"], r["to_label"])] += r["amount"]
    resume = {"adresse": a, "tronque": trunc, "premier": rows[0]["timestamp"], "dernier": rows[-1]["timestamp"],
              "lignes": len(rows), "par_source": dict(Counter(r["source"] for r in rows)),
              "entrees": [dict(zip(("de", "actif", "tags"), k), montant=round(v, 6)) for k, v in sorted(inn.items(), key=lambda x: -x[1])],
              "sorties": [dict(zip(("vers", "actif", "tags", "compte_nobel"), k), montant=round(v, 6)) for k, v in sorted(out.items(), key=lambda x: -x[1])]}
    (OUT / "resume.json").write_text(json.dumps(resume, indent=1, ensure_ascii=False))
    print(json.dumps(resume, indent=1, ensure_ascii=False)[:6000])


if __name__ == "__main__":
    main()
