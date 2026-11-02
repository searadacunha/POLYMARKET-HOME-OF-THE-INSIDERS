"""Audit, exploratory: is the named group's overlap unusual as a group, which E4's per-pair family-wide bar cannot say? Random groups drawn from wallets holding the same token. Reads only."""
import glob,json,os,random,sys
C='/Users/benjamindacunha/Projects/PolySentinel-investigation/'
sys.path.insert(0,C+'collective/code');sys.dont_write_bytecode=True
import rows as R
from ana_overlap_core_v2 import matrix,pair_scores
from collections import Counter,defaultdict
named={json.load(open(f))['address'].lower():os.path.basename(f)[:-5] for f in glob.glob(C+'cases/*.json')}
rows=[r for r in R.family() if r[0]=='M']
cat=R.catalog()
for name,end in (('D2',R.D2),('T_FIN',R.T_FIN)):
    m=matrix(rows,end);real=pair_scores(m)
    by=defaultdict(list)
    for p,v in real.items():by[v[0]].append(v[1])
    for k in by:by[k].sort()
    import bisect
    def pct(v):return bisect.bisect_right(by[v[0]],v[1])/len(by[v[0]])
    inn=[w for w in m if w in named]
    # the token the press selected on: the one most held among named wallets in this universe
    t=Counter(x for w in inn for x in m[w]).most_common(1)[0]
    pool=[w for w in m if t[0] in m[w]]
    print(name,'universe',len(m),'named in it',len(inn),'most shared token held by',t[1],'named, pool of holders',len(pool))
    def stat(group):
        s=[pct(real[tuple(sorted(a))]) if tuple(sorted(a)) in real else None for a in __import__('itertools').combinations(group,2)]
        s=[x for x in s if x is not None]
        return sum(s)/len(s) if s else 0,len(s)
    obs,n=stat(inn);print(' named group mean within-count percentile',round(obs,4),'over',n,'pairs')
    rng=random.Random(20261102)
    others=[w for w in pool]
    nulls=[stat(rng.sample(others,min(len(inn),len(others))))[0] for _ in range(2000)]
    print(' same-token groups: median',round(sorted(nulls)[1000],4),'95th',round(sorted(nulls)[1900],4),'share >= named',round(sum(x>=obs for x in nulls)/2000,4))
    allw=sorted(m)
    nulls2=[stat(rng.sample(allw,len(inn)))[0] for _ in range(2000)]
    print(' any-wallet groups: median',round(sorted(nulls2)[1000],4),'share >= named',round(sum(x>=obs for x in nulls2)/2000,4))
