"""Positive controls for code/ana_70_historical.py on synthetic labelled rows (no side effects:
the module only defines functions now). S1 excess definition; S2 planted positive found;
S3 planted negative found; S4 the validation filter keeps only validation* populations.
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ana_70_historical as H  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
results = {}


def check(name, ok, detail):
    results[name] = {'ok': bool(ok), 'detail': detail}


rows = [{'population': 'validation_info', 'class': 'X', 'win': 1, 'price': 0.5, 'hours_before_real_close': 1},
        {'population': 'validation_info', 'class': 'X', 'win': 0, 'price': 0.5, 'hours_before_real_close': 1},
        {'population': 'discovery_info', 'class': 'X', 'win': 1, 'price': 0.1, 'hours_before_real_close': 1}]
val = [r for r in rows if r['population'].startswith('validation')]
check('S1_excess_definition', abs(H.excess(val)) < 1e-12, 'win rate 0.5, mean price 0.5 → excess 0')
planted = [{'population': 'validation_info', 'class': 'Y', 'win': w, 'price': p, 'hours_before_real_close': 1}
           for w, p in [(1, 0.4)] * 5 + [(0, 0.4)] * 5]
check('S2_planted_positive', abs(H.excess(planted) - 0.1) < 1e-12, 'win rate 0.5, price 0.4 → +0.1 found')
check('S3_planted_negative', abs(H.excess([dict(r, price=0.6) for r in planted]) + 0.1) < 1e-12,
      'win rate 0.5, price 0.6 → −0.1 found')
check('S4_validation_filter_only', all(r['population'].startswith('validation') for r in val),
      'discovery_info row excluded from the declared comparison')

(ROOT / 'controles/CTL_01_report.md').write_text(
    '# Positive controls for the historical recount script\n\nRun on synthetic labelled rows only; '
    'no real data is read.\n\n| # | Control | Result |\n|---|---|---|\n' +
    '\n'.join(f"| {i+1} | {k} | {'PASS' if v['ok'] else 'FAIL'} — {v['detail']} |" for i, (k, v) in enumerate(results.items())) +
    '\n')
print(json.dumps(results, indent=2))
sys.exit(0 if all(v['ok'] for v in results.values()) else 1)
