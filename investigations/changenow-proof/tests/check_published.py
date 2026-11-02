#!/usr/bin/env python3
"""Check the published copy of this investigation from a fresh clone. Standard library, no network.

sources/tools/selfcheck.py needs third-party files kept on the original machine, so it cannot run here.
This script repeats its checks on what is published and says what it cannot check.
"""
import csv
import gzip
import hashlib
import json
import re
import sys
import xml.dom.minidom
from decimal import Decimal
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "sources"
REPORTS = sorted((SRC / "reports").glob("*.md"))
HOT3 = "0xdd3d72c53ff982ff59853da71158bf1538b3ceee"
HW4 = "0xeba88149813bec1cccccfdb0dacefaaa5de94cb1"
DEP = "0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b"
KEY = "0x101b5f4dc0886c32e2b75972101aeaf9f338fb65"
FUND = "0x3eaef6d5e91ecf7b7623eb19978e145ebd417013"
USDC = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
# Cited on purpose as an example of a bad list, from a third-party file that is not published.
ONLY_IN_THIRD_PARTY = {"0x077d360f11d220e4d5d831430c81c26c777e7340"}
fails = []


def check(ok, message):
    if not ok:
        fails.append(message)


known = {p.stem for p in (SRC / "evidence/onchain").glob("*.json")}
for path in list((SRC / "data").glob("*.csv")) + [SRC / f"state/{n}" for n in ("figures.json", "p9.json", "p10.json", "p13.json", "p14.json", "p15.json", "hop2.json", "study_addresses.csv", "universe_raw.csv")] + [SRC / "evidence/labels/changenow_rows.json"]:
    known |= set(re.findall(r"0x[0-9a-f]{40,64}", path.read_text(errors="replace").lower()))
with gzip.open(SRC / "state/study_rows.jsonl.gz", "rt") as handle:
    for line in handle:
        known |= set(re.findall(r"0x[0-9a-f]{40,64}", line.lower()))
check("0x" + "ab" * 32 not in known, "reference check accepts anything")

check(len(REPORTS) == 6, f"expected 6 reports, found {len(REPORTS)}")
for path in REPORTS:
    text = path.read_text()
    check("—" not in text, f"{path.name}: em dash")
    full = set(re.findall(r"0x[0-9a-fA-F]{64}(?![0-9a-fA-F])|0x[0-9a-fA-F]{40}(?![0-9a-fA-F])", text))
    for ref in full:
        check(ref.lower() in known or ref.lower() in ONLY_IN_THIRD_PARTY, f"{path.name}: {ref} is in no published file")
    for short in set(re.findall(r"0x[0-9a-fA-F]{6,20}…[0-9a-fA-F]{0,8}", text)):
        head, _, tail = short.lower().partition("…")
        check(any(a.lower().startswith(head) and a.lower().endswith(tail) for a in full), f"{path.name}: {short} has no full form")

rows = list(csv.DictReader(open(SRC / "data/verified_transfers.csv")))
check(len(rows) == 30, f"verified rows {len(rows)}")
for row in rows:
    proof = SRC / row["node_proof_file"]
    check(proof.exists() and hashlib.sha256(proof.read_bytes()).hexdigest() == row["node_proof_sha256"], f"proof {row['tx']}")
    check(row["node_ok"] == "True", f"node check {row['tx']}")
    check(Decimal(row["amount"]) == Decimal(int(row["raw"])) / (Decimal(10) ** int(row["decimals"])), f"amount {row['tx']}")
    check(int(row["proof_level"]) == 0 or {row["src"], row["dst"]} & {HOT3, HW4, DEP, "0x4958f6c329b61404b1cfd0ec8a44600a9486bd0a"}, f"level without a label {row['tx']}")
    for column in ("service_label", "label_source", "attribution_proof", "relation_to_account", "alternatives", "visibility_limit", "chain_id", "utc"):
        check(row[column] != "", f"empty {column} on {row['tx']}")
check(sum(r["proof_level"] == "2" for r in rows) == 18, "level 2 rows")
total = lambda a, b: sum(Decimal(r["amount"]) for r in rows if r["src"] == a and r["dst"] == b)
check(total(HOT3, KEY) == Decimal("834.848793"), "kraben006 sum")
check(total(HOT3, FUND) == Decimal("510.494311"), "funder USDT sum")
check(total(HW4, FUND) == Decimal("0.01000021"), "funder ETH sum")

seen, balance = set(), 0
with gzip.open(SRC / "state/study_rows.jsonl.gz", "rt") as handle:
    for line in handle:
        r = json.loads(line)
        if r["contract"] == USDC and KEY in (r["src"], r["dst"]) and r["chain"] == 1 and (r["tx"], r["src"], r["dst"], r["raw"]) not in seen:
            seen.add((r["tx"], r["src"], r["dst"], r["raw"]))
            balance += int(r["raw"]) * (1 if r["dst"] == KEY else -1)
check(balance == 15154826661, f"key USDC balance {balance}")

send = json.load(open(SRC / "evidence/onchain/0x1a39308b89cc7d9de6e38fbf0c62aa5d0bdd777863079cd151fe12a6b135dd71.json"))
spent = int(send["tx"]["value"], 16) + int(send["receipt"]["gasUsed"], 16) * int(send["receipt"]["effectiveGasPrice"], 16)
check(4056876899262451 - spent == 1559054917606451, "send arithmetic")
check(round((spent - 2007933228056898) / int(send["tx"]["value"], 16) * 100, 1) == 19.8, "low share")
check(round(2048943671205553 / int(send["tx"]["value"], 16) * 100, 1) == 82.8, "high share")

figures = json.load(open(SRC / "state/figures.json"))
check(figures["sib"]["fingerprint"] == 12 and figures["sib"]["two_tx"] == 13, "fingerprint on tagged addresses")
check(figures["controls"]["with_ff_dep"] == 12 and figures["controls"]["fingerprint"] == 0 and figures["fixedfloat_dep_fingerprint"] == 0, "comparable controls")
check(round(1 - 0.05 ** (1 / 12), 2) == 0.22 == round(figures["controls"]["upper95_one_sided_12"], 2), "control bound")
check(figures["htx_deposit"]["stable_out"] == 44, "deposit address outflows")
base = json.load(open(SRC / "state/p16.json"))
check((base["usable"], base["with_rows"], base["comparators_with_hit"], round(base["fisher_11"], 2)) == (54, 14, 0, 0.17), "base rate")

sums = {}
for line in (SRC / "evidence/SHA256SUMS").read_text().splitlines():
    digest, name = line.split("  ", 1)
    sums[name] = digest
present = [p for p in (SRC / "evidence").rglob("*") if p.is_file() and p.name != "SHA256SUMS"]
for path in present:
    name = str(path.relative_to(SRC / "evidence"))
    check(sums.get(name) == hashlib.sha256(path.read_bytes()).hexdigest(), f"SHA256SUMS {name}")
print(f"evidence hashes checked: {len(present)} published, {len(sums) - len(present)} third-party files listed but not published")

graph = xml.dom.minidom.parse(str(SRC / "graphs/changenow_network.graphml"))
ids = {n.getAttribute("id") for n in graph.getElementsByTagName("node")}
check(all(e.getAttribute("source") in ids and e.getAttribute("target") in ids for e in graph.getElementsByTagName("edge")), "dangling edge")

print("Not checked here: labels and pages from third parties, kept out of the repository. Their URLs and hashes are in evidence/api/MANIFEST.csv on the original machine and in data_manifest.json.")
print("FAIL" if fails else "OK", len(fails))
for message in fails:
    print(" ", message)
sys.exit(1 if fails else 0)
