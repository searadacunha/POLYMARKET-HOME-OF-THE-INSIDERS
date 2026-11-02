"""Behaviour of the two addresses in block windows, never their whole history. Links with every other address some source calls ChangeNOW, read from those addresses' side. Writes state/p9.json."""
import csv, gzip, json, statistics, sys, time
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import arch, es
ROOT = Path(__file__).resolve().parent.parent
DEP, HOT3, HOT4 = '0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b', '0xdd3d72c53ff982ff59853da71158bf1538b3ceee', '0xeba88149813bec1cccccfdb0dacefaaa5de94cb1'
USDC, USDT = '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48', '0xdac17f958d2ee523a2206206994597c13d831ec7'
SWEEP, PAY1, PAY2 = 26122424, 24520622, 24520663


def tags_of(addrs, chain=1, tag='w'):
    out = {}
    addrs = sorted(addrs)
    for i in range(0, len(addrs), 200):
        s, b = arch.fetch(f'https://metadata.services.blockscout.com/api/v1/metadata?chainId={chain}&addresses=' + ','.join(addrs[i:i + 200]), f'bs_{tag}_{chain}_{i // 200:04d}.json', pause=.5)
        if s == 200:
            for a, v in json.loads(b).get('addresses', {}).items():
                out[a.lower()] = [t['name'] for t in v.get('tags', [])]
    return out


def native_stats(rows, me):
    ins = [r for r in rows if r['to'].lower() == me and int(r['value']) > 0 and r.get('isError') == '0']
    outs = [r for r in rows if r['from'].lower() == me and int(r['value']) > 0 and r.get('isError') == '0']
    s, d = Counter(r['from'].lower() for r in ins), Counter(r['to'].lower() for r in outs)
    v = lambda x: int(x['value']) / 1e18
    return dict(rows=len(rows), first=min((int(r['timeStamp']) for r in rows), default=None), last=max((int(r['timeStamp']) for r in rows), default=None), n_in=len(ins), n_out=len(outs), eth_in=round(sum(map(v, ins)), 6), eth_out=round(sum(map(v, outs)), 6), senders=len(s), recipients=len(d), sender_once=sum(c == 1 for c in s.values()), recipient_once=sum(c == 1 for c in d.values()), median_in=round(statistics.median(map(v, ins)), 6) if ins else None, median_out=round(statistics.median(map(v, outs)), 6) if outs else None, top_senders=s.most_common(6), top_recipients=d.most_common(10))


res = {}
samples = dict(first=es.rows('txlist', DEP, sort='asc'), last=es.rows('txlist', DEP, sort='desc'))
samples['event'], ok = es.window('txlist', DEP, start=SWEEP - 1500, end=SWEEP + 1500)
samples['feb'], ok2 = es.window('txlist', DEP, start=PAY1 - 1500, end=PAY2 + 1500)
res['dep_windows_complete'] = dict(event=ok, feb=ok2)
res['dep'] = {k: native_stats(v, DEP) for k, v in samples.items()}
print(json.dumps(res['dep'], indent=0)[:1800], flush=True)
cp = {r['to'].lower() for v in samples.values() for r in v if r['to']} | {r['from'].lower() for v in samples.values() for r in v}
res['dep_cp_tags'] = tags_of(cp, tag='depcp')
print('dep counterparties', len(cp), 'tagged', len(res['dep_cp_tags']), Counter(t for v in res['dep_cp_tags'].values() for t in v if 'hange' not in t).most_common(15), flush=True)
print('with changenow', {a: v for a, v in res['dep_cp_tags'].items() if 'changenow' in ' '.join(v).lower()}, flush=True)
# the sweep and what followed it
ev = sorted(samples['event'], key=lambda r: (int(r['blockNumber']), int(r['transactionIndex'])))
i = next(i for i, r in enumerate(ev) if r['hash'].startswith('0x22710b5e'))
res['after_sweep'] = [dict(h=r['hash'], t=int(r['timeStamp']), f=r['from'], to=r['to'], v=r['value']) for r in ev[i:i + 25]]
print('sweep row', res['after_sweep'][0], flush=True)
print('next out', [x for x in res['after_sweep'] if x['f'].lower() == DEP][:5], flush=True)
# Hot wallet 3
hot = dict(first=es.rows('txlist', HOT3, sort='asc'), last=es.rows('txlist', HOT3, sort='desc'))
hot_first_tok = es.rows('tokentx', HOT3, sort='asc')
res['hot3_first'] = dict(first_tx=hot['first'][0] if hot['first'] else None, first_tok=hot_first_tok[0] if hot_first_tok else None, n_sent_first=sum(r['from'].lower() == HOT3 for r in hot['first']))
feb_usdc, fok = es.window('tokentx', HOT3, start=PAY1 - 300, end=PAY2 + 300, contract=USDC)
feb_all, faok = es.window('tokentx', HOT3, start=PAY1 - 300, end=PAY2 + 300)
oct_usdc, ook = es.window('tokentx', HOT3, start=SWEEP - 100, end=SWEEP + 3000, contract=USDC)
oct_usdt, otok = es.window('tokentx', HOT3, start=SWEEP - 100, end=SWEEP + 1200, contract=USDT)
res['hot3_windows_complete'] = dict(feb_usdc=fok, feb_all=faok, oct_usdc=ook, oct_usdt=otok)
for name, rows in (('feb_usdc', feb_usdc), ('feb_all', feb_all), ('oct_usdc', oct_usdc), ('oct_usdt', oct_usdt)):
    outs = [r for r in rows if r['from'].lower() == HOT3]
    ins = [r for r in rows if r['to'].lower() == HOT3]
    dec = lambda r: int(r['value']) / 10 ** int(r['tokenDecimal'])
    res['hot3_' + name] = dict(n=len(rows), n_out=len(outs), n_in=len(ins), first=min((int(r['timeStamp']) for r in rows), default=None), last=max((int(r['timeStamp']) for r in rows), default=None), recipients=len({r['to'] for r in outs}), senders=len({r['from'] for r in ins}), top_in=Counter(r['from'].lower() for r in ins).most_common(8), top_out=Counter(r['to'].lower() for r in outs).most_common(8), tokens=Counter(r['tokenSymbol'] for r in rows).most_common(8), outs=[(r['to'].lower(), dec(r), int(r['timeStamp']), r['hash'], r['tokenSymbol']) for r in outs][:4000], ins=[(r['from'].lower(), dec(r), int(r['timeStamp']), r['hash'], r['tokenSymbol']) for r in ins][:1500])
    print(name, {k: res['hot3_' + name][k] for k in ('n', 'n_out', 'n_in', 'recipients', 'senders', 'first', 'last', 'tokens', 'top_in')}, flush=True)
cph = {r['to'].lower() for v in hot.values() for r in v if r['to']} | {r['from'].lower() for v in hot.values() for r in v} | {x[0] for k in ('hot3_feb_usdc', 'hot3_feb_all', 'hot3_oct_usdc', 'hot3_oct_usdt') for side in ('outs', 'ins') for x in res[k][side]}
res['hot3_cp_tags'] = tags_of(cph, tag='hotcp')
print('hot3 counterparties', len(cph), 'tagged', len(res['hot3_cp_tags']), 'changenow', {a: v for a, v in res['hot3_cp_tags'].items() if 'changenow' in ' '.join(v).lower()}, flush=True)
# Links from the other labelled addresses' side
cand = {}
for r in csv.DictReader(open(ROOT / 'state/universe_raw.csv')):
    if r['address'].startswith('0x'):
        cand.setdefault(r['address'], set()).add(r['name'])
for a, n in (('0x4778480c6c46521c41f7e4f2318f884b157cb1c9', 'ChangeNow (0x4778)'), ('0xa12e1462d0ced572f396f58b6e2d03894cd7c8a4', 'ChangeNOW: hot wallet')):
    cand.setdefault(a, set()).add(n)
links = []
for a in sorted(cand):
    if a in (DEP, HOT3):
        continue
    for action in ('txlist', 'tokentx'):
        rows = es.rows(action, a, sort='desc')
        hit = [r for r in rows if {r['from'].lower(), (r['to'] or '').lower()} & {DEP, HOT3}]
        links.append(dict(address=a, names=sorted(cand[a]), action=action, read=len(rows), first=min((int(r['timeStamp']) for r in rows), default=None), last=max((int(r['timeStamp']) for r in rows), default=None), hits=[dict(h=r['hash'], t=int(r['timeStamp']), f=r['from'].lower(), to=r['to'].lower(), v=r['value'], sym=r.get('tokenSymbol'), dec=r.get('tokenDecimal')) for r in hit]))
    print('link', a[:10], sorted(cand[a])[:1], [(l['read'], len(l['hits'])) for l in links[-2:]], flush=True)
res['links'] = links
(ROOT / 'state/p9.json').write_text(json.dumps(res))
print('done', flush=True)
