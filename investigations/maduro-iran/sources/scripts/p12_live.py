#!/usr/bin/env python3
"""Phase 12 : journal PAPER ONLY du détecteur sans wallet, en direct (PROTOCOLE_P12 §6.6). Aucun ordre, aucune transaction.
Processus séparé de la phase 11 : ses propres connexions au websocket « market », lecture seule du marché ; il n'écrit que dans
donnees/brut_p12/. Marchés suivis : la dernière watchlist de la phase 11 (plus ses ajouts dynamiques), relue toutes les heures.
Pour chaque signal (B2 AGGRESSIVE_FLOW, B1 PRE_REPRICING_FLOW) et chaque candidat B2 non signalé :
  live_signals.jsonl : timestamp, market, token, direction, pre_wallet_score, signal_type, expected_entry (best ask, VWAP 250 $)
  live_suivi.jsonl   : prix futur réel (mid, best bid, best ask) à +1, 5, 10, 30, 60, 120, 300 s
Usage : python3 p12_live.py   (via p12_run.sh)"""
import asyncio, json, os, sys, time, glob, heapq
import websockets

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p11_common import RAW as RAW11  # noqa: E402
from p12_pre_wallet_detector import PreWalletDetector  # noqa: E402

RAW12 = os.path.expanduser('~/Documents/Crypto/enquete_maduro_iran/donnees/brut_p12')
os.makedirs(RAW12, exist_ok=True)
CHECK = [1, 5, 10, 30, 60, 120, 300]


def jlog(name, obj):
    with open(os.path.join(RAW12, name), 'a') as f:
        f.write(json.dumps(obj, ensure_ascii=False, default=str) + '\n')


def watchlist():
    fps = sorted(glob.glob(os.path.join(RAW11, 'meta', 'watchlist_*.json')))
    wl = json.load(open(fps[-1]))['watchlist'] if fps else {}
    tok = {c: [str(t) for t in x['tokens']] for c, x in wl.items()}
    fp = os.path.join(RAW11, 'meta', 'dynamic_watch.jsonl')
    if os.path.exists(fp):
        for l in open(fp):
            d = json.loads(l)
            tok.setdefault(d['cid'], [str(t) for t in d['tokens']])
    return tok


class Live:
    def __init__(self):
        self.tok = watchlist()
        self.det = PreWalletDetector(self.tok)
        self.tasks = []
        self.seq = 0
        self.last_b1 = {}
        self.n = 0

    def follow(self, sid, s, t):
        for k in CHECK:
            self.seq += 1
            heapq.heappush(self.tasks, (t + k * 10 ** 9, self.seq, sid, s, k))

    def run_due(self):
        now = time.time_ns()
        while self.tasks and self.tasks[0][0] <= now:
            _, _, sid, s, k = heapq.heappop(self.tasks)
            m = self.det.asset_market.get(s['token'])
            b = self.det.mk[m].books[s['token']] if m else None
            if b and b['asks'] and b['bids']:
                ba, bb = min(b['asks']), max(b['bids'])
                jlog('live_suivi.jsonl', dict(signal_id=sid, offset_s=k, t_ns=now, best_ask=ba, best_bid=bb, mid=(ba + bb) / 2))

    def handle(self, t, msg):
        try:
            x = json.loads(msg)
        except Exception:
            return
        for e in (x if isinstance(x, list) else [x]):
            for s in self.det.on_event(t, e):
                if s['signal_type'] == 'PRE_REPRICING_FLOW':
                    key = (s['market'], s['token'])
                    if t - self.last_b1.get(key, 0) < 60 * 10 ** 9:
                        continue
                    self.last_b1[key] = t
                self.n += 1
                sid = f'S{self.n}_{t}'
                rec = {k: v for k, v in s.items() if k != 'features'}
                rec.update(signal_id=sid, paper_only=True)
                jlog('live_signals.jsonl', rec)
                self.follow(sid, s, t)

    async def conn(self, tokens, k):
        backoff = 1
        while True:
            try:
                async with websockets.connect('wss://ws-subscriptions-clob.polymarket.com/ws/market', max_size=2 ** 25, ping_interval=20) as ws:
                    await ws.send(json.dumps({'assets_ids': tokens, 'type': 'market', 'custom_feature_enabled': True}))
                    jlog('etat.jsonl', dict(t_ns=time.time_ns(), event='abonnement', conn=k, n_tokens=len(tokens)))
                    backoff = 1
                    while True:
                        msg = await asyncio.wait_for(ws.recv(), timeout=120)
                        self.handle(time.time_ns(), msg)
            except Exception as ex:
                jlog('etat.jsonl', dict(t_ns=time.time_ns(), event='erreur', conn=k, err=repr(ex)[:200]))
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60)

    async def ticker(self):
        while True:
            self.run_due()
            await asyncio.sleep(0.2)

    async def main(self):
        toks = [t for c in sorted(self.tok) for t in self.tok[c]]
        jlog('etat.jsonl', dict(t_ns=time.time_ns(), event='demarrage', marches=len(self.tok), jetons=len(toks), paper_only=True))
        tasks = [asyncio.create_task(self.conn(toks[i:i + 480], i // 480)) for i in range(0, len(toks), 480)]
        tasks.append(asyncio.create_task(self.ticker()))
        await asyncio.sleep(3600)                         # relecture horaire de la watchlist : on repart proprement
        for t in tasks:
            t.cancel()


if __name__ == '__main__':
    while True:
        if os.path.exists(os.path.join(RAW12, 'STOP')):
            break
        asyncio.run(Live().main())
