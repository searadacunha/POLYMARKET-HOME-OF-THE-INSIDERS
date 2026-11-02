"""Self-check of the accounting and position rules on small tables."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import case_build as C

r = lambda **k: dict(dict(timestamp=1, type='TRADE', side=None, size=0, usdc_size=0, price=0, title='m', outcome='A', condition_id='c', slug='s', event_slug='e', transaction_hash='0x'), **k)
rows = [r(type='DEPOSIT', usdc_size=100), r(side='BUY', size=200, usdc_size=100), r(type='REDEEM', size=200, usdc_size=200), r(type='WITHDRAWAL', usdc_size=200)]
a = C.account(rows, True, dict(POL=0, pUSD=0), 0)
assert a['account_closed'] and a['net_cash_out_minus_in'] == 100 and a['residual'] == 0
# Open position, leftover cash, unknown type or capped history must each refuse a realised figure.
assert C.account(rows, True, dict(POL=0, pUSD=0), 5)['net_cash_out_minus_in'] is None
assert C.account(rows[:3], True, dict(POL=0, pUSD=200), 0)['net_cash_out_minus_in'] is None
assert C.account(rows, False, dict(POL=0, pUSD=0), 0)['net_cash_out_minus_in'] is None
assert C.account(rows + [r(type='MYSTERY')], True, dict(POL=0, pUSD=0), 0)['net_cash_out_minus_in'] is None
p = C.positions(rows)[0]
assert p['buy_shares'] == 200 and p['redeem_shares'] == 200 and p['net_shares_before_article'] == 200
print('ok')
