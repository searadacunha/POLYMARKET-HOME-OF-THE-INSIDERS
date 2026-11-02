"""Does any personal-sized address around the 11 dossiers own a Polymarket Deposit Wallet? CREATE2 address from the key, then owner() and the public activity. Writes state/personal_wallets.json."""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import labels
import net
import walk

FACTORY = bytes.fromhex('00000000000fb5c9adea0298d729a0cb3823cc07')
TEMPLATE = bytes.fromhex('61007d3d8160233d397358ca52ebe0dadfdf531cde7062e76746de4db1eb60095155f3363d3d373d3d363d7f360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc545af43d6000803e6038573d6000fd5b3d6000f300000000000000000000000000000000000fb5c9adea0298d729a0cb3823cc07')
RC = [0x0000000000000001, 0x0000000000008082, 0x800000000000808A, 0x8000000080008000, 0x000000000000808B, 0x0000000080000001, 0x8000000080008081, 0x8000000000008009, 0x000000000000008A, 0x0000000000000088, 0x0000000080008009, 0x000000008000000A, 0x000000008000808B, 0x800000000000008B, 0x8000000000008089, 0x8000000000008003, 0x8000000000008002, 0x8000000000000080, 0x000000000000800A, 0x800000008000000A, 0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008]
ROT = [[0, 36, 3, 41, 18], [1, 44, 10, 45, 2], [62, 6, 43, 15, 61], [28, 55, 25, 21, 56], [27, 20, 39, 8, 14]]
M = (1 << 64) - 1


def keccak(data):
    """Keccak-256, no dependency for one hash."""
    rate = 136
    msg = bytearray(data) + b'\x01' + b'\x00' * ((rate - (len(data) + 1) % rate) % rate)
    msg[-1] |= 0x80
    s = [[0] * 5 for _ in range(5)]
    for off in range(0, len(msg), rate):
        block = msg[off:off + rate]
        for i in range(rate // 8):
            s[i % 5][i // 5] ^= int.from_bytes(block[i * 8:i * 8 + 8], 'little')
        for rc in RC:
            c = [s[x][0] ^ s[x][1] ^ s[x][2] ^ s[x][3] ^ s[x][4] for x in range(5)]
            d = [c[(x + 4) % 5] ^ (((c[(x + 1) % 5] << 1) | (c[(x + 1) % 5] >> 63)) & M) for x in range(5)]
            s = [[s[x][y] ^ d[x] for y in range(5)] for x in range(5)]
            b = [[0] * 5 for _ in range(5)]
            for x in range(5):
                for y in range(5):
                    r = ROT[x][y]
                    b[y][(2 * x + 3 * y) % 5] = ((s[x][y] << r) | (s[x][y] >> (64 - r))) & M if r else s[x][y]
            s = [[b[x][y] ^ ((~b[(x + 1) % 5][y]) & b[(x + 2) % 5][y] & M) for y in range(5)] for x in range(5)]
            s[0][0] ^= rc
    return b''.join(s[i % 5][i // 5].to_bytes(8, 'little') for i in range(4))


BEACON = bytes.fromhex('6100923d8160233d39737a18edfe055488a3128f01f563e5b479d92ffc3a60195155f3363d3d373d3d363d602036600436635c60da1b60e01b36527fa3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50545afa5036515af43d6000803e604d573d6000fd5b3d6000f300000000000000000000000000000000000fb5c9adea0298d729a0cb3823cc07')  # creation code read from a real wallet; wallets deployed since the 29 June 2026 upgrade


def deposit_wallet(owner, template=BEACON):
    o = bytes.fromhex(owner[2:])
    id32 = b'\x00' * 12 + o
    salt = keccak(b'\x00' * 12 + FACTORY + id32)
    return '0x' + keccak(b'\xff' + FACTORY + salt + keccak(template + id32))[12:].hex()


def main():
    assert keccak(b'').hex() == 'c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470'
    assert deposit_wallet('0x08d409aae84f9b7b6a798c97c457a0f41e856c7b', TEMPLATE) == '0x5008c44a36c52f03de75d7aa98c15c14397e2302'  # same anchor as cn_pm_sakana/proxy_resolver.py
    assert deposit_wallet('0x48ec106cf690edd58fcd6df1e8b6abfc16dab12d') == '0xa8e64a3c08d1e2a4e9f25a2dd33b8ac3458f74a5'
    addresses = {}
    for p in sorted((net.ROOT / 'state').glob('walk_*.json')):
        w = json.loads(p.read_text())
        for e in w['edges']:
            for a in (e['src'], e['dst']):
                if walk.is_evm(a) and a != '0x' + '0' * 40:
                    if a in w['own'] or (e['other_cls'] == 'PERSONAL_SIZED' and a == (e['src'] if e['direction'] == 'funding' else e['dst'])):
                        addresses.setdefault(a, set()).add(w['case'])
    # every counterparty a key ever exchanged value with, not only those inside the walk's window
    for p in sorted((net.ROOT / 'state').glob('walk_*.json')):
        w = json.loads(p.read_text())
        for n in w['nodes']:
            if n['address'] in w['own'] and n['chain'] != walk.SOLANA:
                for f in walk.evm_rows(n['address'], n['chain'], 0)[0]:
                    other = f['dst'] if f['src'] == n['address'] else f['src']
                    if walk.is_evm(other) and other != '0x' + '0' * 40 and not labels.lookup(other, n['chain']):
                        addresses.setdefault(other, set()).add(w['case'])
    cases_ = [json.loads(p.read_text()) for p in (walk.INV / 'cases').glob('*.json')]
    own_wallets = {c['address'].lower() for c in cases_}
    known = sum(1 for c in cases_ for o in c['wallet'].get('owners') or [] if deposit_wallet(o.lower()) == c['address'].lower())  # positive control on the 11 dossiers
    print('resolver reproduces the dossier wallets:', known, 'of', len(cases_), flush=True)
    assert known == len(cases_)
    out = []
    for a, cases in sorted(addresses.items()):
        if a in own_wallets:
            continue
        for shape, template in (('beacon', BEACON), ('legacy', TEMPLATE)):
            wallet = deposit_wallet(a, template)
            if wallet in own_wallets:
                continue
            body = net.get('https://data-api.polymarket.com/v2/activity', dict(user=wallet, limit=500, sort_by='TIMESTAMP', sort_direction='ASC', exclude_deposits_withdrawals='false'), pause=.3)
            rows = body.get('data', []) if isinstance(body, dict) else []
            out.append(dict(address=a, cases=sorted(cases), shape=shape, wallet=wallet, activity_rows=len(rows), has_more=bool((body.get('pagination') or {}).get('has_more')) if isinstance(body, dict) else None, types=Counter(r['type'] for r in rows), markets=Counter(r.get('title') for r in rows if r['type'] == 'TRADE').most_common(4), first=rows[0]['timestamp'] if rows else None, last=rows[-1]['timestamp'] if rows else None))
            if rows:
                print(a[:12], sorted(cases), shape, wallet, len(rows), flush=True)
    (net.ROOT / 'state/personal_wallets.json').write_text(json.dumps(out))
    print('addresses', len(out), 'with activity', sum(1 for x in out if x['activity_rows']))
    for x in out:
        if x['activity_rows']:
            print(x)


if __name__ == '__main__':
    main()
