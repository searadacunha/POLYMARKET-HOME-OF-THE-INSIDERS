"""Is a file finished? A written trace.json is not a finished file. Six things are told apart for each account: Polymarket history, funding rebuilt, exits rebuilt, branches stopped at an opacity frontier, coverage or data gaps, and the true end of processing.

METHODOLOGICALLY_COMPLETE asks for what public data can give: every observable branch processed, the frontiers and gaps written down, and an account whose money closes: deposits and direct moves, plus trading cash, minus withdrawals, equals the balance read on chain. It never asks for a civil identity or a platform's internal records.

Any stop this module does not know counts as work left, so a new reason can never pass as finished.
"""
from collections import Counter

from . import ledger_pnl

WORK = ('NODE_BUDGET', 'LIGHT_FLOW_CAP', 'READ_FAILED', 'WALLET_ROWS_NOT_CHECKED', 'WINDOW_SCAN_NEEDED', 'SERVICE_OR_SHARED:UNREAD')  # more budget, a retry or a scan can clear these
GAP = ('HISTORY_INCOMPLETE', 'AMBIGUOUS_PATH', 'NON_EVM_READ_SEPARATELY')  # read as far as this reader goes
END = ('NO_FLOW_IN_WINDOW', 'NO_LATER_OUTFLOW', 'DUST_NOT_FOLLOWED', 'WALLET_FILLS_NOT_FOLLOWED', 'WALLET_ROWS_PAST_ACTIVITY_LIST')
MONEY_ROLES = ('deposit_path', 'withdrawal_path', 'transfer', 'bridge_payout', 'bridge_deposit', 'internal_to_dossier')
COLLATERAL = ('USDC', 'USDC.e', 'pUSD')
RECONCILE_USD = 1.0  # rounding across many activity rows: the named accounts close within cents
COMPLETE, BLOCKED, WORK_LEFT = 'METHODOLOGICALLY_COMPLETE', 'BLOCKED', 'WORK_LEFT'


def sort_stop(stop, full):
    """One of work, frontier, gap or end. A hop whose read failed is work. Depth is a limit written down once a full walk reached it, and work in a light one."""
    reason = stop['reason']
    if reason in WORK:
        return 'work'
    if reason in END:
        return 'end'
    if reason in GAP:
        return 'gap'
    if reason == 'DEPTH_BUDGET':
        return 'gap' if full else 'work'
    if reason == 'BRIDGE_HOP_NOT_PROVEN':
        return 'work' if stop.get('hop_status') in ('RELAY_BUDGET_SPENT', 'READ_FAILED') or stop.get('proof_error') else 'frontier'
    if reason.startswith('SERVICE_OR_SHARED:') or reason == 'HUB_AT_READ':
        return 'frontier'
    return 'work'


def direction_state(result, direction):
    full = result.get('mode', 'full') == 'full'
    work, gaps, named, unnamed, bridges = Counter(), Counter(), Counter(), 0, 0
    for s in result['stops']:
        if s['direction'] != direction:
            continue
        kind = sort_stop(s, full)
        if kind == 'work':
            work[s['reason']] += 1
        elif kind == 'gap':
            gaps[s['reason']] += 1
        elif kind == 'frontier':
            if s['reason'] == 'BRIDGE_HOP_NOT_PROVEN':
                bridges += 1
            elif s.get('name'):
                named[s['name']] += 1
            else:
                unnamed += 1
    money = sum(e['direction'] == direction and e['role'] in MONEY_ROLES for e in result['edges'])
    return dict(work_left=dict(work), gaps=dict(gaps), named_frontier=named.most_common(12), named_branches=sum(named.values()), unnamed_shared_branches=unnamed, unproved_bridge_branches=bridges, money_edges=money, read=bool(money))


def money_chain(result, rows):
    """Funding, trading, gains, exits, from the activity and the wallet's own moves. Moves inside an activity row are counted there, never twice. Open positions are outside cash and shown apart."""
    books = ledger_pnl.account(rows)
    wallet, listed = result['wallet'], {r.get('transaction_hash') or r.get('transactionHash') for r in rows}
    value = lambda e: int(e['raw_amount']) / 10 ** int(e['decimals'] or 0)
    direct = [e for e in result['edges'] if e['transaction_hash'] not in listed and e.get('token') in COLLATERAL and e['role'] in MONEY_ROLES and e.get('source') != 'rpc:137']
    seen, direct_in, direct_out = set(), 0.0, 0.0
    for e in direct:
        key = (e['transaction_hash'], e.get('log_index'), e['from'], e['to'], e['raw_amount'])
        if key in seen:
            continue
        seen.add(key)
        direct_in += value(e) if e['to'] == wallet else 0
        direct_out += value(e) if e['from'] == wallet else 0
    held = (result.get('account') or {}).get('balances_now') or {}
    money = books['wallet']
    computed = float(books['computed_balance']) + direct_in - direct_out
    out = dict(deposits=float(money.get('deposit', 0)), direct_in=round(direct_in, 6), withdrawals=float(money.get('withdrawal', 0)), direct_out=round(direct_out, 6), trading_cash=float(books['trading_cash']), buys=float(money.get('buy', 0)), sells=float(money.get('sell', 0)), redeems=float(money.get('redeem', 0)), markets=len(books['markets']), computed_balance=round(computed, 6), open_positions_value=(held.get('open_positions') or {}).get('current_value'))
    if held.get('pUSD') is None:
        return dict(out, held=None, residual=None, reconciled=None)
    balance = sum(held.get(k) or 0 for k in ('pUSD', 'USDC.e', 'USDC'))
    residual = balance - computed
    return dict(out, held=round(balance, 6), residual=round(residual, 6), reconciled=abs(residual) <= RECONCILE_USD)


def file_state(result, rows=None):
    account = result.get('account') or {}
    limits = []
    if result.get('mode', 'full') != 'full':
        limits.append('LIGHT_MODE')
    if not account.get('history_complete'):
        limits.append('ACTIVITY_LIST_INCOMPLETE')
    if account.get('money_dropped'):
        limits.append('MONEY_ROWS_NOT_READ')
    if account.get('unread'):
        limits.append('MONEY_ROWS_UNREADABLE')
    if not any(n['node'] == result['wallet'] for n in result['nodes']):
        limits.append('TRADING_WALLET_HISTORY_NOT_READ')
    funding, exits = direction_state(result, 'funding'), direction_state(result, 'cashout')
    chain = money_chain(result, rows) if rows is not None else None
    work = Counter(limits) + Counter(funding['work_left']) + Counter(exits['work_left'])
    blocked = []
    if not work:
        if not funding['read']:
            blocked.append('NO_FUNDING_READ')
        if chain is None or chain['reconciled'] is None:
            blocked.append('MONEY_NOT_CHECKED')
        elif not chain['reconciled']:
            blocked.append('MONEY_DOES_NOT_CLOSE')
    processing = WORK_LEFT if work else BLOCKED if blocked else COMPLETE
    return dict(
        processing=processing, work_left=dict(work), blocked_by=blocked,
        polymarket_history=dict(state='COMPLETE' if not (set(limits) & {'ACTIVITY_LIST_INCOMPLETE', 'MONEY_ROWS_NOT_READ', 'MONEY_ROWS_UNREADABLE'}) else 'INCOMPLETE', rows=account.get('rows'), money_listed=account.get('money_listed'), money_not_read=account.get('money_dropped', 0), money_unreadable=len(account.get('unread') or [])),
        funding=dict(funding, state='WORK_LEFT' if funding['work_left'] else 'REBUILT' if funding['read'] else 'NONE_FOUND'),
        exits=dict(exits, state='WORK_LEFT' if exits['work_left'] else 'REBUILT' if exits['read'] else 'NONE_OBSERVED'),
        frontiers=dict(named=funding['named_branches'] + exits['named_branches'], unnamed_shared=funding['unnamed_shared_branches'] + exits['unnamed_shared_branches'], unproved_bridge=funding['unproved_bridge_branches'] + exits['unproved_bridge_branches']),
        gaps=dict(Counter(funding['gaps']) + Counter(exits['gaps'])),
        chain=chain)
