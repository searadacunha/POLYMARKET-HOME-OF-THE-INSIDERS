"""Audit: all 25 withdrawals and 46 deposits re-read from public nodes, independently of the investigation's cache and code. Public reads only."""
import glob,json,os,sys,time
sys.path.insert(0,'/Users/benjamindacunha/Projects/PolySentinel-harness')
os.environ['SIGNAL_ENGINE_STATE']='/Users/benjamindacunha/Projects/PolySentinel-audit-20261102/out/es'
import httpx
from signal_engine.fund_flow.client import Client
I='/Users/benjamindacunha/Projects/PolySentinel-investigation/'
OUT='/Users/benjamindacunha/Projects/PolySentinel-audit-20261102/out/'
cases={os.path.basename(f)[:-5]:json.load(open(f)) for f in sorted(glob.glob(I+'cases/*.json'))}
PUSD,USDCE='0xc011a7e12a19f7b1f670d46f03b03f3a53e3e1a2','0x2791bca1f2de4661ed88a30c99a7a9449aa84174'
sys.path.insert(0,I+'tools')
TRANSFER='0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
Z='0x'+'0'*40
RELAY='0x4cd00e387622c35bddb9b4c962c136462338bc31'
SOLVER='0xf70da97812cb96acdf810712aa562db8dfa3dbef'
c=Client(rpc_limit=900,http_limit=0,pause_s=.2,ledger=OUT+'rpc_requests.jsonl')
SOL=('https://solana-rpc.publicnode.com','https://api.mainnet-beta.solana.com')
def sol(method,params):
    for attempt in range(6):
        for url in SOL:
            try:
                r=httpx.post(url,json=dict(jsonrpc='2.0',id=1,method=method,params=params),timeout=30,trust_env=False)
                if r.status_code==200:
                    b=r.json()
                    if b.get('result') is not None: return b['result']
            except Exception: pass
            time.sleep(1+attempt)
    return None
def moves(rc):
    out=[]
    for l in rc['logs']:
        t=l['topics']
        if t and t[0]==TRANSFER and len(t)==3 and l['data']!='0x':
            out.append(dict(i=int(l['logIndex'],16),token=l['address'].lower(),src='0x'+t[1][-40:],dst='0x'+t[2][-40:],raw=int(l['data'],16)))
    return out
pusd=None
res=dict(withdrawals=[],deposits=[])
for s,case in cases.items():
    w=case['address'].lower()
    for wd in case['withdrawals']:
        rc=c.receipt(wd['tx'],137); m=moves(rc)
        want=round(wd['usd']*1e6)
        tokens={x['token'] for x in m}
        burns=[x for x in m if x['dst']==Z and abs(x['raw']-want)<=1]  # the wallet may send pUSD through a contract before the burn
        row_all=[(x['src'][:10],x['dst'][:10],x['raw'],x['token'][:8]) for x in m]
        out_wallet=[x for x in m if x['src']==w and x['dst']!=Z]
        exact=[x for x in m if abs(x['raw']-want)<=1]
        rel=[r for r in case['chain_relations'] if (r.get('payout_tx') or '').lower()==wd['tx'].lower() or (r.get('tx') or '').lower()==wd['tx'].lower()][0]
        row=dict(case=s,tx=wd['tx'],usd=wd['usd'],status=int(rc['status'],16),burn_raw=[x['raw'] for x in burns],burn_token=sorted({x['token'] for x in burns}),out_of_wallet=[(x['dst'][:10],x['raw'],x['token'][:8]) for x in out_wallet],to_relay=[x['raw'] for x in m if x['dst']==RELAY],exact_logs=len(exact),category=rel['category'],recipient=rel['target'],out_chain=rel['chain'])
        row['burn_equals_api']=len(burns)==1
        row['all_moves']=row_all
        row['n_burns_any']=sum(1 for x in m if x['dst']==Z)
        oid=(rel.get('order_id') or '').lower().replace('0x','')
        row['id_in_polygon_log']=bool(oid) and any(l['address'].lower()==RELAY and oid in l['data'].lower() for l in rc['logs'])
        if rel['category']=='PROTOCOL_CONFIRMED':
            pay=rel['tx']
            if rel['chain']==792703809:
                t=sol('getTransaction',[pay,dict(encoding='jsonParsed',maxSupportedTransactionVersion=0)])
                if t is None:
                    row['id_on_payout']=None;row['payer']='UNREAD'
                else:
                    memos=[str(i.get('parsed')) for i in t['transaction']['message']['instructions'] if i.get('program')=='spl-memo']
                    row['id_on_payout']=any(oid in x.lower() for x in memos)
                    row['payer']=t['transaction']['message']['accountKeys'][0]['pubkey']
                    row['payout_err']=t['meta']['err']
            else:
                tx=c.rpc('eth_getTransactionByHash',[pay],rel['chain'])
                row['id_on_payout']=tx['input'][-64:].lower()==oid
                row['payer']=tx['from'].lower()
                row['payer_is_solver']=tx['from'].lower()==SOLVER
                try:
                    r2=c.receipt(pay,rel['chain'])
                    row['payout_status']=int(r2['status'],16)
                    got=[x for x in moves(r2) if x['dst']==rel['target'].lower()]
                    row['payout_to_recipient']=[(x['raw'],x['token'][:8]) for x in got]
                except Exception as e:
                    row['payout_status']='UNREAD: '+str(e)[:80]
        if rel['category']!='PROTOCOL_CONFIRMED':
            row['logs_addresses']=sorted({l['address'].lower() for l in rc['logs']})[:12]
            row['pol_logs']=[dict(i=int(l['logIndex'],16),t=l['topics'],d=l['data'][:66]) for l in rc['logs'] if l['address'].lower()=='0x0000000000000000000000000000000000001010'][:10]
        res['withdrawals'].append(row); print('W',s,wd['usd'],row['category'],'burn',row['burn_equals_api'],'id',row['id_in_polygon_log'],row.get('id_on_payout'),str(row.get('payer'))[:10],flush=True)
    for d in case['deposits']:
        rc=c.receipt(d['tx'],137); m=moves(rc)
        want=round(d['usd']*1e6)
        mint=[x for x in m if x['src']==Z and x['dst']==w]
        res['deposits'].append(dict(case=s,tx=d['tx'],usd=d['usd'],status=int(rc['status'],16),mint_raw=[x['raw'] for x in mint],mint_equals_api=len(mint)==1 and abs(mint[0]['raw']-want)<=1,other_in=[(x['src'][:10],x['raw']) for x in m if x['dst']==w and x['src']!=Z]))
    json.dump(res,open(OUT+'a2_chain.json','w'),indent=0)
print('rpc used',c.rpc_used)
W=res['withdrawals'];D=res['deposits']
print('withdrawals',len(W),'status ok',sum(x['status']==1 for x in W),'burn equals API',sum(x['burn_equals_api'] for x in W),'protocol',sum(x['category']=='PROTOCOL_CONFIRMED' for x in W),'id both sides',sum(bool(x.get('id_in_polygon_log') and x.get('id_on_payout')) for x in W))
print('deposits',len(D),'status ok',sum(x['status']==1 for x in D),'mint equals API',sum(x['mint_equals_api'] for x in D),'sum mint',round(sum(sum(x['mint_raw']) for x in D)/1e6,2))
print('sum burn',round(sum(sum(x['burn_raw']) for x in W)/1e6,2))
print('payers',{str(x.get('payer'))[:12]:sum(1 for y in W if y.get('payer')==x.get('payer')) for x in W})
print('not burn-equal',[(x['case'],x['usd'],x['burn_raw'],x['out_of_wallet']) for x in W if not x['burn_equals_api']][:8])
print('deposit not mint-equal',[(x['case'],x['usd'],x['mint_raw'],x['other_in']) for x in D if not x['mint_equals_api']][:8])
