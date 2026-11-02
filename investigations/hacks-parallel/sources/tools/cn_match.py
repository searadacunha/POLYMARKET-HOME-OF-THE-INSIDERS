"""Amount and time matching of stolen deposits on ChangeNOW-tagged wallets against later payouts of the studied wallets, with calendar controls and amount placebos. A match is a similarity: it never proves a payout belongs to a deposit."""
import csv
import json
import math
import random
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import chainlib as c
import cn_common as cc
import cn_windows as w
import tokens

ROOT = Path(__file__).resolve().parent.parent
BANDS = {'tight': (.002, .01, 10.0), 'main': (.002, .03, 30.0), 'wide': (0.0, .05, 60.0)}
HOURS = (1, 6, 24, 48)
SEED = 20261102
PLACEBOS = 400


def in_band(value, usd, band):
    low_fee, high_fee, fixed = band
    return usd * (1 - high_fee) - fixed <= value <= usd * (1 - low_fee)


def usd_of(e, chain):
    sym = tokens.canonical_symbol(chain, e)
    if sym not in cc.PRICE_KEY:
        return None
    return c.amount(e) * cc.price(sym, e['ts'])


def universe(incident, excluded):
    """All payouts of all studied wallets, by window name, with USD values and without known service or internal recipients."""
    names = cc.window_names(incident)
    out = {n: [] for n in names}
    for source in w.INCIDENTS[incident]['sources']:
        chain = w.SOURCES[source][1]
        for n in names:
            rows, _ = cc.payouts(incident, source, n)
            for e in rows or []:
                if e['dst'] in excluded:
                    continue
                v = usd_of(e, chain)
                if v and v >= 5:
                    out[n].append(dict(ts=e['ts'], usd=v, e=e, source=source, chain=chain))
    return out


def count(deposit_usd, t, hours, rows, band):
    return [r for r in rows if t < r['ts'] <= t + hours * 3600 and in_band(r['usd'], deposit_usd, band)]


def analyse(deposits, incident, excluded, rng):
    uni = universe(incident, excluded)
    t0 = cc.window_start(incident, 'target48')
    results, cands = [], []
    for d in deposits:
        for hours in HOURS:
            for bname, band in BANDS.items():
                hits = count(d['usd'], d['ts'], hours, uni['target48'], band)
                calendar = {}
                for n in uni:
                    if n == 'target48':
                        continue
                    if n == 'pre48':
                        calendar[n] = sum(1 for r in uni[n] if d['ts'] - hours * 3600 <= r['ts'] < d['ts'] and in_band(r['usd'], d['usd'], band))
                    else:
                        shift = cc.window_start(incident, n) - t0
                        calendar[n] = len(count(d['usd'], d['ts'] + shift, hours, uni[n], band))
                placebo = [len(count(d['usd'] * math.exp(rng.uniform(-.5, .5)), d['ts'], hours, uni['target48'], band)) for _ in range(PLACEBOS)]
                mean_cal = sum(calendar.values()) / len(calendar) if calendar else 0
                results.append(dict(incident=incident, deposit_tx=d['tx'], hub=d['hub'], usd=round(d['usd'], 2), hours=hours, band=bname, observed=len(hits), calendar_mean=round(mean_cal, 3), calendar=json.dumps(calendar), calendar_at_least=sum(v >= len(hits) for v in calendar.values()), calendar_n=len(calendar), placebo_mean=round(sum(placebo) / PLACEBOS, 3), placebo_p=round((1 + sum(p >= len(hits) for p in placebo)) / (PLACEBOS + 1), 4)))
                if bname == 'main' and hours == 48:
                    for r in hits:
                        cands.append(dict(d=d, r=r))
    return results, cands


def main(deposits_file):
    deposits = json.loads(Path(deposits_file).read_text())
    excluded = set(json.loads((ROOT / 'state/runs/cn_excluded.json').read_text()))
    rng = random.Random(SEED)
    all_results, all_cands = [], []
    for incident in sorted({d['incident'] for d in deposits}):
        res, cands = analyse([d for d in deposits if d['incident'] == incident], incident, excluded, rng)
        all_results += res
        all_cands += cands
    with (ROOT / 'state/runs/match_tests.csv').open('w', newline='') as f:
        wr = csv.DictWriter(f, fieldnames=list(all_results[0]))
        wr.writeheader()
        wr.writerows(all_results)
    (ROOT / 'state/runs/match_cands.json').write_text(json.dumps(all_cands))
    print(len(all_results), 'tests', len(all_cands), 'candidates at 48 h, main band')


if __name__ == '__main__':
    main(sys.argv[1])
