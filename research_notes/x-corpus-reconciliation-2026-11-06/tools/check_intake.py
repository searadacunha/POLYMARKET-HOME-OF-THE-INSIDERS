#!/usr/bin/env python3
"""Offline integrity checks for the reported historical-X *summary* intake.

Checks only deterministic arithmetic, CSV shape and timestamp encoded in
Snowflake IDs; it cannot authenticate X texts, RPC traces or the absent
244-file original corpus. Standard library only, no network.
"""

from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path

DIR = Path(__file__).resolve().parents[1]
X_EPOCH_MS = 1288834974657

POSTS = {
    "snoorrason": ("2110285369748963671", "2026-10-14T08:23:34Z"),
    "cypya": ("2111149784858042762", "2026-10-16T17:38:26Z"),
    "ec_unoxx": ("2008147229325013019", "2026-01-05T12:03:03Z"),
    "ec_unoxx_correction": ("2008186913170333953", "2026-01-05T14:40:45Z"),
    "andrey_38": ("2034030676589351244", "2026-03-17T22:14:38Z"),
    "lookonchain": ("2011736650054062085", "2026-01-15T09:46:08Z"),
    "jydyjyd": ("2112913244058755159", "2026-10-21T14:25:48Z"),
    "qkl_dimbull": ("2034669367888318477", "2026-03-19T16:32:34Z"),
}

def test_timestamps() -> None:
    for name, (post_id, expected) in POSTS.items():
        millis = (int(post_id) >> 22) + X_EPOCH_MS
        actual = datetime.fromtimestamp(millis / 1000, tz=timezone.utc)
        wanted = datetime.fromisoformat(expected.replace("Z", "+00:00"))
        assert actual.replace(microsecond=0) == wanted, (
            name,
            actual.isoformat(),
            wanted.isoformat(),
        )
        print(f"TIME {name}: {actual.isoformat()}")

def test_corpus_arithmetic() -> None:
    assert 1416 + 303 == 1719
    assert 179 + 124 == 303
    assert 1301 - 1110 == 191
    assert 986 <= 1301
    print("COUNT self-consistency: PASS (reported figures only)")

def test_registry() -> None:
    with (DIR / "ADJUDICATION.csv").open(newline="", encoding="utf-8") as fd:
        rows = list(csv.DictReader(fd))
    expected_fields = {
        "id", "case", "source_url", "observed_time_utc", "source_claim",
        "reconciled_evidence", "status", "next_test",
    }
    assert len(rows) == 12, f"expected 12 rows; got {len(rows)}"
    assert set(rows[0]) == expected_fields
    assert len({r["id"] for r in rows}) == len(rows)
    for row in rows:
        assert row["source_url"].startswith("https://x.com/")
        assert row["status"] and row["next_test"]
    print("ADJUDICATION.csv: 12 unique rows, shape OK")

def main() -> None:
    test_timestamps()
    test_corpus_arithmetic()
    test_registry()
    print("OFFLINE INTAKE CHECKS PASSED. X text and chain receipts NOT validated.")

if __name__ == "__main__":
    main()
