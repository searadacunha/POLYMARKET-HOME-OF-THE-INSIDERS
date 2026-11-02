"""Bounded public reads on Solana. A failed read raises: it never becomes an empty history."""
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import net

# publicnode answers null for these transactions and has answered 0 signatures for funded addresses: never trust it. Tatum serves them.
ENDPOINT = 'https://api.mainnet-beta.solana.com'
SECOND = 'https://solana-mainnet.gateway.tatum.io'
USDC = 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'
USDT = 'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB'
WSOL = 'So11111111111111111111111111111111111111112'
MINTS = {USDC: 'USDC', USDT: 'USDT', WSOL: 'WSOL'}
PAGE = 1000


def rpc(method, params, endpoint=ENDPOINT, cache=True):
    key = hashlib.sha256(json.dumps(['sol', method, params] if endpoint == ENDPOINT else ['flow-sol', endpoint, method, params]).encode()).hexdigest()  # same key as the investigation's cache on the first endpoint
    if cache:
        hit, value = net._load(key)
        if hit:
            return value
    net.guard()
    errors = []
    for attempt in range(6):
        time.sleep(1.0 + 3 * attempt)
        net.Stats.calls += 1
        req = urllib.request.Request(endpoint, data=json.dumps(dict(jsonrpc='2.0', id=1, method=method, params=params)).encode(), headers=net.UA)
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                body = json.loads(r.read())
        except urllib.error.HTTPError as e:
            errors.append(f'http {e.code}')
            if e.code == 429:
                time.sleep(15 * (attempt + 1))
            continue
        except (urllib.error.URLError, TimeoutError, ValueError, OSError) as e:
            errors.append(type(e).__name__)
            continue
        net.note(kind='sol', method=method, host=endpoint.split('//')[1], ok='result' in body)
        if 'result' in body and body['result'] is not None:
            if cache:
                net._store(key, body['result'])
            return body['result']
        errors.append(str(body.get('error') or 'null')[:100])
    raise RuntimeError(f'{method} failed: ' + '; '.join(errors[-3:]))


def signatures(address, max_pages=1, must_contain=()):
    """Newest first. `complete` False means the page budget ran out, so a busy address is never read as a short one."""
    out, before, complete = [], None, False
    for _ in range(max_pages):
        opts = dict(limit=PAGE)
        if before:
            opts['before'] = before
        page = rpc('getSignaturesForAddress', [address, opts])
        out += page
        if len(page) < PAGE:
            complete = True
            break
        before = page[-1]['signature']
    found = {s['signature'] for s in out}
    missing = [m for m in must_contain if m not in found]
    if missing and complete:
        raise RuntimeError(f'{address}: {len(out)} signatures without the known {missing[:1]}: not a usable history')
    return out, complete


def transaction(signature, endpoint=ENDPOINT):
    return rpc('getTransaction', [signature, dict(encoding='jsonParsed', maxSupportedTransactionVersion=0)], endpoint=endpoint)


def keys_of(tx):
    keys = [k['pubkey'] if isinstance(k, dict) else k for k in tx['transaction']['message']['accountKeys']]
    loaded = tx['meta'].get('loadedAddresses') or {}
    return keys + loaded.get('writable', []) + loaded.get('readonly', [])


def signers(tx):
    return [k['pubkey'] for k in tx['transaction']['message']['accountKeys'] if isinstance(k, dict) and k.get('signer')]


def moves(tx):
    """Per owner: SPL balance deltas (the owner is the party, not the token account) and SOL deltas, fee excluded for nobody: the raw ledger change."""
    meta = tx['meta']
    before = {(b['accountIndex'], b['mint']): b for b in meta.get('preTokenBalances') or []}
    after = {(b['accountIndex'], b['mint']): b for b in meta.get('postTokenBalances') or []}
    out = []
    for key in set(before) | set(after):
        a, b = before.get(key), after.get(key)
        dec = (a or b)['uiTokenAmount']['decimals']
        raw = int((b or {}).get('uiTokenAmount', {}).get('amount', 0)) - int((a or {}).get('uiTokenAmount', {}).get('amount', 0))
        if raw:
            out.append(dict(owner=(b or a).get('owner'), mint=key[1], raw=raw, decimals=dec))
    for k, x, y in zip(keys_of(tx), meta['preBalances'], meta['postBalances']):
        if y != x:
            out.append(dict(owner=k, mint='SOL', raw=y - x, decimals=9))
    return out


def memo(tx):
    for ins in tx['transaction']['message']['instructions']:
        if ins.get('program') == 'spl-memo':
            return ins.get('parsed')
    return None
