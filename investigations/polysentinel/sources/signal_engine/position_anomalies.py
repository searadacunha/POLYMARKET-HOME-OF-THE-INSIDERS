"""Positions, entry prices and market context at the moment of a decision.

Entry price is never read as suspicious by itself: comparators are built per price zone, because a
large buy at 0.20 and one at 0.80 are different bets. Spend is reported per market, because several
markets of one event are interdependent and their spend does not add up to one independent position.
"""
import statistics
from collections import defaultdict
from decimal import Decimal


def position_profile(store, profile, now, config):
    """Uses only rows observed at or before `now`. Any later price stays with post-event analysis."""
    rows = [dict(r) for r in store.cx.execute('SELECT * FROM trades WHERE wallet=? AND event_key=? AND observed_at<=? ORDER BY ts', (profile['wallet'], profile['event_key'], now))]
    tokens = defaultdict(lambda: dict(buy_nominal=0.0, sell_nominal=0.0, buy_shares=0.0, sell_shares=0.0, condition_id=None, outcome=None))
    for r in rows:
        t = tokens[r['token_id']]
        side = 'buy' if r['is_buy'] else 'sell'
        t[side + '_nominal'] += r['nominal']
        t[side + '_shares'] += r['size']
        t['condition_id'] = r['condition_id']
        t['outcome'] = r.get('outcome') or t['outcome']
    positions = [dict(token_id=k, net_shares=v['buy_shares'] - v['sell_shares'], vwap=(v['buy_nominal'] / v['buy_shares']) if v['buy_shares'] else None, **v) for k, v in tokens.items()]
    recent = profile['event_recent']
    per_market = defaultdict(float)
    for g in recent:
        per_market[g['condition_id']] += g['nominal']
    largest = profile['largest']
    market = store.cx.execute('SELECT * FROM markets WHERE condition_id=?', (largest['condition_id'],)).fetchone()
    day_start = now - config['recent_window_s']
    market_total = store.cx.execute('SELECT SUM(nominal) FROM trades WHERE condition_id=? AND ts>=? AND observed_at<=?', (largest['condition_id'], day_start, now)).fetchone()[0] or 0.0
    before = [r[0] for r in store.cx.execute('SELECT price FROM trades WHERE token_id=? AND ts<? AND ts>=? AND observed_at<=? ORDER BY ts DESC LIMIT 20',
                                             (largest['token_id'], largest['first_ts'], largest['first_ts'] - 86400, now))]
    after = [r[0] for r in store.cx.execute('SELECT price FROM trades WHERE token_id=? AND ts>? AND ts<=? AND observed_at<=? ORDER BY ts LIMIT 20',
                                            (largest['token_id'], largest['ts'], largest['ts'] + 1800, now))]
    liquidity = spread = None
    # A liquidity reading only counts if it was taken shortly before the trade.
    if market and market['liquidity'] and market['liquidity_observed_at'] and 0 <= largest['first_ts'] - market['liquidity_observed_at'] <= config['liquidity_max_age_s']:
        liquidity, spread = market['liquidity'], market['spread']
    price_before = statistics.median(before) if before else None
    price_after = statistics.median(after) if after else None
    return dict(
        positions=positions, max_market_spend=max(per_market.values()), event_buy_nominal_24h=sum(g['nominal'] for g in recent), markets_in_event=len({g['condition_id'] for g in recent}),
        outcomes_held=sum(p['net_shares'] > 0 for p in positions), entry_vwap=largest['price'], largest_nominal=largest['nominal'], largest_tx=largest['tx'], largest_token=largest['token_id'],
        price_before=price_before, price_after_observed=price_after, drift_before_entry=None if price_before is None else largest['price'] - price_before,
        impact_observed=None if price_before is None or price_after is None else price_after - price_before,
        market_share_24h=(per_market[largest['condition_id']] / market_total) if market_total else None,
        liquidity=liquidity, spread=spread, liquidity_fraction=(largest['nominal'] / liquidity) if liquidity else None, depth_status='OBSERVED' if liquidity else 'NOT_OBSERVED_AT_TRADE_TIME',
        burst_nominal=profile['burst_nominal'], burst_groups=profile['burst_groups'])


def position_anomalies(profile, position, comparators, keys, config):
    found, unavailable = {}, []
    threshold = config['comparator_tail']
    spend = comparators.tail(keys, 'max_market_spend', position['max_market_spend'])
    if spend['status'] == 'COMPARATOR_INSUFFICIENT':
        unavailable.append('COMPARATOR_INSUFFICIENT:max_market_spend')
    elif spend['tail'] <= threshold:
        found['large_for_context'] = dict(spend=position['max_market_spend'], entry_price=position['entry_vwap'], comparator=spend)
    weight = comparators.tail(keys, 'market_share_24h', position['market_share_24h'])
    if weight['tail'] is not None and weight['tail'] <= threshold and position['market_share_24h'] >= config['market_share_minimum']:
        found['heavy_in_market'] = dict(share=position['market_share_24h'], comparator=weight, limit='Share of volume we observed, not of the order book.')
    depth = comparators.tail(keys, 'liquidity_fraction', position['liquidity_fraction'])
    if depth['tail'] is not None and depth['tail'] <= threshold and position['liquidity_fraction'] >= config['liquidity_fraction_minimum']:
        found['large_against_liquidity'] = dict(fraction=position['liquidity_fraction'], comparator=depth, limit='Catalogue liquidity, not executable depth.')
    burst = comparators.tail(keys, 'burst_nominal', position['burst_nominal'])
    if position['burst_groups'] >= config['burst_groups_minimum'] and not profile['sold_recently'] and burst['tail'] is not None and burst['tail'] <= threshold:
        found['rapid_accumulation'] = dict(groups=position['burst_groups'], nominal=position['burst_nominal'], comparator=burst)
    return found, sorted(set(unavailable))


def reconstruct_from_fills(fills, wallet):
    """Net position per token from decoded exchange fills, for this wallet's own orders only.

    Every order emits its own fill with the owner as `maker`, the taking order included. The `taker`
    field is often the exchange or an operator, so a wallet's outcome is never read from it. Removed
    logs do not count. Duplicate log identities count once.
    """
    wallet = wallet.lower()
    seen, ledger = set(), defaultdict(lambda: dict(shares=Decimal(0), cash=Decimal(0), fees=Decimal(0), fills=0, contracts=set()))
    skipped = dict(not_owner=0, removed=0, duplicate=0)
    for f in fills:
        identity = (f['transaction_hash'].lower(), f['log_index'])
        if identity in seen:
            skipped['duplicate'] += 1
            continue
        seen.add(identity)
        if f.get('removed'):
            skipped['removed'] += 1
            continue
        if f['maker'].lower() != wallet:
            skipped['not_owner'] += 1
            continue
        sign = 1 if f['side'] == 'BUY' else -1
        entry = ledger[f['token_id']]
        entry['shares'] += sign * Decimal(f['shares_raw']) / 1_000_000
        entry['cash'] -= sign * Decimal(f['nominal_raw']) / 1_000_000
        entry['fees'] += Decimal(f.get('fee_raw', 0)) / 1_000_000
        entry['fills'] += 1
        entry['contracts'].add(f['contract'])
    tokens = {k: dict(net_shares=float(v['shares']), net_cash=float(v['cash']), fees=float(v['fees']), fills=v['fills'], contracts=sorted(v['contracts'])) for k, v in ledger.items()}
    return dict(tokens=tokens, skipped=skipped, scope='Exchange fills only. Splits, merges, conversions and redemptions need activity rows and are not included.')


def independent_events(wallet_events, event_groups):
    """How many independent bets a set of events represents, given known groupings of correlated events."""
    groups = {event_groups.get(e, e) for e in wallet_events}
    return len(groups)
