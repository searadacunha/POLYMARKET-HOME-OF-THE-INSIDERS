"""Public reads only. Every answer: raw bytes gzipped under raw/http, one line in the append-only hash-chained ledger.

Design borrowed from ~/Projects/PolySentinel-flow-trace/tools/net.py (one guard, cache as checkpoint), rewritten so nothing is read
from another investigator's cache: this module must re-observe the chain and the APIs by itself.
A failure raises. It is never turned into an empty result.
"""
import fcntl
import gzip
import hashlib
import json
import os
import resource
import shutil
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / 'raw/http'
LEDGER = ROOT / 'evidence/requests.jsonl'
THROTTLE = ROOT / 'state/throttle'
HEARTBEAT = Path.home() / 'Projects/PolySentinel/metrics/heartbeat.json'
UA = {'User-Agent': 'polysentinel-ballon-dor-2026/1 public-read-only', 'Accept': 'application/json', 'Content-Type': 'application/json'}

FREE_FLOOR = 14_500_000_000      # disk rule: 13.5 GB floor + 1 GB of margin for this module
RAW_CAP = 1_500_000_000          # reserved with diskguard, never exceeded
SWAP_RISE_MB = 700               # rise within 10 minutes: other sessions move it too, so a stop here is a pause, not a failure
RSS_CAP = 1_500_000_000
MAX_WAIT = 1800

MIN_INTERVAL = {  # seconds between calls, per host, across every process of this module
    'data-api.polymarket.com': .22, 'gamma-api.polymarket.com': .22, 'api.etherscan.io': .45, 'eth.blockscout.com': .5,
    'metadata.services.blockscout.com': .5, 'explorer.optimism.io': 2.0, 'api.relay.link': 15.0, 'mempool.space': .6,
    'blockstream.info': .8, 'api.mainnet-beta.solana.com': 1.6, 'bridge.polymarket.com': 1.0, 'clob.polymarket.com': .3,
    'coins.llama.fi': .5,
}
RPC = {137: ('https://polygon-bor-rpc.publicnode.com', 'https://polygon.drpc.org', 'https://gateway.tenderly.co/public/polygon'),
       1: ('https://ethereum-rpc.publicnode.com', 'https://eth.drpc.org', 'https://gateway.tenderly.co/public/mainnet'),
       42161: ('https://arbitrum-one-rpc.publicnode.com', 'https://gateway.tenderly.co/public/arbitrum'),
       8453: ('https://base-rpc.publicnode.com', 'https://gateway.tenderly.co/public/base'),
       10: ('https://optimism-rpc.publicnode.com', 'https://gateway.tenderly.co/public/optimism'),
       56: ('https://bsc-rpc.publicnode.com', 'https://bsc.drpc.org', 'https://56.rpc.thirdweb.com')}
READ_METHODS = frozenset({'eth_getCode', 'eth_call', 'eth_getLogs', 'eth_getBalance', 'eth_getTransactionReceipt', 'eth_getTransactionByHash',
                          'eth_getBlockByNumber', 'eth_getTransactionCount', 'eth_blockNumber', 'getSignaturesForAddress', 'getTransaction', 'getAccountInfo',
                          'getTokenAccountsByOwner', 'getBalance', 'getBlockTime', 'getSlot'})


class FetchError(RuntimeError):
    pass


class Pause(RuntimeError):
    """A guard stayed red too long. Everything read so far is on disk: stop and report."""


class Miss(dict):
    """An HTTP 400/404 the caller asked to tolerate. Distinct from an empty answer."""


class Stats:
    calls = hits = 0
    checked = 0.0
    swap_start = None
    swap_at = 0.0


def _red():
    if shutil.disk_usage('/').free < FREE_FLOOR:
        return 'disk under 14.5 GB free'
    used = float(subprocess.run(['sysctl', '-n', 'vm.swapusage'], capture_output=True, text=True).stdout.split('used = ')[1].split('M')[0])
    now = time.time()
    if Stats.swap_start is None or now - Stats.swap_at > 600:  # a burst is the danger: a level left behind by other sessions must not hold this collector forever
        Stats.swap_start, Stats.swap_at = used, now
    if used > Stats.swap_start + SWAP_RISE_MB:
        return f'swap rose to {used:.0f} MB from {Stats.swap_start:.0f} MB in under 10 min'
    if time.time() - json.loads(HEARTBEAT.read_text())['at'] > 180:
        return 'PolySentinel heartbeat older than 180 s'
    if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss > RSS_CAP:
        raise Pause('this process is over its 1.5 GB memory cap')
    return None


def guard():
    if time.time() - Stats.checked < 30:
        return
    Stats.checked = time.time()
    if sum(p.stat().st_size for p in RAW.rglob('*.gz')) > RAW_CAP if int(Stats.checked) % 20 == 0 and RAW.exists() else False:
        raise Pause('raw archive over its 1.5 GB cap')
    start = time.time()
    while (why := _red()):
        note_pause(why)
        if time.time() - start > MAX_WAIT:
            raise Pause(why)
        time.sleep(120)


def _append(record):
    """Append-only chain: each line carries the hash of the previous line, so an edited or removed line breaks every following one."""
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with open(LEDGER, 'a+') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.seek(0, os.SEEK_END)
        size = f.tell()
        prev = 'GENESIS'
        if size:
            f.seek(max(0, size - 4096))
            prev = hashlib.sha256(f.read().splitlines()[-1].encode()).hexdigest()
        line = json.dumps(dict(record, prev=prev), separators=(',', ':'), sort_keys=True)
        f.seek(0, os.SEEK_END)
        f.write(line + '\n')
        f.flush()
        fcntl.flock(f, fcntl.LOCK_UN)
    return hashlib.sha256(line.encode()).hexdigest()


def note_pause(why):
    _append(dict(kind='pause', at=round(time.time()), why=why))


def _throttle(host):
    wait = MIN_INTERVAL.get(host, .3)
    THROTTLE.mkdir(parents=True, exist_ok=True)
    with open(THROTTLE / host, 'a+') as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.seek(0)
        text = f.read().strip()
        last = float(text) if text else 0.0
        delay = last + wait - time.time()
        if delay > 0:
            time.sleep(delay)
        f.seek(0)
        f.truncate()
        f.write(str(time.time()))
        f.flush()
        fcntl.flock(f, fcntl.LOCK_UN)


def _path(key):
    return RAW / key[:2] / (key + '.gz')


def _read(key):
    p = _path(key)
    if p.exists():
        Stats.hits += 1
        with gzip.open(p, 'rb') as f:
            return f.read()
    return None


def _write(key, body):
    p = _path(key)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(f'.{os.getpid()}.tmp')
    with gzip.GzipFile(tmp, 'wb', mtime=0) as f:
        f.write(body)
    os.replace(tmp, p)


def request_key(full):
    return hashlib.sha256(full.encode()).hexdigest()


def get(url, params=None, retries=7, secret=None, accept=(), raw=False):
    """`secret` goes on the wire only: never in the key, the archive path or the ledger. `accept`: statuses returned as Miss."""
    full = url + ('?' + urllib.parse.urlencode(params) if params else '')
    key = request_key(full)
    body = _read(key)
    if body is not None:
        return body if raw else json.loads(body)
    guard()
    host = urllib.parse.urlsplit(full).hostname
    wire = full + (('&' if '?' in full else '?') + urllib.parse.urlencode(secret) if secret else '')
    last = None
    for attempt in range(retries):
        _throttle(host)
        Stats.calls += 1
        try:
            with urllib.request.urlopen(urllib.request.Request(wire, headers=UA), timeout=45) as r:
                body = r.read()
        except urllib.error.HTTPError as e:
            last = f'HTTP {e.code}'
            _append(dict(kind='get', at=round(time.time()), url=full, status=e.code))
            if e.code in accept:
                return Miss(_http_error=e.code)
            if e.code in (429, 503, 502, 504):
                ra = e.headers.get('Retry-After')
                time.sleep(min(float(ra), 180) if ra and ra.replace('.', '').isdigit() else 20 * (attempt + 1))
                continue
            if e.code >= 500:
                time.sleep(10 * (attempt + 1))
                continue
            raise FetchError(f'{last} on {full}')
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last = type(e).__name__
            _append(dict(kind='get', at=round(time.time()), url=full, error=last))
            time.sleep(5 * (attempt + 1))
            continue
        if not raw:
            try:
                value = json.loads(body)
            except ValueError:
                last = 'invalid JSON'
                _append(dict(kind='get', at=round(time.time()), url=full, status=200, error=last, bytes=len(body)))
                time.sleep(5 * (attempt + 1))
                continue
            if isinstance(value, dict) and value.get('status') == '0' and 'message' in value:  # Etherscan answers 200 for its refusals
                text = (str(value.get('message')) + ' ' + str(value.get('result'))).lower()
                if not any(x in text for x in ('no transactions found', 'no internal transactions found', 'no records found', 'no token transfers found')):
                    last = text[:160]
                    _append(dict(kind='get', at=round(time.time()), url=full, status=200, refused=last))
                    if any(w in text for w in ('rate limit', 'busy', 'timeout', 'unexpected', 'try again', 'query timeout')):
                        time.sleep(4 * (attempt + 1))
                        continue
                    raise FetchError(f'explorer refused: {last} on {full}')
        _write(key, body)
        _append(dict(kind='get', at=round(time.time()), url=full, status=200, bytes=len(body), sha256=hashlib.sha256(body).hexdigest(), archive=str(_path(key).relative_to(ROOT))))
        return body if raw else json.loads(body)
    raise FetchError(f'failed after {retries} attempts ({last}): {full}')


def rpc(method, params, chain=137, cache=True):
    """A node refusing hands over to the next. All refusing raises. One node's null receipt is not an answer."""
    if method not in READ_METHODS:
        raise ValueError('method not permitted: ' + method)
    full = f'rpc:{chain}:{method}:' + json.dumps(params, sort_keys=True)
    key = request_key(full)
    if cache:
        body = _read(key)
        if body is not None:
            return json.loads(body)
    guard()
    errors = []
    payload = json.dumps(dict(jsonrpc='2.0', id=1, method=method, params=params)).encode()
    for endpoint in RPC[chain]:
        host = urllib.parse.urlsplit(endpoint).hostname
        _throttle(host)
        Stats.calls += 1
        try:
            with urllib.request.urlopen(urllib.request.Request(endpoint, data=payload, headers=UA), timeout=45) as r:
                body = r.read()
            answer = json.loads(body)
        except (urllib.error.URLError, TimeoutError, ValueError, OSError) as e:
            errors.append(f'{host}: {type(e).__name__}')
            continue
        if 'result' not in answer or answer.get('error'):
            errors.append(f"{host}: {str(answer.get('error'))[:120]}")
            continue
        if answer['result'] is None and method in ('eth_getTransactionReceipt', 'eth_getTransactionByHash'):
            errors.append(f'{host}: null')
            continue
        result = json.dumps(answer['result'], separators=(',', ':')).encode()
        if cache:
            _write(key, result)
        _append(dict(kind='rpc', at=round(time.time()), chain=chain, method=method, params=json.dumps(params)[:300], host=host, sha256=hashlib.sha256(result).hexdigest(), archive=str(_path(key).relative_to(ROOT)) if cache else None))
        return answer['result']
    _append(dict(kind='rpc_fail', at=round(time.time()), chain=chain, method=method, params=json.dumps(params)[:200], errors=errors[:4]))
    raise FetchError(f'{method} failed on every node: ' + '; '.join(errors))


def sol(method, params, cache=True):
    """Solana mainnet-beta only: publicnode has returned 0 signatures for paid addresses. Retries on 429 and node errors, raises after."""
    full = f'solana:{method}:' + json.dumps(params, sort_keys=True)
    key = request_key(full)
    if cache:
        body = _read(key)
        if body is not None:
            return json.loads(body)
    guard()
    endpoint = 'https://api.mainnet-beta.solana.com'
    payload = json.dumps(dict(jsonrpc='2.0', id=1, method=method, params=params)).encode()
    last = None
    for attempt in range(7):
        _throttle('api.mainnet-beta.solana.com')
        Stats.calls += 1
        try:
            with urllib.request.urlopen(urllib.request.Request(endpoint, data=payload, headers=UA), timeout=45) as r:
                answer = json.loads(r.read())
        except urllib.error.HTTPError as e:
            last = f'HTTP {e.code}'
            time.sleep(15 * (attempt + 1))
            continue
        except (urllib.error.URLError, TimeoutError, ValueError, OSError) as e:
            last = type(e).__name__
            time.sleep(5 * (attempt + 1))
            continue
        if answer.get('error') or 'result' not in answer:
            last = str(answer.get('error'))[:160]
            time.sleep(5 * (attempt + 1))
            continue
        if answer['result'] is None:  # a null from a node may be temporary: never archived as an answer
            last = 'null result'
            time.sleep(5 * (attempt + 1))
            continue
        result = json.dumps(answer['result'], separators=(',', ':')).encode()
        if cache:
            _write(key, result)
        _append(dict(kind='solana', at=round(time.time()), method=method, params=json.dumps(params)[:300], sha256=hashlib.sha256(result).hexdigest(), archive=str(_path(key).relative_to(ROOT)) if cache else None))
        return answer['result']
    _append(dict(kind='solana_fail', at=round(time.time()), method=method, params=json.dumps(params)[:200], error=str(last)[:160]))
    raise FetchError(f'solana {method} failed ({last})')


def etherscan_key():
    if os.environ.get('ETHERSCAN_API_KEY'):
        return os.environ['ETHERSCAN_API_KEY']
    for line in (Path.home() / 'Downloads/.env').read_text().splitlines():
        if line.startswith('ETHERSCAN_API_KEY='):
            return line.split('=', 1)[1].strip().strip('"\'')
    raise FetchError('no ETHERSCAN_API_KEY')


ES_COVERED = (1, 137, 42161)  # measured 02/11: the free plan refuses 8453, 10, 56


def es_all(chain, action, address=None, start=0, end=99_999_999, contract=None):
    """Whole list with Etherscan v2. A full page (10 000 rows) moves the start block forward: never silently truncated."""
    rows = []
    while True:
        params = dict(chainid=chain, module='account', action=action, startblock=start, endblock=end, page=1, offset=10000, sort='asc')
        if address:
            params['address'] = address
        if contract:
            params['contractaddress'] = contract
        d = get('https://api.etherscan.io/v2/api', params, secret=dict(apikey=etherscan_key()))
        page = d.get('result')
        if not isinstance(page, list):
            raise FetchError(f'not a list: {str(d)[:200]}')
        if len(page) < 10000:
            return rows + page
        last = int(page[-1]['blockNumber'])
        if last == start:
            raise FetchError(f'over 10 000 rows in the single block {last} of {address}: cannot page further')
        # the last block may be cut: drop it here, the next page re-reads it whole. Two identical transfers in one tx stay two rows.
        rows += [r for r in page if int(r['blockNumber']) < last]
        start = last


def verify_ledger(path=LEDGER):
    """Re-walk the chain. Returns (lines, first_broken_line or None)."""
    prev = 'GENESIS'
    n = 0
    with open(path) as f:
        for n, line in enumerate(f, 1):
            line = line.rstrip('\n')
            if json.loads(line).get('prev') != prev:
                return n, n
            prev = hashlib.sha256(line.encode()).hexdigest()
    return n, None


def verify_archive(limit=None):
    """Every archived body must still hash to what the ledger recorded."""
    bad = checked = 0
    with open(LEDGER) as f:
        for line in f:
            r = json.loads(line)
            if not r.get('archive') or not r.get('sha256'):
                continue
            p = ROOT / r['archive']
            if not p.exists():
                bad += 1
                continue
            with gzip.open(p, 'rb') as g:
                if hashlib.sha256(g.read()).hexdigest() != r['sha256']:
                    bad += 1
            checked += 1
            if limit and checked >= limit:
                break
    return checked, bad


def v2_all(path, params, max_pages=2000, stop=None):
    """Data API v2: cursor-only. Re-sends identical filters on every page, as the v2 docs require. Yields rows. `stop(row)` ends the walk early, on purpose."""
    cursor = None
    for _ in range(max_pages):
        p = dict(params)
        if cursor:
            p['cursor'] = cursor
        d = get('https://data-api.polymarket.com' + path, p)
        if 'data' not in d:
            raise FetchError(f'no data key on {path} {p}: {str(d)[:160]}')
        for row in d['data'] or []:
            if stop and stop(row):
                return
            yield row
        cursor = (d.get('pagination') or {}).get('next_cursor')
        if not cursor:
            return
    raise FetchError(f'over {max_pages} pages on {path} {params}')
