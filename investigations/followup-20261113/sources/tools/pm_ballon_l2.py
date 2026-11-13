"""Piste L02 (Polymarket, Ballon d'Or 2026) : les 11 dossiers sur Base, Arbitrum et Optimism, jamais lus jusqu'ici.

Le test publié des 55 paires (investigations/ballon-dor-flow-trace/sources/state/pairs.json) couvre Ethereum, Polygon et
Solana ; son STATUS.md déclare Base et BSC non lus (anti-bot de base.blockscout.com, levé le 12/11/2026). BSC reste sans
source gratuite.

Méthode, alignée sur pairs.json :
- toutes les adresses EVM des 11 dossiers (pairs.json["nodes"]) ;
- par chaîne et adresse : transactions, transferts de jetons et transactions internes (API Blockscout v2, paginées) ;
- arêtes retenues : ETH natif > 0 et jetons officiels de la liste blanche (contre l'empoisonnement d'adresses) ;
- « direct » = arête entre deux adresses de dossiers différents ;
- « partagée » = contrepartie présente chez au moins deux dossiers, classée ensuite (contrat, étiquette, volume).
Reprise : chaque page déjà lue est relue dans l'archive locale (checkpoints/pm_ballon_l2.jsonl), jamais redemandée.

Usage : python3 scripts/pm_ballon_l2.py [--max-pages N]
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

CASE = "pm_ballon_l2"
PAIRS = ROOT / "entrees/polymarket/investigations/ballon-dor-flow-trace/sources/state/pairs.json"
OUT = ROOT / "resultats" / CASE
CKPT = ROOT / "checkpoints" / f"{CASE}.jsonl"
CHAINS = {  # nom -> (chain id, hôte Blockscout, jetons officiels {contrat: (symbole, décimales)})
    "base": (8453, "base.blockscout.com", {
        "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913": ("USDC", 6), "0xd9aaec86b65d86f6a7b5b1b0c42ffa531710b6ca": ("USDbC", 6),
        "0x4200000000000000000000000000000000000006": ("WETH", 18), "0xfde4c96c8593536e31f229ea8f37b2ada2699bb2": ("USDT", 6),
        "0x50c5725949a6f0c72e6c4a641f24049a917db0cb": ("DAI", 18),
        "0xc1cba3fcea344f92d9239c08c0568f6f2f0ee452": ("wstETH", 18)}),
    "arbitrum": (42161, "arbitrum.blockscout.com", {
        "0xaf88d065e77c8cc2239327c5edb3a432268e5831": ("USDC", 6), "0xff970a61a04b1ca14834a43f5de4533ebddb5cc8": ("USDC.e", 6),
        "0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9": ("USDT", 6), "0x82af49447d8a07e3bd95bd0d56f35241523fbab1": ("WETH", 18),
        "0xda10009cbd5d07dd0cecc66161fc93d7c9000da1": ("DAI", 18),
        "0x5979d7b546e38e414f7e9822514be443a4800529": ("wstETH", 18)}),
    "optimism": (10, "optimism.blockscout.com", {
        "0x0b2c639c533813f4aa9d7837caf62653d097ff85": ("USDC", 6), "0x7f5c764cbc14f9669b88837ca1490cca17c31607": ("USDC.e", 6),
        "0x94b008aa00579c1307b0ef2c499ad98a8ce58e58": ("USDT", 6), "0x4200000000000000000000000000000000000006": ("WETH", 18),
        "0xda10009cbd5d07dd0cecc66161fc93d7c9000da1": ("DAI", 18),
        "0x1f32b1c2345538c0c6f582fcb022739c4a194ebb": ("wstETH", 18)}),
}
ENDPOINTS = ("transactions", "token-transfers", "internal-transactions")


def load_ckpt() -> dict:
    done = {}
    if CKPT.exists():
        for line in CKPT.open():
            r = json.loads(line)
            done[r["key"]] = r
    return done


def fetch_pages(host: str, addr: str, endpoint: str, done: dict, max_pages: int) -> tuple[list, bool]:
    """Toutes les pages d'un point d'accès ; renvoie (items, tronqué?). Reprend depuis l'archive locale."""
    items, params, page = [], {}, 0
    while True:
        key = f"{host}|{addr}|{endpoint}|{json.dumps(params, sort_keys=True)}"
        if key in done:
            r = done[key]
            data = json.loads(r["inline"] if r.get("inline") is not None
                              else gzip.decompress((ROOT / r["file"]).read_bytes()))
        else:
            q = ("?" + urllib.parse.urlencode(params)) if params else ""
            data, ref = http_json(CASE, f"https://{host}/api/v2/addresses/{addr}/{endpoint}{q}", pause=0.25)
            r = {"key": key, "file": ref["file"], "inline": ref["inline"], "sha256": ref["sha256"]}
            with CKPT.open("a") as fh:
                fh.write(json.dumps(r) + "\n")
            done[key] = r
        items += data.get("items") or []
        page += 1
        nxt = data.get("next_page_params")
        if not nxt:
            return items, False
        if page >= max_pages:
            return items, True
        params = nxt


def edges_from(chain: str, endpoint: str, items: list, tokens: dict) -> list[dict]:
    out = []
    for it in items:
        frm, to = (it.get("from") or {}).get("hash"), (it.get("to") or {}).get("hash")
        if not frm or not to:
            continue
        base = {"chain": chain, "from": frm.lower(), "to": to.lower(), "timestamp": it.get("timestamp"),
                "block": it.get("block_number"), "from_tags": tags(it.get("from")), "to_tags": tags(it.get("to"))}
        if endpoint == "token-transfers":
            tok = ((it.get("token") or {}).get("address_hash") or (it.get("token") or {}).get("address") or "").lower()
            if tok not in tokens:
                continue  # jeton hors liste blanche : faux jetons et empoisonnement écartés
            sym, dec = tokens[tok]
            raw = int((it.get("total") or {}).get("value") or 0)
            if raw <= 0:
                continue
            out.append({**base, "tx": it.get("transaction_hash") or it.get("tx_hash"), "asset": sym, "amount": raw / 10 ** dec,
                        "kind": "token"})
        else:
            raw = int(it.get("value") or 0)
            ok = it.get("status", "ok") in ("ok", None) and it.get("success", True) is not False
            if raw <= 0 or not ok:
                continue
            out.append({**base, "tx": it.get("hash") or it.get("transaction_hash"), "asset": "ETH", "amount": raw / 1e18,
                        "kind": "native" if endpoint == "transactions" else "internal"})
    return out


def tags(obj: dict | None) -> str:
    if not obj:
        return ""
    names = ([obj.get("name") or ""] + [t.get("name", "") for t in ((obj.get("metadata") or {}).get("tags") or [])]
             + [t.get("label", "") for t in (obj.get("public_tags") or [])])
    flags = ["contrat" if obj.get("is_contract") else "", "SCAM" if obj.get("is_scam") else ""]
    return "; ".join(x for x in flags + names if x)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-pages", type=int, default=40)
    a = ap.parse_args()
    nodes = json.loads(PAIRS.read_text())["nodes"]
    owner = {addr.lower(): case for case, addrs in nodes.items() for addr in addrs if addr.startswith("0x")}
    done, edges, coverage = load_ckpt(), [], []
    OUT.mkdir(parents=True, exist_ok=True)
    for chain, (cid, host, tokens) in CHAINS.items():
        for addr, case in sorted(owner.items(), key=lambda x: (x[1], x[0])):
            row = {"chain": chain, "case": case, "address": addr}
            for ep in ENDPOINTS:
                items, truncated = fetch_pages(host, addr, ep, done, a.max_pages)
                e = edges_from(chain, ep, items, tokens)
                edges += e
                row[ep] = len(items)
                row[f"{ep}_retenues"] = len(e)
                row[f"{ep}_tronque"] = truncated
            coverage.append(row)
            print(f"{chain:<9}{case:<17}{addr}  " + " ".join(f"{ep[:5]}={row[ep]}{'+' if row[ep + '_tronque'] else ''}"
                                                          for ep in ENDPOINTS), flush=True)
    # Déduplication : une même arête vue depuis ses deux extrémités n'est comptée qu'une fois.
    uniq = {(e["chain"], e["tx"], e["from"], e["to"], e["asset"], round(e["amount"], 12), e["kind"]): e for e in edges}
    edges = list(uniq.values())
    direct = [e for e in edges if e["from"] in owner and e["to"] in owner and owner[e["from"]] != owner[e["to"]]]
    touched = defaultdict(lambda: defaultdict(list))  # contrepartie -> dossier -> arêtes
    for e in edges:
        for mine, other in ((e["from"], e["to"]), (e["to"], e["from"])):
            if mine in owner and other not in owner:
                touched[other][owner[mine]].append(e)
    shared = []
    for cp, by_case in touched.items():
        if len(by_case) >= 2:
            any_e = next(iter(by_case.values()))[0]
            shared.append({"counterparty": cp, "cases": "|".join(sorted(by_case)), "n_cases": len(by_case),
                           "chains": "|".join(sorted({e["chain"] for es in by_case.values() for e in es})),
                           "n_edges": sum(len(v) for v in by_case.values()),
                           "tags": any_e["to_tags"] if any_e["to"] == cp else any_e["from_tags"]})
    write(OUT / "edges.csv", edges)
    write(OUT / "direct.csv", direct)
    write(OUT / "shared.csv", sorted(shared, key=lambda s: -s["n_cases"]))
    write(OUT / "coverage.csv", coverage)
    summary = {"generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "addresses": len(owner),
               "chains": list(CHAINS), "edges": len(edges), "direct": len(direct), "shared_counterparties": len(shared),
               "truncated": [c for c in coverage if any(c[f"{ep}_tronque"] for ep in ENDPOINTS)]}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False))
    print(json.dumps({k: v for k, v in summary.items() if k != "truncated"}, ensure_ascii=False),
          "| tronqués:", len(summary["truncated"]))


def write(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("")
        return
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
