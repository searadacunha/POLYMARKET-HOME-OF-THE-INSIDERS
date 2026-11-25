"""Cash ledger for public activity rows: TRADE, SPLIT, MERGE, REDEEM, CONVERSION.

Rows are the fields kept by public_fetch.py. Profile fields are not read.
A SPLIT pays USDC and creates one share of every outcome. A MERGE does the
reverse. A REDEEM pays USDC and closes the named outcome. Unseen types are
counted and left out of the cash sum.
"""

from collections import defaultdict
from decimal import Decimal

D0 = Decimal("0")
KNOWN = {"TRADE", "SPLIT", "MERGE", "REDEEM", "CONVERSION"}


def _dec(value) -> Decimal:
    number = Decimal(str(value if value is not None else "0"))
    if not number.is_finite():
        raise ValueError("non-finite amount")
    return number


def apply_row(cash, shares, row):
    kind = str(row.get("type") or "TRADE")
    usdc = _dec(row.get("usdc_size"))
    size = _dec(row.get("size"))
    outcome = str(row.get("outcome") or "")
    if kind == "TRADE":
        side = str(row.get("side") or "").upper()
        if side == "BUY":
            return cash - usdc, _add(shares, outcome, size)
        if side == "SELL":
            return cash + usdc, _add(shares, outcome, -size)
        raise ValueError("trade without a side")
    if kind == "REDEEM":
        return cash + usdc, _add(shares, outcome, -size)
    if kind == "SPLIT":
        # Collateral in, one share of each already-seen outcome is not knowable
        # from this row alone. The cash leg is the part the activity row states.
        return cash - usdc, shares
    if kind == "MERGE":
        return cash + usdc, shares
    if kind == "CONVERSION":
        return cash, shares
    raise ValueError("unsupported type")


def _add(shares, outcome, delta):
    nxt = dict(shares)
    nxt[outcome] = nxt.get(outcome, D0) + delta
    return nxt


def market_cash(rows, condition_id: str) -> dict:
    chosen = [row for row in rows if str(row.get("condition_id") or "").lower() == condition_id.lower()]
    cash = D0
    shares = {}
    counts = defaultdict(int)
    unknown = defaultdict(int)
    for row in chosen:
        kind = str(row.get("type") or "TRADE")
        counts[kind] += 1
        if kind not in KNOWN:
            unknown[kind] += 1
            continue
        cash, shares = apply_row(cash, shares, row)
    return {
        "rows": len(chosen),
        "cash": format(cash, "f"),
        "open_shares": {key: format(value, "f") for key, value in shares.items()},
        "counts": dict(counts),
        "unknown_types": dict(unknown),
    }
