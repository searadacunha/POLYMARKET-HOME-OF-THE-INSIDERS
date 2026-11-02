"""Exploratory. Which exact rank combinations did wallets hold, among all taker buyers, and was the later true one unusual? Also checks the screenshot's note on kraben006."""
import gzip,json,re,sys,time,itertools
from collections import Counter,defaultdict
from pathlib import Path
sys.path.insert(0,'collective/code');sys.path.insert(0,'tools')
import rows as R, identities as I
T_FIN=R.T_FIN;T_END=1793044800
U=lambda t:time.strftime('%m-%d %H:%M',time.gmtime(t))
cat=R.catalog()
PAT=re.compile(r"Will (.+) finish (2nd|3rd|4th|5th) in the 2026 Ballon d'Or")
rank={}
for tok,(ev,q,out) in cat.items():
    m=PAT.search(q or '')
    if m and out=='Yes' and ev in('1218178','1218179','1225367','1225368'): rank[tok]=(m.group(2),m.group(1))
print('rank Yes tokens',len(rank),Counter(v[0] for v in rank.values()))
rows=[]
with gzip.open(R.S/'ballon_2026_20261030/data/trades_minimal.jsonl.gz','rt') as f:
    for l in f:
        r=json.loads(l)
        if r['token_id'] in rank and r['timestamp']<T_END: rows.append((r['wallet'],r['token_id'],r['side'],r['size'],r['price'],r['timestamp']))
print('rank rows',len(rows),'wallets',len({r[0] for r in rows}))
named={v['address']:k for k,v in I.IDS.items()}
out={}
for name,end in (('article',T_FIN),('ceremonie',T_END)):
    pos=defaultdict(lambda:defaultdict(float));last={}
    for w,t,side,size,price,ts in sorted(rows,key=lambda x:x[5]):
        if ts>=end: continue
        last[t]=price
        pos[w][t]+=(size*price) if side=='BUY' else -(size*price)
    holds={w:{rank[t] for t,x in d.items() if x>=100} for w,d in pos.items()}
    holds={w:h for w,h in holds.items() if h}
    TRUE={('2nd','Kylian Mbappé'),('3rd','Lamine Yamal'),('4th','Rodri'),('5th','Lionel Messi')}
    combos=Counter()
    pair_all=Counter()
    for w,h in holds.items():
        byr=defaultdict(list)
        for r,p in h: byr[r].append(p)
        for n in (2,3,4):
            for ranks in itertools.combinations(sorted(byr),n):
                for players in itertools.product(*[byr[r] for r in ranks]):
                    if len(set(players))==n: combos[(n,)+tuple(zip(ranks,players))]+=1
    res={}
    for n in (2,3,4):
        top=[(k[1:],v) for k,v in combos.most_common() if k[0]==n][:8]
        def price(c):
            p=1
            for r,pl in c:
                t=[tok for tok,v in rank.items() if v==(r,pl)]
                p*=last.get(t[0],0) if t else 0
            return round(p,5)
        total=sum(v for k,v in combos.items() if k[0]==n)
        true=[(k[1:],v) for k,v in combos.items() if k[0]==n and set(k[1:])<=TRUE]
        res[n]=dict(distinct=sum(1 for k in combos if k[0]==n),holdings=total,top=[(c,v,price(c)) for c,v in top],true_subsets=sorted(true,key=lambda x:-x[1])[:6])
        print(name,'n=',n,'distinct',res[n]['distinct'],'top',[(' '.join(f'{p.split()[-1]}{r}' for r,p in c),v,price(c)) for c,v in top[:6]])
    full=[w for w,h in holds.items() if TRUE<=h]
    three=[w for w,h in holds.items() if len(TRUE&h)>=3]
    print(name,'wallets with rank position',len(holds),'all 4 true',len(full),[named.get(w,w[:8]) for w in full],'at least 3 true',len(three),[named.get(w,w[:8]) for w in three])
    # What the rank wallets that hold a full 4-rank book of a different order look like, the placebo for "exact combination".
    four=Counter()
    for w,h in holds.items():
        byr=defaultdict(list)
        for r,p in h: byr[r].append(p)
        if len(byr)==4: four[w]=1
    res['wallets_rank_any']=len(holds);res['all_four_true']=[named.get(w,w) for w in full];res['three_true']=[named.get(w,w) for w in three];res['wallets_all_four_ranks']=len(four)
    out[name]=res
Path('collective/exploratoire/rank_combos.json').write_text(json.dumps(out,ensure_ascii=False,default=str))
# Screenshot note: kraben006 sold Kane to take Yamal 3rd.
rows=[json.loads(l) for l in gzip.open('evidence/activity/kraben006.jsonl.gz','rt')]
for r in rows:
    if r['type']=='TRADE' and 1792300000<r['timestamp']<T_FIN and (('Kane' in (r.get('title') or '') and r['side']=='SELL') or ('Yamal finish 3rd' in (r.get('title') or ''))):
        print('kraben',U(r['timestamp']),r['side'],round(float(r['usdc_size']),2),(r['title'])[:44],r['outcome'])
