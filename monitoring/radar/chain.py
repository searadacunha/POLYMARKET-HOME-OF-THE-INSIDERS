"""Append-only JSON lines, each carrying the SHA-256 of the previous line, as `phi_engine` writes `<db>.alerts.jsonl`.

What the chain proves: the order of the lines and that no line BEFORE a known head was changed. It cannot, alone, tell
that the last lines were edited, dropped or that the whole file was rewritten: that needs a head published earlier.
`anchor` writes each head it is asked for to `<file>.anchors.jsonl`; `verify` checks every recorded anchor, so a change to
any line up to the last anchor, or a truncation below it, is found. Publish anchors elsewhere to prove a date."""
import contextlib, fcntl, hashlib, json, os, time

ZERO = "0" * 64


def _lines(path):
    if not os.path.exists(path):
        return [], True
    with open(path, "rb") as f:
        data = f.read()
    return data.split(b"\n")[:-1] if data.endswith(b"\n") else data.split(b"\n"), data.endswith(b"\n") or not data


def read(path, partial_tail_ok=False):
    """[(line_bytes, object)] in file order. A last line without its newline is a write in progress: dropped when
    partial_tail_ok (reading another program's file), an error otherwise. A blank line is an error."""
    lines, complete = _lines(path)
    if not complete:
        if not partial_tail_ok:
            raise ValueError(f"{path}: last line has no newline")
        lines = lines[:-1]
    out = []
    for i, l in enumerate(lines, 1):
        if not l.strip():
            raise ValueError(f"{path}: line {i} is blank")
        out.append((l, json.loads(l)))
    return out


def head(path):
    rows = read(path)
    return hashlib.sha256(rows[-1][0]).hexdigest() if rows else ZERO


@contextlib.contextmanager
def lock(path):
    """One writer at a time for a whole read-then-append pass (flock on <path>.lock)."""
    with open(path + ".lock", "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        yield


def append_locked(path, obj):
    """Append one object; the caller holds lock(path). NaN and infinities are refused. Returns the line's SHA-256."""
    line = json.dumps(dict(obj, previous_line_sha256=head(path)), sort_keys=True, allow_nan=False).encode()
    with open(path, "ab") as f:
        f.write(line + b"\n"); f.flush(); os.fsync(f.fileno())
    return hashlib.sha256(line).hexdigest()


def append(path, obj):
    with lock(path):
        return append_locked(path, obj)


def anchor(path, now=time.time):
    """Record the current head and line count in <path>.anchors.jsonl (itself chained). Returns the anchor."""
    with lock(path):
        rows = read(path)
        a = {"lines": len(rows), "head_sha256": hashlib.sha256(rows[-1][0]).hexdigest() if rows else ZERO,
             "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now()))}
    append(path + ".anchors.jsonl", a)
    return a


def verify(path):
    """(number of lines, head hash, list of errors). An empty list means the chain is intact up to its last line and
    agrees with every anchor recorded for it."""
    errors = []
    try:
        rows = read(path)
    except ValueError as e:
        return 0, ZERO, [str(e)]
    prev, hashes = ZERO, []
    for i, (line, obj) in enumerate(rows, 1):
        if obj.get("previous_line_sha256") != prev:
            errors.append(f"line {i}: previous_line_sha256 does not match line {i - 1}")
        prev = hashlib.sha256(line).hexdigest(); hashes.append(prev)
    try:
        anchors = read(path + ".anchors.jsonl")
    except ValueError as e:
        anchors = []; errors.append(f"anchors: {e}")
    for _, a in anchors:
        n = a.get("lines", 0)
        if n > len(rows):
            errors.append(f"anchor of {a.get('utc')}: {n} lines then, {len(rows)} now")
        elif n and hashes[n - 1] != a.get("head_sha256"):
            errors.append(f"anchor of {a.get('utc')}: line {n} changed since")
    return len(rows), prev, errors
