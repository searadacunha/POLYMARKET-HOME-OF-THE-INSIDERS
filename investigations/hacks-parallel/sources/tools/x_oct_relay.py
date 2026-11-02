"""October: Relay's record of the largest inflows of the attacker plus a seeded random sample, slowly: the API answers 429 when shared with other sessions. requests/v2 is retired on 24/11/2026, raw answers stay in the cache."""
import chainlib as c, collections, json, net, random
A='0x3f99139f1c5854bb628c2e576aaf638e99dffc18'
o=json.load(open('../state/runs/oct_core.json'))['137']
inn=[x for x in o if x['dst']==A and x['kind'] in('internal','native') and x['src']=='0xb92fe925dc43a0ecde6c8b1a2709c170ec4fff4f']
by=collections.defaultdict(float)
for x in inn: by[x['tx']]+=c.amount(x)
top=sorted(by,key=lambda t:-by[t])
pick=top[:150]; rest=top[150:]; random.Random(20261102).shuffle(rest); pick+=rest[:50]
print('txs',len(top),'picked',len(pick),'POL covered',round(sum(by[t] for t in pick),2),'of',round(sum(by.values()),2),flush=True)
out={}; fail=0
for i,t in enumerate(pick):
    try:
        r=net.get('https://api.relay.link/requests/v2',dict(hash=t),pause=2.2,retries=3)
        out[t]=r.get('requests') or []
    except RuntimeError:
        fail+=1
    if i%25==0:
        print(i,'fail',fail,flush=True)
        json.dump(out,open('../state/runs/relay_oct.json','w'))
json.dump(out,open('../state/runs/relay_oct.json','w'))
users=collections.Counter(); usd=0.0; none=0; tok=collections.Counter(); chains=collections.Counter()
for t,q in out.items():
    if not q: none+=1; continue
    m=q[0]; users[(m.get('user') or '').lower()]+=1
    md=(m.get('data') or {}).get('metadata') or {}
    ci=(md.get('currencyIn') or {})
    tok[((ci.get('currency') or {}).get('symbol'))]+=1
    chains[((ci.get('currency') or {}).get('chainId'))]+=1
    try: usd+=float(ci.get('amountUsd') or 0)
    except (ValueError,TypeError): pass
print('read',len(out),'failed',fail,'no record',none,'distinct users',len(users),'top',users.most_common(4),'usd in',round(usd,2),'tokens',tok.most_common(4),'chains',chains.most_common(3))
