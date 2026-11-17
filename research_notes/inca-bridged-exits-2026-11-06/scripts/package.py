"""Copies the raw files listed in evidence/NEEDED.txt (written by `verify.py --raw`) into evidence/ as gzip,
and writes SHA256SUMS.txt (SHA-256 of each raw file, of its gzip copy, and of the other files of the note).

python3 -I verify.py --raw && python3 -I scripts/package.py
"""
import gzip
import hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
ROOTS = {"r1": Path.home() / "Projects/Polymarket-inca-raw-20261106/raw",
         "r2": Path.home() / "Projects/Polymarket-inca-bridges-raw-20261106/raw"}
EVID = HERE / "evidence"
sha = lambda b: hashlib.sha256(b).hexdigest()


def main():
    lines = []
    for item in (EVID / "NEEDED.txt").read_text().split():
        root, rel = item.split("/", 1)
        raw = (ROOTS[root] / rel).read_bytes()
        out = EVID / root / (rel + ".gz")
        out.parent.mkdir(parents=True, exist_ok=True)
        gz = gzip.compress(raw, mtime=0)  # mtime 0: the same raw file always gives the same bytes
        out.write_bytes(gz)
        lines.append(f"{sha(raw)}  raw:{item}")
        lines.append(f"{sha(gz)}  evidence/{root}/{rel}.gz")
    for p in sorted(HERE.rglob("*")):
        if p.is_file() and "evidence" not in p.parts and p.name not in ("SHA256SUMS.txt", "verification.json") and "__pycache__" not in p.parts:
            lines.append(f"{sha(p.read_bytes())}  {p.relative_to(HERE)}")
    (HERE / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n")
    print(len(lines), "lines,", sum(1 for l in lines if l.split()[1].startswith("evidence/")), "evidence files")


if __name__ == "__main__":
    main()
