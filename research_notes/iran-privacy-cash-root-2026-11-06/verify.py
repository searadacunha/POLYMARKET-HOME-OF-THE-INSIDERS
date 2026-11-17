"""Offline verification of REPORT.md. Needs this folder and ../iran-solana-beneficiary-2026-11-05/evidence.

python3 -I -B verify.py
"""
import base64
import hashlib
import json
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "scripts"))
from poseidon import poseidon  # noqa: E402
from privacy_cash import decode_tx  # noqa: E402
from privacy_cash_roots import fold, root_at, self_check, zeros  # noqa: E402

PREV = HERE.parent / "iran-solana-beneficiary-2026-11-05" / "evidence"
BEN = "4dLZQynk9SZJf6PCAV73828TZHGJaf9kWgpKVUzV4Fwy"
BYBIT = "Agnhk1VsurW1ic3YNDtp3NeLTGYCiaaUwpRSKag9PdpV"
PROGRAM = "9fhQBbumKEFuXtMBDw8AaQyAjCorLGJQiS3skWZdQyQD"
TREE = "6VVKJ44WTJGCksTGJHjf1kJWZaMf9Nswgj6w7Dtrw55D"
checks = []


def check(name, cond, detail=""):
    checks.append({"check": name, "pass": bool(cond), "detail": detail})


def j(p):
    return json.loads(Path(p).read_text())


ev = HERE / "evidence" / "privacy_cash_roots"
bad = [m.name for m in ev.glob("*.meta.json") if hashlib.sha256((ev / m.name.replace(".meta.json", ".json")).read_bytes()).hexdigest() != j(m)["sha256"]]
check("evidence_sha256", not bad and len(list(ev.glob("*.meta.json"))) == 4, f"{len(bad)} mismatched")
check("poseidon_circomlib_vector", poseidon([1, 2]) == 7853200120776062878684798364095072458815029376092732009249414926327459813530)
check("historical_roots_equal_full_rebuild_on_synthetic_tree", self_check() == [4, 6, 7, 8, 10, 11, 12, 13])

# the three transactions of the earlier notes, decoded byte-exactly from the archived histories
pc = {}
for d in (PREV / "sol" / BEN, PREV / "sol" / BYBIT):
    for f in sorted(d.glob("gtfa_*_p*.json")):
        if not f.name.endswith(".meta.json"):
            for tx in j(f)["result"]["data"]:
                for r in decode_tx(tx):
                    pc[r["signature"]] = r
dep1, dep2, wd = (pc[s] for s in sorted(pc, key=lambda s: pc[s]["slot"]))
check("three_transacts", (dep1["signature"][:8], dep2["signature"][:8], wd["signature"][:8]) == ("3E3rDmYb", "5j3r5HzQ", "2kkJqk86")
      and (dep2["ext_amount"], wd["ext_amount"]) == (12_328_800_200, -990_500_000) and wd["accounts"][7] == BYBIT)
check("leaf_indices", (dep1["leaf_indices"], dep2["leaf_indices"], wd["leaf_indices"]) == ([346804, 346805], [346814, 346815], [346816, 346817]))

# trust anchor: the relayer's root is the root stored on chain
tree = j(ev / "tree_candidates.json")["result"]["value"][0]
data = base64.b64decode(tree["data"][0])
chain_root, chain_next = int.from_bytes(data[880:912], "big"), struct.unpack_from("<Q", data, 40)[0]
check("tree_account", tree["owner"] == PROGRAM and wd["accounts"][0] == dep2["accounts"][0] == TREE and len(data) == 4136)
api = j(ev / "root.json")
check("relayer_root_is_chain_root", int(api["root"]) == chain_root and api["nextIndex"] == chain_next == 890_520,
      f"slot {j(ev / 'tree_candidates.json')['result']['context']['slot']}")

leaf = {346805: dep1["output_commitments"][1], 346814: dep2["output_commitments"][0],
        346815: dep2["output_commitments"][1], 346817: wd["output_commitments"][1]}
known, folds = {}, []
for f, pair in (("proofv2_346815_346805.json", (346815, 346805)), ("proofv2_346814_346817.json", (346814, 346817))):
    d = j(ev / f)
    for i, p in zip(pair, d["proofs"]):
        r, k = fold(i, int(leaf[i], 16), [int(x) for x in p["pathElements"]], p["pathIndices"])
        folds.append(r == chain_root == int(d["root"]))
        known.update(k)
check("four_paths_fold_to_chain_root", folds == [True] * 4)
p0 = j(ev / "proofv2_346815_346805.json")["proofs"][0]
tampered = [int(x) for x in p0["pathElements"]]; tampered[3] += 1
check("tamper_one_sibling_breaks_the_path", fold(346815, int(leaf[346815], 16), tampered, p0["pathIndices"])[0] != chain_root)

z = zeros()
R = {n: root_at(n, known, z) for n in range(346_700, 346_819)}
state = {v: n for n, v in R.items() if v is not None}
check("computable_states", sorted(state.values()) == [346752, 346784, 346800, 346804, 346805, 346806, 346808, 346812,
                                                      346814, 346815, 346816, 346817, 346818])
check("deposit_12_33_proved_R346814", state.get(int(dep2["root"], 16)) == 346_814, "positive control")
check("withdrawal_proved_R346816", state.get(int(wd["root"], 16)) == 346_816 and len({R[346_814], R[346_815], R[346_816]}) == 3)
check("first_deposit_root_older_than_computable_states", int(dep1["root"], 16) not in state)
check("withdrawal_29_seconds_after_deposit", wd["block_time"] - dep2["block_time"] == 29)

out = {"passed": sum(c["pass"] for c in checks), "total": len(checks), "checks": checks}
(HERE / "verification.json").write_text(json.dumps(out, indent=1))
print(f"{out['passed']}/{out['total']} checks passed")
for c in checks:
    if not c["pass"]:
        print("FAIL", c["check"], c["detail"])
sys.exit(0 if out["passed"] == out["total"] else 1)
