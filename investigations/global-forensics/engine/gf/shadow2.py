"""shadow-2: research successor of shadow-1, in isolation. shadow-1's module and outputs stay as they were; nothing here is scheduled or sends anything.

Each change answers a defect measured on the replay (results/shadow/latency_sources.json):
- 100 of 283 shadow-1 alerts group entries spread wider than the window they state, because rows arrive out of order and the window was one-sided. Here a set must fit inside the window.
- A row that arrives late is still evaluated with its neighbours in trade time: entries are kept by observation age, not by the newest trade.
- Most delay comes from the collector. Each alert says how late it was, whether one batch completed it and whether a gap preceded it, and the status counts alerts per hour actually collected.
Like shadow-1, this module has no access to outcomes, and it calls no wallet an insider.
"""
import bisect
import hashlib
import json
from pathlib import Path

from .shadow import CONFIG, WINDOWS, Engine, read_rows

CONFIG2 = dict(CONFIG, version='shadow-2', keep_observed_s=172800, live_s=600)


def tightest_set(entries, ts, window, min_wallets):
    """The set of entries inside one span of `window` seconds that contains `ts` and holds the most wallets, or None. Entries are sorted by trade time."""
    times = [e['ts'] for e in entries]
    best = None
    for start_at in range(bisect.bisect_left(times, ts - window + 1), bisect.bisect_right(times, ts)):
        end = bisect.bisect_left(times, times[start_at] + window)
        members = entries[start_at:end]
        wallets = {m['wallet'] for m in members}
        if len(wallets) >= min_wallets and (best is None or len(wallets) > best[0]):
            best = (len(wallets), members)
    return best[1] if best else None


class Engine2(Engine):
    def __init__(self, config=CONFIG2, previous_hash='0' * 64):
        super().__init__(config, previous_hash)
        self.recent = {}
        self.exposure_s = 0.0

    def feed(self, row, now):
        if row['observed_at'] > now:
            raise ValueError('row not yet observed at this clock')
        self.rows_read += 1
        gap_before = None
        if self.last_observed is not None:
            step = row['observed_at'] - self.last_observed
            if step > self.config['gap_alert_s']:
                gap_before = step
                self.gaps.append(dict(at=row['observed_at'], seconds=step))
            else:
                self.exposure_s += max(step, 0)
        self.last_observed = row['observed_at']
        wallet, market = row['wallet'], row['condition_id']
        self.first_seen[wallet] = min(self.first_seen.get(wallet, row['ts']), row['ts'])
        new = (wallet, market) not in self.seen_in_market
        self.seen_in_market.add((wallet, market))
        if not (new and row['is_buy'] and row['price'] <= self.config['price_max'] and row['nominal'] >= self.config['min_usd']):
            return []
        token = row['token_id']
        entries = self.recent.setdefault(token, [])
        entry = dict(wallet=wallet, ts=row['ts'], observed_at=row['observed_at'], usd=row['nominal'], price=row['price'], tx=row['tx'])
        bisect.insort(entries, entry, key=lambda e: e['ts'])
        entries[:] = [e for e in entries if now - e['observed_at'] <= self.config['keep_observed_s']]
        for window in WINDOWS:
            members = tightest_set(entries, row['ts'], window, self.config['min_wallets'])
            if not members:
                continue
            if abs(row['ts'] - self.last_trigger.get(token, -10 ** 12)) < self.config['cooldown_s']:
                return []
            self.last_trigger[token] = row['ts']
            self.triggers_by_day[int(row['ts'] // 86400)] += 1
            alert = self._alert(row, window, members, now)
            names = sorted({m['wallet'] for m in members})
            for i, a in enumerate(names):
                for b in names[i + 1:]:
                    self.pair_markets[(a, b)].add(market)
            return [self._timed(alert, members, now, gap_before)]
        return []

    def _timed(self, alert, members, now, gap_before):
        """Timing labels join the hash, so the chain covers them too."""
        latency = alert['detection_latency_s']
        recent_gap = next((g['seconds'] for g in reversed(self.gaps) if now - g['at'] < 3600), gap_before)
        alert['timing'] = dict(state='LIVE' if latency <= self.config['live_s'] else 'LATE', one_batch=len({int(m['observed_at']) for m in members}) == 1, gap_within_hour_s=recent_gap)
        body = {k: v for k, v in alert.items() if k != 'decision_hash'}
        alert['decision_hash'] = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        self.previous_hash = alert['decision_hash']
        return alert


def replay(path, out):
    """Same clock as shadow-1. The alert file sits in its own folder."""
    engine = Engine2()
    cx, cursor = read_rows(path)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    states, first, last, count, live, batches = {}, None, None, 0, [], 0
    tmp = out / 'alerts.tmp'
    with tmp.open('w') as f:
        for row in cursor:
            r = dict(row)
            first = r['observed_at'] if first is None else first
            last = r['observed_at']
            for alert in engine.feed(r, r['observed_at']):
                f.write(json.dumps(alert, sort_keys=True) + '\n')
                count += 1
                states[alert['timing']['state']] = states.get(alert['timing']['state'], 0) + 1
                batches += alert['timing']['one_batch']
                if alert['timing']['state'] == 'LIVE':
                    live.append(alert['detection_latency_s'])
    cx.close()
    tmp.replace(out / 'alerts.jsonl')
    live.sort()
    hours = engine.exposure_s / 3600
    status = dict(version=engine.config['version'], rows=engine.rows_read, alerts=count, by_state=states, one_batch=batches, span_days=round((last - first) / 86400, 2), collected_hours=round(hours, 1), gaps=len(engine.gaps), gap_hours=round(sum(g['seconds'] for g in engine.gaps) / 3600, 1), alerts_per_collected_hour=round(count / hours, 3) if hours else None, live_per_collected_hour=round(len(live) / hours, 3) if hours else None, live_latency_median_s=live[len(live) // 2] if live else None, live_latency_p90_s=live[int(.9 * len(live))] if live else None, last_hash=engine.previous_hash, config=engine.config, meaning='A replay of what the collector kept. Rates of a timing pattern. No precision or recall: no ground truth, and no outcome is read.')
    (out / 'status.json').write_text(json.dumps(status, indent=1))
    return status
