"""Public receipt evidence. Never infer a taker's outcome from a maker leg."""
import json
import re
from decimal import Decimal
from pathlib import Path

ORDER_V1 = '0xd0a08e8c493f9c94f29311604c9de1b4e8c8d4c06bd0c789af57f2d65bfec0f6'
ORDER_V2 = '0xd543adfd945773f1a62f74f0ee55a5e3b9b1a28262980ba90b1a89f2ea84d8ee'
TRANSFER = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
ADDRESS = re.compile(r'^0x[0-9a-fA-F]{40}$')
HASH = re.compile(r'^0x[0-9a-fA-F]{64}$')


def registry(root):
    return json.loads((Path(root) / 'config/contracts.json').read_text())


def _address(topic):
    if not HASH.fullmatch(topic) or int(topic[2:26], 16):
        raise ValueError('Invalid indexed address')
    return '0x' + topic[-40:].lower()


def _words(data, count):
    if not isinstance(data, str) or not re.fullmatch(r'0x[0-9a-fA-F]*', data) or len(data) != 2 + count * 64:
        raise ValueError('Unexpected ABI data length')
    return [int(data[i:i + 64], 16) for i in range(2, len(data), 64)]


def decode_order(log, contracts):
    address = str(log.get('address', '')).lower()
    contract = next((x for x in contracts['exchanges'] if x['address'].lower() == address), None)
    topics = log.get('topics', [])
    if not contract or not topics or topics[0].lower() not in (ORDER_V1, ORDER_V2):
        return None
    expected = ORDER_V1 if contract['abi_version'] == 'v1' else ORDER_V2
    if topics[0].lower() != expected or len(topics) != 4 or not HASH.fullmatch(topics[1]):
        raise ValueError('Exchange/topic ABI mismatch')
    if expected == ORDER_V1:
        asset_m, asset_t, amount_m, amount_t, fee = _words(log['data'], 5)
        if asset_m == 0 and asset_t != 0:
            side, token, shares, cash = 'BUY', asset_t, amount_t, amount_m
        elif asset_t == 0 and asset_m != 0:
            side, token, shares, cash = 'SELL', asset_m, amount_m, amount_t
        else:
            raise ValueError('Unsupported v1 asset pair; no direction inferred')
        fee_asset = str(asset_t) if asset_t else 'collateral'
        builder = metadata = None
    else:
        side_raw, token, amount_m, amount_t, fee, builder_raw, metadata_raw = _words(log['data'], 7)
        if side_raw not in (0, 1):
            raise ValueError('Unknown order side')
        side = 'BUY' if side_raw == 0 else 'SELL'
        shares, cash = (amount_t, amount_m) if side == 'BUY' else (amount_m, amount_t)
        fee_asset = 'collateral'
        builder, metadata = f'0x{builder_raw:064x}', f'0x{metadata_raw:064x}'
    if not shares:
        raise ValueError('Zero-share fill')
    return {
        'chain_id': 137, 'contract': address, 'contract_name': contract['name'],
        'abi_version': contract['abi_version'], 'abi_source': contract['abi_source'],
        'block_number': int(log['blockNumber'], 16), 'block_hash': log['blockHash'],
        'transaction_hash': log['transactionHash'], 'log_index': int(log['logIndex'], 16),
        'order_hash': topics[1].lower(), 'maker': _address(topics[2]), 'taker': _address(topics[3]),
        'side': side, 'token_id': str(token), 'shares_raw': str(shares), 'nominal_raw': str(cash),
        'maker_amount_raw': str(amount_m), 'taker_amount_raw': str(amount_t),
        'size': float(Decimal(shares) / 1_000_000), 'nominal': float(Decimal(cash) / 1_000_000),
        'price': float(Decimal(cash) / shares), 'amount_decimals': 6,
        'fee_raw': str(fee), 'fee_asset': fee_asset, 'fee': float(Decimal(fee) / 1_000_000),
        'collateral_symbol': contract.get('collateral_symbol'),
        'builder': builder, 'metadata': metadata, 'removed': bool(log.get('removed', False)),
        'role_note': 'maker = propriétaire de cet ordre ; taker peut être exchange, opérateur ou contrepartie',
        'raw': log,
    }


def reconcile(trade, fills):
    """Only the order belonging to this wallet/token/side can corroborate its row."""
    wallet = str(trade.get('wallet', trade.get('proxy_wallet', ''))).lower()
    matching = [f for f in fills if f['maker'] == wallet and f['token_id'] == str(trade['token_id'])
                and f['side'] == trade['side'] and not f.get('removed')]
    size = Decimal(str(trade['size']))
    nominal = Decimal(str(trade['price'])) * size
    groups = {}
    for f in matching:
        groups.setdefault(f['order_hash'], []).append(f)
    options = list(groups.values())
    if len(groups) > 1:
        options.append(matching)
    for rows in options:
        got_size = sum(Decimal(f['shares_raw']) / 1_000_000 for f in rows)
        got_nominal = sum(Decimal(f['nominal_raw']) / 1_000_000 for f in rows)
        # Data API emits rounded floats; tolerance is disclosed, not exact equality.
        tolerance = max(Decimal('0.00001'), abs(nominal) * Decimal('0.000001'))
        if abs(got_size - size) <= Decimal('0.00001') and abs(got_nominal - nominal) <= tolerance:
            return {'status': 'matched', 'proof_level': 'fait transactionnel vérifié',
                    'log_indices': [f['log_index'] for f in rows], 'order_hashes': sorted({f['order_hash'] for f in rows}),
                    'size_onchain': float(got_size), 'nominal_onchain': float(got_nominal),
                    'nominal_tolerance': float(tolerance), 'fee_components': [dict(raw=f['fee_raw'], asset=f['fee_asset']) for f in rows]}
    return {'status': 'amount_mismatch' if matching else 'unmatched', 'proof_level': 'données insuffisantes',
            'log_indices': [f['log_index'] for f in matching],
            'reason': 'Aucun ordre du wallet/token/sens avec montants concordants ; aucune inversion du taker.'}


def transfers(receipt, wallet, contracts):
    known = {x['address'].lower(): x for x in contracts.get('fungible_tokens', [])}
    services = {x['address'].lower(): x for x in contracts.get('infrastructure', [])}
    services.update({x['address'].lower(): x for x in contracts['exchanges']})
    result = []
    for log in receipt.get('logs', []):
        topics = log.get('topics', [])
        token = known.get(str(log.get('address', '')).lower())
        if not token or not topics or topics[0].lower() != TRANSFER:
            continue
        if log.get('removed'):
            raise ValueError('Removed ERC20 Transfer cannot establish a funding edge')
        if not receipt.get('transactionHash') or not receipt.get('blockHash') or str(log.get('transactionHash', '')).lower() != receipt['transactionHash'].lower() or str(log.get('blockHash', '')).lower() != receipt['blockHash'].lower():
            raise ValueError('Inconsistent ERC20 receipt log identity')
        if len(topics) != 3:
            raise ValueError('Malformed ERC20 Transfer topics')
        source, destination = _address(topics[1]), _address(topics[2])
        if wallet.lower() not in (source, destination):
            continue
        amount = _words(log['data'], 1)[0]
        other = source if destination == wallet.lower() else destination
        label = services.get(other)
        result.append({'source': source, 'target': destination, 'token': log['address'].lower(),
                       'symbol': token['symbol'], 'amount_raw': str(amount), 'decimals': token['decimals'],
                       'amount': float(Decimal(amount) / (10 ** token['decimals'])),
                       'transaction_hash': log['transactionHash'], 'log_index': int(log['logIndex'], 16),
                       'block_number': int(log['blockNumber'], 16), 'block_hash': log['blockHash'],
                       'proof_level': 'lien directement observable', 'relation': 'transfert ERC20',
                       'counterparty_label': label['name'] if label else None,
                       'label_source': label.get('source', label.get('abi_source')) if label else None,
                       'infrastructure': bool(label), 'common_control_inferred': False,
                       'caution': 'Transfert direct observé ; financeur économique et contrôle commun non établis.'})
    return result


async def rpc(net, config, method, params):
    allowed = {'eth_chainId', 'eth_blockNumber', 'eth_getTransactionReceipt', 'eth_getBlockByNumber'}
    if method not in allowed:
        raise ValueError('RPC method not permitted')
    errors = []
    for url in config['rpc_urls']:
        try:
            response = await net.request(url, method='POST', json_body={'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params})
            body = response.body
            if not isinstance(body, dict) or 'result' not in body or body.get('error'):
                raise ValueError(str(body.get('error', 'Malformed RPC result'))[:200])
            return body['result'], response.evidence_id
        except Exception as exc:
            if getattr(exc, 'budget_exhausted', False):
                raise
            errors.append(f'{url}: {type(exc).__name__}: {str(exc)[:160]}')
    raise RuntimeError('; '.join(errors))


async def inspect_receipt(store, net, config, transaction_hash, wallet, trade=None, context=None):
    if not HASH.fullmatch(transaction_hash) or not ADDRESS.fullmatch(wallet):
        raise ValueError('Invalid transaction or wallet')
    context = context if context is not None else {}
    evidence = []
    if 'chain_id' not in context:
        raw, ev = await rpc(net, config, 'eth_chainId', [])
        context['chain_id'] = int(raw, 16)
        evidence.append(ev)
    if context['chain_id'] != 137:
        raise ValueError('RPC chain is not Polygon 137')
    if 'head' not in context:
        raw, ev = await rpc(net, config, 'eth_blockNumber', [])
        context['head'] = int(raw, 16)
        evidence.append(ev)
    receipt, ev = await rpc(net, config, 'eth_getTransactionReceipt', [transaction_hash])
    evidence.append(ev)
    if receipt is None:
        return {'transaction_hash': transaction_hash, 'status': 'unavailable', 'evidence_ids': evidence}
    if receipt.get('transactionHash', '').lower() != transaction_hash.lower():
        raise ValueError('RPC returned wrong transaction')
    block_number = int(receipt['blockNumber'], 16)
    canonical, ev = await rpc(net, config, 'eth_getBlockByNumber', [hex(block_number), False])
    evidence.append(ev)
    if not isinstance(canonical, dict) or not canonical.get('hash'):
        raise ValueError('Canonical block unavailable')
    contracts = registry(config['root'])
    fills, decode_errors = [], []
    for log in receipt.get('logs', []):
        try:
            fill = decode_order(log, contracts)
            if fill:
                if fill['block_hash'] != receipt['blockHash'] or fill['transaction_hash'].lower() != transaction_hash.lower():
                    raise ValueError('Inconsistent receipt log identity')
                fills.append(fill)
        except (ValueError, KeyError, TypeError) as exc:
            decode_errors.append({'log_index': log.get('logIndex'), 'error': str(exc)})
    confirmations = context['head'] - block_number + 1
    canonical_ok = canonical['hash'].lower() == receipt['blockHash'].lower()
    status = ('reorganized' if not canonical_ok or any(f['removed'] for f in fills) else
              'reverted' if int(receipt.get('status', '0x0'), 16) != 1 else
              'pending_confirmations' if confirmations < config['confirmations'] else
              'decode_error' if decode_errors else 'confirmed')
    key = transaction_hash.lower()
    previous = store.get('receipt', key)
    old = previous['payload'] if previous else {}
    changed_block = bool(old.get('block_hash') and old['block_hash'] != receipt['blockHash'])
    result = {'transaction_hash': key, 'chain_id': 137, 'block_number': block_number,
              'block_hash': receipt['blockHash'], 'canonical_block_hash': canonical['hash'],
              'timestamp': int(canonical['timestamp'], 16), 'confirmations': confirmations,
              'status': status, 'prior_block_invalidated': old.get('block_hash') if changed_block else None,
              'operator': receipt.get('from'), 'operator_note': 'Expéditeur de transaction, pas identité du propriétaire',
              'fills': fills, 'transfers': transfers(receipt, wallet, contracts),
              'decode_errors': decode_errors, 'evidence_ids': evidence,
              'url': 'https://polygonscan.com/tx/' + key}
    if trade:
        result['reconciliation'] = reconcile(trade, fills) if status == 'confirmed' else {
            'status': 'not_final', 'proof_level': 'données insuffisantes'}
    if status != 'confirmed':
        for edge in result['transfers']:
            edge['proof_level'] = 'données insuffisantes'
    store.put('receipt', key, result)
    return result
