"""All 55 pairs, from the raw histories read by the walk (native, internal, every ERC-20, Solana). A shared service links nobody: only personal-sized addresses and direct transfers count.
Writes state/pairs.json. No network beyond what the walk already cached, except class lookups for counterparties not yet probed."""
import itertools
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import evm
import net
import walk

STATE = net.ROOT / 'state'
CANDIDATE_MAX_TX = 300  # above this, a low-nonce EOA is still a hub for pair purposes
SKIP = {evm.ZERO, walk.DEAD}


def load():
    return {p.stem[5:]: json.loads(p.read_text()) for p in sorted(STATE.glob('walk_*.json'))}


def hubs_at_read(w):
    return {x['address'] for x in w['stops'] if x['reason'] == 'HIGH_VOLUME_AT_READ'}


def personal_nodes(w):
    """Addresses of this dossier that a transfer between dossiers would mean something for: its own, and the personal-sized ones reached by the walk. A low-nonce address found to be a hub at reading is out."""
    out = {a for a in w['own']}
    for e in w['edges']:
        if e['other_cls'] == 'PERSONAL_SIZED' and e['role'] != 'link_to_other_dossier':
            out.add(e['src'] if e['direction'] == 'funding' else e['dst'])
    return out - SKIP - hubs_at_read(w)


def raw_rows(w):
    """Raw history of each explorer-read node of this dossier, spam tokens included: a real transfer of an unlisted token is still a transfer."""
    for n in w['nodes']:
        a, chain = n['address'], n['chain']
        if a in hubs_at_read(w):
            continue
        if chain == walk.SOLANA:
            for f in walk.sol_rows(a)[0]:
                yield f
        else:
            for f in evm.history(a, chain)[0]:
                if f['ok'] and int(f['raw']) > 0:
                    yield f


def main():
    walks = load()
    nodes = {s: personal_nodes(w) for s, w in walks.items()}
    own = {s: set(w['own']) for s, w in walks.items()}
    owner_of = defaultdict(set)  # dossier that owns an address first; a walked personal node only if no dossier owns it
    for s, ns in own.items():
        for a in ns:
            owner_of[a].add(s)
    for s, ns in nodes.items():
        for a in ns:
            if not any(a in o for o in own.values()):
                owner_of[a].add(s)
    direct, seen = [], set()
    counter = defaultdict(lambda: defaultdict(list))
    unknown_token = 0
    for s, w in walks.items():
        for f in raw_rows(w):
            key = (f['tx'], f['src'], f['dst'], f['raw'], f.get('contract'))
            mine = nodes[s]
            if f['src'] in mine or f['dst'] in mine:
                other = f['dst'] if f['src'] in mine else f['src']
                counter[(other, f['chain'])][s].append(dict(tx=f['tx'], at=f['at'], token=f['token'], known=f.get('known', True), amount=int(f['raw']) / 10 ** int(f['decimals']), kind=f['kind'], direction='out' if f['src'] in mine else 'in'))
            src_cases, dst_cases = owner_of.get(f['src'], set()), owner_of.get(f['dst'], set())
            if src_cases and dst_cases and not (src_cases & dst_cases) and key not in seen:
                seen.add(key)
                is_known = f.get('known', True)
                unknown_token += not is_known
                direct.append(dict(src=f['src'], src_case=sorted(src_cases), dst=f['dst'], dst_case=sorted(dst_cases), chain=f['chain'], tx=f['tx'], block=f.get('block'), at=f['at'], utc=walk.now_utc(f['at']), token=f['token'], kind=f['kind'], amount=int(f['raw']) / 10 ** int(f['decimals']), raw=f['raw'], decimals=f['decimals'], known_token=is_known, source=f.get('source')))
    shared = []
    for (addr, chain), by_case in counter.items():
        if len(by_case) < 2 or addr in SKIP:
            continue
        if all(not x['known'] for rows in by_case.values() for x in rows):
            continue  # shared only through unlisted tokens: airdrop and poisoning spam
        cls = walk.classify(addr, chain)
        shared.append(dict(address=addr, chain=chain, cases=sorted(by_case), cls=cls['cls'], kind=cls.get('kind'), nonce=cls.get('nonce'), label=cls.get('label'), contract_name=cls.get('contract_name'), detail={c: sorted(rows, key=lambda x: x['at'])[:3] for c, rows in by_case.items()}))
    pairs = {f'{a}|{b}': dict(direct=[], shared_personal=[], shared_service=[], shared_unattributed=[]) for a, b in itertools.combinations(sorted(walks), 2)}
    for d in direct:
        for a in d['src_case']:
            for b in d['dst_case']:
                pairs['|'.join(sorted((a, b)))]['direct'].append(d['tx'])
    for x in shared:
        kind = 'shared_service' if x['cls'] == 'SERVICE' else 'shared_personal' if x['cls'] == 'PERSONAL_SIZED' else 'shared_unattributed'
        for a, b in itertools.combinations(x['cases'], 2):
            pairs['|'.join(sorted((a, b)))][kind].append(x['address'])
    out = dict(direct=sorted(direct, key=lambda d: d['at']), shared=sorted(shared, key=lambda x: (x['cls'], -len(x['cases']))), pairs=pairs, nodes={s: sorted(n) for s, n in nodes.items()})
    (STATE / 'pairs.json').write_text(json.dumps(out))
    print('direct', len(direct), 'of which unlisted token', unknown_token)
    print('shared by class', {c: sum(1 for x in shared if x['cls'] == c) for c in {x['cls'] for x in shared}})
    print('pairs with a direct transfer', sum(1 for v in pairs.values() if v['direct']), 'with shared personal', sum(1 for v in pairs.values() if v['shared_personal']), 'with shared service', sum(1 for v in pairs.values() if v['shared_service']))


if __name__ == '__main__':
    main()
