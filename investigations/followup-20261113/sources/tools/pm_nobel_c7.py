"""Piste L11 (Polymarket, Nobel de la paix 2025, dossier C7) : un financeur commun des proxies avant l'annonce ?

Affirmation publique testée (research_notes/c5-c7-recovery-overlaps-2026-11-07/REPORT.md) : « un portefeuille a financé
six comptes pour environ 250 000 $ », sans adresse publiée. Test proposé par le dépôt et jamais exécuté : historiques
d'entrées Polygon indépendants des proxies avant 2025-10-10 09:00 UTC, liens retenus seulement s'ils sont directs et
hors services.

Méthode :
- 5 proxies connus (aenews0 n'a pas d'adresse) ; transferts ERC-20 entrants et sortants (Blockscout Polygon v2) ;
- jetons officiels seulement : USDC.e et USDC natif de Polygon ;
- contreparties classées : contrat / étiquette (service) / compte externe sans étiquette ;
- « financeur commun » = même expéditeur hors service vers au moins deux proxies avant l'annonce ;
- transferts directs entre les proxies eux-mêmes.
Reprise : pages lues relues depuis checkpoints/pm_nobel_c7.jsonl.

Usage : python3 scripts/pm_nobel_c7.py [--max-pages N]
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import time
import urllib.parse
from collections import defaultdict
from pathlib import Path

from onchain import ROOT, http_json

CASE = "pm_nobel_c7"
HOST = "polygon.blockscout.com"
OUT = ROOT / "resultats" / CASE
CKPT = ROOT / "checkpoints" / f"{CASE}.jsonl"
ANNONCE = "2025-10-10T09:00:00"  # annonce du prix, ~09:00 UTC (REPORT.md C7)
PROXIES = {  # research_notes/c5-c7-recovery-overlaps-2026-11-07 et c1-c7-primary-anchors-2026-11-07 (origin/main ed249d8)
    "6741": "0xa430506774f9efaf39903ee7e0db1351f66891ca",
    "dirtycup": "0x234cc49e43dff8b3207bbd3a8a2579f339cb9867",
    "madurowilllose": "0x8507124d416dd181ea552e01a0dfed19ab0b1086",
    "fmaduro": "0x1973177faa69b94b4afab818e612a7c05b3c01a9",
    "trumpdeservesit": "0x03f8aae7ae1687ef7e2d55e4429e72e9a95d8541",
}
TOKENS = {"0x2791bca1f2de4661ed88a30c99a7a9449aa84174": ("USDC.e", 6), "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359": ("USDC", 6)}


def load_ckpt() -> dict:
    return {json.loads(l)["key"]: json.loads(l) for l in CKPT.open()} if CKPT.exists() else {}


def pages(addr: str, flt: str, done: dict, max_pages: int) -> tuple[list, bool]:
    items, params, n = [], {"type": "ERC-20", "filter": flt}, 0
    while True:
        key = f"{addr}|{json.dumps(params, sort_keys=True)}"
        if key in done:
            r = done[key]
            data = json.loads(r["inline"] if r.get("inline") is not None else gzip.decompress((ROOT / r["file"]).read_bytes()))
        else:
            data, ref = http_json(CASE, f"https://{HOST}/api/v2/addresses/{addr}/token-transfers?"
                                  + urllib.parse.urlencode(params), pause=0.25)
            r = {"key": key, "file": ref["file"], "inline": ref["inline"], "sha256": ref["sha256"]}
            with CKPT.open("a") as fh:
                fh.write(json.dumps(r) + "\n")
            done[key] = r
        items += data.get("items") or []
        n += 1
        nxt = data.get("next_page_params")
        if not nxt:
            return items, False
        if n >= max_pages:
            return items, True
        params = {**nxt, "type": "ERC-20", "filter": flt}


def tags(o: dict) -> str:
    names = ([o.get("name") or ""] + [t.get("name", "") for t in ((o.get("metadata") or {}).get("tags") or [])]
             + [t.get("label", "") for t in (o.get("public_tags") or [])])
    return "; ".join(x for x in (["contrat"] if o.get("is_contract") else []) + names if x)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-pages", type=int, default=60)
    a = ap.parse_args()
    done, edges, coverage = load_ckpt(), [], []
    OUT.mkdir(parents=True, exist_ok=True)
    who = {v: k for k, v in PROXIES.items()}
    for name, addr in PROXIES.items():
        row = {"compte": name, "proxy": addr}
        for flt in ("to", "from"):
            items, trunc = pages(addr, flt, done, a.max_pages)
            row[f"{flt}_n"], row[f"{flt}_tronque"] = len(items), trunc
            for it in items:
                tok = ((it.get("token") or {}).get("address_hash") or "").lower()
                if tok not in TOKENS:
                    continue
                sym, dec = TOKENS[tok]
                raw = int((it.get("total") or {}).get("value") or 0)
                if raw <= 0:
                    continue
                f, t = it.get("from") or {}, it.get("to") or {}
                edges.append({"compte": name, "sens": "entree" if flt == "to" else "sortie", "timestamp": it.get("timestamp"),
                              "block": it.get("block_number"), "tx": it.get("transaction_hash"), "asset": sym,
                              "amount": raw / 10 ** dec, "from": (f.get("hash") or "").lower(), "to": (t.get("hash") or "").lower(),
                              "from_tags": tags(f), "to_tags": tags(t)})
        coverage.append(row)
        print(f"{name:<16} {addr}  entrées={row['to_n']}{'+' if row['to_tronque'] else ''} "
              f"sorties={row['from_n']}{'+' if row['from_tronque'] else ''}", flush=True)
    uniq = {(e["tx"], e["from"], e["to"], e["amount"]): e for e in edges}
    edges = sorted(uniq.values(), key=lambda e: e["timestamp"] or "")
    # Financeurs : expéditeurs vers un proxy avant l'annonce.
    funders = defaultdict(lambda: defaultdict(float))
    meta = {}
    for e in edges:
        if e["sens"] == "entree" and (e["timestamp"] or "") < ANNONCE and e["to"] in who:
            funders[e["from"]][who[e["to"]]] += e["amount"]
            meta[e["from"]] = e["from_tags"]
    fund_rows = [{"financeur": f, "tags": meta[f], "n_comptes": len(by), "comptes": "|".join(sorted(by)),
                  "montant_total": round(sum(by.values()), 6), "detail": json.dumps({k: round(v, 2) for k, v in by.items()})}
                 for f, by in funders.items()]
    fund_rows.sort(key=lambda r: (-r["n_comptes"], -r["montant_total"]))
    direct = [e for e in edges if e["from"] in who and e["to"] in who]
    write(OUT / "edges.csv", edges)
    write(OUT / "financeurs_avant_annonce.csv", fund_rows)
    write(OUT / "direct_entre_proxies.csv", direct)
    write(OUT / "coverage.csv", coverage)
    common = [r for r in fund_rows if r["n_comptes"] >= 2]
    summary = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "edges": len(edges),
               "financeurs_avant_annonce": len(fund_rows), "financeurs_communs": len(common),
               "direct_entre_proxies": len(direct), "tronques": [c for c in coverage if c["to_tronque"] or c["from_tronque"]]}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False))
    print(json.dumps({k: v for k, v in summary.items() if k != "tronques"}), "| tronqués:", len(summary["tronques"]))
    for r in common[:15]:
        print("COMMUN", r["financeur"], r["tags"][:40], r["comptes"], r["montant_total"])


def write(path: Path, rows: list[dict]) -> None:
    keys = list(dict.fromkeys(k for r in rows for k in r)) if rows else []
    with path.open("w", newline="") as fh:
        if keys:
            w = csv.DictWriter(fh, fieldnames=keys)
            w.writeheader()
            w.writerows(rows)


if __name__ == "__main__":
    main()
