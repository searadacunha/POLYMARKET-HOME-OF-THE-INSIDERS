#!/usr/bin/env python3
"""Phase 14 : journal papier des 2e achats en direct (PROTOCOLE_P14 §12). PAPER ONLY : aucun ordre, aucune transaction.
Processus séparé ; ne touche à aucun processus des phases 11 à 13, dont il lit seulement les journaux d'alertes :
  donnees/brut_p11/live/alerts.jsonl (listener SIG_HIST V1) et donnees/brut_p13/paper_alerts.jsonl (type SIG_HIST_V1).
Pour chaque alerte (T1), pendant W = 3 600 s (phase13/frozen_p13.json) : même wallet, même jeton, premier achat preneur >= 100 $ (T2),
identifié par RTDS ou par les logs Polygon filtrés sur ce wallet (le premier arrivé compte).
À la détection : carnet REST, entrées papier 50 à 1 000 $ sur les asks ; sorties papier sur les bids à +1, +5, +10, +30, +60, +120, +300 s.
Sorties : phase14/paper_second_buy.csv (une ligne par 2e achat, écrite à +300 s) ;
          donnees/brut_p14/paper_second_buy.jsonl, paper_fenetres.jsonl (toutes les fenêtres, avec ou sans 2e achat), paper_etat.jsonl"""
import asyncio, json, os, sys, time, csv, threading, urllib.request, concurrent.futures as cf
import websockets

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p11_execution import fee_per_share, market_meta  # noqa: E402  (lecture seule)

ROOT = os.path.expanduser('~/Documents/Crypto/enquete_maduro_iran')
RAW14 = os.path.join(ROOT, 'donnees', 'brut_p14')
OUT = os.path.join(ROOT, 'phase14')
SRC = [(os.path.join(ROOT, 'donnees', 'brut_p11', 'live', 'alerts.jsonl'), 'p11'), (os.path.join(ROOT, 'donnees', 'brut_p13', 'paper_alerts.jsonl'), 'p13')]
W = json.load(open(os.path.join(ROOT, 'phase13', 'frozen_p13.json')))['W_second']
TOPIC = '0xd543adfd945773f1a62f74f0ee55a5e3b9b1a28262980ba90b1a89f2ea84d8ee'
EX = ['0xe111180000d2663c0091e4f400237545b87b996b', '0xe2222d279d744050d28e00520010520000310f59']
SIZES = [50, 100, 250, 500, 1000]
HS = [1, 5, 10, 30, 60, 120, 300]
CSV = os.path.join(OUT, 'paper_second_buy.csv')
COLS = (['timestamp', 'alert_id', 'source_alerte', 'wallet', 'token', 'market', 'T1', 'T2', 'tx1', 'tx2', 'source_detection', 'detection_latency', 'second_buy_usd',
         'second_buy_price', 'best_bid_at_detection', 'best_ask_at_detection'] + [f'simulated_entry_${s}' for s in SIZES] + [f'statut_${s}' for s in SIZES]
        + [f'exit_{h}s' for h in HS] + ['exit_note', 'paper_only'])
os.makedirs(RAW14, exist_ok=True)
LOCK = threading.Lock()


def jlog(name, obj):
    with LOCK, open(os.path.join(RAW14, name), 'a') as f:
        f.write(json.dumps(obj, ensure_ascii=False, default=str) + '\n')


def books(token):
    try:
        req = urllib.request.Request('https://clob.polymarket.com/books', data=json.dumps([{'token_id': token}]).encode(),
                                     headers={'User-Agent': 'curl/8.4.0', 'Content-Type': 'application/json'})
        for b in json.loads(urllib.request.urlopen(req, timeout=5).read()):
            if b.get('asset_id') == token:
                return b
    except Exception:
        return None


def walk(levels, dollars=None, shares=None):
    need = dollars if dollars is not None else shares
    sh = val = 0.0
    for p, s in levels:
        if need <= 1e-9:
            break
        if dollars is not None:
            take = min(need, p * s); sh += take / p; val += take; need -= take
        else:
            q = min(need, s); sh += q; val += q * p; need -= q
    return sh, val, max(need, 0.0)


class Logger:
    def __init__(self):
        self.active = {}        # (wallet, token) -> alerte
        self.seen_alerts = set()
        self.done_tx = set()
        self.closed = set()
        self.pos = {fp: 0 for fp, _ in SRC}
        self.rt = {}            # tx -> [t_premier_ns, lignes]
        self.pool = cf.ThreadPoolExecutor(20)
        self.chain_set = frozenset()
        self.meta_cache = {}
        self.found_alerts = set()
        for name in ('paper_second_buy.jsonl', 'paper_fenetres.jsonl'):
            fp = os.path.join(RAW14, name)
            if os.path.exists(fp):
                for l in open(fp):
                    x = json.loads(l)
                    if name == 'paper_second_buy.jsonl':
                        self.done_tx.add(x.get('tx2')); self.found_alerts.add(x.get('alert_id'))
                    else:
                        self.closed.add(x.get('alert_id'))

    # ------------------------------------------------ alertes (T1)
    def read_alerts(self):
        now = time.time()
        for fp, src in SRC:
            if not os.path.exists(fp):
                continue
            with open(fp) as f:
                f.seek(self.pos[fp])
                for l in f:
                    try:
                        a = json.loads(l)
                    except Exception:
                        continue
                    if src == 'p13' and a.get('type') != 'SIG_HIST_V1':
                        continue
                    tx1 = a.get('tx')
                    if not tx1 or tx1 in self.seen_alerts:
                        continue
                    self.seen_alerts.add(tx1)
                    t1 = int(a['ts_echange']) if src == 'p11' else int(a['T_DETECT_ns'] / 1e9) - 2
                    token = str(a.get('asset') or a.get('token'))
                    aid = a['alert_id']
                    if aid in self.closed or t1 + W < now:
                        continue
                    k = (a['wallet'].lower(), token)
                    if k not in self.active:
                        self.active[k] = dict(alert_id=aid, source_alerte=src, wallet=k[0], token=token, market=a['market'], T1=t1, tx1=tx1,
                                              found=aid in self.found_alerts)
                        jlog('paper_etat.jsonl', dict(t_ns=time.time_ns(), event='fenetre_ouverte', alert_id=aid, wallet=k[0][:10], T1=t1))
                self.pos[fp] = f.tell()
        for k, a in list(self.active.items()):
            if a['T1'] + W < now:
                self.active.pop(k)
                if a['alert_id'] not in self.closed:
                    self.closed.add(a['alert_id'])
                    jlog('paper_fenetres.jsonl', dict(alert_id=a['alert_id'], source_alerte=a['source_alerte'], wallet=a['wallet'], token=a['token'],
                                                      market=a['market'], T1=a['T1'], second_achat=a['found'], paper_only=True))

    # ------------------------------------------------ détection du 2e achat
    def candidate(self, wallet, token, side, usd, price, tx, t_ns, source, trade_ts=None):
        a = self.active.get((wallet, token))
        if a is None or a['found'] or side != 'BUY' or usd < 100 or tx == a['tx1'] or tx in self.done_tx:
            return
        if trade_ts is not None and trade_ts <= a['T1']:
            return
        a['found'] = True
        self.done_tx.add(tx)
        rec = dict(a, tx2=tx, source_detection=source, T_DETECT_ns=t_ns, T2_rtds=trade_ts, second_buy_usd=usd, second_buy_price=price, paper_only=True)
        self.pool.submit(self.paper, rec)

    def paper(self, rec):
        t_book0 = time.time_ns()
        b = books(rec['token'])
        rec['T_book_ns'] = time.time_ns()
        rec['latence_carnet_ms'] = (rec['T_book_ns'] - t_book0) / 1e6
        if rec['market'] not in self.meta_cache:
            try:
                self.meta_cache[rec['market']] = market_meta(extra=[rec['market']])
            except Exception:
                self.meta_cache[rec['market']] = {}
        meta = self.meta_cache[rec['market']]
        ent = {}
        if b and b.get('asks'):
            asks = sorted((float(x['price']), float(x['size'])) for x in b['asks'])
            bids = sorted(((float(x['price']), float(x['size'])) for x in b.get('bids') or []), reverse=True)
            rec.update(best_ask=asks[0][0], best_bid=bids[0][0] if bids else None)
            for S in SIZES:
                sh, val, rest = walk(asks, dollars=S)
                if sh > 0:
                    f = fee_per_share(meta, rec['market'], val / sh)
                    ent[S] = dict(actions=sh, cout=val, vwap=val / sh, statut='complet' if rest <= 1e-9 else 'partiel (CAPACITY_LIMIT)',
                                  frais_entree=(f * sh) if f == f else None)
        rec['entrees'] = ent
        jlog('paper_second_buy.jsonl', dict(rec, etape='entree'))
        exits = {}
        for H in HS:
            time.sleep(max(0.0, (rec['T_DETECT_ns'] + H * 10 ** 9 - time.time_ns()) / 1e9))
            bx = books(rec['token'])
            if not bx or not ent:
                continue
            bb = sorted(((float(y['price']), float(y['size'])) for y in bx.get('bids') or []), reverse=True)
            out = {}
            for S, e in ent.items():
                q, got, left = walk(bb, shares=e['actions'])
                f = fee_per_share(meta, rec['market'], got / q) if q > 0 else 0.0
                fout = (f * q) if f == f else None
                net = ((got - e['cout'] - e['frais_entree'] - fout) / e['cout']) if (e['frais_entree'] is not None and fout is not None) else None
                out[S] = dict(produit=got, invendu=left, brut=(got - e['cout']) / e['cout'], net=net)
            exits[H] = out
        rec['sorties'] = exits
        # heure du trade (bloc) lue après coup dans le data-api, pour la latence de détection
        try:
            u = f"https://data-api.polymarket.com/trades?market={rec['market']}&start={rec['T1']}&end={int(time.time())}&limit=10000&takerOnly=true"
            tr = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'curl/8.4.0'}), timeout=30).read())
            m = [x for x in tr if x.get('transactionHash') == rec['tx2']]
            m1 = [x for x in tr if x.get('transactionHash') == rec['tx1']]
            rec['T2'] = int(m[0]['timestamp']) if m else rec.get('T2_rtds')
            rec['T1_data_api'] = int(m1[0]['timestamp']) if m1 else None
            rec['preneur_confirme_data_api'] = bool(m and m[0].get('proxyWallet', '').lower() == rec['wallet'])
            # définition historique : T2 strictement après la seconde de T1 (horodatage de bloc) ; sinon le cas est hors définition, signalé
            rec['hors_definition_meme_seconde'] = bool(rec['T1_data_api'] and rec['T2'] and rec['T2'] <= rec['T1_data_api'])
        except Exception:
            rec['T2'] = rec.get('T2_rtds')
            rec['preneur_confirme_data_api'] = None
        jlog('paper_second_buy.jsonl', dict(rec, etape='sorties'))
        row = dict(timestamp=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(rec['T_DETECT_ns'] / 1e9)), alert_id=rec['alert_id'], source_alerte=rec['source_alerte'],
                   wallet=rec['wallet'], token=rec['token'], market=rec['market'], T1=rec['T1'], T2=rec.get('T2'), tx1=rec['tx1'], tx2=rec['tx2'],
                   source_detection=rec['source_detection'], detection_latency=(rec['T_DETECT_ns'] / 1e9 - rec['T2']) if rec.get('T2') else None,
                   second_buy_usd=rec['second_buy_usd'], second_buy_price=rec['second_buy_price'], best_bid_at_detection=rec.get('best_bid'),
                   best_ask_at_detection=rec.get('best_ask'), exit_note='net à 500 $ (frais du marché) ; brut et autres tailles dans brut_p14'
                   + (' ; HORS DÉFINITION (même seconde que T1)' if rec.get('hors_definition_meme_seconde') else '')
                   + ('' if rec.get('preneur_confirme_data_api') else ' ; preneur non confirmé par le data-api'), paper_only=True)
        for S in SIZES:
            e = ent.get(S)
            row[f'simulated_entry_${S}'] = e['vwap'] if e else None
            row[f'statut_${S}'] = e['statut'] if e else 'impossible'
        for H in HS:
            row[f'exit_{H}s'] = (exits.get(H) or {}).get(500, {}).get('net')
        with LOCK:
            new = not os.path.exists(CSV)
            with open(CSV, 'a', newline='') as f:
                w = csv.DictWriter(f, fieldnames=COLS)
                if new:
                    w.writeheader()
                w.writerow(row)

    # ------------------------------------------------ sources
    def handle_rtds_tx(self, h):
        t_ns, rows = self.rt.pop(h)
        fee_rows = [(t, r) for t, r in rows if r.get('fee') is not None]
        takers = fee_rows[:1] if len(fee_rows) == 1 else (rows if len(rows) == 1 else [])
        for t, r in takers:
            try:
                self.candidate(r.get('proxyWallet', '').lower(), str(r.get('asset')), r.get('side'), float(r['price']) * float(r['size']), float(r['price']), h, t, 'rtds',
                               int(r.get('timestamp', 0)) or None)
            except Exception:
                pass

    async def rtds(self):
        while True:
            try:
                async with websockets.connect('wss://ws-live-data.polymarket.com', max_size=2 ** 25) as ws:
                    await ws.send(json.dumps({'action': 'subscribe', 'subscriptions': [{'topic': 'activity', 'type': 'trades'}]}))
                    last = lp = time.time()
                    while True:
                        if time.time() - lp > 5:
                            await ws.send('PING'); lp = time.time()
                        if time.time() - last > 30:
                            raise RuntimeError('silence RTDS 30 s')
                        try:
                            m = await asyncio.wait_for(ws.recv(), timeout=1)
                            last = time.time()
                            if m.startswith('{'):
                                p = json.loads(m).get('payload') or {}
                                h = p.get('transactionHash')
                                if h and (p.get('proxyWallet', '').lower(), str(p.get('asset'))) in self.active:
                                    self.rt.setdefault(h, [time.time_ns(), []])[1].append((time.time_ns(), p))
                                    if p.get('fee') is not None:
                                        self.handle_rtds_tx(h)
                        except asyncio.TimeoutError:
                            pass
                        now = time.time_ns()
                        for h in [h for h, v in self.rt.items() if now - v[0] > 1.5e9]:
                            self.handle_rtds_tx(h)
            except Exception as ex:
                jlog('paper_etat.jsonl', dict(t_ns=time.time_ns(), event='erreur_rtds', err=repr(ex)[:150]))
                await asyncio.sleep(2)

    def from_chain(self, r, t):
        tp = r.get('topics') or []
        if len(tp) < 4 or tp[3][-40:].lower() not in [e[-40:] for e in EX]:
            return
        w = '0x' + tp[2][-40:].lower()
        d = r['data'][2:]
        v = [int(d[i:i + 64], 16) for i in range(0, len(d), 64)]
        if v[0] != 0:
            return
        mk, tk = v[2] / 1e6, v[3] / 1e6
        if tk:
            self.candidate(w, str(v[1]), 'BUY', mk, mk / tk, r['transactionHash'], t, 'chaine')

    async def chain(self):
        while True:
            ws_set = frozenset(w for w, _ in self.active)
            if not ws_set:
                await asyncio.sleep(1); continue
            self.chain_set = ws_set
            try:
                makers = ['0x' + '0' * 24 + w[2:] for w in ws_set]
                async with websockets.connect('wss://polygon-bor-rpc.publicnode.com', max_size=2 ** 25, open_timeout=20, ping_interval=20) as ws:
                    await ws.send(json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'eth_subscribe', 'params': ['logs', {'address': EX, 'topics': [TOPIC, None, makers]}]}))
                    while frozenset(w for w, _ in self.active) == ws_set:
                        try:
                            m = json.loads(await asyncio.wait_for(ws.recv(), timeout=2))
                        except asyncio.TimeoutError:
                            continue
                        r = (m.get('params') or {}).get('result')
                        if isinstance(r, dict) and r.get('transactionHash'):
                            self.from_chain(r, time.time_ns())
            except Exception as ex:
                jlog('paper_etat.jsonl', dict(t_ns=time.time_ns(), event='erreur_chaine', err=repr(ex)[:150]))
                await asyncio.sleep(3)

    async def alerts_loop(self):
        k = 0
        while True:
            self.read_alerts()
            k += 1
            if k % 300 == 0:
                jlog('paper_etat.jsonl', dict(t_ns=time.time_ns(), event='etat', fenetres_ouvertes=len(self.active), alertes_vues=len(self.seen_alerts),
                                              seconds_achats=len(self.done_tx), paper_only=True))
            await asyncio.sleep(1)

    async def main(self):
        self.read_alerts()
        jlog('paper_etat.jsonl', dict(t_ns=time.time_ns(), event='pret', fenetres_ouvertes=len(self.active), alertes_vues=len(self.seen_alerts), paper_only=True))
        print('prêt', len(self.active), 'fenêtres ouvertes', flush=True)
        await asyncio.gather(self.alerts_loop(), self.rtds(), self.chain())


if __name__ == '__main__':
    asyncio.run(Logger().main())
