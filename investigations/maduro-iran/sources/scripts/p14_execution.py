#!/usr/bin/env python3
"""Phase 14 : exécution simulée au 2e achat (PROTOCOLE_P14 §2 à §11). SIG_HIST V1 inchangé, aucun seuil modifié, aucun ordre.
Historique : flux complets de la phase 10 (p10/tapes, fenêtre [T1 - 900 s, T1 + 4 500 s]) ; le carnet n'est connu que par les niveaux
makers réellement consommés (phase10/CLOB_DATA_AUDIT.md). Direct : carnet reconstruit de la phase 11 (p11_replay.Timeline).
  --simuler  : entrées / sorties (FLUX principal, STRICT, SUIVANT), carnet à T_OBS, chemin des prix -> p14/exec_second.pkl, exec_first.pkl, book.pkl, path.pkl
  --analyser : tables et conclusion -> phase14/phase14_execution.csv, phase14_controls.csv, phase14_capacity.csv, phase14_latency.csv, phase14_tables.csv
  --direct   : 2e achats des alertes live (phase 11) sur le carnet complet -> phase14/phase14_live_second_buy.csv
  --cas      : 8 comptes, Maduro, Iran, nouveaux wallets -> phase14/phase14_cas.csv
Usage : depuis le dossier de données (p8/, p9/, p10/)."""
import os, sys, json, time, argparse, urllib.request
import numpy as np, pandas as pd

# Les pickles lus ici sont produits localement par les scripts p8/p9/p10/p14 de ce dossier ; ne jamais en charger d'autres.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p10_impact import load_tape, leader_index  # noqa: E402

OUT = os.path.expanduser('~/Documents/Crypto/enquete_maduro_iran/phase14/')
LATS = [0, 1, 2, 5, 10, 20, 30, 60, 120, 300]
LATS_REF = [0, 2, 5]
SIZES = [50, 100, 250, 500, 1000]
HS = [1, 5, 10, 30, 60, 120, 300, 600]
PRE = [1, 5, 10, 30, 60, 120]
POST = [1, 5, 10, 30, 60, 120, 300]
TOL = {'STRICT': 2, 'SUIVANT': 60}
DEPTH_WIN, FLUX_ENTRY, FLUX_EXIT, EXIT_TOL = 10, 60, 1800, 900
PRIM = dict(est='FLUX', L=2, S=500, H=300)
SEED = 14


# ------------------------------------------------------------------ simulation historique
def walkp(rows, t_max, dollars=None, shares=None):
    """Niveaux consommés par les trades successifs (ordre d'exécution) jusqu'à t_max ; exécution partielle autorisée.
    Renvoie (actions, dollars, premier niveau, niveaux touchés, heure du dernier trade utilisé, complet) ou None si aucun niveau."""
    need = dollars if dollars is not None else shares
    sh = usd = 0.0
    n = 0
    first = None
    t_last = None
    for t, lv in rows:
        if t > t_max or need <= 1e-9:
            break
        for p, s in lv:
            if p <= 0 or need <= 1e-9:
                continue
            first = p if first is None else first
            n += 1
            t_last = t
            if dollars is not None:
                take = min(need, p * s); sh += take / p; usd += take; need -= take
            else:
                q = min(need, s); sh += q; usd += q * p; need -= q
    if n == 0:
        return None
    return sh, usd, first, n, t_last, need <= 1e-9


def simulate(T, i, w, c, win, lats):
    """Une ligne par (estimateur, latence, taille) ; colonnes par horizon de sortie (compté depuis T_OBS)."""
    t0 = int(T.ts.iloc[i])
    oth = T.iloc[i + 1:]
    oth = oth[oth.wallet != w]
    AE = [(int(t), lv) for t, lv, ae in zip(oth.ts.values, oth.lv.values, oth.ae.values) if ae and lv]
    VE = [(int(t), lv) for t, lv, ae in zip(oth.ts.values, oth.lv.values, oth.ae.values) if (not ae) and lv]
    pt, pp = oth.ts.values.astype(int), oth.pd.values.astype(float)
    out = []
    for L in lats:
        tobs = t0 + L
        cand = AE if L == 0 else [x for x in AE if x[0] >= tobs]
        for est in ('FLUX', 'STRICT', 'SUIVANT'):
            lim = FLUX_ENTRY if est == 'FLUX' else TOL[est]
            if not cand or cand[0][0] > tobs + lim:
                out.extend(dict(est=est, L=L, S=S, statut='pas de repère') for S in SIZES)
                continue
            t_first = cand[0][0]
            tmax = tobs + FLUX_ENTRY if est == 'FLUX' else t_first + DEPTH_WIN
            for S in SIZES:
                b = walkp(cand, tmax, dollars=S)
                if b is None:
                    out.append(dict(est=est, L=L, S=S, statut='impossible', t_book=t_first - t0))
                    continue
                sh, cost, best, nlv, t_last, full = b
                C = cost / sh
                t_in = t_last if est == 'FLUX' else t_first
                fee_in = c * sh * min(C, 1 - C)
                m = (pt >= t_in) & (pt <= t_in + 600)
                r = dict(est=est, L=L, S=S, statut='complet' if full else 'partiel (CAPACITY_LIMIT)', t_book=t_first - t0, t_entree=t_in - t0,
                         exec_usd=cost, part_executee=cost / S, shares=sh, best_ask=best, C=C, slippage_entry=C - best, niveaux=nlv, fee_in=fee_in,
                         mae=(pp[m].min() - C) if m.any() else np.nan)
                for H in HS:
                    ce = [x for x in VE if x[0] >= max(tobs + H, t_in + 1)]
                    s = None
                    if ce and (est == 'FLUX' or ce[0][0] <= tobs + H + EXIT_TOL):
                        s = walkp(ce, (tobs + H + FLUX_EXIT) if est == 'FLUX' else ce[0][0] + DEPTH_WIN, shares=sh)
                    if s is None or not s[5]:
                        r[f'obs_{H}'] = False
                        continue
                    proceeds, X = s[1], s[1] / sh
                    fee_out = c * sh * min(X, 1 - X)
                    r.update({f'obs_{H}': True, f'exit_px_{H}': X, f't_sortie_{H}': s[4] - tobs, f'raw_{H}': proceeds / cost - 1,
                              f'fees_{H}': fee_in + fee_out, f'net_{H}': (proceeds - cost - fee_in - fee_out) / cost,
                              f'pnl_{H}': proceeds - cost - fee_in - fee_out})
                if pd.notna(win):
                    proceeds = sh * float(win)
                    r.update(obs_RES=True, raw_RES=proceeds / cost - 1, net_RES=(proceeds - cost - fee_in) / cost, pnl_RES=proceeds - cost - fee_in)
                else:
                    r['obs_RES'] = False
                out.append(r)
    return out


def book_at_obs(T, i, w, L):
    """Ce qui est observable du carnet autour de T_OBS = T + L (PROTOCOLE_P14 §3) ; rien n'est estimé."""
    t0 = int(T.ts.iloc[i])
    tobs = t0 + L
    own = T.lv.iloc[i]
    r = dict(L=L, own_niveaux=len(own), own_premier=own[0][0] if own else np.nan, own_dernier=own[-1][0] if own else np.nan,
             own_vwap=(sum(p * s for p, s in own) / sum(s for p, s in own)) if own else np.nan, p_wallet=float(T.pd.iloc[i]))
    r['own_glissement'] = r['own_vwap'] - r['own_premier']
    oth = T.iloc[i + 1:]
    oth = oth[oth.wallet != w]
    AE = [(int(t), lv) for t, lv, ae in zip(oth.ts.values, oth.lv.values, oth.ae.values) if ae and lv and (L == 0 or t >= tobs)]
    if AE and AE[0][0] <= tobs + TOL['SUIVANT']:
        tf = AE[0][0]
        B = AE[0][1][0][0]
        lv = [x for t, l in AE if t <= tf + DEPTH_WIN for x in l]
        r.update(T_book_s=tf - t0, best_ask=B, distance_ask_vs_wallet=B - r['p_wallet'],
                 **{f'prof_conso_{k}': sum(p * s for p, s in lv if p <= B + x + 1e-9) for k, x in (('05', .005), ('1', .01), ('2', .02))},
                 prof_conso_totale=sum(p * s for p, s in lv), statut_ask='observé')
    else:
        r.update(statut_ask='UNKNOWN / NO BOOK DATA')
    oa = T[(T.wallet != w) & (~T.ae) & (T.ts >= tobs - 2) & (T.ts <= tobs + 2)]
    oa = oa[[bool(x) for x in oa.lv]]
    if len(oa):
        j = (oa.ts - tobs).abs().values.argmin()
        bid = oa.lv.iloc[j][0][0]
        r.update(best_bid=bid, statut_bid='observé')
        if pd.notna(r.get('best_ask', np.nan)):
            r.update(spread=r['best_ask'] - bid, mid=(r['best_ask'] + bid) / 2)
    else:
        r.update(statut_bid='UNKNOWN / NO BOOK DATA')
    return r


def price_path(T, i, w):
    """p_ref, mouvements avant (tous wallets, avant le trade dans l'ordre d'exécution) et après (autres wallets) ; PROTOCOLE_P14 §8."""
    t0 = int(T.ts.iloc[i])
    pre = T.iloc[:i]
    r = dict(p_wallet=float(T.pd.iloc[i]), p_ref=float(pre.pd.iloc[-1]) if len(pre) else np.nan)
    for k in PRE:
        x = pre[pre.ts <= t0 - k]
        r[f'pre_{k}'] = (r['p_ref'] - float(x.pd.iloc[-1])) if len(x) and pd.notna(r['p_ref']) else np.nan
    post = T.iloc[i + 1:]
    post = post[post.wallet != w]
    for h in POST:
        x = post[post.ts <= t0 + h]
        p = float(x.pd.iloc[-1]) if len(x) else r['p_ref']
        r[f'post_{h}'] = p - r['p_ref'] if pd.notna(r['p_ref']) else np.nan
        r[f'post_vs_wallet_{h}'] = p - r['p_wallet'] if pd.notna(p) else np.nan
        r[f'n_trades_autres_{h}'] = len(x)
    p60 = r.get('pre_60')
    r['segment'] = 'inconnu' if pd.isna(p60) else ('stable' if abs(p60) < 0.01 else ('hausse préalable' if p60 >= 0.01 else 'baisse préalable'))
    return r


def fee_map(W):
    """Coefficient de frais mesuré sur le reçu du 1er achat (règle de la phase 10) ; absent -> 0,02, signalé."""
    FE = pd.read_pickle('p10/fees.pkl').drop_duplicates('tx')
    sh = pd.read_pickle('p8/alltrades.pkl')['size'].values
    FX = W[['tx', 'price', 'rid']].drop_duplicates('tx').merge(FE, on='tx')
    FX['shares'] = sh[FX.rid.values]
    FX['fee_usd'] = np.where(FX.fee_unit == 'jetons', FX.fee_raw * FX.price, FX.fee_raw)
    FX['c'] = FX.fee_usd / (FX.shares * np.minimum(FX.price, 1 - FX.price))
    return FX.set_index('tx').c


def simuler():
    S = pd.read_pickle('p14/second.pkl')
    W = pd.read_pickle('p10/windows.pkl')
    cmap = fee_map(W)
    sec, fst, bks, pts, cov = [], [], [], [], []
    t = time.time()
    for k, e in enumerate(S.itertuples()):
        c = cmap.get(e.tx1, np.nan)
        recu = pd.notna(c)
        c = float(c) if recu else 0.02
        meta = dict(groupe=e.groupe, split=e.train_valid_test, eid9=e.eid9, wid=e.wid, wallet=e.wallet, cid=e.market_id, cat=e.market_category,
                    has_second=e.has_second, c_frais=c, recu_frais=recu)
        st = dict(meta, flux=False, premier_trouve=False, second_trouve=False)
        fp = f'p10/tapes/{e.wid}.pkl'
        T = load_tape(e.wid, int(e.d)) if os.path.exists(fp) else pd.DataFrame()
        if len(T):
            st['flux'] = True
            i1 = leader_index(T, e.tx1, e.wallet)
            if i1 is not None:
                st['premier_trouve'] = True
                for x in simulate(T, i1, e.wallet, c, e.win, LATS_REF):
                    fst.append({**meta, **x})
                for L in (0, 2, 5):
                    bks.append({**meta, 'achat': 'premier', **book_at_obs(T, i1, e.wallet, L)})
                pts.append({**meta, 'achat': 'premier', **price_path(T, i1, e.wallet)})
            if e.has_second:
                i2 = leader_index(T, e.tx2, e.wallet)
                if i2 is not None:
                    st['second_trouve'] = True
                    for x in simulate(T, i2, e.wallet, c, e.win, LATS):
                        sec.append({**meta, **x})
                    for L in (0, 2, 5):
                        bks.append({**meta, 'achat': 'second', **book_at_obs(T, i2, e.wallet, L)})
                    pts.append({**meta, 'achat': 'second', **price_path(T, i2, e.wallet)})
        cov.append(st)
        if k % 500 == 0:
            print(k, len(S), round(time.time() - t), 's', flush=True)
    for name, x in (('exec_second', sec), ('exec_first', fst), ('book', bks), ('path', pts), ('couverture', cov)):
        pd.DataFrame(x).to_pickle(f'p14/{name}.pkl')
    print('fini', round(time.time() - t), 's')


# ------------------------------------------------------------------ analyse
def boot_mean(df, col, n=1000, seed=SEED):
    x = df[['cid', col]].dropna()
    if len(x) < 10:
        return np.nan, np.nan
    rng = np.random.default_rng(seed)
    g = {m: v[col].values for m, v in x.groupby('cid')}
    keys = list(g)
    bs = []
    for _ in range(n):
        v = np.concatenate([g[m] for m in rng.choice(keys, len(keys))])
        bs.append(v.mean())
    return np.quantile(bs, .025), np.quantile(bs, .975)


def boot_diff(a, b, col, n=1000, seed=SEED):
    xa, xb = a[['cid', col]].dropna(), b[['cid', col]].dropna()
    if len(xa) < 10 or len(xb) < 10:
        return np.nan, np.nan
    rng = np.random.default_rng(seed)
    ga = {m: v[col].values for m, v in xa.groupby('cid')}
    gb = {m: v[col].values for m, v in xb.groupby('cid')}
    ka, kb = list(ga), list(gb)
    bs = []
    for _ in range(n):
        va = np.concatenate([ga[m] for m in rng.choice(ka, len(ka))])
        vb = np.concatenate([gb[m] for m in rng.choice(kb, len(kb))])
        bs.append(va.mean() - vb.mean())
    return np.quantile(bs, .025), np.quantile(bs, .975)


def desc(x, pre=''):
    x = pd.Series(x, dtype=float).dropna()
    if not len(x):
        return {pre + 'n': 0}
    return {pre + 'n': len(x), pre + 'moyenne': x.mean(), pre + 'mediane': x.median(), pre + 'P25': x.quantile(.25), pre + 'P75': x.quantile(.75),
            pre + 'P10': x.quantile(.1), pre + 'P90': x.quantile(.9), pre + 'part_positive': (x > 0).mean()}


def analyser():
    S = pd.read_pickle('p14/second.pkl')
    X2 = pd.read_pickle('p14/exec_second.pkl')
    X1 = pd.read_pickle('p14/exec_first.pkl')
    BK = pd.read_pickle('p14/book.pkl')
    PA = pd.read_pickle('p14/path.pkl')
    CV = pd.read_pickle('p14/couverture.pkl')
    S['cid'] = S.market_id
    sec = S[S.has_second].copy()
    tables = []

    def T_(section, **kw):
        tables.append(dict(section=section, **kw))

    # ---- §4 population et conservation
    pop = []
    for (g, sp), x in S.groupby(['groupe', 'train_valid_test']):
        y = x[x.has_second]
        cv = CV[(CV.groupe == g) & (CV.split == sp) & CV.has_second]
        e2 = X2[(X2.groupe == g) & (X2.split == sp) & (X2.est == 'FLUX') & (X2.L == 2) & (X2.S == 500)]
        ent = e2[e2.statut.isin(['complet', 'partiel (CAPACITY_LIMIT)'])]
        full = e2[e2.statut == 'complet']
        ok = ent[ent.get('obs_300', pd.Series(False, index=ent.index)) == True]  # noqa: E712
        okf = full[full.get('obs_300', pd.Series(False, index=full.index)) == True]  # noqa: E712
        pop.append(dict(groupe=g, split=sp, evenements=len(x), ALL_SECOND_BUYS=len(y), avec_flux=int(cv.flux.sum()), second_trouve_dans_flux=int(cv.second_trouve.sum()),
                        entree_observable_FLUX_L2=len(ent), entree_500_complete=len(full), EXECUTION_MEASURABLE_500_300s=len(ok), dont_500_complets=len(okf),
                        taux_conservation=len(ok) / max(len(y), 1), resolution_connue=int(y.win.notna().sum()),
                        marches=y.market_id.nunique(), wallets=y.wallet.nunique(), marches_mesurables=ok.cid.nunique(), wallets_mesurables=ok.wallet.nunique()))
    POP = pd.DataFrame(pop)
    cat = sec.groupby(['groupe', 'train_valid_test', 'market_category']).size().rename('ALL').reset_index()
    okc = X2[(X2.est == 'FLUX') & (X2.L == 2) & (X2.S == 500) & (X2.get('obs_300') == True)].groupby(['groupe', 'split', 'cat']).size()  # noqa: E712
    cat['MEASURABLE'] = [int(okc.get((a, b, c), 0)) for a, b, c in zip(cat.groupe, cat.train_valid_test, cat.market_category)]
    # comparaison ALL vs MEASURABLE (représentativité)
    rep = []
    mk = X2[(X2.est == 'FLUX') & (X2.L == 2) & (X2.S == 500) & (X2.get('obs_300') == True)][['groupe', 'eid9']].copy()  # noqa: E712
    mk['mesurable'] = True
    sm = sec.merge(mk, on=['groupe', 'eid9'], how='left')
    sm['mesurable'] = sm.mesurable.fillna(False).astype(bool)
    for (g, sp, m), x in sm.groupby(['groupe', 'train_valid_test', 'mesurable']):
        rep.append(dict(groupe=g, split=sp, sous_ensemble='EXECUTION-MEASURABLE' if m else 'NON MESURABLE', n=len(x), LEAD60_2=x.LEAD60_2.mean(),
                        mvt_apres_2_moy=x.mvt_apres_2.mean(), second_usd_med=x.second_buy_usd.median(), delta_T1_T2_med=x.delta_T1_T2.median(),
                        prix_2_med=x.second_buy_price.median()))
    for (g, sp), x in sm.groupby(['groupe', 'train_valid_test']):
        rep.append(dict(groupe=g, split=sp, sous_ensemble='ALL SECOND BUYS', n=len(x), LEAD60_2=x.LEAD60_2.mean(), mvt_apres_2_moy=x.mvt_apres_2.mean(),
                        second_usd_med=x.second_buy_usd.median(), delta_T1_T2_med=x.delta_T1_T2.median(), prix_2_med=x.second_buy_price.median()))
    REP = pd.DataFrame(rep)

    # ---- §9 timing
    tim = []
    for (g, sp), x in sec.groupby(['groupe', 'train_valid_test']):
        b2 = BK[(BK.groupe == g) & (BK.split == sp) & (BK.achat == 'second') & (BK.L == 2)]
        tim.append(dict(groupe=g, split=sp, **desc(x.delta_T1_T2, 'T2_moins_T1_s_'), **desc(b2.T_book_s, 'Tbook_moins_T2_s_')))
    TIM = pd.DataFrame(tim)

    # ---- §6 carnet à T_OBS
    bk = []
    for (g, sp, a, L), x in BK.groupby(['groupe', 'split', 'achat', 'L']):
        bk.append(dict(groupe=g, split=sp, achat=a, L=L, n=len(x), part_ask_observe=(x.statut_ask == 'observé').mean(), part_bid_observe=(x.statut_bid == 'observé').mean(),
                       spread_med=x.spread.median() if 'spread' in x else np.nan, n_spread=int(x.spread.notna().sum()) if 'spread' in x else 0,
                       distance_ask_vs_wallet_moy=x.distance_ask_vs_wallet.mean(), distance_ask_vs_wallet_med=x.distance_ask_vs_wallet.median(),
                       prof_conso_05_med=x.prof_conso_05.median(), prof_conso_1_med=x.prof_conso_1.median(), prof_conso_2_med=x.prof_conso_2.median(),
                       prof_conso_totale_med=x.prof_conso_totale.median(), own_niveaux_med=x.own_niveaux.median(), own_glissement_moy=x.own_glissement.mean(),
                       Tbook_med_s=x.T_book_s.median()))
    BKA = pd.DataFrame(bk)

    # ---- §9 / §11 prix avant / après
    pa = []
    for (g, sp, a), x in PA.groupby(['groupe', 'split', 'achat']):
        r = dict(groupe=g, split=sp, achat=a, n=len(x))
        for k in PRE:
            r[f'pre_{k}_moy'] = x[f'pre_{k}'].mean(); r[f'pre_{k}_med'] = x[f'pre_{k}'].median()
        for h in POST:
            r[f'post_{h}_moy'] = x[f'post_{h}'].mean(); r[f'post_{h}_med'] = x[f'post_{h}'].median()
            r[f'post_vs_wallet_{h}_moy'] = x[f'post_vs_wallet_{h}'].mean()
        r['corr_pre60_post300'] = x[['pre_60', 'post_300']].corr().iloc[0, 1] if x.pre_60.notna().sum() > 5 else np.nan
        for s in ('stable', 'hausse préalable', 'baisse préalable', 'inconnu'):
            r[f'part_{s}'] = (x.segment == s).mean()
        pa.append(r)
    PAA = pd.DataFrame(pa)
    # segments descriptifs (§12), 2e achats seulement
    P2 = PA[PA.achat == 'second'].merge(sec[['groupe', 'eid9', 'LEAD60_2', 'mvt_apres_2']], on=['groupe', 'eid9'])
    prim = X2[(X2.est == 'FLUX') & (X2.L == 2) & (X2.S == 500) & (X2.get('obs_300') == True)][['groupe', 'eid9', 'obs_300', 'net_300']]  # noqa: E712
    P2 = P2.merge(prim, on=['groupe', 'eid9'], how='left')
    seg = []
    for (g, sp, s), x in P2.groupby(['groupe', 'split', 'segment']):
        seg.append(dict(groupe=g, split=sp, segment=s, n=len(x), LEAD60_2=x.LEAD60_2.mean(), post_60_moy=x.post_60.mean(), post_300_moy=x.post_300.mean(),
                        post_300_med=x.post_300.median(), n_net=int(x.net_300.notna().sum()), net_300_moy=x.net_300.mean(), net_300_med=x.net_300.median()))
    SEG = pd.DataFrame(seg)

    # ---- §7 / §8 exécution agrégée
    ex = []
    for (g, sp, est, L, Sz), x in X2.groupby(['groupe', 'split', 'est', 'L', 'S']):
        n_all = int(sec[(sec.groupe == g) & (sec.train_valid_test == sp)].shape[0])
        for H in HS + ['RES']:
            ok = x[x.get(f'obs_{H}', pd.Series(False, index=x.index)) == True]  # noqa: E712
            r = dict(achat='second', groupe=g, split=sp, estimateur=est, latence_s=L, taille_usd=Sz, sortie=str(H), ALL_SECOND_BUYS=n_all,
                     part_entree_complete=(x.statut == 'complet').sum() / max(n_all, 1), part_partielle=(x.statut == 'partiel (CAPACITY_LIMIT)').sum() / max(n_all, 1),
                     n_mesurable=len(ok), part_mesurable=len(ok) / max(n_all, 1), slippage_entry_moy=ok.slippage_entry.mean() if len(ok) else np.nan,
                     part_executee_moy=ok.part_executee.mean() if len(ok) else np.nan, fees_moy=ok[f'fees_{H}'].mean() if f'fees_{H}' in ok and len(ok) else np.nan,
                     delai_sortie_med_s=ok[f't_sortie_{H}'].median() if f't_sortie_{H}' in ok and len(ok) else np.nan, mae_moy=ok.mae.mean() if len(ok) else np.nan,
                     marches=ok.cid.nunique(), wallets=ok.wallet.nunique())
            r.update(desc(ok.get(f'raw_{H}', pd.Series(dtype=float)), 'raw_'))
            r.update(desc(ok.get(f'net_{H}', pd.Series(dtype=float)), 'net_'))
            r['net_PnL_moy'] = ok[f'pnl_{H}'].mean() if f'pnl_{H}' in ok and len(ok) else np.nan
            ex.append(r)
    for (g, sp, est, L, Sz), x in X1[X1.has_second].groupby(['groupe', 'split', 'est', 'L', 'S']):
        for H in HS + ['RES']:
            ok = x[x.get(f'obs_{H}', pd.Series(False, index=x.index)) == True]  # noqa: E712
            r = dict(achat='premier (mêmes alertes avec 2e achat)', groupe=g, split=sp, estimateur=est, latence_s=L, taille_usd=Sz, sortie=str(H), n_mesurable=len(ok),
                     marches=ok.cid.nunique(), wallets=ok.wallet.nunique(), slippage_entry_moy=ok.slippage_entry.mean() if len(ok) else np.nan)
            r.update(desc(ok.get(f'raw_{H}', pd.Series(dtype=float)), 'raw_'))
            r.update(desc(ok.get(f'net_{H}', pd.Series(dtype=float)), 'net_'))
            ex.append(r)
    EX = pd.DataFrame(ex)
    EX['net_ic_lo'] = np.nan; EX['net_ic_hi'] = np.nan
    for ix in EX[(EX.estimateur == 'FLUX') & (EX.taille_usd == 500) & (EX.sortie.isin(['300', 'RES'])) & (EX.latence_s.isin([0, 2, 5]))].index:
        k = EX.loc[ix]
        XX = X2 if k.achat == 'second' else X1[X1.has_second]
        y = XX[(XX.groupe == k.groupe) & (XX.split == k.split) & (XX.est == 'FLUX') & (XX.L == k.latence_s) & (XX.S == 500)]
        y = y[y.get(f'obs_{k.sortie}') == True]  # noqa: E712
        EX.loc[ix, ['net_ic_lo', 'net_ic_hi']] = boot_mean(y, f'net_{k.sortie}')
    EX.to_csv(OUT + 'phase14_execution.csv', index=False)

    # ---- §10 / §16 contrôles et statistiques (VALID, TEST ; TRAIN indicatif)
    ctl = []
    for sp in ('TRAIN', 'VALID', 'TEST'):
        a = sec[(sec.groupe == 'SIG_HIST') & (sec.train_valid_test == sp)]
        b = sec[(sec.groupe == 'CONTROLE') & (sec.train_valid_test == sp)]
        lo, hi = boot_diff(a, b, 'LEAD60_2')
        ctl.append(dict(split=sp, mesure='LEAD60_2 (tous les 2e achats)', n_SECOND=len(a), n_CONTROL=len(b), SECOND_moy=a.LEAD60_2.mean(), CONTROL_moy=b.LEAD60_2.mean(),
                        diff=a.LEAD60_2.mean() - b.LEAD60_2.mean(), ic_lo=lo, ic_hi=hi, marches_SECOND=a.market_id.nunique(), wallets_SECOND=a.wallet.nunique(),
                        part_max_wallet=a.wallet.value_counts(normalize=True).max()))
        lo, hi = boot_diff(a, b, 'mvt_apres_2')
        ctl.append(dict(split=sp, mesure='mouvement 60 min après le prix du 2e achat (phase 13)', n_SECOND=len(a), n_CONTROL=len(b), SECOND_moy=a.mvt_apres_2.mean(),
                        CONTROL_moy=b.mvt_apres_2.mean(), SECOND_med=a.mvt_apres_2.median(), CONTROL_med=b.mvt_apres_2.median(),
                        diff=a.mvt_apres_2.mean() - b.mvt_apres_2.mean(), ic_lo=lo, ic_hi=hi))
        # stable seulement (§10 règle MOMENTUM)
        pa_ = P2[(P2.split == sp) & (P2.segment == 'stable')]
        sa, sb = pa_[pa_.groupe == 'SIG_HIST'], pa_[pa_.groupe == 'CONTROLE']
        lo, hi = boot_diff(sa, sb, 'LEAD60_2')
        ctl.append(dict(split=sp, mesure='LEAD60_2, segment stable', n_SECOND=len(sa), n_CONTROL=len(sb), SECOND_moy=sa.LEAD60_2.mean(), CONTROL_moy=sb.LEAD60_2.mean(),
                        diff=sa.LEAD60_2.mean() - sb.LEAD60_2.mean(), ic_lo=lo, ic_hi=hi))
        for (est, L, H) in (('FLUX', 2, 300), ('FLUX', 0, 300), ('FLUX', 5, 300), ('FLUX', 2, 60), ('FLUX', 2, 600), ('FLUX', 2, 'RES'), ('STRICT', 2, 300), ('SUIVANT', 2, 300)):
            ya = X2[(X2.groupe == 'SIG_HIST') & (X2.split == sp) & (X2.est == est) & (X2.L == L) & (X2.S == 500)]
            yb = X2[(X2.groupe == 'CONTROLE') & (X2.split == sp) & (X2.est == est) & (X2.L == L) & (X2.S == 500)]
            ya, yb = ya[ya.get(f'obs_{H}') == True], yb[yb.get(f'obs_{H}') == True]  # noqa: E712
            for col in ('raw', 'net'):
                lo, hi = boot_diff(ya, yb, f'{col}_{H}')
                la, ha = boot_mean(ya, f'{col}_{H}')
                da, db = desc(ya.get(f'{col}_{H}', pd.Series(dtype=float))), desc(yb.get(f'{col}_{H}', pd.Series(dtype=float)))
                ctl.append(dict(split=sp, mesure=f'{col} {est} L={L}s 500$ sortie {H}', n_SECOND=da['n'], n_CONTROL=db['n'], SECOND_moy=da.get('moyenne'), CONTROL_moy=db.get('moyenne'),
                                SECOND_med=da.get('mediane'), CONTROL_med=db.get('mediane'), SECOND_P25=da.get('P25'), SECOND_P75=da.get('P75'),
                                SECOND_part_pos=da.get('part_positive'), CONTROL_part_pos=db.get('part_positive'),
                                SECOND_ic_lo=la, SECOND_ic_hi=ha, diff=(da.get('moyenne', np.nan) - db.get('moyenne', np.nan)) if da['n'] and db['n'] else np.nan,
                                diff_mediane=(da.get('mediane', np.nan) - db.get('mediane', np.nan)) if da['n'] and db['n'] else np.nan, ic_lo=lo, ic_hi=hi,
                                marches_SECOND=ya.cid.nunique(), wallets_SECOND=ya.wallet.nunique(),
                                part_max_wallet=ya.wallet.value_counts(normalize=True).max() if len(ya) else np.nan,
                                SECOND_mae_moy=ya.mae.mean() if len(ya) else np.nan))
    CT = pd.DataFrame(ctl)
    CT.to_csv(OUT + 'phase14_controls.csv', index=False)

    # ---- §17 capacité (FLUX, L = 2 s, sortie 300 s)
    cap = []
    for (g, sp, est, L, Sz), x in X2[X2.L.isin([0, 2, 5])].groupby(['groupe', 'split', 'est', 'L', 'S']):
        n_all = int(sec[(sec.groupe == g) & (sec.train_valid_test == sp)].shape[0])
        ok = x[(x.statut == 'complet') & (x.get('obs_300') == True)]  # noqa: E712
        okp = x[x.get('obs_300') == True]  # noqa: E712
        cap.append(dict(groupe=g, split=sp, estimateur=est, latence_s=L, taille_usd=Sz, ALL_SECOND_BUYS=n_all, n_flux=len(x),
                        part_entierement_executable=(x.statut == 'complet').sum() / max(n_all, 1),
                        part_partielle_CAPACITY_LIMIT=(x.statut == 'partiel (CAPACITY_LIMIT)').sum() / max(n_all, 1),
                        part_impossible=1 - ((x.statut == 'complet').sum() + (x.statut == 'partiel (CAPACITY_LIMIT)').sum()) / max(n_all, 1),
                        part_complete_parmi_observables=(x.statut == 'complet').sum() / max(x.statut.isin(['complet', 'partiel (CAPACITY_LIMIT)']).sum(), 1),
                        slippage_med=x.slippage_entry.median(), slippage_P90=x.slippage_entry.quantile(.9),
                        n_net_complet=len(ok), net_300_moy_complet=ok.net_300.mean() if len(ok) else np.nan, net_300_med_complet=ok.net_300.median() if len(ok) else np.nan,
                        n_net_avec_partiels=len(okp), net_300_moy_avec_partiels=okp.net_300.mean() if len(okp) else np.nan,
                        net_PnL_moy_avec_partiels=okp.pnl_300.mean() if len(okp) else np.nan))
    CAP = pd.DataFrame(cap)
    CAP.to_csv(OUT + 'phase14_capacity.csv', index=False)

    # ---- §5 latences (historique : T_wallet supposé, T_book observé)
    lat = BK[(BK.achat == 'second') & (BK.L == 2)][['groupe', 'split', 'eid9', 'wallet', 'cid', 'T_book_s', 'statut_ask']].merge(
        sec[['groupe', 'eid9', 'T2']], on=['groupe', 'eid9'])
    lat['T_trade'] = lat.T2
    lat['T_wallet'] = lat.T2 + 2
    lat['latency_wallet_ms'] = 2000
    lat['source_latence_wallet'] = 'hypothèse RÉALISTE (phase 13 : médianes 1,19 à 2,08 s) ; historique non observé'
    lat['T_book'] = lat.T2 + lat.T_book_s
    lat['latency_book_ms'] = lat.T_book_s * 1000
    lat['resolution'] = '1 s (horodatage de bloc)'
    lat[['groupe', 'split', 'eid9', 'cid', 'T_trade', 'T_wallet', 'T_book', 'latency_wallet_ms', 'latency_book_ms', 'statut_ask', 'source_latence_wallet', 'resolution']].to_csv(
        OUT + 'phase14_latency.csv', index=False)

    # ---- tables descriptives dans un seul fichier
    for name, D in (('population', POP), ('categories', cat), ('representativite', REP), ('timing', TIM), ('carnet', BKA), ('prix_avant_apres', PAA), ('segments', SEG)):
        D.insert(0, 'table', name)
    pd.concat([POP, cat, REP, TIM, BKA, PAA, SEG], ignore_index=True).to_csv(OUT + 'phase14_tables.csv', index=False)

    # ---- §19 conclusion (arbre pré-enregistré, PROTOCOLE_P14 §10)
    def row(sp, mesure):
        x = CT[(CT.split == sp) & (CT.mesure == mesure)]
        return x.iloc[0] if len(x) else None
    pred = {sp: row(sp, 'LEAD60_2 (tous les 2e achats)') for sp in ('VALID', 'TEST')}
    PRED = all(r is not None and r['ic_lo'] > 0 for r in pred.values())
    nall = {sp: pred[sp]['n_SECOND'] for sp in pred}
    stab = {sp: row(sp, 'LEAD60_2, segment stable') for sp in ('VALID', 'TEST')}
    MOM = any(r is None or not (r['diff'] > 0) for r in stab.values())
    nm = {sp: row(sp, 'net FLUX L=2s 500$ sortie 300') for sp in ('VALID', 'TEST')}
    nmes = {sp: (nm[sp]['n_SECOND'] if nm[sp] is not None else 0) for sp in nm}
    capr = {sp: CAP[(CAP.groupe == 'SIG_HIST') & (CAP.split == sp) & (CAP.estimateur == 'FLUX') & (CAP.latence_s == 2) & (CAP.taille_usd == 500)] for sp in ('VALID', 'TEST')}
    seg_net = {sp: SEG[(SEG.groupe == 'SIG_HIST') & (SEG.split == sp) & (SEG.segment == 'stable')] for sp in ('VALID', 'TEST')}
    if not PRED:
        concl = 'E. ABSENCE D EDGE' if all(v >= 30 for v in nall.values()) else 'D. SIGNAL NON CONFIRMÉ'
    elif MOM:
        concl = 'C. SIGNAL EXPLIQUÉ PAR LE MOMENTUM'
    elif any(v < 30 for v in nmes.values()):
        concl = 'D. SIGNAL NON CONFIRMÉ (exécution : INSUFFICIENT SAMPLE)'
    else:
        A = all(nm[sp]['SECOND_ic_lo'] > 0 and nm[sp]['SECOND_med'] > 0 and nm[sp]['ic_lo'] > 0 and nm[sp]['marches_SECOND'] >= 10 and nm[sp]['wallets_SECOND'] >= 10
                and nm[sp]['part_max_wallet'] <= 0.2 and len(capr[sp]) and capr[sp].part_complete_parmi_observables.iloc[0] >= 0.5
                and len(seg_net[sp]) and seg_net[sp].net_300_moy.iloc[0] > 0 for sp in ('VALID', 'TEST'))
        if A:
            concl = 'A. SIGNAL D EXÉCUTION CONFIRMÉ'
        elif any(not (nm[sp]['SECOND_moy'] > 0) or not (nm[sp]['SECOND_ic_lo'] > 0) for sp in ('VALID', 'TEST')):
            concl = 'B. SIGNAL PRÉDICTIF MAIS NON EXÉCUTABLE'
        else:
            concl = 'E. ABSENCE D EDGE'
    res = dict(conclusion=concl, PREDICTIF=PRED, MOMENTUM=MOM, n_2e_achats=nall, n_mesurables_cas_principal=nmes,
               LEAD60_diff={sp: (pred[sp]['diff'], pred[sp]['ic_lo'], pred[sp]['ic_hi']) for sp in pred},
               LEAD60_diff_stable={sp: (stab[sp]['diff'], stab[sp]['ic_lo'], stab[sp]['ic_hi']) if stab[sp] is not None else None for sp in stab})
    json.dump(res, open(OUT + 'phase14_conclusion.json', 'w'), indent=1, default=float, ensure_ascii=False)
    pd.set_option('display.width', 250); pd.set_option('display.max_columns', 40)
    print(POP.to_string()); print(json.dumps(res, indent=1, default=float, ensure_ascii=False))


# ------------------------------------------------------------------ direct (phase 11)
def direct():
    from p11_common import RAW as RAW11
    from p11_replay import Timeline, iter_raw, events
    from p11_execution import walk, fee_per_share, market_meta
    NS = 10 ** 9
    al = [json.loads(l) for l in open(os.path.join(RAW11, 'live', 'alerts.jsonl'))]
    W = json.load(open(os.path.expanduser('~/Documents/Crypto/enquete_maduro_iran/phase13/frozen_p13.json')))['W_second']
    now = int(time.time())
    rows = []
    for a in al:
        t1 = int(a['ts_echange'])
        end = min(t1 + W, now - 120)
        u = f"https://data-api.polymarket.com/trades?market={a['market']}&start={t1}&end={end}&limit=10000&takerOnly=true"
        tr = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'curl/8.4.0'}), timeout=30).read())
        own = [x for x in tr if x.get('transactionHash') == a['tx']]
        t1_api = int(own[0]['timestamp']) if own else t1        # horodatage de bloc du data-api, comme dans l'historique (le ws peut différer d'1 s)
        b = sorted([x for x in tr if x.get('proxyWallet', '').lower() == a['wallet'] and str(x.get('asset')) == a['asset'] and x.get('side') == 'BUY'
                    and float(x['size']) * float(x['price']) >= 100 and int(x['timestamp']) > t1_api and x.get('transactionHash') != a['tx']],
                   key=lambda x: int(x['timestamp']))
        base = dict(alert_id=a['alert_id'], wallet=a['wallet'], market=a['market'], token=a['asset'], T1=t1_api, T1_ws=t1, fenetre_terminee=t1_api + W <= now - 120,
                    trades_preneurs_lus=len(tr), alerte_trouvee_data_api=bool(own))
        if not b:
            rows.append(dict(base, has_second=False)); continue
        x2 = b[0]
        tx2 = x2['transactionHash']
        t2 = int(x2['timestamp'])
        base.update(has_second=True, T2=t2, delta_T1_T2=t2 - t1_api, second_buy_usd=float(x2['size']) * float(x2['price']), second_buy_price=float(x2['price']), tx2=tx2)
        t0n, t1n = (t2 - 120) * NS, (t2 + 700) * NS
        t_exch = t_loc = t_rtds = t_ch = None
        for t, conn, msg in iter_raw('ws_market', t0n, t1n):
            for e in events(msg):
                if e.get('event_type') == 'last_trade_price' and e.get('transaction_hash') == tx2 and t_loc is None:
                    t_exch, t_loc = int(e['timestamp']), t
        for t, conn, msg in iter_raw('rtds', t0n, t1n):
            if t_rtds is None and isinstance(msg, str) and tx2 in msg:
                t_rtds = t
        for t, conn, msg in iter_raw('chain', t0n, t1n):
            if t_ch is None and isinstance(msg, str) and tx2 in msg:
                t_ch = t
        tw = min([v for v in (t_rtds, t_ch) if v] or [None]) if (t_rtds or t_ch) else None
        base.update(T_trade_ms=t_exch, T_trade_local_ns=t_loc, T_wallet_rtds_ns=t_rtds, T_wallet_chaine_ns=t_ch, T_wallet_ns=tw,
                    latency_wallet_ms=(tw - t_loc) / 1e6 if tw and t_loc else np.nan)
        if not t_loc or not tw:
            rows.append(dict(base, statut='UNKNOWN / NO BOOK DATA (trade absent du flux enregistré)')); continue
        meta = market_meta(extra=[a['market']])
        toks = [str(x) for x in (meta.get(a['market']) or {}).get('tokens', [])] or [a['asset']]
        tl = Timeline(list(set(toks + [a['asset']])), t_loc - 60 * NS, tw + 700 * NS, warm_s=3600)
        for scen, tobs in (('ORACLE', t_loc), ('RÉALISTE', tw)):
            bk = tl.book_at(a['asset'], tobs)
            r = dict(base, scenario=scen, T_OBS_ns=tobs)
            if bk is None or not bk.asks:
                rows.append(dict(r, statut='UNKNOWN / NO BOOK DATA')); continue
            v = bk.view()
            r.update(T_book_ns=tobs, latency_book_ms=0.0, best_bid=v['best_bid'], best_ask=v['best_ask'], mid=v['mid'], spread=v['spread'],
                     **{f'prof_ask_{k}': sum(p * s for p, s in bk.asks.items() if p <= v['mid'] + x + 1e-9) for k, x in (('05', .005), ('1', .01), ('2', .02))},
                     **{f'prof_bid_{k}': sum(p * s for p, s in bk.bids.items() if p >= v['mid'] - x - 1e-9) for k, x in (('05', .005), ('1', .01), ('2', .02))},
                     prof_totale=sum(p * s for p, s in bk.asks.items()) + sum(p * s for p, s in bk.bids.items()),
                     distance_ask_vs_wallet=v['best_ask'] - base['second_buy_price'])
            for S in SIZES:
                sh, cost, vwap, nlv, rest = walk(bk.asks_sorted(), dollars=S)
                st = 'complet' if rest <= 1e-9 else ('impossible' if sh <= 0 else 'partiel (CAPACITY_LIMIT)')
                r[f'statut_{S}'] = st
                if sh <= 0:
                    continue
                fin = (fee_per_share(meta, a['market'], vwap) or 0.0) * sh
                r[f'vwap_{S}'] = vwap; r[f'slippage_{S}'] = vwap - v['best_ask']
                for H in HS:
                    bx = tl.book_at(a['asset'], tobs + H * NS)
                    if bx is None or not bx.bids or tobs + H * NS > (now - 60) * NS:
                        continue
                    q, proceeds, xv, _, unsold = walk(bx.bids_sorted(), shares=sh)
                    fout = (fee_per_share(meta, a['market'], xv) or 0.0) * q if q > 0 else 0.0
                    r[f'net_{S}_{H}'] = (proceeds - cost - fin - fout) / cost
                    r[f'raw_{S}_{H}'] = proceeds / cost - 1
            rows.append(dict(r, statut='mesuré'))
    D = pd.DataFrame(rows)
    D.to_csv(OUT + 'phase14_live_second_buy.csv', index=False)
    print(D.T.to_string() if len(D) else 'aucune alerte')


# ------------------------------------------------------------------ cas particuliers
def cas():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from p13_second_trade import A8
    EV = pd.read_pickle('p9/events_final.pkl')
    P = pd.read_pickle('p9/prints.pkl')
    W = json.load(open(os.path.expanduser('~/Documents/Crypto/enquete_maduro_iran/phase13/frozen_p13.json')))['W_second']
    B = P[P.side == 'BUY'].sort_values('ts')
    rows = []
    # 8 comptes : même règle appliquée à leurs FAE (base phase 9), descriptif
    base = EV[EV.is_FAE & ~EV.FOLLOW & EV.p_before.notna() & EV.wallet.isin(list(A8))]
    for e in base.itertuples():
        b = B[(B.wallet == e.wallet) & (B.asset == e.asset) & (B.ts > e.ts) & (B.ts <= e.ts + W)]
        r = dict(cas='8 comptes', compte=A8[e.wallet], wallet=e.wallet[:10], cid=e.cid, T1=pd.Timestamp(int(e.ts), unit='s'), usd1=e.usd, p1=e.price,
                 SIG_HIST=bool(e.SIG_HIST), hist_n=e.hist_n, has_second=len(b) > 0)
        if len(b):
            r.update(T2=pd.Timestamp(int(b.ts.iloc[0]), unit='s'), delta_T1_T2_s=int(b.ts.iloc[0] - e.ts), usd2=b.usd.iloc[0], p2=b.price.iloc[0])
        rows.append(r)
    # Maduro et Iran : flux de la phase 10 (EVT_MADURO, EVT_IRAN), même code d'exécution, coefficient de frais c = 0 (non mesuré ici, signalé).
    # Chaque paire d'achats consécutifs >= 100 $ du même wallet sur le même jeton à moins de W ; « stricte » si le 1er achat est un FAE
    # (>= 250 $, aucun trade du wallet dans le flux depuis 24 h ou depuis le début du flux), sinon descriptive.
    who = {'0x31a56e9e': 'Maduro', '0x6baf05d1': 'Maduro', '0x4dfd481c': 'Iran', **{k[:10]: v for k, v in A8.items()}}
    for name in ('EVT_MADURO', 'EVT_IRAN'):
        raw = pd.read_pickle(f'p10/tapes/{name}.pkl').reset_index(drop=True)
        t_start = int(raw.ts.min())
        for wp, lab in who.items():
            xa = raw[raw.wallet.str.startswith(wp)].sort_values('seq')
            x = xa[(xa.side == 'BUY') & (xa.usd >= 100)]
            if not len(x):
                continue
            for d in sorted(set(x.oi)):
                T = load_tape(name, int(d))
                y = x[x.oi == d]
                for k in range(len(y) - 1):
                    r1, r2 = y.iloc[k], y.iloc[k + 1]
                    if int(r2.ts) - int(r1.ts) > W or int(r2.ts) <= int(r1.ts):
                        continue
                    prev = xa[(xa.seq < r1.seq) & (xa.ts >= int(r1.ts) - 86400)]
                    fae = (r1.usd >= 250) and len(prev) == 0
                    i2 = int(np.nonzero((T.tx.values == r2.tx) & (T.wallet.values == r2.wallet))[0][0])
                    r = dict(cas=name, compte=lab, wallet=wp, jeton_oi=int(d), T1=pd.Timestamp(int(r1.ts), unit='s'), usd1=r1.usd, p1=r1.price,
                             T2=pd.Timestamp(int(r2.ts), unit='s'), delta_T1_T2_s=int(r2.ts - r1.ts), usd2=r2.usd, p2=r2.price, SIG_HIST=False,
                             paire='stricte (T1 = FAE)' if fae else 'descriptive (T1 non FAE)', debut_flux=pd.Timestamp(t_start, unit='s'),
                             note='wallet non qualifié SIG_HIST au moment des achats (phase 13) : illustration, pas preuve ; frais c = 0', has_second=True)
                    r.update({f'carnet_{kk}': v for kk, v in book_at_obs(T, i2, r2.wallet, 2).items() if kk != 'L'})
                    r.update({f'prix_{kk}': v for kk, v in price_path(T, i2, r2.wallet).items()})
                    for sm in simulate(T, i2, r2.wallet, 0.0, np.nan, [0, 2, 5]):
                        if sm['est'] == 'FLUX' and sm['S'] == 500:
                            r[f'L{sm["L"]}_statut'] = sm['statut']
                            for H in (60, 300, 600):
                                r[f'L{sm["L"]}_net_{H}_c0'] = sm.get(f'net_{H}') if sm.get(f'obs_{H}') else np.nan
                                r[f'L{sm["L"]}_t_sortie_{H}'] = sm.get(f't_sortie_{H}')
                    rows.append(r)
    # nouveaux wallets (§15)
    S = pd.read_pickle('p14/second.pkl')
    N = pd.read_csv(os.path.expanduser('~/Documents/Crypto/enquete_maduro_iran/phase13/new_wallet_detail.csv'), usecols=['wallet', 't_qualif'])
    sec = S[(S.groupe == 'SIG_HIST')].merge(N, on='wallet', how='left')
    sec['jours_depuis_qualif'] = (sec.T1 - sec.t_qualif) / 86400
    sec['recemment_qualifie'] = (sec.hist_n_T1 < 10) | (sec.jours_depuis_qualif < 30)
    first_alert = sec.sort_values('T1').groupby('wallet').head(1)
    for sp, x in sec.groupby('train_valid_test'):
        for lab, y in (('hist_n 5-9 ou qualifié depuis < 30 j', x[x.recemment_qualifie]), ('qualifié ancien (hist_n >= 10 et >= 30 j)', x[~x.recemment_qualifie])):
            z = y[y.has_second]
            rows.append(dict(cas='nouveaux wallets', split=sp, sous_groupe=lab, alertes=len(y), part_avec_2e_achat=y.has_second.mean() if len(y) else np.nan,
                             n_2e_achats=len(z), LEAD60_2=z.LEAD60_2.mean() if len(z) else np.nan))
        fa = first_alert[first_alert.train_valid_test == sp]
        rows.append(dict(cas='nouveaux wallets', split=sp, sous_groupe='première alerte SIG_HIST du wallet', alertes=len(fa), part_avec_2e_achat=fa.has_second.mean(),
                         n_2e_achats=int(fa.has_second.sum()), LEAD60_2=fa[fa.has_second].LEAD60_2.mean()))
    rows.append(dict(cas='nouveaux wallets', sous_groupe='wallets sans historique (jamais qualifiés)', alertes=0, n_2e_achats=0,
                     note='par construction : un 2e achat SIG_HIST exige un 1er achat SIG_HIST, donc un wallet déjà qualifié'))
    D = pd.DataFrame(rows)
    D.to_csv(OUT + 'phase14_cas.csv', index=False)
    pd.set_option('display.width', 250); pd.set_option('display.max_columns', 30)
    print(D.T.to_string())


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--simuler', action='store_true')
    ap.add_argument('--analyser', action='store_true')
    ap.add_argument('--direct', action='store_true')
    ap.add_argument('--cas', action='store_true')
    a = ap.parse_args()
    if a.simuler:
        simuler()
    if a.analyser:
        analyser()
    if a.direct:
        direct()
    if a.cas:
        cas()
