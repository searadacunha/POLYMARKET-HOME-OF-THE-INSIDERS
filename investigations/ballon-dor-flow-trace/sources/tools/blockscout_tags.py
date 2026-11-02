"""Blockscout puts its name tags in metadata.tags of the from/to objects of transaction lists, not on the address page. Reads them for every hub and service met by the walk. Writes evidence/blockscout_tags.json.
Single source per address, on Ethereum and Optimism: other Blockscout hosts sit behind a browser challenge, which is not bypassed."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import net
import walk

HOSTS = {1: 'https://eth.blockscout.com', 10: 'https://explorer.optimism.io'}
EXTRA = ['0x0853ea40b121f9135d7e0c07fae35d59aedb4d0b', '0x2744dfd9898f0babbc570cc594bbbc84b487a22b', '0x3ab2206b98b01ba256dbdd4c50208bf17ab27d50', '0x51cf2d9f67078d76c21258c5aa2cb39a2ca24999', '0x435e3931c6de8def0abd4da54228e2e53a64dd1d', '0xcc0f311eb2c688f30bc9aadb42781e46899723f7', '0xa3222357a0eccf60c73606170be6c99adecb59b3', '0x963737c550e70ffe4d59464542a28604edb2ef9a', '0x6bf18baf7819bd6232879d1cef883caf2dcf7e95', '0x8894e0a0c962cb723c1976a4421c95949be2d4e3', '0xe7804c37c13166ff0b37f5ae0bb07a3aebb6e245', '0xb38e8c17e38363af6ebdcb3dae12e0243582891d', '0x09c30cdcdd971423a3e4a3e8a9f1c2e4c5c1e6a0', '0x7f18bb4dd92cf2404c54cba1a9be4a1153bdb078', '0x04d6f7027a']


def tags_of(address, host):
    body = net.get(f'{host}/api/v2/addresses/{address}/transactions', pause=.4, accept=(400, 404, 422))
    for item in (body.get('items') or []) if isinstance(body, dict) else []:
        for side in ('from', 'to'):
            o = item.get(side) or {}
            if (o.get('hash') or '').lower() == address:
                tags = ((o.get('metadata') or {}).get('tags') or [])
                return [dict(name=t.get('name'), slug=t.get('slug'), type=t.get('tagType')) for t in tags], o.get('name')
    return [], None


def main():
    addresses = set(a for a in EXTRA if len(a) == 42)
    for p in sorted((net.ROOT / 'state').glob('walk_*.json')):
        w = json.loads(p.read_text())
        for e in w['edges']:
            for a in (e['src'], e['dst']):
                if walk.is_evm(a) and a not in w['own'] and a != '0x' + '0' * 40:
                    addresses.add(a)
    out = {}
    for a in sorted(addresses):
        tags, name = [], None
        for chain, host in HOSTS.items():
            try:
                t, n = tags_of(a, host)
            except Exception as e:
                print(a, chain, 'error', str(e)[:80], flush=True)
                continue
            if t:
                tags, name = t, n
                out[a] = dict(chain=chain, tags=tags, name=name, source=f'{host}/api/v2/addresses/{a}/transactions, metadata.tags', read='2026-11-02')
                break
        if tags:
            print(a[:12], [t['name'] for t in tags][:4], flush=True)
    (net.ROOT / 'evidence/blockscout_tags.json').write_text(json.dumps(out, indent=0))
    print('addresses read', len(addresses), 'tagged', len(out), flush=True)


if __name__ == '__main__':
    main()
