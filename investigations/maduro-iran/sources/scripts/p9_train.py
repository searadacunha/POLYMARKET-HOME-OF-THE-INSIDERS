"""Phase 9 : sélection du lead score sur TRAIN uniquement (CV 5 plis groupés par marché), puis gel de la spécification."""
import numpy as np,pandas as pd,json,pickle
from sklearn.model_selection import GroupKFold
from sklearn.metrics import roc_auc_score
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
EV=pd.read_pickle('p9/events_out.pkl')
FEAT=['lusd','size_rank_mkt','rel_size_wallet','n_buys_30m','conc_dir','dpre_1m','dpre_10m','dpre_60m','act_10m','activity_ratio','p_before','hours_to_end','first_in_mkt','prior_trades_univ','hist_score','hist_n']
def X(df):
    x=df[FEAT].astype(float).copy()
    x['act_10m']=np.log1p(x.act_10m); x['activity_ratio']=np.log1p(x.activity_ratio.clip(lower=0)); x['hours_to_end']=np.log1p(x.hours_to_end.clip(lower=0))
    x['prior_trades_univ']=np.log1p(x.prior_trades_univ); x['hist_n']=np.log1p(x.hist_n)
    for c in ('politics','geo','macro'): x['cat_'+c]=(df.cat.fillna('').str.startswith({'politics':'election','geo':'geopolitics','macro':'macro'}[c])).astype(float)
    return x
TR=EV[(EV.split=='TRAIN')&EV.is_FAE&~EV.FOLLOW&EV.p_before.notna()].copy()
Xtr=X(TR); y=TR.LEAD60.values.astype(int); grp=TR.cid.values
med=Xtr.median()
def s1(x):  # poids égaux sur 5 composantes z-score (moyenne/écart-type TRAIN du pli)
    comp=pd.DataFrame({'a':x.size_rank_mkt,'b':x.rel_size_wallet,'c':x.n_buys_30m,'d':x.conc_dir,'e':-x.dpre_10m.abs()})
    return comp
res={}
gkf=GroupKFold(n_splits=5)
for name in ('S1_equal','S2_logit','S3_gbm','S4_sizerank'):
    aucs=[]
    for tri,tei in gkf.split(Xtr,y,grp):
        a,b=Xtr.iloc[tri],Xtr.iloc[tei]
        if name=='S1_equal':
            ca,cb=s1(a),s1(b); mu,sd=ca.mean(),ca.std().replace(0,1)
            sc=((cb-mu)/sd).fillna(0).sum(1).values
        elif name=='S2_logit':
            m=a.fillna(med); mu,sd=m.mean(),m.std().replace(0,1)
            lr=LogisticRegression(max_iter=2000,C=1.0).fit((m-mu)/sd,y[tri]); sc=lr.predict_proba((b.fillna(med)-mu)/sd)[:,1]
        elif name=='S3_gbm':
            g=HistGradientBoostingClassifier(random_state=9).fit(a,y[tri]); sc=g.predict_proba(b)[:,1]
        else: sc=b.size_rank_mkt.fillna(0.5).values
        aucs.append(roc_auc_score(y[tei],sc))
    res[name]=(float(np.mean(aucs)),float(np.std(aucs)))
    print(name,'AUC CV',round(np.mean(aucs),4),'±',round(np.std(aucs),4))
best=max(res,key=lambda k:res[k][0])
# gel : entraînement sur tout TRAIN
if best=='S3_gbm':
    model=HistGradientBoostingClassifier(random_state=9).fit(Xtr,y); sc=model.predict_proba(Xtr)[:,1]; extra={}
elif best=='S2_logit':
    m=Xtr.fillna(med); mu,sd=m.mean(),m.std().replace(0,1); model=LogisticRegression(max_iter=2000).fit((m-mu)/sd,y); sc=model.predict_proba((m-mu)/sd)[:,1]; extra={'mu':mu.to_dict(),'sd':sd.to_dict()}
elif best=='S1_equal':
    ca=s1(Xtr); mu,sd=ca.mean(),ca.std().replace(0,1); model=None; sc=((ca-mu)/sd).fillna(0).sum(1).values; extra={'mu':mu.to_dict(),'sd':sd.to_dict()}
else: model=None; sc=Xtr.size_rank_mkt.fillna(0.5).values; extra={}
thr=float(np.quantile(sc,0.95))
H=EV[(EV.split=='TRAIN')&EV.is_FAE&~EV.FOLLOW&(EV.hist_n>=5)]
hthr=float(np.quantile(H.hist_score,0.99)) if len(H) else 1.0
spec={'best':best,'cv':res,'alert_threshold_raw':thr,'hist_threshold':hthr,'features':FEAT,'median':med.to_dict(),'extra':extra,'theta':0.03,'p0':float(EV.attrs.get('p0',np.nan)) if hasattr(EV,'attrs') else None,
      'frozen_at':pd.Timestamp.utcnow().isoformat(),'train_n':int(len(TR)),'train_lead_rate':float(y.mean())}
WF=['lusd','size_rank_mkt','rel_size_wallet','n_buys_30m','conc_dir','first_in_mkt','prior_trades_univ','hist_score','hist_n']
aw=[]
for tri,tei in gkf.split(Xtr,y,grp):
    mw=HistGradientBoostingClassifier(random_state=9).fit(Xtr.iloc[tri][WF],y[tri]); aw.append(roc_auc_score(y[tei],mw.predict_proba(Xtr.iloc[tei][WF])[:,1]))
wmodel=HistGradientBoostingClassifier(random_state=9).fit(Xtr[WF],y); wsc=wmodel.predict_proba(Xtr[WF])[:,1]
spec['S5_wallet']={'features':WF,'cv_auc':float(np.mean(aw)),'alert_threshold':float(np.quantile(wsc,0.95))}
pickle.dump(wmodel,open('p9/frozen_model_wallet.pkl','wb'))
print('S5_wallet AUC CV',round(np.mean(aw),4),'thr',round(spec['S5_wallet']['alert_threshold'],5))
json.dump(spec,open('p9/frozen_spec.json','w'),indent=1,default=str); pickle.dump(model,open('p9/frozen_model.pkl','wb'))
print('BEST',best,'threshold',round(thr,5),'hist_thr',round(hthr,4),'train n',len(TR),'lead rate',round(y.mean(),4))
