"""What can be said about which inflow fed an outflow, for one address and one token.

Tokens are fungible, so "these exact dollars" has no meaning. What holds without any convention is a pair of bounds: an
inflow's share of an outflow cannot exceed what is left of it, and must be at least what the rest of the balance cannot cover.
FIFO and LIFO are shown as conventions, never as facts. Amounts are integers in raw units. Unexplained amounts stay visible.
"""


def replay(moves, address, opening=0):
    """Balance through time from time-ordered moves. A negative balance means history is missing, and says so."""
    address = address.lower()
    balance, missing, states = opening, 0, []
    for m in sorted(moves, key=lambda x: (x['timestamp'], x['block_number'], x.get('log_index') if x.get('log_index') is not None else -1)):
        raw = int(m['raw_amount'])
        if m['to'] == address and m['from'] != address:
            balance += raw
        elif m['from'] == address and m['to'] != address:
            balance -= raw
            if balance < 0:
                missing += -balance
                balance = 0
        states.append(dict(move=m, balance=balance))
    return dict(closing=balance, missing_raw=missing, states=states)


def bounds(moves, address, outflow, opening=0):
    """For one outflow: [lower, upper] raw units that each earlier inflow can have contributed. `unknown_opening` is the part no read inflow can explain."""
    address = address.lower()
    ordered = sorted(moves, key=lambda x: (x['timestamp'], x['block_number'], x.get('log_index') if x.get('log_index') is not None else -1))
    balance = opening
    outstanding = []  # upper bound of what is left of each inflow: it can only shrink when the balance forces it
    wanted = int(outflow['raw_amount'])
    for m in ordered:
        if m is outflow or (m['transaction_hash'] == outflow['transaction_hash'] and m.get('log_index') == outflow.get('log_index') and m['from'] == address and int(m['raw_amount']) == wanted):
            break
        raw = int(m['raw_amount'])
        if m['to'] == address and m['from'] != address:
            balance += raw
            outstanding.append(dict(move=m, left=raw))
        elif m['from'] == address and m['to'] != address:
            balance = max(0, balance - raw)
            for item in outstanding:
                item['left'] = min(item['left'], balance)
    out = []
    for item in outstanding:
        if item['left'] > 0:
            others = balance - item['left']
            out.append(dict(tx=item['move']['transaction_hash'], source=item['move']['from'], left_raw=item['left'], lower_raw=max(0, wanted - others), upper_raw=min(wanted, item['left'])))
    return dict(outflow_raw=wanted, balance_before_raw=balance, unexplained_raw=max(0, wanted - balance), sources=out)


def convention(moves, address, rule='FIFO', opening=0):
    """FIFO or LIFO allocation of every outflow to inflows. A convention for reading, written as such on every row."""
    if rule not in ('FIFO', 'LIFO'):
        raise ValueError(rule)
    address = address.lower()
    lots = [dict(source='OPENING_BALANCE', tx=None, left=opening)] if opening else []
    rows, unexplained = [], 0
    for m in sorted(moves, key=lambda x: (x['timestamp'], x['block_number'], x.get('log_index') if x.get('log_index') is not None else -1)):
        raw = int(m['raw_amount'])
        if m['to'] == address and m['from'] != address:
            lots.append(dict(source=m['from'], tx=m['transaction_hash'], left=raw))
        elif m['from'] == address and m['to'] != address:
            need = raw
            while need > 0 and lots:
                lot = lots[0] if rule == 'FIFO' else lots[-1]
                take = min(need, lot['left'])
                rows.append(dict(out_tx=m['transaction_hash'], destination=m['to'], from_source=lot['source'], in_tx=lot['tx'], raw=take, rule=rule, meaning='accounting convention, not proof these units moved'))
                lot['left'] -= take
                need -= take
                if not lot['left']:
                    lots.remove(lot)
            if need:
                unexplained += need
                rows.append(dict(out_tx=m['transaction_hash'], destination=m['to'], from_source='UNEXPLAINED', in_tx=None, raw=need, rule=rule, meaning='no read inflow can cover this'))
    return dict(rows=rows, unexplained_raw=unexplained, closing_raw=sum(l['left'] for l in lots))
