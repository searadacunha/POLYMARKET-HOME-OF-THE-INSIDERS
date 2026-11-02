"""Reads only. The collector's database is opened read-only through the engine's own functions, so its schema stays in one place."""
import json
import sqlite3
from pathlib import Path
from urllib.parse import urlsplit

import httpx

from .paths import assert_isolated
from .recover import InvalidResponse, Permanent, Transient

MAX_BODY = 8_000_000


class CollectorSource:
    def __init__(self, source):
        from signal_engine import service
        assert_isolated(service.STATE)  # its enrichment and ledger paths come from here
        self.service = service
        self.database = Path(source['database']).expanduser()
        self.limit = source.get('batch_rows', 20000)
        self.cx = sqlite3.connect(f'file:{self.database}?mode=ro', uri=True, timeout=10)
        self.cx.execute('PRAGMA query_only=ON')

    def close(self):
        self.cx.close()

    def has_new(self, cursor):
        return self.cx.execute('SELECT 1 FROM trade_index WHERE observed_at>? LIMIT 1', (cursor,)).fetchone() is not None

    def new_trades(self, cursor):
        return self.service.read_new_trades(self.cx, cursor, self.limit)

    def refresh_markets(self, store, trades, now):
        self.service.refresh_markets(store, self.cx, trades, now)

    def gaps(self, start, end):
        return self.service.coverage_gaps(self.cx, start, end)

    def milestone(self, event_key):
        return self.service.public_milestone(self.cx, event_key)

    def winners(self, market_id):
        """Winning tokens of a settled market, or None. Only a closed market with a price at one counts as settled."""
        market = self.service.collector_object(self.cx, 'market', market_id)
        if not market or market.get('closed') is not True:
            return None
        raw = market.get('raw') or {}
        try:
            tokens, prices = json.loads(raw['clobTokenIds']), json.loads(raw['outcomePrices'])
        except (KeyError, TypeError, ValueError):
            return None
        won = {str(t) for t, p in zip(tokens, prices) if float(p) >= .99}
        return won or None


class NotFound(Permanent):
    pass


def get_json(url, *, allowed_hosts, validate, timeout=10):
    """One bounded GET, classified: outage and rate limit are retried, refusal is final, and a bad body is never returned as data."""
    parts = urlsplit(url)
    if parts.hostname not in allowed_hosts:
        raise Permanent(f'Host {parts.hostname} is not allowed')
    try:
        response = httpx.get(url, timeout=timeout, follow_redirects=False, trust_env=False, headers={'User-Agent': 'PolySentinel/0.1 public-read-only'})
    except httpx.HTTPError as exc:
        raise Transient(f'{type(exc).__name__} on {parts.hostname}') from exc
    if response.status_code == 429 or response.status_code >= 500:
        after = response.headers.get('retry-after')
        raise Transient(f'HTTP {response.status_code} from {parts.hostname}', retry_after=float(after) if after and after.isdigit() else None)
    if response.status_code == 404:
        raise NotFound(f'HTTP 404 from {parts.hostname}')
    if response.status_code != 200:
        raise Permanent(f'HTTP {response.status_code} from {parts.hostname}')
    if len(response.content) > MAX_BODY:
        raise InvalidResponse(f'{len(response.content)} bytes from {parts.hostname}, over the ceiling')
    try:
        body = response.json()
    except ValueError as exc:
        raise InvalidResponse(f'Unparsable JSON from {parts.hostname}') from exc
    problem = validate(body)
    if problem:
        raise InvalidResponse(f'{problem} from {parts.hostname}')
    return body


def receipt_problem(tx):
    """A receipt that names another transaction, or has no list of fills, is refused rather than read as an empty result."""
    def problem(body):
        if not isinstance(body, dict) or not isinstance(body.get('fills'), list):
            return 'Receipt without a list of fills'
        if str(body.get('transaction_hash', '')).lower() != tx.lower():
            return 'Receipt for another transaction'
        for fill in body['fills']:
            if not isinstance(fill, dict) or not str(fill.get('nominal_raw', '')).isdigit():
                return 'Fill without a raw amount'
        return None
    return problem


class Receipts:
    """Decoded on-chain fills by transaction. `http` reads a service of decoded receipts; `file` reads a saved set; `rpc` reads public nodes, and a block not yet final counts as no receipt."""

    def __init__(self, chain):
        self.type = chain.get('type', 'none')
        self.chain = chain
        self.file = json.loads(Path(chain['path']).read_text()) if self.type == 'file' else None

    def get(self, tx):
        if self.type == 'none':
            return None
        if self.type == 'file':
            return self.file.get(tx.lower())
        if self.type == 'http':
            try:
                return get_json(self.chain['url'].format(tx=tx), allowed_hosts=set(self.chain['hosts']), validate=receipt_problem(tx))
            except NotFound:
                return None  # not mined or not indexed yet: the check stays open, it does not fail
        if self.type == 'rpc':
            return rpc_fills(tx)
        raise Permanent(f'Unknown chain source {self.type}')


def rpc_fills(tx):
    from polysentinel.chain import decode_order, registry
    from signal_engine.fund_flow.client import BudgetExhausted, ChainError, Client, FINAL_DEPTH
    contracts = registry(Path(__file__).resolve().parent.parent)
    client = Client(rpc_limit=6, http_limit=0)
    try:
        receipt = client.receipt(tx)
        if receipt is None or client.head() - int(receipt['blockNumber'], 16) < FINAL_DEPTH:
            return None  # a block that can still be reorganised proves nothing yet
    except (BudgetExhausted, ChainError) as exc:
        raise Transient(str(exc)) from exc
    finally:
        client.close()
    fills = []
    for log in receipt.get('logs', []):
        try:
            decoded = decode_order(log, contracts)
        except (ValueError, KeyError) as exc:  # one unreadable log must not read as a transaction with fewer fills
            raise InvalidResponse(f'Undecodable log in {tx}: {exc}') from exc
        if decoded:
            fills.append(dict(decoded, transaction_hash=tx))
    return dict(transaction_hash=tx, status=int(receipt.get('status', '0x1'), 16), fills=fills)
