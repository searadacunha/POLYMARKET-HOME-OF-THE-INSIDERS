"""Phase 8 : H2 (pression puis retournement), populations A/B/C, Q1 (financement récent -> activité anormale)."""
import json,numpy as np,pandas as pd,bisect,collections
OUT='/Users/benjamindacunha/Documents/Crypto/enquete_maduro_iran/phase8/'
S=pd.read_pickle('p8/event_study.pkl'); T=pd.read_pickle('p8/alltrades.pkl')
# sorties du même wallet sur le même jeton dans les 6 h (constat descriptif postérieur à T, jamais utilisé comme feature)
sells=collections.defaultdict(list)
for w,a,ts in T[T.side=='SELL'][['wallet','asset','ts']].itertuples(index=False): sells[(w,a)].append(ts)
for k in sells: sells[k].sort()
def exit6h(r):
    L=sells.get((r.wallet,r.asset),[]); i=bisect.bisect_right(L,r.ts); return i<len(L) and L[i]<=r.ts+21600
S['exit_6h']=[exit6h(r) for r in S.itertuples(index=False)]
S['imp_5m']=S.p_5m-S.p_T; S['rev_6h']=S.p_6h-S.p_5m
S['pressure_reversal']=(S.imp_5m>=0.02)&(S.rev_6h<=-0.5*S.imp_5m)&S.exit_6h
grp={'S_LARGE, wallet neuf (<=2 trades)':S.S_LARGE&(S.prior_trades_univ<=2),'S_LARGE, wallet établi (>=20 trades)':S.S_LARGE&(S.prior_trades_univ>=20),
     'S_CONV':S.S_CONV,'S_LONGSHOT_LARGE':S.S_LONGSHOT_LARGE,'Baseline aléatoire':S.in_baseline}
h2=[]
for sp in ('TRAIN','VALID','TEST','ALL'):
    for g,m in grp.items():
        x=S[m&((S.split==sp) if sp!='ALL' else True)].dropna(subset=['imp_5m','rev_6h'])
        h2.append(dict(split=sp,groupe=g,n=len(x),impact5m_moy=x.imp_5m.mean(),impact5m_ge2pp=(x.imp_5m>=0.02).mean(),reversal_moy=x.rev_6h.mean(),sortie_6h=x.exit_6h.mean(),pattern_pression_retournement=x.pressure_reversal.mean()))
H2=pd.DataFrame(h2); H2.to_csv(OUT+'pressure_reversal.csv',index=False)
# populations (échantillon financement)
F=S[S.in_fund_sample].copy()
W=pd.read_csv(OUT+'wallet_features.csv')
popmap=dict(W[['wallet','population']].values); F['population']=F.wallet.map(popmap).fillna('C')
pc=[]
for pop,g in F.groupby('population'):
    pc.append(dict(population=pop,n_events=len(g),n_wallets=g.wallet.nunique(),usd_median=g.usd.median(),size_rank_ge95=(g.size_rank_mkt>=0.95).mean(),first_in_mkt=g.first_in_mkt.mean(),
        price_le020=(g.price<=0.2).mean(),S_LARGE=g.S_LARGE.mean(),ret_60m=g.ret_60m.mean(),ret_res=g.ret_res.mean(),wallet_raw_res=g.wallet_raw_res.mean(),hit_res=(g.win==1).mean(),momo_60=g.momo_60.mean()))
PC=pd.DataFrame(pc); PC.to_csv(OUT+'populations_ABC.csv',index=False)
# Q1 : financement récent -> activité anormale ?
q1=[]
F['fund_lt60']=F.last_funding_min<=60; F['fund_lt24h']=F.last_funding_min<=1440
for lab,m in (('financé <60 min',F.fund_lt60),('financé <24 h',F.fund_lt24h),('financé >24 h',F.last_funding_min>1440),('S_FRESH',F.S_FRESH),('non S_FRESH',~F.S_FRESH&F.wallet_age_h.notna())):
    g=F[m]
    q1.append(dict(groupe=lab,n=len(g),size_rank_ge95=(g.size_rank_mkt>=0.95).mean(),size_rank_ge99=(g.size_rank_mkt>=0.99).mean(),first_in_mkt=g.first_in_mkt.mean(),usd_median=g.usd.median(),price_le020=(g.price<=0.2).mean(),hours_to_end_median=g.hours_to_end.median()))
Q1=pd.DataFrame(q1); Q1.to_csv(OUT+'q1_funding_activity.csv',index=False)
# population A
A=S[S.popA.notna()]
arows=[]
for r in A.itertuples(index=False):
    arows.append(dict(compte=r.popA,split=r.split,cid=r.cid,ts=pd.to_datetime(r.ts,unit='s',utc=True),usd=round(r.usd,2),price=r.price,size_rank_mkt=r.size_rank_mkt,first_in_mkt=r.first_in_mkt,prior_trades_univ=r.prior_trades_univ,
        signaux=';'.join(s for s in ('S_LARGE','S_LONGSHOT_LARGE','S_CONV','S_ACCUM','S_FIRST_LARGE','S_FRESH','S_FASTFUND','S_MOONPAY') if getattr(r,s)),
        momo_60=r.momo_60,p_T=r.p_T,p_obs=r.p_obs,ret_60m=r.ret_60m,ret_6h=r.ret_6h,ret_res=r.ret_res,win=r.win,wallet_age_h=getattr(r,'wallet_age_h',np.nan),last_funding_min=getattr(r,'last_funding_min',np.nan)))
AA=pd.DataFrame(arows).sort_values(['compte','ts']); AA.to_csv(OUT+'population_A_events.csv',index=False)
print(H2[H2.split=='ALL'].to_string()); print(PC.to_string()); print(Q1.to_string())
print(AA.groupby('compte').agg(n=('usd','size'),usd=('usd','sum'),signals=('signaux',lambda s:(s!='').mean()),ret_res=('ret_res','mean')).to_string())
