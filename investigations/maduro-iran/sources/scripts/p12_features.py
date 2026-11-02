#!/usr/bin/env python3
"""Phase 12 : features pré-wallet (PROTOCOLE_P12 §2-§4). Aucune feature n'utilise le wallet, son historique ou son statut FAE.
  --hist : flux complets de la phase 10 (H) -> p12/cand_hist.pkl (candidats) et p12/random_hist.pkl (instants aléatoires)
Le wallet ne sert qu'à : repérer a posteriori le trade SIG_HIST (was_SIG_HIST_wallet) et exclure le wallet de l'outcome (« autres wallets »).
Usage : python3 p12_features.py --hist   (depuis le dossier de données contenant p10/)"""
import os, sys, argparse
import numpy as np, pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p10_impact import load_tape, leader_index  # noqa: E402

# Les pickles lus ici sont produits localement par les scripts p10 ; ne jamais en charger d'autres.
WIN_FLOW = (1, 2, 5, 10, 60)
WIN_PRICE = (1, 2, 5, 10, 30, 60)
THR = (0.01, 0.015, 0.02, 0.025, 0.03, 0.04, 0.05)
AVANT = (['p_before', 't_depuis_dernier'] + [f'dp_{w}s' for w in WIN_PRICE] + [f'vol_meme_{w}s' for w in WIN_FLOW] + [f'vol_opp_{w}s' for w in WIN_FLOW]
         + [f'n_meme_{w}s' for w in WIN_FLOW] + [f'n_opp_{w}s' for w in WIN_FLOW] + ['vol_net_10s', 'accel_5s', 'max_usd_10s', 'moy_usd_10s',
         'niveaux_meme_5s', 'niveaux_meme_10s', 'max_niveaux_10s', 'ecart_ask_bid_60s'])
PENDANT = ['log_usd', 'niveaux', 'marche_carnet', 'impact', 'prime']


def avant(ts, ps, same, usd, nlv, first, k, t_ref, s_ae):
    """Features AVANT à l'instant t_ref, sur les trades d'indice < k (ordre d'exécution). ps = prix dans la direction ; same = achat dans la direction."""
    f = {}
    if k <= 0:
        return None
    pb = ps[k - 1]
    f['p_before'] = pb
    f['t_depuis_dernier'] = t_ref - ts[k - 1]
    for w in WIN_PRICE:
        j = np.searchsorted(ts[:k], t_ref - w, side='right') - 1
        f[f'dp_{w}s'] = pb - ps[j] if j >= 0 else np.nan
    for w in WIN_FLOW:
        a = np.searchsorted(ts[:k], t_ref - w, side='right')
        m = same[a:k]
        u = usd[a:k]
        f[f'vol_meme_{w}s'] = float(u[m].sum()); f[f'vol_opp_{w}s'] = float(u[~m].sum())
        f[f'n_meme_{w}s'] = int(m.sum()); f[f'n_opp_{w}s'] = int((~m).sum())
    f['vol_net_10s'] = f['vol_meme_10s'] - f['vol_opp_10s']
    f['accel_5s'] = f['vol_meme_5s'] / max(f['vol_meme_60s'] * 5 / 60, 1.0)
    a10 = np.searchsorted(ts[:k], t_ref - 10, side='right')
    u10 = usd[a10:k]
    f['max_usd_10s'] = float(u10.max()) if len(u10) else 0.0
    f['moy_usd_10s'] = float(u10.mean()) if len(u10) else 0.0
    for w in (5, 10):
        a = np.searchsorted(ts[:k], t_ref - w, side='right')
        f[f'niveaux_meme_{w}s'] = int(nlv[a:k][same[a:k]].sum())
    f['max_niveaux_10s'] = int(nlv[a10:k].max()) if k > a10 else 0
    a60 = np.searchsorted(ts[:k], t_ref - 60, side='right')
    ia = [i for i in range(k - 1, a60 - 1, -1) if same[i] and not np.isnan(first[i])][:1]
    ib = [i for i in range(k - 1, a60 - 1, -1) if (not same[i]) and not np.isnan(first[i])][:1]
    f['ecart_ask_bid_60s'] = (first[ia[0]] - first[ib[0]]) if ia and ib else np.nan
    return f


def outcome(ts, ps, wal, k, t_ref, p_ref, w_excl, horizon=60):
    """Variation du prix des AUTRES wallets entre p_ref et t_ref + horizon ; délais d'atteinte des seuils."""
    b = np.searchsorted(ts, t_ref + horizon, side='right')
    idx = [i for i in range(k + 1, b) if wal[i] != w_excl]
    out = dict(obs=len(idx) > 0, delta=(ps[idx[-1]] - p_ref) if idx else 0.0)
    for th in THR:
        hit = next((ts[i] - t_ref for i in idx if ps[i] - p_ref >= th - 1e-9), np.nan)
        out[f't_{th}'] = hit
    return out


def window(r):
    T = load_tape(r.wid, int(r.d))
    if T.empty:
        return [], []
    i_lead = leader_index(T, r.tx, r.wallet)
    ts = T.ts.values.astype(np.int64)
    a0, b0 = int(T.attrs.get('a', ts.min())), int(T.attrs.get('b', ts.max()))
    pd_ = T.pd.values.astype(float)
    ae = T.ae.values.astype(bool)
    usd = T.usd.values.astype(float)
    wal = T.wallet.values
    nlv = np.array([len(x) for x in T.lv.values])
    lv = T.lv.values
    cands, rnd = [], []
    for s in (1, -1):
        ps = pd_ if s == 1 else 1 - pd_
        same = ae if s == 1 else ~ae
        first = np.array([(x[0][0] if s == 1 else 1 - x[0][0]) if len(x) else np.nan for x in lv])   # premier niveau, dans la direction s
        for k in np.nonzero((T.side.values == 'BUY') & (usd >= 250) & same)[0]:
            t = ts[k]
            if t < a0 + 60 or t > b0 - 60:
                continue
            f = avant(ts, ps, same, usd, nlv, first, k, t, s)
            if f is None:
                continue
            levels = [(p if s == 1 else 1 - p) for p, q in lv[k]]
            if not levels:
                continue
            levels = sorted(levels)
            marg, fst = levels[-1], levels[0]
            f.update(log_usd=np.log(usd[k]), niveaux=len(levels), marche_carnet=marg - fst, impact=marg - f['p_before'], prime=fst - f['p_before'])
            o_pre = outcome(ts, ps, wal, k, t, f['p_before'], wal[k])
            o_post = outcome(ts, ps, wal, k, t, marg, wal[k])
            rec = dict(wid=r.wid, groupe=r.groupe, split=r.split, cid=r.cid, cat=r.cat, ts=int(t), seq=int(k), direction=s, tx=T.tx.values[k], usd=usd[k],
                       marginal=marg, was_SIG_HIST_wallet=bool(r.groupe == 'SIG_HIST' and k == i_lead), was_FAE_controle=bool(r.groupe == 'CONTROLE' and k == i_lead),
                       **f, **{f'pre_{a}': b for a, b in o_pre.items()}, **{f'post_{a}': b for a, b in o_post.items()})
            cands.append(rec)
    # instants aléatoires (activité normale), dans la direction de la fenêtre, toutes les 60 s, hors ± 120 s autour du trade de la fenêtre
    t_lead = ts[i_lead] if i_lead is not None else None
    ps, same = pd_, ae
    first = np.array([x[0][0] if len(x) else np.nan for x in lv])
    for t in range(a0 + 60, b0 - 60, 60):
        if t_lead is not None and abs(t - t_lead) < 120:
            continue
        k = int(np.searchsorted(ts, t, side='left'))
        f = avant(ts, ps, same, usd, nlv, first, k, t, 1)
        if f is None:
            continue
        o = outcome(ts, ps, wal, k - 1, t, f['p_before'], None)
        rnd.append(dict(wid=r.wid, groupe=r.groupe, split=r.split, cid=r.cid, ts=int(t), **f, **{f'pre_{a}': b for a, b in o.items()}))
    return cands, rnd


def hist():
    W = pd.read_pickle('p10/windows.pkl')
    C, R = [], []
    for n, r in enumerate(W.itertuples()):
        if not os.path.exists(f'p10/tapes/{r.wid}.pkl'):
            continue
        c, rr = window(r)
        C += c; R += rr
        if n % 500 == 0:
            print(f'  {n}/{len(W)} fenêtres, {len(C)} candidats', flush=True)
    C = pd.DataFrame(C)
    # un même trade peut figurer dans deux fenêtres qui se recouvrent : une seule ligne, priorité à la fenêtre SIG_HIST
    C = C.sort_values(['was_SIG_HIST_wallet', 'was_FAE_controle'], ascending=False).drop_duplicates(['tx', 'direction', 'seq', 'cid', 'ts'])
    C = C.drop_duplicates(['tx', 'direction', 'usd', 'ts'])
    os.makedirs('p12', exist_ok=True)
    C.to_pickle('p12/cand_hist.pkl')
    pd.DataFrame(R).to_pickle('p12/random_hist.pkl')
    print('candidats', len(C), C.groupby('split').size().to_dict(), 'SIG_HIST', int(C.was_SIG_HIST_wallet.sum()), 'contrôles FAE', int(C.was_FAE_controle.sum()), 'instants aléatoires', len(R))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--hist', action='store_true')
    a = ap.parse_args()
    if a.hist:
        hist()
