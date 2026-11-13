"""Score the targeted Pendulum preview hours and write a replayable JSONL.

Usage:
  python3 run_sample.py /tmp/phi-pendulum /path/to/output_dir

The directory must contain the six files downloaded for this study. Nothing is
fetched from the network.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from alerts import promote
from microstructure import score_events
from pendulum import load_events
from replay import replay_all
from validation import evaluate

SLICES = (
    ("science00.parquet", "2026-10-11T00", "discovery", "science"),
    ("economy00.parquet", "2026-10-11T00", "discovery", "economy"),
    ("earnings00.parquet", "2026-10-11T00", "discovery", "earnings"),
    ("science01.parquet", "2026-10-11T01", "validation", "science"),
    ("economy01.parquet", "2026-10-11T01", "validation", "economy"),
    ("earnings01.parquet", "2026-10-11T01", "validation", "earnings"),
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main(source: Path, output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    scored = []
    sources = []
    for name, hour, split, category in SLICES:
        path = source / name
        sources.append({"file": name, "sha256": _sha256(path), "bytes": path.stat().st_size})
        scored.extend(score_events(load_events(str(path), hour, split, category)))
    evaluation = evaluate(scored)
    alerts = promote(scored, evaluation, "ARCHIVE_HOURLY")
    cases = replay_all(())
    payload = {
        "executed": True,
        "source": "pendulumflow preview v3.1, 2026-10-11T00 and T01, categories science, economy, earnings",
        "licence": "CC BY-NC 4.0",
        "attribution": "pendulumflow. Polymarket Orderbook Archive. https://archive.pendulumflow.com",
        "files": sources,
        "prints": len(scored),
        "funnel": evaluation["funnel"],
        "evaluation": evaluation,
        "alerts": {"emitted": len(alerts["emitted"]), "withheld": alerts["withheld"], "live_claim": False},
        "historical_cases": cases,
    }
    (output / "scored_prints.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in scored),
        encoding="utf-8",
    )
    (output / "results.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: run_sample.py SOURCE_DIR OUTPUT_DIR")
    main(Path(sys.argv[1]), Path(sys.argv[2]))
