"""Read one transaction from nodes and return the moves it proves. This is the only place a level rises.

Two nodes at different hosts must agree on the block hash and on every log; one agreeing node gives ONCHAIN_CONFIRMED,
two give REVERIFIED. A failed transaction moves nothing. An internal native move has no log outside Polygon: a receipt
cannot show it, and it stays LISTED unless a call trace does.
"""
import hashlib
import json

from .events import NATIVE, ONCHAIN, REVERIFIED, TOKENS, FRESH
from .keccak import selector
from .net import RPC, Refused

TRANSFER = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
POL_SYSTEM = '0x0000000000000000000000000000000000001010'
LOG_TRANSFER = '0xe6497e3ee548a3372136af2fcb0696db31fc6cf20260707645068bd3fe97f3c4'


def _digest(receipt):
    keep = dict(status=receipt.get('status'), block=receipt.get('blockHash'), logs=[(l.get('address', '').lower(), l.get('logIndex'), [t.lower() for t in l.get('topics') or []], (l.get('data') or '').lower()) for l in receipt.get('logs') or []])
    return hashlib.sha256(json.dumps(keep, sort_keys=True).encode()).hexdigest()


def moves_in(chain, tx, receipt, transaction, timestamp, level):
    """Every token and native move a receipt proves. Unknown tokens are kept, marked, and never followed."""
    block_hash = receipt['blockHash'].lower()
    block = int(receipt['blockNumber'], 16)
    success = int(receipt.get('status', '0x1'), 16) == 1
    common = dict(chain_id=chain, block_number=block, block_hash=block_hash, transaction_hash=tx.lower(), timestamp=timestamp, level=level, data_class=FRESH, success=success, source=f'rpc:{chain}')
    out = []
    value = int((transaction or {}).get('value') or '0x0', 16)
    if transaction and value:
        out.append(dict(common, log_index=None, kind='native', contract=None, token=NATIVE[chain], decimals=18, raw_amount=str(value), decoding='transaction value, receipt status', **{'from': transaction['from'].lower(), 'to': (transaction.get('to') or '').lower()}))
    for log in receipt.get('logs') or []:
        topics = log.get('topics') or []
        if not topics:
            continue
        address = log['address'].lower()
        index = int(log['logIndex'], 16)
        if topics[0] == TRANSFER and len(topics) == 3 and len(log.get('data') or '') == 66:
            known = TOKENS.get(chain, {}).get(address)
            out.append(dict(common, log_index=index, kind='erc20', contract=address, token=known[0] if known else None, token_known=bool(known), decimals=known[1] if known else 0, raw_amount=str(int(log['data'], 16)), decoding='erc20 Transfer log from receipt', **{'from': '0x' + topics[1][-40:], 'to': '0x' + topics[2][-40:]}))
        elif chain == 137 and topics[0] == LOG_TRANSFER and address == POL_SYSTEM and len(topics) == 4:
            source, target = '0x' + topics[2][-40:], '0x' + topics[3][-40:]
            raw = int(log['data'][2:66], 16)
            if not (transaction and value and source == transaction['from'].lower() and target == (transaction.get('to') or '').lower() and raw == value):
                out.append(dict(common, log_index=index, kind='internal', contract=None, token='POL', decimals=18, raw_amount=str(raw), decoding='Polygon LogTransfer from receipt', **{'from': source, 'to': target}))
    return out


def read_tx(net, chain, tx, second_opinion=True):
    """(moves, record). The record is what a reader needs to redo the check. A transaction no node has is a refusal, not an empty result."""
    tx = tx.lower()
    receipt, meta = net.rpc('eth_getTransactionReceipt', [tx], chain)
    if receipt is None or receipt.get('transactionHash', '').lower() != tx:
        raise Refused(f'node returned no or another receipt for {tx}')
    transaction, _ = net.rpc('eth_getTransactionByHash', [tx], chain)
    number = int(receipt['blockNumber'], 16)
    block, _ = net.rpc('eth_getBlockByNumber', [hex(number), False], chain)
    if block['hash'].lower() != receipt['blockHash'].lower():
        raise Refused(f'{tx}: receipt block hash differs from the canonical block {number}')
    timestamp = int(block['timestamp'], 16)
    digest = _digest(receipt)
    record = dict(chain_id=chain, tx=tx, block_number=number, block_hash=receipt['blockHash'].lower(), timestamp=timestamp, status=int(receipt.get('status', '0x1'), 16), submitter=(transaction or {}).get('from', '').lower(), to=((transaction or {}).get('to') or '').lower(), selector=((transaction or {}).get('input') or '')[:10], first_host=meta['host'], first_origin=meta['origin'], receipt_sha256=digest, logs=len(receipt.get('logs') or []), second_host=None, agree=None)
    level = ONCHAIN
    if second_opinion:
        for endpoint in RPC[chain]:
            host = endpoint.split('/')[2]
            if host == meta['host']:
                continue
            try:
                other, other_meta = net.rpc('eth_getTransactionReceipt', [tx], chain, endpoints=[endpoint])
            except Refused:
                continue
            if other:
                record.update(second_host=host, agree=_digest(other) == digest)
                if not record['agree']:
                    raise Refused(f'{tx}: {meta["host"]} and {host} disagree on the receipt')
                level = REVERIFIED
                break
    return moves_in(chain, tx, receipt, transaction, timestamp, level), record


def owner_at(net, contract, block, chain=137):
    """owner() at a historical block: a wallet's owner today is not proof of its owner then."""
    value, meta = net.rpc('eth_call', [dict(to=contract, data=selector('owner()')), hex(block)], chain)
    return ('0x' + value[-40:].lower() if value and len(value) >= 42 else None), meta
