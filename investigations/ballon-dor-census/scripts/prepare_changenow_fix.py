#!/usr/bin/env python3
"""Prepare corrected ChangeNOW code in a NEW workspace; never edit the evidence snapshot.

No network calls, Git operations, credentials, or collector execution occur here.
Old derived results and HTTP caches are deliberately not reused.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

FIX_ID = "changenow-pagination-attribution-2026-11-05"
EDITS = {
    "net.py": (
        ('    """Whole list with Etherscan v2. A full page (10 000 rows) moves the start block forward: never silently truncated."""\n',
         '    """Read Free-tier-sized pages and re-read cut boundary blocks."""\n    page_size = 1000  # Etherscan Free-tier cap since 2026-07-01.\n'),
        ("endblock=end, page=1, offset=10000, sort='asc')",
         "endblock=end, page=1, offset=page_size, sort='asc')"),
        ("        if len(page) < 10000:\n", "        if len(page) < page_size:\n"),
        ("            raise FetchError(f'over 10 000 rows in the single block {last} of {address}: cannot page further')",
         "            raise FetchError(f'at least {page_size} rows in the single block {last} of {address}: completeness unresolved; cannot page further')"),
    ),
    "ana_75_cn_recipients.py": (
        ("    known_cn = {v['address'] for v in funcs.values()}\n",
         "    # Exploring a neighbor does not establish ChangeNOW attribution.\n    known_cn = {(v['address'].lower(), int(v['chain'])) for v in funcs.values() if v.get('level') == 'A'}\n"),
        ("        is_cn = a in known_cn or ",
         "        is_cn = (a.lower(), int(c)) in known_cn or "),
    ),
}
# Inputs only. No cn_functions*, cn_sends*, cn_links*, cn_population*,
# cn_inactivity*, cn_result*, old registers, labels, or HTTP caches are copied.
INPUTS = (
    "derived/cn_universe.csv",
    "derived/census_trades.jsonl.gz",
    "CLUSTERS.json",
    "PROTOCOL.md",
)


class FixError(RuntimeError):
    """Source drift or an unsafe workspace prevents applying this bounded fix."""


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def patched_text(name: str, text: str) -> str:
    """Apply only reviewed edits. Reject missing, duplicated, or ambiguous anchors."""
    for before, after in EDITS[name]:
        if text.count(before) == 1 and after not in text:
            text = text.replace(before, after, 1)
        elif before not in text and text.count(after) == 1:
            continue  # Idempotent on an already corrected working copy.
        else:
            raise FixError(f"{name}: source has changed; review the patch instead of forcing it")
    compile(text, name, "exec")
    return text


def inspect(project: Path) -> tuple[dict[str, bytes], dict[str, bytes]]:
    code = project / "code"
    if not code.is_dir() or code.is_symlink():
        raise FixError("Expected a real code/ directory in the source project")
    original, corrected = {}, {}
    for name in EDITS:
        path = code / name
        if not path.is_file() or path.is_symlink():
            raise FixError(f"Missing or symlinked source: code/{name}")
        original[name] = path.read_bytes()
        corrected[name] = patched_text(name, original[name].decode("utf-8")).encode("utf-8")
    return original, corrected


def prepare(project: Path, output: Path) -> dict:
    project, output = project.resolve(), output.resolve()
    if output == project or project in output.parents:
        raise FixError("The new workspace must be outside the source project")
    if output.exists():
        raise FixError("The output must not exist; refusing to overwrite another session")
    original, corrected = inspect(project)
    universe = project / INPUTS[0]
    if not universe.is_file() or universe.is_symlink():
        raise FixError("Missing a regular derived/cn_universe.csv input")
    code_files = sorted((project / "code").rglob("*.py"))
    for path in code_files:
        if path.is_symlink() or not path.is_file() or (project / "code").resolve() not in path.resolve().parents:
            raise FixError(f"Unsafe source file: {path.relative_to(project)}")
    for relative in INPUTS:
        path = project / relative
        if path.is_symlink():
            raise FixError(f"Refusing symlinked input: {relative}")
    metadata = {"fix_id": FIX_ID, "network_executed": False,
                "historical_results_recomputed": False, "code": {}, "inputs": {},
                "missing_optional_inputs": []}
    # Exclusive creation also protects against an output appearing after preflight.
    output.mkdir(parents=True, exist_ok=False)
    for directory in ("code", "derived", "state", "study", "evidence", "raw/http"):
        (output / directory).mkdir(parents=True, exist_ok=True)
    try:
        for path in code_files:
            target = output / path.relative_to(project)
            target.parent.mkdir(parents=True, exist_ok=True)
            data = path.read_bytes()
            if path.name in original and path.parent == project / "code":
                if data != original[path.name]:
                    raise FixError(f"Source changed during preparation: {path.name}")
                data = corrected[path.name]
            target.write_bytes(data)
        for name in EDITS:
            metadata["code"][name] = {"source_sha256": digest(original[name]),
                                      "corrected_sha256": digest(corrected[name])}
        for relative in INPUTS:
            source = project / relative
            if source.is_file():
                target = output / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
                # Stream hashing avoids loading a potentially large census into RAM.
                hasher = hashlib.sha256()
                with target.open("rb") as stream:
                    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                        hasher.update(chunk)
                checksum = hasher.hexdigest()
                metadata["inputs"][relative] = checksum
            else:
                metadata["missing_optional_inputs"].append(relative)
        (output / "CHANGENOW_FIX.json").write_text(json.dumps(metadata, indent=2) + "\n")
    except Exception:
        # Never remove an incomplete workspace: retain it for inspection.
        (output / "PREPARATION_FAILED.txt").write_text("Preparation failed. Do not run this workspace.\n")
        raise
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path, help="Project containing code/ and derived/cn_universe.csv")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="Validate the patch without writing anything")
    group.add_argument("--output", type=Path, help="Create a NEW isolated workspace; never run collectors")
    args = parser.parse_args()
    try:
        if args.check:
            inspect(args.project.resolve())
            print("Reviewed code edits apply; no files changed and no network requests made.")
        else:
            result = prepare(args.project, args.output)
            print(json.dumps(result, indent=2))
            print("Workspace prepared only. No recollection or new finding has been produced.")
    except (FixError, OSError, UnicodeError, SyntaxError) as exc:
        parser.exit(1, f"Not prepared: {exc}\n")


if __name__ == "__main__":
    main()
