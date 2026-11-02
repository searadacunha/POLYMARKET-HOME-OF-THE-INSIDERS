"""Shared reading of the window files written by cn_windows.py."""
import gzip
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import chainlib as c
import cn_windows as w
import net
import tokens

WIN = w.OUT
PRICE_KEY = {'POL': 'coingecko:polygon-ecosystem-token', 'WPOL': 'coingecko:polygon-ecosystem-token', 'MATIC': 'coingecko:polygon-ecosystem-token', 'ETH': 'coingecko:ethereum', 'WETH': 'coingecko:ethereum', 'WBTC': 'coingecko:wrapped-bitcoin', 'USDC': 'coingecko:usd-coin', 'USDC.e': 'coingecko:usd-coin', 'USDT': 'coingecko:tether', 'DAI': 'coingecko:dai', 'stETH': 'coingecko:staked-ether', 'wstETH': 'coingecko:wrapped-steth'}
_prices = {}


def price(symbol, ts):
    """USD of a symbol at the day of ts (DeFiLlama), never a fixed peg. A missing price raises."""
    day = ts // 86400 * 86400 + 43200
    key = PRICE_KEY[symbol]
    if (key, day) not in _prices:
        d = net.get(f'https://coins.llama.fi/prices/historical/{day}/{key}', pause=.2)
        _prices[(key, day)] = d['coins'][key]['price']
    return _prices[(key, day)]


def load(incident, source, name):
    path = WIN / f'{incident}__{source}__{name}.jsonl.gz'
    if not path.exists():
        return None
    with gzip.open(path, 'rt') as f:
        return [json.loads(line) for line in f]


def payouts(incident, source, name):
    """Recognized value leaving the source in one window. Token rows on unknown contracts are returned apart: they are mostly spoof spam or small tokens without a checked price."""
    addr, chain = w.SOURCES[source]
    rows = load(incident, source, name)
    if rows is None:
        return None, None
    out = [e for e in rows if e['src'] == addr]
    ok = [e for e in out if tokens.recognized(chain, e)]
    return ok, len(out) - len(ok)


def window_names(incident):
    cfg = w.INCIDENTS[incident]
    return [n for n, _, _ in w.windows(c.ts_of(cfg['t0']), cfg['controls'])]


def window_start(incident, name):
    cfg = w.INCIDENTS[incident]
    for n, a, _ in w.windows(c.ts_of(cfg['t0']), cfg['controls']):
        if n == name:
            return a
    raise KeyError(name)
