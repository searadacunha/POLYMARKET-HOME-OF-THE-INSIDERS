#!/usr/bin/env python3
"""Read-only audit of tracked Python syntax and high-confidence public secrets.

The separate validate_evidence.py scans imported investigation snapshots. This
script covers research_notes, scripts, integrations and datasets, which that
import scanner did not cover. It never prints matched secret material.
"""
from __future__ import annotations

import ast
import re
import subprocess
import sys
import tokenize
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phi_lib  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SCAN_ROOTS = ("research_notes/", "scripts/", "integrations/", "datasets/", ".github/")
ALLOWED_SUFFIXES = (
    ".py", ".md", ".txt", ".json", ".csv", ".tsv", ".jsonl",
    ".yaml", ".yml", ".sh", ".toml", ".xml", ".env",
    ".json.gz", ".csv.gz", ".jsonl.gz", ".txt.gz",
)
MAX_GZ_UNCOMPRESSED = 100_000_000
BUFFER_SIZE = 1 << 20
OVERLAP = 1024
# High-confidence patterns only, not vague "key=" or public wallet addresses.
SECRET_PATTERNS = {
    "pem_private_key": re.compile(b"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "github_classic_token": re.compile(b"\\b(?:gh" + b"p|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,}\\b"),
    "github_fine_grained_token": re.compile(b"\\bgithub_pat_[A-Za-z0-9_]{40,}\\b"),
    "anthropic_api_token": re.compile(b"\\bsk-ant-[A-Za-z0-9_-]{30,}\\b"),
    "openai_project_token": re.compile(b"\\bsk-proj-[A-Za-z0-9_-]{30,}\\b"),
    "aws_access_id": re.compile(b"\\bAKIA[0-9A-Z]{16}\\b"),
    "slack_bot_token": re.compile(b"\\bxoxb-[0-9]{10,}-[A-Za-z0-9-]{16,}\\b"),
}


def tracked_paths():
    raw = subprocess.check_output(["git", "-C", str(ROOT), "ls-files", "-z"])
    return [Path(p.decode("utf-8", "surrogateescape")) for p in raw.split(b"\0") if p]


def inspect_stream(stream, path):
    return inspect_chunks(iter(lambda: stream.read(BUFFER_SIZE), b""), path)


def inspect_chunks(chunks, path):
    previous = b""
    size = 0
    for chunk in chunks:
        size += len(chunk)
        if path.name.lower().endswith(".gz") and size > MAX_GZ_UNCOMPRESSED:
            return [], size, False
        data = previous + chunk
        findings = [label for label, pattern in SECRET_PATTERNS.items() if pattern.search(data)]
        if findings:
            return findings, size, True
        previous = data[-OVERLAP:]
    return [], size, True


def is_scannable(path: Path):
    name = path.name.lower()
    return any(name.endswith(suffix) for suffix in ALLOWED_SUFFIXES)


def check():
    tracked = tracked_paths()
    errors = []
    archived_syntax_warnings = []
    limitations = []
    scanned = 0
    inspected_bytes = 0
    python_files = 0
    for rel in tracked:
        p = ROOT / rel
        if p.is_symlink() or not p.is_file():
            errors.append(f"{rel}: missing or symlinked tracked file")
            continue
        if rel.suffix == ".py":
            python_files += 1
            try:
                with tokenize.open(p) as fh:
                    ast.parse(fh.read(), filename=str(rel))
            except (SyntaxError, UnicodeError, OSError, LookupError) as e:
                msg = f"{rel}: {type(e).__name__}"
                parts = rel.parts
                if len(parts) >= 3 and parts[0] == "investigations" and parts[2] == "sources":
                    archived_syntax_warnings.append(msg)
                else:
                    errors.append(msg)
        if not str(rel).startswith(SCAN_ROOTS) or not is_scannable(rel):
            continue
        try:
            if rel.name.lower().endswith(".gz"):
                with p.open("rb") as source:
                    chunks = phi_lib.iter_gzip_for_scan(source, MAX_GZ_UNCOMPRESSED)
                    hits, n, complete = inspect_chunks(chunks, rel)
            else:
                with p.open("rb") as source:
                    hits, n, complete = inspect_stream(source, rel)
        except phi_lib.GzipScanLimit as exc:
            limitations.append(f"{rel}: {exc}")
            errors.append(f"{rel}: incomplete compressed evidence scan (fail closed)")
            continue
        except (OSError, EOFError, ValueError, zlib.error) as exc:
            errors.append(f"{rel}: unreadable evidence ({type(exc).__name__})")
            continue
        inspected_bytes += n
        scanned += 1
        if not complete:
            limitations.append(f"{rel}: compressed scan exceeded {MAX_GZ_UNCOMPRESSED} uncompressed bytes")
            errors.append(f"{rel}: incomplete compressed evidence scan (fail closed)")
        if hits:
            errors.append(f"{rel}: possible secret format {','.join(sorted(set(hits)))}")
    print(f"Tracked files: {len(tracked)}; Python AST checks: {python_files}; "
          f"research/tooling public-secret file scans: {scanned}; bytes read: {inspected_bytes}; "
          f"archived syntax warnings: {len(archived_syntax_warnings)}; incomplete gzip scans: {len(limitations)}")
    for warning in archived_syntax_warnings[:30]:
        print("ARCHIVED SYNTAX WARNING", warning)
    for warning in limitations[:30]:
        print("LIMITATION", warning)
    for error in errors[:60]:
        print("FAIL", error, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(check())
