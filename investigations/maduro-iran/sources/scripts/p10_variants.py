#!/usr/bin/env python3
"""Phase 10 : variantes de SIG_HIST (PROTOCOLE_P10 §7, §8). SIG_HIST lui-même n'est pas modifié.
  --freeze   : TRAIN uniquement -> seuils τ_I (déjà gelé par p10_impact.py) et τ_F, écrits dans phase10/frozen_p10.json
  --evaluate : applique les règles gelées à TRAIN, VALID, TEST ; stratégie principale = marché, STRICT, L = 2 s, 500 $, sortie au bid à 60 min
Sortie : phase10/signal_variants.csv, phase10/variants_criteres.csv"""
import os, sys, json, argparse
import numpy as np, pandas as pd

# Les pickles lus ici sont produits localement par les scripts p8/p9/p10 ; ne jamais en charger d'autres.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p10_impact import load_tape, leader_index  # noqa: E402
from p10_execution import simulate, boot_ci  # noqa: E402

OUT = os.path.expanduser('~/Documents/Crypto/enquete_maduro_iran/phase10/')
FZ = OUT + 'frozen_p10.json'
K_LINK, W_SOCIAL = 2, 300


def hist_follow():
    """Moyenne causale de move_after_exec (phase 9, trades >= 100 $) sur les FAE non-FOLLOW du wallet résolus avant T0."""
    EV = pd.read_pickle('p9/events_final.pkl')
    W = pd.read_pickle('p10/windows.pkl')
    R = EV[EV.is_FAE & ~EV.FOLLOW & EV.p_before.notna()][['wallet', 'ts', 'move_after_exec']].copy()
    R['res_t'] = R.ts + 3600
    byw = {w: (g.sort_values('res_t').res_t.values, np.cumsum(g.sort_values('res_t').move_after_exec.values)) for w, g in R.groupby('wallet')}
    hf, hn = [], []
    for r in W.itertuples():
        x = byw.get(r.wallet)
        if x is None:
            hf.append(np.nan); hn.append(0); continue
        k = np.searchsorted(x[0], int(r.ts), side='right')
        hf.append(x[1][k - 1] / k if k > 0 else np.nan); hn.append(k)
    W['hist_follow'] = hf
    W['hist_follow_n'] = hn
    return W


def freeze():
    fz = json.load(open(FZ))
    if 'tau_F' in fz:
        print('déjà gelé :', {k: fz[k] for k in ('tau_I', 'tau_F')})
        return
    W = hist_follow()
    tr = W[(W.groupe == 'SIG_HIST') & (W.split == 'TRAIN')].hist_follow.dropna()
    fz.update(tau_F=float(tr.median()), tau_F_n_train=int(len(tr)), K_LINK=K_LINK, W_SOCIAL=W_SOCIAL,
              strategie_principale='marché, STRICT, L = 2 s, 500 $, sortie au bid à 3 600 s, frais mesurés',
              gel_variantes=pd.Timestamp.utcnow().isoformat(), note='gelé sur TRAIN uniquement, avant toute lecture de VALID/TEST des variantes')
    json.dump(fz, open(FZ, 'w'), indent=1)
    print('gel', {k: fz[k] for k in ('tau_I', 'tau_F', 'K_LINK', 'W_SOCIAL', 'gel_variantes')})


def social_runs(W, LK, FE, est='STRICT'):
    """SIG_HIST_SOCIAL : T1 = premier achat de d par un suiveur lié dans ]T0, T0 + 300 s] ; latences comptées depuis T1."""
    out = []
    for r in W[W.groupe == 'SIG_HIST'].itertuples():
        lk = LK.get(r.wid, set())
        if not lk or not os.path.exists(f'p10/tapes/{r.wid}.pkl'):
            continue
        T = load_tape(r.wid, int(r.d))
        i = leader_index(T, r.tx, r.wallet)
        if i is None:
            continue
        t0 = int(T.ts.iloc[i])
        after = T.iloc[i + 1:]
        m = after[(after.ts <= t0 + W_SOCIAL) & after.ae & after.wallet.isin(lk)]
        if m.empty:
            continue
        j = int(m.index[0])
        c = FE.get(r.tx, np.nan)
        for x in simulate(r, T, j, c):
            if x.get('L') == 2 and x.get('est') == est and x.get('S', 500) == 500 and x.get('H', 3600) in (3600, 'RES'):
                out.append(dict(wid=r.wid, T1_delai_s=int(T.ts.iloc[j]) - t0, **x))
    return pd.DataFrame(out)


def evaluate(est='STRICT'):
    fz = json.load(open(FZ))
    assert 'tau_F' in fz, 'lancer --freeze d\'abord'
    W = hist_follow()
    IMP = pd.read_pickle('p10/impact.pkl').set_index('wid')
    W['IMMEDIATE_IMPACT'] = W.wid.map(IMP.IMMEDIATE_IMPACT)
    W['Delta_pre'] = W.wid.map(IMP.Delta_pre)
    X = pd.read_pickle('p10/exec_long.pkl')
    FE = X.drop_duplicates('wid').set_index('wid').c_frais
    LK = pd.read_pickle('p10/linked.pkl')
    prim = X[(X.est == est) & (X.L == 2) & (X.S == 500)]
    P60 = prim[prim.H.astype(str) == '3600'].set_index('wid')
    PRS = prim[prim.H.astype(str) == 'RES'].set_index('wid')
    S = W[W.groupe == 'SIG_HIST'].copy()
    S['LOW_IMPACT'] = S.IMMEDIATE_IMPACT <= fz['tau_I']
    S['FOLLOW'] = S.hist_follow >= fz['tau_F']
    txmap = W.drop_duplicates('wid').set_index('wid').tx
    SOC = social_runs(W, LK, {txmap[k]: v for k, v in FE.items()}, est)
    SOC60 = SOC[SOC.H.astype(str) == '3600'].set_index('wid') if len(SOC) else pd.DataFrame()
    SOCRS = SOC[SOC.H.astype(str) == 'RES'].set_index('wid') if len(SOC) else pd.DataFrame()
    ctl = W[W.groupe == 'CONTROLE'].set_index('alerte_eid9')
    variants = {'SIG_HIST': S.index == S.index, 'SIG_HIST_LOW_IMPACT': S.LOW_IMPACT.values, 'SIG_HIST_FOLLOW': S.FOLLOW.values,
                'SIG_HIST_LOW_IMPACT_FOLLOW': (S.LOW_IMPACT & S.FOLLOW).values, 'SIG_HIST_SOCIAL': S.wid.isin(set(SOC.wid) if len(SOC) else set()).values}
    rows = []
    for name, mask in variants.items():
        V = S[mask]
        for sp in ('TRAIN', 'VALID', 'TEST'):
            v = V[V.split == sp]
            src60, srcrs = (SOC60, SOCRS) if name == 'SIG_HIST_SOCIAL' else (P60, PRS)
            e = src60.loc[src60.index.intersection(v.wid)] if len(src60) else pd.DataFrame()
            e = e[e.sortie_observee == True] if len(e) else e  # noqa: E712
            e = e.assign(cid=v.set_index('wid').loc[e.index, 'cid'].values, wallet=v.set_index('wid').loc[e.index, 'wallet'].values,
                         Delta_pre=v.set_index('wid').loc[e.index, 'Delta_pre'].values) if len(e) else e
            rs = srcrs.loc[srcrs.index.intersection(v.wid)] if len(srcrs) else pd.DataFrame()
            r = dict(estimateur=est, variante=name, split=sp, n_alertes=len(v), n_marches=v.cid.nunique(), n_wallets=v.wallet.nunique(), n_trades_simules=len(e))
            if len(e):
                net = e.net.dropna()
                lo, hi = boot_ci(e.dropna(subset=['net']), n=2000)
                trim = net[net <= net.quantile(0.95)]
                r.update(part_couverte=len(e) / len(v), net_moy=net.mean(), net_ic_lo=lo, net_ic_hi=hi, net_med=net.median(), net_part_pos=(net > 0).mean(),
                         net_moy_sans_top5=trim.mean(), brut_moy=e.brut.mean(), part_top_wallet=e.wallet.value_counts(normalize=True).iloc[0],
                         part_top_marche=e.cid.value_counts(normalize=True).iloc[0], net_moy_Dpre_neg=e[e.Delta_pre <= 0].net.mean(),
                         net_moy_Dpre_pos=e[e.Delta_pre > 0].net.mean(), n_Dpre_neg=(e.Delta_pre <= 0).sum(), n_Dpre_pos=(e.Delta_pre > 0).sum())
                if name != 'SIG_HIST_SOCIAL':
                    ce = ctl.loc[ctl.index.intersection(v.eid9)]
                    cc = P60.loc[P60.index.intersection(ce.wid)] if len(ce) else pd.DataFrame()
                    cc = cc[cc.sortie_observee == True] if len(cc) else cc  # noqa: E712
                    r.update(controle_n=len(cc), controle_net_moy=cc.net.mean() if len(cc) else np.nan)
            if len(rs):
                rr = rs[rs.sortie_observee == True].net.dropna()  # noqa: E712
                r.update(net_resolution_moy=rr.mean(), net_resolution_n=len(rr))
            rows.append(r)
    SV = pd.DataFrame(rows)
    # critères §22 (VALID et TEST)
    crit = []
    for name in variants:
        v = SV[(SV.variante == name) & (SV.split == 'VALID')].iloc[0]
        t = SV[(SV.variante == name) & (SV.split == 'TEST')].iloc[0]
        g = lambda r, k: r.get(k, np.nan)
        both = lambda f: bool(f(v) and f(t))
        pooled_neg = [g(v, 'net_moy_Dpre_neg'), g(t, 'net_moy_Dpre_neg')]
        pooled_pos = [g(v, 'net_moy_Dpre_pos'), g(t, 'net_moy_Dpre_pos')]
        c = {'1 information disponible à T': True,
             '2 survit au contrôle du momentum': bool(np.nanmean(pooled_neg) > 0 and np.nanmean(pooled_pos) > 0),
             '3 positive en VALID (IC > 0, n >= 30)': bool(g(v, 'net_moy') > 0 and g(v, 'net_ic_lo') > 0 and g(v, 'n_trades_simules') >= 30),
             '4 positive en TEST (IC > 0, n >= 30)': bool(g(t, 'net_moy') > 0 and g(t, 'net_ic_lo') > 0 and g(t, 'n_trades_simules') >= 30),
             '5 après frais (mesurés)': both(lambda r: g(r, 'net_moy') > 0),
             '6 après glissement (niveaux consommés)': both(lambda r: g(r, 'net_moy') > 0),
             '7 taille réaliste (500 $)': both(lambda r: g(r, 'net_moy') > 0),
             '8 liquidité (couverture >= 30 %)': both(lambda r: g(r, 'part_couverte') >= 0.3),
             '9 pas dépendante de quelques événements': both(lambda r: g(r, 'net_moy_sans_top5') > 0 and g(r, 'part_top_wallet') < 0.2 and g(r, 'part_top_marche') < 0.2)}
        for k, x in c.items():
            crit.append(dict(estimateur=est, variante=name, critere=k, satisfait=x))
    C = pd.DataFrame(crit)
    pd.set_option('display.width', 250)
    print(SV[['variante', 'split', 'n_alertes', 'n_trades_simules', 'part_couverte', 'net_moy', 'net_ic_lo', 'net_ic_hi', 'net_med', 'net_moy_sans_top5', 'controle_net_moy', 'net_resolution_moy']].round(4).to_string())
    print(C.pivot(index='critere', columns='variante', values='satisfait').to_string())
    return SV, C


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--freeze', action='store_true')
    ap.add_argument('--evaluate', action='store_true')
    a = ap.parse_args()
    if a.freeze:
        freeze()
    if a.evaluate:
        # STRICT = principal pré-enregistré ; FLUX = exploratoire (écart au protocole déclaré dans le rapport)
        res = [evaluate('STRICT'), evaluate('FLUX')]
        pd.concat([r[0] for r in res]).to_csv(OUT + 'signal_variants.csv', index=False)
        pd.concat([r[1] for r in res]).to_csv(OUT + 'variants_criteres.csv', index=False)
