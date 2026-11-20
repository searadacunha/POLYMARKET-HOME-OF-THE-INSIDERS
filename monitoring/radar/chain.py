"""Append-only JSON lines, each carrying the SHA-256 of the previous line, as `phi_engine` writes `<db>.alerts.jsonl`.

A line is never rewritten. `verify` recomputes the chain; any edit, deletion or reordering breaks it at that line.
The head hash can be published elsewhere (a commit, a post) to prove that every earlier line existed at that time."""
import fcntl, hashlib, json, os

ZERO = "0" * 64


def read(path):
    """[(line_bytes, object)] in file order; a missing file is an empty chain."""
    if not os.path.exists(path):
        return []
    with open(path, "rb") as f:
        return [(l, json.loads(l)) for l in f.read().splitlines() if l.strip()]


def head(path):
    rows = read(path)
    return hashlib.sha256(rows[-1][0]).hexdigest() if rows else ZERO


def append(path, obj):
    """Append one object; returns the SHA-256 of the written line. A lock keeps two writers from interleaving."""
    with open(path + ".lock", "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        line = json.dumps(dict(obj, previous_line_sha256=head(path)), sort_keys=True).encode()
        with open(path, "ab") as f:
            f.write(line + b"\n"); f.flush(); os.fsync(f.fileno())
        return hashlib.sha256(line).hexdigest()


def verify(path):
    """(number of lines, head hash, list of errors). An empty list of errors means the chain is intact."""
    prev, errors, rows = ZERO, [], read(path)
    for i, (line, obj) in enumerate(rows, 1):
        if obj.get("previous_line_sha256") != prev:
            errors.append(f"line {i}: previous_line_sha256 does not match line {i - 1}")
        prev = hashlib.sha256(line).hexdigest()
    return len(rows), prev, errors
