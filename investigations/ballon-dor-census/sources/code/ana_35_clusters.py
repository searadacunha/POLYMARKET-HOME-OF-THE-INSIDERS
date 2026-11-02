"""Compare every pair of accounts, independently of the walk's thresholds: all raw transfers of each account's own addresses, every asset, no minimum.
Own addresses: the Polymarket wallet, its owner, and the personal-sized addresses within one hop of its deposits and withdrawals.
Levels are those of PROTOCOL.md section 1. A shared service never links. An unread address never counts as "no link": the pair is marked INDETERMINE.
Coverage is written per account. Base and BSC have no free history: what they hide cannot be excluded."""
import glob
import itertools
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import hist
import labels
import net

ROOT = net.ROOT
CHAINS = (1, 137, 42161, 10)
SKIP = {'0x' + '0' * 40, '0x000000000000000000000000000000000000dead'}
SERVICE_CATEGORIES = ('exchange', 'instant_exchange', 'bridge', 'mixer', 'dex_or_router', 'polymarket')
RELAYERS_NOTE = 'tx.from of a gasless transaction is a relayer: only the transfer logs are compared, never tx.from'


def own_sets():
    out = {}
    for f in sorted(glob.glob(str(ROOT / 'derived/walk/*.json'))):
        w = json.load(open(f))
        own = {w['wallet'], w['owner']}
        for n in w['nodes']:
            if n['hop'] <= 1 and n['cls'] == 'PERSONAL_SIZED':
                own.add(n['address'])
        out[w['wallet']] = dict(labels=w['labels'], own=sorted(a for a in own if a), owner=w['owner'], walk_failed=len(w['failed']), walk_limits=len(w['limits']),
                                nodes=[(n['address'], n['cls'], n['hop'], n['direction']) for n in w['nodes']])
    return out


def rows_of(a, unread):
    if not a.startswith('0x'):
        return []  # Solana and Bitcoin: compared below on the walk nodes, not on raw rows
    rows = []
    for c in CHAINS:
        try:
            r, _ = hist.evm_rows(a, c)
            rows += r
        except net.FetchError as e:
            unread.append(dict(address=a, chain=c, error=str(e)[:120]))
    return rows


def is_personal(a, cache):
    """Same rule as the protocol. personal=None: could not be read, which is not an answer."""
    if a in cache:
        return cache[a]
    lab = labels.lookup(a)
    if lab and lab['category'] in SERVICE_CATEGORIES:
        cache[a] = dict(personal=False, why='label: ' + lab['name'], label=lab['name'])
        return cache[a]
    if not a.startswith('0x'):
        cache[a] = dict(personal=None, why='non-EVM counterparty, size not measured here', label=None)
        return cache[a]
    rows, stats = [], {}
    for c in CHAINS:
        try:
            r, s = hist.evm_rows(a, c)
            rows += r
            stats[c] = s
        except net.FetchError as e:
            cache[a] = dict(personal=None, why='unread: ' + str(e)[:80], label=None)
            return cache[a]
    nonce = max((s.get('nonce_seen') or 0) for s in stats.values())
    cps = {r['src'] if r['dst'] == a else r['dst'] for r in rows if r.get('recognized')}
    try:
        code = net.rpc('eth_getCode', [a, 'latest'], chain=137)
        code1 = net.rpc('eth_getCode', [a, 'latest'], chain=1)
    except net.FetchError as e:
        cache[a] = dict(personal=None, why='code unread: ' + str(e)[:80], label=None)
        return cache[a]
    contract = any(c not in ('0x', None) and not c.startswith('0xef0100') for c in (code, code1))
    if contract:
        cache[a] = dict(personal=False, why='contract', label=None)
    elif nonce >= 1000:
        cache[a] = dict(personal=False, why=f'nonce {nonce}', label=None)
    elif len(cps) >= 400:
        cache[a] = dict(personal=False, why=f'{len(cps)} counterparties', label=None)
    else:
        cache[a] = dict(personal=True, why=f'nonce {nonce}, {len(cps)} counterparties', label=lab['name'] if lab else None)
    return cache[a]


def main():
    accounts = own_sets()
    n = len(accounts)
    print('accounts', n)
    by_addr = defaultdict(set)
    for w, v in accounts.items():
        for a in v['own']:
            by_addr[a].add(w)
    unread = defaultdict(list)
    rows_by_account = {}
    for w, v in accounts.items():
        rows = []
        for a in v['own']:
            rows += [dict(r, own=a) for r in rows_of(a, unread[w])]
        # positions and pUSD moving directly between Polymarket wallets, from the Polygon lists read in col_40
        c = json.load(open(ROOT / f'derived/chain/{w}.json'))
        for kind in ('erc20', 'erc1155'):
            for r in c[kind]:
                frm, to = r['from'].lower(), r['to'].lower()
                other = to if frm == w else frm
                if other in accounts and other != w:
                    amount = int(r.get('value') or r.get('tokenValue') or 0) / 10 ** int(r.get('tokenDecimal') or 0)
                    rows.append(dict(chain='137', tx=r['hash'], block=int(r['blockNumber']), ts=int(r['timeStamp']), src=frm, dst=to, asset=r.get('tokenSymbol') or kind, contract=r['contractAddress'].lower(), raw=str(r.get('value') or r.get('tokenValue')), amount=amount, kind=kind, recognized=True, own=w))
        rows_by_account[w] = rows
        print(w[:10], 'own', len(v['own']), 'rows', len(rows), 'unread', len(unread[w]), flush=True)
    # 1. direct transfers, every asset, every amount
    direct, seen = [], set()
    for w, rows in rows_by_account.items():
        for r in rows:
            other = r['dst'] if r['src'] == r['own'] else r['src']
            for w2 in set(by_addr.get(other, ())) | ({other} if other in accounts else set()):
                if w2 == w:
                    continue
                k = (r['tx'], r['src'], r['dst'], r['asset'], r['raw'], tuple(sorted((w, w2))))
                if k not in seen:
                    seen.add(k)
                    direct.append(dict(a=w, b=w2, chain=r['chain'], tx=r['tx'], block=r['block'], ts=r['ts'], utc=hist.utc(r['ts']), src=r['src'], dst=r['dst'], asset=r['asset'], contract=r.get('contract'), raw=r['raw'], amount=r['amount'], recognized=r.get('recognized'), kind=r['kind']))
    # a position crossing two wallets inside an order match is the order book at work, not a transfer between them
    for d in direct:
        if d['kind'] in ('erc1155', 'erc20') and d['chain'] == '137':
            try:
                rc = net.rpc('eth_getTransactionReceipt', [d['tx']])
                d['book_match'] = any(l['topics'] and l['topics'][0].startswith(('0xd543adfd', '0xd0a08e8c')) for l in rc['logs'])
            except net.FetchError as e:
                d['book_match'] = None
                d['receipt_error'] = str(e)[:100]
    # 2. an address inside two accounts' own sets
    overlap = {a: sorted(ws) for a, ws in by_addr.items() if len(ws) >= 2}
    # 3. shared counterparties of the own addresses, recognized assets, plus any personal node shared by two walks (covers Solana and Bitcoin)
    cp = defaultdict(lambda: defaultdict(list))
    for w, rows in rows_by_account.items():
        for r in rows:
            other = r['dst'] if r['src'] == r['own'] else r['src']
            if not other or other in SKIP or other in by_addr or not r.get('recognized'):
                continue
            cp[other][w].append(dict(tx=r['tx'], chain=r['chain'], ts=r['ts'], direction='out' if r['src'] == r['own'] else 'in', asset=r['asset'], amount=r['amount'], own=r['own']))
    for w, v in accounts.items():
        for a, cls, hop, direction in v['nodes']:
            if a not in by_addr and not a.startswith('0x') and a not in SKIP:
                cp[a][w].append(dict(tx=None, chain='non-evm', ts=None, direction=direction, asset='', amount=None, own=f'walk hop {hop}, {cls}'))
    shared = {a: v for a, v in cp.items() if len(v) >= 2}
    print('counterparties shared by 2+ accounts', len(shared), 'own overlap', len(overlap), flush=True)
    cache = {}
    links = defaultdict(lambda: dict(l1=[], overlap=[], personal_shared=[], service_shared=defaultdict(int), undetermined=[]))
    classified = []
    for a, by in sorted(shared.items(), key=lambda x: len(x[1])):
        info = is_personal(a, cache)
        classified.append(dict(address=a, accounts=len(by), **info))
        for w1, w2 in itertools.combinations(sorted(by), 2):
            pair = links[(w1, w2)]
            if info['personal'] is True:
                pair['personal_shared'].append(dict(address=a, why=info['why'], a=by[w1][:3], b=by[w2][:3], n_accounts=len(by)))
            elif info['personal'] is None:
                pair['undetermined'].append(dict(address=a, why=info['why']))
            else:
                pair['service_shared'][info['label'] or info['why']] += 1
    for a, ws in overlap.items():
        info = is_personal(a, cache)
        for w1, w2 in itertools.combinations(ws, 2):
            links[(w1, w2)]['overlap'].append(dict(address=a, **info))
    for d in direct:
        w1, w2 = sorted((d['a'], d['b']))
        links[(w1, w2)]['l1'].append(d)
    pairs_out = []
    for (w1, w2), v in links.items():
        real = [d for d in v['l1'] if d.get('recognized') and d['amount'] > 0 and not d.get('book_match')]
        token_only = [d for d in v['l1'] if not d.get('recognized')]
        book = [d for d in v['l1'] if d.get('book_match')]
        rare = [p for p in v['personal_shared'] if p['n_accounts'] <= 3]
        if real:
            level = 'L1_PROUVE_TX'
        elif v['overlap']:
            level = 'L2_ADRESSE_PROPRE_COMMUNE'
        elif rare:
            level = 'L2_CANDIDAT_ADRESSE_RARE'
        elif token_only:
            level = 'JETON_NON_RECONNU_A_LIRE'
        elif v['personal_shared']:
            level = 'L3_ADRESSE_COMMUNE_NON_RARE'
        elif v['undetermined']:
            level = 'INDETERMINE'
        elif book:
            level = 'L5_CONTREPARTIE_DE_CARNET'
        elif v['service_shared']:
            level = 'L4_MEME_PRESTATAIRE'
        else:
            level = 'L5_FORTUIT_PLAUSIBLE'
        pairs_out.append(dict(a=w1, b=w2, labels_a=accounts[w1]['labels'], labels_b=accounts[w2]['labels'], level=level, direct=[d for d in v['l1'] if not d.get('book_match')][:12], book_matches=[d for d in v['l1'] if d.get('book_match')][:6], n_direct=len([d for d in v['l1'] if not d.get('book_match')]), n_book_matches=len(book), overlap=v['overlap'][:6], personal_shared=v['personal_shared'][:8], n_personal_shared=len(v['personal_shared']), service_shared=dict(v['service_shared']), undetermined=v['undetermined'][:6], unread_a=len(unread[w1]), unread_b=len(unread[w2])))
    pairs_out.sort(key=lambda p: (p['level'], -p['n_direct']))
    total = n * (n - 1) // 2
    print('pairs total', total, 'with any evidence', len(pairs_out), Counter(p['level'] for p in pairs_out))
    for p in pairs_out:
        if p['level'].startswith(('L1', 'L2', 'JETON')):
            print(p['level'], p['labels_a'][-1][:22], p['labels_b'][-1][:22], p['a'][:10], p['b'][:10], 'direct', [(d['chain'], d['utc'][:16], d['src'][:8], d['dst'][:8], d['asset'][:8], round(d['amount'], 5), d['tx'][:10]) for d in p['direct'][:3]], 'overlap', [o['address'][:10] for o in p['overlap'][:2]], 'shared', [(s['address'][:10], s['why'][:30], s['n_accounts']) for s in p['personal_shared'][:2]])
    # positive control: must be found again, or no "no link" stands
    known = ('0xc852b0938f5ad79b640d105ed11c14499454af26', '0x101b5f4dc0886c32e2b75972101aeaf9f338fb65')
    hit = [d for d in direct if {d['src'], d['dst']} == set(known)]
    if {'0x873848cd27784900e193611845fc3fd2c4716d03', '0x84212ee459d1edaf35983bbec342b0806282d8ec'} <= set(accounts):
        assert hit, 'positive control lost: the brace227 key to kraben006 key transfer read by an earlier audit is not found'
    print('positive control rows', [(d['chain'], d['utc'], d['asset'], d['amount'], d['tx']) for d in hit])
    coverage = dict(read=['ethereum', 'polygon', 'arbitrum', 'optimism: native, internal and ERC-20 of the own addresses', 'polygon ERC-20 and ERC-1155 of the Polymarket wallets'], partial=['solana and bitcoin: only addresses the walk reached, shared-node comparison'], not_read=['base and bsc history: no free source; other chains'], note=RELAYERS_NOTE)
    (ROOT / 'derived/clusters_raw.json').write_text(json.dumps(dict(accounts=accounts, pairs=pairs_out, classified=classified, n_pairs=total, coverage=coverage, unread={k: v for k, v in unread.items() if v}, positive_control=hit[:3]), indent=0))


if __name__ == '__main__':
    main()
