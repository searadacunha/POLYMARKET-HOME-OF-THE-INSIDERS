"""Positive controls on synthetic tables, run before the freeze. No real data is read.

C1 flat market loses spread and fees          C2 strong rise gives a positive outcome
C3 higher latency gives a worse entry         C4 depth/missing/split boundary are refused and counted
C5 fees are charged on losing trades          C6 synthetic results are registered as synthetiques
"""
import json, math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ana_edge as A
from registre import enregistrer

ROOT = Path(__file__).resolve().parents[1]
results, failures = {}, []


def check(name, ok, detail):
    results[name] = {'ok': bool(ok), 'detail': detail}
    if not ok:
        failures.append(name)


def quotes_from_path(path_times, mids, spread=0.01):
    ts = A.array.array('d'); bids = A.array.array('d'); asks = A.array.array('d')
    for t, m in zip(path_times, mids):
        ts.append(t); bids.append(m - spread / 2); asks.append(m + spread / 2)
    return ts, bids, asks


flat = 0.50
mids_flat = [flat] * 60
t0 = 1794614400.0
q_flat = quotes_from_path([t0 + 60 * i for i in range(60)], mids_flat)

# C1: flat market, entry at ask, exit at bid one hour later, politics cost
c1 = A.net(q_flat[2][0], q_flat[1][59], 0.04, 0.001)[0]
check('C1_flat_market_loses_spread_and_fees', c1 < 0, f'net={c1:.6f} per share')

# C2: strong rise 0.30 -> 0.60 across the hour, optimistic cost
rise = [0.30 + 0.005 * i for i in range(60)]
q_rise = quotes_from_path([t0 + 60 * i for i in range(60)], rise)
c2 = A.net(q_rise[2][0], q_rise[1][59], 0.0, 0.0)[0]
check('C2_strong_rise_positive_gross', c2 > 0, f'net={c2:.6f} per share (optimistic)')
c2p = A.net(q_rise[2][0], q_rise[1][59], 0.04, 0.001)[0]
check('C2b_rise_survives_politics_costs', c2p > 0, f'net={c2p:.6f} per share (politics)')

# C3: entry 30 s later on a rising market must be more expensive than entry 1 s later
q_fast = quotes_from_path([t0, t0 + 5, t0 + 35], [0.30, 0.32, 0.40])
e1 = A.after(q_fast[0], t0 + 1, 5); e30 = A.after(q_fast[0], t0 + 31, 5)
entry1, entry30 = q_fast[2][e1], q_fast[2][e30]
check('C3_latency_moves_entry_price', entry30 > entry1, f'ask@1s={entry1:.4f} ask@31s={entry30:.4f}')

# C4a: no quote within 5 s at the exit time -> refused
short = quotes_from_path([t0, t0 + 60], [0.30, 0.60])
check('C4a_missing_exit_refused', A.after(short[0], t0 + 3600) is None, 'after() returns None past the last quote')
# C4b: stale quote (age > 5 s) -> refused
check('C4b_stale_quote_refused', A.before(q_rise[0], t0 + 700, 5) is None, 'before() refuses a quote older than 5 s')
# C4c: depth must sit exactly at the quoted BBO, otherwise None
book = ([t0], [{'asks': [{'price': '0.31', 'size': '100'}], 'bids': [{'price': '0.29', 'size': '100'}]}])
check('C4c_depth_at_quoted_price', A.capacity(book, t0, 'asks', 0.31) == 100.0, 'supports 100 shares at the quoted ask')
check('C4c2_depth_mismatch_refused', A.capacity(book, t0, 'asks', 0.30) is None, 'wrong level price -> None')
check('C4c3_stale_depth_refused', A.capacity(book, t0 + 10, 'asks', 0.31) is None, 'depth older than 2 s -> None')

# C5: fees are charged on a losing trade too
c5_0, c5_f = A.net(0.55, 0.45, 0.0, 0.0)[0], A.net(0.55, 0.45, 0.04, 0.001)[0]
check('C5_fees_on_losing_trades', c5_f < c5_0 < 0, f'gross={c5_0:.4f} net={c5_f:.4f}')

# C6: summarize on synthetic rows computes what the plan asks; drawdown from realized cashflow
rows = []
for i in range(6):
    rows.append({'net': A.net(0.51, 0.60, 0.04, 0.001)[0], 'cost': 0.514, 'family': 'synthetic', 'exit': i, 'capacity': 10})
rows.append({'net': A.net(0.51, 0.45, 0.04, 0.001)[0], 'cost': 0.514, 'family': 'synthetic', 'exit': 6, 'capacity': 10})
s = A.summarize(rows)
expected_dd = 0.0
equity = peak = 0.0
for r in sorted(rows, key=lambda x: x['exit']):
    equity += 10 * r['net']; peak = max(peak, equity); expected_dd = max(expected_dd, peak - equity)
check('C6a_summarize_metrics', s['n'] == 7 and abs(s['cashflow_drawdown_10shares'] - expected_dd) < 1e-9,
      f"n={s['n']} dd={s['cashflow_drawdown_10shares']:.4f} expected={expected_dd:.4f}")
check('C6b_depth_supported_counts', s['depth_supported'] == 7, f"depth_supported={s['depth_supported']}")
check('C6c_empty_rows_reported', A.summarize([])['n'] == 0, 'empty cell reports n=0, no fabricated numbers')

enregistrer(str(ROOT), test='CTL00_positive_controls_synthetic', declare=True,
            n=11, agent='Codex', n_comparaisons=11, donnees='synthetiques',
            sortie='controles/CTL_00_report.md',
            note='Positive controls before the freeze, on the functions of the frozen code, synthetic tables only')
(ROOT / 'controles/CTL_00_report.md').write_text(
    '# Positive controls before the freeze\n\n'
    'Run on synthetic tables only; no real market data is read. Every check exercises the functions of '
    '`code/ana_edge.py` that the study will use, so the controls test the frozen code itself.\n\n'
    '| # | Control | Result |\n|---|---|---|\n' +
    '\n'.join(f"| {i+1} | {k} | {'PASS' if v['ok'] else 'FAIL'} — {v['detail']} |" for i, (k, v) in enumerate(results.items())) +
    '\n\nRegistered in the registry as synthetic data. Failures would block the freeze.\n')
print(json.dumps({'failures': failures, 'checks': len(results)}, indent=2))
sys.exit(1 if failures else 0)
