"""Reclassifies every funding link between the eleven cases, and measures what a naive shared-funder rule would have claimed.

Classes of a shared address:
- SERVICE_ETIQUETE: a cited source names a service.
- SERVICE_MESURE: no name, but measured traffic or nonce shows a pooled address.
- DISCRIMINANT: shared, unlabelled, low traffic. The only class that could say something about a link, and it still proves no owner.
Direct transfers are read apart. Exploratory, written after the results were read.
"""
import glob
import json
import math
import sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import identities as I

ROOT = Path(__file__).resolve().parent.parent
HIGH_NONCE = 10_000
ZERO = '0x' + '0' * 40


def fisher_one_sided(a, b, c, d):
    """P(at least a) in a 2x2 table with fixed margins: a of a+b hits against c of c+d. Exact, standard library only."""
    n, hits, row = a + b + c + d, a + c, a + b
    total = math.comb(n, row)
    return sum(math.comb(hits, k) * math.comb(n - hits, row - k) for k in range(a, min(hits, row) + 1)) / total


assert abs(fisher_one_sided(1, 0, 0, 1) - .5) < 1e-12
assert abs(fisher_one_sided(3, 0, 0, 3) - .05) < 1e-12
assert fisher_one_sided(0, 5, 5, 0) == 1


def nonce_in(basis):
    return int(basis.split('nonce ')[1].split(',')[0]) if 'nonce ' in (basis or '') else None


def classify(address, sample, pooled):
    lab = (sample.get('source_label') if sample['source'] == address else sample.get('target_label'))
    if lab:
        return 'SERVICE_ETIQUETE', lab['name'] + ', selon ' + lab['source'].split('/')[2]
    if address in pooled:
        return 'SERVICE_MESURE', pooled[address]['measure']
    n = nonce_in(sample.get('basis')) if sample['source'] == address else None
    if n is not None and n > HIGH_NONCE:
        return 'SERVICE_MESURE', f'Nonce de {n:,}'.replace(',', ' ')
    return 'DISCRIMINANT', 'Partagée, sans étiquette, sans trafic mesuré élevé.'


def main():
    pooled = json.loads((ROOT / 'tools/pooled.json').read_text())['addresses']
    cases = {s: json.loads((ROOT / f'cases/{s}.json').read_text()) for s in I.IDS}
    wallets = {c['address']: s for s, c in cases.items()}
    touched = defaultdict(lambda: defaultdict(list))
    for s, c in cases.items():
        for r in c.get('chain_relations', []):
            for a in (r['source'], r['target']):
                if a not in wallets and a != ZERO and str(a) != 'None':
                    touched[a][s].append(r)
    nodes = []
    for address, by in touched.items():
        if len(by) < 2:
            continue
        sample = next(r for v in by.values() for r in v)
        kind, why = classify(address, sample, pooled)
        nodes.append(dict(address=address, class_=kind, why=why, cases=sorted(by), pairs=math.comb(len(by), 2), relations={k: [x['id'] for x in v][:6] for k, v in by.items()}))
    nodes.sort(key=lambda n: (-len(n['cases']), n['class_']))
    naive = set()
    for n in nodes:
        naive.update(combinations(n['cases'], 2))
    discriminant = [n for n in nodes if n['class_'] == 'DISCRIMINANT']
    kept = set()
    for n in discriminant:
        kept.update(combinations(n['cases'], 2))
    # Same nodes among comparators, from the replayed hops.
    base = [json.loads(l) for l in open(ROOT / 'controls/funding_baseline_detail.jsonl')]
    base = [b for b in base if 'error' not in b]
    names = {b['wallet']: b['group'] for b in base}
    seen_in = defaultdict(lambda: defaultdict(set))
    for b in base:
        addresses = {x for h in b['hops'] for x in (h['source'], h['target'])} | {b.get('immediate_source'), b.get('payer'), b.get('relay_user')}
        for a in addresses - {None, b['wallet']}:
            seen_in[a][b['group']].add(b['wallet'])
    for n in nodes:
        n['also_in_baseline'] = {g: len(v) for g, v in seen_in.get(n['address'], {}).items()}
    groups = Counter(b['group'] for b in base)
    comparators = [g for g in groups if g != 'named']
    def rate(test):
        out = {}
        for g in groups:
            rows = [b for b in base if b['group'] == g]
            out[g] = dict(hits=sum(1 for b in rows if test(b)), n=len(rows))
        pool_hits = sum(out[g]['hits'] for g in comparators)
        pool_n = sum(out[g]['n'] for g in comparators)
        a, b = out['named']['hits'], out['named']['n'] - out['named']['hits']
        out['comparateurs_ensemble'] = dict(hits=pool_hits, n=pool_n)
        out['fisher_one_sided_named_vs_comparators'] = round(fisher_one_sided(a, b, pool_hits, pool_n - pool_hits), 5)
        fresh = out.get('fraiches_recensement')
        if fresh:
            out['fisher_one_sided_named_vs_fresh_only'] = round(fisher_one_sided(a, b, fresh['hits'], fresh['n'] - fresh['hits']), 5)
        return out
    kucoin = 'BmFdpraQhkiDQE6SnfG5omcA1VwzqfXrwtNYBwWTymy6'
    has = lambda b, a: any(a in (h['source'], h['target']) for h in b['hops']) or a in (b.get('immediate_source'), b.get('payer'), b.get('relay_user'))
    # Rates that the first pass already holds use all its rows; only the hop-level ones need the replay, whose n is stated.
    first = [json.loads(l) for l in open(ROOT / 'controls/funding_baseline.jsonl')]
    first = [b for b in first if b.get('state') == 'READ']
    detail, base = base, first
    groups_detail, groups = groups, Counter(b['group'] for b in first)
    comparators = [g for g in groups if g != 'named']
    rates = dict(kucoin=rate(lambda b: 'KuCoin Hot Wallet 2' in (b.get('labels') or [])), solana_origin=rate(lambda b: b.get('origin_chain') == 792703809), relay_any=rate(lambda b: bool(b.get('relay'))), seven702_bridge=rate(lambda b: b.get('immediate_kind') == 'EIP7702_DELEGATED_EOA'), high_nonce_sender=rate(lambda b: bool(b.get('high_nonce_sender'))))
    base, groups = detail, groups_detail
    comparators = [g for g in groups if g != 'named']
    rates['router_c8a6'] = rate(lambda b: has(b, '0xc8a6871d4ec4dae64f605db0f8a0b3d9ef928d64')) if 'named' in groups and comparators else None
    prefixes = ('B48k', '9byY', 'G2Y')  # the earlier study kept only these prefixes for its Solana ChangeNOW hubs
    prefix_hits = sorted({str(a) for a in touched if str(a).startswith(prefixes)} | {x for b in base for h in b['hops'] for x in (str(h['source']), str(h['target'])) if x.startswith(prefixes)})
    any_deposit_kucoin = sorted(s for s, c in cases.items() if any(r.get('source') == kucoin for r in c.get('chain_relations', [])))
    direct = json.loads((ROOT / 'graphs/direct_transfers.json').read_text())
    cross = [h for h in direct['hits'] if h['source_case'][0] != h['target_case'][0]]
    out = dict(nodes=nodes, naive_pairs=sorted(naive), naive_pair_count=len(naive), possible_pairs=math.comb(len(I.IDS), 2), discriminant_nodes=discriminant, discriminant_pairs=sorted(kept), direct_funds_across_cases=[h for h in cross if h['kind'] != 'position'], clob_matches=[h for h in cross if h['kind'] == 'position'], direct_scan=dict(addresses=direct['addresses'], chunks=direct['chunks']), baseline_groups=dict(Counter(b['group'] for b in first)), baseline_detail_groups=dict(groups), rates=rates, kucoin_any_deposit=any_deposit_kucoin, changenow_solana_prefix_hits=prefix_hits, note='Comparators read one deposit each. Named wallets are read the same way in `rates`; `kucoin_any_deposit` reads all their deposits and is not comparable to the rates.', ownership='OWNERSHIP_NOT_ESTABLISHED')
    (ROOT / 'graphs/links_classified.json').write_text(json.dumps(out, indent=1, ensure_ascii=False, default=list))
    print('nodes', [(n['address'][:10], n['class_'], n['cases'], n['also_in_baseline']) for n in nodes])
    print('naive pairs', len(naive), 'of', out['possible_pairs'], 'discriminant pairs', len(kept), 'direct funds', len(out['direct_funds_across_cases']), 'clob', len(out['clob_matches']))
    print(json.dumps(rates, indent=0)[:1500])
    print('kucoin any deposit', any_deposit_kucoin)


if __name__ == '__main__':
    main()
