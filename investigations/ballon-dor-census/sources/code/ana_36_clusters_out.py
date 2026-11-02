"""CLUSTERS.json from the pair table. Only L1 merges by itself. L2 needs two independent signals, checked by reading: `study/l2_review.json` holds the reading, one entry per candidate pair. No pair is merged because of a service."""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import net

ROOT = net.ROOT


def main():
    d = json.load(open(ROOT / 'derived/clusters_raw.json'))
    review_p = ROOT / 'study/l2_review.json'
    review = json.loads(review_p.read_text()) if review_p.exists() else {}
    parent = {w: w for w in d['accounts']}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    edges = []
    for p in d['pairs']:
        key = '|'.join(sorted((p['a'], p['b'])))
        accepted = review.get(key, {}).get('merge')
        if p['level'] == 'L1_PROUVE_TX' and review.get(key, {}).get('merge', True) or accepted:
            parent[find(p['a'])] = find(p['b'])
            edges.append(dict(a=p['a'], b=p['b'], level=review.get(key, {}).get('final_level', p['level']), reason=review.get(key, {}).get('reason', ''), evidence=[dict(chain=x['chain'], tx=x['tx'], utc=x['utc'], src=x['src'], dst=x['dst'], asset=x['asset'], amount=x['amount']) for x in p['direct']][:8]))
    comps = defaultdict(list)
    for w in d['accounts']:
        comps[find(w)].append(w)
    clusters = []
    for i, (root, ws) in enumerate(sorted(comps.items(), key=lambda x: -len(x[1]))):
        if len(ws) < 2:
            continue
        clusters.append(dict(id=f'C{i + 1}', wallets=sorted(ws), labels={w: d['accounts'][w]['labels'] for w in ws}, links=[e for e in edges if e['a'] in ws], meaning='financial link between addresses. It does not establish common control, identity or a shared bet.'))
    pairs = [{k: v for k, v in p.items() if k != 'direct' or v} for p in d['pairs']]
    out = dict(rule='PROTOCOL.md section 1. L1 merges. L2 only with two independent signals read by hand. L3, L4, L5 never merge.', n_accounts=len(d['accounts']), n_pairs=d['n_pairs'], levels=Counter(p['level'] for p in d['pairs']), pairs_without_evidence=d['n_pairs'] - len(d['pairs']), clusters=clusters, l2_review=review, pairs=pairs, coverage=d['coverage'], unread=d['unread'], positive_control=d['positive_control'])
    (ROOT / 'CLUSTERS.json').write_text(json.dumps(out, indent=1))
    print(out['levels'], 'clusters', [(c['id'], len(c['wallets'])) for c in clusters])


if __name__ == '__main__':
    main()
