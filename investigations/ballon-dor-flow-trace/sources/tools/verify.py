"""Second source for every hop of the path files: the explorer row against a public node's receipt (EVM) or a second Solana endpoint. Fills second_source in the CSVs and writes state/verify.json."""
import csv
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import evm
import net
import sol
import walk

ROOT = net.ROOT
TRANSFER = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
LOG_FEE = '0x4dfe1bbbcf077ddc3e01291eea2d5c70c2b422b415d95645b9adcfd678cb1d63'


def check_evm(r, row):
    chain = int(row['chain_id'])
    if chain not in net.RPC or not row['tx'].startswith('0x'):
        return 'not_checked'
    try:
        rc = net.rpc('eth_getTransactionReceipt', [row['tx']], chain, pause=.2)
    except Exception as e:
        return 'unreadable:' + str(e)[:40]
    if rc.get('status') != '0x1':
        return 'failed_tx'
    src, dst = row['source'].lower(), row['target'].lower()
    addresses = {l['address'].lower() for l in rc['logs']}
    logs = [l for l in rc['logs'] if l['topics'] and l['topics'][0] == TRANSFER and len(l['topics']) == 3]
    seen = {('0x' + l['topics'][1][-40:], '0x' + l['topics'][2][-40:]) for l in logs}
    if (src, dst) in seen:
        return 'node_receipt_log'
    t = net.rpc('eth_getTransactionByHash', [row['tx']], chain, pause=.2)
    if t['from'].lower() == src and (t.get('to') or '').lower() == dst and int(t['value'], 16) > 0:
        return 'node_tx_value'
    if row['event'].startswith(('relay', 'wrap', 'burn', 'onward_relay')) or src == dst:
        return 'node_receipt_tx_exists'
    if dst in {x for pair in seen for x in pair} or src in {x for pair in seen for x in pair}:
        return 'node_receipt_party_seen'
    return 'node_receipt_tx_exists_internal_or_unmatched'  # internal value transfers leave no log on Ethereum


def check_sol(row):
    if not row['tx'] or row['tx'].startswith('0x'):
        return 'not_checked'
    try:
        tx = sol.transaction(row['tx'], endpoint=sol.SECOND)
    except Exception as e:
        return 'unreadable:' + str(e)[:40]
    parties = {m['owner'] for m in sol.moves(tx)}
    return 'second_rpc_parties_seen' if row['source'] in parties and row['target'] in parties else 'second_rpc_tx_exists'


def main():
    tally = Counter()
    cache = {}
    for name in ('funding_paths', 'cashout_paths'):
        path = ROOT / f'data/{name}.csv'
        rows = list(csv.DictReader(path.open()))
        for r in rows:
            key = (r['tx'], r['source'], r['target'], r['chain_id'])
            if key not in cache:
                cache[key] = check_sol(r) if int(r['chain_id']) == walk.SOLANA else check_evm(None, r)
            r['second_source'] = cache[key]
            tally[(name, r['second_source'])] += 1
        with path.open('w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
    (ROOT / 'state/verify.json').write_text(json.dumps({f'{a}|{b}': n for (a, b), n in tally.items()}))
    for k, n in sorted(tally.items()):
        print(k, n)


if __name__ == '__main__':
    main()
