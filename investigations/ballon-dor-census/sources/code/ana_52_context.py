"""Market context and press claims, recomputed from the tape: price path, implied probability of the whole top 5, holders at the capture, cohort, survivors and losers."""
import csv
import gzip
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import net
import seed

T_UPSIDE = 1792768669
T_CEREMONIE = 1793044800
DATES = {'01/10 12:00': 1790856000, '05/10 12:00': 1791201600, '08/10 12:00': 1791460800, '09/10 12:00': 1791547200, '10/10 12:00': 1791633600, '15/10 12:00': 1792065600, '19/10 12:00': 1792411200, '20/10 12:00': 1792497600, '22/10 12:00': 1792670400, '23/10 15:00': 1792767600, '26/10 12:00': 1793016000, '26/10 19:30': 1793043000}
SCEN = {"Will Harry Kane win the 2026 Ballon d'Or?": 'Yes', "Will Kylian Mbappé finish 2nd in the 2026 Ballon d'Or?": 'Yes', "Will Lamine Yamal finish 3rd in the 2026 Ballon d'Or?": 'Yes', "Will Rodri finish 4th in the 2026 Ballon d'Or?": 'Yes', "Will Lionel Messi finish 5th in the 2026 Ballon d'Or?": 'Yes', "Ballon d'Or 2026: Kylian Mbappé or Lamine Yamal to finish higher?": 'Mbappé', "Ballon d'Or 2026: Rodri or Lionel Messi to finish higher?": 'Rodri'}


def utc(ts):
    return time.strftime('%d/%m %H:%M', time.gmtime(ts))


def main():
    with open(net.ROOT / 'derived/markets.csv') as f:
        markets = list(csv.DictReader(f))
    tok = {}
    winner_q = {}
    for m in markets:
        if not m['tokens']:
            continue
        for t, o, p in zip(m['tokens'].split('|'), m['outcomes'].split('|'), m['final_prices'].split('|')):
            tok[t] = dict(q=m['question'], o=o, final=float(p) if p else None, eid=m['event_id'], group=m['group_item'])
            if m['event_id'] == '48361' and o == 'Yes':
                winner_q[t] = m['group_item'] or m['question']
    scen_tok = {t: v for t, v in tok.items() if SCEN.get(v['q']) == v['o']}
    series = defaultdict(list)
    wallets_family = defaultdict(lambda: defaultdict(float))
    with gzip.open(net.ROOT / 'derived/census_trades.jsonl.gz', 'rt') as f:
        for line in f:
            r = json.loads(line)
            if r['token'] in scen_tok or r['token'] in winner_q:
                series[r['token']].append((r['ts'], r['price'], r['size']))
    for s in series.values():
        s.sort()

    def price_at(t, ts, window=6 * 3600):
        rows = [x for x in series.get(t, []) if ts - window <= x[0] <= ts]
        if not rows:
            rows = [x for x in series.get(t, []) if x[0] <= ts][-5:]
        if not rows:
            return None
        n = sum(x[2] for x in rows)
        return sum(x[1] * x[2] for x in rows) / n if n else None

    table = {}
    for label, ts in DATES.items():
        row = {scen_tok[t]['q'][:44]: price_at(t, ts) for t in scen_tok}
        wp = {winner_q[t]: price_at(t, ts) for t in winner_q}
        wp = {k: v for k, v in wp.items() if v}
        total = sum(wp.values())
        strength = {k: v / total for k, v in wp.items()} if total else {}
        order = ['Harry Kane', 'Kylian Mbappé', 'Lamine Yamal', 'Rodri', 'Lionel Messi']
        pl, remaining = 1.0, 1.0
        names_ok = all(any(n.lower() in k.lower() for k in strength) for n in order)
        if names_ok:
            for n in order:
                s = next(v for k, v in strength.items() if n.lower() in k.lower())
                pl *= s / remaining
                remaining -= s
        ranks = [v for k, v in row.items() if ('finish' in k and 'or ' not in k) or k.startswith('Will Harry Kane win')]
        prod = 1.0
        for v in ranks:
            prod *= v if v else float('nan')
        table[label] = dict(prices={k: round(v, 3) if v else None for k, v in row.items()}, pl_exact_top5=round(pl, 6) if names_ok else None, product_rank_markets=round(prod, 4) if len(ranks) == 5 else None, n_rank=len(ranks))
        print(label, {k[:34]: (round(v, 2) if v else None) for k, v in row.items()}, 'PL', table[label]['pl_exact_top5'], 'prod', table[label]['product_rank_markets'])
    # Upside: shares held at the capture
    pos = defaultdict(float)
    mbappe = next(t for t, v in scen_tok.items() if v['q'].startswith("Ballon d'Or 2026: Kylian"))
    names = {}
    with gzip.open(net.ROOT / 'derived/census_trades.jsonl.gz', 'rt') as f:
        for line in f:
            r = json.loads(line)
            if r['token'] == mbappe and r['ts'] <= T_UPSIDE:
                pos[r['w']] += r['size'] if r['side'] == 'BUY' else -r['size']
    stats = json.load(open(net.ROOT / 'derived/population_stats.json'))
    total_long = sum(v for v in pos.values() if v > 0)
    named = {a.lower() for a in list(seed.UPSIDE_PRINTED.values()) + list(seed.UPSIDE_LATER.values())}
    named_share = sum(v for w, v in pos.items() if w in named and v > 0) / total_long
    print('holders long', sum(1 for v in pos.values() if v > 0), 'total_long', round(total_long), 'share of the 11 names', round(named_share, 4))
    top = sorted(pos.items(), key=lambda x: -x[1])[:15]
    top_rows = [dict(wallet=w, shares=round(v, 1), join=stats.get(w, {}).get('join_date'), join_utc=utc(stats[w]['join_date']) if stats.get(w, {}).get('join_date') else None) for w, v in top]
    top15 = sum(v for _, v in top) / total_long
    print('top15 share', round(top15, 4))
    for r in top_rows[:15]:
        print(r['wallet'][:12], r['shares'], r['join_utc'])
    (net.ROOT / 'derived/market_context.json').write_text(json.dumps(dict(dates=table, holders=dict(total_long=total_long, named_share=named_share, top15_share=top15, top=top_rows)), indent=1))


if __name__ == '__main__':
    main()
