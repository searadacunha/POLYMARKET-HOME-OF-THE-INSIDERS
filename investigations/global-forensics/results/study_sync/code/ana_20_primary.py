"""H1, its strata and the label placebo, from the frozen table only. Every run enters the register after its output is written."""
import gzip
import json
import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib_bursts as lib
from registre import enregistrer

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLES = Path(ETUDE) / 'tables'
CLEAN = lambda r: not r['partial']
both = lambda test: (lambda r: test(r) and CLEAN(r), lambda r: test(r) and CLEAN(r))
BAND = lambda low, high: (lambda r: low <= r.get('vwap', r.get('price')) < high)
STRATA = dict(valid=both(lambda r: r['split'] == 'VALID'), test=both(lambda r: r['split'] == 'TEST'), train=both(lambda r: r['split'] == 'TRAIN'), no_shock=(lambda r: r['shock'] is False and CLEAN(r), CLEAN), shock_unknown_or_none=(lambda r: r['shock'] is not True and CLEAN(r), CLEAN), fresh_half=(lambda r: r['fresh_share'] >= .5 and CLEAN(r), CLEAN), with_partial_files=(lambda r: True, lambda r: True), band_low=both(BAND(*lib.BANDS[0])), band_mid=both(BAND(*lib.BANDS[1])), band_high=both(BAND(*lib.BANDS[2])))


def read():
    bursts, entrants = [], []
    with gzip.open(Path(ETUDE) / 'derived/table.jsonl.gz', 'rt') as f:
        for line in f:
            r = json.loads(line)
            (bursts if r['kind'] == 'burst' else entrants).append(r)
    lib.add_crowd(bursts, entrants)
    return bursts, entrants


def main():
    TABLES.mkdir(exist_ok=True)
    bursts, entrants = read()
    out = {}
    for window in lib.WINDOWS:
        results = dict(primary=lib.compare(bursts, entrants, window, CLEAN, CLEAN))
        for name, (keep_b, keep_e) in STRATA.items():
            results[name] = lib.compare(bursts, entrants, window, keep_b, keep_e, draws=2000)
        results['placebo'] = lib.label_placebo([r for r in bursts if CLEAN(r)], [r for r in entrants if CLEAN(r)], window)
        out[str(window)] = results
        print(window, flush=True)
    (TABLES / 'h1.json').write_text(json.dumps(out, indent=1))
    descriptive = {}
    for window in lib.WINDOWS:
        rows = [r for r in bursts if r['window'] == window and CLEAN(r)]
        cvs = sorted(r['cv'] for r in rows)
        descriptive[str(window)] = dict(bursts=len(rows), events=len({r['group'] for r in rows}), shock_true=sum(r['shock'] is True for r in rows), shock_false=sum(r['shock'] is False for r in rows), shock_unknown=sum(r['shock'] is None for r in rows), median_cv=cvs[len(cvs) // 2] if cvs else None, mean_fresh_share=sum(r['fresh_share'] for r in rows) / len(rows) if rows else None, median_usd=sorted(r['usd'] for r in rows)[len(rows) // 2] if rows else None)
    (TABLES / 'descriptive.json').write_text(json.dumps(descriptive, indent=1))
    for window, results in out.items():
        p = results['primary']
        enregistrer(ETUDE, test=f'H1_w{window}', declare=True, n=p['n_bursts'], n_effectif=p['events_bursts'], agent='etude-sync', params=dict(window=int(window)), stat=p['diff'], p=p['p'], n_tirages=p['draws'], sortie='tables/h1.json')
        enregistrer(ETUDE, test=f'H1_strata_w{window}', declare=True, n=p['n_bursts'], agent='etude-sync', params=dict(window=int(window), strata=sorted(STRATA)), n_comparaisons=len(STRATA), sortie='tables/h1.json', note='exploratory strata, never used to choose')
        enregistrer(ETUDE, test=f'H1P_placebo_w{window}', declare=True, n=p['n_bursts'], agent='etude-sync', params=dict(window=int(window)), stat=results['placebo']['diff'], p=results['placebo']['p'], n_tirages=results['placebo']['draws'], sortie='tables/h1.json')


if __name__ == '__main__':
    main()
