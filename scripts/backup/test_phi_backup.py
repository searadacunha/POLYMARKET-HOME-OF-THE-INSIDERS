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
       "roots": [{"name": "proj", "path": str(src)}, {"name": "disk-only", "skip_known": True, "klass": "disk"}], "debounce_s": 300, "pack_min_bytes": 1, "pack_max_wait_s": 0, "internal_floor_bytes": 0, "db_github_hours": 168, "db_snapshot_hours": 0}
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

# Two listed files with the same name are two files, each restored at its own path.
(tmp / "a").mkdir()
(tmp / "b").mkdir()
for folder, text in (("a", "first copy\n"), ("b", "second copy\n")):
    (tmp / folder / "same.env").write_text(text)
    os.utime(tmp / folder / "same.env", (old, old))
listed = dict(cfg, roots=cfg["roots"] + [{"name": "listed", "klass": "secret", "files": [str(tmp / "a" / "same.env"), str(tmp / "b" / "same.env")]}])
core.pass_backup(listed)
core.pass_upload(listed)
rows = db.execute("SELECT f.rel, f.sha, p.gh_state FROM files f JOIN blobs b ON b.sha=f.sha JOIN packs p ON p.name=b.pack WHERE f.root='listed' AND f.gone_at IS NULL").fetchall()
assert len(rows) == 2 and all(r["gh_state"] == "verified" for r in rows), [dict(r) for r in rows]
core.write_index(listed, db, core.disk_root(listed))


class ListedArgs:
    source, root, identity, disk, manifests = "disk", "listed", str(identity), str(tmp / "disk"), str(tmp / "disk" / "manifests")
    dest = str(tmp / "restore-listed")


assert core.restore(ListedArgs, listed) == 0
assert (tmp / "restore-listed" / "listed" / str(tmp / "a" / "same.env").lstrip("/")).read_text() == "first copy\n"
assert (tmp / "restore-listed" / "listed" / str(tmp / "b" / "same.env").lstrip("/")).read_text() == "second copy\n"

# A file rewritten between the scan and the pack is stored as it is now, not dropped and retried forever.
disk_now = core.disk_root(cfg)
spec = core.discover_roots(cfg)[0]
moving = src / "reports" / "status.json"
moving.write_text("version one\n")
os.utime(moving, (old, old))
core.scan_root(cfg, db, spec, disk_now)
moving.write_text("version two, longer\n")
os.utime(moving, (old + 1, old + 1))
core.build_due_packs(cfg, db, disk_now)
row = db.execute("SELECT f.sha, f.size, p.disk_clear FROM files f JOIN blobs b ON b.sha=f.sha JOIN packs p ON p.name=b.pack WHERE f.root='proj' AND f.rel='reports/status.json'").fetchone()
assert row and row["sha"] == core.hash_file(moving) and row["size"] == moving.stat().st_size and row["disk_clear"] == 1, "rewritten file not stored"

# A file written without pause gets a snapshot once it has waited long enough.
busy = src / "requests.jsonl"
busy.write_text("line 1\n")
core.scan_root(cfg, db, spec, disk_now)
row = db.execute("SELECT sha FROM files WHERE root='proj' AND rel='requests.jsonl'").fetchone()
assert row and row["sha"] is None, "a file still moving must be listed as waiting, without a hash"
db.execute("UPDATE files SET last_hashed=? WHERE root='proj' AND rel='requests.jsonl'", (time.time() - 3700,))
with open(busy, "a") as fh:
    fh.write("line 2\n")
core.scan_root(cfg, db, spec, disk_now)
assert db.execute("SELECT sha FROM files WHERE root='proj' AND rel='requests.jsonl'").fetchone()["sha"] == core.hash_file(busy), "never-settling file has no snapshot"

# Caches, virtual environments and links to folders are files like any other.
(src / ".venv" / "lib").mkdir(parents=True)
(src / ".venv" / "lib" / "m.py").write_text("x = 1\n")
(src / "__pycache__").mkdir()
(src / "__pycache__" / "m.pyc").write_bytes(b"\x00pyc")
os.symlink(".venv/lib", src / "linked_dir")
for path in ((src / ".venv" / "lib" / "m.py"), (src / "__pycache__" / "m.pyc")):
    os.utime(path, (old, old))
core.scan_root(cfg, db, spec, disk_now)
names = {r["rel"]: r for r in db.execute("SELECT rel, klass, link FROM files WHERE root='proj' AND gone_at IS NULL")}
assert ".venv/lib/m.py" in names and "__pycache__/m.pyc" in names, "cache or environment skipped"
assert names["linked_dir"]["klass"] == "link" and names["linked_dir"]["link"] == ".venv/lib", "link to a folder lost"

# macOS metadata on the FAT32 disk is not research data.
(tmp / "disk" / "projects" / "._added_by_hand.txt").write_bytes(b"\x00\x05\x16\x07")
os.utime(tmp / "disk" / "projects" / "._added_by_hand.txt", (old, old))
core.scan_root(cfg, db, core.discover_roots(cfg)[1] | {"path": str(disk_now)}, disk_now)
assert not db.execute("SELECT 1 FROM files WHERE root='disk-only' AND rel LIKE '%._added%'").fetchone(), "AppleDouble file taken for data"

# A configuration without any disk, as on a fresh Mac restoring from GitHub.
assert core.disk_root({"repo": "x/y"}) is None

# A temporary name on the Mac is still a file. Only on the disk does .tmp mean an unfinished volume.
(src / "partial.tmp").write_text("intermediate\n")
os.utime(src / "partial.tmp", (old, old))
core.scan_root(cfg, db, spec, disk_now)
assert db.execute("SELECT sha FROM files WHERE root='proj' AND rel='partial.tmp'").fetchone()["sha"], "temporary file skipped"

# The audit reads real bytes: what is on the disk and GitHub is complete, an altered or absent copy is named as such.
import phi_audit  # noqa: E402
core.pass_backup(cfg)
core.pass_upload(cfg)
core.write_index(cfg, db, disk_now)
summary, _ = phi_audit.run(cfg, tmp / "audit1")
assert summary["counts"]["CORRUPTED"] == 0 and summary["counts"]["MISSING_BOTH"] == 0, summary
files = {(r["root"], r["rel"]): r for r in map(json.loads, gzip.open(tmp / "audit1" / "files.jsonl.gz", "rt"))}
assert files[("proj", "reports/final.md")]["category"] == "COMPLETE"
assert files[("proj", "live.sqlite3")]["category"] == "IN_PROGRESS" and files[("proj", "live.sqlite3-wal")]["category"] == "IN_PROGRESS"
assert files[("proj", "requests.jsonl")]["category"] in ("IN_PROGRESS", "COMPLETE")
final = db.execute("SELECT b.pack FROM files f JOIN blobs b ON b.sha=f.sha WHERE f.root='proj' AND f.rel='reports/final.md'").fetchone()["pack"]
pack = db.execute("SELECT * FROM packs WHERE name=?", (final,)).fetchone()
victim = core.pack_row_volumes(pack, disk_now, "clear")[0][0]
good_bytes = victim.read_bytes()
victim.write_bytes(good_bytes[:100] + bytes([good_bytes[100] ^ 1]) + good_bytes[101:])
summary, _ = phi_audit.run(cfg, tmp / "audit2", github=False)
files = {(r["root"], r["rel"]): r for r in map(json.loads, gzip.open(tmp / "audit2" / "files.jsonl.gz", "rt"))}
assert files[("proj", "reports/final.md")]["category"] == "CORRUPTED", files[("proj", "reports/final.md")]
assert summary["errors"] and not summary["clean"]
victim.write_bytes(good_bytes)
asset = tmp / "gh" / json.loads(pack["enc_volumes"])[0]["name"]
hidden = asset.read_bytes()
asset.unlink()
summary, _ = phi_audit.run(cfg, tmp / "audit3")
files = {(r["root"], r["rel"]): r for r in map(json.loads, gzip.open(tmp / "audit3" / "files.jsonl.gz", "rt"))}
assert files[("proj", "reports/final.md")]["category"] == "MISSING_GITHUB", files[("proj", "reports/final.md")]
assert any("asset absent" in e for e in summary["errors"]) and not summary["clean"]
asset.write_bytes(hidden)

# Two databases with the same bytes: the earlier pack has no member left and must still pass its checks.
for name in ("twin_a.sqlite3", "twin_b.sqlite3"):
    twin = sqlite3.connect(str(src / name))
    twin.execute("CREATE TABLE t(x)")
    twin.execute("INSERT INTO t VALUES(1)")
    twin.commit()
    twin.close()
(src / "twin_b.sqlite3").write_bytes((src / "twin_a.sqlite3").read_bytes())
core.pass_backup(cfg)
core.pass_upload(cfg)
twins = db.execute("SELECT name, gh_state, disk_clear, last_error FROM packs WHERE kind='db' ORDER BY created DESC LIMIT 2").fetchall()
assert len(twins) == 2 and all(r["gh_state"] == "verified" and r["disk_clear"] == 1 and not r["last_error"] for r in twins), [dict(r) for r in twins]

# One damaged or unavailable pack on GitHub is reported, and the restore goes on with the others.
broken = db.execute("SELECT b.pack, f.rel FROM files f JOIN blobs b ON b.sha=f.sha WHERE f.root='proj' AND f.rel='reports/final.md'").fetchone()["pack"]
core.write_index(cfg, db, disk_now)
manifests = tmp / "manifests-broken"
manifests.mkdir()
shutil.copyfile(core.STATE / "index.jsonl.gz", manifests / "index.jsonl.gz")
packs = json.loads((core.STATE / "packs.json").read_text())
for entry in packs:
    if entry["name"] == broken:
        entry["gh_assets"] = None
(manifests / "packs.json").write_text(json.dumps(packs))


class BrokenArgs:
    source, root, identity, disk, manifests = "github", "proj", str(identity), None, str(manifests)
    dest = str(tmp / "restore-broken")


restore_cfg = {"github_test_dir": cfg["github_test_dir"], "age_bin": AGE, "repo": "x/y"}
assert core.restore(BrokenArgs, restore_cfg) > 0, "a pack without assets must count as a problem"
assert (tmp / "restore-broken" / "proj" / "partial.tmp").exists() or (tmp / "restore-broken" / "proj" / ".env").exists(), "the other packs must still be restored"
pack_row = db.execute("SELECT * FROM packs WHERE name=?", (broken,)).fetchone()
asset = tmp / "gh" / json.loads(pack_row["enc_volumes"])[0]["name"]
saved = asset.read_bytes()
asset.write_bytes(saved[:len(saved) // 2])  # cut short, as a dropped connection would


class CutArgs(BrokenArgs):
    manifests = str(core.STATE)
    dest = str(tmp / "restore-cut")


assert core.restore(CutArgs, restore_cfg) > 0, "a cut pack must count as a problem"
asset.write_bytes(saved)

# A wrong disk at the same path is refused.
assert core.disk_root({"disk_mount": "/", "disk_uuid": "00000000-0000-0000-0000-000000000000", "disk_folder": "x"}) is None

writer.close()
shutil.rmtree(tmp)
print("ok all")
