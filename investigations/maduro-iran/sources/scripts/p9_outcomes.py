"""Phase 9 : résultats POSTÉRIEURS à T (jamais lus par le moteur de features ni par le détecteur).
Mouvement mesuré sur les trades des AUTRES wallets ; étiquettes LEAD60/FOLLOW ; lead_time ; MFE/MAE ; contrôle E (horodatage aléatoire)."""
import numpy as np,pandas as pd
TH=0.03
P=pd.read_pickle('p9/prints.pkl'); EV=pd.read_pickle('p9/events.pkl')
wcode={w:i for i,w in enumerate(P.wallet.unique())}
P['wc']=P.wallet.map(wcode).astype(np.int64)
M={cid:(g.ts.values,g.p_yes.values,g.wc.values) for cid,g in P.groupby('cid',sort=False)}
H={'5s':5,'10s':10,'30s':30,'1m':60,'5m':300,'10m':600,'30m':1800,'60m':3600}
n=len(EV); out={('dpost_'+k):np.full(n,np.nan) for k in H}
for k in H: out['obs_'+k]=np.zeros(n,dtype=bool)
out.update({'lead_time_s':np.full(n,np.nan),'t_complete_s':np.full(n,np.nan),'mfe_60m':np.full(n,np.nan),'mae_60m':np.full(n,np.nan),'n_other_60m':np.zeros(n,dtype=int),
            'p_t1':np.full(n,np.nan),'dpre10_t1':np.full(n,np.nan),'d_t1_to_T':np.full(n,np.nan)})
for j,(cid,t,d,w,pb,t1) in enumerate(zip(EV.cid.values,EV.ts.values,EV.d.values,EV.wallet.map(wcode).values,EV.p_before.values,EV.conv_t1.values)):
    ts,py,wc=M[cid]
    if np.isnan(pb): continue
    i1=np.searchsorted(ts,t,side='right'); i2=np.searchsorted(ts,t+3600,side='right')
    s_ts=ts[i1:i2]; s_p=py[i1:i2] if d==0 else 1-py[i1:i2]; m=wc[i1:i2]!=w
    o_ts=s_ts[m]; o_p=s_p[m]; out['n_other_60m'][j]=len(o_ts)
    for k,h in H.items():
        q=np.searchsorted(o_ts,t+h,side='right')-1
        if q>=0: out['dpost_'+k][j]=o_p[q]-pb; out['obs_'+k][j]=True
        else: out['dpost_'+k][j]=0.0
    if len(o_p):
        dd=o_p-pb; out['mfe_60m'][j]=dd.max(); out['mae_60m'][j]=dd.min()
        a=np.nonzero(dd>=TH/2)[0]
        if len(a): out['lead_time_s'][j]=o_ts[a[0]]-t
        b=np.nonzero(dd>=TH)[0]
        if len(b): out['t_complete_s'][j]=o_ts[b[0]]-t
    else: out['mfe_60m'][j]=0; out['mae_60m'][j]=0
    if not np.isnan(t1):   # CONV : contexte au 1er wallet (quantités antérieures à T)
        k1=np.searchsorted(ts,t1,side='left')-1; k0=np.searchsorted(ts,t1-600,side='right')-1
        if k1>=0:
            p1=py[k1] if d==0 else 1-py[k1]; out['p_t1'][j]=p1; out['d_t1_to_T'][j]=pb-p1
            if k0>=0: out['dpre10_t1'][j]=p1-(py[k0] if d==0 else 1-py[k0])
for k,v in out.items(): EV[k]=v
EV['FOLLOW']=EV.dpre_10m>=TH/2
EV['LEAD60']=(~EV.FOLLOW)&(EV.dpost_60m>=TH)
EV['LEAD60_2pp']=(EV.dpre_10m<0.01)&(EV.dpost_60m>=0.02); EV['LEAD60_5pp']=(EV.dpre_10m<0.025)&(EV.dpost_60m>=0.05)
A8=pd.read_pickle('p8/alltrades.pkl'); A8=A8[A8.oi.isin([0,1])].reset_index(drop=True)
EV['win']=A8.win.values[EV.rid.values]
# ---- contrôle E : horodatage aléatoire dans le même marché, même direction
rng=np.random.default_rng(9); ctrl=np.full(n,np.nan); ctrl_pre=np.full(n,np.nan)
for j,(cid,d) in enumerate(zip(EV.cid.values,EV.d.values)):
    ts,py,wc=M[cid]
    lo,hi=ts[0]+3600,ts[-1]-3600
    if hi<=lo: continue
    t=rng.uniform(lo,hi)
    i0=np.searchsorted(ts,t,side='left')-1; i6=np.searchsorted(ts,t+3600,side='right')-1; ip=np.searchsorted(ts,t-600,side='right')-1
    f=(lambda x:x) if d==0 else (lambda x:1-x)
    ctrl[j]=f(py[i6])-f(py[i0]); ctrl_pre[j]=f(py[i0])-f(py[ip]) if ip>=0 else np.nan
EV['ctrlE_dpost_60m']=ctrl; EV['ctrlE_dpre_10m']=ctrl_pre
EV['ctrlE_LEAD60']=(ctrl_pre<TH/2)&(ctrl>=TH)
EV.to_pickle('p9/events_out.pkl')
print('events',n,'LEAD60 rate FAE by split',EV[EV.is_FAE&~EV.FOLLOW].groupby('split').LEAD60.mean().round(4).to_dict(),'ctrlE',EV[EV.is_FAE].groupby('split').ctrlE_LEAD60.mean().round(4).to_dict())
