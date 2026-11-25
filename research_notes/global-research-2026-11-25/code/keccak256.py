"""Keccak-256 (not NIST SHA3). Round constants come from the FIPS 202 LFSR."""

_MASK = (1 << 64) - 1


def _rotl(x, n):
    n %= 64
    return ((x << n) | (x >> (64 - n))) & _MASK


def _rc_bit(t):
    if t % 255 == 0:
        return 1
    r = [1, 0, 0, 0, 0, 0, 0, 0]
    for _ in range(t % 255):
        r = [0] + r
        r[0] ^= r[8]
        r[4] ^= r[8]
        r[5] ^= r[8]
        r[6] ^= r[8]
        r = r[:8]
    return r[0]


def _round_constants():
    out = []
    for ir in range(24):
        rc = 0
        for j in range(7):
            rc |= _rc_bit(j + 7 * ir) << ((1 << j) - 1)
        out.append(rc)
    return out


# rot[x][y], Keccak rotation offsets.
_ROT = (
    (0, 36, 3, 41, 18),
    (1, 44, 10, 45, 2),
    (62, 6, 43, 15, 61),
    (28, 55, 25, 21, 56),
    (27, 20, 39, 8, 14),
)
_RC = _round_constants()


def _permute(a):
    for rc in _RC:
        c = [a[x][0] ^ a[x][1] ^ a[x][2] ^ a[x][3] ^ a[x][4] for x in range(5)]
        d = [c[(x - 1) % 5] ^ _rotl(c[(x + 1) % 5], 1) for x in range(5)]
        for x in range(5):
            for y in range(5):
                a[x][y] ^= d[x]
        b = [[0] * 5 for _ in range(5)]
        for x in range(5):
            for y in range(5):
                b[y][(2 * x + 3 * y) % 5] = _rotl(a[x][y], _ROT[x][y])
        for x in range(5):
            for y in range(5):
                a[x][y] = b[x][y] ^ ((~b[(x + 1) % 5][y]) & b[(x + 2) % 5][y] & _MASK)
        a[0][0] = (a[0][0] ^ rc) & _MASK


def keccak256(data: bytes) -> bytes:
    rate = 136
    state = [[0] * 5 for _ in range(5)]
    q = rate - (len(data) % rate)
    padded = data + (b"\x81" if q == 1 else b"\x01" + b"\x00" * (q - 2) + b"\x80")
    for off in range(0, len(padded), rate):
        block = padded[off:off + rate]
        for i in range(rate // 8):
            lane = int.from_bytes(block[i * 8:(i + 1) * 8], "little")
            state[i % 5][i // 5] ^= lane
        _permute(state)
    out = bytearray()
    while len(out) < 32:
        for i in range(rate // 8):
            out += state[i % 5][i // 5].to_bytes(8, "little")
            if len(out) >= 32:
                break
        if len(out) < 32:
            _permute(state)
    return bytes(out[:32])
