#!/usr/bin/env python3
"""Recheck every figure of REPORT.md from the committed files, without network.

usage: python3 -I verify.py
"""
import copy
import csv
import gzip
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

NOTE = Path(__file__).resolve().parent
sys.path.insert(0, str(NOTE.parents[1] / "integrations" / "forensic-intelligence"))
import relay_graph as rg

TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
USDC_E, USDC_POLYGON = "0x2791bca1f2de4661ed88a30c99a7a9449aa84174", "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359"
USDC_ETH, PUSD = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48", "0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb"
DEPOSITORY, SOLVER, ZERO = "0x4cd00e387622c35bddb9b4c962c136462338bc31", "0xf70da97812cb96acdf810712aa562db8dfa3dbef", "0x" + "0" * 40
PAYER, DEPOSIT_ADDRESS, C5_ACCOUNT = "0xfd66d7ed45d7962ad009e669cdaec9319e38fb6d", "0x29ec3716a63cf27c7873831e9458f0486e819031", "0x1fa1be3eab546e06e4290839bf4c1d7abfbf1fa9"
COMPARATOR, NOBEL_BUYER = "0xecb14ac6e9ca447ce2f2912e6217b43d7b655da3", "0xe25b9180f5687aa85bd94ee309bb72a464320f1b"
ORDER_1, ORDER_2 = "0xb81385da58b0028e35f7fffe0f0782b2d433a52dc996512006242c802932878b", "0xe3ec2937f0144ae3973ada3b29fb48f9f9162deab129bb37f9b7412314827231"
LEGS_1 = [  # (chain, transaction, token, from, to, raw amount) of the transfer that each leg must contain
    ("polygon", "0xc716f77872770540b5adf34aef6a694aa2f8085fd5697cfca6f810f18b58d73e", USDC_E, PAYER, DEPOSITORY, 1_000_000_000),
    ("ethereum", "0xdb13cf16ebea06f3bcc37ec86ab84ea9f770476e026278c0466d2dbdcfb63ad7", USDC_ETH, SOLVER, DEPOSIT_ADDRESS, 1_000_000_000),
    ("ethereum", "0xa41680707227f6697248fd9ee404d454edb3efe821282f57d160f7c40f856a47", USDC_ETH, DEPOSIT_ADDRESS, DEPOSITORY, 1_000_000_000),
    ("polygon", "0xade90fd9b144864fdf66fdcfc18f40de0053c9c7c78986c02c3dd907247d8223", USDC_E, SOLVER, DEPOSIT_ADDRESS, 1_000_000_000),
    ("polygon", "0xf99eddffe076296abeeef8bc8236acea0c86c7e183a470c0b633f1647b4e3b14", PUSD, ZERO, C5_ACCOUNT, 1_000_000_000),
]
LEGS_2 = [
    ("polygon", "0x473aef761609e901ba8eb51fc93119b445de00a31903068f7a8d46afcdd7320b", USDC_E, COMPARATOR, DEPOSITORY, 19_000_000),
    ("polygon", "0x00704662785e55c0aceff117cd806a968f435163ab0d4568a9a701c61da1b7ea", USDC_POLYGON, SOLVER, NOBEL_BUYER, 19_000_000),
]
RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append(bool(ok))
    print(f"{'PASS' if ok else 'FAIL'} {name}" + (f"  [{detail}]" if detail else ""))


def read_csv(name):
    with open(NOTE / "data" / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def receipt(chain, tx):
    return json.loads((NOTE / "evidence" / "receipts" / f"{chain}_{tx}.json").read_text())


def nodes_agree(doc):
    views = [([(l["address"].lower(), l["topics"], l["data"]) for l in n["receipt"]["logs"]], n["tx"]["input"], n["block_timestamp"], n["receipt"]["status"])
             for n in doc["nodes"].values()]
    return len(views) == 2 and views[0] == views[1] and views[0][3] == "0x1"


def has_transfer(doc, token, sender, recipient, amount):
    topic = lambda a: "0x" + "0" * 24 + a[2:]
    return all(any(l["address"].lower() == token and l["topics"] == [TRANSFER, topic(sender), topic(recipient)] and int(l["data"], 16) == amount
                   for l in n["receipt"]["logs"]) for n in doc["nodes"].values())


def first(doc):
    return next(iter(doc["nodes"].values()))


def cohort(label):
    m = re.search(r"\[([^\]]+)\]", label)
    return m.group(1) if m else " ".join(label.split()[:2])


def main():
    # A. integrity
    listed = dict(line.split("  ", 1)[::-1] for line in (NOTE / "SHA256SUMS").read_text().splitlines())
    on_disk = sorted(str(p.relative_to(NOTE)) for d in ("data", "evidence") for p in (NOTE / d).rglob("*") if p.is_file())
    check("A1 every data and evidence file is listed in SHA256SUMS and matches", sorted(listed) == on_disk and all(
        hashlib.sha256((NOTE / name).read_bytes()).hexdigest() == digest for name, digest in listed.items()), f"{len(listed)} files")
    manifest = {Path(m["file"]).name: m for m in map(json.loads, (NOTE / "data" / "archive_manifest.jsonl").read_text().splitlines())}
    pages = sorted((NOTE / "evidence" / "relay").glob("*.json.gz"))
    check("A2 the three committed Relay pages match the hashes of the archive manifest", len(pages) == 3 and all(
        hashlib.sha256(gzip.decompress(p.read_bytes())).hexdigest() == manifest[p.name]["sha256_body"] for p in pages))

    check("A3 the manifest lists the 863 pages of the 703 complete histories", len(manifest) == 863 and len({m["value"].lower() for m in manifest.values()}) == 703, str(len(manifest)))

    # B. the census, recomputed from the transfers
    accounts, rows = read_csv("accounts.csv"), read_csv("transfers.csv")
    complete = {a["address"] for a in accounts if a["complete"] == "1"}
    labels = {a["address"]: a["label"] for a in accounts}
    edges = rg.account_edges(rows, complete)
    pair_orders = {o for e in edges for o in e["orders"] + e["orders_via"]}
    counts = (len(accounts), len(complete), len({r["order"] for r in rows}), len(edges), sum(e["via"] is None for e in edges), sum(e["via"] is not None for e in edges), len(pair_orders))
    check("B1 1,005 addresses asked, 703 complete, 14,194 transfers, 204 pairs (186 direct, 18 through one address), 565 orders", counts == (1005, 703, 14194, 204, 186, 18, 565), str(counts))
    saved = [(p["from"], p["to"], p["via"], int(p["n_orders"]), int(p["n_orders_via"])) for p in read_csv("pairs.csv")]
    check("B2 pairs.csv is the recomputed list of pairs", saved == [(e["from"], e["to"], e["via"] or "", len(e["orders"]), len(e["orders_via"])) for e in edges])
    groups = Counter((cohort(labels[e["from"]]), cohort(labels[e["to"]])) for e in edges)
    same_note = sum(n for (a, b), n in groups.items() if {a, b} not in ({"pr92 reference", "C5/C7"}, {"pr92 comparator", "NB-3"}))
    check("B3 two pairs join accounts that no single note of the repository studies together; the other 202 stay inside one investigation's labels",
          groups[("pr92 reference", "C5/C7")] == 1 and groups[("pr92 comparator", "NB-3")] == 1 and same_note == 202, str(same_note))

    # C. transfer 1: an account of the Iran reference population pays the C5 account MAGAMESSI
    by_order = {r["order"]: r for r in rows}
    o = by_order[ORDER_1]
    check("C1 order 1 as the API recorded it: payer to the deposit address, 1,000 USDC.e in, 1,000 USDC out, Polygon to Ethereum",
          (o["sender"], o["recipient"], o["in_chain"], o["out_chain"], o["in_tx"], o["out_tx"], o["amount_in"], o["symbol_in"], o["amount_out"], o["symbol_out"], o["status"])
          == (PAYER, DEPOSIT_ADDRESS, "137", "1", LEGS_1[0][1], LEGS_1[1][1], "1000.0", "USDC.e", "1000.0", "USDC", "success"))
    docs = [receipt(chain, tx) for chain, tx, *_ in LEGS_1]
    check("C2 five transactions, each returned identically by two nodes, each successful", all(map(nodes_agree, docs)))
    check("C3 each leg holds its transfer of exactly 1,000.000000: payer to depository, solver to deposit address, deposit address to depository, solver to deposit address, mint to the C5 account",
          all(has_transfer(d, *leg[2:]) for d, leg in zip(docs, LEGS_1)))
    check("C4 the last leg also moves the 1,000 USDC.e out of the deposit address into the collateral token contract", has_transfer(docs[4], USDC_E, DEPOSIT_ADDRESS, PUSD, 1_000_000_000))
    times = [first(d)["block_timestamp"] for d in docs]
    check("C5 the five legs follow each other within 88 seconds on 16 June 2026 (21:17:43 to 21:19:11 UTC)", times == sorted(times) and times[0] == 1781644663 and times[-1] - times[0] == 88, str(times))
    tail = lambda d: first(d)["tx"]["input"][-64:]
    check("C6 the protocol identifier at the end of each solver payment is inside the calldata of the deposit it answers",
          tail(docs[1]) in first(docs[0])["tx"]["input"] and tail(docs[3]) in first(docs[2])["tx"]["input"] and tail(docs[1]) != tail(docs[3]))
    code = json.loads((NOTE / "evidence" / "receipts" / "deposit_address_code.json").read_text())["chains"]
    check("C7 the deposit address is an EIP-7702 account delegated to 0xe6cae83b..., nonce 1, on Ethereum and Polygon, two nodes each",
          all(len(code[c]) == 2 and all(v == {"code": "0xef0100e6cae83bde06e4c305530e199d7217f42808555b", "nonce": 1} for v in code[c].values()) for c in ("ethereum", "polygon")))
    into_c5 = [r for r in rows if r["recipient"] == C5_ACCOUNT]
    from_deposit = [r for r in into_c5 if r["sender"] == DEPOSIT_ADDRESS]
    usd = sum(float(r["usd_in"]) for r in from_deposit)
    span = (min(int(r["in_time"]) for r in from_deposit), max(int(r["in_time"]) for r in from_deposit))
    check("C8 the deposit address is the sender of 33 successful orders into the C5 account, 87,559.64 USD by the API, 16 February to 21 April 2026, all Ethereum to Polygon",
          len(from_deposit) == 33 and round(usd, 2) == 87559.64 and span == (1771260935, 1776812603) and {(r["status"], r["in_chain"], r["out_chain"]) for r in from_deposit} == {("success", "1", "137")},
          f"{len(from_deposit)} {usd:.2f} {span}")
    page_orders = {q["id"] for p in pages if C5_ACCOUNT in p.name for q in json.loads(gzip.decompress(p.read_bytes()))["requests"]}
    check("C9 those 33 orders are in the committed Relay pages of the C5 account", {r["order"] for r in from_deposit} <= page_orders, f"{len(page_orders)} orders on the pages")
    proxy = json.loads((NOTE / "evidence" / "receipts" / "accounts_code_polygon.json").read_text())
    minimal = lambda c: c.startswith("0x363d3d373d3d3d363d73") and c.endswith("5af43d82803e903d91602b57fd5bf3") and len(c) == 92
    check("C10 the four accounts are EIP-1167 minimal proxies on Polygon, two nodes each", set(proxy) == {PAYER, C5_ACCOUNT, COMPARATOR, NOBEL_BUYER} and all(len(v) == 2 and all(map(minimal, v.values())) for v in proxy.values()))

    notes = NOTE.parent
    rarity = notes / "iran-exit-rarity-2026-11-06" / "data"
    check("C11 the payer is in the cluster E population and the exit-rarity reference population, in no known group; the recipient is a C5 candidate",
          PAYER in (notes / "iran-cluster-e-network-2026-11-05" / "population.txt").read_text().lower() and (rarity / "relay_reference" / f"{PAYER}.json").exists()
          and PAYER not in (rarity / "known_groups.txt").read_text().lower() and C5_ACCOUNT in (notes / "c5-c7-recovery-overlaps-2026-11-07" / "data" / "candidates.csv").read_text().lower())
    entry_point = "0x4337084d9e255ff0702461cf8895ce9e3b5ff108"
    check("C12 steps 3 and 5 are sent to the account-abstraction entry point by another address than the deposit address",
          all(first(d)["tx"]["to"].lower() == entry_point and first(d)["tx"]["from"].lower() != DEPOSIT_ADDRESS for d in (docs[2], docs[4])))

    # D. transfer 2: a comparator wallet of the exit-rarity study pays a Nobel account
    o = by_order[ORDER_2]
    check("D1 order 2 as the API recorded it: comparator to the Nobel account, 19 USDC.e in, 19 USDC out, Polygon to Polygon",
          (o["sender"], o["recipient"], o["in_chain"], o["out_chain"], o["in_tx"], o["out_tx"], o["amount_in"], o["amount_out"], o["status"])
          == (COMPARATOR, NOBEL_BUYER, "137", "137", LEGS_2[0][1], LEGS_2[1][1], "19.0", "19.0", "success"))
    docs2 = [receipt(chain, tx) for chain, tx, *_ in LEGS_2]
    times2 = [first(d)["block_timestamp"] for d in docs2]
    check("D2 two transactions, identical on two nodes, 19.000000 from the comparator to the depository then from the solver to the Nobel account, 3 seconds apart on 29 July 2026",
          all(map(nodes_agree, docs2)) and all(has_transfer(d, *leg[2:]) for d, leg in zip(docs2, LEGS_2)) and times2 == [1785352955, 1785352958], str(times2))
    check("D3 the identifier at the end of the solver payment is inside the calldata of the deposit", tail(docs2[1]) in first(docs2[0])["tx"]["input"])
    check("D4 no other order joins these two pairs of accounts in either direction",
          sum({r["sender"], r["recipient"]} in ({PAYER, DEPOSIT_ADDRESS}, {PAYER, C5_ACCOUNT}) for r in rows) == 1 and sum({r["sender"], r["recipient"]} == {COMPARATOR, NOBEL_BUYER} for r in rows) == 1)

    in_populations = sum(COMPARATOR in f.read_text().lower() for f in (rarity / "populations").glob("*.json"))
    check("D5 the sender is in three comparator populations of the exit-rarity study with its own Relay page there; the recipient is in the graph of the largest Machado buyers",
          in_populations == 3 and (rarity / "relay" / f"{COMPARATOR}.json").exists()
          and NOBEL_BUYER in (notes / "early-detection-2026-11-13" / "data" / "nobel_top_buyers_direct_graph.json").read_text().lower(), str(in_populations))

    # E. the checks can fail
    forged = copy.deepcopy(docs[4])
    for n in forged["nodes"].values():
        for l in n["receipt"]["logs"]:
            l["topics"] = [t.replace(C5_ACCOUNT[2:], PAYER[2:]) for t in l["topics"]]
    check("E1 a receipt whose recipient is changed no longer passes", not has_transfer(forged, *LEGS_1[4][2:]))
    forged = copy.deepcopy(docs[0])
    next(iter(forged["nodes"].values()))["receipt"]["logs"].pop()
    check("E2 two nodes that disagree no longer pass", not nodes_agree(forged))

    print(f"{sum(RESULTS)}/{len(RESULTS)} checks pass")
    return 0 if all(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
