"""Phase 9 : historical_lead_score_at_T sans fuite : seuls les événements FAE non-FOLLOW du wallet résolus (T_e + 3600 <= T)."""
import numpy as np,pandas as pd
EV=pd.read_pickle('p9/events_out.pkl')
R=EV[EV.is_FAE&~EV.FOLLOW&EV.p_before.notna()][['wallet','ts','LEAD60']].copy(); R['res_t']=R.ts+3600
p0=R[R.ts<int(pd.Timestamp('2026-03-01',tz='UTC').timestamp())].LEAD60.mean(); ALPHA=10
hn=np.zeros(len(EV)); hl=np.zeros(len(EV))
Rg={w:(g.sort_values('res_t').res_t.values,np.cumsum(g.sort_values('res_t').LEAD60.values)) for w,g in R.groupby('wallet')}
for j,(w,t) in enumerate(zip(EV.wallet.values,EV.ts.values)):
    if w not in Rg: continue
    rt,cl=Rg[w]; k=np.searchsorted(rt,t,side='right')
    if k>0: hn[j]=k; hl[j]=cl[k-1]
EV['hist_n']=hn; EV['hist_lead']=hl; EV['hist_score']=(hl+ALPHA*p0)/(hn+ALPHA)
EV.to_pickle('p9/events_out.pkl'); print('p0',round(p0,5),'events with history',(hn>0).mean().round(3))
