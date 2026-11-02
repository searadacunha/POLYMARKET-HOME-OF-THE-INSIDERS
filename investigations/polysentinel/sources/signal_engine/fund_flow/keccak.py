"""Keccak-256 and CREATE2, in the standard library's absence. hashlib's sha3_256 is a different padding."""
_RC = [0x0000000000000001, 0x0000000000008082, 0x800000000000808A, 0x8000000080008000, 0x000000000000808B, 0x0000000080000001, 0x8000000080008081, 0x8000000000008009,
       0x000000000000008A, 0x0000000000000088, 0x0000000080008009, 0x000000008000000A, 0x000000008000808B, 0x800000000000008B, 0x8000000000008089, 0x8000000000008003,
       0x8000000000008002, 0x8000000000000080, 0x000000000000800A, 0x800000008000000A, 0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008]
_ROT = [[0, 36, 3, 41, 18], [1, 44, 10, 45, 2], [62, 6, 43, 15, 61], [28, 55, 25, 21, 56], [27, 20, 39, 8, 14]]
_MASK = (1 << 64) - 1


def _rol(x, n):
    return ((x << n) | (x >> (64 - n))) & _MASK if n else x


def _permute(a):
    for rc in _RC:
        c = [a[x][0] ^ a[x][1] ^ a[x][2] ^ a[x][3] ^ a[x][4] for x in range(5)]
        d = [c[(x + 4) % 5] ^ _rol(c[(x + 1) % 5], 1) for x in range(5)]
        a = [[a[x][y] ^ d[x] for y in range(5)] for x in range(5)]
        b = [[0] * 5 for _ in range(5)]
        for x in range(5):
            for y in range(5):
                b[y][(2 * x + 3 * y) % 5] = _rol(a[x][y], _ROT[x][y])
        a = [[b[x][y] ^ (~b[(x + 1) % 5][y] & b[(x + 2) % 5][y]) & _MASK for y in range(5)] for x in range(5)]
        a[0][0] ^= rc
    return a


def keccak256(data):
    rate = 136
    padded = bytearray(data) + b'\x01' + b'\x00' * ((rate - (len(data) + 1) % rate) % rate)
    padded[-1] |= 0x80
    a = [[0] * 5 for _ in range(5)]
    for start in range(0, len(padded), rate):
        block = padded[start:start + rate]
        for i in range(rate // 8):
            a[i % 5][i // 5] ^= int.from_bytes(block[i * 8:i * 8 + 8], 'little')
        a = _permute(a)
    return b''.join(a[i % 5][i // 5].to_bytes(8, 'little') for i in range(4))


def topic(signature):
    return '0x' + keccak256(signature.encode()).hex()


def selector(signature):
    return '0x' + keccak256(signature.encode())[:4].hex()


def create2(deployer, salt, init_code_hash):
    return '0x' + keccak256(b'\xff' + bytes.fromhex(deployer[2:]) + salt + init_code_hash)[12:].hex()


def word(address):
    return bytes(12) + bytes.fromhex(address[2:].lower())
