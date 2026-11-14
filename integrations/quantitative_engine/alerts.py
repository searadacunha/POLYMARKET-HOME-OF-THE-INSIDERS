"""Early-warning records. A score is not an accusation.

Archive hours are delayed. This module never labels an archive replay as a
live alert.
"""

from __future__ import annotations


def promote(rows: list[dict], evaluation: dict, latency_class: str) -> dict:
    if latency_class not in ("ARCHIVE_HOURLY", "VENUE_STREAM"):
        raise ValueError("latency class must say whether the source is delayed")
    passed = set(evaluation["patterns_passing_validation"])
    emitted = []
    seen = set()
    withheld = 0
    for row in rows:
        if row["split"] != "validation":
            continue
        if row["wallet"] is not None:
            raise ValueError("a book or venue print in this pipeline has no wallet")
        fired = _fired(row)
        if not fired:
            continue
        key = (row.get("tx"), row["asset"], tuple(sorted(fired)))
        if key in seen:
            withheld += 1
            continue
        seen.add(key)
        surviving = [name for name in fired if name in passed]
        if not surviving:
            withheld += 1
            continue
        emitted.append({
            "market": row.get("market"),
            "asset": row["asset"],
            "wallet": None,
            "wallet_status": "NOT_IDENTIFIABLE_FROM_BOOK_OR_PRINT",
            "timestamp_utc_ms": row["ts"],
            "transaction_hash": row.get("tx"),
            "chain_receipt_checked": False,
            "object_kind": row["object_kind"],
            "anomaly": surviving,
            "observed": {
                "side": row["side"],
                "spread_1e4": row["spread_1e4"],
                "consumption": row["consumption"],
                "burst_gap_ms": row["burst_gap_ms"],
            },
            "statistical_reference": {
                name: evaluation["tests"][name]["decision"] for name in surviving
            },
            "anomaly_score": None,
            "confidence": "NOT_ASSIGNED",
            "reason": "A hypothesis that passes a pre-registered control test still does not identify a person or prove non-public information.",
            "alternatives": ["market_making", "thin_book", "public_information", "venue_print_without_chain_receipt"],
            "sources": ["pendulumflow CC BY-NC 4.0 preview hour, venue print plus prior book"],
            "validation_state": "PASSES_VALIDATION",
            "latency_class": latency_class,
            "live_claim": latency_class == "VENUE_STREAM",
            "accusation": "NONE",
        })
    return {
        "latency_class": latency_class,
        "live_claim": latency_class == "VENUE_STREAM",
        "emitted": emitted,
        "withheld": withheld,
    }


def _fired(row: dict) -> list[str]:
    from validation import _flag
    return [name for name in (
        "H1_DEPTH_CONSUMPTION", "H2_WIDE_SPREAD", "H3_PRINT_BURST",
    ) if _flag(row, name)]
