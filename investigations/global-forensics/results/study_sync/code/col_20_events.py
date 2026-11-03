"""Event of each market of the universe, read once from Gamma: the archive never kept it, and it is the cluster of every inference. About 110 metadata requests. Raises on a refused answer, and counts what comes back empty."""
import json
import os
import time
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

ETUDE = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ARCHIVE = Path(os.environ.get('P8_DIR', Path.home() / 'Documents/Crypto/enquete_maduro_iran/donnees/brut_p8_p9/p8'))
URL = 'https://gamma-api.polymarket.com/markets'


def get(params):
    url = URL + '?' + urllib.parse.urlencode(params, doseq=True)
    for attempt in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'phi-global-forensics/0.1 read-only', 'Accept': 'application/json'}), timeout=60) as r:
                return json.loads(r.read())
        except Exception:  # retried, and the last failure raises below: never an empty answer
            time.sleep(3 + attempt * 5)
    raise RuntimeError('Gamma refused: ' + url[:200])


def main():
    universe = json.loads((ARCHIVE / 'universe.json').read_text())
    ids = [m['conditionId'] for m in universe]
    found, counts = {}, Counter(requested=len(ids))
    for i in range(0, len(ids), 20):
        chunk = ids[i:i + 20]
        rows = get([('condition_ids', c) for c in chunk] + [('closed', 'true'), ('limit', 100)])
        counts['calls'] += 1
        for m in rows:
            events = m.get('events') or []
            if m.get('conditionId') in chunk and events:
                found[m['conditionId']] = dict(event_id=str(events[0].get('id')), event_slug=events[0].get('slug'), series=(events[0].get('seriesSlug') or None))
        time.sleep(.2)
    counts['returned_with_event'] = len(found)
    counts['missing'] = len(set(ids) - set(found))
    (ETUDE / 'derived').mkdir(exist_ok=True)
    (ETUDE / 'derived/events.json').write_text(json.dumps(dict(read_at=int(time.time()), counts=counts, events=found), indent=0))
    print(dict(counts), 'distinct events', len({v['event_id'] for v in found.values()}))


if __name__ == '__main__':
    main()
