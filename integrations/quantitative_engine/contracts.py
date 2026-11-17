"""Protocol eras. V1 and V2 fills are never treated as one population."""

from __future__ import annotations

# Times below are the migration boundary already recorded in
# investigations/maduro-iran/sources/phase10/CLOB_DATA_AUDIT.md.
# poly_data's own reader starts at V2 genesis block 84_902_353 and indexes only
# the binary CTF Exchange V2. That is not coverage of V1, of the overlap, or of
# the neg-risk exchange.
V1_UNTIL_UTC = "2026-04-28T11:00:00Z"
V2_CONTRACTS_FROM_UTC = "2026-04-03T00:00:00Z"

CTF_EXCHANGE_V1 = "0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e"
NEG_RISK_V1 = "0xc5d563a36ae78145c45a50134d48a1215220f80a"
CTF_EXCHANGE_V2 = "0xe111180000d2663c0091e4f400237545b87b996b"
NEG_RISK_V2 = "0xe2222d279d744050d28e00520010520000310f59"
POLY_DATA_V2_GENESIS_BLOCK = 84_902_353

# Pendulum Flow index read on 2026-11-13 from https://archive.pendulumflow.com/
# and the V1 format page. Hour labels are UTC hour starts. V1's last hour that
# actually contains rows is 2026-04-15T08; later V1 objects are empty placeholders.
PENDULUM_WINDOWS = (
    {
        "era": "pmxt_v1",
        "collector": "PMXT",
        "licence": "CC BY 4.0",
        "grade": "snapshot",
        "start": "2026-02-21T18:00:00Z",
        "end_exclusive": "2026-04-15T09:00:00Z",
        "tx_hash": False,
        "wallet": False,
    },
    {
        "era": "pmxt_v2",
        "collector": "PMXT",
        "licence": "CC BY 4.0",
        "grade": "snapshot",
        "start": "2026-04-13T19:00:00Z",
        "end_exclusive": "2026-08-10T00:00:00Z",
        "tx_hash": False,
        "wallet": False,
    },
    {
        "era": "ag6_v2",
        "collector": "AG6",
        "licence": "UNDECLARED",
        "grade": "snapshot",
        "start": "2026-08-01T13:00:00Z",
        "end_exclusive": "2026-08-15T10:00:00Z",
        "tx_hash": False,
        "wallet": False,
    },
    {
        "era": "pendulum_v3",
        "collector": "pendulumflow",
        "licence": "CC BY-NC 4.0",
        "grade": "military",
        "start": "2026-08-18T06:00:00Z",
        "end_exclusive": "2026-10-30T19:00:00Z",
        "tx_hash": True,
        "wallet": False,
    },
    {
        "era": "pendulum_v3_1",
        "collector": "pendulumflow",
        "licence": "CC BY-NC 4.0",
        "grade": "military_beta",
        "start": "2026-10-27T00:00:00Z",
        "end_exclusive": "2026-11-13T14:00:00Z",
        "tx_hash": True,
        "wallet": False,
    },
)

POLY_DATA_MAIN = "136e129735c73bce3a3d59f20354417b188e47fd"
POLY_DATA_V1_FINAL = "23d9138d334a3c7c7ec549bb2adf33b833334611"


def poly_data_v2_claim(timestamp_utc: str, contract: str) -> str:
    """Say what a poly_data V2 row is allowed to support.

    The returned code is a coverage label, not a statement that the row was re-read
    from a node.
    """
    if not isinstance(timestamp_utc, str) or len(timestamp_utc) < 20:
        raise ValueError("timestamp_utc must be an ISO-8601 UTC string")
    if not isinstance(contract, str) or not contract.startswith("0x"):
        raise ValueError("contract address required")
    address = contract.lower()
    if timestamp_utc < V1_UNTIL_UTC:
        return "BEFORE_V1_CUTOVER_NOT_COVERED"
    if address == NEG_RISK_V2:
        return "NEG_RISK_NOT_IN_POLY_DATA"
    if address == CTF_EXCHANGE_V1 or address == NEG_RISK_V1:
        return "V1_CONTRACT_NOT_IN_POLY_DATA"
    if address != CTF_EXCHANGE_V2:
        return "OTHER_CONTRACT_NOT_IN_POLY_DATA"
    return "SINGLE_V2_CONTRACT_ONLY"
