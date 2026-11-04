"""Recheck the archived Relay mapping and both on-chain receipts, without network."""
import hashlib
import json
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
ENTER = "0xea00f88768a86184a6e515238a549c171769fe7460a011d6fd0bcd48ca078ea4"
MUSD = "0xaca92e438df0b2401ff60da7e4337b687a2435da"
VAULT = "0x1c8a336051d2024e318a229d01f9f6cf96efd316"
SOURCE = "0x48ec106cf690edd58fcd6df1e8b6abfc16dab12d"
BENEFICIARY = "0xea1a3f324c5ee313bb04d9e642c39c8b29e7454b"
ROUTER = "0x0729e2a4716d9f7dd17858d5d504426d228697f7"
DEPOSITORY = "0x4cd00e387622c35bddb9b4c962c136462338bc31"
SOLVER = "0xf70da97812cb96acdf810712aa562db8dfa3dbef"
ZERO = "0x" + "0" * 40


def load(name):
    return json.loads((ROOT / name).read_text())


def transfers(receipt):
    for row in receipt["logs"]:
        topics = row["topics"]
        if len(topics) == 3 and topics[0] == TRANSFER:
            yield (row["address"].lower(), "0x" + topics[1][-40:],
                   "0x" + topics[2][-40:], int(row["data"], 16))


def main():
    for meta_path in sorted(ROOT.glob("*.meta.json")):
        meta = json.loads(meta_path.read_text())
        raw = ROOT / meta_path.name.replace(".meta.json", ".json")
        assert hashlib.sha256(raw.read_bytes()).hexdigest() == meta["sha256"], raw

    request, = load("relay_request.json")["requests"]
    origin, = request["data"]["inTxs"]
    destination, = request["data"]["outTxs"]
    eth = load("ethereum_tenderly.json")["result"]
    monad_results = {r["id"]: r for r in load("monad_receipt.json")}
    monad = monad_results[2]["result"]
    assert request["status"] == origin["status"] == destination["status"] == "success"
    assert origin["chainId"] == 1 and destination["chainId"] == 143
    assert int(monad_results[1]["result"], 16) == 143
    assert eth["status"] == monad["status"] == "0x1"
    assert origin["hash"] == eth["transactionHash"]
    assert destination["hash"] == monad["transactionHash"]
    assert int(eth["blockNumber"], 16) == origin["block"]
    assert int(monad["blockNumber"], 16) == destination["block"]
    assert (MUSD, SOURCE, DEPOSITORY, 2969568353) in set(transfers(eth))

    observed = set(transfers(monad))
    for sender, recipient in [(SOLVER, ROUTER), (ROUTER, BENEFICIARY),
                              (BENEFICIARY, VAULT)]:
        assert (MUSD, sender, recipient, 2969568353) in observed
    assert (VAULT, ZERO, BENEFICIARY, 2904308540) in observed
    enter, = [r for r in monad["logs"] if r["address"].lower() == VAULT
              and r["topics"][0] == ENTER]
    assert "0x" + enter["topics"][1][-40:] == BENEFICIARY
    assert "0x" + enter["topics"][2][-40:] == MUSD
    assert "0x" + enter["topics"][3][-40:] == BENEFICIARY
    words = enter["data"][2:]
    assert int(words[:64], 16) == 2969568353
    assert int(words[64:128], 16) == 2904308540
    assert int(monad_results[3]["result"], 16) == 6
    symbol_bytes = bytes.fromhex(monad_results[4]["result"][2:])
    offset = int.from_bytes(symbol_bytes[:32], "big")
    length = int.from_bytes(symbol_bytes[offset:offset + 32], "big")
    assert symbol_bytes[offset + 32:offset + 32 + length].decode() == "vmUSD"
    assert load("ethereum_blockscout.json")["hash"] == eth["transactionHash"]
    assert load("ethereum_blockscout.json")["status"] == "ok"
    print(json.dumps({
        "status": "VERIFIED_AGAINST_ARCHIVED_RESPONSES",
        "origin_chain": 1, "destination_chain": 143,
        "source": SOURCE, "vault_beneficiary": BENEFICIARY,
        "musd_deposited": str(Decimal(2969568353) / Decimal(10**6)),
        "vmusd_shares_minted": str(Decimal(2904308540) / Decimal(10**6)),
        "seconds_between_transactions": destination["timestamp"] - origin["timestamp"],
        "common_ownership": "NOT_ESTABLISHED",
        "current_holdings": "NOT_QUERIED"
    }, indent=2))


if __name__ == "__main__":
    main()
