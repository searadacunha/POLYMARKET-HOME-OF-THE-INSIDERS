"""Direction 2, step 3. PROTOCOL.md section 4: recipients of PAYOUT_HOT sends, then their link to Polymarket and to the Ballon d'Or census.
`collect` reads labels and the Polymarket API; `analyse` writes the tables and the verdict. A synthetic recipient must be counted at every step (self-check at the end of `analyse`)."""
import csv
import gzip
import json
import random
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import addr
import labels
import net

ROOT = net.ROOT
SENDS = ROOT / 'derived/cn_sends.jsonl.gz'
RECIP = ROOT / 'derived/cn_recipients.json'
LINKS = ROOT / 'derived/cn_links.json'
WINDOW = 30 * 86400
SEED = 20261102
USD_IDS = {'ETH': 'ethereum', 'WETH': 'ethereum', 'POL': 'polygon-ecosystem-token', 'WBTC': 'bitcoin'}
USD_LIKE = {'USDC', 'USDC.e', 'USDT', 'DAI'}
SPECIAL = {'0x' + '0' * 40}


def usd(asset, amount, ts):
    if asset in USD_LIKE:
        return amount
    cid = USD_IDS.get(asset)
    if not cid:
        return None
    day = ts - ts % 86400
    d = net.get(f'https://coins.llama.fi/prices/historical/{day}/coingecko:{cid}')
    p = ((d.get('coins') or {}).get(f'coingecko:{cid}') or {}).get('price')
    return amount * p if p else None


def payouts():
    """Sends of the sources whose measured function is PAYOUT_HOT."""
    with gzip.open(SENDS, 'rt') as f:
        for line in f:
            r = json.loads(line)
            if r['source_function'] == 'PAYOUT_HOT':
                yield r


def collect():
    funcs = json.load(open(ROOT / 'derived/cn_functions.json'))
    known_cn = {v['address'] for v in funcs.values()}
    by_recipient = defaultdict(list)
    for r in payouts():
        by_recipient[(r['dst'], r['chain'])].append(dict(tx=r['tx'], ts=r['ts'], asset=r['asset'], amount=r['amount'], usd=usd(r['asset'], r['amount'], r['ts']), src=r['src'], block=r['block'], raw=r['raw']))
    print('recipient-chain pairs', len(by_recipient), flush=True)
    out = {}
    per_chain = defaultdict(set)
    for (a, c) in by_recipient:
        per_chain[c].add(a)
    for c, addrs in per_chain.items():
        labels.prefetch(sorted(addrs), c)
    n_tag = n_cn = 0
    for (a, c), sends in by_recipient.items():
        got = labels._cache.get((a, c)) or {}
        tags = got.get('tags') or []
        lab = labels.lookup(a, c)
        cat = None
        is_cn = a in known_cn or any('changenow' in t.lower() for t in tags) or (lab and 'changenow' in (lab['name'] or '').lower())
        if lab:
            cat = lab['category']
        if is_cn:
            kind = 'INTERNE_CHANGENOW'
            n_cn += 1
        elif cat in ('exchange', 'instant_exchange', 'bridge', 'mixer', 'dex_or_router', 'polymarket'):
            kind = 'SERVICE'
            n_tag += 1
        else:
            kind = 'CLIENT_CANDIDAT'
        out[f'{a}:{c}'] = dict(address=a, chain=c, kind=kind, label=lab['name'] if lab else None, sends=sends)
    print('internal', n_cn, 'service', n_tag, 'client candidates', sum(v['kind'] == 'CLIENT_CANDIDAT' for v in out.values()), flush=True)
    # contract check, chain of receipt
    n = 0
    for k, v in out.items():
        if v['kind'] != 'CLIENT_CANDIDAT':
            continue
        code = net.rpc('eth_getCode', [v['address'], 'latest'], chain=v['chain'])
        if code not in ('0x', None) and not code.startswith('0xef0100'):
            v['kind'] = 'CONTRAT'
        n += 1
        if n % 1000 == 0:
            RECIP.write_text(json.dumps(out))
            print('code checked', n, flush=True)
    RECIP.write_text(json.dumps(out))
    links = json.loads(LINKS.read_text()) if LINKS.exists() else {}
    n = 0
    for k, v in out.items():
        if v['kind'] != 'CLIENT_CANDIDAT' or v['address'] in links:
            continue
        t0 = min(s['ts'] for s in v['sends'])
        dw = addr.deposit_wallet(v['address'])
        hits = {}
        for label_, w in (('deposit_wallet', dw), ('eoa', v['address'])):
            d = net.get('https://data-api.polymarket.com/v2/activity', dict(user=w, limit=5, start=t0, end=t0 + WINDOW, sort_direction='ASC', exclude_deposits_withdrawals='false'))
            rows = d.get('data') or []
            if rows:
                hits[label_] = dict(wallet=w, first_ts=rows[0]['timestamp'], first_type=rows[0]['type'], n_seen=len(rows))
        links[v['address']] = dict(dw=dw, hits=hits)
        n += 1
        if n % 500 == 0:
            LINKS.write_text(json.dumps(links))
            print('polymarket checked', n, 'linked', sum(1 for x in links.values() if x['hits']), flush=True)
    LINKS.write_text(json.dumps(links))
    print('done, linked', sum(1 for x in links.values() if x['hits']))


def census_wallets():
    out = set()
    with gzip.open(ROOT / 'derived/census_trades.jsonl.gz', 'rt') as f:
        for line in f:
            out.add(json.loads(line)['w'])
    return out


def wilson(k, n, z=1.96):
    if not n:
        return None
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    r = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** .5)
    return [round((c - r) / d, 4), round((c + r) / d, 4)]


def near_pairs(items, tol, window):
    """Pairs (i<j) within `tol` in USD and `window` seconds. items: (ts, usd), sorted by ts."""
    n = 0
    m = len(items)
    for i in range(m):
        t, u = items[i]
        j = i + 1
        while j < m and items[j][0] - t <= window:
            v = items[j][1]
            if abs(u - v) <= tol * max(u, v):
                n += 1
            j += 1
    return n


def inactivity_sample(rec):
    """Protocol item 2: at most 3 transactions sent before receipt, on the chain of receipt. All recipients if N <= 3 000, else a random sample."""
    clients = sorted(k for k, v in rec.items() if v['kind'] == 'CLIENT_CANDIDAT')
    rng = random.Random(SEED)
    sample = clients if len(clients) <= 3000 else rng.sample(clients, 3000)
    res = {}
    path = ROOT / 'derived/cn_inactivity.json'
    if path.exists():
        res = json.loads(path.read_text())
    for i, k in enumerate(sample):
        if k in res:
            continue
        v = rec[k]
        first = min(v['sends'], key=lambda s: s['ts'])
        block = first['block']
        if v['chain'] == 10:
            res[k] = None
            continue
        d = net.get('https://api.etherscan.io/v2/api', dict(chainid=v['chain'], module='account', action='txlist', address=v['address'], startblock=0, endblock=block - 1, page=1, offset=5, sort='desc'), secret=dict(apikey=net.etherscan_key()))
        rows = d.get('result') or []
        sent = [r for r in rows if r['from'].lower() == v['address']]
        res[k] = dict(sent_before=len(sent), any_before=len(rows))
        if i % 500 == 0:
            path.write_text(json.dumps(res))
            print('inactivity', i, flush=True)
    path.write_text(json.dumps(res))
    return res


def analyse(rec=None, links=None, census=None, write=True, inactivity=None, n_draws=10000):
    rec = rec if rec is not None else json.load(open(RECIP))
    links = links if links is not None else json.load(open(LINKS))
    census = census if census is not None else census_wallets()
    kinds = Counter(v['kind'] for v in rec.values())
    clients = {k: v for k, v in rec.items() if v['kind'] == 'CLIENT_CANDIDAT'}
    addresses = {v['address'] for v in clients.values()}
    per_chain = Counter(v['chain'] for v in clients.values())
    total_usd = sum(s['usd'] or 0 for v in rec.values() for s in v['sends'])
    client_usd = sum(s['usd'] or 0 for v in clients.values() for s in v['sends'])
    unpriced = sum(1 for v in rec.values() for s in v['sends'] if s['usd'] is None)
    linked = {a: x for a, x in links.items() if x['hits'] and a in addresses}
    ballon = {}
    for a in addresses:
        dw = addr.deposit_wallet(a)
        if dw in census:
            ballon[a] = dw
        elif a in census:
            ballon[a] = a
    pm_usd = sum(s['usd'] or 0 for v in clients.values() if v['address'] in linked for s in v['sends'])
    ballon_usd = sum(s['usd'] or 0 for v in clients.values() if v['address'] in ballon for s in v['sends'])
    res = dict(sources_payout_hot=None, kinds=dict(kinds), distinct_client_wallets=len(addresses), client_chain_pairs=per_chain and dict(per_chain), total_usd_all_recipients=round(total_usd), client_usd=round(client_usd), unpriced_sends=unpriced,
               linked_polymarket_30d=len(linked), linked_usd=round(pm_usd), ballon_bettors=len(ballon), ballon_usd=round(ballon_usd), ballon=sorted(ballon.items()))
    # protocol items 5 and 6: pairs close in amount and time among Polymarket-linked recipients, against random subsets of all recipients of the same chain
    tests = []
    if linked:
        items = []
        all_items = defaultdict(list)
        link_chains = Counter()
        for v in clients.values():
            s = min(v['sends'], key=lambda x: x['ts'])
            if s['usd'] is None:
                continue
            all_items[v['chain']].append((s['ts'], s['usd']))
            if v['address'] in linked:
                items.append((s['ts'], s['usd']))
                link_chains[v['chain']] += 1
        items.sort()
        rng = random.Random(SEED)
        for tol in (.005, .01, .05):
            for win in (600, 3600, 21600, 86400):
                obs = near_pairs(items, tol, win)
                null = []
                for _ in range(n_draws):
                    draw = []
                    for ch, k in link_chains.items():
                        draw += rng.sample(all_items[ch], k)
                    draw.sort()
                    null.append(near_pairs(draw, tol, win))
                ge = sum(1 for x in null if x >= obs)
                tests.append(dict(tol=tol, window=win, observed=obs, null_mean=round(sum(null) / len(null), 2), p=(ge + 1) / (n_draws + 1), n_draws=n_draws))
        order = sorted(range(len(tests)), key=lambda i: tests[i]['p'])
        top = 0.0
        for r, i in enumerate(order):
            top = max(top, (len(tests) - r) * tests[i]['p'])
            tests[i]['p_holm'] = min(1.0, top)
    res['near_pair_tests'] = tests
    # the same among Ballon bettors
    ball_items = []
    for v in clients.values():
        if v['address'] in ballon:
            s = min(v['sends'], key=lambda x: x['ts'])
            ball_items.append(dict(address=v['address'], wallet=ballon[v['address']], ts=s['ts'], usd=s['usd'], asset=s['asset'], tx=s['tx'], chain=v['chain'], src=s['src']))
    res['ballon_rows'] = ball_items
    near_ballon = []
    for i in range(len(ball_items)):
        for j in range(i + 1, len(ball_items)):
            a, b = ball_items[i], ball_items[j]
            if a['usd'] and b['usd'] and abs(a['usd'] - b['usd']) <= .05 * max(a['usd'], b['usd']) and abs(a['ts'] - b['ts']) <= 86400:
                near_ballon.append((a['address'], b['address']))
    res['ballon_near_pairs_5pct_24h'] = near_ballon
    if inactivity:
        known = [v for v in inactivity.values() if v]
        k = sum(1 for v in known if v['sent_before'] <= 3)
        res['inactive_or_new'] = dict(k=k, n=len(known), share=round(k / len(known), 4) if known else None, wilson95=wilson(k, len(known)), note='offset=5 of the latest sends before the receipt: <=3 is exact, the rest are >3', optimism_left_out=sum(1 for v in inactivity.values() if v is None))
    if write:
        (ROOT / 'derived/cn_result.json').write_text(json.dumps(res, indent=1))
    return res


def selfcheck():
    """A planted recipient goes through every count. No network."""
    a = '0x08d409aae84f9b7b6a798c97c457a0f41e856c7b'
    dw = addr.deposit_wallet(a)
    rec = {f'{a}:1': dict(address=a, chain=1, kind='CLIENT_CANDIDAT', label=None, sends=[dict(tx='0xabc', ts=100, asset='USDC', amount=1000.0, usd=1000.0, src='0xcn', block=1, raw='1000000000')]),
           '0xb:1': dict(address='0xb', chain=1, kind='SERVICE', label='Binance', sends=[dict(tx='0xdef', ts=100, asset='USDC', amount=5.0, usd=5.0, src='0xcn', block=1, raw='5000000')]),
           '0x1111111111111111111111111111111111111111:1': dict(address='0x1111111111111111111111111111111111111111', chain=1, kind='CLIENT_CANDIDAT', label=None, sends=[dict(tx='0x1', ts=120, asset='USDC', amount=1001.0, usd=1001.0, src='0xcn', block=1, raw='1')])}
    links = {a: dict(dw=dw, hits=dict(deposit_wallet=dict(wallet=dw, first_ts=110, first_type='DEPOSIT', n_seen=1))), '0x1111111111111111111111111111111111111111': dict(dw='x', hits={})}
    r = analyse(rec, links, census={dw}, write=False, n_draws=20)
    assert r['distinct_client_wallets'] == 2 and r['linked_polymarket_30d'] == 1 and r['ballon_bettors'] == 1 and r['ballon_usd'] == 1000 and r['client_usd'] == 2001 and r['kinds']['SERVICE'] == 1, r
    assert near_pairs([(0, 100.0), (10, 100.4), (10000, 100.0)], .005, 600) == 1
    print('selfcheck ok')


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'selfcheck':
        selfcheck()
    elif cmd == 'collect':
        collect()
    else:
        rec = json.load(open(RECIP))
        ina = inactivity_sample(rec)
        r = analyse(inactivity=ina)
        print({k: v for k, v in r.items() if k not in ('ballon', 'near_pair_tests', 'ballon_rows')})
        for t in r['near_pair_tests']:
            print(t)
