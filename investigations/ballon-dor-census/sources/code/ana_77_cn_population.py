"""Amendment 3. From the bettors to ChangeNOW: fresh wallets against a random sample of old ones. One hop, labeled counterparties only. Absence of a tag is unknown, not absence of service."""
import json
import math
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import hist
import labels
import net

ROOT = net.ROOT
CHAINS = (1, 137, 42161)
T_END = 1793044800 + 7 * 86400
T_TAPE = 1785542400
SEED = 20261102


def fisher(a, b, c, d):
    """Two-sided exact test on [[a, b], [c, d]]."""
    n = a + b + c + d
    r1, c1 = a + b, a + c
    def p(x):
        return math.comb(r1, x) * math.comb(n - r1, c1 - x) / math.comb(n, c1)
    obs = p(a)
    return min(1.0, sum(p(x) for x in range(max(0, c1 - (n - r1)), min(r1, c1) + 1) if p(x) <= obs * (1 + 1e-9)))


def main():
    d = json.load(open(ROOT / 'derived/stats_v2_table.json'))['wallets']
    fresh = sorted(w for w, v in d.items() if v['status'] == 'fresh')
    old = sorted(w for w, v in d.items() if v['status'] == 'old')
    sample_old = random.Random(SEED).sample(old, len(fresh))
    path = ROOT / 'derived/cn_population.json'
    out = json.loads(path.read_text()) if path.exists() else {}
    for group, wallets in (('fresh', fresh), ('old', sample_old)):
        for i, w in enumerate(wallets):
            if w in out:
                continue
            try:
                res = net.rpc('eth_call', [dict(to=w, data='0x8da5cb5b'), 'latest'])
                owner = '0x' + res[-40:] if res and len(res) >= 42 else None
            except net.FetchError as e:
                out[w] = dict(group=group, error=str(e)[:100])
                continue
            if not owner or owner == '0x' + '0' * 40:
                out[w] = dict(group=group, owner=None)
                continue
            t0 = (d[w]['deploy'] - 60 * 86400) if group == 'fresh' else T_TAPE
            rows, unread = [], []
            for c in CHAINS:
                try:
                    r, _ = hist.evm_rows(owner, c)
                    rows += [x for x in r if t0 <= x['ts'] <= T_END and x.get('recognized')]
                except net.FetchError as e:
                    unread.append(c)
            hits = []
            for c in CHAINS:
                cps = sorted({(x['dst'] if x['src'] == owner else x['src']) for x in rows if x['chain'] == str(c)} - {None})
                labels.prefetch(cps, c)
                for a in cps:
                    got = labels._cache.get((a, c)) or {}
                    tags = [t for t in got.get('tags', []) if 'changenow' in t.lower().replace(' ', '')]
                    if tags:
                        for x in rows:
                            if x['chain'] == str(c) and a in (x['src'], x['dst']):
                                hits.append(dict(chain=c, tx=x['tx'], ts=x['ts'], utc=hist.utc(x['ts']), direction='in' if x['dst'] == owner else 'out', counterparty=a, tags=tags[:3], asset=x['asset'], amount=x['amount']))
            out[w] = dict(group=group, owner=owner, n_rows=len(rows), unread=unread, hits=hits)
            if i % 20 == 0:
                path.write_text(json.dumps(out))
                print(group, i, 'with hit', sum(1 for v in out.values() if v.get('hits')), flush=True)
    path.write_text(json.dumps(out))
    rep = {}
    for g in ('fresh', 'old'):
        rows = [v for v in out.values() if v.get('group') == g]
        read = [v for v in rows if v.get('owner') and not v.get('unread')]
        anyh = [v for v in read if v.get('hits')]
        inn = [v for v in read if any(h['direction'] == 'in' for h in v['hits'])]
        outt = [v for v in read if any(h['direction'] == 'out' for h in v['hits'])]
        rep[g] = dict(n=len(rows), read=len(read), no_owner=sum(1 for v in rows if not v.get('owner')), any_tag=len(anyh), inflow=len(inn), outflow=len(outt))
    a, b = rep['fresh']['any_tag'], rep['fresh']['read'] - rep['fresh']['any_tag']
    c, e = rep['old']['any_tag'], rep['old']['read'] - rep['old']['any_tag']
    rep['fisher_any'] = fisher(a, b, c, e)
    rep['hits_fresh'] = [dict(wallet=w, **h) for w, v in out.items() if v.get('group') == 'fresh' for h in v.get('hits', [])]
    rep['hits_old_n'] = sum(len(v.get('hits', [])) for v in out.values() if v.get('group') == 'old')
    (ROOT / 'derived/cn_population_result.json').write_text(json.dumps(rep, indent=1))
    with open(ROOT / 'study/test_register.jsonl', 'a') as f:
        f.write(json.dumps(dict(at=int(time.time()), script='ana_77_cn_population.py', status='exploratoire', test='cn_frais_contre_anciens', p=rep['fisher_any'], effect=[a, b, c, e])) + '\n')
    print({k: v for k, v in rep.items() if k != 'hits_fresh'})
    for h in rep['hits_fresh'][:30]:
        print(h['wallet'][:10], h['chain'], h['utc'][:16], h['direction'], h['counterparty'][:12], h['tags'][:1], h['asset'], round(h['amount'], 4), h['tx'][:12])


if __name__ == '__main__':
    assert abs(fisher(3, 1, 1, 3) - .4857) < .001
    main()
