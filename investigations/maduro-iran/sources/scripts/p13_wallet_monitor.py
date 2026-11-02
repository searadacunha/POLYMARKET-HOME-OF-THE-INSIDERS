#!/usr/bin/env python3
"""Phase 13 : comparaison des sources publiques d'identification du wallet (PROTOCOLE_P13 §2). Lecture seule, aucun ordre.
Pendant une même fenêtre, sur les mêmes marchés :
  référence  : websocket « market » du CLOB (last_trade_price : heure d'échange ms + hash)
  RTDS       : wss://ws-live-data.polymarket.com (activity/trades)
  chaîne     : eth_subscribe logs OrderFilled v2 sur deux fournisseurs RPC publics (si disponibles)
  data-api   : /trades?market= interrogé en boucle sur les marchés les plus actifs
Sortie : donnees/brut_p13/latence_<debut>.jsonl (une ligne par source et par transaction), phase13/latency_sources.csv, latency_distribution.csv
Usage : python3 p13_wallet_monitor.py --minutes 10"""
import asyncio, json, os, sys, time, argparse, collections, glob, urllib.request
import websockets
import numpy as np, pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from p11_common import RAW as RAW11  # noqa: E402

RAW13 = os.path.expanduser('~/Documents/Crypto/enquete_maduro_iran/donnees/brut_p13')
OUT = os.path.expanduser('~/Documents/Crypto/enquete_maduro_iran/phase13/')
os.makedirs(RAW13, exist_ok=True)
TOPIC = '0xd543adfd945773f1a62f74f0ee55a5e3b9b1a28262980ba90b1a89f2ea84d8ee'
EX = ['0xe111180000d2663c0091e4f400237545b87b996b', '0xe2222d279d744050d28e00520010520000310f59']
SUFFIX = {}
RPCS = ['wss://polygon-bor-rpc.publicnode.com', 'wss://polygon.drpc.org', 'wss://polygon-mainnet.public.blastapi.io', 'wss://polygon.gateway.tenderly.co']


class Mon:
    def __init__(self, minutes):
        self.end = time.time() + minutes * 60
        self.first = collections.defaultdict(dict)        # tx -> source -> t_local_ns
        self.count = collections.defaultdict(collections.Counter)
        self.meta = {}                                    # tx -> infos de la référence
        self.reconnect = collections.Counter()
        self.order = collections.defaultdict(list)        # source -> ordre d'arrivée des tx
        self.block = {}
        fps = sorted(glob.glob(os.path.join(RAW11, 'meta', 'watchlist_*.json')))
        wl = json.load(open(fps[-1]))['watchlist']
        top = sorted(wl.items(), key=lambda kv: -float(kv[1].get('volume24hr') or 0))[:220]
        self.tokens = [str(t) for c, x in top for t in x['tokens']]
        self.markets = [c for c, x in top]
        self.fh = open(os.path.join(RAW13, f'latence_{int(time.time())}.jsonl'), 'a')

    def seen(self, src, tx, extra=None):
        t = time.time_ns()
        self.count[src][tx] += 1
        if src not in self.first[tx]:
            self.first[tx][src] = t
            self.order[src].append(tx)
            self.fh.write(json.dumps(dict(src=src, tx=tx, t_ns=t, **(extra or {}))) + '\n')

    async def clob(self):
        while time.time() < self.end:
            try:
                async with websockets.connect('wss://ws-subscriptions-clob.polymarket.com/ws/market', max_size=2 ** 25) as ws:
                    await ws.send(json.dumps({'assets_ids': self.tokens, 'type': 'market'}))
                    while time.time() < self.end:
                        m = await asyncio.wait_for(ws.recv(), timeout=60)
                        x = json.loads(m)
                        for e in (x if isinstance(x, list) else [x]):
                            if e.get('event_type') == 'last_trade_price' and e.get('transaction_hash'):
                                h = e['transaction_hash']
                                if h not in self.meta:
                                    self.meta[h] = dict(t_exch_ms=int(e['timestamp']), market=e['market'], asset=e['asset_id'], side=e['side'],
                                                        usd=float(e['price']) * float(e['size']))
                                self.seen('clob', h)
            except Exception:
                self.reconnect['clob'] += 1
                await asyncio.sleep(1)

    async def rtds(self):
        while time.time() < self.end:
            try:
                async with websockets.connect('wss://ws-live-data.polymarket.com', max_size=2 ** 25) as ws:
                    await ws.send(json.dumps({'action': 'subscribe', 'subscriptions': [{'topic': 'activity', 'type': 'trades'}]}))
                    last = time.time(); lp = time.time()
                    while time.time() < self.end:
                        if time.time() - lp > 5:
                            await ws.send('PING'); lp = time.time()
                        if time.time() - last > 30:
                            raise RuntimeError('silence')
                        try:
                            m = await asyncio.wait_for(ws.recv(), timeout=1)
                        except asyncio.TimeoutError:
                            continue
                        last = time.time()
                        if m.startswith('{'):
                            p = json.loads(m).get('payload') or {}
                            if p.get('transactionHash'):
                                self.seen('rtds', p['transactionHash'])
            except Exception:
                self.reconnect['rtds'] += 1
                await asyncio.sleep(1)

    async def chain(self, url, name):
        while time.time() < self.end:
            try:
                async with websockets.connect(url, max_size=2 ** 25, open_timeout=15) as ws:
                    await ws.send(json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'eth_subscribe', 'params': ['logs', {'address': EX, 'topics': [TOPIC]}]}))
                    r = json.loads(await asyncio.wait_for(ws.recv(), timeout=15))
                    if 'error' in r:
                        self.reconnect[name + ' (refus)'] += 1
                        return
                    while time.time() < self.end:
                        m = json.loads(await asyncio.wait_for(ws.recv(), timeout=60))
                        r = (m.get('params') or {}).get('result') or {}
                        h = r.get('transactionHash')
                        if h:
                            self.block[h] = int(r.get('blockNumber', '0x0'), 16)
                            self.seen(name, h)
            except Exception:
                self.reconnect[name] += 1
                await asyncio.sleep(2)

    async def dataapi(self):
        """Interroge en boucle les marchés où le carnet a vu un trade récemment (au plus 8 requêtes par seconde)."""
        loop = asyncio.get_running_loop()
        recent = collections.deque(maxlen=40)
        while time.time() < self.end:
            for h, mm in list(self.meta.items())[-40:]:
                if mm['market'] not in recent:
                    recent.append(mm['market'])
            for cid in list(recent)[-8:]:
                def q(c=cid):
                    try:
                        u = f'https://data-api.polymarket.com/trades?market={c}&limit=30&takerOnly=false'
                        return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'curl/8.4.0'}), timeout=10).read())
                    except Exception:
                        return []
                rows = await loop.run_in_executor(None, q)
                for x in rows if isinstance(rows, list) else []:
                    if x.get('transactionHash'):
                        self.seen('dataapi', x['transactionHash'])
            await asyncio.sleep(1)

    async def run(self):
        tasks = [self.clob(), self.rtds(), self.dataapi()] + [self.chain(u, 'chaine_' + u.split('//')[1].replace('.', '_')) for u in RPCS]   # un nom par fournisseur
        await asyncio.gather(*tasks)
        self.fh.close()


def analyse(m):
    rows = []
    for h, mm in m.meta.items():
        f = m.first[h]
        t_ref = f.get('clob')
        for src, t in f.items():
            if src == 'clob':
                continue
            rows.append(dict(tx=h, source=src, latence_vs_carnet_s=(t - t_ref) / 1e9, latence_vs_echange_s=t / 1e9 - mm['t_exch_ms'] / 1e3, **mm,
                             bloc=m.block.get(h), doublons=m.count[src][h] - 1))
    D = pd.DataFrame(rows)
    n_ref = len(m.meta)
    srcs = sorted(set(D.source)) if len(D) else []
    out = []
    for s in srcs:
        x = D[D.source == s]
        q = x.latence_vs_carnet_s
        order = [h for h in m.order[s] if h in m.meta]
        ref_rank = {h: i for i, h in enumerate(m.order['clob'])}
        inv = sum(1 for a, b in zip(order, order[1:]) if ref_rank.get(a, 0) > ref_rank.get(b, 0))
        out.append(dict(source=s, trades_reference=n_ref, vus=len(x), pertes=1 - len(x) / max(n_ref, 1), P10=q.quantile(.1), P50=q.quantile(.5), P90=q.quantile(.9),
                        P99=q.quantile(.99), max=q.max(), moyenne=q.mean(), doublons=int(x.doublons.sum()), inversions_ordre=inv, reconnexions=m.reconnect.get(s, 0)))
    for k, v in m.reconnect.items():
        if k not in srcs:
            out.append(dict(source=k, reconnexions=v, vus=0))
    S = pd.DataFrame(out)
    S.to_csv(OUT + SUFFIX.get('sources', 'latency_sources.csv'), index=False)
    if len(D):
        D['taille'] = pd.cut(D.usd, [0, 100, 1000, 1e12], labels=['< 100 $', '100-1 000 $', '>= 1 000 $'])
        blk = D.groupby('bloc').tx.nunique()
        D['trades_meme_bloc'] = D.bloc.map(blk)
        D['minute'] = (D.t_exch_ms // 60000).astype(int)
        cats = []
        for cat in ('taille', 'side', 'market', 'minute', 'trades_meme_bloc'):
            for (s, v), x in D.groupby(['source', cat], observed=True):
                q = x.latence_vs_carnet_s
                cats.append(dict(source=s, categorie=cat, valeur=str(v), n=len(x), P10=q.quantile(.1), P50=q.median(), P90=q.quantile(.9), P99=q.quantile(.99)))
        pd.DataFrame(cats).to_csv(OUT + SUFFIX.get('distribution', 'latency_distribution.csv'), index=False)
        D.to_csv(OUT + SUFFIX.get('detail', 'latency_detail.csv'), index=False)
    print(S.round(3).to_string())


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--minutes', type=float, default=10)
    ap.add_argument('--suffixe', default='')
    a = ap.parse_args()
    if a.suffixe:
        SUFFIX.update(sources=f'latency_sources_{a.suffixe}.csv', distribution=f'latency_distribution_{a.suffixe}.csv', detail=f'latency_detail_{a.suffixe}.csv')
    m = Mon(a.minutes)
    asyncio.run(m.run())
    analyse(m)
