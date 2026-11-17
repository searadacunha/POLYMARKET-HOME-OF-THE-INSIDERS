"""Historical diagnostic recount (the 1 declared comparison of the plan), on frozen input data.

The file data/historical_alerts.jsonl is a copy of the labelled alerts of a previous local study
(origin volume not mounted); the plan says its reuse is descriptive, not independent validation.
Declared comparison (1): pooled excess of the win rate over the mean price at the alert, across the
validation populations (validation_info + validation_public_process), all classes pooled.
Descriptive, exploratory (not declared): the same recount per class and per population.

Run 1 (before this file was frozen) executed both parts. A post-freeze rerun with --declared-only
registers the declared comparison from frozen code; the earlier exploratory lines stay in the
registry as the honest trail.
"""
import json, statistics, sys
from pathlib import Path
from registre import enregistrer

ROOT = Path(__file__).resolve().parents[1]


def excess(sub):
    return sum(r['win'] for r in sub) / len(sub) - statistics.mean(r['price'] for r in sub)


def load():
    return [json.loads(l) for l in open(ROOT / 'data/historical_alerts.jsonl')]


def declared(rows):
    val = [r for r in rows if r['population'].startswith('validation')]
    out = {'declared': {
        'n': len(val), 'win_rate': sum(r['win'] for r in val) / len(val),
        'mean_price': statistics.mean(r['price'] for r in val), 'excess': excess(val),
        'populations': sorted(set(r['population'] for r in val))}}
    (ROOT / 'derived/historical_recount.json').write_text(json.dumps(out, indent=2))
    enregistrer(str(ROOT), test='H1_pooled_validation_excess', declare=True,
                n=len(val), agent='Codex', n_effectif=1, stat=out['declared']['excess'],
                n_comparaisons=1, sortie='derived/historical_recount.json',
                note='Pooled win rate minus mean price at alert, validation populations, previous local study reused descriptively')
    return out


def exploratory(rows):
    disc = [r for r in rows if r['population'] == 'discovery_info']
    cells = []
    for (pop, cls) in sorted(set((r['population'], r['class']) for r in rows)):
        sub = [r for r in rows if r['population'] == pop and r['class'] == cls]
        cells.append({'population': pop, 'class': cls, 'n': len(sub),
                      'win_rate': sum(r['win'] for r in sub) / len(sub),
                      'mean_price': statistics.mean(r['price'] for r in sub),
                      'excess': excess(sub),
                      'median_hours_before_real_close': statistics.median(r['hours_before_real_close'] for r in sub)})
    out = json.loads((ROOT / 'derived/historical_recount.json').read_text())
    out['exploratory_per_class'] = cells
    out['discovery_pooled_n'] = len(disc)
    (ROOT / 'derived/historical_recount.json').write_text(json.dumps(out, indent=2))
    enregistrer(str(ROOT), test='H2_per_class_recount_exploratory', declare=False,
                n=len(rows), agent='Codex', n_effectif=1, n_comparaisons=len(cells),
                sortie='derived/historical_recount.json',
                note='Descriptive recount of a previous study; classes and populations computed after the verdict of the live-quote study')
    return out


def selftest():
    rows = [{'population': 'validation_info', 'class': 'X', 'win': 1, 'price': 0.5, 'hours_before_real_close': 1},
            {'population': 'validation_info', 'class': 'X', 'win': 0, 'price': 0.5, 'hours_before_real_close': 1},
            {'population': 'discovery_info', 'class': 'X', 'win': 1, 'price': 0.1, 'hours_before_real_close': 1}]
    assert abs(excess([r for r in rows if r['population'].startswith('validation')])) < 1e-12
    planted = [{'population': 'validation_info', 'class': 'Y', 'win': w, 'price': p, 'hours_before_real_close': 1}
               for w, p in [(1, 0.4)] * 5 + [(0, 0.4)] * 5]
    assert abs(excess(planted) - 0.1) < 1e-12
    assert abs(excess([dict(r, price=0.6) for r in planted]) + 0.1) < 1e-12
    print('PASS: excess definition, validation filter, planted positive and negative')


if __name__ == '__main__':
    rows = load()
    out = declared(rows)
    if '--declared-only' not in sys.argv:
        out = exploratory(rows)
        print(f"exploratory cells: {len(out['exploratory_per_class'])}; discovery pooled n: {out['discovery_pooled_n']}")
    print(json.dumps(out['declared'], indent=2))
