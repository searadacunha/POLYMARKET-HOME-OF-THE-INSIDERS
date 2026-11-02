"""Outgoing history of one key on BSC without an explorer: bisect its nonce by block on public archive nodes, then read the block that holds each transaction.
Sees what the key signed, not what it received. Writes state/bsc_<address>.json; every answer cached."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import labels
import net
import walk

ARCHIVE = ('https://bsc-mainnet.gateway.tatum.io', 'https://56.rpc.thirdweb.com')
net.RPC[56] = ARCHIVE


def nonce_at(address, block):
    return int(net.rpc('eth_getTransactionCount', [address, hex(block)], 56, pause=.2), 16)


def block_of_nonce(address, target, low, high):
    """Smallest block whose post-state nonce is >= target."""
    while high - low > 1:
        mid = (low + high) // 2
        if nonce_at(address, mid) >= target:
            high = mid
        else:
            low = mid
    return high


def enumerate_all(address, low, high, n_low, n_high, out):
    """Each nonce step is found once: split the block range and recurse only where the nonce moves."""
    if n_high == n_low:
        return
    if high - low == 1:
        out.append((high, n_low, n_high))
        return
    mid = (low + high) // 2
    n_mid = nonce_at(address, mid)
    enumerate_all(address, low, mid, n_low, n_mid, out)
    enumerate_all(address, mid, high, n_mid, n_high, out)


def main(address):
    latest = int(net.rpc('eth_blockNumber', [], 56, cache=False), 16)
    total = int(net.rpc('eth_getTransactionCount', [address, 'latest'], 56, cache=False), 16)
    # shortcut: only the recent part by default; the older nonces are dated by range only, pass --all to enumerate them (about 2 000 more calls)
    low = 0 if '--all' in sys.argv else 20_000_000
    n_low = nonce_at(address, low) if low else 0
    steps = []
    enumerate_all(address, low, latest, n_low, total, steps)
    txs = []
    for block, _, _ in steps:
        b = net.rpc('eth_getBlockByNumber', [hex(block), True], 56, pause=.2)
        at = int(b['timestamp'], 16)
        for t in b['transactions']:
            if t['from'].lower() == address:
                lab = labels.lookup(t['to'] or '', 56) if t['to'] else None
                txs.append(dict(block=block, utc=walk.now_utc(at), at=at, tx=t['hash'], nonce=int(t['nonce'], 16), to=(t['to'] or '').lower(), value_bnb=int(t['value'], 16) / 1e18, selector=t['input'][:10], to_label=(lab or {}).get('name')))
    result = dict(address=address, latest_block=latest, nonce_now=total, older_nonces_not_enumerated=n_low, older_than_block=low, read=len(txs), complete=len(txs) == total - n_low, first=txs[0]['utc'] if txs else None, last=txs[-1]['utc'] if txs else None, txs=txs, read_at=walk.now_utc(__import__('time').time()), method='nonce bisection on public archive nodes; outgoing only')
    (net.ROOT / f'state/bsc_{address}.json').write_text(json.dumps(result))
    print({k: v for k, v in result.items() if k != 'txs'})
    return result


if __name__ == '__main__':
    main(sys.argv[1].lower())
