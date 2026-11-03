"""Global graph from every traced account: five layers, exports, and the addresses shared between files. Reads wallets/*/trace.json, one at a time."""
import json
import sys
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gf import env, ledger_pnl
from gf.graph import Graph


def write_report(out, summary, cases, links):
    lines = ['# Graph of the traced accounts', '', 'Written by `engine/tools/build_graph.py` from every `trace.json` at the date of the run. Partial: it holds only the accounts traced so far, and light traces stop early.', '', 'Money is not identity. An edge shows a transfer or a read, never a common owner. Hubs, services and contracts cannot join two files.', '', '| Item | Value |', '|---|---:|', f"| Files traced | {summary['cases']} |", f"| Addresses | {summary['nodes']} |", f"| Relations | {summary['edges']} |"]
    lines += [f"| Layer {k} | {v} |" for k, v in summary['by_layer'].items()]
    lines += [f"| Addresses shared by files on the money layer | {summary['shared_addresses']} |", '', '## Files', '', '| File | Group | Mode | Polymarket history complete | Edges | Stops |', '|---|---|---|---|---:|---|']
    for c in cases:
        lines.append(f"| {c['case']} | {c['group']} | {c['mode']} | {c['complete']} | {c['edges']} | {', '.join(f'{k} {v}' for k, v in c['stops'])} |")
    lines += ['', '`complete` is about Polymarket activity only. It says nothing about funding on other chains: see each file in `results/wallets/` for chains read and stops.', '', '## Addresses shared by files', '', 'The relation comes from the direction of the walks. A candidate, read from public money. Ownership is not established for any of them.', '', '| Address | Files | Relation | Class | One proof per file |', '|---|---|---|---|---|']
    for link in links:
        proof = '; '.join(f"{c}: `{v[0]['tx']}` chain {v[0]['chain']}, {v[0]['level']}" for c, v in link['evidence'].items())
        lines.append(f"| `{link['address']}` | {', '.join(link['cases'])} | {link['relation']} | {link['cls']} | {proof} |")
    lines += ['', '## Reading the graph', '', '- `results/graphs/flows.json`: for each file, in time order, who paid in, its markets, what left and where to, with chain, block, block hash, transaction, log index and level on each line.', '- `results/graphs/edges.csv`, `edges.json`, `graph.graphml`: every relation with its proof.', '- `results/graphs/viewer.html`: filter by layer and file, click a relation to read its proof.', '- A bridge hop joins files only when the same id was read on both chains. `results/links/` holds links read hop by hop.']
    (out.parent / 'GRAPH.md').write_text('\n'.join(lines) + '\n')


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
    summary.update(cases=len(cases), shared_addresses=len(links), by_relation=dict(Counter(x['relation'] for x in links)))
    (Path(out) / 'summary.json').write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary))
    write_report(Path(out), summary, cases, links)
    for link in links[:40]:
        print(link['address'], link['cls'], link['cases'])


if __name__ == '__main__':
    main(sys.argv[1])
