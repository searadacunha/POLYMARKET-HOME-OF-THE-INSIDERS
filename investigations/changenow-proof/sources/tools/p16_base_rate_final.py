"""Same raw first-hop reading as p13, on the comparators file once flow-trace finished. Keeps the earlier snapshot. Exploratory."""
import collections, hashlib, json, math, shutil, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import arch, es
ROOT = Path(__file__).resolve().parent.parent
SRC = Path.home() / 'Projects/PolySentinel-flow-trace/state/comparators.jsonl'
SNAP = ROOT / 'evidence/comparators_final.jsonl'
if not SNAP.exists():  # evidence: a replay must not overwrite it
    shutil.copyfile(SRC, SNAP)
rows = [json.loads(l) for l in open(SNAP)]
use = [r for r in rows if r.get('state') == 'READ' and r.get('key') and r.get('key_history_complete')]
print(len(rows), collections.Counter((r.get('group'), r.get('state')) for r in rows), 'usable', len(use), flush=True)
cp, new = {}, collections.defaultdict(set)
for r in use:
    k = r['key'].lower()
    c = set()
    for chain in (1, 137, 42161):
        for action in ('txlist', 'txlistinternal', 'tokentx'):
            for x in es.rows(action, k, chain):
                for side in (x['from'], x['to']):
                    if side and side.lower() != k:
                        c.add((side.lower(), chain))
    cp[r['wallet']] = (k, r['group'], c)
    for a, chain in c:
        new[chain].add(a)
tags = {}
for chain, addrs in sorted(new.items()):
    addrs = sorted(addrs)
    for i in range(0, len(addrs), 200):
        s, b = arch.fetch(f'https://metadata.services.blockscout.com/api/v1/metadata?chainId={chain}&addresses=' + ','.join(addrs[i:i + 200]), f'bs_comp_final_{chain}_{i // 200:04d}.json', pause=.5)
        if s == 200:
            for a, v in json.loads(b).get('addresses', {}).items():
                tags[(a.lower(), chain)] = [t['name'] for t in v.get('tags', [])]
        else:
            print('lookup failed', chain, i, s, flush=True)
hit = {w: sorted(x for x in c if 'changenow' in ' '.join(tags.get(x, [])).lower()) for w, (k, g, c) in cp.items()}


def fisher(a, b, c, d):
    def p(x):
        return math.comb(a + b, x) * math.comb(c + d, a + c - x) / math.comb(a + b + c + d, a + c)
    obs = p(a)
    return sum(p(x) for x in range(max(0, a + c - (c + d)), min(a + b, a + c) + 1) if p(x) <= obs * (1 + 1e-9))


n0, k0, wr = len(cp), sum(bool(v) for v in hit.values()), sum(bool(v[2]) for v in cp.values())
by = {g: dict(lines=sum(1 for r in rows if r.get('group') == g), usable=sum(1 for r in use if r['group'] == g), with_rows=sum(1 for v in cp.values() if v[1] == g and v[2]), hits=sum(1 for w, v in cp.items() if v[1] == g and hit[w])) for g in {r.get('group') for r in rows}}
out = dict(sha256=hashlib.sha256(SNAP.read_bytes()).hexdigest(), lines=len(rows), usable=n0, with_rows=wr, comparators_with_hit=k0, hits={w: v for w, v in hit.items() if v}, by_group=by, fisher_11=fisher(1, 10, k0, n0 - k0), fisher_rows=fisher(1, 5, k0, wr - k0))
(ROOT / 'state/p16.json').write_text(json.dumps(out, indent=1, default=str))
print(json.dumps(out, indent=0, default=str)[:1500])
