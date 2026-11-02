"""What a wallet did before and around a decision, from rows observed by that moment only.

Ages here measure our observation window. The wallet's true creation date is a separate, verified
field, filled only by an on-chain or activity lookup; first seen by us never stands in for it.
"""
import statistics
from collections import defaultdict

BASELINE_INSUFFICIENT = 'BASELINE_INSUFFICIENT'


def fill_groups(rows):
    """One group per token, side and transaction: fills of one transaction are one decision."""
    groups = {}
    for r in rows:
        g = groups.setdefault((r['token_id'], r['is_buy'], r['tx']), dict(token_id=r['token_id'], is_buy=r['is_buy'], tx=r['tx'], event_key=r['event_key'], condition_id=r['condition_id'],
                                                                         nominal=0.0, size=0.0, ts=r['ts'], first_ts=r['ts'], observed_at=r['observed_at'], outcome=r.get('outcome')))
        g['nominal'] += r['nominal']
        g['size'] += r['size']
        g['ts'] = max(g['ts'], r['ts'])
        g['first_ts'] = min(g['first_ts'], r['ts'])
        g['observed_at'] = max(g['observed_at'], r['observed_at'])
    for g in groups.values():
        g['price'] = g['nominal'] / g['size'] if g['size'] else 0.0
    return sorted(groups.values(), key=lambda g: g['ts'])


def wallet_rows(store, wallet, now, window_s, cap):
    rows = store.cx.execute('SELECT * FROM trades WHERE wallet=? AND ts>=? AND observed_at<=? ORDER BY ts DESC LIMIT ?', (wallet, now - window_s, now, cap)).fetchall()
    return [dict(r) for r in rows], len(rows) >= cap


def wallet_profile(store, wallet, event_key, now, config):
    rows, capped = wallet_rows(store, wallet, now, config['baseline_window_s'], config['wallet_row_cap'])
    groups = fill_groups(rows)
    buys = [g for g in groups if g['is_buy']]
    recent_start = now - config['recent_window_s']
    event_recent = [g for g in buys if g['event_key'] == event_key and g['ts'] >= recent_start]
    if not event_recent:
        return None
    largest = max(event_recent, key=lambda g: g['nominal'])
    prior = [g for g in buys if g['ts'] < largest['first_ts']]
    first_ts, first_event = store.first_trade(wallet, now)
    portfolio_start = now - config['portfolio_window_s']
    portfolio = [g for g in buys if g['ts'] >= portfolio_start]
    spend_by_event = defaultdict(float)
    for g in portfolio:
        spend_by_event[g['event_key']] += g['nominal']
    total_spend = sum(spend_by_event.values())
    earlier = [g for g in buys if g['ts'] < portfolio_start]
    earlier_events = defaultdict(float)
    for g in earlier:
        earlier_events[g['event_key']] += g['nominal']
    earlier_top = max(earlier_events.values()) / sum(earlier_events.values()) if earlier_events else None
    baseline_days = max(1.0, (largest['first_ts'] - min((g['ts'] for g in prior), default=largest['first_ts'])) / 86400)
    enough = len(prior) >= config['baseline_minimum']
    median = statistics.median(g['nominal'] for g in prior) if prior else None
    burst_start = now - config['burst_window_s']
    burst = [g for g in event_recent if g['ts'] >= burst_start]
    return dict(
        wallet=wallet, event_key=event_key,
        observed_first_trade=first_ts, observed_age_s=now - first_ts, verified_first_chain_activity=None, verified_first_deposit=None,
        first_trade_on_this_event=first_event == event_key,
        seconds_from_first_trade_to_largest=largest['first_ts'] - first_ts,
        markets_traded=len({g['condition_id'] for g in groups}), events_traded=len({g['event_key'] for g in groups}),
        event_share_of_spend=spend_by_event.get(event_key, 0.0) / total_spend if total_spend else None, top_event_share_before_window=earlier_top,
        baseline_status='OK' if enough else BASELINE_INSUFFICIENT, baseline_groups=len(prior), baseline_median=median if enough else None,
        size_ratio=(largest['nominal'] / median) if enough and median else None,
        frequency_ratio=(len(event_recent) / (len(prior) / baseline_days)) if enough and prior else None,
        burst_groups=len(burst), burst_nominal=sum(g['nominal'] for g in burst), largest=largest, event_recent=event_recent, rows_capped=capped,
        sold_recently=any(not g['is_buy'] and g['event_key'] == event_key and g['ts'] >= recent_start for g in groups))


def is_young_and_concentrated(profile, config):
    young = profile['observed_age_s'] <= config['new_wallet_s'] or profile['baseline_groups'] <= config['new_wallet_baseline_maximum']
    share = profile['event_share_of_spend']
    return young and share is not None and share >= config['event_share_minimum']


def is_candidate(profile, position, comparators, keys, config):
    """Not a finding: a wallet worth comparing with others on the same outcome. Alone it opens nothing."""
    if position['max_market_spend'] < config['minimum_spend']:
        return False
    tail = comparators.tail(keys, 'max_market_spend', position['max_market_spend'])
    share = profile['event_share_of_spend']
    young = profile['observed_age_s'] <= config['new_wallet_s'] or profile['baseline_groups'] <= config['new_wallet_baseline_maximum']
    return tail['tail'] is not None and tail['tail'] <= config['candidate_tail'] and (young or (share is not None and share >= config['event_share_minimum']))


def wallet_anomalies(profile, position, comparators, keys, config):
    """A finding needs an extreme value against its comparator. No comparator, no finding, and it says so."""
    found, unavailable = {}, []
    threshold = config['comparator_tail']
    size_tail = comparators.tail(keys, 'size_ratio', profile['size_ratio'])
    if profile['baseline_status'] != 'OK':
        unavailable.append(BASELINE_INSUFFICIENT)
    elif size_tail['status'] == 'COMPARATOR_INSUFFICIENT':
        unavailable.append('COMPARATOR_INSUFFICIENT:size_ratio')
    elif size_tail['tail'] is not None and size_tail['tail'] <= threshold and profile['size_ratio'] >= config['size_ratio_minimum']:
        found['size_break'] = dict(ratio=profile['size_ratio'], baseline_median=profile['baseline_median'], baseline_groups=profile['baseline_groups'], comparator=size_tail)
    frequency_tail = comparators.tail(keys, 'frequency_ratio', profile['frequency_ratio'])
    if frequency_tail['tail'] is not None and frequency_tail['tail'] <= threshold and profile['frequency_ratio'] >= config['frequency_ratio_minimum']:
        found['frequency_break'] = dict(ratio=profile['frequency_ratio'], comparator=frequency_tail)
    spend_tail = comparators.tail(keys, 'max_market_spend', position['max_market_spend'])
    share = profile['event_share_of_spend']
    if spend_tail['status'] == 'COMPARATOR_INSUFFICIENT':
        unavailable.append('COMPARATOR_INSUFFICIENT:max_market_spend')
    elif is_young_and_concentrated(profile, config):
        joint = comparators.joint_tail(keys, 'young_concentrated_spend', 'max_market_spend', position['max_market_spend'])
        if joint['tail'] is not None and joint['tail'] <= threshold:
            found['new_and_concentrated'] = dict(observed_age_h=profile['observed_age_s'] / 3600, event_share=share, spend=position['max_market_spend'], comparator=joint,
                                                 limit='Age since our first observation, not account creation.')
    previous = profile['top_event_share_before_window']
    if previous is not None and share is not None and share >= config['event_share_minimum'] and previous < config['diversified_share_maximum'] and spend_tail['tail'] is not None and spend_tail['tail'] <= threshold:
        found['concentration_shift'] = dict(share_before=previous, share_now=share, comparator=spend_tail)
    return found, sorted(set(unavailable))
