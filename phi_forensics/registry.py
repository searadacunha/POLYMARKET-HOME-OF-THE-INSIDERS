"""Addresses with a known role: the protocol's own contracts and a seed list of services.

Protocol contracts come from the verified registry published with the data-completion investigation (each role was
read from the chain there). Service labels are a seed list; each names the file of this repository that records
it. An address in neither list is not assumed to be a person: it is classified by its behaviour on the chain.
"""
import json
import re
from functools import lru_cache
from pathlib import Path

from . import repository_root

DATA = Path(__file__).resolve().parent / "data"
SEMANTICS = "investigations/data-completion-20261123/results/contract_semantics.json"


def _from_semantics(document):
    return [{"address": address, "name": c["name"], "generation": c.get("generation"), "role": c["role"]}
            for c in document["contracts"] for address in re.findall(r"0x[0-9a-f]{40}", c["address"])]


@lru_cache(maxsize=1)
def protocol_contracts():
    """{address: {"name", "role", "generation"}} for the exchange, token, collateral, fee and factory contracts."""
    root = repository_root()
    if root and (root / SEMANTICS).exists():
        rows = _from_semantics(json.loads((root / SEMANTICS).read_text(encoding="utf-8")))
    else:  # installed without the checkout: the copy generated from the same file
        rows = json.loads((DATA / "protocol_contracts.json").read_text(encoding="utf-8"))["contracts"]
    return {row["address"]: {k: row[k] for k in ("name", "role", "generation")} for row in rows}


@lru_cache(maxsize=1)
def service_labels():
    """{address: {"label", "service", "source"}} for bridges, swap services, mixers and exchange wallets."""
    rows = json.loads((DATA / "service_labels.json").read_text(encoding="utf-8"))["labels"]
    return {row["address"]: {k: row[k] for k in ("label", "service", "source")} for row in rows}


# Names of the registry through which collateral is wrapped or unwrapped. A transfer of pUSD to the pUSD contract itself
# unwraps it and pays the underlying stablecoin to an address the sender's own transfers do not show.
RAMPS = {"pUSD", "pUSD USDC.e reserve", "CollateralOnramp", "CollateralOfframp"}


def is_collateral_ramp(address):
    """True for an address through which collateral enters or leaves the protocol without a trade: mint or burn, wrap or unwrap."""
    info = known(address)
    return bool(info) and (info["kind"] == "mint" or info.get("label") in RAMPS)


def known(address):
    """The class of an address the registries know, or None: never a guess."""
    address = address.lower()
    if address == "0x" + "0" * 40:
        return {"kind": "mint", "label": "zero address (mint or burn)"}
    if address in protocol_contracts():
        return {"kind": "protocol", "label": protocol_contracts()[address]["name"], "source": SEMANTICS}
    if address in service_labels():
        entry = service_labels()[address]
        return {"kind": "labelled_service", "label": entry["label"], "service": entry["service"], "source": entry["source"]}
    return None
