"""Audit: native-coin funders and fee payers, which the investigation states it did not read. A shared funder that is not a service would be a discriminating link. Public reads only."""
import glob,json,os,sys,time
from collections import Counter,defaultdict
import httpx
I='/Users/benjamindacunha/Projects/PolySentinel-investigation/'
OUT='/Users/benjamindacunha/Projects/PolySentinel-audit-20261102/out/'
cases={os.path.basename(f)[:-5]:json.load(open(f)) for f in sorted(glob.glob(I+'cases/*.json'))}
rel=[json.loads(l) for l in open(I+'graphs/relations.jsonl')]
hubs={n['address'] for n in json.load(open(I+'graphs/links_classified.json'))['nodes']}|{n['address'].lower() for n in json.load(open(I+'graphs/links_classified.json'))['nodes']}
http=httpx.Client(timeout=30,trust_env=False,headers={'User-Agent':'read-only audit'})
sol_addr=defaultdict(set);evm_addr=defaultdict(set)
for r in rel:
    for side in('source','target'):
        a=r[side]
        if not a or r.get(side+'_label') or a in hubs or a.lower() in hubs:continue
        if a.startswith('0x'): evm_addr[a.lower()].add(r['case'])
        else: sol_addr[a].add(r['case'])
for s,c in cases.items():
    for f in c.get('exit_follow',[]) or []:
        for k in('address','next','to','target'):
            v=f.get(k) if isinstance(f,dict) else None
            if isinstance(v,str) and v.startswith('0x'): evm_addr[v.lower()].add(s)
wallets={c['address'].lower() for c in cases.values()}
print('solana addresses',len(sol_addr),'evm addresses',len(evm_addr))
SOL=('https://api.mainnet-beta.solana.com','https://solana-rpc.publicnode.com')  # the public node answers no signatures for addresses that were paid: a false zero
calls=0
def sol(method,params):
    global calls
    for attempt in range(6):
        for url in SOL:
            try:
                calls+=1
                r=http.post(url,json=dict(jsonrpc='2.0',id=1,method=method,params=params))
                if r.status_code==200:
                    b=r.json()
                    if b.get('result'):return b['result']
            except Exception:pass
            time.sleep(.6+attempt)
    return None
out=dict(solana={},evm={})
funded=defaultdict(set);payers=defaultdict(set)
for a,who in sorted(sol_addr.items()):
    sigs=sol('getSignaturesForAddress',[a,dict(limit=200)]) or []
    picks=sigs[-6:]+sigs[:4]
    seen=set();row=dict(cases=sorted(who),signatures=len(sigs),native_in=[],fee_payers=[])
    for s in picks:
        if s['signature'] in seen:continue
        seen.add(s['signature'])
        t=sol('getTransaction',[s['signature'],dict(encoding='jsonParsed',maxSupportedTransactionVersion=0)])
        if not t:continue
        keys=[k['pubkey'] for k in t['transaction']['message']['accountKeys']]
        pre,post=t['meta']['preBalances'],t['meta']['postBalances']
        if a in keys:
            i=keys.index(a)
            if post[i]>pre[i]:
                givers=[(keys[j],pre[j]-post[j]) for j in range(len(keys)) if pre[j]>post[j]]
                row['native_in'].append(dict(sig=s['signature'][:16],at=s.get('blockTime'),lamports=post[i]-pre[i],**{'from':[g[0] for g in givers][:3]}))
                for g in givers[:3]:
                    if g[0]!=a:funded[g[0]].add(a)
        if keys[0]!=a:
            row['fee_payers'].append(keys[0]);payers[keys[0]].add(a)
        time.sleep(.25)
    out['solana'][a]=row
    print('SOL',a[:10],sorted(who),'sigs',len(sigs),'native from',sorted({x for n in row['native_in'] for x in n['from']})[:3],'fee payers',sorted(set(row['fee_payers']))[:3],flush=True)
    json.dump(out,open(OUT+'a7_native.json','w'),indent=0)
SCOUT=dict(ethereum='https://eth.blockscout.com',polygon='https://polygon.blockscout.com',arbitrum='https://arbitrum.blockscout.com',base='https://base.blockscout.com',optimism='https://optimism.blockscout.com')
def scout(net,path):
    global calls
    for attempt in range(4):
        try:
            calls+=1
            r=http.get(SCOUT[net]+path)
            if r.status_code==200:return r.json()
            if r.status_code==404:return dict(items=[])
        except Exception:pass
        time.sleep(2*(attempt+1))
    return None
evm_funders=defaultdict(lambda:defaultdict(set))
for a,who in sorted(evm_addr.items()):
    if a in wallets:continue
    row=dict(cases=sorted(who))
    for net in SCOUT:
        info=scout(net,f'/api/v2/addresses/{a}')
        if not info or info.get('message')=='Not found':continue
        kind='contract' if info.get('is_contract') else 'eoa'
        tx=scout(net,f'/api/v2/addresses/{a}/transactions?filter=to')
        internal=scout(net,f'/api/v2/addresses/{a}/internal-transactions?filter=to')
        senders=Counter()
        for x in (tx or {}).get('items',[]):
            if int(x.get('value') or 0)>0 and x.get('from'):senders[x['from']['hash'].lower()]+=1
        for x in (internal or {}).get('items',[]):
            if int(x.get('value') or 0)>0 and x.get('from'):senders[x['from']['hash'].lower()]+=1
        if senders or tx is None or internal is None:
            row[net]=dict(kind=kind,senders=dict(senders.most_common(8)),read=tx is not None and internal is not None)
        for k in senders:evm_funders[k][a].update(who)
        time.sleep(.3)
    out['evm'][a]=row
    print('EVM',a[:10],sorted(who),{n:list(v['senders'])[:3] for n,v in row.items() if n!='cases'},flush=True)
    json.dump(out,open(OUT+'a7_native.json','w'),indent=0)
print('\n=== shared across cases')
def cases_of(addrs,src):
    res=set()
    for x in addrs:res|=src.get(x,set())
    return res
for k,v in funded.items():
    c=cases_of(v,sol_addr)
    if len(c)>1:print('SOL native funder',k,sorted(c),len(v))
for k,v in payers.items():
    c=cases_of(v,sol_addr)
    if len(c)>1:print('SOL fee payer',k,sorted(c),len(v))
for k,v in evm_funders.items():
    c=set()
    for w in v.values():c|=w
    if len(c)>1:print('EVM native sender',k,sorted(c),len(v))
print('calls',calls)
