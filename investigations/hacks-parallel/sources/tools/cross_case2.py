"""Recipients of the studied ChangeNOW wallets against the other investigations, per window, and the service-only overlaps of the attack trails."""
import collections, gzip, json, sys, glob, re
from pathlib import Path
sys.path.insert(0,'.')
import cross_case as cc, labels, chainlib as c
ROOT=Path('..')
d=json.load(open(ROOT/'state/runs/cross_case.json'))
need=sorted({r['value'] for r in d['rows'] if r['kind']=='address'}|{a for v in d['pairs'].values() for a in v})
m=labels.metadata(need,137); m1=labels.metadata(need,1)
names={a:sorted({x['name'] for x in labels.lookup(a,137,m)+labels.lookup(a,1,m1)})[:3] for a in need}
out=dict(trail_shared=[],pairs={k:[(a,names.get(a)) for a in v] for k,v in d['pairs'].items()},summary=d['summary'])
seen=collections.defaultdict(set)
for r in d['rows']:
    seen[r['value']].add(r['case'])
for a,s in seen.items(): out['trail_shared'].append(dict(address=a,cases=sorted(s),labels=names.get(a,[])))
print('trail shared addresses',len(out['trail_shared']))
for x in out['trail_shared']: print(' ',x['address'],x['labels'][:2],[y[:14] for y in x['cases']])
print('pairs',out['pairs'])
print('tx rows',[r for r in d['rows'] if r['kind']=='tx'][:3])
rec=collections.defaultdict(set)
for f in glob.glob(str(ROOT/'state/cn_windows/*.gz')):
    p=Path(f).name.replace('.jsonl.gz','').split('__')
    for line in gzip.open(f,'rt'):
        e=json.loads(line)
        rec[e['dst']].add('|'.join(p)); rec[e['src']].add('|'.join(p))
print('addresses in CN windows',len(rec))
hits=[]
for case,pat in cc.FILES.items():
    a,h,found=cc.scan(pat)
    both=set(rec)&a
    for b in sorted(both):
        hits.append(dict(case=case,address=b,windows=sorted(rec[b])))
    print(case,'their addresses',len(a),'in CN windows',len(both))
hm={}
for x in hits: hm.setdefault(x['address'],[]).append(x)
ml=labels.metadata(list(hm),137); ml1=labels.metadata(list(hm),1)
final=[]
for a,v in hm.items():
    t=sorted({y['name'] for y in labels.lookup(a,137,ml)+labels.lookup(a,1,ml1)})
    final.append(dict(address=a,labels=t[:3],cases=sorted({y['case'] for y in v}),windows=v[0]['windows'][:6],n_windows=len(v[0]['windows'])))
out['cn_window_hits']=final
for x in sorted(final,key=lambda z:(bool(z['labels']),-z['n_windows']))[:40]:
    print(' ',x['address'],x['labels'][:2],[y[:16] for y in x['cases']],x['n_windows'],x['windows'][:2])
json.dump(out,open(ROOT/'state/runs/cross_case_final.json','w'),indent=1)
