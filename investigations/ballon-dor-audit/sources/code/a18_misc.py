import json,time,httpx
http=httpx.Client(timeout=30,trust_env=False,headers={'User-Agent':'read-only audit'})
OUT='/Users/benjamindacunha/Projects/PolySentinel-audit-20261102/out/'
ch=http.get('https://api.relay.link/chains').json().get('chains',[])
sol={}
for c in ch:
    for v in c.get('solverAddresses') or []:
        sol.setdefault(v.lower() if str(v).startswith('0x') else v,set()).add(c.get('id'))
print('published solver addresses',len(sol))
a2=json.load(open(OUT+'a2_chain.json'))
tally={}
for w in a2['withdrawals']:
    p=w.get('payer')
    if not p:continue
    k=p.lower() if p.startswith('0x') else p
    tally.setdefault(k,[]).append(w['out_chain'])
for k,v in tally.items():print(' ',k[:14],len(v),sorted(set(v)),'published for',sorted(sol.get(k,[]))[:6] if k in sol else 'NOT published')
print('payouts by a published solver',sum(len(v) for k,v in tally.items() if k in sol),'of',sum(len(v) for v in tally.values()))
for net,a in(('polygon','0xdc264714f68d84cf29bc605589405e78bdbe7c9f'),('polygon','0x663dc15d3c1ac63ff12e45ab68fea3f0a883c251'),('ethereum','0xca8B1f1a56A0Fe8947D325BAAFA286F5bD4D6165')):
    base=dict(polygon='https://polygon.blockscout.com',ethereum='https://eth.blockscout.com')[net]
    d=http.get(f'{base}/api/v2/addresses/{a}').json();c=http.get(f'{base}/api/v2/addresses/{a}/counters').json()
    print(net,a,'name',d.get('name'),'contract',d.get('is_contract'),'verified',d.get('is_verified'),'tags',[t.get('display_name') for t in (d.get('public_tags') or [])],'impl',[x.get('name') for x in d.get('implementations') or []],'txs',c.get('transactions_count'),'native',int(d.get('coin_balance') or 0)/1e18)
    time.sleep(.3)
n=json.load(open(OUT+'a7_native.json'))
from collections import defaultdict
pay=defaultdict(set);fund=defaultdict(set)
for a,r in n['solana'].items():
    for p in r['fee_payers']:pay[p].update(r['cases'])
    for x in r['native_in']:
        for f in x['from']:fund[f].update(r['cases'])
print('solana fee payers in 2+ dossiers',{k[:10]:sorted(v) for k,v in pay.items() if len(v)>1})
print('solana native funders in 2+ dossiers',{k[:10]:sorted(v) for k,v in fund.items() if len(v)>1})
print('solana addresses read',len(n['solana']),'with signatures',sum(1 for r in n['solana'].values() if r['signatures']))
