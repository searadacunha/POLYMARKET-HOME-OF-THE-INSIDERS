"""The engine's own bounded state. It never writes to the collector's database."""
import hashlib
import json
import sqlite3
from pathlib import Path

SCHEMA = '''
CREATE TABLE IF NOT EXISTS trades(key BLOB PRIMARY KEY, wallet TEXT, ts INT, observed_at REAL, event_key TEXT, market_id TEXT, condition_id TEXT,
    token_id TEXT, is_buy INT, size REAL, price REAL, nominal REAL, tx TEXT, outcome TEXT);
CREATE INDEX IF NOT EXISTS trades_wallet ON trades(wallet, ts);
CREATE INDEX IF NOT EXISTS trades_event ON trades(event_key, ts);
CREATE INDEX IF NOT EXISTS trades_condition ON trades(condition_id, ts);
CREATE INDEX IF NOT EXISTS trades_token ON trades(token_id, ts);
CREATE TABLE IF NOT EXISTS wallets(wallet TEXT PRIMARY KEY, first_trade_ts INT, first_event_key TEXT);
CREATE TABLE IF NOT EXISTS markets(condition_id TEXT PRIMARY KEY, title TEXT, event_key TEXT, market_id TEXT, end_at REAL, closed_at REAL, rules TEXT, tags TEXT, sports INT,
    neg_risk INT, liquidity REAL, liquidity_observed_at REAL, spread REAL, group_title TEXT, cataloged INT);
CREATE TABLE IF NOT EXISTS strata(id INTEGER PRIMARY KEY, name TEXT UNIQUE);
CREATE TABLE IF NOT EXISTS comparators(stratum INT, metric INT, unit INT, day INT, value REAL, PRIMARY KEY(stratum, metric, unit, day)) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS comparators_value ON comparators(stratum, metric, value);
CREATE TABLE IF NOT EXISTS pairs(wallet TEXT, event_key TEXT, evaluated_at REAL, anomalies TEXT, record TEXT, PRIMARY KEY(wallet, event_key));
CREATE INDEX IF NOT EXISTS pairs_event ON pairs(event_key);
CREATE TABLE IF NOT EXISTS cases(event_key TEXT PRIMARY KEY, version INT, category TEXT, fingerprint TEXT, opened_at REAL, updated_at REAL, reobservations INT, priority INT);
CREATE TABLE IF NOT EXISTS kv(key TEXT PRIMARY KEY, value TEXT);
'''


class SignalStore:
    """A small page cache and file-backed temp storage keep this process's memory flat."""

    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.cx = sqlite3.connect(path, timeout=30)
        self.cx.row_factory = sqlite3.Row
        for pragma in ('journal_mode=WAL', 'synchronous=NORMAL', 'cache_size=-8000', 'temp_store=FILE', 'mmap_size=0', 'wal_autocheckpoint=500'):
            self.cx.execute('PRAGMA ' + pragma)
        self.cx.executescript(SCHEMA)

    def get(self, key):
        row = self.cx.execute('SELECT value FROM kv WHERE key=?', (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def put(self, key, value):
        self.cx.execute('INSERT INTO kv VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value', (key, json.dumps(value)))

    def add_market(self, condition_id, *, title=None, event_key=None, market_id=None, end_at=None, closed_at=None, rules=None, tags=(), sports=False, neg_risk=False,
                   liquidity=None, liquidity_observed_at=None, spread=None, group_title=None, cataloged=False):
        self.cx.execute('''INSERT INTO markets VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(condition_id) DO UPDATE SET
            title=COALESCE(excluded.title,title), event_key=COALESCE(excluded.event_key,event_key), market_id=COALESCE(excluded.market_id,market_id),
            end_at=COALESCE(excluded.end_at,end_at), closed_at=COALESCE(excluded.closed_at,closed_at), rules=COALESCE(excluded.rules,rules), tags=COALESCE(excluded.tags,tags),
            sports=MAX(sports,excluded.sports), neg_risk=MAX(neg_risk,excluded.neg_risk), liquidity=COALESCE(excluded.liquidity,liquidity),
            liquidity_observed_at=COALESCE(excluded.liquidity_observed_at,liquidity_observed_at), spread=COALESCE(excluded.spread,spread),
            group_title=COALESCE(excluded.group_title,group_title), cataloged=MAX(cataloged,excluded.cataloged)''',
                        (condition_id, title, event_key, market_id, end_at, closed_at, rules, json.dumps(list(tags)) if tags else None, int(sports), int(neg_risk), liquidity, liquidity_observed_at,
                         spread, group_title, int(cataloged)))

    def add_trades(self, rows):
        """Rows carry the time they were observed. Returns wallet-event pairs that gained a BUY."""
        touched = set()
        for r in rows:
            # An 8-byte digest keeps identity while storing far less than the long source key.
            inserted = self.cx.execute('INSERT OR IGNORE INTO trades VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                                       (hashlib.blake2b(r['key'].encode(), digest_size=8).digest(), r['wallet'], r['ts'], r['observed_at'], r['event_key'], r['market_id'], r['condition_id'], r['token_id'], int(r['is_buy']), r['size'], r['price'],
                                        r['size'] * r['price'], r['tx'], r.get('outcome'))).rowcount
            if inserted and r['is_buy']:
                touched.add((r['wallet'], r['event_key']))
        return touched

    def purge(self, now, retention_days, comparator_days):
        # Rows leaving the window hand over the wallet's earliest known trade before they go.
        limit = now - retention_days * 86400
        self.cx.execute('''INSERT INTO wallets SELECT wallet, MIN(ts), event_key FROM trades WHERE ts<? GROUP BY wallet
                           ON CONFLICT(wallet) DO UPDATE SET first_event_key=CASE WHEN excluded.first_trade_ts<first_trade_ts THEN excluded.first_event_key ELSE first_event_key END,
                           first_trade_ts=MIN(first_trade_ts,excluded.first_trade_ts)''', (limit,))
        self.cx.execute('DELETE FROM trades WHERE ts<?', (limit,))
        self.cx.execute('DELETE FROM comparators WHERE day<?', (int((now - comparator_days * 86400) // 86400),))

    def first_trade(self, wallet, now):
        """Earliest trade known at `now`: a row observed later must not move a past decision."""
        row = self.cx.execute('SELECT ts, event_key FROM trades WHERE wallet=? AND observed_at<=? ORDER BY ts LIMIT 1', (wallet, now)).fetchone()
        archived = self.cx.execute('SELECT first_trade_ts, first_event_key FROM wallets WHERE wallet=?', (wallet,)).fetchone()
        if archived and (row is None or archived[0] <= row[0]):
            return archived[0], archived[1]
        return (row[0], row[1]) if row else (None, None)

    def close(self):
        self.cx.close()
