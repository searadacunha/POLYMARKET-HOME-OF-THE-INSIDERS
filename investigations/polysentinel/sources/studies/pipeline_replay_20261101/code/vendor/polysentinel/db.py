"""Latest objects + immutable observation history; atomic page checkpoints."""
import contextlib
import hashlib
import json
import sqlite3
import time
import zlib
from pathlib import Path

def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)

def register_functions(cx):
    cx.create_function('payload_text',1,lambda body:zlib.decompress(body).decode('utf-8'),deterministic=True)

def create_schema(cx):
    register_functions(cx)
    cx.executescript('''
CREATE TABLE IF NOT EXISTS contents(id TEXT PRIMARY KEY,body BLOB NOT NULL,raw_bytes INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS object_refs(kind TEXT,key TEXT,content_id TEXT NOT NULL REFERENCES contents(id),first_seen REAL,observed_at REAL,PRIMARY KEY(kind,key));
CREATE INDEX IF NOT EXISTS objects_time ON object_refs(kind,observed_at);
CREATE TABLE IF NOT EXISTS history_refs(id TEXT PRIMARY KEY,kind TEXT,key TEXT,content_id TEXT NOT NULL REFERENCES contents(id),observed_at REAL);
CREATE INDEX IF NOT EXISTS history_time ON history_refs(kind,observed_at);
CREATE TABLE IF NOT EXISTS response_refs(id TEXT PRIMARY KEY,source TEXT,params TEXT,status INTEGER,content_id TEXT NOT NULL REFERENCES contents(id),observed_at REAL);
CREATE TABLE IF NOT EXISTS trade_index(key TEXT PRIMARY KEY,wallet TEXT,trade_time REAL,observed_at REAL,condition_id TEXT);
CREATE INDEX IF NOT EXISTS trade_wallet_time ON trade_index(wallet,trade_time,observed_at);
CREATE INDEX IF NOT EXISTS trade_time ON trade_index(trade_time,observed_at);
CREATE INDEX IF NOT EXISTS trade_condition ON trade_index(condition_id);
CREATE VIEW IF NOT EXISTS objects AS SELECT r.kind,r.key,payload_text(c.body) payload,r.first_seen,r.observed_at FROM object_refs r JOIN contents c ON c.id=r.content_id;
CREATE VIEW IF NOT EXISTS history AS SELECT r.id,r.kind,r.key,payload_text(c.body) payload,r.observed_at FROM history_refs r JOIN contents c ON c.id=r.content_id;
CREATE VIEW IF NOT EXISTS responses AS SELECT r.id,r.source,r.params,r.status,c.body,r.observed_at FROM response_refs r JOIN contents c ON c.id=r.content_id;
CREATE TABLE IF NOT EXISTS checkpoints(key TEXT PRIMARY KEY,value TEXT,updated_at REAL);
CREATE TABLE IF NOT EXISTS cycles(id INTEGER PRIMARY KEY,start REAL,end REAL,status TEXT,metrics TEXT);
PRAGMA user_version=2;
''')

def save_content(cx,raw):
    digest=hashlib.sha256(raw).hexdigest()
    if cx.execute('SELECT 1 FROM contents WHERE id=?',(digest,)).fetchone() is None:
        cx.execute('INSERT INTO contents VALUES(?,?,?)',(digest,zlib.compress(raw),len(raw)))
    return digest

def index_trade(cx,key,payload,at):
    if payload.get('wallet') and isinstance(payload.get('timestamp'),(int,float)):
        cx.execute('INSERT OR IGNORE INTO trade_index VALUES(?,?,?,?,?)',
                   (str(key),payload['wallet'].lower(),payload['timestamp'],at,payload.get('condition_id','')))

class Store:
    def __init__(self, root):
        self.root = Path(root)
        (self.root / 'data').mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.root / 'data/polysentinel.sqlite3', timeout=30)
        self.conn.row_factory = sqlite3.Row
        register_functions(self.conn)
        legacy=self.conn.execute("SELECT 1 FROM sqlite_master WHERE name='objects' AND type='table'").fetchone()
        if legacy:
            self.conn.close()
            raise RuntimeError('Stockage v1 : migration explicite requise, service arrêté et sauvegarde vérifiée.')
        self.conn.execute('PRAGMA journal_mode=WAL')
        self.conn.execute('PRAGMA synchronous=FULL')
        self.conn.execute('PRAGMA busy_timeout=30000')
        self.conn.execute('PRAGMA foreign_keys=ON')
        if self.conn.execute('PRAGMA user_version').fetchone()[0]!=2:create_schema(self.conn)
        self.conn.commit()

    @contextlib.contextmanager
    def transaction(self):
        self.conn.execute('BEGIN IMMEDIATE')
        try:
            yield self.conn
            self.conn.commit()
        except BaseException:
            self.conn.rollback()
            raise

    def put(self, kind, key, payload, observed_at=None, conn=None):
        at = time.time() if observed_at is None else observed_at
        raw = encode(payload)
        digest = hashlib.sha256(encode([kind,str(key),raw,at]).encode()).hexdigest()
        cx = conn or self.conn
        content=save_content(cx,raw.encode())
        cx.execute('INSERT OR IGNORE INTO history_refs VALUES(?,?,?,?,?)', (digest,kind,str(key),content,at))
        cx.execute('INSERT INTO object_refs VALUES(?,?,?,?,?) ON CONFLICT(kind,key) DO UPDATE SET content_id=excluded.content_id,observed_at=excluded.observed_at', (kind,str(key),content,at,at))
        if kind=='trade':index_trade(cx,key,payload,at)
        if conn is None:
            cx.commit()
        return digest

    @staticmethod
    def _object(row):
        if row is None:
            return None
        obj = dict(row)
        obj['payload'] = json.loads(obj['payload'])
        return obj

    def get(self,kind,key):
        return self._object(self.conn.execute('SELECT * FROM objects WHERE kind=? AND key=?',(kind,str(key))).fetchone())

    def list(self,kind,limit=1000):
        return [self._object(r) for r in self.conn.execute('SELECT * FROM objects WHERE kind=? ORDER BY observed_at DESC,key LIMIT ?',(kind,limit))]

    def checkpoint(self,key,value=None,conn=None):
        cx = conn or self.conn
        if value is None:
            r = cx.execute('SELECT value FROM checkpoints WHERE key=?',(key,)).fetchone()
            return json.loads(r[0]) if r else None
        cx.execute('INSERT INTO checkpoints VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value,updated_at=excluded.updated_at',(key,encode(value),time.time()))
        if conn is None:
            cx.commit()

    def health(self,source,status,detail,**metrics):
        self.put('health',source,dict(source=source,status=status,detail=detail,**metrics))

    def evidence(self,source,params,status,body,observed_at=None,conn=None):
        at = time.time() if observed_at is None else observed_at
        raw = body if isinstance(body,bytes) else encode(body).encode()
        digest = hashlib.sha256(encode([source,params,status,at]).encode()+raw).hexdigest()
        cx = conn or self.conn
        content=save_content(cx,raw)
        cx.execute('INSERT OR IGNORE INTO response_refs VALUES(?,?,?,?,?,?)',(digest,source,encode(params),status,content,at))
        if conn is None:
            cx.commit()
        return digest

    def count(self,kind):
        return self.conn.execute('SELECT COUNT(*) FROM object_refs WHERE kind=?',(kind,)).fetchone()[0]

    def close(self):
        self.conn.close()
