"""Read-only forensic toolkit for on-chain investigation of Polymarket wallets and markets.

Standard library only. Every function reads public data (Polymarket APIs, Polygon nodes, the archives of this
repository) and never signs, trades or writes outside its own cache. Results carry their sources and their limits:
a transfer is a movement of money, never an identity.
"""
import os
from pathlib import Path

__version__ = "0.1.0"


def repository_root():
    """The checkout that holds the published investigations, or None when the package is installed without it.

    PHI_REPO_ROOT overrides the location. Archive tools need the checkout; live tools do not.
    """
    for candidate in (os.environ.get("PHI_REPO_ROOT"), Path(__file__).resolve().parents[1]):
        if candidate and (Path(candidate) / "investigations").is_dir() and (Path(candidate) / "research_notes").is_dir():
            return Path(candidate).resolve()
    return None
