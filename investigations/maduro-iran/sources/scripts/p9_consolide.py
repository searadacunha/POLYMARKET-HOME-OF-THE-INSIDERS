"""Phase 9 : table consolidée backtest_results.csv (un signal x split par ligne) et critères du §23 (criteres_23.csv).
Réutilise les sorties de p9_backtest.py / p9_exec.py / p9_extra.py ; ajoute les contrôles B, C, D et la sensibilité au seuil (2 et 5 points).
Aucun paramètre n'est choisi ici : seuils et définitions sont ceux figés dans PROTOCOLE_P9.md."""
import sys, os, numpy as np, pandas as pd
OUT = os.path.expanduser('~/Documents/Crypto/enquete_maduro_iran/phase9/')
os.chdir(sys.argv[1])
rng = np.random.default_rng(9)
EV = pd.read_pickle('p9/events_final.pkl')
SIGS = ['SIG_HIST', 'SIG_WALLET', 'SIG_CTX', 'SIG_CONV', 'SIG_ACC', 'SIG_NEW']
ok = EV.p_before.notna()
BASE = EV.is_FAE & ~EV.FOLLOW & ok
for c in ('LEAD60', 'LEAD60_2pp', 'LEAD60_5pp'):
    EV[c] = EV[c].astype(float)
med_hist = EV[BASE & (EV.split == 'TRAIN')].hist_score.median()


def matched(sig, pool, col, n_boot=300):
    """Écart moyen signal - moyenne de la même strate dans le pool (>= 20 obs), IC bootstrap groupé par marché."""
    s = EV[sig]
    cm = EV[pool].groupby('stratum')[col].agg(['mean', 'size'])
    cm = cm[cm['size'] >= 20]
    s = s[s.stratum.isin(cm.index)]
    if len(s) < 10:
        return np.nan, np.nan, np.nan, len(s)
    d = s[col].values - cm.loc[s.stratum, 'mean'].values
    mk = s.cid.values
    um = np.unique(mk)
    idx = {m: np.nonzero(mk == m)[0] for m in um}
    bs = [d[np.concatenate([idx[m] for m in rng.choice(um, len(um))])].mean() for _ in range(n_boot)]
    return d.mean(), np.quantile(bs, .025), np.quantile(bs, .975), len(s)


UP = pd.read_csv(OUT + 'out_of_sample_results.csv')
XS = pd.read_csv(OUT + 'execution_simulation.csv')
LT = pd.read_csv(OUT + 'lead_time.csv')
AUC = pd.read_csv(OUT + 'auc_hors_echantillon.csv')
aucmap = {'SIG_CTX': 'score_ctx', 'SIG_WALLET': 'score_wallet', 'SIG_HIST': 'hist_score|wallets connus (>=10)', 'SIG_NEW': 'score_wallet|nouveaux wallets'}
rows = []
for k in SIGS:
    for sp in ('TRAIN', 'VALID', 'TEST'):
        m = EV[k] & (EV.split == sp)
        g = EV[m]
        u = UP[(UP.signal == k) & (UP.split == sp)].set_index('metric')
        r = dict(signal=k, split=sp, n=int(m.sum()), n_marches=g.cid.nunique(), n_wallets=g.wallet.nunique(),
                 part_top_wallet=g.wallet.value_counts().iloc[0] / len(g) if len(g) else np.nan,
                 part_top_marche=g.cid.value_counts().iloc[0] / len(g) if len(g) else np.nan,
                 lead60_signal=g.LEAD60.mean(), lead60_controle_A=u.loc['LEAD60', 'control_A_matched_mean'],
                 uplift_lead60_vs_A=u.loc['LEAD60', 'uplift'], ic_lo=u.loc['LEAD60', 'ci_lo'], ic_hi=u.loc['LEAD60', 'ci_hi'],
                 uplift_dpost60_vs_A=u.loc['dpost_60m', 'uplift'], dpost_ic_lo=u.loc['dpost_60m', 'ci_lo'], dpost_ic_hi=u.loc['dpost_60m', 'ci_hi'])
        pool_split = BASE & (EV.split == sp) & ~EV[k]
        # contrôle B : wallets ordinaires (score historique <= médiane TRAIN), même strate
        e, lo, hi, n = matched(m, pool_split & (EV.hist_score <= med_hist), 'LEAD60')
        r.update(uplift_lead60_vs_B=e, B_ic_lo=lo, B_ic_hi=hi)
        # contrôle C : mêmes wallets, événements FAE du même split sans le signal
        ws = set(g.wallet)
        cC = pool_split & EV.wallet.isin(ws)
        r.update(n_controle_C=int(cC.sum()), lead60_controle_C=EV[cC].LEAD60.mean())
        eC, _, _, _ = matched(cC, pool_split, 'LEAD60')
        r.update(uplift_lead60_C_vs_A=eC)
        # contrôle D : même marché avant intervention (mouvement de l'heure précédente)
        r.update(dpre_60m_moy=g.dpre_60m.mean(), part_dpre_60m_sup_theta=(g.dpre_60m >= 0.03).mean())
        # contrôle E : horodatage aléatoire, même marché
        r.update(lead60_controle_E=g.ctrlE_LEAD60.mean())
        # décomposition du mouvement
        r.update(impact_propre_moy=g.impact_own.mean(), mvt_apres_exec_moy=g.move_after_exec.mean())
        e, lo, hi, n = matched(m, pool_split, 'move_after_exec')
        r.update(mvt_apres_exec_vs_A=e, mae_ic_lo=lo, mae_ic_hi=hi)
        # sensibilité au seuil de mouvement
        for c in ('LEAD60_2pp', 'LEAD60_5pp'):
            e, lo, hi, n = matched(m, pool_split, c)
            r.update(**{f'uplift_{c}': e, f'{c}_ic_lo': lo})
        # lead-time
        lt = LT[(LT.signal == k) & (LT.split == sp)]
        if len(lt):
            r.update(lead_time_p25=lt.lead_time_p25.iloc[0], lead_time_med=lt.lead_time_med.iloc[0], lead_time_p75=lt.lead_time_p75.iloc[0],
                     lead_time_p90=lt.lead_time_p90.iloc[0], part_mvt_debut_avant_60s=lt.part_debut_avant_60s.iloc[0])
        # exécution
        for L, S in ((1, 500), (60, 500), (60, 1000), (60, 5000), (60, 10000)):
            x = XS[(XS.signal == k) & (XS.split == sp) & (XS.groupe == 'signal') & (XS.latence_s == L) & (XS.taille_usd == S)]
            if len(x):
                r.update(**{f'net_{L}s_{S}': x.net_frais_moy.iloc[0], f'net_{L}s_{S}_ic_lo': x.net_frais_ci_lo.iloc[0],
                            f'net_{L}s_{S}_ic_hi': x.net_frais_ci_hi.iloc[0], f'part_exec_{L}s_{S}': x.part_executable.iloc[0]})
        x = XS[(XS.signal == k) & (XS.split == sp) & (XS.groupe == 'controle_A') & (XS.latence_s == 60) & (XS.taille_usd == 500)]
        r.update(net_60s_500_controle_A=x.net_frais_moy.iloc[0] if len(x) else np.nan)
        x = XS[(XS.signal == k) & (XS.split == sp) & (XS.groupe == 'signal') & (XS.latence_s == 60) & (XS.taille_usd == 500)]
        r.update(net_60s_500_sans_frais=x.net_sans_frais_moy.iloc[0] if len(x) else np.nan, brut_1s_500=XS[(XS.signal == k) & (XS.split == sp) & (XS.groupe == 'signal') & (XS.latence_s == 1) & (XS.taille_usd == 500)].gross_moy.iloc[0])
        if k in aucmap:
            a = AUC[(AUC.split == sp) & (AUC.score == aucmap[k])]
            r.update(auc_score=a.auc.iloc[0] if len(a) else np.nan, auc_de=aucmap[k])
        r['faux_positifs_lead60'] = 1 - r['lead60_signal']
        rows.append(r)
B = pd.DataFrame(rows)
B.to_csv(OUT + 'backtest_results.csv', index=False)
# ---------- critères du §23 (sur VALID et TEST, jamais sur TRAIN)
H3 = pd.read_csv(OUT + 'strates_h3_categories.csv')
CO = pd.read_csv(OUT + 'detector_concordance.csv')
crit = []
for k in SIGS:
    v, t = B[(B.signal == k) & (B.split == 'VALID')].iloc[0], B[(B.signal == k) & (B.split == 'TEST')].iloc[0]
    both = lambda f: bool(f(v) and f(t))
    cats = H3[(H3.signal == k) & H3.strate.str.startswith('catégorie') & (H3.n >= 30)]
    catpos = cats.groupby('strate').apply(lambda d: bool((d.ci_lo > 0).all() and len(d) == 2), include_groups=False)
    conc = CO[CO.controle.str.startswith(k + ' ')].valeur.min()
    c = {
        '1 observable avant le mouvement': both(lambda r: r.dpre_60m_moy < 0.03 / 2 and r.part_dpre_60m_sup_theta < 0.5),
        '2 supérieur au contrôle': both(lambda r: r.ic_lo > 0 and r.uplift_lead60_vs_B > 0 and r.lead60_signal > r.lead60_controle_E and r.mvt_apres_exec_vs_A > 0 and r.mae_ic_lo > 0),
        '3 reproductible': both(lambda r: r.ic_lo > 0) and bool(np.sign(v.uplift_lead60_vs_A) == np.sign(t.uplift_lead60_vs_A)),
        '4 hors échantillon': both(lambda r: r.ic_lo > 0 and r.mae_ic_lo > 0),
        '5 plusieurs marchés': both(lambda r: r.n_marches >= 10 and r.part_top_marche < 0.2) and int(catpos.sum()) >= 2,
        '6 capturable après frais': both(lambda r: r.get('net_60s_500_ic_lo', np.nan) > 0),
        '7 robuste (seuils 2 et 5 points)': both(lambda r: r.LEAD60_2pp_ic_lo > 0 and r.LEAD60_5pp_ic_lo > 0),
        '8 sans utilisation du futur': bool(conc >= 0.999),
        '9 lead-time suffisant pour agir (médiane >= 60 s et net > 0 à 60 s)': both(lambda r: r.get('lead_time_med', 0) >= 60 and r.get('net_60s_500', -1) > 0),
    }
    for kk, vv in c.items():
        crit.append(dict(signal=k, critere=kk, satisfait=vv))
    crit.append(dict(signal=k, critere='catégories à uplift LEAD60 IC > 0 sur VALID et TEST', satisfait=', '.join(catpos[catpos].index.str.replace('catégorie ', '')) or 'aucune'))
C = pd.DataFrame(crit)
C.to_csv(OUT + 'criteres_23.csv', index=False)
pd.set_option('display.width', 250)
print(C.pivot(index='critere', columns='signal', values='satisfait').to_string())
print(B[['signal', 'split', 'n', 'uplift_lead60_vs_A', 'ic_lo', 'uplift_lead60_vs_B', 'lead60_controle_C', 'uplift_lead60_C_vs_A', 'dpre_60m_moy', 'mvt_apres_exec_vs_A', 'mae_ic_lo', 'uplift_LEAD60_2pp', 'uplift_LEAD60_5pp', 'net_60s_500', 'net_60s_500_ic_lo']].round(4).to_string())
