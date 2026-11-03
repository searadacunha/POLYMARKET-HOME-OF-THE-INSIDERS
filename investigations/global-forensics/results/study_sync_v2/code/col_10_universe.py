"""Universe of the holdout, from Gamma, without outcomes: `outcomePrices` is not written here. Usage: col_10_universe.py <end_min> <end_max> <out.json>.

Gamma stops answering past an offset of about 2,000, so the range is read one UTC day at a time, and a day that reaches the cap stops the run. A refusal raises: nothing is kept as an empty day.
Selection is on the scheduled `endDate`, which Gamma leaves in place when a market closes early (checked on the first study's universe: 799 of 2,097 closed over a day before it). So a market due later never enters because it resolved early. end_max must be at least 30 days old, so that markets due in range have had time to close. Those still open are counted, and they leave.
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ETUDE = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
URL = 'https://gamma-api.polymarket.com/markets'
KEEP = ('conditionId', 'slug', 'question', 'startDate', 'endDate', 'closedTime', 'negRisk', 'negRiskMarketID', 'clobTokenIds', 'volumeNum', 'createdAt', 'groupItemTitle')
MIN_LIFETIME_VOLUME = 20_000  # under the point-in-time floor of $25,000, with room for Gamma's volume differing from the taker sum
CLOSE_MARGIN_DAYS = 30  # 95% of the first study's markets closed within 18 days of endDate
OUT_OF_SCOPE = re.compile(r'(^|-)(nba|nfl|mlb|nhl|epl|ucl|uel|cs2|lol|dota|atp|wta|ufc|f1|ncaa|cbb|cfb|mls|ipl|bundesliga|la-liga|serie-a|ligue-1|valorant|boxing|golf|tennis|soccer|bitcoin|btc|ethereum|eth|solana|sol|xrp|doge|up-or-down|tweets?|elon-musk-of-tweets|temperature|weather|highest-temperature|hurricane)(-|$)')
OFFSET_CAP = 1900


def get(params):
    url = URL + '?' + urllib.parse.urlencode(params)
    last = None
    for attempt in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'phi-global-forensics/0.1 read-only', 'Accept': 'application/json'}), timeout=60) as r:
                body = json.loads(r.read())
            if not isinstance(body, list):
                raise ValueError('not a list')
            return body
        except Exception as exc:  # retried, and the last failure raises: never an empty answer
            last = exc
            time.sleep(3 + attempt * 5)
    raise RuntimeError(f'Gamma refused {url[:160]}: {last}')


def events_of(market):
    found = market.get('events') or []
    return [e.get('slug') for e in found if e.get('slug')]


def main(end_min, end_max, out):
    day = datetime.fromisoformat(end_min).replace(tzinfo=timezone.utc)
    stop = datetime.fromisoformat(end_max).replace(tzinfo=timezone.utc)
    if stop > datetime.now(timezone.utc) - timedelta(days=CLOSE_MARGIN_DAYS):
        raise SystemExit(f'end_max must be at least {CLOSE_MARGIN_DAYS} days old: a market due later must not enter because it closed early')
    kept, per_day, counts = {}, {}, dict(days=0, read=0, kept=0, out_of_scope=0, no_condition=0, no_events=0, still_open_due_in_range=0)
    while day < stop:
        offset = 0
        following = day + timedelta(days=1)
        while True:
            page = get(dict(closed='true', end_date_min=day.strftime('%Y-%m-%dT%H:%M:%SZ'), end_date_max=following.strftime('%Y-%m-%dT%H:%M:%SZ'), volume_num_min=MIN_LIFETIME_VOLUME, limit=100, offset=offset, order='id', ascending='true'))  # id is unique, so pages cannot repeat or skip on ties
            for m in page:
                counts['read'] += 1
                if not m.get('conditionId'):
                    counts['no_condition'] += 1
                elif OUT_OF_SCOPE.search(m.get('slug') or ''):
                    counts['out_of_scope'] += 1
                else:
                    row = {k: m.get(k) for k in KEEP}
                    row['event_slugs'] = events_of(m)
                    row['event_ids'] = [str(e.get('id')) for e in m.get('events') or [] if e.get('id')]
                    counts['no_events'] += not row['event_ids']
                    kept[m['conditionId'].lower()] = row
            offset += len(page)
            if len(page) < 100:
                break
            if offset >= OFFSET_CAP:
                raise RuntimeError(f'{day.date()} reaches the offset cap: narrow the slice, do not keep a partial day')
            time.sleep(.2)
        per_day[day.strftime('%Y-%m-%d')] = offset
        counts['days'] += 1
        offset = 0
        while True:
            page = get(dict(closed='false', end_date_min=day.strftime('%Y-%m-%dT%H:%M:%SZ'), end_date_max=following.strftime('%Y-%m-%dT%H:%M:%SZ'), volume_num_min=MIN_LIFETIME_VOLUME, limit=100, offset=offset, order='id', ascending='true'))
            counts['still_open_due_in_range'] += len(page)
            offset += len(page)
            if len(page) < 100 or offset >= OFFSET_CAP:
                break
        day = following
    counts['kept'] = len(kept)
    Path(out).write_text(json.dumps(dict(end_min=end_min, end_max=end_max, read_at=int(time.time()), counts=counts, read_per_day=per_day, markets=list(kept.values())), indent=0))
    print(json.dumps(counts))


if __name__ == '__main__':
    main(*sys.argv[1:])
