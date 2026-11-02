"""Part B, after the seal of part A. Reads public accounts, resolutions and later history. Nothing here goes back into part A."""
import gzip
import hashlib
import json
import os
import random
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import rows as R
import signals as K
from registre import enregistrer

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
E = Path(ETUDE)
SEED = 20261101
UTC = lambda t: time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(t))

seal = json.loads((E / 'derived/A_seal.json').read_text())
for name, sha in seal['sha256'].items():
    if hashlib.sha256((E / name).read_bytes()).hexdigest() != sha:
        raise RuntimeError('part A differs from its seal: ' + name)
labels = json.loads((E / 'data/labels_retro.json').read_text())
G = {v: k for k, v in labels['named'].items()}
G0 = {v: k for k, v in labels['not_highlighted'].items()}
MBAPPE, YAMAL = labels['token_same'], labels['token_opposite']
rows = [r for r in R.family() if r[0] == 'M' and r[4] == 'BUY']
by_wallet = defaultdict(list)
for r in rows:
    by_wallet[r[3]].append((r[2], r[8], r[5]))
for v in by_wallet.values():
    v.sort(key=lambda x: x[1])
spent = defaultdict(lambda: defaultdict(float))
for r in rows:
    spent[r[2]][r[3]] += r[5]


def group_stats(group):
    """Pairs buying one token within 5, 15, 60 minutes; tokens shared by at least two members; part of the group's dollars in its busiest 24 hours."""
    members = [w for w in group if w in by_wallet]
    token_times = defaultdict(list)
    for w in members:
        for token, ts, _ in by_wallet[w]:
            token_times[token].append((ts, w))
    close = {5: set(), 15: set(), 60: set()}
    for token, events in token_times.items():
        events.sort()
        low = 0
        for high, (t, w) in enumerate(events):
            while events[low][0] < t - 3600:
                low += 1
            for ts, other in events[low:high]:
                if other != w:
                    pair = tuple(sorted((w, other)))
                    gap = t - ts
                    for m in close:
                        if gap <= m * 60:
                            close[m].add(pair)
    shared = sum(1 for e in token_times.values() if len({w for _, w in e}) >= 2)
    dollars = sorted((ts, usd) for w in members for _, ts, usd in by_wallet[w])
    best, low, running = 0.0, 0, 0.0
    for t, usd in dollars:
        running += usd
        while dollars[low][0] <= t - R.DAY:
            running -= dollars[low][1]
            low += 1
        best = max(best, running)
    total = sum(u for _, u in dollars)
    pairs = len(members) * (len(members) - 1) / 2
    return dict(members=len(members), pairs_5=len(close[5]), pairs_15=len(close[15]), pairs_60=len(close[60]), share_pairs_60=round(len(close[60]) / pairs, 4) if pairs else None, tokens_shared=shared, usd=round(total, 2), busiest_24h_share=round(best / total, 4) if total else None)


def percentile(value, values):
    return round(sum(1 for v in values if v <= value) / len(values), 4)


def draw(pool, size, n=2000):
    rng = random.Random(SEED)
    pool = sorted(pool)
    return [group_stats(rng.sample(pool, size)) for _ in range(n)]


named, comparators = group_stats(G), {}
comparators['non_surlignes'] = group_stats(G0)
for tag, token in (('meme_token', MBAPPE), ('token_oppose', YAMAL)):
    pool = {w for w, x in spent[token].items() if x >= 1000 and w not in G}
    size = min(len(G), len(pool))
    sims = draw(pool, size) if size >= 3 else []
    comparators[tag] = dict(pool=len(pool), size=size, draws=len(sims), named_percentile={k: percentile(named[k], [s[k] for s in sims]) for k in ('pairs_5', 'pairs_15', 'pairs_60', 'tokens_shared', 'busiest_24h_share')} if sims else None, median={k: sorted(s[k] for s in sims)[len(sims) // 2] for k in ('pairs_5', 'pairs_15', 'pairs_60', 'tokens_shared', 'busiest_24h_share')} if sims else None)
coverage = {labels['named'][w] if w in labels['named'] else w: None for w in ()}
per_wallet = {G[w]: dict(address=w, taker_buy_rows=len(by_wallet.get(w, [])), taker_buy_usd=round(sum(x[2] for x in by_wallet.get(w, [])), 2), first_buy=UTC(by_wallet[w][0][1]) if w in by_wallet else None, tokens=len({x[0] for x in by_wallet.get(w, [])})) for w in G}
(E / 'derived/B_E5.json').write_text(json.dumps(dict(named=named, comparators=comparators, per_wallet=per_wallet, note='Group selected by the press after the fact, on size and account date, and all on the same token by construction.'), ensure_ascii=False))
enregistrer(ETUDE, 'E5_group', True, len(G), 'claude', n_effectif=1, n_comparaisons=len(comparators) * 5, n_tirages=2000, sortie='derived/B_E5.json')

# E7: the 20 largest buy decisions before the article. No dated book exists: depth stays unknown.
per_token = defaultdict(list)
for r in R.family():
    if r[0] == 'M':
        per_token[r[2]].append(r)
for v in per_token.values():
    v.sort(key=lambda x: x[8])
decisions = []
for token, trs in per_token.items():
    by = defaultdict(list)
    for r in trs:
        if r[4] == 'BUY':
            by[r[3]].append((r[8], r[9], r[5]))
    for wallet, v in by.items():
        _, dec = K.decisions(v)
        for ts, usd in dec:
            decisions.append((usd, ts, token, wallet))
decisions.sort(reverse=True)
cat = R.catalog()
top = []
for usd, ts, token, wallet in decisions[:20]:
    trs = per_token[token]
    before = [r for r in trs if r[8] < ts]
    during = [r for r in trs if ts <= r[8] <= ts + 120 and r[3] == wallet and r[4] == 'BUY']
    after = [r for r in trs if ts + 120 < r[8] <= ts + 420]
    day_before = sum(r[5] for r in before if r[8] >= ts - R.DAY)
    paid = sum(r[5] for r in during) / max(sum(r[6] for r in during), 1e-9)
    top.append(dict(utc=UTC(ts), usd=round(usd, 2), wallet=wallet, named=G.get(wallet), question=cat.get(token, ('', '', ''))[1], outcome=cat.get(token, ('', '', ''))[2], price_before=before[-1][7] if before else None, average_paid=round(paid, 4), price_5min_after=after[-1][7] if after else None, volume_24h_before=round(day_before, 2), multiple_of_24h_volume=round(usd / day_before, 2) if day_before else None))
(E / 'derived/B_E7.json').write_text(json.dumps(top, ensure_ascii=False))
enregistrer(ETUDE, 'E7_price', True, len(top), 'claude', n_effectif=1, n_comparaisons=len(top), sortie='derived/B_E7.json')

# Who was in each part-A alert, and how did those tokens end? Read only now.
outcome = {}
for item in json.loads((R.S / 'ballon_2026_20261030/data/catalog_refreshed.json').read_text())['events']:
    for m in item['event']['markets']:
        tokens, prices = m.get('clobTokenIds'), m.get('outcomePrices')
        tokens = json.loads(tokens) if isinstance(tokens, str) else tokens
        prices = json.loads(prices) if isinstance(prices, str) else prices
        for t, p in zip(tokens or [], prices or []):
            outcome[t] = float(p)
a = json.loads((E / 'derived/A_E1.json').read_text())
review = []
for token, v in a['e1']['M']['a0'].items():
    review.append(dict(utc=v['utc'], question=v.get('question'), outcome=v.get('outcome'), n=v['n'], u=v['u'], price_30_oct=outcome.get(token), named_members=sorted(G[w] for w in v['members'] if w in G), others=[w for w in v['members'] if w not in G]))
review.sort(key=lambda x: x['utc'])
g = json.loads((E / 'derived/A_E1G.json').read_text())
review_g = {name: [dict(rank=x['rank'], n=x['n'], u=x['u'], universe=x['universe'], event=x.get('event'), question=x.get('question'), outcome=x.get('outcome'), named_members=sorted(G[w] for w in x['members'] if w in G)) for x in rows_ if x['universe'] != 'G'] for name, rows_ in g['ranks'].items()}
(E / 'derived/B_review.json').write_text(json.dumps(dict(alerts_M=review, census_family_rows=review_g), ensure_ascii=False))
enregistrer(ETUDE, 'B_review_alerts', True, len(review), 'claude', n_effectif=1, n_comparaisons=len(review), sortie='derived/B_review.json')
print(json.dumps(dict(named=named, comparators=comparators), ensure_ascii=False)[:1800])
