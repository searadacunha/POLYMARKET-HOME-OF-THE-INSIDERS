"""Full public tape of one market, makers included, sliced so a full page never truncates silently."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import net

API = 'https://data-api.polymarket.com/trades'
LIMIT = 10000


def tape(condition, start, end, taker_only='false', depth=0):
    rows = net.get(API, dict(market=condition, start=start, end=end, limit=LIMIT, takerOnly=taker_only))
    if not isinstance(rows, list):
        raise RuntimeError(f'tape {condition}: {rows}')
    if len(rows) >= LIMIT:
        if end - start < 2 or depth > 20:
            raise RuntimeError(f'full page on a tiny slice: {condition} {start} {end}')
        mid = (start + end) // 2
        return tape(condition, start, mid, taker_only, depth + 1) + tape(condition, mid + 1, end, taker_only, depth + 1)
    return rows
