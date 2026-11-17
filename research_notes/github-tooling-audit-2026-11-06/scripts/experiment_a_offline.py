"""Experiment A (offline): chain-only Relay matching vs the archived Relay API records of PR 27.

python3 -I experiment_a_offline.py <pr27_beneficiary_note_dir> <out.json>
Reads only archived files. Asserts every comparison and writes the measurements.
"""
import json, resource, sys, time, tracemalloc
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from relay_onchain import deposits_from_receipt, solana_fills, match  # noqa: E402

USDCE = "0x2791bca1f2de4661ed88a30c99a7a9449aa84174"
DEPOSITORY = "0x4cd00e387622c35bddb9b4c962c136462338bc31"
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
BENEFICIARY = "4dLZQynk9SZJf6PCAV73828TZHGJaf9kWgpKVUzV4Fwy"


def main(note: Path, out: Path):
    ev = note / "evidence"
    t0 = time.perf_counter(); tracemalloc.start()
    receipts = {f.name.split(".")[0]: json.loads(f.read_text())["result"] for f in sorted((ev / "polygon").glob("*.eth_getTransactionReceipt.json"))}
    txs = {f.name.split(".")[0]: json.loads(f.read_text())["result"] for f in sorted((ev / "polygon").glob("*.eth_getTransactionByHash.json"))}
    deps = [d for rc in receipts.values() for d in deposits_from_receipt(rc)]
    fills = solana_fills(ev / "sol" / BENEFICIARY, BENEFICIARY)
    pairs, ud, uf = match(deps, fills)
    elapsed = time.perf_counter() - t0
    _, peak = tracemalloc.get_traced_memory(); tracemalloc.stop()

    api = {}
    for f in sorted((ev / "http").glob("relay_*.json")):
        if f.name.endswith(".meta.json"):
            continue
        for r in json.loads(f.read_text()).get("requests", []):
            if r["recipient"] == BENEFICIARY:
                api[r["data"]["inTxs"][0]["hash"].lower()] = r

    rows, checks = [], {}
    for p in pairs:
        d, fl = p["deposit"], p["fill"]
        r = api.get(d["tx"])
        rc, tx = receipts[d["tx"]], txs[d["tx"]]
        erc20 = [int(l["data"], 16) for l in rc["logs"] if l["address"].lower() == USDCE and l["topics"][0] == TRANSFER
                 and "0x" + l["topics"][2][-40:] == DEPOSITORY]
        rows.append({
            "polygon_tx": d["tx"], "log_index": d["log_index"], "depositor": d["depositor"], "token": d["token"], "amount_raw": d["amount"],
            "relay_id": d["id"], "solana_signature": fl["signature"], "lamports_to_beneficiary": fl["lamports_to_recipient"],
            "solver_fee_payer": fl["fee_payer"], "seconds_deposit_to_fill": None,
            "api_record_found": r is not None,
            "api_user_equals_depositor": bool(r) and r["user"].lower() == d["depositor"],
            "api_outtx_equals_fill": bool(r) and r["data"]["outTxs"][0]["hash"] == fl["signature"],
            "usdce_transfer_to_depository_equals_amount": erc20 == [d["amount"]],
            "calldata_tail_equals_id": "0x" + tx["input"][-64:] == d["id"],
            "api_request_id_equals_chain_id": bool(r) and r["id"].lower() == d["id"],
            "status_ok": d["status"] == 1 and fl["err"] is None,
        })
    for k in ("api_record_found", "api_user_equals_depositor", "api_outtx_equals_fill", "usdce_transfer_to_depository_equals_amount", "status_ok"):
        checks[k] = sum(r[k] for r in rows)
        assert checks[k] == len(rows) == 11, (k, checks[k])
    checks["calldata_tail_equals_id"] = sum(r["calldata_tail_equals_id"] for r in rows)
    checks["api_request_id_equals_chain_id"] = sum(r["api_request_id_equals_chain_id"] for r in rows)
    assert len(api) == 11 and set(api) == {r["polygon_tx"] for r in rows}, "chain-only set differs from the API set"
    assert not uf, "a fill to the beneficiary has no archived origin deposit"
    usdce = sum(r["amount_raw"] for r in rows)
    lam = sum(r["lamports_to_beneficiary"] for r in rows)
    assert usdce == 70_065_262_869 and lam == 856_840_698_827, (usdce, lam)
    by_dep = {}
    for r in rows:
        by_dep.setdefault(r["depositor"], [0, 0, 0]); x = by_dep[r["depositor"]]; x[0] += 1; x[1] += r["amount_raw"]; x[2] += r["lamports_to_beneficiary"]
    res = {"experiment": "A-offline", "inputs": {"polygon_receipts": len(receipts), "solana_history_signatures_with_relay_memo": len(fills),
                                                 "api_records_for_beneficiary": len(api)},
           "matched_orders": len(pairs), "deposits_to_other_recipients": len(ud), "fills_without_origin": len(uf),
           "checks_passed_of_11": checks, "total_usdce_raw": usdce, "total_lamports": lam,
           "per_depositor": {k: {"orders": v[0], "usdce_raw": v[1], "lamports": v[2]} for k, v in by_dep.items()},
           "cost": {"network_requests": 0, "seconds": round(elapsed, 3), "python_peak_bytes": peak,
                    "process_maxrss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},
           "rows": rows}
    out.write_text(json.dumps(res, indent=1))
    return res


if __name__ == "__main__":
    r = main(Path(sys.argv[1]), Path(sys.argv[2]))
    print(json.dumps({k: v for k, v in r.items() if k != "rows"}, indent=1))
