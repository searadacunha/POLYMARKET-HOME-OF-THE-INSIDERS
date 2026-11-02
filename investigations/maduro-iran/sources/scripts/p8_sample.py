"""Phase 8 : échantillonnage (graine 8), sans regarder aucun résultat postérieur à T."""
import json,numpy as np,pandas as pd
rng=np.random.default_rng(8)
ev=pd.read_pickle('p8/events.pkl')
SIG=['S_LARGE','S_LONGSHOT_LARGE','S_CONV','S_ACCUM','S_FIRST_LARGE']
pick=set(); BASE=set()
for sp in ('TRAIN','VALID','TEST'):
    e=ev[ev.split==sp]
    b=set(rng.choice(e.eid.values,size=min(2000,len(e)),replace=False)); pick|=b; BASE.update(b)
    for s in SIG:
        f=e[e[s]]
        pick|=set(rng.choice(f.eid.values,size=min(1500,len(f)),replace=False)) if len(f) else set()
pick|=set(ev[ev.popA.notna()].eid)
# financement : 1 500 wallets aléatoires + population A ; 4 premiers + 4 aléatoires événements par wallet
ws=ev.wallet.unique(); fw=set(rng.choice(ws,size=min(1500,len(ws)),replace=False))|set(ev[ev.popA.notna()].wallet)
fund_ev=set()
for w,g in ev[ev.wallet.isin(fw)].groupby('wallet'):
    g=g.sort_values('ts'); ids=list(g.eid.values[:4]); rest=g.eid.values[4:]
    if len(rest): ids+=list(rng.choice(rest,size=min(4,len(rest)),replace=False))
    fund_ev|=set(ids)
pick|=fund_ev
S=ev[ev.eid.isin(pick)].copy()
S["in_baseline"]=S.eid.isin(BASE)
for sp in ('TRAIN','VALID','TEST'):
    pass
json.dump(sorted(fw),open('p8/funding_wallets.json','w'))
S['in_fund_sample']=S.eid.isin(fund_ev)
S.to_pickle('p8/sample_events.pkl')
print('sampled events',len(S),'assets',S.asset.nunique(),'funding wallets',len(fw),'funding events',len(fund_ev))
