"""The confirmatory run. Reads the frozen table and the outcomes file written once at the end of the holdout, runs the plan, writes tables/ and the register. Usage: ana_10_primary.py <outcomes.json>."""
import json
import os
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_v2 as lib  # noqa: E402
from registre import enregistrer  # noqa: E402

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOT, H2_DRAWS = 9999, 1999


def main(outcomes_path):
    data = np.load(Path(ETUDE) / 'derived' / 'table.npz')
    t = {k: data[k] for k in data.files}
    outcomes = json.loads(Path(outcomes_path).read_text())
    if set(outcomes['values'].values()) - {0, 1}:
        raise SystemExit('outcomes file holds a value other than 0 and 1')
    win = np.array([outcomes['values'].get(str(tok), -1) for tok in t.pop('token_id')], dtype=float)
    keep = win >= 0  # a token whose market did not end on exactly 1 and 0 leaves, counted
    counts = dict(rows=int(len(win)), rows_without_clean_outcome=int((~keep).sum()), outcome_file_counts=outcomes['counts'])
    if not keep.any():
        raise SystemExit('no row has an outcome: the file does not match the table')
    t.pop('market')
    t = {k: v[keep] for k, v in t.items()}
    t['win'] = win[keep]
    out = Path(ETUDE) / 'tables'
    out.mkdir(exist_ok=True)
    results = {}
    for window in lib.WINDOWS:
        r = lib.analyse_window(t, window, BOOT, H2_DRAWS)
        label, reasons = lib.verdict(r)
        r.update(verdict=label, reasons=reasons, primary=window == lib.PRIMARY)
        results[window] = r
    secondary = sorted((r['h1']['p'], w) for w, r in results.items() if w != lib.PRIMARY and r['h1']['p'] is not None)
    adjusted, running = {}, 1.0
    for rank in range(len(secondary), 0, -1):
        running = min(running, secondary[rank - 1][0] * len(secondary) / rank)
        adjusted[secondary[rank - 1][1]] = running
    (out / 'results.json').write_text(json.dumps(dict(counts=counts, windows=results, secondary_bh_p=adjusted), indent=1, default=float))
    for window, r in results.items():
        role = 'primary' if window == lib.PRIMARY else 'secondary, never changes the verdict'
        enregistrer(ETUDE, test=f'H1_w{window}', declare=True, n=r['h1']['n_triggers'], n_effectif=r['h1']['facts_triggers'], agent='etude-sync-v2', params=dict(window=window), stat=r['h1']['diff'], p=r['h1']['p'], n_tirages=r['h1']['draws'], sortie='tables/results.json', note=role)
        enregistrer(ETUDE, test=f'H2_w{window}', declare=True, n=r['h2']['observed'], agent='etude-sync-v2', params=dict(window=window), p=r['h2']['p'], n_tirages=r['h2']['draws'], sortie='tables/results.json', note=role)
        enregistrer(ETUDE, test=f'NCE_w{window}', declare=True, n=r['nce']['n_triggers'], n_effectif=r['nce']['facts_triggers'], agent='etude-sync-v2', params=dict(window=window), stat=r['nce']['diff'], p=r['nce']['p'], n_tirages=r['nce']['draws'], sortie='tables/results.json', note=role)
    print(json.dumps({w: (r['verdict'], r['h1']['diff'], r['h1']['ci']) for w, r in results.items()}, default=float))


if __name__ == '__main__':
    main(sys.argv[1])
