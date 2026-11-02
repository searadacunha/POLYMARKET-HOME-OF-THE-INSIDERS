"""Phase 9 : lead-time, classement des wallets (observé vs attendu par le contexte, BH), convergence (1er wallet), nouveaux wallets,
test copy-trading, population A, alertes, tables livrables."""
import numpy as np,pandas as pd,json,collections
from scipy.stats import norm
OUT='/Users/benjamindacunha/Documents/Crypto/enquete_maduro_iran/phase9/'
spec=json.load(open('p9/frozen_spec.json'))
EV=pd.read_pickle('p9/events_scored.pkl')
EXD=pd.read_pickle('p9/exec_detail.pkl')
EV=EV.merge(EXD,on='eid9',how='left')
EV['impact_own']=EV.price-EV.p_before; EV['move_after_exec']=EV.p_before+EV.dpost_60m-EV.price
BASE=EV.is_FAE&~EV.FOLLOW&EV.p_before.notna()
thr=spec['alert_threshold_raw']; wthr=spec['S5_wallet']['alert_threshold']; hthr=spec['hist_threshold']
SIG={'SIG_HIST':BASE&(EV.hist_n>=5)&(EV.hist_score>=hthr),'SIG_WALLET':BASE&(EV.score_wallet>=wthr),'SIG_CTX':BASE&(EV.score_ctx>=thr),
     'SIG_CONV':EV.is_CONV&~EV.FOLLOW&EV.p_before.notna(),'SIG_ACC':EV.is_ACC&~EV.FOLLOW&EV.p_before.notna(),'SIG_NEW':BASE&(EV.prior_trades_univ<=2)&(EV.score_wallet>=wthr)}
for k,m in SIG.items(): EV[k]=m
# ---- lead-time
lt=[]
for k,m in SIG.items():
    for sp in ('TRAIN','VALID','TEST'):
        g=EV[m&(EV.split==sp)&EV.LEAD60.astype(bool)]
        x=g.lead_time_s.dropna(); y=g.t_complete_s.dropna()
        if len(x): lt.append(dict(signal=k,split=sp,n_lead=len(g),lead_time_p25=x.quantile(.25),lead_time_med=x.median(),lead_time_p75=x.quantile(.75),lead_time_p90=x.quantile(.9),
                                  complete_med=y.median(),part_debut_avant_60s=(x<=60).mean(),part_debut_avant_300s=(x<=300).mean()))
LT=pd.DataFrame(lt); LT.to_csv(OUT+'lead_time.csv',index=False)
# ---- classement des wallets : LEAD60 observé vs attendu (modèle de contexte p_ctx, figé TRAIN)
F=EV[BASE].copy()
def zp(obs,exp,var):
    z=(obs-exp)/np.sqrt(np.maximum(var,1e-9)); return z,1-norm.cdf(z)
W=[]
for w,g in F.groupby('wallet'):
    tr=g[g.split=='TRAIN']; oo=g[g.split!='TRAIN']
    if len(tr)<5: continue
    z,p=zp(tr.LEAD60.sum(),tr.p_ctx.sum(),(tr.p_ctx*(1-tr.p_ctx)).sum())
    z2,p2=(zp(oo.LEAD60.sum(),oo.p_ctx.sum(),(oo.p_ctx*(1-oo.p_ctx)).sum()) if len(oo)>=3 else (np.nan,np.nan))
    allw=EV[EV.wallet==w] if False else None
    W.append(dict(wallet=w,n_train=len(tr),lead_train=int(tr.LEAD60.sum()),exp_train=tr.p_ctx.sum(),z_train=z,p_train=p,n_oos=len(oo),lead_oos=int(oo.LEAD60.sum()) if len(oo) else 0,exp_oos=oo.p_ctx.sum() if len(oo) else np.nan,
                  z_oos=z2,p_oos=p2,move_after_exec_oos=oo.move_after_exec.mean() if len(oo) else np.nan,impact_own_oos=oo.impact_own.mean() if len(oo) else np.nan,net_60s_500_oos=oo.net_60s_500.mean() if len(oo) else np.nan,
                  n_net_oos=oo.net_60s_500.notna().sum() if len(oo) else 0,usd_median=g.usd.median()))
W=pd.DataFrame(W)
# FOLLOWER : part d'événements FAE FOLLOW
fol=EV[EV.is_FAE&EV.p_before.notna()].groupby('wallet').FOLLOW.mean(); W['follow_share']=W.wallet.map(fol)
W=W.sort_values('p_train'); m=len(W); W['bh_rank']=np.arange(1,m+1); W['bh_crit']=0.10*W.bh_rank/m
cut=W[W.p_train<=W.bh_crit].bh_rank.max() if (W.p_train<=W.bh_crit).any() else 0
W['candidat_TRAIN']=W.bh_rank<=cut
def cls(r):
    if r.follow_share>=0.5: return 'FOLLOWER'
    if not r.candidat_TRAIN: return 'NO_LEAD'
    if r.n_oos>=3 and r.p_oos<0.05:
        return 'ACTIONABLE_LEAD (UNKNOWN_CAUSE)' if (r.n_net_oos>=3 and r.net_60s_500_oos>0) else 'PERSISTENT_LEAD (UNKNOWN_CAUSE)'
    return 'EARLY_FLOW'
W['classe']=W.apply(cls,axis=1)
W.to_csv(OUT+'wallet_lead_scores.csv',index=False)
print('wallets classés',len(W),W.classe.value_counts().to_dict())
# ---- test copy-trading : suiveurs récurrents derrière les wallets SIG_HIST
P=pd.read_pickle('p9/prints.pkl')
buys=P[(P.side=='BUY')][['asset','ts','wallet']]
bya={a:(g.ts.values,g.wallet.values) for a,g in buys.groupby('asset')}
def followers(r,win=600):
    ts,wl=bya.get(r.asset,(np.array([]),np.array([])))
    i=np.searchsorted(ts,r.ts,side='right'); j=np.searchsorted(ts,r.ts+win,side='right')
    return set(wl[i:j])-{r.wallet}
cp=[]
for lab,m in (('SIG_HIST',SIG['SIG_HIST']),('contrôle : FAE même wallet-taille (établis, non SIG_HIST)',BASE&(EV.hist_n>=5)&(EV.hist_score<hthr))):
    g=EV[m&(EV.split!='TRAIN')]
    if len(g)>4000: g=g.sample(4000,random_state=9)
    rec=[];tot=0
    for w,gg in g.groupby('wallet'):
        seen=collections.Counter()
        for r in gg.itertuples(index=False):
            f=followers(r); tot+=1
            rec.append(sum(1 for x in f if seen[x]>=1)/max(len(f),1) if f else np.nan)
            for x in f: seen[x]+=1
    cp.append(dict(groupe=lab,n_events=tot,part_suiveurs_deja_vus_derriere_ce_wallet=np.nanmean(rec)))
CP=pd.DataFrame(cp); print(CP.to_string())
# ---- convergence : le 1er wallet a-t-il une avance ?
C=EV[EV.is_CONV&EV.p_before.notna()].copy()
C['lead_premier_wallet']=C.d_t1_to_T  # mouvement entre 1er et 3e wallet
C[['split','cid','asset','wallet','conv_t1','ts','conv_nwallets_10m','dpre10_t1','d_t1_to_T','dpre_10m','dpost_10m','dpost_60m','LEAD60','FOLLOW','impact_own']].to_csv(OUT+'convergence_events.csv',index=False)
cv=C.groupby('split').agg(n=('ts','size'),delai_1er_3e_med_s=('ts',lambda s:(s-C.loc[s.index,'conv_t1']).median()),mvt_avant_1er=('dpre10_t1','mean'),mvt_1er_a_3e=('d_t1_to_T','mean'),mvt_apres_3e_60m=('dpost_60m','mean'),follow_share=('FOLLOW','mean'))
print(cv.round(4).to_string())
# ---- nouveaux wallets : rang du trade (1er, 2e, 3e) et quintile de score_wallet
nw=EV[BASE&(EV.prior_trades_univ<=2)&(EV.split!='TRAIN')].copy()
nw['q']=pd.qcut(nw.score_wallet.rank(method='first'),5,labels=[1,2,3,4,5])
NW=nw.groupby(['split','prior_trades_univ','q'],observed=True).agg(n=('LEAD60','size'),lead60=('LEAD60','mean'),p_ctx=('p_ctx','mean'),mvt_apres_exec=('move_after_exec','mean')).reset_index()
NW['lead60_moins_attendu']=NW.lead60-NW.p_ctx
NW.to_csv(OUT+'new_wallet_test.csv',index=False)
# ---- population A
A={'0x168b100d7a6620a2f49a455344c2c006eaf1714b':'Chiwawas','0x5621116629c5d640c8186f577362478cc6605245':'TacticalInsiderNews','0x38745db27f7360a287f6ca3c9b6a6a9c76149801':'Planktonbets','0x60280beffdfeaf962de4e6397ab49ed05a1b99e1':'X34','0x834079f62fa9b4b0bdfad5b8b7a841e8267da024':'chileno777','0xbf32f7a77ccea8bba647fea63d438ce1778b1762':'154x838hjd6','0x56efadc9defe5b7a21af751e0d026f2cf54136db':'Neodbs','0xe9b80c387ba77a585423b13c850c2e126c3befd8':'Mrs.Joker'}
PA=EV[EV.wallet.isin(A)].copy(); PA['compte']=PA.wallet.map(A)
PA=PA[['compte','split','cid','ts','usd','price','p_before','impact_own','dpre_10m','dpost_1m','dpost_10m','dpost_60m','move_after_exec','LEAD60','FOLLOW','score_ctx','score_wallet','hist_n','hist_score','is_FAE','is_ACC','is_CONV']+list(SIG)]
PA['ts']=pd.to_datetime(PA.ts,unit='s',utc=True); PA.to_csv(OUT+'population_A_signature.csv',index=False)
print(PA[['compte','ts','usd','price','p_before','dpre_10m','dpost_60m','move_after_exec','LEAD60','score_wallet','hist_n']+[k for k in SIG]].round(3).to_string())
# ---- tables livrables
keep=['eid9','split','cid','cat','asset','wallet','ts','d','price','usd','p_before','impact_own','dpre_10s','dpre_30s','dpre_1m','dpre_5m','dpre_10m','dpre_30m','dpre_60m','act_10m','activity_ratio','hours_to_end','size_rank_mkt','rel_size_wallet','n_buys_30m','conc_dir','first_in_mkt','prior_trades_univ','hist_n','hist_score','score_ctx','score_ctx_market_adj','score_wallet','p_ctx']+\
     ['dpost_5s','dpost_10s','dpost_30s','dpost_1m','dpost_5m','dpost_10m','dpost_30m','dpost_60m','obs_5s','obs_10s','obs_30s','obs_1m','obs_5m','obs_10m','n_other_60m','mfe_60m','mae_60m','lead_time_s','t_complete_s','move_after_exec','FOLLOW','LEAD60','ctrlE_LEAD60','win','is_FAE','is_ACC','is_CONV']+list(SIG)
anyS=np.zeros(len(EV),dtype=bool)
for k in SIG: anyS|=EV[k].values
MS=pd.concat([EV[anyS],EV[BASE&~anyS].sample(20000,random_state=9)])
MS[keep].to_csv(OUT+'microstructure_features.csv',index=False)
EV[(EV.split!='TRAIN')][['eid9','split','cid','cat','wallet','ts','d','price','usd','p_before','is_FAE','is_ACC','is_CONV','FOLLOW','LEAD60','dpre_10m','dpost_10m','dpost_60m','move_after_exec','score_ctx','score_wallet','hist_score','hist_n']+list(SIG)].to_csv(OUT+'wallet_market_events.csv',index=False)
AL=[]
for k in SIG:
    g=EV[EV[k]&(EV.split!='TRAIN')]
    for r in g.itertuples(index=False):
        AL.append(dict(timestamp=pd.to_datetime(r.ts,unit='s',utc=True),split=r.split,market=r.cid,wallet=r.wallet,signal=k,signal_score=r.hist_score if k=='SIG_HIST' else (r.score_ctx if k=='SIG_CTX' else r.score_wallet),
            price_at_signal=r.p_before,price_paid_by_wallet=r.price,price_5s=r.p_before+r.dpost_5s,price_10s=r.p_before+r.dpost_10s,price_30s=r.p_before+r.dpost_30s,price_1m=r.p_before+r.dpost_1m,price_5m=r.p_before+r.dpost_5m,
            price_60m=r.p_before+r.dpost_60m,max_favorable=r.mfe_60m,max_adverse=r.mae_60m,lead_time=r.lead_time_s,observer_entry_60s_500usd=r.entry_60s_500,net_return_60s_500usd_fees=r.net_60s_500))
pd.DataFrame(AL).to_csv(OUT+'alerts.csv',index=False)
EV.to_pickle('p9/events_final.pkl')
print(LT.round(1).to_string())
