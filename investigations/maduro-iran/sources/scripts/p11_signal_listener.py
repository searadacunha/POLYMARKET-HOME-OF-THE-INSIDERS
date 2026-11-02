#!/usr/bin/env python3
"""Phase 11 : détection de SIG_HIST en direct (RECHERCHE UNIQUEMENT, aucun ordre).

1. Réchauffe p9_detector.Detecteur (SIG_HIST V1, inchangé) sur l'historique de la phase 9 (trades >= 100 $ jusqu'au 16/09/2026).
2. Rattrape la période 16/09 -> démarrage par le data-api (takerOnly=true, >= 100 $, marchés de l'univers actifs ou fermés depuis le 16/09).
   Les réponses brutes sont conservées dans donnees/brut_p11/backfill/.
3. Lit RTDS (activity/trades). Le preneur d'une transaction est la ligne qui porte `fee`, ou la seule ligne ; sinon la transaction est
   « ambiguë » : son prix alimente l'état, et une ligne d'un wallet éligible y est traitée comme candidate puis vérifiée par le data-api.
4. À chaque alerte SIG_HIST : ligne dans live/alerts.jsonl (T_obs = réception RTDS en ns), demande de rafale REST au collecteur,
   ajout du marché à la watchlist dynamique, vérification a posteriori par le data-api (live/verifications.jsonl).
Usage : python3 p11_signal_listener.py"""
import asyncio, json, os, sys, time, gzip, threading, collections, concurrent.futures as cf, datetime as dt
import numpy as np, pandas as pd
import websockets

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p11_common import RAW, DATA, excluded, category, get, sig_hist_version  # noqa: E402
from p9_detector import Detecteur  # noqa: E402

LIVE = os.path.join(RAW, 'live')
BF = os.path.join(RAW, 'backfill')
for d in (LIVE, BF, os.path.join(RAW, 'meta')):
    os.makedirs(d, exist_ok=True)
VERSION = sig_hist_version()
API = 'https://data-api.polymarket.com/trades'


def jlog(path, obj):
    with open(path, 'a') as f:
        f.write(json.dumps(obj, ensure_ascii=False, default=str) + '\n')


def iso_ts(s):
    try:
        return int(pd.Timestamp(s).timestamp()) if s else None
    except Exception:
        return None


class Meta:
    """Catégorie et échéance par marché (Gamma), en cache."""
    def __init__(self):
        self.m = {}
        self.lock = threading.Lock()
        self.pending = set()

    def load_lists(self):
        out = {}
        d0, end = dt.date(2026, 9, 1), dt.date.today() + dt.timedelta(days=900)
        for closed in ('false', 'true'):
            d = d0
            while d < end:
                d1 = d + dt.timedelta(days=7 if d < dt.date.today() + dt.timedelta(days=120) else 60)
                if closed == 'true' and d > dt.date.today() + dt.timedelta(days=1):
                    break
                off = 0
                while off < 2000:
                    try:
                        r = get(f'https://gamma-api.polymarket.com/markets?closed={closed}&volume_num_min=10000&end_date_min={d}&end_date_max={d1}&limit=100&offset={off}', tries=2)
                    except Exception:
                        break
                    for x in r:
                        out[x['conditionId']] = x
                    if len(r) < 100:
                        break
                    off += 100
                d = d1
        for c, x in out.items():
            self.put(x)
        return out

    def put(self, x):
        with self.lock:
            self.m[x['conditionId']] = dict(slug=x.get('slug'), cat=category(x.get('slug')), end=iso_ts(x.get('endDate')),
                                           excl=excluded(x.get('slug'), x.get('question')), tokens=json.loads(x['clobTokenIds']) if x.get('clobTokenIds') else [])

    def get(self, cid, slug=None):
        x = self.m.get(cid)
        if x is None and cid not in self.pending:
            self.pending.add(cid)
            threading.Thread(target=self._fetch, args=(cid,), daemon=True).start()
        return x

    def _fetch(self, cid):
        for closed in ('false', 'true'):
            try:
                r = get(f'https://gamma-api.polymarket.com/markets?closed={closed}&condition_ids={cid}', tries=2)
                if r:
                    self.put(r[0]); return
            except Exception:
                pass


def fetch_window(cid, a, b):
    url = f'{API}?market={cid}&start={a}&end={b}&limit=10000&takerOnly=true&filterType=CASH&filterAmount=100'
    rows = get(url, tries=4)
    if isinstance(rows, list) and len(rows) >= 10000 and b - a > 2:
        m = (a + b) // 2
        return fetch_window(cid, m + 1, b) + fetch_window(cid, a, m)
    return rows if isinstance(rows, list) else []


def backfill(meta, t_from, t_to, chained=False):
    """Trades preneurs >= 100 $ des marchés de l'univers entre t_from et t_to (data-api), bruts conservés."""
    cids = [c for c, x in meta.m.items() if not x['excl']]
    if chained:
        return _fetch_all(meta, cids, t_from, t_to)
    import glob
    prev = sorted(glob.glob(os.path.join(BF, f'backfill_{t_from}_*.jsonl.gz')), key=lambda f: int(f.split('_')[-1].split('.')[0]))
    if prev:                                   # cache existant : on le relit et on ne rattrape que l'incrément
        rows = []
        for fpx in prev:
            for l in gzip.open(fpx, 'rt'):
                rows += json.loads(l)['rows']
        last_to = int(prev[-1].split('_')[-1].split('.')[0])
        if t_to - last_to > 60:
            rows += backfill(meta, last_to + 1, t_to, chained=True)
        return rows
    return _fetch_all(meta, cids, t_from, t_to)


def _fetch_all(meta, cids, t_from, t_to):
    fp = os.path.join(BF, f'backfill_{t_from}_{t_to}.jsonl.gz')
    rows = []
    t0 = time.time()
    with gzip.open(fp + '.tmp', 'wt') as f, cf.ThreadPoolExecutor(8) as ex:
        futs = {ex.submit(fetch_window, c, t_from, t_to): c for c in cids}
        for i, fu in enumerate(cf.as_completed(futs)):
            c = futs[fu]
            try:
                r = fu.result()
            except Exception as e:
                jlog(os.path.join(LIVE, 'listener.log.jsonl'), dict(t_ns=time.time_ns(), event='erreur_backfill', cid=c, err=repr(e)[:150]))
                continue
            keep = ('proxyWallet', 'side', 'asset', 'conditionId', 'size', 'price', 'timestamp', 'outcomeIndex', 'transactionHash')
            r = [{k: x.get(k) for k in keep} for x in r]
            f.write(json.dumps(dict(cid=c, rows=r)) + '\n')
            rows += r
            if i % 500 == 0:
                print(f'  rattrapage {i}/{len(cids)} marchés, {len(rows)} trades, {time.time() - t0:.0f} s', flush=True)
    os.replace(fp + '.tmp', fp)
    return rows


def to_trade(r, meta, rid):
    x = meta.m.get(r['conditionId'])
    return dict(ts=int(r['timestamp']), cid=r['conditionId'], cat=x['cat'] if x else None, end=x['end'] if x else None,
                wallet=r['proxyWallet'].lower(), side=r['side'], asset=str(r['asset']), price=float(r['price']),
                usd=float(r['price']) * float(r['size']), oi=int(r['outcomeIndex']), rid=rid)


class Listener:
    def __init__(self):
        self.meta = Meta()
        self.det = None
        self.tx = {}                     # hash -> [premier t_ns, lignes]
        self.done = collections.OrderedDict()
        self.n_alerts = 0
        self.stats = collections.Counter()
        self.pool = cf.ThreadPoolExecutor(4)

    def warm(self):
        t = time.time()
        print('listes Gamma...', flush=True)
        self.meta.load_lists()
        print('marchés connus', len(self.meta.m), flush=True)
        det = Detecteur(differe=True)
        P = pd.read_pickle(os.path.join(DATA, 'p9', 'prints.pkl'))     # pickle local (phase 9)
        last = int(P.ts.max())
        det.rejouer(P, log_every=0)
        det.lignes = []
        print('historique rejoué', round(time.time() - t), 's ; dernier trade', pd.to_datetime(last, unit='s'), flush=True)
        now = int(time.time())
        rows = backfill(self.meta, last + 1, now)
        rows.sort(key=lambda r: (int(r['timestamp']), r['transactionHash']))
        print('rattrapage', len(rows), 'trades', flush=True)
        for k, r in enumerate(rows):
            if self.meta.m.get(r['conditionId'], {}).get('excl'):
                continue
            det.traiter(to_trade(r, self.meta, -1 - k))
            det.lignes = []
        det.differe = False
        self.det = det
        elig = [w for w, h in det.hist.items() if h[0] >= 5 and (h[1] + 10 * det.p0) / (h[0] + 10) >= det.hthr]
        jlog(os.path.join(LIVE, 'listener.log.jsonl'), dict(t_ns=time.time_ns(), event='pret', sig_hist_sha256=VERSION, wallets_eligibles=len(elig),
                                                           backfill_de=last + 1, backfill_a=now, n_backfill=len(rows), duree_s=round(time.time() - t)))
        json.dump(sorted(elig), open(os.path.join(LIVE, 'wallets_eligibles_au_demarrage.json'), 'w'))
        print('prêt ; wallets éligibles', len(elig), round(time.time() - t), 's', flush=True)
        self.backfill_to = now

    def handle_tx(self, h):
        t_ns, rows = self.tx.pop(h)
        self.done[h] = 1
        if len(self.done) > 200000:
            self.done.popitem(last=False)
        r0 = rows[0][1]
        x = self.meta.get(r0['conditionId'], r0.get('slug'))
        if x is None:
            if excluded(r0.get('eventSlug') or r0.get('slug'), r0.get('title', '')):
                return
            self.meta.m.setdefault(r0['conditionId'], dict(slug=r0.get('slug'), cat=category(r0.get('slug')), end=None, excl=False, tokens=[]))
            x = self.meta.m[r0['conditionId']]
        if x['excl']:
            return
        fee_rows = [(t, r) for t, r in rows if r.get('fee') is not None]
        if len(fee_rows) == 1:
            takers, statut = fee_rows, 'fee'
        elif len(rows) == 1:
            takers, statut = rows, 'ligne_unique'
        else:
            takers, statut = [rows[0]], 'ambigu'
            elig = [(t, r) for t, r in rows if r['side'] == 'BUY' and self.eligible(r['proxyWallet'].lower()) and float(r['price']) * float(r['size']) >= 250]
            takers = elig + [x for x in takers if x not in elig] if elig else takers
        self.stats[statut] += 1
        for t_obs, r in takers:
            usd = float(r['price']) * float(r['size'])
            if usd < 100:
                continue
            tr = to_trade(r, self.meta, -1)
            E = self.det.traiter(tr)
            if len(E):
                for e in E[E.is_FAE].itertuples():
                    jlog(os.path.join(LIVE, 'fae_events.jsonl'), dict(T_obs_ns=t_obs, ts_echange=int(e.ts), tx=r.get('transactionHash'), wallet=e.wallet, market=e.cid,
                         asset=e.asset, outcomeIndex=int(e.d), price=float(e.price), usd=float(e.usd), p_before=None if pd.isna(e.p_before) else float(e.p_before),
                         FOLLOW=bool(e.FOLLOW), dpre_10m=None if pd.isna(e.dpre_10m) else float(e.dpre_10m), act_10m=None if pd.isna(e.act_10m) else float(e.act_10m),
                         hours_to_end=None if pd.isna(e.hours_to_end) else float(e.hours_to_end), cat=e.cat, hist_n=int(e.hist_n), hist_score=float(e.hist_score),
                         SIG_HIST=bool(e.SIG_HIST), preneur=statut))
            if len(E) and E.SIG_HIST.any():
                for e in E[E.SIG_HIST].itertuples():
                    self.alert(e, r, t_obs, statut)

    def eligible(self, w):
        h = self.det.hist.get(w)
        return bool(h and h[0] >= 5 and (h[1] + 10 * self.det.p0) / (h[0] + 10) >= self.det.hthr)

    def alert(self, e, r, t_obs, statut):
        self.n_alerts += 1
        aid = f'A{time.strftime("%Y%m%dT%H%M%S", time.gmtime())}_{self.n_alerts}'
        x = self.meta.m.get(e.cid, {})
        a = dict(alert_id=aid, sig_hist_sha256=VERSION, T_obs_ns=t_obs, T_alerte_ns=time.time_ns(), ts_echange=int(e.ts), tx=r.get('transactionHash'),
                 wallet=e.wallet, market=e.cid, asset=e.asset, outcomeIndex=int(e.d), direction='outcome0 (YES)' if int(e.d) == 0 else 'outcome1 (NO)',
                 price=float(e.price), usd=float(e.usd), p_before=float(e.p_before), hist_n=int(e.hist_n), hist_score=float(e.hist_score),
                 score_ctx=float(e.score_ctx), score_wallet=float(e.score_wallet), p_ctx=float(e.p_ctx), conv_nwallets_10m=int(e.conv_nwallets_10m),
                 preneur=statut, slug=x.get('slug'), cat=x.get('cat'), fee_rtds=r.get('fee'))
        jlog(os.path.join(LIVE, 'alerts.jsonl'), a)
        toks = x.get('tokens') or [e.asset]
        jlog(os.path.join(RAW, 'meta', 'burst_requests.jsonl'), dict(t_ns=time.time_ns(), alert_id=aid, tokens=toks))
        jlog(os.path.join(RAW, 'meta', 'dynamic_watch.jsonl'), dict(cid=e.cid, tokens=toks, slug=x.get('slug'), cat=x.get('cat'), raison=aid))
        self.pool.submit(self.verify, a)
        print('ALERTE', aid, e.wallet[:10], x.get('slug'), round(float(e.usd)), flush=True)

    def verify(self, a):
        """Recalcul a posteriori : le trade figure-t-il comme preneur dans le data-api ? (60 s puis 10 min après)"""
        for delay in (60, 600):
            time.sleep(delay)
            try:
                r = get(f'{API}?market={a["market"]}&start={a["ts_echange"] - 2}&end={a["ts_echange"] + 2}&takerOnly=true&limit=500')
                ok = any(x['transactionHash'] == a['tx'] and x['proxyWallet'].lower() == a['wallet'] for x in r)
                jlog(os.path.join(LIVE, 'verifications.jsonl'), dict(alert_id=a['alert_id'], delai_s=delay, preneur_confirme=ok, n_lignes=len(r), t_ns=time.time_ns()))
                if ok:
                    return
            except Exception as ex:
                jlog(os.path.join(LIVE, 'verifications.jsonl'), dict(alert_id=a['alert_id'], delai_s=delay, erreur=repr(ex)[:150]))

    async def run(self):
        await asyncio.get_running_loop().run_in_executor(None, self.warm)
        backoff = 1
        last_stat = time.time()
        while True:
            try:
                async with websockets.connect('wss://ws-live-data.polymarket.com', max_size=2 ** 25, ping_interval=None) as ws:
                    await ws.send(json.dumps({'action': 'subscribe', 'subscriptions': [{'topic': 'activity', 'type': 'trades'}]}))
                    backoff = 1
                    last_ping = time.time()
                    last_msg = time.time()
                    while True:
                        if time.time() - last_ping > 5:
                            await ws.send('PING'); last_ping = time.time()
                        if time.time() - last_msg > 30:     # chien de garde (01/10 09:52) : flux RTDS tari sans fermeture observé à 09:31
                            raise RuntimeError('RTDS silencieux depuis 30 s')
                        try:
                            msg = await asyncio.wait_for(ws.recv(), timeout=0.2)
                            t_ns = time.time_ns()
                            last_msg = time.time()
                            if msg.startswith('{'):
                                p = json.loads(msg).get('payload') or {}
                                h = p.get('transactionHash')
                                if h and h not in self.done and int(p.get('timestamp', 0)) > self.backfill_to:
                                    self.tx.setdefault(h, [t_ns, []])[1].append((t_ns, p))
                                    if p.get('fee') is not None:
                                        self.handle_tx(h)
                        except asyncio.TimeoutError:
                            pass
                        now = time.time_ns()
                        for h in [h for h, v in self.tx.items() if now - v[0] > 1_000_000_000]:
                            self.handle_tx(h)
                        if time.time() - last_stat > 600:
                            jlog(os.path.join(LIVE, 'listener.log.jsonl'), dict(t_ns=time.time_ns(), event='etat', alertes=self.n_alerts, preneurs=dict(self.stats)))
                            last_stat = time.time()
            except Exception as ex:
                jlog(os.path.join(LIVE, 'listener.log.jsonl'), dict(t_ns=time.time_ns(), event='erreur_ws', err=repr(ex)[:200]))
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60)


if __name__ == '__main__':
    asyncio.run(Listener().run())
