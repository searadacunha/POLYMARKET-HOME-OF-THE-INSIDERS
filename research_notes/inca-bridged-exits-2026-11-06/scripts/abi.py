"""Minimal ABI readers (stdlib only) for the source-side bridge events read in this note."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # run with -I: import the sibling module explicitly
from keccak import keccak256  # noqa: E402

RAW = Path.home() / "Projects/Polymarket-inca-raw-20261106/raw"
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"


def topic(sig: str) -> str:
    return "0x" + keccak256(sig.encode()).hex()


# deBridge DLN: DlnSource.CreatedOrder(Order, bytes32 orderId, bytes affiliateFee, uint256 nativeFixFee,
# uint256 percentFee, uint32 referralCode, bytes metadata)
ORDER_T = "(uint64,bytes,uint256,bytes,uint256,uint256,bytes,uint256,bytes,bytes,bytes,bytes,bytes,bytes)"
DLN_CREATED = topic(f"CreatedOrder({ORDER_T},bytes32,bytes,uint256,uint256,uint32,bytes)")
# deBridge DLN destination: DlnDestination.FulfilledOrder(Order, bytes32 orderId, address sender, address unlockAuthority)
DLN_FULFILLED = topic(f"FulfilledOrder({ORDER_T},bytes32,address,address)")
# LI.FI diamond: LiFiTransferStarted(BridgeData) and BridgeToNonEVMChainBytes32(bytes32 indexed, uint256 indexed, bytes32)
LIFI_STARTED = topic("LiFiTransferStarted((bytes32,string,string,address,address,address,uint256,uint256,bool,bool))")
LIFI_NONEVM = topic("BridgeToNonEVMChainBytes32(bytes32,uint256,bytes32)")
LIFI_NONEVM_BYTES = topic("BridgeToNonEVMChain(bytes32,uint256,bytes)")
MAYAN_ORDER_CREATED = topic("OrderCreated(bytes32)")


def words(data: str):
    b = bytes.fromhex(data[2:])
    return b, [b[i:i + 32] for i in range(0, len(b), 32)]


def u(w: bytes) -> int:
    return int.from_bytes(w, "big")


def dyn_bytes(b: bytes, off: int) -> bytes:
    n = u(b[off:off + 32])
    return b[off + 32: off + 32 + n]


def decode_dln_order(b: bytes, base: int) -> dict:
    """Order tuple at byte offset `base` of `b` (offsets inside are relative to `base`)."""
    w = lambda i: b[base + 32 * i: base + 32 * (i + 1)]
    d = lambda i: dyn_bytes(b, base + u(w(i)))
    return {
        "makerOrderNonce": u(w(0)), "makerSrc": "0x" + d(1).hex(), "giveChainId": u(w(2)),
        "giveTokenAddress": "0x" + d(3).hex(), "giveAmount": u(w(4)), "takeChainId": u(w(5)),
        "takeTokenAddress": "0x" + d(6).hex(), "takeAmount": u(w(7)), "receiverDst": "0x" + d(8).hex(),
        "givePatchAuthoritySrc": "0x" + d(9).hex(), "orderAuthorityAddressDst": "0x" + d(10).hex(),
        "allowedTakerDst": "0x" + d(11).hex(), "allowedCancelBeneficiarySrc": "0x" + d(12).hex(),
        "externalCall": "0x" + d(13).hex(),
    }


def decode_dln_created(log: dict) -> dict:
    b, w = words(log["data"])
    out = decode_dln_order(b, u(w[0]))
    out["orderId"] = "0x" + w[1].hex()
    out["affiliateFee"] = "0x" + dyn_bytes(b, u(w[2])).hex()
    out["nativeFixFee"], out["percentFee"], out["referralCode"] = u(w[3]), u(w[4]), u(w[5])
    return out


def decode_dln_fulfilled(log: dict) -> dict:
    b, w = words(log["data"])
    out = decode_dln_order(b, u(w[0]))
    out["orderId"] = "0x" + w[1].hex()
    out["sender"] = "0x" + w[2][12:].hex()
    out["unlockAuthority"] = "0x" + w[3][12:].hex()
    return out


def decode_lifi_started(log: dict) -> dict:
    b, w = words(log["data"])
    base = u(w[0])
    t = lambda i: b[base + 32 * i: base + 32 * (i + 1)]
    s = lambda i: dyn_bytes(b, base + u(t(i))).decode()
    return {"transactionId": "0x" + t(0).hex(), "bridge": s(1), "integrator": s(2),
            "referrer": "0x" + t(3)[12:].hex(), "sendingAssetId": "0x" + t(4)[12:].hex(),
            "receiver": "0x" + t(5)[12:].hex(), "minAmount": u(t(6)), "destinationChainId": u(t(7)),
            "hasSourceSwaps": bool(u(t(8))), "hasDestinationCall": bool(u(t(9)))}


def load_rpc(chain_dir: str, h: str):
    d = RAW / chain_dir
    tx = json.loads((d / f"{h}.eth_getTransactionByHash.json").read_bytes())["result"]
    rc = json.loads((d / f"{h}.eth_getTransactionReceipt.json").read_bytes())["result"]
    return tx, rc


B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def b58(b: bytes) -> str:
    n, s = int.from_bytes(b, "big"), ""
    while n:
        n, r = divmod(n, 58)
        s = B58[r] + s
    return "1" * (len(b) - len(b.lstrip(b"\0"))) + s


def b58decode(s: str) -> bytes:
    n = 0
    for c in s:
        n = n * 58 + B58.index(c)
    raw = n.to_bytes((n.bit_length() + 7) // 8, "big") if n else b""
    return b"\0" * (len(s) - len(s.lstrip("1"))) + raw


if __name__ == "__main__":
    # self-checks: known Ethereum topic, base58 round trip on a 32-byte key
    assert TRANSFER == topic("Transfer(address,address,uint256)")
    k = bytes(range(32))
    assert b58decode(b58(k)) == k and b58(b"\0" + k[1:]).startswith("1")
    print("abi self-check OK", DLN_CREATED[:18], LIFI_STARTED[:18], LIFI_NONEVM[:18], MAYAN_ORDER_CREATED[:18])
