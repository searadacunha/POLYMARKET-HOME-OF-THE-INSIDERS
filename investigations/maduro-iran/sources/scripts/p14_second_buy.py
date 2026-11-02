#!/usr/bin/env python3
"""Phase 14 : reconstruction exhaustive des 2e achats, définition de la phase 13 reprise telle quelle (PROTOCOLE_P14 §1).
  2e achat = premier trade preneur BUY >= 100 $ (p9/prints.pkl) du même wallet sur le même jeton, T1 < T2 <= T1 + W, W gelé (phase13/frozen_p13.json).
  Groupes : SIG_HIST (alertes phase 9, inchangées) et CONTROLE (contrôles appariés de la phase 10).
  Vérification bloquante : les T2 et les comptes doivent être identiques à phase13/second_trade_detail.csv ; sinon arrêt.
Sorties : phase14/phase14_second_buy_events.csv (une ligne par alerte ou contrôle, 2e achat ou non), donnees de travail p14/second.pkl
Usage : depuis le dossier de données (p8/, p9/, p10/) : python3 p14_second_buy.py"""
import os, sys, json
import numpy as np, pandas as pd

# Les pickles lus ici sont produits localement par les scripts p8/p9/p10 ; ne jamais en charger d'autres.
P13 = os.path.expanduser('~/Documents/Crypto/enquete_maduro_iran/phase13/')
OUT = os.path.expanduser('~/Documents/Crypto/enquete_maduro_iran/phase14/')
SIGV = json.load(open(os.path.expanduser('~/Documents/Crypto/enquete_maduro_iran/phase11/SIG_HIST_VERSION.json')))


def main():
    EV = pd.read_pickle('p9/events_final.pkl')
    P = pd.read_pickle('p9/prints.pkl')
    A = pd.read_pickle('p8/alltrades.pkl')
    W10 = pd.read_pickle('p10/windows.pkl')
    W = json.load(open(P13 + 'frozen_p13.json'))['W_second']
    tx_of = A.tx.values
    # ---- index identiques à p13_second_trade.second(), avec en plus le rid (pour retrouver la transaction)
    B = P[P.side == 'BUY'].sort_values(['wallet', 'asset', 'ts'])
    Pb = {k: (g.ts.values, g.price.values, g.usd.values, g.rid.values) for k, g in B.groupby(['wallet', 'asset'])}
    M = {c: (g.ts.values, g.p_yes.values, g.wallet.values) for c, g in P.groupby('cid', sort=False)}

    def oth(cid, d, t, h, w):
        ts, py, wl = M[cid]
        a, b = np.searchsorted(ts, t, side='right'), np.searchsorted(ts, t + h, side='right')
        idx = [i for i in range(b - 1, a - 1, -1) if wl[i] != w]
        if not idx:
            return np.nan
        p = py[idx[0]]
        return p if d == 0 else 1 - p

    def before(cid, d, t):
        ts, py, wl = M[cid]
        k = np.searchsorted(ts, t, side='left') - 1
        if k < 0:
            return np.nan
        return py[k] if d == 0 else 1 - py[k]

    def nxt(w, asset, t):
        x = Pb.get((w, asset))
        if x is None:
            return None
        ts, pr, us, rd = x
        a, b = np.searchsorted(ts, t, side='right'), np.searchsorted(ts, t + W, side='right')
        return (ts[a], pr[a], us[a], rd[a]) if b > a else None

    def seq(w, asset, t):
        out = []
        while len(out) < 3:
            n = nxt(w, asset, t)
            if n is None:
                break
            out.append(n); t = n[0]
        return out

    # ---- variables historiques du wallet, observables avant T2
    first_print = P.groupby('wallet').ts.min()
    Pw = {w: (g.ts.values, g.cid.values) for w, g in P.sort_values('ts').groupby('wallet')}
    FF = pd.read_csv(os.path.expanduser('~/Documents/Crypto/enquete_maduro_iran/phase8/wallet_features.csv')).set_index('wallet')
    prior_univ = P.set_index('rid').prior_trades_univ
    sig = EV[EV.SIG_HIST].copy()
    ctl = EV[EV.eid9.isin(W10[W10.groupe == 'CONTROLE'].eid9)].copy()
    wid = {(g, e): w for g, e, w in zip(W10.groupe, W10.eid9, W10.wid)}
    rows = []
    for grp, X in (('SIG_HIST', sig), ('CONTROLE', ctl)):
        for e in X.itertuples():
            s = seq(e.wallet, e.asset, e.ts)
            r = dict(groupe=grp, train_valid_test=e.split, eid9=e.eid9, wid=wid.get((grp, e.eid9)), wallet=e.wallet, token_id=e.asset, market_id=e.cid,
                     market_category=e.cat, d=int(e.d), T1=int(e.ts), first_buy_usd=float(e.usd), first_buy_price=float(e.price), tx1=tx_of[e.rid],
                     hist_n_T1=float(e.hist_n), hist_score_T1=float(e.hist_score), LEAD60_1=float(e.LEAD60), win=e.win, n_achats_suivants=len(s),
                     SIG_HIST_version=f"V1 {SIGV.get('sha256', '')[:16]}", has_second=bool(s))
            if s:
                t2, p2, u2, rid2 = s[0]
                pb2 = before(e.cid, int(e.d), t2)
                p60 = oth(e.cid, int(e.d), t2, 3600, e.wallet)
                ts_w, cs_w = Pw.get(e.wallet, (np.array([]), np.array([])))
                k = np.searchsorted(ts_w, t2, side='left')
                fw = FF.loc[e.wallet] if e.wallet in FF.index else None
                r.update(T2=int(t2), T_OBS_oracle=int(t2), T_OBS=int(t2) + 2, delta_T1_T2=int(t2 - e.ts), second_buy_usd=float(u2), second_buy_price=float(p2),
                         side='BUY', tx2=tx_of[rid2], rid2=int(rid2),
                         wallet_age_at_T2_h=(t2 - first_print[e.wallet]) / 3600, prior_trades_count=int(prior_univ.get(rid2, np.nan)) if pd.notna(prior_univ.get(rid2, np.nan)) else np.nan,
                         prior_trades_100_count=int(k), prior_markets_count=len(set(cs_w[:k])),
                         funding_sample=fw is not None,
                         funding_age_at_T2_h=((t2 - fw.first_inflow_ts) / 3600) if fw is not None and pd.notna(fw.first_inflow_ts) and fw.first_inflow_ts < t2 else np.nan,
                         funding_moonpay=bool(fw.moonpay_any) if fw is not None and pd.notna(fw.moonpay_any) else np.nan,
                         p_before_2=pb2, mvt_apres_2=(p60 - p2) if p60 == p60 else 0.0,
                         LEAD60_2=float((p60 - pb2) >= 0.03) if p60 == p60 and pb2 == pb2 else 0.0)
            rows.append(r)
    S = pd.DataFrame(rows)
    # ---- vérification bloquante contre la phase 13
    D13 = pd.read_csv(P13 + 'second_trade_detail.csv')
    m = S.merge(D13[['groupe', 'eid9', 'T2', 'n_achats_suivants', 'lead60_2']], on=['groupe', 'eid9'], how='outer', suffixes=('', '_p13'), indicator=True)
    ok_rows = (m._merge == 'both').all()
    ok_t2 = ((m.T2.fillna(-1) == m.T2_p13.fillna(-1))).all()
    ok_n = (m.n_achats_suivants == m.n_achats_suivants_p13).all()
    ok_l = (m.LEAD60_2.fillna(-1) == m.lead60_2.astype(float).fillna(-1)).all()
    cnt = S[S.has_second].groupby(['groupe', 'train_valid_test']).size()
    print('vérification phase 13 : lignes', ok_rows, 'T2', ok_t2, 'n suivants', ok_n, 'LEAD60_2', ok_l)
    print(cnt.to_string())
    if not (ok_rows and ok_t2 and ok_n and ok_l):
        print('ARRÊT : la définition de la phase 13 n est pas reproduite exactement')
        sys.exit(2)
    os.makedirs('p14', exist_ok=True)
    S.to_pickle('p14/second.pkl')
    cols = ['wallet', 'token_id', 'market_id', 'T1', 'T2', 'T_OBS', 'T_OBS_oracle', 'delta_T1_T2', 'first_buy_usd', 'second_buy_usd', 'first_buy_price', 'second_buy_price',
            'side', 'market_category', 'wallet_age_at_T2_h', 'prior_trades_count', 'prior_trades_100_count', 'prior_markets_count', 'funding_sample', 'funding_age_at_T2_h',
            'funding_moonpay', 'SIG_HIST_version', 'train_valid_test', 'groupe', 'eid9', 'wid', 'hist_n_T1', 'hist_score_T1', 'LEAD60_1', 'p_before_2', 'LEAD60_2',
            'mvt_apres_2', 'n_achats_suivants', 'tx1', 'tx2']
    S[S.has_second][cols].to_csv(OUT + 'phase14_second_buy_events.csv', index=False)
    print('2e achats écrits', int(S.has_second.sum()), 'sur', len(S), 'événements')


if __name__ == '__main__':
    main()
