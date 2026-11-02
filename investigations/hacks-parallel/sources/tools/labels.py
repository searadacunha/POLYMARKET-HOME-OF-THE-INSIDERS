"""Who says what about an address. Every label keeps its source, a label is never a fact about the address."""
import csv
import gzip
import json
import os
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import net

PROOF = Path.home() / 'Projects/PolySentinel-ChangeNOW-proof'
TRACE = Path.home() / 'Projects/PolySentinel-flow-trace'
META = 'https://metadata.services.blockscout.com/api/v1/metadata'
SERVICE_WORDS = re.compile(r'changenow|change now|binance|coinbase|kraken|kucoin|okx|okex|bybit|bitget|gate\.io|htx|huobi|mexc|bitfinex|crypto\.com|bitstamp|gemini|upbit|bithumb|poloniex|bitmart|lbank|whitebit|bitcoinvn|bitcoin vietnam|fixedfloat|fixed float|simpleswap|sideshift|stealthex|exolix|letsexchange|godex|swft|swapspace|trocador|shapeshift|bridge|across|stargate|layerzero|hop |wormhole|debridge|synapse|orbiter|relay|celer|socket|li\.?fi|mayan|squid|axelar|connext|thorchain|symbiosis|tornado|railgun|uniswap|1inch|sushiswap|curve|cow|pancakeswap|kyber|paraswap|odos|balancer|quickswap|openocean|permit2|exchange|hot wallet|deposit', re.I)


def _local():
    out = {}
    with (PROOF / 'state/universe_raw.csv').open() as f:
        for r in csv.DictReader(f):
            out.setdefault(r['address'].lower(), []).append(dict(name=r['name'], source=r['source'], chain=r['chain_id']))
    with gzip.open(PROOF / 'state/bs_changenow_list.csv.gz', 'rt') as f:
        for r in csv.DictReader(f):
            out.setdefault(r['address'].lower(), []).append(dict(name=r['slug'], source='blockscout tag list (ChangeNOW-proof)', chain=r['chain_id']))
    with (TRACE / 'data/service_labels_manual.csv').open() as f:
        for r in csv.DictReader(f):
            out.setdefault(r['address'].lower(), []).append(dict(name=r['name'], source='flow-trace manual: ' + r['source'][:80], chain=''))
    for sub in ('dawsbot', 'brianleect'):
        for p in (TRACE / 'evidence/labels' / sub).rglob('*'):
            if p.suffix == '.json' and p.stat().st_size < 60_000_000:
                _scan_json(p, sub, out)
    return out


def _scan_json(path, source, out):
    try:
        data = json.loads(path.read_text())
    except ValueError:
        return
    rows = data if isinstance(data, list) else data.get('data', data) if isinstance(data, dict) else []
    if isinstance(rows, dict):
        rows = [dict(address=k, **(v if isinstance(v, dict) else dict(name=v))) for k, v in rows.items()]
    for r in rows:
        if isinstance(r, dict) and str(r.get('address', '')).startswith('0x'):
            name = r.get('label') or r.get('name') or r.get('nameTag') or ''
            out.setdefault(r['address'].lower(), []).append(dict(name=str(name), source=source + ':' + path.name, chain=str(r.get('chainId', ''))))


LOCAL = None


def metadata(addresses, chain):
    """Blockscout metadata tags by batch, in the original case-insensitive form. Answers are cached by net.get."""
    out = {}
    addresses = sorted({a.lower() for a in addresses})
    for i in range(0, len(addresses), 50):
        batch = addresses[i:i + 50]
        d = net.get(META, dict(addresses=','.join(batch), chainId=chain), pause=.4)
        for k, v in (d.get('addresses') or {}).items():
            out[k.lower()] = [t.get('name', '') for t in v.get('tags', []) if t.get('name')]
    return out


def lookup(address, chain, meta=None):
    global LOCAL
    if LOCAL is None:
        LOCAL = _local()
    a = address.lower()
    out = [dict(name=x['name'], source=x['source']) for x in LOCAL.get(a, []) if not x['chain'] or x['chain'] == str(chain)]
    if meta and a in meta:
        out += [dict(name=n, source=f'blockscout metadata chain {chain}') for n in meta[a]]
    return out


def is_service(labels):
    return any(SERVICE_WORDS.search(x['name']) for x in labels)


def is_changenow(labels):
    return any(re.search(r'change.?now', x['name'], re.I) for x in labels)
