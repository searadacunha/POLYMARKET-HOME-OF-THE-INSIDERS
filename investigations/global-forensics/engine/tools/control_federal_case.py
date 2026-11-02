"""External positive control: rebuild from public data, read today, what the SDNY indictment (26 Cr. 156, unsealed 2026-04-23) states about one Polymarket account.

The indictment is an accusation, not a verdict, and it names no wallet: the link to this address is the username in the charging press coverage and in the API's own rows.
Figures below were read by eye from the scanned PDF (sha256 in the output). Only flows are compared, nothing about intent. No civil name is written here.
"""
import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gf import account, env, ledger_pnl, pm
from gf.net import Net

WALLET = '0x31a56e9e690c621ed21de08cb559e9524cdb8ed9'
PDF = env.data_root() / 'catalog/docs_doj/indictment.pdf'
EST = timezone(timedelta(hours=-5))
# (paragraph, EST date, market fragment, shares)
BUYS = [('11a', '2025-12-27', 'US forces in Venezuela', 634), ('11b', '2025-12-30', 'Maduro out', 13769), ('11b', '2025-12-30', 'Maduro out', 850), ('11c', '2026-01-01', 'invade Venezuela', 17858), ('11c', '2026-01-01', 'War Powers', 1752), ('11c', '2026-01-01', 'Maduro out', 73685), ('11d', '2026-01-02', 'War Powers', 3618), ('11d', '2026-01-02', 'Maduro out', 90347), ('11d', '2026-01-02', 'Maduro out', 82421), ('11d', '2026-01-02', 'US forces in Venezuela', 564), ('11d', '2026-01-02', 'Maduro out', 87500), ('11d', '2026-01-02', 'Maduro out', 88187)]
TOTALS = dict(purchases_usd=33934, profit_usd=409881, occasions=13, withdrawn_usdce=437859, last_buy_est='2026-01-02 21:58', created_est='2025-12-26')


def main(out):
    net = Net()
    acct, rows = account.load(net, WALLET)
    books = ledger_pnl.account(rows)
    trades = [r for r in rows if r.get('type') == 'TRADE']
    buys = [r for r in trades if r.get('side') == 'BUY']
    table = []
    by_day_market = defaultdict(list)
    for r in buys:
        day = datetime.fromtimestamp(r['timestamp'], EST).strftime('%Y-%m-%d')
        by_day_market[(day, r.get('title'))].append(r)
    for para, day, fragment, shares in BUYS:
        rows_here = [r for (d, title), items in by_day_market.items() if d == day and fragment.lower() in (title or '').lower() for r in items]
        total = sum(float(r['size']) for r in rows_here)
        exact = any(abs(float(r['size']) - shares) <= 1 for r in rows_here)
        table.append(dict(paragraph=para, est_date=day, market=fragment, indictment_shares=shares, api_rows=len(rows_here), api_total_shares_that_day_market=round(total, 2), one_row_within_1_share=exact))
    last_buy = max(r['timestamp'] for r in buys)
    withdrawals = sorted(acct['withdrawals'], key=lambda w: -float(w['api_usd'] or 0))
    result = dict(
        wallet=WALLET,
        pdf_sha256=hashlib.sha256(PDF.read_bytes()).hexdigest(), pdf_url='https://www.justice.gov/usao-sdny/media/1437781/dl',
        status_of_document='Indictment: accusation, no verdict known to this study',
        history_complete=acct['history_complete'],
        checks=[
            dict(item='purchases, USD', indictment=TOTALS['purchases_usd'], rebuilt=books['wallet']['buy']),
            dict(item='buy rows', indictment=TOTALS['occasions'], rebuilt=len(buys)),
            dict(item='profit, USD', indictment=TOTALS['profit_usd'], rebuilt=str(sum(Decimal(m['cash_result']) for m in books['markets'])), note='Sum of cash by market'),
            dict(item='largest withdrawal, USDC.e', indictment=TOTALS['withdrawn_usdce'], rebuilt=withdrawals[0]['api_usd'], tx=withdrawals[0]['tx'], level=withdrawals[0]['level'], block=withdrawals[0]['block'], block_hash=withdrawals[0]['block_hash']),
            dict(item='last buy, EST', indictment=TOTALS['last_buy_est'], rebuilt=datetime.fromtimestamp(last_buy, EST).strftime('%Y-%m-%d %H:%M')),
            dict(item='first activity, EST date', indictment=TOTALS['created_est'], rebuilt=datetime.fromtimestamp(acct['first_activity'], EST).strftime('%Y-%m-%d')),
        ],
        buys=table, books=books, deposits=[{k: d.get(k) for k in ('tx', 'at', 'api_usd', 'level', 'block', 'block_hash', 'submitter', 'services')} for d in acct['deposits']], withdrawals=[{k: d.get(k) for k in ('tx', 'at', 'api_usd', 'level', 'block', 'block_hash', 'submitter', 'services')} for d in acct['withdrawals']], control=acct['control_latest'],
        not_reproducible_from_public_data=['The foreign vault of paragraph 16 is not named. Public flow: Relay to Solana, then to an address that an earlier report called Coinbase 4 on a single Solscan name.', 'The 444,209 USDC.e of January 16 and the brokerage account are in private records.', 'Access to information, intent, VPN use and the email changes: nothing on chain can speak to them.'],
    )
    Path(out).mkdir(parents=True, exist_ok=True)
    (Path(out) / 'control.json').write_text(json.dumps(result, indent=1, default=str))
    for c in result['checks']:
        print(c['item'], '| indictment', c['indictment'], '| rebuilt', c['rebuilt'])
    print('buys with a matching row:', sum(b['one_row_within_1_share'] for b in table), 'of', len(table))
    for b in table:
        print(b)
    print('markets', [(m['title'][:44], m['cash_result']) for m in books['markets']], 'unknown', books['unknown_types'], 'wallet', books['wallet'])


if __name__ == '__main__':
    main(sys.argv[1])
