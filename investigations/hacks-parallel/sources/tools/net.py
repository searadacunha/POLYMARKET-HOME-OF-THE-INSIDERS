"""Copy of outflows tools/net.py, own folder. Bounded public reads: one worker, own gz cache, read-through to the proof, flow-trace and investigation caches (never written), request ledger, resource guards, and a global gate: never a third network worker.
Every answer is cached for this run: the cache is the checkpoint, a re-run replays it at no network cost, and the whole study is a snapshot of its collection date."""
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
PRIOR_CACHES = tuple(Path.home() / f'Projects/{d}/state/http_cache' for d in ('PolySentinel-ChangeNOW-outflows', 'PolySentinel-ChangeNOW-proof', 'PolySentinel-flow-trace', 'PolySentinel-investigation'))  # read only
OTHER_LEDGERS = tuple(Path.home() / f'Projects/{d}/state/requests.jsonl' for d in ('PolySentinel-ChangeNOW-proof', 'PolySentinel-flow-trace', 'PolySentinel-investigation'))
BUSY_SECONDS = 120
LEDGER = ROOT / 'state/requests.jsonl'
HEARTBEAT = Path.home() / 'Projects/PolySentinel/metrics/heartbeat.json'
UA = {'User-Agent': 'PolySentinel-hacks-parallel/0.1 public-read-only', 'Content-Type': 'application/json', 'Accept': 'application/json'}
FREE_FLOOR = 14_500_000_000  # mission: suspend costly collection under 14.5 GB free
SWAP_RISE_MB = 300  # a rise since start, not a level: swap stays high long after a hibernation
CACHE_CAP = 700_000_000
MAX_WAIT = 3600  # seconds a guard may hold the worker before raising

RPC = {137: ('https://polygon-bor-rpc.publicnode.com', 'https://polygon.drpc.org', 'https://gateway.tenderly.co/public/polygon'),
       1: ('https://ethereum-rpc.publicnode.com', 'https://gateway.tenderly.co/public/mainnet'),
       42161: ('https://arbitrum-one-rpc.publicnode.com', 'https://gateway.tenderly.co/public/arbitrum'),
       8453: ('https://base-rpc.publicnode.com', 'https://gateway.tenderly.co/public/base'),
       10: ('https://optimism-rpc.publicnode.com', 'https://gateway.tenderly.co/public/optimism'),
       56: ('https://bsc-rpc.publicnode.com', 'https://bsc.drpc.org', 'https://56.rpc.thirdweb.com')}
READ_METHODS = frozenset({'eth_getCode', 'eth_call', 'eth_getLogs', 'eth_getBalance', 'eth_getTransactionReceipt', 'eth_getTransactionByHash', 'eth_getBlockByNumber', 'eth_getTransactionCount', 'eth_blockNumber'})


class Pause(RuntimeError):
    """A guard stayed red too long: stop, everything read so far is cached."""


class Stats:
    calls = cached = 0
    checked = 0.0
    swap_start = None
    cache_size = None


def _red():
    if shutil.disk_usage('/').free < FREE_FLOOR:
        return 'disk under 14.5 GB free'
    used = float(subprocess.run(['sysctl', '-n', 'vm.swapusage'], capture_output=True, text=True).stdout.split('used = ')[1].split('M')[0])
    if Stats.swap_start is None:
        Stats.swap_start = used
    if used > Stats.swap_start + SWAP_RISE_MB:
        return f'swap rose to {used:.0f} MB from {Stats.swap_start:.0f} MB'
    if time.time() - json.loads(HEARTBEAT.read_text())['at'] > 180:
        return 'PolySentinel heartbeat older than 180 s'
    if Stats.cache_size is None:
        Stats.cache_size = sum(p.stat().st_size for p in CACHE.rglob('*.gz')) if CACHE.exists() else 0
    if Stats.cache_size > CACHE_CAP:
        return 'cache over its 700 MB cap'
    return None


def guard():
    if time.time() - Stats.checked < 30:
        return
    Stats.checked = time.time()
    start = time.time()
    while (why := _red()):
        note(kind='pause', why=why)
        if time.time() - start > MAX_WAIT:
            raise Pause(why)
        time.sleep(120)


def note(**fields):
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER.open('a') as f:
        f.write(json.dumps(dict(at=round(time.time()), **fields)) + '\n')


def _load(key):
    for base in (CACHE, *PRIOR_CACHES):
        path = base / key[:2] / (key + '.json.gz')
        if path.exists():
            Stats.cached += 1
            with gzip.open(path, 'rt') as f:
                return True, json.load(f)
    return False, None


def _store(key, value):
    path = CACHE / key[:2] / (key + '.json.gz')
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(f'.{os.getpid()}.tmp')
    with gzip.GzipFile(tmp, 'wb', mtime=0) as f:
        f.write(json.dumps(value, separators=(',', ':')).encode())
    Stats.cache_size = (Stats.cache_size or 0) + tmp.stat().st_size
    os.replace(tmp, path)


def _key_from_env():
    if os.environ.get('ETHERSCAN_API_KEY'):
        return os.environ['ETHERSCAN_API_KEY']
    for line in (Path.home() / 'Downloads/.env').read_text().splitlines():
        if line.startswith('ETHERSCAN_API_KEY='):
            return line.split('=', 1)[1].strip().strip('"\'')
    raise RuntimeError('no ETHERSCAN_API_KEY')


def is_empty_answer(value):
    return isinstance(value, dict) and value.get('status') == '0' and 'No ' in str(value.get('message'))


def get(url, params=None, pause=.25, retries=6, secret=None, accept=(400, 404), store=True):
    """JSON from a public GET. `secret` is appended to the request only: never in the cache key, never in the ledger. store=False: big pages kept as compact rows by the caller, the ledger keeps their SHA-256."""
    full = url + ('?' + urllib.parse.urlencode(params) if params else '')
    key = hashlib.sha256(full.encode()).hexdigest()
    hit, value = _load(key)
    if hit and not is_empty_answer(value):  # an empty answer from any cache is never trusted, see es.rows
        return value
    guard()
    wire = full + (('&' if '?' in full else '?') + urllib.parse.urlencode(secret) if secret else '')
    for attempt in range(retries):
        time.sleep(pause * (1 + 4 * attempt))
        Stats.calls += 1
        try:
            with urllib.request.urlopen(urllib.request.Request(wire, headers=UA), timeout=40) as r:
                body = r.read()
            value = json.loads(body)
            note(kind='get', url=full, status=200, bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
            if isinstance(value, dict) and value.get('status') == '0' and 'No ' not in str(value.get('message')):  # explorer refusal or overload: a failure, never an empty history, never cached
                if any(w in (str(value.get('message')) + str(value.get('result'))).lower() for w in ('rate limit', 'busy', 'timeout', 'unexpected')):
                    time.sleep(5 * (attempt + 1))
                    continue
                return value
            if store and not is_empty_answer(value):
                _store(key, value)
            return value
        except urllib.error.HTTPError as e:
            note(kind='get', url=full, status=e.code)
            if e.code in accept:
                return dict(_http_error=e.code)
            if e.code == 429:
                time.sleep(45 * (attempt + 1))
        except (urllib.error.URLError, TimeoutError, ValueError, OSError) as e:
            note(kind='get', url=full, error=type(e).__name__)
    raise RuntimeError('GET failed after retries: ' + full)


def rpc(method, params, chain=137, pause=.15, cache=True):
    """A node refusing the call hands over to the next; all failing raises, never an empty result."""
    if method not in READ_METHODS:
        raise ValueError('Method not permitted: ' + method)
    key = hashlib.sha256(json.dumps([chain, method, params]).encode()).hexdigest()
    if cache:
        hit, value = _load(key)
        if hit:
            return value
    guard()
    errors = []
    for endpoint in RPC[chain]:
        time.sleep(pause)
        Stats.calls += 1
        request = urllib.request.Request(endpoint, data=json.dumps(dict(jsonrpc='2.0', id=1, method=method, params=params)).encode(), headers=UA)
        host = urllib.parse.urlsplit(endpoint).hostname
        try:
            with urllib.request.urlopen(request, timeout=30) as r:
                body = json.loads(r.read())
        except (urllib.error.URLError, TimeoutError, ValueError, OSError) as e:
            errors.append(f'{host}: {type(e).__name__}')
            continue
        if 'result' in body and not body.get('error'):
            note(kind='rpc', chain=chain, method=method, host=host, ok=True)
            if body['result'] is None and method in ('eth_getTransactionReceipt', 'eth_getTransactionByHash'):
                errors.append(f'{host}: null')  # one node's null is not an answer
                continue
            if cache:
                _store(key, body['result'])
            return body['result']
        note(kind='rpc', chain=chain, method=method, host=host, ok=False)
        errors.append(f"{host}: {str(body.get('error'))[:120]}")
    raise RuntimeError(f'{method} failed on every node: ' + '; '.join(errors))
