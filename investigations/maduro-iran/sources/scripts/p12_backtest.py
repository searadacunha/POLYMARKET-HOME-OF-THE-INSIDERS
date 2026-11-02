#!/usr/bin/env python3
"""Phase 12 : backtest des détecteurs sans wallet (PROTOCOLE_P12 §4-§6).
  --freeze   : TRAIN uniquement -> seuils θ_pre / θ_post, modèles B1 (AVANT) et B2 (AVANT + PENDANT anonyme), seuils d'alerte -> phase12/frozen_p12.json, phase12/modeles/
  --evaluate : applique les règles gelées à TRAIN, VALID, TEST -> pre_wallet_scores.csv, pre_wallet_events.csv, control_events.csv, pre_wallet_features.csv,
               comparaison_A_B.csv, signature_clob.csv
Usage : python3 p12_backtest.py --freeze ; python3 p12_backtest.py --evaluate   (depuis le dossier de données contenant p12/)"""
import os, sys, json, pickle, argparse
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p12_features import AVANT, PENDANT, THR  # noqa: E402

# Les pickles lus ici sont produits localement par p12_features.py ; ne jamais en charger d'autres.
OUT = os.path.expanduser('~/Documents/Crypto/enquete_maduro_iran/phase12/')
MOD = OUT + 'modeles/'
FZ = OUT + 'frozen_p12.json'
LAT_WALLET = {'mediane': 1.75, 'P10': 0.84, 'P90': 2.56}   # CLOB -> wallet, mesuré en direct (CLOB_LATENCY.md)
rng = np.random.default_rng(12)


def labels(C, fz):
    C['REPRICING_60_PRE'] = C.pre_delta >= fz['theta_pre'] - 1e-9
    C['REPRICING_60_POST'] = C.post_delta >= fz['theta_post'] - 1e-9
    C['t_rep_pre'] = C[f"pre_t_{fz['theta_pre']}"]
    C['t_rep_post'] = C[f"post_t_{fz['theta_post']}"]
    return C


def freeze():
    C = pd.read_pickle('p12/cand_hist.pkl')
    tr = C[C.split == 'TRAIN']
    def th(x):
        q = float(np.quantile(x, 0.9))
        return max(0.01, np.floor(q / 0.005) * 0.005)
    fz = dict(theta_pre=round(th(tr.pre_delta), 3), theta_post=round(th(tr.post_delta), 3), n_train=int(len(tr)))
    for k in ('theta_pre', 'theta_post'):
        fz[k] = min(THR, key=lambda t: abs(t - fz[k]))                       # seuils disponibles dans les délais pré-calculés
    tr = labels(tr.copy(), fz)
    os.makedirs(MOD, exist_ok=True)
    m1 = HistGradientBoostingClassifier(random_state=12).fit(tr[AVANT], tr.REPRICING_60_PRE.astype(int))
    m2 = HistGradientBoostingClassifier(random_state=12).fit(tr[AVANT + PENDANT], tr.REPRICING_60_POST.astype(int))
    s1, s2 = m1.predict_proba(tr[AVANT])[:, 1], m2.predict_proba(tr[AVANT + PENDANT])[:, 1]
    fz.update(seuil_B1=float(np.quantile(s1, 0.95)), seuil_B2=float(np.quantile(s2, 0.95)), features_B1=AVANT, features_B2=AVANT + PENDANT,
              taux_base_pre_train=float(tr.REPRICING_60_PRE.mean()), taux_base_post_train=float(tr.REPRICING_60_POST.mean()),
              gele_le=pd.Timestamp.utcnow().isoformat(), note='gelé sur TRAIN uniquement, avant toute lecture de VALID, TEST ou du direct')
    pickle.dump(m1, open(MOD + 'B1.pkl', 'wb')); pickle.dump(m2, open(MOD + 'B2.pkl', 'wb'))
    json.dump(fz, open(FZ, 'w'), indent=1)
    print({k: v for k, v in fz.items() if not k.startswith('features')})


def boot_diff(a, b, ga, gb, n=1000):
    """IC 95 % de mean(a) - mean(b), bootstrap groupé par marché."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    ua, ub = np.unique(ga), np.unique(gb)
    ia = {m: np.nonzero(ga == m)[0] for m in ua}; ib = {m: np.nonzero(gb == m)[0] for m in ub}
    bs = []
    for _ in range(n):
        xa = np.concatenate([ia[m] for m in rng.choice(ua, len(ua))]); xb = np.concatenate([ib[m] for m in rng.choice(ub, len(ub))])
        bs.append(np.nanmean(a[xa]) - np.nanmean(b[xb]))
    return np.nanquantile(bs, 0.025), np.nanquantile(bs, 0.975)


def evaluate():
    fz = json.load(open(FZ))
    m1, m2 = pickle.load(open(MOD + 'B1.pkl', 'rb')), pickle.load(open(MOD + 'B2.pkl', 'rb'))
    C = labels(pd.read_pickle('p12/cand_hist.pkl'), fz)
    R = pd.read_pickle('p12/random_hist.pkl')
    C['score_B1'] = m1.predict_proba(C[AVANT])[:, 1]
    C['score_B2'] = m2.predict_proba(C[AVANT + PENDANT])[:, 1]
    C['B1'] = C.score_B1 >= fz['seuil_B1']
    C['B2'] = C.score_B2 >= fz['seuil_B2']
    R['score_B1'] = m1.predict_proba(R[AVANT])[:, 1]
    R['B1'] = R.score_B1 >= fz['seuil_B1']
    R['REPRICING_60_PRE'] = R.pre_delta >= fz['theta_pre'] - 1e-9
    # ---------------- A contre B
    rows = []
    for sp in ('TRAIN', 'VALID', 'TEST'):
        x = C[C.split == sp]
        for det, flag, lab, t_rep, t_sig in (('A SIG_HIST (wallet)', x.was_SIG_HIST_wallet, 'REPRICING_60_POST', 't_rep_post', LAT_WALLET['mediane']),
                                             ('A SIG_HIST (wallet), cadre PRE', x.was_SIG_HIST_wallet, 'REPRICING_60_PRE', 't_rep_pre', LAT_WALLET['mediane']),
                                             ('B1 AVANT', x.B1, 'REPRICING_60_PRE', 't_rep_pre', 0.0),
                                             ('B2 AVANT + trade anonyme', x.B2, 'REPRICING_60_POST', 't_rep_post', 0.02)):
            f = x[flag]; nf = x[~flag]
            y = x[lab]
            lead = f[t_rep] - t_sig
            lo, hi = boot_diff(f[lab].astype(float), nf[lab].astype(float), f.cid.values, nf.cid.values) if len(f) >= 20 else (np.nan, np.nan)
            rows.append(dict(split=sp, detecteur=det, outcome=lab, n_candidats=len(x), n_signales=len(f), taux_base=y.mean(), precision=f[lab].mean(),
                             ecart_vs_non_signales=f[lab].mean() - nf[lab].mean(), ic_lo=lo, ic_hi=hi, rappel=(f[lab]).sum() / max(y.sum(), 1),
                             taux_faux_positifs=(~f[lab]).sum() / max((~y).sum(), 1), lead_median_s=lead.median(), lead_P25_s=lead.quantile(.25), lead_P75_s=lead.quantile(.75),
                             part_repricing_deja_fait=(lead[f[lab]] < 0).mean() if f[lab].any() else np.nan,
                             rappel_sur_SIG_HIST=(f.was_SIG_HIST_wallet.sum() / max(x.was_SIG_HIST_wallet.sum(), 1)) if det.startswith('B') else np.nan))
        sc = x[x.was_SIG_HIST_wallet | x.was_FAE_controle]
        for s in ('score_B1', 'score_B2'):
            if sc.was_SIG_HIST_wallet.nunique() == 2:
                rows.append(dict(split=sp, detecteur=f'AUC {s} : trade SIG_HIST contre FAE de contrôle', n_candidats=len(sc), precision=roc_auc_score(sc.was_SIG_HIST_wallet, sc[s])))
    AB = pd.DataFrame(rows)
    AB.to_csv(OUT + 'comparaison_A_B.csv', index=False)
    # ---------------- le signal vient-il du carnet ? (AVANT : SIG_HIST contre contrôle et contre instants aléatoires)
    sig = []
    clf = HistGradientBoostingClassifier(random_state=12)
    trn = C[(C.split == 'TRAIN') & (C.was_SIG_HIST_wallet | C.was_FAE_controle)]
    clf.fit(trn[AVANT], trn.was_SIG_HIST_wallet.astype(int))
    for sp in ('VALID', 'TEST'):
        x = C[(C.split == sp) & (C.was_SIG_HIST_wallet | C.was_FAE_controle)]
        sig.append(dict(split=sp, mesure='AUC AVANT seules (classifieur TRAIN) : SIG_HIST contre contrôle', valeur=roc_auc_score(x.was_SIG_HIST_wallet, clf.predict_proba(x[AVANT])[:, 1]), n=len(x)))
        S = C[(C.split == sp) & C.was_SIG_HIST_wallet]; K = C[(C.split == sp) & C.was_FAE_controle]; Rr = R[R.split == sp]
        for feat in ['dp_1s', 'dp_5s', 'dp_60s', 'vol_meme_1s', 'vol_meme_5s', 'vol_meme_60s', 'vol_opp_5s', 'vol_net_10s', 'accel_5s', 'n_meme_5s', 'max_usd_10s',
                     'niveaux_meme_10s', 'max_niveaux_10s', 'ecart_ask_bid_60s', 't_depuis_dernier']:
            lo, hi = boot_diff(S[feat], K[feat], S.cid.values, K.cid.values, n=500)
            lo2, hi2 = boot_diff(S[feat], Rr[feat], S.cid.values, Rr.cid.values, n=300)
            sig.append(dict(split=sp, mesure=feat, moy_SIG_HIST=S[feat].mean(), moy_controle=K[feat].mean(), moy_aleatoire=Rr[feat].mean(),
                            med_SIG_HIST=S[feat].median(), med_controle=K[feat].median(), med_aleatoire=Rr[feat].median(),
                            ecart_vs_controle_ic=f'[{lo:.4g} ; {hi:.4g}]', ecart_vs_aleatoire_ic=f'[{lo2:.4g} ; {hi2:.4g}]'))
        sig.append(dict(split=sp, mesure='part des instants aléatoires signalés par B1 (faux positifs en continu)', valeur=Rr.B1.mean(), n=len(Rr)))
        sig.append(dict(split=sp, mesure='taux de REPRICING_60_PRE : instants aléatoires signalés B1 / non signalés', valeur=Rr[Rr.B1].REPRICING_60_PRE.mean(),
                        valeur2=Rr[~Rr.B1].REPRICING_60_PRE.mean(), n=int(Rr.B1.sum())))
    pd.DataFrame(sig).to_csv(OUT + 'signature_clob.csv', index=False)
    # ---------------- tables livrables
    keep = ['wid', 'groupe', 'split', 'cid', 'cat', 'ts', 'seq', 'direction', 'tx', 'usd', 'was_SIG_HIST_wallet', 'was_FAE_controle', 'score_B1', 'score_B2', 'B1', 'B2',
            'REPRICING_60_PRE', 'REPRICING_60_POST', 'pre_delta', 'post_delta', 't_rep_pre', 't_rep_post']
    C[keep].to_csv(OUT + 'pre_wallet_scores.csv', index=False)
    C[keep + AVANT + PENDANT].to_csv(OUT + 'pre_wallet_features.csv.gz', index=False, compression='gzip')
    E = C[C.was_SIG_HIST_wallet].copy()
    E['T_SIGNAL_B1_s'] = 0.0; E['T_SIGNAL_B2_s'] = 0.02; E['T_WALLET_s'] = LAT_WALLET['mediane']
    E['T_REPRICING_post_s'] = E.t_rep_post; E['T_REPRICING_pre_s'] = E.t_rep_pre
    E['lead_wallet_s'] = E.t_rep_post - LAT_WALLET['mediane']; E['lead_B2_s'] = E.t_rep_post - 0.02; E['gain_B2_s'] = LAT_WALLET['mediane'] - 0.02
    E[keep + ['T_SIGNAL_B1_s', 'T_SIGNAL_B2_s', 'T_WALLET_s', 'T_REPRICING_pre_s', 'T_REPRICING_post_s', 'lead_wallet_s', 'lead_B2_s', 'gain_B2_s'] + AVANT + PENDANT].to_csv(OUT + 'pre_wallet_events.csv', index=False)
    C[C.was_FAE_controle][keep + AVANT + PENDANT].to_csv(OUT + 'control_events.csv', index=False)
    pd.set_option('display.width', 250)
    print(AB.round(4).to_string())
    print(pd.DataFrame(sig)[['split', 'mesure', 'valeur', 'moy_SIG_HIST', 'moy_controle', 'moy_aleatoire', 'ecart_vs_controle_ic', 'ecart_vs_aleatoire_ic']].round(4).to_string())


def cases():
    """Maduro et Iran (§21, §22) : features AVANT et scores B1/B2 juste avant chaque gros achat, rang percentile parmi tous les
    autres achats anonymes >= 250 $ et tous les instants (toutes les 60 s) de la même nuit. Aucun wallet dans les features."""
    from types import SimpleNamespace
    from p12_features import window
    fz = json.load(open(FZ))
    m1, m2 = pickle.load(open(MOD + 'B1.pkl', 'rb')), pickle.load(open(MOD + 'B2.pkl', 'rb'))
    T_ = lambda x: int(pd.Timestamp(x, tz='UTC').timestamp())
    CAS = {'maduro': dict(wid='EVT_MADURO', cid='0x580adc1327de9bf7c179ef5aaffa3377bb5cb252b7d6390b027172d43fd6f993', debut=T_('2026-01-03 01:00'), fin=T_('2026-01-03 06:16:11'),
                          interet={'0x31a56e9e690c621ed21de08cb559e9524cdb8ed9': '0x31a56e9e', '0x6baf05d193692bb208d616709e27442c910a94c5': '0x6baf05d1',
                                   '0x168b100d7a6620a2f49a455344c2c006eaf1714b': 'Chiwawas'}),
           'iran': dict(wid='EVT_IRAN', cid='0x3488f31e6449f9803f99a8b5dd232c7ad883637f1c86e6953305a2ef19c77f20', debut=T_('2026-02-27 12:00'), fin=T_('2026-02-28 06:13:22'),
                        interet={'0x4dfd481c16d9995b809780fd8a9808e8689f6e4a': '0x4dfd481c', '0x38745db27f7360a287f6ca3c9b6a6a9c76149801': 'Planktonbets',
                                 '0xbf32f7a77ccea8bba647fea63d438ce1778b1762': '154x838hjd6', '0xae0f21790d847393dcc4da8b4d15f72ff84cf647': '0xae0f2179'})}
    from p10_impact import load_tape
    for nom, c in CAS.items():
        r = SimpleNamespace(wid=c['wid'], d=0, tx=None, wallet=None, groupe='CAS', split='CAS', cid=c['cid'], cat='geopolitics/war')
        cand, rnd = window(r)
        C = pd.DataFrame(cand); R = pd.DataFrame(rnd)
        C = C[(C.ts >= c['debut']) & (C.ts <= c['fin'])].copy(); R = R[(R.ts >= c['debut']) & (R.ts <= c['fin'])].copy()
        T = load_tape(c['wid'], 0)
        wal = dict(zip(zip(T.tx, T.ts), T.wallet))          # identification a posteriori (évaluation seulement)
        C['wallet_a_posteriori'] = [wal.get((t, s)) for t, s in zip(C.tx, C.ts)]
        C['compte'] = C.wallet_a_posteriori.map(c['interet']).fillna('')
        C['score_B1'] = m1.predict_proba(C[AVANT])[:, 1]; C['score_B2'] = m2.predict_proba(C[AVANT + PENDANT])[:, 1]
        R['score_B1'] = m1.predict_proba(R[AVANT])[:, 1]
        feats = ['score_B1', 'score_B2', 'dp_5s', 'dp_60s', 'vol_meme_5s', 'vol_meme_60s', 'accel_5s', 'n_meme_5s', 'niveaux_meme_10s', 'max_usd_10s', 't_depuis_dernier']
        for f in feats:
            C['rang_' + f] = C[f].rank(pct=True)
        for f in ('score_B1', 'dp_5s', 'dp_60s', 'vol_meme_5s', 'vol_meme_60s', 'accel_5s'):
            ref = R[f].dropna().values
            C['rang_vs_instants_' + f] = [(ref < v).mean() if v == v else np.nan for v in C[f]]
        C['B1'] = C.score_B1 >= fz['seuil_B1']; C['B2'] = C.score_B2 >= fz['seuil_B2']
        C['heure_utc'] = pd.to_datetime(C.ts, unit='s', utc=True).dt.strftime('%Y-%m-%d %H:%M:%S')
        cols = ['heure_utc', 'compte', 'direction', 'usd', 'p_before', 'score_B1', 'score_B2', 'B1', 'B2'] + [x for x in C.columns if x.startswith('rang_')] + AVANT + PENDANT + ['pre_delta', 'post_delta']
        C.sort_values('ts')[cols].to_csv(OUT + f'{nom}_pre_wallet.csv', index=False)
        I = C[C.compte != '']
        print(nom, 'candidats', len(C), 'instants', len(R), 'signaux B1', int(C.B1.sum()), 'B2', int(C.B2.sum()), '; instants signalés B1', int((R.score_B1 >= fz['seuil_B1']).sum()))
        pd.set_option('display.width', 250)
        print(I[['heure_utc', 'compte', 'direction', 'usd', 'score_B1', 'score_B2', 'rang_score_B1', 'rang_score_B2', 'rang_vs_instants_vol_meme_60s', 'rang_vs_instants_dp_60s', 'rang_vs_instants_accel_5s']].round(3).to_string())


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--freeze', action='store_true')
    ap.add_argument('--evaluate', action='store_true')
    ap.add_argument('--cases', action='store_true')
    a = ap.parse_args()
    if a.cases:
        cases()
    if a.freeze:
        freeze()
    if a.evaluate:
        evaluate()
