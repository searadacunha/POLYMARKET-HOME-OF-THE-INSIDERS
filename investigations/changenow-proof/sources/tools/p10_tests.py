"""Counter-checks. A: link test on non-ChangeNOW controls. B: witnesses of the deposit relay profile. C: properties on the other recipients of the same hot wallet window. D: amount matches by chance. E: second hop against the candidates. Seeded, stored in state/p10.json."""
import csv, json, random, statistics, sys, time
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import arch, es
ROOT = Path(__file__).resolve().parent.parent
DEP, HOT3, HOT4 = '0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b', '0xdd3d72c53ff982ff59853da71158bf1538b3ceee', '0xeba88149813bec1cccccfdb0dacefaaa5de94cb1'
USDC = '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48'
SWEEP, PAY1, PAY2 = 26122424, 24520622, 24520663
RELAY = '0x7e67df45e0a0bab092cbb2ff045f8aa8dfab6e23'
p = json.load(open(ROOT / 'state/p9.json'))
res = {}
rng = random.Random(20261102)
# A. Same link test on wallets some source gives to other services
ctl = {}
src = (ROOT / 'evidence/repos/swap_services_quantumdev.py').read_text()
import re
for m in re.finditer(r'"(fixedfloat|simpleswap)", Chain\.ETHEREUM,\s*"(0x[0-9a-fA-F]{40})",\s*"([a-z-]+)", "([^"]+)"', src):
    ctl[m.group(2).lower()] = f'{m.group(4)} (QuantumDev list, {m.group(3)})'
for a, n in (('0x4976a4a02f38326660d17bf34b431dc6e2eb2327', 'Binance 20'), ('0xcad621da75a66c7a8f4ff86d30a2bf981bfc8fdd', 'KuCoin 10'), ('0x7ff8bbf9c8ab106db589e7863fb100525f61cce5', 'BloFin: Hot Wallet 1'), ('0xc1d13492285eb664951e201bf7c80c7c6318a1b5', 'SwftSwap'), ('0x2cff890f0378a11913b6129b2e97417a2c302680', 'NEAR Intents')):
    ctl[a] = n
out = []
for a, n in ctl.items():
    for action in ('txlist', 'tokentx'):
        rows = es.rows(action, a, sort='desc')
        hit = [r for r in rows if {r['from'].lower(), (r['to'] or '').lower()} & {DEP, HOT3}]
        out.append(dict(address=a, name=n, action=action, read=len(rows), first=min((int(r['timeStamp']) for r in rows), default=None), last=max((int(r['timeStamp']) for r in rows), default=None), hits=len(hit), tokens=len({r.get('tokenSymbol') for r in hit}), ex=[r['hash'] for r in hit[:3]]))
    print('control', a[:10], n, out[-2]['read'], out[-2]['hits'], out[-1]['read'], out[-1]['hits'], flush=True)
res['controls'] = out
# hot3 last rows towards dep and hot4, and dep's first funding
last_hot = es.rows('txlist', HOT3, sort='desc')
first_dep = es.rows('txlist', DEP, sort='asc')
res['hot3_to_dep'] = [r for r in last_hot if r['to'].lower() in (DEP, HOT4) or r['from'].lower() in (DEP, HOT4)][:20]
res['dep_first_rows'] = first_dep[:6]
print('hot3<->dep/hot4 in last hot3 rows', len(res['hot3_to_dep']), 'dep first', [(r['from'][:10], r['to'][:10], r['value'], r['timeStamp']) for r in first_dep[:4]], flush=True)
hot3_last_sent = [int(r['timeStamp']) for r in last_hot if r['from'].lower() == HOT3]
res['hot3_sent_after_2026_08_12'] = sum(t > 1786492800 for t in hot3_last_sent)
# B. Witnesses of the relay profile: senders to DEP around the sweep
ev, _ = es.window('txlist', DEP, start=SWEEP - 1500, end=SWEEP + 1500)
senders = sorted({r['from'].lower() for r in ev if r['to'].lower() == DEP and int(r['value']) > 0 and r['from'].lower() != RELAY} - set(p['dep_cp_tags']))
sample = rng.sample(senders, 60)
wit = []
for a in sample:
    tx = es.rows('txlist', a, sort='asc')
    ins = [r for r in tx if r['to'].lower() == a and int(r['value']) > 0]
    outs = [r for r in tx if r['from'].lower() == a]
    to_dep = [r for r in outs if r['to'].lower() == DEP and int(r['value']) > 0]
    delay = None
    if to_dep:
        before = [r for r in ins if int(r['timeStamp']) <= int(to_dep[0]['timeStamp'])]
        delay = int(to_dep[0]['timeStamp']) - int(before[-1]['timeStamp']) if before else None
    wit.append(dict(address=a, tx=len(tx), capped=len(tx) >= 1000, n_in=len(ins), n_out=len(outs), n_to_dep=len(to_dep), delay=delay, only_dep=bool(outs) and all(r['to'].lower() == DEP for r in outs), ratio=(int(to_dep[0]['value']) / int(ins[0]['value'])) if to_dep and ins and int(ins[0]['value']) else None, first_in_from=ins[0]['from'].lower() if ins else None))
res['witness_relay'] = wit
single = [w for w in wit if w['tx'] == 2 and w['n_in'] == 1 and w['n_out'] == 1 and w['n_to_dep'] == 1]
res['witness_relay_summary'] = dict(n=len(wit), population=len(senders), same_shape=len(single), median_delay_single=statistics.median(w['delay'] for w in single) if single else None, q1_delay=statistics.quantiles([w['delay'] for w in single], n=4)[0] if len(single) > 3 else None, q3_delay=statistics.quantiles([w['delay'] for w in single], n=4)[2] if len(single) > 3 else None, median_ratio=statistics.median(w['ratio'] for w in single if w['ratio']) if single else None, median_tx_all=statistics.median(w['tx'] for w in wit), only_dep=sum(w['only_dep'] for w in wit), reused_in=sum(w['n_in'] > 1 for w in wit), over_50_tx=sum(w['tx'] > 50 for w in wit))
print(res['witness_relay_summary'], flush=True)
rel = es.rows('txlist', RELAY, sort='asc')
res['relay_rows'] = rel
print('relay', [(r['from'][:10], r['to'][:10], r['value'], r['gasUsed'], r['gasPrice'], r['timeStamp'], r['isError']) for r in rel], flush=True)
# C. Properties on the other recipients in the same hot wallet window
outs = p['hot3_feb_usdc']['outs']
by = {}
for to, amount, t, h, sym in outs:
    by.setdefault(to, []).append((t, amount, h))
props = []
for a, pays in sorted(by.items()):
    pays.sort()
    rows, ok = es.window('tokentx', a, start=PAY1 - 300, end=PAY2 + 900, contract=USDC, max_pages=2)
    if not ok:
        props.append(dict(address=a, service_sized=True, pays=len(pays), two_within_10min=any(pays[i + 1][0] - pays[i][0] <= 600 for i in range(len(pays) - 1))))
        continue
    last_t, received = pays[-1][0], sum(x[1] for x in pays)
    sent = [(int(r['timeStamp']), int(r['value']) / 1e6, r['to'].lower()) for r in rows if r['from'].lower() == a and int(r['timeStamp']) >= pays[0][0]]
    q5 = sum(x[1] for x in sent if x[0] - last_t <= 300)
    q15 = sum(x[1] for x in sent if x[0] - last_t <= 900)
    props.append(dict(address=a, pays=len(pays), received=received, two_within_10min=any(pays[i + 1][0] - pays[i][0] <= 600 for i in range(len(pays) - 1)), fwd90_5min=q5 >= .9 * received, fwd90_15min=q15 >= .9 * received, first_dest=sent[0][2] if sent else None, service_sized=False))
res['recipient_props'] = props
n = [x for x in props if not x['service_sized']]
res['recipient_summary'] = dict(recipients=len(props), readable=len(n), service_sized=len(props) - len(n), two_within_10min=sum(x['two_within_10min'] for x in props), fwd90_5min=sum(x['fwd90_5min'] for x in n), fwd90_15min=sum(x['fwd90_15min'] for x in n))
print(res['recipient_summary'], flush=True)
dests = sorted({x['first_dest'] for x in n if x.get('first_dest')})
tags = {}
for i in range(0, len(dests), 200):
    s, b = arch.fetch('https://metadata.services.blockscout.com/api/v1/metadata?chainId=1&addresses=' + ','.join(dests[i:i + 200]), f'bs_recipdest_{i // 200:04d}.json')
    if s == 200:
        tags.update({a.lower(): [t['name'] for t in v.get('tags', [])] for a, v in json.loads(b).get('addresses', {}).items()})
res['recipient_dest_tags'] = tags
# D. Amount matches by chance
def around(rows, target, tol):
    return sum(abs(x[1] - target) <= tol * target for x in rows)
feb = p['hot3_feb_usdc']
hours = (feb['last'] - feb['first']) / 3600
res['amount_chance'] = dict(window_hours=hours, payouts=feb['n_out'], within_1pct_654=around(feb['outs'], 654.466304, .01), within_1pct_180=around(feb['outs'], 180.382489, .01), within_10pct_654=around(feb['outs'], 654.466304, .1), within_10pct_180=around(feb['outs'], 180.382489, .1))
ev_out = [(r['to'].lower(), int(r['value']) / 1e18) for r in ev if r['from'].lower() == DEP and int(r['value']) > 0]
span = (max(int(r['timeStamp']) for r in ev) - min(int(r['timeStamp']) for r in ev)) / 3600
res['amount_chance_dep'] = dict(window_hours=span, native_out=len(ev_out), within_5pct_payin=around(ev_out, .00241406, .05), within_10pct_payin=around(ev_out, .00241406, .10))
print(res['amount_chance'], res['amount_chance_dep'], flush=True)
# E. Second hop of the keys against the candidates
cand = {r['address'] for r in csv.DictReader(open(ROOT / 'state/universe_raw.csv')) if r['address'].startswith('0x')}
for a, v in p['dep_cp_tags'].items():
    if 'changenow' in ' '.join(v).lower():
        cand.add(a)
for a, v in p['hot3_cp_tags'].items():
    if 'changenow' in ' '.join(v).lower():
        cand.add(a)
hop = []
for t in json.load(open(ROOT / 'state/hop2_targets.json')):
    if not t['from_key']:
        continue
    a, c = t['address'], t['chain']
    hits = []
    for action in ('txlist', 'tokentx', 'txlistinternal'):
        hits += [dict(action=action, h=r['hash'], f=r['from'].lower(), to=(r['to'] or '').lower(), v=r['value'], sym=r.get('tokenSymbol'), t=r['timeStamp']) for r in es.rows(action, a, c) if {r['from'].lower(), (r['to'] or '').lower()} & cand]
    hop.append(dict(address=a, chain=c, senders=t['senders'], hits=hits))
    print('hop2', a[:10], c, t['senders'][0][:10], len(hits), flush=True)
res['hop2_hits'] = hop
(ROOT / 'state/p10.json').write_text(json.dumps(res))
print('done', flush=True)
