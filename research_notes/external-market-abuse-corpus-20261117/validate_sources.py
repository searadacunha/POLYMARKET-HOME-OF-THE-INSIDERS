#!/usr/bin/env python3
"""Offline structural checks for the external source bibliography (not an evidentiary audit)."""
from __future__ import annotations

import argparse
import csv
import io
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
EXPECTED_COLUMNS = ("id", "kind", "source", "title", "url", "contribution", "status", "priority")
VALID_PRIORITIES = {"P0", "P1", "P2"}


def validate_text(data: str) -> dict:
    rows = list(csv.DictReader(io.StringIO(data), strict=True))
    if not rows:
        raise ValueError("Catalog has no source records")
    if tuple(rows[0]) != EXPECTED_COLUMNS:
        raise ValueError("Header changed; update the bibliography contract intentionally")
    seen_ids: set[str] = set()
    seen_urls: set[str] = set()
    counts = Counter()
    for number, row in enumerate(rows, 2):
        if any(value is None or not str(value).strip() for value in row.values()):
            raise ValueError(f"Row {number}: empty or missing required field")
        identifier = row["id"]
        if identifier != f"EXT-{number - 1:03d}":
            raise ValueError(f"Row {number}: nonsequential source ID {identifier!r}")
        if identifier in seen_ids:
            raise ValueError(f"Row {number}: duplicate ID {identifier}")
        url = row["url"]
        parts = urlparse(url)
        if (parts.scheme != "https" or not parts.hostname or parts.username or parts.password or
                any(c.isspace() for c in url)):
            raise ValueError(f"Row {number}: invalid external URL")
        if url in seen_urls:
            raise ValueError(f"Row {number}: duplicate URL; use source lineage instead")
        if row["priority"] not in VALID_PRIORITIES:
            raise ValueError(f"Row {number}: unknown priority")
        if not re.fullmatch(r"[a-z][a-z0-9_]*", row["kind"]):
            raise ValueError(f"Row {number}: invalid kind")
        if not re.fullmatch(r"[a-z][a-z0-9_]*", row["status"]):
            raise ValueError(f"Row {number}: invalid evidence-review status")
        seen_ids.add(identifier)
        seen_urls.add(url)
        counts[row["kind"]] += 1
    return {"entries": len(rows), "categories": dict(sorted(counts.items()))}


def selftest() -> None:
    head = ",".join(EXPECTED_COLUMNS)
    good = ('"EXT-001","academic","Author","Title","https://example.org/paper",'
            '"Reported study only","abstract_only","P0"')
    assert validate_text(head + "\n" + good + "\n")["entries"] == 1
    bad = [
        good.replace("https://", "http://"),
        good.replace("EXT-001", "EXT-002"),
        good.replace("P0", "P9"),
        good.replace("Reported study only", ""),
    ]
    for line in bad:
        try:
            validate_text(head + "\n" + line + "\n")
        except ValueError:
            continue
        raise AssertionError("Invalid fixture was not rejected")
    print("SELFTEST PASS")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--file", type=Path, default=HERE / "SOURCES.csv")
    p.add_argument("--selftest", action="store_true")
    args = p.parse_args()
    if args.selftest:
        selftest()
    result = validate_text(args.file.read_text(encoding="utf-8"))
    print(f"STRUCTURE PASS: {result['entries']} unique source URLs, {len(result['categories'])} categories")
    for kind, count in result["categories"].items():
        print(f"  {kind}: {count}")
    print("NOTE: passing this check does not validate a study, legal claim, link availability or licence.")


if __name__ == "__main__":
    main()
