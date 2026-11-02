"""How rare is a deposit above 10,000 $ into this service? A random sample of its transactions over about five days, which is a floor since it only sees what was sampled."""
import json,random,sys,time
from pathlib import Path
sys.path.insert(0,'tools')
import net,sol
G='GxjcMTWWDcKx5sxnHkNfPtuTSfV9cLgVkw3G7KvMnvBW'
sigs=[];before=None
for _ in range(9):
    p=sol.rpc('getSignaturesForAddress',[G,dict(limit=1000,**({'before':before} if before else {}))]); sigs+=p; before=p[-1]['signature']
rng=random.Random(20261101)
sample=rng.sample(sigs,400)
ins=[];payers=set()
for s in sample:
    t=sol.transaction(s['signature'])
    mv=sol.token_moves(t)
    for m in mv:
        if m['owner']==G and m['delta']>0:
            ins.append(m['delta'])
            for o in mv:
                if o['owner']!=G and o['delta']<0: payers.add(o['owner'])
ins.sort()
n=len(ins)
out=dict(signatures=len(sigs),span=[sigs[-1]['blockTime'],sigs[0]['blockTime']],sampled=400,inflows_seen=n,median=ins[n//2] if n else None,p90=ins[int(n*.9)] if n else None,max=ins[-1] if n else None,over_1000=sum(1 for x in ins if x>=1000),over_10000=sum(1 for x in ins if x>=10000),distinct_payers=len(payers))
Path('evidence/gxjc_sizes.json').write_text(json.dumps(out,indent=1));print(out)
