"""Audit of E4 v2, on the study's own code, read-only: reproduction under another hash seed, and whether named wallets could appear at all."""
import glob,hashlib,json,os,sys,time
C='/Users/benjamindacunha/Projects/PolySentinel-investigation/'
sys.path.insert(0,C+'collective/code')
sys.dont_write_bytecode=True
import rows as R
from ana_overlap_core_v2 import run,matrix,pair_scores,curveball
import random
from collections import defaultdict,Counter
named={json.load(open(f))['address'].lower():os.path.basename(f)[:-5] for f in glob.glob(C+'cases/*.json')}
rows=[r for r in R.family() if r[0]=='M']
print('family M rows',len(rows),'PYTHONHASHSEED',os.environ.get('PYTHONHASHSEED'))
stored=json.load(open(C+'collective/derived/A_E4_v2.json'))
out={}
for name,end in (('D2',R.D2),('T_FIN',R.T_FIN)):
    t=time.time()
    seed=20261101
    res=run(rows,end,seed=seed)
    same=json.dumps(res,sort_keys=True)==json.dumps(stored[f'{name}_{seed}'],sort_keys=True)
    print(name,'identical to the stored output under this hash seed:',same,'pairs above',res['pairs_above_null_max'],round(time.time()-t,1),'s')
    m=matrix(rows,end)
    # who is in the universe, and why not
    spent=defaultdict(lambda:defaultdict(float))
    for r in rows:
        if r[4]=='BUY' and r[8]<=end: spent[r[3]][r[2]]+=r[5]
    print(' named in the universe:',sorted(named[w] for w in m if w in named),len([w for w in m if w in named]),'of 11; universe',len(m))
    for w,s in sorted(named.items(),key=lambda x:x[1]):
        if w not in m:
            tk=spent.get(w,{})
            print('   out:',s,'taker usd',round(sum(tk.values()),2),'tokens>=100',sum(1 for x in tk.values() if x>=100),'tokens',len(tk))
    only_plan={w for w,t in spent.items() if sum(t.values())>=500}
    print(' wallets >=500$ as the plan says',len(only_plan),'kept by the code',len(m),'dropped by the 2-token filter',len(only_plan)-len(m),'of which named',[named[w] for w in only_plan-set(m) if w in named])
    real=pair_scores(m)
    thr=res['null_max_by_shared']
    rows_named=[]
    by_count=defaultdict(list)
    for p,v in real.items(): by_count[v[0]].append(v[1])
    for p,v in real.items():
        if p[0] in named or p[1] in named:
            pct=sum(x<=v[1] for x in by_count[v[0]])/len(by_count[v[0]])
            rows_named.append((named.get(p[0],p[0][:8]),named.get(p[1],p[1][:8]),v[0],round(v[1],3),thr.get(str(v[0])),round(pct,4),len(by_count[v[0]]),p[0] in named and p[1] in named))
    both=[x for x in rows_named if x[-1]]
    print(' pairs with a named wallet',len(rows_named),'both named',len(both),'above threshold',sum(1 for x in rows_named if x[4] is None or x[3]>x[4]))
    print(' both-named pairs, sorted by margin (a,b,shared,score,null max,pct within same shared count,n at that count):')
    for x in sorted(both,key=lambda x:-(x[3]/(x[4] or 1)))[:14]: print('   ',x[:7],'ratio',round(x[3]/(x[4] or 1),3))
    print(' any-named top by percentile:')
    for x in sorted(rows_named,key=lambda x:-x[5])[:8]: print('   ',x[:7])
    # how far is the bar: top-pair margin among the non-named
    tops=[(t['shared'],t['score'],thr.get(str(t['shared']))) for t in res['top']][:6]
    print(' top pairs (shared,score,null max)',tops)
    print(' threshold by shared count',{k:round(v,2) for k,v in list(thr.items())[:8]})
    # power: a planted pair sharing k tokens among the rarest held, score vs null max
    df=Counter(t for ts in m.values() for t in ts)
    n=len(m)
    import math
    idf=sorted((math.log(n/c) for c in df.values()),reverse=True)
    med=sorted(math.log(n/c) for c in df.values())[len(df)//2]
    print(' shared k: score if k median-rarity tokens / if k rarest / null max at k')
    for k in (2,3,4,5,6,8):
        print('   ',k,round(k*med,2),round(sum(idf[:k]),2),thr.get(str(k)))
    # is Mbappé/Yamal itself common?
    ts=[t for t,c in df.most_common(5)];print(' most common tokens counts',[df[t] for t in ts])
    out[name]=dict(both=both[:60],named=rows_named[:0])
json.dump(out,open(sys.argv[1],'w'),default=str)
