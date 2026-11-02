"""What a named source calls an address. A label is an attribution, never a proof. No label means unknown, not personal.
Sources kept apart: official Relay chain list, Blockscout metadata (tags, some from OLI), two public lists (dawsbot; brianleect, dump of 2023), manual notes with their reason."""
import hashlib
import json
import re
from pathlib import Path
import net

LISTS = Path.home() / 'Projects/PolySentinel-flow-trace/evidence/labels'  # read only; every file is checked against SHA256SUMS before use
INSTANT = ('changenow', 'fixedfloat', 'simpleswap', 'sideshift', 'stealthex', 'exolix', 'letsexchange', 'godex', 'swft', 'swapspace', 'trocador', 'exch.cx', 'coinswitch', 'shapeshift', 'near intents')
CEX = ('binance', 'coinbase', 'kraken', 'kucoin', 'okx', 'okex', 'bybit', 'bitget', 'gate.io', 'htx', 'huobi', 'mexc', 'bitfinex', 'crypto.com', 'bitstamp', 'gemini', 'upbit', 'bithumb', 'hitbtc', 'blofin', 'revolut', 'deblock', 'poloniex', 'bitmart', 'lbank', 'bingx', 'robinhood', 'exodus')
BRIDGE = ('relay', 'across', 'stargate', 'layerzero', 'hop protocol', 'wormhole', 'debridge', 'dln', 'synapse', 'orbiter', 'celer', 'socket', 'lifi', 'li.fi', 'mayan', 'squid', 'axelar', 'connext', 'thorchain', 'chainflip', 'circle', 'cctp', 'polygon: bridge', 'bridge')
MIXER = ('tornado', 'railgun', 'mixer', 'wasabi', 'sinbad', 'blender', 'cyclone', 'hinkal')
DEX = ('uniswap', '1inch', '0x:', '0x exchange', 'sushi', 'curve', 'cow', 'pancake', 'kyber', 'paraswap', 'velora', 'odos', 'balancer', 'quickswap', 'aerodrome', 'openocean', 'metamask', 'matcha', 'permit2', 'weth', 'router', 'swap')
GENERIC = {'exchange', 'hot wallet', 'deposit address', 'bridge', 'dex', 'router', 'credible token', 'token contract', 'stablecoin', 'note_0'}
BLOCKSCOUT_CHAINS = (1, 137, 42161, 10, 8453, 56)
_lists = None
_relay = None
_cache = {}


def category(text):
    t = text.lower()
    for names, cat in ((MIXER, 'mixer'), (INSTANT, 'instant_exchange'), (CEX, 'exchange'), (BRIDGE, 'bridge'), (DEX, 'dex_or_router')):
        if any(n in t for n in names):
            return cat
    if 'polymarket' in t:
        return 'polymarket'
    if 'exchange' in t or 'hot wallet' in t or 'deposit' in t:
        return 'exchange'
    return 'other_labeled'


def _load_lists():
    global _lists
    if _lists is not None:
        return _lists
    want = dict(reversed(l.split()) for l in (LISTS / 'SHA256SUMS').read_text().splitlines() if l.strip())
    _lists = {}
    for name, sha in want.items():
        p = LISTS / name
        if hashlib.sha256(p.read_bytes()).hexdigest() != sha:
            raise RuntimeError(f'label list changed: {p}')
        d = json.loads(p.read_text())
        items = d.items() if isinstance(d, dict) else [(x.get('address'), x) for x in d]
        for a, v in items:
            if isinstance(v, dict):
                text = ' '.join(str(x) for x in (v.get('name'), v.get('nameTag'), v.get('label'), v.get('labels')) if x)
            else:
                text = str(v)
            if a and text:
                _lists.setdefault(a.lower(), []).append(dict(source=name, text=text[:120]))
    return _lists


def _load_relay():
    global _relay
    if _relay is not None:
        return _relay
    _relay = {}
    for c in net.get('https://api.relay.link/chains')['chains']:
        for s in c.get('solverAddresses') or []:
            _relay[s.lower() if s.startswith('0x') else s] = dict(source='relay_chains_official', text=f"Relay solver ({c['name']})")
        dep = ((c.get('protocol') or {}).get('v2') or {}).get('depository')
        if dep:
            _relay[dep.lower() if dep.startswith('0x') else dep] = dict(source='relay_chains_official', text=f"Relay depository ({c['name']})")
    return _relay


def prefetch(addresses, chain):
    """Blockscout metadata in batches of 50: one call instead of fifty."""
    if chain not in BLOCKSCOUT_CHAINS:
        return
    todo = sorted({a for a in addresses if a.startswith('0x') and (a, chain) not in _cache})
    for i in range(0, len(todo), 50):
        batch = todo[i:i + 50]
        d = net.get('https://metadata.services.blockscout.com/api/v1/metadata', dict(addresses=','.join(batch), chainId=chain))
        got = {k.lower(): v for k, v in (d.get('addresses') or {}).items()}
        for a in batch:
            tags = [t['name'] for t in (got.get(a) or {}).get('tags') or [] if t.get('name')]
            meta = [t for t in (got.get(a) or {}).get('tags') or []]
            oli = any('OLI' in (t.get('meta') or '') for t in meta)
            _cache[(a, chain)] = dict(tags=tags, oli=oli)


def lookup(address, chain=None):
    """Returns dict(category, name, sources=[…]) or None."""
    key = address.lower() if address.startswith('0x') else address
    sources = []
    relay = _load_relay().get(key)
    if relay:
        sources.append(relay)
    if address.startswith('0x'):
        for hit in _load_lists().get(key, []):
            sources.append(hit)
        chains = [int(chain)] if chain and str(chain).isdigit() else [1, 137]
        for c in chains:
            prefetch([key], c)
            got = _cache.get((key, c))
            for t in (got or {}).get('tags', []):
                if t.lower() not in GENERIC:
                    sources.append(dict(source=f"blockscout_{c}" + ('_oli' if got.get('oli') else ''), text=t))
    if not sources:
        return None
    best = next((s for s in sources if category(s['text']) in ('mixer', 'instant_exchange', 'exchange', 'bridge')), sources[0])
    return dict(category=category(best['text']), name=best['text'], sources=sources)


def lineages(sources):
    """Copies are not independent: count origins, not lines."""
    out = set()
    for s in sources:
        src = s['source']
        if 'relay' in src:
            out.add('relay_official')
        elif 'oli' in src:
            out.add('oli')
        elif src.startswith('blockscout'):
            out.add('blockscout_tag')
        else:
            out.add('etherscan_copy')  # both public lists are dumps of Etherscan name tags
    return sorted(out)
