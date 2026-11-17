"""Historical Merkle roots of a Privacy Cash pool from current Merkle paths, without rebuilding the tree.

The pool's tree is append-only (merkle_tree.rs, `append`): a node whose leaves are all below n
never changes after state n, and a node whose leaves are all at or above n was the zero value
then. So the root R(n) of the tree holding leaves 0..n-1 needs only, at each level, the left
sibling of the path of leaf n-1 when that path goes right, and the zero value when it goes left.
Those left siblings are complete subtrees, and current Merkle paths of nearby leaves contain them.
Each append pushes one root into a history of 100 (`root_history`), so R(n) for every n is a root
the program may accept for a while.

Input: paths as returned by the pool's public relayer (`/merkle/proofv2`), each checked here
against the current root before use; the current root is itself checked against the chain by the
caller. Standard library only; Poseidon from poseidon.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from poseidon import hash2  # noqa: E402

HEIGHT = 26


def zeros(height=HEIGHT):
    z = [0]
    for _ in range(height):
        z.append(hash2(z[-1], z[-1]))
    return z


def fold(index, leaf, elements, indices):
    """Root of a current path; also every (level, position) -> value it reveals."""
    known, cur = {(0, index): leaf}, leaf
    for lv, (sib, bit) in enumerate(zip(elements, indices)):
        pos = index >> lv
        if (pos & 1) != bit:
            raise ValueError(f"path index bit {lv} disagrees with leaf index {index}")
        known[(lv, pos ^ 1)] = sib
        cur = hash2(sib, cur) if bit else hash2(cur, sib)
        known[(lv + 1, pos >> 1)] = cur
    return cur, known


def root_at(n, known, z, height=HEIGHT):
    """R(n), or None if the paths given do not reveal the nodes it needs.

    Start at the lowest level whose node holding leaf n-1 is known and complete at state n,
    then go up: left sibling from `known` when the node is a right child, zero otherwise.
    """
    for l0 in range(height + 1):
        x = (n - 1) >> l0
        if (l0, x) in known and ((x + 1) << l0) <= n:
            cur = known[(l0, x)]
            break
    else:
        return None
    for lv in range(l0, height):
        x = (n - 1) >> lv
        if x & 1:
            left = known.get((lv, x - 1))
            if left is None:
                return None
            cur = hash2(left, cur)
        else:
            cur = hash2(cur, z[lv])
    return cur


def self_check():
    """Synthetic tree of 13 leaves, height 5: every computable R(n) equals a full rebuild. Returns those n."""
    import random
    rng = random.Random(1)
    H, z = 5, zeros(5)
    leaves = [rng.randrange(1, 2 ** 200) for _ in range(13)]

    def full_root(ls):
        level = ls + [z[0]] * (2 ** H - len(ls))
        for _ in range(H):
            level = [hash2(level[2 * k], level[2 * k + 1]) for k in range(len(level) // 2)]
        return level[0]

    def path(ls, i):
        level, els, idx = ls + [z[0]] * (2 ** H - len(ls)), [], []
        for lv in range(H):
            pos = i >> lv
            els.append(level[pos ^ 1]); idx.append(pos & 1)
            level = [hash2(level[2 * k], level[2 * k + 1]) for k in range(len(level) // 2)]
        return els, idx
    now, known = full_root(leaves), {}
    for i in (12, 11, 6):
        e, ix = path(leaves, i)
        r, k = fold(i, leaves[i], e, ix)
        assert r == now
        known.update(k)
    done = []
    for n in range(1, 14):
        v = root_at(n, known, z, H)
        if v is not None:
            assert v == full_root(leaves[:n]), n
            done.append(n)
    return done


if __name__ == "__main__":
    print("self-check: R(n) recomputed for n =", self_check(), "all equal to a full rebuild")
