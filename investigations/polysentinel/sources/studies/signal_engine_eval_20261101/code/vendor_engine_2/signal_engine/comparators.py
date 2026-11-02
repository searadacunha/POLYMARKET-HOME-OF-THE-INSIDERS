"""Empirical comparison groups, built only from values stored before the decision being scored.

A wallet is compared with others in the same stratum: market type, price zone, wallet maturity,
position size class, liquidity class, time to resolution. A sparse stratum falls back to a coarser
one and the output says so; a tail is never computed on too few values.
"""
import hashlib
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


METRICS = {'size_ratio': 1, 'frequency_ratio': 2, 'max_market_spend': 3, 'market_share_24h': 4, 'liquidity_fraction': 5, 'burst_nominal': 6}


class Comparators:
    """Integers for strata, metrics and units: this table has one row per pair, metric, stratum and day."""

    def __init__(self, store, minimum, tail_threshold):
        self.store, self.minimum, self.threshold = store, minimum, tail_threshold
        self._sizes = {}
        self._ids = {name: i for i, name in store.cx.execute('SELECT id, name FROM strata')}

    def begin_cycle(self):
        self._sizes = {}

    def _stratum_id(self, name):
        if name not in self._ids:
            self._ids[name] = self.store.cx.execute('INSERT INTO strata(name) VALUES(?)', (name,)).lastrowid
        return self._ids[name]

    def _size(self, stratum, metric):
        key = stratum, metric
        if key not in self._sizes:
            known = self._ids.get(stratum)
            self._sizes[key] = 0 if known is None else self.store.cx.execute('SELECT COUNT(*) FROM comparators WHERE stratum=? AND metric=?', (known, METRICS[metric])).fetchone()[0]
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
                k = self.store.cx.execute('SELECT COUNT(*) FROM (SELECT 1 FROM comparators WHERE stratum=? AND metric=? AND value>=? LIMIT ?)', (self._ids[stratum], METRICS[metric], value, cap)).fetchone()[0]
                return dict(tail=(k + 1) / (n + 1), n=n, stratum=stratum, fallback_level=level, at_least=k >= cap, status='OK')
        return dict(tail=None, n=last, stratum=None, status='COMPARATOR_INSUFFICIENT')

    def remember(self, keys, metric, unit, now, value):
        if value is None:
            return
        unit_id = int.from_bytes(hashlib.blake2b(unit.encode(), digest_size=7).digest(), 'big')
        for stratum in keys:
            self.store.cx.execute('INSERT OR REPLACE INTO comparators VALUES(?,?,?,?,?)', (self._stratum_id(stratum), METRICS[metric], unit_id, int(now // 86400), value))
