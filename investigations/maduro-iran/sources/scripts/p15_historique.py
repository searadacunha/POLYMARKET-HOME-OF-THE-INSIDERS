#!/usr/bin/env python3
"""Phase 15 : audits sur les données déjà enregistrées par les phases 11 à 14 (lecture seule) et sur les sources publiques.
  cas Oklahoma, champs RTDS (marché vide, outcome), trous des flux, doublons, horodatages, couverture des marchés, watchlist, 8 comptes,
  bout en bout (FAE du listener contre la définition), régression Maduro / Iran, rejouabilité des alertes SIG_HIST, chiens de garde.
Sorties (phase15/) : *_p11.csv (période du 01/10 08:51 à 11:30 UTC) et tables complètes (market_coverage, watchlist_audit, sig_hist_replay, ...).
Usage : python3 p15_historique.py   (environ 10 min ; appels Gamma, data-api, RPC publics)"""
import os, sys, json, glob, time, random, subprocess, urllib.request, concurrent.futures as cf
import numpy as np, pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p11_replay import iter_raw, events, _read  # noqa: E402
from p11_common import excluded, category, EXCL, GAME, DATA  # noqa: E402

ROOT = os.path.expanduser('~/Documents/Crypto/enquete_maduro_iran')
B = os.path.join(ROOT, 'donnees') + '/'
OUT = os.path.join(ROOT, 'phase15') + '/'
CACHE = os.path.join(B, 'brut_p15', 'cache') + '/'
os.makedirs(CACHE, exist_ok=True)
T0 = int(pd.Timestamp('2026-10-01T08:45', tz='UTC').value)
T1 = int(pd.Timestamp('2026-10-01T11:30', tz='UTC').value)
OKLA = '0xabe90f8b5b16fe3e4cd6fb2d6bf35461e752719ea9cdb0947c4ec1b383ec18ad'
OKLA_TX = '0x4d0a723dc9f6e9e94316392e5c834d959e7da43f206405f2215788558563649a'
A8 = {'0x168b100d7a6620a2f49a455344c2c006eaf1714b': 'Chiwawas', '0x5621116629c5d640c8186f577362478cc6605245': 'TacticalInsiderNews',
      '0x38745db27f7360a287f6ca3c9b6a6a9c76149801': 'Planktonbets', '0x60280beffdfeaf962de4e6397ab49ed05a1b99e1': 'X34',
      '0x834079f62fa9b4b0bdfad5b8b7a841e8267da024': 'chileno777', '0xbf32f7a77ccea8bba647fea63d438ce1778b1762': '154x838hjd6',
      '0x56efadc9defe5b7a21af751e0d026f2cf54136db': 'Neodbs', '0xe9b80c387ba77a585423b13c850c2e126c3befd8': 'Mrs.Joker'}


def get(u, t=60):
    for k in range(5):
        try:
            return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'curl/8.4.0'}), timeout=t).read())
        except Exception:
            time.sleep(2)
    return None


def rpc(method, params, url='https://polygon.drpc.org'):
    for k in range(4):
        try:
            req = urllib.request.Request(url, data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}).encode(),
                                         headers={'Content-Type': 'application/json', 'User-Agent': 'curl/8.4.0'})
            return json.loads(urllib.request.urlopen(req, timeout=60).read()).get('result')
        except Exception:
            time.sleep(2)


def jl(fp):
    return [json.loads(l) for l in open(fp)] if os.path.exists(fp) else []


# ------------------------------------------------------------------ chargement des données brutes P11
def charger():
    fp = CACHE + 'p11_rtds.pkl'
    if os.path.exists(fp):
        return {k: pd.read_pickle(CACHE + f'p11_{k}.pkl') for k in ('rtds', 'ltp', 'chain', 'heads')}
    R = []
    for t, conn, msg in iter_raw('rtds', T0, T1):
        if not msg.startswith('{'):
            continue
        p = json.loads(msg).get('payload') or {}
        if p.get('transactionHash'):
            R.append((t, p['transactionHash'], str(p.get('asset')), p.get('conditionId') or '', (p.get('proxyWallet') or '').lower(), p.get('side'), p.get('outcomeIndex'),
                      float(p.get('price') or 0), float(p.get('size') or 0), int(p.get('timestamp') or 0), p.get('fee'), p.get('slug') or '', p.get('outcome') or ''))
    R = pd.DataFrame(R, columns=['t_recv', 'tx', 'asset', 'cid', 'wallet', 'side', 'oi', 'price', 'size', 'ts', 'fee', 'slug', 'outcome'])
    L = []
    for t, conn, msg in iter_raw('ws_market', T0, T1):
        for e in events(msg):
            if isinstance(e, dict) and e.get('event_type') == 'last_trade_price':
                L.append((t, conn, e.get('transaction_hash'), e.get('asset_id'), e.get('market'), e.get('side'), float(e.get('price') or 0), float(e.get('size') or 0), int(e.get('timestamp') or 0)))
    L = pd.DataFrame(L, columns=['t_recv', 'conn', 'tx', 'asset', 'cid', 'side', 'price', 'size', 'ts_ms'])
    C, H = [], []
    for t, conn, msg in iter_raw('chain', T0, T1):
        try:
            r = (json.loads(msg).get('params') or {}).get('result')
        except Exception:
            continue
        if isinstance(r, dict) and 'topics' in r:
            C.append((t, r['transactionHash'], int(r['blockNumber'], 16), int(r['logIndex'], 16), r['topics'], r['data']))
        elif isinstance(r, dict) and 'number' in r:
            H.append((t, int(r['number'], 16), int(r['timestamp'], 16)))
    C = pd.DataFrame(C, columns=['t_recv', 'tx', 'block', 'logIndex', 'topics', 'data'])
    H = pd.DataFrame(H, columns=['t_recv', 'block', 'block_ts'])
    for k, D in (('rtds', R), ('ltp', L), ('chain', C), ('heads', H)):
        D.to_pickle(CACHE + f'p11_{k}.pkl')
    return dict(rtds=R, ltp=L, chain=C, heads=H)


def mapper(assets):
    """Jeton -> marché (Gamma, clobTokenIds ; l'ordre donne l'outcome). Vérité D."""
    fp = CACHE + 'map_assets.pkl'
    M = pd.read_pickle(fp) if os.path.exists(fp) else pd.DataFrame(columns=['asset'])
    todo = [a for a in set(assets) if a not in set(M.asset)]

    def batch(b):
        out = {}
        for closed in ('false', 'true'):
            q = '&'.join('clob_token_ids=' + t for t in b if t not in out)
            if not q:
                break
            for m in get(f'https://gamma-api.polymarket.com/markets?closed={closed}&limit=100&' + q) or []:
                for j, t in enumerate(json.loads(m.get('clobTokenIds') or '[]')):
                    out[t] = dict(cid_vrai=m['conditionId'], slug_vrai=m.get('slug'), question=m.get('question'), oi_vrai=j, createdAt=m.get('createdAt'),
                                  volume=float(m.get('volume') or 0), excl=excluded(m.get('slug'), m.get('question')), negRisk=m.get('negRisk'),
                                  feesEnabled=m.get('feesEnabled'))
        return out
    new = {}
    with cf.ThreadPoolExecutor(6) as ex:
        for o in ex.map(batch, [todo[i:i + 40] for i in range(0, len(todo), 40)]):
            new.update(o)
    if new:
        M = pd.concat([M, pd.DataFrame([dict(asset=a, **v) for a, v in new.items()])]).drop_duplicates('asset')
        M.to_pickle(fp)
    return M


# ------------------------------------------------------------------ audits
def oklahoma(D, M):
    R = D['rtds']
    al = jl(B + 'brut_p11/live/alerts.jsonl')
    fae = [f for f in jl(B + 'brut_p11/live/fae_events.jsonl') if f.get('tx') == OKLA_TX]
    p13 = [a for a in jl(B + 'brut_p13/paper_alerts.jsonl') if a.get('tx') == OKLA_TX]
    api = get(f'https://data-api.polymarket.com/trades?market={OKLA}&start=1790850500&end=1790850600&limit=500&takerOnly=true') or []
    x = [r for r in api if r['transactionHash'] == OKLA_TX][0]
    rc = rpc('eth_getTransactionReceipt', [OKLA_TX])
    blk = rpc('eth_getBlockByNumber', [rc['blockNumber'], False]) if rc else None
    gam = (get(f'https://gamma-api.polymarket.com/markets?condition_ids={OKLA}') or [{}])[0]
    subs = jl(B + 'brut_p11/meta/subscriptions.jsonl')
    gap = [s for s in subs if s.get('conn') == 'rtds' and abs(s['t_ns'] - 1790850569252836000) < 2e9]
    rows = [dict(etape='T0 trade (vérité A, bloc)', t=pd.Timestamp(int(blk['timestamp'], 16), unit='s') if blk else None, source='Polygon (reçu, drpc archive)',
                 detail=f"bloc {int(rc['blockNumber'], 16) if rc else None} ; data-api timestamp {x['timestamp']} ; wallet {x['proxyWallet'][:10]} ; BUY {x['outcome']} (outcomeIndex {x['outcomeIndex']}) à {x['price']} ; {float(x['price']) * float(x['size']):.2f} $"),
            dict(etape='marché (vérité D)', t=pd.Timestamp(gam.get('createdAt')), source='Gamma', detail=f"{gam.get('slug')} ; créé le {gam.get('createdAt')} ; jetons {json.loads(gam.get('clobTokenIds', '[]'))[1][:12]}… = No"),
            dict(etape='T1 carnet CLOB', t=None, source='collecteur P11', detail='marché jamais abonné (hors watchlist P11 / P12) : aucun message carnet'),
            dict(etape='T3 RTDS listener P11', t=pd.Timestamp(fae[0]['T_obs_ns'], unit='ns') if fae else None, source='RTDS (connexion du listener)',
                 detail=f"conditionId VIDE, outcomeIndex {fae[0]['outcomeIndex']} (vrai : 1), ts RTDS {fae[0]['ts_echange']} ; rangé dans le pseudo-marché '' : p_before {fae[0]['p_before']} (vrai : 0,66), dpre_10m {fae[0]['dpre_10m']:.3f} -> FOLLOW -> pas d alerte" if fae else ''),
            dict(etape='RTDS collecteur P11', t=None, source='RTDS (connexion du collecteur)', detail=f"non reçu : connexion silencieuse de 10:28:59 à 10:29:30 (chien de garde : {gap[0]['err'] if gap else ''})"),
            dict(etape='T2 / T4 log Polygon P13', t=pd.Timestamp(p13[0]['T_DETECT_ns'], unit='ns') if p13 else None, source='nœud publicnode (connexion P13)',
                 detail=f"détection par la chaîne (jeton -> marché par la liste Gamma de P13) : p_before {p13[0].get('p_before')}, hist_n {p13[0].get('hist_n')} -> alerte SIG_HIST_V1 ; la ligne RTDS au marché vide est ignorée par P13 (marché inconnu)" if p13 else ''),
            dict(etape='T6 P12', t=None, source='carnet', detail='non abonné : rien'),
            dict(etape='P14', t=None, source='journal papier', detail='fenêtre ouverte au démarrage de P14 (10:44:38) sur l alerte P13')]
    pd.DataFrame(rows).to_csv(OUT + 'phase15_oklahoma_timeline.csv', index=False)
    return rows


def champs_rtds(D, M):
    R = D['rtds'].merge(M[['asset', 'cid_vrai', 'oi_vrai', 'excl', 'volume', 'slug_vrai', 'createdAt']], on='asset', how='left')
    R['vide'] = R.cid == ''
    R['usd'] = R.price * R['size']
    out = dict(lignes=len(R), part_cid_vide=R.vide.mean(), jetons_toujours_vides=int(R[R.vide].asset.nunique()), jetons_jamais_vides=int(R[~R.vide].asset.nunique()),
               jetons_mixtes=len(set(R[R.vide].asset) & set(R[~R.vide].asset)), marches_vides=int(R[R.vide].cid_vrai.nunique()),
               oi_vides=json.dumps(R[R.vide].oi.value_counts().to_dict()), part_oi_faux_si_vide=float((R[R.vide].oi != R[R.vide].oi_vrai).mean()),
               part_oi_faux_si_non_vide=float((R[~R.vide].oi != R[~R.vide].oi_vrai).mean()), part_cid_faux_si_non_vide=float((R[~R.vide].cid != R[~R.vide].cid_vrai).mean()))
    univ = R[(R.excl == False) & (R.volume >= 1e4)]  # noqa: E712
    tk = univ[univ.fee.notna()]
    out.update(univers_live_lignes_preneur=len(tk), univers_live_part_cid_vide=tk.vide.mean(),
               univers_live_achats_250_part_cid_vide=tk[(tk.usd >= 250) & (tk.side == 'BUY')].vide.mean())
    g = R.groupby('tx').agg(nfee=('fee', lambda s: s.notna().sum()), n=('fee', 'size'))
    out.update(tx=len(g), tx_fee_unique=(g.nfee == 1).mean(), tx_sans_fee=(g.nfee == 0).mean(), tx_fee_multiple=(g.nfee >= 2).mean(), lignes_fee_zero=int((R.fee == 0).sum()))
    top = R[R.vide & (R.excl == False)].drop_duplicates('cid_vrai').sort_values('volume', ascending=False)[['slug_vrai', 'volume', 'createdAt']].head(15)  # noqa: E712
    top.to_csv(OUT + 'phase15_marches_sans_conditionId_top.csv', index=False)
    return R, out


def trous_doublons_horloges(D, R):
    H = D['heads'].sort_values('t_recv')
    Rs = R.sort_values('t_recv')
    g = np.diff(Rs.t_recv.values) / 1e9
    i = np.nonzero(g > 5)[0]
    gaps = pd.DataFrame(dict(source='RTDS collecteur P11', gap_start=pd.to_datetime(Rs.t_recv.values[i], unit='ns'), gap_end=pd.to_datetime(Rs.t_recv.values[i + 1], unit='ns'), duree_s=g[i]))
    gh = np.diff(H.t_recv.values) / 1e9
    ih = np.nonzero(gh > 10)[0]
    gaps = pd.concat([gaps, pd.DataFrame(dict(source='chaîne collecteur P11 (en-têtes)', gap_start=pd.to_datetime(H.t_recv.values[ih], unit='ns'),
                                              gap_end=pd.to_datetime(H.t_recv.values[ih + 1], unit='ns'), duree_s=gh[ih]))])
    for l in jl(B + 'brut_p11/live/listener.log.jsonl'):
        if l.get('event') == 'erreur_ws':
            gaps = pd.concat([gaps, pd.DataFrame([dict(source='RTDS listener P11', gap_start=pd.Timestamp(l['t_ns'] - (30e9 if 'silencieux' in l.get('err', '') else 0), unit='ns'),
                                                      gap_end=pd.Timestamp(l['t_ns'], unit='ns'), duree_s=30.0 if 'silencieux' in l.get('err', '') else 0, cause=l.get('err', '')[:50])])])
    for f, n in (('brut_p13/paper_etat.jsonl', 'P13'), ('brut_p14/paper_etat.jsonl', 'P14')):
        for l in jl(B + f):
            if l.get('event', '').startswith('erreur'):
                gaps = pd.concat([gaps, pd.DataFrame([dict(source=f'{n} {l["event"]}', gap_start=pd.Timestamp(l['t_ns'] - 30e9, unit='ns') if 'silence' in l.get('err', '').lower() else pd.Timestamp(l['t_ns'], unit='ns'),
                                                          gap_end=pd.Timestamp(l['t_ns'], unit='ns'), duree_s=30.0 if 'silence' in l.get('err', '').lower() else None, cause=l.get('err', '')[:50])])])
    gaps['recovered'] = 'non : aucune source ne rejoue RTDS ; la chaîne n est pas rattrapée'
    gaps['periode'] = 'P11 (08:45-11:30)'
    hb = H.drop_duplicates('block').sort_values('block')
    manq = int((np.diff(hb.block.values) - 1).clip(min=0).sum())
    # doublons RTDS : contrôle d un échantillon contre les fills du data-api
    key = ['tx', 'wallet', 'asset', 'side', 'size', 'price']
    Dd = R[R.duplicated(key, keep=False)]
    gr = Dd.groupby(key).agg(n=('t_recv', 'size'), n_ts=('ts', 'nunique'), cid=('cid_vrai', 'first'), ts=('ts', 'min')).reset_index()
    s = gr.sample(min(40, len(gr)), random_state=15)
    chk = []
    for r in s.itertuples():
        rows = get(f'https://data-api.polymarket.com/trades?market={r.cid}&start={r.ts - 3}&end={r.ts + 3}&limit=1000&takerOnly=false') or []
        k = sum(1 for x in rows if x['transactionHash'] == r.tx and x['proxyWallet'].lower() == r.wallet and str(x['asset']) == r.asset and abs(float(x['size']) - r.size) < 1e-6)
        chk.append(dict(periode='P11', source='RTDS collecteur P11', tx=r.tx, wallet=r.wallet, asset=r.asset, lignes=r.n, fills_data_api=k, timestamps=r.n_ts,
                        classe='TRUE_DUPLICATE' if r.n > k else ('TIMESTAMP_ALIAS' if r.n_ts > 1 else 'fills distincts (pas un doublon)')))
    dups = pd.DataFrame(chk)
    dres = dict(groupes_lignes_identiques=len(gr), lignes_en_trop_si_dedoublonnage_naif=int(R.duplicated(key).sum()), echantillon=len(s),
                echantillon_vrais_doublons=int((dups.classe == 'TRUE_DUPLICATE').sum()), meme_trade_deux_timestamps=int((R.groupby(['tx', 'wallet', 'asset']).ts.nunique() > 1).sum()),
                ltp_doublons=int(D['ltp'].duplicated(['tx', 'asset']).sum()), logs_doublons=int(D['chain'].duplicated(['tx', 'logIndex']).sum()), blocs_manquants_chaine=manq,
                blocs_total=int(hb.block.max() - hb.block.min() + 1))
    clk = jl(B + 'brut_p11/meta/clock.jsonl')
    return gaps, dups, dres, clk


def couverture_marches(D, M, R):
    from p11_clob_collector import fetch_active
    act = fetch_active()
    wl = {}
    for fp in sorted(glob.glob(B + 'brut_p11/meta/watchlist_*.json')):
        wl.update(json.load(open(fp))['watchlist'])
    sub = set()
    for x in jl(B + 'brut_p11/meta/subscriptions.jsonl'):
        if str(x.get('conn', '')).startswith('c') and x.get('event') in ('subscribe', 'ajout_dynamique'):
            sub |= set(x.get('markets') or [])
    al = jl(B + 'brut_p11/live/alerts.jsonl') + [a for a in jl(B + 'brut_p13/paper_alerts.jsonl') if a.get('type') == 'SIG_HIST_V1']
    p14m = {a['market'] for a in al}
    mk = M.drop_duplicates('cid_vrai').set_index('cid_vrai')
    g = R.groupby('cid_vrai').agg(trades=('tx', 'nunique'), wallets=('wallet', 'nunique'), nom=('cid', lambda s: (s != '').mean()), first=('t_recv', 'min'), last=('t_recv', 'max'))
    oi_ok = R.assign(ok=R.oi == R.oi_vrai).groupby('cid_vrai').ok.mean()
    lt = D['ltp'].groupby('cid').tx.nunique()
    rows = []
    for c in set(act) | set(R.cid_vrai.dropna()) | sub:
        m = act.get(c) or {}
        slug = m.get('slug') or (mk.slug_vrai.get(c) if c in mk.index else None) or (wl.get(c) or {}).get('slug')
        q = m.get('question') or (mk.question.get(c) if c in mk.index else None) or ''
        vol = float(m.get('volume') or (mk.volume.get(c) if c in mk.index else 0) or 0)
        toks = json.loads(m['clobTokenIds']) if m.get('clobTokenIds') else ((wl.get(c) or {}).get('tokens') or M[M.cid_vrai == c].asset.tolist())
        p8 = not EXCL.search((slug or '') + ' ' + q.lower().replace(' ', '-'))
        rows.append(dict(market_id=c, token_id='|'.join(map(str, toks)), slug=slug, category=category(slug), eligible_phase8=p8 and vol >= 250000, exclu_regles_phase8=not p8,
                         exclu_regles_live=excluded(slug, q), univers_live=c in act, p11_seen=c in sub, p12_seen=c in sub, p13_seen='liste Gamma au démarrage (probable)' if c in act else 'non',
                         p14_seen=c in p14m, clob_seen=c in sub, clob_trades=int(lt.get(c, 0)), trades_seen=int(g.trades.get(c, 0)), wallet_seen=int(g.wallets.get(c, 0)),
                         market_name_resolved=g.nom.get(c) if c in g.index else None, price_valid=oi_ok.get(c) if c in oi_ok.index else None,
                         first_seen=pd.Timestamp(g['first'][c], unit='ns') if c in g.index else None, last_seen=pd.Timestamp(g['last'][c], unit='ns') if c in g.index else None, volume=vol))
    C = pd.DataFrame(rows)
    C.to_csv(OUT + 'phase15_market_coverage.csv', index=False)
    u = C[C.univers_live]
    w = R[(R.fee.notna()) & (R.cid_vrai.isin(set(u.market_id)))]
    res = dict(univers_live=len(u), univers_live_abonnes_carnet=int(u.p11_seen.sum()), part_marches=u.p11_seen.mean(), univers_live_avec_trades=int((u.trades_seen > 0).sum()),
               univers_live_nom_toujours_vide=int((u[u.trades_seen > 0].market_name_resolved == 0).sum()),
               part_volume_preneur_univers_sur_marches_abonnes=float((w[w.cid_vrai.isin(sub)].price * w[w.cid_vrai.isin(sub)]['size']).sum() / (w.price * w['size']).sum()),
               exclusions_phase8_vs_live='EXCL identique ; le direct ajoute GAME (codes d équipes + date) et abaisse le volume à 10 000 $ (phase 8 : 250 000 $ à la clôture)')
    return C, res


def bout_en_bout(D, R):
    L = D['ltp'].copy()
    L['usd'] = L.price * L['size']
    t_list = int(pd.Timestamp('2026-10-01T09:57:01', tz='UTC').value)
    c = L[(L.usd >= 250) & (L.side == 'BUY') & (L.t_recv >= t_list)].drop_duplicates('tx')

    def truth(r):
        t = int(r.ts_ms / 1000)
        rows = get(f'https://data-api.polymarket.com/trades?market={r.cid}&start={t - 5}&end={t + 8}&limit=1000&takerOnly=true') or []
        m = [x for x in rows if x['transactionHash'] == r.tx]
        if not m:
            return dict(tx=r.tx, trouve_api=False)
        x = m[0]
        w, ts = x['proxyWallet'].lower(), int(x['timestamp'])
        prev = get(f'https://data-api.polymarket.com/trades?user={w}&market={r.cid}&start={ts - 86400}&end={ts}&limit=50&takerOnly=true') or []
        prev = [p for p in prev if p['transactionHash'] != r.tx and float(p['price']) * float(p['size']) >= 100 and int(p['timestamp']) <= ts]
        usd = float(x['price']) * float(x['size'])
        return dict(tx=r.tx, trouve_api=True, wallet=w, T_trade_bloc=ts, prix_api=float(x['price']), side_api=x['side'], usd_api=usd,
                    fae_definition=(x['side'] == 'BUY' and usd >= 250 and len(prev) == 0))
    with cf.ThreadPoolExecutor(6) as ex:
        T = pd.DataFrame(list(ex.map(truth, c.itertuples())))
    E = c.merge(T, on='tx')
    anyr = R.sort_values('t_recv').drop_duplicates('tx').set_index('tx')
    nfee = R.groupby('tx').fee.apply(lambda s: s.notna().sum())
    C = D['chain'].sort_values('t_recv').drop_duplicates('tx').set_index('tx')
    F = pd.DataFrame(jl(B + 'brut_p11/live/fae_events.jsonl')).drop_duplicates('tx').set_index('tx')
    S = pd.DataFrame(jl(B + 'brut_p12/live_signals.jsonl'))
    al11 = {a['tx'] for a in jl(B + 'brut_p11/live/alerts.jsonl')}
    al13 = {a['tx'] for a in jl(B + 'brut_p13/paper_alerts.jsonl')}
    E = E.assign(T_clob_ltp_echange=pd.to_datetime(E.ts_ms, unit='ms'), T_clob_reception=pd.to_datetime(E.t_recv, unit='ns'),
                 T_rtds_reception=[pd.Timestamp(anyr.t_recv[t], unit='ns') if t in anyr.index else None for t in E.tx],
                 rtds_statut_preneur=[('fee' if nfee.get(t) == 1 else 'ambigu') if t in anyr.index else 'absent' for t in E.tx],
                 rtds_conditionId_vide=[anyr.cid.get(t) == '' if t in anyr.index else None for t in E.tx],
                 T_rpc_reception=[pd.Timestamp(C.t_recv[t], unit='ns') if t in C.index else None for t in E.tx],
                 p11_listener_FAE=E.tx.isin(F.index), p11_listener_T_obs=[pd.Timestamp(F.T_obs_ns[t], unit='ns') if t in F.index else None for t in E.tx],
                 p11_listener_wallet=[F.wallet.get(t) for t in E.tx], p11_listener_marche_vide=[F.market.get(t) == '' if t in F.index else None for t in E.tx],
                 p12_signal_jeton_60s=[bool(((S.token == a) & ((S.t_local_ns - t).abs() <= 60e9)).any()) if len(S) else False for a, t in zip(E.asset, E.t_recv)],
                 p11_alerte=E.tx.isin(al11), p13_alerte=E.tx.isin(al13), p14='fenêtres seulement après une alerte : non applicable')
    E['p11_listener_bon_wallet'] = E.p11_listener_wallet == E.wallet
    E['periode'] = 'P11 (09:57-11:30)'
    cols = ['periode', 'tx', 'cid', 'asset', 'wallet', 'usd_api', 'T_trade_bloc', 'T_clob_ltp_echange', 'T_clob_reception', 'T_rtds_reception', 'rtds_statut_preneur',
            'rtds_conditionId_vide', 'T_rpc_reception', 'fae_definition', 'p11_listener_FAE', 'p11_listener_bon_wallet', 'p11_listener_marche_vide', 'p11_listener_T_obs',
            'p12_signal_jeton_60s', 'p11_alerte', 'p13_alerte', 'p14']
    E[cols].to_csv(OUT + 'phase15_end_to_end_p11.csv', index=False)
    f = E[E.fae_definition]
    return dict(trades=len(E), fae_definition=len(f), fae_bon_wallet=int((f.p11_listener_FAE & f.p11_listener_bon_wallet).sum()),
                fae_mauvais_wallet=int((f.p11_listener_FAE & ~f.p11_listener_bon_wallet).sum()), fae_non_logges=int((~f.p11_listener_FAE).sum()),
                fae_non_logges_ambigus=int((~f.p11_listener_FAE & (f.rtds_statut_preneur == 'ambigu')).sum()), fae_hors_definition=int((~E.fae_definition & E.p11_listener_FAE).sum()),
                part_ambigus=float((E.rtds_statut_preneur == 'ambigu').mean()), part_rtds_vu=float((E.rtds_statut_preneur != 'absent').mean()))


def alertes_live():
    v = jl(B + 'brut_p11/live/verifications.jsonl')
    out = []
    for a in jl(B + 'brut_p11/live/alerts.jsonl'):
        vv = [x for x in v if x['alert_id'] == a['alert_id']]
        out.append(dict(source='P11 listener', alert_id=a['alert_id'], wallet=a['wallet'], market=a['market'] or '(vide)', slug=a.get('slug'), preneur=a['preneur'],
                        p_before=a['p_before'], preneur_confirme_data_api=any(x.get('preneur_confirme') for x in vv)))
    for a in jl(B + 'brut_p13/paper_alerts.jsonl'):
        out.append(dict(source='P13 paper', alert_id=a['alert_id'], wallet=a['wallet'], market=a['market'], preneur=a['source_detection'], p_before=a.get('p_before')))
    A = pd.DataFrame(out)
    # vérité : preneur et p_before recalculés au data-api (dernier trade preneur >= 100 $ du marché avant le trade)
    res = []
    for r in A.itertuples():
        a = [x for x in jl(B + ('brut_p11/live/alerts.jsonl' if r.source.startswith('P11') else 'brut_p13/paper_alerts.jsonl')) if x['alert_id'] == r.alert_id][0]
        tx = a['tx']
        t = a.get('ts_echange') or int(a['T_DETECT_ns'] / 1e9)
        # le marché vrai depuis le jeton
        asset = str(a.get('asset') or a.get('token'))
        g = (get(f'https://gamma-api.polymarket.com/markets?clob_token_ids={asset}') or get(f'https://gamma-api.polymarket.com/markets?closed=true&clob_token_ids={asset}') or [{}])[0]
        cid = g.get('conditionId')
        oi = json.loads(g.get('clobTokenIds', '[]')).index(asset) if g.get('clobTokenIds') else None
        rows = get(f'https://data-api.polymarket.com/trades?market={cid}&start={t - 86400 * 3}&end={t + 10}&limit=10000&takerOnly=true') or []
        me = [x for x in rows if x['transactionHash'] == tx]
        taker = me[0]['proxyWallet'].lower() if me else None
        tts = int(me[0]['timestamp']) if me else None
        # le data-api renvoie l ordre exact d exécution, du plus récent au plus ancien (phase 10) : les trades antérieurs suivent la ligne du trade
        k = next((i for i, x in enumerate(rows) if x['transactionHash'] == tx), None)
        before = [x for x in (rows[k + 1:] if k is not None else []) if float(x['price']) * float(x['size']) >= 100 and x['transactionHash'] != tx]
        pb = None
        if before:
            p = float(before[0]['price'])
            p_yes = p if int(before[0]['outcomeIndex']) == 0 else 1 - p
            pb = p_yes if oi == 0 else 1 - p_yes
        res.append(dict(marche_vrai=g.get('slug'), outcome_vrai=oi, preneur_data_api=taker, wallet_est_le_preneur=taker == r.wallet, p_before_verite=pb))
    A = pd.concat([A, pd.DataFrame(res)], axis=1)
    A['p_before_ecart'] = A.p_before - A.p_before_verite
    A.to_csv(OUT + 'phase15_alertes_live_audit.csv', index=False)
    return A


def watchlist_et_comptes(D, R):
    C = D['chain'].copy()
    C['maker'] = '0x' + C.topics.str[2].str[-40:]
    C['preneur'] = C.topics.str[3].str[-40:].isin(['e111180000d2663c0091e4f400237545b87b996b', 'e2222d279d744050d28e00520010520000310f59'])
    F = pd.DataFrame(jl(B + 'brut_p11/live/fae_events.jsonl'))
    elig = set(json.load(open(B + 'brut_p11/live/wallets_eligibles_au_demarrage.json')))
    EV = pd.read_pickle(os.path.join(DATA, 'p9', 'events_final.pkl'))      # pickle local (phase 9)
    hist = set(EV[EV.SIG_HIST].wallet)
    WL = pd.read_csv(ROOT + '/phase13/wallet_watchlist.csv')
    cls = dict(zip(WL.wallet, WL.classe))
    al = jl(B + 'brut_p11/live/alerts.jsonl') + [a for a in jl(B + 'brut_p13/paper_alerts.jsonl') if a.get('type') == 'SIG_HIST_V1']
    p14w = {a['wallet'] for a in al}
    out = []
    for w in sorted(elig | hist | p14w | set(A8)):
        rr, cc = R[R.wallet == w], C[C.maker == w]
        out.append(dict(wallet=w, present_p11_listener=w in elig, present_p11_chaine_collecteur=w in (elig | hist), present_p12=False, present_p13=w in elig, present_p14=w in p14w,
                        watchlist_reason=cls.get(w, 'compte de l enquête' if w in A8 else ('alerte live' if w in p14w else 'SIG historique')),
                        first_seen=pd.Timestamp(rr.t_recv.min(), unit='ns') if len(rr) else None, last_seen=pd.Timestamp(rr.t_recv.max(), unit='ns') if len(rr) else None,
                        trade_count=int(rr.tx.nunique()), trade_count_preneur_rtds=int(rr[rr.fee.notna()].tx.nunique()), trade_count_chaine=int(cc.tx.nunique()),
                        trade_count_preneur_chaine=int(cc[cc.preneur].tx.nunique()), fae_listener=int((F.wallet == w).sum())))
    W = pd.DataFrame(out)
    W.to_csv(OUT + 'phase15_watchlist_audit.csv', index=False)
    t0, t1 = int(T0 / 1e9), int(T1 / 1e9)
    comptes = []
    for w, name in A8.items():
        api = get(f'https://data-api.polymarket.com/trades?user={w}&start={t0}&end={t1}&limit=500&takerOnly=false') or []
        last = get(f'https://data-api.polymarket.com/trades?user={w}&limit=1&takerOnly=false') or []
        comptes.append(dict(compte=name, wallet=w, dernier_trade=pd.Timestamp(int(last[0]['timestamp']), unit='s') if last else None, trades_data_api_periode=len(api),
                            vus_p11_rtds=int((R.wallet == w).sum()), vus_p11_chaine=int((C.maker == w).sum()), dans_filtre_chaine_p11=w in (elig | hist), fae_listener=int((F.wallet == w).sum()),
                            vus_p12='non (P12 sans wallet)', dans_watchlist_p13=w in elig, fenetre_p14=w in p14w, erreurs_mapping=0))
    pd.DataFrame(comptes).to_csv(OUT + 'phase15_comptes8.csv', index=False)
    return W, pd.DataFrame(comptes)


def regression():
    rows = []
    for n in ('EVT_MADURO', 'EVT_IRAN'):
        import gzip
        x = json.load(gzip.open(os.path.join(DATA, 'p10', 'raw', f'{n}.json.gz'), 'rt'))
        T = pd.read_pickle(os.path.join(DATA, 'p10', 'tapes', f'{n}.pkl'))       # pickle local (phase 10)

        def fw(a, b):
            r = get(f'https://data-api.polymarket.com/trades?market={x["cid"]}&start={a}&end={b}&limit=10000&takerOnly=true')
            if r is not None and len(r) >= 10000 and b - a > 2:
                m = (a + b) // 2
                return fw(a, m) + fw(m + 1, b)
            return r or []
        N = pd.DataFrame(fw(x['a'], x['b']))
        N['wallet'] = N.proxyWallet.str.lower()
        old = T[['tx', 'wallet', 'side', 'oi', 'price', 'size', 'ts']]
        ko, kn = set(zip(old.tx, old.wallet)), set(zip(N.transactionHash, N.wallet))
        m = N.merge(old, left_on=['transactionHash', 'wallet'], right_on=['tx', 'wallet'], suffixes=('_n', '_o')).drop_duplicates(['transactionHash', 'wallet'])
        g = (get(f'https://gamma-api.polymarket.com/markets?closed=true&condition_ids={x["cid"]}') or [{}])[0]
        mp = {str(t): i for i, t in enumerate(json.loads(g.get('clobTokenIds', '[]')))}
        random.seed(15)
        d = []
        for h in random.sample(list(N.transactionHash.unique()), 15):
            rc = rpc('eth_getTransactionReceipt', [h])
            b = rpc('eth_getBlockByNumber', [rc['blockNumber'], False]) if rc else None
            d.append(int(N[N.transactionHash == h].timestamp.iloc[0]) - int(b['timestamp'], 16) if b else None)
        rows.append(dict(fenetre=n, cid=x['cid'], debut=pd.Timestamp(x['a'], unit='s'), fin=pd.Timestamp(x['b'], unit='s'), preneurs_phase10=len(old), preneurs_aujourdhui=len(N),
                         communs=len(ko & kn), seulement_phase10=len(ko - kn), seulement_aujourdhui=len(kn - ko), ts_identique=float((m.timestamp == m.ts).mean()),
                         prix_identique=float(((m.price_n.astype(float) - m.price_o).abs() < 1e-9).mean()), cote_identique=float((m.side_n == m.side_o).mean()),
                         outcome_identique=float((m.outcomeIndex == m.oi).mean()), taille_identique=float(((m.size_n.astype(float) - m.size_o).abs() < 1e-6).mean()),
                         slug_gamma=g.get('slug'), outcomes=g.get('outcomes'), outcome_vs_gamma=float((N.asset.astype(str).map(mp) == N.outcomeIndex).mean()),
                         ts_data_api_moins_bloc=json.dumps(pd.Series(d).value_counts(dropna=False).to_dict())))
    R = pd.DataFrame(rows)
    R.to_csv(OUT + 'phase15_regression_maduro_iran.csv', index=False)
    return R


def sig_hist_replay(taux):
    """Alertes historiques (phase 9, inchangées) : visibles en direct avec les défauts mesurés ? Probabilités appliquées, pas recalcul de SIG_HIST."""
    W = pd.read_pickle(os.path.join(DATA, 'p10', 'windows.pkl'))                # pickle local (phase 10)
    S = W[W.groupe == 'SIG_HIST'].copy()
    U = {m['conditionId']: m for m in json.load(open(os.path.join(DATA, 'p8', 'universe.json')))}
    FE = pd.read_pickle(os.path.join(DATA, 'p10', 'fees.pkl')).drop_duplicates('tx').set_index('tx')   # pickle local (phase 10)
    S['slug'] = S.cid.map(lambda c: (U.get(c) or {}).get('slug'))
    S['exclu_en_direct'] = [excluded(s, (U.get(c) or {}).get('question')) for s, c in zip(S.slug, S.cid)]
    S['frais_payes'] = S.tx.map(lambda t: FE.fee_raw.get(t) if t in FE.index else np.nan)
    S['preneur_marque_par_fee'] = S.frais_payes > 0
    p_deliv, p_cid = taux['rappel_rtds_une_connexion'], 1 - taux['part_cid_vide_univers_achats_250']
    S['P11_seen'] = np.where(S.exclu_en_direct, 0.0, p_deliv)
    S['P11_alerte_bien_calculee'] = S.P11_seen * p_cid
    S['wallet_identified'] = np.where(S.preneur_marque_par_fee, 'oui (ligne fee)', 'oui si éligible et achat >= 250 $ (règle ambiguë : d autres makers éligibles aussi)')
    S['P12_seen'] = taux['part_volume_marches_abonnes']
    S['P13_seen'] = 'chaîne (wallet dans la liste au démarrage, nœud disponible) ou RTDS avec marché non vide'
    S['timestamp_error'] = 'ts RTDS = ts bloc - 1 s (mode), 0 à -2 s'
    S['price_error'] = np.where(S.preneur_marque_par_fee, 'aucune (ligne preneur)', 'aucune si la ligne retenue est celle du wallet')
    cols = ['eid9', 'split', 'tx', 'wallet', 'cid', 'slug', 'ts', 'usd', 'exclu_en_direct', 'frais_payes', 'preneur_marque_par_fee', 'P11_seen', 'P11_alerte_bien_calculee',
            'wallet_identified', 'P12_seen', 'P13_seen', 'timestamp_error', 'price_error']
    S[cols].rename(columns={'tx': 'historical_trade'}).to_csv(OUT + 'phase15_sig_hist_replay.csv', index=False)
    return dict(alertes=len(S), exclues_en_direct=int(S.exclu_en_direct.sum()), part_preneur_marque_par_fee=float(S.preneur_marque_par_fee.mean()),
                par_split_fee=S.groupby('split').preneur_marque_par_fee.mean().round(3).to_dict(), attendues_vues=float(S.P11_seen.sum()),
                attendues_bien_calculees=float(S.P11_alerte_bien_calculee.sum()), taux=taux)


def chiens_de_garde():
    now = time.time_ns()

    def last_raw(kind):
        fs = sorted(glob.glob(B + f'brut_p11/{kind}/*/*.jsonl.zst'), key=os.path.getmtime)
        t = None
        for x in _read(fs[-1]):
            t = x[0]
        return t

    def last(fp, key='t_ns'):
        t = None
        for x in jl(fp):
            t = x.get(key) or t
        return t
    alive = {n: bool(subprocess.run(['pgrep', '-f', f'Python {n}'], capture_output=True).stdout) for n in
             ['p11_clob_collector.py', 'p11_signal_listener.py', 'p12_live.py', 'p13_paper.py', 'p14_paper.py']}
    age = lambda t: None if t is None else round((now - t) / 1e9, 1)  # noqa: E731
    sil = lambda f, cond: sum(1 for x in jl(f) if cond(x))  # noqa: E731
    rows = [dict(processus='P11 collecteur RTDS', process_alive=alive['p11_clob_collector.py'], last_event_age_s=age(last_raw('rtds')), battement_avec_compteur='oui (etat.jsonl)',
                 chien_de_garde='silence 30 s', silences_observes=sil(B + 'brut_p11/meta/subscriptions.jsonl', lambda x: x.get('conn') == 'rtds' and 'silencieux' in str(x.get('err'))),
                 automatic_restart='p11_run.sh', restart_latency_s='1 à 2 (reconnexion)', vivant_mais_aveugle='oui : 30 s de silence avant détection, sans rattrapage'),
            dict(processus='P11 collecteur carnet', process_alive=alive['p11_clob_collector.py'], last_event_age_s=age(last_raw('ws_market')), battement_avec_compteur='oui',
                 chien_de_garde='silence 120 s', automatic_restart='p11_run.sh', restart_latency_s='1 à 60 (backoff)', vivant_mais_aveugle='possible 120 s ; REST toutes les 10 min'),
            dict(processus='P11 collecteur chaîne', process_alive=alive['p11_clob_collector.py'], last_event_age_s=age(last_raw('chain')), battement_avec_compteur='oui',
                 chien_de_garde='aucun bloc 60 s', silences_observes=sil(B + 'brut_p11/meta/subscriptions.jsonl', lambda x: x.get('conn') == 'chain' and 'aucun bloc' in str(x.get('err'))),
                 automatic_restart='p11_run.sh', vivant_mais_aveugle='oui : nœud en retard (en-têtes jusqu à 250 s de retard) et blocs manquants non rattrapés'),
            dict(processus='P11 listener', process_alive=alive['p11_signal_listener.py'], last_event_age_s=age(last(B + 'brut_p11/live/listener.log.jsonl')),
                 battement_avec_compteur='oui toutes les 10 min (preneurs par statut)', chien_de_garde='silence RTDS 30 s',
                 silences_observes=sil(B + 'brut_p11/live/listener.log.jsonl', lambda x: x.get('event') == 'erreur_ws'), automatic_restart='p11_run.sh',
                 vivant_mais_aveugle='oui (30 s) ; et aveugle aux marchés sans conditionId même quand le flux est vivant'),
            dict(processus='P12 live', process_alive=alive['p12_live.py'], last_event_age_s=age(last(B + 'brut_p12/live_signals.jsonl', 't_local_ns')),
                 battement_avec_compteur='non (signaux seulement)', chien_de_garde='silence carnet 120 s', automatic_restart='p12_run.sh ; relance horaire',
                 vivant_mais_aveugle='indétectable dans ses journaux'),
            dict(processus='P13 paper', process_alive=alive['p13_paper.py'], last_event_age_s=age(last(B + 'brut_p13/paper_etat.jsonl')), battement_avec_compteur='non',
                 chien_de_garde='RTDS 30 s ; chaîne 600 s', silences_observes=sil(B + 'brut_p13/paper_etat.jsonl', lambda x: x.get('event') == 'erreur_rtds'),
                 automatic_restart='p13_run.sh', vivant_mais_aveugle='indétectable : aucun compteur ; chaîne aveugle jusqu à 10 min'),
            dict(processus='P14 paper', process_alive=alive['p14_paper.py'], last_event_age_s=age(last(B + 'brut_p14/paper_etat.jsonl')),
                 battement_avec_compteur='oui toutes les 5 min (fenêtres) mais sans compteur de messages', chien_de_garde='RTDS 30 s ; chaîne : aucun',
                 silences_observes=sil(B + 'brut_p14/paper_etat.jsonl', lambda x: x.get('event') == 'erreur_rtds'), automatic_restart='p14_run.sh',
                 vivant_mais_aveugle='oui pour la chaîne (aucune détection de blocage)')]
    D = pd.DataFrame(rows)
    D.to_csv(OUT + 'phase15_watchdog.csv', index=False)
    return D


def couverture_trades_p11(D, R, M):
    """Vérité data-api (preneurs, complet) sur un échantillon de 70 marchés + Oklahoma, 09:00-11:25 : RTDS du collecteur et carnet."""
    random.seed(15)
    sub = set()
    for x in jl(B + 'brut_p11/meta/subscriptions.jsonl'):
        if str(x.get('conn', '')).startswith('c') and x.get('event') in ('subscribe', 'ajout_dynamique'):
            sub |= set(x.get('markets') or [])
    univ = R[(R.excl == False) & (R.volume >= 1e4)]  # noqa: E712
    mk = univ.groupby('cid_vrai').agg(vide=('cid', lambda s: (s == '').mean())).reset_index()
    pv = mk[mk.vide > 0].cid_vrai.tolist(); pn = mk[(mk.vide == 0) & (~mk.cid_vrai.isin(sub))].cid_vrai.tolist(); pw = [c for c in mk.cid_vrai if c in sub]
    S = list(dict.fromkeys(random.sample(pv, min(20, len(pv))) + random.sample(pn, min(25, len(pn))) + random.sample(pw, min(25, len(pw))) + [OKLA]))
    a, b = int(pd.Timestamp('2026-10-01T09:00', tz='UTC').timestamp()), int(pd.Timestamp('2026-10-01T11:25', tz='UTC').timestamp())
    with cf.ThreadPoolExecutor(6) as ex:
        res = list(ex.map(lambda c: (c, get(f'https://data-api.polymarket.com/trades?market={c}&start={a}&end={b}&limit=10000&takerOnly=true') or []), S))
    T = pd.DataFrame([dict(cid=c, tx=x['transactionHash'], wallet=x['proxyWallet'].lower(), asset=str(x['asset']), side=x['side'], oi=x['outcomeIndex'], price=float(x['price']),
                           size=float(x['size']), ts=int(x['timestamp'])) for c, t in res for x in t])
    T['groupe'] = ['marché sans conditionId RTDS' if c in pv else ('marché abonné au carnet' if c in sub else 'univers non abonné') for c in T.cid]
    R2 = R.copy(); R2['fee_row'] = R2.fee.notna()
    first = R2.sort_values(['tx', 'fee_row', 't_recv'], ascending=[True, False, True]).drop_duplicates('tx')
    nf = R2.groupby('tx').fee_row.sum().rename('n_fee')
    X = T.merge(first[['tx', 'wallet', 'side', 'oi', 'price', 'size', 'cid', 'ts', 't_recv']], on='tx', how='left', suffixes=('', '_r')).merge(nf, on='tx', how='left')
    L = D['ltp'].drop_duplicates('tx').set_index('tx')
    X['rtds_vu'] = X.wallet_r.notna(); X['ltp_vu'] = X.tx.isin(L.index)
    X['statut'] = np.where(X.n_fee == 1, 'fee unique', np.where(X.n_fee.isna(), 'absent', 'ambigu (0 ou 2+ fee)'))
    rows = []
    for (g, st), x in X.groupby(['groupe', 'statut']):
        v = x[x.rtds_vu]
        rows.append(dict(periode='P11 (09:00-11:25)', source='RTDS collecteur P11', groupe=g, valeur=st, verite_tx=len(x), observes=int(x.rtds_vu.sum()),
                         wallet_ok=float((v.wallet == v.wallet_r).mean()) if len(v) else None, prix_ok=float(((v.price - v.price_r).abs() < 1e-6).mean()) if len(v) else None,
                         side_ok=float((v.side == v.side_r).mean()) if len(v) else None, outcome_ok=float((v.oi == v.oi_r).mean()) if len(v) else None))
    for g, x in X.groupby('groupe'):
        rows.append(dict(periode='P11 (09:00-11:25)', source='RTDS collecteur P11', groupe=g, valeur='tous', verite_tx=len(x), observes=int(x.rtds_vu.sum()), rappel=float(x.rtds_vu.mean())))
        if g == 'marché abonné au carnet':
            rows.append(dict(periode='P11 (09:00-11:25)', source='carnet P11 last_trade_price', groupe=g, valeur='tous', verite_tx=len(x), observes=int(x.ltp_vu.sum()), rappel=float(x.ltp_vu.mean()),
                             note='abonnement au marché à un moment de la période, pas forcément à l heure du trade'))
    X['ecart_ts_rtds_moins_data_api_s'] = X.ts_r - X.ts
    X.to_csv(OUT + 'phase15_trade_coverage_p11_detail.csv', index=False)
    pd.DataFrame(rows).to_csv(OUT + 'phase15_trade_coverage_p11.csv', index=False)
    lat = []
    def add(nom, x, nature):
        x = pd.Series(x, dtype=float).dropna()
        if len(x):
            lat.append(dict(periode='P11', paire=nom, n=len(x), P1=x.quantile(.01), P10=x.quantile(.1), P50=x.median(), P90=x.quantile(.9), P99=x.quantile(.99), max=x.max(), nature=nature))
    add('ts RTDS - ts data-api (s)', X.ts_r - X.ts, 'deux horodatages source ; le data-api donne l horodatage de bloc (régression : 30/30)')
    add('réception RTDS - ts data-api (s)', X.t_recv / 1e9 - X.ts, 'réception locale contre horodatage de bloc')
    Lj = D['ltp'].drop_duplicates('tx').merge(T[['tx', 'ts']], on='tx')
    add('heure d échange ltp - ts data-api (ms)', Lj.ts_ms - Lj.ts * 1000, 'heure d échange (ms) contre bloc (s)')
    J = D['ltp'].merge(R[R.fee.notna()].drop_duplicates('tx')[['tx', 'ts', 't_recv']], on='tx', suffixes=('_l', '_r'))
    add('ts RTDS - heure d échange ltp (ms)', J.ts * 1000 - J.ts_ms, 'secondes contre millisecondes')
    add('réception RTDS - réception ltp (ms)', (J.t_recv_r - J.t_recv_l) / 1e6, 'même horloge locale')
    add('réception ltp - heure d échange (ms)', D['ltp'].t_recv / 1e6 - D['ltp'].ts_ms, 'réception locale contre heure d échange')
    H = D['heads'].drop_duplicates('block')
    add('réception en-tête - ts bloc (s), nœud du collecteur', H.t_recv / 1e9 - H.block_ts, 'réception locale contre horodatage de bloc ; P90 élevé = nœud en retard')
    clk = jl(B + 'brut_p11/meta/clock.jsonl')
    import re
    offs = [v for v in (float(m.group(0)) for c in clk for m in [re.search(r'[+-]\d+\.\d+', str(c.get('sntp', '')))] if m) if abs(v) < 10]
    add('décalage SNTP de l horloge du Mac (s)', offs, 'time.apple.com, ± 0,05 s')
    pd.DataFrame(lat).to_csv(OUT + 'phase15_latency_p11.csv', index=False)
    return dict(marches=len(S), trades=len(T), rappel=X.groupby('groupe').rtds_vu.mean().round(4).to_dict())


def main():
    D = charger()
    M = mapper(D['rtds'].asset.unique().tolist())
    res = {}
    res['oklahoma'] = oklahoma(D, M)
    R, res['champs_rtds'] = champs_rtds(D, M)
    gaps, dups, res['doublons'], res['horloge'] = trous_doublons_horloges(D, R)
    gaps.to_csv(OUT + 'phase15_trous_p11.csv', index=False)
    dups.to_csv(OUT + 'phase15_duplicates_p11.csv', index=False)
    C, res['couverture_marches'] = couverture_marches(D, M, R)
    res['bout_en_bout'] = bout_en_bout(D, R)
    res['couverture_trades_p11'] = couverture_trades_p11(D, R, M)
    res['alertes_live'] = alertes_live().to_dict('records')
    W, A8d = watchlist_et_comptes(D, R)
    res['comptes8'] = A8d.to_dict('records')
    res['regression'] = regression().to_dict('records')
    res['chiens_de_garde'] = chiens_de_garde().to_dict('records')
    json.dump(res, open(OUT + 'phase15_historique_resume.json', 'w'), indent=1, default=str, ensure_ascii=False)
    print(json.dumps({k: v for k, v in res.items() if k in ('champs_rtds', 'doublons', 'couverture_marches', 'bout_en_bout')}, indent=1, default=str, ensure_ascii=False))
    print(pd.DataFrame(res['alertes_live']).to_string())


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--sig-hist':
        taux = json.load(open(OUT + 'phase15_taux_mesures.json'))
        print(json.dumps(sig_hist_replay(taux), indent=1, default=str, ensure_ascii=False))
    else:
        main()
