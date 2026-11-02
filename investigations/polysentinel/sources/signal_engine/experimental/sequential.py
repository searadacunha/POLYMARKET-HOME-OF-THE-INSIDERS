"""Sequential change detection on irregular, heavy-tailed trade streams: a CUSUM on causal ranks.

Each value becomes a normal score of its rank among the stream's own past, so no distribution is assumed
and one huge trade adds a bounded amount to the statistic. Ranking a short history against other wallets
was tried and dropped: on shuffled development rows nearly all its alarms were steady whales, not changes.

A stream below its minimum history gets no statistic and is counted as unscored, not as quiet. A CUSUM
needs a sequence, so a single first bet from a new wallet is out of its reach: the engine's comparators
and the quantile baseline keep that case. An alarm says a stream changed, and nothing about why.
"""
import bisect
import math
from collections import defaultdict, deque
from statistics import NormalDist

DEFAULTS = dict(k=0.5, h=8.0, half_life_s=86400, own_minimum=8, own_window=200, population_minimum=100)
_normal = NormalDist()


class Reference:
    """Past values, sorted. Ties take their mid-rank, because round amounts are common."""

    def __init__(self, values=(), window=None):
        self.window = window
        self.order = deque(values, window)
        self.sorted = sorted(self.order)

    def __len__(self):
        return len(self.sorted)

    def score(self, x):
        rank = (bisect.bisect_left(self.sorted, x) + bisect.bisect_right(self.sorted, x)) / 2
        return _normal.inv_cdf((rank + 0.5) / (len(self.sorted) + 1))

    def add(self, x):
        if self.window and len(self.order) == self.window:
            self.sorted.pop(bisect.bisect_left(self.sorted, self.order[0]))
        self.order.append(x)
        bisect.insort(self.sorted, x)


class StreamCusum:
    """One upward CUSUM with time decay. One alarm per episode: a rupture does not alert twice."""

    def __init__(self, params=DEFAULTS):
        self.p = params
        self.own = Reference(window=params['own_window'])
        self.s, self.last_ts, self.active, self.since = 0.0, None, False, None
        self.unscored = 0

    def update(self, ts, x):
        alarm = None
        if len(self.own) < self.p['own_minimum']:
            self.unscored += 1
        else:
            if self.last_ts is not None:
                self.s *= 0.5 ** (max(0, ts - self.last_ts) / self.p['half_life_s'])
            before = self.s
            self.s = max(0.0, self.s + self.own.score(x) - self.p['k'])
            if before == 0.0 or self.since is None:
                self.since = ts
            if self.s >= self.p['h'] and not self.active:
                self.active = True
                alarm = dict(ts=ts, statistic=self.s, since=self.since, history=len(self.own))
            elif self.active and self.s < self.p['h'] / 2:
                self.active = False
        self.last_ts = ts
        self.own.add(x)
        return alarm


def wallet_observations(groups, gaps=()):
    """Stream values from one wallet's fill groups, in time order. A collection gap is not inactivity."""
    last_buy = None
    for g in groups:
        ts = g['ts']
        yield 'net', ts, g['nominal'] if g['is_buy'] else -g['nominal']
        if not g['is_buy']:
            continue
        yield 'size', ts, g['nominal']
        if last_buy is not None and not any(a <= ts and b >= last_buy for a, b in gaps):
            yield 'rate', ts, -math.log1p(max(0, ts - last_buy))
        last_buy = ts


def scan_wallet(groups, params=DEFAULTS, gaps=(), streams=('size', 'rate', 'net')):
    """Alarms for one wallet. Nothing later than a value can reach its score."""
    state = {s: StreamCusum(params) for s in streams}
    alarms = []
    for stream, ts, x in wallet_observations(groups, gaps):
        if stream in state:
            alarm = state[stream].update(ts, x)
            if alarm:
                alarms.append(dict(alarm, stream=stream))
    return alarms


def event_hours(rows, minimum_rows=20, max_hours=24 * 21):
    """Distinct buying wallets per hour, for one event's rows; silent hours count as zero within its span."""
    by_event = defaultdict(lambda: defaultdict(set))
    for r in rows:
        if r['is_buy']:
            by_event[r['event_key']][r['ts'] // 3600].add(r['wallet'])
    for event, hours in by_event.items():
        if sum(len(w) for w in hours.values()) < minimum_rows:
            continue
        first, last = min(hours), max(hours)
        for hour in range(max(first, last - max_hours), last + 1):
            yield event, hour * 3600 + 3599, len(hours.get(hour, ()))


def quantile_rule(groups, population, tail=0.001):
    """Baseline: a buy beyond a fixed quantile of the reference. Memoryless, no history needed."""
    if len(population) < DEFAULTS['population_minimum']:
        return []
    cut = population.sorted[min(len(population) - 1, int(len(population) * (1 - tail)))]
    return [dict(ts=g['ts']) for g in groups if g['is_buy'] and g['nominal'] > cut]


def robust_rule(groups, minimum=8, ratio=5.0, z=5.0):
    """Baseline: the wallet's own median and MAD on log amounts, plus the engine's size-ratio floor."""
    logs, alarms = Reference(), []
    for g in groups:
        if not g['is_buy'] or g['nominal'] <= 0:
            continue
        x = math.log(g['nominal'])
        if len(logs) >= minimum:
            median = logs.sorted[len(logs) // 2]
            mad = sorted(abs(v - median) for v in logs.sorted)[len(logs) // 2]
            if x - median >= math.log(ratio) and (x - median) >= z * 1.4826 * max(mad, 0.05):
                alarms.append(dict(ts=g['ts']))
        logs.add(x)
    return alarms
