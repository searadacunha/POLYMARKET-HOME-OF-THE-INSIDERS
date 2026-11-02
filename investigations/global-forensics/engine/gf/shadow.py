"""Shadow engine: components of an unusual entry, each detected apart, from what was observed by the decision time and nothing later.

Reads the signal engine's state database read-only and changes nothing in PolySentinel: no write to its files, no shared lock, no alert to anyone. An alert is a
reason to look. It carries what was visible, what is missing and what else explains it, and its hash chains to the previous one. The function `evaluate` receives
only rows with observed_at at or before its clock, so outcome, later prices and later trades cannot enter. No wallet is called an insider, and this module has no
access to outcomes: `win`, `resolved` and `outcome_prices` appear nowhere in it, and a test enforces that.
"""
import argparse
import hashlib
import json
import sqlite3
import time
from collections import defaultdict, deque
from pathlib import Path

WINDOWS = (5, 30, 90, 300, 900, 3600)
CONFIG = dict(version='shadow-1', price_max=0.35, min_wallets=3, min_usd=100.0, cooldown_s=21600, concentrated_share=0.8, cv_similar=0.15, big_entry_usd=5000.0, keep_s=3700, gap_alert_s=600)
ALTERNATIVES = ('A public report or a visible price move triggered several traders at once.', 'One shared signal channel, or copy-trading bots following one wallet.', 'A market maker or arbitrage bot working several wallets.', 'Independent traders reaching the same view, or chance on a busy market.')
MISSING_ALWAYS = ('Maker fills are not read: a resting order has no decision time.', 'The collector keeps a size filter and a rotating sample: smaller or unsampled entries are invisible.', 'Funding was not read: it needs network reads and a budget.', 'Identity, access to information and intent: public data cannot say.')


class Engine:
    """Time-ordered rows go in, alerts come out. State holds no row older than keep_s beyond first-seen per market."""

    def __init__(self, config=CONFIG, previous_hash='0' * 64):
        self.config = config
        self.recent = defaultdict(deque)
        self.seen_in_market = set()
        self.first_seen = {}
        self.last_trigger = {}
        self.pair_markets = defaultdict(set)
        self.previous_hash = previous_hash
        self.triggers_by_day = defaultdict(int)
        self.rows_read = 0
        self.last_observed = None
        self.gaps = []

    def _alert(self, row, window, members, now):
        wallets = sorted({m['wallet'] for m in members})
        usd = [m['usd'] for m in members]
        mean = sum(usd) / len(usd)
        cv = (sum((u - mean) ** 2 for u in usd) / len(usd)) ** .5 / mean if mean else 0
        components = dict(synchronised_entrants=dict(window_s=window, wallets=len(wallets)), new_to_universe=sum(1 for w in wallets if row['ts'] - self.first_seen[w] <= 7 * 86400), similar_sizes=cv <= self.config['cv_similar'], total_usd=round(sum(usd), 2), largest_share=round(max(usd) / sum(usd), 4), mean_price=round(sum(m['price'] for m in members) / len(members), 5))
        repeat = sorted({p for a in wallets for b in wallets if a < b for p in (self.pair_markets.get((a, b)) or ()) if p != row['condition_id']})
        components['same_pairs_on_other_markets'] = repeat[:20]
        day = int(row['ts'] // 86400)
        record = dict(schema=self.config['version'], observed_at=now, first_visible_row_ts=min(m['ts'] for m in members), detection_latency_s=round(now - max(m['ts'] for m in members), 2), market=row.get('condition_id'), event=row.get('event_key'), token=row['token_id'], outcome_label=row.get('outcome'), wallets=wallets, trades=[dict(wallet=m['wallet'], tx=m['tx'], ts=m['ts'], observed_at=m['observed_at'], usd=round(m['usd'], 2), price=m['price']) for m in members], components=components, comparators=dict(triggers_today_all_tokens=self.triggers_by_day[day], note='Rate of this same trigger today over everything observed; no comparison with outcomes is possible here.'), proven_financial_links=[], missing=list(MISSING_ALWAYS) + ([f"Collection gap of {self.gaps[-1]['seconds']:.0f} s before this alert."] if self.gaps and now - self.gaps[-1]['at'] < 3600 else []), alternatives=list(ALTERNATIVES), meaning='A timing pattern. Not a finding of coordination, nor of insider trading.', previous_hash=self.previous_hash)
        record['decision_hash'] = hashlib.sha256(json.dumps(record, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        self.previous_hash = record['decision_hash']
        return record

    def feed(self, row, now):
        """One row, whose observed_at must be at or before `now`. Raises rather than read the future."""
        if row['observed_at'] > now:
            raise ValueError('row not yet observed at this clock')
        self.rows_read += 1
        if self.last_observed is not None and row['observed_at'] - self.last_observed > self.config['gap_alert_s']:
            self.gaps.append(dict(at=row['observed_at'], seconds=row['observed_at'] - self.last_observed))
        self.last_observed = row['observed_at']
        wallet, market = row['wallet'], row['condition_id']
        self.first_seen.setdefault(wallet, row['ts'])
        new = (wallet, market) not in self.seen_in_market
        self.seen_in_market.add((wallet, market))
        usd = row['nominal']
        if not (new and row['is_buy'] and row['price'] <= self.config['price_max'] and usd >= self.config['min_usd']):
            return []
        entry = dict(wallet=wallet, ts=row['ts'], observed_at=row['observed_at'], usd=usd, price=row['price'], tx=row['tx'])
        token = row['token_id']
        recent = self.recent[token]
        recent.append(entry)
        while recent and recent[0]['ts'] <= row['ts'] - self.config['keep_s']:
            recent.popleft()
        alerts = []
        for window in WINDOWS:
            members = [m for m in recent if m['ts'] > row['ts'] - window]
            if len({m['wallet'] for m in members}) < self.config['min_wallets']:
                continue
            # one cooldown per token, across windows: a wider window would restate the same entrants
            if row['ts'] - self.last_trigger.get(token, -10 ** 12) < self.config['cooldown_s']:
                break
            self.last_trigger[token] = row['ts']
            self.triggers_by_day[int(row['ts'] // 86400)] += 1
            alerts.append(self._alert(row, window, members, now))
            names = sorted({m['wallet'] for m in members})
            for i, a in enumerate(names):
                for b in names[i + 1:]:
                    self.pair_markets[(a, b)].add(market)
            break
        return alerts


def verify_chain(records, start='0' * 64):
    """Every alert's hash and link. Returns the first broken index, or None."""
    previous = start
    for i, r in enumerate(records):
        body = {k: v for k, v in r.items() if k != 'decision_hash'}
        if r['previous_hash'] != previous or hashlib.sha256(json.dumps(body, sort_keys=True, separators=(',', ':')).encode()).hexdigest() != r['decision_hash']:
            return i
        previous = r['decision_hash']
    return None


def read_rows(path, since=None):
    """Read-only, ordered by observation. mode=ro cannot create or change anything in the collector's state."""
    cx = sqlite3.connect(f'file:{path}?mode=ro', uri=True, timeout=30)
    cx.row_factory = sqlite3.Row
    query = 'SELECT wallet, ts, observed_at, event_key, market_id, condition_id, token_id, is_buy, size, price, nominal, tx, outcome FROM trades' + (' WHERE observed_at>?' if since is not None else '') + ' ORDER BY observed_at, ts'
    return cx, cx.execute(query, (since,) if since is not None else ())


def replay(path, out, step_s=300):
    """Clock moves by observation time. Reports the alert rate, latency and collection gaps. No precision or recall: there is no ground truth."""
    engine = Engine()
    cx, cursor = read_rows(path)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    count, latencies, first, last = 0, [], None, None
    tmp = out / 'alerts.tmp'
    with tmp.open('w') as f:
        for row in cursor:
            r = dict(row)
            first = first if first is not None else r['observed_at']
            last = r['observed_at']
            for alert in engine.feed(r, r['observed_at']):
                f.write(json.dumps(alert, sort_keys=True) + '\n')
                count += 1
                latencies.append(alert['detection_latency_s'])
    cx.close()
    tmp.replace(out / 'alerts.jsonl')
    latencies.sort()
    days = (last - first) / 86400 if first is not None and last > first else None
    status = dict(rows=engine.rows_read, alerts=count, span_days=round(days, 2) if days else None, alerts_per_day=round(count / days, 2) if days else None, latency_median_s=latencies[len(latencies) // 2] if latencies else None, latency_p90_s=latencies[int(.9 * len(latencies))] if latencies else None, collection_gaps=len(engine.gaps), largest_gap_s=max((g['seconds'] for g in engine.gaps), default=0), meaning='Rates of a timing pattern on what the collector kept. No accuracy can be stated: no ground truth exists.', config=CONFIG, first_observed=first, last_observed=last, last_hash=engine.previous_hash)
    (out / 'status.json').write_text(json.dumps(status, indent=1))
    return status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', default=str(Path.home() / '.local/state/polysentinel-signal-engine/state.sqlite3'))
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    print(json.dumps(replay(args.db, args.out), indent=1))


if __name__ == '__main__':
    main()
