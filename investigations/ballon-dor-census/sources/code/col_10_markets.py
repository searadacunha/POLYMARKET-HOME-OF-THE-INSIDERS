"""Catalog: every event found by public-search for the Ballon d'Or 2026, with markets, condition ids, tokens, resolution. Writes derived/markets.csv."""
import csv
import json
from pathlib import Path
import net

OUT = net.ROOT / 'derived/markets.csv'
QUERIES = ["ballon d'or 2026", 'ballon dor 2026', "ballon d'or", "women's ballon d'or 2026", 'ballon d or top 10 2026', "ballon d'or attend ceremony"]


def main():
    events = {}
    for q in QUERIES:
        page = 1
        while True:
            d = net.get('https://gamma-api.polymarket.com/public-search', dict(q=q, limit_per_type=50, events_status='all', keep_closed_markets=1, page=page))
            for e in d.get('events') or []:
                text = (e.get('title', '') + e.get('slug', '')).lower()
                if ('ballon' in text) and ('2026' in text or '2026' in (e.get('endDate') or '') or '2026' in (e.get('startDate') or '') or '2027' in (e.get('endDate') or '')):
                    events[str(e['id'])] = e
            if not (d.get('pagination') or {}).get('hasMore') or page >= 6:
                break
            page += 1
    rows = []
    for eid in sorted(events, key=int):
        full = net.get('https://gamma-api.polymarket.com/events/' + eid)  # search answers can be partial
        for m in full.get('markets') or []:
            tokens = json.loads(m['clobTokenIds']) if m.get('clobTokenIds') else []
            outs = json.loads(m['outcomes']) if m.get('outcomes') else []
            prices = json.loads(m['outcomePrices']) if m.get('outcomePrices') else []
            rows.append(dict(event_id=eid, event_slug=full.get('slug'), event_title=full.get('title'), market_id=m.get('id'), condition_id=m.get('conditionId'),
                             question=m.get('question'), group_item=m.get('groupItemTitle'), outcomes='|'.join(outs), tokens='|'.join(tokens), final_prices='|'.join(prices),
                             closed=m.get('closed'), uma_status=m.get('umaResolutionStatus'), closed_time=m.get('closedTime'), start=m.get('startDate'), created=m.get('createdAt'),
                             volume=m.get('volumeNum') or m.get('volume'), fee_type=m.get('feeType'), neg_risk=m.get('negRisk')))
    OUT.parent.mkdir(exist_ok=True)
    with open(OUT, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print('events', len(events), 'markets', len(rows))
    for eid in sorted(events, key=int):
        e = events[eid]
        n = sum(1 for r in rows if r['event_id'] == eid)
        print(eid, e.get('slug')[:60], 'markets', n, 'vol', round(float(e.get('volume') or 0)), 'start', e.get('startDate'))


if __name__ == '__main__':
    main()
