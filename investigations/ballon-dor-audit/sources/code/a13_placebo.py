"""Audit: the E1 placebo. The frozen code lets a shuffled birth date fall after a wallet's buy and still counts it as fresh, which inflates the null. Recomputed three ways, frozen files untouched."""
import gzip,json,random,sys,time
C='/Users/benjamindacunha/Projects/PolySentinel-investigation/collective/'
sys.path.insert(0,C+'code');sys.dont_write_bytecode=True
import rows as R,signals as K
AGES={}
with gzip.open(C+'data/ages.jsonl.gz','rt') as f:
    for line in f:
        a=json.loads(line)
        if 'first_ts' in a:AGES[a['wallet']]=a['first_ts']
FAM=list(R.family());CTL=list(R.controls())
TOK={'M':K.by_token([r for r in FAM if r[0]=='M']),'X':K.by_token(CTL)}
stored=json.load(open(C+'derived/A_placebo.json'))
DAY=R.DAY
def run(u,end,draws=1000,seed=20261101):
    sets={}
    for token,rs in TOK[u].items():
        for t in K.hourly_ticks(max(R.T0,rs[0][0]),end):
            q=K.qualified(rs,t,72,1000)
            if len(q)>=2:sets[tuple(sorted((w,first) for w,(first,_) in q.items()))]=token
    wallets=sorted({w for s in sets for w,_ in s});known=[w for w in wallets if w in AGES]
    limit={}
    for s in sets:
        for w,first in s:limit[w]=min(limit.get(w,9e18),first)
    sets=list(sets)
    def stat(age,strict):
        best=0
        for s in sets:
            n=0
            for w,first in s:
                if w in age:
                    d=first-age[w]
                    if d<=14*DAY and (not strict or d>=0):n+=1
            if n>best:best=n
        return best
    real=stat(AGES,False)
    assert real==stat(AGES,True),'a real birth date after a buy'
    rng=random.Random(seed);values=[AGES[w] for w in known]
    impossible=0;hits=dict(frozen=0,strict=0,constrained=0)
    dist=dict(frozen={},strict={},constrained={})
    order=sorted(known,key=lambda w:limit[w])
    for k in range(draws):
        rng.shuffle(values);age=dict(zip(known,values))
        impossible+=sum(1 for w in known if age[w]>limit[w])
        for name,strict in(('frozen',False),('strict',True)):
            v=stat(age,strict);dist[name][v]=dist[name].get(v,0)+1;hits[name]+=v>=real
        # a feasible shuffle: each wallet draws at random among the dates still free that are not after its first buy
        pool=sorted(values);a2={}
        import bisect
        for w in order:
            i=bisect.bisect_right(pool,limit[w])
            j=rng.randrange(i);a2[w]=pool.pop(j)
        v=stat(a2,False);dist['constrained'][v]=dist['constrained'].get(v,0)+1;hits['constrained']+=v>=real
    key=f"{u}_{time.strftime('%Y-%m-%d %H:%M:%S',time.gmtime(end))}"
    print(key,'real',real,'stored p',round(stored[key]['p'],4),'recomputed frozen p',round((hits['frozen']+1)/(draws+1),4),'strict p',round((hits['strict']+1)/(draws+1),4),'feasible-shuffle p',round((hits['constrained']+1)/(draws+1),4),'impossible date share',round(impossible/(draws*len(known)),3),flush=True)
    print('   null constrained',dict(sorted(dist['constrained'].items())),flush=True)
for u,end in(('M',R.D2),('M',R.T_FIN),('X',R.D2),('X',R.T_FIN)):
    run(u,end)
