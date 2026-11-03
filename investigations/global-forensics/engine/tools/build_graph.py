"""Global graph from every traced account: five layers, exports, and the addresses shared between files. Reads wallets/*/trace.json, one at a time."""
import json
import sys
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gf import env, ledger_pnl, state
from gf.graph import ALTERNATIVES, Graph
from datetime import datetime, timezone

DAY = lambda t: datetime.fromtimestamp(int(t), timezone.utc).strftime('%Y-%m-%d %H:%M') if t else 'unknown'


def amount(raw, decimals):
    return f'{int(raw) / 10 ** int(decimals or 0):,.6f}' if decimals is not None else str(raw)


def discovery_entries(results):
    """Entry rows of the reading lists, for the behaviour layer. Timing only, from the tapes."""
    for path in sorted((results / 'discovery').glob('*.json')):
        if path.name in ('wallets.json', 'queue.json'):
            continue
        body = json.loads(path.read_text())
        for row in body.get('chosen', []):
            yield dict(row, market=body['market'])


def write_report(out, summary, cases, links, direct, routes, states):
    lines = ['# Graph of the traced accounts', '', 'Written by `engine/tools/build_graph.py` from every `trace.json` at the date of the run. Partial: it holds only the accounts traced so far, and light traces stop early. Relations re-read from nodes, with what each one proves, are in `results/links/SHARED.md`.', '', 'Money is not identity. An edge shows a transfer or a read, never a common owner. Hubs, services and contracts cannot join two files.', '', '| Item | Value |', '|---|---:|', f"| Files traced | {summary['cases']} |", f"| Addresses | {summary['nodes']} |", f"| Relations | {summary['edges']} |"]
    lines += [f"| Layer {k} | {v} |" for k, v in summary['by_layer'].items()]
    lines += [f"| Addresses shared by files on the money layer | {summary['shared_addresses']} |", f"| Direct transfers between accounts | {summary['direct_transfers']} |", f"| Same address behind a proved bridge hop | {summary['bridge_routes']} |", '', '## Files', '', '| File | Group | Trace | Books | Polymarket history | Funding | Exits | Edges | Stops |', '|---|---|---|---|---|---|---|---:|---|']
    for c in cases:
        s = states[c['case']]
        lines.append(f"| {c['case']} | {c['group']} | {s['processing']} | {s['accounting']} | {s['polymarket_history']['state']} | {s['funding']['state']} | {s['exits']['state']} | {c['edges']} | {', '.join(f'{k} {v}' for k, v in c['stops'])} |")
    lines += ['', '`complete` is about Polymarket activity only. The state is from `engine/gf/state.py`: see `results/COUNTERS.md`.', '', '## Direct transfers between accounts', '', 'From a wallet or owner key of one file to a wallet or owner key of another. Other explanations: ' + ALTERNATIVES['DIRECT_TRANSFER'], '', '| UTC | From file | To file | Amount | Chain | Level | Transaction |', '|---|---|---|---:|---|---|---|']
    for d in direct:
        lines.append(f"| {DAY(d['timestamp'])} | {', '.join(d['from_files'])} | {', '.join(d['to_files'])} | {amount(d['raw'], d['decimals'])} {d['token']} | {d['chain']} | {d['level']} | `{d['tx']}` |")
    lines += ['', '## Addresses shared by files', '', 'The relation comes from the direction of the walks. A candidate, read from public money. Ownership is not established for any of them.', '', '| Address | Files | Relation | Class | One proof per file | Other explanations |', '|---|---|---|---|---|---|']
    for link in links:
        proof = '; '.join(f"{c}: {amount(v[0]['raw'], v[0].get('decimals'))} {v[0]['token']} `{v[0]['tx']}` chain {v[0]['chain']}, {v[0]['level']}" for c, v in link['evidence'].items())
        lines.append(f"| `{link['address']}` | {', '.join(link['cases'])} | {link['relation']} | {link['cls']} | {proof} | {link['alternatives']} |")
    lines += ['', '## The same address behind a proved bridge hop', '', 'Only hops whose id was read on both chains, or a verified CCTP message. Two files using the same chains is no lead and is not listed.', '', '| Side | Address | Route | Files | One proof per file |', '|---|---|---|---|---|']
    for r in routes:
        proof = '; '.join(f"{c}: {amount(v[0]['raw'], v[0].get('decimals'))} {v[0]['token']} `{v[0]['tx']}`, {v[0]['level']}" for c, v in r['evidence'].items())
        lines.append(f"| {r['side']} | `{r['address']}` | {r['origin_chain']} to {r['destination_chain']} | {', '.join(r['files'])} | {proof} |")
    lines += ['', '## Reading the graph', '', '- `results/graphs/flows.json`: for each file, in time order, who paid in, its markets, what left and where to, with chain, block, block hash, transaction, log index and level on each line.', '- `results/graphs/edges.csv`, `edges.json`, `graph.graphml`: every relation with its proof.', '- `results/graphs/viewer.html`: filter by layer and file, click a relation to read its proof.', '- A bridge hop joins files only when the same id was read on both chains. `results/links/` holds links read hop by hop.']
    (out.parent / 'GRAPH.md').write_text('\n'.join(lines) + '\n')


def main(out):
    root = env.data_root() / 'wallets'
    graph = Graph()
    cases, states = [], {}
    traces = sorted(root.glob('*/trace.json'), key=lambda p: (p.parent.name.startswith(('d-', 'cn-')), p.parent.name))  # a named file reads wider, so it is kept when discovery lists the same wallet
    for path in traces:
        result = json.loads(path.read_text())
        if not graph.add_trace(result):
            continue
        activity = path.with_name('activity.json')
        rows = json.loads(activity.read_text()) if activity.exists() else None
        states[result['case']] = state.file_state(result, rows)
        if rows is not None:
            books = ledger_pnl.account(rows)
            graph.add_positions(result['wallet'], books['markets'][:40], case=result['case'])
        cases.append(dict(case=result['case'], wallet=result['wallet'], group=result.get('group'), mode=result.get('mode', 'full'), edges=len(result['edges']), stops=Counter(s['reason'].split(':')[0] for s in result['stops']).most_common(), complete=(result.get('account') or {}).get('history_complete')))
    graph.add_behaviour(discovery_entries(Path(out).parent))
    summary = graph.export(out)
    links = graph.links_between_cases()
    direct, routes = graph.transfers_between_accounts(), graph.bridge_routes()
    (Path(out) / 'shared_addresses.json').write_text(json.dumps(links, indent=1))
    (Path(out) / 'direct_transfers.json').write_text(json.dumps(direct, indent=1))
    (Path(out) / 'bridge_routes.json').write_text(json.dumps(routes, indent=1))
    (Path(out) / 'cases.json').write_text(json.dumps(cases, indent=1))
    summary.update(cases=len(cases), shared_addresses=len(links), direct_transfers=len(direct), bridge_routes=len(routes), by_relation=dict(Counter(x['relation'] for x in links)))
    (Path(out) / 'summary.json').write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary))
    write_report(Path(out), summary, cases, links, direct, routes, states)
    for link in links[:40]:
        print(link['address'], link['cls'], link['cases'])


if __name__ == '__main__':
    main(sys.argv[1])
