"""Comparator shocks from the phase-8 universe, offline. Writes data/shocks.json.

python3 -I code/col_10_select.py

Reads the archive frozen on 30 September 2026 for another question (2,097 closed markets of at
least $250,000, sports, crypto prices, tweet counts and weather excluded, taker rows of at least
$100). No exit data is read here.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import CATALOG_GAP_S, DATA, JUMP_PRICE, PRE_VWAP, SHOCK_GAP_S, WINDOW_S, sha256  # noqa: E402

P8 = Path.home() / "Documents/Crypto/enquete_maduro_iran/donnees/brut_p8_p9/p8"


def jump(rows, yes):
    """First Yes taker row at >= JUMP_PRICE whose preceding window has a Yes VWAP <= PRE_VWAP."""
    r = sorted((x for x in rows if x["asset"] == yes), key=lambda x: (x["timestamp"], x["transactionHash"]))
    for i, x in enumerate(r):
        if x["price"] >= JUMP_PRICE:
            t = x["timestamp"]
            win = [y for y in r[:i] if t - WINDOW_S <= y["timestamp"] < t]
            vol = sum(y["size"] for y in win)
            if win and sum(y["size"] * y["price"] for y in win) / vol <= PRE_VWAP:
                return t
    return None


def main():
    ub = (P8 / "universe.json").read_bytes()
    universe = json.loads(ub)
    catalog = json.loads((DATA / "catalog_markets.json").read_text())
    cat_t = [int(datetime.fromisoformat(c["event_utc"].replace("Z", "+00:00")).timestamp()) for c in catalog]
    cat_c = {c["condition"] for c in catalog}
    count = {"universe": len(universe), "not_resolved_yes": 0, "first_outcome_not_yes": 0, "no_trade_file": 0,
             "truncated_file": 0, "no_jump": 0, "jump": 0}
    out, files = [], {}
    for m in universe:
        if m["outcomePrices"] != '["1", "0"]':
            count["not_resolved_yes"] += 1; continue
        if json.loads(m["outcomes"])[0] != "Yes":
            count["first_outcome_not_yes"] += 1; continue
        f = P8 / "trades" / f'{m["conditionId"]}.json'
        if not f.exists():
            count["no_trade_file"] += 1; continue
        b = f.read_bytes(); files[f.name] = sha256(b)
        d = json.loads(b)
        if d.get("maybe_truncated"):
            count["truncated_file"] += 1; continue  # oldest rows may be missing: T could be wrong
        yes = json.loads(m["clobTokenIds"])[0]
        t = jump(d["rows"], yes)
        if t is None:
            count["no_jump"] += 1; continue
        count["jump"] += 1
        alleged = m["conditionId"] in cat_c or any(abs(t - c) <= CATALOG_GAP_S for c in cat_t)
        # completeness oracle for col_20: the archive's oldest row and its Yes taker rows inside the window
        oracle = sorted({(x["transactionHash"].lower(), x["proxyWallet"].lower()) for x in d["rows"]
                         if x["asset"] == yes and t - WINDOW_S <= x["timestamp"] < t})
        out.append({"condition": m["conditionId"], "question": m["question"], "cat": m["cat"], "endDate": m["endDate"],
                    "yes_token": yes, "T": t,
                    "T_utc": datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                    "window": [t - WINDOW_S, t], "alleged": alleged,
                    "archive_oldest_ts": min(x["timestamp"] for x in d["rows"]), "archive_window_yes_rows": oracle})
    # shock clusters among comparator candidates only: jumps closer than SHOCK_GAP_S are one shock
    out.sort(key=lambda x: (x["T"], x["condition"]))
    sid, last = 0, None
    for x in out:
        if x["alleged"]:
            x["shock"] = None; continue
        if last is not None and x["T"] - last > SHOCK_GAP_S:
            sid += 1
        x["shock"] = sid; last = x["T"]
    res = {"universe_sha256": sha256(ub), "trade_files_sha256": files, "counts": count,
           "comparator_candidates": sum(1 for x in out if not x["alleged"]), "alleged": sum(1 for x in out if x["alleged"]),
           "markets": out}
    (DATA / "shocks.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(count), "candidates", res["comparator_candidates"], "alleged", res["alleged"])


if __name__ == "__main__":
    main()
