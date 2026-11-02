"""Phase 9 : exécution simulée d'un observateur après le signal (latence L, taille S), sortie à T+H,
au prix des achats / ventes réellement exécutés par d'autres wallets (proxy ask / bid). Signal contre contrôle apparié (même strate)."""
import numpy as np,pandas as pd,json
OUT='/Users/benjamindacunha/Documents/Crypto/enquete_maduro_iran/phase9/'
rng=np.random.default_rng(9)
spec=json.load(open('p9/frozen_spec.json'))
EV=pd.read_pickle('p9/events_scored.pkl'); P=pd.read_pickle('p9/prints.pkl')
wcode={w:i for i,w in enumerate(P.wallet.unique())}; P['wc']=P.wallet.map(wcode).astype(np.int64)
P['shares']=P.usd/P.price
M={cid:(g.ts.values,g.p_yes.values,g.wc.values,g.buyeq_yes.values,g.shares.values) for cid,g in P.groupby('cid',sort=False)}
HS=0.01
def fee(p,sh,on): return 0.02*min(p,1-p)*sh if on else 0.0
def sim(cid,T,d,w,L,S,H):
    ts,py,wc,bey,sh=M[cid]
    pd_=py if d==0 else 1-py; buyeq=bey if d==0 else ~bey
    a=np.searchsorted(ts,T+L,side='left'); b=np.searchsorted(ts,T+L+600,side='right')
    idx=[i for i in range(a,b) if buyeq[i] and wc[i]!=w]
    need=S; shares=0.0; pe_last=None
    for i in idx:
        notional=pd_[i]*sh[i]; take=min(notional,need); shares+=take/pd_[i]; need-=take; pe_last=pd_[i]
        if need<=1e-9: break
    if need>1e-9: return None
    entry=S/shares
    a2=np.searchsorted(ts,T+H,side='left'); b2=np.searchsorted(ts,T+H+600,side='right')
    left=shares; proceeds=0.0
    for i in range(a2,b2):
        if (not buyeq[i]) and wc[i]!=w:
            q=min(sh[i],left); proceeds+=q*pd_[i]; left-=q
            if left<=1e-9: break
    partial=left>1e-9
    if partial:
        k=np.searchsorted(ts,T+H,side='right')-1
        last=pd_[k] if k>=0 else entry
        proceeds+=left*max(last-HS,0.0)
    exitp=proceeds/shares
    g=(exitp-entry)/entry
    net_fee=(proceeds-S-fee(entry,shares,True)-fee(exitp,shares,True))/S
    net_nofee=(proceeds-S)/S
    return entry,exitp,g,net_fee,net_nofee,partial
BASE=EV.is_FAE&~EV.FOLLOW&EV.p_before.notna()
thr=spec['alert_threshold_raw']; wthr=spec['S5_wallet']['alert_threshold']; hthr=spec['hist_threshold']
SIG={'SIG_HIST':BASE&(EV.hist_n>=5)&(EV.hist_score>=hthr),'SIG_WALLET':BASE&(EV.score_wallet>=wthr),'SIG_CTX':BASE&(EV.score_ctx>=thr),
     'SIG_CONV':EV.is_CONV&~EV.FOLLOW&EV.p_before.notna(),'SIG_ACC':EV.is_ACC&~EV.FOLLOW&EV.p_before.notna(),'SIG_NEW':BASE&(EV.prior_trades_univ<=2)&(EV.score_wallet>=wthr)}
Lats=[1,5,10,30,60,300]; Sizes=[100,500,1000,5000,10000]
strat=EV[BASE].groupby('stratum').groups
rows=[]; det=[]
for name,m in SIG.items():
    for sp in ('TRAIN','VALID','TEST'):
        g=EV[m&(EV.split==sp)]
        if len(g)>3000: g=g.sample(3000,random_state=9)
        # contrôle apparié : un FAE non-FOLLOW non signalé de la même strate
        ctl=[]
        for s in g.stratum.values:
            pool=strat.get(s)
            ctl.append(rng.choice(pool) if pool is not None and len(pool) else None)
        C=EV.loc[[c for c in ctl if c is not None]]
        for grp_name,G in (('signal',g),('controle_A',C)):
            for L in Lats:
                for S in Sizes:
                    if grp_name=='controle_A' and not (S==500): continue
                    res=[sim(r.cid,r.ts,r.d,wcode.get(r.wallet,-1),L,S,3600) for r in G.itertuples(index=False)]
                    ok=[x for x in res if x is not None]
                    net=np.array([x[3] for x in ok]); nn=np.array([x[4] for x in ok]); gr=np.array([x[2] for x in ok])
                    if len(net)>=10:
                        bs=[net[rng.integers(0,len(net),len(net))].mean() for _ in range(300)]; lo,hi=np.quantile(bs,[0.025,0.975])
                    else: lo=hi=np.nan
                    rows.append(dict(signal=name,split=sp,groupe=grp_name,latence_s=L,taille_usd=S,n_evenements=len(G),part_executable=len(ok)/max(len(G),1),
                        gross_moy=gr.mean() if len(gr) else np.nan,net_frais_moy=net.mean() if len(net) else np.nan,net_frais_ci_lo=lo,net_frais_ci_hi=hi,net_sans_frais_moy=nn.mean() if len(nn) else np.nan,
                        part_net_positif=(net>0).mean() if len(net) else np.nan,sortie_partielle=np.mean([x[5] for x in ok]) if ok else np.nan))
                    if grp_name=='signal' and L==60 and S==500:
                        for r,x in zip(G.itertuples(index=False),res):
                            det.append(dict(eid9=r.eid9,entry_60s_500=x[0] if x else np.nan,exit_60m=x[1] if x else np.nan,net_60s_500=x[3] if x else np.nan,executable=x is not None))
        print(name,sp,'done',flush=True)
X=pd.DataFrame(rows); X.to_csv(OUT+'execution_simulation.csv',index=False)
pd.DataFrame(det).drop_duplicates('eid9').to_pickle('p9/exec_detail.pkl')
pd.set_option('display.width',250)
print(X[(X.taille_usd==500)&(X.latence_s.isin([1,10,60,300]))][['signal','split','groupe','latence_s','n_evenements','part_executable','gross_moy','net_frais_moy','net_frais_ci_lo','net_frais_ci_hi','net_sans_frais_moy']].round(4).to_string())
