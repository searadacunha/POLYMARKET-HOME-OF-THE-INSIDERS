"""Order the discovery list without dropping anyone. Usage: discovery_queue.py <results dir> [--budget=N].

Reads only what the trace reads anyway, under the same store keys: each wallet's control, then the Polygon history of its key. So the pass adds no net cost, and the batches that follow replay it.
Writes discovery/queue.json, one row per wallet with its tier and reason, then rewrites discovery/wallets.json in that order with the same entries. A priority is a reading order, and a shared address here is a hint to read first, no finding.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gf import account, env, explorer, labels
from gf.net import BudgetSpent, Net, Refused
from gf.tracer import is_value

env.redirect_temp()


def read_wallet(net, wallet):
    """Owners, then who paid each key and whom each key paid, on Polygon. An address that is its own key is read as a key."""
    owners = account.control(net, wallet).get('owners') or []
    paid_by, paid_to, states = set(), set(), {}
    for key in owners:
        events, coverage = explorer.history(net, key, 137)
        states[key] = coverage['status']
        for e in events:
            if not is_value(e) or not e.get('success', True) or int(e['raw_amount']) <= 0:
                continue
            if e['to'] == key and e['from'] != key:
                paid_by.add(e['from'])
            elif e['from'] == key and e['to'] and e['to'] != key:
                paid_to.add(e['to'])
    return dict(owners=owners, paid_by=paid_by, paid_to=paid_to, states=states)


def private_shared(net, by_address, cache):
    """Addresses seen beside at least two wallets, kept only when sized like a person. A label, a contract, a hub or a failed probe is no hint."""
    out = {}
    for address, wallets in by_address.items():
        if len(wallets) < 2:
            continue
        if address not in cache:
            try:
                cache[address] = labels.classify(net, address, 137).get('cls')
            except Refused:
                cache[address] = labels.UNREAD
        if cache[address] == labels.PERSONAL:
            out[address] = wallets
    return out


def tiers(entries, reads, largest, traced_nodes, net):
    """Tier 1: same owner key, a private funder shared with another listed wallet, a direct move to another listed wallet or key, or money already seen in a traced file. Tier 2: a private destination shared, or several markets. Tier 3: everything else, largest entry first."""
    wallets = {e['wallet'] for e in entries}
    keys, funders, destinations = defaultdict(set), defaultdict(set), defaultdict(set)
    for wallet, r in reads.items():
        for key in r['owners']:
            keys[key].add(wallet)
        for a in r['paid_by']:
            funders[a].add(wallet)
        for a in r['paid_to']:
            destinations[a].add(wallet)
    cache = {}
    shared_funders, shared_destinations = private_shared(net, funders, cache), private_shared(net, destinations, cache)
    everyone = wallets | set(keys)
    rows = []
    for entry in entries:
        w, r, why = entry['wallet'], reads.get(entry['wallet']), []
        if r is None:
            rows.append(dict(entry, tier=3, reasons=['NOT_READ_IN_THIS_PASS'], largest_entry_usd=largest.get(w, 0)))
            continue
        for key in r['owners']:
            if len(keys[key]) > 1:
                why.append(f'same owner key {key} as {len(keys[key]) - 1} other listed wallet(s)')
        why += [f'private funder {a} shared with {len(shared_funders[a]) - 1} other listed wallet(s)' for a in sorted(r['paid_by']) if a in shared_funders]
        why += [f'direct move with listed address {a}' for a in sorted((r['paid_by'] | r['paid_to']) & everyone - {w, *r['owners']})]
        seen_in = sorted({c for a in {w, *r['owners']} for c in traced_nodes.get(a, ()) if c != entry['slug']})
        if seen_in:
            why.append(f"address seen in traced file(s) {', '.join(seen_in[:5])}")
        tier = 1 if why else 2
        if not why:
            why += [f'private destination {a} shared with {len(shared_destinations[a]) - 1} other listed wallet(s)' for a in sorted(r['paid_to']) if a in shared_destinations]
            if len(entry['markets']) > 1:
                why.append(f"in {len(entry['markets'])} markets")
        if not why:
            tier = 3
            why = ['no hint in this pass: order by largest entry']
        rows.append(dict(entry, tier=tier, reasons=why, largest_entry_usd=largest.get(w, 0), key_history={k: v for k, v in r['states'].items()}))
    rows.sort(key=lambda x: (x['tier'], -x['largest_entry_usd'], x['wallet']))
    return rows, dict(shared_funders={a: sorted(v) for a, v in shared_funders.items()}, shared_destinations={a: sorted(v) for a, v in shared_destinations.items()}, same_owner={k: sorted(v) for k, v in keys.items() if len(v) > 1})


def main(results):
    results = Path(results)
    budget = next((int(a.split('=', 1)[1]) for a in sys.argv[2:] if a.startswith('--budget=')), 6000)
    net = Net(budget=budget)
    path = results / 'discovery/wallets.json'
    entries = json.loads(path.read_text())
    largest = {}
    for market in results.glob('discovery/*.json'):
        if market.name not in ('wallets.json', 'queue.json'):
            for row in json.loads(market.read_text()).get('chosen', []):
                largest[row['wallet']] = max(largest.get(row['wallet'], 0), row['usd'])
    graph_nodes = results / 'graphs/nodes.json'
    traced = {n['id']: n['cases'] for n in json.loads(graph_nodes.read_text()) if n.get('cases')} if graph_nodes.exists() else {}
    reads, failed = {}, {}
    try:
        for i, entry in enumerate(entries):
            try:
                reads[entry['wallet']] = read_wallet(net, entry['wallet'])
            except Refused as exc:
                failed[entry['wallet']] = str(exc)[:160]
            if i % 25 == 0:
                print(i, 'of', len(entries), 'calls', net.calls, flush=True)
    except BudgetSpent:
        print('budget spent after', len(reads), flush=True)
    rows, shared = tiers(entries, reads, largest, traced, net)
    assert {r['wallet'] for r in rows} == {e['wallet'] for e in entries} and len(rows) == len(entries)  # a queue never drops a wallet
    (results / 'discovery/queue.json').write_text(json.dumps(dict(read=len(reads), failed=failed, of=len(entries), calls=net.calls, shared=shared, queue=rows), indent=0))
    order = {r['wallet']: i for i, r in enumerate(rows)}
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(sorted(entries, key=lambda e: order[e['wallet']]), indent=0))
    tmp.replace(path)  # run_wallets reads this list when each batch starts, so the next batch follows the new order
    tally = {t: sum(r['tier'] == t for r in rows) for t in (1, 2, 3)}
    print(json.dumps(dict(tiers=tally, read=len(reads), failed=len(failed), calls=net.calls, shared_funders=len(shared['shared_funders']), shared_destinations=len(shared['shared_destinations']), same_owner=len(shared['same_owner']))), flush=True)


if __name__ == '__main__':
    main(sys.argv[1])
