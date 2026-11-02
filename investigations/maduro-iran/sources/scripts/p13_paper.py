#!/usr/bin/env python3
"""Phase 13 : paper trading de SIG_HIST V1 par la voie la plus rapide (PROTOCOLE_P13 §9). PAPER ONLY : aucun ordre, aucune transaction.
Processus séparé des phases 11 et 12 : il lit le cache de rattrapage de la phase 11 sans l'écrire, et n'écrit que dans donnees/brut_p13/.
  1. Détecteur V1 (p9_detector) réchauffé : historique phase 9 + rattrapage (cache phase 11 en lecture, incrément dans brut_p13/).
  2. Deux sources d'identification en parallèle, la première arrivée compte :
       chaîne : logs OrderFilled v2 (nœud Polygon public) filtrés sur les wallets de la watchlist ; le fill de l'ordre preneur (taker = contrat)
                donne le wallet, le jeton, le côté, le prix et la taille, avant RTDS dans la plupart des cas ;
       RTDS   : tous les trades (état du marché pour SIG_HIST : prix de référence, mouvement des 10 min, historique des wallets).
  3. À chaque alerte SIG_HIST V1 (et à chaque achat >= 250 $ d'un wallet de la watchlist, journal secondaire) : entrée papier sur le carnet REST
     au moment de la détection (50 à 1 000 $), sorties papier à +60 et +300 s, frais du marché.
Journaux : donnees/brut_p13/paper_alerts.jsonl, paper_exits.jsonl, paper_etat.jsonl"""
import asyncio, json, os, sys, time, gzip, glob, heapq, math, collections, concurrent.futures as cf, urllib.request
import numpy as np, pandas as pd
import websockets

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p11_common import RAW as RAW11, DATA, excluded, category, get  # noqa: E402
from p11_signal_listener import Meta, to_trade, fetch_window  # noqa: E402  (fonctions sans écriture)
from p9_detector import Detecteur  # noqa: E402

RAW13 = os.path.expanduser('~/Documents/Crypto/enquete_maduro_iran/donnees/brut_p13')
os.makedirs(os.path.join(RAW13, 'backfill'), exist_ok=True)
TOPIC = '0xd543adfd945773f1a62f74f0ee55a5e3b9b1a28262980ba90b1a89f2ea84d8ee'
EX = ['0xe111180000d2663c0091e4f400237545b87b996b', '0xe2222d279d744050d28e00520010520000310f59']
SIZES = [50, 100, 250, 500, 1000]


def jlog(name, obj):
    with open(os.path.join(RAW13, name), 'a') as f:
        f.write(json.dumps(obj, ensure_ascii=False, default=str) + '\n')


def books(tokens):
    try:
        req = urllib.request.Request('https://clob.polymarket.com/books', data=json.dumps([{'token_id': t} for t in tokens]).encode(),
                                     headers={'User-Agent': 'curl/8.4.0', 'Content-Type': 'application/json'})
        return {b['asset_id']: b for b in json.loads(urllib.request.urlopen(req, timeout=5).read())}
    except Exception:
        return {}


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


class Paper:
    def __init__(self):
        self.meta = Meta()
        self.det = None
        self.tok_info = {}            # token -> (cid, outcomeIndex)
        self.done = collections.OrderedDict()
        self.tx = {}
        self.pool = cf.ThreadPoolExecutor(50)       # une alerte occupe un fil 300 s (sorties papier)
        self.n = 0

    def warm(self):
        t = time.time()
        self.meta.load_lists()
        for c, x in self.meta.m.items():
            for i, tk in enumerate(x.get('tokens') or []):
                self.tok_info[str(tk)] = (c, i)
        det = Detecteur(differe=True)
        P = pd.read_pickle(os.path.join(DATA, 'p9', 'prints.pkl'))        # pickle local (phase 9)
        last = int(P.ts.max())
        det.rejouer(P, log_every=0)
        det.lignes = []
        rows = []
        files = sorted(glob.glob(os.path.join(RAW11, 'backfill', f'backfill_{last + 1}_*.jsonl.gz')), key=lambda f: int(f.split('_')[-1].split('.')[0]))
        to = last
        for fp in files:                                             # lecture seule du cache de la phase 11
            for l in gzip.open(fp, 'rt'):
                rows += json.loads(l)['rows']
            to = int(fp.split('_')[-1].split('.')[0])
        now = int(time.time())
        cids = [c for c, x in self.meta.m.items() if not x['excl']]
        with cf.ThreadPoolExecutor(8) as ex:                         # incrément depuis le cache, stocké dans brut_p13
            inc = []
            for r in ex.map(lambda c: fetch_window(c, to + 1, now), cids):
                inc += r or []
        with gzip.open(os.path.join(RAW13, 'backfill', f'increment_{to + 1}_{now}.jsonl.gz'), 'wt') as f:
            f.write(json.dumps(inc))
        rows += inc
        rows.sort(key=lambda r: (int(r['timestamp']), r['transactionHash']))
        for k, r in enumerate(rows):
            if self.meta.m.get(r['conditionId'], {}).get('excl'):
                continue
            det.traiter(to_trade(r, self.meta, -1 - k)); det.lignes = []
        det.differe = False
        self.det = det
        self.backfill_to = now
        self.watch = sorted(w for w, h in det.hist.items() if h[0] >= 5 and (h[1] + 10 * det.p0) / (h[0] + 10) >= det.hthr)
        jlog('paper_etat.jsonl', dict(t_ns=time.time_ns(), event='pret', wallets_watchlist=len(self.watch), duree_s=round(time.time() - t), paper_only=True))
        print('prêt', len(self.watch), 'wallets', round(time.time() - t), 's', flush=True)

    def eligible(self, w):
        h = self.det.hist.get(w)
        return bool(h and h[0] >= 5 and (h[1] + 10 * self.det.p0) / (h[0] + 10) >= self.det.hthr)

    # ------------------------------------------------ traitement d'un trade identifié
    def process(self, trade, source, t_detect, tx):
        if tx in self.done:
            return
        self.done[tx] = (source, t_detect)
        if len(self.done) > 300000:
            self.done.popitem(last=False)
        E = self.det.traiter(trade)
        w = trade['wallet']
        sig = bool(len(E) and E.SIG_HIST.any())
        if sig or (w in self.watch_set and trade['side'] == 'BUY' and trade['usd'] >= 250):
            self.n += 1
            aid = f'P{self.n}_{t_detect}'
            rec = dict(alert_id=aid, type='SIG_HIST_V1' if sig else 'WATCHLIST_ACHAT_250', source_detection=source, T_DETECT_ns=t_detect, T_calcul_ns=time.time_ns(),
                       tx=tx, wallet=w, market=trade['cid'], token=trade['asset'], prix_wallet=trade['price'], usd=trade['usd'], paper_only=True)
            if sig:
                e = E[E.SIG_HIST].iloc[0]
                rec.update(hist_n=int(e.hist_n), hist_score=float(e.hist_score), p_before=float(e.p_before))
            self.pool.submit(self.paper_entry, rec)

    def paper_entry(self, rec):
        t1 = time.time_ns()
        b = books([rec['token']]).get(rec['token'])
        rec['T_carnet_ns'] = time.time_ns()
        rec['latence_carnet_ms'] = (rec['T_carnet_ns'] - t1) / 1e6
        if not b or not b.get('asks'):
            rec['entree'] = None; jlog('paper_alerts.jsonl', rec); return
        asks = sorted((float(x['price']), float(x['size'])) for x in b['asks'])
        bids = sorted(((float(x['price']), float(x['size'])) for x in b['bids']), reverse=True)
        x = self.meta.m.get(rec['market'], {})
        rec.update(best_ask=asks[0][0], best_bid=bids[0][0] if bids else None)
        ent = {}
        for S in SIZES:
            sh, val, rest = walk(asks, dollars=S)
            if sh > 0:
                ent[S] = dict(actions=sh, cout=val, vwap=val / sh, restant=rest)
        rec['entree'] = ent
        jlog('paper_alerts.jsonl', rec)
        for H in (60, 300):
            time.sleep(max(0, (rec['T_carnet_ns'] + H * 10 ** 9 - time.time_ns()) / 1e9)) if H == 60 else time.sleep(240)
            bx = books([rec['token']]).get(rec['token'])
            if not bx:
                continue
            bb = sorted(((float(y['price']), float(y['size'])) for y in bx['bids']), reverse=True)
            out = {}
            for S, e in ent.items():
                q, got, left = walk(bb, shares=e['actions'])
                out[S] = dict(produit=got, invendu=left, brut=(got - e['cout']) / e['cout'])
            jlog('paper_exits.jsonl', dict(alert_id=rec['alert_id'], horizon_s=H, t_ns=time.time_ns(), sorties=out, frais_note='frais appliqués à l analyse (feeSchedule du marché)'))

    # ------------------------------------------------ sources
    def from_chain(self, r, t):
        """Fill de l'ordre preneur (taker = contrat d'échange) d'un wallet de la watchlist -> trade identifié."""
        tp = r.get('topics') or []
        if len(tp) < 4 or tp[3][-40:].lower() not in [e[-40:] for e in EX]:
            return
        w = '0x' + tp[2][-40:].lower()
        d = r['data'][2:]
        v = [int(d[i:i + 64], 16) for i in range(0, len(d), 64)]
        side = 'BUY' if v[0] == 0 else 'SELL'
        tok = str(v[1])
        mk, tk = v[2] / 1e6, v[3] / 1e6
        price = (mk / tk) if side == 'BUY' and tk else ((tk / mk) if mk else None)
        info = self.tok_info.get(tok)
        if price is None or info is None:
            return
        cid, oi = info
        x = self.meta.m.get(cid, {})
        if x.get('excl'):
            return
        usd = mk if side == 'BUY' else tk
        trade = dict(ts=int(t / 1e9), cid=cid, cat=x.get('cat'), end=x.get('end'), wallet=w, side=side, asset=tok, price=price, usd=usd, oi=oi, rid=-1)
        if usd >= 100:
            self.process(trade, 'chaine', t, r['transactionHash'])

    def handle_rtds_tx(self, h):
        t_ns, rows = self.tx.pop(h)
        if h in self.done:
            return
        fee_rows = [(t, r) for t, r in rows if r.get('fee') is not None]
        takers = fee_rows[:1] if len(fee_rows) == 1 else (rows if len(rows) == 1 else rows[:1])
        for t, r in takers:
            x = self.meta.get(r['conditionId'])
            if x is None or x.get('excl'):
                continue
            usd = float(r['price']) * float(r['size'])
            if usd >= 100:
                self.process(to_trade(r, self.meta, -1), 'rtds', t, h)

    async def chain(self):
        while True:
            try:
                makers = ['0x' + '0' * 24 + w[2:] for w in self.watch]
                async with websockets.connect('wss://polygon-bor-rpc.publicnode.com', max_size=2 ** 25, open_timeout=20, ping_interval=20) as ws:
                    await ws.send(json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'eth_subscribe', 'params': ['logs', {'address': EX, 'topics': [TOPIC, None, makers]}]}))
                    while True:
                        m = json.loads(await asyncio.wait_for(ws.recv(), timeout=600))
                        r = (m.get('params') or {}).get('result')
                        if isinstance(r, dict) and r.get('transactionHash'):
                            self.from_chain(r, time.time_ns())
            except Exception as ex:
                jlog('paper_etat.jsonl', dict(t_ns=time.time_ns(), event='erreur_chaine', err=repr(ex)[:150]))
                await asyncio.sleep(3)

    async def rtds(self):
        while True:
            try:
                async with websockets.connect('wss://ws-live-data.polymarket.com', max_size=2 ** 25) as ws:
                    await ws.send(json.dumps({'action': 'subscribe', 'subscriptions': [{'topic': 'activity', 'type': 'trades'}]}))
                    lp = lm = time.time()
                    while True:
                        if time.time() - lp > 5:
                            await ws.send('PING'); lp = time.time()
                        if time.time() - lm > 30:
                            raise RuntimeError('RTDS silencieux')
                        try:
                            m = await asyncio.wait_for(ws.recv(), timeout=0.2)
                            lm = time.time()
                            if m.startswith('{'):
                                p = json.loads(m).get('payload') or {}
                                h = p.get('transactionHash')
                                if h and int(p.get('timestamp', 0)) > self.backfill_to and h not in self.done:
                                    self.tx.setdefault(h, [time.time_ns(), []])[1].append((time.time_ns(), p))
                                    if p.get('fee') is not None:
                                        self.handle_rtds_tx(h)
                        except asyncio.TimeoutError:
                            pass
                        now = time.time_ns()
                        for h in [h for h, v in self.tx.items() if now - v[0] > 10 ** 9]:
                            self.handle_rtds_tx(h)
            except Exception as ex:
                jlog('paper_etat.jsonl', dict(t_ns=time.time_ns(), event='erreur_rtds', err=repr(ex)[:150]))
                await asyncio.sleep(2)

    async def main(self):
        await asyncio.get_running_loop().run_in_executor(None, self.warm)
        self.watch_set = set(self.watch)
        await asyncio.gather(self.chain(), self.rtds())


if __name__ == '__main__':
    asyncio.run(Paper().main())
