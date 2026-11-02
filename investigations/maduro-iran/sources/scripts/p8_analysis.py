"""Phase 8 : mesure des résultats (après T) et évaluation hors échantillon des signaux pré-enregistrés."""
import json,os,bisect,collections
import numpy as np,pandas as pd
rng=np.random.default_rng(8)
OUT='/Users/benjamindacunha/Documents/Crypto/enquete_maduro_iran/phase8/'
S=pd.read_pickle('p8/sample_events.pkl')
FUND=pd.read_pickle('p8/funding_features.pkl') if os.path.exists('p8/funding_features.pkl') else None
if FUND is not None: S=S.merge(FUND,on='eid',how='left')
H={'5m':300,'15m':900,'30m':1800,'60m':3600,'6h':21600}
cache={}
def series(a):
    if a not in cache:
        fp=f'p8/prices/{a}.json'
        L=json.load(open(fp)) if os.path.exists(fp) else []
        cache[a]=([int(t) for t,p in L],[float(p) for t,p in L])
    return cache[a]
def last_le(ts,ps,t,lo=None):
    i=bisect.bisect_right(ts,t)-1
    if i<0 or (lo is not None and ts[i]<lo): return np.nan
    return ps[i]
recs=[]
for r in S.itertuples(index=False):
    ts,ps=series(r.asset); T=r.ts
    if not ts: recs.append({'eid':r.eid}); continue
    pT=last_le(ts,ps,T,T-600); p60=last_le(ts,ps,T-3600,T-4200); p15=last_le(ts,ps,T-900,T-1500)
    j=bisect.bisect_left(ts,T+60)
    pobs=ps[j] if j<len(ts) and ts[j]<=T+660 else np.nan; tobs=ts[j] if j<len(ts) else None
    d={'eid':r.eid,'p_T':pT,'p_obs':pobs,'momo_60':pT-p60 if not np.isnan(pT) else np.nan,'momo_15':pT-p15 if not np.isnan(pT) else np.nan}
    for k,h in H.items():
        ph=last_le(ts,ps,T+h,T+60)
        d['p_'+k]=ph
    if not np.isnan(pobs):
        k0=bisect.bisect_left(ts,T+60); k1=bisect.bisect_right(ts,T+21600)
        w=ps[k0:k1]
        if w:
            d['mfe_6h']=max(w)-pobs; d['mae_6h']=min(w)-pobs
            im=int(np.argmax(w)); d['t_mfe_min']=(ts[k0+im]-T)/60
    recs.append(d)
R=pd.DataFrame(recs); S=S.merge(R,on='eid',how='left')
for k in H: 
    S['ret_'+k]=S['p_'+k]-S.p_obs
    S['wallet_raw_'+k]=S['p_'+k]-S.price
S['ret_res']=S.win-S.p_obs
S['wallet_raw_res']=S.win-S.price
S['slip_obs']=S.p_obs-S.price
S['pbucket']=pd.cut(S.price,[0,0.2,0.5,0.8,1.0001],labels=['0-0.2','0.2-0.5','0.5-0.8','0.8-1'],include_lowest=True)
tr=S[(S.split=='TRAIN')&S.in_baseline].momo_60.dropna()
q1,q2=np.quantile(tr,[1/3,2/3]) if len(tr) else (0,0)
S['momo_t']=np.where(S.momo_60<=q1,'bas',np.where(S.momo_60<=q2,'moyen','haut'))
S.loc[S.momo_60.isna(),'momo_t']='NA'
SIG=['S_LARGE','S_LONGSHOT_LARGE','S_CONV','S_ACCUM','S_FIRST_LARGE','S_FRESH','S_FASTFUND','S_MOONPAY']
for s in SIG:
    if s not in S: S[s]=False
    S[s]=S[s].fillna(False).astype(bool)
S.to_pickle('p8/event_study.pkl')
def strat_diff(sig,base,col):
    """écart moyen signal - baseline, post-stratifié par tranche de prix × tercile de momentum (poids = signal)"""
    sig=sig.dropna(subset=[col]); base=base.dropna(subset=[col])
    if len(sig)==0: return np.nan
    tot=0; wsum=0
    for (pb,mt),g in sig.groupby(['pbucket','momo_t'],observed=True):
        b=base[(base.pbucket==pb)&(base.momo_t==mt)]
        if len(b)<10: continue
        tot+=len(g)*(g[col].mean()-b[col].mean()); wsum+=len(g)
    return tot/wsum if wsum else np.nan
def boot(sig,base,col,n=1000):
    """IC 95 % par bootstrap groupé par marché (rééchantillonnage des marchés, séparément signal et baseline)."""
    sig=sig.dropna(subset=[col]); base=base.dropna(subset=[col])
    if len(sig)==0: return (np.nan,np.nan)
    st=sorted(set(zip(sig.pbucket.astype(str),sig.momo_t)))
    key={k:i for i,k in enumerate(st)}
    def mats(df):
        df=df[[ (a,b) in key for a,b in zip(df.pbucket.astype(str),df.momo_t)]]
        ms=df.cid.unique(); mi={m:i for i,m in enumerate(ms)}
        Sm=np.zeros((len(ms),len(st))); Cm=np.zeros((len(ms),len(st)))
        for c,a,b,v in zip(df.cid,df.pbucket.astype(str),df.momo_t,df[col]):
            Sm[mi[c],key[(a,b)]]+=v; Cm[mi[c],key[(a,b)]]+=1
        return Sm,Cm
    Ss,Cs=mats(sig); Sb,Cb=mats(base)
    if len(Ss)==0 or len(Sb)==0: return (np.nan,np.nan)
    vals=[]
    for _ in range(n):
        a=rng.integers(0,len(Ss),len(Ss)); b=rng.integers(0,len(Sb),len(Sb))
        ss,cs=Ss[a].sum(0),Cs[a].sum(0); sb,cb=Sb[b].sum(0),Cb[b].sum(0)
        ok=(cs>0)&(cb>=10)
        if ok.sum()==0: continue
        vals.append(((ss[ok]/cs[ok]-sb[ok]/cb[ok])*cs[ok]).sum()/cs[ok].sum())
    v=np.array(vals)
    return (np.quantile(v,0.025),np.quantile(v,0.975)) if len(v)>100 else (np.nan,np.nan)
COSTS=[0.01,0.02]; COLS=['ret_5m','ret_15m','ret_30m','ret_60m','ret_6h','ret_res']
rows=[]; ntests=0
for sp in ('TRAIN','VALID','TEST'):
    base_all=S[(S.split==sp)&S.in_baseline]
    for s in SIG:
        pool=S[(S.split==sp)]
        if s in ('S_FRESH','S_FASTFUND','S_MOONPAY'):
            pool=pool[pool.in_fund_sample]; base=pool[~pool[s]]
        else:
            base=base_all[~base_all[s]]
        sig=pool[pool[s]]
        for col in COLS:
            for c in COSTS:
                ntests+=1
                x=sig[col].dropna()-c; b=base[col].dropna()-c
                dd=strat_diff(sig,base,col)
                lo,hi=(boot(sig,base,col) if col in ('ret_60m','ret_res') and c==0.01 and len(sig.dropna(subset=[col]))>=15 else (np.nan,np.nan))
                rows.append(dict(split=sp,signal=s,horizon=col.replace('ret_',''),cost_pp=c*100,n_sig=len(x),n_mkts=sig.dropna(subset=[col]).cid.nunique(),n_wallets=sig.dropna(subset=[col]).wallet.nunique(),
                    top_wallet_share=(sig.dropna(subset=[col]).wallet.value_counts().iloc[0]/len(x)) if len(x) else np.nan,
                    mean_net_sig=x.mean() if len(x) else np.nan,mean_net_base=b.mean() if len(b) else np.nan,hit_sig=(x>0).mean() if len(x) else np.nan,
                    diff_strat=dd,ci_lo=lo,ci_hi=hi,wallet_raw_mean=sig['wallet_raw_'+col.replace('ret_','')].mean() if len(sig) else np.nan,
                    momo60_sig=sig.momo_60.mean(),momo60_base=base.momo_60.mean(),slip_obs=sig.slip_obs.mean()))
BT=pd.DataFrame(rows); BT.to_csv(OUT+'backtest_results.csv',index=False)
# momentum terciles for primary endpoints
mrows=[]
for sp in ('TRAIN','VALID','TEST'):
    for s in SIG:
        pool=S[S.split==sp]
        base=(pool[pool.in_fund_sample&~pool[s]] if s in ('S_FRESH','S_FASTFUND','S_MOONPAY') else pool[pool.in_baseline&~pool[s]])
        if s in ('S_FRESH','S_FASTFUND','S_MOONPAY'): pool=pool[pool.in_fund_sample]
        sig=pool[pool[s]]
        for mt in ('bas','moyen','haut'):
            for col in ('ret_60m','ret_res'):
                a=sig[sig.momo_t==mt][col].dropna(); b=base[base.momo_t==mt][col].dropna()
                mrows.append(dict(split=sp,signal=s,momo_tercile=mt,horizon=col,n_sig=len(a),diff=(a.mean()-b.mean()) if len(a) and len(b) else np.nan))
MT=pd.DataFrame(mrows)
# classification
cls=[]
for s in SIG:
    d={}
    for sp in ('TRAIN','VALID','TEST'):
        for hz in ('60m','res'):
            r=BT[(BT.split==sp)&(BT.signal==s)&(BT.horizon==hz)&(BT.cost_pp==1.0)]
            d[(sp,hz)]=r.iloc[0] if len(r) else None
    def ok(sp,hz):
        r=d[(sp,hz)]
        return r is not None and r.n_sig>=30 and r.n_mkts>=10 and r.n_wallets>=10 and (r.top_wallet_share<=0.2) and r.ci_lo>0
    def pos(sp,hz):
        r=d[(sp,hz)]; return r is not None and r.n_sig>=15 and r.diff_strat>0
    def momo_ok(hz):
        m=MT[(MT.signal==s)&(MT.horizon=='ret_'+hz)&(MT.split.isin(['VALID','TEST']))&(MT.n_sig>=5)]
        return len(m)>0 and (m['diff']>0).all()
    conf=[hz for hz in ('60m','res') if ok('VALID',hz) and ok('TEST',hz) and momo_ok(hz)]
    if conf: c='SIGNAL CONFIRMÉ'
    elif any(pos('VALID',hz) and pos('TEST',hz) for hz in ('60m','res')): c='SIGNAL PROMETTEUR'
    elif any((d[('VALID',hz)] is not None and d[('VALID',hz)].wallet_raw_mean>0 and d[('VALID',hz)].diff_strat<=0) for hz in ('60m','res')): c='SIGNAL NON CAPTURABLE / NON REPRODUCTIBLE'
    else: c='AUCUN SIGNAL'
    tr=d[('TRAIN','60m')]
    cls.append(dict(signal=s,classification=c,**{f'{sp}_{hz}_n':(d[(sp,hz)].n_sig if d[(sp,hz)] is not None else 0) for sp in ('TRAIN','VALID','TEST') for hz in ('60m','res')},
        **{f'{sp}_{hz}_diff':(round(d[(sp,hz)].diff_strat,4) if d[(sp,hz)] is not None else np.nan) for sp in ('TRAIN','VALID','TEST') for hz in ('60m','res')},
        **{f'{sp}_{hz}_ci':(f"[{d[(sp,hz)].ci_lo:.4f};{d[(sp,hz)].ci_hi:.4f}]" if d[(sp,hz)] is not None else '') for sp in ('TRAIN','VALID','TEST') for hz in ('60m','res')}))
CL=pd.DataFrame(cls); CL.to_csv(OUT+'signals.csv',index=False)
BT[BT.split.isin(['VALID','TEST'])&BT.horizon.isin(['60m','res'])].to_csv(OUT+'out_of_sample_results.csv',index=False)
MT.to_csv(OUT+'momentum_control.csv',index=False)
# price impact path
pi=[]
for sp in ('TRAIN','VALID','TEST'):
    for s in SIG+['BASELINE']:
        g=S[(S.split==sp)&(S.in_baseline if s=='BASELINE' else S[s])]
        pi.append(dict(split=sp,group=s,n=len(g),momo_60=g.momo_60.mean(),momo_15=g.momo_15.mean(),slip_obs=g.slip_obs.mean(),
            **{f'd_{k}':(g['p_'+k]-g.p_T).mean() for k in H},**{f'ret_{k}':g['ret_'+k].mean() for k in H},ret_res=g.ret_res.mean(),mfe_6h=g.mfe_6h.mean(),mae_6h=g.mae_6h.mean(),t_mfe_min=g.t_mfe_min.median()))
pd.DataFrame(pi).to_csv(OUT+'price_impact.csv',index=False)
cols=['eid','split','cid','cat','wallet','popA','asset','ts','price','usd','size_rank_mkt','first_in_mkt','prior_trades_univ','conv_30m','accum','hours_to_end','momo_60','p_T','p_obs','slip_obs']+['p_'+k for k in H]+['ret_'+k for k in H]+['ret_res','win','mfe_6h','mae_6h','t_mfe_min','in_baseline','in_fund_sample']+[c for c in ('wallet_age_h','last_funding_min','funding_src','moonpay_funded') if c in S]+SIG
S[[c for c in cols if c in S]].to_csv(OUT+'event_study.csv',index=False)
print('tests',ntests); print(CL[['signal','classification','VALID_60m_n','VALID_60m_diff','TEST_60m_n','TEST_60m_diff','VALID_res_diff','TEST_res_diff']].to_string())
