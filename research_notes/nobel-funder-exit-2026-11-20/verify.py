"""Offline re-check of every figure in REPORT.md, from the saved pages of this folder only. Exit code 1 on any failure.

Network access is blocked for the whole run: a page or response that is not saved makes a check fail, never a fetch.
A  integrity: manifests, gzip pages against their SHA-256, the Relay archive page, and the file list in SHA256SUMS.
B  reproduction: case outputs, replay.json, relay/relay_check.csv and native/summary.json re-derived byte for byte.
C  counts of the walk package.
D  figures quoted in REPORT.md, in raw token units, from the saved outputs and pages.
E  cross-case join: data/cross_case_hits.csv against the addresses met and the indexer tags.
F  negative self-tests: a corrupted copy of one page, and a copy with one page removed, must fail.
usage: python3 -I verify.py
"""
import csv
import gzip
import hashlib
import importlib.util
import io
import json
import shutil
import socket
import sys
import tempfile
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

sys.dont_write_bytecode = True  # a __pycache__ folder in the repository breaks the publication checks
HERE = Path(__file__).resolve().parent
TOOLS = HERE.parents[1] / 'integrations' / 'forensic-intelligence'
sys.path.insert(0, str(TOOLS))


def no_network(*args, **kwargs):
    raise RuntimeError('network call attempted during offline verification')


socket.socket.connect = no_network
socket.create_connection = no_network
urllib.request.urlopen = no_network
import value_trace as vt  # noqa: E402
import relay_check as rc  # noqa: E402

vt.http = no_network
spec = importlib.util.spec_from_file_location('native_history', HERE / 'native_history.py')
nh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nh)
nh.http = no_network

CASE, RELAY, NATIVE = HERE / 'case', HERE / 'relay', HERE / 'native'
TREASURY = '0xb282b48ae713fa2201282e298f3393130c4f851d'
RECIPIENT = '0x0d40d7cb8e1245c2aefde329375ed2d09377dcc1'
HOP2 = '0x15ff50f3915e0f8410a8b1c0055fcce706de3c93'
SIDE = '0x3d266394f4073959a6689c7be58c88635b570322'
H3A = '0x919be4210a82644fbfbd42cbf88faf00de5c0769'
H3B = '0x710cbbf21ae317f6a5f3c0789f218bf3c7d11749'
H3C = '0xa25ffd0694c123e40f0223c5143d2d95d2b6cc29'
SEVEN = [TREASURY, RECIPIENT, HOP2, SIDE, H3A, H3B, H3C]
DOWNSTREAM = {HOP2, SIDE, H3A, H3B, H3C}
DEPOSITORY = '0x4cd00e387622c35bddb9b4c962c136462338bc31'
SOLVER = '0xf70da97812cb96acdf810712aa562db8dfa3dbef'
SWAPS = '0x74de5d4fcbf63e00296fd95d33236b9794016631'
USDC_POLYGON = '0x3c499c542cef5e3811e1192ce70d8cc03d5c3359'
USDT = '0xdac17f958d2ee523a2206206994597c13d831ec7'
SINK = '0x2640104d54a4ae88f043dcea854ff472ec318036'
TERMINAL_CITED = '0x6d988d1233c72ce43b1e344314cbd736ba60509c'
FUNDER, SOURCE = '0xe206961002feebd9edb152eed9b630a351874043', '0x3e2c6d068fc6958684e836998285e3a836dbd96f'
RESULTS = []


def check(name, ok, detail=''):
    RESULTS.append((name, bool(ok), detail))


def guarded(name, fn):
    """Run one check body; an exception (a missing page, a network attempt) is a FAIL, not a crash."""
    try:
        fn()
    except Exception as exc:  # reported as a failed check
        check(name, False, repr(exc)[:200])


def manifest_problems(folder, raw_name=lambda entry: f"raw/{entry['name']}.json.gz", key='name'):
    """Problems of one manifest.jsonl: duplicate names, missing or altered pages, wrong lengths, unlisted pages."""
    entries = [json.loads(line) for line in (folder / 'manifest.jsonl').read_text().splitlines()]
    problems = []
    if len({e[key] for e in entries}) != len(entries):
        problems.append('duplicate names')
    listed = set()
    for entry in entries:
        page = folder / raw_name(entry)
        listed.add(page.name)
        if not page.exists():
            problems.append(f'missing {page.name}')
            continue
        body = gzip.decompress(page.read_bytes())
        if hashlib.sha256(body).hexdigest() != entry['sha256_body'] or len(body) != entry['bytes']:
            problems.append(f'altered {page.name}')
    unlisted = {p.name for p in (folder / 'raw').glob('*')} - listed
    if unlisted:
        problems.append(f'unlisted {sorted(unlisted)[:3]}')
    return entries, problems


def lines(rows, fields):
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def table(path):
    return list(csv.DictReader(Path(path).read_text().splitlines()))


# A. integrity
def a_manifests():
    for folder, expected in ((CASE, 333), (RELAY, 32), (NATIVE, 52)):
        entries, problems = manifest_problems(folder)
        check(f'A1 {folder.name}/manifest.jsonl: {expected} unique pages, each present, unaltered and listed',
              len(entries) == expected and not problems, f'{len(entries)} entries, problems {problems[:3]}')


def a_relay_archive():
    entries, problems = manifest_problems(RELAY / 'archive', raw_name=lambda e: e['file'], key='file')
    entry = entries[0] if len(entries) == 1 else {}
    check('A2 relay/archive: one Relay page, sha256 25c787af0ec5..., 36655 bytes, 4 requests, complete, neutral label',
          len(entries) == 1 and not problems and entry['sha256_body'].startswith('25c787af0ec5') and entry['bytes'] == 36655
          and entry['n_requests'] == 4 and entry['complete'] is True
          and entry['label'] == 'nobel-c7 treasury address (investigations/followup-20261113)', f'problems {problems}')


def a_sha256sums():
    listed = {}
    for line in (HERE / 'SHA256SUMS').read_text().splitlines():
        digest, name = line.split('  ', 1)
        listed[name] = digest
    on_disk = {str(p.relative_to(HERE)) for p in HERE.rglob('*') if p.is_file() and p.name not in ('SHA256SUMS', 'REPORT.md', 'verify.py')}
    bad = [n for n, d in listed.items() if not (HERE / n).is_file() or hashlib.sha256((HERE / n).read_bytes()).hexdigest() != d]
    check('A3 SHA256SUMS: every data file and stored .gz page listed, every listed file matches its file-level SHA-256',
          set(listed) == on_disk and not bad, f'{len(listed)} files, mismatched {bad[:3]}, unlisted {sorted(on_disk - set(listed))[:3]}')


for name, fn in (('A1 manifests', a_manifests), ('A2 relay archive', a_relay_archive), ('A3 SHA256SUMS', a_sha256sums)):
    guarded(name, fn)


# B. reproduction
def b_case():
    outputs = vt.compute(CASE, offline=True)
    different = [n for n, body in outputs.items() if (CASE / n).read_bytes() != body]
    check('B1 compute(case, offline) reproduces evidence_edges.csv, path.csv, nodes.json, labels.json, package.json byte for byte',
          sorted(outputs) == ['evidence_edges.csv', 'labels.json', 'nodes.json', 'package.json', 'path.csv'] and not different, f'differs: {different}')
    package = json.loads((CASE / 'package.json').read_text())
    check('B2 package.json outputs_sha256 matches the four saved outputs',
          all(hashlib.sha256((CASE / n).read_bytes()).hexdigest() == d for n, d in package['outputs_sha256'].items()) and len(package['outputs_sha256']) == 4)


def b_replay():
    replayed = vt.replay(CASE, write=False, offline=True)
    check('B3 replay(case, offline) re-derives replay.json byte for byte from the saved receipts',
          (json.dumps(replayed, indent=1, sort_keys=True) + '\n').encode() == (CASE / 'replay.json').read_bytes())


def b_relay():
    rows = rc.check(str(RELAY / 'archive'), str(RELAY), [TREASURY], write=False, offline=True)
    check('B4 relay_check.check(offline) re-derives relay/relay_check.csv byte for byte', lines(rows, rc.FIELDS) == (RELAY / 'relay_check.csv').read_text())


def b_native():
    summary = nh.summarize(str(NATIVE), json.loads((NATIVE / 'config.json').read_text()), offline=True)
    check('B5 native_history.summarize(offline) re-derives native/summary.json byte for byte',
          json.dumps(summary, indent=1) + '\n' == (NATIVE / 'summary.json').read_text())


for name, fn in (('B1 case outputs', b_case), ('B3 replay', b_replay), ('B4 relay_check', b_relay), ('B5 native summary', b_native)):
    guarded(name, fn)

# C. counts
package = json.loads((CASE / 'package.json').read_text())
edges = table(CASE / 'evidence_edges.csv')
path = table(CASE / 'path.csv')
replay = json.loads((CASE / 'replay.json').read_text())
labels = json.loads((CASE / 'labels.json').read_text())
nodes = json.loads((CASE / 'nodes.json').read_text())
node = {n['address']: n for n in nodes['read']}
summary = json.loads((NATIVE / 'summary.json').read_text())
relay_rows = table(RELAY / 'relay_check.csv')
positive = [e for e in edges if int(e['raw_amount']) > 0 and e['from'].lower() != e['to'].lower()]
met = {e['from'].lower() for e in edges} | {e['to'].lower() for e in edges}

check('C1 package: 7 addresses read, 141 pages, 6777 edges, 48 path edges, 0 spoofed token items, 48 receipts ok, 0 failed',
      (package['addresses_read'], package['pages_read'], package['edges'], package['path_edges'], package['spoofed_token_items_skipped'],
       package['receipts_replayed_ok'], package['receipts_replayed_failed']) == (7, 141, 6777, 48, 0, 48, 0))
check('C2 edges: 6729 CANDIDATE and 48 ONCHAIN_CONFIRMED, all of them official USDT',
      Counter(e['evidence_level'] for e in edges) == {'CANDIDATE': 6729, 'ONCHAIN_CONFIRMED': 48} and {e['token_contract'].lower() for e in edges} == {USDT})
check('C3 path: 48 rows, depths {0:5, 1:3, 2:10, 3:9, 4:21}, every row ONCHAIN_CONFIRMED',
      len(path) == 48 and Counter(int(p['depth']) for p in path) == {0: 5, 1: 3, 2: 10, 3: 9, 4: 21} and all(p['evidence_level'] == 'ONCHAIN_CONFIRMED' for p in path))
check('C4 replay: 48 of 48 ok on 2 endpoints each, 43 signed by the sending holder',
      len(replay) == 48 and all(v['ok'] and v['endpoints'] == 2 for v in replay.values()) and sum(v['holder_signed'] for v in replay.values()) == 43)
check('C5 labels: 18 tagged addresses met; 1230 distinct addresses in the edges', len(labels) == 18 and len(met) == 1230, f'{len(labels)} labels, {len(met)} addresses')
check('C6 nodes: the 7 wallets read, each ledger complete and none overdrawn; 15 terminals',
      sorted(node) == sorted(SEVEN) and all(n['ledger_complete'] and not n['overdrawn'] for n in nodes['read']) and len(nodes['terminals']) == 15)


def raw(amount):
    whole, _, frac = amount.lstrip('-').partition('.')
    return int(whole + frac.ljust(6, '0')[:6])


def rows_of(sender, depth=None):
    return [p for p in path if p['from'].lower() == sender and (depth is None or int(p['depth']) == depth)]


def secs(a, b):
    return (datetime.fromisoformat(b[:19]) - datetime.fromisoformat(a[:19])).total_seconds()


flow = defaultdict(int)
for e in positive:
    flow[(e['from'].lower(), e['to'].lower())] += int(e['raw_amount'])


# D. figures
def d_relay():
    usdt = [r for r in relay_rows if r['currency'] in (USDC_POLYGON, USDT)]
    origin = [r for r in usdt if r['side'] == 'origin']
    dest = [r for r in usdt if r['side'] == 'destination']
    paid, got = sum(int(r['amount_raw']) for r in origin), sum(int(r['amount_raw']) for r in dest)
    check('D1 Relay: three USDC->USDT orders paid 330,025.963260 (5.000000 + 165,093.028144 + 164,927.935116) and delivered 329,426.024331',
          len(origin) == len(dest) == 3 and paid == 330025963260 and got == 329426024331
          and sorted(int(r['amount_raw']) for r in origin) == [5000000, 164927935116, 165093028144], f'{paid} {got}')
    check('D2 Relay: the two main orders are 330,020.963260 (the followup figure); cost 599.938929, 0.18 %',
          paid - 5000000 == 330020963260 and paid - got == 599938929 and round((paid - got) / paid * 100, 2) == 0.18)
    check('D3 Relay: all 6 USDT-order legs verified, payments to the depository, deliveries from the Relay solver, all at the treasury',
          all(r['verified'] == 'true' for r in usdt) and {r['counterparty'] for r in origin} == {DEPOSITORY}
          and {r['counterparty'] for r in dest} == {SOLVER} and {r['user'].lower() for r in usdt} | {r['recipient'].lower() for r in usdt} == {TREASURY})
    native = [r for r in relay_rows if r['currency'] == '0x' + '0' * 40]
    o = [r for r in native if r['side'] == 'origin']
    d = [r for r in native if r['side'] == 'destination']
    check('D4 Relay gas order 03:55:49: origin 0.002339 ETH verified, destination 65.04 POL NOT_CHECKED',
          len(o) == len(d) == 1 and o[0]['verified'] == 'true' and int(o[0]['amount_raw']) == 2338583016118224 and round(2338583016118224 / 1e18, 6) == 0.002339
          and d[0]['verified'] == 'NOT_CHECKED' and round(int(d[0]['amount_raw']) / 1e18, 2) == 65.04 and o[0]['created_utc'].startswith('2026-04-15T03:55:49'))


def d_conversions():
    t = summary['transactions']
    a = t['0xd55b7273d43b58965b19928d4a8dffb38b71f1d233acb8f412134cd7aaab5d4e']
    b = t['0x9db96bdea5c28cf8024fb738bc17e0b633bc1f6576beb0ac45234afb1660b6af']
    c = t['0x4a5b521a8023b6fded3647bcada55da85e8a53746b995bccac9502eb83db20f7']

    def legs(items, token, frm=None, to=None):
        return [int(x['raw_amount']) for x in items if x['token'] == token and (frm is None or x['from'].lower() == frm) and (to is None or x['to'].lower() == to)]
    moves = summary['addresses']['treasury']['native_moves']
    eth_out = [int(m['wei']) for m in moves if m['transaction_hash'] == '0x9db96bdea5c28cf8024fb738bc17e0b633bc1f6576beb0ac45234afb1660b6af' and m['direction'] == 'out']
    check('D5 conversions: 39,983.213328 USDC -> 39,611.487618 USDT; 6.945045 ETH -> 16,046.604562 MUSD -> 15,898.082270 USDT',
          legs(a, 'USDC', frm=TREASURY) == [39983213328] and legs(a, 'USDT', to=TREASURY) == [39611487618]
          and len(eth_out) == 1 and round(eth_out[0] / 1e18, 6) == 6.945045 and legs(b, 'MUSD', to=TREASURY) == [16046604562]
          and legs(c, 'MUSD', frm=TREASURY) == [16046604562] and legs(c, 'USDT', to=TREASURY) == [15898082270])
    first = summary['addresses']['treasury']['first_native_inflow']
    check('D6 funder inflow: 6.950374 ETH from the funder; USDC paid in the conversion is 0.000100 above the published 39,983.213228',
          first['counterparty']['address'].lower() == FUNDER and round(int(first['wei']) / 1e18, 6) == 6.950374 and 39983213328 - 39983213228 == 100)
    check('D7 treasury keeps 0.000471 ETH (native balance 471360852894747 wei when read)',
          summary['addresses']['treasury']['native_balance_wei_when_read'] == '471360852894747' and round(471360852894747 / 1e18, 6) == 0.000471)


def d_seed_and_treasury():
    seed = [p for p in path if p['depth'] == '0']
    total = sum(raw(p['amount']) for p in seed)
    check('D8 seed: 5 rows totalling 384,935.594219 = three Relay deliveries + two conversions',
          len(seed) == 5 and total == 384935594219 == 329426024331 + 39611487618 + 15898082270 and {p['to'].lower() for p in seed} == {TREASURY})
    n = node[TREASURY]
    check('D9 treasury USDT: in 384,936.600888, out 384,936.596888, 0.004000 left, 19 transfers, 2 senders above dust, 1 recipient',
          (n['in_total'], n['out_total'], n['balance_from_ledger'], n['transfers'], n['senders_above_dust'], n['recipients'])
          == ('384936.600888', '384936.596888', '0.004000', 19, 2, 1))
    check('D10 non-seed inflow 1.006669 (bait and dust); sent minus seed 1.002669',
          raw(n['in_total']) - total == 1006669 and raw(n['out_total']) - total == 1002669)
    check('D11 seed senders are the only tagged addresses on the path: Relay solver and MetaMask Swaps spender',
          {p['from'].lower() for p in seed} == {SOLVER, SWAPS} and 'Relay: Solver' in labels[SOLVER]['tags'] and 'MetaMask: Swaps Spender' in labels[SWAPS]['tags']
          and {a for p in path for a in (p['from'].lower(), p['to'].lower()) if a in labels} == {SOLVER, SWAPS})


def d_hops():
    hop1 = sorted(rows_of(TREASURY, 1), key=lambda p: int(p['block_number']))
    check('D12 hop 1: 1.000000, 369,000.000000, 15,935.596888 in blocks 24895557/569/601, 23:02:59 to 23:11:47, signed by the treasury',
          [(p['amount'], p['block_number'], p['timestamp_utc'][11:19]) for p in hop1]
          == [('1.000000', '24895557', '23:02:59'), ('369000.000000', '24895569', '23:05:23'), ('15935.596888', '24895601', '23:11:47')]
          and all(p['to'].lower() == RECIPIENT and replay[f"1:{p['transaction_hash'].lower()}:{p['log_index']}"]['holder_signed'] for p in hop1)
          and [p['transaction_hash'][:10] for p in hop1] == ['0xe3f4e53f', '0x2bdde555', '0x255d7864'])
    check('D13 hop 1 sums: 384,936.596888 sent, 384,935.594219 followed under both conventions',
          sum(raw(p['amount']) for p in hop1) == 384936596888 and sum(raw(p['tracked_others_first']) for p in hop1) == 384935594219 == sum(raw(p['tracked_first']) for p in hop1))
    bait = [e for e in edges if e['transaction_hash'].lower().startswith('0x2d00554b')]
    lookalikes = node[TREASURY]['lookalike_counterparties']
    check('D14 bait: 1.000000 official USDT from 0x0D4015Ad to the treasury at 23:04:35, 96 s after the test and 48 s before the 369,000; 3 look-alikes of the recipient',
          len(bait) == 1 and bait[0]['from'].lower().startswith('0x0d4015ad') and bait[0]['to'].lower() == TREASURY and bait[0]['raw_amount'] == '1000000'
          and bait[0]['timestamp_utc'] == '2026-04-16T23:04:35Z' and bait[0]['evidence_level'] == 'CANDIDATE'
          and secs(hop1[0]['timestamp_utc'], bait[0]['timestamp_utc']) == 96 and secs(bait[0]['timestamp_utc'], hop1[1]['timestamp_utc']) == 48
          and len(lookalikes) == 1 and sorted(a[:10] for a in lookalikes[0]) == ['0x0d4015ad', '0x0d4066c1', '0x0d4069d5', '0x0d40d7cb'])
    table_rows = [(p['depth'], p['timestamp_utc'], p['from'].lower(), p['to'].lower(), p['amount'], p['tracked_others_first'], p['tracked_first'])
                  for p in rows_of(RECIPIENT, 2) + rows_of(HOP2, 3) if raw(p['amount']) >= 10000000000 and p['timestamp_utc'] < '2026-04-18']
    check('D15 hop table: the six rows of hops 2 and 3 on 16 and 17 April exact',
          table_rows == [('2', '2026-04-16T23:17:59Z', RECIPIENT, HOP2, '370000.000000', '369650.523377', '370000.000000'),
                         ('2', '2026-04-17T15:50:35Z', RECIPIENT, SIDE, '20000.000000', '12285.380131', '14935.594219'),
                         ('3', '2026-04-16T23:59:23Z', HOP2, H3B, '139300.000000', '95349.898491', '139300.000000'),
                         ('3', '2026-04-17T00:19:23Z', HOP2, H3A, '173652.000000', '173651.992570', '173652.000000'),
                         ('3', '2026-04-17T00:56:59Z', HOP2, H3A, '34783.000000', '34782.990313', '34783.000000'),
                         ('3', '2026-04-17T01:10:11Z', HOP2, H3A, '65865.000000', '65864.992983', '22265.000000')], str(table_rows[:2]))
    rest = [p for p in rows_of(RECIPIENT, 2) if raw(p['amount']) < 10000000000 and raw(p['tracked_others_first'])]
    check('D16 others-first remainder: 2,999.690711 in 8 payments below 10,000 USDT, 19 April to 18 June 2026; followed-first sends none of them',
          len(rest) == 8 and sum(raw(p['tracked_others_first']) for p in rest) == 2999690711 == 384935594219 - 369650523377 - 12285380131
          and rest[0]['timestamp_utc'].startswith('2026-04-19') and rest[-1]['timestamp_utc'].startswith('2026-06-18')
          and not any(raw(p['tracked_first']) for p in rest))
    hop3 = [p for p in rows_of(HOP2, 3) if p['timestamp_utc'] <= '2026-04-17T01:10:11Z']
    check('D17 hop 3: 413,600 out of 0x15fF between 23:59:23 and 01:10:11, within 1 h 52 min of receiving the 370,000',
          sum(raw(p['amount']) for p in hop3) == 413600000000 and {p['to'].lower() for p in hop3} == {H3A, H3B}
          and len(hop3) == 4 and hop3[0]['timestamp_utc'] == '2026-04-16T23:59:23Z' and 112 * 60 <= secs('2026-04-16T23:17:59Z', hop3[-1]['timestamp_utc']) < 113 * 60)
    balance = 0
    for e in sorted(positive, key=lambda e: (int(e['block_number']), int(e['log_index']))):
        if int(e['block_number']) >= 24895557:
            break
        balance += int(e['raw_amount']) * ((e['to'].lower() == RECIPIENT) - (e['from'].lower() == RECIPIENT))
    check('D18 recipient held 348.473326 USDT of its own before block 24895557', balance == 348473326, str(balance))
    first = rows_of(H3B, 4)[0]
    check('D19 first 100,000 that 0x710C sent on: 0 under others first, 100,000 under followed first',
          (first['amount'], first['tracked_others_first'], first['tracked_first']) == ('100000.000000', '0.000000', '100000.000000'))


def d_wallets():
    expected = {TREASURY: (19, 2, 1, '384936.60', '2026-04-15', '2026-04-23'), RECIPIENT: (222, 6, 25, '598854.50', '2026-04-03', '2026-10-21'),
                HOP2: (644, 13, 14, '1424898.59', '2026-02-28', '2026-05-03'), SIDE: (895, 42, 21, '3573288.98', '2025-10-09', '2026-05-21'),
                H3A: (191, 12, 22, '1183722.75', '2026-03-03', '2026-07-10'), H3B: (3281, 70, 14, '4285814.63', '2026-01-28', '2026-05-01'),
                H3C: (544, 23, 20, '2267642.85', '2025-12-10', '2026-11-09')}
    got = {a: (n['transfers'], n['senders_above_dust'], n['recipients'], f"{raw(n['in_total']) / 1e6:.2f}", n['first_utc'][:10], n['last_utc'][:10]) for a, n in node.items()}
    check('D20 wallet table: transfers, senders above 1 USDT, recipients, USDT in and active dates of the 7 wallets', got == expected,
          str({a[:6]: v for a, v in got.items() if v != expected.get(a)}))
    check('D21 the downstream wallets have 12 to 70 senders above 1 USDT; the recipient has 6, the treasury among them',
          sorted(node[a]['senders_above_dust'] for a in DOWNSTREAM) == [12, 13, 23, 42, 70] and node[RECIPIENT]['senders_above_dust'] == 6
          and flow[(TREASURY, RECIPIENT)] > 1000000)
    pairs = {(SIDE, HOP2): 377457000000, (SIDE, H3A): 482065000000, (HOP2, H3C): 495996000000, (HOP2, H3A): 299681611334,
             (HOP2, H3B): 173130000000, (H3A, H3C): 282500008387, (H3C, H3B): 980617069024, (H3B, SINK): 2722000000000}
    check('D22 pairwise flows: 377,457 / 482,065 / 495,996 / 299,681.611334 / 173,130 / 282,500.008387 / 980,617.069024 / 2,722,000',
          all(flow[k] == v for k, v in pairs.items()) and SINK not in labels
          and max((v, b) for (a, b), v in flow.items() if a == H3B)[1] == SINK, str({(a[:6], b[:6]): flow[(a, b)] for a, b in pairs if flow[(a, b)] != pairs[(a, b)]}))
    tagged = defaultdict(int)
    for e in positive:
        if e['to'].lower() in DOWNSTREAM and e['from'].lower() in labels:
            tagged[e['from'].lower()] += int(e['raw_amount'])
    by_tag = {next(t for t in labels[a]['tags'] if t in ('Coinbase10', 'Binance 14', 'Binance 15', 'FixedFloat: Hot Wallet 2', 'MEXC 21')): v
              for a, v in tagged.items() if set(labels[a]['tags']) & {'Coinbase10', 'Binance 14', 'Binance 15', 'FixedFloat: Hot Wallet 2', 'MEXC 21'}}
    check('D23 tagged senders into the downstream wallets: Coinbase 10 443,945.721492, Binance 14 160,076.57, Binance 15 157,814.70, FixedFloat 41,886.851, MEXC 21 7,518.281416',
          by_tag == {'Coinbase10': 443945721492, 'Binance 14': 160076570000, 'Binance 15': 157814700000, 'FixedFloat: Hot Wallet 2': 41886851000, 'MEXC 21': 7518281416}, str(by_tag))
    check('D24 no public tag on the 7 wallets, nor on any terminal',
          not any(n['label'] and n['label']['tags'] for n in nodes['read']) and not any(t['label'] and t['label']['tags'] for t in nodes['terminals']))
    into = defaultdict(int)
    for e in positive:
        if e['to'].lower() == RECIPIENT:
            into[e['from'].lower()] += int(e['raw_amount'])
    rhino = [a for a in into if a in labels and 'Rhino.fi' in labels[a]['tags']]
    chainflip = [a for a in into if a in labels and 'Chainflip' in labels[a]['tags']]
    check('D25 recipient USDT sources: treasury 64 %, Rhino.fi bridge 85,441.00, Chainflip vault 82,615.60',
          round(into[TREASURY] / sum(into.values()) * 100) == 64 and len(rhino) == len(chainflip) == 1
          and f'{into[rhino[0]] / 1e6:.2f}' == '85441.00' and f'{into[chainflip[0]] / 1e6:.2f}' == '82615.60')
    pay = sorted((e['timestamp_utc'], int(e['raw_amount'])) for e in positive if e['from'].lower() == RECIPIENT and e['to'].lower() == SIDE)
    r = summary['addresses']['recipient']
    first = r['first_native_inflow']
    check('D26 recipient first native coin 0.22 ETH from 0x3D26 at 2026-04-05T17:07:59Z; 52,005 USDT to 0x3D26 1 h 41 min later; eleven days to 16 April',
          first['time_utc'] == '2026-04-05T17:07:59Z' and first['wei'] == '220000000000000000' and first['counterparty']['address'].lower() == SIDE
          and pay[0][1] == 52005000000 and round(secs(first['time_utc'], pay[0][0]) / 60) == 101 and r['first_transaction_utc'] == first['time_utc']
          and (datetime(2026, 4, 16) - datetime(2026, 4, 5)).days == 11)
    gemini = [m for m in r['native_moves'] if 'Gemini 9' in m['counterparty']['tags']]
    check('D27 recipient: EIP-7702 delegation to 0x63c0c19a (EIP7702StatelessDeleGator), 598 transactions read completely, 5 April to 17 November 2026, 7.65 ETH from Gemini 9 on 11 November',
          r['proxy_type'] == 'eip7702' and r['implementations'] == [{'address': '0x63c0c19a282a1B52b07dD5a65b58948A07DAE32B', 'name': 'EIP7702StatelessDeleGator'}]
          and r['transactions_read'] == 598 and r['transactions_complete'] and r['last_transaction_utc'].startswith('2026-11-17')
          and len(gemini) == 1 and gemini[0]['direction'] == 'in' and gemini[0]['wei'] == '7650000000000000000' and gemini[0]['time_utc'].startswith('2026-11-11'))
    check('D28 0x15fF paid the first gas of 0x919B',
          summary['addresses']['hop_3a']['first_native_inflow']['counterparty']['address'].lower() == HOP2)
    contacts = {a for e in positive for a in (e['from'].lower(), e['to'].lower()) if TREASURY in (e['from'].lower(), e['to'].lower())} & set(SEVEN)
    check('D29 the funder and its source appear in 0 edges; the treasury\'s only contact among the 7 wallets is the recipient',
          not any({FUNDER, SOURCE} & {e['from'].lower(), e['to'].lower()} for e in edges) and contacts == {TREASURY, RECIPIENT})
    side = summary['addresses']['side_wallet']
    check('D30 0x3D26: first USDT transfer 2025-10-09T23:02:11Z, first native coin on 7 October 2025',
          node[SIDE]['first_utc'] == '2025-10-09T23:02:11Z' and side['first_native_inflow']['time_utc'].startswith('2025-10-07'))


for name, fn in (('D relay', d_relay), ('D conversions', d_conversions), ('D seed', d_seed_and_treasury), ('D hops', d_hops), ('D wallets', d_wallets)):
    guarded(name, fn)


# E. cross-case join
def e_cross():
    hits = table(HERE / 'data' / 'cross_case_hits.csv')
    classes = Counter(h['class'] for h in hits)
    consistent = all(h['address'] in met and h['class'] == ('treasury' if h['address'] == TREASURY else 'tagged' if h['address'] in labels else 'untagged')
                     and h['cited_in_folders'] and 'nobel-funder-exit' not in h['cited_in_folders'] for h in hits)
    check('E1 cross-case hits: 23 addresses met = 16 tagged + 1 treasury + 6 untagged, classes match labels.json',
          len(hits) == 23 == len({h['address'] for h in hits}) and classes == {'tagged': 16, 'treasury': 1, 'untagged': 6} and consistent, str(classes))
    cited = next((h for h in hits if h['address'] == TERMINAL_CITED), {})
    check('E2 terminal 0x6d988d1233... is untagged, a terminal of the walk, and cited in investigations/changenow-polymarket',
          cited.get('class') == 'untagged' and cited.get('cited_in_folders') == 'investigations/changenow-polymarket'
          and TERMINAL_CITED in {t['address'] for t in nodes['terminals']})
    early = {a for e in edges if e['timestamp_utc'] < '2025-11' and SIDE in (e['from'].lower(), e['to'].lower()) for a in (e['from'].lower(), e['to'].lower())}
    early |= {m['counterparty']['address'].lower() for m in summary['addresses']['side_wallet']['native_moves'] if m['time_utc'] < '2025-11'}
    check('E3 no USDT or native-coin counterparty of 0x3D26 before November 2025 is a cross-case hit',
          len(early - {SIDE}) > 0 and not (early - {SIDE}) & {h['address'] for h in hits})


guarded('E cross-case', e_cross)


# F. negative self-tests on temporary copies
def f_negative():
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / 'case'
        shutil.copytree(CASE, copy)
        page = sorted((copy / 'raw').glob('ethereum_*.json.gz'))[0]
        body = bytearray(gzip.decompress(page.read_bytes()))
        body[-2] = (body[-2] + 1) % 256
        page.write_bytes(gzip.compress(bytes(body), mtime=0))
        check('F1 a corrupted copy of one page makes the integrity check fail', any(p.startswith('altered') for p in manifest_problems(copy)[1]))
        try:
            vt.compute(copy, offline=True)
            refused = False
        except ValueError:
            refused = True
        check('F2 the same corrupted page makes compute refuse to load it', refused)
        shutil.copy(CASE / 'raw' / page.name, page)
        receipt = next(p for p in (copy / 'raw').glob('rpc0_*.json.gz') if '_block_' not in p.name)
        receipt.unlink()
        try:
            vt.replay(copy, write=False, offline=True)
            closed = False
        except FileNotFoundError:
            closed = True
        check('F3 a removed receipt makes offline replay fail closed, with no network call', closed and 'missing' in ' '.join(manifest_problems(copy)[1]))


guarded('F negative self-tests', f_negative)

width = max(len(n) for n, _, _ in RESULTS)
for n, ok, d in RESULTS:
    print(('PASS ' if ok else 'FAIL ') + n.ljust(width), d if not ok else '')
fails = sum(not ok for _, ok, _ in RESULTS)
print(f'{len(RESULTS) - fails}/{len(RESULTS)} checks pass')
sys.exit(1 if fails else 0)
