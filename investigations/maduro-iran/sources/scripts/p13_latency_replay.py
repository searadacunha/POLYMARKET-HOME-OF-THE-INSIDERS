#!/usr/bin/env python3
"""Phase 13 : les trois temps de chaque trade d'un wallet de la watchlist, dans les données live de la phase 11 (lecture seule).
  T_EXEC   : heure d'échange (ms) du last_trade_price portant le hash ; T_EXEC_local = sa réception locale
  T_DETECT : réception locale du premier message identifiant le wallet, par source (RTDS ; logs Polygon filtrés sur les wallets SIG_HIST)
Sortie : phase13/wallet_trades_live.csv (un trade par ligne, toutes les sources), phase13/wallet_watchlist.csv
Usage : python3 p13_latency_replay.py [--debut 2026-10-01T08:52]"""
import os, sys, json, time, argparse
import numpy as np, pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p11_common import RAW as RAW11, DATA  # noqa: E402
from p11_replay import iter_raw, events  # noqa: E402

OUT = os.path.expanduser('~/Documents/Crypto/enquete_maduro_iran/phase13/')


def watchlist():
    """KNOWN_HIGH_LEAD (qualifié, hist_n >= 10), NEWLY_QUALIFIED (qualifié, hist_n 5-9), à partir de l'état du détecteur V1 au démarrage du listener
    (wallets_eligibles_au_demarrage.json) et des historiques de la phase 9. Fichier local, jamais publié."""
    elig = set(json.load(open(os.path.join(RAW11, 'live', 'wallets_eligibles_au_demarrage.json'))))
    EV = pd.read_pickle(os.path.join(DATA, 'p9', 'events_final.pkl'))          # pickle local (phase 9)
    b = EV[EV.is_FAE & ~EV.FOLLOW & EV.p_before.notna()]
    last = b.sort_values('ts').groupby('wallet').last()
    rows = []
    leaders = set(EV[EV.SIG_HIST].wallet)
    for w in sorted(elig | leaders):
        n = float(last.hist_n.get(w, 0)) + 1 if w in last.index else 0
        rows.append(dict(wallet=w, eligible_au_demarrage=w in elig, a_declenche_SIG_HIST_historique=w in leaders,
                         hist_n_dernier_evenement_phase9=float(last.hist_n.get(w, np.nan)), hist_score_dernier_evenement_phase9=float(last.hist_score.get(w, np.nan))))
    W = pd.DataFrame(rows)
    W['classe'] = np.where(~W.eligible_au_demarrage, 'UNKNOWN (non qualifié au démarrage)', np.where(W.hist_n_dernier_evenement_phase9 >= 10, 'KNOWN_HIGH_LEAD', 'NEWLY_QUALIFIED'))
    W.to_csv(OUT + 'wallet_watchlist.csv', index=False)
    print(W.classe.value_counts().to_dict())
    return W


def main(t0, t1):
    W = watchlist()
    wl = set(W[W.eligible_au_demarrage].wallet)
    ltp = {}
    for t, conn, msg in iter_raw('ws_market', t0, t1):
        for e in events(msg):
            if e.get('event_type') == 'last_trade_price' and e.get('transaction_hash'):
                h = e['transaction_hash']
                if h not in ltp:
                    ltp[h] = dict(T_EXEC_ms=int(e['timestamp']), T_EXEC_local_ns=t, market=e['market'], asset=e['asset_id'], side=e['side'],
                                  price=float(e['price']), size=float(e['size']))
    rt = {}
    for t, conn, msg in iter_raw('rtds', t0, t1):
        if isinstance(msg, str) and msg.startswith('{'):
            p = json.loads(msg).get('payload') or {}
            h = p.get('transactionHash')
            if h and h in ltp:
                rt.setdefault(h, []).append((t, p))
    ch = {}
    for t, conn, msg in iter_raw('chain', t0, t1):
        if isinstance(msg, str) and 'transactionHash' in msg:
            try:
                r = (json.loads(msg).get('params') or {}).get('result') or {}
            except Exception:
                continue
            h = r.get('transactionHash')
            if h and h not in ch:
                ch[h] = t
    rows = []
    for h, x in ltp.items():
        rr = rt.get(h, [])
        tk = [p for t, p in rr if p.get('fee') is not None] or [p for t, p in rr]
        wal = tk[0]['proxyWallet'].lower() if tk else None
        t_rtds = min((t for t, p in rr), default=None)
        t_ch = ch.get(h)
        cand = [v for v in (t_rtds, t_ch) if v]
        rows.append(dict(tx=h, **x, usd=x['price'] * x['size'], wallet=wal, watchlist=wal in wl, T_DETECT_rtds_ns=t_rtds, T_DETECT_chaine_ns=t_ch,
                         T_DETECT_ns=min(cand) if cand else None))
    D = pd.DataFrame(rows)
    for c in ('rtds', 'chaine'):
        D[f'IDENT_LAT_{c}_s'] = (D[f'T_DETECT_{c}_ns'] - D.T_EXEC_local_ns) / 1e9
    D['IDENT_LAT_s'] = (D.T_DETECT_ns - D.T_EXEC_local_ns) / 1e9
    D['IDENT_LAT_vs_echange_s'] = D.T_DETECT_ns / 1e9 - D.T_EXEC_ms / 1e3
    D.to_csv(OUT + 'wallet_trades_live.csv', index=False)
    w = D[D.watchlist]
    print('trades carnet', len(D), 'identifiés', int(D.wallet.notna().sum()), 'wallets de la watchlist', len(w), 'achats >= 250 $', int(((w.side == 'BUY') & (w.usd >= 250)).sum()))
    print(w[['IDENT_LAT_rtds_s', 'IDENT_LAT_chaine_s', 'IDENT_LAT_s']].describe(percentiles=[.1, .5, .9, .99]).round(3).to_string())


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--debut', default='2026-10-01T08:52')
    a = ap.parse_args()
    main(int(pd.Timestamp(a.debut, tz='UTC').value), time.time_ns() - 90 * 10 ** 9)
