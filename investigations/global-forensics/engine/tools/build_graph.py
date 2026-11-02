"""Global graph from every traced account: five layers, exports, and the addresses shared between files. Reads wallets/*/trace.json, one at a time."""
import json
import sys
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gf import env, ledger_pnl
from gf.graph import Graph


def main(out):
    root = env.data_root() / 'wallets'
    graph = Graph()
    cases = []
    for path in sorted(root.glob('*/trace.json')):
        result = json.loads(path.read_text())
        graph.add_trace(result)
        activity = path.with_name('activity.json')
        if activity.exists():
            books = ledger_pnl.account(json.loads(activity.read_text()))
            graph.add_positions(result['wallet'], books['markets'][:40], case=result['case'])
        cases.append(dict(case=result['case'], wallet=result['wallet'], group=result.get('group'), mode=result.get('mode', 'full'), edges=len(result['edges']), stops=Counter(s['reason'].split(':')[0] for s in result['stops']).most_common(), complete=(result.get('account') or {}).get('history_complete')))
    summary = graph.export(out)
    links = graph.links_between_cases()
    (Path(out) / 'shared_addresses.json').write_text(json.dumps(links, indent=1))
    (Path(out) / 'cases.json').write_text(json.dumps(cases, indent=1))
    summary.update(cases=len(cases), shared_addresses=len(links))
    (Path(out) / 'summary.json').write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary))
    for link in links[:40]:
        print(link['address'], link['cls'], link['cases'])


if __name__ == '__main__':
    main(sys.argv[1])
