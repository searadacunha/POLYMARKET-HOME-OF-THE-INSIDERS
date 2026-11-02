"""Part A, E4. Wallet by token overlap against a Curveball null that keeps each wallet's and each token's totals. No name, no resolution."""
import json
import math
import os
import random
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import rows as R

SEED = 20261101


def matrix(rows, end, min_usd=500):
    spent = defaultdict(lambda: defaultdict(float))
    for r in rows:
        if r[4] == 'BUY' and r[8] <= end:
            spent[r[3]][r[2]] += r[5]
    return {w: {t for t, x in tokens.items() if x >= 100} for w, tokens in spent.items() if sum(tokens.values()) >= min_usd and sum(1 for x in tokens.values() if x >= 100) >= 2}


def pair_scores(m):
    n = len(m)
    df = Counter(t for tokens in m.values() for t in tokens)
    idf = {t: math.log(n / c) for t, c in df.items()}
    by_token = defaultdict(list)
    for w, tokens in m.items():
        for t in tokens:
            by_token[t].append(w)
    shared = defaultdict(lambda: [0, 0.0])
    for t, ws in by_token.items():
        ws.sort()
        for i in range(len(ws)):
            for j in range(i + 1, len(ws)):
                s = shared[(ws[i], ws[j])]
                s[0] += 1
                s[1] += idf[t]
    return shared


def curveball(m, rng, trades):
    """Keeps every wallet's and every token's total: two wallets trade tokens only one of them holds."""
    names = list(m)
    sets = [set(m[w]) for w in names]
    for _ in range(trades):
        a, b = rng.sample(range(len(sets)), 2)
        only_a, only_b = list(sets[a] - sets[b]), list(sets[b] - sets[a])
        k = min(len(only_a), len(only_b))
        if not k:
            continue
        rng.shuffle(only_a)
        rng.shuffle(only_b)
        give_a, give_b = only_a[:k], only_b[:k]
        take = rng.randint(0, k)
        sets[a] -= set(give_a[:take])
        sets[b] -= set(give_b[:take])
        sets[a] |= set(give_b[:take])
        sets[b] |= set(give_a[:take])
    return dict(zip(names, sets))


def run(rows, end, draws=200):
    m = matrix(rows, end)
    real = pair_scores(m)
    rng = random.Random(SEED)
    null_max = defaultdict(float)
    current = m
    mix = 5 * len(m)
    for _ in range(draws):
        current = curveball(current, rng, mix)
        for count, score in pair_scores(current).values():
            if score > null_max[count]:
                null_max[count] = score
    above = {p: v for p, v in real.items() if v[1] > null_max.get(v[0], 0)}
    top = sorted(((p, v) for p, v in above.items()), key=lambda kv: -kv[1][1])[:40]
    return dict(end=time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(end)), wallets=len(m), tokens=len({t for x in m.values() for t in x}), pairs_sharing=len(real), draws=draws, null_max_by_shared=dict(sorted(null_max.items())), pairs_above_null_max=len(above), top=[dict(a=p[0], b=p[1], shared=v[0], score=round(v[1], 3)) for p, v in top], max_shared=max((v[0] for v in real.values()), default=0))




def planted_beats_null(m, a, b, draws=50):
    real = pair_scores(m)
    rng = random.Random(SEED)
    best = 0.0
    current = m
    for _ in range(draws):
        current = curveball(current, rng, 5 * len(m))
        for count, score in pair_scores(current).values():
            if count == real[tuple(sorted((a, b)))][0] and score > best:
                best = score
    return real[tuple(sorted((a, b)))][1] > best
