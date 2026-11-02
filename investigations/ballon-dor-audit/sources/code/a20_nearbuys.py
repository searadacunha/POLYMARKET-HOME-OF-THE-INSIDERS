"""Audit, exploratory: near-simultaneous buys per pair, against the same wallet's buys shifted in time, which keeps each wallet's rhythm. All 55 pairs, so a Bonferroni bar applies. Plus the Polygon filter control. Reads, plus public lookups."""
import glob,gzip,itertools,json,os,random,bisect
from collections import defaultdict
import httpx
I='/Users/benjamindacunha/Projects/PolySentinel-investigation/';OUT='/Users/benjamindacunha/Projects/PolySentinel-audit-20261102/out/'
act=json.load(gzip.open(OUT+'a3_named_activity.json.gz','rt'))
buys={s:defaultdict(list) for s in act}
for s,rows in act.items():
    for r in rows:
        if r['type']=='TRADE' and r.get('side')=='BUY' and float(r.get('usdc_size') or 0)>=100:
            buys[s][(r.get('title'),r.get('outcome'))].append(r['timestamp'])
    for k in buys[s]:buys[s][k].sort()
def dedupe(ts,g=60):
    out=[]
    for t in ts:
        if not out or t-out[-1]>g:out.append(t)
    return out
B={s:{k:dedupe(v) for k,v in d.items()} for s,d in buys.items()}
def near(a,b,shift=0,w=300):
    n=0
    for t in set(B[a])&set(B[b]):
        ys=B[b][t]
        for x in B[a][t]:
            i=bisect.bisect_left(ys,x-w-shift)
            if i<len(ys) and ys[i]+shift<=x+w:n+=1
    return n
rng=random.Random(20261102)
res=[]
for a,b in itertools.combinations(sorted(B),2):
    obs=near(a,b)
    if not obs:continue
    draws=[rng.choice((-1,1))*rng.uniform(3600,7*86400) for _ in range(5000)]
    hits=sum(near(a,b,s)>=obs for s in draws)
    res.append((round((hits+1)/5001,5),a,b,obs,len(set(B[a])&set(B[b]))))
for r in sorted(res)[:12]:print(r)
print('pairs with a near buy',len(res),'of 55; Bonferroni bar 0.05/55 =',round(.05/55,5))
json.dump(res,open(OUT+'a20_nearbuys.json','w'))
print('\nkraben and brace shared tokens')
for t in set(B['kraben006'])&set(B['brace227']):
    print(' ',t,len(B['kraben006'][t]),len(B['brace227'][t]))
    xs=[(x,y) for x in B['kraben006'][t] for y in B['brace227'][t] if abs(x-y)<=300]
    import time
    print('   ',[(time.strftime('%m-%d %H:%M',time.gmtime(x)),y-x) for x,y in xs][:10])
print('\nPolygon filter positive control, with the address list direct_links.py uses')
http=httpx.Client(timeout=30,trust_env=False)
rel=[json.loads(l) for l in open(I+'graphs/relations.jsonl')]
cases={os.path.basename(p)[:-5]:json.load(open(p)) for p in glob.glob(I+'cases/*.json')}
c=[r for r in rel if r['chain']==137 and r['tx'] and str(r['token']).startswith('USDC') and r['token']!='USDC.e→pUSD' and (r['source'] or '').startswith('0x') and (r['target'] or '').startswith('0x') and r['log_index'] is not None]
pad=lambda a:'0x'+'0'*24+a[2:].lower()
T='0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
tokens=['0x2791bca1f2de4661ed88a30c99a7a9449aa84174','0x3c499c542cef5e3811e1192ce70d8cc03d5c3359','0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb','0xc2132d05d31c914a87c6611c10748aeb04b58e8f']
wallets=[x['address'] for x in cases.values()]
for r in c[:3]:
    rc=http.post('https://polygon-bor-rpc.publicnode.com',json=dict(jsonrpc='2.0',id=1,method='eth_getTransactionReceipt',params=[r['tx']])).json()['result']
    b=int(rc['blockNumber'],16)
    q=dict(address=tokens,fromBlock=hex(b-4000),toBlock=hex(b+4000),topics=[T,[pad(r['source'])]+[pad(w) for w in wallets],[pad(r['target'])]+[pad(w) for w in wallets]])
    logs=http.post('https://polygon-bor-rpc.publicnode.com',json=dict(jsonrpc='2.0',id=1,method='eth_getLogs',params=[q])).json()
    res2=logs.get('result')
    print(' ',r['tx'][:14],'returned',None if res2 is None else len(res2),'found',any(l['transactionHash']==r['tx'] for l in (res2 or [])),str(logs.get('error'))[:100])
