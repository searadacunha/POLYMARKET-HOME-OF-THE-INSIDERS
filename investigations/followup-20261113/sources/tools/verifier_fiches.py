"""Contrôle des références : chaque adresse ou hash cité dans les fiches et rapports doit exister dans les données.

Corpus de preuve : resultats/ (CSV, JSON), entrees/ (copies des dépôts), sources/ (réponses brutes, décompressées).
Identifiants contrôlés : hex 0x de 40 ou 64 caractères, et chaînes base58 Solana de 43 à 88 caractères.
Un identifiant tronqué (avec « … ») n'est pas contrôlé. Code de sortie 1 si un identifiant est introuvable.

Usage : python3 scripts/verifier_fiches.py
"""
from __future__ import annotations

import gzip
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HEX = re.compile(r"0x[0-9a-fA-F]{64}(?![0-9a-fA-F])|0x[0-9a-fA-F]{40}(?![0-9a-fA-F])")
B58 = re.compile(r"(?<![1-9A-HJ-NP-Za-km-z])[1-9A-HJ-NP-Za-km-z]{43,88}(?![1-9A-HJ-NP-Za-km-z…])")


def corpus() -> str:
    parts = []
    for base in ("resultats", "entrees", "sources"):
        for p in (ROOT / base).rglob("*"):
            if p.is_file():
                b = p.read_bytes()
                if p.suffix == ".gz":
                    b = gzip.decompress(b)
                parts.append(b.decode("utf-8", errors="replace"))
    return "\n".join(parts)


def main() -> int:
    text = corpus()
    low = text.lower()
    bad = 0
    files = sorted((ROOT / "decouvertes").glob("*.md")) + sorted((ROOT / "rapports").glob("*.md")) + [ROOT / "RAPPORT_GENERAL.md"]
    for f in files:
        if not f.exists():
            continue
        s = f.read_text()
        ids = set(HEX.findall(s)) | set(B58.findall(s))
        missing = sorted(i for i in ids if (i.lower() not in low if i.startswith("0x") else i not in text))
        bad += len(missing)
        print(f"{'OK  ' if not missing else 'ÉCHEC'} {f.relative_to(ROOT)} : {len(ids)} identifiants, {len(missing)} introuvables")
        for m in missing:
            print(f"      introuvable : {m}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
