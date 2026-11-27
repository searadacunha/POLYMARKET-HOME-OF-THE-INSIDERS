"""Loader for the null model of integrations/forensic-intelligence, a folder whose modules import each other by flat names.

The folder name has a hyphen, so it is no package, and temporal.py runs `from ledger import ...`. Its ledger.py is
loaded under a private name and lent as `ledger` only while temporal.py executes; sys.path is never touched and
sys.modules keeps whatever it held before.
"""
import importlib.util
import sys

from . import repository_root


def temporal():
    """temporal.py of the repository checkout, or None when the checkout or the file is absent."""
    root = repository_root()
    folder = root / "integrations" / "forensic-intelligence" if root else None
    if folder is None or not (folder / "temporal.py").is_file():
        return None
    saved = sys.modules.get("ledger")
    try:
        loaded = {}
        for name in ("ledger", "temporal"):
            spec = importlib.util.spec_from_file_location(f"phi_forensics._legacy_{name}", folder / f"{name}.py")
            loaded[name] = importlib.util.module_from_spec(spec)
            if name == "temporal":
                sys.modules["ledger"] = loaded["ledger"]
            spec.loader.exec_module(loaded[name])
        return loaded["temporal"]
    finally:
        if saved is None:
            sys.modules.pop("ledger", None)
        else:
            sys.modules["ledger"] = saved
