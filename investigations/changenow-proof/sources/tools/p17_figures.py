"""Every figure the reports quote that no earlier script stored: recomputed here, written to state/figures.json. Also archives repository metadata, direct label reads and node proofs of supporting transfers."""
import csv, datetime, gzip, hashlib, json, re, subprocess, sys, urllib.parse
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import arch, es, net
ROOT = Path(__file__).resolve().parent.parent
FT = Path.home() / 'Projects/PolySentinel-flow-trace'
INV = Path.home() / 'Projects/PolySentinel-investigation'
DIR = ROOT / 'evidence/onchain'
HOT3, DEP, HW4, RELAY = '0xdd3d72c53ff982ff59853da71158bf1538b3ceee', '0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b', '0xeba88149813bec1cccccfdb0dacefaaa5de94cb1', '0x7e67df45e0a0bab092cbb2ff045f8aa8dfab6e23'
KEY, BRACE, FUND, HTX = '0x101b5f4dc0886c32e2b75972101aeaf9f338fb65', '0xc852b0938f5ad79b640d105ed11c14499454af26', '0x3eaef6d5e91ecf7b7623eb19978e145ebd417013', '0x66d582e5e0670bd99153199f179733c6ee5d19be'
A, B, X = '0xa2768df0b1fb437d5d238d5d0e9b7ca584e84628', '0xb2c257557fd1c7a0738d7e9e2c953441f333b8fd', '0x077d360f11d220e4d5d831430c81c26c9be7c4a4'
USDC, USDT = '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48', '0xdac17f958d2ee523a2206206994597c13d831ec7'
T = lambda x: datetime.datetime.fromtimestamp(int(x), datetime.UTC).strftime('%Y-%m-%d %H:%M:%S')
fig = {}
# hot wallet rotation
hot = es.rows('txlist', HOT3, sort='desc')
fig['hot3_sent_per_hour'] = sorted(Counter(T(r['timeStamp'])[:13] for r in hot if r['from'].lower() == HOT3).items())
fig['hot3_sent_since_2026_08_12'] = sum(T(r['timeStamp']) >= '2026-08-12' for r in hot if r['from'].lower() == HOT3)
hw = es.rows('txlist', HW4, sort='desc')
fig['hw4_window'] = [T(hw[-1]['timeStamp']), T(hw[0]['timeStamp'])]
fig['hw4_sent_per_day'] = sorted(Counter(T(r['timeStamp'])[:10] for r in hw if r['from'].lower() == HW4).items())
fig['dep_first'] = {k: es.rows('txlist', DEP, sort='asc')[0][k] for k in ('hash', 'from', 'value', 'timeStamp')}
# balances
seen, rows = set(), []
with gzip.open(ROOT / 'state/study_rows.jsonl.gz', 'rt') as g:
    for line in g:
        r = json.loads(line)
        if r['chain'] == 1 and ((r['contract'] == USDC and KEY in (r['src'], r['dst'])) or (r['contract'] == USDT and BRACE in (r['src'], r['dst']))):
            k = (r['contract'], r['tx'], r['src'], r['dst'], r['raw'])
            if k not in seen:
                seen.add(k)
                rows.append(r)
rows.sort(key=lambda r: int(r['ts']) if str(r['ts']).isdigit() else 0)
bal, fig['key_usdc'], fig['brace_usdt'] = {USDC: 0, USDT: 0}, [], []
for r in rows:
    me = KEY if r['contract'] == USDC else BRACE
    bal[r['contract']] += int(r['raw']) * (1 if r['dst'] == me else -1)
    (fig['key_usdc'] if r['contract'] == USDC else fig['brace_usdt']).append(dict(utc=T(r['ts']), side='in' if r['dst'] == me else 'out', raw=r['raw'], other=r['src'] if r['dst'] == me else r['dst'], tx=r['tx'], balance_raw=bal[r['contract']]))
fig['key_fake_usdc_rows'] = None
names = Counter()
with gzip.open(ROOT / 'state/study_rows.jsonl.gz', 'rt') as g:
    fake = set()
    for line in g:
        r = json.loads(line)
        if r['kind'] == 'erc20' and KEY in (r['src'], r['dst']) and r['contract'] != USDC and r['token'] in ('USDC', 'ꓴꓢꓓС'):
            fake.add((r['tx'], r['contract']))
fig['key_fake_usdc_rows'] = len(fake)
fig['node_balances_key'] = {b: int(net.rpc('eth_getBalance', [KEY, hex(b)], 1), 16) for b in (26119419, 26119420, 26122382, 26122383)}
# downstream 0x66d582e5
tk = es.rows('tokentx', HTX, sort='asc')
real = [r for r in tk if r['contractAddress'].lower() in (USDC, USDT)]
outs = [r for r in real if r['from'].lower() == HTX]
ins = [r for r in real if r['to'].lower() == HTX]
tx = es.rows('txlist', HTX, sort='asc')
fig['htx_deposit'] = dict(stable_out=len(outs), out_to=Counter(r['to'].lower() for r in outs).most_common(2), stable_in=len(ins), senders=len({r['from'].lower() for r in ins}), first=T(tx[0]['timeStamp']), last=T(tx[-1]['timeStamp']), tx=len(tx), native_out_to=Counter(r['to'].lower() for r in tx if r['from'].lower() == HTX).most_common(2))
# funder grappe
ra = es.rows('txlist', A, sort='asc')
ia = [r for r in ra if r['to'] and r['to'].lower() == A and int(r['value']) > 0]
oa = [r for r in ra if r['from'].lower() == A and int(r['value']) > 0]
fig['a2768'] = dict(rows=len(ra), inflows=len(ia), senders=len({r['from'].lower() for r in ia}), recipients=len({r['to'].lower() for r in oa}), eth_in_wei=sum(int(r['value']) for r in ia), from_x_n=sum(r['from'].lower() == X for r in ia), from_x_wei=sum(int(r['value']) for r in ia if r['from'].lower() == X), first=T(ra[0]['timeStamp']), last=T(ra[-1]['timeStamp']))
rb = es.rows('txlist', B, sort='asc')
fig['b2c2_in'] = Counter(r['from'].lower() for r in rb if r['to'] and r['to'].lower() == B and int(r['value']) > 0).most_common()
RT = {'ChangeNOW 17': '0xd72cd83afba0dcfeff95d463adcb2b8def6aa623', 'Hot Wallet 4': HW4, 'ChangeNOW: Deposit Funder 9': '0x458c2a06ba8dc3def078513ad98e9da8ced39e02'}
fig['round_trips'] = {n: [dict(utc=T(r['timeStamp']), side='out' if r['from'].lower() == A else 'in', raw=r['value'], tx=r['hash']) for r in ra if c in (r['from'].lower(), (r['to'] or '').lower()) and int(r['value']) > 0] for n, c in RT.items()}
# fingerprint
p14 = json.load(open(ROOT / 'state/p14.json'))
sib = [x for x in p14['sib'] if x.get('to')]
FP = lambda x: x['gas_price'] == '1000000000' and x['gas'] == '22000' and 6 * 10 ** 13 <= x['diff'] <= 601 * 10 ** 11 and 400 <= x['delay'] <= 600
fig['sib'] = dict(tags=len(p14['sib']), two_tx=len(sib), fingerprint=sum(map(FP, sib)), swept_to=Counter(x['to'] for x in sib).most_common(), first_in=T(min(x['t_in'] for x in sib)), last_in=T(max(x['t_in'] for x in sib)), not_fp=[x['address'] for x in sib if not FP(x)], other=[(x['address'], x['tx']) for x in p14['sib'] if not x.get('to')])
ff = []
for a in ('0xc2cd4b1e89fe561702b72ff9329303a2dd0dc225', '0xfa1c172e5f8a7dbde93ac3bcb02ab164ecfa6a2b', '0x7a128903fbf43cf2b6121994c850a0103fcb5247'):
    t = es.rows('txlist', a, sort='asc')
    i = [x for x in t if x['to'] and x['to'].lower() == a and int(x['value']) > 0]
    o = [x for x in t if x['from'].lower() == a]
    ff.append(dict(address=a, gas=o[0]['gas'], gas_price=o[0]['gasPrice'], delay=int(o[0]['timeStamp']) - int(i[0]['timeStamp']), diff=int(i[0]['value']) - int(o[0]['value']), to=o[0]['to'].lower()))
fig['fixedfloat_dep'] = ff
fig['fixedfloat_dep_fingerprint'] = sum(map(FP, ff))
p13 = json.load(open(ROOT / 'state/p13.json'))
same = sum(c['same_shape'] for c in p13['controls'])
fp = sum(c['fingerprint'] for c in p13['controls'])
n = same + len(ff)
fig['controls'] = dict(sampled=sum(c['sampled'] for c in p13['controls']), same_shape=same, fingerprint=fp, with_ff_dep=n, upper95_one_sided_9=1 - .05 ** (1 / same), upper95_one_sided_12=1 - .05 ** (1 / n))
# local searches, literal
lit = dict(files=0, with_changenow=0, order_terms=0)
TERMS = re.compile(rb'payinHash|payoutHash|payinAddress|payoutAddress|exchangeId|changenow\.io/exchange/txs', re.I)
for base in (FT / 'state/http_cache', INV / 'state/http_cache'):
    for p in base.rglob('*.json.gz'):
        lit['files'] += 1
        b = gzip.open(p, 'rb').read()
        lit['with_changenow'] += b'changenow' in b.lower()
        lit['order_terms'] += bool(TERMS.search(b))
fig['cache_literal'] = lit
hits = {}
for label, root in (('flow-trace', FT), ('investigation', INV), ('audit', Path.home() / 'Projects/PolySentinel-audit-20261102'), ('cn_pm_sakana', Path.home() / 'Documents/Crypto/cn_pm_sakana')):
    r = subprocess.run(['grep', '-rIlE', 'payinHash|payoutHash|payinAddress|payoutAddress|changenow\\.io/exchange/txs', str(root)], capture_output=True, text=True)
    hits[label] = r.stdout.split()
fig['order_terms_files'] = hits
# calldata of every node proof on file
long_input = []
files = list(DIR.glob('*.json'))
for p in files:
    i = json.loads(p.read_bytes())['tx']['input']
    if len(i) not in (2, 138):
        long_input.append((p.stem, len(i)))
fig['calldata'] = dict(proofs=len(files), non_standard=long_input)
# repositories
meta = {}
for r in 'blockscout/swaggers dawsbot/eth-labels blockchain-etl/ethereum-etl blockscout/mcp-server ChangeNow-io/ChangeNOW-api-python QuantumDev-CERN/Automated-Vasp-Atrribution-Engine Xaxrich/okx-ai-quant-lab opun/amlbot-agent'.split():
    a = subprocess.run(['gh', 'api', f'repos/{r}', '--jq', '{full_name,archived,pushed_at,created_at,stars:.stargazers_count,open_issues:.open_issues_count,license:.license.spdx_id,default_branch}'], capture_output=True, text=True).stdout
    c = subprocess.run(['gh', 'api', f'repos/{r}/commits?per_page=1', '--jq', '.[0]|{sha:.sha,date:.commit.committer.date,msg:(.commit.message|split("\\n")[0])}'], capture_output=True, text=True).stdout
    meta[r] = dict(repo=json.loads(a or '{}'), last_commit=json.loads(c or '{}'))
(ROOT / 'evidence/repos/repos_metadata.json').write_text(json.dumps(dict(read_utc=datetime.datetime.now(datetime.UTC).strftime('%Y-%m-%dT%H:%M:%SZ'), repos=meta), indent=1))
# direct label read, including the addresses used as references
lab = [X, A, B, HW4, HOT3, DEP, '0xd72cd83afba0dcfeff95d463adcb2b8def6aa623', '0x59855c07cdd4924609df4f5f175da3188699932f', '0xa12e1462d0ced572f396f58b6e2d03894cd7c8a4', '0x48c04ed5691981c42154c6167398f95e8f38a7ff', '0x6ba7fe01eec4c6a4308c8e2b35970e0488ce9a86', '0x4778480c6c46521c41f7e4f2318f884b157cb1c9', '0x3525d3a883f743ca146288c146de7ccd59d48bf5', '0x458c2a06ba8dc3def078513ad98e9da8ced39e02']
s, b = arch.fetch('https://metadata.services.blockscout.com/api/v1/metadata?chainId=1&addresses=' + ','.join(lab), 'bs_labels_direct.json')
fig['labels_direct'] = {a.lower(): [dict(name=t['name'], type=t['tagType'], meta=t['meta'][:200]) for t in v['tags']] for a, v in json.loads(b)['addresses'].items()}
# node proofs of supporting transfers
want = [(1, r['tx']) for r in fig['key_usdc'] if r['tx'].startswith(('0xf2a54e357a14', '0x4f7bf1ca04'))] + [(1, r['tx']) for r in fig['brace_usdt'] if r['tx'].startswith(('0x1a6beb1e35', '0x5ed83ab342'))]
want += [(1, r['hash']) for r in outs if r['hash'].startswith('0x7ef5aa477f')]
want += [(1, r['hash']) for r in es.rows('tokentx', '0x6b33c41cac7db6726dd1240bc8bbce5e6dbb2180') if r['from'].lower() == '0x6b33c41cac7db6726dd1240bc8bbce5e6dbb2180']
for n_, trips in fig['round_trips'].items():
    want += [(1, x['tx']) for x in trips]
want += [(1, r['hash']) for r in rb if r['from'].lower() == HW4]
polygon = [r['tx'] for r in map(json.loads, gzip.open(ROOT / 'state/study_rows.jsonl.gz', 'rt')) if r['chain'] == 137 and r['dst'] == '0x4958f6c329b61404b1cfd0ec8a44600a9486bd0a' and r['kind'] == 'erc20']
want += [(137, h) for h in sorted(set(polygon))]
out = []
for chain, h in sorted(set(want)):
    t = net.rpc('eth_getTransactionByHash', [h], chain)
    rc = net.rpc('eth_getTransactionReceipt', [h], chain)
    bl = net.rpc('eth_getBlockByNumber', [t['blockNumber'], False], chain)
    body = json.dumps(dict(chain_id=chain, tx=t, receipt=rc, block=dict(number=t['blockNumber'], timestamp=int(bl['timestamp'], 16), hash=bl['hash'])), sort_keys=True).encode()
    (DIR / f'{h}.json').write_bytes(body)
    logs = [dict(contract=l['address'].lower(), src='0x' + l['topics'][1][-40:], dst='0x' + l['topics'][2][-40:], raw=str(int(l['data'], 16)), log_index=int(l['logIndex'], 16)) for l in rc['logs'] if l['topics'] and l['topics'][0].startswith('0xddf252ad') and len(l['topics']) == 3 and l['data'] != '0x']
    out.append(dict(chain_id=chain, tx=h, block=int(t['blockNumber'], 16), utc=T(int(bl['timestamp'], 16)), status=int(rc['status'], 16), src=t['from'].lower(), dst=(t['to'] or '').lower(), value=str(int(t['value'], 16)), logs=logs, sha256=hashlib.sha256(body).hexdigest()))
    print(out[-1]['utc'], chain, h[:14], out[-1]['status'], len(logs), flush=True)
fig['supporting_proofs'] = out
(ROOT / 'state/figures.json').write_text(json.dumps(fig, indent=0, default=str))
print({k: fig[k] for k in ('sib', 'controls', 'cache_literal', 'order_terms_files', 'calldata', 'fixedfloat_dep_fingerprint', 'hot3_sent_since_2026_08_12', 'key_fake_usdc_rows', 'htx_deposit', 'a2768')})
