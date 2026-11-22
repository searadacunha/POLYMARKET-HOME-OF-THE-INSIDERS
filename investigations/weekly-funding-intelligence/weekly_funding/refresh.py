"""Capture a completed week in a separate directory; fail visible coverage gates after writing diagnostics."""

import argparse
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from .collect import collect_week
from .common import HOME, SNAP, STREAMS, bounds, read, save
from .frame import capture_frame, prices
from .report import build
from .routes import capture as native_paths
from .token_routes import capture as token_paths


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--week")
    p.add_argument("--dest", type=Path, required=True)
    p.add_argument("--previous-report", type=Path)
    args = p.parse_args()
    now = datetime.now(timezone.utc)
    week = args.week or (now.date() - timedelta(days=now.weekday() + 1)).strftime("%G-W%V")
    if bounds(week)[1] > now.timestamp():
        p.error("week must be closed")
    dest = args.dest.resolve()
    if dest == HOME or dest.is_relative_to(SNAP):
        p.error("use a separate capture directory")
    snap = dest / "snapshot"
    previous = args.previous_report
    if previous is None:
        checked = HOME / "results/weekly_funding.json"
        if checked.exists() and bounds(read(checked)["last_week"])[1] == bounds(week)[0]:
            previous = checked
    dest.mkdir(parents=True, exist_ok=True)
    if previous:
        prior_copy = dest / "previous_report.json"
        if previous.resolve() != prior_copy:
            shutil.copyfile(previous, prior_copy)
        previous = prior_copy
    frozen = dest / "capture.json"
    if frozen.exists():
        meta = read(frozen)
        if meta["week"] != week:
            p.error("this directory holds another week")
    else:
        meta = {
            "week": week,
            "asof_exclusive": int(now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()),
        }
        save(frozen, meta)
    if "repository_commit" not in meta:
        meta["repository_commit"] = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=HOME, text=True
        ).strip()
        save(frozen, meta)
    # The network stages are sequential and bounded. The two service filters run once per chain.
    for c in (137, 1):
        for stream in STREAMS:
            collect_week(week, stream, snap, chain=c)
    capture_frame(week, snap)
    prices(week, week, snap)
    native_paths(snap, week, week, meta["asof_exclusive"])
    token_paths(snap, week, week)
    subprocess.run(
        [
            sys.executable,
            "-m",
            "weekly_funding.accounts",
            "--from-week",
            week,
            "--to-week",
            week,
            "--dest",
            str(snap),
            "--asof",
            str(meta["asof_exclusive"]),
            "--work",
            str(dest / "work"),
        ],
        check=True,
        cwd=HOME,
    )
    result = build(snap, dest / "results", week, week, previous, not bool(previous))
    gaps = [
        key
        for key, v in result["coverage"][week].items()
        if key.split("/")[0] in {"137", "1"}
        and "native_archive" not in key
        and v["status"] != "SCOPED_COMPLETE"
    ]
    if gaps or result["account_ascertainment"]["unknown"]:
        raise SystemExit(
            f"partial capture: missing log coverage {gaps}, unresolved account lookups {result['account_ascertainment']['unknown']}"
        )
    print(dest / "results/REPORT.md")


if __name__ == "__main__":
    main()
