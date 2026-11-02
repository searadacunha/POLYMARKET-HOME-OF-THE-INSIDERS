"""Audit: base rate with the truncated readings set aside, pair view on real tokens, and a positive control for the Polygon log filter. Reads, plus two public lookups."""
import glob,gzip,itertools,json,os,time
from collections import Counter,defaultdict
from math import comb
import httpx
I='/Users/benjamindacunha/Projects/PolySentinel-investigation/';OUT='/Users/benjamindacunha/Projects/PolySentinel-audit-20261102/out/'
def f(a,n1,c,n2):
    K=a+c;return sum(comb(n1,k)*comb(n2,K-k) for k in range(a,min(K,n1)+1))/comb(n1+n2,K)
det=[json.loads(l) for l in open(I+'controls/funding_baseline_detail.jsonl')]
e6=json.load(open(I+'collective/derived/B_E6.json'))['per_wallet']
comp=[r for r in det if r['group']!='named'];named=[r for r in det if r['group']=='named']
lag=[];trunc=[]
for r in comp:
    p=e6.get(r['wallet'])
    if not p:continue
    ffb=p.get('first_family_buy')
    gap=(ffb-r['at'])/86400 if ffb and r['at'] else None
    lag.append(gap)
    if p.get('complete') is False:trunc.append(r['wallet'])
print('comparators with E6 history',len(lag),'deposit more than 30 days before first family buy',sum(1 for x in lag if x is not None and x>30),'history cut',len(trunc))
print(' example',[(r['wallet'][:8],round(r['usd'],2),time.strftime('%Y-%m',time.gmtime(r['at']))) for r in comp if e6.get(r['wallet'],{}).get('first_family_buy') and (e6[r['wallet']]['first_family_buy']-r['at'])/86400>300][:6])
noread=[r for r in comp if not r.get('immediate_source')]
print('no wrap read',len(noread),'no origin',sum(1 for r in comp if not r.get('origin_chain')))
readable=[r for r in comp if r.get('origin_chain')]
cut=set(trunc)
clean=[r for r in readable if r['wallet'] not in cut]
ku=lambda r:any('KuCoin' in str(h.get('label')) for h in r.get('hops',[]))
so=lambda r:r.get('origin_chain')==792703809
c8=lambda r:str(r.get('immediate_source')).lower().startswith('0xc8a6871d')
for name,fn in(('KuCoin',ku),('Solana',so),('c8a6',c8)):
    a=sum(map(fn,named))
    print(name,f'named {a}/11','| published',f'{sum(map(fn,comp))}/50','p',round(f(a,11,sum(map(fn,comp)),50),4),'| origin read',f'{sum(map(fn,readable))}/{len(readable)}','p',round(f(a,11,sum(map(fn,readable)),len(readable)),4),'| also full history',f'{sum(map(fn,clean))}/{len(clean)}','p',round(f(a,11,sum(map(fn,clean)),len(clean)),4))
fresh=[r for r in readable if r['group']=='fraiches_recensement']
print('fresh with origin read',len(fresh))
print('\n=== pair view on real tokens, buys of 100 $ or more')
act=json.load(gzip.open(OUT+'a3_named_activity.json.gz','rt'))
cases={os.path.basename(p)[:-5]:json.load(open(p)) for p in sorted(glob.glob(I+'cases/*.json'))}
buys={s:defaultdict(list) for s in cases}
print('asset present',sum(1 for r in act['thin'] if r.get('asset')),'of',len(act['thin']))
for s,rows in act.items():
    for r in rows:
        if r['type']=='TRADE' and r.get('side')=='BUY' and float(r.get('usdc_size') or 0)>=100:buys[s][(r.get('title'),r.get('outcome'))].append(r['timestamp'])
main={s:max(c['withdrawals'],key=lambda w:w['usd'])['at'] for s,c in cases.items()}
dep={s:[d['at'] for d in c['deposits']] for s,c in cases.items()}
mg=lambda xs,ys:min(abs(x-y) for x in xs for y in ys)
rows=[]
for a,b in itertools.combinations(sorted(cases),2):
    common=set(buys[a])&set(buys[b])
    n5=sum(1 for t in common for x in buys[a][t] for y in buys[b][t] if abs(x-y)<=300)
    rows.append(dict(a=a,b=b,withdraw_gap_min=round(abs(main[a]-main[b])/60,1),deposit_gap_min=round(mg(dep[a],dep[b])/60,1),common_tokens=len(common),near_buys_5min=n5))
for r in sorted(rows,key=lambda r:r['withdraw_gap_min'])[:6]:print(' ',r)
print(' most near buys:')
for r in sorted(rows,key=lambda r:-r['near_buys_5min'])[:6]:print(' ',r)
json.dump(rows,open(OUT+'a19_pairs.json','w'))
print('\n=== Kane buys by named wallets per day, full activity')
kane=defaultdict(lambda:defaultdict(float))
for s,v in act.items():
    for r in v:
        if r['type']=='TRADE' and r.get('side')=='BUY' and 'Harry Kane win' in (r.get('title') or '') and r.get('outcome')=='Yes':
            kane[time.strftime('%m-%d',time.gmtime(r['timestamp']))][s]+=float(r['usdc_size'])
for d in sorted(kane):
    if d<='10-13':print(' ',d,{k:round(v) for k,v in kane[d].items()})
print('\n=== positive control, Polygon ERC-20 OR-filter')
http=httpx.Client(timeout=30,trust_env=False)
rel=[json.loads(l) for l in open(I+'graphs/relations.jsonl')]
c=[r for r in rel if r['chain']==137 and r['tx'] and str(r['token']).startswith('USDC') and r['token']!='USDC.e→pUSD' and (r['source'] or '').startswith('0x') and (r['target'] or '').startswith('0x') and r['log_index'] is not None]
print('candidates',len(c))
pad=lambda a:'0x'+'0'*24+a[2:].lower()
T='0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
wallets=[x['address'] for x in cases.values()]
for r in c[:3]:
    rc=http.post('https://polygon-bor-rpc.publicnode.com',json=dict(jsonrpc='2.0',id=1,method='eth_getTransactionReceipt',params=[r['tx']])).json()['result']
    b=rc['blockNumber']
    logs=http.post('https://polygon-bor-rpc.publicnode.com',json=dict(jsonrpc='2.0',id=1,method='eth_getLogs',params=[dict(fromBlock=hex(int(b,16)-4000),toBlock=hex(int(b,16)+4000),topics=[T,[pad(r['source'])]+[pad(w) for w in wallets[:5]],[pad(r['target'])]+[pad(w) for w in wallets[5:]]])])).json()
    res=logs.get('result')
    print(' ',r['tx'][:14],'range 8000 blocks, returned',None if res is None else len(res),'found',any(l['transactionHash']==r['tx'] for l in (res or [])),str(logs.get('error'))[:100])
