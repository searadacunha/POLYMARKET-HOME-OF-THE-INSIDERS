"""Rebuild each account's money from fills and settlements, then check it twice against sources that do not share code with the API rollups:
the pUSD mint/burn logs on Polygon, and the wallet's pUSD balance read on-chain. Realized, unrealized, deposits, withdrawals and net stay separate.
Writes derived/ledger.json, derived/positions.csv, TRADES.csv."""
import csv
import glob
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import net

ROOT = net.ROOT
PUSD = '0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb'
TRANSFER = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
ZERO = '0x' + '0' * 40


def utc(ts):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(ts))


def main():
    summary, pos_rows, trade_rows = {}, [], []
    for f in sorted(glob.glob(str(ROOT / 'derived/accounts/*.json'))):
        a = json.load(open(f))
        w = a['address']
        c = json.load(open(ROOT / f'derived/chain/{w}.json'))
        by = defaultdict(float)
        n = defaultdict(int)
        pos = defaultdict(lambda: dict(buy_size=0.0, buy_usdc=0.0, sell_size=0.0, sell_usdc=0.0, redeem_size=0.0, redeem_usdc=0.0, fills=0, first=None, last=None, title=None, outcome=None, cond=None))
        first_dep = first_trade = last_trade = None
        for r in sorted(a['activity'], key=lambda x: x['timestamp']):
            t = r['type']
            by[t] += r['usdc_size']
            n[t] += 1
            if t == 'DEPOSIT' and first_dep is None:
                first_dep = r['timestamp']
            if t == 'TRADE':
                first_trade = first_trade or r['timestamp']
                last_trade = r['timestamp']
                p = pos[r['token_id']]
                p.update(title=r['title'], outcome=r['outcome'], cond=r['condition_id'])
                p['first'] = p['first'] or r['timestamp']
                p['last'] = r['timestamp']
                p['fills'] += 1
                if r['side'] == 'BUY':
                    p['buy_size'] += r['size']
                    p['buy_usdc'] += r['usdc_size']
                else:
                    p['sell_size'] += r['size']
                    p['sell_usdc'] += r['usdc_size']
                trade_rows.append(dict(wallet=w, labels=' '.join(a['labels']), utc=utc(r['timestamp']), ts=r['timestamp'], tx=r['transaction_hash'], condition_id=r['condition_id'], token_id=r['token_id'], market=r['title'], outcome=r['outcome'], side=r['side'], size=r['size'], price=r['price'],
                                       notional=round(r['size'] * r['price'], 6), usdc_incl_fee=r['usdc_size'], fee_est=round(abs(r['usdc_size'] - r['size'] * r['price']), 6), source='data-api /v2/activity TRADE'))
            if t == 'REDEEM':
                p = pos[r['token_id']]
                p.update(title=r['title'], outcome=r['outcome'], cond=r['condition_id'])
                p['redeem_size'] += r['size']
                p['redeem_usdc'] += r['usdc_size']
        inflow = by['DEPOSIT']
        outflow = by['WITHDRAWAL']
        income = sum(by[k] for k in by if k in ('REWARD', 'MAKER_REBATE', 'TAKER_REBATE', 'REFERRAL_REWARD', 'YIELD'))
        known = {'DEPOSIT', 'WITHDRAWAL', 'TRADE', 'REDEEM', 'REWARD', 'MAKER_REBATE', 'TAKER_REBATE', 'REFERRAL_REWARD', 'YIELD'}
        other = sorted(set(by) - known)
        if other:
            raise SystemExit(f'{w}: unhandled activity types {other}: a type left out would silently falsify the books')
        buys = sum(p['buy_usdc'] for p in pos.values())
        sells = sum(p['sell_usdc'] for p in pos.values())
        redeems = sum(p['redeem_usdc'] for p in pos.values())
        cash_api = inflow - outflow + income - buys + sells + redeems
        # chain: every pUSD mint into and burn out of the wallet's flows, from the receipts themselves
        chain_dep = chain_wd = 0.0
        flows_ok = flows_bad = 0
        for tx, fl in c['flows'].items():
            amount = 0.0
            for log in fl['receipt']['logs']:
                if log['address'].lower() == PUSD and log['topics'][0] == TRANSFER:
                    src, dst = '0x' + log['topics'][1][-40:], '0x' + log['topics'][2][-40:]
                    v = int(log['data'], 16) / 1e6
                    if fl['type'] == 'DEPOSIT' and dst == w:
                        amount += v
                    if fl['type'] == 'WITHDRAWAL' and src == w:
                        amount += v
            if abs(amount - fl['usdc']) < .01:
                flows_ok += 1
            else:
                flows_bad += 1
            if fl['type'] == 'DEPOSIT':
                chain_dep += amount
            else:
                chain_wd += amount
        # chain: all pUSD through the wallet, Etherscan list, with no API rollup in the path
        p_in = sum(int(r['value']) for r in c['erc20'] if r['contractAddress'].lower() == PUSD and r['to'].lower() == w) / 1e6
        p_out = sum(int(r['value']) for r in c['erc20'] if r['contractAddress'].lower() == PUSD and r['from'].lower() == w) / 1e6
        bal = int(net.rpc('eth_call', [dict(to=PUSD, data='0x70a08231' + '0' * 24 + w[2:]), 'latest'], cache=False), 16) / 1e6
        open_value = sum(x.get('current_value') or 0 for x in a['positions']['OPEN'])
        unrealized = sum(x.get('unrealized_pnl') or 0 for x in a['positions']['OPEN'])
        realized_api = sum(x.get('realized_pnl') or 0 for s in ('OPEN', 'CLOSED') for x in a['positions'][s])
        all_time = ((a['stats'] or {}).get('data') or {}).get('all_time_pnl') or {}
        net_flow = outflow - inflow
        equity_now = bal + open_value
        summary[w] = dict(labels=a['labels'], name=(a['profile'] or {}).get('name'), pseudonym=(a['profile'] or {}).get('pseudonym'), created_at=(a['profile'] or {}).get('createdAt'), join_date=((a['stats'] or {}).get('data') or {}).get('join_date'),
                          owner=c.get('owner'), create2=c.get('create2_beacon'), deposits=round(inflow, 6), withdrawals=round(outflow, 6), n_deposits=n['DEPOSIT'], n_withdrawals=n['WITHDRAWAL'], buys_usdc=round(buys, 6), sells_usdc=round(sells, 6), redeems_usdc=round(redeems, 6), income=round(income, 6),
                          n_trades=n['TRADE'], cash_expected_api=round(cash_api, 6), pusd_balance_chain=round(bal, 6), cash_gap=round(cash_api - bal, 6), open_value=round(open_value, 6), unrealized_api=round(unrealized, 6), realized_positions_api=round(realized_api, 6),
                          net_flow_withdrawals_minus_deposits=round(net_flow, 6), economic_pnl_books=round(outflow + equity_now - inflow, 6), economic_pnl_api=all_time.get('economic_pnl'), fees_api=all_time.get('fees_paid'),
                          chain_mint_sum=round(chain_dep, 6), chain_burn_sum=round(chain_wd, 6), flows_match=flows_ok, flows_mismatch=flows_bad, pusd_in_chain=round(p_in, 6), pusd_out_chain=round(p_out, 6), chain_identity_gap=round(p_in - p_out - bal, 6),
                          first_deposit=first_dep, first_trade=first_trade, last_trade=last_trade)
        for tok, p in pos.items():
            pos_rows.append(dict(wallet=w, labels=' '.join(a['labels']), market=p['title'], outcome=p['outcome'], condition_id=p['cond'], token_id=tok, fills=p['fills'], first_utc=utc(p['first']) if p['first'] else '', last_utc=utc(p['last']) if p['last'] else '', buy_size=round(p['buy_size'], 6), buy_usdc=round(p['buy_usdc'], 6),
                                 vwap_buy=round(p['buy_usdc'] / p['buy_size'], 6) if p['buy_size'] else '', sell_size=round(p['sell_size'], 6), sell_usdc=round(p['sell_usdc'], 6), redeem_size=round(p['redeem_size'], 6), redeem_usdc=round(p['redeem_usdc'], 6), left_size=round(p['buy_size'] - p['sell_size'] - p['redeem_size'], 6),
                                 cash_pnl=round(p['sell_usdc'] + p['redeem_usdc'] - p['buy_usdc'], 6)))
    (ROOT / 'derived/ledger.json').write_text(json.dumps(summary, indent=1))
    pos_rows.sort(key=lambda r: (r['wallet'], r['first_utc']))
    with open(ROOT / 'derived/positions.csv', 'w', newline='') as f:
        wr = csv.DictWriter(f, fieldnames=list(pos_rows[0]))
        wr.writeheader()
        wr.writerows(pos_rows)
    trade_rows.sort(key=lambda r: (r['wallet'], r['ts']))
    with open(ROOT / 'TRADES.csv', 'w', newline='') as f:
        wr = csv.DictWriter(f, fieldnames=list(trade_rows[0]))
        wr.writeheader()
        wr.writerows(trade_rows)
    keys = ('labels', 'name', 'created_at', 'owner', 'deposits', 'withdrawals', 'net_flow_withdrawals_minus_deposits', 'pusd_balance_chain', 'open_value', 'economic_pnl_books', 'economic_pnl_api', 'cash_gap', 'flows_match', 'flows_mismatch', 'chain_identity_gap', 'n_deposits', 'n_withdrawals', 'n_trades')
    for w, s in summary.items():
        print(w[:10], {k: s[k] for k in keys})


if __name__ == '__main__':
    main()
