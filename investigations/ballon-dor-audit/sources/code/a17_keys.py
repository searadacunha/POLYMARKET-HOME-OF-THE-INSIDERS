"""Audit: full public history of each dossier's keys and recipients: any counterparty shared across dossiers, and any direct transfer in either direction, native or token. Public reads only."""
import glob,json,os,sys,time
from collections import defaultdict
import httpx
I='/Users/benjamindacunha/Projects/PolySentinel-investigation/';OUT='/Users/benjamindacunha/Projects/PolySentinel-audit-20261102/out/'
cases={os.path.basename(f)[:-5]:json.load(open(f)) for f in sorted(glob.glob(I+'cases/*.json'))}
http=httpx.Client(timeout=30,trust_env=False,headers={'User-Agent':'read-only audit'})
rel=[json.loads(l) for l in open(I+'graphs/relations.jsonl')]
nodes=json.load(open(I+'graphs/links_classified.json'))['nodes']
hubs={n['address'].lower() for n in nodes}
own=defaultdict(set)   # address -> dossiers
for s,c in cases.items():
    for o in c['wallet'].get('owners') or []:own[o.lower()].add(s)
    for x in c.get('recipients',[]):
        if str(x['address']).startswith('0x'):own[x['address'].lower()].add(s)
    for h in c.get('funding_chain',[]):
        if h and h.get('immediate_source') and (h.get('kind') or {}).get('kind')!='CONTRACT':own[h['immediate_source'].lower()].add(s)
    for f in c.get('exit_follow',[]) or []:
        for k in f.get('hops',[]) if isinstance(f,dict) else []:
            if not k.get('label') and (k.get('kind') or {}).get('kind')=='EOA' and (k.get('kind') or {}).get('nonce',9e9)<1000:own[k['target'].lower()].add(s)
for r in rel:
    for side in('source','target'):
        a=(r[side] or '').lower()
        if a.startswith('0x') and not r.get(side+'_label') and a not in hubs and r['basis'].find('nonce 1')>=0:own[a].add(r['case'])
wallets={c['address'].lower() for c in cases.values()}
targets=sorted(a for a in own if a not in wallets)
print('addresses',len(targets),flush=True)
SCOUT=dict(ethereum='https://eth.blockscout.com',arbitrum='https://arbitrum.blockscout.com',base='https://base.blockscout.com',optimism='https://optimism.blockscout.com')  # polygon.blockscout.com answers 403: Polygon native is scanned from logs in a22
calls=0
def get(net,path,params=None):
    global calls
    for k in range(4):
        try:
            calls+=1
            r=http.get(SCOUT[net]+path,params=params or {})
            if r.status_code==200:return r.json()
            if r.status_code in(403,404):return None
        except Exception:pass
        time.sleep(1.5*(k+1))
    return 'ERR'
def pages(net,path,flt,maxp=3):
    out=[];params={'filter':flt}
    for _ in range(maxp):
        d=get(net,path,params)
        if d in(None,'ERR'):return out,d=='ERR'
        out+=d.get('items',[])
        if not d.get('next_page_params'):return out,False
        params=dict(d['next_page_params'],filter=flt);time.sleep(.2)
    return out,True
edges=[];errors=[];capped=[]
for a in targets:
    for net in SCOUT:
        info=get(net,f'/api/v2/addresses/{a}')
        if info in(None,'ERR'):
            if info=='ERR':errors.append((a,net))
            continue
        for kind,flt in(('transactions','to'),('transactions','from'),('token-transfers','to'),('token-transfers','from'),('internal-transactions','to')):
            items,more=pages(net,f'/api/v2/addresses/{a}/{kind}',flt)
            if more:capped.append((a[:10],net,kind))
            for x in items:
                f=(x.get('from') or {}).get('hash','').lower();t=(x.get('to') or {}).get('hash','').lower()
                other=f if t==a else t
                if not other or other==a:continue
                tok=(x.get('token') or {}).get('symbol') if kind=='token-transfers' else None
                val=int(x.get('value') or 0) if kind!='token-transfers' else int((x.get('total') or {}).get('value') or 0)
                if kind!='token-transfers' and val==0:continue
                edges.append(dict(a=a,cases=sorted(own[a]),net=net,kind=kind,flt=flt,other=other,other_name=((x.get('from') if t==a else x.get('to')) or {}).get('name'),other_contract=((x.get('from') if t==a else x.get('to')) or {}).get('is_contract'),tx=x.get('hash') or x.get('transaction_hash'),at=x.get('timestamp'),value=val,token=tok,dec=(x.get('token') or {}).get('decimals') if tok else 18))
    print(a[:10],sorted(own[a]),'edges so far',len(edges),'calls',calls,flush=True)
    json.dump(dict(edges=edges,errors=errors,capped=capped),open(OUT+'a17_keys.json','w'))
print('errors',len(errors),'capped',len(capped),capped[:20])
print('\n=== direct transfers between addresses of different dossiers')
seen=set()
for e in edges:
    oc=own.get(e['other'],set())|({[s for s,c in cases.items() if c['address'].lower()==e['other']][0]} if e['other'] in wallets else set())
    if oc and not (oc&set(e['cases'])):
        k=(e['tx'],e['kind'])
        if k in seen:continue
        seen.add(k)
        print(' ',e['at'],e['net'],e['kind'],e['cases'],e['a'][:10],'<->',sorted(oc),e['other'][:10],e['token'] or 'native',e['value']/10**int(e['dec'] or 18),e['tx'])
print('\n=== counterparties shared by two or more dossiers, not contracts')
by=defaultdict(lambda:defaultdict(list))
for e in edges:
    for c in e['cases']:by[e['other']][c].append(e)
for o,v in sorted(by.items(),key=lambda x:-len(x[1])):
    if len(v)<2 or o in wallets:continue
    sample=next(iter(v.values()))[0]
    print(' ',o,sample['other_name'],'contract' if sample['other_contract'] else 'EOA',sorted(v),{c:[(x['kind'][:5],x['flt'],x['net'][:3],(x['at'] or '')[:10]) for x in l][:2] for c,l in list(v.items())[:3]})
print('calls',calls)
