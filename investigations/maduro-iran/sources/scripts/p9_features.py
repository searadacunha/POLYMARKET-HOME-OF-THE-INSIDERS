"""Phase 9 : événements FAE / ACC / CONV et features observables à T (uniquement des trades antérieurs à T).
Entrée : p8/alltrades.pkl (trades preneurs >= 100 $). Sortie : p9/events.pkl, p9/prints.pkl"""
import numpy as np,pandas as pd,collections,datetime as dt
T=pd.read_pickle('p8/alltrades.pkl')[['cid','cat','wallet','side','asset','price','usd','ts','oi','end','size_rank_mkt','prior_trades_univ','first_in_mkt']].copy()
T=T[T.oi.isin([0,1])].reset_index(drop=True)
T['rid']=np.arange(len(T))
T=T.sort_values(['ts','rid']).reset_index(drop=True)
T['p_yes']=np.where(T.oi==0,T.price,1-T.price)
T['buyeq_yes']=((T.side=='BUY')&(T.oi==0))|((T.side=='SELL')&(T.oi==1))
b1=int(dt.datetime(2026,3,1,tzinfo=dt.UTC).timestamp()); b2=int(dt.datetime(2026,6,1,tzinfo=dt.UTC).timestamp())
T['split']=np.where(T.ts<b1,'TRAIN',np.where(T.ts<b2,'VALID','TEST'))
T.to_pickle('p9/prints.pkl')
# ---- FAE : achat >= 250 $, aucun trade du wallet dans ce marché dans les 24 h précédentes
T['prev_ts_wm']=T.groupby(['wallet','cid']).ts.shift(1)
fae=(T.side=='BUY')&(T.usd>=250)&((T.prev_ts_wm.isna())|((T.ts-T.prev_ts_wm)>86400))
# ---- achats du wallet sur le même jeton : fenêtre 30 min (vectorisé)
B=T[T.side=='BUY'].sort_values(['wallet','asset','ts','rid']).copy()
gid=B.groupby(['wallet','asset']).ngroup().values.astype(np.int64)
key=gid*10**10+B.ts.values; lo=np.searchsorted(key,key-1800,side='left')
idx=np.arange(len(B)); cnt=idx-lo+1; cu=np.concatenate([[0],np.cumsum(B.usd.values)]); cum=cu[idx+1]-cu[lo]
B['n_buys_30m_incl']=cnt; B['cum_usd_30m']=cum; B['t_first_30m']=B.ts.values[lo]
acc_raw=(cnt>=3)&(cum>=750)
prev_ok=np.r_[False,acc_raw[:-1]]&np.r_[False,gid[1:]==gid[:-1]]
B['acc_event']=acc_raw&~prev_ok
T=T.merge(B[['rid','n_buys_30m_incl','cum_usd_30m','t_first_30m','acc_event']],on='rid',how='left')
T['n_buys_30m']=T.n_buys_30m_incl.fillna(1)-1
T['acc_event']=T.acc_event.fillna(False).astype(bool)
# ---- CONV : 3e wallet distinct achetant le même jeton (>=250 $) en 10 min
conv=np.zeros(len(T),dtype=bool); conv_t1=np.full(len(T),np.nan); conv_nw=np.zeros(len(T),dtype=int)
BB=T[(T.side=='BUY')&(T.usd>=250)]
last_conv={}
for asset,g in BB.groupby('asset',sort=False):
    dq=collections.deque()
    for i,t,w in zip(g.index.values,g.ts.values,g.wallet.values):
        while dq and dq[0][0]<=t-600: dq.popleft()
        dq.append((t,w))
        first={}
        for tt,ww in dq:
            if ww not in first: first[ww]=tt
        conv_nw[i]=len(first)
        if len(first)>=3 and (asset not in last_conv or t-last_conv[asset]>600):
            conv[i]=True; conv_t1[i]=min(first.values()); last_conv[asset]=t
T['conv_event']=conv; T['conv_t1']=conv_t1; T['conv_nwallets_10m']=conv_nw
# ---- taille relative au wallet (log usd - moyenne des log usd antérieurs du wallet)
T['lusd']=np.log(T.usd)
g=T.groupby('wallet').lusd
T['wallet_prev_mean_lusd']=(g.cumsum()-T.lusd)/g.cumcount().replace(0,np.nan)
T['rel_size_wallet']=T.lusd-T.wallet_prev_mean_lusd
# ---- concentration directionnelle du wallet dans le marché (volume antérieur dans la même direction YES-équivalente)
T['dir_yes']=T.buyeq_yes.astype(int)*2-1
gw=T.groupby(['wallet','cid'])
T['past_vol_wm']=gw.usd.cumsum()-T.usd
T['dv']=T.usd*T.dir_yes
T['past_dirvol_wm']=T.groupby(['wallet','cid']).dv.cumsum()-T.dv
T['conc_dir']=np.where(T.past_vol_wm>0,T.past_dirvol_wm*T.dir_yes/T.past_vol_wm,np.nan)  # +1 = même direction que le passé
# ---- mouvements avant T et activité (série YES-équivalente du marché, trades < T strictement)
EV=T[fae|T.acc_event|T.conv_event].copy()
EV['is_FAE']=fae[EV.index].values; EV['is_ACC']=EV.acc_event; EV['is_CONV']=EV.conv_event
EV['d']=EV.oi  # jeton acheté (0=YES,1=NO)
PRE={'10s':10,'30s':30,'1m':60,'5m':300,'10m':600,'30m':1800,'60m':3600}
M={cid:(g.ts.values,g.p_yes.values) for cid,g in T.groupby('cid',sort=False)}
res={k:np.full(len(EV),np.nan) for k in ['p_before']+['dpre_'+k for k in PRE]+['act_10m','act_7d']}
for j,(cid,t,d) in enumerate(zip(EV.cid.values,EV.ts.values,EV.d.values)):
    ts,py=M[cid]
    i0=np.searchsorted(ts,t,side='left')-1   # dernier trade strictement avant T
    if i0<0: continue
    s=1 if d==0 else -1
    pb=py[i0] if d==0 else 1-py[i0]; res['p_before'][j]=pb
    for k,w in PRE.items():
        iw=np.searchsorted(ts,t-w,side='right')-1
        if iw>=0: res['dpre_'+k][j]=pb-(py[iw] if d==0 else 1-py[iw])
    res['act_10m'][j]=i0+1-np.searchsorted(ts,t-600,side='left')
    res['act_7d'][j]=i0+1-np.searchsorted(ts,t-7*86400,side='left')
for k,v in res.items(): EV[k]=v
EV['activity_ratio']=EV.act_10m/np.maximum(EV.act_7d*600/(7*86400),1e-6)
EV['hours_to_end']=(EV.end-EV.ts)/3600
EV['eid9']=np.arange(len(EV))
EV.to_pickle('p9/events.pkl')
print('events',len(EV),'FAE',EV.is_FAE.sum(),'ACC',EV.is_ACC.sum(),'CONV',EV.is_CONV.sum(),EV.groupby('split').size().to_dict())
