"""Audit, offline: base rate, the 33 missing wallets, E4 and the other published statistics, recomputed from the study's own outputs. Reads only."""
import json,math,random
from collections import Counter,defaultdict
from math import comb
I='/Users/benjamindacunha/Projects/PolySentinel-investigation/'
def fisher_gt(a,n1,c,n2):
    """P(at least a of the K positives fall in group 1)."""
    K=a+c;N=n1+n2
    return sum(comb(n1,k)*comb(n2,K-k) for k in range(a,min(K,n1)+1))/comb(N,K)
def cp_upper(k,n,conf=.975):
    lo,hi=0.0,1.0
    for _ in range(80):
        m=(lo+hi)/2
        if sum(comb(n,i)*m**i*(1-m)**(n-i) for i in range(k+1))>1-conf: lo=m
        else: hi=m
    return hi
raw=[json.loads(l) for l in open(I+'controls/funding_baseline.jsonl')]
det=[json.loads(l) for l in open(I+'controls/funding_baseline_detail.jsonl')]
print('raw rows',len(raw),Counter((r['group'],r.get('state')) for r in raw))
print('detail rows',len(det),Counter(r['group'] for r in det),'errors',sum('error' in r for r in det))
print('fields',sorted(raw[0]))
meta=json.load(open(I+'controls/funding_baseline_meta.json'));print(meta)
print('\nfirst-deposit choice, named:')
cases={}
import glob,os
for f in glob.glob(I+'cases/*.json'):
    c=json.load(open(f));cases[c['address'].lower()]=c
for r in det:
    if r['group']=='named':
        c=cases[r['wallet'].lower()];first=min(c['deposits'],key=lambda d:d['at'])
        print(' ',c['slug'],'first deposit used',first['tx']==r['deposit_tx'],r['origin_chain'],str(r.get('immediate_source'))[:10],r.get('immediate_kind'),'stops',len(r.get('stops') or []),[ (h['source'][:10],h.get('label')) for h in r['hops']][:4])
print('\ncomparators, origin and whether the origin could be read:')
tab=Counter()
for r in det:
    labs=[h.get('label') for h in r.get('hops',[]) if h.get('label')]
    tab[(r['group'],r.get('origin_chain'),bool(r.get('stops')),'kucoin' if any('KuCoin' in str(l) for l in labs) else '')]+=1
for k,v in sorted(tab.items(),key=str):print(' ',k,v)
print('\nstops among comparators:')
st=Counter()
for r in det:
    for s in r.get('stops') or []:
        st[(r['group']=='named',s.get('state'),str(s.get('basis'))[:60])]+=1
for k,v in st.most_common():print(' ',k,v)
print('\nwhat each comparator without Relay shows:')
for r in det:
    if r['group']!='named' and not r.get('origin_chain'):
        print(' ',r['group'],r['wallet'][:10],r.get('immediate_kind'),str(r.get('immediate_source'))[:10],[s.get('state') for s in r.get('stops') or []],r.get('error','')[:50],len(r.get('hops',[])))
def has(r,fn):return fn(r)
ku=lambda r:any('KuCoin' in str(h.get('label')) for h in r.get('hops',[]))
sol=lambda r:r.get('origin_chain')==792703809
c8=lambda r:str(r.get('immediate_source')).lower().startswith('0xc8a6871d')
rel=lambda r:bool(r.get('relay_user'))
groups=defaultdict(list)
for r in det:groups[r['group']].append(r)
print('\ngroup sizes',{k:len(v) for k,v in groups.items()})
comp=[r for r in det if r['group']!='named']
named=groups['named']
for name,fn in (('kucoin',ku),('solana',sol),('c8a6',c8),('relay',rel)):
    a=sum(map(fn,named));c=sum(map(fn,comp));print(name,f'{a}/{len(named)} vs {c}/{len(comp)}',{g:sum(map(fn,v)) for g,v in groups.items()},'p',round(fisher_gt(a,len(named),c,len(comp)),4))
fresh=[g for g in groups if 'fra' in g][0]
print('\nnamed vs fresh only (age-matched):')
for name,fn in (('kucoin',ku),('solana',sol),('c8a6',c8),('relay',rel)):
    a=sum(map(fn,named));c=sum(map(fn,groups[fresh]));print(' ',name,f'{a}/11 vs {c}/{len(groups[fresh])}','p',round(fisher_gt(a,11,c,len(groups[fresh])),4))
print('\nconditional on a Solana origin: KuCoin among Solana origins, named',sum(ku(r) for r in named if sol(r)),'/',sum(sol(r) for r in named),'comparators',sum(ku(r) for r in comp if sol(r)),'/',sum(sol(r) for r in comp))
print('Bonferroni, 5 traits: kucoin',round(.0164*5,3),'c8a6',round(fisher_gt(5,11,5,50)*5,3))
print('upper 95% two-sided on rates: fresh kucoin 0/12',round(cp_upper(0,12),3),'all comparators 1/50',round(cp_upper(1,50),3),'named 3/11',round(cp_upper(3,11),3))
print('\n33 missing wallets (3 same token, 2 opposite, 28 fresh): p for KuCoin as a function of positives among them')
for k in range(0,9):
    print(' ',k,round(fisher_gt(3,11,1+k,83),4),' fresh-only with k of 28:',round(fisher_gt(3,11,0+k,40),4))
print('expected positives among the 28 fresh if rate equals named 27%:',round(28*3/11,1),'if 2% (1/50):',round(28*.02,2))
print('missing depends on address order? read wallets are a prefix of the sorted group:')
for g in ('meme_token','token_oppose','fraiches_recensement','non_surlignes'):
    rr=[r for r in raw if r['group']==g]
    print(' ',g,len(rr),Counter(r.get('state') for r in rr))
