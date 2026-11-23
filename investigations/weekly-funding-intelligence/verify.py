"""Verify each frozen input, rerun without network and compare every published output byte."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from weekly_funding.common import HOME, REPO, SNAP, digest
from weekly_funding.report import build


def main():
    official = HOME / "results"
    published = json.loads((official / "weekly_funding.json").read_bytes())
    for name, expected in published["inputs_sha256"].items():
        path = (HOME if name.startswith("snapshot/") else REPO) / name
        if digest(path) != expected:
            raise SystemExit(f"input digest mismatch: {name}")
    with (
        tempfile.TemporaryDirectory() as temp,
        patch(
            "socket.socket.connect",
            side_effect=AssertionError("offline verification opened a network socket"),
        ),
    ):
        output = Path(temp)
        build(SNAP, output, published["first_week"], published["last_week"])
        if {p.name for p in output.iterdir()} != {p.name for p in official.iterdir()}:
            raise SystemExit("published output set mismatch")
        for path in output.iterdir():
            if digest(path) != digest(official / path.name):
                raise SystemExit("offline replay mismatch: " + path.name)
    print(
        f"Verified {len(published['inputs_sha256'])} inputs, weekly tables, wallet receipts, report and chart offline."
    )


if __name__ == "__main__":
    main()
