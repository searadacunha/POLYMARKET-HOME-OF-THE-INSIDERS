"""Match Relay cross-chain orders from chain data alone, without the Relay API.

Key (read in relayprotocol/relay-settlement b2f3e0e, packages/depository/packages/ethereum-vm/src/RelayDepository.sol):
the Relay Depository emits RelayErc20Deposit(address from, address token, uint256 amount, bytes32 id) or
RelayNativeDeposit(address from, uint256 amount, bytes32 id) on the origin chain. The solver's payment on Solana
carries the same 32-byte `id` as a Memo instruction ("0x" + 64 hex). The Relay API request `id` is a different value.

Offline use: python3 -I relay_onchain.py match <polygon_receipt_dir> <solana_gtfa_dir> <solana_recipient>
Stdlib only. No network in this module except `find_origin`, which takes an injected `rpc` callable.
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script dir
from keccak import topic  # noqa: E402

DEPOSITORIES = {"0x4cd00e387622c35bddb9b4c962c136462338bc31"}  # deployments/addresses.prod.json (Polygon, Ethereum, BSC, Base...)
T_ERC20 = topic("RelayErc20Deposit(address,address,uint256,bytes32)")
T_NATIVE = topic("RelayNativeDeposit(address,uint256,bytes32)")
MEMO_PROGRAMS = {"MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr", "Memo1UhkJRfHyvLMcVucJwxXeuD728EvVP4q1HGAqTB6"}


def _words(data: str):
    h = data[2:]
    if len(h) % 64:
        raise ValueError(f"log data not word-aligned: {len(h)} hex chars")
    return [h[i:i + 64] for i in range(0, len(h), 64)]


def decode_deposit_log(log: dict):
    """One Relay Depository log -> dict, or None if the log is not a Relay deposit."""
    if log["address"].lower() not in DEPOSITORIES or not log["topics"]:
        return None
    t0 = log["topics"][0].lower()
    if t0 == T_ERC20:
        w = _words(log["data"])
        if len(w) != 4 or len(log["topics"]) != 1:
            raise ValueError("RelayErc20Deposit layout changed")  # fail closed: never guess a layout
        return {"kind": "erc20", "depositor": "0x" + w[0][24:], "token": "0x" + w[1][24:], "amount": int(w[2], 16), "id": "0x" + w[3]}
    if t0 == T_NATIVE:
        w = _words(log["data"])
        if len(w) != 3 or len(log["topics"]) != 1:
            raise ValueError("RelayNativeDeposit layout changed")
        return {"kind": "native", "depositor": "0x" + w[0][24:], "token": None, "amount": int(w[1], 16), "id": "0x" + w[2]}
    return None


def deposits_from_receipt(rc: dict, chain_id: int = 137):
    out = []
    for log in rc["logs"]:
        d = decode_deposit_log(log)
        if d:
            out.append({**d, "chain_id": chain_id, "tx": rc["transactionHash"].lower(), "log_index": int(log["logIndex"], 16),
                        "block": int(rc["blockNumber"], 16), "status": int(rc["status"], 16)})
    return out


def _keys(tx):
    ak = tx["transaction"]["message"]["accountKeys"]
    la = tx["meta"].get("loadedAddresses") or {}
    return [k["pubkey"] if isinstance(k, dict) else k for k in ak] + la.get("writable", []) + la.get("readonly", [])


def solana_fills(gtfa_dir: Path, recipient: str):
    """Transactions in an archived getTransactionsForAddress history whose memo is a 32-byte id, with what `recipient` received."""
    seen, out = set(), []
    for f in sorted(gtfa_dir.glob("gtfa_*_p*.json")):
        if f.name.endswith(".meta.json"):
            continue
        for tx in json.loads(f.read_text())["result"]["data"]:
            sig = tx["transaction"]["signatures"][0]
            if sig in seen:
                continue
            seen.add(sig)
            ids = []
            for ins in tx["transaction"]["message"]["instructions"]:
                if ins.get("programId") in MEMO_PROGRAMS:
                    m = ins.get("parsed") if isinstance(ins.get("parsed"), str) else None
                    if m and m.startswith("0x") and len(m) == 66 and all(c in "0123456789abcdef" for c in m[2:].lower()):
                        ids.append(m.lower())
            if not ids:
                continue
            if len(ids) > 1:
                raise ValueError(f"{sig}: several 32-byte memos, ambiguous fill")
            k, m = _keys(tx), tx["meta"]
            lam = {k[i]: m["postBalances"][i] - m["preBalances"][i] for i in range(len(m["preBalances"]))}
            pre = {b["accountIndex"]: b for b in m.get("preTokenBalances") or []}
            post = {b["accountIndex"]: b for b in m.get("postTokenBalances") or []}
            tok = []
            for i in set(pre) | set(post):
                b = post.get(i) or pre[i]
                d = (int(post[i]["uiTokenAmount"]["amount"]) if i in post else 0) - (int(pre[i]["uiTokenAmount"]["amount"]) if i in pre else 0)
                if d and b.get("owner") == recipient:
                    tok.append({"mint": b["mint"], "raw": d})
            out.append({"signature": sig, "slot": tx["slot"], "block_time": tx["blockTime"], "err": m["err"], "id": ids[0],
                        "fee_payer": k[0], "lamports_to_recipient": lam.get(recipient, 0), "tokens_to_recipient": tok})
    out.sort(key=lambda r: r["slot"])
    return out


def match(deposits, fills):
    """Join on the Relay id. Returns (pairs, unmatched_deposits, unmatched_fills)."""
    by_id = {}
    for d in deposits:
        by_id.setdefault(d["id"], []).append(d)
    pairs, used = [], set()
    for f in fills:
        ds = by_id.get(f["id"], [])
        if len(ds) > 1:
            raise ValueError(f"id {f['id']} has {len(ds)} deposit logs")
        if ds:
            pairs.append({"deposit": ds[0], "fill": f}); used.add(f["id"])
    return pairs, [d for d in deposits if d["id"] not in used], [f for f in fills if f["id"] not in used]


def find_origin(rpc, relay_id: str, fill_time: int, block_at, window_blocks=300, max_windows=4, depository=next(iter(DEPOSITORIES))):
    """Find the origin deposit of a fill from chain logs only.

    rpc(method, params) -> result; block_at(unix_time) -> block number at or before that time.
    `id` is not indexed, so every RelayErc20Deposit/RelayNativeDeposit log of the window is fetched and filtered locally.
    Scans windows backwards from the fill time; returns (deposit or None, calls, logs_scanned).
    """
    hi, calls, scanned = block_at(fill_time), 0, 0
    for _ in range(max_windows):
        lo = hi - window_blocks + 1
        logs = rpc("eth_getLogs", [{"address": depository, "fromBlock": hex(lo), "toBlock": hex(hi), "topics": [[T_ERC20, T_NATIVE]]}])
        calls += 1; scanned += len(logs)
        for log in logs:
            d = decode_deposit_log(log)
            if d and d["id"] == relay_id.lower():
                return {**d, "tx": log["transactionHash"].lower(), "log_index": int(log["logIndex"], 16), "block": int(log["blockNumber"], 16)}, calls, scanned
        hi = lo - 1
    return None, calls, scanned


if __name__ == "__main__":
    if sys.argv[1:2] != ["match"]:
        raise SystemExit(__doc__)
    rdir, sdir, rcpt = Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4]
    deps = [d for f in sorted(rdir.glob("*.eth_getTransactionReceipt.json")) for d in deposits_from_receipt(json.loads(f.read_text())["result"])]
    pairs, ud, uf = match(deps, solana_fills(sdir, rcpt))
    for p in pairs:
        d, f = p["deposit"], p["fill"]
        print(d["tx"], d["depositor"], d["amount"], "->", f["signature"][:16], f["lamports_to_recipient"], f["tokens_to_recipient"])
    print(len(pairs), "matched;", len(ud), "deposits without a fill to this recipient;", len(uf), "fills without an archived deposit")
