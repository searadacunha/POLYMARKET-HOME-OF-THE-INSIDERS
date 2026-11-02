"""PROTOCOL.md section 6, measures. No ground truth exists: an alert is never called a true or false positive. The control rate bounds the load, it is not a precision."""
import csv
import json
import math
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import net
import seed

ROOT = net.ROOT
T_UPSIDE = 1792768669
NAMED = {a.lower(): n for n, a in list(seed.UPSIDE_PRINTED.items()) + list(seed.UPSIDE_LATER.items())}
IR = {a['profile'].lower(): f'irboz_{n}' for n, a in seed.IRBOZ.items()}
PUBLIC = {**IR, **NAMED}


def poisson_upper(k, conf=.95):
    """Exact one-sided upper bound for a Poisson count."""
    lam = k + 1e-9
    while True:
        p = sum(math.exp(-lam) * lam ** i / math.factorial(i) for i in range(k + 1))
        if p <= 1 - conf:
            return lam
        lam += .01


def binom_tail(k, n, p):
    """P(X >= k), exact."""
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))


def evaluate(path):
    d = json.load(open(path))
    coh = {r['wallet']: r for r in json.load(open(ROOT / 'derived/cohort.json'))['rows']}
    out = {}
    for det in ('D1', 'D3'):
        al = [a for a in d['alerts'] if a['det'] == det]
        before = [a for a in al if a['ts'] < T_UPSIDE]
        public = {a['wallet']: a['ts'] for a in al if a['wallet'] in PUBLIC}
        pub_before = {PUBLIC[w]: time.strftime('%d/%m %H:%M', time.gmtime(t)) for w, t in public.items() if t < T_UPSIDE}
        pub_after = {PUBLIC[w]: time.strftime('%d/%m %H:%M', time.gmtime(t)) for w, t in public.items() if t >= T_UPSIDE}
        missed = sorted(PUBLIC[w] for w in PUBLIC if w not in public)
        fl = [coh[a['wallet']] for a in before if a['wallet'] in coh]
        nf, pf = sum(r['notional'] for r in fl), sum(r['hold_pnl'] for r in fl)
        fresh_rest = [r for r in coh.values() if r['status'] == 'fresh' and r['wallet'] not in {a['wallet'] for a in before}]
        nr, pr = sum(r['notional'] for r in fresh_rest), sum(r['hold_pnl'] for r in fresh_rest)
        out[det] = dict(alerts=len(al), first=time.strftime('%d/%m %H:%M', time.gmtime(min(a['ts'] for a in al))) if al else None, before_upside=len(before), public_before=pub_before, public_after=pub_after, public_missed=missed,
                        flagged_before_with_result=len(fl), winners=sum(r['hold_pnl'] > 0 for r in fl), losers=sum(r['hold_pnl'] < 0 for r in fl), roi_flagged=round(pf / nf, 4) if nf else None, roi_other_fresh=round(pr / nr, 4) if nr else None, n_other_fresh=len(fresh_rest), not_public_before=sum(1 for a in before if a['wallet'] not in PUBLIC))
    d2 = [a for a in d['alerts'] if a['det'] == 'D2']
    final = {}
    with open(ROOT / 'derived/markets.csv') as f:
        for m in csv.DictReader(f):
            for t, p in zip(m['tokens'].split('|'), m['final_prices'].split('|')):
                final[t] = float(p) if p else None
    d2_rows = [dict(ts=time.strftime('%d/%m %H:%M', time.gmtime(a['ts'])), won=final.get(a['token']), price=round(a['price'], 3), public_in=sum(w in PUBLIC for w in a['wallets'])) for a in sorted(d2, key=lambda x: x['ts'])]
    out['D2'] = dict(alerts=len(d2), before_upside=sum(a['ts'] < T_UPSIDE for a in d2), won=sum(r['won'] == 1.0 for r in d2_rows), lost=sum(r['won'] == 0.0 for r in d2_rows), won_before=sum(1 for a in d2 if a['ts'] < T_UPSIDE and final.get(a['token']) == 1.0), lost_before=sum(1 for a in d2 if a['ts'] < T_UPSIDE and final.get(a['token']) == 0.0), rows=d2_rows)
    return d, out


def main():
    d, ballon = evaluate(ROOT / 'derived/detectors_ballon.json')
    report = dict(ballon_full_tape=ballon, ballon_wallets=d['wallets'], ballon_rows=d['rows'])
    p = ROOT / 'derived/detectors_ballon_min1000.json'
    if p.exists():
        _, f = evaluate(p)
        report['ballon_collector_filter_1000'] = f
    oos = json.load(open(ROOT / 'derived/detectors_oos.json'))
    rows = []
    for eid, r in oos.items():
        c = {k: sum(1 for a in r['alerts'] if a['det'] == k) for k in ('D1', 'D2', 'D3')}
        rows.append(dict(event=eid, title=r.get('title'), kind=r.get('kind'), wallets=r.get('wallets'), buy_rows=r.get('rows'), **c, weeks=round((r['last_ts'] - r['first_ts']) / (7 * 86400), 2) if r.get('first_ts') else None, copy=r.get('summary')))
    report['oos'] = rows
    wc = sum(r['wallets'] or 0 for r in rows)
    spec = {}
    for det in ('D1', 'D3'):
        kc = sum(r[det] for r in rows)
        kb = ballon[det]['alerts']
        rb = kb / d['wallets'] * 1000
        rc = kc / wc * 1000 if wc else None
        share = d['wallets'] / (d['wallets'] + wc)
        spec[det] = dict(ballon_alerts=kb, ballon_per_1000_wallets=round(rb, 3), control_alerts=kc, control_wallets=wc, control_per_1000_wallets=round(rc, 3), control_upper95_per_1000=round(poisson_upper(kc) / wc * 1000, 3), p_ballon_excess=binom_tail(kb, kb + kc, share) if kb + kc else None)
    spec['D2'] = dict(ballon_alerts=ballon['D2']['alerts'], control_alerts=sum(r['D2'] for r in rows), control_wallets=wc)
    report['specificity'] = spec
    report['note'] = 'Ballon family is 31 events, each control is one event. Detectors were written after reading this affair: the Ballon figures are in-sample.'
    (ROOT / 'derived/detector_eval.json').write_text(json.dumps(report, indent=1))
    for k in ('D1', 'D2', 'D3'):
        print(k, {x: v for x, v in ballon[k].items() if x != 'rows'})
    print(spec)
    print(json.dumps(rows, ensure_ascii=False)[:1500])
    if 'ballon_collector_filter_1000' in report:
        print('FILTER 1000', {k: {x: report['ballon_collector_filter_1000'][k].get(x) for x in ('alerts', 'before_upside', 'public_before', 'public_missed')} for k in ('D1', 'D3')})


if __name__ == '__main__':
    main()
