"""Position ids for Gnosis conditional tokens.

The arithmetic is the public alt_bn128 hash-to-curve used by the conditional
token framework: y^2 = x^3 + 3 over the BN254 base field, then
keccak256(collateral || collectionId). This file does not copy the LGPL
Solidity sources. It is an independent implementation checked against archived
Gamma token ids.
"""

from .keccak256 import keccak256

# BN254 base-field prime. y^2 = x^3 + B.
P = 21888242871839275222246405745257275088696311157297823662689037894645226208583
B = 3

# Polygon collateral used by ordinary Polymarket binary markets (USDC.e).
USDC_E = "0x2791bca1f2de4661ed88a30c99a7a9449aa84174"
# Wrapped collateral used by the Neg Risk adapter. Matching a Gamma token id
# still has to be tested; the address alone is not a proof.
NEG_RISK_WRAPPED = "0x3a3bd7bb9528e159577f7c2e685cc81a765002e2"


def _sqrt(yy):
    y = pow(yy, (P + 1) // 4, P)
    return y if (y * y) % P == yy else None


def collection_id(condition_id: str, index_set: int, parent: bytes = b"\x00" * 32) -> bytes:
    if not 1 <= index_set < 256:
        raise ValueError("index set out of range")
    condition = bytes.fromhex(condition_id.removeprefix("0x"))
    if len(condition) != 32 or len(parent) != 32:
        raise ValueError("condition id and parent must be 32 bytes")
    hashed = int.from_bytes(keccak256(condition + index_set.to_bytes(32, "big")), "big")
    odd = (hashed >> 255) != 0
    x1 = hashed
    y1 = None
    for _ in range(256):
        x1 = (x1 + 1) % P
        y1 = _sqrt((pow(x1, 3, P) + B) % P)
        if y1 is not None:
            break
    else:
        raise ValueError("no curve point")
    if (odd and y1 % 2 == 0) or ((not odd) and y1 % 2 == 1):
        y1 = P - y1
    if int.from_bytes(parent, "big") != 0:
        raise ValueError("nonzero parents are not implemented")
    if y1 % 2 == 1:
        x1 ^= 1 << 254
    return x1.to_bytes(32, "big")


def position_id(collateral: str, condition_id: str, index_set: int) -> int:
    token = bytes.fromhex(collateral.removeprefix("0x"))
    if len(token) != 20:
        raise ValueError("collateral must be a 20-byte address")
    return int.from_bytes(keccak256(token + collection_id(condition_id, index_set)), "big")
