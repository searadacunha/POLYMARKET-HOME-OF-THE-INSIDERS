"""Denominators for the selection bias: every fresh or old wallet of the population, its hold-to-resolution result, whether a published list named it. Finds the wallets that behave like the named ones and were not named, winners and losers alike."""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import net
import seed

NAMED = {a.lower(): n for n, a in list(seed.UPSIDE_PRINTED.items()) + list(seed.UPSIDE_LATER.items())}
IRBOZ = {a['profile'].lower(): f'irboz_{n}' for n, a in seed.IRBOZ.items()}


def day(ts):
    return time.strftime('%Y-%m-%d %H:%M', time.gmtime(ts)) if ts else None


def main():
    d = json.load(open(net.ROOT / 'derived/stats_table.json'))['wallets']
    stats = json.load(open(net.ROOT / 'derived/population_stats.json'))
    rows = []
    for w, v in d.items():
        pnl = v['payoff'] - v['notional']
        rows.append(dict(wallet=w, status=v['status'], notional=round(v['notional'], 2), payoff=round(v['payoff'], 2), hold_pnl=round(pnl, 2), roi=round(pnl / v['notional'], 4), scen_share=round(v['scen'] / v['notional'], 4), n=v['n'], join=day(v['join_date']), first=day(v['first']), lag_h=round((v['first'] - v['join_date']) / 3600, 2) if v['join_date'] else None, markets=stats.get(w, {}).get('markets'), named=NAMED.get(w), irboz=IRBOZ.get(w), economic_pnl=stats.get(w, {}).get('economic_pnl')))
    rows.sort(key=lambda r: -r['hold_pnl'])
    summary = {}
    for st in ('fresh', 'old', 'unknown'):
        sub = [r for r in rows if r['status'] == st]
        n = len(sub)
        nt = sum(r['notional'] for r in sub)
        summary[st] = dict(n=n, notional=round(nt), roi=round(sum(r['hold_pnl'] for r in sub) / nt, 4) if nt else None, winners=sum(r['hold_pnl'] > 0 for r in sub), losers=sum(r['hold_pnl'] < 0 for r in sub), scen80=sum(r['scen_share'] >= .8 for r in sub), scen80_winners=sum(r['scen_share'] >= .8 and r['hold_pnl'] > 0 for r in sub))
    print(summary)
    fresh = [r for r in rows if r['status'] == 'fresh']
    # lookalikes: fresh, at least 2 000 $, at least 80 % on the winning scenario, not named
    look = [r for r in fresh if r['notional'] >= 2000 and r['scen_share'] >= .8]
    print('fresh >=2000$ and >=80% scenario:', len(look), 'named', sum(1 for r in look if r['named'] or r['irboz']), 'not named', sum(1 for r in look if not r['named'] and not r['irboz']))
    for r in look[:30]:
        print(r['wallet'][:12], r['notional'], 'pnl', r['hold_pnl'], 'scen', r['scen_share'], 'join', r['join'], 'first', r['first'], 'lag_h', r['lag_h'], 'mk', r['markets'], r['named'] or r['irboz'] or '')
    # the mirror: fresh and at least 2 000 $, mostly NOT on the winning scenario
    other = sorted([r for r in fresh if r['notional'] >= 2000 and r['scen_share'] < .5], key=lambda r: r['hold_pnl'])
    print('fresh >=2000$ with <50% on scenario:', len(other), 'losers', sum(r['hold_pnl'] < 0 for r in other), 'sum pnl', round(sum(r['hold_pnl'] for r in other)))
    for r in other[:10]:
        print(' ', r['wallet'][:12], r['notional'], 'pnl', r['hold_pnl'], 'roi', r['roi'], 'scen', r['scen_share'], 'join', r['join'], 'mk', r['markets'])
    # all fresh by notional band
    bands = [(500, 2000), (2000, 10000), (10000, 1e12)]
    for lo, hi in bands:
        sub = [r for r in fresh if lo <= r['notional'] < hi]
        print('band', lo, hi, 'n', len(sub), 'winners', sum(r['hold_pnl'] > 0 for r in sub), 'losers', sum(r['hold_pnl'] < 0 for r in sub), 'roi', round(sum(r['hold_pnl'] for r in sub) / max(1, sum(r['notional'] for r in sub)), 3))
    # named wallets, rank inside the fresh population
    print('named before T_UPSIDE:', [(r['named'] or r['irboz'], r['notional'], r['hold_pnl'], r['status']) for r in rows if r['named'] or r['irboz']])
    print('irboz accounts not in table:', [k for k in IRBOZ if k not in d])
    # old accounts near the 41 000 $ and 23 000 $ of Upside
    old = sorted([r for r in rows if r['status'] == 'old' and r['join'] and r['join'].startswith('2026-08') and r['scen_share'] >= .5], key=lambda r: -r['notional'])
    print('old, joined Aug 2026, >=50% scenario:', [(r['wallet'][:12], r['notional'], r['first'], r['join']) for r in old[:6]])
    (net.ROOT / 'derived/cohort.json').write_text(json.dumps(dict(summary=summary, lookalikes=look, others=other, rows=rows), indent=0))


if __name__ == '__main__':
    main()
