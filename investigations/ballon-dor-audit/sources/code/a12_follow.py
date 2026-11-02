"""Audit: what the report left unread. Native POL of the 77,050 $ withdrawal, ETH of 0xdd97e6, Relay's published solvers, and who signs the sweeps toward Gxjc. Public reads only."""
import glob,json,os,sys,time
sys.path.insert(0,'/Users/benjamindacunha/Projects/PolySentinel-harness')
os.environ['SIGNAL_ENGINE_STATE']='/Users/benjamindacunha/Projects/PolySentinel-audit-20261102/out/es'
import httpx
from signal_engine.fund_flow.client import Client
I='/Users/benjamindacunha/Projects/PolySentinel-investigation/'
OUT='/Users/benjamindacunha/Projects/PolySentinel-audit-20261102/out/'
cases={os.path.basename(f)[:-5]:json.load(open(f)) for f in sorted(glob.glob(I+'cases/*.json'))}
known={}
for s,c in cases.items():
    known[c['address'].lower()]=s
    for o in c['wallet'].get('owners') or []:known[o.lower()]=s
for r in (json.loads(l) for l in open(I+'graphs/relations.jsonl')):
    for side in('source','target'):
        a=r[side]
        if a and not r.get(side+'_label'):known.setdefault(a.lower() if a.startswith('0x') else a,r['case'])
LT='0xe6497e3ee548a3372136af2fcb0696db31fc6cf20260707645068bd3fe97f3c4';SYS='0x0000000000000000000000000000000000001010'
c=Client(rpc_limit=500,http_limit=0,pause_s=.25,ledger=OUT+'rpc_requests.jsonl')
http=httpx.Client(timeout=30,trust_env=False)
out={}
TX='0x909d9602d5ad975b2f30c66d4a058592306e2468a002dd0a691170b61677a6f1'
KEY='0x1b500b6c40a2ff0930e540e8f53c559a32e75f2c'
rc=c.receipt(TX,137)
pols=[dict(i=int(l['logIndex'],16),src='0x'+l['topics'][2][-40:],dst='0x'+l['topics'][3][-40:],pol=int(l['data'][2:66],16)/1e18) for l in rc['logs'] if l['address'].lower()==SYS and l['topics'][0]==LT]
to_key=[p for p in pols if p['dst']==KEY]
print('POL logs in the withdrawal receipt',len(pols),'to the key',to_key,flush=True)
out['pol_to_key']=to_key
block=int(rc['blockNumber'],16);head=c.head(137)
print('blocks',block,head,flush=True)
moved=[];incoming=[]
step=9000;errors=0
for s in range(block,head+1,step):
    for side,topics in (('out',[LT,None,'0x'+'0'*24+KEY[2:]]),):
        try:
            logs=c.rpc('eth_getLogs',[dict(address=SYS,fromBlock=hex(s),toBlock=hex(min(head,s+step-1)),topics=topics)],137)
        except Exception as e:
            errors+=1;print('ERR',s,str(e)[:100],flush=True);continue
        for l in logs:
            moved.append(dict(tx=l['transactionHash'],block=int(l['blockNumber'],16),dst='0x'+l['topics'][3][-40:],pol=int(l['data'][2:66],16)/1e18))
big=[m for m in moved if m['pol']>=1]
print('native outflows from the key since the withdrawal',len(moved),'>=1 POL',len(big),'errors',errors,'rpc',c.rpc_used,flush=True)
dest={}
for m in big:dest[m['dst']]=dest.get(m['dst'],0)+m['pol']
out['pol_out']=big;out['pol_dest']=dest
for a,v in sorted(dest.items(),key=lambda x:-x[1])[:8]:
    code=c.rpc('eth_getCode',[a,'latest'],137);nonce=int(http.post('https://polygon-bor-rpc.publicnode.com',json=dict(jsonrpc='2.0',id=1,method='eth_getTransactionCount',params=[a,'latest'])).json()['result'],16)
    print(' to',a,round(v,2),'POL','contract' if code not in('0x',None) else 'EOA','nonce',nonce,'in another case:',known.get(a),flush=True)
    for m in big[:0]:pass
for m in big[:6]:
    t=c.block_time(m['block'],137);print('  ',time.strftime('%m-%d %H:%M:%S',time.gmtime(t)),m['dst'][:12],round(m['pol'],2),m['tx'][:14],flush=True)
print('\n=== ETH of 0xdd97e6')
r=http.get('https://eth.blockscout.com/api/v2/addresses/0xca8B1f1a56A0Fe8947D325BAAFA286F5bD4D6165/transactions?filter=from')
items=r.json().get('items',[]) if r.status_code==200 else []
info=http.get('https://eth.blockscout.com/api/v2/addresses/0xca8B1f1a56A0Fe8947D325BAAFA286F5bD4D6165').json()
print('balance ETH',int(info.get('coin_balance') or 0)/1e18,'tx out',len(items))
out['eth_out']=[]
for x in items[:12]:
    row=dict(at=x['timestamp'],to=(x.get('to') or {}).get('hash'),name=(x.get('to') or {}).get('name'),eth=int(x['value'])/1e18,tx=x['hash'],method=x.get('method'));out['eth_out'].append(row);print(' ',row,'in another case:',known.get((row['to'] or '').lower()))
print('\n=== Relay published solvers')
r=http.get('https://api.relay.link/chains')
chains=r.json().get('chains',[]) if r.status_code==200 else []
sol_map={}
for ch in chains:
    for k,v in ch.items():
        if 'solver' in k.lower() and isinstance(v,str):sol_map.setdefault(v.lower(),set()).add(ch.get('id'))
print('chains',len(chains),'solver fields',sorted({k for ch in chains for k in ch if 'solver' in k.lower()}),'distinct solver addresses',len(sol_map))
a2=json.load(open(OUT+'a2_chain.json'))
pay={}
for w in a2['withdrawals']:
    p=w.get('payer')
    if p:pay.setdefault(p.lower() if p.startswith('0x') else p,[]).append(w['case'])
for p,v in pay.items():print(' ',p[:14],len(v),'published' if p in sol_map or p.lower() in sol_map else 'NOT in the chains endpoint')
out['solvers']=sorted(sol_map)[:40]
print('\n=== sweeps into Gxjc')
SOL='https://api.mainnet-beta.solana.com'
def srpc(m,p):
    for k in range(6):
        try:
            b=http.post(SOL,json=dict(jsonrpc='2.0',id=1,method=m,params=p));
            if b.status_code==200 and b.json().get('result') is not None:return b.json()['result']
        except Exception:pass
        time.sleep(2+k)
for a in ('DMmDPF9sFcNbq8dVKfxqZsKV4xKZBtsUZ4hXSwy1wt5T','F7ew8r8X5YL3DPLtzg9Az3cPDKcVxXGjUpqgpskNh5Eh','H8eTcB5vXvsHc54Hnpa61Uof3PfNVaHtQ8CooY6aXFvJ'):
    sigs=srpc('getSignaturesForAddress',[a,dict(limit=100)]) or []
    print(a[:10],'signatures',len(sigs),'span',time.strftime('%m-%d %H:%M',time.gmtime(sigs[-1]['blockTime'])) if sigs else None,time.strftime('%m-%d %H:%M',time.gmtime(sigs[0]['blockTime'])) if sigs else None,flush=True)
    for s in (sigs if a[0]!='H' else sigs[:2]):
        t=srpc('getTransaction',[s['signature'],dict(encoding='jsonParsed',maxSupportedTransactionVersion=0)])
        if not t:continue
        keys=t['transaction']['message']['accountKeys']
        signers=[k['pubkey'][:10] for k in keys if k.get('signer')]
        pre,post=t['meta']['preBalances'],t['meta']['postBalances']
        native=[(keys[i]['pubkey'][:10],round((post[i]-pre[i])/1e9,6)) for i in range(len(keys)) if post[i]!=pre[i]]
        tok=[(b['owner'][:10],b['uiTokenAmount']['uiAmount'],b['mint'][:6]) for b in t['meta'].get('postTokenBalances',[])][:5]
        ins=[i.get('parsed',{}).get('type') if isinstance(i.get('parsed'),dict) else i.get('program') for i in t['transaction']['message']['instructions']]
        print('   ',time.strftime('%m-%d %H:%M:%S',time.gmtime(s['blockTime'])),'signers',signers,'native',native[:5],'tokens',tok,'ins',ins[:6],flush=True)
        time.sleep(.4)
json.dump(out,open(OUT+'a12_follow.json','w'),indent=0,default=str)
