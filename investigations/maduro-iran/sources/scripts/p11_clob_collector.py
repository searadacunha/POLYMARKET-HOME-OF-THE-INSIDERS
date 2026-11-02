#!/usr/bin/env python3
"""Phase 11 : collecteur en direct du CLOB Polymarket (RECHERCHE UNIQUEMENT, aucun ordre).

Enregistre, sans transformation, dans donnees/brut_p11/ :
  ws_market/AAAA-MM-JJ/HH_cN.jsonl.zst : messages du websocket « market » (book, price_change, best_bid_ask, last_trade_price)
  rtds/AAAA-MM-JJ/HH.jsonl.zst        : tous les trades de la plateforme (activity/trades), avec wallet, hash, frais
  chain/AAAA-MM-JJ/HH.jsonl.zst       : logs OrderFilled v2 et en-têtes de blocs d'un nœud Polygon public (wallet, hash, bloc, logIndex)
  rest_books/AAAA-MM-JJ/HH.jsonl.zst  : instantanés REST POST /books de la watchlist (toutes les 10 min) et rafales demandées
  meta/                               : watchlists horodatées, abonnements, horloge (sntp), état
Chaque ligne : [heure locale en ns, identifiant de connexion, message brut tel que reçu].

Watchlist (reconstruite toutes les heures, jamais réduite en cours de route) :
  A = marchés actifs de l'univers touchés par les wallets SIG_HIST historiques (trades sur 30 j ou positions ouvertes) ;
  C = échantillon de contrôle tiré au hasard (graine 11) parmi les autres marchés actifs comparables ;
  D = marchés ajoutés en direct par p11_signal_listener.py (meta/dynamic_watch.jsonl).
Usage : python3 p11_clob_collector.py           (boucle infinie ; arrêt propre par SIGTERM)"""
import asyncio, json, os, sys, time, random, signal, shutil, subprocess, collections, threading
import zstandard as zstd
import websockets

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p11_common import RAW, DATA, excluded, category, get  # noqa: E402

WS_MARKET = 'wss://ws-subscriptions-clob.polymarket.com/ws/market'
WS_RTDS = 'wss://ws-live-data.polymarket.com'
TOK_PER_CONN = 480
CAP_A, CAP_C = 500, 150
CAP_TOTAL = 700                      # plafond de marchés suivis (disque)
MIN_FREE_GB_CONTROL, MIN_FREE_GB_ALL = 6, 3
os.makedirs(os.path.join(RAW, 'meta'), exist_ok=True)


class Sink:
    """Fichier zstd par heure, trame vidée toutes les 60 s (au plus 60 s perdues en cas d'arrêt brutal)."""
    def __init__(self, kind, tag=''):
        self.kind, self.tag = kind, tag
        self.hour = None
        self.fh = self.w = None
        self.last_flush = time.time()
        self.n = 0
        self.bytes = 0
        self.lock = threading.Lock()

    def _open(self):
        t = time.gmtime()
        hour = time.strftime('%Y-%m-%d/%H', t)
        if hour == self.hour:
            return
        self._close()
        d = os.path.join(RAW, self.kind, hour.split('/')[0])
        os.makedirs(d, exist_ok=True)
        fn = os.path.join(d, f'{hour.split("/")[1]}{("_" + self.tag) if self.tag else ""}.jsonl.zst')
        k = 1
        while os.path.exists(fn):                     # redémarrage dans la même heure : nouveau fichier
            fn = fn.replace('.jsonl.zst', f'.{k}.jsonl.zst'); k += 1
        self.fh = open(fn, 'wb')
        self.w = zstd.ZstdCompressor(level=12).stream_writer(self.fh, closefd=False)
        self.hour = hour

    def write(self, conn, msg):
        with self.lock:
            self._write(conn, msg)

    def _write(self, conn, msg):
        self._open()
        line = json.dumps([time.time_ns(), conn, msg], ensure_ascii=False) + '\n'
        b = line.encode()
        self.w.write(b)
        self.n += 1
        self.bytes += len(b)
        if time.time() - self.last_flush > 60:
            self.w.flush(zstd.FLUSH_FRAME)
            self.fh.flush()
            self.last_flush = time.time()

    def close(self):
        with self.lock:
            self._close()

    def _close(self):
        if self.w:
            self.w.flush(zstd.FLUSH_FRAME)
            self.w.close()
            self.fh.close()
        self.w = self.fh = None


def meta_log(name, obj):
    with open(os.path.join(RAW, 'meta', name), 'a') as f:
        f.write(json.dumps(obj, ensure_ascii=False) + '\n')


def fetch_active():
    """Marchés actifs de l'univers (mêmes exclusions et catégories que les phases 8-9), par fenêtres d'échéance."""
    import datetime as dt
    out = {}
    d0, end = dt.date.today() - dt.timedelta(days=30), dt.date.today() + dt.timedelta(days=900)
    while d0 < end:
        d1 = d0 + dt.timedelta(days=7 if d0 < dt.date.today() + dt.timedelta(days=120) else 60)
        off = 0
        while off < 2000:
            try:
                r = get(f'https://gamma-api.polymarket.com/markets?active=true&closed=false&volume_num_min=10000&end_date_min={d0}&end_date_max={d1}&limit=100&offset={off}', tries=2)
            except Exception:
                break
            for m in r:
                out[m['conditionId']] = m
            if len(r) < 100:
                break
            off += 100
        d0 = d1
    keep = {}
    for c, m in out.items():
        if m.get('clobTokenIds') and m.get('enableOrderBook', True) and not excluded(m.get('slug'), m.get('question')):
            m['cat'] = category(m['slug'])
            keep[c] = m
    return keep


def leaders_markets():
    import pandas as pd
    EV = pd.read_pickle(os.path.join(DATA, 'p9', 'events_final.pkl'))   # pickle local produit par p9_*.py
    leaders = sorted(set(EV[EV.SIG_HIST].wallet))
    now = time.time()
    touch = collections.Counter()
    for w in leaders:
        try:
            tr = get(f'https://data-api.polymarket.com/trades?user={w}&limit=500&takerOnly=false', tries=2)
            po = get(f'https://data-api.polymarket.com/positions?user={w}&limit=500&sizeThreshold=1', tries=2)
        except Exception:
            continue
        for t in tr:
            if now - int(t['timestamp']) < 30 * 86400:
                touch[t['conditionId']] += 1
        for p in po:
            touch[p['conditionId']] += 1
    return leaders, touch


def build_watchlist(prev=None):
    act = fetch_active()
    leaders, touch = leaders_markets()
    A = sorted([c for c in act if touch.get(c)], key=lambda c: (-touch[c], -float(act[c].get('volume24hr') or 0)))[:CAP_A]
    rest = [c for c in act if c not in set(A) and float(act[c].get('volume24hr') or 0) >= 100]
    rnd = random.Random(11)
    rnd.shuffle(rest)
    catmix = collections.Counter(act[c]['cat'] for c in A)
    C = []
    for cat, k in catmix.items():
        pool = [c for c in rest if act[c]['cat'] == cat]
        C += pool[:max(1, round(CAP_C * k / max(len(A), 1)))]
    wl = dict(prev or {})
    for tier, ids in (('A', A), ('C', C)):
        for c in ids:
            if c in wl:
                continue
            m = act[c]
            wl[c] = dict(tier=tier, tokens=json.loads(m['clobTokenIds']), slug=m.get('slug'), question=m.get('question'), cat=m['cat'],
                         endDate=m.get('endDate'), negRisk=m.get('negRisk'), feesEnabled=m.get('feesEnabled'), feeSchedule=m.get('feeSchedule'),
                         volume24hr=m.get('volume24hr'), liquidityClob=m.get('liquidityClob'), leader_touches=touch.get(c, 0), ajoute_ns=time.time_ns())
    snap = os.path.join(RAW, 'meta', time.strftime('watchlist_%Y%m%dT%H%M%SZ.json', time.gmtime()))
    json.dump(dict(cree_ns=time.time_ns(), n_actifs_univers=len(act), n_leaders=len(leaders), watchlist=wl), open(snap, 'w'))
    return wl


class Collector:
    def __init__(self):
        self.wl = {}
        self.subscribed = set()
        self.conns = []
        self.sinks = {}
        self.stats = collections.Counter()
        self.stop = asyncio.Event()
        self.rest_sink = Sink('rest_books')
        self.rtds_sink = Sink('rtds')
        self.paused_control = False
        self.dyn_pos = 0

    async def ws_market(self, cid_list, k):
        toks = [t for c in cid_list for t in self.wl[c]['tokens']]
        sink = self.sinks.setdefault(k, Sink('ws_market', f'c{k}'))
        backoff = 1
        while not self.stop.is_set():
            if self.paused_control and all(self.wl[c]['tier'] == 'C' for c in cid_list):
                await asyncio.sleep(30); continue
            try:
                async with websockets.connect(WS_MARKET, max_size=2 ** 25, ping_interval=20, ping_timeout=20) as ws:
                    await ws.send(json.dumps({'assets_ids': toks, 'type': 'market', 'custom_feature_enabled': True}))
                    meta_log('subscriptions.jsonl', dict(t_ns=time.time_ns(), conn=f'c{k}', event='subscribe', n_tokens=len(toks), markets=cid_list))
                    backoff = 1
                    while not self.stop.is_set():
                        try:
                            msg = await asyncio.wait_for(ws.recv(), timeout=120)
                        except asyncio.TimeoutError:          # chien de garde (01/10) : connexion silencieuse -> reconnexion
                            raise RuntimeError('carnet silencieux depuis 120 s')
                        sink.write(f'c{k}', msg)
                        self.stats[f'c{k}'] += 1
            except Exception as e:
                meta_log('subscriptions.jsonl', dict(t_ns=time.time_ns(), conn=f'c{k}', event='erreur', err=repr(e)[:200]))
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60)

    async def rtds(self):
        backoff = 1
        while not self.stop.is_set():
            try:
                async with websockets.connect(WS_RTDS, max_size=2 ** 25, ping_interval=None) as ws:
                    await ws.send(json.dumps({'action': 'subscribe', 'subscriptions': [{'topic': 'activity', 'type': 'trades'}]}))
                    meta_log('subscriptions.jsonl', dict(t_ns=time.time_ns(), conn='rtds', event='subscribe'))
                    backoff = 1
                    last_ping = time.time()
                    last_msg = time.time()
                    while not self.stop.is_set():
                        if time.time() - last_ping > 5:
                            await ws.send('PING'); last_ping = time.time()
                        if time.time() - last_msg > 30:       # chien de garde (01/10) : flux tari sans fermeture observé sur le listener
                            raise RuntimeError('RTDS silencieux depuis 30 s')
                        try:
                            msg = await asyncio.wait_for(ws.recv(), timeout=10)
                        except asyncio.TimeoutError:
                            continue
                        last_msg = time.time()
                        self.rtds_sink.write('rtds', msg)
                        self.stats['rtds'] += 1
            except Exception as e:
                meta_log('subscriptions.jsonl', dict(t_ns=time.time_ns(), conn='rtds', event='erreur', err=repr(e)[:200]))
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60)

    async def chain(self):
        """Logs OrderFilled v2 reçus d'un nœud Polygon public (le wallet y est connu ~0,8 s avant RTDS, mesuré le 01/10)."""
        sink = self.sinks.setdefault('chain', Sink('chain'))
        topic = '0xd543adfd945773f1a62f74f0ee55a5e3b9b1a28262980ba90b1a89f2ea84d8ee'
        ex = ['0xe111180000d2663c0091e4f400237545b87b996b', '0xe2222d279d744050d28e00520010520000310f59']
        backoff = 1
        while not self.stop.is_set():
            try:
                async with websockets.connect('wss://polygon-bor-rpc.publicnode.com', max_size=2 ** 25, open_timeout=20, ping_interval=20) as ws:
                    # filtre sur le maker (topic 2) : wallets SIG_HIST historiques et éligibles au démarrage du listener (volume réduit d'environ 99 %)
                    ws_list = set()
                    fp = os.path.join(RAW, 'live', 'wallets_eligibles_au_demarrage.json')
                    if os.path.exists(fp):
                        ws_list |= set(json.load(open(fp)))
                    try:
                        import pandas as pd
                        EV = pd.read_pickle(os.path.join(DATA, 'p9', 'events_final.pkl'))   # pickle local (phase 9)
                        ws_list |= set(EV[EV.SIG_HIST].wallet)
                    except Exception:
                        pass
                    makers = ['0x' + '0' * 24 + w.lower()[2:] for w in sorted(ws_list)]
                    meta_log('subscriptions.jsonl', dict(t_ns=time.time_ns(), conn='chain', event='filtre_makers', n=len(makers)))
                    await ws.send(json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'eth_subscribe', 'params': ['logs', {'address': ex, 'topics': [topic, None, makers]}]}))
                    await ws.send(json.dumps({'jsonrpc': '2.0', 'id': 2, 'method': 'eth_subscribe', 'params': ['newHeads']}))
                    meta_log('subscriptions.jsonl', dict(t_ns=time.time_ns(), conn='chain', event='subscribe'))
                    backoff = 1
                    while not self.stop.is_set():
                        try:
                            msg = await asyncio.wait_for(ws.recv(), timeout=60)
                        except asyncio.TimeoutError:
                            raise RuntimeError('aucun bloc depuis 60 s')
                        sink.write('chain', msg)
                        self.stats['chain'] += 1
            except Exception as e:
                meta_log('subscriptions.jsonl', dict(t_ns=time.time_ns(), conn='chain', event='erreur', err=repr(e)[:200]))
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60)

    def snapshot_books(self, tokens, tag):
        for i in range(0, len(tokens), 50):
            try:
                t1 = time.time_ns()
                r = get('https://clob.polymarket.com/books', data=[{'token_id': t} for t in tokens[i:i + 50]], tries=2)
                self.rest_sink.write(tag, dict(t_envoi_ns=t1, books=r))
            except Exception as e:
                self.rest_sink.write(tag, dict(erreur=repr(e)[:200]))

    async def rest_loop(self):
        while not self.stop.is_set():
            toks = [t for c in list(self.wl) for t in self.wl[c]['tokens']]
            await asyncio.get_running_loop().run_in_executor(None, self.snapshot_books, toks, 'rest_10min')
            await asyncio.sleep(600)

    async def burst_loop(self):
        """Rafales REST demandées par le listener (meta/burst_requests.jsonl) : T+0, 100, 250, 500 ms, 1, 2, 3, 5, 10, 30, 60 s."""
        fp = os.path.join(RAW, 'meta', 'burst_requests.jsonl')
        pos = os.path.getsize(fp) if os.path.exists(fp) else 0      # au redémarrage, ne pas rejouer les rafales passées
        while not self.stop.is_set():
            if os.path.exists(fp):
                with open(fp) as f:
                    f.seek(pos)
                    lines = f.readlines()
                    pos = f.tell()
                for l in lines:
                    req = json.loads(l)
                    asyncio.create_task(self.burst(req))
            await asyncio.sleep(0.05)

    async def burst(self, req):
        t0 = req['t_ns'] / 1e9
        if time.time() - t0 > 5:                                       # demande trop ancienne : rafale non représentative
            meta_log('etat.jsonl', dict(t_ns=time.time_ns(), event='rafale_ignoree', alert_id=req.get('alert_id'), retard_s=round(time.time() - t0, 1)))
            return
        for off in (0, 0.1, 0.25, 0.5, 1, 2, 3, 5, 10, 30, 60):
            dt = t0 + off - time.time()
            if dt > 0:
                await asyncio.sleep(dt)
            await asyncio.get_running_loop().run_in_executor(None, self.snapshot_books, req['tokens'], f'burst:{req["alert_id"]}:{off}')

    async def dynamic_loop(self):
        fp = os.path.join(RAW, 'meta', 'dynamic_watch.jsonl')
        while not self.stop.is_set():
            new = []
            if os.path.exists(fp):
                with open(fp) as f:
                    f.seek(self.dyn_pos)
                    for l in f.readlines():
                        d = json.loads(l)
                        if d['cid'] not in self.wl:
                            self.wl[d['cid']] = dict(tier='D', tokens=d['tokens'], slug=d.get('slug'), cat=d.get('cat'), ajoute_ns=time.time_ns(), raison=d.get('raison'))
                            new.append(d['cid'])
                    self.dyn_pos = f.tell()
            if new:
                k = len(self.conns)
                self.conns.append(asyncio.create_task(self.ws_market(new, k)))
                self.subscribed |= set(new)
                meta_log('subscriptions.jsonl', dict(t_ns=time.time_ns(), conn=f'c{k}', event='ajout_dynamique', markets=new))
            await asyncio.sleep(0.2)

    async def refresh_loop(self):
        while not self.stop.is_set():
            await asyncio.sleep(3600)
            try:
                wl = await asyncio.get_running_loop().run_in_executor(None, build_watchlist, self.wl)
            except Exception as e:
                meta_log('subscriptions.jsonl', dict(t_ns=time.time_ns(), event='erreur_refresh', err=repr(e)[:200])); continue
            new = [c for c in wl if c not in self.subscribed][:max(0, CAP_TOTAL - len(self.subscribed))]
            self.wl = {c: v for c, v in wl.items() if c in self.subscribed or c in set(new)}
            for i in range(0, len(new), TOK_PER_CONN // 2):
                k = len(self.conns)
                self.conns.append(asyncio.create_task(self.ws_market(new[i:i + TOK_PER_CONN // 2], k)))
            self.subscribed |= set(new)

    async def housekeeping(self):
        last_clock = 0
        while not self.stop.is_set():
            free = shutil.disk_usage(RAW).free / 1e9
            self.paused_control = free < MIN_FREE_GB_CONTROL
            if free < MIN_FREE_GB_ALL:
                meta_log('etat.jsonl', dict(t_ns=time.time_ns(), event='arret_disque', libre_go=free))
                self.stop.set()
            if time.time() - last_clock > 1800:
                try:
                    out = subprocess.run(['sntp', '-t', '3', 'time.apple.com'], capture_output=True, text=True, timeout=10).stdout.strip()
                except Exception as e:
                    out = repr(e)
                meta_log('clock.jsonl', dict(t_ns=time.time_ns(), sntp=out))
                last_clock = time.time()
            st = dict(t_ns=time.time_ns(), libre_go=round(free, 2), marches=len(self.wl), connexions=len(self.conns), messages=dict(self.stats),
                      controle_en_pause=self.paused_control, octets_bruts={k: s.bytes for k, s in self.sinks.items()}, rtds_octets=self.rtds_sink.bytes)
            json.dump(st, open(os.path.join(RAW, 'meta', 'etat_courant.json'), 'w'))
            await asyncio.sleep(30)

    async def run(self):
        loop = asyncio.get_running_loop()
        for s in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(s, self.stop.set)
        self.wl = await loop.run_in_executor(None, build_watchlist, None)
        cids = sorted(self.wl, key=lambda c: (self.wl[c]['tier'], c))
        step = TOK_PER_CONN // 2
        for i in range(0, len(cids), step):
            self.conns.append(asyncio.create_task(self.ws_market(cids[i:i + step], len(self.conns))))
        self.subscribed = set(cids)
        tasks = [asyncio.create_task(x) for x in (self.rtds(), self.chain(), self.rest_loop(), self.burst_loop(), self.dynamic_loop(), self.refresh_loop(), self.housekeeping())]
        meta_log('etat.jsonl', dict(t_ns=time.time_ns(), event='demarrage', marches=len(self.wl), connexions=len(self.conns)))
        await self.stop.wait()
        for t in tasks + self.conns:
            t.cancel()
        for s in list(self.sinks.values()) + [self.rest_sink, self.rtds_sink]:
            s.close()
        meta_log('etat.jsonl', dict(t_ns=time.time_ns(), event='arret'))


if __name__ == '__main__':
    asyncio.run(Collector().run())
