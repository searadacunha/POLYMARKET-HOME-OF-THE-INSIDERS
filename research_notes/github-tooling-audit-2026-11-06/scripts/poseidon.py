"""Poseidon over BN254, circom parameters (x^5, R_F = 8, t = 3 -> R_P = 57), standard library only.

Constants are generated as in the Poseidon reference script (generate_parameters_grain.sage):
an 80-bit Grain LFSR seeded with the parameters, self-shrinking output, round constants by
rejection sampling below p, then a Cauchy MDS matrix from 2t further samples. Nothing is copied
from a library; the result is checked against the circomlib test vector poseidon([1, 2]).

    python3 -I poseidon.py     # self-check
"""
from functools import lru_cache

P = 21888242871839275222246405745257275088548364400416034343698204186575808495617  # BN254 scalar field
R_F, ALPHA = 8, 5
R_P = {2: 56, 3: 57, 4: 56, 5: 60}  # circom's table, indexed by t


def _grain(t, rf, rp, n=254):
    bits = [int(b) for b in format(1, "02b") + format(0, "04b") + format(n, "012b") + format(t, "012b")
            + format(rf, "010b") + format(rp, "010b")] + [1] * 30

    def step():
        b = bits[62] ^ bits[51] ^ bits[38] ^ bits[23] ^ bits[13] ^ bits[0]
        bits.pop(0); bits.append(b)
        return b
    for _ in range(160):
        step()
    while True:  # self-shrinking: a pair (1, b) outputs b, a pair (0, b) outputs nothing
        if step() == 1:
            yield step()
        else:
            step()


def _field(gen, n=254):
    v = 0
    for _ in range(n):
        v = (v << 1) | next(gen)
    return v


@lru_cache(maxsize=None)
def params(t):
    rp = R_P[t]
    g = _grain(t, R_F, rp)
    consts = []
    while len(consts) < (R_F + rp) * t:
        v = _field(g)
        if v < P:
            consts.append(v)
    while True:
        xs_ys = [_field(g) % P for _ in range(2 * t)]
        if len(set(xs_ys)) != 2 * t:
            continue
        xs, ys = xs_ys[:t], xs_ys[t:]
        if any((x + y) % P == 0 for x in xs for y in ys):
            continue
        mds = [[pow(x + y, P - 2, P) for y in ys] for x in xs]
        return consts, mds, rp


def poseidon(inputs):
    t = len(inputs) + 1
    consts, mds, rp = params(t)
    s = [0] + [int(x) % P for x in inputs]
    for r in range(R_F + rp):
        s = [(v + consts[r * t + i]) % P for i, v in enumerate(s)]
        if r < R_F // 2 or r >= R_F // 2 + rp:
            s = [pow(v, ALPHA, P) for v in s]
        else:
            s[0] = pow(s[0], ALPHA, P)
        s = [sum(m * v for m, v in zip(row, s)) % P for row in mds]
    return s[0]


def hash2(left: int, right: int) -> int:
    return poseidon([left, right])


if __name__ == "__main__":
    got = poseidon([1, 2])
    want = 7853200120776062878684798364095072458815029376092732009249414926327459813530
    print("poseidon([1,2])", got, "OK" if got == want else "MISMATCH")
    assert got == want
