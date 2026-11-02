"""The two addresses and their deposit relay: exact Blockscout metadata, Etherscan and OKLink pages, archived. Prints where each label sits in each answer."""
import json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import arch
A = {'hot3': '0xdd3d72c53ff982ff59853da71158bf1538b3ceee', 'dep': '0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b', 'relay': '0x7e67df45e0a0bab092cbb2ff045f8aa8dfab6e23', 'hot4': '0xeba88149813bec1cccccfdb0dacefaaa5de94cb1'}
for k, a in A.items():
    s, b = arch.fetch(f'https://metadata.services.blockscout.com/api/v1/metadata?addresses={a}&chainId=1', f'blockscout_metadata_{k}_{a[:10]}.json')
    print(k, 'metadata', s, b[:600].decode())
    s, b = arch.fetch(f'https://eth.blockscout.com/api/v2/addresses/{a}', f'blockscout_address_{k}_{a[:10]}.json')
    d = json.loads(b) if s == 200 else {}
    print(k, 'address', s, {x: d.get(x) for x in ('is_contract', 'name', 'creation_tx_hash', 'creator_address_hash', 'has_token_transfers', 'coin_balance', 'exchange_rate')}, 'metadata=', d.get('metadata'), 'public_tags=', d.get('public_tags'), 'private_tags=', d.get('private_tags'))
    s, b = arch.fetch(f'https://eth.blockscout.com/api/v2/addresses/{a}/counters', f'blockscout_counters_{k}_{a[:10]}.json')
    print(k, 'counters', s, b[:200].decode())
    s, b = arch.fetch(f'https://etherscan.io/address/{a}', f'etherscan_page_{k}_{a[:10]}.html')
    t = b.decode('utf8', 'replace')
    title = re.search(r'<title>(.*?)</title>', t, re.S)
    print(k, 'etherscan', s, len(b), 'title=', title and ' '.join(title.group(1).split())[:160])
    for m in list(re.finditer(r'(?i)(changenow|name tag|Public Name Tag|data-bs-title="[^"]{0,120}"[^>]{0,40}>\s*[^<]{0,60}changenow)', t))[:6]:
        print('   ', ' '.join(t[max(0, m.start() - 90):m.end() + 120].split())[:300])
    s, b = arch.fetch(f'https://www.oklink.com/ethereum/address/{a}', f'oklink_page_{k}_{a[:10]}.html')
    t = b.decode('utf8', 'replace')
    print(k, 'oklink', s, len(b), [' '.join(t[max(0, m.start() - 60):m.end() + 60].split())[:180] for m in list(re.finditer(r'(?i)changenow', t))[:3]])
