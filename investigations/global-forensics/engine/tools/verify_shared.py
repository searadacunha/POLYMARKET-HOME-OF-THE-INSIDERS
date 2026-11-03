"""Every address two files share on the money layer, and every direct transfer between accounts: read each proving transaction again from two nodes, then answer funder, service and holder apart, with the size of what passed through.

Usage: verify_shared.py <graph dir> <out.json> [--budget=N]. Writes <out.json> and SHARED.md beside it. A shared address joining files is a lead. A large flow or many parties through a small address suggests a service nobody labelled, and it is flagged rather than decided.
"""
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gf import env, explorer, labels, proof
from gf.events import rough_usd
from gf.net import BudgetSpent, Net, Refused

env.redirect_temp()
LARGE_USD = 1_000_000
MANY_PARTIES = 100


def amount(raw, decimals):
    return f'{int(raw) / 10 ** int(decimals or 0):,.6f}' if decimals is not None else str(raw)


def read_proof(net, tx, chain, raw):
    """One move read again from two hosts. Chains without a reader here stay marked, never counted as read."""
    if not isinstance(chain, int) or chain not in (1, 137, 42161, 8453, 10, 56):
        return dict(level='NOT_READ_HERE', amount_found=None)
    try:
        moves, record = proof.read_tx(net, chain, tx)
    except Refused as exc:
        return dict(level='READ_FAILED', amount_found=None, error=str(exc)[:160])
    found = [m for m in moves if m['raw_amount'] == str(raw)]
    return dict(block=record['block_number'], status=record['status'], second_host=record.get('second_host'), level=found[0]['level'] if found else None, log_index=found[0].get('log_index') if found else None, amount_found=bool(found))


def write_report(path, rows, direct, routes):
    flagged = [r for r in rows if r.get('flag')]
    plain = [r for r in rows if not r.get('flag')]
    lines = ['# Shared addresses and direct transfers, read again', '', 'Written by `engine/tools/verify_shared.py` from `results/graphs/`. Each proof is read again from two node hosts. Ownership is not established for any address here, and none of this says what anyone knew.', '', f'{len(plain)} shared addresses without a flag, {len(flagged)} flagged, {len(direct)} direct transfers, {len(routes)} same addresses behind a proved bridge hop.', '']
    for title, items in (('Shared addresses', plain), ('Flagged: may be a service nobody labelled, joins no one', flagged)):
        lines += [f'## {title}', '', '| Address | Relation | Files | Proofs: file, amount, chain, level, transaction | Received, rough USD | Parties | Holder | Other explanations |', '|---|---|---|---|---:|---:|---|---|']
        for r in items:
            proofs = '<br>'.join(f"{p['case']}: {amount(p['raw'], p.get('decimals'))} {p.get('token')}, chain {p['chain']}, {p['level']}, `{p['tx']}`" for p in r['proofs'])
            lines.append(f"| `{r['address']}` | {r['relation']} | {', '.join(r['cases'])} | {proofs} | {r.get('value_received_rough_usd', 0):,} | {r.get('value_parties')} | {r['ownership']} | {r.get('alternatives')} |")
        lines.append('')
    lines += ['## Direct transfers between accounts', '', '| From file | To file | Amount | Chain | Level | Transaction | Other explanations |', '|---|---|---:|---|---|---|---|']
    for d in direct:
        lines.append(f"| {', '.join(d['from_files'])} | {', '.join(d['to_files'])} | {amount(d['raw'], d.get('decimals'))} {d.get('token')} | {d['chain']} | {d['level']} | `{d['tx']}` | {d['alternatives']} |")
    lines += ['', '## The same address behind a proved bridge hop', '', '| Side | Address | Route | Files | Proofs | Other explanations |', '|---|---|---|---|---|---|']
    for r in routes:
        proofs = '<br>'.join(f"{c}: {amount(v[0]['raw'], v[0].get('decimals'))} {v[0].get('token')}, chain {v[0]['chain']}, {v[0]['level']}, `{v[0]['tx']}`" for c, v in r['evidence'].items())
        lines.append(f"| {r['side']} | `{r['address']}` | {r['origin_chain']} to {r['destination_chain']} | {', '.join(r['files'])} | {proofs} | {r['alternatives']} |")
    path.write_text('\n'.join(lines) + '\n')


def main(graph_dir, out):
    budget = next((int(a.split('=', 1)[1]) for a in sys.argv[3:] if a.startswith('--budget=')), 2500)
    net = Net(budget=budget)
    links = json.loads((Path(graph_dir) / 'shared_addresses.json').read_text())
    cases = {c['case']: c['wallet'] for c in json.loads((Path(graph_dir) / 'cases.json').read_text())}
    rows = []
    try:
        for link in links:
            address = link['address']
            row = dict(address=address, cases=link['cases'], relation=link['relation'], ownership='OWNERSHIP_NOT_ESTABLISHED', proofs=[], alternatives=link.get('alternatives'))
            for case, items in link['evidence'].items():
                for item in items[:3]:
                    row['proofs'].append(dict(case=case, tx=item['tx'], chain=item['chain'], role=item['role'], direction=item['direction'], raw=item['raw'], decimals=item.get('decimals'), token=item['token'], **read_proof(net, item['tx'], item['chain'], item['raw'])))
            usd, parties, statuses, wallets_paid = 0.0, set(), {}, []
            for chain in (1, 137):
                events, coverage = explorer.history(net, address, chain)
                statuses[chain] = dict(status=coverage['status'], rows=coverage.get('rows'))
                for e in events:
                    if e.get('success', True) and int(e['raw_amount']) > 0 and (e.get('token_known') or e['kind'] != 'erc20'):
                        usd += rough_usd(e) if e['to'] == address else 0
                        parties.add(e['from'] if e['to'] == address else e['to'])
                        if e['from'] == address and e['to'] in set(cases[c] for c in link['cases'] if c in cases):
                            wallets_paid.append(dict(to=e['to'], tx=e['transaction_hash'], token=e['token'], raw=e['raw_amount'], t=e['timestamp'], level=e['level']))
            info = labels.classify(net, address, 1)
            row.update(history=statuses, value_received_rough_usd=round(usd), value_parties=len(parties), classify=dict(kind=info.get('kind'), nonce=info.get('nonce'), cls=info.get('cls'), label=(info.get('label') or {}).get('name')), paid_a_file_wallet_directly=wallets_paid[:6], flag='LARGE_FLOW_POSSIBLE_UNLABELLED_SERVICE' if usd >= LARGE_USD else 'MANY_PARTIES_POSSIBLE_UNLABELLED_SERVICE' if len(parties) >= MANY_PARTIES else None)
            rows.append(row)
            print(address[:12], link['cases'], link['relation'], round(usd), len(parties), row['flag'], [p.get('level') for p in row['proofs']], flush=True)
    except BudgetSpent:
        print('budget spent at', len(rows), 'of', len(links), flush=True)
    direct = json.loads((Path(graph_dir) / 'direct_transfers.json').read_text())
    routes = json.loads((Path(graph_dir) / 'bridge_routes.json').read_text())
    for d in direct:
        d.update(read_proof(net, d['tx'], d['chain'], d['raw']))
    Path(out).write_text(json.dumps(dict(read=len(rows), of=len(links), calls=net.calls, rows=rows, direct=direct, routes=routes), indent=1))
    write_report(Path(out).parent / 'SHARED.md', rows, direct, routes)


if __name__ == '__main__':
    main(*sys.argv[1:3])
