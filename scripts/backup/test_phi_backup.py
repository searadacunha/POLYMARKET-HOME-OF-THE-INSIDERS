#!/usr/bin/env python3
"""End-to-end self-check on temporary folders, with a folder standing in for GitHub: python3 scripts/backup/test_phi_backup.py"""
import gzip
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path

tmp = Path(tempfile.mkdtemp())
os.environ["PHI_STATE"] = str(tmp / "state")
os.environ["PHI_CONFIG"] = str(tmp / "config.json")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import phi_backup as core  # noqa: E402

AGE = shutil.which("age") or "/opt/homebrew/bin/age"
identity = tmp / "id.txt"
keygen = subprocess.run([AGE + "-keygen", "-o", str(identity)], capture_output=True, text=True)
recipient = keygen.stderr.split("Public key: ")[1].strip()


def make_sources():
    src = tmp / "proj"
    (src / "reports").mkdir(parents=True)
    (src / "state" / "http_cache").mkdir(parents=True)
    (src / "reports" / "final.md").write_text("result 42\n")
    (src / "same_copy.md").write_text("result 42\n")
    (src / ".env").write_text("K=v\n")
    (src / "leaky.json").write_text('{"url": "https://x?apikey=' + "A" * 34 + '"}')
    (src / "state" / "http_cache" / "r.gz").write_bytes(gzip.compress(b"payload"))
    os.symlink("reports/final.md", src / "link.md")
    db = sqlite3.connect(str(src / "live.sqlite3"))
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("CREATE TABLE t(x)")
    db.executemany("INSERT INTO t VALUES(?)", [(i,) for i in range(5000)])
    db.commit()
    return src, db  # the connection stays open: a real writer


src, writer = make_sources()
old = time.time() - 4000
for path in src.rglob("*"):
    if path.is_file() and not path.name.startswith("live.sqlite3") and not path.is_symlink():
        os.utime(path, (old, old))
cfg = {"disk_test_root": str(tmp / "disk"), "age_bin": AGE, "recipient": recipient, "identity": str(identity), "github_test_dir": str(tmp / "gh"), "repo": "x/y",
       "roots": [{"name": "proj", "path": str(src)}, {"name": "disk-only", "skip_known": True, "klass": "disk"}], "debounce_s": 300, "pack_min_bytes": 1, "pack_max_wait_s": 0, "db_github_hours": 168, "db_snapshot_hours": 0}
Path(os.environ["PHI_CONFIG"]).write_text(json.dumps(cfg))
before = {str(p): (p.lstat().st_mtime_ns, p.lstat().st_size) for p in src.rglob("*") if not p.name.startswith("live.sqlite3")}

core.pass_backup(cfg)
db = core.open_db()
assert before == {str(p): (p.lstat().st_mtime_ns, p.lstat().st_size) for p in src.rglob("*") if not p.name.startswith("live.sqlite3")}, "source changed"
rows = {r["rel"]: r for r in db.execute("SELECT * FROM files WHERE root='proj'")}
assert rows[".env"]["klass"] == "secret" and rows["leaky.json"]["klass"] == "secret", "secrets not routed"
assert rows["link.md"]["klass"] == "link" and rows["live.sqlite3"]["klass"] == "live"
assert "live.sqlite3-wal" not in rows and "live.sqlite3-shm" not in rows
assert rows["same_copy.md"]["sha"] == rows["reports/final.md"]["sha"]
assert db.execute("SELECT COUNT(*) FROM blobs WHERE sha=?", (rows["reports/final.md"]["sha"],)).fetchone()[0] == 1, "no dedupe"

# Secrets never reach the disk in clear.
clear = [p for d in ("projects", "raw-data") for p in (tmp / "disk" / d).rglob("*") if p.is_file()]
assert clear, "no clear pack"
for path in clear:
    data = path.read_bytes()
    data = gzip.decompress(data) if ".gz" in path.name else data
    assert b"apikey=" not in data and b"K=v" not in data, f"secret in clear in {path.name}"
assert db.execute("SELECT COUNT(*) FROM packs WHERE kind='secret' AND clear_volumes='[]' AND disk_enc=1").fetchone()[0] == 1

# GitHub: upload, verified by reading back. An altered asset must fail.
core.pass_upload(cfg)
states = [r["gh_state"] for r in db.execute("SELECT gh_state FROM packs")]
assert states and all(s == "verified" for s in states), states
victim = db.execute("SELECT * FROM packs WHERE kind='project'").fetchone()
asset = tmp / "gh" / json.loads(victim["enc_volumes"])[0]["name"]
good = asset.read_bytes()
asset.write_bytes(good[:-1] + bytes([good[-1] ^ 1]))
db.execute("UPDATE packs SET gh_state='uploaded' WHERE name=?", (victim["name"],))
core.upload_pending(cfg, db, core.disk_root(cfg))
row = db.execute("SELECT * FROM packs WHERE name=?", (victim["name"],)).fetchone()
assert row["gh_state"] != "verified" and row["last_error"], "altered asset accepted"
asset.write_bytes(good)
db.execute("UPDATE packs SET gh_state='pending', next_try=0, last_error=NULL WHERE name=?", (victim["name"],))
core.upload_pending(cfg, db, core.disk_root(cfg))
assert db.execute("SELECT gh_state FROM packs WHERE name=?", (victim["name"],)).fetchone()[0] == "verified"

core.write_index(cfg, db, core.disk_root(cfg))
status = core.build_status(cfg, db, core.disk_root(cfg))
assert "NOT COMPLETE" not in status, status[:400]


def restored(source, dest, identity_path, problems=0):
    class A:
        pass
    args = A()
    args.source, args.dest, args.root, args.identity, args.disk, args.manifests = source, str(dest), "proj", identity_path, str(tmp / "disk"), str(tmp / "disk" / "manifests")
    assert core.restore(args, cfg) == problems
    return Path(dest) / "proj"


for source, identity_path in (("disk", str(identity)), ("github", str(identity))):
    out = restored(source, tmp / f"restore-{source}", identity_path)
    assert (out / "reports" / "final.md").read_text() == "result 42\n"
    assert (out / "same_copy.md").read_text() == "result 42\n"
    assert (out / ".env").read_text() == "K=v\n"
    assert os.readlink(out / "link.md") == "reports/final.md"
    check = sqlite3.connect(str(out / "live.sqlite3"))
    assert check.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert check.execute("SELECT COUNT(*) FROM t").fetchone()[0] == 5000, "database image incomplete"
    check.close()

# Without the key the disk still gives everything but the secrets.
out = restored("disk", tmp / "restore-nokey", None, problems=2)  # the 2 secret files, reported rather than hidden
assert (out / "reports" / "final.md").exists() and not (out / ".env").exists()

# A new file only on the disk is picked up and sent to GitHub, not lost, not repacked in a loop.
extra = tmp / "disk" / "projects" / "added_by_hand.txt"
extra.write_text("only here")
os.utime(extra, (old, old))
core.pass_backup(cfg)
core.pass_upload(cfg)
row = db.execute("SELECT f.sha, p.gh_state, p.kind FROM files f JOIN blobs b ON b.sha=f.sha JOIN packs p ON p.name=b.pack WHERE f.root='disk-only' AND f.rel='projects/added_by_hand.txt'").fetchone()
assert row and row["gh_state"] == "verified" and row["kind"] == "disk", "disk-only file not published"
packs_before = db.execute("SELECT COUNT(*) FROM packs WHERE kind!='db'").fetchone()[0]
core.pass_backup(cfg)
assert db.execute("SELECT COUNT(*) FROM packs WHERE kind!='db'").fetchone()[0] == packs_before, "sync loop"

# Disk away: packs wait in the outbox, GitHub still gets them. Disk back: encrypted and clear copies arrive.
away = dict(cfg, disk_test_root=None, disk_mount=str(tmp / "nowhere"), disk_uuid="x")
new = src / "reports" / "later.md"
new.write_text("found later\n")
os.utime(new, (old, old))
core.pass_backup(away)
pack = db.execute("SELECT * FROM packs f WHERE EXISTS (SELECT 1 FROM blobs b JOIN files x ON x.sha=b.sha WHERE b.pack=f.name AND x.rel='reports/later.md')").fetchone()
assert pack and pack["enc_dir"].startswith("/") and pack["disk_clear"] == -1
core.pass_upload(away)
assert db.execute("SELECT gh_state FROM packs WHERE name=?", (pack["name"],)).fetchone()[0] == "verified"
core.pass_backup(cfg)
pack = db.execute("SELECT * FROM packs WHERE name=?", (pack["name"],)).fetchone()
assert pack["disk_enc"] == 1 and pack["disk_clear"] == 1 and not pack["enc_dir"].startswith("/"), dict(pack)

# A wrong disk at the same path is refused.
assert core.disk_root({"disk_mount": "/", "disk_uuid": "00000000-0000-0000-0000-000000000000", "disk_folder": "x"}) is None

writer.close()
shutil.rmtree(tmp)
print("ok all")
