"""Shared helpers: hashing and the scan that keeps secrets and profile data out of the repo."""
import hashlib
import json
import os
import re
import struct
import zlib
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
# Agent working files stay on the Mac, as in the owner's public repositories.
AGENT_FILES = {"JOURNAL_AGENTS.md", "AGENTS.md", "CLAUDE.md"}


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


def load_known_digests(path=None):
    """Known secrets as digests only: a service can refuse a value without holding it in clear."""
    path = path or os.environ.get("PHI_KNOWN_DIGESTS")
    try:
        return json.loads(Path(path).read_text()) if path else []
    except (OSError, ValueError):
        return []


def digest_entries(values):
    """values: {secret bytes: variable name}. The first 4 bytes only speed up the search."""
    return [{"key": key, "len": len(value), "prefix": value[:4].hex(), "sha": hashlib.sha256(value).hexdigest()} for value, key in values.items()]


def digest_hits(data, entries):
    hits = []
    for entry in entries:
        prefix, pos = bytes.fromhex(entry["prefix"]), 0
        while True:
            pos = data.find(prefix, pos)
            if pos < 0:
                break
            if hashlib.sha256(data[pos:pos + entry["len"]]).hexdigest() == entry["sha"]:
                hits.append(f"known_secret:{entry['key']}")
                break
            pos += 1
    return hits


KNOWN_DIGESTS = load_known_digests()


def scan_bytes(data, known=None):
    """Return the names of what was found. Never returns the matched value."""
    hits = [name for name, rx in SECRET_RES if rx.search(data)]
    if PROFILE_RE.search(data):
        hits.append("profile_fields")
    for value, key in (known or {}).items():
        if value in data:
            hits.append(f"known_secret:{key}")
    return hits + digest_hits(data, KNOWN_DIGESTS)


class GzipScanLimit(ValueError):
    """A complete scan would exceed a resource limit; never a clean result."""


MAX_GZ_HEADER_BYTES = 1 << 20
GZ_CHUNK_BYTES = 1 << 16


class _GzipInput:
    """Bounded reads plus at most one compressed chunk of lookahead."""

    def __init__(self, source, limit):
        self.source = source
        self.limit = limit
        self.used = 0
        self.pending = b""

    def some(self):
        if self.pending:
            data, self.pending = self.pending, b""
            return data
        data = self.source.read(min(GZ_CHUNK_BYTES, self.limit - self.used + 1))
        self.used += len(data)
        if self.used > self.limit:
            raise GzipScanLimit("compressed gzip input exceeds the scan limit")
        return data

    def put_back(self, data):
        self.pending = data + self.pending

    def exact(self, size):
        result = bytearray()
        while len(result) < size:
            data = self.some()
            if not data:
                raise EOFError("truncated gzip member")
            take = min(size - len(result), len(data))
            result.extend(data[:take])
            self.put_back(data[take:])
        return bytes(result)


def iter_gzip_for_scan(source, max_bytes):
    """Yield all member bodies, then their plaintext header fields.

    Bodies remain contiguous, so a token split over members is still detected.
    Compressed reads, decoded output and accumulated metadata are bounded. CRC,
    ISIZE and optional header CRC are checked for every member; truncated input
    or an exceeded bound raises rather than producing a partial clean result.
    """
    reader = _GzipInput(source, max_bytes + MAX_GZ_HEADER_BYTES)
    metadata = bytearray()
    header_size = total = members = 0
    while True:
        lead = reader.some()
        if members:
            # gzip permits zero padding after/between complete members.
            while lead and not lead.lstrip(b"\0"):
                lead = reader.some()
            lead = lead.lstrip(b"\0")
        if not lead:
            if not members:
                raise ValueError("empty gzip stream")
            break
        reader.put_back(lead)
        header = bytearray(reader.exact(10))
        if header[:3] != b"\x1f\x8b\x08" or header[3] & 0xe0:
            raise ValueError("invalid gzip header")
        flags = header[3]

        def add_field(field):
            metadata.extend(field)
            metadata.extend(b"\n")
            if header_size + len(header) > MAX_GZ_HEADER_BYTES:
                raise GzipScanLimit("gzip headers exceed the scan limit")

        if flags & 0x04:
            length_bytes = reader.exact(2)
            header.extend(length_bytes)
            field = reader.exact(int.from_bytes(length_bytes, "little"))
            header.extend(field)
            add_field(field)
        for flag in (0x08, 0x10):
            if flags & flag:
                field = bytearray()
                while True:
                    data = reader.some()
                    if not data:
                        raise EOFError("truncated gzip header field")
                    index = data.find(b"\0")
                    part = data if index < 0 else data[:index + 1]
                    header.extend(part)
                    if header_size + len(header) > MAX_GZ_HEADER_BYTES:
                        raise GzipScanLimit("gzip headers exceed the scan limit")
                    field.extend(part if index < 0 else part[:-1])
                    if index >= 0:
                        reader.put_back(data[index + 1:])
                        break
                add_field(field)
        if flags & 0x02:
            expected = int.from_bytes(reader.exact(2), "little")
            if expected != zlib.crc32(header) & 0xffff:
                raise ValueError("gzip header CRC mismatch")
        header_size += len(header) + (2 if flags & 0x02 else 0)
        if header_size > MAX_GZ_HEADER_BYTES:
            raise GzipScanLimit("gzip headers exceed the scan limit")
        decoder = zlib.decompressobj(-zlib.MAX_WBITS)
        checksum = decoded_size = 0
        compressed = reader.some()
        while True:
            if not compressed:
                raise EOFError("truncated gzip deflate stream")
            chunk = decoder.decompress(compressed, GZ_CHUNK_BYTES)
            checksum = zlib.crc32(chunk, checksum)
            decoded_size += len(chunk)
            total += len(chunk)
            if total + len(metadata) > max_bytes:
                raise GzipScanLimit("decompressed content exceeds the scan limit")
            if chunk:
                yield chunk
            if decoder.eof:
                reader.put_back(decoder.unused_data)
                break
            compressed = decoder.unconsumed_tail or reader.some()
        expected_crc, expected_size = struct.unpack("<II", reader.exact(8))
        if checksum != expected_crc or decoded_size & 0xffffffff != expected_size:
            raise ValueError("gzip body CRC or length mismatch")
        members += 1
    if metadata:
        if total + len(metadata) + 1 > max_bytes:
            raise GzipScanLimit("decompressed content and headers exceed the scan limit")
        yield b"\n" + bytes(metadata)


def read_for_scan(path):
    """Read bounded decoded gzip bodies and metadata; otherwise read the file."""
    with open(path, "rb") as fh:
        if str(path).lower().endswith(".gz"):
            return b"".join(iter_gzip_for_scan(fh, MAX_GZ_SCAN_BYTES))
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
OPTIONAL_SECTIONS = ("Contradictions", "Missing to conclude", "Prospective monitoring")


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
