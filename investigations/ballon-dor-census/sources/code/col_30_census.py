"""Tape of the whole Ballon d'Or 2026 family, both sides of each fill. Population for the controls: selected on having traded, not on having won.

Data API v2 event shape ignores start/end, so the walk runs newest first and stops at CUTOFF on purpose. The stop is written per event.
Streams to disk: one page in memory at a time.
"""
import csv
import gzip
import json
import time
import net

CUTOFF = 1785542400  # 2026-08-01 00:00 UTC: two months of baseline before the first alleged account
OUT = net.ROOT / 'derived/census_trades.jsonl.gz'
SUMMARY = net.ROOT / 'derived/census_summary.json'


def main():
    with open(net.ROOT / 'derived/markets.csv') as f:
        markets = list(csv.DictReader(f))
    events = sorted({m['event_id'] for m in markets if '2027' not in m['event_slug']}, key=int)
    summary = {}
    done = json.loads(SUMMARY.read_text()) if SUMMARY.exists() else {}
    mode = 'at' if done else 'wt'
    with gzip.open(OUT, mode, compresslevel=6) as out:
        for eid in events:
            if eid in done:
                summary[eid] = done[eid]
                continue
            cursor, rows, pages, oldest, newest, stop_reason = None, 0, 0, None, None, 'exhausted'
            while True:
                p = dict(event_id=eid, limit=1000, taker_only='false')
                if cursor:
                    p['cursor'] = cursor
                d = net.get('https://data-api.polymarket.com/v2/trades', p)
                pages += 1
                page = d.get('data') or []
                stop = False
                for r in page:
                    if r['timestamp'] < CUTOFF:
                        stop = True
                        stop_reason = 'reached cutoff'
                        continue
                    out.write(json.dumps(dict(ts=r['timestamp'], w=r['proxy_wallet'], side=r['side'], token=r['token_id'], cond=r['condition_id'], size=r['size'], price=r['price'],
                                              tx=r['transaction_hash'], eid=eid, name=r.get('name'), pseud=r.get('pseudonym'), outcome=r.get('outcome'), oi=r.get('outcome_index')), separators=(',', ':')) + '\n')
                    rows += 1
                    newest = max(newest or 0, r['timestamp'])
                    oldest = r['timestamp'] if oldest is None else min(oldest, r['timestamp'])
                cursor = (d.get('pagination') or {}).get('next_cursor')
                if stop or not cursor:
                    break
                if pages % 25 == 0:
                    print(eid, 'pages', pages, 'rows', rows, 'oldest', time.strftime('%Y-%m-%d', time.gmtime(oldest or 0)), flush=True)
            summary[eid] = dict(pages=pages, rows=rows, oldest=oldest, newest=newest, stop=stop_reason)
            done[eid] = summary[eid]
            out.flush()
            SUMMARY.write_text(json.dumps(done, indent=0))
            print('DONE', eid, summary[eid], flush=True)
    print('TOTAL rows', sum(s['rows'] for s in summary.values()), 'calls', net.Stats.calls)


if __name__ == '__main__':
    main()
