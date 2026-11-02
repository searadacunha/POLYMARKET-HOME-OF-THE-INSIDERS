"""Exact wallet decomposition of the vendored detector with empty metadata.

The only cross-wallet rule in this scope is 90-second transaction synchrony.
All selected rows of every included wallet are retained, including old fills.
"""
from bisect import bisect_left, bisect_right
from collections import defaultdict


def sync_key(group):
    return str(group['event_id']), str(group['market_id']), group['token_id']


class WalletCache:
    def __init__(self, module):
        self.module = module
        self.rows = {}
        self.groups = {}
        self.cases = {}
        self.previous_time = None
        self.kernel_calls = 0
        self.kernel_input_rows = 0

    def evaluate(self, trades, *, now, config, wallet_history, diagnostics):
        rows = defaultdict(list)
        for row in trades:
            rows[row['wallet']].append(row)
        changed = {wallet for wallet in self.rows.keys() | rows.keys()
                   if [r['id'] for r in self.rows.get(wallet, [])] != [r['id'] for r in rows.get(wallet, [])]}
        old_groups = {wallet: self.groups.get(wallet, []) for wallet in changed}
        for wallet in changed:
            if wallet in rows:
                self.groups[wallet] = self.module.group_fills(rows[wallet], now=now)
            else:
                self.groups.pop(wallet, None)
                self.cases.pop(wallet, None)
        window = float(config.get('signal_window_seconds', 86400))
        cutoff = now - window
        affected = set(changed)
        if self.previous_time is not None:
            previous_cutoff = self.previous_time - window
            for wallet, groups in self.groups.items():
                if any(previous_cutoff <= group['timestamp'] < cutoff for group in groups):
                    affected.add(wallet)
                    old_groups.setdefault(wallet, groups)
        threshold = float(config.get('large_nominal', 1000)) / 4
        index = defaultdict(list)
        for groups in self.groups.values():
            for group in groups:
                if group['side'] == 'BUY' and group['nominal'] >= threshold and group['timestamp'] >= cutoff:
                    index[sync_key(group)].append((group['timestamp'], group['id'], group['wallet']))
        for values in index.values():
            values.sort()

        def neighbors(groups):
            found = set()
            for group in groups:
                if group['side'] != 'BUY' or group['nominal'] < threshold:
                    continue
                values = index.get(sync_key(group), [])
                lo = bisect_left(values, (group['timestamp'] - 90,))
                hi = bisect_right(values, (group['timestamp'] + 90, '\uffff', '\uffff'))
                found.update(wallet for _, _, wallet in values[lo:hi])
            return found

        # Old groups are essential when a fill group disappears, shrinks or moves in time.
        for wallet in tuple(affected):
            affected.update(neighbors(old_groups.get(wallet, []) + self.groups.get(wallet, [])))
        targets = affected & rows.keys()
        included = set(targets)
        for wallet in targets:
            included.update(neighbors(g for g in self.groups[wallet] if g['timestamp'] >= cutoff))
        if targets:
            subset = [row for row in trades if row['wallet'] in included]
            fresh = self.module.evaluate(subset, [], [], now=now, config=config, wallet_history=wallet_history)
            self.kernel_calls += 1
            self.kernel_input_rows += len(subset)
            for wallet in targets:
                self.cases[wallet] = []
            for case in fresh:
                if case['wallet'] in targets:
                    self.cases[case['wallet']].append(case)
        self.rows = dict(rows)
        self.previous_time = now
        cases = [case for values in self.cases.values() for case in values]
        for case in cases:
            case['calculated_at'] = now
            for signal in case['signals']:
                if 'window_start' in signal['reference']:
                    signal['reference'].update(window_start=cutoff, window_end=now)
        pairs = {(group['wallet'], str(group['event_id'])) for groups in self.groups.values() for group in groups}
        recent_pairs = {(group['wallet'], str(group['event_id'])) for groups in self.groups.values() for group in groups
                        if group['side'] == 'BUY' and group['timestamp'] >= cutoff}
        emitted_pairs = {(case['wallet'], case['event_id']) for case in cases}
        diagnostics.update(input_trade_rows=len(trades), grouped_fills=sum(map(len, self.groups.values())),
                           wallets=len(rows), events=len({event for _, event in pairs}),
                           wallet_event_pairs=len(pairs), examined_recent_buy_pairs=len(recent_pairs),
                           without_signal=len(recent_pairs - emitted_pairs), emitted_cases=len(cases),
                           priority_cases=sum(bool(case['priority']) for case in cases),
                           denominator='Wallet-event pairs with at least one BUY in the configured recent window; collected sample only.')
        return sorted(cases, key=lambda case: (-case['score'], case['id']))
