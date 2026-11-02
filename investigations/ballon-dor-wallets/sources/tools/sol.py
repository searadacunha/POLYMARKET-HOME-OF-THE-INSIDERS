"""Bounded public reads on Solana, cached. A failed read raises: it never becomes an empty history."""
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import net

ENDPOINTS = ('https://api.mainnet-beta.solana.com', 'https://solana-rpc.publicnode.com')
USDC = 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'
USDT = 'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB'


def rpc(method, params, pause=.5, immutable=False):
    key = net.hashlib.sha256(json.dumps(['sol', method, params]).encode()).hexdigest()
    if immutable:
        hit, value = net._load(key)
        if hit:
            return value
    net.guard()
    errors = []
    for attempt in range(4):
        for endpoint in ENDPOINTS:
            time.sleep(pause * (1 + attempt))
            net.Stats.calls += 1
            request = urllib.request.Request(endpoint, data=json.dumps(dict(jsonrpc='2.0', id=1, method=method, params=params)).encode(), headers=net.UA)
            try:
                with urllib.request.urlopen(request, timeout=40) as r:
                    body = json.loads(r.read())
            except (urllib.error.URLError, TimeoutError, ValueError) as e:
                errors.append(f'{endpoint}: {type(e).__name__}')
                continue
            net._note(kind='sol', method=method, host=endpoint, ok='result' in body)
            if 'result' in body and body['result'] is not None:
                if immutable:
                    net._store(key, body['result'])
                return body['result']
            errors.append(f"{endpoint}: {str(body.get('error') or 'null')[:100]}")
    raise RuntimeError(f'{method} failed: ' + '; '.join(errors[-4:]))


def signatures(address, limit=1000, max_pages=3, must_contain=()):
    """Newest first. `complete` is False when the page budget ran out, so a short history is never mistaken for the whole one.
    A node has answered an empty list for a funded address: any signature known to touch the address must appear, or this raises."""
    out, before = [], None
    complete = False
    for _ in range(max_pages):
        opts = dict(limit=limit)
        if before:
            opts['before'] = before
        page = rpc('getSignaturesForAddress', [address, opts])
        out += page
        if len(page) < limit:
            complete = True
            break
        before = page[-1]['signature']
    found = {s['signature'] for s in out}
    missing = [m for m in must_contain if m not in found]
    if missing and complete:
        raise RuntimeError(f'{address}: node returned {len(out)} signatures without the known {missing[:1]}: not a usable history')
    return out, complete


def transaction(signature):
    return rpc('getTransaction', [signature, dict(encoding='jsonParsed', maxSupportedTransactionVersion=0)], immutable=True)


def token_moves(tx):
    """Per owner and mint, what each account's token balance changed by in this transaction. The owner, not the token account, is the party."""
    meta = tx['meta']
    before = {(b['accountIndex'], b['mint']): b for b in meta.get('preTokenBalances') or []}
    after = {(b['accountIndex'], b['mint']): b for b in meta.get('postTokenBalances') or []}
    moves = []
    for key in set(before) | set(after):
        a, b = before.get(key), after.get(key)
        decimals = (a or b)['uiTokenAmount']['decimals']
        delta = int((b or {}).get('uiTokenAmount', {}).get('amount', 0)) - int((a or {}).get('uiTokenAmount', {}).get('amount', 0))
        if delta:
            moves.append(dict(owner=(b or a).get('owner'), mint=key[1], delta=delta / 10 ** decimals, raw=delta, decimals=decimals))
    return sorted(moves, key=lambda m: m['delta'])


def native_moves(tx, min_sol=.01):
    keys = [k['pubkey'] if isinstance(k, dict) else k for k in tx['transaction']['message']['accountKeys']]
    keys += (tx['meta'].get('loadedAddresses') or {}).get('writable', []) + (tx['meta'].get('loadedAddresses') or {}).get('readonly', [])
    return [dict(owner=k, delta=(b - a) / 1e9) for k, a, b in zip(keys, tx['meta']['preBalances'], tx['meta']['postBalances']) if abs(b - a) >= min_sol * 1e9]
