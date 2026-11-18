"""One SQLite file (WAL) holds everything the engine knows. Rows are added or replaced by key, so reading a block, a
wallet or a receipt twice stores nothing twice. Every fill is counted (table coverage, by hour and exchange); only the
fills the engine needs are kept as rows: those of 1,000 USD or more, and every fill of a wallet under watch. Keeping all
of them would cost about 2 GB a day. The journal is an append-only chain: each entry commits to the previous
one, to its own time and to its own sequence number, and every alert is also appended to a JSON-lines file."""
import hashlib, json, os, sqlite3, time

SCHEMA = """
create table if not exists checkpoints(key text primary key, value text, updated real);
create table if not exists fills(tx text, log_index integer, block integer, ts integer, exchange text, wallet text, counterparty text,
  token_id text, side text, shares real, cash real, fee real, price real, seen real, primary key(tx, log_index));
create index if not exists fills_token_ts on fills(token_id, ts);
create index if not exists fills_wallet on fills(wallet, ts);
create table if not exists tokens(token_id text primary key, condition_id text, oi integer, status text, checked real);
create table if not exists markets(condition_id text primary key, event_slug text, title text, outcomes text, tags text, family text,
  neg_risk integer, version text, end_ts integer, updated real);
create table if not exists entries(wallet text, condition_id text, oi integer, t integer, block integer, price real, cash real, tx text,
  log_index integer, state text, tries integer default 0, next_try real default 0, note text, primary key(wallet, condition_id, oi));
create index if not exists entries_state on entries(state, next_try);
create table if not exists pending_fills(rowid_fill integer primary key, token_id text, first_seen real);
create table if not exists coverage(hour integer, exchange text, fills integer, large integer, cash real, primary key(hour, exchange));
create table if not exists views(wallet text, condition_id text, oi integer, body text, fetched real, primary key(wallet, condition_id, oi));
create table if not exists deposits(wallet text, tx text, ts integer, usdc real, status text, payer text, via text, block integer, sha256 text,
  primary key(wallet, tx));
create table if not exists addresses(address text primary key, is_contract integer, nonce integer, tags text, tags_status text, fetched real);
create table if not exists inflows(wallet text, tx text, block integer, status text, rows text, primary key(wallet, tx));
create table if not exists hops(address text, block integer, status text, rows text, primary key(address, block));
create table if not exists links(wallet text, root text, kind integer, tx text, ts integer, primary key(wallet, root, tx));
create index if not exists links_root on links(root, ts);
create table if not exists alerts(id text primary key, cls text, t_alert integer, created real, wallet text, condition_id text, oi integer, body text);
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


def journal(con, kind, body, now=None):
    """Append one entry. The hash covers the previous hash, the sequence number, the time, the kind and the body."""
    prev = con.execute("select seq, hash from journal order by seq desc limit 1").fetchone()
    seq, prev_hash = ((prev[0] + 1, prev[1]) if prev else (1, "0" * 64))
    t = time.time() if now is None else now
    text = json.dumps(body, sort_keys=True)
    h = hashlib.sha256(f"{prev_hash}|{seq}|{t!r}|{kind}|{text}".encode()).hexdigest()
    con.execute("insert into journal(seq, t, kind, body, prev, hash) values(?,?,?,?,?,?)", (seq, t, kind, text, prev_hash, h))
    return h


def verify_journal(con):
    """Recompute the chain. Returns (entries, first broken seq or None). A missing sequence number is a break."""
    prev, n, expect = "0" * 64, 0, 1
    for seq, t, kind, body, p, h in con.execute("select seq, t, kind, body, prev, hash from journal order by seq"):
        if seq != expect or p != prev or hashlib.sha256(f"{prev}|{seq}|{t!r}|{kind}|{body}".encode()).hexdigest() != h:
            return n, seq
        prev, n, expect = h, n + 1, seq + 1
    return n, None


def append_alert_file(db_path, body):
    """Alerts are also written to <db>.alerts.jsonl, one JSON object a line, each carrying the hash of the previous line."""
    path = db_path + ".alerts.jsonl"; prev = "0" * 64
    if os.path.exists(path):
        with open(path, "rb") as f:
            lines = f.read().splitlines()
        if lines:
            prev = hashlib.sha256(lines[-1]).hexdigest()
    with open(path, "a") as f:
        f.write(json.dumps(dict(body, previous_line_sha256=prev), sort_keys=True) + "\n")
    return path
