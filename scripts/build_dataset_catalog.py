#!/usr/bin/env python3
"""Generate datasets/catalog.json: every tracked table of the repository, with its size, hash, columns and owner.

One entry per file that `git ls-files` lists with a tabular extension (.csv, .csv.gz, .tsv, .jsonl, .jsonl.gz,
.parquet), sorted by path. Columns are the CSV header or the keys of the first JSON line; rows are counted by reading
the file to its end. The standard library cannot read parquet, so its columns and rows are null and a note says so.
The catalogue describes files, not what they prove: what a table means is in the report of its owner.

--check recomputes path, size and SHA-256 of every tracked table and fails when the catalogue differs. It counts no
rows: columns and rows follow from the bytes, but a changed title of an owner's README is not seen.

usage: python3 scripts/build_dataset_catalog.py [--check]
Standard library only.
"""
import csv
import gzip
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = Path("datasets") / "catalog.json"
FORMATS = ("csv.gz", "jsonl.gz", "csv", "tsv", "jsonl", "parquet")
PARQUET_NOTE = "the standard library cannot read parquet: columns and rows not read"
ARRAY_NOTE = "lines are JSON arrays: no column names"


def table_format(path):
    return next((f for f in FORMATS if path.endswith("." + f)), None)


def tracked_tables(root):
    listed = subprocess.run(["git", "-C", str(root), "ls-files", "-z"], capture_output=True, check=True).stdout.decode("utf-8")
    return sorted(p for p in listed.split("\0") if p and table_format(p))


def owner(path):
    """investigations/<id> or research_notes/<name>, else the top folder; '.' for a file at the root."""
    parts = path.split("/")
    if len(parts) == 1:
        return "."
    return "/".join(parts[:2]) if parts[0] in ("investigations", "research_notes") and len(parts) > 2 else parts[0]


def title(root, folder):
    """First Markdown heading of the folder's README.md, else of its REPORT.md, else None."""
    for name in ("README.md", "REPORT.md"):
        path = root / folder / name
        if path.is_file():
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.startswith("#"):
                    return line.lstrip("#").strip()
    return None


def digest(path):
    with open(path, "rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def shape(path, fmt):
    """(columns, rows) of one table, read to its end. Rows exclude the CSV header; blank JSON lines are not rows."""
    if fmt == "parquet":
        return None, None
    with (gzip.open if fmt.endswith(".gz") else open)(path, "rt", encoding="utf-8-sig", newline="") as handle:
        if fmt.startswith("jsonl"):
            lines = (line for line in handle if line.strip())
            first = next(lines, None)
            if first is None:
                return [], 0
            record = json.loads(first)
            return (list(record) if isinstance(record, dict) else None), 1 + sum(1 for _ in lines)
        reader = csv.reader(handle, delimiter="\t" if fmt == "tsv" else ",")
        return next(reader, []), sum(1 for _ in reader)


def build(root):
    out = []
    for path in tracked_tables(root):
        fmt, folder = table_format(path), owner(path)
        columns, rows = shape(root / path, fmt)
        out.append({"path": path, "format": fmt, "bytes": (root / path).stat().st_size, "sha256": digest(root / path), "columns": columns,
                    "rows": rows, "owner": folder, "owner_title": title(root, folder),
                    "note": PARQUET_NOTE if fmt == "parquet" else ARRAY_NOTE if columns is None else None})
    return out


def render(entries):
    """One entry per line, so that a change of one table is a change of one line."""
    lines = ",\n".join(json.dumps(e, ensure_ascii=False) for e in entries)
    return '{"generator": "scripts/build_dataset_catalog.py", "entries": [\n' + lines + "\n]}\n"


def stale(root):
    """Paths whose catalogue entry differs from the file now, or that only one side has. Empty when up to date."""
    listed = {e["path"]: (e["bytes"], e["sha256"]) for e in json.loads((root / CATALOG).read_text(encoding="utf-8"))["entries"]}
    now = {p: ((root / p).stat().st_size, digest(root / p)) for p in tracked_tables(root)}
    return sorted(p for p in listed.keys() | now.keys() if listed.get(p) != now.get(p))


def main(argv, root=ROOT):
    if "--check" in argv:
        if not (root / CATALOG).exists():
            print(f"stale: {CATALOG} is missing")
            return 1
        changed = stale(root)
        more = f" and {len(changed) - 20} more" if len(changed) > 20 else ""
        print(f"stale: {', '.join(changed[:20])}{more}" if changed else "catalogue up to date")
        return 1 if changed else 0
    entries = build(root)
    (root / CATALOG).parent.mkdir(parents=True, exist_ok=True)
    (root / CATALOG).write_text(render(entries), encoding="utf-8")
    print(f"{len(entries)} tables catalogued")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
