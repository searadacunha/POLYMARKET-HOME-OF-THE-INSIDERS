"""Tapes of the control families listed in study/oos_events.json, both sides of each fill, from 45 days before the last close. Finals from Gamma."""
import gzip
import json
import time
from datetime import datetime
import net

OUT = net.ROOT / 'derived/oos'


def main():
    OUT.mkdir(exist_ok=True)
    spec = json.load(open(net.ROOT / 'study/oos_events.json'))
    for e in spec['sealed'] + spec['sport']:
        path = OUT / f"{e['event_id']}.jsonl.gz"
        done = OUT / f"{e['event_id']}.finals.json"
        if done.exists():
            continue
        last = int(datetime.fromisoformat(e['last_close'].replace(' ', 'T').split('+')[0].replace('Z', '')).timestamp())
        cutoff = last - 45 * 86400
        cursor, rows, pages, stop = None, 0, 0, 'exhausted'
        tmp = path.with_suffix('.tmp')
        with gzip.open(tmp, 'wt') as out:
            while True:
                p = dict(event_id=e['event_id'], limit=1000, taker_only='false')
                if cursor:
                    p['cursor'] = cursor
                d = net.get('https://data-api.polymarket.com/v2/trades', p)
                pages += 1
                ended = False
                for r in d['data'] or []:
                    if r['timestamp'] < cutoff:
                        ended = True
                        stop = 'cutoff'
                        continue
                    out.write(json.dumps(dict(ts=r['timestamp'], w=r['proxy_wallet'], side=r['side'], token=r['token_id'], cond=r['condition_id'], size=r['size'], price=r['price'], tx=r['transaction_hash'], outcome=r.get('outcome')), separators=(',', ':')) + '\n')
                    rows += 1
                cursor = (d.get('pagination') or {}).get('next_cursor')
                if ended or not cursor or pages >= 1200:
                    if pages >= 1200 and cursor and not ended:
                        stop = 'page_cap'
                    break
        tmp.replace(path)
        full = net.get('https://gamma-api.polymarket.com/events/' + e['event_id'])
        finals = {}
        for m in full.get('markets') or []:
            if m.get('clobTokenIds') and m.get('outcomePrices'):
                for t, q in zip(json.loads(m['clobTokenIds']), json.loads(m['outcomePrices'])):
                    finals[t] = float(q)
        if not finals or not full.get('closed'):
            raise net.FetchError(f"event {e['event_id']}: closed={full.get('closed')}, {len(finals)} finals")
        (OUT / f"{e['event_id']}.summary.json").write_text(json.dumps(dict(rows=rows, pages=pages, stop=stop, cutoff=cutoff)))
        done.write_text(json.dumps(finals))
        print(e['kind'], e['event_id'], e['title'][:40], 'rows', rows, 'pages', pages, 'stop', stop, flush=True)


if __name__ == '__main__':
    main()
