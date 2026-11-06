"""Offline verification of every figure in REPORT.md. Needs only this folder. Run: python3 -I verify.py"""
import hashlib, json, struct, sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "scripts"))
from keccak import keccak256, topic  # noqa: E402
from relay_onchain import T_ERC20, T_NATIVE, decode_deposit_log, deposits_from_receipt, match, solana_fills  # noqa: E402
from privacy_cash import decode_tx  # noqa: E402
import experiment_a_offline  # noqa: E402

FIX = HERE / "fixtures" / "iran-solana-beneficiary"
SOL = FIX / "evidence" / "sol"
BEN = "4dLZQynk9SZJf6PCAV73828TZHGJaf9kWgpKVUzV4Fwy"
BYBIT = "Agnhk1VsurW1ic3YNDtp3NeLTGYCiaaUwpRSKag9PdpV"
checks = []


def check(name, cond, detail=""):
    checks.append({"check": name, "pass": bool(cond), "detail": detail})


def j(p):
    return json.loads(Path(p).read_text())


# 0. fixtures are the bytes recorded from PR 27 commit cbbdd64
fx = j(HERE / "fixtures" / "FIXTURES.json")
bad = [f["fixture"] for f in fx["files"] if hashlib.sha256((FIX / "evidence" / f["fixture"]).read_bytes()).hexdigest() != f["sha256"]]
check("fixtures_match_recorded_sha256", not bad and len(fx["files"]) == 128, f"{len(fx['files'])} files, {len(bad)} mismatched")

# 1. Keccak and the Relay event topics
check("keccak_empty_vector", keccak256(b"").hex() == "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470")
check("keccak_transfer_topic", topic("Transfer(address,address,uint256)") == "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef")
check("relay_erc20_topic", T_ERC20 == "0x49fed1d0b752ce30eee63c7a81133f3363b532fec5d4d7dd1ccfd005de4555e1", T_ERC20)
check("relay_native_topic", T_NATIVE == "0x8032066556caf3967d8fec4ad22a2d9e1e9576556b2903a0fcd5b1fd201e3477", T_NATIVE)

n_logs = [l for f in sorted((FIX / "evidence" / "polygon").glob("*.eth_getTransactionReceipt.json")) for l in j(f)["result"]["logs"]
          if l["address"].lower() == "0x4cd00e387622c35bddb9b4c962c136462338bc31"]
check("relay_topic_on_all_archived_depository_logs", len(n_logs) == 15 and all(l["topics"][0] == T_ERC20 for l in n_logs), f"{len(n_logs)} logs")

# 2. Experiment A offline: chain-only join reproduces the 11 Relay API records
res = experiment_a_offline.main(FIX, HERE / "results" / "_reverify_a_offline.json")
(HERE / "results" / "_reverify_a_offline.json").unlink()
rec = j(HERE / "results" / "experiment_a_offline.json")
check("a_offline_11_matched", res["matched_orders"] == 11 and res["fills_without_origin"] == 0)
check("a_offline_totals", res["total_usdce_raw"] == 70_065_262_869 and res["total_lamports"] == 856_840_698_827)
check("a_offline_all_api_fields_agree", all(v == 11 for k, v in res["checks_passed_of_11"].items() if k not in ("calldata_tail_equals_id", "api_request_id_equals_chain_id")))
check("a_offline_calldata_tail_never_the_id", res["checks_passed_of_11"]["calldata_tail_equals_id"] == 0)
check("a_offline_api_request_id_is_not_chain_id", res["checks_passed_of_11"]["api_request_id_equals_chain_id"] == 0)
check("a_offline_rows_equal_recorded", res["rows"] == rec["rows"])

# 3. Tamper control: change one memo id, the join must lose exactly that order
fills = solana_fills(SOL / BEN, BEN)
deps = [d for f in sorted((FIX / "evidence" / "polygon").glob("*.eth_getTransactionReceipt.json")) for d in deposits_from_receipt(j(f)["result"])]
fills[0] = {**fills[0], "id": "0x" + "00" * 32}
p2, _, uf2 = match(deps, fills)
check("tamper_one_memo_drops_one_match", len(p2) == 10 and len(uf2) == 1)

# 4. Experiment A live: rescore the archived Polygon responses without network
live = j(HERE / "results" / "experiment_a_live.json")
calls = sorted((HERE / "evidence" / "polygon_live").glob("*.meta.json"))
truth = {d["id"]: d for d in deps}
found = {}
for m in calls:
    meta = j(m)
    body = (m.parent / m.name.replace(".meta.json", ".json")).read_bytes()
    assert hashlib.sha256(body).hexdigest() == meta["sha256"], m.name
    if meta["method"] == "eth_getLogs":
        for log in json.loads(body)["result"]:
            d = decode_deposit_log(log)
            if d and d["id"] in truth:
                found[d["id"]] = (log["transactionHash"].lower(), d["depositor"], d["amount"])
ok = sum(1 for i, t in truth.items() if found.get(i) == (t["tx"], t["depositor"], t["amount"]) and i in {f["id"] for f in solana_fills(SOL / BEN, BEN)})
check("a_live_11_origins_rederived_from_archived_logs", ok == 11 and live["score"]["origin_found"] == 11, f"{ok} of 11")
check("a_live_one_getlogs_window_per_fill", sum(1 for m in calls if j(m)["method"] == "eth_getLogs") == 11)
check("a_fills_paid_by_one_solver_key", {f["fee_payer"] for f in solana_fills(SOL / BEN, BEN)} == {"F7p3dFrjRTbtRp8FRF6qHLomXbKRBzpvBLjtQcfcgmNe"})
check("a_live_call_count", len(calls) == live["cost"]["rpc_calls"] == 43, f"{len(calls)} archived calls")

# 4b. Experiment A forward: from the Polygon log to the unknown Solana recipient, rescored from kept transactions
fw = j(HERE / "results" / "experiment_a_forward.json")
kept = {tx["transaction"]["signatures"][0]: tx for tx in j(HERE / "evidence" / "forward_live" / "matched_solver_transactions.json")}
sys.path.insert(0, str(HERE / "scripts"))
from experiment_a_forward import recipient_of  # noqa: E402
truth_sig = {f["id"]: f["signature"] for f in solana_fills(SOL / BEN, BEN)}
rec_ok = 0
for i, sig in truth_sig.items():
    r = recipient_of(kept[sig], i, "F7p3dFrjRTbtRp8FRF6qHLomXbKRBzpvBLjtQcfcgmNe") if sig in kept else None
    rec_ok += bool(r and BEN in r["lamport_credited"])
check("a_forward_11_recipients_recovered", rec_ok == 11 and fw["score"]["beneficiary_recipient_recovered"] == 11, f"{rec_ok} of 11")
pages = j(HERE / "evidence" / "forward_live" / "SOLVER_PAGES.json")["pages"]
check("a_forward_cost", fw["cost"]["calls"] == 40 and len(pages) == 25 and sum(p["transactions"] for p in pages) == 1767)
same_chain = [r for r in fw["rows"] if not r["found"]]
check("a_forward_two_same_chain_orders_not_on_solana", sorted(r["polygon_tx"][:10] for r in same_chain) == ["0x4562efcb", "0x580944ce"])

# 5. Privacy Cash: byte-exact decode, leaf indices, deployed version
pc = {}
for d in (SOL / BEN, SOL / BYBIT):
    for f in sorted(d.glob("gtfa_*_p*.json")):
        if f.name.endswith(".meta.json"):
            continue
        for tx in j(f)["result"]["data"]:
            for r in decode_tx(tx):
                pc[r["signature"]] = r
dep1, dep2, wd = (pc[s] for s in sorted(pc, key=lambda s: pc[s]["slot"]))
check("pc_three_transacts", len(pc) == 3)
check("pc_ext_amounts", (dep1["ext_amount"], dep2["ext_amount"], wd["ext_amount"], wd["fee"]) == (119_021_900, 12_328_800_200, -990_500_000, 9_500_000))
check("pc_withdrawal_recipient_is_bybit_deposit", wd["accounts"][7] == BYBIT and dep2["accounts"][9] == BEN, wd["accounts"][7])
check("pc_leaf_indices", (dep1["leaf_indices"], dep2["leaf_indices"], wd["leaf_indices"]) == ([346804, 346805], [346814, 346815], [346816, 346817]))
check("pc_no_pool_transact_between_deposit_and_withdrawal", wd["leaf_indices"][0] == dep2["leaf_indices"][1] + 1)
check("pc_four_pool_transacts_between_the_two_deposits", (dep2["leaf_indices"][0] - dep1["leaf_indices"][1] - 1) // 2 == 4)
check("pc_roots_all_different", len({dep1["root"], dep2["root"], wd["root"]}) == 3)
sp = HERE / "evidence" / "solana_program"
pd = j(sp / "programdata_9fhQ.json")["result"]["value"]["data"][0]
import base64  # noqa: E402
_, last_slot = struct.unpack_from("<IQ", base64.b64decode(pd))
sigs = j(sp / "programdata_signatures.json")["result"]
writes = sorted(s["slot"] for s in sigs if s["err"] is None)
before = max(s for s in writes if s < wd["slot"])
after = min(s for s in writes if s > wd["slot"])
check("pc_programdata_last_deploy_after_case", last_slot == 427_378_345 > wd["slot"])
check("pc_program_unchanged_from_11_feb_to_18_jun", (before, after) == (399_466_617, 427_378_345) and len(sigs) == 14,
      f"{datetime.fromtimestamp(next(s['blockTime'] for s in sigs if s['slot'] == before), timezone.utc).isoformat()}")

# 6. TIP completeness check
tip = j(HERE / "evidence" / "tip_summary" / "tip_summary.json")
check("tip_counts", (tip["addresses"], tip["addresses_with_tip"], tip["tip_rows"], tip["errors"]) == (125, 9, 261, 0))
check("tip_none_for_note_accounts", tip["note_accounts_queried"] == 25 and tip["note_accounts_with_tip"] == 0)
check("tip_starts_after_case", datetime.fromtimestamp(tip["earliest_tip_ts"], timezone.utc).date().isoformat() == "2026-07-24")

out = {"passed": sum(c["pass"] for c in checks), "total": len(checks), "checks": checks}
(HERE / "verification.json").write_text(json.dumps(out, indent=1))
print(f"{out['passed']}/{out['total']} checks passed")
for c in checks:
    if not c["pass"]:
        print("FAIL", c["check"], c["detail"])
sys.exit(0 if out["passed"] == out["total"] else 1)
