#!/usr/bin/env python3
"""Phase 10 : décomposition du mouvement autour du trade du wallet signalé (PROTOCOLE_P10 §2).
Δ_total(H) = Δ_pre + IMMEDIATE_IMPACT + FOLLOW_THROUGH(H), additif par construction, sur le flux complet (toutes tailles, ordre exact).
Sorties : phase10/impact_decomposition.csv (une ligne par alerte et par contrôle), phase10/follow_through.csv (résumés).
Usage : python3 p10_impact.py   (depuis le dossier de données contenant p10/)"""
import os, sys, json
import numpy as np, pandas as pd

# Les pickles lus ici sont produits localement par p10_replay.py ; ne jamais en charger d'autres.
OUT = os.path.expanduser('~/Documents/Crypto/enquete_maduro_iran/phase10/')
HS = [10, 60, 300, 600, 3600]


def load_tape(wid, d):
    """Flux d'une fenêtre, exprimé dans la direction d (jeton acheté par le wallet signalé)."""
    T = pd.read_pickle(f'p10/tapes/{wid}.pkl')
    if T.empty:
        return T
    T = T.reset_index(drop=True)
    T['pd'] = np.where(T.oi == d, T.price, 1 - T.price)
    T['ae'] = ((T.side == 'BUY') & (T.oi == d)) | ((T.side == 'SELL') & (T.oi != d))
    lv = []
    for levels, ae in zip(T.levels.values, T.ae.values):
        x = [((q if o == d else 1 - q), s) for (o, sd, q, s, w) in levels]
        lv.append(sorted(x, key=lambda z: z[0], reverse=not ae))   # asks croissants, bids décroissants
    T['lv'] = lv
    return T


def leader_index(T, tx, wallet):
    m = np.nonzero((T.tx.values == tx) & (T.wallet.values == wallet))[0]
    return int(m[0]) if len(m) else None


def decompose(r):
    T = load_tape(r.wid, int(r.d))
    out = dict(wid=r.wid, groupe=r.groupe, split=r.split, eid9=r.eid9, alerte_eid9=r.alerte_eid9, wallet=r.wallet, cid=r.cid, cat=r.cat,
               ts=int(r.ts), usd=r.usd, p_before_p9=r.p_before, impact_p9=r.impact_own, dpost_60m_p9=r.dpost_60m, LEAD60=r.LEAD60, win=r.win,
               leader_trouve=False)
    if T.empty:
        return out
    i = leader_index(T, r.tx, r.wallet)
    if i is None:
        return out
    L = T.iloc[i]
    t0 = int(L.ts)
    A = float(L.pd)
    lv = L.lv
    ask_before = lv[0][0] if lv else np.nan
    marginal = lv[-1][0] if lv else np.nan
    before = T.iloc[:i]
    pb = float(before.pd.iloc[-1]) if len(before) else np.nan
    pb_src = 'flux complet' if len(before) else 'absent (aucun trade dans les 900 s)'
    b600 = before[before.ts <= t0 - 600]
    p_m600 = float(b600.pd.iloc[-1]) if len(b600) else np.nan
    after = T.iloc[i + 1:]
    oth = after[after.wallet != r.wallet]
    out.update(leader_trouve=True, t0=t0, A=A, P_BEFORE=pb, P_BEFORE_source=pb_src, delai_P_BEFORE_s=(t0 - int(before.ts.iloc[-1])) if len(before) else np.nan,
               ASK_BEFORE=ask_before, MARGINAL=marginal, n_niveaux_leader=len(lv), P_m600=p_m600,
               leader_shares=float(L['size']))
    out['marche_dans_carnet'] = marginal - ask_before
    out['IMMEDIATE_IMPACT'] = marginal - pb
    out['impact_A_vs_P_BEFORE'] = A - pb
    out['Delta_pre'] = pb - p_m600
    # premier trade d'un autre wallet après le trade du wallet (prix « immédiatement après »)
    if len(oth):
        f = oth.iloc[0]
        out.update(P_AFTER1=float(f.pd), P_AFTER1_sens='AE' if f.ae else 'VE', delai_P_AFTER1_s=int(f.ts) - t0, meme_bloc_P_AFTER1=int(f.ts) == t0)
    fa = oth[oth.ae]
    fv = oth[~oth.ae]
    if len(fa):
        out.update(ASK_AFTER1=fa.lv.iloc[0][0][0] if fa.lv.iloc[0] else float(fa.pd.iloc[0]), delai_ASK_AFTER1_s=int(fa.ts.iloc[0]) - t0)
    if len(fv):
        out.update(BID_AFTER1=fv.lv.iloc[0][0][0] if fv.lv.iloc[0] else float(fv.pd.iloc[0]), delai_BID_AFTER1_s=int(fv.ts.iloc[0]) - t0)
    for H in HS:
        o = oth[oth.ts <= t0 + H]
        obs = len(o) > 0
        p = float(o.pd.iloc[-1]) if obs else np.nan
        out[f'P_oth_{H}'] = p
        out[f'obs_{H}'] = obs
        out[f'FOLLOW_THROUGH_{H}'] = p - marginal if obs else np.nan
        out[f'Delta_total_{H}'] = (p - p_m600) if obs else np.nan
        oa = o[o.ae]
        out[f'ask_oth_{H}'] = (oa.lv.iloc[-1][0][0] if oa.lv.iloc[-1] else float(oa.pd.iloc[-1])) if len(oa) else np.nan
        ov = o[~o.ae]
        out[f'bid_oth_{H}'] = (ov.lv.iloc[-1][0][0] if ov.lv.iloc[-1] else float(ov.pd.iloc[-1])) if len(ov) else np.nan
    out['follow_through_ratio'] = out['FOLLOW_THROUGH_3600'] / max(out['IMMEDIATE_IMPACT'], 0.005) if pd.notna(out['FOLLOW_THROUGH_3600']) and pd.notna(out['IMMEDIATE_IMPACT']) else np.nan
    return out


def main():
    W = pd.read_pickle('p10/windows.pkl')
    rows = [decompose(r) for r in W.itertuples() if os.path.exists(f'p10/tapes/{r.wid}.pkl')]
    D = pd.DataFrame(rows)
    # seuil τ_I : médiane TRAIN des alertes SIG_HIST (PROTOCOLE_P10 §2), rien d'autre n'est ajusté
    tr = D[(D.groupe == 'SIG_HIST') & (D.split == 'TRAIN')].IMMEDIATE_IMPACT.dropna()
    tau_I = float(tr.median())
    D['SELF_IMPACT'] = np.where(D.IMMEDIATE_IMPACT.isna(), 'INCONNU', np.where(D.IMMEDIATE_IMPACT > tau_I, 'SELF_IMPACT_HIGH', 'SELF_IMPACT_LOW'))
    ft = D.FOLLOW_THROUGH_3600
    D['cas'] = np.select([(D.IMMEDIATE_IMPACT <= tau_I) & (ft >= 0.015), (D.IMMEDIATE_IMPACT > tau_I) & (ft <= 0), (D.IMMEDIATE_IMPACT > tau_I) & (ft >= 0.015)],
                         ['A INFORMATION', 'B PRICE IMPACT', 'C MIXTE'], 'AUTRE')
    D.loc[D.IMMEDIATE_IMPACT.isna() | ft.isna(), 'cas'] = 'INCONNU'
    fr = {'tau_I': tau_I, 'tau_I_n_train': int(len(tr)), 'calcule_le': pd.Timestamp.utcnow().isoformat(), 'source': 'médiane de IMMEDIATE_IMPACT, alertes SIG_HIST de TRAIN'}
    fz = OUT + 'frozen_p10.json'
    old = json.load(open(fz)) if os.path.exists(fz) else {}
    old.update(fr)
    json.dump(old, open(fz, 'w'), indent=1)
    D.to_csv(OUT + 'impact_decomposition.csv', index=False)
    D.to_pickle('p10/impact.pkl')
    # résumés
    rows = []
    for (g, sp), x in D[D.leader_trouve].groupby(['groupe', 'split']):
        for lab, y in (('toutes', x), ('gagnantes LEAD60=1', x[x.LEAD60 == 1]), ('perdantes LEAD60=0', x[x.LEAD60 == 0])):
            r = dict(groupe=g, split=sp, sous_ensemble=lab, n=len(y))
            for c in ['Delta_pre', 'IMMEDIATE_IMPACT', 'marche_dans_carnet', 'impact_A_vs_P_BEFORE', 'FOLLOW_THROUGH_10', 'FOLLOW_THROUGH_60', 'FOLLOW_THROUGH_300',
                      'FOLLOW_THROUGH_600', 'FOLLOW_THROUGH_3600', 'Delta_total_3600']:
                r[c + '_moy'] = y[c].mean()
                r[c + '_med'] = y[c].median()
            r['follow_through_ratio_med'] = y.follow_through_ratio.median()
            r['obs_3600'] = y.obs_3600.mean()
            for k, v in y.cas.value_counts(normalize=True).items():
                r['part_' + k] = v
            rows.append(r)
    S = pd.DataFrame(rows)
    S.to_csv(OUT + 'follow_through.csv', index=False)
    pd.set_option('display.width', 250)
    print('tau_I', round(tau_I, 4), 'n TRAIN', len(tr))
    print(S[S.sous_ensemble != 'perdantes LEAD60=0'][['groupe', 'split', 'sous_ensemble', 'n', 'Delta_pre_moy', 'IMMEDIATE_IMPACT_moy', 'IMMEDIATE_IMPACT_med', 'marche_dans_carnet_moy',
                                                       'FOLLOW_THROUGH_60_moy', 'FOLLOW_THROUGH_600_moy', 'FOLLOW_THROUGH_3600_moy', 'Delta_total_3600_moy', 'follow_through_ratio_med']].round(4).to_string())


if __name__ == '__main__':
    main()
