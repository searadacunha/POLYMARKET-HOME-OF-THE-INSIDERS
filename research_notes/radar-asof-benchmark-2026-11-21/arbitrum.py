"""Capture and verify the intermediate Arbitrum USDC legs of the frozen Relay screen."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from decimal import Decimal
from functools import partial
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
RPC = "https://gateway.tenderly.co/public/arbitrum"
USDC = "0xaf88d065e77c8cc2239327c5edb3a432268e5831"
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
LOG_FIELDS = ("address", "topics", "data", "logIndex", "blockNumber", "blockHash", "transactionHash", "removed")


def topic(address):
    return "0x" + address[2:].lower().zfill(64)


def compact(log):
    return {k: log[k] for k in LOG_FIELDS if k in log}


def rpc(provider, method, params):
    data = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    try:
        with urlopen(Request(provider, data=data, headers={"Content-Type": "application/json", "User-Agent": "Polymarket-public-research/1"}), timeout=15) as response:
            raw = response.read()
        envelope = json.loads(raw)
        capture = {"sha256_raw": hashlib.sha256(raw).hexdigest()}
        if "error" in envelope:
            return {**capture, "error": envelope["error"]}
        result = envelope["result"]
        if result is None:
            return {**capture, "error": "no result"}
        if method == "eth_getTransactionReceipt":
            result = {**{k: result[k] for k in ("transactionHash", "blockHash", "blockNumber", "status")},
                      "logs": [compact(l) for l in result["logs"]]}
        elif method == "eth_getBlockByNumber":
            result = {k: result[k] for k in ("number", "hash", "timestamp")}
        elif method == "eth_getLogs":
            result = [compact(l) for l in result]
        return {**capture, "result": result}
    except (OSError, ValueError, KeyError) as e:
        return {"error": str(e)}


def capture(pair, provider=RPC):
    request = partial(rpc, provider)
    via = pair["via"]
    out = {"chain": request("eth_chainId", [])}
    receipts = [request("eth_getTransactionReceipt", [pair[k]]) for k in ("arrival_tx", "departure_tx")]
    out["receipts"] = receipts
    if not all("result" in r for r in receipts):
        return out
    a, b = (int(r["result"]["blockNumber"], 16) for r in receipts)
    out["blocks"] = [request("eth_getBlockByNumber", [hex(h), False]) for h in (a, b)]
    out["decimals"] = request("eth_call", [{"to": USDC, "data": "0x313ce567"}, hex(a)])
    balance = {"to": USDC, "data": "0x70a08231" + topic(via)[2:]}
    out["balances"] = [request("eth_call", [balance, hex(h)]) for h in (a - 1, b)]
    window = {"fromBlock": hex(a), "toBlock": hex(b), "address": USDC}
    out["transfers"] = [request("eth_getLogs", [{**window, "topics": t}]) for t in
                        ([TRANSFER, None, topic(via)], [TRANSFER, topic(via)])]
    return out


def key(log):
    return (log["blockHash"].lower(), log["transactionHash"].lower(), int(log["logIndex"], 16))


def verify(pair, data):
    result = {"via": pair["via"], "orders": [pair["upstream_order"], pair["downstream_order"]],
              "tx": [pair["arrival_tx"], pair["departure_tx"]], "receipt_pair": False, "balance_reconciled": False}
    if (len(data.get("receipts", [])) != 2 or len(data.get("blocks", [])) != 2 or
            any(v.get("result") is None for v in [data.get("chain", {}), data.get("decimals", {}), *data["receipts"], *data["blocks"]])):
        return result
    if int(data["chain"]["result"], 16) != 42161 or int(data["decimals"]["result"], 16) != 6:
        raise ValueError("wrong chain or token decimals")
    expected_amounts = [Decimal(pair[k]) * 10**6 for k in ("arrived", "departed")]
    times, numbers, matches = [], [], []
    for i, (entry, header, tx, amount) in enumerate(zip(data["receipts"], data["blocks"], result["tx"], expected_amounts, strict=True)):
        receipt, block = entry["result"], header["result"]
        if (receipt["transactionHash"].lower() != tx or int(receipt["status"], 16) != 1 or
                receipt["blockHash"] != block["hash"] or receipt["blockNumber"] != block["number"]):
            raise ValueError("unexpected receipt or block")
        times.append(int(block["timestamp"], 16))
        numbers.append(int(block["number"], 16))
        logs = [l for l in receipt["logs"] if l["address"].lower() == USDC and len(l["topics"]) == 3
                and l["topics"][0] == TRANSFER and l["topics"][2-i].lower() == topic(pair["via"])
                and int(l["data"], 16) == amount and l["transactionHash"].lower() == tx
                and l["blockHash"] == block["hash"] and l["blockNumber"] == block["number"] and not l.get("removed")]
        if len(logs) != 1:
            return result
        matches.append(logs[0])
    expected_times = [int(datetime.fromisoformat(pair[k]).timestamp()) for k in ("arrival_utc", "departure_utc")]
    if numbers[0] >= numbers[1] or times[0] >= times[1] or times != expected_times:
        return result
    result.update(receipt_pair=True, chain_seconds=times[1]-times[0], blocks=numbers,
                  amount_atomic=[str(x.to_integral_exact()) for x in expected_amounts],
                  log_indices=[key(l)[2] for l in matches])
    if (len(data.get("balances", [])) != 2 or len(data.get("transfers", [])) != 2 or
            any(v.get("result") is None for v in data["balances"] + data["transfers"])):
        return result
    balances = [int(v["result"], 16) for v in data["balances"]]
    window = [l for v in data["transfers"] for l in v["result"]]
    result.update(balance_before_after=balances, transfer_logs_in_window=len(window))
    result["balance_reconciled"] = (balances == [0, 0] and expected_amounts[0] == expected_amounts[1]
                                    and len(window) == 2 and sorted(matches, key=key) == sorted(window, key=key))
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--collect", type=Path, help="write new RPC observations to this file")
    ap.add_argument("--provider", choices=(RPC, "https://arbitrum-one-rpc.publicnode.com", "https://arbitrum.drpc.org"),
                    default=RPC, help="public Arbitrum endpoint used with --collect")
    args = ap.parse_args()
    pairs = json.loads((HERE / "cases.json").read_text())["relay"]["candidates_24h"]
    if args.collect:
        with ThreadPoolExecutor(3) as pool:
            rows = list(pool.map(partial(capture, provider=args.provider), pairs))
        envelope = {"observed_utc": datetime.now(timezone.utc).isoformat(), "provider": args.provider, "rows": rows}
        with args.collect.open("x") as f:
            json.dump(envelope, f, indent=2)
            f.write("\n")
    else:
        envelope = json.loads((HERE / "arbitrum_receipts.json").read_text())
    print(json.dumps([verify(pair, d) for pair, d in zip(pairs, envelope["rows"], strict=True)], indent=2))


if __name__ == "__main__":
    main()
