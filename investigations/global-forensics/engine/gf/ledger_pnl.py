"""Accounting by wallet and market. Withdrawals minus deposits is not a profit, and a figure is not printed without what it leaves out.

Cash per market from the activity rows: buys, sells, redemptions, splits, merges. Cash at the wallet level adds deposits, withdrawals, rewards,
rebates and conversions. The residual against the balance read from a node is shown, never absorbed. Open positions are not valued unless a price
is given, so `realized` is the only figure called realized.
"""
from collections import defaultdict
from decimal import Decimal

CASH_IN = ('REDEEM', 'MERGE', 'REWARD', 'MAKER_REBATE', 'TAKER_REBATE', 'REFERRAL_REWARD', 'YIELD')
CASH_OUT = ('SPLIT',)
EXTERNAL = {'DEPOSIT': 1, 'WITHDRAWAL': -1}
ZERO_CASH = ('CONVERSION',)


def dec(value):
    return Decimal(str(value or 0))


def account(rows):
    """rows: complete /v2/activity. Returns per-market lines and the wallet's cash, with unknown types counted apart."""
    markets = defaultdict(lambda: dict(bought_shares=Decimal(0), sold_shares=Decimal(0), redeemed_shares=Decimal(0), merged_shares=Decimal(0), split_shares=Decimal(0), buy_usd=Decimal(0), sell_usd=Decimal(0), redeem_usd=Decimal(0), merge_usd=Decimal(0), split_usd=Decimal(0), title=None, first=None, last=None, trades=0, outcomes=set()))
    wallet = defaultdict(Decimal)
    unknown = defaultdict(int)
    for r in rows:
        kind = r.get('type')
        usd = dec(r.get('usdc_size') if r.get('usdc_size') is not None else r.get('usdcSize'))
        size = dec(r.get('size'))
        condition = r.get('condition_id') or r.get('conditionId')
        if kind == 'TRADE':
            m = markets[condition]
            m['title'] = m['title'] or r.get('title')
            m['trades'] += 1
            m['first'] = r['timestamp'] if m['first'] is None else min(m['first'], r['timestamp'])
            m['last'] = r['timestamp'] if m['last'] is None else max(m['last'], r['timestamp'])
            m['outcomes'].add(r.get('outcome'))
            if r.get('side') == 'BUY':
                m['buy_usd'] += usd
                m['bought_shares'] += size
                wallet['buy'] += usd
            else:
                m['sell_usd'] += usd
                m['sold_shares'] += size
                wallet['sell'] += usd
        elif kind in ('REDEEM', 'MERGE', 'SPLIT'):
            m = markets[condition]
            m['title'] = m['title'] or r.get('title')
            m[{'REDEEM': 'redeem_usd', 'MERGE': 'merge_usd', 'SPLIT': 'split_usd'}[kind]] += usd
            m[{'REDEEM': 'redeemed_shares', 'MERGE': 'merged_shares', 'SPLIT': 'split_shares'}[kind]] += size
            wallet[kind.lower()] += usd
        elif kind in EXTERNAL:
            wallet[kind.lower()] += usd
        elif kind in CASH_IN:
            wallet[kind.lower()] += usd
        elif kind in ZERO_CASH:
            wallet[kind.lower() + '_rows'] += 1
        else:
            unknown[kind] += 1
    lines = []
    for condition, m in markets.items():
        cash = m['sell_usd'] + m['redeem_usd'] + m['merge_usd'] - m['buy_usd'] - m['split_usd']
        open_shares = m['bought_shares'] + m['split_shares'] - m['sold_shares'] - m['redeemed_shares'] - m['merged_shares']
        lines.append(dict(condition=condition, title=m['title'], trades=m['trades'], first=m['first'], last=m['last'], outcomes=sorted(str(o) for o in m['outcomes']), capital_engaged=str(m['buy_usd'] + m['split_usd']), cash_result=str(cash), shares_left_by_api=str(open_shares), buy_usd=str(m['buy_usd']), sell_usd=str(m['sell_usd']), redeem_usd=str(m['redeem_usd']), merge_usd=str(m['merge_usd']), split_usd=str(m['split_usd'])))
    trading = sum((wallet[k] for k in ('sell', 'redeem', 'merge', 'reward', 'maker_rebate', 'taker_rebate', 'referral_reward', 'yield')), Decimal(0)) - wallet['buy'] - wallet['split']
    computed_balance = wallet['deposit'] - wallet['withdrawal'] + trading
    return dict(markets=sorted(lines, key=lambda l: -abs(Decimal(l['cash_result']))), wallet={k: str(v) for k, v in wallet.items()}, unknown_types=dict(unknown), trading_cash=str(trading), computed_balance=str(computed_balance), meaning='Cash over the rows read. An unredeemed winning position counts for nothing here, and the shares left are the API\'s own figure.')


def residual(computed_balance, chain_balance):
    """Computed against read. A gap is a finding to explain, never rounded away."""
    return str(Decimal(str(chain_balance)) - Decimal(str(computed_balance)))
