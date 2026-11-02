"""Service attribution. A label says what a named source said; absence means unknown, never personal."""
import csv
import json
import os
import re
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = {1: 'etherscan', 137: 'polygonscan', 42161: 'arbiscan', 56: 'bscscan', 10: 'optimism'}
PRIOR_SERVICES = Path.home() / 'Projects/PolySentinel-investigation/tools/services.json'
MANUAL = ROOT / 'data/service_labels_manual.csv'
# comparators and named wallets must see the same labels: hand attributions and Blockscout tags were only gathered around the dossiers
PUBLIC_ONLY = bool(os.environ.get('LABELS_PUBLIC_ONLY'))

CEX = 'binance coinbase kraken kucoin okx okex bybit bitget gate.io gate htx huobi mexc bitfinex crypto.com bitstamp gemini upbit bithumb poloniex bitmart lbank whitebit deribit bilaxy robinhood cex.io bingx coinone korbit paribu btcturk revolut blofin wise nexo'.split()
INSTANT = 'changenow fixedfloat simpleswap sideshift stealthex exolix letsexchange godex swft swftswap swapspace trocador exch.cx coinswitch shapeshift swapzone'.split()
MIXER = 'tornado railgun mixer privacy aztec wasabi sinbad blender cyclone hinkal zkbob'.split()
BRIDGE = 'bridge across stargate layerzero hop wormhole debridge synapse orbiter relay celer cbridge socket lifi li.fi mayan squid axelar connext thorchain symbiosis portal gas.zip gaszip bungee rhino chainflip intents bridgers'.split()
GENERIC_TAGS = {'Exchange', 'HOT WALLET', 'DEPOSIT ADDRESS', 'Bridge', 'DEX', 'Router', 'Credible token', 'Token Contract', 'Stablecoin', 'Beacon Depositor', 'BLOCKED'}
DEX = 'uniswap 1inch 0x sushiswap curve cow pancakeswap kyber paraswap velora odos balancer quickswap aerodrome openocean metamask matcha permit2 weth'.split()


def category(text):
    t = text.lower()
    words = set(re.split(r'[^a-z0-9.]+', t))
    for names, cat in ((MIXER, 'mixer_or_privacy'), (INSTANT, 'instant_exchange'), (CEX, 'exchange'), (BRIDGE, 'bridge'), (DEX, 'dex_or_router')):
        if words & set(names) or any(n in t for n in names if len(n) >= 5):
            return cat
    if 'exchange' in words or 'hot wallet' in t or 'deposit' in words:
        return 'exchange'
    return 'other_labeled'


@lru_cache(maxsize=1)
def _manual():
    out = {}
    if MANUAL.exists() and not PUBLIC_ONLY:
        with MANUAL.open() as f:
            for r in csv.DictReader(f):
                out[r['address'].lower() if r['address'].startswith('0x') else r['address']] = r
    prior = json.loads(PRIOR_SERVICES.read_text())['addresses']
    for a, v in prior.items():
        key = a.lower() if a.startswith('0x') else a
        if key not in out:
            cat = {'bridge': 'bridge', 'exchange': 'exchange', 'exchange_candidate': 'exchange_candidate'}.get(v['kind'], v['kind'])
            # shortcut: ChangeNOW entries are secondhand PolygonScan tags, kept with their own source text
            out[key] = dict(address=key, name=v['name'], category=cat, level='named_source', source=v['source'], checked=v.get('checked', ''))
    chains = json.loads((ROOT / 'evidence/docs/relay_chains.json').read_text())['chains']
    for c in chains:
        for s in c.get('solverAddresses') or []:
            key = s.lower() if s.startswith('0x') else s
            out.setdefault(key, dict(address=key, name='Relay solver', category='bridge', level='official_doc', source='https://api.relay.link/chains (solverAddresses)', checked='2026-11-02'))
    for line in (ROOT / 'evidence/docs/polymarket_resources_contracts.md').read_text().splitlines():
        m = re.match(r'\|\s*([^|]+?)\s*\|\s*\[`(0x[0-9a-fA-F]{40})`', line)
        if m:
            out.setdefault(m.group(2).lower(), dict(address=m.group(2).lower(), name='Polymarket ' + m.group(1), category='polymarket_contract', level='official_doc', source='https://docs.polymarket.com/resources/contracts.md', checked='2026-11-02'))
    return out


@lru_cache(maxsize=1)
def _blockscout():
    path = ROOT / 'evidence/blockscout_tags.json'
    return json.loads(path.read_text()) if path.exists() else {}


@lru_cache(maxsize=1)
def _public():
    out = {}
    for chain, name in PUBLIC.items():
        for a, v in json.loads((ROOT / f'evidence/labels/brianleect/{name}.json').read_text()).items():
            out.setdefault((chain, a.lower()), []).append(dict(name=v.get('name') or '', labels=v.get('labels') or [], source=f'brianleect/etherscan-labels:{name} (2023 dump)'))
    for r in json.loads((ROOT / 'evidence/labels/dawsbot/accounts.json').read_text()):
        out.setdefault((r['chainId'], r['address'].lower()), []).append(dict(name=r.get('nameTag') or '', labels=[r.get('label') or ''], source=f"dawsbot/eth-labels:{r['chainId']}"))
    return out


def lookup(address, chain):
    """Most official label for this address, or None. Public labels on another chain are reported as weaker: an exchange often reuses an address, but not always."""
    key = address.lower() if address.startswith('0x') else address
    m = _manual().get(key)
    if m:
        return dict(name=m['name'], category=m['category'], level=m['level'], source=m['source'], checked=m.get('checked', ''))
    if not key.startswith('0x'):
        return None
    b = None if PUBLIC_ONLY else _blockscout().get(key)
    if b:
        names = [t['name'] for t in b['tags'] if t.get('name') and t['name'] not in GENERIC_TAGS and not t['name'].startswith('note_')]
        if names:
            best = max(names, key=lambda n: (':' in n, len(n)))
            return dict(name=best, category=category(' '.join(names)), level=f"blockscout_tag_chain_{b['chain']}", source=b['source'], checked=b['read'])
    pub = _public()
    hits = pub.get((chain, key))
    level = 'public_label_same_chain'
    if not hits:
        for other in (1, 137, 42161, 56, 10, 8453):
            if pub.get((other, key)):
                hits, level = pub[(other, key)], f'public_label_other_chain:{other}'
                break
    if not hits:
        return None
    best = hits[0]
    text = ' '.join([best['name']] + best['labels'])
    return dict(name=best['name'] or ' '.join(best['labels']), category=category(text), level=level, source=best['source'] + (f' (+{len(hits) - 1} other)' if len(hits) > 1 else ''), checked='2026-11-02')


if __name__ == '__main__':
    assert category('Tornado.Cash: 100 ETH') == 'mixer_or_privacy'
    assert category('Binance 14') == 'exchange'
    assert category('Uniswap V3: Router') == 'dex_or_router'
    assert lookup('0x4cd00e387622c35bddb9b4c962c136462338bc31', 1)['category'] == 'bridge'
    assert lookup('0x28C6c06298d514Db089934071355E5743bf21d60', 1)['category'] == 'exchange', lookup('0x28C6c06298d514Db089934071355E5743bf21d60', 1)
    assert lookup('0x910Cbd523D972eb0a6f4cAe4618aD62622b39DbF', 1)['category'] == 'mixer_or_privacy'
    assert lookup('0x00000000000fb5c9adea0298d729a0cb3823cc07', 137)['category'] == 'polymarket_contract'
    assert lookup('0xf70da97812cb96acdf810712aa562db8dfa3dbef', 137)['name'].startswith('Relay')
    assert lookup('0x0000000000000000000000000000000000dEaD01', 1) is None
    print('labels self-check ok')
