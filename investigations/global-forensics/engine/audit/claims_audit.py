"""Claims auditor, kept apart from the engine: it imports nothing from gf, reads through its own nodes, and each check can fail.

Usage: claims_audit.py <checks.json> <out.json> [--root DIR], or --self-test. A check says what a claim needs to be true:
  tx        a move read again from nodes the engine does not use: native value, or a Transfer log at its index, from, to, exact raw amount, status 1.
  json      a value at a path in an output file.
  csv_count number of rows matching columns in a CSV.
  forbid    a pattern that must not occur in a text file.
  require   a pattern that must occur in a text file.
A check that cannot be read is UNREAD, never PASS. Exit code 1 if anything is not PASS.
"""
import csv
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

NODES = {1: ('https://eth.llamarpc.com', 'https://1rpc.io/eth'), 137: ('https://polygon.llamarpc.com', 'https://1rpc.io/matic'), 42161: ('https://arbitrum.llamarpc.com', 'https://1rpc.io/arb'), 8453: ('https://base.llamarpc.com', 'https://1rpc.io/base'), 10: ('https://optimism.llamarpc.com', 'https://1rpc.io/op'), 56: ('https://binance.llamarpc.com', 'https://1rpc.io/bnb')}
TRANSFER = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'


def rpc(chain, method, params):
    last = None
    for endpoint in NODES[chain]:
        for attempt in range(3):
            try:
                req = urllib.request.Request(endpoint, data=json.dumps(dict(jsonrpc='2.0', id=1, method=method, params=params)).encode(), headers={'Content-Type': 'application/json', 'User-Agent': 'phi-claims-audit/0.1 read-only'})
                with urllib.request.urlopen(req, timeout=40) as r:
                    body = json.loads(r.read())
                if body.get('result') is not None:
                    return body['result'], endpoint.split('/')[2]
                last = str(body.get('error') or 'null result')[:120]
            except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
                last = type(exc).__name__
            time.sleep(1 + 2 * attempt)
    raise LookupError(last)


def check_tx(c, read=rpc):
    receipt, host = read(c['chain'], 'eth_getTransactionReceipt', [c['tx']])
    if int(receipt['status'], 16) != 1:
        return 'FAIL', 'reverted'
    source, target = c['from'].lower(), c['to'].lower()
    if c.get('contract') is None:
        tx, _ = read(c['chain'], 'eth_getTransactionByHash', [c['tx']])
        got = (tx['from'].lower(), (tx.get('to') or '').lower(), int(tx['value'], 16))
        return ('PASS', host) if got == (source, target, int(c['raw'])) else ('FAIL', f'read {got}')
    for log in receipt['logs']:
        topics = log['topics']
        if int(log['logIndex'], 16) == c['log_index']:
            ok = log['address'].lower() == c['contract'].lower() and topics[0] == TRANSFER and '0x' + topics[1][-40:] == source and '0x' + topics[2][-40:] == target and int(log['data'], 16) == int(c['raw'])
            return ('PASS', host) if ok else ('FAIL', f"log {c['log_index']} differs")
    return 'FAIL', f"no log at index {c['log_index']}"


def at_path(value, path):
    for part in path:
        value = value[part]
    return value


def check_json(c, root):
    got = at_path(json.loads((root / c['file']).read_text()), c['path'])
    if c.get('tolerance') is not None:
        return ('PASS', got) if abs(float(got) - float(c['value'])) <= c['tolerance'] else ('FAIL', f'read {got}')
    return ('PASS', got) if got == c['value'] else ('FAIL', f'read {got}')


def check_csv(c, root):
    with (root / c['file']).open() as f:
        n = sum(1 for r in csv.DictReader(f) if all(r.get(k) == v for k, v in c['where'].items()))
    return ('PASS', n) if n == c['n'] else ('FAIL', f'read {n}')


def check_text(c, root):
    text = (root / c['file']).read_text()
    found = re.findall(c['pattern'], text, re.I | re.M)
    if c['kind'] == 'forbid':
        return ('PASS', 0) if not found else ('FAIL', f'{len(found)}: {str(found[:2])[:160]}')
    return ('PASS', len(found)) if found else ('FAIL', 'absent')


def run_one(c, root, read=rpc):
    try:
        if c['kind'] == 'tx':
            return check_tx(c, read)
        if c['kind'] == 'json':
            return check_json(c, root)
        if c['kind'] == 'csv_count':
            return check_csv(c, root)
        return check_text(c, root)
    except (LookupError, KeyError, IndexError, TypeError, ValueError, OSError) as exc:
        return 'UNREAD', f'{type(exc).__name__}: {str(exc)[:120]}'


def self_test():
    """The auditor must fail on tampered claims, or its PASS means nothing. No network."""
    import tempfile
    tx = dict(status='0x1', logs=[dict(logIndex='0x5', address='0xabc', topics=[TRANSFER, '0x' + '0' * 24 + 'a' * 40, '0x' + '0' * 24 + 'b' * 40], data=hex(100))])
    plain = {'from': '0x' + 'a' * 40, 'to': '0x' + 'b' * 40, 'value': hex(7)}

    def read(chain, method, params):
        return (tx if method == 'eth_getTransactionReceipt' else plain), 'fake'
    base = {'kind': 'tx', 'chain': 1, 'tx': '0x1', 'from': '0x' + 'a' * 40, 'to': '0x' + 'b' * 40, 'contract': '0xabc', 'log_index': 5, 'raw': 100}
    cases = [(base, 'PASS'), (dict(base, raw=101), 'FAIL'), (dict(base, to='0x' + 'c' * 40), 'FAIL'), (dict(base, log_index=6), 'FAIL'), (dict(base, contract=None, raw=7), 'PASS'), (dict(base, contract=None, raw=8), 'FAIL')]
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / 'a.json').write_text(json.dumps(dict(x=[dict(y=3)])))
        (root / 'b.csv').write_text('r\nok\nok\nno\n')
        (root / 'c.md').write_text('This wallet is an insider.\n')
        cases += [(dict(kind='json', file='a.json', path=['x', 0, 'y'], value=3), 'PASS'), (dict(kind='json', file='a.json', path=['x', 0, 'y'], value=4), 'FAIL'), (dict(kind='json', file='a.json', path=['x', 1, 'y'], value=3), 'UNREAD'), (dict(kind='json', file='absent.json', path=[], value=3), 'UNREAD'), (dict(kind='csv_count', file='b.csv', where=dict(r='ok'), n=2), 'PASS'), (dict(kind='csv_count', file='b.csv', where=dict(r='ok'), n=3), 'FAIL'), (dict(kind='forbid', file='c.md', pattern=r'is an insider'), 'FAIL'), (dict(kind='require', file='c.md', pattern=r'no such line'), 'FAIL')]
        def down(*a):
            raise LookupError('all nodes failed')
        got = [(run_one(c, root, read)[0], want) for c, want in cases] + [(run_one(base, root, down)[0], 'UNREAD')]
    assert all(a == b for a, b in got), got
    print(f'self-test: {len(got)} cases, tampered claims fail, unreadable never passes')


def main():
    if '--self-test' in sys.argv:
        return self_test()
    checks = json.loads(Path(sys.argv[1]).read_text())
    root = Path(sys.argv[sys.argv.index('--root') + 1]) if '--root' in sys.argv else Path(sys.argv[1]).resolve().parents[2]
    rows, tally = [], {}
    for c in checks:
        state, detail = run_one(c, root)
        tally[state] = tally.get(state, 0) + 1
        rows.append(dict(claim=c['claim'], kind=c['kind'], state=state, detail=detail, what=c.get('tx') or c.get('file')))
    Path(sys.argv[2]).write_text(json.dumps(dict(at=int(time.time()), tally=tally, rows=rows), indent=0))
    print(json.dumps(tally))
    for r in rows:
        if r['state'] != 'PASS':
            print(r['state'], r['claim'], r['kind'], str(r['what'])[:50], str(r['detail'])[:160])
    return 0 if set(tally) <= {'PASS'} else 1


if __name__ == '__main__':
    sys.exit(main())
