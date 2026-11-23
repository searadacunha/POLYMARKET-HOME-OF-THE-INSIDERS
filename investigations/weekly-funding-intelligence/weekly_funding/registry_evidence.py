"""Verify registered pool denominations against two pinned upstream source files."""

import hashlib
import re
import urllib.request
from .common import ETH_POOLS, POOLS, SNAP, save

DOCS = "https://raw.githubusercontent.com/tornadocash/docs/b91f1a469ff7c7094e535fd41c4586d1080869c4/general/tornado-cash-smart-contracts.md"
CORE = "https://raw.githubusercontent.com/tornadocash/tornado-core/1ef6a263ac6a0e476d063fcb269a9df65a1bd56a/contracts/Tornado.sol"


def check(v):
    expected = {(137, a): ("POL", str(n * 10**18)) for a, n in POOLS.items()}
    expected.update(
        {(1, a): ("ETH" if t == "native" else "USDC", str(n)) for a, (t, n) in ETH_POOLS.items()}
    )
    actual = {(r["chain"], r["address"]): (r["token"], r["denomination_units"]) for r in v["pools"]}
    if (
        expected != actual
        or len(v["pools"]) != len(expected)
        or v["registry_url"] != DOCS
        or v["contract_url"] != CORE
    ):
        raise ValueError("official pool registry differs from the event decoder")
    if (
        v["event"]
        != "Withdrawal(address to, bytes32 nullifierHash, address indexed relayer, uint256 fee)"
    ):
        raise ValueError("different withdrawal ABI")


def capture():
    from decimal import Decimal

    def fetch(url):
        req = urllib.request.Request(url, headers={"User-Agent": "weekly-funding-research"})
        with urllib.request.urlopen(req, timeout=20) as response:
            return response.read()

    doc, sol = fetch(DOCS), fetch(CORE)
    rows = []
    for chain, link in ((137, "polygonscan.com"), (1, "etherscan.io")):
        allowed = POOLS if chain == 137 else ETH_POOLS
        for line in doc.decode().splitlines():
            m = re.match(
                r"\|\s*([0-9.,]+)\s+(MATIC|ETH|USDC)\s*\|\s*\[(0x[0-9a-fA-F]{40})\]\(https://"
                + re.escape(link)
                + r"/address/(0x[0-9a-fA-F]{40})\)",
                line,
            )
            if not m or m[3].lower() not in allowed or m[3].lower() != m[4].lower():
                continue
            token = "POL" if m[2] == "MATIC" else m[2]
            units = int(Decimal(m[1].replace(",", "")) * 10 ** (6 if token == "USDC" else 18))
            rows.append(
                dict(chain=chain, address=m[3].lower(), token=token, denomination_units=str(units))
            )
    ev = re.search(r"event (Withdrawal\([^;]+\));", sol.decode())
    if not ev:
        raise ValueError("event missing from official source")
    v = dict(
        registry_url=DOCS,
        contract_url=CORE,
        registry_sha256=hashlib.sha256(doc).hexdigest(),
        contract_sha256=hashlib.sha256(sol).hexdigest(),
        event=ev[1],
        pools=rows,
    )
    check(v)
    save(SNAP.parent / "pool_registry.json", v)


if __name__ == "__main__":
    capture()
