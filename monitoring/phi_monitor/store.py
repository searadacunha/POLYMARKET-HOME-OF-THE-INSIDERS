"""Durable local state in one SQLite file (WAL). Rows are only added or replaced by key: re-reading a block, a page or
a market is idempotent, so an interrupted run resumes without duplicates. The journal is an append-only hash chain."""
import hashlib, json, sqlite3, time

SCHEMA = """
create table if not exists checkpoints(key text primary key, value text, updated real);
create table if not exists markets(condition_id text primary key, event_slug text, title text, tags text, neg_risk integer,
  yes_token text, no_token text, end_ts integer, closed integer, updated real);
create table if not exists tokens(token_id text primary key, condition_id text, outcome text);
create table if not exists fills(tx text, log_index integer, block integer, ts integer, source text, wallet text, counterparty text,
  token_id text, side text, shares real, cash real, price real, seen real, primary key(tx, log_index));
create index if not exists fills_token_ts on fills(token_id, ts);
create table if not exists prices(token_id text, ts integer, price real, primary key(token_id, ts));
create table if not exists baselines(wallet text, as_of integer, body text, fetched real, primary key(wallet, as_of));
create table if not exists funding(tx text, log_index integer, block integer, ts integer, proxy text, payer text, token text, amount real,
  payer_kind text, payer_nonce integer, primary key(tx, log_index));
create index if not exists funding_payer on funding(payer);
create table if not exists owners(proxy text primary key, owners text, fetched real);
create table if not exists candidates(condition_id text, side text, first_seen integer, state text, note text, primary key(condition_id, side));
create table if not exists alerts(id text primary key, t_alert integer, created real, condition_id text, side text, level text, body text);
create table if not exists journal(seq integer primary key autoincrement, t real, kind text, body text, prev text, hash text);
"""


def connect(path):
    con = sqlite3.connect(path, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("pragma journal_mode=wal"); con.execute("pragma synchronous=normal")
    con.executescript(SCHEMA)
    return con


def checkpoint(con, key, value=None):
    if value is None:
        r = con.execute("select value from checkpoints where key=?", (key,)).fetchone()
        return json.loads(r[0]) if r else None
    con.execute("insert or replace into checkpoints values(?,?,?)", (key, json.dumps(value), time.time()))


def add_fills(con, fills, source):
    """Insert fills; an already known (tx, log_index) keeps its first observation. Returns the number of new rows."""
    before = con.total_changes
    con.executemany("insert or ignore into fills values(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    [(f["tx"], f["log_index"], f.get("block"), f["ts"], source, f["wallet"], f.get("counterparty"), f["token_id"],
                      f["side"], f["shares"], f["cash"], f["price"], time.time()) for f in fills])
    return con.total_changes - before


def put_market(con, m):
    con.execute("insert or replace into markets values(?,?,?,?,?,?,?,?,?,?)",
                (m["condition_id"], m.get("event_slug"), m.get("title"), json.dumps(m.get("tags") or []), int(bool(m.get("neg_risk"))),
                 m["yes_token"], m["no_token"], m.get("end_ts"), int(bool(m.get("closed"))), time.time()))
    con.executemany("insert or replace into tokens values(?,?,?)",
                    [(m["yes_token"], m["condition_id"], "Yes"), (m["no_token"], m["condition_id"], "No")])


def tape(con, condition_id, t_from, t_to):
    """Rows of one market as (ts, wallet, side, outcome, size, price), oldest first: the shape tapefeat expects."""
    return [tuple(r) for r in con.execute(
        "select f.ts, f.wallet, f.side, t.outcome, f.shares, f.price from fills f join tokens t on t.token_id=f.token_id "
        "where t.condition_id=? and f.ts between ? and ? order by f.ts, f.block, f.log_index", (condition_id, t_from, t_to))]


def journal(con, kind, body):
    """Append one entry to the evidence journal; each entry commits to the previous one."""
    prev = con.execute("select hash from journal order by seq desc limit 1").fetchone()
    prev = prev[0] if prev else "0" * 64
    text = json.dumps(body, sort_keys=True)
    h = hashlib.sha256((prev + kind + text).encode()).hexdigest()
    con.execute("insert into journal(t, kind, body, prev, hash) values(?,?,?,?,?)", (time.time(), kind, text, prev, h))
    return h


def verify_journal(con):
    """Recompute the chain. Returns (entries, first broken seq or None)."""
    prev, n = "0" * 64, 0
    for seq, kind, body, p, h in con.execute("select seq, kind, body, prev, hash from journal order by seq"):
        if p != prev or hashlib.sha256((prev + kind + body).encode()).hexdigest() != h:
            return n, seq
        prev, n = h, n + 1
    return n, None
