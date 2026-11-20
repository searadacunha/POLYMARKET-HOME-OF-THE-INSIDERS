"""Conservative receipt matcher for the active phi_engine (read-only).

The original chainfund.py is a frozen, hash-locked study dependency and is
intentionally preserved byte-for-byte. This additive guard is used only by
the live engine; it does not rewrite historical research outcomes.
"""
from . import chainfund


def payer_of_deposit(logs, wallet):
    """Identify a receipt-level apparent payer only where amount and log order agree.

    Equal-sized ERC-20 chainfund.transfers are fungible: their equality alone is not a
    unique pay-in/payout link. Ambiguous candidates are explicitly unresolved.
    A sole in-transaction upstream hop is still only a possible economic path,
    not proof of human control or the origin of all balances.
    """
    wallet = wallet.lower()
    tr = chainfund.transfers(logs)
    credits = [t for t in tr if t["to"] == wallet and t["value"] > 0]
    if not credits:
        return None
    largest = max(t["value"] for t in credits)
    top = [t for t in credits if t["value"] == largest]
    if len(top) != 1:
        return {"payer": None, "via": "ambiguous_credit", "token": None,
                "value": largest, "path": [], "unresolved": "multiple_maximal_credits"}
    c = top[0]
    if c["from"] == chainfund.ZERO or c["from"] in chainfund.INFRA:
        # Minted or released collateral: a source leg must be uniquely
        # identifiable *before* the credit, never inferred from a later log.
        candidates = [t for t in tr if t["token"] in (chainfund.USDC, chainfund.USDC_E)
                      and t["to"] in chainfund.INFRA and t["from"] not in chainfund.INFRA
                      and t["value"] == c["value"] and c["log_index"] is not None
                      and t["log_index"] is not None and t["log_index"] < c["log_index"]]
        if len(candidates) != 1:
            return {"payer": None,
                    "via": "wrapped_unmatched" if not candidates else "wrapped_ambiguous",
                    "token": c["token"], "value": c["value"], "path": [],
                    "unresolved": "missing_ordered_source" if not candidates else "multiple_equal_value_sources"}
        src = candidates[0]
        found = {"payer": src["from"], "via": "wrapped", "token": src["token"],
                 "value": src["value"], "path": []}
        cursor = src["log_index"]
    else:
        # The immediate payer is directly named by the confirmed Transfer log.
        found = {"payer": c["from"], "via": "direct", "token": c["token"],
                 "value": c["value"], "path": []}
        cursor = c["log_index"]
    for _ in range(6):
        # Never cross a token boundary or look after the transfer being
        # explained. Multiple equally plausible pay-ins must not be selected
        # by their incidental ordering in the receipt.
        possible = [t for t in tr if t["to"] == found["payer"]
                    and t["from"] != found["payer"] and t["from"] not in chainfund.INFRA
                    and t["from"] != wallet and t["token"] == found["token"]
                    and t["value"] == found["value"] and cursor is not None
                    and t["log_index"] is not None and t["log_index"] < cursor]
        if len(possible) != 1:
            if len(possible) > 1:
                found["unresolved"] = "ambiguous_upstream_equal_value_candidates"
            break
        prev = possible[0]
        found["path"].append(found["payer"])
        found["payer"] = prev["from"]
        cursor = prev["log_index"]
    return found

