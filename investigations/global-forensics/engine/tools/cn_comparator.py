"""A base rate for the ChangeNOW join: the same test on recipients of other swap services, same 90 days, same known wallets, same wallet forms.

Usage: cn_comparator.py <out.json> [--budget=N]. Reads listed outgoing transfers of each service address by block window, stops on its budget and says so. A label here is a public list's word, and an address may be one of many a service holds, so a rate is per address read, not per service.
"""
import csv
import gzip
import json
import math
import sys
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gf import env, explorer, proxy
from gf.events import TOKENS
from gf.keccak import create2, keccak256
from gf.net import BudgetSpent, Net, Refused

env.redirect_temp()
WINDOW = json.loads((Path.home() / 'Projects/PolySentinel-ChangeNOW-outflows/state/window.json').read_text())
RECIPIENTS = Path.home() / 'Projects/PolySentinel-ChangeNOW-outflows/state/recipients.csv'
SERVICES = (('Bridgers', '0xb685760ebd368a891f27ae547391f4e2a289895b', 1, 'September archive names it; contract'),
            ('FixedFloat hot wallet', '0x4727250679294802377dd6ca6541b8e459077c95', 1, 'public list, BscScan tag, same address read on Ethereum'),
            ('SwftSwap', '0xc1d13492285eb664951e201bf7c80c7c6318a1b5', 1, 'manual label of the flow trace'),
            ('Bridgers', '0xb685760ebd368a891f27ae547391f4e2a289895b', 137, 'September archive names it on Ethereum; same address read on Polygon'))
MAX_PAGES = 150


def recipients_of(net, service, chain):
    """Outgoing value in the window, listed rows. The block cursor runs until the window ends or the pages run out."""
    start, end = WINDOW['chains'][str(chain)]
    found, rows, pages, status = {}, 0, 0, 'COMPLETE'
    for action in ('tokentx', 'txlistinternal', 'txlist'):
        cursor = start
        while True:
            params = dict(chainid=chain, module='account', action=action, address=service, page=1, offset=1000, sort='asc', startblock=cursor, endblock=end)
            body, _ = net.get(explorer.ETHERSCAN, params, pause=.25, secret=dict(apikey=net.etherscan_key()))
            message = str(body.get('message', ''))
            if body.get('status') != '1' and not any(m in message for m in ('No transactions', 'No records', 'No internal', 'No token')):
                raise Refused(f'{service} {chain} {action}: {message}')
            batch = body.get('result') or []
            pages += 1
            for r in batch:
                if (r.get('from') or '').lower() != service or int(r.get('value') or 0) <= 0 or not r.get('to'):
                    continue
                if action == 'tokentx' and (r.get('contractAddress') or '').lower() not in TOKENS.get(chain, {}):
                    continue
                rows += 1
                found[r['to'].lower()] = found.get(r['to'].lower(), 0) + 1
            if len(batch) < 1000:
                break
            last = int(batch[-1]['blockNumber'])
            if last == cursor:
                status = 'INCOMPLETE: a full page within one block'
                break
            cursor = last
            if pages >= MAX_PAGES:
                status = f'INCOMPLETE: page cap {MAX_PAGES}'
                break
    return found, rows, pages, status


def wilson(k, n, z=1.96):
    if not n:
        return None
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    r = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return [(c - r) / d, (c + r) / d]


def join(addresses, known, init_magic):
    hits = Counter()
    wallets = set()
    for address in addresses:
        forms = dict(itself=address, deposit_beacon=proxy.deposit_wallet(address), deposit_legacy=proxy.deposit_wallet(address, 'legacy'), magic_proxy=create2(proxy.PROXY_FACTORY, keccak256(bytes.fromhex(address[2:])), init_magic))
        matched = {w for w in forms.values() if w in known}
        for form, wallet in forms.items():
            if wallet in known:
                hits[form] += 1
        if matched:
            hits['recipients'] += 1
            wallets |= matched
    return hits, wallets


def main(out):
    budget = next((int(a.split('=', 1)[1]) for a in sys.argv[2:] if a.startswith('--budget=')), 500)
    root = env.data_root()
    proxy.self_check()
    with gzip.open(root / 'catalog' / 'known_wallets.json.gz', 'rt') as f:
        known = json.load(f)
    magic = (root / 'catalog' / 'magic_implementation.txt').read_text().strip()
    init_magic = keccak256(proxy._PROXY_HEAD + bytes.fromhex(proxy.PROXY_FACTORY[2:]) + proxy._PROXY_MIDDLE + bytes.fromhex(magic[2:]) + proxy._PROXY_TAIL + proxy._PROXY_ARGS)
    net = Net(budget=budget)
    rows = []
    for name, service, chain, source in SERVICES:
        try:
            found, listed, pages, status = recipients_of(net, service, chain)
        except (Refused, BudgetSpent) as exc:
            rows.append(dict(service=name, address=service, chain=chain, label_source=source, error=str(exc)[:200]))
            continue
        addresses = [a for a in found if a.startswith('0x') and len(a) == 42]
        hits, wallets = join(addresses, known, init_magic)
        rows.append(dict(service=name, address=service, chain=chain, label_source=source, status=status, pages=pages, outgoing_rows=listed, recipients=len(addresses), recipients_matching=hits['recipients'], wallets=sorted(wallets), by_form={k: v for k, v in hits.items() if k != 'recipients'}, rate=hits['recipients'] / len(addresses) if addresses else None, wilson95=wilson(hits['recipients'], len(addresses))))
        print(rows[-1]['service'], chain, status, len(addresses), hits['recipients'], flush=True)
    base = Counter()
    with RECIPIENTS.open() as f:
        for r in csv.DictReader(f):
            if r['recipient'].startswith('0x'):
                base[r['chain']] += 1
    hits_by_chain = Counter()
    seen = set()
    for line in (Path(__file__).resolve().parents[1].parent / 'results/changenow/cn_polymarket_hits.jsonl').read_text().splitlines():
        h = json.loads(line)
        if (h['chain'], h['recipient']) not in seen:
            seen.add((h['chain'], h['recipient']))
            hits_by_chain[h['chain']] += 1
    reference = {c: dict(recipients=base[c], recipients_matching=hits_by_chain[c], rate=hits_by_chain[c] / base[c] if base[c] else None, wilson95=wilson(hits_by_chain[c], base[c])) for c in base}
    Path(out).write_text(json.dumps(dict(window=WINDOW, known_wallets=len(known), changenow=reference, comparators=rows, calls=net.calls, reading='Rates of a key or address reaching a known trading wallet. Not a rate of funding a bet. Addresses read differ in size and in what they serve.'), indent=1))
    print(json.dumps(reference), net.calls, flush=True)


if __name__ == '__main__':
    main(sys.argv[1])
