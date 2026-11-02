"""Windowed reads from SQD's public portal: keyless, all logs with block hash and log index, on chains with no free explorer.

Measured 2026-11-02: about 150 blocks/s on Base and Polygon, 1,250 on BSC, with HTTP 529 under load. A chain-long
pass per address is out of reach, so one scan carries many addresses over a chosen window and resumes from its
own checkpoint. The window is always stated: outside it nothing was read.
"""
import gzip
import hashlib
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

from .env import Guard, data_root
from .events import FRESH, LISTED, NATIVE, TOKENS

PORTAL = 'https://portal.sqd.dev/datasets/'
DATASET = {1: 'ethereum-mainnet', 10: 'optimism-mainnet', 56: 'binance-mainnet', 137: 'polygon-mainnet', 8453: 'base-mainnet', 42161: 'arbitrum-one'}
TRANSFER = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
FIELDS = {'block': {'number': True, 'hash': True, 'timestamp': True}, 'log': {'address': True, 'topics': True, 'data': True, 'transactionHash': True, 'logIndex': True, 'transactionIndex': True},
          'transaction': {'hash': True, 'from': True, 'to': True, 'value': True, 'status': True, 'transactionIndex': True, 'sighash': True}, 'trace': {'type': True, 'transactionIndex': True, 'traceAddress': True, 'callFrom': True, 'callTo': True, 'callValue': True, 'error': True}}
RETRY = (429, 500, 502, 503, 504, 529)


def _post(chain, query, tries=40, sleep=time.sleep):
    request = urllib.request.Request(PORTAL + DATASET[chain] + '/stream', data=json.dumps(query).encode(), headers={'content-type': 'application/json', 'user-agent': 'phi-global-forensics/0.1 read-only'})
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(request, timeout=180) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            if e.code not in RETRY:
                raise RuntimeError(f'sqd {chain}: HTTP {e.code} {e.read()[:200]}') from e
        except (urllib.error.URLError, TimeoutError, OSError):
            pass
        sleep(min(60, 3 + attempt * 2))
    raise RuntimeError(f'sqd {chain}: no answer after {tries} tries')


def address_query(addresses, from_block, to_block=None, traces=False):
    addresses = sorted(a.lower() for a in addresses)
    padded = ['0x' + a[2:].rjust(64, '0') for a in addresses]
    q = dict(type='evm', fromBlock=from_block, fields=FIELDS, logs=[dict(topic0=[TRANSFER], topic1=padded), dict(topic0=[TRANSFER], topic2=padded)], transactions=[{'from': addresses}, {'to': addresses}])
    if to_block is not None:
        q['toBlock'] = to_block
    if traces:
        q['traces'] = [dict(type=['call'], callFrom=addresses), dict(type=['call'], callTo=addresses)]
    return q


def decode_block(chain, block):
    """Events of one block. A row is LISTED: it comes from an archive, not from a node's receipt."""
    head = block['header']
    common = dict(chain_id=chain, block_number=head['number'], block_hash=head['hash'], timestamp=head['timestamp'], level=LISTED, data_class=FRESH, source=f'sqd-portal:{DATASET[chain]}')
    out = []
    success = {}
    for t in block.get('transactions') or []:
        success[t.get('transactionIndex')] = t.get('status') in (1, None, '0x1')
        if int(t.get('value') or '0x0', 16) > 0 or True:
            out.append(dict(common, transaction_hash=t['hash'], log_index=None, kind='native', contract=None, token=NATIVE[chain], decimals=18, raw_amount=str(int(t.get('value') or '0x0', 16)), success=success[t.get('transactionIndex')], method=t.get('sighash'), decoding='sqd transaction', **{'from': (t.get('from') or '').lower(), 'to': (t.get('to') or '').lower()}))
    tx_hash = {t.get('transactionIndex'): t['hash'] for t in block.get('transactions') or []}
    for l in block.get('logs') or []:
        topics = l.get('topics') or []
        if not topics or topics[0] != TRANSFER or len(topics) != 3 or len(l.get('data') or '') != 66:
            continue
        contract = l['address'].lower()
        known = TOKENS.get(chain, {}).get(contract)
        out.append(dict(common, transaction_hash=l['transactionHash'], log_index=l['logIndex'], kind='erc20', contract=contract, token=known[0] if known else None, token_known=bool(known), decimals=known[1] if known else 0, raw_amount=str(int(l['data'], 16)), success=success.get(l.get('transactionIndex'), True), method=None, decoding='erc20 Transfer log, sqd', **{'from': '0x' + topics[1][-40:], 'to': '0x' + topics[2][-40:]}))
    for t in block.get('traces') or []:
        value = int(t.get('callValue') or '0x0', 16) if t.get('type') == 'call' else 0
        if value and not t.get('error') and t.get('traceAddress'):
            out.append(dict(common, transaction_hash=tx_hash.get(t.get('transactionIndex'), ''), log_index=None, trace_address=t['traceAddress'], kind='internal', contract=None, token=NATIVE[chain], decimals=18, raw_amount=str(value), success=True, method=None, decoding='sqd call trace', **{'from': (t.get('callFrom') or '').lower(), 'to': (t.get('callTo') or '').lower()}))
    return [e for e in out if e['kind'] != 'native' or int(e['raw_amount']) > 0 or e['from']]


class Scan:
    """One query over one window, resumable. Raw non-empty blocks are kept gzipped; the checkpoint moves only after they are on disk."""

    def __init__(self, chain, addresses, from_block, to_block, traces=False, root=None, guard=None, post=_post):
        self.chain, self.addresses, self.from_block, self.to_block, self.traces = chain, sorted(a.lower() for a in addresses), from_block, to_block, traces
        self.post, self.guard = post, guard or Guard()
        tag = hashlib.sha256(json.dumps([chain, self.addresses, from_block, to_block, traces]).encode()).hexdigest()[:24]
        base = Path(root) if root else data_root() / 'raw' / 'sqd'
        base.mkdir(parents=True, exist_ok=True)
        self.state_path, self.raw_path = base / f'{tag}.state.json', base / f'{tag}.ndjson.gz'
        self.state = json.loads(self.state_path.read_text()) if self.state_path.exists() else dict(chain=chain, addresses=self.addresses, from_block=from_block, to_block=to_block, traces=traces, next_block=from_block, requests=0, bytes=0, kept_blocks=0, done=False, started=time.time(), updated=None)

    def _save(self):
        tmp = self.state_path.with_suffix('.tmp')
        tmp.write_text(json.dumps(self.state))
        tmp.replace(self.state_path)

    def run(self, max_seconds=None, log=None):
        started = time.time()
        while not self.state['done'] and self.state['next_block'] <= self.to_block:
            if max_seconds and time.time() - started > max_seconds:
                return False
            self.guard()
            status, body = self.post(self.chain, address_query(self.addresses, self.state['next_block'], self.to_block, self.traces))
            self.state['requests'] += 1
            self.state['bytes'] += len(body)
            if status == 204 or not body.strip():
                self.state['done'] = True
                break
            kept, last = [], None
            for line in body.splitlines():
                if line.strip():
                    block = json.loads(line)
                    last = block['header']['number']
                    if block.get('logs') or block.get('transactions') or block.get('traces'):
                        kept.append(line)
            if kept:
                with gzip.open(self.raw_path, 'ab') as f:
                    f.write(b'\n'.join(kept) + b'\n')
                self.state['kept_blocks'] += len(kept)
            self.state['next_block'] = last + 1
            self.state['updated'] = time.time()
            self._save()
            if log and self.state['requests'] % 50 == 0:
                log(f"sqd {self.chain} next {self.state['next_block']} of {self.to_block}, kept {self.state['kept_blocks']}")
        self.state['done'] = self.state['next_block'] > self.to_block or self.state['done']
        self._save()
        return self.state['done']

    def events(self):
        if not self.raw_path.exists():
            return
        seen = set()
        with gzip.open(self.raw_path, 'rt') as f:
            for line in f:
                if line.strip():
                    block = json.loads(line)
                    number = block['header']['number']
                    if number not in seen:  # a crash between writing and the checkpoint re-reads a block once
                        seen.add(number)
                        yield from decode_block(self.chain, block)

    def coverage(self):
        return dict(chain_id=self.chain, addresses=len(self.addresses), source='sqd-portal', status='WINDOW_COMPLETE' if self.state['done'] else 'INCOMPLETE', from_block=self.from_block, to_block_exclusive=self.state['next_block'], requested_to_block=self.to_block, requests=self.state['requests'], bytes=self.state['bytes'], note='Only this window was read. Nothing is claimed before or after it.')
