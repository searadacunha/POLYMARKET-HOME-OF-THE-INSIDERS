"""The same migrations on real PostgreSQL, as Supabase would run them, on a throw-away local cluster (unix socket only).

Skipped when no PostgreSQL server binaries are found. Set PHI_REGISTRY_PG_BIN to the folder holding initdb/pg_ctl/psql.
This proves the SQL, the access model and the claim protocol on PostgreSQL. It does not prove anything about a hosted
Supabase project (network, quotas, pausing, key handling): no project was used.
"""
import glob
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import fixture as fx  # noqa: E402
import phi_registry as reg  # noqa: E402

TABLES = ["registry_meta", "investigations", "findings", "open_items", "evidence", "finding_addresses", "wallet_mentions",
          "hypothesis_tests", "agent_tasks", "task_events"]


def find_bin():
    if os.environ.get("PHI_REGISTRY_PG_BIN") == "none":  # skip these tests on purpose, as the continuous integration does
        return None
    candidates = [os.environ.get("PHI_REGISTRY_PG_BIN")]
    found = shutil.which("initdb")
    candidates.append(os.path.dirname(found) if found else None)
    for pattern in ("/opt/homebrew/opt/postgresql@*/bin", "/usr/local/opt/postgresql@*/bin"):  # Linux: set PHI_REGISTRY_PG_BIN
        candidates += sorted(glob.glob(pattern), reverse=True)
    for c in candidates:
        if c and all(os.access(os.path.join(c, b), os.X_OK) for b in ("initdb", "pg_ctl", "psql")):
            return c
    return None


class PsqlError(Exception):
    pass


@unittest.skipUnless(find_bin(), "PostgreSQL server binaries not found")
class Postgres(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bin = find_bin()
        cls.tmp = tempfile.mkdtemp(prefix="phi-pg-")
        cls.sock = os.path.join(cls.tmp, "s")
        if len(cls.sock) > 80:  # unix socket paths are short-limited
            shutil.rmtree(cls.tmp)
            cls.tmp = tempfile.mkdtemp(prefix="phi-pg-", dir="/tmp")
            cls.sock = os.path.join(cls.tmp, "s")
        os.makedirs(cls.sock)
        cls.data = os.path.join(cls.tmp, "data")
        cls.env = {**os.environ, "LC_ALL": "C"}  # an invalid locale in the caller's shell makes the postmaster refuse to start
        run = lambda name, *a: subprocess.run([os.path.join(cls.bin, name), *a], capture_output=True, text=True, check=True, env=cls.env)  # noqa: E731
        cls.addClassCleanup(shutil.rmtree, cls.tmp, True)
        run("initdb", "-D", cls.data, "-U", "postgres", "--auth=trust", "-E", "UTF8", "--locale=C", "--no-sync")
        run("pg_ctl", "-D", cls.data, "-l", os.path.join(cls.tmp, "log"), "-w", "-o",
            f"-c listen_addresses='' -c unix_socket_directories={cls.sock} -c port=54329 -c fsync=off -c max_connections=60 "
            "-c wal_level=minimal -c max_wal_senders=0 -c max_wal_size=96MB -c min_wal_size=32MB -c checkpoint_timeout=30s", "start")
        cls.addClassCleanup(lambda: (subprocess.run([os.path.join(cls.bin, "pg_ctl"), "-D", cls.data, "-m", "immediate", "stop"],
                                                    capture_output=True, env=cls.env), shutil.rmtree(cls.tmp, True)))
        # Supabase creates these three roles on every project; here the test creates them.
        cls.sql("CREATE ROLE anon NOLOGIN; CREATE ROLE authenticated NOLOGIN; CREATE ROLE service_role NOLOGIN BYPASSRLS;")
        cls.migrate()

    @classmethod
    def sql(cls, text, check=True):
        done = subprocess.run([os.path.join(cls.bin, "psql"), "-X", "-q", "-t", "-A", "-v", "ON_ERROR_STOP=1", "-h", cls.sock,
                               "-p", "54329", "-U", "postgres", "-d", "postgres", "-f", "-"],
                              input=text, capture_output=True, text=True, env=cls.env)
        if check and done.returncode:
            raise PsqlError(done.stderr.strip())
        return done.stdout.strip() if done.returncode == 0 else done.stderr.strip()

    @classmethod
    def migrate(cls):
        for f in sorted(reg.MIGRATIONS.glob("*.sql")):
            cls.sql(f.read_text())

    def setUp(self):
        self.sql("DELETE FROM task_events; DELETE FROM agent_tasks;")

    def loaded(self):
        root = Path(tempfile.mkdtemp(prefix="phi-pgfx-"))
        self.addCleanup(shutil.rmtree, root, True)
        fx.make_tree(root / "tree")
        con = reg.connect(root / "r.sqlite3")
        self.addCleanup(con.close)
        reg.build(con, reg.DirSource(root / "tree"))
        self.sql(reg.export_sql(con, reg.DERIVED))
        return con

    # -- the SQL itself
    def test_migrations_can_be_applied_again(self):
        self.migrate()

    def test_same_tables_and_columns_as_sqlite(self):
        root = Path(tempfile.mkdtemp(prefix="phi-pgcols-"))
        self.addCleanup(shutil.rmtree, root, True)
        con = reg.connect(root / "r.sqlite3")
        self.addCleanup(con.close)
        for t in TABLES:
            lite = [r[1] for r in con.execute(f"PRAGMA table_info({t})")]
            pg = self.sql(f"SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = '{t}' "
                          "ORDER BY ordinal_position").splitlines()
            self.assertEqual(lite, pg, t)

    def test_export_loads_twice_with_the_same_content(self):
        con = self.loaded()
        self.loaded()  # a second export replaces, never duplicates
        self.assertEqual({t: int(self.sql(f"SELECT count(*) FROM {t}")) for t in reg.DERIVED},
                         {t: con.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in reg.DERIVED})
        lite = "\n".join(f"{a}|{b}|{c}|{d}" for a, b, c, d in con.execute(
            "SELECT investigation_id, finding_id, level, claim FROM findings ORDER BY investigation_id, finding_id"))
        pg = self.sql("SELECT string_agg(investigation_id || '|' || finding_id || '|' || level || '|' || claim, E'\\n' "
                      "ORDER BY investigation_id, finding_id) FROM findings")
        self.assertEqual(hashlib.md5(lite.encode()).hexdigest(), hashlib.md5(pg.encode()).hexdigest())
        self.assertEqual(float(self.sql("SELECT p_value FROM hypothesis_tests WHERE study = 'beta' AND test_id = 'L2:T4'")), 0.0005)
        self.assertEqual(self.sql("SELECT value FROM registry_meta WHERE key = 'content_sha256'"), reg.digest(con))

    def test_constraints_refuse_bad_rows(self):
        self.loaded()
        with self.assertRaisesRegex(PsqlError, "violates check constraint"):
            self.sql("INSERT INTO findings VALUES ('alpha', 'F-500', 'MAYBE', 'c', '', '', '', '')")
        with self.assertRaisesRegex(PsqlError, "violates foreign key constraint"):
            self.sql("INSERT INTO findings VALUES ('nobody', 'F-001', 'CONFIRMED', 'c', '', '', '', '')")

    # -- who may do what
    def test_access_model(self):
        self.loaded()
        self.sql("SELECT * FROM add_task('wallet', 'x')")
        self.assertTrue(all(v == "t" for v in self.sql(
            "SELECT relrowsecurity FROM pg_class WHERE relname IN ('" + "','".join(TABLES) + "')").splitlines()))
        with self.assertRaisesRegex(PsqlError, "permission denied"):
            self.sql("SET ROLE anon; SELECT count(*) FROM findings;")
        self.assertEqual(self.sql("SET ROLE authenticated; SELECT count(*) FROM findings;").splitlines()[-1], "3")
        with self.assertRaisesRegex(PsqlError, "permission denied"):
            self.sql("SET ROLE authenticated; INSERT INTO findings VALUES ('alpha', 'F-600', 'REFUTED', 'c', '', '', '', '');")
        with self.assertRaisesRegex(PsqlError, "permission denied"):
            self.sql("SET ROLE authenticated; SELECT count(*) FROM agent_tasks;")
        with self.assertRaisesRegex(PsqlError, "permission denied for function"):
            self.sql("SET ROLE authenticated; SELECT * FROM claim_task('me');")
        with self.assertRaisesRegex(PsqlError, "permission denied for function"):
            self.sql("SET ROLE anon; SELECT * FROM claim_task('me');")
        self.assertEqual(self.sql("SET ROLE service_role; SELECT count(*) FROM agent_tasks;").splitlines()[-1], "1")

    def test_row_level_security_is_a_second_lock(self):
        self.sql("SELECT * FROM add_task('wallet', 'x')")
        got = self.sql("BEGIN; GRANT SELECT ON agent_tasks TO authenticated; SET ROLE authenticated; "
                       "SELECT count(*) FROM agent_tasks; ROLLBACK;")
        self.assertIn("0", got.splitlines(), "a grant alone shows no row: no policy, no access")

    # -- the claim protocol, on PostgreSQL
    def test_dedup_key_matches_python(self):
        for kind, subject in (("Wallet", "0xAbC  def"), ("hypothesis", "  Funding\tprecedes\nthe  purchase  "), ("market", "Election 2026")):
            self.sql(f"SELECT * FROM add_task($k${kind}$k$, $s${subject}$s$)")  # a separate statement: the function's row is not in this one's snapshot
            key = f"{kind.lower()}:{reg.norm(subject)}"
            got = self.sql(f"SELECT dedup_key, id, subject FROM agent_tasks WHERE dedup_key = $k${key}$k$")
            self.assertEqual(got, f"{key}|{hashlib.sha256(key.encode()).hexdigest()[:16]}|{reg.collapse(subject)}")
        again = self.sql("SELECT created FROM add_task('wallet', '0xabc DEF')")
        self.assertEqual(again, "f")

    def test_lease_takeover_fencing_and_events(self):
        task = self.sql("SELECT task_id FROM add_task('hypothesis', 'h1', 3, 2)")
        first = self.sql("SELECT task_id, token FROM claim_task('a1', 1)").split("|")
        self.assertEqual(first, [task, "1"])
        self.assertEqual(self.sql("SELECT count(*) FROM claim_task('a2', 1)"), "0")
        self.assertEqual(self.sql(f"SELECT complete_task('{task}', 'a1', 99)"), "f")
        time.sleep(2.1)
        self.assertEqual(self.sql("SELECT task_id, token FROM claim_task('a2', 60)").split("|"), [task, "2"])
        self.assertEqual(self.sql(f"SELECT complete_task('{task}', 'a1', 1, 'late')"), "f", "the old holder is fenced out")
        self.assertEqual(self.sql(f"SELECT heartbeat_task('{task}', 'a2', 2, 60)"), "t")
        self.assertEqual(self.sql(f"SELECT complete_task('{task}', 'a2', 2, 'F-007')"), "t")
        self.assertEqual(self.sql(f"SELECT complete_task('{task}', 'a2', 2)"), "f")
        self.assertEqual(self.sql("SELECT string_agg(event, ',' ORDER BY at, event) FROM task_events").split(",").count("claimed"), 2)
        self.assertEqual(self.sql("SELECT status || '/' || result_ref FROM agent_tasks"), "done/F-007")

    def test_failure_requeues_then_closes_and_exhausted_leases_are_reaped(self):
        self.sql("SELECT * FROM add_task('market', 'm1', 3, 2)")
        self.assertEqual(self.sql("SELECT token FROM claim_task('a', 60)"), "1")
        tid = self.sql("SELECT id FROM agent_tasks")
        self.assertEqual(self.sql(f"SELECT fail_task('{tid}', 'a', 1, 'rate limited')"), "queued")
        self.assertEqual(self.sql("SELECT token FROM claim_task('b', 60)"), "2")
        self.assertEqual(self.sql(f"SELECT fail_task('{tid}', 'b', 2, 'again')"), "failed")
        self.assertEqual(self.sql("SELECT count(*) FROM claim_task('c', 60)"), "0")
        self.sql("SELECT * FROM add_task('market', 'm2', 3, 1)")
        self.sql("SELECT * FROM claim_task('crasher', 1)")
        time.sleep(2.1)
        self.assertEqual(self.sql("SELECT count(*) FROM claim_task('d', 60)"), "0")
        self.assertEqual(self.sql("SELECT last_error FROM agent_tasks WHERE dedup_key = 'market:m2'"), "lease expired after max attempts")

    def test_concurrent_agents_never_share_a_task_and_crashes_are_recovered(self):
        total = 80
        self.sql("\n".join(f"SELECT add_task('wallet', 'subject {i}', 3, 20);" for i in range(total)))
        lock, done_by = threading.Lock(), []

        def worker(n, janitor=False):
            step = 0
            while True:
                step += 1
                got = self.sql(f"SELECT task_id, token FROM claim_task('agent-{n}', {30 if janitor else 1})")
                if not got:
                    if int(self.sql("SELECT count(*) FROM agent_tasks WHERE status IN ('queued', 'running')")) == 0:
                        return
                    time.sleep(0.2)
                    continue
                task, token = got.split("|")
                if not janitor and step % 6 == 0:  # this agent "crashes": the 1 s lease is left to expire
                    continue
                if self.sql(f"SELECT complete_task('{task}', 'agent-{n}', {token}, 'by-{n}')") == "t":
                    with lock:
                        done_by.append(task)

        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(worker, range(8)))
        self.assertEqual(len(done_by), total)
        self.assertEqual(len(set(done_by)), total, "no task completed twice")
        self.assertEqual(self.sql("SELECT status || ':' || count(*) FROM agent_tasks GROUP BY status"), f"done:{total}")
        self.assertEqual(self.sql("SELECT count(*) FROM (SELECT task_id FROM task_events WHERE event = 'done' GROUP BY task_id HAVING count(*) > 1) x"), "0")


if __name__ == "__main__":
    unittest.main()
