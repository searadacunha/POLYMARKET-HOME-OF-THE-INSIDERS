"""Shared helpers: hashing and the scan that keeps secrets and profile data out of the repo."""
import gzip
import hashlib
import json
import os
import re
from pathlib import Path
from urllib.parse import urlsplit

REPO = Path(__file__).resolve().parent.parent
MAX_FILE_BYTES = 25_000_000
MAX_GZ_SCAN_BYTES = 300_000_000
LEVELS = ("CONFIRMED", "SUPPORTED", "HYPOTHESIS", "REFUTED", "UNRESOLVED")
STATES = ("IN_PROGRESS", "DONE", "PAUSED", "ABANDONED")

# Values are at least 16 characters so that variable names and short placeholders do not match.
SECRET_RES = [(name, re.compile(rx)) for name, rx in [
    ("key_assignment", rb"(?i)(?:api[_-]?key|apikey|access[_-]?token|auth[_-]?token|client[_-]?secret|password|passwd)[\"'\s]*[:=][\"'\s]*(?!os\.|env|None|null|your|YOUR|<|\$|\{|xxx|XXX|\*)[A-Za-z0-9_\-\.]{16,}(?![A-Za-z0-9_\-\.(])"),
    ("url_key", rb"(?i)[?&](?:api[_-]?key|apikey|token|access_token|key)=(?!\{|<|\$|YOUR|your|xxx|XXX|\*)[A-Za-z0-9_\-]{16,}"),
    ("bearer", rb"(?i)\bbearer\s+(?!\{|<|\$|YOUR|your|xxx)[A-Za-z0-9_\-\.=]{20,}"),
    ("github_token", rb"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{40,})\b"),
    ("provider_key", rb"\b(?:sk-[A-Za-z0-9\-_]{24,}|xox[baprs]-[A-Za-z0-9\-]{20,}|AKIA[0-9A-Z]{16})\b"),
    ("private_key_block", rb"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    ("private_key_value", rb"(?i)(?:private[_ -]?key|privkey|secret[_ -]?key|seed[_ -]?phrase|mnemonic)[\"'\s]*[:=][\"'\s]*(?:0x)?[0-9a-z ]{32,}"),
    ("telegram_token", rb"\b\d{8,10}:[A-Za-z0-9_-]{35}\b"),
    ("cookie", rb"(?i)\b(?:set-cookie|cookie)[\"']?\s*:\s*[\"']?[A-Za-z0-9_\-]+=[^\s\"';]{12,}"),
]]
# Polymarket API rows carry these profile fields next to the wallet: never publish them.
PROFILE_RE = re.compile(rb"[\"'](?:bio|pseudonym|profileImage|profileImageOptimized|displayUsernamePublic)[\"']\s*:\s*[\"'][^\"']")
TEXT_EXT = {".py", ".md", ".txt", ".json", ".jsonl", ".csv", ".tsv", ".sh", ".command", ".plist", ".toml",
            ".yaml", ".yml", ".lock", ".in", ".html", ".graphml", ".sha256", ".log", ".sb", ".out", ".err",
            ".ipynb", ".js", ".svg", ".cfg", ".ini", ".sql", ".bak", ".gitignore", ""}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf"}


# A watched service wallet (SOURCE_WALLET) is public; the owner's own proxy address is not for publication.
SENSITIVE_ENV_NAME = re.compile(r"KEY|SECRET|TOKEN|PASS|PRIVATE|API_HASH|PROXY_ADDRESS")


def is_sensitive_env(name, value):
    """A public API URL or a user name in a .env file must not refuse every script that cites it."""
    if SENSITIVE_ENV_NAME.search(name):
        return True
    if "://" in value:
        parts = urlsplit(value)
        return "@" in parts.netloc or bool(re.search(r"[A-Za-z0-9_-]{20,}", parts.path + "?" + parts.query))
    return False


def known_secret_values(env_files):
    """Values of KEY=VALUE files, used only to refuse any exact occurrence. Never printed."""
    values = {}
    for path in env_files:
        try:
            lines = Path(path).expanduser().read_text(errors="ignore").splitlines()
        except OSError:
            continue
        for line in lines:
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            value = value.strip().strip("\"'")
            key = key.replace("export ", "").strip()
            if len(value) >= 12 and is_sensitive_env(key, value):
                values[value.encode()] = key
    return values


def env_files_from_environment():
    return [p for p in os.environ.get("PHI_ENV_FILES", "").split(":") if p]


def scan_bytes(data, known=None):
    """Return the names of what was found. Never returns the matched value."""
    hits = [name for name, rx in SECRET_RES if rx.search(data)]
    if PROFILE_RE.search(data):
        hits.append("profile_fields")
    for value, key in (known or {}).items():
        if value in data:
            hits.append(f"known_secret:{key}")
    return hits


def read_for_scan(path):
    """Bytes to scan: the file itself, decompressed when gzip. Bounded, streaming into one buffer."""
    if str(path).endswith(".gz"):
        with gzip.open(path, "rb") as fh:
            return fh.read(MAX_GZ_SCAN_BYTES)
    with open(path, "rb") as fh:
        return fh.read()


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(inv_dir):
    path = Path(inv_dir) / "data_manifest.json"
    return json.loads(path.read_text()) if path.exists() else None


def parse_status(text):
    match = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if not match:
        return None, text
    fields = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    return fields, match.group(2)


FINDING_RE = re.compile(r"^## (F-\d{3,}) \| ([A-Z]+) \| (.+)$", re.M)
BULLET_RE = re.compile(r"^- (Sources|Method|Limits|Links): (.*)$", re.M)
OPTIONAL_SECTIONS = ("Contradictions", "Manque pour conclure", "Surveillance prospective")


def parse_findings(text):
    """Return (findings, optional sections). A finding runs up to the next level-2 heading."""
    findings = []
    heads = list(re.finditer(r"^## .*$", text, re.M))
    sections = {}
    for i, head in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        body = text[head.end():end]
        line = head.group(0)
        match = FINDING_RE.match(line)
        if match:
            bullets = dict(BULLET_RE.findall(body))
            findings.append({"id": match.group(1), "level": match.group(2), "claim": match.group(3).strip(), **bullets})
        else:
            title = line[3:].strip()
            sections[title] = [b[2:].strip() for b in body.splitlines() if b.startswith("- ")]
    return findings, sections


def investigation_dirs():
    root = REPO / "investigations"
    return sorted(p for p in root.iterdir() if p.is_dir()) if root.exists() else []
