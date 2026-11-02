#!/usr/bin/env python3
"""Phase 15 : analyse de l'enregistrement d'audit (donnees/brut_p15/) contre la vérité chaîne (PROTOCOLE_P15 §1, §2).
Vérité trade et wallet : fills de l'ordre preneur (topic 3 = contrat d'échange) des logs OrderFilled v2, rattrapés par eth_getLogs en cas de trou.
Sources comparées : RTDS A (continue), RTDS B (coupée 30 s toutes les 20 min), RTDS du collecteur P11, last_trade_price du collecteur (marchés suivis),
logs filtrés du collecteur, listener P11 (FAE), P12, P13, P14. Lecture seule de tous les fichiers. Aucun signal, aucun ordre.
Sorties : phase15/phase15_trade_coverage.csv, phase15_latency.csv, phase15_duplicates.csv, phase15_price_audit.csv, phase15_wallet_audit.csv,
          phase15_reconnect.csv, phase15_live_resume.json"""
import os, sys, json, glob, gzip, zlib, time, urllib.request
import numpy as np, pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p11_replay import iter_raw, events  # noqa: E402

ROOT = os.path.expanduser('~/Documents/Crypto/enquete_maduro_iran')
RAW15 = os.path.join(ROOT, 'donnees', 'brut_p15')
B = os.path.join(ROOT, 'donnees') + '/'
OUT = os.path.join(ROOT, 'phase15') + '/'
EXL = ['e111180000d2663c0091e4f400237545b87b996b', 'e2222d279d744050d28e00520010520000310f59']
CACHE = os.path.join(RAW15, 'cache')
os.makedirs(CACHE, exist_ok=True)


def read_gz(pattern):
    """Lit des jsonl.gz éventuellement en cours d'écriture (dernier bloc incomplet ignoré)."""
    out = []
    for fp in sorted(glob.glob(os.path.join(RAW15, pattern))):
        d = zlib.decompressobj(16 + zlib.MAX_WBITS)
        data = d.decompress(open(fp, 'rb').read())
        for l in data.split(b'\n'):
            if l:
                try:
                    out.append(json.loads(l))
                except Exception:
                    pass
    return out


def rpc(method, params, url='https://polygon.drpc.org'):
    for k in range(4):
        try:
            req = urllib.request.Request(url, data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}).encode(),
                                         headers={'Content-Type': 'application/json', 'User-Agent': 'curl/8.4.0'})
            return json.loads(urllib.request.urlopen(req, timeout=60).read()).get('result')
        except Exception:
            time.sleep(2)


def get(u):
    for k in range(4):
        try:
            return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'curl/8.4.0'}), timeout=60).read())
        except Exception:
            time.sleep(2)
    return None


def load():
    rt = pd.DataFrame(read_gz('rtds_*.jsonl.gz'), columns=['t_recv', 'conn', 'tx', 'asset', 'cid', 'wallet', 'side', 'oi', 'price', 'size', 'ts', 'fee', 'slug', 'outcome'])
    ch = read_gz('chain_*.jsonl.gz')
    logs = pd.DataFrame([r for r in ch if r[1] in ('log', 'backfill')], columns=['t_recv', 'src', 'tx', 'block', 'logIndex', 'topics', 'data'])
    heads = pd.DataFrame([r for r in ch if r[1] == 'head'], columns=['t_recv', 'src', 'block', 'block_ts'])
    ev = pd.DataFrame([dict(t=r[0], **r[1]) for r in read_gz('evenements_*.jsonl.gz')])
    return rt, logs, heads, ev


def truth_fills(logs, heads):
    """Fills de l'ordre preneur : un par (tx, logIndex). Prix et montants dans le sens du preneur."""
    L = logs.drop_duplicates(['tx', 'logIndex']).copy()
    t3 = L.topics.str[3].str[-40:].str.lower()
    L = L[t3.isin(EXL)].copy()
    L['wallet'] = '0x' + L.topics.str[2].str[-40:].str.lower()
    v = L.data.str[2:].map(lambda d: [int(d[i:i + 64], 16) for i in range(0, 5 * 64, 64)])
    L['side'] = np.where(v.str[0] == 0, 'BUY', 'SELL')
    L['asset'] = v.str[1].astype(str)
    mk, tk = v.str[2] / 1e6, v.str[3] / 1e6
    L['price'] = np.where(L.side == 'BUY', mk / tk.replace(0, np.nan), tk / mk.replace(0, np.nan))
    L['size'] = np.where(L.side == 'BUY', tk, mk)
    L['usd'] = np.where(L.side == 'BUY', mk, tk)
    hb = heads.drop_duplicates('block').set_index('block').block_ts
    L['block_ts'] = L.block.map(hb)
    miss = sorted(set(L[L.block_ts.isna()].block))
    for b in miss:                                     # blocs rattrapés sans en-tête : horodatage par RPC
        r = rpc('eth_getBlockByNumber', [hex(int(b)), False])
        if r:
            L.loc[L.block == b, 'block_ts'] = int(r['timestamp'], 16)
    first = L.sort_values('t_recv').drop_duplicates(['tx', 'logIndex'])
    return first


def taker_row(rows, elig=None):
    """Règle du listener P11 : ligne fee unique ; sinon ligne unique ; sinon « ambigu » -> première ligne reçue."""
    fee = rows[rows.fee.notna()]
    if len(fee) == 1:
        return fee.iloc[0], 'fee'
    if len(rows) == 1:
        return rows.iloc[0], 'ligne_unique'
    return rows.sort_values('t_recv').iloc[0], 'ambigu'


def price_class(p_src, p_true, asset_src, asset_true):
    if p_src is None or (isinstance(p_src, float) and np.isnan(p_src)):
        return 'UNKNOWN'
    if asset_src is not None and str(asset_src) != str(asset_true):
        return 'WRONG_TOKEN'
    d = abs(float(p_src) - float(p_true))
    if d < 1e-6:
        return 'CORRECT'
    if abs(float(p_src) - (1 - float(p_true))) < 1e-6:
        return 'WRONG_SIDE'
    if d < 0.005:
        return 'ROUNDING'
    return 'WRONG (écart > 0,5 point)'


def bout_en_bout_live(Tt):
    """Trades d'au moins 250 $ (achats) des marchés abonnés au carnet P11 pendant l'audit : chaque étape, et le FAE du listener contre la définition."""
    import concurrent.futures as cf
    E = Tt[(Tt.side == 'BUY') & (Tt.usd >= 250) & Tt.marche_suivi_carnet].copy()
    S = pd.read_pickle(os.path.join(CACHE, 'p11_rtds_live.pkl')) if os.path.exists(os.path.join(CACHE, 'p11_rtds_live.pkl')) else None

    def fae(r):
        g = (get(f'https://gamma-api.polymarket.com/markets?clob_token_ids={r.asset}') or get(f'https://gamma-api.polymarket.com/markets?closed=true&clob_token_ids={r.asset}') or [{}])[0]
        cid = g.get('conditionId')
        if not cid:
            return dict(tx=r.tx, cid=None, fae_definition=None)
        prev = get(f'https://data-api.polymarket.com/trades?user={r.wallet}&market={cid}&start={int(r.block_ts) - 86400}&end={int(r.block_ts)}&limit=50&takerOnly=true') or []
        prev = [p for p in prev if p['transactionHash'] != r.tx and float(p['price']) * float(p['size']) >= 100 and int(p['timestamp']) <= r.block_ts]
        return dict(tx=r.tx, cid=cid, slug=g.get('slug'), fae_definition=len(prev) == 0)
    with cf.ThreadPoolExecutor(6) as ex:
        F2 = pd.DataFrame(list(ex.map(fae, E.itertuples())))
    E = E.merge(F2, on='tx', how='left')
    F = pd.DataFrame([json.loads(l) for l in open(B + 'brut_p11/live/fae_events.jsonl')]).drop_duplicates('tx').set_index('tx')
    Sg = pd.DataFrame([json.loads(l) for l in open(B + 'brut_p12/live_signals.jsonl')])
    jl_ = lambda f: [json.loads(l) for l in open(f)] if os.path.exists(f) else []  # noqa: E731
    al11 = {a['tx'] for a in jl_(B + 'brut_p11/live/alerts.jsonl')}
    al13 = {a['tx'] for a in jl_(B + 'brut_p13/paper_alerts.jsonl')}
    p14 = {a.get('tx2') for a in jl_(B + 'brut_p14/paper_second_buy.jsonl')}
    ts = lambda v: pd.Timestamp(v, unit='ns') if v == v and v is not None else None  # noqa: E731
    E = E.assign(periode='audit live', T_trade_bloc=E.block_ts, T_rpc_reception=E.recv_chaine.map(ts), T_rtds_A=E.recv_A.map(ts), T_rtds_B=E.recv_B.map(ts),
                 T_rtds_collecteur_P11=E.recv_p11_rtds.map(ts), T_clob_reception=E.recv_p11_ltp.map(ts), rtds_statut_preneur=E.statut_preneur, rtds_conditionId_vide=E.cid_vide,
                 p11_listener_FAE=E.tx.isin(F.index), p11_listener_wallet=[F.wallet.get(t) for t in E.tx], p11_listener_marche_vide=[F.market.get(t) == '' if t in F.index else None for t in E.tx],
                 p11_listener_T_obs=[ts(F.T_obs_ns.get(t)) if t in F.index else None for t in E.tx],
                 p12_signal_jeton_60s=[bool(((Sg.token == a) & ((Sg.t_local_ns - t * 1e9).abs() <= 60e9)).any()) if len(Sg) else False for a, t in zip(E.asset, E.block_ts)],
                 p11_alerte=E.tx.isin(al11), p13_alerte=E.tx.isin(al13), p14_second_achat=E.tx.isin(p14))
    E['p11_listener_bon_wallet'] = E.p11_listener_wallet == E.wallet
    cols = ['periode', 'tx', 'cid', 'slug', 'asset', 'wallet', 'usd', 'T_trade_bloc', 'T_rpc_reception', 'T_rtds_A', 'T_rtds_B', 'T_rtds_collecteur_P11', 'T_clob_reception',
            'rtds_statut_preneur', 'rtds_conditionId_vide', 'fae_definition', 'p11_listener_FAE', 'p11_listener_bon_wallet', 'p11_listener_marche_vide', 'p11_listener_T_obs',
            'p12_signal_jeton_60s', 'p11_alerte', 'p13_alerte', 'p14_second_achat']
    E[cols].to_csv(OUT + 'phase15_end_to_end_live.csv', index=False)
    f = E[E.fae_definition == True]  # noqa: E712
    return dict(trades=len(E), fae_definition=len(f), fae_bon_wallet=int((f.p11_listener_FAE & f.p11_listener_bon_wallet).sum()),
                fae_mauvais_wallet=int((f.p11_listener_FAE & ~f.p11_listener_bon_wallet).sum()), fae_non_logges=int((~f.p11_listener_FAE).sum()),
                fae_non_logges_ambigus=int((~f.p11_listener_FAE & (f.rtds_statut_preneur == 'ambigu')).sum()),
                fae_non_logges_marche_vide=int((~f.p11_listener_FAE & (f.rtds_conditionId_vide == True)).sum()),  # noqa: E712
                fae_hors_definition=int(((E.fae_definition == False) & E.p11_listener_FAE).sum()),  # noqa: E712
                part_ambigus=float((E.rtds_statut_preneur == 'ambigu').mean()) if len(E) else None)


def main():
    rt, logs, heads, ev = load()
    T = truth_fills(logs, heads)
    t0 = ev[ev.ev == 'demarrage'].t.min()
    t_end = min(rt.t_recv.max(), logs.t_recv.max())
    # coupure de l'enregistrement (veille du Mac : aucun message pendant plus de 10 min) : la fenêtre de vérité s'arrête avant
    ra = np.sort(rt[rt.conn == 'A'].t_recv.values)
    gaps_long = np.nonzero(np.diff(ra) > 600e9)[0]
    veille = None
    if len(gaps_long):
        veille = (int(ra[gaps_long[0]]), int(ra[gaps_long[0] + 1]))
        t_end = veille[0]
    # fenêtre de vérité : blocs horodatés entre démarrage + 60 s et fin - 120 s
    w0, w1 = t0 / 1e9 + 60, t_end / 1e9 - 120
    T = T[(T.block_ts >= w0) & (T.block_ts <= w1)].copy()
    hb = heads.drop_duplicates('block')
    blocks = set(hb[(hb.block_ts >= w0) & (hb.block_ts <= w1)].block) | set(T.block)
    bmin, bmax = (min(blocks), max(blocks)) if blocks else (0, -1)
    bf = ev[(ev.ev == 'rattrapage')]
    covered = set(hb.block)
    for r in bf.itertuples():
        if getattr(r, 'ok', False):
            covered |= set(range(int(r.de), int(r.a) + 1))
    manquants = [b for b in range(bmin, bmax + 1) if b not in covered]
    resume = dict(debut_audit=str(pd.Timestamp(t0, unit='ns')), fin_lue=str(pd.Timestamp(t_end, unit='ns')), fenetre_verite=[str(pd.Timestamp(w0, unit='s')), str(pd.Timestamp(w1, unit='s'))],
                  blocs_fenetre=bmax - bmin + 1, blocs_sans_entete=int(sum(1 for b in range(bmin, bmax + 1) if b not in set(hb.block))),
                  blocs_non_couverts_apres_rattrapage=len(manquants), fills_preneur_verite=len(T), tx_verite=int(T.tx.nunique()),
                  logs_live=int((logs.src == 'log').sum()), logs_rattrapes=int((logs.src == 'backfill').sum()),
                  coupure_enregistrement=[str(pd.Timestamp(veille[0], unit='ns')), str(pd.Timestamp(veille[1], unit='ns'))] if veille else None)
    print(json.dumps(resume, indent=1))
    Tt = T.sort_values('logIndex').drop_duplicates('tx')          # un trade = une transaction (premier fill preneur)
    # ---- sources
    rtA, rtB = rt[rt.conn == 'A'], rt[rt.conn == 'B']
    # RTDS du collecteur P11 et carnet P11 sur la même fenêtre
    a_ns, b_ns = int(w0 * 1e9) - 120 * 10 ** 9, int(w1 * 1e9) + 300 * 10 ** 9
    p11r = []
    for t, conn, msg in iter_raw('rtds', a_ns, b_ns):
        if msg.startswith('{'):
            p = json.loads(msg).get('payload') or {}
            if p.get('transactionHash'):
                p11r.append((t, p['transactionHash'], (p.get('proxyWallet') or '').lower(), str(p.get('asset')), p.get('fee'), p.get('conditionId') or ''))
    p11r = pd.DataFrame(p11r, columns=['t_recv', 'tx', 'wallet', 'asset', 'fee', 'cid'])
    ltp = []
    for t, conn, msg in iter_raw('ws_market', a_ns, b_ns):
        for e in events(msg):
            if isinstance(e, dict) and e.get('event_type') == 'last_trade_price':
                ltp.append((t, e.get('transaction_hash'), e.get('asset_id'), float(e.get('price') or 0), int(e.get('timestamp') or 0)))
    ltp = pd.DataFrame(ltp, columns=['t_recv', 'tx', 'asset', 'price', 'ts_ms'])
    p11c = []
    for t, conn, msg in iter_raw('chain', a_ns, b_ns):
        try:
            r = (json.loads(msg).get('params') or {}).get('result')
        except Exception:
            continue
        if isinstance(r, dict) and 'topics' in r:
            p11c.append((t, r['transactionHash']))
    p11c = pd.DataFrame(p11c, columns=['t_recv', 'tx'])
    snaps, cur = [], {}                                  # abonnements actifs du carnet P11 au fil du temps (par connexion)
    for l in open(B + 'brut_p11/meta/subscriptions.jsonl'):
        x = json.loads(l)
        c = str(x.get('conn', ''))
        if c.startswith('c') and x.get('event') == 'subscribe':
            cur[c] = set(x.get('markets') or [])
        elif c.startswith('c') and x.get('event') == 'ajout_dynamique':
            cur[c] = cur.get(c, set()) | set(x.get('markets') or [])
        else:
            continue
        snaps.append((x['t_ns'], set().union(*cur.values())))
    snap_t = [t for t, _ in snaps]
    import bisect
    def suivi(cid, t_ns):
        k = bisect.bisect_right(snap_t, t_ns) - 1
        return k >= 0 and cid in snaps[k][1]
    wl = {}
    for fp in sorted(glob.glob(B + 'brut_p11/meta/watchlist_*.json')):
        for c, x in json.load(open(fp))['watchlist'].items():
            for tk in x['tokens']:
                wl[str(tk)] = c
    elig = set(json.load(open(B + 'brut_p11/live/wallets_eligibles_au_demarrage.json')))
    hist_sig = elig.copy()
    # ---- trade par trade
    first = lambda D: D.sort_values('t_recv').drop_duplicates('tx').set_index('tx').t_recv  # noqa: E731
    fa, fb, fp11, fl, fc = first(rtA), first(rtB), first(p11r), first(ltp), first(p11c)
    fchain = T.sort_values('t_recv').drop_duplicates('tx').set_index('tx').t_recv
    Tt = Tt.assign(recv_chaine=Tt.tx.map(fchain), recv_A=Tt.tx.map(fa), recv_B=Tt.tx.map(fb), recv_p11_rtds=Tt.tx.map(fp11), recv_p11_ltp=Tt.tx.map(fl),
                   recv_p11_chaine=Tt.tx.map(fc), marche_suivi_carnet=[suivi(wl.get(a), int(t * 1e9)) for a, t in zip(Tt.asset, Tt.block_ts)], wallet_filtre_p11=Tt.wallet.isin(hist_sig))
    Tt['taille'] = pd.cut(Tt.usd, [0, 10, 100, 1000, 1e12], labels=['< 10 $', '10-100 $', '100-1 000 $', '>= 1 000 $'], right=False)
    Tt['heure'] = pd.to_datetime(Tt.block_ts, unit='s').dt.floor('h')
    # champs RTDS A contre la vérité (règle du listener)
    gA = {k: g for k, g in rtA.groupby('tx')}
    recs = []
    for r in Tt.itertuples():
        g = gA.get(r.tx)
        if g is None:
            continue
        row, statut = taker_row(g)
        tk = g[g.wallet == r.wallet]
        tkr = tk.iloc[0] if len(tk) else None
        recs.append(dict(tx=r.tx, statut_preneur=statut, n_lignes=len(g), n_fee=int(g.fee.notna().sum()), wallet_verite=r.wallet, wallet_regle_listener=row.wallet,
                         wallet_ok=row.wallet == r.wallet, wallet_present_dans_lignes=tkr is not None, cid_vide=row.cid in ('', None),
                         prix_verite=r.price, prix_regle_listener=row.price, prix_ligne_preneur=tkr.price if tkr is not None else None,
                         classe_prix_regle=price_class(row.price, r.price, row.asset, r.asset),
                         classe_prix_ligne_preneur=price_class(tkr.price, r.price, tkr.asset, r.asset) if tkr is not None else 'UNKNOWN',
                         side_ok=(row.side == r.side), jeton_ok=str(row.asset) == str(r.asset), oi_rtds=row.oi, ts_rtds=row.ts, usd=r.usd, block_ts=r.block_ts))
    FA = pd.DataFrame(recs)
    Tt = Tt.merge(FA[['tx', 'statut_preneur', 'wallet_ok', 'cid_vide', 'classe_prix_regle', 'ts_rtds']], on='tx', how='left')
    Tt.to_pickle(os.path.join(CACHE, 'trades_verite.pkl'))
    FA.to_pickle(os.path.join(CACHE, 'champs_A.pkl'))
    # ---- couverture et latence par source
    rows = []
    srcs = [('RTDS A (continue)', 'recv_A', None), ('RTDS B (coupée 30 s / 20 min)', 'recv_B', None), ('RTDS collecteur P11', 'recv_p11_rtds', None),
            ('carnet P11 last_trade_price (marchés suivis)', 'recv_p11_ltp', 'marche_suivi_carnet'), ('chaîne collecteur P11 (wallets filtrés)', 'recv_p11_chaine', 'wallet_filtre_p11'),
            ('chaîne audit (vérité, flux)', 'recv_chaine', None)]
    for name, col, scope in srcs:
        for grp in ['global', 'taille', 'heure', 'side']:
            X = Tt if scope is None else Tt[Tt[scope]]
            parts = [('tous', X)] if grp == 'global' else [(str(k), x) for k, x in X.groupby(grp, observed=True)]
            for k, x in parts:
                seen = x[x[col].notna()]
                lat = (seen[col] / 1e9 - seen.block_ts)
                rows.append(dict(source=name, groupe=grp, valeur=k, verite_tx=len(x), observes=len(seen), manquants=len(x) - len(seen), rappel=len(seen) / max(len(x), 1),
                                 latence_vs_bloc_P50_s=lat.quantile(.5), P90=lat.quantile(.9), P95=lat.quantile(.95), P99=lat.quantile(.99), max=lat.max(),
                                 note='réception locale (Mac, SNTP ±0,1 s) moins horodatage de bloc : horloges de nature différente'))
    # précision : transactions RTDS absentes de la vérité (fenêtre et blocs couverts)
    for name, D in (('RTDS A (continue)', rtA), ('RTDS B (coupée 30 s / 20 min)', rtB), ('RTDS collecteur P11', p11r)):
        ts_col = 'ts' if 'ts' in D else None
        Dw = D[(D.t_recv / 1e9 >= w0 + 5) & (D.t_recv / 1e9 <= w1 - 5)]
        txs = set(Dw.tx)
        ok = len(txs & set(T.tx))
        rows.append(dict(source=name, groupe='précision', valeur='tx RTDS présentes dans la vérité', verite_tx=len(txs), observes=ok, rappel=ok / max(len(txs), 1),
                         note='précision ; les manquantes peuvent tomber dans des blocs non couverts'))
    C = pd.DataFrame(rows)
    C.to_csv(OUT + 'phase15_trade_coverage_live.csv', index=False)
    # ---- champs (prix, wallet)
    FA.to_csv(OUT + 'phase15_price_audit.csv', index=False, columns=['tx', 'usd', 'statut_preneur', 'n_lignes', 'n_fee', 'prix_verite', 'prix_regle_listener', 'classe_prix_regle',
                                                                      'prix_ligne_preneur', 'classe_prix_ligne_preneur', 'side_ok', 'jeton_ok', 'cid_vide', 'oi_rtds'])
    FA.to_csv(OUT + 'phase15_wallet_audit.csv', index=False, columns=['tx', 'usd', 'statut_preneur', 'n_lignes', 'n_fee', 'wallet_verite', 'wallet_regle_listener', 'wallet_ok',
                                                                       'wallet_present_dans_lignes', 'cid_vide'])
    # ---- horodatages
    lat = []
    def add(nom, x, nature):
        x = pd.Series(x, dtype=float).dropna()
        if len(x):
            lat.append(dict(paire=nom, n=len(x), P1=x.quantile(.01), P10=x.quantile(.1), P50=x.median(), P90=x.quantile(.9), P99=x.quantile(.99), max=x.max(), nature=nature))
    add('ts RTDS - ts bloc (s)', FA.ts_rtds - FA.block_ts, 'deux horodatages source (secondes)')
    add('réception RTDS A - ts bloc (ms)', (Tt.recv_A / 1e6 - Tt.block_ts * 1e3), 'réception locale contre horodatage de bloc : natures différentes')
    add('réception chaîne - ts bloc (ms)', (Tt.recv_chaine / 1e6 - Tt.block_ts * 1e3), 'idem')
    add('réception RTDS A - réception chaîne (ms)', (Tt.recv_A - Tt.recv_chaine) / 1e6, 'même horloge locale')
    add('réception RTDS B - réception RTDS A (ms)', (Tt.recv_B - Tt.recv_A) / 1e6, 'même horloge locale, deux connexions')
    add('réception RTDS collecteur - réception RTDS A (ms)', (Tt.recv_p11_rtds - Tt.recv_A) / 1e6, 'même horloge locale, deux processus')
    add('réception ltp collecteur - réception chaîne (ms)', (Tt.recv_p11_ltp - Tt.recv_chaine) / 1e6, 'même horloge locale')
    lj = ltp.drop_duplicates('tx').merge(Tt[['tx', 'block_ts', 'recv_A']], on='tx')
    add('heure d échange ltp - ts bloc (ms)', lj.ts_ms - lj.block_ts * 1e3, 'heure d échange (ms) contre bloc (s)')
    add('réception ltp - heure d échange ltp (ms)', ltp.t_recv / 1e6 - ltp.ts_ms, 'réception locale contre heure d échange')
    hb2 = heads.drop_duplicates('block')
    add('réception en-tête - ts bloc (ms)', hb2.t_recv / 1e6 - hb2.block_ts * 1e3, 'réception locale contre horodatage de bloc')
    pd.DataFrame(lat).to_csv(OUT + 'phase15_latency_live.csv', index=False)
    # ---- doublons (RTDS A et B) contre le nombre de fills de la chaîne
    Lall = logs.drop_duplicates(['tx', 'logIndex']).copy()
    Lall['wallet'] = '0x' + Lall.topics.str[2].str[-40:].str.lower()
    Lall['asset'] = Lall.data.str[2:].map(lambda d: str(int(d[64:128], 16)))
    nch = Lall.groupby(['tx', 'wallet', 'asset']).size()
    dup = []
    for conn, D in (('A', rtA), ('B', rtB)):
        D = D[D.tx.isin(set(T.tx))]
        g = D.groupby(['tx', 'wallet', 'asset']).agg(n=('t_recv', 'size'), n_ts=('ts', 'nunique'), ecart=('t_recv', lambda s: (s.max() - s.min()) / 1e9))
        g['n_chaine'] = [nch.get(k, 0) for k in g.index]
        g = g[g.n >= 2]
        for k, r in g.iterrows():
            cls = 'TRUE_DUPLICATE' if r.n > r.n_chaine else ('TIMESTAMP_ALIAS' if r.n_ts > 1 else 'fills distincts (pas un doublon)')
            dup.append(dict(source=f'RTDS {conn}', tx=k[0], wallet=k[1], asset=k[2], lignes=int(r.n), fills_chaine=int(r.n_chaine), timestamps=int(r.n_ts), ecart_reception_s=r.ecart, classe=cls))
        # même trade sur deux sources : clé = hash de transaction (RTDS) = hash de transaction (chaîne) ; pas d identifiant de fill commun
    lg = logs.groupby(['tx', 'logIndex']).size()
    for k, n in lg[lg > 1].items():
        dup.append(dict(source='chaîne audit', tx=k[0], lignes=int(n), classe='TRUE_DUPLICATE (log reçu deux fois : direct + rattrapage)'))
    pd.DataFrame(dup).to_csv(OUT + 'phase15_duplicates_live.csv', index=False)
    # ---- reconnexions
    rc = []
    for conn in ('A', 'B'):
        e = ev[ev.src == f'rtds_{conn}'].sort_values('t')
        for r in e[e.ev.isin(['coupure_volontaire', 'erreur'])].itertuples():
            nxt = e[(e.t > r.t) & (e.ev == 'connexion')]
            if not len(nxt):
                continue
            g1 = nxt.t.iloc[0]
            g0 = r.t - (30e9 if 'silence' in str(getattr(r, 'err', '')) else 0)
            x = Tt[(Tt.recv_chaine >= g0) & (Tt.recv_chaine <= g1)] if 'recv_chaine' in Tt else Tt.iloc[0:0]
            xin = Tt[(Tt.block_ts * 1e9 >= g0 - 2e9) & (Tt.block_ts * 1e9 <= g1)]
            col = f'recv_{conn}'
            other = 'recv_B' if conn == 'A' else 'recv_A'
            rc.append(dict(connexion=f'RTDS {conn}', cause=r.ev + ' ' + str(getattr(r, 'err', ''))[:40], gap_start=pd.Timestamp(g0, unit='ns'), reconnect_time=pd.Timestamp(g1, unit='ns'),
                           duree_s=(g1 - g0) / 1e9, trades_verite_dans_le_trou=len(xin), manques_par_la_connexion=int(xin[col].isna().sum()),
                           vus_par_l_autre_connexion=int(xin[xin[col].isna()][other].notna().sum()), recovered='non (RTDS ne rejoue pas)',
                           recuperable_par='data-api /trades (complet, phase 10) ou eth_getLogs', duplicates_apres_reconnexion=0))
    for r in ev[ev.ev == 'trou_entetes'].itertuples():
        bfr = ev[(ev.ev == 'rattrapage') & (ev.de == r.de)]
        rc.append(dict(connexion='chaîne audit', cause='trou d en-têtes', gap_start=pd.Timestamp(r.t, unit='ns'), blocs=f'{int(r.de)}-{int(r.a)}', duree_blocs=int(r.a - r.de + 1),
                       recovered='oui (eth_getLogs)' if len(bfr) and bool(bfr.ok.iloc[0]) else 'non', recuperable_par='eth_getLogs'))
    pd.DataFrame(rc).to_csv(OUT + 'phase15_reconnect_live.csv', index=False)
    # ---- résumé
    def rap(col, scope=None):
        X = Tt if scope is None else Tt[Tt[scope]]
        return round(float(X[col].notna().mean()), 4) if len(X) else None
    resume.update(rappel_A=rap('recv_A'), rappel_B=rap('recv_B'), rappel_p11_rtds=rap('recv_p11_rtds'), rappel_ltp_suivis=rap('recv_p11_ltp', 'marche_suivi_carnet'),
                  rappel_p11_chaine_filtres=rap('recv_p11_chaine', 'wallet_filtre_p11'), rappel_union_A_B=round(float((Tt.recv_A.notna() | Tt.recv_B.notna()).mean()), 4),
                  statut_preneur=FA.statut_preneur.value_counts(normalize=True).round(4).to_dict(),
                  wallet_ok_regle_listener=round(float(FA.wallet_ok.mean()), 4) if len(FA) else None,
                  wallet_ok_si_ambigu=round(float(FA[FA.statut_preneur == 'ambigu'].wallet_ok.mean()), 4) if (FA.statut_preneur == 'ambigu').any() else None,
                  classe_prix_regle=FA.classe_prix_regle.value_counts(normalize=True).round(4).to_dict(), cid_vide=round(float(FA.cid_vide.mean()), 4) if len(FA) else None,
                  sur_100_dollars=dict(n=int((FA.usd >= 100).sum()), wallet_ok=round(float(FA[FA.usd >= 100].wallet_ok.mean()), 4) if (FA.usd >= 100).any() else None,
                                       prix_correct=round(float(FA[FA.usd >= 100].classe_prix_regle.isin(['CORRECT', 'ROUNDING']).mean()), 4) if (FA.usd >= 100).any() else None,
                                       ambigu=round(float((FA[FA.usd >= 100].statut_preneur == 'ambigu').mean()), 4) if (FA.usd >= 100).any() else None))
    resume['bout_en_bout_live'] = bout_en_bout_live(Tt)
    json.dump(resume, open(OUT + 'phase15_live_resume.json', 'w'), indent=1, default=str, ensure_ascii=False)
    print(json.dumps(resume, indent=1, default=str, ensure_ascii=False))


if __name__ == '__main__':
    main()
