"""Population of the rarity test (PLAN_RARITY.md): wallets with >= 1,000 USDC of Yes bought 00:00-06:15 UTC on 28 Feb 2026.

Same rule and deduplication as ../iran-solana-beneficiary-2026-11-05/verify.py (section 8). Offline.
python3 -I population.py > population.txt
"""
import gzip, json
from collections import defaultdict
from pathlib import Path

PREV = Path(__file__).resolve().parents[2] / "iran-solana-beneficiary-2026-11-05" / "evidence" / "polymarket_reduced"


def population():
    act = json.loads((PREV / "pm_v2activity_0x97e490d61b530d5078348d76143a25c43a47164d_p000.json").read_text())["data"]
    yes = next(x["token_id"] for x in act if (x.get("title") or "").startswith("US strikes") and x.get("outcome") == "Yes")
    seen, buy, first = set(), defaultdict(float), {}
    with gzip.open(PREV / "us_strikes_feb28_trades_reduced.jsonl.gz", "rt") as g:
        for line in g:
            if line in seen:
                continue
            seen.add(line)
            x = json.loads(line)
            t = int(x["timestamp"])
            if x["token_id"] == yes and x["side"] == "BUY" and 1772236800 <= t < 1772259300:
                w = x["proxy_wallet"].lower()
                buy[w] += float(x["size"]) * float(x["price"])
                first[w] = min(first.get(w, t), t)
    return sorted([w for w, v in buy.items() if v >= 1000], key=lambda w: first[w])


if __name__ == "__main__":
    pop = population()
    assert len(pop) == 115, len(pop)  # the previous note's count
    print("\n".join(pop))
