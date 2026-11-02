"""Phase 9 : backtest historique du détecteur (spécifications FIGÉES, frozen_spec.json) sur TRAIN / VALID / TEST.
Les signaux évalués ici sont exactement ceux qu'émet p9_detector.py en flux : concordance vérifiée trade par trade
(phase9/detector_concordance.csv : SIG_HIST, SIG_ACC, SIG_CONV 100 %, SIG_WALLET, SIG_CTX, SIG_NEW >= 99,98 %).
Ordre d'exécution (depuis le dossier de données contenant p8/ et p9/) :
  p9_features.py -> p9_outcomes.py -> p9_history.py -> p9_train.py (gel) -> p9_backtest.py -> p9_exec.py -> p9_extra.py
  -> p9_freeze_ctx.py -> p9_detector.py --verify -> p9_consolide.py -> p9_cas_maduro_iran.py
Contenu : uplift contre contrôle A apparié sur le contexte, contrôle E, AUC hors échantillon, strates H3 et catégories."""
import numpy as np,pandas as pd,json,pickle,collections
from scipy.stats import binomtest,norm
from sklearn.metrics import roc_auc_score
from sklearn.ensemble import HistGradientBoostingClassifier
OUT='/Users/benjamindacunha/Documents/Crypto/enquete_maduro_iran/phase9/'
rng=np.random.default_rng(9)
spec=json.load(open('p9/frozen_spec.json')); m3=pickle.load(open('p9/frozen_model.pkl','rb')); m5=pickle.load(open('p9/frozen_model_wallet.pkl','rb'))
exec(open('p9_train.py').read().split("TR=EV[")[0].split("EV=pd.read_pickle")[0])  # imports
src=open('p9_train.py').read(); exec(src[src.index('FEAT='):src.index("TR=EV[")])       # FEAT + X()
EV=pd.read_pickle('p9/events_out.pkl')
ok=EV.p_before.notna()
Xa=X(EV); EV['score_ctx']=np.nan; EV['score_wallet']=np.nan
EV.loc[ok,'score_ctx']=m3.predict_proba(Xa[ok])[:,1]
WF=spec['S5_wallet']['features']; EV.loc[ok,'score_wallet']=m5.predict_proba(Xa.loc[ok,WF])[:,1]
# score ajusté au marché : rang parmi les FAE antérieurs du même marché (>=20)
EV=EV.sort_values('ts').reset_index(drop=True)
ok=EV.p_before.notna()
adj=np.full(len(EV),np.nan)
import bisect
for cid,g in EV[EV.is_FAE&ok].groupby('cid',sort=False):
    past=[]
    for i,s in zip(g.index.values,g.score_ctx.values):
        if len(past)>=20: adj[i]=bisect.bisect_left(past,s)/len(past)
        bisect.insort(past,s)
EV['score_ctx_market_adj']=adj
# modèle de contexte seul (TRAIN) = taux attendu pour le classement des wallets et les contrôles
CTX=['dpre_1m','dpre_10m','dpre_60m','act_10m','activity_ratio','p_before','hours_to_end','cat_politics','cat_geo','cat_macro']
trm=(EV.split=='TRAIN')&EV.is_FAE&~EV.FOLLOW&ok
Xa=X(EV)
mctx=HistGradientBoostingClassifier(random_state=9).fit(Xa.loc[trm,CTX],EV.loc[trm,'LEAD60'].astype(int))
EV['p_ctx']=np.nan; EV.loc[ok,'p_ctx']=mctx.predict_proba(Xa.loc[ok,CTX])[:,1]
# strates de contexte (contrôle A apparié)
EV['pbin']=np.clip((EV.p_before*10).fillna(-1).astype(int),-1,9)
EV['htb']=pd.cut(EV.hours_to_end,[-1e9,1,6,24,168,1e12],labels=False)
EV['actb']=pd.cut(EV.act_10m,[-1,0,1,4,1e9],labels=False)
EV['stratum']=EV.split+'|'+EV.pbin.astype(str)+'|'+EV.htb.astype(str)+'|'+EV.actb.astype(str)
BASE=EV.is_FAE&~EV.FOLLOW&ok
thr=spec['alert_threshold_raw']; wthr=spec['S5_wallet']['alert_threshold']; hthr=spec['hist_threshold']
SIG={'SIG_CTX':BASE&(EV.score_ctx>=thr),'SIG_WALLET':BASE&(EV.score_wallet>=wthr),'SIG_ACC':EV.is_ACC&~EV.FOLLOW&ok,'SIG_CONV':EV.is_CONV&~EV.FOLLOW&ok,
     'SIG_HIST':BASE&(EV.hist_n>=5)&(EV.hist_score>=hthr),'SIG_NEW':BASE&(EV.prior_trades_univ<=2)&(EV.score_wallet>=wthr)}
first_ts=EV.groupby('cid').ts.transform('min'); EV['new_market']=first_ts>=int(pd.Timestamp('2026-03-01',tz='UTC').timestamp())
# ---------- uplift apparié + bootstrap groupé par marché
def uplift(sig,col,n_boot=500):
    s=EV[sig]; c=EV[BASE&~sig]
    cm=c.groupby('stratum')[col].agg(['mean','size']); cm=cm[cm['size']>=20]
    s=s[s.stratum.isin(cm.index)]
    if len(s)==0: return (np.nan,np.nan,np.nan,0,np.nan,np.nan)
    d=(s[col].values-cm.loc[s.stratum,'mean'].values)
    est=d.mean()
    mk=s.cid.values; um=np.unique(mk); idx={m:np.nonzero(mk==m)[0] for m in um}
    bs=[]
    for _ in range(n_boot):
        pick=rng.choice(um,len(um)); ii=np.concatenate([idx[m] for m in pick]); bs.append(d[ii].mean())
    return (est,np.quantile(bs,0.025),np.quantile(bs,0.975),len(s),s[col].mean(),cm.loc[s.stratum,'mean'].mean())
rows=[]
for name,m in SIG.items():
    for sp in ('TRAIN','VALID','TEST'):
        mm=m&(EV.split==sp)
        for col in ('LEAD60','dpost_60m','dpost_10m'):
            e,lo,hi,n,ms,mc=uplift(mm,col if col!='LEAD60' else 'LEAD60')
            rows.append(dict(signal=name,split=sp,metric=col,n=n,n_markets=EV[mm].cid.nunique(),n_wallets=EV[mm].wallet.nunique(),signal_mean=ms,control_A_matched_mean=mc,uplift=e,ci_lo=lo,ci_hi=hi,
                ctrlE_LEAD60=EV[mm].ctrlE_LEAD60.mean(),dpre_60m_mean=EV[mm].dpre_60m.mean(),top_wallet_share=(EV[mm].wallet.value_counts().iloc[0]/mm.sum()) if mm.sum() else np.nan))
UP=pd.DataFrame(rows)
for c in ('LEAD60',): EV[c]=EV[c].astype(float)
# ---------- AUC hors échantillon
auc=[]
for sp in ('TRAIN','VALID','TEST'):
    b=EV[BASE&(EV.split==sp)]
    for sc in ('score_ctx','score_wallet','p_ctx','hist_score','size_rank_mkt'):
        x=b[[sc,'LEAD60']].dropna()
        if x.LEAD60.nunique()==2: auc.append(dict(split=sp,score=sc,n=len(x),auc=roc_auc_score(x.LEAD60,x[sc])))
    nw=b[b.prior_trades_univ<=2][['score_wallet','LEAD60']].dropna()
    if nw.LEAD60.nunique()==2: auc.append(dict(split=sp,score='score_wallet|nouveaux wallets',n=len(nw),auc=roc_auc_score(nw.LEAD60,nw.score_wallet)))
    kw=b[b.hist_n>=10][['hist_score','LEAD60']].dropna()
    if kw.LEAD60.nunique()==2: auc.append(dict(split=sp,score='hist_score|wallets connus (>=10)',n=len(kw),auc=roc_auc_score(kw.LEAD60,kw.hist_score)))
AUC=pd.DataFrame(auc)
# ---------- H3 / strates
h3=[]
for name,m in SIG.items():
    for sp in ('VALID','TEST'):
        for lab,cond in (('activité calme',EV.act_10m<=EV[EV.split=='TRAIN'].act_10m.median()),('sans mouvement préalable',EV.dpre_10m.abs()<0.005),('nouveaux marchés',EV.new_market)):
            e,lo,hi,n,ms,mc=uplift(m&(EV.split==sp)&cond,'LEAD60',n_boot=300)
            h3.append(dict(signal=name,split=sp,strate=lab,n=n,uplift_LEAD60=e,ci_lo=lo,ci_hi=hi))
        for cat,g in EV[m&(EV.split==sp)].groupby('cat'):
            e,lo,hi,n,ms,mc=uplift(m&(EV.split==sp)&(EV.cat==cat),'LEAD60',n_boot=300)
            h3.append(dict(signal=name,split=sp,strate='catégorie '+str(cat),n=n,uplift_LEAD60=e,ci_lo=lo,ci_hi=hi))
H3=pd.DataFrame(h3)
EV.to_pickle('p9/events_scored.pkl')
UP.to_csv(OUT+'out_of_sample_results.csv',index=False); AUC.to_csv(OUT+'auc_hors_echantillon.csv',index=False); H3.to_csv(OUT+'strates_h3_categories.csv',index=False)
pd.set_option('display.width',250)
print(UP[UP.metric=='LEAD60'][['signal','split','n','n_markets','n_wallets','signal_mean','control_A_matched_mean','uplift','ci_lo','ci_hi','ctrlE_LEAD60','dpre_60m_mean','top_wallet_share']].round(4).to_string())
print(UP[UP.metric=='dpost_60m'][['signal','split','n','uplift','ci_lo','ci_hi']].round(4).to_string())
print(AUC.round(4).to_string())
