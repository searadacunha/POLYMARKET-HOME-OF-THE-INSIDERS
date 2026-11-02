"""Phase 8 : features de financement à T (uniquement afflux antérieurs à T) + wallet_features.csv"""
import json,os,numpy as np,pandas as pd
OUT='/Users/benjamindacunha/Documents/Crypto/enquete_maduro_iran/phase8/'
from p8_sets import MOON,RELAY
S=pd.read_pickle('p8/sample_events.pkl'); fe=S[S.in_fund_sample]
F={}; wrows=[]
for w in fe.wallet.unique():
    fp=f'p8/funding/{w}.json'
    if not os.path.exists(fp): continue
    F[w]=json.load(open(fp))
    ro=f'p8/relayorig/{w}.json'
    F[w]['relayfam']=[x['ts'] for x in (json.load(open(ro)) if os.path.exists(ro) else []) if x.get('family')]
    F[w]['relay_checked']=os.path.exists(ro)
    f=F[w]; inf=f['inflows']
    srcs={x[1] for x in inf}
    wrows.append(dict(wallet=w,first_any=f['first_any'],n_inflows=len(inf),n_funders=len(srcs),first_inflow_ts=inf[0][0] if inf else None,first_inflow_src=inf[0][1] if inf else None,
        first_inflow_usd=inf[0][2] if inf else None,moonpay_any=bool(srcs&MOON) or bool(f['relayfam']),moonpay_via_relay=bool(f['relayfam']),relay_checked=f['relay_checked'],relay_any=bool(srcs&RELAY),truncated=any(f['full'].values())))
rows=[]
for r in fe.itertuples(index=False):
    f=F.get(r.wallet)
    if f is None: continue
    inf=[x for x in f['inflows'] if x[0]<r.ts]
    covered=not any(f['full'].values()) or r.ts<=min([f.get('last_seen_'+k,9e12) for k,v in f['full'].items() if v] or [9e12])
    age=(r.ts-f['first_any'])/3600 if f['first_any'] and f['first_any']<r.ts else np.nan
    last=inf[-1] if inf else None
    relfam=[t for t in f['relayfam'] if t<r.ts]
    src='MOONPAY' if last and (last[1] in MOON or last[0] in f['relayfam']) else ('RELAY' if last and last[1] in RELAY else ('OTHER' if last else 'NONE'))
    rows.append(dict(eid=r.eid,wallet_age_h=age,last_funding_min=((r.ts-last[0])/60 if (last and covered) else np.nan),funding_src=src,
        moonpay_funded=any(x[1] in MOON for x in inf) or bool(relfam),n_funders_T=len({x[1] for x in inf})))
FF=pd.DataFrame(rows)
FF=FF.merge(fe[['eid','prior_trades_univ']],on='eid',how='left')
FF['S_FRESH']=(FF.wallet_age_h<=48)&(FF.prior_trades_univ<=2)
FF=FF.drop(columns=['prior_trades_univ'])
FF['S_FASTFUND']=(FF.last_funding_min<=60).values
FF['S_MOONPAY']=FF.moonpay_funded.fillna(False).astype(bool)
FF.to_pickle('p8/funding_features.pkl')
W=pd.DataFrame(wrows)
A=dict(S[S.popA.notna()][['wallet','popA']].drop_duplicates().values)
W['popA']=W.wallet.map(A); W['population']=np.where(W.popA.notna(),'A',np.where(W.moonpay_any,'B','C'))
W.to_csv(OUT+'wallet_features.csv',index=False)
print('funding wallets',len(W),W.population.value_counts().to_dict(),'events with funding feats',len(FF),FF[['S_FRESH','S_FASTFUND','S_MOONPAY']].sum().to_dict())
