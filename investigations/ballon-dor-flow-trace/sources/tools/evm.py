"""Full history of one EVM address, native + internal + ERC-20, normalised. A failed or capped read says so: it never becomes a short history."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import net

ZERO = '0x' + '0' * 40
CHAIN = {1: 'ethereum', 137: 'polygon', 42161: 'arbitrum', 8453: 'base', 10: 'optimism', 56: 'bsc'}
NATIVE = {1: 'ETH', 137: 'POL', 42161: 'ETH', 8453: 'ETH', 10: 'ETH', 56: 'BNB'}
ETHERSCAN = 'https://api.etherscan.io/v2/api'
ETHERSCAN_CHAINS = (1, 137, 42161)
BLOCKSCOUT = {8453: 'https://base.blockscout.com', 10: 'https://explorer.optimism.io'}
PAGE = 1000
MAX_PAGES = 6
# Value tokens only: anything else in a wallet history is mostly airdrop and poisoning spam, counted but never walked.
TOKENS = {
    1: {'0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48': 'USDC', '0xdac17f958d2ee523a2206206994597c13d831ec7': 'USDT', '0x6b175474e89094c44da98b954eedeac495271d0f': 'DAI', '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2': 'WETH', '0x2260fac5e5542a773aa44fbcfedf7c193bc2c599': 'WBTC'},
    137: {'0x2791bca1f2de4661ed88a30c99a7a9449aa84174': 'USDC.e', '0x3c499c542cef5e3811e1192ce70d8cc03d5c3359': 'USDC', '0xc2132d05d31c914a87c6611c10748aeb04b58e8f': 'USDT', '0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb': 'pUSD', '0x8f3cf7ad23cd3cadbd9735aff958023239c6a063': 'DAI', '0x7ceb23fd6bc0add59e62ac25578270cff1b9f619': 'WETH', '0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270': 'WPOL'},
    42161: {'0xaf88d065e77c8cc2239327c5edb3a432268e5831': 'USDC', '0xff970a61a04b1ca14834a43f5de4533ebddb5cc8': 'USDC.e', '0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9': 'USDT', '0xda10009cbd5d07dd0cecc66161fc93d7c9000da1': 'DAI', '0x82af49447d8a07e3bd95bd0d56f35241523fbab1': 'WETH'},
    8453: {'0x833589fcd6edb6e08f4c7c32d4f71b54bda02913': 'USDC', '0xd9aaec86b65d86f6a7b5b1b0c42ffa531710b6ca': 'USDbC', '0xfde4c96c8593536e31f229ea8f37b2ada2699bb2': 'USDT', '0x4200000000000000000000000000000000000006': 'WETH'},
    10: {'0x0b2c639c533813f4aa9d7837caf62653d097ff85': 'USDC', '0x7f5c764cbc14f9669b88837ca1490cca17c31607': 'USDC.e', '0x94b008aa00579c1307b0ef2c499ad98a8ce58e58': 'USDT', '0x4200000000000000000000000000000000000006': 'WETH'},
    56: {'0x55d398326f99059ff775485246999027b3197955': 'USDT', '0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d': 'USDC', '0xe9e7cea3dedca5984780bafc599bd69add087d56': 'BUSD', '0xbb4cdb9cbd36b01bd1cbaebf2de08d9173095bbc': 'WBNB'},
}
STABLE = {'USDC', 'USDC.e', 'USDT', 'DAI', 'pUSD', 'USDbC', 'BUSD'}
DECIMALS = {'USDC': 6, 'USDC.e': 6, 'USDT': 6, 'pUSD': 6, 'USDbC': 6, 'DAI': 18, 'WETH': 18, 'WPOL': 18, 'WBNB': 18, 'WBTC': 8, 'BUSD': 18}


def decimals(chain, token, reported=None):
    if chain == 56 and token in ('USDT', 'USDC'):
        return 18  # Binance-Peg tokens carry 18 decimals on BSC
    return DECIMALS.get(token, int(reported) if reported not in (None, '') else 18)


def _etherscan(chain, action, address, page, module='account', sort='asc'):
    params = dict(chainid=chain, module=module, action=action, address=address, page=page, offset=PAGE, sort=sort, startblock=0, endblock=999999999)
    d = net.get(ETHERSCAN, params, pause=.3, secret=dict(apikey=net._key_from_env()))
    msg = str(d.get('message', ''))
    if d.get('status') == '1' or 'No transactions' in msg or 'No records' in msg or 'No internal' in msg or 'No token' in msg:
        return d.get('result') or []
    raise RuntimeError(f'etherscan {chain} {action} {address}: {msg} {str(d.get("result"))[:120]}')


def _pull(fetch):
    """Oldest pages first; if the budget runs out, the newest pages too, so a capped address keeps both ends of its history and only loses its middle. Flagged incomplete."""
    rows, complete = [], False
    for page in range(1, MAX_PAGES + 1):
        batch = fetch(page, 'asc')
        rows += batch
        if len(batch) < PAGE:
            complete = True
            break
    if not complete:
        seen = {(r.get('hash'), r.get('from'), r.get('to'), r.get('value'), r.get('contractAddress'), r.get('traceId')) for r in rows}
        for page in range(1, MAX_PAGES + 1):
            batch = fetch(page, 'desc')
            rows += [r for r in batch if (r.get('hash'), r.get('from'), r.get('to'), r.get('value'), r.get('contractAddress'), r.get('traceId')) not in seen]
            if len(batch) < PAGE:
                break
    return rows, complete


def _norm_tx(chain, r, kind):
    return dict(chain=chain, tx=r.get('hash') or r.get('transactionHash'), block=int(r['blockNumber']), at=int(r['timeStamp']), kind=kind, token=NATIVE[chain], contract=None, decimals=18, raw=str(r['value']), src=r['from'].lower(), dst=(r.get('to') or r.get('contractAddress') or '').lower(), ok=r.get('isError', '0') == '0', method=(r.get('functionName') or '').split('(')[0] or r.get('methodId') or None, source=f'etherscan-v2:{chain}')


def _norm_token(chain, r):
    contract = r['contractAddress'].lower()
    known = TOKENS[chain].get(contract)
    return dict(chain=chain, tx=r['hash'], block=int(r['blockNumber']), at=int(r['timeStamp']), kind='erc20', token=known or r.get('tokenSymbol'), contract=contract, decimals=decimals(chain, known, r.get('tokenDecimal')) if known else int(r.get('tokenDecimal') or 0), raw=str(r['value']), src=r['from'].lower(), dst=r['to'].lower(), ok=True, method=None, known=bool(known), source=f'etherscan-v2:{chain}')


def _blockscout_pages(chain, path, params):
    out, query, complete = [], dict(params), False
    for _ in range(MAX_PAGES):
        d = net.get(BLOCKSCOUT[chain] + path, query, pause=.4, accept=(400, 404))
        if '_http_error' in d:
            if d['_http_error'] == 404:
                return out, True  # the address was never seen on this chain
            raise RuntimeError(f'blockscout {chain} {path}: {d}')
        out += d.get('items') or []
        if not d.get('next_page_params'):
            complete = True
            break
        query = dict(params, **d['next_page_params'])
    return out, complete


def _epoch(text):
    import datetime
    return int(datetime.datetime.fromisoformat(text.replace('Z', '+00:00')).timestamp())


def _history_blockscout(address, chain):
    rows, complete = [], True
    base = f'/api/v2/addresses/{address}'
    for path, kind in ((base + '/transactions', 'native'), (base + '/internal-transactions', 'internal')):
        items, done = _blockscout_pages(chain, path, {})
        complete &= done
        for x in items:
            rows.append(dict(chain=chain, tx=x.get('hash') or x.get('transaction_hash'), block=int(x.get('block') or x.get('block_number') or 0), at=_epoch(x['timestamp']), kind=kind, token=NATIVE[chain], contract=None, decimals=18, raw=str(x.get('value') or 0), src=((x.get('from') or {}).get('hash') or '').lower(), dst=((x.get('to') or {}).get('hash') or '').lower(), ok=(x.get('status') or x.get('success')) in ('ok', True), method=x.get('method'), source=f'blockscout:{chain}'))
    items, done = _blockscout_pages(chain, base + '/token-transfers', dict(type='ERC-20'))
    complete &= done
    for x in items:
        contract = ((x.get('token') or {}).get('address_hash') or (x.get('token') or {}).get('address') or '').lower()
        known = TOKENS[chain].get(contract)
        rows.append(dict(chain=chain, tx=x.get('transaction_hash'), block=int(x.get('block_number') or 0), at=_epoch(x['timestamp']), kind='erc20', token=known or (x.get('token') or {}).get('symbol'), contract=contract, decimals=int((x.get('token') or {}).get('decimals') or 0), raw=str((x.get('total') or {}).get('value') or 0), src=((x.get('from') or {}).get('hash') or '').lower(), dst=((x.get('to') or {}).get('hash') or '').lower(), ok=True, method=None, known=bool(known), log_index=x.get('log_index'), source=f'blockscout:{chain}'))
    return rows, complete


def history(address, chain):
    """(rows, info). Zero-value natives are dropped; failed transactions are kept and flagged, and never count as a flow."""
    address = address.lower()
    info = dict(address=address, chain=chain, complete=True, source=None)
    if chain in ETHERSCAN_CHAINS:
        info['source'] = 'etherscan-v2'
        txs, c1 = _pull(lambda p, o: _etherscan(chain, 'txlist', address, p, sort=o))
        internal, c2 = _pull(lambda p, o: _etherscan(chain, 'txlistinternal', address, p, sort=o))
        tokens, c3 = _pull(lambda p, o: _etherscan(chain, 'tokentx', address, p, sort=o))
        info['complete'] = c1 and c2 and c3
        rows = [_norm_tx(chain, r, 'native') for r in txs] + [_norm_tx(chain, r, 'internal') for r in internal] + [_norm_token(chain, r) for r in tokens]
        info['tx_count'] = len(txs)
        info['sent'] = sum(1 for r in txs if r['from'].lower() == address)
    elif chain in BLOCKSCOUT:
        info['source'] = 'blockscout'
        rows, info['complete'] = _history_blockscout(address, chain)
        info['tx_count'] = sum(1 for r in rows if r['kind'] == 'native')
        info['sent'] = sum(1 for r in rows if r['kind'] == 'native' and r['src'] == address)
    else:
        raise ValueError(f'no explorer for chain {chain}')
    keep = [r for r in rows if r['kind'] != 'native' or int(r['raw']) > 0 or r['src'] == address]
    keep.sort(key=lambda r: (r['at'], r['tx'], r['kind']))
    return keep, info


def contract_name(address, chain):
    """Verified source name, from Etherscan on its chains and Blockscout on Base and Optimism. None when unverified."""
    if chain in ETHERSCAN_CHAINS:
        d = net.get(ETHERSCAN, dict(chainid=chain, module='contract', action='getsourcecode', address=address), pause=.3, secret=dict(apikey=net._key_from_env()))
        row = (d.get('result') or [{}])[0] if isinstance(d.get('result'), list) else {}
        return row.get('ContractName') or None
    if chain in BLOCKSCOUT:
        d = net.get(BLOCKSCOUT[chain] + f'/api/v2/addresses/{address}', pause=.4)
        return d.get('name')
    return None


def probe(address, chain):
    """Code, nonce and native balance now, from a public node: independent of the explorer."""
    code = net.rpc('eth_getCode', [address, 'latest'], chain)
    nonce = int(net.rpc('eth_getTransactionCount', [address, 'latest'], chain), 16)
    delegated = bool(code) and code.startswith('0xef0100')
    kind = 'EIP7702_DELEGATED_EOA' if delegated else 'CONTRACT' if code not in ('0x', '0x0', None) else 'EOA'
    return dict(kind=kind, nonce=nonce)
