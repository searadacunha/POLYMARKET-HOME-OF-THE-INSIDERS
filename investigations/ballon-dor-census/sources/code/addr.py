"""Address arithmetic with no dependency: keccak-256, EIP-55, bech32, base58, Polymarket deposit wallet (CREATE2).
Constants copied from ~/Projects/PolySentinel-flow-trace/tools/proxy_check.py, then re-tested in tests/test_addr.py against on-chain owner() reads."""
import hashlib

FACTORY = bytes.fromhex('00000000000fb5c9adea0298d729a0cb3823cc07')
TEMPLATE_OLD = bytes.fromhex('61007d3d8160233d397358ca52ebe0dadfdf531cde7062e76746de4db1eb60095155f3363d3d373d3d363d7f360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc545af43d6000803e6038573d6000fd5b3d6000f300000000000000000000000000000000000fb5c9adea0298d729a0cb3823cc07')  # before the 29/06/2026 upgrade
TEMPLATE_BEACON = bytes.fromhex('6100923d8160233d39737a18edfe055488a3128f01f563e5b479d92ffc3a60195155f3363d3d373d3d363d602036600436635c60da1b60e01b36527fa3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50545afa5036515af43d6000803e604d573d6000fd5b3d6000f300000000000000000000000000000000000fb5c9adea0298d729a0cb3823cc07')  # from 29/06/2026
RC = [0x0000000000000001, 0x0000000000008082, 0x800000000000808A, 0x8000000080008000, 0x000000000000808B, 0x0000000080000001, 0x8000000080008081, 0x8000000000008009, 0x000000000000008A, 0x0000000000000088, 0x0000000080008009, 0x000000008000000A, 0x000000008000808B, 0x800000000000008B, 0x8000000000008089, 0x8000000000008003, 0x8000000000008002, 0x8000000000000080, 0x000000000000800A, 0x800000008000000A, 0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008]
ROT = [[0, 36, 3, 41, 18], [1, 44, 10, 45, 2], [62, 6, 43, 15, 61], [28, 55, 25, 21, 56], [27, 20, 39, 8, 14]]
M = (1 << 64) - 1


def keccak(data):
    rate = 136
    msg = bytearray(data) + b'\x01' + b'\x00' * ((rate - (len(data) + 1) % rate) % rate)
    msg[-1] |= 0x80
    s = [[0] * 5 for _ in range(5)]
    for off in range(0, len(msg), rate):
        block = msg[off:off + rate]
        for i in range(rate // 8):
            s[i % 5][i // 5] ^= int.from_bytes(block[i * 8:i * 8 + 8], 'little')
        for rc in RC:
            c = [s[x][0] ^ s[x][1] ^ s[x][2] ^ s[x][3] ^ s[x][4] for x in range(5)]
            d = [c[(x + 4) % 5] ^ (((c[(x + 1) % 5] << 1) | (c[(x + 1) % 5] >> 63)) & M) for x in range(5)]
            s = [[s[x][y] ^ d[x] for y in range(5)] for x in range(5)]
            b = [[0] * 5 for _ in range(5)]
            for x in range(5):
                for y in range(5):
                    r = ROT[x][y]
                    b[y][(2 * x + 3 * y) % 5] = ((s[x][y] << r) | (s[x][y] >> (64 - r))) & M if r else s[x][y]
            s = [[b[x][y] ^ ((~b[(x + 1) % 5][y]) & b[(x + 2) % 5][y] & M) for y in range(5)] for x in range(5)]
            s[0][0] ^= rc
    return b''.join(s[i % 5][i // 5].to_bytes(8, 'little') for i in range(4))


def deposit_wallet(owner, template=TEMPLATE_BEACON):
    o = bytes.fromhex(owner[2:].lower())
    id32 = b'\x00' * 12 + o
    salt = keccak(b'\x00' * 12 + FACTORY + id32)
    return '0x' + keccak(b'\xff' + FACTORY + salt + keccak(template + id32))[12:].hex()


def eip55(address):
    a = address[2:].lower()
    h = keccak(a.encode()).hex()
    return '0x' + ''.join(c.upper() if int(h[i], 16) >= 8 else c for i, c in enumerate(a))


def eip55_status(address):
    """'valid', 'invalid' or 'no_checksum' when written all in one case, which carries no check."""
    a = address[2:]
    if len(a) != 40 or any(c not in '0123456789abcdefABCDEF' for c in a):
        return 'malformed'
    if a == a.lower() or a == a.upper():
        return 'no_checksum'
    return 'valid' if eip55(address) == address else 'invalid'


BECH32 = 'qpzry9x8gf2tvdw0s3jn54khce6mua7l'


def bech32_valid(address):
    """bc1 addresses, BIP-173 (v0) and BIP-350 (v1+)."""
    a = address.lower()
    if '1' not in a:
        return False
    hrp, data = a.rsplit('1', 1)
    try:
        vals = [BECH32.index(c) for c in data]
    except ValueError:
        return False
    gen = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3]
    chk = 1
    for v in [ord(c) >> 5 for c in hrp] + [0] + [ord(c) & 31 for c in hrp] + vals:
        top = chk >> 25
        chk = (chk & 0x1ffffff) << 5 ^ v
        for i in range(5):
            chk ^= gen[i] if (top >> i) & 1 else 0
    return chk == (1 if vals and vals[0] == 0 else 0x2bc830a3)


B58 = '123456789ABCDEFGHJKMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'


def base58_32(address):
    """A Solana address is 32 bytes in base58. Base58 has no checksum, so this only proves the shape."""
    n = 0
    for c in address:
        if c not in B58:
            return False
        n = n * 58 + B58.index(c)
    return len(n.to_bytes((n.bit_length() + 7) // 8, 'big')) + len(address) - len(address.lstrip('1')) == 32


def is_evm(a):
    return a.startswith('0x') and len(a) == 42
