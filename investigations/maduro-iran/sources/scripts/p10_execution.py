#!/usr/bin/env python3
"""Phase 10 : exécution simulée d'un observateur après une alerte SIG_HIST (et un contrôle apparié), PROTOCOLE_P10 §3, §4, §5.
Prix d'entrée = niveaux makers réellement consommés par le premier achat-équivalent d'un autre wallet après T0 + L ;
sortie = niveaux de bid consommés par la première vente-équivalente après T0 + H (ou résolution). Rien n'est interpolé.
Sorties : phase10/execution_simulation.csv, latency_curve.csv, size_curve.csv, limit_orders.csv, reproduction_p9.csv ; p10/exec_long.pkl
Usage : python3 p10_execution.py   (depuis le dossier de données contenant p8/, p9/, p10/)"""
import os, sys, json
import numpy as np, pandas as pd

# Les pickles lus ici sont produits localement par les scripts p8/p9/p10 ; ne jamais en charger d'autres.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p10_impact import load_tape, leader_index  # noqa: E402

OUT = os.path.expanduser('~/Documents/Crypto/enquete_maduro_iran/phase10/')
LATS = [0, 1, 2, 5, 10, 20, 30, 60, 120, 300]
SIZES = [50, 100, 250, 500, 1000, 2500, 5000]
EXITS = [60, 300, 600, 3600, 'RES']
TOL = {'STRICT': 2, 'SUIVANT': 60}
DEPTH_WIN = 10
EXIT_TOL = 900
rng = np.random.default_rng(10)


def ladder(rows, t_first):
    """Concatène les niveaux du premier trade et des trades du même sens dans les DEPTH_WIN secondes suivantes."""
    lv = []
    for ts, levels in rows:
        if ts > t_first + DEPTH_WIN:
            break
        lv.extend(levels)
    return lv


def buy_on(lv, dollars):
    """Achète pour `dollars` sur des asks ; renvoie (actions, prix moyen, premier niveau, niveaux touchés) ou None si profondeur insuffisante."""
    need = dollars
    sh = 0.0
    n = 0
    for p, s in lv:
        if p <= 0:
            continue
        take = min(need, p * s)
        sh += take / p
        need -= take
        n += 1
        if need <= 1e-9:
            return sh, dollars / sh, lv[0][0], n
    return None


def sell_on(lv, shares):
    """Vend `shares` sur des bids ; renvoie (produit, prix moyen) ou None si profondeur insuffisante."""
    left = shares
    got = 0.0
    for p, s in lv:
        q = min(left, s)
        got += q * p
        left -= q
        if left <= 1e-9:
            return got, got / shares
    return None


def simulate(r, T, i, c):
    """Toutes les cases (latence x taille x estimateur x sortie) pour une fenêtre."""
    t0 = int(T.ts.iloc[i])
    after = T.iloc[i + 1:]
    oth = after[after.wallet != r.wallet]
    AE = [(int(t), lv) for t, lv, ae in zip(oth.ts.values, oth.lv.values, oth.ae.values) if ae and lv]
    VE = [(int(t), lv) for t, lv, ae in zip(oth.ts.values, oth.lv.values, oth.ae.values) if (not ae) and lv]
    path_t = oth.ts.values.astype(int)
    path_p = oth.pd.values.astype(float)
    out = []
    for L in LATS:
        cand = AE if L == 0 else [x for x in AE if x[0] >= t0 + L]
        out.extend(flux(r, t0, L, cand, VE, path_t, path_p, c))
        for est, tol in TOL.items():
            if not cand or cand[0][0] > t0 + L + tol:
                out.append(dict(L=L, est=est, entree_observee=False))
                continue
            t_in = cand[0][0]
            lv_in = ladder(cand, t_in)
            for S in SIZES:
                b = buy_on(lv_in, S)
                base = dict(L=L, est=est, S=S, entree_observee=True, t_entree=t_in - t0, B=lv_in[0][0])
                if b is None:
                    out.append(dict(base, profondeur_ok=False))
                    continue
                sh, C, best, nlv = b
                fee_in = c * sh * min(C, 1 - C) if pd.notna(c) else np.nan
                m = path_t > t_in
                mt, mp = path_t[m & (path_t <= t0 + 3600)], path_p[m & (path_t <= t0 + 3600)]
                mae = (mp.min() - C) if len(mp) else np.nan
                mfe = (mp.max() - C) if len(mp) else np.nan
                for H in EXITS:
                    rec = dict(base, profondeur_ok=True, C=C, glissement=C - best, niveaux_consommes=nlv, shares=sh, H=H, mae=mae, mfe=mfe)
                    if H == 'RES':
                        if pd.isna(r.win):
                            rec.update(sortie_observee=False)
                        else:
                            proceeds = sh * float(r.win)
                            rec.update(sortie_observee=True, t_sortie=np.nan, exit_px=float(r.win), brut=proceeds / S - 1,
                                       net=(proceeds - S - fee_in) / S if pd.notna(fee_in) else np.nan)
                        out.append(rec)
                        continue
                    ce = [x for x in VE if x[0] >= max(t0 + H, t_in + 1)]
                    if not ce or ce[0][0] > t0 + H + EXIT_TOL:
                        rec.update(sortie_observee=False)
                        out.append(rec)
                        continue
                    s = sell_on(ladder(ce, ce[0][0]), sh)
                    if s is None:
                        rec.update(sortie_observee=False, sortie_profondeur_insuffisante=True)
                        out.append(rec)
                        continue
                    proceeds, X = s
                    fee_out = c * sh * min(X, 1 - X) if pd.notna(c) else np.nan
                    rec.update(sortie_observee=True, t_sortie=ce[0][0] - t0, exit_px=X, brut=proceeds / S - 1,
                               net=(proceeds - S - fee_in - fee_out) / S if pd.notna(fee_in) else np.nan)
                    out.append(rec)
    return out


FLUX_ENTRY, FLUX_EXIT = 60, 1800


def walk(rows, t_max, dollars=None, shares=None):
    """Niveaux consommés par les trades successifs (ordre d'exécution) jusqu'à t_max ; achète `dollars` ou vend `shares`.
    Renvoie (quantité, prix moyen, heure du trade qui complète, premier niveau, niveaux touchés) ou None."""
    need = dollars if dollars is not None else shares
    got_sh = got_usd = 0.0
    n = 0
    first = None
    for t, lv in rows:
        if t > t_max:
            return None
        for p, s in lv:
            if p <= 0:
                continue
            first = p if first is None else first
            n += 1
            if dollars is not None:
                take = min(need, p * s); got_sh += take / p; got_usd += take; need -= take
            else:
                q = min(need, s); got_sh += q; got_usd += q * p; need -= q
            if need <= 1e-9:
                return (got_sh, got_usd / got_sh, t, first, n)
    return None


def flux(r, t0, L, cand, VE, path_t, path_p, c):
    """ÉCART AU PROTOCOLE (déclaré) : l'observateur paie les niveaux réellement consommés par les achats suivants des autres wallets
    dans les 60 s après T0 + L, et sort sur les niveaux de bid consommés par les ventes suivantes dans les 1 800 s après T0 + H."""
    out = []
    if not cand:
        return [dict(L=L, est='FLUX', entree_observee=False)]
    for S in SIZES:
        b = walk(cand, t0 + L + FLUX_ENTRY, dollars=S)
        base = dict(L=L, est='FLUX', S=S, entree_observee=True, B=cand[0][1][0][0], t_premier=cand[0][0] - t0)
        if b is None:
            out.append(dict(base, profondeur_ok=False))
            continue
        sh, C, t_in, best, nlv = b
        fee_in = c * sh * min(C, 1 - C)
        m = path_t > t_in
        mp = path_p[m & (path_t <= t0 + 3600)]
        mae = (mp.min() - C) if len(mp) else np.nan
        mfe = (mp.max() - C) if len(mp) else np.nan
        for H in EXITS:
            rec = dict(base, profondeur_ok=True, t_entree=t_in - t0, C=C, glissement=C - best, niveaux_consommes=nlv, shares=sh, H=H, mae=mae, mfe=mfe)
            if H == 'RES':
                if pd.isna(r.win):
                    rec.update(sortie_observee=False)
                else:
                    proceeds = sh * float(r.win)
                    rec.update(sortie_observee=True, exit_px=float(r.win), brut=proceeds / S - 1, net=(proceeds - S - fee_in) / S)
                out.append(rec)
                continue
            ce = [x for x in VE if x[0] >= max(t0 + H, t_in + 1)]
            s2 = walk(ce, t0 + H + FLUX_EXIT, shares=sh) if ce else None
            if s2 is None:
                rec.update(sortie_observee=False)
                out.append(rec)
                continue
            _, X, t_out, _, _ = s2
            proceeds = sh * X
            fee_out = c * sh * min(X, 1 - X)
            rec.update(sortie_observee=True, t_sortie=t_out - t0, exit_px=X, brut=proceeds / S - 1, net=(proceeds - S - fee_in - fee_out) / S)
            out.append(rec)
    return out


def limit_orders(r, T, i, c, imp):
    """Ordres limites posés à T0 + 2 s (PROTOCOLE_P10 §4)."""
    t0 = int(T.ts.iloc[i])
    oth = T.iloc[i + 1:]
    oth = oth[oth.wallet != r.wallet]
    Ks = {'K1 ask avant impact': imp.get('ASK_BEFORE'), 'K2 prix du wallet': imp.get('A'),
          'K3 mi-chemin': (imp.get('P_BEFORE') + 0.5 * (imp.get('A') - imp.get('P_BEFORE'))) if pd.notna(imp.get('P_BEFORE')) else np.nan}
    VE = [(int(t), lv) for t, lv, ae in zip(oth.ts.values, oth.lv.values, oth.ae.values) if (not ae) and lv]
    res = []
    for kname, K in Ks.items():
        if pd.isna(K) or K <= 0 or K >= 1:
            continue
        sh = 500 / K
        for D in (60, 300):
            for rule in ('conservatrice', 'optimiste'):
                fill = None
                cum = 0.0
                for t, lv, ae in zip(oth.ts.values, oth.lv.values, oth.ae.values):
                    t = int(t)
                    if t < t0 + 2:
                        continue
                    if t > t0 + 2 + D:
                        break
                    if ae and lv:
                        dep = sum(s * p for p, s in lv if p <= K + 1e-12)
                        if dep >= 500:
                            b = buy_on([(p, s) for p, s in lv if p <= K + 1e-12], 500)
                            fill = ('preneur', t, b[1], b[0])
                            break
                    if (not ae) and lv:
                        cum += sum(s for p, s in lv if (p < K - 1e-12 if rule == 'conservatrice' else p <= K + 1e-12))
                        if cum >= sh:
                            fill = ('maker', t, K, sh)
                            break
                rec = dict(K=kname, K_prix=K, D=D, regle=rule, rempli=fill is not None)
                if fill:
                    kind, tf, px, shares = fill
                    fee_in = (c * shares * min(px, 1 - px)) if kind == 'preneur' and pd.notna(c) else 0.0
                    ce = [x for x in VE if x[0] >= max(t0 + 3600, tf + 1)]
                    rec.update(type_remplissage=kind, t_remplissage=tf - t0, prix=px)
                    if ce and ce[0][0] <= t0 + 3600 + EXIT_TOL:
                        s = sell_on(ladder(ce, ce[0][0]), shares)
                        if s:
                            proceeds, X = s
                            fee_out = c * shares * min(X, 1 - X) if pd.notna(c) else np.nan
                            rec.update(sortie_observee=True, net=(proceeds - 500 - fee_in - fee_out) / 500)
                    if pd.notna(r.win):
                        rec['net_resolution'] = (shares * float(r.win) - 500 - fee_in) / 500
                res.append(rec)
    return res


def p9_reproduction(W):
    """§5 : même code que p9_exec.sim (L = 1 s, 500 $, trades >= 100 $), avec le détail de l'entrée et de la sortie."""
    P = pd.read_pickle('p9/prints.pkl')
    wcode = {w: k for k, w in enumerate(P.wallet.unique())}
    P['wc'] = P.wallet.map(wcode).astype(np.int64)
    P['shares'] = P.usd / P.price
    M = {cid: (g.ts.values, g.p_yes.values, g.wc.values, g.buyeq_yes.values, g.shares.values) for cid, g in P.groupby('cid', sort=False)}
    rows = []
    for r in W[W.groupe == 'SIG_HIST'].itertuples():
        ts, py, wc, bey, sh = M[r.cid]
        d = int(r.d)
        pd_ = py if d == 0 else 1 - py
        buyeq = bey if d == 0 else ~bey
        w = wcode.get(r.wallet, -1)
        T, L, S, H = int(r.ts), 1, 500, 3600
        a = np.searchsorted(ts, T + L, side='left'); b = np.searchsorted(ts, T + L + 600, side='right')
        idx = [k for k in range(a, b) if buyeq[k] and wc[k] != w]
        need = S; shares = 0.0; used = []
        for k in idx:
            notional = pd_[k] * sh[k]; take = min(notional, need); shares += take / pd_[k]; need -= take; used.append((ts[k], pd_[k], take))
            if need <= 1e-9:
                break
        rec = dict(eid9=r.eid9, split=r.split, wallet=r.wallet, cid=r.cid, LEAD60=r.LEAD60, A=r.price, p_before=r.p_before, executable=need <= 1e-9)
        if need > 1e-9:
            rows.append(rec)
            continue
        entry = S / shares
        a2 = np.searchsorted(ts, T + H, side='left'); b2 = np.searchsorted(ts, T + H + 600, side='right')
        left = shares; proceeds = 0.0
        for k in range(a2, b2):
            if (not buyeq[k]) and wc[k] != w:
                q = min(sh[k], left); proceeds += q * pd_[k]; left -= q
                if left <= 1e-9:
                    break
        partial = left > 1e-9
        k = np.searchsorted(ts, T + H, side='right') - 1
        last = pd_[k] if k >= 0 else entry
        if partial:
            proceeds += left * max(last - 0.01, 0.0)
        exitp = proceeds / shares
        f_in = 0.02 * min(entry, 1 - entry) * shares
        f_out = 0.02 * min(exitp, 1 - exitp) * shares
        rec.update(entry=entry, exit=exitp, last_60=last, partial=partial, part_sortie_repli=left / shares if partial else 0.0,
                   delai_entree_premier_s=used[0][0] - T, delai_entree_moyen_s=np.average([u[0] for u in used], weights=[u[2] for u in used]) - T,
                   n_trades_entree=len(used), brut=(proceeds - S) / S, frais=(f_in + f_out) / S, net=(proceeds - S - f_in - f_out) / S)
        rows.append(rec)
    return pd.DataFrame(rows)


def stats(x):
    x = pd.Series(x).dropna()
    if len(x) == 0:
        return dict(n=0)
    return dict(n=len(x), moyenne=x.mean(), mediane=x.median(), P10=x.quantile(.1), P25=x.quantile(.25), P75=x.quantile(.75), P90=x.quantile(.9),
                min=x.min(), max=x.max(), part_positive=(x > 0).mean())


def boot_ci(df, col='net', n=2000):
    x = df[['cid', col]].dropna()
    if len(x) < 10:
        return np.nan, np.nan
    mk = x.cid.values; v = x[col].values
    um = np.unique(mk); idx = {m: np.nonzero(mk == m)[0] for m in um}
    bs = [v[np.concatenate([idx[m] for m in rng.choice(um, len(um))])].mean() for _ in range(n)]
    return np.quantile(bs, .025), np.quantile(bs, .975)


def main():
    W = pd.read_pickle('p10/windows.pkl')
    IMP = pd.read_pickle('p10/impact.pkl').set_index('wid')
    # coefficient de frais mesuré sur le reçu du wallet signalé (PROTOCOLE_P10 §3) ; reçu absent -> c = 0,02 (hypothèse phase 9), signalé
    FE = pd.read_pickle('p10/fees.pkl').drop_duplicates('tx')
    sh = pd.read_pickle('p8/alltrades.pkl')['size'].values
    FX = W[['tx', 'price', 'rid']].drop_duplicates('tx').merge(FE, on='tx')
    FX['shares'] = sh[FX.rid.values]
    FX['fee_usd'] = np.where(FX.fee_unit == 'jetons', FX.fee_raw * FX.price, FX.fee_raw)
    FX['c'] = FX.fee_usd / (FX.shares * np.minimum(FX.price, 1 - FX.price))
    cmap = FX.set_index('tx').c
    print('reçus disponibles', len(cmap), 'sur', W.tx.nunique())
    long, lim = [], []
    for r in W.itertuples():
        if not os.path.exists(f'p10/tapes/{r.wid}.pkl'):
            continue
        T = load_tape(r.wid, int(r.d))
        if T.empty:
            continue
        i = leader_index(T, r.tx, r.wallet)
        if i is None:
            continue
        c = cmap.get(r.tx, np.nan)
        recu = pd.notna(c)
        c = c if recu else 0.02
        meta = dict(wid=r.wid, groupe=r.groupe, split=r.split, eid9=r.eid9, alerte_eid9=r.alerte_eid9, wallet=r.wallet, cid=r.cid, LEAD60=r.LEAD60, c_frais=c, recu_frais=recu)
        for x in simulate(r, T, i, c):
            long.append({**meta, **x})
        imp = IMP.loc[r.wid].to_dict() if r.wid in IMP.index else {}
        for x in limit_orders(r, T, i, c, imp):
            lim.append({**meta, **x})
    X = pd.DataFrame(long)
    X.to_pickle('p10/exec_long.pkl')
    LM = pd.DataFrame(lim)
    LM.to_pickle('p10/limit_long.pkl')
    # --- tables agrégées (dénominateur = toutes les alertes du groupe et du split)
    nal = W.groupby(['groupe', 'split']).size()
    agg = []
    ent = X.groupby(['groupe', 'split', 'est', 'L']).apply(lambda g: g[g.entree_observee == True].wid.nunique(), include_groups=False)  # noqa: E712
    dep = X[X.S.notna()].groupby(['groupe', 'split', 'est', 'L', 'S']).apply(lambda g: g[g.profondeur_ok == True].wid.nunique(), include_groups=False)  # noqa: E712
    for key, g in X[X.H.notna()].groupby(['groupe', 'split', 'est', 'L', 'S', X.H.astype(str)]):
        n_al = int(nal[(key[0], key[1])])
        ok = g[g.sortie_observee == True]  # noqa: E712
        r = dict(zip(['groupe', 'split', 'estimateur', 'latence_s', 'taille_usd', 'sortie'], key), n_alertes=n_al,
                 part_B_observe=ent.get((key[0], key[1], key[2], key[3]), 0) / n_al, part_profondeur_observee=dep.get(key[:5], 0) / n_al,
                 part_entree_et_sortie=len(ok) / n_al, delai_premier_med_s=g.t_premier.median() if 't_premier' in g else np.nan,
                 delai_entree_med_s=g.t_entree.median(), B_moy=g.B.mean(), C_moy=g.C.mean(), glissement_moy=g.glissement.mean(),
                 niveaux_consommes_moy=g.niveaux_consommes.mean(), mae_moy=ok.mae.mean(), mfe_moy=ok.mfe.mean())
        for k, v in stats(ok.brut).items():
            r['brut_' + k] = v
        for k, v in stats(ok.net).items():
            r['net_' + k] = v
        agg.append(r)
    A = pd.DataFrame(agg)
    A['net_ic_lo'] = np.nan; A['net_ic_hi'] = np.nan
    prim = (A.taille_usd == 500) & A.sortie.isin(['3600', 'RES'])
    for ix in A[prim].index:
        k = A.loc[ix]
        g = X[(X.groupe == k.groupe) & (X.split == k.split) & (X.est == k.estimateur) & (X.L == k.latence_s) & (X.S == 500) & (X.H.astype(str) == k.sortie) & (X.sortie_observee == True)]  # noqa: E712
        A.loc[ix, ['net_ic_lo', 'net_ic_hi']] = boot_ci(g, n=1000)
    A.to_csv(OUT + 'execution_simulation.csv', index=False)
    A[(A.taille_usd == 500) & A.sortie.isin(['3600', 'RES'])].to_csv(OUT + 'latency_curve.csv', index=False)
    A[(A.latence_s == 2) & A.sortie.isin(['3600', 'RES'])].to_csv(OUT + 'size_curve.csv', index=False)
    # --- ordres limites
    la = []
    for key, g in LM.groupby(['groupe', 'split', 'K', 'D', 'regle']):
        n = g.wid.nunique()
        f = g[g.rempli]
        la.append(dict(zip(['groupe', 'split', 'K', 'duree_s', 'regle'], key), n_alertes=n, proba_remplissage=len(f) / n,
                       part_preneur=(f.type_remplissage == 'preneur').mean() if len(f) else np.nan,
                       net_conditionnel_moy=f.net.mean() if 'net' in f.columns else np.nan, net_conditionnel_med=f.net.median() if 'net' in f.columns else np.nan,
                       n_sortie_observee=f.net.notna().sum() if 'net' in f.columns else 0,
                       esperance_par_alerte=(len(f) / n) * f.net.mean() if 'net' in f.columns and f.net.notna().any() else np.nan,
                       net_resolution_conditionnel_moy=f.net_resolution.mean() if 'net_resolution' in f.columns else np.nan))
    LA = pd.DataFrame(la)
    LA['classement'] = np.where((LA.proba_remplissage < 0.25) | (LA.esperance_par_alerte <= 0) | LA.esperance_par_alerte.isna(), 'NON CAPTURABLE', 'à examiner')
    LA.to_csv(OUT + 'limit_orders.csv', index=False)
    # --- reproduction phase 9
    R = p9_reproduction(W)
    R.to_csv(OUT + 'reproduction_p9_detail.csv', index=False)
    rep = []
    for sp, g in R[R.executable].groupby('split'):
        for lab, y in (('toutes', g), ('gagnantes (net > 0)', g[g.net > 0]), ('perdantes (net <= 0)', g[g.net <= 0])):
            r = dict(split=sp, sous_ensemble=lab, **{('net_' + k): v for k, v in stats(y.net).items()})
            r.update(brut_moy=y.brut.mean(), frais_moy=y.frais.mean(), delai_entree_premier_med_s=y.delai_entree_premier_s.median(),
                     delai_entree_moyen_med_s=y.delai_entree_moyen_s.median(), prime_entree_vs_A_moy=(y.entry - y.A).mean(),
                     prime_entree_vs_p_before_moy=(y.entry - y.p_before).mean(), sortie_vs_dernier_prix_moy=(y.exit - y.last_60).mean(),
                     part_sortie_repli=y.partial.mean(), LEAD60_moy=y.LEAD60.mean())
            rep.append(r)
    pd.DataFrame(rep).to_csv(OUT + 'reproduction_p9.csv', index=False)
    pd.set_option('display.width', 250)
    print(pd.DataFrame(rep).round(4).to_string())
    print(A[prim & (A.latence_s.isin([0, 2, 10, 60]))][['groupe', 'split', 'estimateur', 'latence_s', 'sortie', 'part_B_observe', 'part_profondeur_observee', 'part_entree_et_sortie', 'net_n', 'brut_moyenne', 'net_moyenne', 'net_mediane', 'net_ic_lo', 'net_ic_hi']].round(4).to_string())


if __name__ == '__main__':
    main()
