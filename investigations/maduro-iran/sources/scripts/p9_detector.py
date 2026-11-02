#!/usr/bin/env python3
"""Phase 9 : prototype de détecteur de lead en flux. OUTIL DE RECHERCHE ET DE BACKTEST, aucune exécution d'ordre.

Entrée : un flux de trades preneurs Polymarket (format data-api /trades), dans l'ordre chronologique.
Sortie : une alerte par événement signalé, avec timestamp, market, wallet, direction, lead_score, wallet_history_score,
market_context_score, convergence_score, signal_strength, estimated_lead_time.

Tout est causal :
  - chaque feature n'utilise que les trades déjà reçus, et les trades de la même seconde que T sont exclus du prix de référence ;
  - l'historique d'un wallet n'utilise que ses événements FAE non-FOLLOW déjà résolus (T_e + 3600 s <= T), l'étiquette
    étant recalculée par le détecteur lui-même à partir du flux (mouvement des AUTRES wallets sur 60 min) ;
  - modèles et seuils sont ceux figés en TRAIN (phase9/modeles/), jamais réajustés.

Usages :
  python3 p9_detector.py --verify  --prints p9/prints.pkl --events p9/events_final.pkl   # concordance avec le calcul en lot
  python3 p9_detector.py --replay  --prints p9/prints.pkl --since 2026-03-01 --out alertes.csv
  python3 p9_detector.py --jsonl trades.jsonl --markets p8/universe.json [--warmup p9/prints.pkl]
"""
import argparse, bisect, collections, heapq, json, math, os, pickle, sys, time
import numpy as np, pandas as pd

# Les pickles lus ici (modèles figés, trades) sont produits localement par les scripts p8/p9 de ce dossier ; ne jamais en charger d'autres.

HERE = os.path.dirname(os.path.abspath(__file__))
MODELES = os.path.normpath(os.path.join(HERE, '..', 'phase9', 'modeles'))
THETA = 0.03
ALPHA = 10
PRE = {'10s': 10, '30s': 30, '1m': 60, '5m': 300, '10m': 600, '30m': 1800, '60m': 3600}
ORDRE = ['SIG_HIST', 'SIG_WALLET', 'SIG_NEW', 'SIG_CTX', 'SIG_CONV', 'SIG_ACC']
# lead-time des événements LEAD60 de TRAIN (P25, médiane, P75, en secondes), seule source permise au détecteur
LEAD_TRAIN = {'SIG_HIST': (32, 156, 977), 'SIG_WALLET': (82, 428, 1338), 'SIG_CTX': (76, 348, 1164.5),
              'SIG_CONV': (52, 200, 780), 'SIG_ACC': (66, 332, 1071), 'SIG_NEW': (58, 446, 1712)}


def matrice(df, feat):
    """Transformations identiques à X() de p9_train.py."""
    x = df[feat].astype(float).copy()
    x['act_10m'] = np.log1p(x.act_10m)
    x['activity_ratio'] = np.log1p(x.activity_ratio.clip(lower=0))
    x['hours_to_end'] = np.log1p(x.hours_to_end.clip(lower=0))
    x['prior_trades_univ'] = np.log1p(x.prior_trades_univ)
    x['hist_n'] = np.log1p(x.hist_n)
    cat = df.cat.fillna('')
    x['cat_politics'] = cat.str.startswith('election').astype(float)
    x['cat_geo'] = cat.str.startswith('geopolitics').astype(float)
    x['cat_macro'] = cat.str.startswith('macro').astype(float)
    return x


class Detecteur:
    def __init__(self, modeles=MODELES, differe=False):
        spec = json.load(open(os.path.join(modeles, 'frozen_spec.json')))
        self.m_lead = pickle.load(open(os.path.join(modeles, 'frozen_model.pkl'), 'rb'))          # S3, lead_score_raw
        self.m_wallet = pickle.load(open(os.path.join(modeles, 'frozen_model_wallet.pkl'), 'rb'))  # S5, wallet seul
        c = pickle.load(open(os.path.join(modeles, 'frozen_model_ctx.pkl'), 'rb'))                 # contexte seul
        self.m_ctx, self.ctx_feat = c['model'], c['features']
        self.feat, self.wfeat = spec['features'], spec['S5_wallet']['features']
        self.thr, self.wthr, self.hthr = spec['alert_threshold_raw'], spec['S5_wallet']['alert_threshold'], spec['hist_threshold']
        self.p0 = spec['train_lead_rate']
        self.differe = differe
        # état du flux
        self.mk = {}                                       # cid -> ([ts], [p_yes], [wallet])
        self.mk_usd = collections.defaultdict(list)        # cid -> tailles antérieures triées (rang de taille)
        self.mk_seen = collections.defaultdict(set)        # cid -> wallets déjà vus
        self.n_univ = collections.Counter()                # wallet -> trades antérieurs dans l'univers
        self.w_lusd = {}                                   # wallet -> [somme log usd, n]
        self.last_wm = {}                                  # (wallet, cid) -> dernier ts
        self.vol_wm = {}                                   # (wallet, cid) -> [volume, volume signé YES]
        self.buys_wa = {}                                  # (wallet, asset) -> [deque (ts, usd), somme, dernier acc_raw]
        self.conv_a = {}                                   # asset -> deque (ts, wallet)
        self.last_conv = {}
        self.pending = []                                  # tas (res_t, seq, cid, T, d, wallet, p_before)
        self.hist = collections.defaultdict(lambda: [0, 0])
        self.mk_scores = collections.defaultdict(list)     # cid -> lead_score des FAE antérieurs (rang ajusté marché)
        self.seq = 0
        self.lignes = []

    # ---------- résolution causale des étiquettes (historique des wallets)
    def _resoudre(self, now):
        while self.pending and self.pending[0][0] <= now:
            res_t, _, cid, T, d, w, pb = heapq.heappop(self.pending)
            S, P, Wl = self.mk[cid]
            j = bisect.bisect_right(S, res_t) - 1
            while j >= 0 and S[j] > T and Wl[j] == w:
                j -= 1
            dpost = ((P[j] if d == 0 else 1 - P[j]) - pb) if (j >= 0 and S[j] > T) else 0.0
            h = self.hist[w]
            h[0] += 1
            h[1] += int(dpost >= THETA)

    # ---------- un trade
    def traiter(self, t):
        ts, cid, w, side, asset = int(t['ts']), t['cid'], t['wallet'], t['side'], t['asset']
        price, usd, oi = float(t['price']), float(t['usd']), int(t['oi'])
        self._resoudre(ts)
        if cid not in self.mk:
            self.mk[cid] = ([], [], [])
        S, P, Wl = self.mk[cid]
        p_yes = price if oi == 0 else 1 - price
        buyeq_yes = (side == 'BUY' and oi == 0) or (side == 'SELL' and oi == 1)
        dir_yes = 1 if buyeq_yes else -1
        lusd = math.log(usd)
        # features de wallet et de marché (état antérieur au trade)
        prior = self.n_univ[w]
        first = w not in self.mk_seen[cid]
        U = self.mk_usd[cid]
        srank = bisect.bisect_left(U, usd) / len(U) if len(U) >= 30 else np.nan
        wl = self.w_lusd.get(w)
        rel = lusd - wl[0] / wl[1] if wl and wl[1] > 0 else np.nan
        vw = self.vol_wm.get((w, cid))
        conc = vw[1] * dir_yes / vw[0] if vw and vw[0] > 0 else np.nan
        last = self.last_wm.get((w, cid))
        fae = side == 'BUY' and usd >= 250 and (last is None or ts - last > 86400)
        n30, cum30, acc = 0, 0.0, False
        if side == 'BUY':
            b = self.buys_wa.get((w, asset))
            if b is None:
                b = self.buys_wa[(w, asset)] = [collections.deque(), 0.0, False]
            dq = b[0]
            while dq and dq[0][0] < ts - 1800:
                b[1] -= dq.popleft()[1]
            dq.append((ts, usd))
            b[1] += usd
            n30, cum30 = len(dq) - 1, b[1]
            raw = len(dq) >= 3 and b[1] >= 750
            acc = raw and not b[2]
            b[2] = raw
        conv, conv_nw, conv_t1 = False, 0, np.nan
        if side == 'BUY' and usd >= 250:
            dq = self.conv_a.get(asset)
            if dq is None:
                dq = self.conv_a[asset] = collections.deque()
            while dq and dq[0][0] <= ts - 600:
                dq.popleft()
            dq.append((ts, w))
            conv_nw = len({x[1] for x in dq})
            lc = self.last_conv.get(asset)
            if conv_nw >= 3 and (lc is None or ts - lc > 600):
                conv, conv_t1 = True, dq[0][0]
                self.last_conv[asset] = ts
        if fae or acc or conv:
            self._evenement(t, ts, cid, w, oi, price, usd, lusd, S, P, fae, acc, conv, conv_nw, conv_t1,
                            prior, first, srank, rel, conc, n30, cum30)
        # mise à jour de l'état
        S.append(ts); P.append(p_yes); Wl.append(w)
        bisect.insort(U, usd)
        self.mk_seen[cid].add(w)
        self.n_univ[w] += 1
        if wl:
            wl[0] += lusd; wl[1] += 1
        else:
            self.w_lusd[w] = [lusd, 1]
        self.last_wm[(w, cid)] = ts
        if vw:
            vw[0] += usd; vw[1] += usd * dir_yes
        else:
            self.vol_wm[(w, cid)] = [usd, usd * dir_yes]
        if not self.differe and self.lignes:
            out = self._scorer()
            return out
        return []

    def _evenement(self, t, ts, cid, w, oi, price, usd, lusd, S, P, fae, acc, conv, conv_nw, conv_t1,
                   prior, first, srank, rel, conc, n30, cum30):
        d = oi
        r = dict(rid=t.get('rid'), ts=ts, cid=cid, cat=t.get('cat'), asset=t['asset'], wallet=w, d=d, price=price, usd=usd,
                 lusd=lusd, size_rank_mkt=srank, rel_size_wallet=rel, n_buys_30m=n30, cum_usd_30m=cum30, conc_dir=conc,
                 first_in_mkt=float(first), prior_trades_univ=prior, is_FAE=fae, is_ACC=acc, is_CONV=conv,
                 conv_nwallets_10m=conv_nw, conv_t1=conv_t1, p_before=np.nan, hours_to_end=np.nan)
        for k in PRE:
            r['dpre_' + k] = np.nan
        i0 = bisect.bisect_left(S, ts) - 1          # dernier trade strictement avant T
        if i0 >= 0:
            f = (lambda v: v) if d == 0 else (lambda v: 1 - v)
            pb = f(P[i0])
            r['p_before'] = pb
            for k, win in PRE.items():
                iw = bisect.bisect_right(S, ts - win) - 1
                if iw >= 0:
                    r['dpre_' + k] = pb - f(P[iw])
            r['act_10m'] = i0 + 1 - bisect.bisect_left(S, ts - 600)
            r['act_7d'] = i0 + 1 - bisect.bisect_left(S, ts - 7 * 86400)
        else:
            r['act_10m'] = r['act_7d'] = np.nan
        r['activity_ratio'] = r['act_10m'] / max(r['act_7d'] * 600 / (7 * 86400), 1e-6) if i0 >= 0 else np.nan
        if t.get('end') is not None and not (isinstance(t.get('end'), float) and math.isnan(t['end'])):
            r['hours_to_end'] = (t['end'] - ts) / 3600
        r['FOLLOW'] = bool(r['dpre_10m'] >= THETA / 2) if not np.isnan(r['dpre_10m']) else False
        h = self.hist[w]
        r['hist_n'], r['hist_lead'] = h[0], h[1]
        r['hist_score'] = (h[1] + ALPHA * self.p0) / (h[0] + ALPHA)
        if fae and not r['FOLLOW'] and i0 >= 0:
            self.seq += 1
            heapq.heappush(self.pending, (ts + 3600, self.seq, cid, ts, d, w, r['p_before']))
        self.lignes.append(r)

    # ---------- scores (sans état : l'ordre de calcul ne change rien, sauf le rang ajusté au marché, fait dans l'ordre)
    def _scorer(self):
        E = pd.DataFrame(self.lignes)
        self.lignes = []
        ok = E.p_before.notna()
        for c in ('score_ctx', 'score_wallet', 'p_ctx', 'score_ctx_market_adj'):
            E[c] = np.nan
        if ok.any():
            Xa = matrice(E[ok], self.feat)
            E.loc[ok, 'score_ctx'] = self.m_lead.predict_proba(Xa)[:, 1]
            E.loc[ok, 'score_wallet'] = self.m_wallet.predict_proba(Xa[self.wfeat])[:, 1]
            E.loc[ok, 'p_ctx'] = self.m_ctx.predict_proba(Xa[self.ctx_feat])[:, 1]
        adj = np.full(len(E), np.nan)
        for i, (cid, s, fae, o) in enumerate(zip(E.cid.values, E.score_ctx.values, E.is_FAE.values, ok.values)):
            if not (fae and o):
                continue
            past = self.mk_scores[cid]
            if len(past) >= 20:
                adj[i] = bisect.bisect_left(past, s) / len(past)
            bisect.insort(past, s)
        E['score_ctx_market_adj'] = adj
        base = E.is_FAE & ~E.FOLLOW & ok
        E['SIG_CTX'] = base & (E.score_ctx >= self.thr)
        E['SIG_WALLET'] = base & (E.score_wallet >= self.wthr)
        E['SIG_ACC'] = E.is_ACC & ~E.FOLLOW & ok
        E['SIG_CONV'] = E.is_CONV & ~E.FOLLOW & ok
        E['SIG_HIST'] = base & (E.hist_n >= 5) & (E.hist_score >= self.hthr)
        E['SIG_NEW'] = base & (E.prior_trades_univ <= 2) & (E.score_wallet >= self.wthr)
        return E

    def alertes(self, E):
        """Événements scorés -> alertes au format du détecteur."""
        ratio = {'SIG_HIST': E.hist_score / self.hthr, 'SIG_WALLET': E.score_wallet / self.wthr, 'SIG_NEW': E.score_wallet / self.wthr,
                 'SIG_CTX': E.score_ctx / self.thr, 'SIG_CONV': E.conv_nwallets_10m / 3, 'SIG_ACC': E.cum_usd_30m / 750}
        any_ = np.zeros(len(E), dtype=bool)
        for k in ORDRE:
            any_ |= E[k].values
        A = E[any_].copy()
        if A.empty:
            return pd.DataFrame()
        sig = A[ORDRE].apply(lambda r: '|'.join(k for k in ORDRE if r[k]), axis=1)
        prem = sig.str.split('|').str[0]
        strength = np.nanmax(np.column_stack([np.where(A[k], ratio[k][A.index], np.nan) for k in ORDRE]), axis=1)
        return pd.DataFrame({
            'timestamp': pd.to_datetime(A.ts, unit='s', utc=True), 'ts': A.ts, 'market': A.cid, 'asset': A.asset, 'wallet': A.wallet,
            'direction': np.where(A.d == 0, 'outcome0 (YES)', 'outcome1 (NO)'), 'usd': A.usd, 'price_paid': A.price, 'p_before': A.p_before,
            'signals': sig, 'lead_score': A.score_ctx, 'lead_score_market_adjusted': A.score_ctx_market_adj, 'wallet_score': A.score_wallet,
            'wallet_history_score': A.hist_score, 'wallet_history_n': A.hist_n, 'market_context_score': A.p_ctx,
            'convergence_score': A.conv_nwallets_10m / 3, 'signal_strength': strength,
            'estimated_lead_time_s': prem.map(lambda k: LEAD_TRAIN[k][1]),
            'estimated_lead_time_p25_p75': prem.map(lambda k: f'{LEAD_TRAIN[k][0]}-{LEAD_TRAIN[k][2]}'),
            'rid': A.rid,
            'usage': 'recherche uniquement, aucun ordre',
        })

    def rejouer(self, prints, log_every=500000):
        cols = ['ts', 'cid', 'cat', 'end', 'wallet', 'side', 'asset', 'price', 'usd', 'oi', 'rid']
        arr = [prints[c].values for c in cols]
        t0 = time.time()
        for n, row in enumerate(zip(*arr)):
            self.traiter(dict(zip(cols, row)))
            if log_every and n and n % log_every == 0:
                print(f'  {n:,} trades, {time.time() - t0:.0f} s', file=sys.stderr, flush=True)
        return self._scorer()


def depuis_data_api(r, meta):
    """Ligne data-api /trades + métadonnées de marché -> trade au format du détecteur."""
    cid = r['conditionId']
    m = meta.get(cid, {})
    return dict(ts=int(r['timestamp']), cid=cid, cat=m.get('cat'), end=m.get('end'), wallet=r['proxyWallet'].lower(), side=r['side'],
                asset=r['asset'], price=float(r['price']), usd=float(r['price']) * float(r['size']), oi=int(r['outcomeIndex']))


def verifier(D, ev_path):
    """Concordance détecteur en flux contre calcul en lot (p9_features / p9_history / p9_backtest)."""
    EV = pd.read_pickle(ev_path)
    m = EV.merge(D, on='rid', how='outer', suffixes=('_lot', '_flux'), indicator=True)
    rows = [dict(controle='événements présents des deux côtés', valeur=float((m._merge == 'both').mean()),
                 detail=m._merge.value_counts().to_dict())]
    b = m[m._merge == 'both']
    for c, tol in (('p_before', 1e-9), ('dpre_10m', 1e-9), ('dpre_60m', 1e-9), ('act_10m', 0), ('size_rank_mkt', 1e-9),
                   ('prior_trades_univ', 0), ('first_in_mkt', 0), ('rel_size_wallet', 1e-6), ('conc_dir', 1e-6), ('n_buys_30m', 0),
                   ('hist_n', 0), ('hist_score', 1e-9), ('score_ctx', 1e-9), ('score_wallet', 1e-9), ('p_ctx', 1e-9)):
        x, y = b[c + '_lot'].astype(float), b[c + '_flux'].astype(float)
        eq = ((x - y).abs() <= tol) | (x.isna() & y.isna())
        rows.append(dict(controle='égalité ' + c, valeur=float(eq.mean()), detail=f'n={len(b)}, écarts={int((~eq).sum())}'))
    for k in ORDRE + ['FOLLOW', 'is_FAE', 'is_ACC', 'is_CONV']:
        for sp in ('TRAIN', 'VALID', 'TEST'):
            s = b[b.split == sp]
            x, y = s[k + '_lot'].astype(bool), s[k + '_flux'].astype(bool)
            rows.append(dict(controle=f'{k} {sp}', valeur=float((x == y).mean()),
                             detail=f'lot={int(x.sum())}, flux={int(y.sum())}, les deux={int((x & y).sum())}'))
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--modeles', default=MODELES)
    ap.add_argument('--prints', help='pickle des trades (p9/prints.pkl), triés par (ts, rid)')
    ap.add_argument('--events', help='events_final.pkl du calcul en lot (pour --verify)')
    ap.add_argument('--verify', action='store_true')
    ap.add_argument('--replay', action='store_true')
    ap.add_argument('--since', help='date ISO : alertes émises à partir de cette date (l\'état est chauffé avant)')
    ap.add_argument('--jsonl', help='trades data-api en JSON lines (flux)')
    ap.add_argument('--markets', help='universe.json (conditionId, endDate, cat)')
    ap.add_argument('--warmup', help='pickle de trades pour chauffer l\'état avant le flux JSON lines')
    ap.add_argument('--out', default='alertes_detecteur.csv')
    ap.add_argument('--concordance', default='detector_concordance.csv')
    a = ap.parse_args()
    if a.verify or a.replay:
        P = pd.read_pickle(a.prints)
        det = Detecteur(a.modeles, differe=True)
        E = det.rejouer(P)
        if a.verify:
            V = verifier(E, a.events)
            V.to_csv(a.concordance, index=False)
            print(V.to_string())
        AL = det.alertes(E)
        if a.since:
            AL = AL[AL.ts >= int(pd.Timestamp(a.since, tz='UTC').timestamp())]
        AL.to_csv(a.out, index=False)
        print(f'{len(AL):,} alertes -> {a.out}', file=sys.stderr)
    elif a.jsonl:
        meta = {}
        if a.markets:
            import datetime as dt
            for m in json.load(open(a.markets)):
                end = m.get('endDate')
                meta[m['conditionId']] = dict(cat=m.get('cat'), end=int(dt.datetime.fromisoformat(end.replace('Z', '+00:00')).timestamp()) if end else None)
        det = Detecteur(a.modeles, differe=True)
        if a.warmup:
            det.rejouer(pd.read_pickle(a.warmup))
        det.differe = False
        src = sys.stdin if a.jsonl == '-' else open(a.jsonl)
        for line in src:
            if not line.strip():
                continue
            E = det.traiter(depuis_data_api(json.loads(line), meta))
            if len(E):
                for r in det.alertes(E).to_dict('records'):
                    print(json.dumps(r, default=str), flush=True)
    else:
        ap.print_help()


if __name__ == '__main__':
    main()
