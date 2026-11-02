"""Universe of addresses a public source calls ChangeNOW, each with its source, on each chain. No address is added by reasoning: only what a source wrote."""
import csv, json, re, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import arch
ROOT = Path(__file__).resolve().parent.parent
FT = Path.home() / 'Projects/PolySentinel-flow-trace'
INV = Path.home() / 'Projects/PolySentinel-investigation'
BASE = 'https://metadata.services.blockscout.com/api/v1'
CHAINS = (1, 137, 56, 8453, 42161, 10, 43114)
rows = []

def add(addr, chain, name, source, kind):
    rows.append(dict(address=addr.lower() if addr.startswith('0x') else addr, chain_id=chain, name=name, source=source, source_kind=kind))

# 1. Blockscout tag search: one call per page returns the tags and their addresses
import urllib.parse
for chain in CHAINS:
    tok, n_tags, capped = '', 0, False
    for page in range(1, 41):
        s, b = arch.fetch(f'{BASE}/tags:search?chainId={chain}&tag_types=name,protocol,generic&name=changenow&pageSize=50&addressLimit=50' + (f'&pageToken={urllib.parse.quote(tok)}' if tok else ''), f'blockscout_tagsearch_{chain}_{page}.json', pause=.5)
        if s != 200:
            print('tagsearch', chain, page, s, b[:200])
            break
        d = json.loads(b)
        for it in d.get('items') or []:
            t = it.get('tag', it)
            n_tags += 1
            addrs = it.get('addresses') or []
            if len(addrs) >= 50:
                capped = True
                print('capped tag', chain, t.get('slug'), len(addrs))
            for x in addrs:
                add(x if isinstance(x, str) else (x.get('address') or x.get('hash')), chain, t.get('name'), f"blockscout_metadata:{t.get('slug')}:{t.get('tagType')}:meta={t.get('meta')}", 'blockscout')
        tok = (d.get('next_page_params') or {}).get('page_token') or ''
        if not tok:
            break
    print(chain, 'tags', n_tags, 'pages', page, 'more' if tok else 'end', 'capped' if capped else '')
# 2. Label lists kept by flow-trace (read only)
for x in json.load(open(FT / 'evidence/labels/dawsbot/accounts.json')):
    if 'changenow' in json.dumps(x).lower():
        add(x['address'], x['chainId'], x.get('nameTag') or x.get('label'), 'dawsbot/eth-labels v1 data/json/accounts.json', 'dawsbot')
for chain, file in ((1, 'etherscan'), (137, 'polygonscan'), (56, 'bscscan'), (42161, 'arbiscan'), (10, 'optimism')):
    d = json.load(open(FT / f'evidence/labels/brianleect/{file}.json'))
    for a, v in d.items():
        if 'changenow' in json.dumps(v).lower():
            add(a, chain, v.get('name'), f'brianleect/etherscan-labels {file}.json (2023)', 'brianleect')
# 3. Second-hand copies in public repositories
add('0xdd3d72c53ff982ff59853da71158bf1538b3ceee', 1, 'ChangeNOW, Hot Wallet (Arkham fields)', 'Xaxrich/okx-ai-quant-lab@fc8b09aa7b arkham_entity_labeled_transfers.csv, source_channel ARKHAM_CHANNEL', 'arkham_copy')
add('0xdd3d72c53ff982ff59853da71158bf1538b3ceee', 1, 'ChangeNOW, exchange_licensed, global_id 2360', 'opun/amlbot-agent@15fc31e210 docs/examples/example-6.json', 'amlbot_copy')
add('G2YxRa6wt1qePMwfJzdXZG62ej4qaTC7YURzuh2Lwd3t', 'solana', 'ChangeNow', 'Marzel7/flex src/utils/infra_mapping.py, comment says verified, no source given', 'github_list')
for line in open(ROOT / 'evidence/repos/thirdparty/PeLegend__BlockchainAnalysis__wallets_exchange.csv.txt', errors='replace'):
    if 'changenow' in line.lower():
        m = re.match(r'"(0x[0-9a-fA-F]{40})","([^"]+)"', line)
        if m:
            add(m.group(1), 1, m.group(2), 'PeLegend/BlockchainAnalysis public/wallets_exchange.csv', 'github_list')
# 4. Etherscan page read for this study
for a, name in (('0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b', 'ChangeNOW Dep: 0x3f3...07B'), ('0xeba88149813bec1cccccfdb0dacefaaa5de94cb1', 'ChangeNOW: Hot Wallet 4')):
    add(a, 1, name, 'etherscan.io address page, Public Name Tag, read 2026-11-02', 'etherscan_page')
# Tags read directly on Blockscout for the studied addresses and their counterparties
for a, n in (('0x4778480c6c46521c41f7e4f2318f884b157cb1c9', 'ChangeNow (0x4778)'), ('0xa12e1462d0ced572f396f58b6e2d03894cd7c8a4', 'ChangeNOW: hot wallet'), ('0xdd3d72c53ff982ff59853da71158bf1538b3ceee', 'ChangeNOW: Hot Wallet 3'), ('0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b', 'ChangeNOW Dep: 0x3f3...07B'), ('0xeba88149813bec1cccccfdb0dacefaaa5de94cb1', 'ChangeNOW: Hot Wallet 4')):
    add(a, 1, n, 'blockscout_metadata', 'blockscout')
# 5. Investigation's service list, secondhand
for a, v in json.load(open(INV / 'tools/services.json')).get('addresses', {}).items() if isinstance(json.load(open(INV / 'tools/services.json')), dict) and 'addresses' in json.load(open(INV / 'tools/services.json')) else []:
    if 'changenow' in json.dumps(v).lower():
        add(a, 137, v.get('name'), 'investigation tools/services.json', 'services_json')
seen = set()
out = [r for r in rows if not ((k := (r['address'], r['chain_id'], r['name'], r['source'])) in seen or seen.add(k))]
with (ROOT / 'state/universe_raw.csv').open('w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['address', 'chain_id', 'name', 'source', 'source_kind'])
    w.writeheader(); w.writerows(out)
from collections import Counter
print(len(out), 'rows', len({r['address'] for r in out}), 'addresses')
print(Counter(r['source_kind'] for r in out))
print(Counter(r['chain_id'] for r in out))
