"""Writes the seal of part A, once, before part B may run."""
import hashlib
import json
import sys
import time
from pathlib import Path

E = Path(__file__).resolve().parent.parent
out = E / 'derived/A_seal.json'
if out.exists():
    sys.exit('A_seal.json already exists: part A is sealed once')
files = ['derived/A_E1.json', 'derived/A_E1G.json', 'derived/A_E2.json', 'derived/A_E3.json', 'derived/A_E4.json', 'derived/A_placebo.json']
out.write_text(json.dumps(dict(sealed_at=time.time(), sha256={f: hashlib.sha256((E / f).read_bytes()).hexdigest() for f in files}), indent=1))
print(out.read_text())
