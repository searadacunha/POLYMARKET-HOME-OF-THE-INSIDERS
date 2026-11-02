"""Compare every pair of accounts, independently of the walk's thresholds: all raw transfers of each account's own addresses, every asset, no minimum.
Own addresses: the Polymarket wallet, its owner, and the personal-sized addresses that directly fed or received its deposits and withdrawals.
Levels are those of PROTOCOL.md section 1. A shared service never links. Positive controls must pass before any "no link" is believed."""
import glob
import itertools
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import hist
import labels
import net

ROOT = net.ROOT
CHAINS = (1, 137, 42161, 10)
SKIP = {'0x' + '0' * 40, '0x000000000000000000000000000000000000dead'}
SPAM_NATIVE_MIN = 0.0


def own_sets():
    out = {}
    for f in sorted(glob.glob(str(ROOT / 'derived/walk/*.json'))):
        w = json.load(open(f))
        own = {w['wallet'], w['owner']}
        for n in w['nodes']:
            # the first hop of a personal size is the account's own temporary address only when the published record or the direct flow named it
            if n['hop'] <= 1 and n['cls'] == 'PERSONAL_SIZED':
                own.add(n['address'])
        out[w['wallet']] = dict(labels=w['labels'], own=sorted(a for a in own if a), owner=w['owner'])
    return out


def rows_of(a):
    if a.startswith('0x'):
        rows = []
        for c in CHAINS:
            try:
                r, _ = hist.evm_rows(a, c)
                rows += r
            except net.FetchError:
                pass
        return rows
    return []


def is_personal(a, cache):
    """Same rule as the protocol. Reads history only if the label says nothing."""
    if a in cache:
        return cache[a]
    lab = labels.lookup(a)
    if lab and lab['category'] in ('exchange', 'instant_exchange', 'bridge', 'mixer', 'dex_or_router', 'polymarket'):
        cache[a] = dict(personal=False, why='label: ' + lab['name'], label=lab['name'])
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
    code = net.rpc('eth_getCode', [a, 'latest'], chain=137)
    code1 = net.rpc('eth_getCode', [a, 'latest'], chain=1)
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
    print('accounts', len(accounts))
    by_addr = defaultdict(set)
    for w, v in accounts.items():
        for a in v['own']:
            by_addr[a].add(w)
    rows_by_account = {}
    for w, v in accounts.items():
        rows = []
        for a in v['own']:
            if a.startswith('0x'):
                rows += [dict(r, own=a) for r in rows_of(a)]
        rows_by_account[w] = rows
        print(w[:10], 'own', len(v['own']), 'rows', len(rows), flush=True)
    # direct transfers: every asset, every amount, spam kept apart
    direct = []
    for w, rows in rows_by_account.items():
        for r in rows:
            other = r['dst'] if r['src'] == r['own'] else r['src']
            for w2 in by_addr.get(other, ()):
                if w2 != w:
                    direct.append(dict(a=w, b=w2, chain=r['chain'], tx=r['tx'], block=r['block'], ts=r['ts'], utc=hist.utc(r['ts']), src=r['src'], dst=r['dst'], asset=r['asset'], contract=r.get('contract'), raw=r['raw'], amount=r['amount'], recognized=r.get('recognized'), kind=r['kind']))
    seen = set()
    uniq = []
    for d in direct:
        k = (d['tx'], d['src'], d['dst'], d['asset'], d['raw'])
        if k not in seen:
            seen.add(k)
            uniq.append(d)
    direct = uniq
    # shared counterparties
    cp = defaultdict(lambda: defaultdict(list))
    for w, rows in rows_by_account.items():
        for r in rows:
            other = r['dst'] if r['src'] == r['own'] else r['src']
            if not other or other in SKIP or other in by_addr or not r.get('recognized'):
                continue
            cp[other][w].append(dict(tx=r['tx'], chain=r['chain'], ts=r['ts'], direction='out' if r['src'] == r['own'] else 'in', asset=r['asset'], amount=r['amount'], own=r['own']))
    shared = {a: v for a, v in cp.items() if len(v) >= 2}
    print('counterparties shared by 2+ accounts', len(shared), flush=True)
    cache = {}
    links = defaultdict(lambda: dict(l1=[], personal_shared=[], service_shared=defaultdict(int), fortuitous=[]))
    classified = []
    for a, by in sorted(shared.items(), key=lambda x: len(x[1])):
        info = is_personal(a, cache)
        classified.append(dict(address=a, accounts=len(by), **info))
        for w1, w2 in itertools.combinations(sorted(by), 2):
            pair = links[(w1, w2)]
            if info['personal'] is True:
                pair['personal_shared'].append(dict(address=a, why=info['why'], a=by[w1][:3], b=by[w2][:3], n_accounts=len(by)))
            else:
                pair['service_shared'][info['label'] or info['why']] += 1
    for d in direct:
        w1, w2 = sorted((d['a'], d['b']))
        links[(w1, w2)]['l1'].append(d)
    pairs_out = []
    for (w1, w2), v in links.items():
        level = 'L4_MEME_PRESTATAIRE' if v['service_shared'] else 'L5_FORTUIT_PLAUSIBLE'
        real = [d for d in v['l1'] if d.get('recognized') and d['amount'] > 0]
        if real:
            level = 'L1_PROUVE_TX'
        elif v['personal_shared']:
            only_rare = [p for p in v['personal_shared'] if p['n_accounts'] <= 3]
            level = 'L2_CANDIDAT' if only_rare else 'L3_ADRESSE_COMMUNE_NON_RARE'
        pairs_out.append(dict(a=w1, b=w2, labels_a=accounts[w1]['labels'], labels_b=accounts[w2]['labels'], level=level, direct=v['l1'][:12], n_direct=len(v['l1']), personal_shared=v['personal_shared'][:8], n_personal_shared=len(v['personal_shared']), service_shared=dict(v['service_shared'])))
    pairs_out.sort(key=lambda p: (p['level'], -p['n_direct']))
    n = len(accounts)
    from collections import Counter
    print('pairs total', n * (n - 1) // 2, 'with any evidence', len(pairs_out), Counter(p['level'] for p in pairs_out))
    for p in pairs_out:
        if p['level'] in ('L1_PROUVE_TX', 'L2_CANDIDAT'):
            print(p['level'], p['labels_a'][-1][:24], p['labels_b'][-1][:24], p['a'][:10], p['b'][:10], 'direct', [(d['chain'], d['utc'], d['src'][:8], d['dst'][:8], d['asset'], round(d['amount'], 5), d['tx'][:10]) for d in p['direct'][:3]], 'shared', [(s['address'][:10], s['why']) for s in p['personal_shared'][:3]])
    # positive controls
    controls = {'brace227_key_to_kraben006_key': ('0xc852b0938f5ad79b640d105ed11c14499454af26', '0x101b5f4dc0886c32e2b75972101aeaf9f338fb65')}
    results = {}
    for name, (a, b) in controls.items():
        hit = [d for d in direct if {d['src'], d['dst']} == {a, b}]
        results[name] = dict(found=bool(hit), rows=hit[:3])
    print('positive controls', {k: v['found'] for k, v in results.items()})
    (ROOT / 'derived/clusters_raw.json').write_text(json.dumps(dict(accounts=accounts, pairs=pairs_out, classified=classified, controls=results, n_pairs=n * (n - 1) // 2), indent=0))


if __name__ == '__main__':
    main()
