#!/usr/bin/env python3
"""Phase 10 : collecte et reconstruction du flux complet autour de chaque alerte SIG_HIST (et d'un contrôle apparié).

Source : data-api /trades?market=&start=&end= (toutes tailles), deux passes par fenêtre :
  takerOnly=true  -> les preneurs (ordre exact d'exécution, vérifié contre les logs on-chain) ;
  takerOnly=false -> preneurs + fills makers (les niveaux du carnet réellement consommés par chaque trade).
Aucun calcul de résultat ici : seulement la collecte et la mise en forme.

Usage (depuis le dossier de données contenant p8/ et p9/) :
  python3 p10_replay.py --select      # SIG_HIST (phase 9, inchangé) + contrôles appariés -> p10/windows.pkl
  python3 p10_replay.py --collect     # fenêtres [T0 - 900 s, T0 + 4 500 s] -> p10/raw/{wid}.json.gz
  python3 p10_replay.py --build       # flux reconstruits -> p10/tapes/{wid}.pkl
  python3 p10_replay.py --receipts    # frais payés par le wallet signalé (reçus de transaction) -> p10/fees.pkl
  python3 p10_replay.py --event CID START END NAME   # fenêtre libre (Maduro, Iran)
"""
import argparse, gzip, json, os, sys, time, concurrent.futures as cf
import numpy as np, pandas as pd

# Les pickles lus ici sont produits localement par les scripts p8/p9/p10 de ce dossier ; ne jamais en charger d'autres.

sys.path.insert(0, os.getcwd())
from common2 import http, throttle, es  # noqa: E402  (limiteur partagé, déjà utilisé en phases 8-9)

PRE, POST = 900, 4500
API = 'https://data-api.polymarket.com/trades'
os.makedirs('p10/raw', exist_ok=True)
os.makedirs('p10/tapes', exist_ok=True)


def select():
    """Alertes SIG_HIST exactement telles qu'en phase 9, plus un contrôle apparié par alerte (même strate, FAE non-FOLLOW, non SIG_HIST)."""
    EV = pd.read_pickle('p9/events_final.pkl')
    A = pd.read_pickle('p8/alltrades.pkl')[['tx', 'size']]
    EV['tx'] = A.tx.values[EV.rid.values]
    base = EV.is_FAE & ~EV.FOLLOW & EV.p_before.notna()
    S = EV[EV.SIG_HIST].copy()
    rng = np.random.default_rng(10)
    pool = EV[base & ~EV.SIG_HIST].groupby('stratum').indices
    ctl = []
    for s in S.stratum.values:
        ix = pool.get(s)
        ctl.append(EV.index[base & ~EV.SIG_HIST][rng.choice(ix)] if ix is not None and len(ix) else None)
    keep = ['eid9', 'rid', 'split', 'cid', 'cat', 'asset', 'wallet', 'ts', 'd', 'price', 'usd', 'p_before', 'impact_own', 'dpre_10m', 'dpre_60m',
            'dpost_60m', 'move_after_exec', 'LEAD60', 'hist_n', 'hist_score', 'win', 'stratum', 'tx', 'net_60s_500', 'entry_60s_500', 'end']
    W = S[keep].assign(groupe='SIG_HIST')
    C = EV.loc[[c for c in ctl if c is not None], keep].assign(groupe='CONTROLE')
    C['alerte_eid9'] = [e for e, c in zip(S.eid9.values, ctl) if c is not None]
    W['alerte_eid9'] = W.eid9
    W = pd.concat([W, C], ignore_index=True)
    W['wid'] = W.groupe.str[0] + W.eid9.astype(str)
    W = W.drop_duplicates('wid')
    W.to_pickle('p10/windows.pkl')
    print('fenêtres', len(W), W.groupby(['groupe', 'split']).size().to_dict())


def fetch(cid, a, b, taker_only):
    """Tous les trades du marché dans [a, b] ; découpe l'intervalle si la page est pleine."""
    url = f'{API}?market={cid}&start={a}&end={b}&limit=10000&takerOnly={"true" if taker_only else "false"}'
    rows = http(url, cache=False)
    if not isinstance(rows, list):
        raise RuntimeError(f'réponse inattendue {str(rows)[:120]}')
    if len(rows) >= 10000:
        if b - a < 2:
            raise RuntimeError(f'plus de 10 000 trades dans [{a},{b}] sur {cid}')
        m = (a + b) // 2
        return fetch(cid, m + 1, b, taker_only) + fetch(cid, a, m, taker_only)   # ordre décroissant conservé
    return rows


def collect_one(wid, cid, t0, a=None, b=None):
    fp = f'p10/raw/{wid}.json.gz'
    if os.path.exists(fp):
        return wid, 'déjà'
    a = t0 - PRE if a is None else a
    b = t0 + POST if b is None else b
    tk = fetch(cid, a, b, True)
    al = fetch(cid, a, b, False)
    keep = ('proxyWallet', 'side', 'asset', 'conditionId', 'size', 'price', 'timestamp', 'outcomeIndex', 'transactionHash')
    out = {'cid': cid, 'a': a, 'b': b, 't0': t0, 'taker': [{k: r.get(k) for k in keep} for r in tk], 'all': [{k: r.get(k) for k in keep} for r in al]}
    tmp = fp + '.tmp'
    with gzip.open(tmp, 'wt') as f:
        json.dump(out, f)
    os.replace(tmp, fp)
    return wid, len(tk), len(al)


def collect(workers=8):
    W = pd.read_pickle('p10/windows.pkl')
    todo = [(r.wid, r.cid, int(r.ts)) for r in W.itertuples() if not os.path.exists(f'p10/raw/{r.wid}.json.gz')]
    print('à collecter', len(todo), flush=True)
    t = time.time()
    err = 0
    with cf.ThreadPoolExecutor(workers) as ex:
        futs = {ex.submit(collect_one, *x): x for x in todo}
        for i, f in enumerate(cf.as_completed(futs)):
            try:
                f.result()
            except Exception as e:
                err += 1
                print('ERREUR', futs[f][0], repr(e)[:160], flush=True)
            if i % 200 == 0:
                print(f'  {i}/{len(todo)} {time.time() - t:.0f} s, erreurs {err}', flush=True)
    print('fini, erreurs', err)


def build_one(wid, d=None):
    """Flux reconstruit : une ligne par trade preneur, dans l'ordre exact, avec ses niveaux makers (prix et taille, dans la direction du jeton d)."""
    raw = json.load(gzip.open(f'p10/raw/{wid}.json.gz', 'rt'))
    tk = raw['taker'][::-1]                      # data-api renvoie l'ordre décroissant
    al = raw['all'][::-1]
    key = lambda r: (r['transactionHash'], r['proxyWallet'].lower(), r['side'], r['asset'], round(float(r['size']), 6))
    tkeys = {}
    for i, r in enumerate(tk):
        tkeys.setdefault(key(r), []).append(i)
    makers = {}
    for r in al:
        k = key(r)
        if k in tkeys and tkeys[k]:
            continue                             # ligne preneur (déjà dans tk)
        makers.setdefault(r['transactionHash'], []).append(r)
    rows = []
    for seq, r in enumerate(tk):
        oi = int(r['outcomeIndex'])
        px = float(r['price']); sz = float(r['size'])
        lv = [(int(m['outcomeIndex']), m['side'], float(m['price']), float(m['size']), m['proxyWallet'].lower()) for m in makers.get(r['transactionHash'], [])]
        rows.append(dict(seq=seq, ts=int(r['timestamp']), tx=r['transactionHash'], wallet=r['proxyWallet'].lower(), side=r['side'], oi=oi,
                         price=px, size=sz, usd=px * sz, levels=lv))
    T = pd.DataFrame(rows)
    T.attrs.update(cid=raw['cid'], a=raw['a'], b=raw['b'], t0=raw['t0'])
    return T


def build():
    W = pd.read_pickle('p10/windows.pkl')
    n = 0
    for r in W.itertuples():
        fo = f'p10/tapes/{r.wid}.pkl'
        if os.path.exists(fo) or not os.path.exists(f'p10/raw/{r.wid}.json.gz'):
            continue
        build_one(r.wid).to_pickle(fo)
        n += 1
    print('flux reconstruits', n)


V1 = {'0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e', '0xc5d563a36ae78145c45a50134d48a1215220f80a'}
V2 = {'0xe111180000d2663c0091e4f400237545b87b996b', '0xe2222d279d744050d28e00520010520000310f59'}
T_OF1 = '0xd0a08e8c493f9c94f29311604c9de1b4e8c8d4c06bd0c789af57f2d65bfec0f6'
T_OF2 = '0xd543adfd945773f1a62f74f0ee55a5e3b9b1a28262980ba90b1a89f2ea84d8ee'
T_FEE2 = '0x55bb3cade9d43b798a4fe5ffdd05024b2d7870df53920673bfc7e68047cd0ab1'


def receipt_fee(tx, wallet):
    """Frais payés par le preneur dans la transaction. v1 : champ fee du fill preneur (en actif reçu) ; v2 : événements FeeCharged."""
    R = es(137, module='proxy', action='eth_getTransactionReceipt', txhash=tx)['result']
    out = dict(tx=tx, block=int(R['blockNumber'], 16), version=None, fee_raw=0.0, fee_unit=None, n_maker_fills=0)
    for l in R['logs']:
        a = l['address'].lower(); t0 = l['topics'][0]
        d = l['data'][2:]; w = [int(d[i:i + 64], 16) for i in range(0, len(d), 64)]
        if a in V1 and t0 == T_OF1:
            out['version'] = 'v1'
            if l['topics'][3][-40:] == a[-40:]:          # fill du preneur (taker = contrat)
                out['fee_raw'] += w[4] / 1e6
                out['fee_unit'] = 'usdc' if w[1] == 0 else 'jetons'   # actif reçu par le preneur
            else:
                out['n_maker_fills'] += 1
        elif a in V2 and t0 == T_OF2:
            out['version'] = 'v2'
            if l['topics'][3][-40:] != a[-40:]:
                out['n_maker_fills'] += 1
        elif a in V2 and t0 == T_FEE2:
            out['fee_raw'] += w[0] / 1e6
            out['fee_unit'] = 'collateral'
    return out


def receipts(workers=4):
    W = pd.read_pickle('p10/windows.pkl')
    fp = 'p10/fees.pkl'
    done = pd.read_pickle(fp) if os.path.exists(fp) else pd.DataFrame(columns=['tx'])
    todo = [(r.tx, r.wallet) for r in W.drop_duplicates('tx').itertuples() if r.tx not in set(done.tx)]
    print('reçus à lire', len(todo), flush=True)
    res = []
    with cf.ThreadPoolExecutor(workers) as ex:
        for i, x in enumerate(ex.map(lambda a: _safe(receipt_fee, *a), todo)):
            if x:
                res.append(x)
            if i % 250 == 0:
                print('  ', i, flush=True)
                pd.concat([done, pd.DataFrame(res)], ignore_index=True).to_pickle(fp)
    pd.concat([done, pd.DataFrame(res)], ignore_index=True).to_pickle(fp)
    print('reçus', len(res))


def _safe(f, *a):
    try:
        return f(*a)
    except Exception as e:
        print('ERREUR reçu', a[0][:12], repr(e)[:120], flush=True)
        return None


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--select', action='store_true')
    ap.add_argument('--collect', action='store_true')
    ap.add_argument('--build', action='store_true')
    ap.add_argument('--receipts', action='store_true')
    ap.add_argument('--event', nargs=4, metavar=('CID', 'START', 'END', 'NAME'))
    ap.add_argument('--workers', type=int, default=8)
    a = ap.parse_args()
    if a.select:
        select()
    if a.collect:
        collect(a.workers)
    if a.build:
        build()
    if a.receipts:
        receipts()
    if a.event:
        cid, s, e, name = a.event
        print(collect_one(name, cid, int(s), int(s), int(e)))
        build_one(name).to_pickle(f'p10/tapes/{name}.pkl')
