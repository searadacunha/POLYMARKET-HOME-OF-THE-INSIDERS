#!/usr/bin/env python3
"""Phase 13 : analyses historiques wallet-aware (PROTOCOLE_P13 §3, §5 à §8). SIG_HIST V1 inchangé.
  --watchlist : détecteur V1 rejoué (historique phase 9 + rattrapage phase 11) -> phase13/wallet_watchlist.csv (local, jamais publié)
  --second    : SIG_HIST_SECOND (W gelé sur TRAIN), continuation, positions, wallet déjà actif -> second_trade.csv, continuation.csv, positions.csv, wallet_actif.csv
  --nouveaux  : limite des nouveaux wallets et filtres de priorisation -> new_wallet_limit.csv, priorisation.csv
  --cas       : 8 comptes, Maduro et Iran -> comptes_8.csv, maduro_wallet_replay.csv, iran_wallet_replay.csv
Usage : depuis le dossier de données (p8/, p9/, p10/)."""
import os, sys, json, gzip, argparse, collections, bisect
import numpy as np, pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p9_detector import Detecteur  # noqa: E402

# Les pickles lus ici sont produits localement par les scripts p8/p9/p10 ; ne jamais en charger d'autres.
OUT = os.path.expanduser('~/Documents/Crypto/enquete_maduro_iran/phase13/')
RAW11 = os.path.expanduser('~/Documents/Crypto/enquete_maduro_iran/donnees/brut_p11')
FZ = OUT + 'frozen_p13.json'
LAT = {'P10': 0.84, 'P50': 1.75, 'P90': 2.56}          # CLOB -> wallet, mesuré en direct (phase 12)
A8 = {'0x168b100d7a6620a2f49a455344c2c006eaf1714b': 'Chiwawas', '0x5621116629c5d640c8186f577362478cc6605245': 'TacticalInsiderNews',
      '0x38745db27f7360a287f6ca3c9b6a6a9c76149801': 'Planktonbets', '0x60280beffdfeaf962de4e6397ab49ed05a1b99e1': 'X34',
      '0x834079f62fa9b4b0bdfad5b8b7a841e8267da024': 'chileno777', '0xbf32f7a77ccea8bba647fea63d438ce1778b1762': '154x838hjd6',
      '0x56efadc9defe5b7a21af751e0d026f2cf54136db': 'Neodbs', '0xe9b80c387ba77a585423b13c850c2e126c3befd8': 'Mrs.Joker'}


def load():
    EV = pd.read_pickle('p9/events_final.pkl')
    P = pd.read_pickle('p9/prints.pkl')
    spec = json.load(open(os.path.expanduser('~/Documents/Crypto/enquete_maduro_iran/phase9/frozen_spec.json')))
    return EV, P, spec


class Paths:
    """Prix YES-équivalent par marché (trades >= 100 $), pour mesurer les mouvements sur les trades des AUTRES wallets."""
    def __init__(self, P):
        self.M = {c: (g.ts.values, g.p_yes.values, g.wallet.values) for c, g in P.groupby('cid', sort=False)}

    def oth(self, cid, d, t, h, w):
        ts, py, wl = self.M[cid]
        a, b = np.searchsorted(ts, t, side='right'), np.searchsorted(ts, t + h, side='right')
        idx = [i for i in range(b - 1, a - 1, -1) if wl[i] != w]
        if not idx:
            return np.nan
        p = py[idx[0]]
        return p if d == 0 else 1 - p

    def before(self, cid, d, t):
        ts, py, wl = self.M[cid]
        k = np.searchsorted(ts, t, side='left') - 1
        if k < 0:
            return np.nan
        return py[k] if d == 0 else 1 - py[k]


def buys_after(Pb, w, asset, t, W):
    x = Pb.get((w, asset))
    if x is None:
        return []
    ts, pr, us = x
    a, b = np.searchsorted(ts, t, side='right'), np.searchsorted(ts, t + W, side='right')
    return list(zip(ts[a:b], pr[a:b], us[a:b]))


def second(EV, P, spec):
    paths = Paths(P)
    B = P[P.side == 'BUY'].sort_values(['wallet', 'asset', 'ts'])
    Pb = {k: (g.ts.values, g.price.values, g.usd.values) for k, g in B.groupby(['wallet', 'asset'])}
    W10 = pd.read_pickle('p10/windows.pkl')
    base = EV.is_FAE & ~EV.FOLLOW & EV.p_before.notna()
    sig = EV[EV.SIG_HIST]
    ctl = EV[EV.eid9.isin(W10[W10.groupe == 'CONTROLE'].eid9)]

    def seq(e, W):
        """Achats successifs du même wallet sur le même jeton, chaque écart < W."""
        out = []
        t = e.ts
        while len(out) < 3:
            nxt = buys_after(Pb, e.wallet, e.asset, t, W)
            if not nxt:
                break
            out.append(nxt[0]); t = nxt[0][0]
        return out

    def outc(e, t2, p2):
        pb2 = paths.before(e.cid, int(e.d), t2)
        p60 = paths.oth(e.cid, int(e.d), t2, 3600, e.wallet)
        return dict(p_before_2=pb2, mvt_apres_2=(p60 - p2) if p60 == p60 else 0.0, lead60_2=float((p60 - pb2) >= 0.03) if p60 == p60 and pb2 == pb2 else 0.0)

    # ---- choix de W sur TRAIN uniquement
    if not os.path.exists(FZ):
        tr = sig[sig.split == 'TRAIN']
        best = None
        for W in (300, 1800, 3600):
            n = 0
            for e in tr.itertuples():
                s = seq(e, W)
                if s:
                    o = outc(e, s[0][0], s[0][1])
                    n += int(o['lead60_2'])
            best = max(best or (n, W), (n, W))
            print('W', W, 'seconds achats suivis de +3 points (TRAIN)', n)
        json.dump(dict(W_second=int(best[1]), choisi_sur='TRAIN, max du nombre de seconds achats suivis de +3 points à 60 min', gele_le=pd.Timestamp.utcnow().isoformat()), open(FZ, 'w'), indent=1)
    W = json.load(open(FZ))['W_second']
    rows, crow = [], []
    for grp, X in (('SIG_HIST', sig), ('CONTROLE', ctl)):
        for e in X.itertuples():
            s = seq(e, W)
            r = dict(groupe=grp, split=e.split, eid9=e.eid9, wallet=e.wallet, cid=e.cid, T1=int(e.ts), p1=float(e.price), usd1=float(e.usd), LEAD60_1=float(e.LEAD60),
                     mvt_apres_1=float(e.move_after_exec) if e.move_after_exec == e.move_after_exec else np.nan, n_achats_suivants=len(s))
            if s:
                t2, p2, u2 = s[0]
                o = outc(e, t2, p2)
                r.update(T2=int(t2), p2=float(p2), usd2=float(u2), delai_12_s=int(t2 - e.ts), delai_dispo_apres_detection_s=float(t2 - e.ts - LAT['P50']),
                         derive_12=(o['p_before_2'] - float(e.price)) if o['p_before_2'] == o['p_before_2'] else np.nan, **o)
            rows.append(r)
            crow.append(dict(groupe=grp, split=e.split, rang=1, mvt_apres=r['mvt_apres_1'], lead60=r['LEAD60_1'], usd=r['usd1']))
            for k, (t, p, u) in enumerate(s, start=2):
                o = outc(e, t, p)
                crow.append(dict(groupe=grp, split=e.split, rang=k, mvt_apres=o['mvt_apres_2'], lead60=float(o['lead60_2']), usd=u))
    S = pd.DataFrame(rows)
    S.to_csv(OUT + 'second_trade_detail.csv', index=False)
    agg = []
    for (g, sp), x in S.groupby(['groupe', 'split']):
        y = x[x.n_achats_suivants > 0]
        agg.append(dict(groupe=g, split=sp, W_s=W, n_alertes=len(x), part_avec_2e_achat=len(y) / len(x), delai_12_median_s=y.delai_12_s.median(),
                        part_2e_avant_detection=(y.delai_12_s < LAT['P50']).mean() if len(y) else np.nan, derive_12_moy=y.derive_12.mean(),
                        LEAD60_1=x.LEAD60_1.mean(), mvt_apres_1_moy=x.mvt_apres_1.mean(), LEAD60_2=y.lead60_2.mean() if len(y) else np.nan,
                        mvt_apres_2_moy=y.mvt_apres_2.mean() if len(y) else np.nan, mvt_apres_2_med=y.mvt_apres_2.median() if len(y) else np.nan))
    A = pd.DataFrame(agg)
    A.to_csv(OUT + 'second_trade.csv', index=False)
    C = pd.DataFrame(crow)
    cont = C.groupby(['groupe', 'split', 'rang']).agg(n=('mvt_apres', 'size'), mvt_apres_moy=('mvt_apres', 'mean'), mvt_apres_med=('mvt_apres', 'median'),
                                                      LEAD60=('lead60', 'mean'), usd_med=('usd', 'median')).reset_index()
    cont.to_csv(OUT + 'continuation.csv', index=False)
    pd.set_option('display.width', 250)
    print(A.round(4).to_string()); print(cont[cont.split != 'TRAIN'].round(4).to_string())
    # ---- positions avant / après (trades >= 100 $ du wallet sur le jeton)
    Pw = P.sort_values('ts').groupby(['wallet', 'asset'])
    pos_idx = {k: (g.ts.values, np.where(g.side.values == 'BUY', g.usd.values / g.price.values, -g.usd.values / g.price.values)) for k, g in Pw}
    prow = []
    for grp, X in (('SIG_HIST', sig), ('CONTROLE', ctl)):
        for e in X.itertuples():
            ts, q = pos_idx.get((e.wallet, e.asset), (np.array([]), np.array([])))
            k = np.searchsorted(ts, e.ts, side='left')
            before = float(q[:k].sum())
            sh = e.usd / e.price
            prow.append(dict(groupe=grp, split=e.split, position_avant=before, position_apres=before + sh, classe='nouvelle position' if before <= 0.1 * sh else 'renforcement',
                             LEAD60=float(e.LEAD60), mvt_apres_exec=e.move_after_exec))
    PO = pd.DataFrame(prow)
    pa = PO.groupby(['groupe', 'split', 'classe']).agg(n=('LEAD60', 'size'), LEAD60=('LEAD60', 'mean'), mvt_apres_exec=('mvt_apres_exec', 'mean')).reset_index()
    pa.to_csv(OUT + 'positions.csv', index=False)
    print(pa[pa.split != 'TRAIN'].round(4).to_string())
    # ---- wallet déjà actif avant le trade (trades >= 100 $, tous marchés)
    Pa = {w: (g.ts.values, g.cid.values) for w, g in P.sort_values('ts').groupby('wallet')}
    arow = []
    for grp, X in (('SIG_HIST', sig), ('CONTROLE', ctl)):
        for e in X.itertuples():
            ts, cs = Pa.get(e.wallet, (np.array([]), np.array([])))
            k = np.searchsorted(ts, e.ts, side='left')
            a24 = np.searchsorted(ts, e.ts - 86400, side='left')
            a10 = np.searchsorted(ts, e.ts - 600, side='left')
            arow.append(dict(groupe=grp, split=e.split, depuis_dernier_trade_s=(e.ts - ts[k - 1]) if k > 0 else np.nan, trades_24h=k - a24, marches_24h=len(set(cs[a24:k])),
                             actif_10min=k - a10 > 0))
    AC = pd.DataFrame(arow)
    ac = AC.groupby(['groupe', 'split']).agg(n=('trades_24h', 'size'), depuis_dernier_med_s=('depuis_dernier_trade_s', 'median'), trades_24h_med=('trades_24h', 'median'),
                                             marches_24h_moy=('marches_24h', 'mean'), part_actif_10min=('actif_10min', 'mean')).reset_index()
    ac.to_csv(OUT + 'wallet_actif.csv', index=False)
    print(ac.round(3).to_string())


def nouveaux(EV, P, spec):
    thr = spec['hist_threshold']
    base = EV[EV.is_FAE & ~EV.FOLLOW & EV.p_before.notna()].sort_values('ts')
    first = P.groupby('wallet').ts.min()
    last = P.groupby('wallet').ts.max()
    t_end = P.ts.max()
    rows = []
    for w, g in base.groupby('wallet'):
        q = g[(g.hist_n >= 5) & (g.hist_score >= thr)]
        rows.append(dict(wallet=w, n_fae=len(g), hist_n_max=g.hist_n.max(), qualifie=len(q) > 0, premier_trade=first.get(w), dernier_trade=last.get(w),
                         t_qualif=q.ts.min() if len(q) else np.nan, fae_avant_qualif=int((g.ts < q.ts.min()).sum()) if len(q) else np.nan,
                         alerte_SIG=bool(g.SIG_HIST.any())))
    N = pd.DataFrame(rows)
    N['jours_jusqu_qualif'] = (N.t_qualif - N.premier_trade) / 86400
    N['disparu'] = (~N.qualifie) & (N.hist_n_max < 5) & ((t_end - N.dernier_trade) > 30 * 86400)
    out = [dict(mesure='wallets avec au moins 1 FAE non-FOLLOW', valeur=len(N)),
           dict(mesure='atteignent 5 FAE résolus (hist_n >= 5)', valeur=int((N.hist_n_max >= 5).sum())),
           dict(mesure='se qualifient un jour (hist_n >= 5 et score >= seuil)', valeur=int(N.qualifie.sum())),
           dict(mesure='déclenchent au moins une alerte SIG_HIST', valeur=int(N.alerte_SIG.sum())),
           dict(mesure='FAE avant la qualification : médiane', valeur=N[N.qualifie].fae_avant_qualif.median()),
           dict(mesure='FAE avant la qualification : P25 / P75', valeur=f"{N[N.qualifie].fae_avant_qualif.quantile(.25)} / {N[N.qualifie].fae_avant_qualif.quantile(.75)}"),
           dict(mesure='jours entre le premier trade et la qualification : médiane', valeur=N[N.qualifie].jours_jusqu_qualif.median()),
           dict(mesure='jours : P25 / P75 / P90', valeur='{:.1f} / {:.1f} / {:.1f}'.format(*N[N.qualifie].jours_jusqu_qualif.quantile([.25, .75, .9]).values)),
           dict(mesure='wallets à 1-4 FAE résolus inactifs depuis plus de 30 jours (disparus avant qualification)', valeur=int(N.disparu.sum())),
           dict(mesure='part des wallets jamais qualifiés qui ont disparu', valeur=float(N[~N.qualifie].disparu.mean()))]
    for n in (1, 2, 3, 4, 5, 10, 20):
        out.append(dict(mesure=f'wallets avec au moins {n} FAE', valeur=int((N.n_fae >= n).sum())))
    pd.DataFrame(out).to_csv(OUT + 'new_wallet_limit.csv', index=False)
    N.to_csv(OUT + 'new_wallet_detail.csv', index=False)
    print(pd.DataFrame(out).to_string())
    # ---- filtres de priorisation (échantillon financement de la phase 8)
    WF = pd.read_csv(os.path.expanduser('~/Documents/Crypto/enquete_maduro_iran/phase8/wallet_features.csv'))
    WF['wallet'] = WF.wallet.str.lower()
    X = WF.merge(N[['wallet', 'qualifie', 'premier_trade', 'n_fae']], on='wallet', how='left')
    X['qualifie'] = X.qualifie.fillna(False)
    X['age_premier_trade_j'] = (X.premier_trade - X.first_inflow_ts) / 86400
    X['classe_age'] = pd.cut(X.age_premier_trade_j, [-1e9, 1, 7, 30, 1e9], labels=['< 1 j', '1-7 j', '7-30 j', '> 30 j'])
    pr = []
    for col in ('classe_age', 'moonpay_any'):
        for v, g in X.groupby(col, observed=True):
            pr.append(dict(filtre=col, valeur=str(v), n_wallets=len(g), taux_qualification=g.qualifie.mean()))
    pd.DataFrame(pr).to_csv(OUT + 'priorisation.csv', index=False)
    print(pd.DataFrame(pr).round(4).to_string())


def replay_hist(queries):
    """Rejoue le détecteur V1 sur les trades >= 100 $ et lit l'historique de chaque wallet à l'instant demandé (état causal)."""
    P = pd.read_pickle('p9/prints.pkl')
    det = Detecteur(differe=True)
    cols = ['ts', 'cid', 'cat', 'end', 'wallet', 'side', 'asset', 'price', 'usd', 'oi', 'rid']
    queries = sorted(queries)
    out = {}
    qi = 0
    for row in zip(*[P[c].values for c in cols]):
        while qi < len(queries) and queries[qi][0] < row[0]:
            t, w = queries[qi]
            det._resoudre(t)
            n, l = det.hist[w]
            out[(t, w)] = (n, l, (l + 10 * det.p0) / (n + 10), det.n_univ[w])
            qi += 1
        det.traiter(dict(zip(cols, row)))
        det.lignes = []
    return out, det.hthr


def cas(EV, P, spec):
    from p10_impact import load_tape
    T_ = lambda s: int(pd.Timestamp(s, tz='UTC').timestamp())
    # ---- 8 comptes
    elig = set(json.load(open(os.path.join(RAW11, 'live', 'wallets_eligibles_au_demarrage.json'))))
    base = EV[EV.is_FAE & ~EV.FOLLOW & EV.p_before.notna()]
    WF = pd.read_csv(os.path.expanduser('~/Documents/Crypto/enquete_maduro_iran/phase8/wallet_features.csv')); WF['wallet'] = WF.wallet.str.lower()
    rows = []
    for w, lab in A8.items():
        g = base[base.wallet == w]; p = P[P.wallet == w]
        f = WF[WF.wallet == w]
        rows.append(dict(compte=lab, wallet=w, dans_watchlist_live=w in elig, trades_100=len(p), fae=len(g), hist_n_max=g.hist_n.max() if len(g) else 0,
                         jamais_qualifie=not ((g.hist_n >= 5) & (g.hist_score >= spec['hist_threshold'])).any(), alertes_SIG=int(g.SIG_HIST.sum()),
                         achats_meme_jeton_apres_fae=int(sum(((p.asset == e.asset) & (p.side == 'BUY') & (p.ts > e.ts) & (p.ts <= e.ts + 3600)).sum() for e in g.itertuples())),
                         financement_moonpay=bool(f.moonpay_any.iloc[0]) if len(f) else None, premier_afflux=str(pd.to_datetime(f.first_inflow_ts.iloc[0], unit='s')) if len(f) and f.first_inflow_ts.iloc[0] == f.first_inflow_ts.iloc[0] else None))
    pd.DataFrame(rows).to_csv(OUT + 'comptes_8.csv', index=False)
    print(pd.DataFrame(rows).to_string())
    # ---- Maduro et Iran : statut V1, T_EXEC, T_DETECT estimé, prix observé, repricing, événement public
    CAS = {'maduro': dict(tape='EVT_MADURO', trades=[('0x31a56e9e690c621ed21de08cb559e9524cdb8ed9', '2026-01-03 01:38:35'), ('0x31a56e9e690c621ed21de08cb559e9524cdb8ed9', '2026-01-03 02:15:05'),
                                                     ('0x31a56e9e690c621ed21de08cb559e9524cdb8ed9', '2026-01-03 02:58:25'), ('0x6baf05d193692bb208d616709e27442c910a94c5', '2026-01-03 03:42:01')],
                          rep=[('repricing CLOB (1,5 x)', '2026-01-03 06:16:11', 'MESURÉ'), ('premier trade >= 0,5', '2026-01-03 06:15:41', 'MESURÉ')],
                          pub=[('premières explosions', '2026-01-03 06:00:00', 'APPROXIMATE'), ('annonce de Trump', '2026-01-03 09:21:00', 'APPROXIMATE')]),
           'iran': dict(tape='EVT_IRAN', trades=[('0x4dfd481c16d9995b809780fd8a9808e8689f6e4a', '2026-02-28 05:15:53'), ('0x4dfd481c16d9995b809780fd8a9808e8689f6e4a', '2026-02-28 05:21:55'),
                                                 ('0x4dfd481c16d9995b809780fd8a9808e8689f6e4a', '2026-02-28 05:33:47')],
                        rep=[('repricing CLOB (1,5 x)', '2026-02-28 06:13:22', 'MESURÉ'), ('premier trade >= 0,5', '2026-02-28 06:12:17', 'MESURÉ'),
                             ('début de l anomalie, référence glissante 12 h', '2026-02-28 05:15:00', 'MESURÉ (définition 1)'), ('début de l anomalie, référence veille', '2026-02-28 06:10:00', 'MESURÉ (définition 2)')],
                        pub=[('début des frappes', '2026-02-28 06:15:00', 'APPROXIMATE'), ('annonce israélienne (Katz)', '2026-02-28 06:23:00', 'VERIFIED')])}
    q = [(T_(t), w) for c in CAS.values() for w, t in c['trades']]
    hist, hthr = replay_hist(q)
    for nom, c in CAS.items():
        T = load_tape(c['tape'], 0)
        tsv, pdv, wv = T.ts.values, T.pd.values, T.wallet.values

        def prix_obs(t, excl):
            """Prix YES du prochain trade d'un autre wallet à partir de t (observation, pas une garantie d'exécution), et son délai."""
            k = np.searchsorted(tsv, t, side='left')
            while k < len(tsv) and wv[k] == excl:
                k += 1
            return (float(pdv[k]), float(tsv[k] - t)) if k < len(tsv) else (np.nan, np.nan)

        def prix_dernier(t):
            k = np.searchsorted(tsv, t, side='right') - 1
            return float(pdv[k]) if k >= 0 else np.nan
        rows = []
        for w, ts in c['trades']:
            t = T_(ts)
            n, l, sc, nu = hist[(t, w)]
            r = T[(T.ts == t) & (T.wallet == w)]
            px = float(r.pd.iloc[0]) if len(r) else np.nan
            usd = float(r.usd.sum()) if len(r) else np.nan
            row = dict(wallet=w[:10], T_EXEC=ts, usd=round(usd, 2), prix_paye_yes=px, hist_n=n, hist_lead=l, hist_score=round(sc, 4), trades_anterieurs_100=nu,
                       qualifie_SIG_HIST_V1=bool(n >= 5 and sc >= hthr))
            for k, lat in LAT.items():
                p, dl = prix_obs(t + lat, w)
                row[f'T_DETECT_{k}'] = f'+{lat} s'
                row[f'prix_obs_apres_detect_{k}'] = p
                row[f'delai_prochain_trade_{k}_s'] = dl
            row['prix_+60s'] = prix_dernier(t + 60); row['prix_+300s'] = prix_dernier(t + 300); row['prix_+3600s'] = prix_dernier(t + 3600)
            for lab, h, niv in c['rep'] + c['pub']:
                row[f'prix_a: {lab} ({niv}, {h[11:16]})'] = prix_dernier(T_(h))
            rows.append(row)
        D = pd.DataFrame(rows)
        D.to_csv(OUT + f'{nom}_wallet_replay.csv', index=False)
        pd.set_option('display.width', 250); pd.set_option('display.max_columns', 40)
        print(nom); print(D.T.to_string())


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    for k in ('second', 'nouveaux', 'cas'):
        ap.add_argument('--' + k, action='store_true')
    a = ap.parse_args()
    EV, P, spec = load()
    if a.second:
        second(EV, P, spec)
    if a.nouveaux:
        nouveaux(EV, P, spec)
    if a.cas:
        cas(EV, P, spec)
