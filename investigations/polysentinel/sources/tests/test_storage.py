"""Synthetic evidence: shared content must not merge observations or fills."""
import sqlite3
import tempfile
import unittest
import zlib
from pathlib import Path
from polysentinel.db import Store

class ContentTests(unittest.TestCase):
    def test_same_content_keeps_distinct_identities_times_and_aba(self):
        with tempfile.TemporaryDirectory() as d:
            s=Store(d)
            try:
                for key,at in [('fill1',10),('fill2',11)]:s.put('trade',key,{'tx':'same','size':1},at)
                s.put('trade','fill1',{'tx':'same','size':2},12)
                s.put('trade','fill1',{'tx':'same','size':1},13)
                self.assertEqual(s.count('trade'),2)
                self.assertEqual(s.conn.execute('SELECT COUNT(*) FROM history').fetchone()[0],4)
                self.assertEqual(s.conn.execute('SELECT COUNT(*) FROM contents').fetchone()[0],2)
                self.assertEqual(s.get('trade','fill1')['first_seen'],10)
                self.assertEqual(s.get('trade','fill1')['observed_at'],13)
                self.assertEqual(s.get('trade','fill1')['payload']['size'],1)
            finally:s.close()
    def test_raw_response_observations_share_bytes_not_request_context(self):
        with tempfile.TemporaryDirectory() as d:
            s=Store(d)
            try:
                a=s.evidence('a',{'cursor':'one'},200,b'exact bytes',1)
                b=s.evidence('a',{'cursor':'two'},200,b'exact bytes',2)
                self.assertNotEqual(a,b)
                rows=s.conn.execute('SELECT * FROM responses ORDER BY observed_at').fetchall()
                self.assertEqual(len(rows),2)
                self.assertEqual([zlib.decompress(r['body']) for r in rows],[b'exact bytes']*2)
                self.assertEqual(s.conn.execute('SELECT COUNT(*) FROM contents').fetchone()[0],1)
            finally:s.close()
    def test_content_and_refs_rollback_with_checkpoint(self):
        with tempfile.TemporaryDirectory() as d:
            s=Store(d)
            try:
                with self.assertRaises(RuntimeError):
                    with s.transaction() as cx:
                        s.put('trade','x',{'size':1},conn=cx);s.checkpoint('cursor',{'next':'a'},conn=cx)
                        raise RuntimeError('crash')
                for table in ('contents','objects','history','checkpoints'):
                    self.assertEqual(s.conn.execute('SELECT COUNT(*) FROM '+table).fetchone()[0],0)
            finally:s.close()

class MigrationTests(unittest.TestCase):
    def test_legacy_migration_preserves_every_logical_row(self):
        from polysentinel.storage_migration import build_migration, logical_digest
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);old=root/'old.sqlite3';new=root/'new.sqlite3'
            cx=sqlite3.connect(old)
            cx.executescript('''CREATE TABLE objects(kind TEXT,key TEXT,payload TEXT,first_seen REAL,observed_at REAL,PRIMARY KEY(kind,key));
CREATE TABLE history(id TEXT PRIMARY KEY,kind TEXT,key TEXT,payload TEXT,observed_at REAL);
CREATE TABLE checkpoints(key TEXT PRIMARY KEY,value TEXT,updated_at REAL);
CREATE TABLE responses(id TEXT PRIMARY KEY,source TEXT,params TEXT,status INTEGER,body BLOB,observed_at REAL);
CREATE TABLE cycles(id INTEGER PRIMARY KEY,start REAL,end REAL,status TEXT,metrics TEXT);''')
            cx.execute('INSERT INTO objects VALUES(?,?,?,?,?)',('trade','a','{"size":1}',1,3))
            for at,raw in ((1,'{"size":1}'),(2,'{"size":2}'),(3,'{"size":1}')):
                cx.execute('INSERT INTO history VALUES(?,?,?,?,?)',(str(at),'trade','a',raw,at))
            cx.execute('INSERT INTO responses VALUES(?,?,?,?,?,?)',('e','rpc','{}',200,zlib.compress(b'hello'),2))
            cx.execute('INSERT INTO checkpoints VALUES(?,?,?)',('c','{"next":"x"}',3))
            cx.commit();cx.close()
            result=build_migration(old,new,min_free_bytes=0)
            self.assertTrue(result['identical'])
            self.assertEqual(logical_digest(old),logical_digest(new))
            with self.assertRaises(FileExistsError):build_migration(old,new,min_free_bytes=0)
