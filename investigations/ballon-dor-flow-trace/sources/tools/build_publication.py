"""Builds publish/origin, the folder given to the central repository's import_snapshot.py: same layout as this project, so that scripts keep their relative paths. Local only: no git, no network.
Left out on purpose: state/http_cache (raw answers, some carry profile fields) and the raw label dumps (third-party, kept as hashes and URLs)."""
import json
import os
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'publish/origin'
TREES = ['reports', 'data', 'graphs', 'tools', 'tests', 'evidence/docs', 'evidence/relay']
FILES = ['evidence/blockscout_tags.json', 'evidence/labels/SHA256SUMS', 'JOURNAL_AGENTS.md', 'README.md']
SOURCES_NOTE = """# Listes d'étiquettes tierces, non copiées

`tools/labels.py` lit ces fichiers. Pour relancer les scripts, les télécharger ici, puis contrôler avec `shasum -a 256 -c SHA256SUMS` :

- `brianleect/<nom>.json` : https://raw.githubusercontent.com/brianleect/etherscan-labels/main/data/<nom>/combined/combinedAllLabels.json, pour etherscan, polygonscan, arbiscan, bscscan, optimism
- `dawsbot/accounts.json` : https://raw.githubusercontent.com/dawsbot/eth-labels/v1/data/json/accounts.json

Lus le 2026-11-02. Le dépôt dawsbot change : l'empreinte peut ne plus correspondre à une lecture ultérieure.
"""


def secret_values():
    values = []
    for path in (Path.home() / 'Downloads/.env', Path.home() / '.env'):
        if path.exists():
            for line in path.read_text(errors='ignore').splitlines():
                if '=' in line and not line.strip().startswith('#'):
                    v = line.split('=', 1)[1].strip().strip('"\'')
                    if len(v) >= 16 and not v.startswith(('http://', 'https://')):
                        values.append(v)
                    elif v.startswith('http') and re.search(r'[?&/](api[-_]?key=)?[A-Za-z0-9_-]{24,}', v):
                        values.append(v)
    return values


PATTERNS = [rb'gh[pousr]_[A-Za-z0-9]{20,}', rb'github_pat_[A-Za-z0-9_]{20,}', rb'(?<![A-Za-z0-9-])sk-[A-Za-z0-9_-]{20,}', rb'-----BEGIN [A-Z ]*PRIVATE KEY', rb'\b\d{8,10}:[A-Za-z0-9_-]{30,}\b', rb'apikey=[A-Za-z0-9]{10,}', rb'api-key=[A-Za-z0-9-]{10,}', rb'[A-Za-z0-9._%+-]+@gmail\.com', rb'"bio": ?"[^"]*', rb'"pseudonym": ?"', rb'"profile_image[a-z_]*": ?"']


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    for tree in TREES:
        shutil.copytree(ROOT / tree, OUT / tree, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for name in FILES:
        (OUT / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, OUT / name)
    (OUT / 'evidence/labels/SOURCES.md').write_text(SOURCES_NOTE)
    shutil.copytree(ROOT / 'state', OUT / 'state', ignore=shutil.ignore_patterns('http_cache', '__pycache__', '*.pyc'))
    # scan before anything can leave this Mac
    secrets = [v.encode() for v in secret_values()]
    bad = []
    for d, _, fs in os.walk(OUT):
        for f in fs:
            p = Path(d) / f
            body = p.read_bytes()
            for pat in PATTERNS:
                if re.search(pat, body):
                    bad.append((str(p.relative_to(OUT)), pat.decode()[:24]))
            if any(v in body for v in secrets):
                bad.append((str(p.relative_to(OUT)), 'value from a .env file'))
            if len(body) > 25_000_000:
                bad.append((str(p.relative_to(OUT)), 'over 25 MB'))
    total = sum((Path(d) / f).stat().st_size for d, _, fs in os.walk(OUT) for f in fs)
    print('files', sum(len(fs) for _, _, fs in os.walk(OUT)), 'bytes', total, 'secret scan findings', len(bad))
    for b in bad[:30]:
        print('  ', b)
    return 1 if bad else 0


if __name__ == '__main__':
    raise SystemExit(main())
