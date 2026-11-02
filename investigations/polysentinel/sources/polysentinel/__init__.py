"""PolySentinel: surveillance publique en lecture seule."""
__version__ = '0.1.0'

# Pin before package modules load; activation requires a cold process with these same files.
import hashlib as _hashlib
from pathlib import Path as _Path
_PACKAGE_DIRECTORY = _Path(__file__).resolve().parent
STARTUP_CODE_HASHES = {p.name:_hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in sorted(_PACKAGE_DIRECTORY.glob('*.py'))}
