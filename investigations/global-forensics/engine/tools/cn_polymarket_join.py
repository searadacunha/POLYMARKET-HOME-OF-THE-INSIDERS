"""ChangeNOW towards Polymarket, offline: does a recipient of attributed payout addresses own, or is it, a wallet seen trading? No network.

A recipient is an address that received from an address some source attributes to the service. Each recipient is tested as itself, and through the wallet forms computable from a key: deposit beacon, deposit legacy, Magic proxy.
Safe forms need a node, so they are not tested here and the output says so. Known wallets: taker rows of the phase 8 universe to 2026-09-15, the Ballon d'Or census to late October, and the catalogue tapes.
A hit is a key and a wallet derived from it: it says nothing of who holds either, and nothing of whether this payment funded a bet. Streams recipients; only hits stay in memory.
"""
import csv
import glob
import gzip
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gf import env, proxy
from gf.keccak import create2, keccak256

RECIPIENTS = Path.home() / 'Projects/PolySentinel-ChangeNOW-outflows/state/recipients.csv'
CENSUS = Path.home() / 'Projects/PolySentinel-ballon-dor-2026/derived/census_trades.jsonl.gz'
P8 = Path.home() / 'Documents/Crypto/enquete_maduro_iran/donnees/brut_p8_p9/p8/trades'
# implementation read once from the proxy factory, checked by self_check below; a change there only makes the magic form miss
IMPLEMENTATION_FILE = 'magic_implementation.txt'


def known_wallets(root):
    cache = root / 'catalog' / 'known_wallets.json.gz'
    if cache.exists():
        with gzip.open(cache, 'rt') as f:
            return json.load(f)
    known = {}
    with gzip.open(CENSUS, 'rt') as f:
        for line in f:
            r = json.loads(line)
            w = r['w'].lower()
            k = known.setdefault(w, dict(first=r['ts'], last=r['ts'], sources=['census']))
            k['first'], k['last'] = min(k['first'], r['ts']), max(k['last'], r['ts'])
    print('census wallets', len(known), flush=True)
    for path in sorted(root.glob('markets/*/tape.jsonl.gz')):
        with gzip.open(path, 'rt') as f:
            for line in f:
                r = json.loads(line)
                w = r['proxy_wallet'].lower()
                k = known.setdefault(w, dict(first=r['timestamp'], last=r['timestamp'], sources=[]))
                k['first'], k['last'] = min(k['first'], r['timestamp']), max(k['last'], r['timestamp'])
                if 'tape' not in k['sources']:
                    k['sources'].append('tape')
    print('with tapes', len(known), flush=True)
    for i, path in enumerate(sorted(glob.glob(str(P8 / '*.json')))):
        with open(path) as f:
            for r in json.load(f)['rows']:
                w = r['proxyWallet'].lower()
                t = int(r['timestamp'])
                k = known.setdefault(w, dict(first=t, last=t, sources=[]))
                k['first'], k['last'] = min(k['first'], t), max(k['last'], t)
                if 'p8' not in k['sources']:
                    k['sources'].append('p8')
        if i % 200 == 0:
            print('p8 files', i, 'wallets', len(known), flush=True)
    with gzip.open(cache, 'wt') as f:
        json.dump(known, f)
    return known


def main(out):
    root = env.data_root()
    proxy.self_check()
    known = known_wallets(root)
    print('known wallets', len(known), flush=True)
    magic = (root / 'catalog' / IMPLEMENTATION_FILE).read_text().strip()
    init_magic_parts = proxy._PROXY_HEAD + bytes.fromhex(proxy.PROXY_FACTORY[2:]) + proxy._PROXY_MIDDLE + bytes.fromhex(magic[2:]) + proxy._PROXY_TAIL + proxy._PROXY_ARGS
    init_magic = keccak256(init_magic_parts)
    hits, counts, started = [], Counter(), time.time()
    tmp = Path(out).with_suffix('.tmp')
    with RECIPIENTS.open() as f, tmp.open('w') as sink:
        for i, r in enumerate(csv.DictReader(f)):
            address = r['recipient'].lower()
            counts['rows'] += 1
            counts['tier_' + r['tier']] += 1
            if not address.startswith('0x') or len(address) != 42:
                counts['not_evm'] += 1
                continue
            forms = {'itself': address, 'deposit_beacon': proxy.deposit_wallet(address), 'deposit_legacy': proxy.deposit_wallet(address, 'legacy'), 'magic_proxy': create2(proxy.PROXY_FACTORY, keccak256(bytes.fromhex(address[2:])), init_magic)}
            for form, wallet in forms.items():
                if wallet in known:
                    hit = dict(recipient=address, form=form, wallet=wallet, chain=r['chain'], tier=r['tier'], first_ts=int(r['first_ts'] or 0), first_source=r['first_source'], first_tx=r['first_tx'], last_ts=int(r['last_ts'] or 0), n_transfers=int(r['n_transfers'] or 0), usd=float(r['usd'] or 0), classes=r['classes'], wallet_first_trade=known[wallet]['first'], wallet_last_trade=known[wallet]['last'], known_from=known[wallet]['sources'], payment_before_first_trade=int(r['first_ts'] or 0) <= known[wallet]['first'])
                    hits.append(hit)
                    sink.write(json.dumps(hit) + '\n')
                    sink.flush()
                    counts['hits_' + form] += 1
            if i % 20000 == 0:
                print('rows', i, 'hits', len(hits), f'{time.time() - started:.0f}s', flush=True)
    tmp.replace(out)
    summary = dict(counts=counts, recipients_file_sha_note='recipients.csv of PolySentinel-ChangeNOW-outflows, collected 2026-11-02', known_wallets=len(known), forms_not_tested=['safe: needs a node'], window='payouts from 2026-08-04 to 2026-11-02; wallets seen to 2026-09-15 in phase 8, to late October in the Ballon d Or family', reading='A hit is a key and a derived wallet, or the same address. It does not show that this payment funded a bet, nor who holds either.')
    Path(out).with_name('cn_join_summary.json').write_text(json.dumps(summary, indent=1, default=dict))
    print(json.dumps(summary, default=dict))


if __name__ == '__main__':
    main(sys.argv[1])
