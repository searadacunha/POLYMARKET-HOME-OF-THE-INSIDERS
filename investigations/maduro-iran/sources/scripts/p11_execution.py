#!/usr/bin/env python3
"""Phase 11 : exécution simulée sur le carnet RÉEL enregistré (PROTOCOLE_P11 §3-§6). Aucun ordre n'est passé.
Règle centrale : la décision à t n'utilise que le carnet reconstruit à partir des messages reçus avant t (p11_replay.Timeline.book_at).
Le futur ne sert qu'à mesurer le résultat (sortie, MAE/MFE, remplissage des limites).
Entrées : live/alerts.jsonl (+ verifications), live/fae_events.jsonl (réservoir de contrôles), brut ws_market, rtds, watchlists.
Sorties (phase11/) : execution_simulation.csv, orderbook_snapshots.csv, lead_time_distribution.csv (détail), self_impact.csv,
follower_impact.csv, limit_orders.csv ; p11/exec_long.pkl
Usage : python3 p11_execution.py [--controles 3]"""
import os, sys, json, glob, argparse, collections, bisect
import numpy as np, pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p11_common import RAW, OUT, DATA, get  # noqa: E402
from p11_replay import Timeline, rtds_rows, iter_raw  # noqa: E402

NS = 10 ** 9
LATS = [0, 0.1, 0.25, 0.5, 1, 2, 3, 5, 10, 30, 60]
SIZES = [50, 100, 250, 500, 1000, 2500, 5000, 10000]
EXITS = [10, 30, 60, 120, 300]
SNAPS = [0, 0.1, 0.25, 0.5, 1, 2, 3, 5, 10, 30, 60]
LIMITS = {'best_ask': 0.0, 'best_ask_-0.5pt': 0.005, 'best_ask_-1pt': 0.01, 'best_ask_-2pt': 0.02}
LIMIT_LIFE = [10, 30, 60, 300]
WORK = os.path.join(RAW, 'travail')
os.makedirs(WORK, exist_ok=True)


def jread(fp):
    return [json.loads(l) for l in open(fp)] if os.path.exists(fp) else []


_META = None


def market_meta(extra=()):
    """Métadonnées (jetons, frais, catégorie) des watchlists successives ; marchés dynamiques (alertes) complétés par Gamma."""
    global _META
    if _META is None:
        m = {}
        for fp in sorted(glob.glob(os.path.join(RAW, 'meta', 'watchlist_*.json'))):
            for c, x in json.load(open(fp))['watchlist'].items():
                m.setdefault(c, x)
        for d in jread(os.path.join(RAW, 'meta', 'dynamic_watch.jsonl')):
            m.setdefault(d['cid'], dict(tier='D', tokens=d['tokens'], slug=d.get('slug'), cat=d.get('cat')))
        _META = m
    for c in extra:
        x = _META.get(c)
        if x is None or 'feeSchedule' not in x:
            for closed in ('false', 'true'):
                try:
                    r = get(f'https://gamma-api.polymarket.com/markets?closed={closed}&condition_ids={c}', tries=2)
                except Exception:
                    r = []
                if r:
                    g = r[0]
                    _META[c] = dict(x or {}, tokens=json.loads(g['clobTokenIds']), slug=g.get('slug'), feesEnabled=g.get('feesEnabled'),
                                    feeSchedule=g.get('feeSchedule'), tier=(x or {}).get('tier', 'hors_watchlist'))
                    break
    return _META


def fee_per_share(meta, cid, p):
    x = meta.get(cid) or {}
    if x.get('feesEnabled') is False:
        return 0.0
    fs = x.get('feeSchedule') or {}
    rate = fs.get('rate')
    if rate is None:
        return np.nan
    return float(rate) * min(p, 1 - p) ** float(fs.get('exponent', 1))


def walk(levels, dollars=None, shares=None):
    """Parcourt des niveaux [(prix, actions)] ; renvoie (actions, coût ou produit, prix moyen, niveaux touchés, restant)."""
    need = dollars if dollars is not None else shares
    sh = val = 0.0
    n = 0
    for p, s in levels:
        if need <= 1e-9:
            break
        if dollars is not None:
            take = min(need, p * s); sh += take / p; val += take; need -= take
        else:
            q = min(need, s); sh += q; val += q * p; need -= q
        n += 1
    vwap = val / sh if sh > 0 else np.nan
    return sh, val, vwap, n, max(need, 0.0)


def depth_within(book, pts, side='ask'):
    bb, ba = book.best()
    if side == 'ask' and ba is not None:
        return sum(p * s for p, s in book.asks.items() if p <= ba + pts + 1e-9)
    if side == 'bid' and bb is not None:
        return sum(p * s for p, s in book.bids.items() if p >= bb - pts - 1e-9)
    return np.nan


def simulate_event(ev, tl, meta):
    """Toutes les cases latence x taille x sortie pour un événement (alerte ou contrôle)."""
    a = ev['asset']
    rows = []
    for L in LATS:
        t = ev['T_obs_ns'] + int(L * NS)
        bk = tl.book_at(a, t)
        if bk is None or not bk.ok or not bk.asks:
            rows.append(dict(L=L, carnet=False)); continue
        v = bk.view()
        asks = bk.asks_sorted()
        for S in SIZES:
            sh, cost, vwap, nlv, rest = walk(asks, dollars=S)
            fee_in = fee_per_share(meta, ev['market'], vwap) * sh if sh > 0 else 0.0
            base = dict(L=L, carnet=True, S=S, best_ask=v['best_ask'], mid=v['mid'], spread=v['spread'], VWAP_EXECUTION=vwap,
                        SLIPPAGE_VS_MID=(vwap - v['mid']) if v['mid'] is not None and sh > 0 else np.nan, rempli_usd=cost, restant_usd=rest,
                        taux_remplissage=cost / S, niveaux_consommes=nlv, frais_entree=fee_in, age_carnet_ms=(t - bk.t_local) / 1e6)
            if sh <= 0:
                rows.append(dict(base, H=None)); continue
            for H in EXITS:
                tx_ = t + int(H * NS)
                bx = tl.book_at(a, tx_)
                if bx is None or not bx.bids:
                    rows.append(dict(base, H=H, sortie=False)); continue
                q, proceeds, xvwap, _, unsold = walk(bx.bids_sorted(), shares=sh)
                fee_out = fee_per_share(meta, ev['market'], xvwap) * q if q > 0 else 0.0
                mids = [s.view()['mid'] for _, s in tl.path(a, t, tx_)]
                mids = [x for x in mids if x is not None]
                r = dict(base, H=H, sortie=True, VWAP_SORTIE=xvwap, invendu_actions=unsold, frais_sortie=fee_out,
                         brut=(proceeds - cost) / cost, net=(proceeds - cost - fee_in - fee_out) / cost,
                         MAE=(min(mids) - vwap) if mids else np.nan, MFE=(max(mids) - vwap) if mids else np.nan)
                rows.append(r)
    return rows


def pre_trade(ev, tl):
    """Carnet juste avant le trade du wallet (réception du last_trade_price de sa transaction), heure T0 et impact propre."""
    tr = [x for x in tl.trades if x['tx'] and x['tx'] == ev.get('tx')]
    t0_local = min(x['t_local'] for x in tr) if tr else None
    t0_exch = min(x['t_exch'] for x in tr) if tr else None
    if t0_local is None:
        return dict(T0_local_ns=None)
    # les price_change d'un trade précèdent son last_trade_price d'environ 20 ms (horodatage d'échange -300 à +50 ms) :
    # le carnet « avant » est le dernier état antérieur à cette rafale
    st = tl.states[ev['asset']]
    k = bisect.bisect_left(tl.keys[ev['asset']], t0_local) - 1
    while k >= 0 and st[k][1].t_exch and st[k][1].t_exch >= t0_exch - 300:
        k -= 1
    b0 = st[k][1] if k >= 0 else None
    if k + 1 < len(st):
        t0_local = min(t0_local, st[k + 1][0])
    if b0 is None or not b0.asks:
        return dict(T0_local_ns=t0_local, T0_exch_ms=t0_exch)
    v = b0.view()
    shares = ev['usd'] / ev['price'] if ev['price'] else np.nan
    sh, cost, vwap, nlv, rest = walk(b0.asks_sorted(), shares=shares)
    marg = b0.asks_sorted()[nlv - 1][0] if nlv else np.nan
    last = [x for x in tl.trades if x['t_local'] < t0_local]
    p_last = (last[-1]['price'] if last[-1]['asset'] == ev['asset'] else 1 - last[-1]['price']) if last else np.nan
    d2 = depth_within(b0, 0.02)
    return dict(T0_local_ns=t0_local, T0_exch_ms=t0_exch, retard_T_obs_s=(ev['T_obs_ns'] - t0_local) / NS, ask0=v['best_ask'], bid0=v['best_bid'], mid0=v['mid'],
                spread0=v['spread'], depth_ask_2pt=d2, part_profondeur_2pt=ev['usd'] / d2 if d2 else np.nan, marginal=marg, p_last_avant=p_last,
                IMMEDIATE_IMPACT=(marg - p_last) if pd.notna(p_last) else np.nan)


def lead_times(ev, tl, pre, tick=0.01):
    """Premier changement du best ask, du mid, mouvement de 1 et 3 points, depuis T0 (carnet d'avant le trade)."""
    out = {}
    if pre.get('T0_local_ns') is None or pre.get('mid0') is None:
        return out
    t0 = pre['T0_local_ns']
    for t, b in tl.path(ev['asset'], t0, t0 + 600 * NS):
        v = b.view()
        if v['best_ask'] is not None and 'lt_ask_s' not in out and v['best_ask'] >= pre['ask0'] + tick - 1e-9:
            out['lt_ask_s'] = (t - t0) / NS
        if v['mid'] is not None:
            dm = v['mid'] - pre['mid0']
            for k, th in (('lt_mid_0.5pt_s', 0.005), ('lt_mid_1pt_s', 0.01), ('lt_mid_3pt_s', 0.03)):
                if k not in out and dm >= th - 1e-9:
                    out[k] = (t - t0) / NS
    for off in (0.25, 0.5, 1, 2, 3, 5):
        for ref, tref in (('T0', t0), ('Tobs', ev['T_obs_ns'])):
            b = tl.book_at(ev['asset'], tref + int(off * NS))
            if b is not None:
                v = b.view()
                out[f'ask_{ref}+{off}s'] = v['best_ask']
                out[f'mid_{ref}+{off}s'] = v['mid']
    return out


def snapshots(ev, tl):
    rows = []
    for ref in ('T_obs', 'T0'):
        tref = ev['T_obs_ns'] if ref == 'T_obs' else ev.get('T0_local_ns')
        if tref is None:
            continue
        for off in SNAPS:
            b = tl.book_at(ev['asset'], tref + int(off * NS))
            if b is None:
                rows.append(dict(reference=ref, offset_s=off, carnet=False)); continue
            v = b.view()
            rows.append(dict(reference=ref, offset_s=off, carnet=True, age_ms=(tref + off * NS - b.t_local) / 1e6, timestamp_exchange_ms=b.t_exch, **v,
                             ask_depth_2pt=depth_within(b, 0.02), bid_depth_2pt=depth_within(b, 0.02, 'bid'),
                             asks_top10=json.dumps(b.asks_sorted()[:10]), bids_top10=json.dumps(b.bids_sorted()[:10])))
    return rows


def limit_orders(ev, tl, meta):
    """Ordres limites posés à T_obs à un prix défini par le carnet à T_obs (§3). Remplissage conservateur et optimiste."""
    a = ev['asset']
    b = tl.book_at(a, ev['T_obs_ns'])
    if b is None or not b.asks:
        return []
    ba = b.best()[1]
    out = []
    trades = [x for x in tl.trades if x['t_local'] > ev['T_obs_ns']]
    for name, off in LIMITS.items():
        K = round((ba - off) * 1000) / 1000
        shares = 500 / K
        queue = b.bids.get(K, 0.0)
        for life in LIMIT_LIFE:
            t_end = ev['T_obs_ns'] + life * NS
            if off == 0:            # au best ask : marchand immédiatement sur la profondeur affichée à K
                sh, cost, vwap, nlv, rest = walk([(p, s) for p, s in b.asks_sorted() if p <= K + 1e-9], dollars=500)
                filled = rest <= 1e-6
                out.append(dict(limite=name, K=K, duree_s=life, regle='immédiat', rempli=filled, t_remplissage_s=0.0 if filled else None, prix=vwap if filled else None))
                continue
            for rule in ('conservatrice', 'optimiste'):
                q_ahead = queue
                done = None
                vol_at_K = 0.0
                prev = b
                for t, bk in tl.path(a, ev['T_obs_ns'] + 1, t_end):
                    if rule == 'optimiste':
                        q_ahead = min(q_ahead, bk.bids.get(K, 0.0))
                    prev = bk
                for x in trades:
                    if x['t_local'] > t_end:
                        break
                    if x['asset'] == a and x['side'] == 'SELL':
                        px = x['price']                                   # vente preneuse du jeton : touche les bids
                    elif x['asset'] == ev.get('complement') and x['side'] == 'BUY':
                        px = round(1 - x['price'], 6)                     # achat du jeton opposé : touche les bids par miroir
                    else:
                        continue
                    if px < K - 1e-9:
                        done = x['t_local']; break
                    if abs(px - K) < 1e-9:
                        vol_at_K += x['size']
                        if vol_at_K >= q_ahead + shares:
                            done = x['t_local']; break
                out.append(dict(limite=name, K=K, duree_s=life, regle=rule, rempli=done is not None,
                                t_remplissage_s=(done - ev['T_obs_ns']) / NS if done else None, prix=K if done else None, file_devant=queue))
    # rendement conditionnel : sortie sur les bids à T_obs + 300 s (carnet connu à ce moment)
    bx = tl.book_at(a, ev['T_obs_ns'] + 300 * NS)
    for o in out:
        if o['rempli'] and bx is not None and bx.bids:
            sh = 500 / o['prix']
            q, proceeds, xv, _, unsold = walk(bx.bids_sorted(), shares=sh)
            fee_in = fee_per_share(meta, ev['market'], o['prix']) * sh if o['regle'] == 'immédiat' else 0.0
            fee_out = fee_per_share(meta, ev['market'], xv) * q if q > 0 else 0.0
            o['net_300s'] = (proceeds - 500 - fee_in - fee_out) / 500
    return out


def followers(ev, pre, rt, known):
    """Acheteurs après T0 (RTDS, 10 min), séparés en suiveurs connus (avant T0) et inconnus."""
    if pre.get('T0_local_ns') is None:
        return []
    d = ev['outcomeIndex']
    out = []
    for r in rt:
        if r['conditionId'] != ev['market'] or r['proxyWallet'].lower() == ev['wallet'] or r['t_local'] <= pre['T0_local_ns']:
            continue
        if r['t_local'] > pre['T0_local_ns'] + 600 * NS:
            continue
        buy_d = (r['side'] == 'BUY') == (int(r['outcomeIndex']) == d)
        out.append(dict(delai_s=(r['t_local'] - pre['T0_local_ns']) / NS, wallet=r['proxyWallet'].lower(), sens='achat_d' if buy_d else 'vente_d',
                        usd=float(r['price']) * float(r['size']), preneur=r.get('fee') is not None, tx=r.get('transactionHash'),
                        groupe_suiveur='KNOWN_FOLLOWER' if r['proxyWallet'].lower() in known.get(ev['wallet'], set()) else 'UNKNOWN_FOLLOWER'))
    return out


def mechanism(ev, tl, pre, rt, known):
    """Variation du mid entre T0 et T0 + H, attribuée sans résidu : changements du carnet portant l'horodatage d'échange d'un trade
    -> wallet preneur de ce trade (RTDS) ; changements sans trade -> QUOTES (placements, annulations)."""
    if pre.get('T0_local_ns') is None or pre.get('mid0') is None:
        return []
    taker = {}
    for r in rt:
        if r.get('fee') is not None or r['transactionHash'] not in taker:
            taker[r['transactionHash']] = r['proxyWallet'].lower()
    tts = sorted((x['t_exch'], x['tx']) for x in tl.trades if x['t_exch'])
    keys = [x[0] for x in tts]

    def trade_of(te):
        """Trade dont la rafale de mises à jour contient l'horodatage te (trade dans [te - 50, te + 300] ms)."""
        if not te:
            return None
        i = bisect.bisect_left(keys, te - 50)
        cands = [tts[j] for j in range(i, min(i + 5, len(tts))) if tts[j][0] - 300 <= te <= tts[j][0] + 50]
        return min(cands, key=lambda z: abs(z[0] - te))[1] if cands else None
    out = []
    for H in (60, 300):
        acc = collections.Counter()
        prev = pre['mid0']
        for t, b in tl.path(ev['asset'], pre['T0_local_ns'] - 400 * 10 ** 6, pre['T0_local_ns'] + H * NS):
            if b.t_exch and pre.get('T0_exch_ms') and b.t_exch < pre['T0_exch_ms'] - 300:
                continue
            m = b.view()['mid']
            if m is None:
                continue
            dm = m - prev
            prev = m
            h = trade_of(b.t_exch)
            if h is not None and h == ev.get('tx'):
                acc['SELF_IMPACT'] += dm
            elif h is not None:
                w = taker.get(h)
                acc['KNOWN_FOLLOWER_IMPACT' if w in known.get(ev['wallet'], set()) else 'UNKNOWN_TRADER_IMPACT'] += dm
            else:
                acc['QUOTES'] += dm
        out.append(dict(H=H, variation_mid=prev - pre['mid0'], **{k: acc.get(k, 0.0) for k in ('SELF_IMPACT', 'KNOWN_FOLLOWER_IMPACT', 'UNKNOWN_TRADER_IMPACT', 'QUOTES')}))
    return out


def chain_time(tx, t0_ns, t1_ns):
    """Première réception locale d'un log OrderFilled de la transaction par le nœud Polygon (flux `chain`)."""
    for t, conn, msg in iter_raw('chain', t0_ns, t1_ns):
        if isinstance(msg, str) and tx and tx[2:12] in msg:
            try:
                r = (json.loads(msg).get('params') or {}).get('result') or {}
            except Exception:
                continue
            if r.get('transactionHash') == tx:
                return t
    return None


def known_followers():
    """Suiveurs connus avant la phase 11 : relations FOLLOWER et liens de la phase 10."""
    fp = os.path.join(DATA, 'p10', 'pairs.pkl')
    k = collections.defaultdict(set)
    if os.path.exists(fp):
        PR = pd.read_pickle(fp)                       # pickle local (phase 10)
        for r in PR[(PR.relation == 'FOLLOWER') | (PR.marches_aval >= 2)].itertuples():
            k[r.leader].add(r.suiveur)
    return k


def controls(alerts, fae, n=3):
    """Contrôles appariés (§6) parmi les FAE non SIG_HIST de la même période : prix, catégorie, temps restant, activité ; plus proche en temps."""
    F = pd.DataFrame(fae)
    if F.empty:
        return []
    F = F[~F.SIG_HIST & ~F.FOLLOW & F.p_before.notna()].copy()
    F = F[F.market.isin(set(market_meta()))]          # contrôles pris dans les marchés dont le carnet est enregistré
    F['pbin'] = (F.p_before * 10).astype(int).clip(0, 9)
    F['htb'] = pd.cut(F.hours_to_end.fillna(1e6), [-1e9, 1, 6, 24, 168, 1e12], labels=False)
    F['actb'] = pd.cut(F.act_10m.fillna(0), [-1, 0, 1, 4, 1e9], labels=False)
    out = []
    for a in alerts:
        pb = int(min(max(a['p_before'] * 10, 0), 9))
        x = F[(F.pbin == pb) & (F.cat == a.get('cat'))]
        if len(x) < n:
            x = F[F.pbin == pb]
        x = x.assign(dt=(x.T_obs_ns - a['T_obs_ns']).abs()).sort_values('dt').head(n)
        for r in x.to_dict('records'):
            r['controle_de'] = a['alert_id']
            out.append(r)
    return out


def main(n_ctl, tous_fae=False):
    alerts = jread(os.path.join(RAW, 'live', 'alerts.jsonl'))
    ver = {}
    for v in jread(os.path.join(RAW, 'live', 'verifications.jsonl')):
        ver[v['alert_id']] = ver.get(v['alert_id'], False) or bool(v.get('preneur_confirme'))
    for a in alerts:
        a['confirme'] = ver.get(a['alert_id'])
    fae = jread(os.path.join(RAW, 'live', 'fae_events.jsonl'))
    ctl = controls(alerts, fae, n_ctl)
    meta = market_meta(extra=[a['market'] for a in alerts])
    known = known_followers()
    evs = [dict(a, groupe='SIG_HIST', event_id=a['alert_id']) for a in alerts] + \
          [dict(c, groupe='CONTROLE', event_id=f"C_{c['controle_de']}_{k}", alert_id=c['controle_de']) for k, c in enumerate(ctl)]
    if tous_fae:      # description du carnet « normal » : tous les FAE vus en direct (non-FOLLOW, prix de référence connu)
        wl = set(market_meta())
        evs += [dict(f, groupe='FAE_LIVE', event_id=f"F{k}", alert_id=None) for k, f in enumerate(fae)
                if not f.get('FOLLOW') and f.get('p_before') is not None and not f.get('SIG_HIST') and f['market'] in wl]
    longrows, snaprows, ltrows, limrows, folrows, mechrows = [], [], [], [], [], []
    for ev in evs:
        ev['asset'] = str(ev['asset'])
        toks = [str(x) for x in (meta.get(ev['market']) or {}).get('tokens', [])]
        ev['complement'] = next((x for x in toks if x != ev['asset']), None)
        t = ev['T_obs_ns']
        tl = Timeline([x for x in [ev['asset'], ev['complement']] if x], t - 900 * NS, t + 420 * NS, warm_s=3600)
        pre = pre_trade(ev, tl)
        ev.update(pre)
        tc = chain_time(ev.get('tx'), t - 10 * NS, t + 5 * NS) if ev['groupe'] == 'SIG_HIST' else None
        pre['T_obs_chaine_ns'] = tc
        pre['avance_chaine_sur_rtds_s'] = (t - tc) / NS if tc else None
        if tc:                                             # variante : décision dès réception du log on-chain (secondaire)
            evc = dict(ev, T_obs_ns=tc)
            for r in simulate_event(evc, tl, meta):
                if r.get('S') in (None, 500):
                    longrows.append(dict(event_id=ev['event_id'], groupe='SIG_HIST_T_OBS_CHAINE', alert_id=ev.get('alert_id'), market=ev['market'],
                                         wallet=ev['wallet'], usd=ev['usd'], confirme=ev.get('confirme'), cat=ev.get('cat'), **r))
        base = dict(event_id=ev['event_id'], groupe=ev['groupe'], alert_id=ev.get('alert_id'), market=ev['market'], wallet=ev['wallet'], usd=ev['usd'],
                    confirme=ev.get('confirme'), cat=ev.get('cat'))
        for r in simulate_event(ev, tl, meta):
            longrows.append({**base, **r})
        for r in snapshots(ev, tl):
            snaprows.append({**base, **r})
        lt = lead_times(ev, tl, pre)
        ltrows.append({**base, **{k: v for k, v in pre.items()}, **lt})
        for r in limit_orders(ev, tl, meta):
            limrows.append({**base, **r})
        if pre.get('T0_local_ns'):
            rt = rtds_rows(pre['T0_local_ns'] - 5 * NS, pre['T0_local_ns'] + 600 * NS, cids={ev['market']})
            for r in followers(ev, pre, rt, known):
                folrows.append({**base, **r})
            for r in mechanism(ev, tl, pre, rt, known):
                mechrows.append({**base, **r})
    X = pd.DataFrame(longrows)
    X.to_pickle(os.path.join(WORK, 'exec_long.pkl'))
    pd.DataFrame(snaprows).to_csv(os.path.join(OUT, 'orderbook_snapshots.csv'), index=False)
    pd.DataFrame(ltrows).to_csv(os.path.join(WORK, 'lead_time_detail.csv'), index=False)
    pd.DataFrame(limrows).to_csv(os.path.join(OUT, 'limit_orders.csv'), index=False)
    pd.DataFrame(folrows).to_csv(os.path.join(WORK, 'followers_detail.csv'), index=False)
    pd.DataFrame(mechrows).to_csv(os.path.join(WORK, 'mechanism.csv'), index=False)
    pd.DataFrame([dict(e) for e in evs]).to_csv(os.path.join(WORK, 'events.csv'), index=False)
    print('événements', len(evs), '(alertes', len(alerts), ', contrôles', len(ctl), ') lignes simulées', len(X))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--controles', type=int, default=3)
    ap.add_argument('--tous-fae', action='store_true')
    a = ap.parse_args()
    main(a.controles, a.tous_fae)
