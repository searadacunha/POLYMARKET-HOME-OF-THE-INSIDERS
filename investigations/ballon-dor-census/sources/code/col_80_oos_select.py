"""PROTOCOL.md section 6: out-of-sample families chosen by a fixed rule, written to study/oos_events.json BEFORE any of their trades is read.
Rule: closed event, last market closed between 2026-09-15 and 2026-11-02, volume >= 100 000 $, result revealed at once, not the Ballon d'Or. Sealed-type: awards, science, culture. Plus 3 sport events of comparable volume, no secret vote."""
import json
import time
import net

T0, T1 = '2026-09-15', '2026-11-02'
SEALED_TAGS = ('awards', 'nobel-prize', 'nobel', 'oscars', 'grammys', 'emmys', 'golden-globes', 'culture', 'science', 'literature', 'movies', 'music')
SEALED_WORDS = ('nobel', 'prize', 'award', 'golden boy', 'emmy', 'grammy', 'oscar', 'booker', 'winner of', 'of the year', 'trophy', 'kopa', 'yashin', 'cma ', 'mtv', 'bafta', 'cesar', 'goncourt')
SPORT_WORDS = (' vs. ', ' vs ')


def fetch(tag):
    out, offset = [], 0
    while True:
        d = net.get('https://gamma-api.polymarket.com/events', dict(tag_slug=tag, closed='true', end_date_min=T0, limit=100, offset=offset, order='volume', ascending='false'), accept=(400, 404, 422))
        if isinstance(d, net.Miss) or not d:
            return out
        out += d
        if len(d) < 100 or offset >= 900:
            return out
        offset += 100


def main():
    seen = {}
    for tag in SEALED_TAGS:
        rows = fetch(tag)
        print('tag', tag, len(rows), flush=True)
        for e in rows:
            seen[str(e['id'])] = e
    for q in ('nobel prize 2026', 'nobel peace prize', 'golden boy 2026', 'booker prize 2026', 'award winner october 2026', 'prize winner 2026', 'goncourt 2026'):
        d = net.get('https://gamma-api.polymarket.com/public-search', dict(q=q, limit_per_type=30, events_status='all', keep_closed_markets=1))
        for e in d.get('events') or []:
            seen.setdefault(str(e['id']), e)
    sealed = []
    for eid, e in seen.items():
        text = (e.get('title', '') + ' ' + e.get('slug', '')).lower()
        vol = float(e.get('volume') or 0)
        if 'ballon' in text or vol < 100000 or not e.get('closed'):
            continue
        if not any(w in text for w in SEALED_WORDS):
            continue
        full = net.get('https://gamma-api.polymarket.com/events/' + eid)
        closes = sorted(m.get('closedTime') or '' for m in full.get('markets') or [] if m.get('closedTime'))
        if not closes or not (T0 <= closes[-1][:10] <= T1):
            continue
        sealed.append(dict(event_id=eid, slug=e.get('slug'), title=e.get('title'), volume=round(vol), start=e.get('startDate'), last_close=closes[-1], kind='sealed'))
    sealed.sort(key=lambda x: -x['volume'])
    sport = []
    d = fetch('soccer')
    d = [e for e in d if float(e.get('volume') or 0) >= 300000 and any(w in e.get('title', '').lower() for w in SPORT_WORDS)]
    d.sort(key=lambda e: abs(float(e.get('volume') or 0) - 1_000_000))
    for e in d:
        full = net.get('https://gamma-api.polymarket.com/events/' + str(e['id']))
        closes = sorted(m.get('closedTime') or '' for m in full.get('markets') or [] if m.get('closedTime'))
        if closes and T0 <= closes[-1][:10] <= T1:
            sport.append(dict(event_id=str(e['id']), slug=e.get('slug'), title=e.get('title'), volume=round(float(e.get('volume') or 0)), start=e.get('startDate'), last_close=closes[-1], kind='sport_witness'))
        if len(sport) == 3:
            break
    out = dict(rule=__doc__, written_at=int(time.time()), sealed=sealed, sport=sport)
    p = net.ROOT / 'study/oos_events.json'
    p.write_text(json.dumps(out, indent=1))
    print('sealed', len(sealed))
    for s in sealed + sport:
        print(s['kind'], s['event_id'], s['volume'], s['last_close'][:16], s['title'][:64])


if __name__ == '__main__':
    main()
