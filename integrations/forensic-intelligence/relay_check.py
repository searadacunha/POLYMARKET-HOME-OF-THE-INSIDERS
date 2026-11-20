#!/usr/bin/env python3
"""Check archived Relay request records against chain receipts, so the records stay usable after the API is gone.

For every request of the given addresses found in ARCHIVE_DIR/raw/user_<address>_p*.json.gz, each origin and
destination transaction on a supported chain is read on two JSON-RPC endpoints. A leg is verified when both show
a successful transaction that moves exactly the recorded amount of the recorded currency from the user (origin)
or to the recipient (destination). Responses are saved gzip-compressed with their SHA-256 in OUT_DIR.
A verified leg shows that the chain agrees with the record; it does not show who controls either address.

usage: relay_check.py ARCHIVE_DIR OUT_DIR ADDRESS [ADDRESS ...]
"""
import csv
import glob
import gzip
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from value_trace import CHAINS, TRANSFER_TOPIC, Store, rpc  # noqa: E402

RPC = {chain_id: (name, endpoints) for name, (chain_id, _, endpoints) in CHAINS.items()}
NATIVE = '0x' + '0' * 40
FIELDS = ('request_id', 'created_utc', 'status', 'user', 'recipient', 'side', 'chain_id', 'transaction_hash', 'block_number',
          'time_utc', 'currency', 'amount_raw', 'counterparty', 'verified')


def topic(address):
    return '0x' + address.lower()[2:].rjust(64, '0')


def leg(store, chain_id, tx, currency, amount, holder, outgoing, offline=False):
    """(verified, block, time, counterparty) for one transaction; verified is NOT_CHECKED on an unsupported chain.

    A native-coin leg paid inside a contract call is NOT_CHECKED as soon as the first endpoint shows it: no endpoint
    can verify it by this method, so the second is not read for that leg."""
    if chain_id not in RPC or not tx.startswith('0x'):
        return 'NOT_CHECKED', '', '', ''
    name, endpoints = RPC[chain_id]
    seen = []
    for i, url in enumerate(endpoints):
        def call(kind, method, params):
            return rpc(store, f'rpc{i}_{name}_{kind}_{params[0].lower()}', url, method, params, offline=offline)
        receipt = call('receipt', 'eth_getTransactionReceipt', [tx])
        found = None
        if currency.lower() == NATIVE:  # native coin: the value of the transaction itself
            body = call('tx', 'eth_getTransactionByHash', [tx])
            mine, other = (body.get('from'), body.get('to')) if outgoing else (body.get('to'), body.get('from'))
            if mine and mine.lower() == holder.lower() and int(body.get('value', '0x0'), 16) == amount:
                found = other.lower()
            elif receipt.get('status') == '0x1':
                # shortcut: native coin moved inside a contract call is not checked, read traces when a case depends on it
                return 'NOT_CHECKED', int(receipt['blockNumber'], 16), '', ''
        else:
            for log in receipt.get('logs', []):
                if log['address'].lower() == currency.lower() and log['topics'][0].lower() == TRANSFER_TOPIC and len(log['topics']) == 3 \
                        and log['topics'][1 if outgoing else 2].lower() == topic(holder) and int(log['data'], 16) == amount:
                    found = '0x' + log['topics'][2 if outgoing else 1][-40:]
        block = int(receipt['blockNumber'], 16) if receipt.get('blockNumber') else None
        stamp = ''
        if block is not None:
            head = call('block', 'eth_getBlockByNumber', [hex(block), False])
            stamp = datetime.fromtimestamp(int(head['timestamp'], 16), timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        seen.append((receipt.get('status') == '0x1' and found is not None, block, stamp, found or ''))
    agreed = all(s == seen[0] for s in seen) and seen[0][0]
    return ('true' if agreed else 'false',) + seen[0][1:]


def check(archive_dir, out_dir, addresses, write=True, offline=False):
    """offline=True raises on a response that is not saved instead of fetching it."""
    store, rows = Store(out_dir), []
    for address in addresses:
        files = sorted(glob.glob(f'{archive_dir}/raw/user_{address.lower()}_p*.json.gz'))
        if not files:
            raise FileNotFoundError(f'no archived Relay page for {address}')
        for name in files:
            for request in json.load(gzip.open(name)).get('requests', []):
                data = request.get('data') or {}
                meta = data.get('metadata') or {}
                for side, txs, money, holder in (('origin', data.get('inTxs') or [], meta.get('currencyIn') or {}, request['user']),
                                                 ('destination', data.get('outTxs') or [], meta.get('currencyOut') or {}, request['recipient'])):
                    currency = (money.get('currency') or {}).get('address') or ''
                    for tx in txs:
                        verified, block, stamp, other = leg(store, tx.get('chainId'), tx.get('hash') or '', currency,
                                                            int(money.get('amount') or 0), holder, side == 'origin', offline)
                        rows.append({'request_id': request['id'], 'created_utc': request['createdAt'], 'status': request['status'],
                                     'user': request['user'], 'recipient': request['recipient'], 'side': side, 'chain_id': tx.get('chainId'),
                                     'transaction_hash': tx.get('hash'), 'block_number': block, 'time_utc': stamp, 'currency': currency,
                                     'amount_raw': money.get('amount'), 'counterparty': other, 'verified': verified})
    rows = sorted({(r['request_id'], r['side'], r['transaction_hash']): r for r in rows}.values(), key=lambda r: (r['created_utc'], r['side']), reverse=False)
    if write:
        with (Path(out_dir) / 'relay_check.csv').open('w', newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator='\n')
            writer.writeheader()
            writer.writerows(rows)
    return rows


if __name__ == '__main__':
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    result = check(sys.argv[1], sys.argv[2], sys.argv[3:])
    counts = {v: sum(1 for r in result if r['verified'] == v) for v in ('true', 'false', 'NOT_CHECKED')}
    print(f"{len(result)} legs: {counts['true']} verified, {counts['false']} not verified, {counts['NOT_CHECKED']} on chains not checked")
    sys.exit(1 if counts['false'] else 0)
