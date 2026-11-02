"""Public reads through one content-addressed store: the store is the checkpoint, and every answer keeps when and from whom.

One SQLite file instead of one file per answer, because the volume is a mechanical disk and the backup packs files.
A failure is never stored, so it can never replay as an empty history. Read-through to earlier investigations'
gz caches is explicit in the returned origin: an archived answer is not a fresh one.
"""
import gzip
import hashlib
import json
import os
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from .env import Guard, data_root

UA = {'User-Agent': 'phi-global-forensics/0.1 public-read-only', 'Content-Type': 'application/json', 'Accept': 'application/json'}
RPC = {137: ('https://polygon-bor-rpc.publicnode.com', 'https://polygon.drpc.org', 'https://gateway.tenderly.co/public/polygon'),
       1: ('https://ethereum-rpc.publicnode.com', 'https://eth.drpc.org', 'https://gateway.tenderly.co/public/mainnet'),
       42161: ('https://arbitrum-one-rpc.publicnode.com', 'https://arbitrum.drpc.org', 'https://gateway.tenderly.co/public/arbitrum'),
       8453: ('https://base-rpc.publicnode.com', 'https://base.drpc.org', 'https://gateway.tenderly.co/public/base'),
       10: ('https://optimism-rpc.publicnode.com', 'https://optimism.drpc.org', 'https://gateway.tenderly.co/public/optimism'),
       56: ('https://bsc-rpc.publicnode.com', 'https://bsc.drpc.org', 'https://56.rpc.thirdweb.com', 'https://bsc-mainnet.gateway.tatum.io')}
READ_METHODS = frozenset({'eth_getCode', 'eth_call', 'eth_getLogs', 'eth_getBalance', 'eth_getTransactionReceipt', 'eth_getTransactionByHash', 'eth_getBlockByNumber', 'eth_getTransactionCount', 'eth_blockNumber', 'eth_getStorageAt'})
PRIOR_CACHES = tuple(Path.home() / 'Projects' / p / 'state/http_cache' for p in ('PolySentinel-flow-trace', 'PolySentinel-investigation'))
RETRY_STATUS = (408, 425, 429, 500, 502, 503, 504, 520, 522, 524, 529)
FRESH, ARCHIVED = 'fresh', 'archived'


class Refused(RuntimeError):
    """The source said no, or every source failed. Never an empty result."""


class BudgetSpent(RuntimeError):
    pass


class Store:
    def __init__(self, path=None):
        self.path = Path(path) if path else data_root() / 'raw' / 'http_store.sqlite3'
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path, timeout=120)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('PRAGMA synchronous=NORMAL')
        self.db.execute('CREATE TABLE IF NOT EXISTS answers(key TEXT PRIMARY KEY, request TEXT NOT NULL, at REAL NOT NULL, host TEXT, sha256 TEXT NOT NULL, bytes INTEGER NOT NULL, body BLOB NOT NULL)')
        self.db.execute('CREATE TABLE IF NOT EXISTS ledger(id INTEGER PRIMARY KEY, at REAL, kind TEXT, host TEXT, request TEXT, status INTEGER, bytes INTEGER, note TEXT)')

    def get(self, key):
        row = self.db.execute('SELECT body, at, host, sha256 FROM answers WHERE key=?', (key,)).fetchone()
        return None if row is None else (json.loads(gzip.decompress(row[0])), dict(at=row[1], host=row[2], sha256=row[3], origin=FRESH))

    def put(self, key, request, host, value):
        raw = json.dumps(value, separators=(',', ':'), sort_keys=True).encode()
        now = time.time()
        digest = hashlib.sha256(raw).hexdigest()
        self.db.execute('INSERT OR REPLACE INTO answers VALUES(?,?,?,?,?,?,?)', (key, request[:4000], now, host, digest, len(raw), gzip.compress(raw, 6, mtime=0)))
        self.db.commit()
        return dict(at=now, host=host, sha256=digest, origin=FRESH)

    def note(self, kind, host, request, status=None, size=None, note=None):
        self.db.execute('INSERT INTO ledger(at,kind,host,request,status,bytes,note) VALUES(?,?,?,?,?,?,?)', (time.time(), kind, host, request[:500], status, size, note))
        self.db.commit()


class Net:
    """One worker. Budgets are per run, and the guard is polled before every network call."""

    def __init__(self, store=None, budget=200_000, guard=None, read_prior=True):
        self.store, self.budget, self.guard, self.read_prior = store or Store(), budget, guard or Guard(), read_prior
        self.calls = self.hits = 0
        self.key_cache = None

    def _spend(self):
        if self.calls >= self.budget:
            raise BudgetSpent(f'{self.budget} requests spent')
        self.calls += 1

    def _prior(self, key):
        if not self.read_prior:
            return None
        for base in PRIOR_CACHES:
            path = base / key[:2] / (key + '.json.gz')
            if path.exists():
                with gzip.open(path, 'rt') as f:
                    return json.load(f), dict(at=path.stat().st_mtime, host=base.parent.parent.name, sha256=None, origin=ARCHIVED)
        return None

    def get(self, url, params=None, pause=.25, retries=7, secret=None, accept=(400, 404), fresh=False):
        """JSON from a public GET. `secret` goes on the wire only, never in the key, the store or the ledger."""
        full = url + ('?' + urllib.parse.urlencode(params) if params else '')
        key = hashlib.sha256(full.encode()).hexdigest()
        if not fresh:
            found = self.store.get(key) or self._prior(key)
            if found:
                self.hits += 1
                return found
        wire = full + (('&' if '?' in full else '?') + urllib.parse.urlencode(secret) if secret else '')
        host = urllib.parse.urlsplit(url).hostname
        for attempt in range(retries):
            self.guard()
            self._spend()
            time.sleep(pause * (1 + 3 * attempt))
            try:
                with urllib.request.urlopen(urllib.request.Request(wire, headers=UA), timeout=60) as r:
                    body = r.read()
                value = json.loads(body)
                self.store.note('get', host, full, 200, len(body))
                if isinstance(value, dict) and value.get('status') == '0' and 'No ' not in str(value.get('message')):
                    text = (str(value.get('message')) + str(value.get('result'))).lower()
                    if any(w in text for w in ('rate limit', 'busy', 'timeout', 'unexpected', 'max calls')):
                        time.sleep(5 * (attempt + 1))
                        continue
                    raise Refused(f'{host}: {str(value.get("message"))[:120]} {str(value.get("result"))[:160]}')
                return value, self.store.put(key, full, host, value)
            except urllib.error.HTTPError as e:
                self.store.note('get', host, full, e.code)
                if e.code in accept:
                    return dict(_http_error=e.code), dict(at=time.time(), host=host, sha256=None, origin=FRESH)
                if e.code not in RETRY_STATUS:
                    raise Refused(f'{host}: HTTP {e.code}') from e
                time.sleep(min(60, 5 * (attempt + 1)))
            except (urllib.error.URLError, TimeoutError, ValueError, OSError) as e:
                self.store.note('get', host, full, None, None, type(e).__name__)
        raise Refused(f'GET failed after {retries} tries: {full[:200]}')

    def rpc(self, method, params, chain=137, pause=.12, cache=True, endpoints=None):
        """A node refusing hands over to the next. All failing raises. A null receipt from one node is not an answer."""
        if method not in READ_METHODS:
            raise ValueError('Method not permitted: ' + method)
        key = hashlib.sha256(json.dumps([chain, method, params]).encode()).hexdigest()
        request = json.dumps([chain, method, params])
        if cache and not endpoints:
            found = self.store.get(key) or self._prior(key)
            if found:
                self.hits += 1
                return found
        errors = []
        for endpoint in endpoints or RPC[chain]:
            self.guard()
            self._spend()
            time.sleep(pause)
            host = urllib.parse.urlsplit(endpoint).hostname
            try:
                req = urllib.request.Request(endpoint, data=json.dumps(dict(jsonrpc='2.0', id=1, method=method, params=params)).encode(), headers=UA)
                with urllib.request.urlopen(req, timeout=45) as r:
                    body = json.loads(r.read())
            except (urllib.error.URLError, TimeoutError, ValueError, OSError) as e:
                errors.append(f'{host}: {type(e).__name__}')
                self.store.note('rpc', host, request, None, None, type(e).__name__)
                continue
            if 'result' in body and not body.get('error'):
                if body['result'] is None and method in ('eth_getTransactionReceipt', 'eth_getTransactionByHash', 'eth_getBlockByNumber'):
                    errors.append(f'{host}: null')
                    continue
                self.store.note('rpc', host, request, 200)
                meta = dict(at=time.time(), host=host, sha256=None, origin=FRESH)
                if cache:
                    meta = self.store.put(key if not endpoints else hashlib.sha256((key + host).encode()).hexdigest(), request, host, body['result'])
                return body['result'], meta
            errors.append(f"{host}: {str(body.get('error'))[:140]}")
            self.store.note('rpc', host, request, None, None, str(body.get('error'))[:200])
        raise Refused(f'{method} failed on every node: ' + '; '.join(errors))

    def post_json(self, endpoint, method, params, pause=1.0, retries=5):
        """JSON-RPC on a non-EVM node. Stored like every answer; a null or an error is never stored."""
        request = json.dumps([endpoint, method, params])
        key = hashlib.sha256(request.encode()).hexdigest()
        found = self.store.get(key)
        if found:
            self.hits += 1
            return found
        host = urllib.parse.urlsplit(endpoint).hostname
        errors = []
        for attempt in range(retries):
            self.guard()
            self._spend()
            time.sleep(pause * (1 + 3 * attempt))
            try:
                req = urllib.request.Request(endpoint, data=json.dumps(dict(jsonrpc='2.0', id=1, method=method, params=params)).encode(), headers=UA)
                with urllib.request.urlopen(req, timeout=60) as r:
                    body = json.loads(r.read())
            except urllib.error.HTTPError as e:
                errors.append(f'http {e.code}')
                self.store.note('rpc', host, request, e.code)
                if e.code == 429:
                    time.sleep(15 * (attempt + 1))
                continue
            except (urllib.error.URLError, TimeoutError, ValueError, OSError) as e:
                errors.append(type(e).__name__)
                continue
            if 'result' in body and body['result'] is not None:
                self.store.note('rpc', host, request, 200)
                return body['result'], self.store.put(key, request, host, body['result'])
            errors.append(str(body.get('error') or 'null')[:120])
        raise Refused(f'{host} {method}: ' + '; '.join(errors[-3:]))

    def tron_info(self, tx, pause=1.1, retries=5):
        """TronGrid's receipt of one transaction, stored. Keyless limit about 1 request per second. Empty means the node has no such transaction: that raises."""
        url = 'https://api.trongrid.io/wallet/gettransactioninfobyid'
        request = json.dumps(['tron', tx])
        key = hashlib.sha256(request.encode()).hexdigest()
        found = self.store.get(key)
        if found:
            self.hits += 1
            return found[0]
        for attempt in range(retries):
            self.guard()
            self._spend()
            time.sleep(pause * (1 + 2 * attempt))
            try:
                req = urllib.request.Request(url, data=json.dumps(dict(value=tx)).encode(), headers=UA)
                with urllib.request.urlopen(req, timeout=45) as r:
                    body = json.loads(r.read())
            except urllib.error.HTTPError as e:
                self.store.note('rpc', 'api.trongrid.io', request, e.code)
                time.sleep(10 * (attempt + 1))
                continue
            except (urllib.error.URLError, TimeoutError, ValueError, OSError) as e:
                self.store.note('rpc', 'api.trongrid.io', request, None, None, type(e).__name__)
                continue
            if body:
                self.store.put(key, request, 'api.trongrid.io', body)
                return body
            raise Refused(f'tron: no such transaction {tx}')
        raise Refused(f'tron: no answer for {tx}')

    def etherscan_key(self):
        """Only this variable is read from the file; the private keys beside it are never loaded."""
        if self.key_cache:
            return self.key_cache
        if os.environ.get('ETHERSCAN_API_KEY'):
            self.key_cache = os.environ['ETHERSCAN_API_KEY']
            return self.key_cache
        for line in (Path.home() / 'Downloads/.env').read_text().splitlines():
            if line.startswith('ETHERSCAN_API_KEY='):
                self.key_cache = line.split('=', 1)[1].strip().strip('"\'')
                return self.key_cache
        raise Refused('no ETHERSCAN_API_KEY')
