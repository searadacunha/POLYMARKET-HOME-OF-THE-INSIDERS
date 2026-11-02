"""A directed graph of money with evidence on every edge. Grouping needs a verifiable link, never shared infrastructure.

Kinds come from cited labels. An unlabelled address stays UNKNOWN whatever its activity: a high fanout
marks it POTENTIAL_INFRASTRUCTURE, a question for review, and it then links nobody. One payment does not
group two addresses, since exchanges pay strangers all day: a group needs on-chain control or money going
both ways between them, and it still names no owner.
"""
from collections import Counter, defaultdict

from .flows import ZERO, is_collateral_mechanics, label_of
from .links import OWNERSHIP

FANOUT_LIMIT = 20
INFRASTRUCTURE_KINDS = {'protocol', 'bridge', 'router', 'exchange', 'pool', 'factory', 'collateral_contract', 'relayer'}
CONTROL = 'CONTROL_ONCHAIN'
LINKING_STATES = {'ONCHAIN_CONFIRMED'}


def node_kind(address, fanout=0, known=None):
    known = known or {}
    if address in known:
        return known[address]
    label = label_of(address)
    if label:
        return label['kind'].upper()
    if address == ZERO or is_collateral_mechanics(address):
        return 'COLLATERAL_MECHANICS'
    return 'POTENTIAL_INFRASTRUCTURE' if fanout >= FANOUT_LIMIT else 'UNKNOWN'


def build_graph(relations, known=None):
    """Edges are kept one per chain, transaction and log. Fanout is counted over this graph only, and says so."""
    unique, unkeyed = {}, []
    for r in relations:
        if r.get('tx') and r.get('log_index') is not None:
            unique.setdefault((r['chain_id'], r['tx'], r['log_index'], r['source'], r['target']), r)
        else:
            unkeyed.append(r)
    edges = list(unique.values()) + unkeyed
    out, into = defaultdict(set), defaultdict(set)
    for e in edges:
        out[e['source']].add(e['target'])
        into[e['target']].add(e['source'])
    addresses = set(out) | set(into)
    nodes = {a: dict(kind=node_kind(a, max(len(out[a]), len(into[a])), known), name=(label_of(a) or {}).get('name'), label_source=(label_of(a) or {}).get('source'), out_degree=len(out[a]), in_degree=len(into[a])) for a in sorted(addresses)}
    return dict(nodes=nodes, edges=edges, fanout_scope='Counted in this graph only.', states=dict(Counter(e['state'] for e in edges)))


def clusters(graph, control_links=()):
    """Groups only through on-chain control or a direct transfer between two non-infrastructure addresses."""
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    reasons = defaultdict(list)
    for link in control_links:
        parent[find(link['owner'])] = find(link['wallet'])
        reasons[link['owner'], link['wallet']].append(dict(kind=CONTROL, basis=link['basis']))
    usable = {'UNKNOWN', 'STUDIED_WALLET'}
    directed = defaultdict(list)
    for e in graph['edges']:
        if e['state'] in LINKING_STATES and {graph['nodes'][e['source']]['kind'], graph['nodes'][e['target']]['kind']} <= usable:
            directed[e['source'], e['target']].append(e)
    for (a, b), there in directed.items():
        back = directed.get((b, a))
        if back and a < b:
            parent[find(a)] = find(b)
            reasons[a, b].extend(dict(kind='TWO_WAY_TRANSFERS', tx=e['tx'], log_index=e['log_index'], chain_id=e['chain_id'], direction=f"{e['source']}->{e['target']}") for e in there + back)
    members = defaultdict(set)
    for x in list(parent):
        members[find(x)].add(x)
    out = []
    for group in members.values():
        if len(group) < 2:
            continue
        evidence = [dict(between=list(k), **v) for k, items in reasons.items() if k[0] in group and k[1] in group for v in items]
        out.append(dict(members=sorted(group), corroborating=evidence, ownership=OWNERSHIP, control_only=all(x['kind'] == CONTROL for x in evidence), alternatives=['A payment between two people.', 'A service or custodian paying from an address we cannot label.', 'A key controlled by a service for its customer.']))
    return sorted(out, key=lambda c: -len(c['members']))
