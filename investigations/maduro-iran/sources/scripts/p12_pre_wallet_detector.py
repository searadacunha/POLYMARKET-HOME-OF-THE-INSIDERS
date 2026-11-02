#!/usr/bin/env python3
"""Phase 12 : détecteur SANS WALLET en flux (PROTOCOLE_P12 §5). Recherche uniquement : aucun ordre.
Entrée : messages du websocket « market » du CLOB (book, price_change, last_trade_price), dans l'ordre de réception.
Sortie à chaque signal : timestamp, market, token, direction, pre_wallet_score, signal_type (+ entrée attendue : best ask, VWAP 250 $).
Aucune donnée n'identifie un wallet : le flux « market » n'en contient pas.
  B2 (AGGRESSIVE_FLOW) : à chaque achat anonyme >= 250 $, features AVANT (trades antérieurs du marché) + empreinte anonyme du trade
                          (niveaux consommés lus sur le carnet juste avant le trade).
  B1 (PRE_REPRICING_FLOW) : après chaque trade du marché, features AVANT seules, dans les deux directions.
Modèles et seuils : phase12/modeles/B1.pkl, B2.pkl, phase12/frozen_p12.json (gelés sur TRAIN)."""
import os, sys, json, pickle, math, bisect, collections
import numpy as np, pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p12_features import AVANT, PENDANT, WIN_FLOW, WIN_PRICE  # noqa: E402

# Les pickles chargés ici sont les modèles produits localement par p12_backtest.py --freeze ; ne jamais en charger d'autres.
D12 = os.path.expanduser('~/Documents/Crypto/enquete_maduro_iran/phase12/')


class Market:
    def __init__(self):
        self.trades = []                                  # (ts_s, t_local, asset, side, price, usd, nlv, first)
        self.books = collections.defaultdict(lambda: dict(bids={}, asks={}, ok=False))
        self.hist = collections.defaultdict(lambda: collections.deque(maxlen=200))   # asset -> (t_exch, asks copie, bids copie)


class PreWalletDetector:
    def __init__(self, tokens_of_market):
        fz = json.load(open(D12 + 'frozen_p12.json'))
        self.m1 = pickle.load(open(D12 + 'modeles/B1.pkl', 'rb'))
        self.m2 = pickle.load(open(D12 + 'modeles/B2.pkl', 'rb'))
        self.t1, self.t2 = fz['seuil_B1'], fz['seuil_B2']
        self.tok = tokens_of_market                       # market -> [token0, token1]
        self.mk = collections.defaultdict(Market)
        self.asset_market = {t: m for m, ts in tokens_of_market.items() for t in ts}

    # ---------------- carnet
    def _snap(self, M, a, t_exch):
        b = M.books[a]
        M.hist[a].append((t_exch, dict(b['asks']), dict(b['bids'])))

    def on_event(self, t_local, e):
        et = e.get('event_type')
        if et == 'book':
            a = e.get('asset_id'); m = self.asset_market.get(a)
            if m is None:
                return []
            M = self.mk[m]
            M.books[a] = dict(bids={float(x['price']): float(x['size']) for x in e.get('bids', [])},
                              asks={float(x['price']): float(x['size']) for x in e.get('asks', [])}, ok=True)
            self._snap(M, a, int(e.get('timestamp') or 0))
            return []
        if et == 'price_change':
            ts = int(e.get('timestamp') or 0)
            out = []
            for c in e.get('price_changes', []):
                a = c.get('asset_id'); m = self.asset_market.get(a)
                if m is None:
                    continue
                M = self.mk[m]
                if not M.books[a]['ok']:
                    continue
                self._snap(M, a, ts)                      # état AVANT ce changement
                side = M.books[a]['bids'] if c['side'] == 'BUY' else M.books[a]['asks']
                p, s = float(c['price']), float(c['size'])
                if s <= 0:
                    side.pop(p, None)
                else:
                    side[p] = s
            return out
        if et == 'last_trade_price':
            return self.on_trade(t_local, e)
        return []

    def _pre_book(self, M, a, t_exch):
        """Carnet juste avant la rafale de mises à jour du trade (dernier état d'horodatage < t_exch - 300 ms)."""
        for te, asks, bids in reversed(M.hist[a]):
            if te < t_exch - 300:
                return asks, bids
        b = M.books[a]
        return b['asks'], b['bids']

    # ---------------- features
    def _avant(self, M, X, t_ref):
        """Features AVANT dans la direction du jeton X, sur les trades antérieurs du marché."""
        T = M.trades
        if not T:
            return None
        ts = np.array([x[0] for x in T], float)
        same = np.array([(x[2] == X and x[3] == 'BUY') or (x[2] != X and x[3] == 'SELL') for x in T])
        ps = np.array([x[4] if x[2] == X else 1 - x[4] for x in T])
        usd = np.array([x[5] for x in T]); nlv = np.array([x[6] for x in T])
        first = np.array([(x[7] if x[2] == X else (1 - x[7] if x[7] == x[7] else np.nan)) for x in T])
        k = len(T)
        f = dict(p_before=ps[-1], t_depuis_dernier=t_ref - ts[-1])
        for w in WIN_PRICE:
            j = np.searchsorted(ts, t_ref - w, side='right') - 1
            f[f'dp_{w}s'] = ps[-1] - ps[j] if j >= 0 else np.nan
        for w in WIN_FLOW:
            a = np.searchsorted(ts, t_ref - w, side='right')
            m, u = same[a:k], usd[a:k]
            f[f'vol_meme_{w}s'] = float(u[m].sum()); f[f'vol_opp_{w}s'] = float(u[~m].sum())
            f[f'n_meme_{w}s'] = int(m.sum()); f[f'n_opp_{w}s'] = int((~m).sum())
        f['vol_net_10s'] = f['vol_meme_10s'] - f['vol_opp_10s']
        f['accel_5s'] = f['vol_meme_5s'] / max(f['vol_meme_60s'] * 5 / 60, 1.0)
        a10 = np.searchsorted(ts, t_ref - 10, side='right')
        u10 = usd[a10:k]
        f['max_usd_10s'] = float(u10.max()) if len(u10) else 0.0
        f['moy_usd_10s'] = float(u10.mean()) if len(u10) else 0.0
        for w in (5, 10):
            a = np.searchsorted(ts, t_ref - w, side='right')
            f[f'niveaux_meme_{w}s'] = int(nlv[a:k][same[a:k]].sum())
        f['max_niveaux_10s'] = int(nlv[a10:k].max()) if k > a10 else 0
        a60 = np.searchsorted(ts, t_ref - 60, side='right')
        ia = [i for i in range(k - 1, a60 - 1, -1) if same[i] and first[i] == first[i]][:1]
        ib = [i for i in range(k - 1, a60 - 1, -1) if (not same[i]) and first[i] == first[i]][:1]
        f['ecart_ask_bid_60s'] = (first[ia[0]] - first[ib[0]]) if ia and ib else np.nan
        return f

    def on_trade(self, t_local, e):
        a = e.get('asset_id'); m = self.asset_market.get(a)
        if m is None:
            return []
        M = self.mk[m]
        ts = int(e.get('timestamp') or 0)
        price, size, side = float(e['price']), float(e['size']), e.get('side')
        usd = price * size
        asks, bids = self._pre_book(M, a, ts)
        lv = sorted(asks.items()) if side == 'BUY' else sorted(bids.items(), reverse=True)
        need, levels = size, []
        for p, s in lv:
            if need <= 1e-9:
                break
            levels.append(p); need -= min(need, s)
        first = levels[0] if levels else price
        nlv = len(levels)
        out = []
        ts_s = ts / 1000.0
        if side == 'BUY' and usd >= 250 and len(M.trades) > 0 and levels:
            f = self._avant(M, a, ts_s)
            if f is not None:
                marg = levels[-1]
                f.update(log_usd=math.log(usd), niveaux=nlv, marche_carnet=marg - first, impact=marg - f['p_before'], prime=first - f['p_before'])
                x = pd.DataFrame([f])
                s2 = float(self.m2.predict_proba(x[AVANT + PENDANT])[:, 1][0])
                s1 = float(self.m1.predict_proba(x[AVANT])[:, 1][0])
                b = M.books[a]
                cur_asks = sorted(b['asks'].items())
                exp = _vwap(cur_asks, 250)
                out.append(dict(t_local_ns=t_local, ts_echange_ms=ts, market=m, token=a, direction=a, tx=e.get('transaction_hash'), usd=usd,
                                score_B1_avant=s1, pre_wallet_score=s2, B2=s2 >= self.t2, signal_type='AGGRESSIVE_FLOW' if s2 >= self.t2 else 'CANDIDAT',
                                best_ask=cur_asks[0][0] if cur_asks else None, entree_attendue_vwap_250=exp, features=f))
        M.trades.append((ts_s, t_local, a, side, price, usd, nlv, first))
        if len(M.trades) > 5000:
            M.trades = M.trades[-3000:]
        # B1 après chaque trade, dans les deux directions
        for X in self.tok.get(m, []):
            f = self._avant(M, X, ts_s + 0.001)
            if f is None:
                continue
            s1 = float(self.m1.predict_proba(pd.DataFrame([f])[AVANT])[:, 1][0])
            if s1 >= self.t1:
                b = M.books[X]
                cur = sorted(b['asks'].items())
                out.append(dict(t_local_ns=t_local, ts_echange_ms=ts, market=m, token=X, direction=X, pre_wallet_score=s1, signal_type='PRE_REPRICING_FLOW',
                                best_ask=cur[0][0] if cur else None, entree_attendue_vwap_250=_vwap(cur, 250)))
        return out


def _vwap(asks, dollars):
    need, sh, val = dollars, 0.0, 0.0
    for p, s in asks:
        take = min(need, p * s); sh += take / p; val += take; need -= take
        if need <= 1e-9:
            break
    return val / sh if sh > 0 and need <= 1e-9 else None
