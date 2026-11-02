"""Bounded public HTTP reads, preserving response bytes and failure states."""
import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import ipaddress
import json
import random
import socket
import shutil
from pathlib import Path
import time
from urllib.parse import urlsplit

import httpx
from .storage_budget import require_capacity, reserve_bytes


class SourceError(RuntimeError):
    def __init__(self, message, status=None, evidence_id=None, retry_after=None):
        super().__init__(message)
        self.status = status
        self.evidence_id = evidence_id
        self.retry_after = retry_after


class ResponseTooLarge(SourceError):
    """The unchanged decoded-response byte ceiling was reached."""


@dataclass
class Response:
    body: object
    status: int
    observed_at: float
    evidence_id: str
    headers: dict


class Net:
    def __init__(self, store, config):
        self.store = store
        self.config = config
        self.requests_used = 0
        self._sem = asyncio.Semaphore(min(4, config.get('request_concurrency', 4)))
        self._client = None
        self._hosts = set()
        self._stats = {}

    def begin_cycle(self):
        self.requests_used = 0
        for metrics in self._stats.values():
            for key in ('requests','responses','bytes','errors','empty_responses','rate_limited','dns_errors'):
                metrics[key] = 0

    async def __aenter__(self):
        self._client = httpx.AsyncClient(timeout=self.config.get('request_timeout', 20),
                                       follow_redirects=False, trust_env=False,
                                       headers={'User-Agent': 'PolySentinel/0.1 public-read-only'})
        return self

    async def __aexit__(self, *args):
        await self._client.aclose()

    async def _public_url(self, url):
        parts = urlsplit(url)
        if parts.scheme != 'https' or parts.username or parts.password or not parts.hostname:
            raise SourceError('URL publique HTTPS requise')
        host = parts.hostname
        if parts.port not in (None, 443) or '.' not in host or host.endswith(('.local', '.localhost')):
            raise SourceError('Hôte non public refusé')
        if host not in self._hosts:
            addresses = await asyncio.to_thread(socket.getaddrinfo, host, 443, type=socket.SOCK_STREAM)
            if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
                raise SourceError('Adresse réseau privée refusée')
            self._hosts.add(host)
        return host

    @staticmethod
    def retry_delay(header):
        if not header:
            return None
        try:
            return max(0, float(header))
        except ValueError:
            try:
                return max(0, (parsedate_to_datetime(header) - datetime.now(timezone.utc)).total_seconds())
            except (ValueError, TypeError):
                return None

    def _source_health(self, host, status, detail, **metrics):
        previous = self.store.get('health', 'http:' + host)
        prior_success = previous['payload'].get('last_success') if previous else None
        current_success = metrics.get('last_success')
        metrics['last_success'] = max(prior_success or 0, current_success or 0) or None
        self.store.health('http:' + host, status, detail, **metrics)

    def _resource_guard(self):
        try:require_capacity(self.store.root,self.config,reserve_bytes(self.config))
        except RuntimeError as exc:
            self.store.health('resources','degraded','Collecte suspendue : '+str(exc))
            raise SourceError(str(exc),status=507) from exc

    async def request(self, url, params=None, method='GET', json_body=None):
        method = method.upper()
        if method not in ('GET', 'POST'):
            raise SourceError('Méthode interdite: lecture seule')
        if method == 'POST':
            rpc_reads = {'eth_chainId', 'eth_blockNumber', 'eth_getTransactionReceipt', 'eth_getTransactionByHash',
                         'eth_getBlockByNumber', 'eth_getBlockByHash', 'eth_getLogs', 'eth_getCode', 'eth_call'}
            if not isinstance(json_body, dict) or json_body.get('method') not in rpc_reads:
                raise SourceError('Seules les lectures JSON-RPC autorisées peuvent utiliser POST')
        host = urlsplit(url).hostname or 'invalid-url'
        previous = self.store.get('health', 'http:' + host)
        prior = previous['payload'] if previous else {}
        initial = {}
        for key in ('requests','responses','bytes','errors','empty_responses','rate_limited','dns_errors'):
            initial[key] = 0
            initial[key+'_total'] = prior.get(key+'_total',0)
        metrics = self._stats.setdefault(host,initial)
        last_success = prior.get('last_success')
        try:
            host = await self._public_url(url)
        except (OSError, ValueError, SourceError) as exc:
            for key in ('errors','dns_errors'):
                metrics[key] += 1
                metrics[key+'_total'] += 1
            self._source_health(host,'error',str(exc),**metrics,last_success=last_success)
            raise SourceError(str(exc)) from exc
        last_error = None
        attempts = self.config.get('request_attempts', 3)
        for attempt in range(attempts):
            async with self._sem:
                if self.requests_used >= self.config.get('requests_per_cycle', 100):
                    raise SourceError('Budget de requêtes du cycle épuisé', status=429)
                self._resource_guard()
                self.requests_used += 1
                metrics['requests'] += 1
                metrics['requests_total'] += 1
                started = time.time()
                body = bytearray()
                status = 0
                headers = {}
                try:
                    async with self._client.stream(method, url, params=params, json=json_body) as response:
                        status = response.status_code
                        metrics['responses'] += 1
                        metrics['responses_total'] += 1
                        if status == 429:
                            metrics['rate_limited'] += 1
                            metrics['rate_limited_total'] += 1
                        headers = dict(response.headers)
                        async for chunk in response.aiter_bytes():
                            if len(body) + len(chunk) > self.config.get('response_max_bytes', 8000000):
                                raise ResponseTooLarge('Réponse tronquée: plafond octets atteint', status=status)
                            body.extend(chunk)
                    observed = time.time()
                    evidence_id = self.store.evidence(url, {'query': params or {}, 'method': method,
                                                           'json': json_body, 'headers': headers}, status,
                                                      bytes(body), observed)
                    metrics['bytes'] += len(body)
                    metrics['bytes_total'] += len(body)
                    if status < 200 or status >= 300:
                        metrics['errors'] += 1
                        metrics['errors_total'] += 1
                        detail = body.decode('utf-8', errors='replace')[:400]
                        retry_after = self.retry_delay(headers.get('retry-after'))
                        last_error = SourceError(f'HTTP {status}: {detail}', status, evidence_id, retry_after)
                        self._source_health(host, 'error', str(last_error), **metrics,
                                          elapsed=time.time()-started, http_status=status, last_success=last_success)
                        if status not in (429, 500, 502, 503, 504):
                            raise last_error
                    else:
                        content_type = headers.get('content-type', '')
                        if 'json' in content_type:
                            try:
                                parsed = json.loads(body)
                            except (ValueError, UnicodeError) as exc:
                                raise SourceError('JSON malformé', status, evidence_id) from exc
                        else:
                            parsed = body.decode('utf-8', errors='replace')
                        if parsed == '' or parsed == [] or (isinstance(parsed,dict) and any(k in parsed and parsed[k] == [] for k in ('data','events','markets'))):
                            metrics['empty_responses'] += 1
                            metrics['empty_responses_total'] += 1
                        self._source_health(host, 'ok', 'Réponse reçue', **metrics,
                                          elapsed=time.time()-started, http_status=status,
                                          cache_age=headers.get('age'), last_success=observed)
                        return Response(parsed, status, observed, evidence_id, headers)
                except (httpx.HTTPError, OSError) as exc:
                    evidence_id = self.store.evidence(url, {'query': params or {}, 'method': method, 'json': json_body},
                                                      status, {'transport_error': str(exc), 'partial_bytes': len(body)})
                    last_error = SourceError(f'Erreur transport: {exc}', status, evidence_id)
                    metrics['errors'] += 1
                    metrics['errors_total'] += 1
                    self._source_health(host, 'error', str(last_error), **metrics, last_success=last_success)
                except SourceError as exc:
                    if exc is not last_error:
                        evidence_id = exc.evidence_id or self.store.evidence(url, {'query': params or {}, 'error': str(exc)}, status, bytes(body))
                        metrics['errors'] += 1
                        metrics['errors_total'] += 1
                        self._source_health(host, 'error', str(exc), **metrics, last_success=last_success)
                        exc.evidence_id = evidence_id
                    raise
            if attempt + 1 < attempts:
                delay = last_error.retry_after
                if delay is not None and delay > 30:
                    raise last_error
                await asyncio.sleep(delay if delay is not None else min(10, 2**attempt + random.random()))
        raise last_error
