#!/usr/bin/env python3
"""Continuous backup of the Polymarket research to an external disk and to GitHub Releases.

Files are stored as immutable packs, never updated in place: a tar stream, compressed, written
to the disk in clear and encrypted with age for both the disk and GitHub. Secrets only ever exist
in the encrypted form. A file counts as saved only once its bytes were read back and hashed.

  phi_backup.py run backup|upload|repo   one pass under a lock and a watchdog (launchd entry point)
  phi_backup.py status                   write BACKUP_STATUS.md and the local dashboard
  phi_backup.py restore --source disk|github --dest DIR [--root NAME]

Python 3.9 standard library plus the age binary, so that a fresh Mac can restore.
"""
import argparse
import fcntl
import fnmatch
import glob
import gzip
import hashlib
import html
import json
import os
import plistlib
import re
import shutil
import signal
import sqlite3
import stat
import subprocess
import sys
import tarfile
import threading
import time
from pathlib import Path

CHUNK = 1 << 20
VOLUME_BYTES = 1400 * 1024 * 1024  # GitHub limit asked by the owner: under 1.5 GiB. Also under the FAT32 4 GiB limit.
PACK_BYTES = 1300 * 1024 * 1024
HOME = Path.home()
STATE = Path(os.environ.get("PHI_STATE", HOME / ".local/state/phi-backup"))
CONFIG = Path(os.environ.get("PHI_CONFIG", HOME / ".config/phi-backup/config.json"))
SUBDIRS = ("projects", "investigations", "raw-data", "git-backups", "archives", "manifests", "sync-logs", "recovery")
EXCLUDED_DIRS = {".venv", "__pycache__", "node_modules", ".pytest_cache", ".Spotlight-V100", ".fseventsd", ".Trashes"}
EXCLUDED_NAMES = {".DS_Store"}
SECRET_NAME = re.compile(r"^(\.env(\..*)?|.*\.(pem|key|p12|pfx|keystore)|id_(rsa|ed25519|ecdsa).*|.*credentials.*|.*cookies?(\.txt|\.json|\.sqlite)?)$", re.I)
COMPRESSED_EXT = {".gz", ".zst", ".zip", ".xz", ".bz2", ".png", ".jpg", ".jpeg", ".webp", ".pdf", ".parquet", ".bundle"}
RAW_PATH = re.compile(r"(^|/)(http_cache|raw|donnees|data|state|logs|metrics|cache|activity_cache)(/|$)|\.(log|sqlite3?|db|pkl|pickle|jsonl)$", re.I)
# shortcut: only the first 8 MB of a file are searched, and raw caches not at all. This routing only keeps secrets out of
# the clear copy on the owner's own disk: on GitHub everything is encrypted whatever the routing says.
SCAN_LIMIT = 8_000_000
NO_SCAN_PATH = re.compile(r"(^|/)(http_cache|activity_cache|raw/http|donnees/brut_)")
# Same patterns as the repository scan: a hit keeps the file out of the clear copy on the disk.
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(1, str(Path(__file__).resolve().parent.parent))
import phi_lib  # noqa: E402

SCHEMA = """
CREATE TABLE IF NOT EXISTS files(root TEXT, rel TEXT, size INT, mtime_ns INT, mode INT, sha TEXT, klass TEXT, link TEXT,
  last_seen REAL, last_hashed REAL, gone_at REAL, PRIMARY KEY(root, rel));
CREATE TABLE IF NOT EXISTS versions(root TEXT, rel TEXT, sha TEXT, size INT, mtime_ns INT, seen_at REAL, PRIMARY KEY(root, rel, sha));
CREATE TABLE IF NOT EXISTS blobs(sha TEXT PRIMARY KEY, size INT, pack TEXT, member TEXT);
CREATE TABLE IF NOT EXISTS packs(name TEXT PRIMARY KEY, kind TEXT, root TEXT, created REAL, n_files INT, bytes_in INT,
  clear_dir TEXT, clear_volumes TEXT, enc_dir TEXT, enc_volumes TEXT, disk_clear INT, disk_enc INT, gh_state TEXT, gh_tag TEXT,
  gh_assets TEXT, tries INT DEFAULT 0, next_try REAL DEFAULT 0, last_error TEXT, verified_at REAL);
CREATE TABLE IF NOT EXISTS kv(k TEXT PRIMARY KEY, v TEXT);
CREATE TABLE IF NOT EXISTS exports(rel TEXT PRIMARY KEY, sha TEXT);
CREATE INDEX IF NOT EXISTS files_sha ON files(sha);
CREATE INDEX IF NOT EXISTS blobs_pack ON blobs(pack);
"""


def now():
    return time.time()


def stamp(t=None):
    return time.strftime("%Y%m%d-%H%M%S", time.gmtime(t or now()))


def iso(t):
    return time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(t)) if t else "never"


def load_config():
    return json.loads(CONFIG.read_text())


def open_db():
    STATE.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(STATE / "state.sqlite3"), timeout=120, isolation_level=None)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA busy_timeout=120000")
    for attempt in range(30):  # changing the journal mode ignores the busy timeout when several services start together
        try:
            db.execute("PRAGMA journal_mode=WAL")
            break
        except sqlite3.OperationalError:
            time.sleep(2)
    db.execute("PRAGMA synchronous=NORMAL")
    db.executescript(SCHEMA)
    return db


def kv_get(db, key, default=None):
    row = db.execute("SELECT v FROM kv WHERE k=?", (key,)).fetchone()
    return json.loads(row["v"]) if row else default


def kv_set(db, key, value):
    db.execute("INSERT OR REPLACE INTO kv VALUES(?,?)", (key, json.dumps(value)))


def log(event, **fields):
    STATE.mkdir(parents=True, exist_ok=True)
    path = STATE / "events.jsonl"
    if path.exists() and path.stat().st_size > 10_000_000:
        path.replace(STATE / "events.jsonl.1")
    with open(path, "a") as fh:
        fh.write(json.dumps({"t": iso(now()), "event": event, **fields}) + "\n")


def beat():
    (STATE / f"heartbeat.{os.getpid()}").touch()


# ---------------------------------------------------------------- destinations

def disk_root(cfg):
    """The configured disk only, recognised by UUID. Any other volume at the same path is refused."""
    if cfg.get("disk_test_root"):
        root = Path(cfg["disk_test_root"])
    else:
        mount = cfg["disk_mount"]
        if not os.path.ismount(mount):
            return None
        try:
            info = plistlib.loads(subprocess.run(["/usr/sbin/diskutil", "info", "-plist", mount], capture_output=True, timeout=30).stdout)
        except (subprocess.SubprocessError, plistlib.InvalidFileException, ValueError):
            return None
        if info.get("VolumeUUID") != cfg["disk_uuid"]:
            log("disk_refused", reason="UUID differs")
            return None
        root = Path(mount) / cfg["disk_folder"]
    for sub in SUBDIRS:
        (root / sub).mkdir(parents=True, exist_ok=True)
    return root


def on_low_battery():
    try:
        out = subprocess.run(["/usr/bin/pmset", "-g", "batt"], capture_output=True, text=True, timeout=10).stdout
    except subprocess.SubprocessError:
        return False
    match = re.search(r"(\d+)%; discharging", out)
    return bool(match and int(match.group(1)) < 15)


def free_bytes(path):
    return shutil.disk_usage(path).free


class VolumeWriter:
    """Stream to numbered files, each renamed only once complete, with the SHA-256 of each."""

    def __init__(self, base, limit=VOLUME_BYTES):
        self.base, self.limit, self.volumes = Path(base), limit, []
        self.base.parent.mkdir(parents=True, exist_ok=True)
        self.fh = None

    def _open(self):
        self.name = f"{self.base.name}.{len(self.volumes) + 1:03d}"
        self.fh = open(self.base.parent / (self.name + ".tmp"), "wb")
        self.sha, self.size = hashlib.sha256(), 0

    def _close(self):
        self.fh.flush()
        os.fsync(self.fh.fileno())
        self.fh.close()
        os.replace(self.base.parent / (self.name + ".tmp"), self.base.parent / self.name)
        self.volumes.append({"name": self.name, "size": self.size, "sha": self.sha.hexdigest()})
        self.fh = None

    def write(self, data):
        view = memoryview(data)
        while len(view):
            if self.fh is None:
                self._open()
            room = self.limit - self.size
            part = view[:room]
            self.fh.write(part)
            self.sha.update(part)
            self.size += len(part)
            view = view[room:]
            if self.size >= self.limit:
                self._close()
        return len(data)

    def close(self):
        if self.fh is not None:
            self._close()


class AgeWriter:
    """Encrypt to a VolumeWriter. Only the public recipient is needed, the service never holds the key to write."""

    def __init__(self, age_bin, recipient, volumes):
        self.volumes = volumes
        self.proc = subprocess.Popen([age_bin, "-r", recipient], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        self.error = None
        self.thread = threading.Thread(target=self._drain, daemon=True)
        self.thread.start()

    def _drain(self):
        try:
            for chunk in iter(lambda: self.proc.stdout.read(CHUNK), b""):
                self.volumes.write(chunk)
        except OSError as exc:
            self.error = exc

    def write(self, data):
        self.proc.stdin.write(data)
        return len(data)

    def close(self):
        self.proc.stdin.close()
        self.thread.join()
        if self.proc.wait() != 0 or self.error:
            raise OSError(f"age failed: {self.error or self.proc.returncode}")
        self.volumes.close()


class Tee:
    def __init__(self, sinks):
        self.sinks = sinks

    def write(self, data):
        for sink in self.sinks:
            sink.write(data)
        return len(data)

    def flush(self):
        pass


class ConcatReader:
    def __init__(self, paths):
        self.paths, self.fh = list(paths), None

    def read(self, n=-1):
        while True:
            if self.fh is None:
                if not self.paths:
                    return b""
                self.fh = open(self.paths.pop(0), "rb")
            data = self.fh.read(n)
            if data:
                return data
            self.fh.close()
            self.fh = None


class HashingReader:
    """Hand tarfile exactly `size` bytes and hash what really left the file. A file that shrank is padded and flagged."""

    def __init__(self, fh, size):
        self.fh, self.left, self.sha, self.short = fh, size, hashlib.sha256(), False

    def read(self, n=-1):
        n = self.left if n < 0 else min(n, self.left)
        if n <= 0:
            return b""
        data = self.fh.read(n)
        if not data:
            self.short = True
            data = b"\0" * n
        else:
            self.sha.update(data)
        self.left -= len(data)
        return data


# ---------------------------------------------------------------- what to back up

def discover_roots(cfg):
    roots = []
    seen = set()
    for spec in cfg["roots"]:
        if "glob" in spec:
            for path in sorted(glob.glob(os.path.expanduser(spec["glob"]))):
                name = spec.get("prefix", "") + os.path.basename(path)
                if os.path.isdir(path) and not os.path.islink(path) and name not in seen:
                    seen.add(name)
                    roots.append({**spec, "name": name, "path": path})
        elif spec["name"] not in seen:
            seen.add(spec["name"])
            roots.append({**spec, "path": os.path.expanduser(spec.get("path", ""))})
    return roots


def is_git_with_commits(path):
    if not os.path.exists(os.path.join(path, ".git")):
        return False
    return subprocess.run(["git", "-C", path, "rev-parse", "--verify", "-q", "HEAD"], capture_output=True).returncode == 0


def classify(rel, name, data_path, size, forced=None):
    if forced:
        return forced
    if SECRET_NAME.match(name):
        return "secret"
    if not NO_SCAN_PATH.search(rel) and not name.endswith((".png", ".jpg", ".jpeg", ".zst", ".zip", ".pdf", ".sqlite3", ".db", ".pkl")):
        try:
            if name.endswith(".gz"):
                with gzip.open(data_path, "rb") as fh:
                    data = fh.read(SCAN_LIMIT)
            else:
                with open(data_path, "rb") as fh:
                    data = fh.read(SCAN_LIMIT)
        except (OSError, EOFError, ValueError):
            data = b""
        if any(rx.search(data) for _, rx in phi_lib.SECRET_RES) or phi_lib.digest_hits(data, phi_lib.KNOWN_DIGESTS):
            return "secret"
    return "normal"


def is_live_db(full, st):
    if not full.endswith((".sqlite3", ".sqlite", ".db")):
        return False
    return os.path.exists(full + "-wal") or now() - st.st_mtime < 3600


def hash_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def walk_root(root):
    """Yield (rel, full path). `files` lists exact paths; `dirs_glob` and `only` narrow a folder shared with other work."""
    if root.get("files"):
        for pattern in root["files"]:
            for full in sorted(glob.glob(os.path.expanduser(pattern))):
                if os.path.isfile(full):
                    yield os.path.basename(full), full
        return
    base = root["path"]
    if root.get("skip_known"):
        tops = [os.path.join(base, d) for d in ("projects", "raw-data", "investigations")]
    else:
        tops = sorted(glob.glob(os.path.join(base, root["dirs_glob"]))) if root.get("dirs_glob") else [base]
    keep_git = not is_git_with_commits(base)
    only = set(root["only"]) if root.get("only") else None
    for top in tops:
        for dirpath, dirnames, filenames in os.walk(top):
            dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS and (d != ".git" or keep_git)]
            for name in filenames:
                if name in EXCLUDED_NAMES or (only and name not in only):
                    continue
                full = os.path.join(dirpath, name)
                yield os.path.relpath(full, base), full


def scan_root(cfg, db, root, disk=None):
    """Record every file. Unchanged size and mtime are not read again. A file still moving waits for the next pass."""
    name, started, debounce = root["name"], now(), cfg.get("debounce_s", 300)
    if now() - (kv_get(db, f"scan:{name}", {}) or {}).get("at", 0) < root.get("scan_every_s", 0):
        db.execute("UPDATE files SET last_seen=? WHERE root=?", (started, name))
        return 0
    slow, slow_s = cfg.get("slow_globs", []), cfg.get("slow_hours", 24) * 3600
    known = {r["rel"]: r for r in db.execute("SELECT rel,size,mtime_ns,sha,last_hashed,klass FROM files WHERE root=?", (name,))}
    skip = known_disk_paths(db) if root.get("skip_known") else set()
    seen, n, hashed, unstable = [], 0, 0, 0
    for rel, full in walk_root(root):
        n += 1
        if n % 2000 == 0:
            beat()
        if rel in skip or rel.endswith(".tmp"):
            continue
        try:
            rel.encode("utf-8")
            st = os.lstat(full)
        except (OSError, UnicodeEncodeError) as exc:
            log("skip_file", root=name, error=type(exc).__name__)
            continue
        t = now()
        if stat.S_ISLNK(st.st_mode):
            db.execute("INSERT OR REPLACE INTO files VALUES(?,?,?,?,?,?,?,?,?,?,NULL)", (name, rel, 0, st.st_mtime_ns, st.st_mode, None, "link", os.readlink(full), t, t))
            continue
        if not stat.S_ISREG(st.st_mode):
            continue
        if full.endswith("-shm") or (full.endswith("-wal") and os.path.exists(full[:-4])):
            continue  # part of a live database, captured by its snapshot
        row = known.get(rel)
        if is_live_db(full, st) or (row and row["klass"] == "live"):
            db.execute("""INSERT INTO files VALUES(?,?,?,?,?,?,?,?,?,?,NULL) ON CONFLICT(root,rel) DO UPDATE SET size=excluded.size,
                          mtime_ns=excluded.mtime_ns, klass='live', last_seen=excluded.last_seen, gone_at=NULL""",
                       (name, rel, st.st_size, st.st_mtime_ns, st.st_mode, row["sha"] if row else None, "live", None, t, row["last_hashed"] if row else 0))
            continue
        if row and row["size"] == st.st_size and row["mtime_ns"] == st.st_mtime_ns:
            seen.append(rel)
            continue
        is_slow = any(fnmatch.fnmatch(rel, g) for g in slow)
        if (is_slow and row and t - (row["last_hashed"] or 0) < slow_s) or (not is_slow and t - st.st_mtime < debounce):
            unstable += 0 if is_slow else 1
            if row:
                seen.append(rel)
            continue
        try:
            sha = hash_file(full)
        except OSError as exc:
            log("read_error", root=name, rel=rel, error=type(exc).__name__)
            continue
        hashed += 1
        beat()
        klass = classify(rel, os.path.basename(full), full, st.st_size, root.get("klass"))
        db.execute("INSERT OR REPLACE INTO files VALUES(?,?,?,?,?,?,?,?,?,?,NULL)", (name, rel, st.st_size, st.st_mtime_ns, st.st_mode, sha, klass, None, t, t))
        db.execute("INSERT OR IGNORE INTO versions VALUES(?,?,?,?,?,?)", (name, rel, sha, st.st_size, st.st_mtime_ns, t))
    if seen:
        db.execute("BEGIN")
        db.executemany("UPDATE files SET last_seen=?, gone_at=NULL WHERE root=? AND rel=?", [(now(), name, rel) for rel in seen])
        db.execute("COMMIT")
    db.execute("UPDATE files SET gone_at=? WHERE root=? AND last_seen<? AND gone_at IS NULL", (now(), name, started - 1))
    kv_set(db, f"scan:{name}", {"at": now(), "files": n, "hashed": hashed, "unstable": unstable})
    return hashed


def pack_kind(row):
    if row["klass"] == "secret":
        return "secret"
    if row["klass"] == "disk":
        return "disk"
    if os.path.splitext(row["rel"])[1].lower() in COMPRESSED_EXT:
        return "rawz"
    return "raw" if RAW_PATH.search(row["rel"]) else "project"


def safe_name(name):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name)


# ---------------------------------------------------------------- packs

def sinks_for(cfg, disk, kind, root, name, ext, encrypt=True):
    """Clear copy on the disk unless secret, encrypted copy on the disk, or in the outbox while the disk is away."""
    clear = None
    if disk and kind not in ("secret", "disk"):
        sub = "projects" if kind == "project" else "raw-data"
        clear = VolumeWriter(disk / sub / safe_name(root) / (name + ext))
    enc = None
    if encrypt:
        enc_dir = disk / "archives" / time.strftime("%Y-%m", time.gmtime()) if disk else STATE / "outbox"
        enc = AgeWriter(cfg["age_bin"], cfg["recipient"], VolumeWriter(enc_dir / (name + ext + ".age")))
    return clear, enc


def record_pack(db, name, kind, root, n_files, bytes_in, clear, enc, disk):
    def rel_dir(writer):
        return str(writer.base.parent.relative_to(disk)) if disk and writer else (str(writer.base.parent) if writer else None)
    enc_vol = enc.volumes if enc else None
    db.execute("INSERT INTO packs(name,kind,root,created,n_files,bytes_in,clear_dir,clear_volumes,enc_dir,enc_volumes,disk_clear,disk_enc,gh_state) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", (
        name, kind, root, now(), n_files, bytes_in, rel_dir(clear), json.dumps(clear.volumes if clear else []), rel_dir(enc_vol),
        json.dumps(enc_vol.volumes if enc_vol else []), 0 if clear else -1, 0 if (disk and enc) else -1, "pending" if enc else "skipped"))


def build_pack(cfg, db, disk, root, kind, rows):
    name = f"{stamp()}-{kind}-{safe_name(root)}-{os.getpid()}-{kv_next(db)}"
    gz = kind != "rawz"
    ext = ".tar.gz" if gz else ".tar"
    clear, enc = sinks_for(cfg, disk, kind, root, name, ext)
    tee = Tee([s for s in (clear, enc) if s])
    out = gzip.GzipFile(fileobj=tee, mode="wb", compresslevel=3, mtime=0, filename="") if gz else tee
    tar = tarfile.open(fileobj=out, mode="w|", format=tarfile.PAX_FORMAT)
    stored = []
    base_of = {r["name"]: r for r in discover_roots(cfg)}
    if disk and root in base_of and base_of[root].get("skip_known"):
        base_of[root]["path"] = str(disk)
    seen = set()
    for row in rows:
        if row["sha"] in seen or db.execute("SELECT 1 FROM blobs WHERE sha=?", (row["sha"],)).fetchone():
            continue
        seen.add(row["sha"])
        full = source_path(base_of.get(root), row["rel"], disk)
        if not full:
            continue
        try:
            fh = open(full, "rb")
        except OSError as exc:
            log("read_error", root=root, rel=row["rel"], error=type(exc).__name__)
            continue
        with fh:
            info = tarfile.TarInfo(f"{safe_name(root)}/{row['rel']}")
            info.size, info.mtime, info.mode = row["size"], row["mtime_ns"] / 1e9, stat.S_IMODE(row["mode"])
            reader = HashingReader(fh, row["size"])
            tar.addfile(info, reader)
        if reader.short or reader.sha.hexdigest() != row["sha"]:
            # Changed between the scan and the read: forget it, the next pass sees the new version.
            db.execute("UPDATE files SET size=-1 WHERE root=? AND rel=?", (root, row["rel"]))
            continue
        stored.append((row["sha"], row["size"], info.name))
        beat()
    tar.close()
    if gz:
        out.close()
    for sink in (clear, enc):
        if sink:
            sink.close()
    db.execute("BEGIN")
    record_pack(db, name, kind, root, len(stored), sum(s[1] for s in stored), clear, enc, disk)
    db.executemany("INSERT OR REPLACE INTO blobs VALUES(?,?,?,?)", [(sha, size, name, member) for sha, size, member in stored])
    db.execute("COMMIT")
    log("pack", name=name, files=len(stored), bytes=sum(s[1] for s in stored))
    verify_disk_pack(cfg, db, disk, name)
    return name


def kv_next(db):
    value = kv_get(db, "seq", 0) + 1
    kv_set(db, "seq", value)
    return value


def source_path(root, rel, disk):
    if root is None:
        return None
    if root.get("files"):
        for pattern in root["files"]:
            for full in glob.glob(os.path.expanduser(pattern)):
                if os.path.basename(full) == rel:
                    return full
        return None
    if root.get("skip_known"):
        return str(disk / rel) if disk else None
    return os.path.join(root["path"], rel)


def snapshot_live_db(cfg, db, disk, root, row):
    """A consistent image of a database in use, read page by page inside one read transaction, so nothing blocks the writer."""
    base = {r["name"]: r for r in discover_roots(cfg)}[root]
    full = os.path.join(base["path"], row["rel"])
    gh_every = cfg.get("db_github_hours", 168) * 3600
    gh_due = now() - kv_get(db, f"dbgh:{root}:{row['rel']}", 0) >= gh_every
    name = f"{stamp()}-db-{safe_name(root)}-{os.getpid()}-{kv_next(db)}"
    clear, enc = sinks_for(cfg, disk, "raw", root, name, ".sqlite3.gz", encrypt=gh_due)
    out = gzip.GzipFile(fileobj=Tee([s for s in (clear, enc) if s]), mode="wb", compresslevel=3, mtime=0, filename="")
    proc = subprocess.Popen(["/usr/bin/sqlite3", "-readonly", "-batch", full, "SELECT hex(data) FROM sqlite_dbpage ORDER BY pgno;"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1 << 16)
    digest, size, count = hashlib.sha256(), 0, 0
    for line in proc.stdout:
        page = bytes.fromhex(line.strip())
        digest.update(page)
        out.write(page)
        size += len(page)
        count += 1
        if count % 25000 == 0:
            beat()
    err = proc.stderr.read()
    rc = proc.wait()
    out.close()
    for sink in (clear, enc):
        if sink:
            sink.close()
    if rc != 0 or size == 0:
        log("db_snapshot_failed", root=root, rel=row["rel"], rc=rc, error=err[:160])
        return None
    sha = digest.hexdigest()
    db.execute("BEGIN")
    record_pack(db, name, "db", root, 1, size, clear, enc, disk)
    db.execute("INSERT OR REPLACE INTO blobs VALUES(?,?,?,?)", (sha, size, name, "<sqlite pages>"))
    db.execute("UPDATE files SET sha=?, last_hashed=? WHERE root=? AND rel=?", (sha, now(), root, row["rel"]))
    db.execute("INSERT OR IGNORE INTO versions VALUES(?,?,?,?,?,?)", (root, row["rel"], sha, size, row["mtime_ns"], now()))
    db.execute("COMMIT")
    if gh_due:
        kv_set(db, f"dbgh:{root}:{row['rel']}", now())
        kv_set(db, f"dbghpack:{root}:{row['rel']}", name)
    log("db_snapshot", name=name, bytes=size, github=gh_due)
    verify_disk_pack(cfg, db, disk, name)
    return name


def pack_row_volumes(row, disk, which):
    folder = row["clear_dir"] if which == "clear" else row["enc_dir"]
    volumes = json.loads(row["clear_volumes"] if which == "clear" else row["enc_volumes"])
    base = Path(folder) if os.path.isabs(folder or "") else (disk / folder if disk and folder else None)
    return [(base / v["name"] if base else None, v) for v in volumes]


def members_of(db, name):
    return {r["member"]: r["sha"] for r in db.execute("SELECT member, sha FROM blobs WHERE pack=?", (name,))}


def check_members(stream, name, expected, gz):
    """Read a pack back and hash every member against what was recorded. Returns the number of problems."""
    source = gzip.GzipFile(fileobj=stream) if gz else stream
    if "<sqlite pages>" in expected:
        digest = hashlib.sha256()
        for chunk in iter(lambda: source.read(CHUNK), b""):
            digest.update(chunk)
        return 0 if digest.hexdigest() == expected["<sqlite pages>"] else 1
    bad, seen = 0, 0
    with tarfile.open(fileobj=source, mode="r|") as tar:
        for member in tar:
            if member.name not in expected:
                continue  # a member dropped because its source changed during the pack
            digest = hashlib.sha256()
            fh = tar.extractfile(member)
            for chunk in iter(lambda: fh.read(CHUNK), b""):
                digest.update(chunk)
            seen += 1
            if digest.hexdigest() != expected[member.name]:
                bad += 1
            beat()
    return bad + (len(expected) - seen)


def verify_disk_pack(cfg, db, disk, name):
    """Read back what was written. On failure the blobs are released, so the files go in another pack."""
    if not disk:
        return
    row = db.execute("SELECT * FROM packs WHERE name=?", (name,)).fetchone()
    ok = True
    for which in ("clear", "enc"):
        for path, volume in pack_row_volumes(row, disk, which):
            try:
                ok = ok and hash_file(path) == volume["sha"]
            except OSError:
                ok = False
    if ok and row["clear_volumes"] != "[]":
        reader = ConcatReader([p for p, _ in pack_row_volumes(row, disk, "clear")])
        gz = row["kind"] != "rawz"
        try:
            ok = check_members(reader, name, members_of(db, name), gz) == 0
        except (OSError, EOFError, tarfile.TarError) as exc:
            log("verify_error", pack=name, error=type(exc).__name__)
            ok = False
    if ok:
        db.execute("UPDATE packs SET disk_clear=CASE WHEN disk_clear=0 THEN 1 ELSE disk_clear END, disk_enc=CASE WHEN disk_enc=0 THEN 1 ELSE disk_enc END WHERE name=?", (name,))
    else:
        log("disk_verify_failed", pack=name)
        db.execute("BEGIN")
        db.execute("DELETE FROM blobs WHERE pack=?", (name,))
        db.execute("UPDATE packs SET disk_clear=-2, disk_enc=-2, gh_state='bad' WHERE name=?", (name,))
        db.execute("COMMIT")


def pending_groups(db):
    """Files with no stored bytes yet, grouped by root and kind."""
    groups = {}
    query = """SELECT f.root, f.rel, f.size, f.mtime_ns, f.mode, f.sha, f.klass, f.last_hashed FROM files f
               LEFT JOIN blobs b ON b.sha=f.sha WHERE f.gone_at IS NULL AND f.sha IS NOT NULL AND f.klass NOT IN ('link','live') AND f.size>=0 AND b.sha IS NULL ORDER BY f.root, f.rel"""
    for row in db.execute(query):
        groups.setdefault((row["root"], pack_kind(row)), []).append(row)
    return groups


def build_due_packs(cfg, db, disk):
    min_bytes, max_wait = cfg.get("pack_min_bytes", 200_000_000), cfg.get("pack_max_wait_s", 3600)
    order = {r["name"]: i for i, r in enumerate(discover_roots(cfg))}
    groups = sorted(pending_groups(db).items(), key=lambda kv: order.get(kv[0][0], 999))
    for (root, kind), rows in groups:
        total = sum(r["size"] for r in rows)
        oldest = min((r["last_hashed"] or 0) for r in rows)
        if total < min_bytes and now() - oldest < max_wait:
            continue
        if not disk:
            need = min(total, PACK_BYTES) + 2_000_000_000
            if free_bytes(STATE) - need < cfg.get("internal_floor_bytes", 13_500_000_000):
                log("queue_local", root=root, reason="no disk and no internal room")
                continue
        batch, size = [], 0
        for row in rows:
            if batch and size + row["size"] > PACK_BYTES:
                build_pack(cfg, db, disk, root, kind, batch)
                batch, size = [], 0
            batch.append(row)
            size += row["size"]
        if batch:
            build_pack(cfg, db, disk, root, kind, batch)


def snapshot_due_dbs(cfg, db, disk):
    if not disk:
        return  # shortcut: a database image is too large for the internal disk, it waits for the external one
    every = cfg.get("db_snapshot_hours", 24) * 3600
    for row in db.execute("SELECT * FROM files WHERE klass='live' AND gone_at IS NULL").fetchall():
        last = kv_get(db, f"dbmtime:{row['root']}:{row['rel']}")
        if now() - (row["last_hashed"] or 0) >= every and last != row["mtime_ns"]:
            if snapshot_live_db(cfg, db, disk, row["root"], row):
                kv_set(db, f"dbmtime:{row['root']}:{row['rel']}", row["mtime_ns"])


def sync_git_bundles(cfg, disk):
    """Local history that exists nowhere else: repositories with no remote, or commits not pushed."""
    out = STATE / "bundles"
    out.mkdir(parents=True, exist_ok=True)
    for root in discover_roots(cfg):
        path = root.get("path")
        if not path or root.get("no_bundle") or not is_git_with_commits(path):
            continue
        has_remote = bool(subprocess.run(["git", "-C", path, "remote"], capture_output=True, text=True).stdout.strip())
        refs = subprocess.run(["git", "-C", path, "for-each-ref", "--format=%(objectname) %(refname)"], capture_output=True, text=True).stdout
        digest = hashlib.sha256(refs.encode()).hexdigest()[:16]
        target = out / f"{safe_name(root['name'])}.bundle"
        marker = out / f"{safe_name(root['name'])}.refs"
        if marker.exists() and marker.read_text() == digest and (target.exists() or has_remote):
            continue
        args = ["--branches", "--tags", "--not", "--remotes=origin"] if has_remote else ["--all"]
        tmp = out / (target.name + ".tmp")
        result = subprocess.run(["git", "-C", path, "bundle", "create", str(tmp)] + args, capture_output=True, text=True)
        if result.returncode == 0 and tmp.exists():
            os.replace(tmp, target)
            if disk:
                shutil.copyfile(target, disk / "git-backups" / f"{safe_name(root['name'])}-{digest}.bundle")
        marker.write_text(digest)


def known_disk_paths(db):
    """Everything the system itself wrote on the disk. Anything else there is a file only the disk has."""
    known = set()
    for row in db.execute("SELECT clear_dir, clear_volumes, enc_dir, enc_volumes FROM packs"):
        for folder, volumes in ((row["clear_dir"], row["clear_volumes"]), (row["enc_dir"], row["enc_volumes"])):
            for volume in json.loads(volumes or "[]"):
                if folder and not os.path.isabs(folder):
                    known.add(f"{folder}/{volume['name']}")
    known.update(r["rel"] for r in db.execute("SELECT rel FROM exports"))
    return known


def outbox_to_disk(cfg, db, disk):
    """The disk came back: copy what waited in the outbox, then rebuild its clear copy from the encrypted one."""
    for row in db.execute("SELECT * FROM packs WHERE disk_enc=-1 AND enc_volumes!='[]' AND enc_dir LIKE '/%'").fetchall():
        target = disk / "archives" / time.strftime("%Y-%m", time.gmtime(row["created"]))
        target.mkdir(parents=True, exist_ok=True)
        volumes = json.loads(row["enc_volumes"])
        for volume in volumes:
            source = Path(row["enc_dir"]) / volume["name"]
            if not source.exists():
                break
            tmp = target / (volume["name"] + ".tmp")
            shutil.copyfile(source, tmp)
            if hash_file(tmp) != volume["sha"]:
                log("outbox_copy_bad", pack=row["name"])
                break
            os.replace(tmp, target / volume["name"])
        else:
            db.execute("UPDATE packs SET disk_enc=1, enc_dir=? WHERE name=?", (str(target.relative_to(disk)), row["name"]))
            restore_clear_from_enc(cfg, db, disk, row["name"])
            for volume in volumes:
                (Path(row["enc_dir"]) / volume["name"]).unlink(missing_ok=True)
            log("outbox_flushed", pack=row["name"])


def restore_clear_from_enc(cfg, db, disk, name):
    row = db.execute("SELECT * FROM packs WHERE name=?", (name,)).fetchone()
    if row["kind"] in ("secret", "disk") or not os.path.exists(os.path.expanduser(cfg["identity"])):
        db.execute("UPDATE packs SET disk_clear=-1 WHERE name=?", (name,))
        return
    sub = "projects" if row["kind"] == "project" else "raw-data"
    ext = name_ext(row["kind"])
    writer = VolumeWriter(disk / sub / safe_name(row["root"]) / (name + ext))
    proc = subprocess.Popen([cfg["age_bin"], "-d", "-i", os.path.expanduser(cfg["identity"])], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    feeder = threading.Thread(target=feed, args=(ConcatReader([p for p, _ in pack_row_volumes(row, disk, "enc")]), proc.stdin), daemon=True)
    feeder.start()
    for chunk in iter(lambda: proc.stdout.read(CHUNK), b""):
        writer.write(chunk)
    writer.close()
    feeder.join()
    proc.wait()
    db.execute("UPDATE packs SET clear_dir=?, clear_volumes=?, disk_clear=0 WHERE name=?", (str(writer.base.parent.relative_to(disk)), json.dumps(writer.volumes), name))
    verify_disk_pack(cfg, db, disk, name)


def name_ext(kind):
    return ".sqlite3.gz" if kind == "db" else (".tar" if kind == "rawz" else ".tar.gz")


def feed(reader, sink):
    try:
        for chunk in iter(lambda: reader.read(CHUNK), b""):
            sink.write(chunk)
    except OSError:
        pass
    finally:
        sink.close()


# ---------------------------------------------------------------- GitHub

class GitHub:
    """Releases over the REST API. The token never appears in a command line or in a log."""

    def __init__(self, cfg):
        self.cfg, self.repo = cfg, cfg["repo"]

    def token(self):
        return subprocess.run([self.cfg["gh_bin"], "auth", "token"], capture_output=True, text=True, timeout=30, check=True).stdout.strip()

    def _curl(self, args, stream=False):
        config = f'header = "Authorization: Bearer {self.token()}"\nheader = "X-GitHub-Api-Version: 2022-11-28"\n'
        cmd = ["/usr/bin/curl", "-sS", "-K", "-"] + args
        if stream:
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            proc.stdin.write(config.encode())
            proc.stdin.close()
            return proc
        return subprocess.run(cmd, input=config.encode(), capture_output=True)

    def api(self, method, path, body=None):
        args = ["-X", method, "-H", "Accept: application/vnd.github+json", f"https://api.github.com/repos/{self.repo}{path}"]
        if body is not None:
            args += ["-H", "Content-Type: application/json", "-d", json.dumps(body)]
        result = self._curl(args)
        try:
            return json.loads(result.stdout or b"null")
        except ValueError:
            return None

    def release_for(self, db):
        """Monthly release, rolled over before the limit of 1000 assets."""
        month = time.strftime("%Y-%m", time.gmtime())
        n = kv_get(db, f"rel:{month}", 1)
        while True:
            tag = f"backup-{month}-{n:02d}"
            release = self.api("GET", f"/releases/tags/{tag}")
            if not release or "id" not in release:
                release = self.api("POST", "/releases", {"tag_name": tag, "name": f"Encrypted backup {tag}", "prerelease": True,
                                                         "body": "Encrypted research archives. See BACKUP_STATUS.md and manifests."})
            if not release or "id" not in release:
                raise OSError("cannot create release")
            if len(release.get("assets", [])) < 900:
                kv_set(db, f"rel:{month}", n)
                return release
            n += 1

    def assets(self, release_id):
        out, page = [], 1
        while True:
            batch = self.api("GET", f"/releases/{release_id}/assets?per_page=100&page={page}") or []
            out += batch
            if len(batch) < 100:
                return out
            page += 1

    def upload(self, release_id, path, name):
        rate = str(self.cfg.get("upload_limit_bytes_per_s", 4_000_000))
        result = self._curl(["--fail-with-body", "-X", "POST", "--limit-rate", rate, "-H", "Content-Type: application/octet-stream", "-T", str(path), "-o", "-",
                             f"https://uploads.github.com/repos/{self.repo}/releases/{release_id}/assets?name={name}"])
        if result.returncode != 0:
            raise OSError(f"upload failed, curl {result.returncode}")
        return json.loads(result.stdout)

    def delete_asset(self, asset_id):
        self.api("DELETE", f"/releases/assets/{asset_id}")

    def open_asset(self, asset_id):
        return self._curl(["-L", "-H", "Accept: application/octet-stream", "--limit-rate", str(self.cfg.get("download_limit_bytes_per_s", 8_000_000)),
                           f"https://api.github.com/repos/{self.repo}/releases/assets/{asset_id}"], stream=True)


class DirBackend:
    """Test double with the same methods, backed by a folder."""

    def __init__(self, cfg):
        self.root = Path(cfg["github_test_dir"])
        self.root.mkdir(parents=True, exist_ok=True)

    def release_for(self, db):
        return {"id": 1, "tag_name": "backup-test"}

    def api(self, method, path, body=None):
        return {"id": 1, "tag_name": "backup-test"}

    def assets(self, release_id):
        return [{"id": str(p), "name": p.name, "size": p.stat().st_size, "state": "uploaded"} for p in sorted(self.root.iterdir())]

    def upload(self, release_id, path, name):
        target = self.root / name
        shutil.copyfile(path, target)
        return {"id": str(target), "name": name, "size": target.stat().st_size, "state": "uploaded"}

    def delete_asset(self, asset_id):
        Path(asset_id).unlink()

    def open_asset(self, asset_id):
        return subprocess.Popen(["/bin/cat", asset_id], stdout=subprocess.PIPE)


def backend(cfg):
    return DirBackend(cfg) if cfg.get("github_test_dir") else GitHub(cfg)


def verify_github_pack(cfg, db, gh, row, assets):
    """Download what GitHub really holds: hash each volume, decrypt, and hash every member."""
    identity = os.path.expanduser(cfg["identity"])
    volumes = json.loads(row["enc_volumes"])
    proc = subprocess.Popen([cfg["age_bin"], "-d", "-i", identity], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    errors = []

    def pump():
        try:
            for volume in volumes:
                dl = gh.open_asset(assets[volume["name"]]["id"])
                digest = hashlib.sha256()
                for chunk in iter(lambda: dl.stdout.read(CHUNK), b""):
                    digest.update(chunk)
                    proc.stdin.write(chunk)
                dl.wait()
                if digest.hexdigest() != volume["sha"]:
                    errors.append("hash of " + volume["name"])
        except OSError as exc:
            errors.append(type(exc).__name__)
        finally:
            proc.stdin.close()

    thread = threading.Thread(target=pump, daemon=True)
    thread.start()
    bad = check_members(proc.stdout, row["name"], members_of(db, row["name"]), row["kind"] != "rawz")
    # Drain whatever follows the end of the tar stream, or age and the pump would block.
    for _ in iter(lambda: proc.stdout.read(CHUNK), b""):
        pass
    thread.join()
    rc = proc.wait()
    return not errors and rc == 0 and bad == 0, (errors or ([f"{bad} members"] if bad else []) or ([f"age {rc}"] if rc else []))


def upload_pending(cfg, db, disk):
    gh = backend(cfg)
    rows = db.execute("SELECT * FROM packs WHERE gh_state IN ('pending','uploaded') AND next_try<=? ORDER BY created", (now(),)).fetchall()
    for row in rows:
        beat()
        try:
            local = {v["name"]: p for p, v in pack_row_volumes(row, disk, "enc")}
            if any(p is None or not p.exists() for p in local.values()):
                continue  # on the disk, which is away: try again when it returns
            release = gh.release_for(db) if not row["gh_tag"] else gh.api("GET", f"/releases/tags/{row['gh_tag']}")
            assets = {a["name"]: a for a in gh.assets(release["id"])}
            for volume in json.loads(row["enc_volumes"]):
                asset = assets.get(volume["name"])
                if asset and (asset.get("state") != "uploaded" or asset.get("size") != volume["size"]):
                    gh.delete_asset(asset["id"])  # an interrupted upload, not a copy
                    asset = None
                if not asset:
                    assets[volume["name"]] = gh.upload(release["id"], local[volume["name"]], volume["name"])
                    beat()
            db.execute("UPDATE packs SET gh_state='uploaded', gh_tag=?, gh_assets=? WHERE name=?", (release.get("tag_name"), json.dumps({v["name"]: assets[v["name"]]["id"] for v in json.loads(row["enc_volumes"])}), row["name"]))
            ok, problems = verify_github_pack(cfg, db, gh, row, assets)
            if not ok:
                raise OSError("verification: " + ", ".join(problems))
            db.execute("UPDATE packs SET gh_state='verified', verified_at=?, last_error=NULL, tries=0 WHERE name=?", (now(), row["name"]))
            log("github_verified", pack=row["name"])
        except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError, tarfile.TarError, EOFError) as exc:
            tries = (row["tries"] or 0) + 1
            db.execute("UPDATE packs SET tries=?, next_try=?, last_error=? WHERE name=?", (tries, now() + min(21600, 60 * 2 ** tries), f"{type(exc).__name__}: {str(exc)[:160]}", row["name"]))
            log("github_error", pack=row["name"], tries=tries, error=f"{type(exc).__name__}: {str(exc)[:160]}")


# ---------------------------------------------------------------- manifests, status

def write_index(cfg, db, disk):
    """The restore needs only this: every file with its hash and its pack, plus every pack with its volumes."""
    STATE.mkdir(parents=True, exist_ok=True)
    tmp = STATE / "index.jsonl.gz"
    query = """SELECT f.root,f.rel,f.size,f.mtime_ns,f.mode,f.sha,f.klass,f.link,f.gone_at,b.pack,b.member FROM files f LEFT JOIN blobs b ON b.sha=f.sha"""
    with gzip.open(tmp, "wt") as fh:
        for row in db.execute(query):
            fh.write(json.dumps(dict(row)) + "\n")
    packs = [dict(r) for r in db.execute("SELECT name,kind,root,created,n_files,bytes_in,clear_dir,clear_volumes,enc_dir,enc_volumes,disk_clear,disk_enc,gh_state,gh_tag,gh_assets,verified_at FROM packs")]
    (STATE / "packs.json").write_text(json.dumps(packs))
    if disk:
        shutil.copyfile(tmp, disk / "manifests" / "index-latest.jsonl.gz")
        shutil.copyfile(STATE / "packs.json", disk / "manifests" / "packs-latest.json")
        (disk / "manifests" / "disk.json").write_text(json.dumps({"uuid": cfg.get("disk_uuid"), "written": iso(now())}))
        day = time.strftime("%Y-%m-%d", time.gmtime())
        history = disk / "manifests" / f"index-{day}.jsonl.gz"
        if not history.exists():
            shutil.copyfile(tmp, history)
        if (STATE / "events.jsonl").exists():
            shutil.copyfile(STATE / "events.jsonl", disk / "sync-logs" / f"events-{day}.jsonl")
    return tmp


def backup_counts(db):
    query = """SELECT f.root AS root, COUNT(*) AS n, SUM(CASE WHEN f.size>0 THEN f.size ELSE 0 END) AS bytes,
       SUM(CASE WHEN p.disk_clear=1 OR p.disk_enc=1 THEN 1 ELSE 0 END) AS disk_n, SUM(CASE WHEN p.disk_clear=1 OR p.disk_enc=1 THEN f.size ELSE 0 END) AS disk_b,
       SUM(CASE WHEN p.gh_state='verified' THEN 1 ELSE 0 END) AS gh_n, SUM(CASE WHEN p.gh_state='verified' THEN f.size ELSE 0 END) AS gh_b,
       SUM(CASE WHEN b.sha IS NULL THEN 1 ELSE 0 END) AS no_pack,
       MAX(p.verified_at) AS last_gh, MAX(p.created) AS last_pack
       FROM files f LEFT JOIN blobs b ON b.sha=f.sha LEFT JOIN packs p ON p.name=b.pack
       WHERE f.gone_at IS NULL AND f.klass!='link' GROUP BY f.root"""
    return {r["root"]: dict(r) for r in db.execute(query)}


def gb(n):
    return f"{(n or 0) / 1e9:,.2f} GB"


def build_status(cfg, db, disk):
    counts = backup_counts(db)
    roots = discover_roots(cfg)
    invest = {v["root"]: k for k, v in cfg.get("investigations", {}).items()}
    t = {k: sum((c.get(k) or 0) for c in counts.values()) for k in ("n", "bytes", "disk_n", "disk_b", "gh_n", "gh_b", "no_pack")}
    both = db.execute("""SELECT COUNT(*) FROM files f JOIN blobs b ON b.sha=f.sha JOIN packs p ON p.name=b.pack
                         WHERE f.gone_at IS NULL AND f.klass!='link' AND p.gh_state='verified' AND (p.disk_clear=1 OR p.disk_enc=1)""").fetchone()[0]
    limit = cfg.get("db_github_hours", 168) * 3600 * 1.3
    for row in db.execute("SELECT f.root, f.rel, p.gh_state FROM files f JOIN blobs b ON b.sha=f.sha JOIN packs p ON p.name=b.pack WHERE f.klass='live' AND f.gone_at IS NULL AND p.gh_state='skipped' AND (p.disk_clear=1 OR p.disk_enc=1)").fetchall():
        pack = db.execute("SELECT gh_state, verified_at FROM packs WHERE name=?", (kv_get(db, f"dbghpack:{row['root']}:{row['rel']}", ""),)).fetchone()
        if pack and pack["gh_state"] == "verified" and now() - pack["verified_at"] < limit:
            both += 1
    missing_two = t["n"] - both
    unstable = sum((kv_get(db, f"scan:{r['name']}", {}) or {}).get("unstable", 0) for r in roots)
    failures = db.execute("SELECT COUNT(*) FROM packs WHERE last_error IS NOT NULL").fetchone()[0]
    missing = kv_get(db, "missing", {"count": 0, "by_root": {}})
    out = ["<!-- Generated by phi_backup.py. Do not edit by hand. -->\n", "# Backup status\n", f"Written {iso(now())}. Disk: {'connected, UUID checked' if disk else 'NOT CONNECTED'}.\n"]
    verdict = "All current files have two verified copies." if missing_two == 0 and t["n"] else f"NOT COMPLETE: {missing_two:,} of {t['n']:,} current files do not yet have two verified copies."
    out.append(f"**{verdict}**\n")
    out.append(f"- Found: {t['n']:,} files, {gb(t['bytes'])}\n- Verified on the disk: {t['disk_n']:,} files, {gb(t['disk_b'])}\n- Verified on GitHub by download and decryption: {t['gh_n']:,} files, {gb(t['gh_b'])}\n- Not yet in a pack: {t['no_pack']:,}\n- Still changing, waiting to settle: {unstable:,}\n- Listed in a repository manifest but gone from the source (MISSING, no copy claimed): {missing.get('count', 0):,}\n- Packs with an error being retried: {failures}\n")
    out.append("| Source | Investigation | Files | Size | On disk | On GitHub | Waiting | Missing | Last pack | Last GitHub check |\n|---|---|---:|---:|---:|---:|---:|---:|---|---|")
    for root in roots:
        c = counts.get(root["name"], {})
        waiting = (c.get("n") or 0) - (c.get("gh_n") or 0)
        out.append(f"| `{root['name']}` | {invest.get(root['name'], '')} | {c.get('n', 0) or 0:,} | {gb(c.get('bytes'))} | {c.get('disk_n', 0) or 0:,} | {c.get('gh_n', 0) or 0:,} | {waiting:,} | {missing.get('by_root', {}).get(root['name'], 0):,} | {iso(c.get('last_pack'))} | {iso(c.get('last_gh'))} |")
    out.append("")
    errors = db.execute("SELECT name,last_error,tries FROM packs WHERE last_error IS NOT NULL ORDER BY created DESC LIMIT 20").fetchall()
    if errors:
        out.append("## Errors being retried\n")
        out += [f"- `{e['name']}`, try {e['tries']}: {e['last_error']}" for e in errors]
        out.append("")
    holds = kv_get(db, "holds", {})
    if holds:
        out.append("## Waiting for central review\n")
        out += [f"- {k}: {v}" for k, v in holds.items()]
        out.append("")
    pending = kv_get(db, "pending_registry", [])
    if pending:
        out.append("## Investigations still running\n")
        out.append("| Investigation | State | Reports present | Last change in source |\n|---|---|---:|---|")
        out += [f"| `{p['id']}` | {p['state']} | {p['reports']} | {iso(p['last_change'])} |" for p in pending]
        out.append("")
    text = "\n".join(out)
    (STATE / "BACKUP_STATUS.md").write_text(text)
    rows = "".join("<tr>" + "".join(f"<td>{html.escape(cell.strip())}</td>" for cell in line.strip("|").split("|")) + "</tr>" for line in out if line.startswith("| ") and not line.startswith("|---"))
    (STATE / "dashboard.html").write_text(f"<!doctype html><meta charset=utf-8><title>Backup status</title><style>body{{font:14px system-ui;margin:2em}}td{{border:1px solid #ccc;padding:3px 7px}}table{{border-collapse:collapse}}</style><h1>Backup status</h1><p>{html.escape(verdict)}</p><p>Written {iso(now())}</p><table>{rows}</table>")
    if disk:
        shutil.copyfile(STATE / "BACKUP_STATUS.md", disk / "manifests" / "BACKUP_STATUS.md")
        shutil.copyfile(STATE / "dashboard.html", disk / "manifests" / "dashboard.html")
    return text


# ---------------------------------------------------------------- restore

def restore(args, cfg=None):
    """Rebuild files from the index alone, so that it also works on another machine without the state database."""
    disk = Path(args.disk) if getattr(args, "disk", None) else (disk_root(cfg) if cfg else None)
    manifests = Path(args.manifests) if getattr(args, "manifests", None) else (disk / "manifests" if disk else STATE)
    index = manifests / ("index-latest.jsonl.gz" if (manifests / "index-latest.jsonl.gz").exists() else "index.jsonl.gz")
    packs_file = manifests / ("packs-latest.json" if (manifests / "packs-latest.json").exists() else "packs.json")
    packs = {p["name"]: p for p in json.loads(packs_file.read_text())}
    dest = Path(args.dest)
    wanted, links = {}, []
    with gzip.open(index, "rt") as fh:
        for line in fh:
            row = json.loads(line)
            if args.root and row["root"] != args.root:
                continue
            if row.get("gone_at") and not getattr(args, "include_gone", False):
                continue
            if row["klass"] == "link" and row.get("link"):
                links.append(row)
            elif row.get("pack"):
                wanted.setdefault(row["pack"], {}).setdefault(row["member"], []).append(row)
    done = bad = 0
    identity = os.path.expanduser(args.identity) if getattr(args, "identity", None) else None
    for name, members in sorted(wanted.items()):
        stream, cleanup = open_for_restore(args.source, packs[name], disk, identity, cfg)
        if stream is None:
            print(f"UNAVAILABLE {name}")
            bad += sum(len(v) for v in members.values())
            continue
        kind = packs[name]["kind"]
        source = gzip.GzipFile(fileobj=stream) if kind != "rawz" else stream
        if "<sqlite pages>" in members:
            done_here, bad_here = restore_stream(source, members["<sqlite pages>"], dest)
            done, bad = done + done_here, bad + bad_here
        else:
            with tarfile.open(fileobj=source, mode="r|") as tar:
                for member in tar:
                    rows = members.get(member.name)
                    if rows:
                        done_here, bad_here = restore_stream(tar.extractfile(member), rows, dest)
                        done, bad = done + done_here, bad + bad_here
        cleanup()
    for row in links:
        target = dest / row["root"] / row["rel"]
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.is_symlink() and not target.exists():
            os.symlink(row["link"], target)
    print(f"restored {done} files, {bad} problems, {len(links)} links")
    return bad


def restore_stream(stream, rows, dest):
    first = dest / rows[0]["root"] / rows[0]["rel"]
    first.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    with open(first, "wb") as out:
        for chunk in iter(lambda: stream.read(CHUNK), b""):
            digest.update(chunk)
            out.write(chunk)
    if digest.hexdigest() != rows[0]["sha"]:
        print(f"HASH MISMATCH {rows[0]['root']}/{rows[0]['rel']}")
        return 0, len(rows)
    for row in rows[1:]:
        target = dest / row["root"] / row["rel"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(first, target)
    for row in rows:
        target = dest / row["root"] / row["rel"]
        os.chmod(target, stat.S_IMODE(row["mode"]) | 0o600)
        os.utime(target, ns=(row["mtime_ns"], row["mtime_ns"]))
    return len(rows), 0


def open_for_restore(source, pack, disk, identity, cfg):
    def nothing():
        return None
    clear = json.loads(pack["clear_volumes"] or "[]")
    if source == "disk" and clear and pack["clear_dir"] and disk:
        paths = [disk / pack["clear_dir"] / v["name"] for v in clear]
        if all(p.exists() for p in paths):
            return ConcatReader(paths), nothing
    if not identity or not os.path.exists(identity):
        return None, nothing
    enc = json.loads(pack["enc_volumes"] or "[]")
    if not enc:
        return None, nothing
    age = (cfg or {}).get("age_bin") or shutil.which("age") or ""
    proc = subprocess.Popen([age, "-d", "-i", identity], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    if source == "disk":
        paths = [disk / pack["enc_dir"] / v["name"] for v in enc]
        if not all(p.exists() for p in paths):
            return None, nothing
        threading.Thread(target=feed, args=(ConcatReader(paths), proc.stdin), daemon=True).start()
    else:
        gh = backend(cfg)
        ids = json.loads(pack["gh_assets"] or "{}")

        def pump():
            for volume in enc:
                dl = gh.open_asset(ids[volume["name"]])
                for chunk in iter(lambda: dl.stdout.read(CHUNK), b""):
                    proc.stdin.write(chunk)
                dl.wait()
            proc.stdin.close()
        threading.Thread(target=pump, daemon=True).start()

    def finish():
        for _ in iter(lambda: proc.stdout.read(CHUNK), b""):
            pass
        proc.wait()
    return proc.stdout, finish


# ---------------------------------------------------------------- passes

def write_recovery(cfg, disk):
    here = Path(__file__).resolve().parent
    for name in ("phi_backup.py", "phi_lib.py", "restore_all.sh", "RECOVERY.md"):
        if (here / name).exists():
            shutil.copyfile(here / name, disk / "recovery" / name)
    if cfg.get("age_bin") and os.path.exists(cfg["age_bin"]):
        shutil.copyfile(os.path.realpath(cfg["age_bin"]), disk / "recovery" / "age-darwin-arm64")
    (disk / "recovery" / "public-config.json").write_text(json.dumps({"repo": cfg["repo"], "recipient": cfg["recipient"], "disk_uuid": cfg.get("disk_uuid")}, indent=1))


def refresh_outputs(cfg, db, disk):
    """A new index when packs changed, or every 10 minutes: not on each 60-second pass."""
    signature = list(db.execute("SELECT COUNT(*), SUM(gh_state='verified'), SUM(disk_clear=1) FROM packs").fetchone())
    if signature == kv_get(db, "outputs_sig") and now() - kv_get(db, "outputs_at", 0) < 600:
        return
    write_index(cfg, db, disk)
    build_status(cfg, db, disk)
    kv_set(db, "outputs_sig", signature)
    kv_set(db, "outputs_at", now())


def pass_backup(cfg):
    db = open_db()
    if on_low_battery():
        log("skip", reason="low battery")
        return
    disk = disk_root(cfg)
    if disk:
        write_recovery(cfg, disk)
    sync_git_bundles(cfg, disk)
    for root in discover_roots(cfg):
        if root.get("skip_known"):
            if not disk:
                continue
            root["path"] = str(disk)
        elif root.get("path") and not os.path.exists(root["path"]):
            continue
        try:
            scan_root(cfg, db, root, disk)
        except OSError as exc:
            log("scan_error", root=root["name"], error=type(exc).__name__)
    if disk:
        outbox_to_disk(cfg, db, disk)
        snapshot_due_dbs(cfg, db, disk)
    build_due_packs(cfg, db, disk)
    refresh_outputs(cfg, db, disk)
    kv_set(db, "last_backup", now())


def pass_upload(cfg):
    db = open_db()
    if on_low_battery():
        return
    disk = disk_root(cfg)
    upload_pending(cfg, db, disk)
    refresh_outputs(cfg, db, disk)
    upload_index(cfg, db, disk)


def upload_index(cfg, db, disk):
    """The encrypted index goes up too, otherwise GitHub alone could not rebuild anything. At most once a day."""
    last = kv_get(db, "index_uploaded", 0)
    if now() - last < cfg.get("index_upload_hours", 24) * 3600 or not (STATE / "index.jsonl.gz").exists():
        return
    gh = backend(cfg)
    name = f"index-{stamp()}.tar.age"
    tmp = STATE / name
    proc = subprocess.Popen([cfg["age_bin"], "-r", cfg["recipient"], "-o", str(tmp)], stdin=subprocess.PIPE)
    with tarfile.open(fileobj=proc.stdin, mode="w|") as tar:
        tar.add(STATE / "index.jsonl.gz", arcname="index-latest.jsonl.gz")
        tar.add(STATE / "packs.json", arcname="packs-latest.json")
    proc.stdin.close()
    proc.wait()
    try:
        gh.upload(gh.release_for(db)["id"], tmp, name)
        kv_set(db, "index_uploaded", now())
        log("index_uploaded", name=name)
    except (OSError, ValueError) as exc:
        log("index_upload_error", error=type(exc).__name__)
    finally:
        if tmp.exists():
            tmp.unlink()


def run_locked(which, func, cfg, limit_s):
    """launchd entry: one pass at a time, and a stuck pass is killed. Nothing is lost, the state is in the database."""
    STATE.mkdir(parents=True, exist_ok=True)
    lock = open(STATE / f"{which}.lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return 0
    pid = os.fork()
    if pid == 0:
        try:
            func(cfg)
        except Exception as exc:  # the pass fails, the service does not; launchd runs it again
            log("pass_failed", which=which, error=f"{type(exc).__name__}: {str(exc)[:200]}")
            os._exit(1)
        os._exit(0)
    beat_file = STATE / f"heartbeat.{pid}"
    started = now()
    try:
        while True:
            done, status = os.waitpid(pid, os.WNOHANG)
            if done:
                return os.waitstatus_to_exitcode(status) if hasattr(os, "waitstatus_to_exitcode") else status
            last = beat_file.stat().st_mtime if beat_file.exists() else started
            if now() - last > limit_s:
                log("watchdog_kill", which=which)
                os.kill(pid, signal.SIGKILL)
            time.sleep(5)
    finally:
        if beat_file.exists():
            beat_file.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run")
    run.add_argument("which", choices=["backup", "upload", "repo"])
    sub.add_parser("status")
    res = sub.add_parser("restore")
    res.add_argument("--source", choices=["disk", "github"], default="disk")
    res.add_argument("--dest", required=True)
    res.add_argument("--root")
    res.add_argument("--identity")
    res.add_argument("--disk")
    res.add_argument("--manifests")
    args = parser.parse_args()
    if args.cmd == "restore":
        cfg = load_config() if CONFIG.exists() else None
        if not args.identity and cfg:
            args.identity = cfg.get("identity")
        return 1 if restore(args, cfg) else 0
    cfg = load_config()
    if args.cmd == "status":
        print(build_status(cfg, open_db(), disk_root(cfg)))
        return 0
    if args.which == "repo":
        import phi_repo
        return run_locked("repo", phi_repo.pass_repo, cfg, 3600)
    return run_locked(args.which, pass_backup if args.which == "backup" else pass_upload, cfg, 3600)


if __name__ == "__main__":
    sys.exit(main())
