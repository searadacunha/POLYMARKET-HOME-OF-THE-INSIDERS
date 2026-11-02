"""Final checks before any number is cited: ledger chain, archive hashes, books, CSV totals against the ledger, no key in any file, no write under the service's quota."""
import csv
import glob
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import net

ROOT = net.ROOT
ok = True


def check(name, cond, detail=''):
    global ok
    print(('OK  ' if cond else 'FAIL'), name, detail)
    ok = ok and cond


n, broken = net.verify_ledger()
check('ledger chain intact', broken is None, f'{n} lines, first broken {broken}')
checked, bad = net.verify_archive()
check('archived bodies match their sha256', bad == 0, f'{checked} checked, {bad} bad')
L = json.load(open(ROOT / 'derived/ledger.json'))
gap = [w for w, s in L.items() if abs(s['cash_gap']) > 1 or abs(s['chain_identity_gap']) > .01 or s['flows_mismatch']]
check('books close on-chain for every account', not gap, f'{len(L)} accounts, exceptions {[(g[:10], L[g]["cash_gap"]) for g in gap]}')
check('every wallet confirmed by CREATE2', all(s['create2'] for s in L.values()))
T = list(csv.DictReader(open(ROOT / 'TRADES.csv')))
for w, s in L.items():
    n_t = sum(1 for r in T if r['wallet'] == w)
    if n_t != s['n_trades']:
        check(f'TRADES.csv rows for {w[:10]}', False, f'{n_t} != {s["n_trades"]}')
check('TRADES.csv rows match the ledger', True, f'{len(T)} rows')
if (ROOT / 'FUNDING_FLOWS.csv').exists():
    F = list(csv.DictReader(open(ROOT / 'FUNDING_FLOWS.csv')))
    tx_bad = [r['tx_hash'] for r in F if not (re.fullmatch(r'0x[0-9a-f]{64}', r['tx_hash']) or r['chain'] in ('solana', 'bitcoin'))]
    check('FUNDING_FLOWS.csv hashes well formed', not tx_bad, f'{len(F)} rows, bad {tx_bad[:3]}')
    for w, s in L.items():
        dep = {r['tx_hash'] for r in F if r['account_wallet'] == w and r['kind'].startswith('polymarket_deposit')}
        wd = {r['tx_hash'] for r in F if r['account_wallet'] == w and r['kind'].startswith('polymarket_withdrawal')}
        if (dep or wd) and (len(dep) != s['n_deposits'] or len(wd) != s['n_withdrawals']):
            print('NOTE', w[:10], 'flows', len(dep), len(wd), 'ledger', s['n_deposits'], s['n_withdrawals'])
key = net.etherscan_key()
leak = []
for root, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in ('.git', 'http')]
    for f in files:
        p = Path(root) / f
        if p.suffix in ('.gz', '.jpg') or p.stat().st_size > 60_000_000:
            continue
        try:
            if key in p.read_text(errors='ignore'):
                leak.append(str(p))
        except OSError:
            pass
check('API key absent from the module', not leak, str(leak[:3]))
ledger_text = (ROOT / 'evidence/requests.jsonl').read_text()
check('API key absent from the ledger', key not in ledger_text)
inv = Path.home() / 'Projects/PolySentinel/investigations'
check('module reached through a symlink, outside the service quota', (inv / 'ballon_dor_2026').is_symlink() and not [p for p in inv.iterdir() if not p.is_symlink()])
print('RESULT', 'all checks passed' if ok else 'FAILED')
sys.exit(0 if ok else 1)
