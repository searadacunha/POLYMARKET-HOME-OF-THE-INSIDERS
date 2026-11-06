#!/usr/bin/env python3
"""Validate relative Markdown links in the actively published research index.

Archived investigation source snapshots are immutable and are not included.
This checks links only, not the factual truth of text or external URLs.
Standard library, offline. Use --self-test for small synthetic fixtures.
"""

from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
INDEX_DOCS = (
    "README.md",
    "VERIFIED_FINANCIAL_FINDINGS.md",
    "METHODOLOGY.md",
    "CONTRIBUTING.md",
    "AGENTS.md",
    "CLAUDE.md",
    "MASTER_REPORT.md",
    "INVENTORY.md",
    "BACKUP_STATUS.md",
    "AUDIT_2026-11-04.md",
    "research_notes/relay-followup-2026-11-04/REPORT.md",
    "research_notes/x-history-2026-11-06/REPORT.md",
    "research_notes/x-history-2026-11-06/SECOND_PASS.md",
    "research_notes/x-history-2026-11-06/verification/REPORT.md",
    "research_notes/x-corpus-reconciliation-2026-11-06/REPORT.md",
    "research_notes/publication-integrity-20261106/RECOVERY.md",
)
LINK = re.compile(r"!?(?:\[[^\]\n]*\])\(([^)\s]+)(?:\s+['\"][^'\"]*['\"])?\)")


def included_documents(root: Path) -> list[Path]:
    documents = [root / p for p in INDEX_DOCS]
    documents.extend(sorted((root / "investigations").glob("*/README.md")))
    return documents


def check_document(root: Path, file: Path) -> list[str]:
    if not file.is_file():
        return [f"{file.relative_to(root)}: indexed Markdown file missing"]
    errors = []
    fenced = False
    fence_marker = ""
    for line_num, line in enumerate(file.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.lstrip()
        if stripped.startswith("~~~") or stripped.startswith("```"):
            marker = stripped[:3]
            if not fenced:
                fenced, fence_marker = True, marker
            elif marker == fence_marker:
                fenced, fence_marker = False, ""
            continue
        if fenced:
            continue
        for found in LINK.finditer(line):
            href = found.group(1)
            if href.startswith("#"):
                continue
            parts = urlsplit(href)
            if parts.scheme or parts.netloc or href.startswith("//"):
                continue
            path = unquote(parts.path)
            if not path:
                continue
            absolute = (file.parent / path).resolve()
            try:
                absolute.relative_to(root.resolve())
            except ValueError:
                errors.append(f"{file.relative_to(root)}:{line_num}: link escapes repository: {href}")
                continue
            if not absolute.exists():
                errors.append(f"{file.relative_to(root)}:{line_num}: broken link: {href}")
    return errors


def self_test() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        (root / "docs").mkdir()
        (root / "target.md").write_text("content\n", encoding="utf-8")
        page = root / "docs" / "index.md"
        page.write_text(
            "[works](../target.md#heading) [web](https://example.com/path)\n"
            "```md\n[not parsed](missing.md)\n```\n", encoding="utf-8"
        )
        assert check_document(root, page) == []
        page.write_text("[broken](does-not-exist.md)\n", encoding="utf-8")
        failures = check_document(root, page)
        assert len(failures) == 1 and "broken link" in failures[0]
        page.write_text("[escape](../../outside.md)\n", encoding="utf-8")
        failures = check_document(root, page)
        assert len(failures) == 1 and "escapes repository" in failures[0]
    print("PASS: Markdown link self-tests")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    docs = included_documents(ROOT)
    errors = [err for p in docs for err in check_document(ROOT, p)]
    for err in errors:
        print("ERROR", err, file=sys.stderr)
    print(f"Checked {len(docs)} published index documents; {len(errors)} broken local links")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
