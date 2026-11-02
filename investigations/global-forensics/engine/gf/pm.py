"""Polymarket's public read routes. No key, no order route, and the profile fields (name, bio, image) stay out.

A capped history says it is capped. The v1 routes answer 410 since their retirement, so everything here goes through /v2.
"""
from .net import Refused

DATA = 'https://data-api.polymarket.com'
GAMMA = 'https://gamma-api.polymarket.com'
ROW_KEEP = ('type', 'timestamp', 'usdc_size', 'usdcSize', 'size', 'side', 'transaction_hash', 'transactionHash', 'condition_id', 'conditionId', 'token_id', 'asset', 'price', 'outcome', 'outcome_index', 'outcomeIndex', 'title', 'slug', 'event_slug', 'eventSlug')
TRADE_KEEP = ('proxy_wallet', 'side', 'token_id', 'condition_id', 'size', 'price', 'timestamp', 'transaction_hash', 'outcome', 'outcome_index', 'title', 'slug', 'event_slug')


def activity(net, wallet, max_rows=50_000, limit=500):
    """Whole /v2/activity, oldest first. `complete` is true only when the API says there is no next page."""
    wallet = wallet.lower()
    rows, cursor = [], None
    origins = set()
    while len(rows) < max_rows:
        params = dict(user=wallet, limit=limit, sort_by='TIMESTAMP', sort_direction='ASC', exclude_deposits_withdrawals='false')
        if cursor:
            params['cursor'] = cursor
        body, meta = net.get(DATA + '/v2/activity', params, pause=.15)
        origins.add(meta['origin'])
        if '_http_error' in body:
            raise Refused(f"activity {wallet}: HTTP {body['_http_error']}")
        rows += [{k: r[k] for k in ROW_KEEP if k in r} for r in body.get('data') or []]
        page = body.get('pagination') or {}
        cursor = page.get('next_cursor')
        if not cursor or not page.get('has_more', True):
            return dict(wallet=wallet, rows=rows, complete=True, origins=sorted(origins))
    return dict(wallet=wallet, rows=rows, complete=False, origins=sorted(origins))


def has_activity(net, wallet):
    body, _ = net.get(DATA + '/v2/activity', dict(user=wallet.lower(), limit=5, sort_by='TIMESTAMP', sort_direction='ASC', exclude_deposits_withdrawals='false'), pause=.15)
    return bool(body.get('data')) if '_http_error' not in body else False


def markets_by_condition(net, condition_ids):
    out = {}
    ids = list(condition_ids)
    for i in range(0, len(ids), 20):
        for closed in ('true', 'false'):
            body, _ = net.get(GAMMA + '/markets', [('condition_ids', c) for c in ids[i:i + 20]] + [('closed', closed), ('limit', 100)], pause=.15)
            for m in body if isinstance(body, list) else []:
                out[m.get('conditionId', '').lower()] = m
    return out


def search_markets(net, **params):
    body, _ = net.get(GAMMA + '/markets', params, pause=.15)
    return body if isinstance(body, list) else []


def event(net, slug):
    body, _ = net.get(GAMMA + '/events', dict(slug=slug), pause=.15)
    return body[0] if isinstance(body, list) and body else None


def trades(net, condition, start, end, taker_only=True, max_pages=4000):
    """Every trade of one market in [start, end], streamed newest first by cursor (v1 /trades answers 410 since its retirement).

    Yields rows and finally a dict with key _coverage: stopped_at says how far back the walk went. A walk that ends on the page cap says so.
    """
    cursor, pages, oldest, newest, stop = None, 0, None, None, 'exhausted'
    while pages < max_pages:
        params = dict(condition=condition, limit=1000, taker_only='true' if taker_only else 'false', start=start, end=end)
        if cursor:
            params['cursor'] = cursor
        body, _ = net.get(DATA + '/v2/trades', params, pause=.12)
        if '_http_error' in body:
            raise Refused(f"v2 trades {condition}: HTTP {body['_http_error']}")
        rows = body.get('data') or []
        pages += 1
        for r in rows:
            t = r['timestamp']
            oldest, newest = t if oldest is None else min(oldest, t), t if newest is None else max(newest, t)
            if start <= t <= end:
                yield r
        cursor = (body.get('pagination') or {}).get('next_cursor')
        if rows and min(r['timestamp'] for r in rows) < start:
            stop = 'reached window start'
            break
        if not cursor:
            break
    else:
        stop = f'page cap {max_pages}: older trades not read'
    yield dict(_coverage=dict(condition=condition, start=start, end=end, pages=pages, oldest=oldest, newest=newest, stop=stop, taker_only=taker_only))
