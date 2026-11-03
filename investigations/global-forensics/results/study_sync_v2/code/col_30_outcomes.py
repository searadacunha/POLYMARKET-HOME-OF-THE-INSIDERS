"""Outcomes, read once, after the table is frozen. Usage: col_30_outcomes.py <universe.json> <out.json>. Keyed by token id. Only markets whose two outcome prices are exactly 1 and 0 enter, both tokens together. Anything else is counted and leaves. A refusal raises."""
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

URL = 'https://gamma-api.polymarket.com/markets'


def get(params):
    last = None
    for attempt in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(URL + '?' + urllib.parse.urlencode(params, doseq=True), headers={'User-Agent': 'phi-global-forensics/0.1 read-only', 'Accept': 'application/json'}), timeout=60) as r:
                body = json.loads(r.read())
            if isinstance(body, list):
                return body
            last = 'not a list'
        except Exception as exc:  # retried, and the last failure raises
            last = exc
        time.sleep(3 + attempt * 5)
    raise RuntimeError(f'Gamma refused: {last}')


def parse_market(m):
    prices, tokens = json.loads(m['outcomePrices']), json.loads(m['clobTokenIds'])
    if len(prices) != 2 or len(tokens) != 2 or sorted(prices, key=float) != ['0', '1']:
        return None
    return {tokens[i]: int(prices[i]) for i in range(2)}


def main(universe, out):
    wanted = [m['conditionId'] for m in json.loads(Path(universe).read_text())['markets']]
    values, counts = {}, dict(requested=len(wanted), clean=0, not_exactly_1_and_0=0, not_returned=0)
    for i in range(0, len(wanted), 20):
        batch = wanted[i:i + 20]
        found = {m['conditionId'].lower(): m for m in get([('condition_ids', c) for c in batch] + [('closed', 'true'), ('limit', 100)])}
        for c in batch:
            m = found.get(c.lower())
            if m is None:
                counts['not_returned'] += 1
                continue
            parsed = parse_market(m)
            if parsed is None:
                counts['not_exactly_1_and_0'] += 1
            else:
                counts['clean'] += 1
                values.update(parsed)
        time.sleep(.2)
    Path(out).write_text(json.dumps(dict(read_at=int(time.time()), counts=counts, values=values)))
    print(json.dumps(counts))


if __name__ == '__main__':
    main(*sys.argv[1:])
