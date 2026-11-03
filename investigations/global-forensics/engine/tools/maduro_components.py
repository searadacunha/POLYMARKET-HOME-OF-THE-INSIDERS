"""Does the September claim of one money network survive once only re-read edges count? Connected components over edges of results/maduro_iran/edge_verification.csv that came back AGREES or CROSSCHAIN_SAME_ID, services removed.

Usage: maduro_components.py <out.json>. A component is a reading aid over money, never a common owner. A shortest path with its proofs is written for each pair of accounts in one component.
"""
import csv
import json
import re
import sys
from collections import defaultdict, deque
from pathlib import Path

HERE = Path(__file__).resolve().parents[2]
ARCHIVE = Path.home() / 'Documents/Crypto/enquete_maduro_iran/phase2'
SERVICE = re.compile(r'relay|bridgers|unknown service|coinbase|kraken|mexc|li\.fi|aeroswap|n\.exchange|hitbtc|dhaman|binance|okx|bybit|gate|kucoin|fun\.xyz|batch-withdrawal|contract', re.I)
PROVED = ('AGREES', 'CROSSCHAIN_SAME_ID')
LOW = lambda a: a.lower() if a.startswith('0x') else a


def main(out):
    rows = list(csv.DictReader((HERE / 'results/maduro_iran/edge_verification.csv').open()))
    accounts = {r['account'].lower(): r['name'] for r in csv.DictReader((ARCHIVE / 'pnl_summary.csv').open())}
    adjacency, kept, removed = defaultdict(list), 0, 0
    for r in rows:
        if r['result'] not in PROVED:
            continue
        if SERVICE.search(r['src_label']) or SERVICE.search(r['dst_label']):
            removed += 1
            continue
        source, target = LOW(r['source']), LOW(r['destination'])
        if source == target:
            continue
        kept += 1
        line = dict(source=source, target=target, chain=r['chain'], asset=r['asset'], amount=r['amount'], utc=r['utc'], tx=r['tx'], level=r['level'], result=r['result'])
        adjacency[source].append((target, line))
        adjacency[target].append((source, line))
    seen, components = set(), []
    for start in adjacency:
        if start in seen:
            continue
        queue, part = deque([start]), set()
        while queue:
            a = queue.popleft()
            if a in part:
                continue
            part.add(a)
            queue.extend(b for b, _ in adjacency[a])
        seen |= part
        held = sorted(accounts[a] or a for a in part if a in accounts)
        if held:
            top = sorted(((len(adjacency[a]), a) for a in part), reverse=True)[:5]
            components.append(dict(addresses=len(part), accounts=held, busiest=[dict(address=a, edges=n) for n, a in top], members=[a for a in part if a in accounts]))
    components.sort(key=lambda c: -len(c['accounts']))

    def path(a, b):
        previous, queue = {a: None}, deque([a])
        while queue:
            x = queue.popleft()
            if x == b:
                break
            for y, line in adjacency[x]:
                if y not in previous:
                    previous[y] = (x, line)
                    queue.append(y)
        steps, x = [], b
        while previous.get(x):
            x, line = previous[x]
            steps.append(line)
        return steps[::-1]
    for c in components:
        members = c.pop('members')
        c['paths_from_first_account'] = {accounts[b] or b: path(members[0], b) for b in members[1:]}
        c['first_account'] = accounts[members[0]] or members[0]
    def groups_without(removed_nodes):
        seen_here, groups = set(removed_nodes), []
        for start in accounts:
            if start in seen_here or start not in adjacency:
                continue
            queue, part = deque([start]), set()
            while queue:
                x = queue.popleft()
                if x in part or x in removed_nodes:
                    continue
                part.add(x)
                queue.extend(y for y, _ in adjacency[x])
            seen_here |= part
            groups.append(sorted(accounts[x] or x for x in part if x in accounts))
        return sorted(groups, key=len, reverse=True)
    # a busy unlabelled address could be a service: does the group hold without it?
    busy = [a for a in sorted(adjacency, key=lambda x: -len(adjacency[x])) if a not in accounts][:6]
    robustness = dict(busiest_non_account=[dict(address=a, edges=len(adjacency[a])) for a in busy], each_removed={a: groups_without({a}) for a in busy}, all_removed=groups_without(set(busy)))
    result = dict(robustness=robustness, edges_read=len(rows), edges_used=kept, edges_touching_a_service=removed, accounts_in_table=len(accounts), components=components, reading='Money between addresses, on re-read edges, services removed by the archive label. An unlabelled service in a path would join what it should not: check the busiest addresses. No common owner is established.')
    Path(out).write_text(json.dumps(result, indent=1))
    print(json.dumps(dict(edges_used=kept, removed=removed, components=[dict(addresses=c['addresses'], accounts=c['accounts'], busiest=c['busiest'][:3]) for c in components]), indent=0)[:1800])


if __name__ == '__main__':
    main(sys.argv[1])
