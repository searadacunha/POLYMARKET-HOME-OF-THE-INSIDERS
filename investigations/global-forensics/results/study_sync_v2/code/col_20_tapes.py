"""Taker tape of each market, one gz file per market written atomically, so a run resumes market by market. Usage: col_20_tapes.py <universe.json> <budget of requests> [--limit N].

No outcome is read. An HTTP failure raises and the market stays unread. A page cap is recorded as partial, never as complete. Counters: requested, pages, rows, errors, empty, markets_done. A market whose walk ends oddly stays unread, and an empty tape is written as empty and leaves the table.
"""
import gzip
import http.client
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ETUDE = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TAPES = ETUDE / 'data' / 'tapes'
URL = 'https://data-api.polymarket.com/v2/trades'
KEEP = ('proxy_wallet', 'side', 'token_id', 'size', 'price', 'timestamp', 'transaction_hash')
MAX_PAGES = 4000


class Spent(Exception):
    """Budget reached: stops the run, and no market is called failed for it."""


def get(params, state):
    if state['requests'] >= state['budget']:
        raise Spent('budget')
    url = URL + '?' + urllib.parse.urlencode(params)
    last = None
    for attempt in range(7):
        state['requests'] += 1
        time.sleep(.15 * (1 + 3 * attempt))
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'phi-global-forensics/0.1 read-only', 'Accept': 'application/json'}), timeout=60) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as exc:
            last = exc
            state['http_errors'] += 1
            if exc.code not in (408, 425, 429, 500, 502, 503, 504, 520, 522, 524, 529):
                break
            time.sleep(min(60, 5 * (attempt + 1)))
        except (urllib.error.URLError, TimeoutError, ValueError, OSError, http.client.HTTPException) as exc:
            last = exc
            state['net_errors'] += 1
    raise RuntimeError(f'trades refused: {str(last)[:160]}')


def read_market(market, state):
    condition = market['conditionId']
    path = TAPES / f'{condition}.jsonl.gz'
    if path.exists():
        return 'kept'
    cursor, pages, rows, stop = None, 0, 0, 'exhausted'
    tmp = path.with_suffix('.tmp')
    seen = set()
    with gzip.open(tmp, 'wt') as f:
        while True:
            params = dict(condition=condition, limit=1000, taker_only='true')
            if cursor:
                params['cursor'] = cursor
            body = get(params, state)
            if not isinstance(body, dict) or 'data' not in body or body.get('error'):
                raise RuntimeError(f'{condition}: unexpected answer {str(body)[:160]}')
            data = body['data'] or []
            page = body.get('pagination') or {}
            pages += 1
            # the walk runs newest first, so a cut loses the oldest rows, and a later row would pass for a wallet's first
            if page.get('has_more') and not page.get('next_cursor'):
                raise RuntimeError(f'{condition}: more rows announced with no cursor, page {pages}')
            if not data and page.get('next_cursor'):
                raise RuntimeError(f'{condition}: empty page with a cursor, page {pages}')
            keys = []
            for r in data:
                key = (r.get('transaction_hash'), r.get('proxy_wallet'), r.get('token_id'), r.get('size'), r.get('price'), r.get('side'))
                keys.append(key)
                if key in seen:  # only across pages: equal fills inside one page are real
                    state['repeats_across_pages'] += 1
                    continue
                f.write(json.dumps({k: r.get(k) for k in KEEP}) + '\n')
                rows += 1
            seen.update(keys)
            cursor = page.get('next_cursor')
            if not cursor:
                break
            if pages >= MAX_PAGES:
                stop = 'page cap'
                break
        if rows == 0:
            stop = 'empty'
            state['empty'] += 1
        f.write(json.dumps(dict(_coverage=dict(condition=condition, pages=pages, rows=rows, stop=stop, read_at=int(time.time())))) + '\n')
    tmp.replace(path)
    state['pages'] += pages
    state['rows'] += rows
    state['markets_done'] += 1
    return stop


def main(universe, budget, *flags):
    TAPES.mkdir(parents=True, exist_ok=True)
    limit = next((int(a) for a, b in zip(flags[1:], flags) if b == '--limit'), None)
    markets = json.loads(Path(universe).read_text())['markets']
    state = dict(budget=int(budget), requests=0, pages=0, rows=0, http_errors=0, net_errors=0, markets_done=0, kept=0, empty=0, repeats_across_pages=0, failed=[], requested=len(markets))
    try:
        for i, market in enumerate(markets):
            if limit is not None and state['markets_done'] >= limit:
                break
            try:
                state['kept'] += read_market(market, state) == 'kept'
            except RuntimeError as exc:  # one market stays unread, counted and retried next run
                state['failed'].append(dict(condition=market['conditionId'], error=str(exc)[:200]))
    except Spent:
        state['stopped'] = 'budget'
    (ETUDE / 'derived').mkdir(exist_ok=True)
    (ETUDE / 'derived' / f'collection_{int(time.time())}.json').write_text(json.dumps(state))
    print(json.dumps({k: (v if k != 'failed' else len(v)) for k, v in state.items()}))


if __name__ == '__main__':
    main(*sys.argv[1:])
