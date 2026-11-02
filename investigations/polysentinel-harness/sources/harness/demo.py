"""Synthetic demonstration data in the collector's real schema. It proves mechanics, never detection power: every address, hash and case here is invented.

Five cases are planted among ordinary trading, each with a known expected outcome, so the end-to-end test can say whether the whole chain decided correctly.
"""
import hashlib
import json
import random
from pathlib import Path

from polysentinel.db import Store

T0 = 1_800_000_000
HIGH_RISK_TITLE = 'Will the company announce the acquisition?'
ORDINARY_TITLE = 'Will the committee approve the budget?'
EXPECTED = dict(true_case='validated', public_decoy='rejected', two_sided_decoy='rejected', no_receipts='needs_data', tampered_receipts='rejected')


def h(text, n=64):
    return hashlib.sha256(text.encode()).hexdigest()[:n]


def address(text):
    return '0x' + h('wallet:' + text, 40)


def tx(text):
    return '0x' + h('tx:' + text)


def condition(text):
    return '0x' + h('condition:' + text)


def token(text):
    return str(int(h('token:' + text, 30), 16))


def put_event(store, event, title, end, closed=False, winner=None, cx=None):
    """One event, one market, two tokens."""
    tokens = [token(event + ':yes'), token(event + ':no')]
    prices = ['1', '0'] if winner == 'yes' else ['0', '1'] if winner == 'no' else ['0.5', '0.5']
    raw = dict(description='Resolves according to the official announcement.', clobTokenIds=json.dumps(tokens), outcomePrices=json.dumps(prices), closed=closed, spread=.01)
    store.put('event', event, dict(id=event, title=title, tags=[], observed_at=T0 - 40 * 86400), observed_at=T0 - 40 * 86400, conn=cx)
    store.put('market', 'm' + event, dict(id='m' + event, event_id=event, question=title, end_date=end, closed=closed, active=not closed, liquidity=100000, observed_at=T0 - 40 * 86400, condition_id=condition(event), raw=raw), observed_at=T0 - 40 * 86400, conn=cx)
    return tokens


def put_trade(store, key, wallet, event, side_token, ts, nominal, price, title, side='BUY', cx=None):
    payload = dict(wallet=wallet, timestamp=ts, condition_id=condition(event), token_id=side_token, side=side, size=round(nominal / price, 6), price=price, nominal=nominal, transaction_hash=tx(key), outcome='Yes', event_id=event, market_id='m' + event, raw=dict(title=title))
    store.put('trade', key, payload, observed_at=ts + 60, conn=cx)
    return payload


def receipt_for(payload, factor=1.0):
    raw = int(round(payload['nominal'] * 1e6 * factor))
    fill = dict(transaction_hash=payload['transaction_hash'], token_id=payload['token_id'], maker=payload['wallet'], taker='0x' + 'ab' * 20, side=payload['side'], nominal_raw=str(raw), shares_raw=str(int(payload['size'] * 1e6)), removed=False, log_index=1)
    return dict(transaction_hash=payload['transaction_hash'], status=1, fills=[fill])


def case_start(order):
    return T0 + (order - 4) * 86400


def plant(store, name, cx, *, order, price=.3, two_sided=False):
    """One case a day, each larger than the last: an earlier case counts among the controls of a later one, as it should, so it must stay smaller to leave the later one rare."""
    event, nominal, start = 'case_' + name, 20000 if two_sided else 50000 + 10000 * order, case_start(order)
    tokens = put_event(store, event, HIGH_RISK_TITLE, T0 + 40 * 86400, cx=cx)
    rows = []
    for i in range(3):
        wallet = address(f'{name}:{i}')
        rows.append(put_trade(store, f'{name}:{i}:a', wallet, event, tokens[0], start + 50 + i, nominal, price, HIGH_RISK_TITLE, cx=cx))
        if two_sided:
            rows.append(put_trade(store, f'{name}:{i}:b', wallet, event, tokens[1], start + 80 + i, nominal, 1 - price, HIGH_RISK_TITLE, cx=cx))
    return event, rows


def build(root, seed=7, wallets=1500, events=60, days=14, batch_rows=300, plant_cases=True):
    root = Path(root)
    store = Store(root / 'demo_collector')
    rng = random.Random(seed)
    receipts = {}
    with store.transaction() as cx:
        tokens = {}
        for i in range(events):
            settled = i % 2 == 0
            tokens[i] = put_event(store, f'e{i}', ORDINARY_TITLE, T0 + 40 * 86400, closed=settled, winner=rng.choice(('yes', 'no')) if settled else None, cx=cx)
        n = 0
        for w in range(wallets):
            wallet = address(f'bg{w}')
            for _ in range(rng.randrange(3, 7)):
                i = rng.randrange(events)
                n += 1
                price = rng.choice((.15, .3, .6, .9))
                put_trade(store, f'bg{n}', wallet, f'e{i}', tokens[i][rng.randrange(2)], T0 - rng.randrange(0, days * 86400), rng.uniform(100, 1500), price, ORDINARY_TITLE, cx=cx)
        cases = {}
        if plant_cases:
            event, rows = plant(store, 'two_sided_decoy', cx, order=0, two_sided=True)
            cases['two_sided_decoy'] = event
            receipts.update({r['transaction_hash']: receipt_for(r) for r in rows})
            event, rows = plant(store, 'public_decoy', cx, order=1)
            cases['public_decoy'] = event
            receipts.update({r['transaction_hash']: receipt_for(r) for r in rows})
            store.put('public_milestone', event, dict(verified=True, result_available=True, public_at=case_start(1) - 7200, public_observed_at=case_start(1) - 7000, source_url='https://example.invalid/announcement', proof_level='demo', milestone_type='public_information'), observed_at=case_start(1) - 7000, conn=cx)
            event, rows = plant(store, 'tampered_receipts', cx, order=2)
            cases['tampered_receipts'] = event
            receipts.update({r['transaction_hash']: receipt_for(r, factor=.5) for r in rows})
            event, rows = plant(store, 'no_receipts', cx, order=3)
            cases['no_receipts'] = event
            event, rows = plant(store, 'true_case', cx, order=4)
            cases['true_case'] = event
            receipts.update({r['transaction_hash']: receipt_for(r) for r in rows})
    store.conn.execute('PRAGMA wal_checkpoint(TRUNCATE)')
    store.conn.close()
    (root / 'demo_receipts.json').write_text(json.dumps(receipts))
    config = dict(source=dict(database=str(root / 'demo_collector/data/polysentinel.sqlite3'), heartbeat=None, batch_rows=batch_rows, batches_per_task=4),
                  chain=dict(type='file', path=str(root / 'demo_receipts.json')),
                  pipeline=dict(max_lag_s=None), resources=dict(max_load=1000, root_quota_bytes=2_000_000_000), recovery=dict(backoff_base_s=.05, backoff_cap_s=.2, read_backoff_s=.01))
    (root / 'config.json').write_text(json.dumps(config, indent=1))
    return dict(cases=cases, trades=n, receipts=len(receipts))
