"""Budgeted breadth-first walk downstream through addresses of personal size. Stops, with the reason written, at any label, contract, nonce >= 1000 or 400+ counterparties, and never reads past t1."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import chainlib as c
import labels
import net
import tokens


def profile(a, chain, b0, b1, meta):
    code = net.rpc('eth_getCode', [a, 'latest'], chain=chain)
    nonce = int(net.rpc('eth_getTransactionCount', [a, 'latest'], chain=chain), 16)
    tags = labels.lookup(a, chain, meta)
    kind = 'eoa' if code == '0x' else 'eoa7702' if code.startswith('0xef01') else 'contract'
    return dict(address=a, chain=chain, kind=kind, nonce=nonce, labels=tags)


def stop_reason(p, counterparties=None):
    if labels.is_service(p['labels']):
        return 'labelled service'
    if p['kind'] == 'contract':
        return 'contract'
    if p['nonce'] >= 1000:
        return f"nonce {p['nonce']}"
    if counterparties is not None and counterparties >= 400:
        return f'{counterparties} counterparties'
    return ''


def walk(seeds, chain, t0, t1, hops=6, budget=150, cap=4000, extra_stop=()):
    b0, b1 = c.block_at(t0, chain), c.block_at(t1, chain)
    seen, nodes, edges, frontier = set(), {}, {}, [(s.lower(), 0) for s in seeds]
    while frontier and len(nodes) < budget:
        a, depth = frontier.pop(0)
        if a in seen:
            continue
        seen.add(a)
        meta = labels.metadata([a], chain)
        p = profile(a, chain, b0, b1, meta)
        p['depth'] = depth
        nodes[a] = p
        why = stop_reason(p) if a not in {s.lower() for s in seeds} else ''
        if a in extra_stop:
            why = 'declared stop'
        if why:
            p['stop'] = why
            continue
        rows, cut = c.all_edges(a, chain, b0, b1, cap=cap)
        p['truncated'] = cut
        partners = {x['src'] for x in rows} | {x['dst'] for x in rows}
        why = stop_reason(p, len(partners) - 1)
        if why:
            p['stop'] = why
        p['counterparties'] = len(partners) - 1
        p['in_rows'] = sum(x['dst'] == a for x in rows)
        p['out_rows'] = sum(x['src'] == a for x in rows)
        for x in rows:
            x['recognized'] = tokens.recognized(chain, x)
            edges[(x['tx'], x['kind'], str(x['log']), x['src'], x['dst'], x['token'], x['raw'])] = x
        if why or depth >= hops:
            p['stop'] = p.get('stop') or 'hop limit'
            continue
        out = [x for x in rows if x['src'] == a and tokens.worth_following(chain, x)]
        for d in sorted({x['dst'] for x in out}):
            if d not in seen:
                frontier.append((d, depth + 1))
    left = [a for a, _ in frontier if a not in seen]
    for a in left:
        nodes.setdefault(a, dict(address=a, chain=chain, stop='budget', kind='unread', labels=[]))
    return dict(nodes=nodes, edges=list(edges.values()), unread=left, params=dict(seeds=seeds, chain=chain, t0=t0, t1=t1, hops=hops, budget=budget, cap=cap))


def save(result, name):
    path = Path(__file__).resolve().parent.parent / 'state/runs' / (name + '.json')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result))
    return path


if __name__ == '__main__':
    seeds, chain, t0, t1, name, hops, budget = sys.argv[1].split(','), int(sys.argv[2]), c.ts_of(sys.argv[3]), c.ts_of(sys.argv[4]), sys.argv[5], int(sys.argv[6]), int(sys.argv[7])
    r = walk(seeds, chain, t0, t1, hops, budget)
    print(save(r, name), len(r['nodes']), len(r['edges']), 'unread', len(r['unread']))
