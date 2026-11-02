"""Bounded public reads for the investigation: disk cache, request ledger, resource guard. No key, no write method."""
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / 'state/http_cache'
LEDGER = ROOT / 'state/requests.jsonl'
HEARTBEAT = Path.home() / 'Projects/PolySentinel/metrics/heartbeat.json'
RPC = {137: ('https://polygon-bor-rpc.publicnode.com', 'https://polygon.drpc.org', 'https://gateway.tenderly.co/public/polygon'),
       1: ('https://ethereum-rpc.publicnode.com', 'https://gateway.tenderly.co/public/mainnet'),
       42161: ('https://arbitrum-one-rpc.publicnode.com', 'https://gateway.tenderly.co/public/arbitrum'),
       8453: ('https://base-rpc.publicnode.com', 'https://gateway.tenderly.co/public/base'),
       10: ('https://optimism-rpc.publicnode.com', 'https://gateway.tenderly.co/public/optimism'),
       56: ('https://bsc-rpc.publicnode.com',)}
READ_METHODS = frozenset({'eth_blockNumber', 'eth_getCode', 'eth_call', 'eth_getLogs', 'eth_getBalance', 'eth_getTransactionReceipt', 'eth_getTransactionByHash', 'eth_getBlockByNumber', 'eth_getTransactionCount'})
FREE_FLOOR = 14_500_000_000  # above the shared 13.5 GB floor and the replay's own 14 GB guard
SWAP_RISE_MB = 300  # a rise since this process started, not a level: swap stays high long after a hibernation without any pressure
UA = {'User-Agent': 'PolySentinel-investigation/0.1 public-read-only', 'Content-Type': 'application/json'}


class Pause(RuntimeError):
    """Production or replay comes first: stop here and resume from cache later."""


class Stats:
    calls = cached = 0
    checked = 0.0
    swap_start = None


def guard():
    if time.time() - Stats.checked < 30:
        return
    Stats.checked = time.time()
    if shutil.disk_usage('/').free < FREE_FLOOR:
        raise Pause('disk under 14.5 GB free')
    swap = subprocess.run(['sysctl', '-n', 'vm.swapusage'], capture_output=True, text=True).stdout
    used = float(swap.split('used = ')[1].split('M')[0])
    if Stats.swap_start is None:
        Stats.swap_start = used
    if used > Stats.swap_start + SWAP_RISE_MB:
        raise Pause(f'swap rose to {used:.0f} MB from {Stats.swap_start:.0f} MB')
    beat = json.loads(HEARTBEAT.read_text())
    if time.time() - beat['at'] > 180:
        raise Pause('collector heartbeat older than 180 s')


def _note(**fields):
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open('a') as f:
        f.write(json.dumps(dict(at=time.time(), **fields)) + '\n')


def _load(key):
    path = CACHE / key[:2] / (key + '.json.gz')
    if path.exists():
        Stats.cached += 1
        with gzip.open(path, 'rt') as f:
            return True, json.load(f)
    return False, None


def _store(key, value):
    path = CACHE / key[:2] / (key + '.json.gz')
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(f'.{os.getpid()}.tmp')  # two workers can store the same key
    with gzip.GzipFile(tmp, 'wb', mtime=0) as f:
        f.write(json.dumps(value, separators=(',', ':')).encode())
    os.replace(tmp, path)


def get(url, params=None, pause=.25, retries=4):
    """JSON from a public GET, cached forever: re-reading a finished market or wallet history must not cost a request."""
    full = url + ('?' + urllib.parse.urlencode(params) if params else '')
    key = hashlib.sha256(full.encode()).hexdigest()
    hit, value = _load(key)
    if hit:
        return value
    guard()
    for attempt in range(retries):
        time.sleep(pause * (1 + 4 * attempt))
        Stats.calls += 1
        try:
            with urllib.request.urlopen(urllib.request.Request(full, headers=UA), timeout=30) as r:
                body = r.read()
            value = json.loads(body)
            _note(kind='get', url=full, status=200, bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
            _store(key, value)
            return value
        except urllib.error.HTTPError as e:
            _note(kind='get', url=full, status=e.code)
            if e.code in (400, 404):
                return dict(_http_error=e.code)
            if e.code == 429:
                time.sleep(45 * (attempt + 1))  # no Retry-After on Relay v2: back off well past its window
        except (urllib.error.URLError, TimeoutError, ValueError) as e:
            _note(kind='get', url=full, error=type(e).__name__)
    raise RuntimeError('GET failed after retries: ' + full)


def rpc(method, params, chain=137, pause=.15):
    """Each method's answer is cached only when it cannot change. A node refusing the call hands over to the next; all failing raises, never an empty result."""
    if method not in READ_METHODS:
        raise ValueError('Method not permitted: ' + method)
    immutable = method in ('eth_getTransactionReceipt', 'eth_getTransactionByHash', 'eth_getLogs') or (method == 'eth_getBlockByNumber' and params[0] != 'latest')
    key = hashlib.sha256(json.dumps([chain, method, params]).encode()).hexdigest()
    if immutable:
        hit, value = _load(key)
        if hit:
            return value
    guard()
    errors = []
    for endpoint in RPC[chain]:
        time.sleep(pause)
        Stats.calls += 1
        request = urllib.request.Request(endpoint, data=json.dumps(dict(jsonrpc='2.0', id=1, method=method, params=params)).encode(), headers=UA)
        try:
            with urllib.request.urlopen(request, timeout=30) as r:
                body = json.loads(r.read())
        except (urllib.error.URLError, TimeoutError, ValueError) as e:
            errors.append(f'{endpoint}: {type(e).__name__}')
            continue
        host = urllib.parse.urlsplit(endpoint).hostname
        if 'result' in body and not body.get('error'):
            _note(kind='rpc', chain=chain, method=method, host=host, ok=True)
            # A null receipt on one node is not an answer: try the others before accepting it.
            if body['result'] is None and method == 'eth_getTransactionReceipt':
                errors.append(f'{host}: null')
                continue
            if immutable:
                _store(key, body['result'])
            return body['result']
        _note(kind='rpc', chain=chain, method=method, host=host, ok=False)
        errors.append(f"{host}: {str(body.get('error'))[:120]}")
    raise RuntimeError(f'{method} failed on every node: ' + '; '.join(errors))


TRANSFER = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
TOKENS = {'USDC.e': '0x2791bca1f2de4661ed88a30c99a7a9449aa84174', 'USDC': '0x3c499c542cef5e3811e1192ce70d8cc03d5c3359', 'pUSD': '0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb', 'USDT': '0xc2132d05d31c914a87c6611c10748aeb04b58e8f'}
TOKEN_NAME = {v: k for k, v in TOKENS.items()}
CHUNK = 9000  # public nodes serve under 10,000 blocks per log call


def pad(address):
    return '0x' + address.lower()[2:].rjust(64, '0')


def transfers(address, start, end, tokens=('USDC.e', 'USDC', 'pUSD', 'USDT'), chain=137):
    """Every transfer of these tokens touching one address in a block range, both directions, with no gap: a failed chunk raises rather than returning fewer rows."""
    contracts = [TOKENS[t] for t in tokens]
    rows = {}
    for low in range(start, end + 1, CHUNK):
        high = min(end, low + CHUNK - 1)
        range_args = dict(fromBlock=hex(low), toBlock=hex(high), address=contracts)
        for topics in ([TRANSFER, pad(address)], [TRANSFER, None, pad(address)]):
            for log in rpc('eth_getLogs', [dict(range_args, topics=topics)], chain):
                rows[(log['transactionHash'], int(log['logIndex'], 16))] = dict(tx=log['transactionHash'], log_index=int(log['logIndex'], 16), block=int(log['blockNumber'], 16), token=TOKEN_NAME[log['address'].lower()], source='0x' + log['topics'][1][-40:], target='0x' + log['topics'][2][-40:], raw=int(log['data'], 16))
    return sorted(rows.values(), key=lambda r: (r['block'], r['log_index']))


def block_time(block, chain=137):
    return int(rpc('eth_getBlockByNumber', [hex(block), False], chain)['timestamp'], 16)


def is_contract(address, chain=137):
    return rpc('eth_getCode', [address, 'latest'], chain) not in ('0x', '0x0', None)


def nonce(address, chain=137):
    return int(rpc('eth_getTransactionCount', [address, 'latest'], chain), 16)
