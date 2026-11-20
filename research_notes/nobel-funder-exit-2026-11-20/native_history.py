#!/usr/bin/env python3
"""Native-coin history and account type of a few addresses, from saved public indexer pages.

value_trace.py follows one token. This companion reads what a token ledger cannot show: who first sent native
coin (gas) to an address, what an address is (plain key, contract, EIP-7702 delegation), and which tokens moved
in given transactions. Pages are saved gzip-compressed with their SHA-256 (same store as value_trace.py); with
every page already saved the script makes no network call, so summary.json can be re-derived offline.

usage: native_history.py STORE_DIR CONFIG_JSON
config: {"addresses": {"label": "0x..."}, "internal": ["label"], "transactions": ["0x..."]}
internal lists the labels whose internal transactions are read too (payouts made inside contract calls).
"""
import json
import sys
import time
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'integrations' / 'forensic-intelligence'))
sys.path.insert(0, str(Path(__file__).resolve().parent))  # lets the script run beside a copy of value_trace.py
from value_trace import Store, http  # noqa: E402

BASE = 'https://eth.blockscout.com/api/v2'
MIN_WEI = 5 * 10 ** 14  # 0.0005 native coin: below this a transfer is dust or a poisoning bait


def party(obj):
    obj = obj or {}
    return {'address': obj.get('hash'), 'name': obj.get('name'), 'is_contract': bool(obj.get('is_contract')),
            'tags': sorted({t.get('name', '') for t in ((obj.get('metadata') or {}).get('tags') or [])})}


def summarize(store_dir, config, offline=False):
    """offline=True raises on a page that is not saved instead of fetching it."""
    store = Store(store_dir)

    def get(name, path, params=None):
        if not store.has(name):
            if offline:
                raise FileNotFoundError(f'{name}: page needed but not saved')
            query = {k: str(v).lower() if isinstance(v, bool) else v for k, v in (params or {}).items()}
            url = BASE + path + ('?' + urllib.parse.urlencode(query) if query else '')
            store.save(name, url, http(url))
            time.sleep(0.3)
        return store.load(name)

    def pages(prefix, path, cap):
        items, params = [], None
        for number in range(cap):
            page = get(f'{prefix}_p{number:03d}', path, params)
            items += page.get('items', [])
            params = page.get('next_page_params')
            if not params:
                return items, True
        return items, False

    out = {'addresses': {}, 'transactions': {}}
    for label, address in config['addresses'].items():
        low = address.lower()
        info = get(f'eth_{low}_info', f'/addresses/{address}')
        txs, complete = pages(f'eth_{low}_txs', f'/addresses/{address}/transactions', 40)
        internal, complete_internal = (pages(f'eth_{low}_internal', f'/addresses/{address}/internal-transactions', 6)
                                       if label in config.get('internal', []) else ([], None))
        moves = []
        for kind, rows in (('transaction', txs), ('internal', internal)):
            for row in rows:
                value = int(row.get('value') or 0)
                if value < MIN_WEI or not row.get('to'):
                    continue
                incoming = row['to']['hash'].lower() == low
                moves.append({'time_utc': row['timestamp'][:19] + 'Z', 'direction': 'in' if incoming else 'out', 'wei': str(value),
                              'kind': kind, 'transaction_hash': row.get('hash') or row.get('transaction_hash'),
                              'method': row.get('method') if kind == 'transaction' else None,
                              'counterparty': party(row['from'] if incoming else row['to'])})
        moves.sort(key=lambda m: (m['time_utc'], m['transaction_hash'] or ''))
        times = sorted(row['timestamp'][:19] + 'Z' for row in txs)
        out['addresses'][label] = {
            'address': address, 'is_contract': bool(info.get('is_contract')), 'proxy_type': info.get('proxy_type'),
            'native_balance_wei_when_read': info.get('coin_balance'),
            'implementations': [{'address': i.get('address_hash') or i.get('address'), 'name': i.get('name')} for i in info.get('implementations') or []],
            'transactions_read': len(txs), 'transactions_complete': complete, 'internal_complete': complete_internal,
            'first_transaction_utc': times[0] if times else None, 'last_transaction_utc': times[-1] if times else None,
            'first_native_inflow': next((m for m in moves if m['direction'] == 'in'), None), 'native_moves': moves}
    for tx in config.get('transactions', []):
        legs = get(f'eth_tx_{tx}_tokentransfers', f'/transactions/{tx}/token-transfers').get('items', [])
        out['transactions'][tx] = [{'token': leg['token'].get('symbol'), 'token_contract': leg['token'].get('address_hash'),
                                    'raw_amount': leg['total']['value'], 'decimals': leg['total']['decimals'],
                                    'from': leg['from']['hash'], 'to': leg['to']['hash']} for leg in legs]
    return out


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    result = summarize(sys.argv[1], json.loads(Path(sys.argv[2]).read_text()))
    (Path(sys.argv[1]) / 'summary.json').write_text(json.dumps(result, indent=1) + '\n')
    for label, a in result['addresses'].items():
        first = a['first_native_inflow']
        print(label, a['address'], 'contract' if a['is_contract'] else 'plain key', a['proxy_type'] or '',
              '| first native inflow:', (first['time_utc'], first['wei'], first['counterparty']['address'], first['counterparty']['tags']) if first else None)
