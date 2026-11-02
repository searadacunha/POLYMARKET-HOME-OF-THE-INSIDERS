#!/usr/bin/env python3
"""Phase 10 : suiveurs et copy-trading (PROTOCOLE_P10 §6).
1. Graphe leader -> suiveur sur les trades >= 100 $ (tout l'historique), avec contrôle temporel symétrique (précurseurs).
2. Par alerte, sur le flux complet : qui déplace le ask entre T0 et T0 + 600 s ?
   Variation du ask = somme des marches dans le carnet des achats (par groupe de wallets) + sauts entre trades (cotations des makers).
3. Suiveurs liés « causaux » (liens construits uniquement avant T0), pour SIG_HIST_SOCIAL.
Sorties : phase10/follower_analysis.csv (couples), follower_summary.csv, follower_attribution.csv ; p10/followers.pkl, p10/linked.pkl"""
import os, sys, collections, bisect
import numpy as np, pandas as pd

# Les pickles lus ici sont produits localement par les scripts p8/p9/p10 ; ne jamais en charger d'autres.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p10_impact import load_tape, leader_index  # noqa: E402

OUT = os.path.expanduser('~/Documents/Crypto/enquete_maduro_iran/phase10/')
WIN = 600
TH_IND = 0.015


def graph():
    EV = pd.read_pickle('p9/events_final.pkl')
    P = pd.read_pickle('p9/prints.pkl')
    leaders = set(EV[EV.SIG_HIST].wallet)
    LE = EV[EV.is_FAE & EV.wallet.isin(leaders) & EV.p_before.notna()][['eid9', 'wallet', 'cid', 'asset', 'd', 'ts', 'price', 'split', 'move_after_exec', 'SIG_HIST']].copy()
    B = P[P.side == 'BUY'][['asset', 'ts', 'wallet', 'price', 'cid', 'rid']].sort_values(['asset', 'ts', 'rid'])
    by = {a: (g.ts.values, g.wallet.values, g.price.values) for a, g in B.groupby('asset')}
    # série de prix par marché (prix YES-équivalent, tous les trades >= 100 $) pour le mouvement indépendant et les rendements
    M = {cid: (g.ts.values, g.p_yes.values, g.wallet.values) for cid, g in P.groupby('cid', sort=False)}

    def p_d(cid, d, t, excl=(), side='left'):
        ts, py, wl = M[cid]
        k = np.searchsorted(ts, t, side=side) - 1
        while k >= 0 and wl[k] in excl:
            k -= 1
        if k < 0:
            return np.nan
        return py[k] if d == 0 else 1 - py[k]

    def ret60(cid, d, t, w, px):
        ts, py, wl = M[cid]
        k = np.searchsorted(ts, t + 3600, side='right') - 1
        k0 = np.searchsorted(ts, t, side='right')
        while k >= k0 and wl[k] == w:
            k -= 1
        if k < k0:
            return 0.0
        return (py[k] if d == 0 else 1 - py[k]) - px

    rows = []
    for e in LE.itertuples():
        ts, wl, pr = by.get(e.asset, (np.array([]), np.array([]), np.array([])))
        i1 = np.searchsorted(ts, e.ts, side='right'); i2 = np.searchsorted(ts, e.ts + WIN, side='right')
        i0 = np.searchsorted(ts, e.ts - WIN, side='left'); ib = np.searchsorted(ts, e.ts, side='left')
        seen = set()
        for k in range(i1, i2):
            f = wl[k]
            if f == e.wallet or f in seen:
                continue
            seen.add(f)
            pm = p_d(e.cid, int(e.d), ts[k], excl=(f, e.wallet))
            rows.append(dict(leader=e.wallet, suiveur=f, sens='aval', eid9=e.eid9, cid=e.cid, split=e.split, t_leader=e.ts, delai_s=int(ts[k] - e.ts),
                             mvt_independant=(pm - e.price) >= TH_IND if pd.notna(pm) else False, prix_suiveur=pr[k],
                             ret_suiveur_60=ret60(e.cid, int(e.d), ts[k], f, pr[k]), ret_leader_60=e.move_after_exec, SIG_HIST=e.SIG_HIST))
        seen = set()
        for k in range(i0, ib):
            f = wl[k]
            if f == e.wallet or f in seen:
                continue
            seen.add(f)
            rows.append(dict(leader=e.wallet, suiveur=f, sens='amont', eid9=e.eid9, cid=e.cid, split=e.split, t_leader=e.ts, delai_s=int(e.ts - ts[k]), SIG_HIST=e.SIG_HIST))
    G = pd.DataFrame(rows)
    G.to_pickle('p10/followers.pkl')
    pairs = []
    for (a, b), g in G.groupby(['leader', 'suiveur']):
        av, am = g[g.sens == 'aval'], g[g.sens == 'amont']
        r = dict(leader=a, suiveur=b, n_aval=len(av), marches_aval=av.cid.nunique(), n_amont=len(am), marches_amont=am.cid.nunique(),
                 delai_med_s=av.delai_s.median() if len(av) else np.nan, part_mvt_independant=av.mvt_independant.mean() if len(av) else np.nan,
                 ret_suiveur_60_moy=av.ret_suiveur_60.mean() if len(av) else np.nan, ret_leader_60_moy=av.ret_leader_60.mean() if len(av) else np.nan,
                 premier_t=g.t_leader.min(), splits=','.join(sorted(set(g.split))))
        if r['marches_aval'] >= 3 and r['marches_aval'] >= 3 * max(r['marches_amont'], 1) and (r['part_mvt_independant'] or 0) < 0.5:
            r['relation'] = 'FOLLOWER'
        elif r['marches_amont'] >= 3 and r['marches_amont'] >= 3 * max(r['marches_aval'], 1):
            r['relation'] = 'LEADER'
        else:
            r['relation'] = 'INDEPENDENT'
        pairs.append(r)
    PR = pd.DataFrame(pairs)
    PR[(PR.marches_aval + PR.marches_amont) >= 2].to_csv(OUT + 'follower_analysis.csv', index=False)
    PR.to_pickle('p10/pairs.pkl')
    # chaînes A -> B -> C : C suit B (dans les 600 s après B) sachant que B a suivi A
    fol = PR[PR.relation == 'FOLLOWER']
    fset = collections.defaultdict(set)
    for r in fol.itertuples():
        fset[r.leader].add(r.suiveur)
    ch = []
    for e, g in G[G.sens == 'aval'].groupby('eid9'):
        g = g.sort_values('delai_s')
        ldr = g.leader.iloc[0]
        fl = [f for f in g.suiveur if f in fset[ldr]]
        others = [f for f in g.suiveur if f not in fset[ldr]]
        ch.append(dict(eid9=e, leader=ldr, SIG_HIST=g.SIG_HIST.iloc[0], n_suiveurs=len(g), n_suiveurs_recurrents=len(fl), chaine_2=len(fl) >= 2, n_autres=len(others)))
    CH = pd.DataFrame(ch)
    # résumé par leader
    summ = []
    for ldr, g in PR.groupby('leader'):
        f = g[g.relation == 'FOLLOWER']
        ev = CH[CH.leader == ldr]
        summ.append(dict(leader=ldr, n_couples=len(g), n_followers=len(f), n_leaders_de_lui=(g.relation == 'LEADER').sum(),
                         repetition_med_marches=f.marches_aval.median() if len(f) else np.nan, delai_med_s=f.delai_med_s.median() if len(f) else np.nan,
                         ret_suiveurs_60_moy=f.ret_suiveur_60_moy.mean() if len(f) else np.nan, ret_leader_60_moy=g.ret_leader_60_moy.mean(),
                         n_fae=ev.eid9.nunique(), part_fae_avec_suiveur_recurrent=(ev.n_suiveurs_recurrents > 0).mean() if len(ev) else np.nan,
                         part_fae_chaine_2=ev.chaine_2.mean() if len(ev) else np.nan))
    SM = pd.DataFrame(summ)
    SM.to_csv(OUT + 'follower_summary.csv', index=False)
    CH.to_pickle('p10/chains.pkl')
    print('couples', len(PR), PR.relation.value_counts().to_dict())
    print('leaders', len(SM), 'avec >=1 FOLLOWER', (SM.n_followers > 0).sum(), 'médiane followers', SM.n_followers.median())
    print('FAE avec suiveur récurrent', CH.groupby('SIG_HIST').apply(lambda x: (x.n_suiveurs_recurrents > 0).mean(), include_groups=False).to_dict())
    return G, PR


def linked(G):
    """Suiveurs liés causaux : >= 2 marchés distincts où le suiveur a acheté dans les 600 s après un FAE du leader, les deux avant T0 - 600 s."""
    W = pd.read_pickle('p10/windows.pkl')
    av = G[G.sens == 'aval'][['leader', 'suiveur', 'cid', 't_leader']].sort_values('t_leader')
    byl = {l: g for l, g in av.groupby('leader')}
    res = {}
    for r in W[W.groupe == 'SIG_HIST'].itertuples():
        g = byl.get(r.wallet)
        if g is None:
            res[r.wid] = set()
            continue
        past = g[g.t_leader + 600 <= int(r.ts) - 600]
        cnt = past.groupby('suiveur').cid.nunique()
        res[r.wid] = set(cnt[cnt >= 2].index)
    pd.to_pickle(res, 'p10/linked.pkl')
    return res


def attribution(PR, LK):
    """Variation du ask entre le trade du wallet et T0 + 600 s : marches des acheteurs (par groupe) + sauts de cotation entre trades."""
    W = pd.read_pickle('p10/windows.pkl')
    fol = PR[PR.relation == 'FOLLOWER']
    fset = collections.defaultdict(set)
    for r in fol.itertuples():
        fset[r.leader].add(r.suiveur)
    rows = []
    for r in W.itertuples():
        if not os.path.exists(f'p10/tapes/{r.wid}.pkl'):
            continue
        T = load_tape(r.wid, int(r.d))
        if T.empty:
            continue
        i = leader_index(T, r.tx, r.wallet)
        if i is None:
            continue
        t0 = int(T.ts.iloc[i])
        lv = T.lv.iloc[i]
        if not lv:
            continue
        prev = lv[-1][0]
        start = prev
        after = T.iloc[i + 1:]
        after = after[after.ts <= t0 + WIN]
        lk = LK.get(r.wid, set())
        contrib = collections.Counter()
        vol = collections.Counter()
        nw = collections.defaultdict(set)
        for w, ae, l2, usd, ts in zip(after.wallet.values, after.ae.values, after.lv.values, after.usd.values, after.ts.values):
            if w == r.wallet:
                grp = 'leader (re-trade)'
            elif w in lk:
                grp = 'suiveurs liés (causal)'
            elif w in fset[r.wallet]:
                grp = 'followers récurrents (graphe)'
            else:
                grp = 'autres'
            key = grp + (' AE' if ae else ' VE')
            vol[key] += usd
            nw[key].add(w)
            if ae and l2:
                contrib['cotations (saut entre trades)'] += l2[0][0] - prev
                contrib[grp + ' : marche dans le carnet'] += l2[-1][0] - l2[0][0]
                prev = l2[-1][0]
        row = dict(wid=r.wid, groupe=r.groupe, split=r.split, LEAD60=r.LEAD60, ask_debut=start, ask_fin=prev, variation_ask=prev - start)
        for k, v in contrib.items():
            row['contrib ' + k] = v
        for k, v in vol.items():
            row['volume ' + k] = v
            row['wallets ' + k] = len(nw[k])
        rows.append(row)
    AT = pd.DataFrame(rows).fillna({c: 0 for c in []})
    AT.to_csv(OUT + 'follower_attribution.csv', index=False)
    cc = [c for c in AT.columns if c.startswith('contrib ')]
    AT[cc] = AT[cc].fillna(0)
    vv = [c for c in AT.columns if c.startswith('volume ') or c.startswith('wallets ')]
    AT[vv] = AT[vv].fillna(0)
    pd.set_option('display.width', 250)
    print(AT.groupby(['groupe', 'split'])[['variation_ask'] + cc].mean().round(4).T.to_string())
    return AT


if __name__ == '__main__':
    G, PR = graph()
    LK = linked(G)
    attribution(PR, LK)
