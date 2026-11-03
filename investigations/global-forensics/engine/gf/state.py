"""Is a file finished? A written trace.json is not a finished file, and money that closes is not a finished trace. Two questions stay apart.

ACCOUNTING_RECONCILED: on a complete activity list, deposits and direct moves, plus trading cash, minus withdrawals, equal the balance read on chain. It says nothing about who paid or who was paid.

The trace has one of three states:
- TRACE_COMPLETE_TO_PUBLIC_FRONTIERS: every deposit and withdrawal row has its path for its amount, the books close, and every branch ended for a documented reason: nothing further on a complete history, a named service or verified contract, or a hub measured in the file.
- WORK_LEFT: a read, a budget, a branch or a check is still open. A budget is never a frontier.
- BLOCKED_BY_DATA: nothing is left to read here, and what is needed is not public. Each motive is written.

Work outranks a block, so a blocked file has truly nothing left to do. Any stop this module does not know counts as work, so a new reason can never pass as finished. No state asks for a civil identity or a platform's internal records.
"""
from collections import Counter

from . import ledger_pnl

WORK = ('NODE_BUDGET', 'DEPTH_BUDGET', 'LIGHT_FLOW_CAP', 'READ_FAILED', 'WALLET_ROWS_NOT_CHECKED', 'WINDOW_SCAN_NEEDED', 'SERVICE_OR_SHARED:UNREAD', 'AMBIGUOUS_PATH', 'NON_EVM_READ_SEPARATELY')  # more budget, a retry, a scan or a decoder can clear these
END = ('NO_FLOW_IN_WINDOW', 'NO_LATER_OUTFLOW', 'NO_SPEND_HOLDS_VALUE', 'WALLET_FILLS_NOT_FOLLOWED', 'WALLET_ROWS_PAST_ACTIVITY_LIST')
MONEY_ROLES = ('deposit_path', 'withdrawal_path', 'transfer', 'bridge_payout', 'bridge_deposit', 'internal_to_dossier')
ROW_PATHS = (('funding', 'DEPOSIT', ('deposit_path', 'bridge_payout')), ('cashout', 'WITHDRAWAL', ('withdrawal_path', 'bridge_deposit')))
COLLATERAL = ('USDC', 'USDC.e', 'pUSD')
RECONCILE_USD = 1.0  # rounding across many activity rows: the named accounts close within cents
DUST_SUM_USD = 100.0  # moves under 1 USD each stop being dust once they add up to this
SOURCE_LIMIT = 'a full page within one block'  # the explorer cannot page inside a block: more budget does not help. Every other cap is ours
ACCOUNTING_RECONCILED, NOT_RECONCILED, NOT_CHECKED = 'ACCOUNTING_RECONCILED', 'NOT_RECONCILED', 'NOT_CHECKED'
TRACE_COMPLETE, WORK_LEFT, BLOCKED_BY_DATA = 'TRACE_COMPLETE_TO_PUBLIC_FRONTIERS', 'WORK_LEFT', 'BLOCKED_BY_DATA'
value = lambda e: int(e['raw_amount']) / 10 ** int(e['decimals'] or 0)
row_tx = lambda r: r.get('transaction_hash') or r.get('transactionHash')


def sort_stop(stop):
    """(kind, motive), kind being work, end, frontier or blocked. Only what is listed here can end a branch."""
    reason = stop['reason']
    if reason in WORK:
        return 'work', reason
    if reason in END:
        return 'end', reason
    if reason == 'DUST_NOT_FOLLOWED':
        return ('end', reason) if stop.get('usd', DUST_SUM_USD) < DUST_SUM_USD else ('work', 'DUST_SUM_NOT_FOLLOWED')
    if reason == 'HISTORY_INCOMPLETE':
        parts = stop.get('parts') or {}
        return ('blocked', 'EXPLORER_CANNOT_PAGE_INSIDE_A_BLOCK') if parts and all(v == SOURCE_LIMIT for v in parts.values()) else ('work', reason)
    if reason == 'BRIDGE_HOP_NOT_PROVEN':
        if stop.get('hop_status') == 'success' and stop.get('proof') is False and not stop.get('proof_error'):
            return 'blocked', 'BRIDGE_ID_ABSENT_ON_BOTH_CHAINS'  # both sides read, and the id is on neither
        return 'work', 'BRIDGE_FAR_SIDE_NOT_READ'
    if reason == 'SERVICE_OR_SHARED:CONTRACT':
        if stop.get('name'):
            return 'frontier', reason
        motive = {'NOT_PUBLISHED': 'CONTRACT_SOURCE_NOT_PUBLISHED', 'NO_FREE_EXPLORER': 'CONTRACT_NAME_NOT_READABLE_ON_THIS_CHAIN'}.get(stop.get('source_status'))
        return ('blocked', motive) if motive else ('work', 'CONTRACT_NOT_IDENTIFIED')
    if reason == 'SERVICE_OR_SHARED:SERVICE':
        return ('frontier', reason) if stop.get('name') else ('work', 'SERVICE_WITHOUT_A_NAME')
    if reason == 'SERVICE_OR_SHARED:HUB_MEASURED':
        return ('frontier', reason) if stop.get('name') or stop.get('nonce') is not None or stop.get('kind') == 'SOLANA' else ('work', 'HUB_WITHOUT_A_MEASURE')
    if reason == 'HUB_AT_READ':
        return ('frontier', reason) if stop.get('value_counterparties') else ('work', 'HUB_WITHOUT_A_MEASURE')
    return 'work', reason


def rows_not_traced(result, rows, direction, kind, roles):
    """Activity rows of this kind with no path in the file for their amount, in USD. A gas transfer or any other edge cannot stand in for one."""
    paid = Counter()
    for e in result['edges']:
        if e['direction'] == direction and e['role'] in roles:
            paid[e['transaction_hash']] += value(e)
    missing = [r for r in rows if r.get('type') == kind and abs(paid[row_tx(r)] - float(r.get('usdc_size') or r.get('usdcSize') or 0)) > RECONCILE_USD]
    return len(missing), round(sum(float(r.get('usdc_size') or r.get('usdcSize') or 0) for r in missing), 2)


def direction_state(result, direction, rows=None):
    work, blocked, named, unnamed = Counter(), Counter(), Counter(), 0
    hubs = {(s['address'], s['chain']) for s in result['stops'] if s['direction'] == direction and s['reason'] == 'HUB_AT_READ' and s.get('value_counterparties')}
    for s in result['stops']:
        if s['direction'] != direction:
            continue
        if s['reason'] == 'HISTORY_INCOMPLETE' and (s['address'], s['chain']) in hubs:  # the part read already measures a hub: reading the rest changes nothing
            continue
        kind, motive = sort_stop(s)
        if kind == 'work':
            work[motive] += 1
        elif kind == 'blocked':
            blocked[motive] += 1
        elif kind == 'frontier':
            if s.get('name'):
                named[s['name']] += 1
            else:
                unnamed += 1
    untraced_usd = 0.0
    if rows is not None:
        kind, roles = next((k, r) for d, k, r in ROW_PATHS if d == direction)
        count, untraced_usd = rows_not_traced(result, rows, direction, kind, roles)
        if count:
            work[kind + '_ROW_NOT_TRACED'] += count
    money = sum(e['direction'] == direction and e['role'] in MONEY_ROLES for e in result['edges'])
    return dict(work_left=dict(work), blocked_by=dict(blocked), named_frontier=named.most_common(12), named_branches=sum(named.values()), measured_hub_branches=unnamed, untraced_row_usd=untraced_usd, money_edges=money, read=bool(money))


def money_chain(result, rows):
    """Funding, trading, gains, exits, from the activity and the wallet's own moves on Polygon, the chain of the balance read. Moves inside an activity row are counted there, never twice. Open positions are outside cash and shown apart."""
    books = ledger_pnl.account(rows)
    wallet, listed = result['wallet'], {row_tx(r) for r in rows}
    direct = [e for e in result['edges'] if e['transaction_hash'] not in listed and e.get('token') in COLLATERAL and e['role'] in MONEY_ROLES and e.get('source') != 'rpc:137' and e.get('chain_id') == 137]
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


def accounting_state(chain, account):
    """(state, the check still open). A list cut short or an account with no flow closes nothing, whatever its residual."""
    if chain is None:
        return NOT_CHECKED, 'ACTIVITY_ROWS_NOT_READ'
    if not account.get('history_complete'):
        return NOT_CHECKED, None  # already counted as ACTIVITY_LIST_INCOMPLETE
    if chain['reconciled'] is None:
        return NOT_CHECKED, 'BALANCE_NOT_READ'
    if not (chain['deposits'] or chain['direct_in'] or chain['withdrawals'] or chain['direct_out'] or chain['buys'] or chain['sells'] or chain['redeems']):
        return NOT_CHECKED, None  # nothing to reconcile: NO_FUNDER_OBSERVED says the rest
    return (ACCOUNTING_RECONCILED, None) if chain['reconciled'] else (NOT_RECONCILED, 'ACCOUNTING_NOT_RECONCILED')


def side_state(side, none):
    return WORK_LEFT if side['work_left'] else BLOCKED_BY_DATA if side['blocked_by'] else 'REBUILT' if side['read'] else none


def file_state(result, rows=None):
    account = result.get('account') or {}
    limits = []
    if result.get('mode') != 'full':  # a file that does not say it is full is not
        limits.append('LIGHT_MODE')
    if not account.get('history_complete'):
        limits.append('ACTIVITY_LIST_INCOMPLETE')
    if account.get('money_dropped'):
        limits.append('MONEY_ROWS_NOT_READ')
    if account.get('unread'):
        limits.append('MONEY_ROWS_UNREADABLE')
    if not any(n['node'] == result['wallet'] for n in result['nodes']):
        limits.append('TRADING_WALLET_HISTORY_NOT_READ')
    funding, exits = direction_state(result, 'funding', rows), direction_state(result, 'cashout', rows)
    chain = money_chain(result, rows) if rows is not None else None
    accounting, check = accounting_state(chain, account)
    windows = sum(n.get('status') == 'WINDOW_COMPLETE' for n in result['nodes'])  # a chosen time range: the rest of that address's history is unread
    work = Counter(limits) + Counter(funding['work_left']) + Counter(exits['work_left']) + Counter({check: 1} if check else {}) + Counter(READ_IN_WINDOWS_ONLY=windows)
    blocked = Counter(funding['blocked_by']) + Counter(exits['blocked_by'])
    if not funding['read'] and not funding['work_left']:
        blocked['NO_FUNDER_OBSERVED'] += 1
    processing = WORK_LEFT if work else BLOCKED_BY_DATA if blocked else TRACE_COMPLETE
    return dict(
        processing=processing, accounting=accounting, work_left=dict(work), blocked_by=dict(blocked),
        polymarket_history=dict(state='COMPLETE' if not (set(limits) & {'ACTIVITY_LIST_INCOMPLETE', 'MONEY_ROWS_NOT_READ', 'MONEY_ROWS_UNREADABLE'}) else 'INCOMPLETE', rows=account.get('rows'), money_listed=account.get('money_listed'), money_not_read=account.get('money_dropped', 0), money_unreadable=len(account.get('unread') or [])),
        funding=dict(funding, state=side_state(funding, 'NONE_FOUND')),
        exits=dict(exits, state=side_state(exits, 'NONE_OBSERVED')),
        frontiers=dict(named=funding['named_branches'] + exits['named_branches'], measured_hub=funding['measured_hub_branches'] + exits['measured_hub_branches']),
        chain=chain)
