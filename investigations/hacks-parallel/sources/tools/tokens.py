"""Tokens whose contract is checked. A symbol alone proves nothing: 'PỌL' with a dotted O (0xa1a33d44…) is spoof spam sent from address look-alikes on the May wallets."""
RECOGNIZED = {
    137: {'0x2791bca1f2de4661ed88a30c99a7a9449aa84174': 'USDC.e', '0x3c499c542cef5e3811e1192ce70d8cc03d5c3359': 'USDC', '0xc2132d05d31c914a87c6611c10748aeb04b58e8f': 'USDT', '0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270': 'WPOL', '0x7ceb23fd6bc0add59e62ac25578270cff1b9f619': 'WETH', '0x8f3cf7ad23cd3cadbd9735aff958023239c6a063': 'DAI', '0x1bfd67037b42cf73acf2047067bd4f2c47d9bfd6': 'WBTC'},
    1: {'0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48': 'USDC', '0xdac17f958d2ee523a2206206994597c13d831ec7': 'USDT', '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2': 'WETH', '0x6b175474e89094c44da98b954eedeac495d1d0f': 'DAI', '0x2260fac5e5542a773aa44fbcfedf7c193bc2c599': 'WBTC', '0xae7ab96520de3a18e5e111b5eaab095312d7fe84': 'stETH', '0x7f39c581f595b53c5cb19bd0b3f8da6c935e2ca0': 'wstETH', '0x7d1afa7b718fb893db30a3abc0cfc608aacfebb0': 'MATIC', '0x455e53cbb86018ac2b8092fdcd39d8444affc3f6': 'POL'},
}
MIN_FOLLOW = {'POL': 50, 'WPOL': 50, 'USDC': 5, 'USDC.e': 5, 'USDT': 5, 'DAI': 5, 'pUSD': 5, 'ETH': .002, 'WETH': .002, 'WBTC': .0001, 'stETH': .002, 'wstETH': .002, 'MATIC': 50}
PUSD_NOTE = 'pUSD contract is added at run time from the June victims'


def recognized(chain, edge):
    return edge['kind'] != 'erc20' or edge['token'] in RECOGNIZED.get(chain, {})


def canonical_symbol(chain, edge):
    return edge['symbol'] if edge['kind'] != 'erc20' else RECOGNIZED.get(chain, {}).get(edge['token'], '?' + edge['symbol'])


def worth_following(chain, edge):
    sym = canonical_symbol(chain, edge)
    if sym.startswith('?'):
        return False
    return int(edge['raw']) / 10 ** edge['decimals'] >= MIN_FOLLOW.get(sym, 1e18)
