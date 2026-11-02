#!/usr/bin/env python3
"""Phase 13 : valeur restante entre l'exécution d'un wallet de la watchlist et l'entrée d'un observateur (PROTOCOLE_P13 §4).
Carnet réel de la phase 11, connu à l'instant de décision (p11_replay.Timeline.book_at) ; jamais de profondeur future.
  contrefactuel : entrée à T_EXEC + L (L = 0 à 10 s) -> latency_capture_curve.csv
  réaliste      : entrée à T_DETECT (source la plus rapide réellement enregistrée) + 0 / 100 / 250 ms (envoi de l'ordre, hypothèse)
Événements : (principal) alertes SIG_HIST V1 live ; (élargi) achats >= 250 $ des wallets de la watchlist.
Sorties : phase13/latency_capture_curve.csv, capacity_curve.csv, execution_detail.csv"""
import os, sys, json, time
import numpy as np, pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p11_common import RAW as RAW11  # noqa: E402
from p11_replay import Timeline  # noqa: E402
from p11_execution import walk, fee_per_share, market_meta  # noqa: E402

OUT = os.path.expanduser('~/Documents/Crypto/enquete_maduro_iran/phase13/')
NS = 10 ** 9
LATS = [0, 0.1, 0.25, 0.5, 0.75, 1, 1.5, 2, 3, 5, 10]
SIZES = [50, 100, 250, 500, 1000, 2500, 5000]
EXITS = [60, 300]


def sim(asset, t, tl, meta, cid):
    out = []
    bk = tl.book_at(asset, t)
    if bk is None or not bk.asks:
        return [dict(carnet=False)]
    v = bk.view()
    for S in SIZES:
        sh, cost, vwap, nlv, rest = walk(bk.asks_sorted(), dollars=S)
        if sh <= 0:
            continue
        fin = (fee_per_share(meta, cid, vwap) or 0.0) * sh
        for H in EXITS:
            bx = tl.book_at(asset, t + H * NS)
            if bx is None or not bx.bids:
                continue
            q, proceeds, xv, _, unsold = walk(bx.bids_sorted(), shares=sh)
            fout = (fee_per_share(meta, cid, xv) or 0.0) * q
            mids = [s.view()['mid'] for _, s in tl.path(asset, t, t + H * NS)]
            mids = [m for m in mids if m is not None]
            out.append(dict(carnet=True, S=S, H=H, best_ask=v['best_ask'], mid=v['mid'], spread=v['spread'], VWAP=vwap, slippage_vs_mid=vwap - v['mid'] if v['mid'] else None,
                            taux_remplissage=cost / S, invendu=unsold, brut=(proceeds - cost) / cost, net=(proceeds - cost - fin - fout) / cost,
                            REMAINING_EDGE_mid=(mids[-1] - vwap) if mids else None, MAE=(min(mids) - vwap) if mids else None, MFE=(max(mids) - vwap) if mids else None))
    return out


def main():
    D = pd.read_csv(OUT + 'wallet_trades_live.csv')
    al = [json.loads(l) for l in open(os.path.join(RAW11, 'live', 'alerts.jsonl'))]
    sig_tx = {a['tx'] for a in al}
    ev = D[(D.watchlist) & (D.side == 'BUY') & (D.usd >= 250)].copy()
    ev['groupe'] = np.where(ev.tx.isin(sig_tx), 'SIG_HIST_V1', 'WATCHLIST_ACHAT_250')
    missing = sig_tx - set(ev.tx)
    meta = market_meta(extra=list(set(ev.market)))
    rows = []
    for e in ev.itertuples():
        toks = [str(x) for x in (meta.get(e.market) or {}).get('tokens', [])]
        tl = Timeline([x for x in set(toks + [str(e.asset)])], int(e.T_EXEC_local_ns) - 600 * NS, int(e.T_EXEC_local_ns) + 330 * NS, warm_s=3600)
        base = dict(tx=e.tx, groupe=e.groupe, wallet=e.wallet, market=e.market, usd=e.usd, IDENT_LAT_s=e.IDENT_LAT_s)
        for L in LATS:
            for r in sim(str(e.asset), int(e.T_EXEC_local_ns) + int(L * NS), tl, meta, e.market):
                rows.append(dict(base, scenario='contrefactuel', latence_s=L, **r))
        if e.T_DETECT_ns == e.T_DETECT_ns:
            for envoi in (0, 0.1, 0.25):
                for r in sim(str(e.asset), int(e.T_DETECT_ns) + int(envoi * NS), tl, meta, e.market):
                    rows.append(dict(base, scenario=f'réaliste T_DETECT + {int(envoi * 1000)} ms', latence_s=round((e.T_DETECT_ns - e.T_EXEC_local_ns) / NS + envoi, 3), **r))
    X = pd.DataFrame(rows)
    X.to_csv(OUT + 'execution_detail.csv', index=False)
    ok = X[X.carnet == True] if len(X) else X  # noqa: E712
    cur = []
    for (g, sc, L, S, H), x in ok.groupby(['groupe', 'scenario', 'latence_s', 'S', 'H']) if len(ok) else []:
        cur.append(dict(groupe=g, scenario=sc, latence_s=L, taille_usd=S, sortie_s=H, n=len(x), fill_rate=x.taux_remplissage.mean(), mean_return=x.brut.mean(),
                        median_return=x.brut.median(), net_return=x.net.mean(), net_median=x.net.median(), max_adverse=x.MAE.mean(), max_favorable=x.MFE.mean(),
                        slippage_vs_mid=x.slippage_vs_mid.mean(), spread=x.spread.mean()))
    C = pd.DataFrame(cur)
    if len(C):
        C[C.taille_usd == 500].to_csv(OUT + 'latency_capture_curve.csv', index=False)
        cap = []
        for (g, sc, L, H), x in C.groupby(['groupe', 'scenario', 'latence_s', 'sortie_s']):
            pos = x[x.net_return > 0]
            cap.append(dict(groupe=g, scenario=sc, latence_s=L, sortie_s=H, n=int(x.n.max()), taille_max_positive=pos.taille_usd.max() if len(pos) else 0,
                            **{f'net_{int(s)}': v for s, v in zip(x.taille_usd, x.net_return)}))
        pd.DataFrame(cap).to_csv(OUT + 'capacity_curve.csv', index=False)
    pd.set_option('display.width', 250)
    print('événements', len(ev), ev.groupe.value_counts().to_dict(), 'alertes SIG_HIST sans trade carnet enregistré', len(missing))
    if len(C):
        print(C[(C.taille_usd == 500)].round(4).to_string())


if __name__ == '__main__':
    main()
