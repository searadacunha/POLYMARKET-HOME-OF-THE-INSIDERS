"""Empirical comparison groups, built only from values stored before the decision being scored.

A wallet is compared with others in the same stratum: market type, price zone, wallet maturity,
position size class, liquidity class, time to resolution. A sparse stratum falls back to a coarser
one and the output says so; a tail is never computed on too few values.
"""
import math

STRUCTURE_FAMILY = {'continuous_price': 'continuous', 'natural_phenomenon': 'continuous', 'competitive_outcome': 'competitive', 'competitive_micro_event': 'competitive', 'broad_public': 'public'}


def price_zone(price):
    return 'p<.2' if price < .2 else 'p<.5' if price < .5 else 'p<.8' if price < .8 else 'p>=.8'


def time_to_end_zone(end_at, now):
    if end_at is None:
        return 'end?'
    left = end_at - now
    return 'end<=0' if left <= 0 else 'end<3d' if left < 3 * 86400 else 'end<30d' if left < 30 * 86400 else 'end>=30d'


def wallet_maturity(observed_age_s):
    return 'wallet<3d' if observed_age_s < 3 * 86400 else 'wallet<14d' if observed_age_s < 14 * 86400 else 'wallet>=14d'


def liquidity_zone(liquidity):
    return 'liq?' if not liquidity or liquidity <= 0 else 'liq10^%d' % min(7, int(math.log10(liquidity)))


def strata(structure, price, end_at, now, observed_age_s, liquidity):
    """Fine to coarse. Size is what these comparators measure, so it stays out of the stratum."""
    family = STRUCTURE_FAMILY.get(structure, 'discrete')
    return ['|'.join((family, price_zone(price), time_to_end_zone(end_at, now), wallet_maturity(observed_age_s), liquidity_zone(liquidity))),
            '|'.join((family, price_zone(price), time_to_end_zone(end_at, now))),
            family + '|*']


class Comparators:
    def __init__(self, store, minimum, tail_threshold):
        self.store, self.minimum, self.threshold = store, minimum, tail_threshold
        self._sizes = {}

    def begin_cycle(self):
        self._sizes = {}

    def _size(self, stratum, metric):
        key = stratum, metric
        if key not in self._sizes:
            self._sizes[key] = self.store.cx.execute('SELECT COUNT(*) FROM comparators WHERE stratum=? AND metric=?', key).fetchone()[0]
        return self._sizes[key]

    def tail(self, keys, metric, value):
        """Upper tail with add-one smoothing. The count stops once a value is clearly not extreme."""
        if value is None:
            return dict(tail=None, n=0, stratum=None, status='NOT_APPLICABLE')
        last = 0
        for level, stratum in enumerate(keys):
            n = last = self._size(stratum, metric)
            if n >= self.minimum:
                cap = max(64, int(n * 2 * self.threshold) + 1)
                k = self.store.cx.execute('SELECT COUNT(*) FROM (SELECT 1 FROM comparators WHERE stratum=? AND metric=? AND value>=? LIMIT ?)', (stratum, metric, value, cap)).fetchone()[0]
                return dict(tail=(k + 1) / (n + 1), n=n, stratum=stratum, fallback_level=level, at_least=k >= cap, status='OK')
        return dict(tail=None, n=last, stratum=None, status='COMPARATOR_INSUFFICIENT')

    def remember(self, keys, metric, unit, now, value):
        if value is None:
            return
        for stratum in keys:
            self.store.cx.execute('INSERT OR REPLACE INTO comparators VALUES(?,?,?,?,?)', (stratum, metric, unit, int(now // 86400), value))
