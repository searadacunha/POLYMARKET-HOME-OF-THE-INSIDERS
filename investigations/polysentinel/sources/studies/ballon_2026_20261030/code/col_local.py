"""Short autocommit reads only; never backdate locally acquired information."""
import json
import sqlite3
import time
from datetime import datetime
from pathlib import Path

STUDY = Path(__file__).resolve().parents[1]
CUTOFFS = {'before_public_report': '2026-10-23T15:17:49+00:00',
           'before_ceremony': '2026-10-26T20:00:00+00:00'}


def main():
    destination = STUDY / 'data/local_availability.json'
    if destination.exists() or (STUDY / 'PROTOCOL.lock').exists():
        raise RuntimeError('Existing extraction or frozen study; do not overwrite')
    db = STUDY.parents[1] / 'data/polysentinel.sqlite3'
    cx = sqlite3.connect(db.as_uri() + '?mode=ro', uri=True, isolation_level=None)
    cx.execute('PRAGMA query_only=ON')
    cx.row_factory = sqlite3.Row
    records = {'acquired_at': time.time(), 'database': str(db), 'queries': []}
    def query(sql, params=()):
        start = time.monotonic()
        cx.set_progress_handler(lambda: int(time.monotonic() - start > 5), 1000)
        rows = [dict(r) for r in cx.execute(sql, params).fetchall()]
        records['queries'].append({'sql': sql, 'params': params, 'rows': rows,
                                   'seconds': time.monotonic() - start})
        return rows
    try:
        records['first_cycle'] = query('SELECT id,start,end,status FROM cycles ORDER BY id LIMIT 1')[0]
        if records['first_cycle']['id'] != 1:
            raise RuntimeError('The first cycle is missing; installation timing is not certified')
        records['windows'] = {}
        for label, iso in CUTOFFS.items():
            cutoff = datetime.fromisoformat(iso).timestamp()
            counts = {}
            for kind in ('trade', 'market', 'event', 'public_milestone', 'public_condition', 'alert'):
                counts[kind] = query('SELECT COUNT(*) n FROM history_refs WHERE kind=? AND observed_at<?',
                                     (kind, cutoff))[0]['n']
            records['windows'][label] = {'cutoff': cutoff, 'iso': iso, 'counts': counts}
        records['latest_completed_cycle'] = query('SELECT id,start,end,status FROM cycles WHERE end IS NOT NULL ORDER BY id DESC LIMIT 1')[0]
        records['current_trade_count'] = query('SELECT COUNT(*) n FROM trade_index')[0]['n']
        # A nonempty historical dataset needs a separate bounded extraction, not a guessed empty one.
        if any(v for w in records['windows'].values() for v in w['counts'].values()):
            raise RuntimeError('Historical rows exist; extraction of their payloads is required')
        records['historical_inputs'] = {'trades': [], 'markets': [], 'events': []}
        with destination.open('x') as stream:
            json.dump(records, stream, indent=2)
        print(json.dumps({k: records[k] for k in ('first_cycle', 'windows', 'current_trade_count')}))
    finally:
        cx.close()


if __name__ == '__main__':
    main()
