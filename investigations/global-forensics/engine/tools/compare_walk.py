"""New tracer against the flow-trace walk, on the same dossiers. An edge only one of them holds is listed, never hidden. Writes results/comparison_walk.json."""
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gf import env

OLD = Path.home() / 'Projects/PolySentinel-flow-trace/data/walk_edges.csv'


def main(out):
    root = env.data_root() / 'wallets'
    old = defaultdict(dict)
    for r in csv.DictReader(OLD.open()):
        old[r['case']][(r['tx'].lower(), r['src'].lower(), r['dst'].lower(), r['raw'])] = r
    table = {}
    for case, rows in old.items():
        path = root / case / 'trace.json'
        if not path.exists():
            continue
        new = json.loads(path.read_text())
        mine = {(e['transaction_hash'].lower(), e['from'].lower(), e['to'].lower(), str(e['raw_amount'])): e for e in new['edges']}
        only_old = [k for k in rows if k not in mine]
        only_new = [k for k in mine if k not in rows]
        table[case] = dict(old_edges=len(rows), new_edges=len(mine), both=len(rows) - len(only_old), only_old=len(only_old), only_new=len(only_new), only_old_rows=[dict(tx=k[0], src=k[1], dst=k[2], raw=k[3], role=rows[k].get('role'), token=rows[k].get('token'), chain=rows[k].get('chain'), direction=rows[k].get('direction')) for k in only_old][:40], only_new_rows=[dict(tx=k[0], src=k[1], dst=k[2], raw=k[3], role=mine[k].get('role'), token=mine[k].get('token'), chain=mine[k].get('chain_id'), direction=mine[k].get('direction'), level=mine[k].get('level'), other=mine[k].get('other_cls'), service=mine[k].get('service')) for k in only_new][:60], new_stops=Counter(s['reason'].split(':')[0] for s in new['stops']), old_chains=Counter(r['chain'] for r in rows.values()), new_chains=Counter(str(e['chain_id']) for e in new['edges']))
    Path(out).write_text(json.dumps(table, indent=1, default=dict))
    for case, t in table.items():
        print(case, {k: t[k] for k in ('old_edges', 'new_edges', 'both', 'only_old', 'only_new')}, dict(t['new_chains']), dict(t['new_stops']))
        print('   only old roles', Counter(r['role'] for r in t['only_old_rows']).most_common(5), ' only new roles', Counter((r['role'], r['other']) for r in t['only_new_rows']).most_common(5))


if __name__ == '__main__':
    main(sys.argv[1])
