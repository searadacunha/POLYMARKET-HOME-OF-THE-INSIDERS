"""Keep Relay's record of every cross-chain hop already found, before the route retires on 2026-11-24. The record is a pointer and stays one: proof remains the same id read on both chains.

Usage: archive_relay.py <out.json> [--budget=N]. Reads hashes from the Maduro re-reading and from every trace. Answers go to the store; the output lists hash, found or not, id, sender, recipient. One call per 12 s, the route's limit.
"""
import csv
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gf import bridges, env
from gf.net import BudgetSpent, Net, Refused

env.redirect_temp()
HERE = Path(__file__).resolve().parents[1].parent


def hashes():
    out = {}
    with (HERE / 'results/maduro_iran/edge_verification.csv').open() as f:
        for r in csv.DictReader(f):
            if '|' in r['tx']:
                first = r['tx'].split('|')[0]
                out.setdefault(first, 'maduro table')
    for path in sorted((env.data_root() / 'wallets').glob('*/trace.json')):
        for e in json.loads(path.read_text())['edges']:
            if e.get('role') in ('bridge_payout', 'bridge_deposit'):
                out.setdefault(e['transaction_hash'], path.parent.name)
    return out


def main(out_path):
    budget = next((int(a.split('=', 1)[1]) for a in sys.argv[2:] if a.startswith('--budget=')), 2000)
    net = Net(budget=budget)
    rows, found = [], 0
    try:
        for tx, origin in hashes().items():
            try:
                rec = bridges.relay_record(net, tx)
            except Refused as exc:
                rows.append(dict(tx=tx, origin=origin, error=str(exc)[:160]))
                continue
            found += bool(rec)
            rows.append(dict(tx=tx, origin=origin, found=bool(rec), id=(rec or {}).get('id'), sender=(rec or {}).get('sender'), recipient=(rec or {}).get('recipient'), in_txs=(rec or {}).get('in_txs'), out_txs=(rec or {}).get('out_txs')))
    except BudgetSpent:
        print('budget spent', flush=True)
    Path(out_path).write_text(json.dumps(dict(asked=len(rows), found=found, calls=net.calls, rows=rows), indent=0))
    print(dict(asked=len(rows), found=found, calls=net.calls, hits=net.hits), flush=True)


if __name__ == '__main__':
    main(sys.argv[1])
