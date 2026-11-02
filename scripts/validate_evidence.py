#!/usr/bin/env python3
"""Refuse an investigation folder that breaks the rules. Exit 1 when anything is wrong.

  python3 scripts/validate_evidence.py investigations/<id>   # one investigation
  python3 scripts/validate_evidence.py                       # everything, plus root links
  python3 scripts/validate_evidence.py investigations/<id> --fill   # write missing hashes in EVIDENCE.md
"""
import argparse
import gzip
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phi_lib as lib  # noqa: E402

REQUIRED_FILES = ("README.md", "STATUS.md", "FINDINGS.md", "EVIDENCE.md", "data_manifest.json")
AUTHORED = ("README.md", "STATUS.md", "FINDINGS.md", "EVIDENCE.md")
FULL_HEX_RE = re.compile(r"0x[0-9a-fA-F]{40}(?:[0-9a-fA-F]{24})?\b")
SHORT_HEX_RE = re.compile(r"0x([0-9a-fA-F]{4,})…([0-9a-fA-F]{2,})")
NUMBER_RE = re.compile(r"(?<![\w.,])\d{1,3}(?: \d{3})+(?:,\d+)?|(?<![\w.,])\d+,\d+|(?<![\w.,])\d{4,}(?![\w-])")
PATH_RE = re.compile(r"(?:^|[\s;`(])((?:sources|results|tests|scripts)/[^\s;`,)]+)")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
EVIDENCE_ROW_RE = re.compile(r"^\| `([^`]+)` \| (auto|[0-9a-f]{64}|local_only) \|", re.M)


def normalize_numbers(text):
    """Same digits whatever the thousands separator: 304 137,63 and 304,137.63 and 304137.63 agree."""
    text = text.replace(" ", " ").replace(" ", " ")
    return re.sub(r"(?<=\d)[ ,](?=\d{3}\b)", "", text).replace(",", ".")


def cited_paths(sources_field):
    return PATH_RE.findall(" " + sources_field)


def read_text(path):
    data = lib.read_for_scan(path)
    return data.decode("utf-8", "ignore")


def check_findings(inv_dir, errors):
    path = inv_dir / "FINDINGS.md"
    findings, _ = lib.parse_findings(path.read_text())
    seen = set()
    for finding in findings:
        label = f"{inv_dir.name}:{finding['id']}"
        if finding["id"] in seen:
            errors.append(f"{label} : identifiant en double")
        seen.add(finding["id"])
        if finding["level"] not in lib.LEVELS:
            errors.append(f"{label} : niveau inconnu {finding['level']}")
        for bullet in ("Sources", "Method", "Limits", "Links"):
            if not finding.get(bullet, "").strip():
                errors.append(f"{label} : puce {bullet} absente ou vide")
        paths = cited_paths(finding.get("Sources", ""))
        if not paths:
            errors.append(f"{label} : aucun fichier cité dans Sources")
        corpus = []
        for rel in paths:
            target = inv_dir / rel
            if not target.exists():
                errors.append(f"{label} : source introuvable {rel}")
            elif target.is_file():
                try:
                    corpus.append(read_text(target))
                except OSError as exc:
                    errors.append(f"{label} : source illisible {rel} : {exc}")
        if not corpus:
            continue
        joined = "\n".join(corpus)
        lower = joined.lower()
        checked = finding["claim"]
        for token in FULL_HEX_RE.findall(checked + " " + finding.get("Sources", "")):
            if token.lower() not in lower:
                errors.append(f"{label} : {token} absent des sources citées")
        for start, end in SHORT_HEX_RE.findall(checked):
            if f"0x{start}".lower() not in lower:
                errors.append(f"{label} : 0x{start}… absent des sources citées")
        normalized = normalize_numbers(joined)
        for number in NUMBER_RE.findall(checked):
            if normalize_numbers(number) not in normalized:
                errors.append(f"{label} : le nombre « {number} » n'apparaît pas dans les sources citées")
    return findings


def check_manifest(inv_dir, errors):
    manifest = lib.load_manifest(inv_dir)
    if manifest is None:
        return
    listed = set()
    for entry in manifest["files"]:
        if entry.get("status") != "imported":
            continue
        listed.add(entry["repo_path"])
        target = lib.REPO / entry["repo_path"]
        if not target.is_file():
            errors.append(f"{inv_dir.name} : manifeste, fichier absent {entry['repo_path']}")
        elif lib.sha256_file(target) != entry["sha256"]:
            errors.append(f"{inv_dir.name} : empreinte différente {entry['repo_path']}")
    for dirpath, _, filenames in os.walk(inv_dir / "sources"):
        for name in filenames:
            if name == ".DS_Store":
                continue
            rel = str((Path(dirpath) / name).relative_to(lib.REPO))
            if rel not in listed:
                errors.append(f"{inv_dir.name} : fichier hors manifeste {rel}")


def check_scan(inv_dir, known, errors):
    for dirpath, _, filenames in os.walk(inv_dir):
        for name in filenames:
            path = Path(dirpath) / name
            rel = path.relative_to(lib.REPO)
            size = path.stat().st_size
            if size > lib.MAX_FILE_BYTES and name != "data_manifest.json":
                errors.append(f"{rel} : {size / 1e6:.0f} Mo, au-dessus de la limite")
            if name in (".env",) or name.startswith(".env.") or name.endswith((".pem", ".key")):
                errors.append(f"{rel} : nom de fichier interdit")
            if path.suffix.lower() in lib.IMAGE_EXT:
                continue
            try:
                hits = lib.scan_bytes(lib.read_for_scan(path), known)
            except (OSError, EOFError, gzip.BadGzipFile, ValueError) as exc:
                errors.append(f"{rel} : illisible par le scan, {type(exc).__name__}")
                continue
            if hits:
                errors.append(f"{rel} : {', '.join(sorted(set(h.split(':')[0] for h in hits)))}")


def fill_or_check_evidence(inv_dir, fill, errors):
    path = inv_dir / "EVIDENCE.md"
    text = path.read_text()
    manifest = lib.load_manifest(inv_dir) or {"files": []}
    by_path = {f"sources/{e['path']}": e for e in manifest["files"]}

    def resolve(match):
        rel, value = match.group(1), match.group(2)
        target = inv_dir / rel
        if target.is_file():
            digest = lib.sha256_file(target)
        elif by_path.get(rel, {}).get("sha256"):
            digest = by_path[rel]["sha256"]
        else:
            errors.append(f"{inv_dir.name} : EVIDENCE cite {rel}, ni présent ni au manifeste")
            return match.group(0)
        if value != "auto" and value != digest and value != "local_only":
            errors.append(f"{inv_dir.name} : EVIDENCE, empreinte fausse pour {rel}")
        if value == "auto" and not fill:
            errors.append(f"{inv_dir.name} : EVIDENCE, empreinte non remplie pour {rel} (--fill)")
        return f"| `{rel}` | {digest} |"

    new_text = EVIDENCE_ROW_RE.sub(resolve, text)
    if fill and new_text != text:
        path.write_text(new_text)


def check_links(md_path, errors):
    for target in LINK_RE.findall(md_path.read_text()):
        if target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        if not (md_path.parent / target.split("#")[0]).exists():
            errors.append(f"{md_path.relative_to(lib.REPO)} : lien cassé {target}")


def check_investigation(inv_dir, known, fill, errors, ids):
    for name in REQUIRED_FILES:
        if not (inv_dir / name).exists():
            errors.append(f"{inv_dir.name} : {name} manquant")
    if any(not (inv_dir / name).exists() for name in ("STATUS.md", "FINDINGS.md", "EVIDENCE.md")):
        return
    fields, _ = lib.parse_status((inv_dir / "STATUS.md").read_text())
    if fields is None:
        errors.append(f"{inv_dir.name} : STATUS.md sans bloc ---")
    else:
        for key in ("id", "title", "state", "updated_utc", "origin", "version"):
            if not fields.get(key):
                errors.append(f"{inv_dir.name} : STATUS.md, champ {key} manquant")
        if fields.get("id") != inv_dir.name:
            errors.append(f"{inv_dir.name} : STATUS.md, id différent du dossier")
        if fields.get("state") not in lib.STATES:
            errors.append(f"{inv_dir.name} : STATUS.md, état inconnu {fields.get('state')}")
    findings = check_findings(inv_dir, errors)
    for finding in findings:
        for other_id, other_finding in re.findall(r"\b([a-z0-9-]+):(F-\d{3,})", finding.get("Links", "")):
            other_path = lib.REPO / "investigations" / other_id / "FINDINGS.md"
            if other_id in ids and other_path.exists():
                other, _ = lib.parse_findings(other_path.read_text())
                if other_finding not in [f["id"] for f in other]:
                    errors.append(f"{inv_dir.name}:{finding['id']} : lien vers {other_id}:{other_finding} inexistant")
    check_manifest(inv_dir, errors)
    fill_or_check_evidence(inv_dir, fill, errors)
    check_scan(inv_dir, known, errors)
    for name in AUTHORED:
        if (inv_dir / name).exists():
            check_links(inv_dir / name, errors)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", nargs="?")
    parser.add_argument("--fill", action="store_true")
    args = parser.parse_args()
    known = lib.known_secret_values(lib.env_files_from_environment())
    errors = []
    ids = {p.name for p in lib.investigation_dirs()}
    if args.target:
        check_investigation(Path(args.target).resolve(), known, args.fill, errors, ids)
    else:
        for inv_dir in lib.investigation_dirs():
            check_investigation(inv_dir, known, args.fill, errors, ids)
        for name in ("README.md", "MASTER_REPORT.md", "INVENTORY.md", "METHODOLOGY.md", "CONTRIBUTING.md"):
            if (lib.REPO / name).exists():
                check_links(lib.REPO / name, errors)
    for line in errors:
        print("ERREUR", line)
    print(f"{len(errors)} erreur(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
