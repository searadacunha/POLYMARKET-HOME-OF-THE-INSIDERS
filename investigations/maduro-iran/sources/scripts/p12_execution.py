#!/usr/bin/env python3
"""Phase 12 : rejoue les données live de la phase 11 (lecture seule) à travers le détecteur sans wallet, et simule l'exécution
sur le carnet CONNU à l'instant de décision (PROTOCOLE_P12 §6.4). Aucun ordre n'est passé.
Un ordonnanceur exécute chaque entrée et chaque sortie au moment où la relecture atteint cette heure : le carnet utilisé est
exactement celui reconstruit à partir des messages reçus avant (jamais de profondeur future).
Contrôle : candidats non signalés (score B2 sous la médiane des candidats), même marché, heure la plus proche.
Sortie : phase12/pre_wallet_execution.csv (agrégé), phase12/live_candidats.csv (détail), phase12/live_alerts.csv (signaux rejoués)
Usage : python3 p12_execution.py [--debut 2026-10-01T08:52] [--fin maintenant-2min]"""
import os, sys, json, glob, heapq, argparse, time, collections
import numpy as np, pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p11_common import RAW as RAW11, OUT as OUT11  # noqa: E402
from p11_replay import iter_raw, events  # noqa: E402
from p12_pre_wallet_detector import PreWalletDetector, _vwap  # noqa: E402

OUT = os.path.expanduser('~/Documents/Crypto/enquete_maduro_iran/phase12/')
NS = 10 ** 9
LATS = [0, 0.1, 0.25, 0.5, 1, 2, 5]
SIZES = [50, 100, 250, 500, 1000]
EXITS = [60, 300]
CHECK = [1, 5, 10, 30, 60, 120, 300]


def meta11():
    m = {}
    for fp in sorted(glob.glob(os.path.join(RAW11, 'meta', 'watchlist_*.json'))):
        for c, x in json.load(open(fp))['watchlist'].items():
            m.setdefault(c, x)
    for l in open(os.path.join(RAW11, 'meta', 'dynamic_watch.jsonl')) if os.path.exists(os.path.join(RAW11, 'meta', 'dynamic_watch.jsonl')) else []:
        d = json.loads(l)
        m.setdefault(d['cid'], dict(tokens=d['tokens']))
    return m


def fee(meta, cid, p):
    x = meta.get(cid) or {}
    if x.get('feesEnabled') is False:
        return 0.0
    fs = x.get('feeSchedule') or {}
    return float(fs.get('rate', 0.0)) * min(p, 1 - p) ** float(fs.get('exponent', 1)) if fs else np.nan


def walk_bids(bids, shares):
    got, left = 0.0, shares
    for p, s in sorted(bids.items(), reverse=True):
        q = min(left, s); got += q * p; left -= q
        if left <= 1e-9:
            break
    return got, left


def run(t0, t1):
    meta = meta11()
    toks = {c: [str(t) for t in x.get('tokens', [])] for c, x in meta.items()}
    det = PreWalletDetector(toks)
    cand, b1 = [], []
    tasks = []                                            # (heure_ns, seq, fonction, argument)
    seq = 0
    last_b1 = {}

    def book(asset):
        m = det.asset_market.get(asset)
        return det.mk[m].books[asset] if m else None

    def do_entry(arg):
        c, L, tdec = arg
        b = book(c['token'])
        if not b or not b['asks']:
            return
        asks = sorted(b['asks'].items())
        bb = max(b['bids']) if b['bids'] else None
        mid = (asks[0][0] + bb) / 2 if bb is not None else None
        for S in SIZES:
            need, sh, val = S, 0.0, 0.0
            for p, s in asks:
                take = min(need, p * s); sh += take / p; val += take; need -= take
                if need <= 1e-9:
                    break
            if sh <= 0:
                continue
            vw = val / sh
            e = dict(L=L, S=S, best_ask=asks[0][0], mid=mid, spread=(asks[0][0] - bb) if bb is not None else None, VWAP=vw,
                     slippage_vs_mid=(vw - mid) if mid else None, rempli_usd=val, taux_remplissage=val / S, frais_entree=fee(meta, c['market'], vw) * sh)
            c['entrees'].append(e)
            for H in EXITS:
                nonlocal_seq[0] += 1
                heapq.heappush(tasks, (tdec + int(H * NS), nonlocal_seq[0], 'exit', (c, e, sh, H)))

    def do_exit(arg):
        c, e, sh, H = arg
        b = book(c['token'])
        if not b or not b['bids']:
            return
        got, left = walk_bids(b['bids'], sh - 0.0)
        xp = got / (sh - left) if sh - left > 0 else np.nan
        fo = fee(meta, c['market'], xp) * (sh - left) if sh - left > 0 else 0.0
        c['sorties'].append(dict(e, H=H, VWAP_sortie=xp, invendu=left, brut=(got - e['rempli_usd']) / e['rempli_usd'],
                                 net=(got - e['rempli_usd'] - e['frais_entree'] - fo) / e['rempli_usd']))

    def do_check(arg):
        c, k = arg
        b = book(c['token'])
        if b and b['asks'] and b['bids']:
            c['mids'][k] = (min(b['asks']) + max(b['bids'])) / 2
        m = det.mk[c['market']]
        lt = [x for x in m.trades if x[1] > c['t_local_ns']]
        if lt:
            x = lt[-1]
            c['dernier_prix'][k] = x[4] if x[2] == c['token'] else 1 - x[4]

    nonlocal_seq = [0]
    n = 0
    t_start = time.time()
    for t, conn, msg in iter_raw('ws_market', t0, t1):
        while tasks and tasks[0][0] <= t:
            _, _, kind, arg = heapq.heappop(tasks)
            if kind == 'entry':
                do_entry(arg)
            elif kind == 'exit':
                do_exit(arg)
            elif kind == 'check':
                do_check(arg)
        for e in events(msg):
            for s in det.on_event(t, e):
                if s['signal_type'] in ('AGGRESSIVE_FLOW', 'CANDIDAT'):
                    s.update(entrees=[], sorties=[], mids={}, dernier_prix={})
                    cand.append(s)
                    for L in LATS:
                        nonlocal_seq[0] += 1
                        heapq.heappush(tasks, (t + int(L * NS), nonlocal_seq[0], 'entry', (s, L, t + int(L * NS))))
                    for k in CHECK:
                        nonlocal_seq[0] += 1
                        heapq.heappush(tasks, (t + int(k * NS), nonlocal_seq[0], 'check', (s, k)))
                else:
                    key = (s['market'], s['token'])
                    if t - last_b1.get(key, 0) > 60 * NS:           # un signal B1 par marché et direction et par minute
                        last_b1[key] = t
                        s.update(mids={}, dernier_prix={})
                        b1.append(s)
                        for k in CHECK:
                            nonlocal_seq[0] += 1
                            heapq.heappush(tasks, (t + int(k * NS), nonlocal_seq[0], 'check', (s, k)))
        n += 1
        if n % 200000 == 0:
            print(f'  {n} messages, {len(cand)} candidats, {len(b1)} signaux B1, {time.time() - t_start:.0f} s', flush=True)
    return cand, b1, meta


def main(t0, t1):
    cand, b1, meta = run(t0, t1)
    # tables
    rows, det_rows = [], []
    for c in cand:
        base = {k: c.get(k) for k in ('t_local_ns', 'ts_echange_ms', 'market', 'token', 'tx', 'usd', 'pre_wallet_score', 'score_B1_avant', 'B2', 'signal_type', 'best_ask', 'entree_attendue_vwap_250')}
        mk = c['features'].get('p_before')
        base['p_before'] = mk
        for k, v in c['mids'].items():
            base[f'mid_+{k}s'] = v
        for k, v in c['dernier_prix'].items():
            base[f'prix_+{k}s'] = v
        det_rows.append(base)
        for s in c['sorties']:
            rows.append(dict(base, **s))
    D = pd.DataFrame(det_rows)
    X = pd.DataFrame(rows)
    # contrôle : candidats non signalés sous la médiane du score, même marché ; libellé de groupe
    if len(D):
        med = D.pre_wallet_score.median()
        D['groupe'] = np.where(D.B2, 'B2_SIGNAL', np.where(D.pre_wallet_score < med, 'CONTROLE_sous_mediane', 'autre'))
        X = X.merge(D[['t_local_ns', 'token', 'groupe']], on=['t_local_ns', 'token'], how='left')
    # rattachement a posteriori (évaluation seulement) : le trade était-il celui d'un wallet SIG_HIST ?
    al = [json.loads(l) for l in open(os.path.join(RAW11, 'live', 'alerts.jsonl'))] if os.path.exists(os.path.join(RAW11, 'live', 'alerts.jsonl')) else []
    D['was_SIG_HIST_wallet'] = D.tx.isin({a['tx'] for a in al}) if len(D) else []
    D.to_csv(OUT + 'live_candidats.csv', index=False)
    pd.DataFrame([{k: v for k, v in s.items() if k not in ('mids', 'dernier_prix', 'features')} | {f'mid_+{k}s': v for k, v in s['mids'].items()} for s in b1]).to_csv(OUT + 'live_signaux_B1.csv', index=False)
    agg = []
    if len(X):
        for (g, L, S, H), x in X.groupby(['groupe', 'L', 'S', 'H']):
            net = x.net.dropna()
            agg.append(dict(groupe=g, latence_s=L, taille_usd=S, sortie_s=H, n=len(x), n_marches=x.market.nunique(), taux_remplissage=x.get('taux_remplissage', pd.Series(dtype=float)).mean(),
                            brut_moy=x.brut.mean(), net_moy=net.mean(), net_med=net.median(), net_P10=net.quantile(.1), net_P90=net.quantile(.9), part_net_positif=(net > 0).mean(),
                            net_sans_top5=net[net <= net.quantile(.95)].mean() if len(net) else np.nan, part_top_marche=x.market.value_counts(normalize=True).iloc[0]))
    A = pd.DataFrame(agg)
    A.to_csv(OUT + 'pre_wallet_execution.csv', index=False)
    pd.set_option('display.width', 250)
    print('candidats', len(D), 'signaux B2', int(D.B2.sum()) if len(D) else 0, 'signaux B1', len(b1))
    if len(A):
        print(A[(A.taille_usd == 250)].round(4).to_string())


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--debut', default='2026-10-01T08:52')
    ap.add_argument('--fin', default=None)
    a = ap.parse_args()
    t0 = int(pd.Timestamp(a.debut, tz='UTC').value)
    t1 = int(pd.Timestamp(a.fin, tz='UTC').value) if a.fin else time.time_ns() - 120 * NS
    main(t0, t1)
