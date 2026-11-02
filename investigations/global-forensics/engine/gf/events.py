"""The one event record every layer shares, and the only way an event gets a higher level of proof.

Levels of an event, lowest first:
  LISTED              a provider's listing (explorer, data API). Not yet read from a node. No log index on token rows.
  ONCHAIN_CONFIRMED   the receipt read from a node shows this exact move, with its log index and block hash.
  REVERIFIED          the same, from a second independent source.
A level never rises from a report, a cache of a report, or a label. data_class says where the bytes came from.
"""
from decimal import Decimal

LISTED, ONCHAIN, REVERIFIED = 'LISTED', 'ONCHAIN_CONFIRMED', 'REVERIFIED'
ARCHIVED, FRESH, SYNTHETIC, COMPUTED = 'archived', 'fresh', 'synthetic', 'computed'
ZERO = '0x' + '0' * 40
DEAD = '0x000000000000000000000000000000000000dead'
SOLANA, TRON = 792703809, 728126428
CHAIN_NAME = {1: 'ethereum', 10: 'optimism', 56: 'bsc', 137: 'polygon', 8453: 'base', 42161: 'arbitrum', SOLANA: 'solana', TRON: 'tron', 999: 'hyperliquid'}
NATIVE = {1: 'ETH', 137: 'POL', 42161: 'ETH', 8453: 'ETH', 10: 'ETH', 56: 'BNB', SOLANA: 'SOL', TRON: 'TRX', 999: 'HYPE'}
# Value tokens only: anything else is listed and counted but never followed, because most of it is airdrop and poisoning spam.
TOKENS = {
    1: {'0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48': ('USDC', 6), '0xdac17f958d2ee523a2206206994597c13d831ec7': ('USDT', 6), '0x6b175474e89094c44da98b954eedeac495271d0f': ('DAI', 18), '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2': ('WETH', 18), '0x2260fac5e5542a773aa44fbcfedf7c193bc2c599': ('WBTC', 8), '0x7f39c581f595b53c5cb19bd0b3f8da6c935e2ca0': ('wstETH', 18), '0xae7ab96520de3a18e5e111b5eaab095312d7fe84': ('stETH', 18), '0x4c9edd5852cd905f086c759e8383e09bff1e68b3': ('USDe', 18), '0x6c3ea9036406852006290770bedfcaba0e23a0e8': ('PYUSD', 6), '0xcbb7c0000ab88b473b1f5afd9ef808440eed33bf': ('cbBTC', 8), '0x8292bb45bf1ee4d140127049757c2e0ff06317ed': ('RLUSD', 18)},
    137: {'0x2791bca1f2de4661ed88a30c99a7a9449aa84174': ('USDC.e', 6), '0x3c499c542cef5e3811e1192ce70d8cc03d5c3359': ('USDC', 6), '0xc2132d05d31c914a87c6611c10748aeb04b58e8f': ('USDT', 6), '0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb': ('pUSD', 6), '0x8f3cf7ad23cd3cadbd9735aff958023239c6a063': ('DAI', 18), '0x7ceb23fd6bc0add59e62ac25578270cff1b9f619': ('WETH', 18), '0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270': ('WPOL', 18), '0x1bfd67037b42cf73acf2047067bd4f2c47d9bfd6': ('WBTC', 8)},
    42161: {'0xaf88d065e77c8cc2239327c5edb3a432268e5831': ('USDC', 6), '0xff970a61a04b1ca14834a43f5de4533ebddb5cc8': ('USDC.e', 6), '0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9': ('USDT', 6), '0xda10009cbd5d07dd0cecc66161fc93d7c9000da1': ('DAI', 18), '0x82af49447d8a07e3bd95bd0d56f35241523fbab1': ('WETH', 18), '0x2f2a2543b76a4166549f7aab2e75bef0aefc5b0f': ('WBTC', 8)},
    8453: {'0x833589fcd6edb6e08f4c7c32d4f71b54bda02913': ('USDC', 6), '0xd9aaec86b65d86f6a7b5b1b0c42ffa531710b6ca': ('USDbC', 6), '0xfde4c96c8593536e31f229ea8f37b2ada2699bb2': ('USDT', 6), '0x4200000000000000000000000000000000000006': ('WETH', 18), '0xcbb7c0000ab88b473b1f5afd9ef808440eed33bf': ('cbBTC', 8)},
    10: {'0x0b2c639c533813f4aa9d7837caf62653d097ff85': ('USDC', 6), '0x7f5c764cbc14f9669b88837ca1490cca17c31607': ('USDC.e', 6), '0x94b008aa00579c1307b0ef2c499ad98a8ce58e58': ('USDT', 6), '0x4200000000000000000000000000000000000006': ('WETH', 18)},
    56: {'0x55d398326f99059ff775485246999027b3197955': ('USDT', 18), '0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d': ('USDC', 18), '0xe9e7cea3dedca5984780bafc599bd69add087d56': ('BUSD', 18), '0xbb4cdb9cbd36b01bd1cbaebf2de08d9173095bbc': ('WBNB', 18), '0x2170ed0880ac9a755fd29b2688956bd959f933f8': ('ETH', 18), '0x7130d2a12b9bcbfae4f2634d864a1ee1ce3ead9c': ('BTCB', 18)},
}
STABLE = {'USDC', 'USDC.e', 'USDT', 'DAI', 'pUSD', 'USDbC', 'BUSD', 'USDe', 'PYUSD', 'RLUSD'}
REQUIRED = ('chain_id', 'block_number', 'transaction_hash', 'kind', 'raw_amount', 'decimals', 'timestamp', 'from', 'to', 'source', 'decoding', 'level', 'data_class')
ROUGH_USD = {'ETH': 2300, 'WETH': 2300, 'wstETH': 2600, 'stETH': 2300, 'POL': .1, 'WPOL': .1, 'BNB': 700, 'WBNB': 700, 'WBTC': 90000, 'cbBTC': 90000, 'BTCB': 90000, 'SOL': 150, 'WSOL': 150, 'TRX': .3}  # shortcut: ranks flows only, never reported as a value


def amount(e):
    return Decimal(int(e['raw_amount'])) / (Decimal(10) ** int(e['decimals']))


def rough_usd(e):
    return float(amount(e)) * (1 if e.get('token') in STABLE else ROUGH_USD.get(e.get('token'), 0))


def identity(e):
    """Same on-chain move, whichever provider listed it. A native or listed token row has no log index, so its route stands in, and the number of such rows stays visible."""
    base = (e['chain_id'], e['transaction_hash'].lower())
    if e.get('log_index') is not None:
        return base + ('log', e['log_index'])
    if e.get('trace_address') is not None:
        return base + ('trace', tuple(e['trace_address']))
    return base + ('route', e['kind'], e['from'], e['to'], e.get('contract'), str(e['raw_amount']), e.get('seq', 0))


def validate(e):
    missing = [k for k in REQUIRED if e.get(k) is None]
    if missing:
        raise ValueError(f'event missing {missing}: {str(e)[:200]}')
    if int(e['raw_amount']) < 0:
        raise ValueError('negative raw amount')
    if e['level'] in (ONCHAIN, REVERIFIED) and e['kind'] == 'erc20' and e.get('log_index') is None:
        raise ValueError('a confirmed token move needs its log index')
    if e['level'] in (ONCHAIN, REVERIFIED) and not e.get('block_hash'):
        raise ValueError('a confirmed move needs its block hash')
    if e['data_class'] not in (ARCHIVED, FRESH, SYNTHETIC, COMPUTED):
        raise ValueError('unknown data class')
    return e


def merge(events):
    """One record per on-chain move; the higher level wins, and two providers disagreeing on a move raises instead of counting twice."""
    rank = {LISTED: 0, ONCHAIN: 1, REVERIFIED: 2}
    seen = {}
    for e in events:
        key = identity(validate(e))
        if key not in seen:
            seen[key] = e
            continue
        old = seen[key]
        if (old['from'], old['to'], str(old['raw_amount'])) != (e['from'], e['to'], str(e['raw_amount'])):
            raise ValueError(f'two readings of one move disagree: {key}')
        if rank[e['level']] > rank[old['level']]:
            seen[key] = e
    return sorted(seen.values(), key=lambda x: (x['timestamp'], x['transaction_hash'], x.get('log_index') if x.get('log_index') is not None else -1))
