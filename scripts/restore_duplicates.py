#!/usr/bin/env python3
"""Rebuild a runnable tree of one investigation: sources/ plus its files deduplicated elsewhere in the repo.

  python3 scripts/restore_duplicates.py --id <id> --dest <new folder>
"""
import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phi_lib as lib  # noqa: E402


def restore(inv_dir, dest):
    dest = Path(dest)
    if dest.exists():
        raise SystemExit(f"refus : {dest} existe déjà")
    shutil.copytree(inv_dir / "sources", dest)
    restored = 0
    for entry in lib.load_manifest(inv_dir)["files"]:
        if entry.get("status") == "duplicate":
            source = lib.REPO / entry["repo_path"]
            if lib.sha256_file(source) != entry["sha256"]:
                raise SystemExit(f"empreinte différente : {entry['repo_path']}")
            target = dest / entry["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            restored += 1
    return restored


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--id", required=True)
    parser.add_argument("--dest", required=True)
    args = parser.parse_args()
    print(restore(lib.REPO / "investigations" / args.id, args.dest), "fichiers restaurés")
