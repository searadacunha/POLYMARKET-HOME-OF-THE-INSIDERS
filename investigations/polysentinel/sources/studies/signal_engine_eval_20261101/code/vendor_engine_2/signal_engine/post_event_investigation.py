"""Engine B: what happened after an event resolved. It enriches a case and never changes its past score.

Its numbers depend on the outcome, so nothing here may flow back into detection. Four amounts stay
apart because they are often confused: realized trading profit, unrealized value, redemption of
winning shares, and money simply withdrawn from the platform. A withdrawal is not a profit.
"""
from collections import defaultdict
from decimal import Decimal

HORIZONS = {'1d': 86400, '3d': 3 * 86400, '7d': 7 * 86400}


def price_after_entry(points, entry_ts, entry_price):
    """Change at 1, 3 and 7 days from a price series of (timestamp, price) pairs. Unknown stays None."""
    result = {}
    ordered = sorted(points)
    for name, delta in HORIZONS.items():
        target = entry_ts + delta
        candidates = [p for t, p in ordered if entry_ts < t <= target]
        result[name] = None if not candidates else candidates[-1] - entry_price
    return result


def settle_position(trades, activity, resolution_price=None, last_price=None, history_complete=False):
    """Average-cost ledger for one wallet on one token. It refuses to call anything realized without a known start.

    `activity` rows are typed REDEEM, SPLIT, MERGE, CONVERSION, DEPOSIT or WITHDRAWAL.
    """
    shares = cost = realized = Decimal(0)
    invalid = False
    for t in sorted(trades, key=lambda r: (r['ts'], r.get('tx', ''))):
        size, price = Decimal(str(t['size'])), Decimal(str(t['price']))
        if t['is_buy']:
            shares += size
            cost += size * price
        else:
            if size > shares:
                invalid = True
                continue
            fraction = size / shares
            realized += size * price - cost * fraction
            cost -= cost * fraction
            shares -= size
    redeemed = sum((Decimal(str(a.get('usdc_size', a.get('size', 0)))) for a in activity if a.get('type') == 'REDEEM'), Decimal(0))
    withdrawn = sum((Decimal(str(a.get('usdc_size', a.get('size', 0)))) for a in activity if a.get('type') == 'WITHDRAWAL'), Decimal(0))
    transforms = sorted({a['type'] for a in activity if a.get('type') in ('SPLIT', 'MERGE', 'CONVERSION')})
    calculable = history_complete and not invalid and not transforms
    settlement = None
    if resolution_price is not None and calculable:
        settlement = float(shares * Decimal(str(resolution_price)) - cost)
    unrealized = float(shares * Decimal(str(last_price)) - cost) if last_price is not None and resolution_price is None and calculable else None
    return dict(status='calculable' if calculable else 'not_calculable',
                reason=None if calculable else ('sold more than observed: opening inventory unknown' if invalid else 'splits, merges or conversions change the cost basis' if transforms else 'history not known to be complete'),
                realized_trading_profit=float(realized) if calculable else None, settlement_value_minus_cost=settlement, unrealized_value_minus_cost=unrealized,
                redeemed_amount=float(redeemed), withdrawn_amount=float(withdrawn), net_shares_observed=float(shares), remaining_cost_observed=float(cost),
                transformations=transforms, note='A redemption pays out shares; a withdrawal moves money. Neither is a profit by itself.')


def wallet_record_on_resolved(positions):
    """Hit rate on resolved markets actually observed, with its denominator, never on wins alone."""
    resolved = [p for p in positions if p.get('won') is not None]
    return dict(resolved_positions=len(resolved), won=sum(bool(p['won']) for p in resolved), hit_rate=(sum(bool(p['won']) for p in resolved) / len(resolved)) if resolved else None,
                scope='Only markets in our collection; wallets active elsewhere have an unknown record.')


def compare_with_other_side(wallet_entries):
    """Same event, both sides: what separates this wallet from those who entered and lost."""
    sides = defaultdict(list)
    for e in wallet_entries:
        sides[bool(e['won'])].append(e)

    def describe(rows):
        if not rows:
            return dict(wallets=0, median_entry_price=None, median_nominal=None)
        prices = sorted(r['entry_price'] for r in rows)
        nominals = sorted(r['nominal'] for r in rows)
        return dict(wallets=len(rows), median_entry_price=prices[len(prices) // 2], median_nominal=nominals[len(nominals) // 2])
    return dict(winners=describe(sides[True]), losers=describe(sides[False]), selection_warning='Comparing winners with losers conditions on the outcome: descriptive, never a detection input.')


def investigate_resolved_case(sealed_case, trades_by_wallet, activity_by_wallet, prices_by_token, resolution_by_token, last_price_by_token=None):
    """Adds a report next to a sealed case. The input is read only and is returned with its fingerprint untouched."""
    report = dict(case_fingerprint=sealed_case['fingerprint'], event_key=sealed_case['event_key'], engine='post_event', wallets={})
    for wallet, trades in trades_by_wallet.items():
        per_token = defaultdict(list)
        for t in trades:
            per_token[t['token_id']].append(t)
        entries = {}
        for token, rows in per_token.items():
            buys = [r for r in rows if r['is_buy']]
            if buys:
                nominal = sum(r['size'] * r['price'] for r in buys)
                vwap = nominal / sum(r['size'] for r in buys)
                entries[token] = dict(entry_ts=sum(r['ts'] * r['size'] * r['price'] for r in buys) / nominal, entry_price=vwap, nominal=nominal,
                                      price_change=price_after_entry(prices_by_token.get(token, []), min(r['ts'] for r in buys), vwap),
                                      settlement=settle_position(rows, activity_by_wallet.get(wallet, []), resolution_by_token.get(token), (last_price_by_token or {}).get(token)),
                                      resolved_to=resolution_by_token.get(token))
        report['wallets'][wallet] = entries
    return report
