"""Bounded public reads with a request ledger. No key, no write method, no other host."""
import json
import time
from pathlib import Path
from urllib.parse import urlsplit

import httpx

ENDPOINTS = {137: ('https://gateway.tenderly.co/public/polygon', 'https://rpc-mainnet.matic.quiknode.pro', 'https://polygon-bor-rpc.publicnode.com', 'https://polygon.drpc.org'),
             1: ('https://gateway.tenderly.co/public/mainnet', 'https://ethereum-rpc.publicnode.com'), 42161: ('https://gateway.tenderly.co/public/arbitrum', 'https://arbitrum-one-rpc.publicnode.com'),
             8453: ('https://gateway.tenderly.co/public/base', 'https://base-rpc.publicnode.com'), 10: ('https://gateway.tenderly.co/public/optimism', 'https://optimism-rpc.publicnode.com'), 56: ('https://bsc-rpc.publicnode.com',)}
METHODS = frozenset({'eth_chainId', 'eth_blockNumber', 'eth_getCode', 'eth_call', 'eth_getLogs', 'eth_getBalance', 'eth_getStorageAt', 'eth_getTransactionReceipt', 'eth_getTransactionByHash', 'eth_getBlockByNumber'})
HOSTS = frozenset({'data-api.polymarket.com', 'bridge.polymarket.com', 'api.relay.link'})
FINAL_DEPTH = 256  # Polygon blocks; a younger receipt is reported, not treated as settled
MAX_BODY = 32_000_000


class BudgetExhausted(RuntimeError):
    pass


class ChainError(RuntimeError):
    pass


class Client:
    def __init__(self, rpc_limit=300, http_limit=60, pause_s=.15, ledger=None, transport=None):
        self.rpc_limit, self.http_limit, self.pause_s, self.ledger = rpc_limit, http_limit, pause_s, Path(ledger) if ledger else None
        self.rpc_used = self.http_used = 0
        self.http = httpx.Client(timeout=25, headers={'User-Agent': 'PolySentinel/0.1 public-read-only'}, transport=transport)
        self.receipts, self.heads, self.blocks = {}, {}, {}

    def _note(self, **fields):
        if self.ledger:
            self.ledger.parent.mkdir(parents=True, exist_ok=True)
            with self.ledger.open('a') as f:
                f.write(json.dumps(dict(at=time.time(), **fields)) + '\n')

    def rpc(self, method, params, chain=137):
        """Each attempt spends budget. A node that cannot answer hands over to the next, and all failing raises."""
        if method not in METHODS:
            raise ValueError('Method not permitted: ' + method)
        errors = []
        for url in ENDPOINTS[chain]:
            if self.rpc_used >= self.rpc_limit:
                raise BudgetExhausted(f'{self.rpc_limit} RPC requests spent')
            self.rpc_used += 1
            time.sleep(self.pause_s)
            try:
                response = self.http.post(url, json=dict(jsonrpc='2.0', id=1, method=method, params=params))
                body = response.json()
            except (httpx.HTTPError, ValueError) as exc:
                errors.append(f'{urlsplit(url).hostname}: {type(exc).__name__}')
                continue
            self._note(kind='rpc', chain=chain, method=method, host=urlsplit(url).hostname, ok='result' in body)
            if 'result' in body and not body.get('error'):
                return body['result']
            message = str(body.get('error'))[:160]
            if 'revert' in message:
                raise ChainError('reverted')
            errors.append(f'{urlsplit(url).hostname}: {message}')
        raise ChainError('; '.join(errors))

    def head(self, chain=137):
        if chain not in self.heads:
            self.heads[chain] = int(self.rpc('eth_blockNumber', [], chain), 16)
        return self.heads[chain]

    def receipt(self, transaction, chain=137):
        key = (chain, transaction.lower())
        if key not in self.receipts:
            receipt = self.rpc('eth_getTransactionReceipt', [transaction], chain)
            if receipt is None:
                self.receipts[key] = None
            else:
                if receipt.get('transactionHash', '').lower() != transaction.lower():
                    raise ChainError('Node returned another transaction')
                self.receipts[key] = receipt
        return self.receipts[key]

    def block_time(self, number, chain=137):
        key = (chain, number)
        if key not in self.blocks:
            block = self.rpc('eth_getBlockByNumber', [hex(number), False], chain)
            if not block:
                raise ChainError(f'Block {number} unavailable on chain {chain}')
            self.blocks[key] = int(block['timestamp'], 16)
        return self.blocks[key]

    def call(self, to, data, block='latest', chain=137):
        return self.rpc('eth_call', [dict(to=to, data=data), block], chain)

    def get_json(self, url, params=None):
        host = urlsplit(url).hostname
        if host not in HOSTS:
            raise ValueError('Host not permitted: ' + str(host))
        if self.http_used >= self.http_limit:
            raise BudgetExhausted(f'{self.http_limit} HTTP requests spent')
        self.http_used += 1
        time.sleep(self.pause_s)
        response = self.http.get(url, params=params)
        self._note(kind='http', host=host, path=urlsplit(url).path, status=response.status_code)
        if len(response.content) > MAX_BODY:
            raise ChainError('Response too large')
        return response.status_code, response.json() if 'json' in response.headers.get('content-type', '') else None

    def close(self):
        self.http.close()
