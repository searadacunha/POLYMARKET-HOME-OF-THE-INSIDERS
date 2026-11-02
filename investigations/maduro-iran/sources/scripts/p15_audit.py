#!/usr/bin/env python3
"""Phase 15 : audit de couverture et de détection (PROTOCOLE_P15). AUDIT UNIQUEMENT : aucune décision, aucun ordre, SIG_HIST V1 non modifié.
Ne touche à aucun processus des phases 11 à 14 ; relit seulement leurs fichiers.
  --live --heures N : enregistreur indépendant -> donnees/brut_p15/
        RTDS A (continue) et RTDS B (coupée volontairement 30 s toutes les 20 min), chien de garde 30 s comme en production ;
        logs OrderFilled v2 non filtrés + en-têtes de blocs (publicnode) ; trous d'en-têtes rattrapés par eth_getLogs.
  --analyse         : tables phase15/*.csv (voir RAPPORT_PHASE15.md)"""
import asyncio, json, os, sys, time, gzip, argparse, threading, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.expanduser('~/Documents/Crypto/enquete_maduro_iran')
RAW15 = os.path.join(ROOT, 'donnees', 'brut_p15')
OUT = os.path.join(ROOT, 'phase15') + '/'
TOPIC = '0xd543adfd945773f1a62f74f0ee55a5e3b9b1a28262980ba90b1a89f2ea84d8ee'
EX = ['0xe111180000d2663c0091e4f400237545b87b996b', '0xe2222d279d744050d28e00520010520000310f59']
WSS_CHAIN = 'wss://polygon-bor-rpc.publicnode.com'
HTTP_CHAIN = 'https://polygon-bor-rpc.publicnode.com'
os.makedirs(RAW15, exist_ok=True)


class Sink:
    """jsonl.gz par heure et par flux ; une ligne = liste [t_local_ns, ...]."""
    def __init__(self, kind):
        self.kind, self.hour, self.f = kind, None, None
        self.lock = threading.Lock()
        self.n = 0

    def write(self, row):
        with self.lock:
            h = time.strftime('%Y%m%dT%H', time.gmtime())
            if h != self.hour:
                if self.f:
                    self.f.close()
                k = 0
                fn = os.path.join(RAW15, f'{self.kind}_{h}.jsonl.gz')
                while os.path.exists(fn):
                    k += 1; fn = os.path.join(RAW15, f'{self.kind}_{h}.{k}.jsonl.gz')
                self.f = gzip.open(fn, 'at', compresslevel=5)
                self.hour = h
            self.f.write(json.dumps(row, separators=(',', ':')) + '\n')
            self.n += 1
            if self.n % 2000 == 0 or self.kind == 'evenements':
                self.f.flush()

    def close(self):
        with self.lock:
            if self.f:
                self.f.close()


def http_rpc(method, params):
    req = urllib.request.Request(HTTP_CHAIN, data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}).encode(),
                                 headers={'Content-Type': 'application/json', 'User-Agent': 'curl/8.4.0'})
    return json.loads(urllib.request.urlopen(req, timeout=60).read()).get('result')


class Live:
    def __init__(self, heures):
        self.end = time.time() + heures * 3600
        self.rt = Sink('rtds')
        self.ch = Sink('chain')
        self.ev = Sink('evenements')
        self.cnt = {'A': 0, 'B': 0, 'log': 0, 'head': 0, 'backfill': 0}
        self.last_head = None

    def event(self, **kw):
        self.ev.write([time.time_ns(), kw])

    async def rtds(self, name, drop_every=None):
        next_drop = time.time() + drop_every if drop_every else None
        while time.time() < self.end:
            try:
                import websockets
                async with websockets.connect('wss://ws-live-data.polymarket.com', max_size=2 ** 25, ping_interval=None) as ws:
                    await ws.send(json.dumps({'action': 'subscribe', 'subscriptions': [{'topic': 'activity', 'type': 'trades'}]}))
                    self.event(src=f'rtds_{name}', ev='connexion')
                    lp = lm = time.time()
                    while time.time() < self.end:
                        if time.time() - lp > 5:
                            await ws.send('PING'); lp = time.time()
                        if time.time() - lm > 30:
                            raise RuntimeError('silence 30 s')
                        if next_drop and time.time() >= next_drop:
                            next_drop = time.time() + drop_every
                            raise ConnectionAbortedError('coupure volontaire 30 s (test §19)')
                        try:
                            m = await asyncio.wait_for(ws.recv(), timeout=1)
                        except asyncio.TimeoutError:
                            continue
                        t = time.time_ns()
                        lm = time.time()
                        if not m.startswith('{'):
                            continue
                        p = json.loads(m).get('payload') or {}
                        if not p.get('transactionHash'):
                            continue
                        self.cnt[name] += 1
                        self.rt.write([t, name, p.get('transactionHash'), str(p.get('asset')), p.get('conditionId'), (p.get('proxyWallet') or '').lower(), p.get('side'),
                                       p.get('outcomeIndex'), p.get('price'), p.get('size'), p.get('timestamp'), p.get('fee'), p.get('slug'), p.get('outcome')])
            except Exception as ex:
                vol = isinstance(ex, ConnectionAbortedError)
                self.event(src=f'rtds_{name}', ev='coupure_volontaire' if vol else 'erreur', err=repr(ex)[:150])
                await asyncio.sleep(30 if vol else 2)
                self.event(src=f'rtds_{name}', ev='reconnexion')

    def backfill(self, b0, b1):
        """Rattrapage des logs des blocs manqués (b0..b1 inclus) par eth_getLogs ; prouve si la chaîne est récupérable."""
        try:
            for a in range(b0, b1 + 1, 50):
                z = min(b1, a + 49)
                logs = http_rpc('eth_getLogs', [{'fromBlock': hex(a), 'toBlock': hex(z), 'address': EX, 'topics': [TOPIC]}]) or []
                t = time.time_ns()
                for r in logs:
                    self.cnt['backfill'] += 1
                    self.ch.write([t, 'backfill', r['transactionHash'], int(r['blockNumber'], 16), int(r['logIndex'], 16), r['topics'], r['data']])
            self.event(src='chaine', ev='rattrapage', de=b0, a=b1, ok=True)
        except Exception as ex:
            self.event(src='chaine', ev='rattrapage', de=b0, a=b1, ok=False, err=repr(ex)[:150])

    async def chain(self):
        loop = asyncio.get_running_loop()
        while time.time() < self.end:
            try:
                import websockets
                async with websockets.connect(WSS_CHAIN, max_size=2 ** 25, open_timeout=20, ping_interval=20) as ws:
                    await ws.send(json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'eth_subscribe', 'params': ['logs', {'address': EX, 'topics': [TOPIC]}]}))
                    await ws.send(json.dumps({'jsonrpc': '2.0', 'id': 2, 'method': 'eth_subscribe', 'params': ['newHeads']}))
                    self.event(src='chaine', ev='connexion')
                    while time.time() < self.end:
                        m = json.loads(await asyncio.wait_for(ws.recv(), timeout=60))
                        t = time.time_ns()
                        r = (m.get('params') or {}).get('result')
                        if not isinstance(r, dict):
                            continue
                        if 'topics' in r:
                            self.cnt['log'] += 1
                            self.ch.write([t, 'log', r['transactionHash'], int(r['blockNumber'], 16), int(r['logIndex'], 16), r['topics'], r['data']])
                        elif 'number' in r:
                            n = int(r['number'], 16)
                            self.cnt['head'] += 1
                            self.ch.write([t, 'head', n, int(r['timestamp'], 16)])
                            if self.last_head is not None and n > self.last_head + 1:
                                self.event(src='chaine', ev='trou_entetes', de=self.last_head + 1, a=n - 1)
                                loop.run_in_executor(None, self.backfill, self.last_head + 1, n - 1)
                            self.last_head = max(n, self.last_head or 0)
            except Exception as ex:
                self.event(src='chaine', ev='erreur', err=repr(ex)[:150])
                await asyncio.sleep(2)

    async def heartbeat(self):
        while time.time() < self.end:
            await asyncio.sleep(60)
            self.event(src='audit', ev='etat', **self.cnt)

    async def main(self):
        self.event(src='audit', ev='demarrage', fin=self.end, paper_only=True)
        await asyncio.gather(self.rtds('A'), self.rtds('B', drop_every=1200), self.chain(), self.heartbeat())
        self.event(src='audit', ev='fin', **self.cnt)
        for s in (self.rt, self.ch, self.ev):
            s.close()


def fusion():
    """Tables finales : période P11 (p15_historique.py) + audit live (p15_analyse.py) ; taux mesurés ; rejeu des alertes SIG_HIST."""
    import pandas as pd
    def cat(names, out):
        parts = []
        for n, per in names:
            fp = OUT + n
            if os.path.exists(fp):
                d = pd.read_csv(fp, low_memory=False)
                if 'periode' not in d.columns:
                    d.insert(0, 'periode', per)
                parts.append(d)
        if parts:
            pd.concat(parts, ignore_index=True).to_csv(OUT + out, index=False)
    cat([('phase15_duplicates_live.csv', 'audit live'), ('phase15_duplicates_p11.csv', 'P11')], 'phase15_duplicates.csv')
    cat([('phase15_end_to_end_live.csv', 'audit live'), ('phase15_end_to_end_p11.csv', 'P11')], 'phase15_end_to_end.csv')
    cat([('phase15_reconnect_live.csv', 'audit live'), ('phase15_trous_p11.csv', 'P11')], 'phase15_reconnect.csv')
    cat([('phase15_latency_live.csv', 'audit live'), ('phase15_latency_p11.csv', 'P11')], 'phase15_latency.csv')
    cat([('phase15_trade_coverage_live.csv', 'audit live'), ('phase15_trade_coverage_p11.csv', 'P11')], 'phase15_trade_coverage.csv')
    live = json.load(open(OUT + 'phase15_live_resume.json'))
    hist = json.load(open(OUT + 'phase15_historique_resume.json'))
    taux = dict(rappel_rtds_une_connexion=live['rappel_p11_rtds'], rappel_rtds_connexion_continue_A=live['rappel_A'],
                part_cid_vide_univers_achats_250=hist['champs_rtds']['univers_live_achats_250_part_cid_vide'],
                part_volume_marches_abonnes=hist['couverture_marches']['part_volume_preneur_univers_sur_marches_abonnes'])
    json.dump(taux, open(OUT + 'phase15_taux_mesures.json', 'w'), indent=1)
    from p15_historique import sig_hist_replay
    r = sig_hist_replay(taux)
    json.dump(r, open(OUT + 'phase15_sig_hist_resume.json', 'w'), indent=1, default=str, ensure_ascii=False)
    print(json.dumps(r, indent=1, default=str, ensure_ascii=False))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--live', action='store_true')
    ap.add_argument('--heures', type=float, default=3)
    ap.add_argument('--analyse', action='store_true')
    ap.add_argument('--fusion', action='store_true')
    a = ap.parse_args()
    if a.live:
        asyncio.run(Live(a.heures).main())
    if a.analyse:
        from p15_analyse import main as analyse
        analyse()
    if a.fusion:
        fusion()
