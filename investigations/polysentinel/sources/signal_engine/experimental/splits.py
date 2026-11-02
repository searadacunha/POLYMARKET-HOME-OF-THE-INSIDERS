"""Partitions that keep linked wallets, one event's markets and the future out of each other's way.

Performance measured across a contaminated split looks better than it is. True owners are unknown here,
so wallet groups are conservative unions over documented links: a group can be too large, which only
costs data. Any overlap the split cannot remove is reported, never hidden.
"""
import hashlib
from collections import defaultdict


class Groups:
    """Union-find over documented links, keeping the reason of each merge."""

    def __init__(self):
        self.parent, self.reasons = {}, defaultdict(list)

    def find(self, x):
        self.parent.setdefault(x, x)
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def link(self, a, b, reason):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[ra] = rb
            self.reasons[rb].extend(self.reasons.pop(ra, []))
        self.reasons[self.find(a)].append(reason)


def bucket(key, salt, share):
    return int(hashlib.sha256(f'{salt}|{key}'.encode()).hexdigest()[:12], 16) / 16 ** 12 < share


def temporal_group_split(rows, split_ts, embargo_s, groups=None, excluded_events=(), excluded_wallets=(), salt='20261101', dev_share=0.5):
    """dev: its wallet groups, before split_ts. test: the others, after the embargo. Their earlier rows only warm up."""
    groups = groups or Groups()
    out = dict(dev=[], test=[], burn_in=[], dropped_embargo=0, dropped_excluded=0)
    dev_events = set()
    for r in rows:
        if r['event_key'] in excluded_events or r['wallet'] in excluded_wallets:
            out['dropped_excluded'] += 1
            continue
        if bucket(groups.find(r['wallet']), salt, dev_share):
            if r['ts'] < split_ts:
                out['dev'].append(r)
                dev_events.add(r['event_key'])
            continue
        if r['ts'] >= split_ts + embargo_s:
            out['test'].append(r)
        elif r['ts'] < split_ts:
            out['burn_in'].append(r)
        else:
            out['dropped_embargo'] += 1
    out['events_in_dev'] = dev_events
    out['test_rows_on_unseen_events'] = sum(r['event_key'] not in dev_events for r in out['test'])
    return out


def assert_no_leak(split, split_ts, embargo_s, groups=None, excluded_events=(), excluded_wallets=()):
    """Raises on a broken partition. Run on the result, so a bug in the splitter cannot pass unseen."""
    groups = groups or Groups()
    dev = {groups.find(r['wallet']) for r in split['dev']}
    test = {groups.find(r['wallet']) for r in split['test']} | {groups.find(r['wallet']) for r in split['burn_in']}
    if dev & test:
        raise AssertionError(f'{len(dev & test)} wallet groups on both sides')
    if split['dev'] and max(r['ts'] for r in split['dev']) >= split_ts:
        raise AssertionError('Development row after the split')
    if split['test'] and min(r['ts'] for r in split['test']) < split_ts + embargo_s:
        raise AssertionError('Test row inside the embargo')
    for side in ('dev', 'test', 'burn_in'):
        for r in split[side]:
            if r['event_key'] in excluded_events or r['wallet'] in excluded_wallets:
                raise AssertionError('Excluded case inside a partition')
            if r['observed_at'] < r['ts']:
                raise AssertionError('Row observed before it happened')


def available_at_decision(metadata_observed_at, decision_ts):
    """A catalogue value read after the decision is not a contemporary fact; say which it is."""
    if metadata_observed_at is None:
        return 'UNDATED'
    return 'CONTEMPORARY' if metadata_observed_at <= decision_ts else 'ACTUALIZED_AFTER_DECISION'
