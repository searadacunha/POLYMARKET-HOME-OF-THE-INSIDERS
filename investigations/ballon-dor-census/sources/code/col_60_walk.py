"""Budgeted walk around each Polymarket wallet, upstream of its deposits and downstream of its withdrawals.

Rules fixed before reading the results (PROTOCOL.md):
- Only personal-sized addresses are expanded. A stop always writes its reason: label, contract, nonce >= 1000, >= 400 counterparties.
- At most HOPS hops, NODES nodes per account and direction, TOP edges per node. Hitting a budget is written, never hidden.
- Cross-chain links only from a protocol record (Relay) or the chain. Never from a similar amount or a close date.
- Keys: all exits from 30 days before the first deposit, not only after the first withdrawal.
- Every personal address met is tested for its own Polymarket deposit wallet (CREATE2 + user-stats).

Failures raise for the node, are written, and the walk moves on: a node in `failed` is a hole in the record, never a zero.
"""
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import addr
import hist
import labels
import net
import seed

OUT = net.ROOT / 'derived/walk'
HOPS, NODES, TOP = int(os.environ.get('WALK_HOPS', 3)), int(os.environ.get('WALK_NODES', 45)), int(os.environ.get('WALK_TOP', 8))  # protocol values by default; the unnamed lookalikes use a smaller budget, written in PROTOCOL.md
MIN_USD = 20.0
RELAY_CAP = int(os.environ.get('WALK_RELAY_CAP', 15))  # measured: Relay answers 429 most of the time, its budget is shared with other local sessions. Each lookup beyond the cap is written in `limits`
EVM_CHAINS = (1, 137, 42161, 10)
ZERO = '0x' + '0' * 40
RELAY_CHAIN_NAMES = {1: 'ethereum', 137: 'polygon', 42161: 'arbitrum', 10: 'optimism', 8453: 'base', 56: 'bsc', 792703809: 'solana', 8253038: 'bitcoin'}
_price = {}


def price_usd(asset, ts):
    if asset in hist.USD_LIKE:
        return 1.0
    ids = {'ETH': 'ethereum', 'WETH': 'ethereum', 'POL': 'polygon-ecosystem-token', 'WPOL': 'polygon-ecosystem-token', 'SOL': 'solana', 'WSOL': 'solana', 'BNB': 'binancecoin', 'BTC': 'bitcoin', 'WBTC': 'bitcoin'}
    cid = ids.get(asset)
    if not cid:
        return None
    day = ts - ts % 86400
    k = (cid, day)
    if k not in _price:
        d = net.get(f'https://coins.llama.fi/prices/historical/{day}/coingecko:{cid}')
        _price[k] = ((d.get('coins') or {}).get(f'coingecko:{cid}') or {}).get('price')
    return _price[k]


def usd(row):
    if not row.get('recognized', True):
        return None
    p = price_usd(row['asset'], row['ts'])
    return row['amount'] * p if p is not None else None


def relay_lookup(tx, budget):
    if budget['left'] <= 0:
        budget['skipped'] += 1
        return None
    budget['left'] -= 1
    d = net.get('https://api.relay.link/requests/v2', dict(hash=tx), retries=3)
    if 'requests' not in d:
        raise net.FetchError(f'relay answer without requests for {tx}')
    return d['requests']


def relay_parties(req):
    d = req.get('data') or {}
    m = d.get('metadata') or {}
    def cur(k):
        c = m.get(k) or {}
        return dict(chain=((c.get('currency') or {}).get('chainId')), symbol=((c.get('currency') or {}).get('symbol')), amount=c.get('amountFormatted'), usd=c.get('amountUsd'))
    return dict(id=req.get('id'), status=req.get('status'), user=req.get('user'), recipient=req.get('recipient'), sender=m.get('sender'), meta_recipient=m.get('recipient'),
                in_txs=[dict(chain=t.get('chainId'), hash=t.get('hash'), ts=t.get('timestamp')) for t in d.get('inTxs') or []], out_txs=[dict(chain=t.get('chainId'), hash=t.get('hash'), ts=t.get('timestamp')) for t in d.get('outTxs') or []], cin=cur('currencyIn'), cout=cur('currencyOut'))


class Walk:
    def __init__(self, account, ledger):
        self.account = account
        self.ledger = ledger
        self.nodes, self.edges, self.failed, self.relay_records, self.polymarket_hits, self.limits = {}, [], [], {}, [], []
        self.budget = dict(left=RELAY_CAP, skipped=0)
        self.seen_edges = set()

    def classify(self, a, chain=None):
        """Service or personal-sized. Reads the label before anything costly."""
        try:
            lab = labels.lookup(a, chain)
        except net.FetchError as e:
            self.failed.append(dict(address=a, labels=True, error=str(e)[:200]))
            lab = None
        if lab and lab['category'] in ('exchange', 'instant_exchange', 'bridge', 'mixer', 'dex_or_router', 'polymarket'):
            return dict(cls='SERVICE', reason=f"label: {lab['name']}", label=lab)
        return dict(cls='UNLABELED', reason='', label=lab)

    def read(self, a):
        """Whole history on every readable chain. Returns rows + per-chain stats. A chain that fails is written as a hole."""
        rows, stats = [], {}
        if a.startswith('0x'):
            for c in EVM_CHAINS:
                try:
                    r, s = hist.evm_rows(a, c)
                except net.Pause:
                    raise
                except net.FetchError as e:
                    self.failed.append(dict(address=a, chain=c, error=str(e)[:200]))
                    continue
                rows += r
                stats[c] = s
        elif a.startswith('bc1') or (a[0] in '13' and len(a) <= 35):
            n_tx = hist.btc_info(a)['chain_stats']['tx_count']
            if n_tx >= 400:
                return [], dict(bitcoin=dict(n_tx=n_tx, complete=False, high_activity=True))
            txs, complete = hist.btc_txs(a)
            stats['bitcoin'] = dict(n_tx=len(txs), complete=complete)
            for t in txs:
                ts = (t.get('status') or {}).get('block_time') or 0
                for v in t['vout']:
                    if v.get('scriptpubkey_address') == a:
                        ins = sorted({x['prevout'].get('scriptpubkey_address') for x in t['vin'] if x.get('prevout')} - {None})
                        rows.append(dict(chain='bitcoin', tx=t['txid'], block=(t.get('status') or {}).get('block_height'), ts=ts, src=ins[0] if len(ins) == 1 else f'{len(ins)}_inputs:' + ','.join(ins[:3]), dst=a, asset='BTC', contract='', decimals=8, raw=str(v['value']), amount=v['value'] / 1e8, kind='utxo_in', recognized=True, n_inputs=len(t['vin']), inputs=ins[:20]))
                ins_a = sum(x['prevout']['value'] for x in t['vin'] if x.get('prevout') and x['prevout'].get('scriptpubkey_address') == a)
                if ins_a:
                    for v in t['vout']:
                        d = v.get('scriptpubkey_address')
                        if d and d != a:
                            rows.append(dict(chain='bitcoin', tx=t['txid'], block=(t.get('status') or {}).get('block_height'), ts=ts, src=a, dst=d, asset='BTC', contract='', decimals=8, raw=str(v['value']), amount=v['value'] / 1e8, kind='utxo_out', recognized=True, n_outputs=len(t['vout'])))
        else:
            r, s = hist.sol_rows(a)
            rows += r
            stats['solana'] = s
        return rows, stats

    def size_stop(self, a, rows, stats):
        if a.startswith('0x'):
            for c, s in stats.items():
                if (s.get('nonce_seen') or 0) >= 1000:
                    return f'nonce {s["nonce_seen"]} on chain {c}'
            cps = {r['src'] if r['dst'] == a else r['dst'] for r in rows if r.get('recognized')}
            if len(cps) >= 400:
                return f'{len(cps)} counterparties'
        else:
            n = sum(s.get('n_signatures', 0) + s.get('n_tx', 0) for s in stats.values())
            cps = {r['src'] if r['dst'] == a else r['dst'] for r in rows}
            if n >= 400 or len(cps) >= 400 or any(not s.get('complete', True) for s in stats.values()):
                return f'{n} transactions, {len(cps)} counterparties'
        return None

    def add_edge(self, r, hop, direction, parent):
        key = (r['chain'], r['tx'], r['src'], r['dst'], r['asset'], r['raw'], r['kind'])
        if key in self.seen_edges:
            return
        self.seen_edges.add(key)
        self.edges.append(dict(r, hop=hop, direction=direction, parent=parent, usd_approx=usd(r)))

    def test_polymarket(self, a):
        if not a.startswith('0x'):
            return
        for label_, candidate in (('deposit_wallet', addr.deposit_wallet(a)), ('deposit_wallet_old', addr.deposit_wallet(a, addr.TEMPLATE_OLD)), ('eoa', a)):
            try:
                d = net.get('https://data-api.polymarket.com/v2/user-stats', dict(user=candidate))
            except net.FetchError as e:
                self.failed.append(dict(address=a, polymarket_test=label_, error=str(e)[:200]))
                continue
            s = d.get('data')
            if s and (s.get('trades') or 0) > 0:
                self.polymarket_hits.append(dict(address=a, via=label_, wallet=candidate, trades=s.get('trades'), join_date=s.get('join_date'), pnl=(s.get('all_time_pnl') or {}).get('economic_pnl')))

    def relay_edges(self, r, hop, direction, parent):
        """A row touching a Relay address: ask Relay what was on the other side. Returns the far-side party, chain and record."""
        try:
            reqs = relay_lookup(r['tx'], self.budget)
        except net.FetchError as e:
            self.failed.append(dict(address=r['tx'], relay=True, error=str(e)[:200]))
            self.limits.append(f"relay lookup failed for {r['tx']}: the far side of this transfer stays unknown")
            return []
        if reqs is None:
            self.limits.append(f"relay budget spent, {r['tx']} not looked up")
            return []
        out = []
        for q in reqs:
            p = relay_parties(q)
            self.relay_records[q.get('id')] = p
            if direction == 'upstream':
                far = p['user'] or p['sender']
                out.append((far, p))
            else:
                far = p['recipient'] or p['meta_recipient']
                out.append((far, p))
        return out

    def walk(self, seeds, direction, t_from, t_to):
        """seeds: [(address, hop, parent, t_limit)]. t_limit keeps only flows that could precede (upstream) or follow (downstream) the child."""
        queue = list(seeds)
        expanded = 0
        while queue:
            a, hop, parent, t_limit = queue.pop(0)
            a = a.lower() if a.startswith('0x') else a
            # the widest window asked for this address: a later deposit must not lose its funding because an earlier seed came first
            same = [q[3] for q in queue if (q[0].lower() if q[0].startswith('0x') else q[0]) == a and q[3]]
            if same and t_limit:
                t_limit = max([t_limit] + same) if direction == 'upstream' else min([t_limit] + same)
            if (a, direction) in self.nodes:
                continue
            if expanded >= NODES:
                self.limits.append(f'{direction}: {NODES} nodes reached, {a} and {len(queue)} more not read')
                break
            info = self.classify(a)
            node = dict(address=a, hop=hop, direction=direction, parent=parent, cls=info['cls'], reason=info['reason'], label=info['label'])
            self.nodes[(a, direction)] = node
            if info['cls'] == 'SERVICE':
                continue
            expanded += 1
            try:
                rows, stats = self.read(a)
            except net.FetchError as e:
                node['cls'] = 'FAILED'
                node['reason'] = str(e)[:200]
                self.failed.append(dict(address=a, error=str(e)[:200]))
                continue
            node['stats'] = stats
            if not stats:  # no chain could be read: a hole, not an empty address
                node['cls'] = 'FAILED'
                node['reason'] = 'no chain readable'
                continue
            why = self.size_stop(a, rows, stats)
            contract = False
            if a.startswith('0x'):
                is7702 = lambda c: c.startswith('0xef0100')
                try:
                    code = net.rpc('eth_getCode', [a, 'latest'], chain=137)
                    code1 = net.rpc('eth_getCode', [a, 'latest'], chain=1)
                    contract = (code not in ('0x', None) and not is7702(code)) or (code1 not in ('0x', None) and not is7702(code1))
                except net.FetchError as e:
                    self.failed.append(dict(address=a, code=True, error=str(e)[:200]))
                    contract = False
                    node['code_unread'] = True
                node['contract'] = contract
            if contract and a != self.account['owner']:
                why = why or 'contract'
            if why:
                node['cls'], node['reason'] = 'HIGH_ACTIVITY', why
                continue
            node['cls'] = 'PERSONAL_SIZED'
            self.test_polymarket(a)
            inflow = [r for r in rows if r['dst'] == a and r.get('recognized')]
            outflow = [r for r in rows if r['src'] == a and r.get('recognized')]
            node['n_in'], node['n_out'] = len(inflow), len(outflow)
            node['first_ts'] = min((r['ts'] for r in rows if r['ts']), default=None)
            node['last_ts'] = max((r['ts'] for r in rows if r['ts']), default=None)
            node['spam_rows'] = sum(1 for r in rows if not r.get('recognized'))
            cand = inflow if direction == 'upstream' else outflow
            if direction == 'upstream':
                cand = [r for r in cand if r['ts'] <= (t_limit or t_to)]
            else:
                cand = [r for r in cand if r['ts'] >= (t_limit or t_from)]
            unpriced = sum(1 for r in cand if usd(r) is None)
            if unpriced:
                self.limits.append(f'{a}: {unpriced} {direction} edges without a price, kept and written')
            cand = [r for r in cand if (usd(r) is None or usd(r) >= MIN_USD) and r['src'] != ZERO]
            cand.sort(key=lambda r: -(usd(r) or 0))
            node['candidates'] = len(cand)
            if len(cand) > TOP:
                self.limits.append(f'{a}: {len(cand) - TOP} {direction} edges beyond the top {TOP} not followed (all rows remain in raw)')
            # every candidate is written, only the top ones are followed
            for r in cand:
                self.add_edge(r, hop, direction, a)
            if hop >= HOPS:
                node['stopped_at_hop_limit'] = True
                continue
            for r in cand[:TOP]:
                if r['chain'] == 'bitcoin' and direction == 'upstream':
                    # common inputs are read one by one, never merged into one owner
                    queue += [(x, hop + 1, a, r['ts']) for x in r.get('inputs', [])[:TOP] if x != a]
                    continue
                other = r['src'] if direction == 'upstream' else r['dst']
                if not other:
                    continue
                try:
                    lab = labels.lookup(other, r['chain'] if str(r['chain']).isdigit() else None)
                except net.FetchError as e:
                    self.failed.append(dict(address=other, labels=True, error=str(e)[:200]))
                    lab = None
                if lab and 'relay' in lab['name'].lower():
                    for far, p in self.relay_edges(r, hop, direction, a):
                        node.setdefault('relay', []).append(p)
                        if far and far.lower() != a.lower():
                            queue.append((far, hop + 1, a, r['ts']))
                else:
                    queue.append((other, hop + 1, a, r['ts']))
        return expanded


def seeds_for(wallet, led, chain, relay):
    up, down, direct = [], [], []
    for tx, fl in chain['flows'].items():
        rec = relay.get(tx, {}).get('requests') or []
        parties = [relay_parties(q) for q in rec]
        logs = [(l['address'].lower(), '0x' + l['topics'][1][-40:], '0x' + l['topics'][2][-40:], int(l['data'], 16)) for l in fl['receipt']['logs'] if l['topics'][0] == '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef' and len(l['topics']) == 3 and l['data'] != '0x']
        usdce = [t for t in logs if t[0] == '0x2791bca1f2de4661ed88a30c99a7a9449aa84174']
        if not usdce:  # direct pUSD movement, no USDC.e leg
            usdce = [t for t in logs if t[0] == '0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb' and ZERO not in (t[1], t[2])]
        entry = dict(tx=tx, type=fl['type'], usdc=fl['usdc'], ts=fl['ts'], first_sender=usdce[0][1] if usdce else None, last_receiver=usdce[-1][2] if usdce else None, relay=parties)
        direct.append(entry)
        if fl['type'] == 'DEPOSIT':
            if parties:
                for p in parties:
                    for far in (p['user'], p['sender']):
                        if far:
                            up.append((far, 1, wallet, fl['ts']))
            elif usdce:
                up.append((usdce[0][1], 1, wallet, fl['ts']))
        else:
            if parties:
                for p in parties:
                    far = p['recipient'] or p['meta_recipient']
                    if far:
                        down.append((far, 1, wallet, fl['ts']))
            elif usdce:
                down.append((usdce[-1][2], 1, wallet, fl['ts']))
    return up, down, direct


def main():
    OUT.mkdir(exist_ok=True)
    ledger = json.load(open(net.ROOT / 'derived/ledger.json'))
    relay = json.load(open(net.ROOT / 'derived/relay.json'))
    only = sys.argv[1:]
    order = sorted(ledger, key=lambda w: (not any(l.startswith('irboz') for l in ledger[w]['labels']), w))
    for w in order:
        if only and w not in only:
            continue
        path = OUT / f'{w}.json'
        if path.exists() and (not only or os.environ.get('WALK_SKIP_DONE')):
            continue
        led = ledger[w]
        chain = json.load(open(net.ROOT / f'derived/chain/{w}.json'))
        walker = Walk(dict(wallet=w, owner=led['owner']), led)
        up, down, direct = seeds_for(w, led, chain, relay)
        for n, a in seed.IRBOZ.items():
            if a['profile'].lower() == w:
                for s in a.get('evm', []) + a.get('sol', []) + a.get('btc', []):
                    (up if led['first_deposit'] else up).append((s, 1, f'irboz_{n}_published', led['last_trade'] or time.time()))
        t0 = led['first_deposit'] - 30 * 86400
        t1 = led['last_trade'] or int(time.time())
        n_up = walker.walk([(led['owner'], 0, w, t1)] + up, 'upstream', t0, t1)
        n_down = walker.walk([(led['owner'], 0, w, t0)] + down, 'downstream', t0, int(time.time()))
        out = dict(wallet=w, labels=led['labels'], owner=led['owner'], direct_flows=direct, nodes=list(walker.nodes.values()), edges=walker.edges, failed=walker.failed, polymarket_hits=walker.polymarket_hits, relay_records=walker.relay_records, limits=walker.limits,
                   relay_budget=walker.budget, expanded=dict(up=n_up, down=n_down), read_at=int(time.time()))
        path.write_text(json.dumps(out))
        c = Counter(n['cls'] for n in walker.nodes.values())
        print(w[:10], led['labels'][:2], dict(c), 'edges', len(walker.edges), 'failed', len(walker.failed), 'pm_hits', len({h['wallet'] for h in walker.polymarket_hits}), 'relay_left', walker.budget['left'], 'limits', len(walker.limits), 'calls', net.Stats.calls, flush=True)


if __name__ == '__main__':
    main()
