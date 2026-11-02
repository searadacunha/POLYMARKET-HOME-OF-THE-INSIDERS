"""Audit: everything that touches the two unclassified addresses, the hubs' public identity, and a multi-signal view of each pair, which the report did not build. Reads, plus a few public lookups."""
import glob,itertools,json,os,sys,time,gzip
from collections import defaultdict,Counter
import httpx
I='/Users/benjamindacunha/Projects/PolySentinel-investigation/';OUT='/Users/benjamindacunha/Projects/PolySentinel-audit-20261102/out/'
cases={os.path.basename(f)[:-5]:json.load(open(f)) for f in sorted(glob.glob(I+'cases/*.json'))}
http=httpx.Client(timeout=30,trust_env=False,headers={'User-Agent':'read-only audit'})
print('=== origin_submitter and other addresses in the hop records')
ADDR=defaultdict(lambda:defaultdict(list))
def walk(o,case,path=''):
    if isinstance(o,dict):
        for k,v in o.items():
            if k in('chain_relations','relations','rows'):continue
            walk(v,case,path+'/'+k)
    elif isinstance(o,list):
        for v in o:walk(v,case,path)
    elif isinstance(o,str) and o.startswith('0x') and len(o)==42:
        ADDR[o.lower()][case].append(path)
for s,c in cases.items():
    walk({k:c.get(k) for k in('funding_chain','funding_trace','exit_chain','exit_follow','owner_upstream','upstream','recipients','stops','chain_stops','exits')},s)
rel=[json.loads(l) for l in open(I+'graphs/relations.jsonl')]
inrel={(r[x] or '').lower() for r in rel for x in('source','target')}
print('addresses in two or more cases anywhere in the case files:')
extra=[]
for a,v in sorted(ADDR.items(),key=lambda x:-len(x[1])):
    if len(v)>1:
        roles=sorted({p.split('/')[-1] for ps in v.values() for p in ps})
        print(' ',a,sorted(v),'in relations' if a in inrel else 'NOT IN RELATIONS',roles[:6])
        if a not in inrel:extra.append(a)
print('\n=== public identity of hubs and those addresses')
hubs=['0xc8a6871d4ec4dae64f605db0f8a0b3d9ef928d64','0xee7ae85f2fe2239e27d9c1e23fffe168d63b4055','0x0ce9bdf38714143043b1d36de9bd90f7335bf06d','0xc1d13492285eb664951e201bf7c80c7c6318a1b5']+[n['address'] for n in json.load(open(I+'graphs/links_classified.json'))['nodes'] if n['address'].lower().startswith('0x58f2')]+extra
for a in hubs:
    row={}
    for net,base in(('eth','https://eth.blockscout.com'),('polygon','https://polygon.blockscout.com'),('arbitrum','https://arbitrum.blockscout.com')):
        try:
            r=http.get(f'{base}/api/v2/addresses/{a}')
            if r.status_code==200:
                d=r.json();cnt=http.get(f'{base}/api/v2/addresses/{a}/counters');cn=cnt.json() if cnt.status_code==200 else {}
                row[net]=dict(contract=d.get('is_contract'),name=d.get('name'),verified=d.get('is_verified'),impl=[x.get('name') for x in d.get('implementations') or []],tags=[t.get('display_name') for t in ((d.get('public_tags') or [])+(d.get('metadata') or {}).get('tags',[]))][:4],txs=cn.get('transactions_count'),transfers=cn.get('token_transfers_count'))
        except Exception as e:row[net]=str(e)[:60]
        time.sleep(.25)
    print(' ',a,json.dumps(row,ensure_ascii=False)[:520],flush=True)
print('\n=== open positions behind two settled or closed accounts')
for s in('0xdd97e6','zoomman17'):
    r=http.get('https://data-api.polymarket.com/positions',params=dict(user=cases[s]['address'],limit=50))
    rows=r.json() if r.status_code==200 else []
    print(' ',s,r.status_code,[(x.get('title','')[:38],x.get('outcome'),round(float(x.get('size',0)),2),x.get('curPrice'),round(float(x.get('currentValue',0)),2),round(float(x.get('initialValue',0)),2)) for x in rows][:6],flush=True)
print('\n=== positive control for the direct-transfer filter on Polygon')
def pad(a):return '0x'+'0'*24+a[2:].lower()
ids=[cases[s]['address'] for s in cases]
known=[r for r in rel if r['chain']==137 and r['tx'] and r['log_index'] is not None and (r['target'] or '').lower().startswith('0xc8a6') and r['at']]
if known:
    r0=known[0];rc=http.post('https://polygon-bor-rpc.publicnode.com',json=dict(jsonrpc='2.0',id=1,method='eth_getTransactionReceipt',params=[r0['tx']])).json()['result']
    b=rc['blockNumber']
    tok='0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
    src,dst=pad(r0['source']),pad(r0['target'])
    logs=http.post('https://polygon-bor-rpc.publicnode.com',json=dict(jsonrpc='2.0',id=1,method='eth_getLogs',params=[dict(fromBlock=b,toBlock=b,topics=[tok,[src,pad(ids[0])],[dst,pad(ids[1])]])])).json().get('result')
    print(' known transfer',r0['source'][:10],'->',r0['target'][:10],r0['tx'][:14],'found by an OR-filter on publicnode:',any(l['transactionHash']==r0['tx'] for l in (logs or [])),len(logs or []))
print('\n=== pair matrix')
act=json.load(gzip.open(OUT+'a3_named_activity.json.gz','rt')) if os.path.exists(OUT+'a3_named_activity.json.gz') else {}
shared=defaultdict(list)
nodes=json.load(open(I+'graphs/links_classified.json'))['nodes']
for n in nodes:
    for a,b in itertools.combinations(sorted(n['cases']),2):shared[(a,b)].append(n['address'][:6])
for a,v in ADDR.items():
    if a not in inrel and len(v)>1:
        for x,y in itertools.combinations(sorted(v),2):shared[(x,y)].append(a[:6]+'*')
main={s:max(c['withdrawals'],key=lambda w:w['usd'])['at'] for s,c in cases.items()}
dep={s:[d['at'] for d in c['deposits']] for s,c in cases.items()}
def mingap(xs,ys):return min(abs(x-y) for x in xs for y in ys)
tok={s:{(r.get('title'),r.get('outcome')):r['timestamp'] for r in act.get(s,[]) if r['type']=='TRADE' and r.get('side')=='BUY'} for s in cases}
buys={s:defaultdict(list) for s in cases}
for s in cases:
    for r in act.get(s,[]):
        if r['type']=='TRADE' and r.get('side')=='BUY' and float(r.get('usdc_size') or 0)>=100:buys[s][r['asset']].append(r['timestamp'])
rows=[]
for a,b in itertools.combinations(sorted(cases),2):
    common=set(buys[a])&set(buys[b])
    near5=min((mingap(buys[a][t],buys[b][t]) for t in common),default=None)
    n5=sum(1 for t in common for x in buys[a][t] for y in buys[b][t] if abs(x-y)<=300)
    wd=abs(main[a]-main[b]);dg=mingap(dep[a],dep[b])
    keya=(cases[a]['wallet'].get('owners') or [''])[0];keyb=(cases[b]['wallet'].get('owners') or [''])[0]
    score=(len(shared[(a,b)])>0)+(wd<=600)+(dg<=900)+(n5>=2)
    rows.append((score,a,b,shared[(a,b)],round(wd/60,1),round(dg/60,1),len(common),n5))
for r in sorted(rows,key=lambda r:(-r[0],r[4]))[:14]:print(' ',r)
json.dump(rows,open(OUT+'a15_pairs.json','w'),default=str)
print(' pairs by score',Counter(r[0] for r in rows))
