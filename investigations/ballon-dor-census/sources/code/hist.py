"""Normalized transfer history of one address, per chain. A row = one transfer on chain. Failed transactions and zero values are left out and counted."""
import json
import time
import net

SOL_LAMPORTS = 10 ** 9
STABLE = {  # recognized assets per chain: contract -> (symbol, decimals). Anything else is kept as unrecognized, never summed in dollars.
    1: {'0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48': ('USDC', 6), '0xdac17f958d2ee523a2206206994597c13d831ec7': ('USDT', 6), '0x6b175474e89094c44da98b954eedeac495271d0f': ('DAI', 18), '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2': ('WETH', 18), '0x2260fac5e5542a773aa44fbcfedf7c193bc2c599': ('WBTC', 8)},
    137: {'0x2791bca1f2de4661ed88a30c99a7a9449aa84174': ('USDC.e', 6), '0x3c499c542cef5e3811e1192ce70d8cc03d5c3359': ('USDC', 6), '0xc2132d05d31c914a87c6611c10748aeb04b58e8f': ('USDT', 6), '0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb': ('pUSD', 6), '0x7ceb23fd6bc0add59e62ac25578270cff1b9f619': ('WETH', 18), '0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270': ('WPOL', 18)},
    42161: {'0xaf88d065e77c8cc2239327c5edb3a432268e5831': ('USDC', 6), '0xff970a61a04b1ca14834a43f5de4533ebddb5cc8': ('USDC.e', 6), '0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9': ('USDT', 6), '0x82af49447d8a07e3bd95bd0d56f35241523fbab1': ('WETH', 18)},
    10: {'0x0b2c639c533813f4aa9d7837caf62653d097ff85': ('USDC', 6), '0x7f5c764cbc14f9669b88837ca1490cca17c31607': ('USDC.e', 6), '0x94b008aa00579c1307b0ef2c499ad98a8ce58e58': ('USDT', 6), '0x4200000000000000000000000000000000000006': ('WETH', 18)},
}
NATIVE = {1: 'ETH', 137: 'POL', 42161: 'ETH', 10: 'ETH', 8453: 'ETH', 56: 'BNB'}
USD_LIKE = {'USDC', 'USDC.e', 'USDT', 'DAI', 'pUSD'}


def _row(chain, tx, block, ts, src, dst, asset, contract, decimals, raw, kind, recognized=True, extra=None):
    return dict(chain=str(chain), tx=tx, block=int(block), ts=int(ts), src=src.lower() if src and src.startswith('0x') else src, dst=dst.lower() if dst and dst.startswith('0x') else dst,
                asset=asset, contract=contract, decimals=decimals, raw=str(raw), amount=int(raw) / 10 ** decimals, kind=kind, recognized=recognized, **(extra or {}))


def _fee(r):
    """Gas of the whole transaction, in native units, as the explorer reports it. Paid by tx.from, who may be a relayer and not the address of the row."""
    try:
        return dict(fee_native=int(r['gasUsed']) * int(r['gasPrice']) / 1e18, tx_from=(r.get('from') or '').lower())
    except (KeyError, ValueError, TypeError):
        return dict(fee_native=None, tx_from=None)


def evm_rows(address, chain):
    """Native, internal and ERC-20. Polygon `tokentx` carries the native MATIC transfers that the `LogTransfer` of 0x…1010 mirrors: not double counted because that contract is not recognized."""
    a = address.lower()
    if chain == 10:
        lists = {k: _op_all(k, a) for k in ('txlist', 'txlistinternal', 'tokentx')}
    else:
        lists = {k: net.es_all(chain, k, a) for k in ('txlist', 'txlistinternal', 'tokentx')}
    rows, dropped = [], 0
    for r in lists['txlist']:
        if r.get('isError') == '1' or r.get('txreceipt_status') == '0':
            dropped += 1
            continue
        if int(r['value']) > 0:
            rows.append(_row(chain, r['hash'], r['blockNumber'], r['timeStamp'], r['from'], r['to'] or r.get('contractAddress'), NATIVE[chain], '', 18, r['value'], 'native', extra=_fee(r)))
    for r in lists['txlistinternal']:
        if r.get('isError') == '1':
            dropped += 1
            continue
        if int(r['value']) > 0:
            rows.append(_row(chain, r['hash'], r['blockNumber'], r['timeStamp'], r['from'], r['to'], NATIVE[chain], '', 18, r['value'], 'internal'))
    for r in lists['tokentx']:
        c = r['contractAddress'].lower()
        known = STABLE.get(chain, {}).get(c)
        if int(r['value']) == 0:
            continue
        rows.append(_row(chain, r['hash'], r['blockNumber'], r['timeStamp'], r['from'], r['to'], known[0] if known else r.get('tokenSymbol', '?')[:20], c, known[1] if known else int(r.get('tokenDecimal') or 0), r['value'], 'erc20', recognized=bool(known), extra=_fee(r)))
    nonce = None
    sent = [r for r in lists['txlist'] if r['from'].lower() == a]
    if sent:
        nonce = max(int(r['nonce']) for r in sent) + 1
    return rows, dict(dropped_failed=dropped, n_txlist=len(lists['txlist']), n_internal=len(lists['txlistinternal']), n_token=len(lists['tokentx']), nonce_seen=nonce)


def _op_all(action, address):
    """explorer.optimism.io, Blockscout-style API, no key. 10 000 rows per query at most; a full page raises rather than truncates."""
    d = net.get('https://explorer.optimism.io/api', dict(module='account', action=action, address=address, page=1, offset=10000, sort='asc'))
    page = d.get('result')
    if d.get('status') == '0' and not page:
        return []
    if not isinstance(page, list):
        raise net.FetchError(f'optimism not a list: {str(d)[:160]}')
    if len(page) >= 10000:
        raise net.FetchError(f'optimism: full page for {address}')
    return page


def btc_txs(address, max_pages=40):
    """mempool.space, all confirmed transactions, newest first, 25 per page. Raw transaction objects, one per txid."""
    out, last = [], None
    for _ in range(max_pages):
        url = f'https://mempool.space/api/address/{address}/txs/chain' + (f'/{last}' if last else '')
        page = net.get(url)
        if not page:
            return out, True
        out += page
        last = page[-1]['txid']
        if len(page) < 25:
            return out, True
    return out, False


def btc_info(address):
    return net.get(f'https://mempool.space/api/address/{address}')


SYSTEM = '11111111111111111111111111111111'


def sol_signatures(address, max_pages=20):
    out, before = [], None
    for _ in range(max_pages):
        opts = dict(limit=1000)
        if before:
            opts['before'] = before
        page = net.sol('getSignaturesForAddress', [address, opts])
        out += page
        if len(page) < 1000:
            return out, True
        before = page[-1]['signature']
    return out, False


def sol_tx(sig):
    return net.sol('getTransaction', [sig, dict(encoding='jsonParsed', maxSupportedTransactionVersion=0, commitment='finalized')])


def sol_rows(address, max_tx=400):
    """Balance deltas of the address and of every token account it owns, read from the transaction metadata.
    A transfer into an existing token account does not cite the owner: its signature only appears on the token account, so those are read too."""
    first = net.sol('getSignaturesForAddress', [address, dict(limit=1000)])
    if len(first) >= 400:  # a service, not a person: reading it would cost 10 minutes and tell nothing
        return [], dict(complete=False, n_signatures=len(first), high_activity=True, token_accounts=[])
    sigs, complete = first, True
    token_accounts = set()
    rows, seen = [], set()
    queue = [(s['signature'], s.get('err')) for s in sigs]
    done_accounts = set()
    i = 0
    while i < len(queue):
        sig, err = queue[i]
        i += 1
        if sig in seen or err:
            continue
        seen.add(sig)
        if len(seen) > max_tx:
            complete = False
            break
        t = sol_tx(sig)
        if not t:
            raise net.FetchError(f'solana: empty transaction {sig}')
        meta = t['meta']
        keys = [k['pubkey'] if isinstance(k, dict) else k for k in t['transaction']['message']['accountKeys']]
        pre, post = {}, {}
        for side, store in (('preTokenBalances', pre), ('postTokenBalances', post)):
            for b in meta.get(side) or []:
                store[b['accountIndex']] = b
        for idx in set(pre) | set(post):
            b = post.get(idx) or pre.get(idx)
            if b.get('owner') == address:
                token_accounts.add(keys[idx])
        memo = None
        for ins in t['transaction']['message']['instructions']:
            if ins.get('program') == 'spl-memo':
                memo = ins.get('parsed')
        by_owner = {}
        for idx in set(pre) | set(post):
            b = post.get(idx) or pre.get(idx)
            a0 = int((pre.get(idx) or {}).get('uiTokenAmount', {}).get('amount', 0))
            a1 = int((post.get(idx) or {}).get('uiTokenAmount', {}).get('amount', 0))
            if a1 != a0:
                by_owner.setdefault((b.get('mint'), b['uiTokenAmount']['decimals']), []).append((b.get('owner'), a1 - a0, keys[idx]))
        for (mint, decimals), deltas in by_owner.items():
            mine = sum(d for o, d, _ in deltas if o == address)
            if not mine:
                continue
            others = [(o, d) for o, d, _ in deltas if o != address and (d < 0) == (mine > 0)]
            other = max(others, key=lambda x: abs(x[1]))[0] if others else None
            src, dst = (other, address) if mine > 0 else (address, other)
            sym = {'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v': 'USDC', 'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB': 'USDT', 'So11111111111111111111111111111111111111112': 'WSOL'}.get(mint, mint[:8])
            rows.append(_row('solana', sig, t['slot'], t['blockTime'], src, dst, sym, mint, decimals, abs(mine), 'spl', recognized=sym in ('USDC', 'USDT', 'WSOL'), extra=dict(memo=memo)))
        if address in keys:
            k = keys.index(address)
            delta = meta['postBalances'][k] - meta['preBalances'][k]
            if abs(delta) > 2_000_000:  # above rent and fee noise
                deltas = [(keys[j], meta['postBalances'][j] - meta['preBalances'][j]) for j in range(len(keys)) if j != k]
                opposite = [(a, d) for a, d in deltas if (d < 0) == (delta > 0) and d != 0]
                other = max(opposite, key=lambda x: abs(x[1]))[0] if opposite else None
                src, dst = (other, address) if delta > 0 else (address, other)
                rows.append(_row('solana', sig, t['slot'], t['blockTime'], src, dst, 'SOL', '', 9, abs(delta), 'native', extra=dict(memo=memo)))
        if i == len(queue):
            for ta in sorted(token_accounts - done_accounts):
                done_accounts.add(ta)
                extra, ok = sol_signatures(ta)
                complete = complete and ok
                queue += [(s['signature'], s.get('err')) for s in extra]
    return rows, dict(complete=complete, n_signatures=len(seen), token_accounts=sorted(token_accounts))


def utc(ts):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(ts))
