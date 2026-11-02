import json,collections,random,datetime as dt
from common2 import es
OFF={'0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48','0xdac17f958d2ee523a2206206994597c13d831ec7'}
START=int(dt.datetime(2024,5,21,tzinfo=dt.UTC).timestamp()); EARLY=int(dt.datetime(2024,6,20,tzinfo=dt.UTC).timestamp())
pay=collections.defaultdict(list)
for a in ('0xb93e3d70ac9cacd51764f09ae0d01b905dc291e1','0x26c50e673fca05131c9b9f23d213b977d9a34c77'):
    for x in json.load(open(f'deep_{a[:10]}_1_tokentx.json')):
        if x['from'].lower()==a and x['contractAddress'].lower() in OFF and int(x['value'])>=10**6: pay[x['to'].lower()].append(int(x['timeStamp']))
early=[b for b,l in pay.items() if min(l)<EARLY and len(l)>=3]
random.seed(11); smp=random.sample(early,min(160,len(early)))
senders=collections.Counter(); per={}; nprior=0
for b in smp:
    r=es(1,module='account',action='tokentx',address=b,page=1,offset=300,sort='asc') or []
    prior=[x for x in r if x['to'].lower()==b and x['contractAddress'].lower() in OFF and int(x['value'])>=10**6 and int(x['timeStamp'])<START]
    s=set(x['from'].lower() for x in prior)
    if prior: nprior+=1
    for q in s: senders[q]+=1
    per[b]=sorted(s)
json.dump({'n_early':len(early),'sample':len(smp),'with_prior':nprior,'senders':senders.most_common(60),'per':per},open('p5_predecessor.json','w'))
print('early repeat beneficiaries',len(early),'sample',len(smp),'with USDT/USDC received before 21/05/2024:',nprior)
for s,n in senders.most_common(25): print(' ',s,n)
