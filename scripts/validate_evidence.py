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
import zlib
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phi_lib as lib  # noqa: E402

REQUIRED_FILES = ("README.md", "STATUS.md", "FINDINGS.md", "EVIDENCE.md", "data_manifest.json")
AUTHORED = ("README.md", "STATUS.md", "FINDINGS.md", "EVIDENCE.md")
FULL_HEX_RE = re.compile(r"0x[0-9a-fA-F]{40}(?:[0-9a-fA-F]{24})?\b")
SHORT_HEX_RE = re.compile(r"0x([0-9a-fA-F]{4,})…([0-9a-fA-F]{2,})")
NUMBER_RE = re.compile(r"(?<![\w.,])(?:\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d{1,3}(?: \d{3})+(?:,\d+)?|\d+[.,]\d+|\d{4,}(?![\w-]))")
# Complete numeric tokens in normalized source text, including scientific
# notation and the explicit k/M/B magnitude suffixes used in published reports.
# Do not treat digits embedded in a transaction hash or identifier as evidence.
NUMBER_TOKEN_RE = re.compile(r"(?<![\w.])\d+(?:\.\d+)?(?:[eE][+-]?\d+)?(?:[kKmMbB](?!\w))?(?!\w|\.\d)")
PATH_RE = re.compile(r"(?:^|[\s;`(])((?:sources|results|tests|scripts)/[^\s;`,)]+)")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
EVIDENCE_ROW_RE = re.compile(r"^\| `([^`]+)` \| (auto|[0-9a-f]{64}|local_only) \|", re.M)


def normalize_numbers(text):
    """Same digits whatever the thousands separator: 304 137,63 and 304,137.63 and 304137.63 agree."""
    text = text.replace(" ", " ").replace(" ", " ").replace("−", "-")
    return re.sub(r"(?<=\d)[ ,](?=\d{3}\b)", "", text).replace(",", ".")


def number_value(text, match):
    """Read the full matched number, its adjacent sign and an explicit magnitude.

    Moving the Decimal exponent is exact even for values above the process's
    Decimal precision. A missing sign means positive, not either sign.
    """
    token = normalize_numbers(match.group())
    suffix = re.match(r"[kKmMbB](?!\w)", text[match.end():match.end() + 2])
    if suffix:
        token += suffix.group()
    scale = 0
    if token[-1] in "kKmMbB":
        scale = {"k": 3, "m": 6, "b": 9}[token[-1].lower()]
        token = token[:-1]
    value = Decimal(token)
    prefix = text[max(0, match.start() - 2):match.start()].replace("−", "-")
    sign = re.search(r"([+-])[$€£]?$", prefix)
    if sign and sign.group(1) == "-":
        value = value.copy_negate()
    sign_bit, digits, exponent = value.as_tuple()
    return Decimal((sign_bit, digits, exponent + scale))


def numbers_in_text(text):
    normalized = normalize_numbers(text)
    return {number_value(normalized, match) for match in NUMBER_TOKEN_RE.finditer(normalized)}


def number_in_text(number, text):
    """Whether one complete signed amount occurs in the cited text.

    This checks literal numerical support, not the interpretation or units of a
    claim. Rounded claims require the rounded value in the cited evidence too.
    """
    wanted = numbers_in_text(number)
    return len(wanted) == 1 and wanted.issubset(numbers_in_text(text))


def cited_paths(sources_field):
    return PATH_RE.findall(" " + sources_field)


def read_text(path):
    data = lib.read_for_scan(path)
    return data.decode("utf-8", "ignore")


def source_inside(inv_dir, rel):
    """Resolve a relative path inside its root, rejecting traversal and symlink escapes."""
    if not isinstance(rel, (str, os.PathLike)):
        return None
    path = Path(rel)
    if path.is_absolute() or ".." in path.parts:
        return None
    try:
        root = inv_dir.resolve()
        target = (inv_dir / path).resolve()
    except (OSError, RuntimeError, ValueError):
        return None
    if target != root and root not in target.parents:
        return None
    return target


def check_findings(inv_dir, errors):
    path = inv_dir / "FINDINGS.md"
    text = path.read_text()
    # A malformed finding must not disappear into the optional-section parser.
    for heading in re.findall(r"^##\s+F-[^\n]*$", text, re.M):
        if not lib.FINDING_RE.fullmatch(heading):
            errors.append(f"{inv_dir.name}: malformed finding heading: {heading}")
    findings, _ = lib.parse_findings(text)
    seen = set()
    for finding in findings:
        label = f"{inv_dir.name}:{finding['id']}"
        if finding["id"] in seen:
            errors.append(f"{label}: duplicate id")
        seen.add(finding["id"])
        if finding["level"] not in lib.LEVELS:
            errors.append(f"{label}: unknown level {finding['level']}")
        for bullet in ("Sources", "Method", "Limits", "Links"):
            if not finding.get(bullet, "").strip():
                errors.append(f"{label}: bullet {bullet} missing or empty")
        paths = cited_paths(finding.get("Sources", ""))
        if not paths:
            errors.append(f"{label}: no file cited in Sources")
        corpus = []
        for rel in paths:
            target = source_inside(inv_dir, rel)
            if target is None:
                errors.append(f"{label}: source escapes the investigation {rel}")
            elif not target.exists():
                errors.append(f"{label}: source not found {rel}")
            elif not target.is_file():
                errors.append(f"{label}: source is not a file {rel}")
            else:
                try:
                    corpus.append(read_text(target))
                except (OSError, EOFError, ValueError, zlib.error) as exc:
                    errors.append(f"{label}: source unreadable {rel}: {exc}")
        if not corpus:
            continue
        joined = "\n".join(corpus)
        lower = joined.lower()
        checked = finding["claim"]
        for token in FULL_HEX_RE.findall(checked + " " + finding.get("Sources", "")):
            if token.lower() not in lower:
                errors.append(f"{label}: {token} not in the cited sources")
        for start, end in SHORT_HEX_RE.findall(checked):
            abbreviation = f"0x{start}…{end}".lower()
            address = re.compile(r"0x" + re.escape(start) + r"[0-9a-f]*" + re.escape(end) + r"(?![0-9a-f])", re.I)
            if abbreviation not in lower and not address.search(joined):
                errors.append(f"{label}: {abbreviation} not in the cited sources")
        supported_numbers = numbers_in_text(joined)
        for match in NUMBER_RE.finditer(checked):
            if number_value(checked, match) not in supported_numbers:
                errors.append(f"{label}: the number {match.group()} is not in the cited sources")
    return findings


def check_manifest(inv_dir, errors):
    manifest = lib.load_manifest(inv_dir)
    if manifest is None:
        return
    sources = source_inside(inv_dir, "sources")
    if sources is None:
        errors.append(f"{inv_dir.name}: sources directory escapes the investigation")
        return
    try:
        inv_rel = inv_dir.relative_to(lib.REPO)
    except ValueError:
        errors.append(f"{inv_dir.name}: investigation is outside the repository")
        return
    listed = set()
    for entry in manifest["files"]:
        status = entry.get("status")
        if status not in ("imported", "duplicate"):
            continue
        rel, repo_rel = entry.get("path"), entry.get("repo_path")
        target = source_inside(lib.REPO, repo_rel)
        if target is None:
            errors.append(f"{inv_dir.name}: manifest target escapes the repository {repo_rel}")
            continue
        expected = source_inside(inv_dir / "sources", rel)
        if expected is None:
            errors.append(f"{inv_dir.name}: manifest path escapes sources {rel}")
            continue
        if status == "duplicate":
            if not target.is_file() or lib.sha256_file(target) != entry["sha256"]:
                errors.append(f"{inv_dir.name}: broken duplicate, {entry['path']} points to {entry['repo_path']}")
            continue
        expected_rel = inv_rel / "sources" / rel
        if Path(repo_rel) != expected_rel or target != expected:
            errors.append(f"{inv_dir.name}: imported manifest path does not match its own sources/{rel}")
            continue
        listed.add(str(expected_rel))
        if not target.is_file():
            errors.append(f"{inv_dir.name}: manifest, missing file {entry['repo_path']}")
        elif lib.sha256_file(target) != entry["sha256"]:
            errors.append(f"{inv_dir.name}: hash mismatch {entry['repo_path']}")
    for dirpath, _, filenames in os.walk(inv_dir / "sources"):
        for name in filenames:
            if name == ".DS_Store":
                continue
            rel = str((Path(dirpath) / name).relative_to(lib.REPO))
            if rel not in listed:
                errors.append(f"{inv_dir.name}: file not in manifest {rel}")


def check_scan(inv_dir, known, errors):
    for dirpath, _, filenames in os.walk(inv_dir):
        for name in filenames:
            path = Path(dirpath) / name
            rel = path.relative_to(lib.REPO)
            safe_path = source_inside(inv_dir, path.relative_to(inv_dir))
            if safe_path is None:
                errors.append(f"{rel}: scan path escapes the investigation")
                continue
            size = safe_path.stat().st_size
            if size > lib.MAX_FILE_BYTES and name != "data_manifest.json":
                errors.append(f"{rel}: {size / 1e6:.0f} MB, above the limit")
            if name in (".env",) or name.startswith(".env.") or name.endswith((".pem", ".key")):
                errors.append(f"{rel}: forbidden file name")
            if path.suffix.lower() in lib.IMAGE_EXT:
                continue
            try:
                hits = lib.scan_bytes(lib.read_for_scan(safe_path), known)
            except (OSError, EOFError, gzip.BadGzipFile, ValueError, zlib.error) as exc:
                errors.append(f"{rel}: unreadable by the scan, {type(exc).__name__}")
                continue
            if hits:
                errors.append(f"{rel} : {', '.join(sorted(set(h.split(':')[0] for h in hits)))}")


def fill_or_check_evidence(inv_dir, fill, errors):
    path = inv_dir / "EVIDENCE.md"
    text = path.read_text()
    manifest = lib.load_manifest(inv_dir) or {"files": []}
    by_path = {f"sources/{e['path']}": e for e in manifest["files"]}
    initial_errors = len(errors)

    def resolve(match):
        rel, value = match.group(1), match.group(2)
        target = source_inside(inv_dir, rel)
        if target is None:
            errors.append(f"{inv_dir.name}: EVIDENCE source escapes the investigation {rel}")
            return match.group(0)
        if target.is_file():
            digest = lib.sha256_file(target)
            recorded = by_path.get(rel, {}).get("sha256")
            if recorded and recorded != digest:
                errors.append(f"{inv_dir.name}: EVIDENCE, hash mismatch with manifest for {rel}")
                return match.group(0)
        elif by_path.get(rel, {}).get("sha256"):
            digest = by_path[rel]["sha256"]
        else:
            errors.append(f"{inv_dir.name}: EVIDENCE cites {rel}, neither present nor in the manifest")
            return match.group(0)
        if not fill and value != "auto" and value != digest and value != "local_only":
            errors.append(f"{inv_dir.name}: EVIDENCE, wrong hash for {rel}")
        if value == "auto" and not fill:
            errors.append(f"{inv_dir.name}: EVIDENCE, hash not filled for {rel} (--fill)")
        return f"| `{rel}` | {digest} |"

    # EVIDENCE.md may also contain tables of endpoints, services or facts.
    # Only rows in an explicitly headed SHA-256 table declare file hashes.
    in_hash_table = False
    new_lines = []
    for line in text.splitlines(keepends=True):
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if line.startswith("|") and len(cells) >= 2 and cells[1].upper() == "SHA-256":
            in_hash_table = True
        elif not line.startswith("|"):
            in_hash_table = False
        elif in_hash_table and not re.fullmatch(r"[|\s:-]+", line):
            if not EVIDENCE_ROW_RE.match(line):
                errors.append(f"{inv_dir.name}: malformed evidence row")
            else:
                line = EVIDENCE_ROW_RE.sub(resolve, line)
        new_lines.append(line)
    new_text = "".join(new_lines)
    if fill and len(errors) == initial_errors and new_text != text:
        path.write_text(new_text)


def check_style(md_path, errors):
    if "\u2014" in md_path.read_text():
        errors.append(f"{md_path.relative_to(lib.REPO)}: em dash, use a comma or two sentences")


def check_links(md_path, errors):
    for target in LINK_RE.findall(md_path.read_text()):
        if target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        if not (md_path.parent / target.split("#")[0]).exists():
            errors.append(f"{md_path.relative_to(lib.REPO)}: broken link {target}")


def check_investigation(inv_dir, known, fill, errors, ids):
    initial_errors = len(errors)
    for name in REQUIRED_FILES:
        if not (inv_dir / name).exists():
            errors.append(f"{inv_dir.name}: {name} missing")
    if any(not (inv_dir / name).exists() for name in ("STATUS.md", "FINDINGS.md", "EVIDENCE.md")):
        return
    fields, _ = lib.parse_status((inv_dir / "STATUS.md").read_text())
    if fields is None:
        errors.append(f"{inv_dir.name}: STATUS.md has no --- block")
    else:
        for key in ("id", "title", "state", "updated_utc", "origin", "version"):
            if not fields.get(key):
                errors.append(f"{inv_dir.name}: STATUS.md, field {key} missing")
        if fields.get("id") != inv_dir.name:
            errors.append(f"{inv_dir.name}: STATUS.md, id differs from the folder")
        if fields.get("state") not in lib.STATES:
            errors.append(f"{inv_dir.name}: STATUS.md, unknown state {fields.get('state')}")
    findings = check_findings(inv_dir, errors)
    for finding in findings:
        for other_id, other_finding in re.findall(r"\b([a-z0-9-]+):(F-\d{3,})", finding.get("Links", "")):
            other_path = lib.REPO / "investigations" / other_id / "FINDINGS.md"
            if other_id not in ids or not other_path.is_file():
                errors.append(f"{inv_dir.name}:{finding['id']}: link to missing {other_id}:{other_finding}")
            else:
                other, _ = lib.parse_findings(other_path.read_text())
                if other_finding not in [f["id"] for f in other]:
                    errors.append(f"{inv_dir.name}:{finding['id']}: link to missing {other_id}:{other_finding}")
    check_manifest(inv_dir, errors)
    check_scan(inv_dir, known, errors)
    for name in AUTHORED:
        if (inv_dir / name).exists():
            check_links(inv_dir / name, errors)
            check_style(inv_dir / name, errors)
    # --fill may refresh a correctly re-imported snapshot, but must not rewrite
    # recorded evidence when its sources or the investigation fail validation.
    fill_or_check_evidence(inv_dir, fill and len(errors) == initial_errors, errors)


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
                check_style(lib.REPO / name, errors)
    for line in errors:
        print("ERROR", line)
    print(f"{len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
