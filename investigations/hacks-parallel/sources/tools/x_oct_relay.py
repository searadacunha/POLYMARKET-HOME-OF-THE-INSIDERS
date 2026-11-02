"""October: Relay's record of each inflow of the attacker, to count source accounts and amounts. requests/v2 is retired on 24/11/2026, raw answers stay in the cache."""
import chainlib as c, collections, json, net
A='0x3f99139f1c5854bb628c2e576aaf638e99dffc18'
o=json.load(open('../state/runs/oct_core.json'))['137']
inn=[x for x in o if x['dst']==A and x['kind'] in('internal','native')]
txs=sorted({x['tx'] for x in inn})
print(len(inn),len(txs),flush=True)
out={}
for i,t in enumerate(txs):
    r=net.get('https://api.relay.link/requests/v2',dict(hash=t),pause=.4)
    out[t]=r.get('requests') or []
    if i%100==0: print(i,flush=True)
json.dump(out,open('../state/runs/relay_oct.json','w'))
users=collections.Counter(); usd=0.0; none=0; tok=collections.Counter()
for t,q in out.items():
    if not q: none+=1; continue
    m=q[0]; users[(m.get('user') or '').lower()]+=1
    md=(m.get('data') or {}).get('metadata') or {}
    ci=(md.get('currencyIn') or {})
    tok[((ci.get('currency') or {}).get('symbol'))]+=1
    try: usd+=float(ci.get('amountUsd') or 0)
    except ValueError: pass
print('records none',none,'users',len(users),'top',users.most_common(5),'usd in',round(usd,2),'tokens',tok.most_common(5))
