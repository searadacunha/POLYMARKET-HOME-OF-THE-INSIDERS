"""Pre-jump description of one selected market tape.

The cohort was named by a third party after the market resolved. A rank inside
that tape is not a prospective detector and not a probability of non-public
information. Thresholds are fixed: a Yes buy at price 0.50 or more is the jump,
and 5,000 USDC is the large-buyer line.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

JUMP_PRICE = 0.50
LARGE_USDC = 5000.0
SEED = 20261113
PERMUTATIONS = 2000

# Addresses already published in research_notes/inca-crosscheck-2026-11-06/REPORT.md.
COHORT = {
    "0x6c2c072a0aa8fb8b4faf9aecae5520541f3b2d2a": "9TungSahur",
    "0xd5de5cad9ef22b16317fe30a4234c72ece3eac1a": "PorcoRosso",
    "0x0afc7ce56285bde1fbe3a75efaffdfc86d6530b2": "ricosuave666",
    "0xcb18ea2923d957bd9cf049cce60a87638722f867": "DonkeyDonkey999",
    "0xa3a6fa49a39a4bf84cf510b7c8a2ab8be8508c44": "truthlord",
}


def load_tape(directory: Path) -> list[dict]:
    rows = []
    seen = set()
    for path in sorted(directory.glob("p*.json")):
        if path.name.endswith(".meta.json"):
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        for row in payload.get("data") or []:
            key = (
                str(row.get("transaction_hash") or ""),
                str(row.get("proxy_wallet") or "").lower(),
                row.get("timestamp"),
                row.get("side"),
                row.get("outcome"),
                row.get("size"),
                row.get("price"),
            )
            if key in seen:
                continue
            seen.add(key)
            rows.append(row)
    return rows


def _yes_buys(rows: list[dict]) -> list[dict]:
    kept = []
    for row in rows:
        if row.get("outcome") != "Yes" or row.get("side") != "BUY":
            continue
        price, size = row.get("price"), row.get("size")
        if not isinstance(price, (int, float)) or not isinstance(size, (int, float)):
            continue
        if price < 0 or size < 0:
            continue
        wallet = str(row.get("proxy_wallet") or "").lower()
        if not wallet.startswith("0x") or len(wallet) != 42:
            continue
        kept.append({
            "wallet": wallet,
            "timestamp": int(row["timestamp"]),
            "price": float(price),
            "notional": float(price) * float(size),
        })
    kept.sort(key=lambda item: (item["timestamp"], item["wallet"]))
    return kept


def prejump(rows: list[dict], cohort: dict[str, str] | None = None) -> dict:
    """Describe Yes buys strictly before the first Yes buy at or above the jump price.

    ``cohort`` only labels wallets. It is not used to choose the jump or the threshold.
    """
    names = {key.lower(): value for key, value in (cohort or COHORT).items()}
    buys = _yes_buys(rows)
    jump = next((item for item in buys if item["price"] >= JUMP_PRICE), None)
    if jump is None:
        return {"status": "NO_JUMP", "yes_buys": len(buys)}
    before = [item for item in buys if item["timestamp"] < jump["timestamp"]]
    by_wallet = {}
    for item in before:
        slot = by_wallet.setdefault(item["wallet"], {"notional": 0.0, "first": item["timestamp"], "trades": 0})
        slot["notional"] += item["notional"]
        slot["first"] = min(slot["first"], item["timestamp"])
        slot["trades"] += 1
    ranked = sorted(by_wallet.items(), key=lambda pair: -pair[1]["notional"])
    large = [wallet for wallet, slot in ranked if slot["notional"] >= LARGE_USDC]
    cohort_rows = []
    for wallet, name in sorted(names.items()):
        slot = by_wallet.get(wallet)
        rank = next((index + 1 for index, (addr, _) in enumerate(ranked) if addr == wallet), None)
        cohort_rows.append({
            "wallet": wallet,
            "name": name,
            "prejump_notional": None if slot is None else round(slot["notional"], 2),
            "first_timestamp": None if slot is None else slot["first"],
            "rank_by_notional": rank,
            "large": wallet in large,
        })
    notionals = [slot["notional"] for _, slot in ranked]
    cohort_present = [wallet for wallet in names if wallet in by_wallet]
    observed = sum(by_wallet[wallet]["notional"] for wallet in cohort_present)
    perm = _permutation(notionals, len(cohort_present), observed) if cohort_present else None
    return {
        "status": "DESCRIBED",
        "selection": "COHORT_NAMED_AFTER_RESOLUTION",
        "prospective_detector": False,
        "insider_probability": None,
        "jump_timestamp": jump["timestamp"],
        "jump_price": jump["price"],
        "yes_buys": len(buys),
        "prejump_yes_buys": len(before),
        "prejump_wallets": len(ranked),
        "large_prejump_wallets": len(large),
        "large_line_usdc": LARGE_USDC,
        "large_base_rate": (len(large) / len(ranked)) if ranked else None,
        "cohort_in_prejump": len(cohort_present),
        "cohort_large": sum(1 for row in cohort_rows if row["large"]),
        "other_large_wallets": len(large) - sum(1 for row in cohort_rows if row["large"]),
        "cohort_notional": round(observed, 2),
        "permutation_tail": perm,
        "decision": "NOT_DISCRIMINANT" if len(large) > sum(1 for row in cohort_rows if row["large"]) else "NO_OUTSIDE_LARGE_WALLET",
        "cohort": cohort_rows,
        "note": "The jump and the size line do not use the cohort. The cohort was chosen because it won, so the tail is not a false-positive rate for insider trading.",
    }


def _permutation(notionals: list[float], width: int, observed: float):
    if width == 0 or width > len(notionals):
        return None
    rng = random.Random(SEED)
    beat = 0
    for _ in range(PERMUTATIONS):
        draw = sum(rng.sample(notionals, width))
        if draw >= observed:
            beat += 1
    return (1 + beat) / (1 + PERMUTATIONS)
