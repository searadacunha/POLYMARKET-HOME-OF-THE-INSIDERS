"""Positive and negative controls on synthetic tables, through the study's own functions and verdict. Writes controles/controles_positifs.md. No real data."""
import json
import os
import random
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib_bursts as lib
from registre import enregistrer

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = Path(ETUDE) / 'controles'
WINDOWS = (5, 30, 300, 3600)
MARKETS = 600
NULL_DRAWS = 199  # 499 on real data: 199 still resolves the threshold here


def market(rng, m, lift, coordinated, span, crowd, popular_win, news_win):
    """One market, one token. `coordinated`: share of markets with a planted group. `popular_win`: crowded tokens win more, with no alignment: the trap H1S exists for."""
    price = rng.choice((.05, .08, .12, .15, .22, .3))
    start = 1_700_000_000
    n = rng.randint(*crowd)
    popular = popular_win and rng.random() < .3
    if popular:
        n *= 4
        span = span // 4
    rows = [dict(wallet=f'w{m}_{i}', side='BUY', token=f't{m}', size=rng.uniform(150, 3000) / price, price=price * rng.uniform(.9, 1.1), ts=start + rng.randint(0, span), seq=i) for i in range(n)]
    news = news_win and rng.random() < .3
    if news:  # entrants pile onto one news day, and the token wins: no alignment is planted
        day = start + rng.randint(0, span) // 86400 * 86400
        rows = [dict(r, ts=day + rng.randint(0, 21600)) for r in rows] + [dict(rows[0], wallet=f'n{m}_{i}', ts=day + rng.randint(0, 21600), seq=n + i) for i in range(n * 3)]
    planted = rng.random() < coordinated
    if planted:
        at = start + rng.randint(100, max(101, span - 100))
        rows += [dict(wallet=f'p{m}_{i}', side='BUY', token=f't{m}', size=rng.uniform(500, 5000) / price, price=price, ts=at + rng.randint(0, 3), seq=n + i) for i in range(rng.randint(3, 6))]
    p_win = min(1, price + (lift if planted else 0) + (popular_win if popular else 0) + (news_win if news else 0))
    return rows, int(rng.random() < p_win), f'g{m // 2}', ('VALID' if m % 2 else 'TEST')


def table(seed, lift, coordinated, span=864000, crowd=(15, 60), popular_win=0.0, news_win=0.0):
    rng = random.Random(seed)
    bursts, entrants = [], []
    for m in range(MARKETS):
        rows, win, group, split = market(rng, m, lift, coordinated, span, crowd, popular_win, news_win)
        items, history = lib.entrants(rows, {})
        items = sorted(items, key=lambda x: x['ts'])
        token = f't{m}'
        in_burst = {w: lib.bursts(items, w, history[token]) for w in lib.WINDOWS}
        common = dict(condition=f'c{m}', token=token, group=group, split=split, win=win, truncated=0, volume=1, closed=0)
        for w, (events, _) in in_burst.items():
            bursts += [dict(common, kind='burst', window=w, ts=e['ts'], vwap=e['vwap'], fresh_share=e['fresh_share'], shock=e['shock']) for e in events]
        entrants += [dict(common, kind='entrant', ts=e['ts'], price=e['price'], usd=e['usd'], fresh=e['fresh'], burst_windows=[w for w, (_, members) in in_burst.items() if i in members]) for i, e in enumerate(items)]
    lib.add_crowd(bursts, entrants)
    return bursts, entrants


def run(seed, window, tables, **kw):
    bursts, entrants = tables.setdefault((seed, json.dumps(kw, sort_keys=True)), table(seed, **kw))
    primary = lib.compare(bursts, entrants, window, draws=1000, seed=seed)
    valid = lib.compare(bursts, entrants, window, lambda r: r['split'] == 'VALID', lambda r: r['split'] == 'VALID', draws=200, seed=seed)
    test = lib.compare(bursts, entrants, window, lambda r: r['split'] == 'TEST', lambda r: r['split'] == 'TEST', draws=200, seed=seed)
    placebo = lib.label_placebo(bursts, entrants, window, draws=500, seed=seed)
    count = lib.h2_test(entrants, window, draws=NULL_DRAWS, seed=seed)
    return dict(primary=primary, placebo=placebo, count=count, verdict=lib.verdict(primary, valid, test, placebo, count))


SCENARIOS = (('real null: groups planted, no information', dict(lift=0.0, coordinated=.3)), ('real null: independent wallets, dense enough for chance bursts', dict(lift=0.0, coordinated=0.0, span=7200, crowd=(40, 90))), ('trap: crowded tokens win more, no alignment', dict(lift=0.0, coordinated=0.0, span=86400, crowd=(10, 25), popular_win=.25)), ('trap: news day, entrants pile on, token wins, no alignment', dict(lift=0.0, coordinated=0.0, news_win=.25)), ('combined trap: crowded tokens win more, plus groups with no information', dict(lift=0.0, coordinated=.3, span=86400, crowd=(10, 25), popular_win=.25)), ('combined trap: news day wins, plus groups with no information', dict(lift=0.0, coordinated=.3, news_win=.25)), ('medium: planted groups at price plus 0.10', dict(lift=.10, coordinated=.3)), ('strong: planted groups at price plus 0.25', dict(lift=.25, coordinated=.3)))


def main():
    OUT.mkdir(exist_ok=True)
    lines = ['# Controls on synthetic tables', '', f'Written by `code/ctl_10_synth.py`, {MARKETS} synthetic markets, threshold 0.05/6, through the verdict of the plan. {NULL_DRAWS} H2 draws here against 499 on real data. No real data.', '', '| Scenario | Window | Seed | Bursts | Matched share | Difference | p H1 | Placebo p | H2 observed / median / p | Verdict |', '|---|---:|---:|---:|---:|---:|---:|---:|---|---|']
    passes, tables = {}, {}
    for name, kw in SCENARIOS:
        for window in WINDOWS:
            key = f'{name}, w={window}'
            passes[key] = 0
            for seed in (1, 2, 3):
                r = run(seed, window, tables, **kw)
                f = lambda v, d=4: '' if v is None else format(v, f'.{d}f')
                lines.append(f"| {name} | {window} | {seed} | {r['primary']['n_bursts']} | {f(r['primary']['matched_share'], 2)} | {f(r['primary']['diff'])} | {f(r['primary']['p'])} | {f(r['placebo']['p'])} | {r['count']['observed']} / {r['count']['null_median']} / {f(r['count']['p'], 3)} | {r['verdict']} |")
                passes[key] += r['verdict'] == 'PREDICTIVE_TIMING_PATTERN'
                print(lines[-1], flush=True)
        tables.clear()
    lines += ['', '## Reading', '', f'Passes of the verdict, out of 3 seeds: {json.dumps(passes, indent=0)}', '', 'The real nulls and both traps must stay at or near 0. Medium and strong show power on this synthetic size only. Real effective n is events, so real power is lower than a passing medium suggests. A real effect smaller than the medium scenario can be missed: not supported is not disproved.', '']
    (OUT / 'controles_positifs.md').write_text('\n'.join(lines))
    enregistrer(ETUDE, test='controls_synthetic', declare=True, n=MARKETS, agent='etude-sync', donnees='synthetiques', n_comparaisons=len(SCENARIOS) * len(WINDOWS) * 3, sortie='controles/controles_positifs.md', note=json.dumps(passes))


if __name__ == '__main__':
    main()
