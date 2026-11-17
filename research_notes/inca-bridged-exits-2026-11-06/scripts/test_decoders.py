"""Synthetic positive and negative tests of the decoders used by verify.py. python3 -I scripts/test_decoders.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from abi import (DLN_CREATED, DLN_FULFILLED, LIFI_STARTED, TRANSFER, b58, b58decode, decode_dln_created,  # noqa: E402
                 decode_dln_fulfilled, decode_lifi_started, topic)
from keccak import keccak256  # noqa: E402
import verify as V  # noqa: E402

W = lambda n: n.to_bytes(32, "big")


def enc_bytes(b: bytes) -> bytes:
    return W(len(b)) + b + b"\0" * ((32 - len(b) % 32) % 32)


def enc_order(o):
    """ABI-encodes the DLN Order tuple (static head of 14 words, dynamic bytes after)."""
    kinds = ["u", "b", "u", "b", "u", "u", "b", "u", "b", "b", "b", "b", "b", "b"]
    head, tail = b"", b""
    for k, v in zip(kinds, o):
        if k == "u":
            head += W(v)
        else:
            head += W(14 * 32 + len(tail))
            tail += enc_bytes(v)
    return head + tail


def order(receiver: bytes, take_chain: int, take_amount: int):
    return [7, bytes(20), 137, bytes.fromhex("3c499c542cef5e3811e1192ce70d8cc03d5c3359"), 10**9, take_chain, bytes(32), take_amount,
            receiver, bytes(20), receiver, b"", bytes(20), b""]


def created_log(o, oid: bytes):
    enc = enc_order(o)
    head = W(7 * 32) + oid + W(7 * 32 + len(enc)) + W(0) + W(0) + W(0) + W(7 * 32 + len(enc) + 32)
    return {"topics": [DLN_CREATED], "data": "0x" + (head + enc + enc_bytes(b"") + enc_bytes(b"")).hex()}


def main():
    ok = 0
    # known vectors
    assert keccak256(b"").hex() == "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470"; ok += 1
    assert TRANSFER == topic("Transfer(address,address,uint256)"); ok += 1
    assert b58(bytes(32)) == "1" * 32; ok += 1
    assert b58(bytes.fromhex("c6fa7af3bedbad3a3d65f36aabc97431b1bbe4c2d2f6e0e47ca60203452f5d61")) == "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"; ok += 1
    assert b58decode("J4t48znSuoXVyfytFMBCu7Y5Y4RtmCvK985EkUAZKxVe").hex().startswith("fd9525b0"); ok += 1
    # DLN CreatedOrder round trip (positive) and a different receiver (negative)
    rcv = b58decode("J4t48znSuoXVyfytFMBCu7Y5Y4RtmCvK985EkUAZKxVe")
    d = decode_dln_created(created_log(order(rcv, 7565164, 123), b"\x11" * 32))
    assert d["orderId"] == "0x" + "11" * 32 and d["takeChainId"] == 7565164 and d["takeAmount"] == 123; ok += 1
    assert b58(bytes.fromhex(d["receiverDst"][2:])) == "J4t48znSuoXVyfytFMBCu7Y5Y4RtmCvK985EkUAZKxVe"; ok += 1
    d2 = decode_dln_created(created_log(order(b"\x22" * 32, 7565164, 123), b"\x11" * 32))
    assert b58(bytes.fromhex(d2["receiverDst"][2:])) != "J4t48znSuoXVyfytFMBCu7Y5Y4RtmCvK985EkUAZKxVe"; ok += 1
    # FulfilledOrder: order, id, two addresses
    enc = enc_order(order(rcv, 1, 5))
    f = {"topics": [DLN_FULFILLED], "data": "0x" + (W(4 * 32) + b"\x33" * 32 + W(0xAB) + W(0xCD) + enc).hex()}
    df = decode_dln_fulfilled(f)
    assert df["orderId"] == "0x" + "33" * 32 and df["sender"].endswith("ab") and df["takeAmount"] == 5; ok += 1
    # truncated data must raise, not decode to zeros silently
    try:
        decode_dln_created({"topics": [DLN_CREATED], "data": "0x" + W(7 * 32).hex()})
        raise AssertionError("truncated CreatedOrder decoded")
    except (IndexError, ValueError):
        ok += 1
    except AssertionError:
        raise
    except Exception:
        ok += 1
    # LI.FI BridgeData round trip
    def s(x):
        return enc_bytes(x.encode())
    heads = [b"\x44" * 32, None, None, W(0), W(0xC4), W(0x11F1), W(777), W(1151111081099710), W(1), W(0)]
    strings = [s("mayan"), s("phantom")]
    head, tail = b"", b""
    for i, h in enumerate(heads):
        if h is None:
            head += W(10 * 32 + len(tail)); tail += strings.pop(0)
        else:
            head += h
    lf = decode_lifi_started({"topics": [LIFI_STARTED], "data": "0x" + (W(32) + head + tail).hex()})
    assert lf["bridge"] == "mayan" and lf["integrator"] == "phantom" and lf["minAmount"] == 777 and lf["destinationChainId"] == 1151111081099710; ok += 1
    # transfers(): only 3-topic Transfer logs, amounts kept exact
    rc = {"logs": [{"address": V.USDC, "topics": [TRANSFER, "0x" + "0" * 24 + "a" * 40, "0x" + "0" * 24 + "b" * 40], "data": "0x" + W(10**6).hex()},
                   {"address": V.USDC, "topics": [TRANSFER, "0x" + "0" * 24 + "a" * 40], "data": "0x" + W(5).hex()}]}
    t = V.transfers(rc)
    assert t == [(V.USDC, "0x" + "a" * 40, "0x" + "b" * 40, 10**6)]; ok += 1
    # sol_deltas(): owner lamports and token balance change; another owner's change is not counted
    tx = {"transaction": {"message": {"accountKeys": [{"pubkey": "A"}, {"pubkey": "B"}]}},
          "meta": {"preBalances": [10, 0], "postBalances": [4, 6],
                   "preTokenBalances": [{"owner": "A", "mint": "M", "uiTokenAmount": {"amount": "100"}}, {"owner": "B", "mint": "M", "uiTokenAmount": {"amount": "0"}}],
                   "postTokenBalances": [{"owner": "A", "mint": "M", "uiTokenAmount": {"amount": "40"}}, {"owner": "B", "mint": "M", "uiTokenAmount": {"amount": "60"}}]}}
    lam, tok, _ = V.sol_deltas(tx, "A")
    assert lam == -6 and tok == {"M": -60}; ok += 1
    lamb, tokb, _ = V.sol_deltas(tx, "B")
    assert lamb == 6 and tokb == {"M": 60}; ok += 1
    # cash_by_market(): sells and redemptions minus buys
    rows = [{"type": "TRADE", "side": "BUY", "usdc_size": "100", "title": "X"}, {"type": "REDEEM", "usdc_size": "150", "title": "X"},
            {"type": "DEPOSIT", "usdc_size": "999", "title": ""}]
    cm = V.cash_by_market(rows)
    assert cm["X"] == 50.0 and cm["__buys__X"] == 100.0 and "" not in cm; ok += 1
    print(f"test_decoders: {ok}/15 OK")


if __name__ == "__main__":
    main()
