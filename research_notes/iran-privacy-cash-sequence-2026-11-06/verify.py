"""Offline verification of REPORT.md. Needs this folder and ../iran-solana-beneficiary-2026-11-05/evidence. Run: python3 -I verify.py"""
import base64, hashlib, json, struct, sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "scripts"))
from keccak import keccak256  # noqa: E402
from privacy_cash import decode_tx  # noqa: E402
from relay_onchain import T_ERC20, deposits_from_receipt, match, solana_fills  # noqa: E402

PREV = HERE.parent / "iran-solana-beneficiary-2026-11-05" / "evidence"
BEN = "4dLZQynk9SZJf6PCAV73828TZHGJaf9kWgpKVUzV4Fwy"
BYBIT = "Agnhk1VsurW1ic3YNDtp3NeLTGYCiaaUwpRSKag9PdpV"
checks = []


def check(name, cond, detail=""):
    checks.append({"check": name, "pass": bool(cond), "detail": detail})


def j(p):
    return json.loads(Path(p).read_text())


# 0. archived responses of this note match their recorded sha256
bad = []
for m in sorted((HERE / "evidence").rglob("*.meta.json")):
    body = m.parent / m.name.replace(".meta.json", ".json")
    if hashlib.sha256(body.read_bytes()).hexdigest() != j(m)["sha256"]:
        bad.append(body.name)
check("evidence_sha256", not bad, f"{len(bad)} mismatched")
check("keccak_vector", keccak256(b"").hex() == "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470")

# 1. Privacy Cash: the three transactions of the previous note, decoded byte-exactly
pc = {}
for d in (PREV / "sol" / BEN, PREV / "sol" / BYBIT):
    for f in sorted(d.glob("gtfa_*_p*.json")):
        if not f.name.endswith(".meta.json"):
            for tx in j(f)["result"]["data"]:
                for r in decode_tx(tx):
                    pc[r["signature"]] = r
dep1, dep2, wd = (pc[s] for s in sorted(pc, key=lambda s: pc[s]["slot"]))
check("pc_three_transacts", len(pc) == 3)
check("pc_signatures", (dep1["signature"][:8], dep2["signature"][:8], wd["signature"][:8]) == ("3E3rDmYb", "5j3r5HzQ", "2kkJqk86"))
check("pc_ext_amounts", (dep1["ext_amount"], dep2["ext_amount"], wd["ext_amount"], wd["fee"]) == (119_021_900, 12_328_800_200, -990_500_000, 9_500_000))
check("pc_withdrawal_recipient", wd["accounts"][7] == BYBIT)
check("pc_leaf_indices", (dep1["leaf_indices"], dep2["leaf_indices"], wd["leaf_indices"]) == ([346804, 346805], [346814, 346815], [346816, 346817]))
check("pc_withdrawal_is_next_pool_transact", wd["leaf_indices"][0] == dep2["leaf_indices"][1] + 1)
check("pc_four_other_transacts_between_deposits", (dep2["leaf_indices"][0] - dep1["leaf_indices"][1] - 1) // 2 == 4)
check("pc_three_distinct_roots", len({dep1["root"], dep2["root"], wd["root"]}) == 3)
check("pc_times", [datetime.fromtimestamp(x["block_time"], timezone.utc).strftime("%H:%M:%S") for x in (dep1, dep2, wd)] == ["14:50:06", "14:54:50", "14:55:19"])

# 2. Deployed version: programdata writes bracket the case
sp = HERE / "evidence" / "solana_program"
_, last_slot = struct.unpack_from("<IQ", base64.b64decode(j(sp / "programdata_9fhQ.json")["result"]["value"]["data"][0]))
sigs = j(sp / "programdata_signatures.json")["result"]
writes = sorted(s["slot"] for s in sigs if s["err"] is None)
before = max(s for s in writes if s < wd["slot"])
after = min(s for s in writes if s > wd["slot"])
bt = {s["slot"]: s["blockTime"] for s in sigs}
check("program_last_deploy_after_case", last_slot == 427_378_345)
check("program_unchanged_11_feb_to_18_jun", (before, after) == (399_466_617, 427_378_345),
      f"{datetime.fromtimestamp(bt[before], timezone.utc).isoformat()} -> {datetime.fromtimestamp(bt[after], timezone.utc).isoformat()}")
gh = HERE / "evidence" / "github"
cmp = j(gh / "compare_0bd1889_f79b82f.json")
src = [f for f in cmp["files"] if f["filename"].startswith("anchor/programs/zkcash/src/")]
check("source_only_lib_rs_changed_since_0bd1889", [(f["filename"], f["additions"], f["deletions"]) for f in src] == [("anchor/programs/zkcash/src/lib.rs", 6, 4)])
commits = j(gh / "commits_lib_rs.json")
check("closest_commit_before_feb_deploy", [c["sha"][:7] for c in commits if c["date"] < datetime.fromtimestamp(bt[before], timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")][0] == "0bd1889")

# 3. Relay: the Depository's own log carries the id that the Solana memo carries
deps = [d for f in sorted((PREV / "polygon").glob("*.eth_getTransactionReceipt.json")) for d in deposits_from_receipt(j(f)["result"])]
fills = solana_fills(PREV / "sol" / BEN, BEN)
pairs, _, uf = match(deps, fills)
check("relay_11_links_from_chain_only", len(pairs) == 11 and not uf)
check("relay_totals", sum(p["deposit"]["amount"] for p in pairs) == 70_065_262_869 and sum(p["fill"]["lamports_to_recipient"] for p in pairs) == 856_840_698_827)
check("relay_depositors_are_the_four_proxies", {p["deposit"]["depositor"] for p in pairs} == {
    "0xcc32a117ac254fe51fd867b928e45492b1f6dc7e", "0x97e490d61b530d5078348d76143a25c43a47164d",
    "0x0a142164f48dab6448872f0abac310d03e305316", "0xd36fa21eb3fa7b1aaf97c8499253f76f82a16d48"})
check("relay_event_topic", T_ERC20 == "0x49fed1d0b752ce30eee63c7a81133f3363b532fec5d4d7dd1ccfd005de4555e1")

out = {"passed": sum(c["pass"] for c in checks), "total": len(checks), "checks": checks}
(HERE / "verification.json").write_text(json.dumps(out, indent=1))
print(f"{out['passed']}/{out['total']} checks passed")
for c in checks:
    if not c["pass"]:
        print("FAIL", c["check"], c["detail"])
sys.exit(0 if out["passed"] == out["total"] else 1)
