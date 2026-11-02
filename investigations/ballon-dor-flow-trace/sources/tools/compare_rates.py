"""Named accounts against comparators, same reader, unreadable lines out of the denominator. Exploratory: traits were chosen after seeing the dossiers."""
import itertools
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import labels
import net
import walk

STATE = net.ROOT / 'state'


def load(name):
    p = STATE / name
    return [json.loads(l) for l in p.read_text().splitlines()] if p.exists() else []


def fisher_one_sided(a, n, b, m):
    """P(named count >= a) with hypergeometric margins."""
    total, hits = n + m, a + b
    comb = math.comb
    return sum(comb(hits, k) * comb(total - hits, n - k) for k in range(a, min(n, hits) + 1)) / comb(total, n)


def senders(r, kind=None, name=None):
    rows = r.get('key_senders') or []
    return [x for x in rows if (kind is None or x['kind'] == kind) and (name is None or name.lower() in (x['name'] or '').lower())]


VAULT = '0xc8a6871d4ec4dae64f605db0f8a0b3d9ef928d64'
SWFT = '0xc1d13492285eb664951e201bf7c80c7c6318a1b5'


def vault_in_tx(r):
    """The contract sits between Relay's solver and pUSD in the same transaction: read it from the receipt, the first sender is the solver."""
    if not r.get('pick_tx'):
        return False
    rc = net.rpc('eth_getTransactionReceipt', [r['pick_tx']], 137)
    return any(l['topics'] and len(l['topics']) == 3 and VAULT[2:] in (l['topics'][1] + l['topics'][2]) for l in rc['logs'])


TRAITS = {
    'dépôt via VaultDepositooor (fun.xyz)': (vault_in_tx, lambda r: r.get('immediate') is not None),
    'dépôt via adresse de pont 7702': (lambda r: r.get('via_7702'), lambda r: r.get('immediate') is not None),
    'Relay sur le dépôt lu': (lambda r: r.get('relay'), lambda r: r.get('immediate') is not None),
    'origine Solana (Relay)': (lambda r: r.get('origin_chain') == walk.SOLANA, lambda r: r.get('relay')),
    'KuCoin Hot Wallet 2 avant le pont Solana': (lambda r: any((f.get('label') or '').startswith('KuCoin') for f in r.get('solana_funders') or []), lambda r: r.get('origin_chain') == walk.SOLANA and 'solana_error' not in r),
    'financement moins d\'1 h avant le premier achat': (lambda r: r.get('gap_s') is not None and r['gap_s'] < 3600, lambda r: r.get('gap_s') is not None and r.get('history_complete')),
    'clé reçoit d\'une plateforme étiquetée': (lambda r: bool(senders(r, 'exchange')), lambda r: r.get('key_history_complete')),
    'clé touche SwftSwap': (lambda r: any(x.startswith(SWFT) for x in r.get('counterparties') or []), lambda r: r.get('key_history_complete')),
    'clé reçoit de MetaMask Gas Station': (lambda r: bool(senders(r, None, 'metamask: gas station')), lambda r: r.get('key_history_complete')),
}


def links(rows):
    """Direct key to key transfers and shared personal-sized counterparties inside one group."""
    keys = {r['key']: r['wallet'] for r in rows if r.get('key')}
    parties = {r['key']: {tuple(x.split(':')) for x in r.get('counterparties') or []} for r in rows if r.get('key')}
    direct = []
    for a, b in itertools.combinations(keys, 2):
        if any(x == b for x, _ in parties[a]) or any(x == a for x, _ in parties[b]):
            direct.append((keys[a], keys[b]))
    shared = defaultdict(set)
    for k, ps in parties.items():
        for addr, chain in ps:
            shared[(addr, int(chain))].add(k)
    personal = []
    for (addr, chain), ks in shared.items():
        if len(ks) >= 2 and addr not in keys:
            lab = labels.lookup(addr, chain)
            if lab and lab['category'] != 'other_labeled':
                continue
            c = walk.classify_evm(addr, chain)
            if c['cls'] == 'PERSONAL_SIZED':
                try:
                    rows_, info = walk.evm_rows(addr, chain, 1)
                    n = len({f['src'] if f['dst'] == addr else f['dst'] for f in rows_})
                except Exception:
                    n = None
                if n is not None and n >= walk.HIGH_PARTIES:
                    continue
                personal.append(dict(address=addr, chain=chain, keys=len(ks), value_counterparties=n))
    return dict(keys=len(keys), pairs=math.comb(len(keys), 2), direct=direct, shared_personal=personal)


def main():
    comp, named = load('comparators.jsonl'), load('comparators_named.jsonl')
    # a wallet can sit in two comparator groups: count it once
    read_ok = list({r['wallet']: r for r in comp if r.get('state') == 'READ'}.values())
    fresh = [r for r in read_ok if r['group'] == 'fraiches_recensement']
    out = dict(comparators=len({r['wallet'] for r in comp}), lines=len(comp), states=Counter(r.get('state') for r in comp), groups=Counter(r['group'] for r in comp), read_by_group=Counter(r['group'] for r in read_ok), distinct_read=len(read_ok), traits=[])
    for name, (trait, usable) in TRAITS.items():
        row = dict(trait=name)
        for label, group in (('named', named), ('all', read_ok), ('fresh', fresh)):
            denom = [r for r in group if usable(r)]
            row[label] = [sum(1 for r in denom if trait(r)), len(denom)]
        a, n = row['named']
        for label in ('all', 'fresh'):
            b, m = row[label]
            row[f'p_{label}'] = fisher_one_sided(a, n, b, m) if n and m else None
        out['traits'].append(row)
    out['named_links'] = links(named)
    out['comparator_links'] = links(read_ok)
    out['fresh_links'] = links(fresh)
    named_keys = {r['key']: r['wallet'] for r in named if r.get('key')}
    cross = []
    for r in read_ok:
        for x in r.get('counterparties') or []:
            a = x.split(':')[0]
            if a in named_keys:
                cross.append(dict(comparator=r['wallet'], named_wallet=named_keys[a], counterparty=x))
    out['named_comparator_direct'] = cross
    (STATE / 'compare_rates.json').write_text(json.dumps(out, default=str))
    for r in out['traits']:
        print(r)
    for k in ('named_links', 'comparator_links', 'fresh_links'):
        v = out[k]
        print(k, 'keys', v['keys'], 'pairs', v['pairs'], 'direct', len(v['direct']), 'shared personal', len(v['shared_personal']), v['direct'][:3], v['shared_personal'][:5])
    print('named-comparator direct', cross[:5])


if __name__ == '__main__':
    main()
