"""Archive one public answer as evidence: raw bytes, UTC date and SHA-256 in evidence/api/MANIFEST.csv. Guards from net.py. The Etherscan key never reaches the URL written here."""
import csv, datetime, hashlib, re, sys, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import net

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / 'evidence/api'
MANIFEST = DIR / 'MANIFEST.csv'
UA = {'User-Agent': 'Mozilla/5.0 (PolySentinel-ChangeNOW-proof public-read-only)', 'Accept': '*/*'}


def fetch(url, name=None, secret=None, pause=.6):
    """Bytes of a public GET, archived once per name. A refusal is archived too and raises nothing: the caller reads the status. Anti-bot pages are never retried around."""
    DIR.mkdir(parents=True, exist_ok=True)
    name = name or re.sub(r'[^A-Za-z0-9._-]+', '_', urllib.parse.urlsplit(url).netloc + urllib.parse.urlsplit(url).path + '_' + urllib.parse.urlsplit(url).query)[:150]
    path = DIR / name
    if path.exists():
        return 200, path.read_bytes()
    net.guard()
    time.sleep(pause)
    wire = url + (('&' if '?' in url else '?') + urllib.parse.urlencode(secret) if secret else '')
    try:
        with urllib.request.urlopen(urllib.request.Request(wire, headers=UA), timeout=45) as r:
            status, body = r.status, r.read()
    except urllib.error.HTTPError as e:
        status, body = e.code, e.read()
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        status, body = 0, repr(e).encode()
    if status != 200:
        name = name + f'.status{status}'
        path = DIR / name
    path.write_bytes(body)
    new = not MANIFEST.exists()
    with MANIFEST.open('a', newline='') as f:
        w = csv.writer(f)
        if new:
            w.writerow(['file', 'url', 'collected_utc', 'http_status', 'bytes', 'sha256'])
        w.writerow([name, url, datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), status, len(body), hashlib.sha256(body).hexdigest()])
    return status, body
