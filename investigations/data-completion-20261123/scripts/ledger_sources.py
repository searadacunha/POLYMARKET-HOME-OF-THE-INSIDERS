"""Network side of the ledger: market identity, official payouts, marks, balance checkpoints, Data API control.

Every answer is cached under --out with its receipt time and SHA-256, so the offline build is reproducible and a rerun
only asks for what is missing. A failed request raises; it is never stored as an empty answer.

  markets      Gamma /markets by clob_token_ids (closed and open), 80 ids per call -> token -> condition, outcome
  resolutions  ConditionResolution logs of Conditional Tokens for those conditions (official payout vectors)
  balances     eth_call balanceOf of every cohort account for each collateral token at the window start and end,
               and ERC-1155 balanceOf for a deterministic sample of (account, token) pairs at the end block
  activity     Data API /v2/activity, every page, as an independent count of each account's trades
"""

import argparse
import gzip
import hashlib
import json
import sys
import threading
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2]))
import ledger_build as B  # noqa: E402
import ledger_collect as C  # noqa: E402
from monitoring.phi_monitor import net  # noqa: E402

GAMMA = "https://gamma-api.polymarket.com/markets"
DATA_API = "https://data-api.polymarket.com/v2/activity"
CONDITION_RESOLUTION = "0xb44d84d3289691f71497564b85d4233648d9dbae8cbdbb4329f301c3a0185894"
BALANCE_OF = "0x70a08231"
BALANCE_OF_1155 = "0x00fdd58e"


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def save_json(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_bytes(gzip.compress(json.dumps(obj, sort_keys=True).encode(), mtime=0))
    tmp.replace(p)


def load_json(p, default):
    return json.loads(gzip.decompress(p.read_bytes())) if p.exists() else default


def http_json(url):
    status, body = net.fetch(url, timeout=60, tries=5)
    if status != 200:
        raise net.SourceError(f"HTTP {status} for {url}: {body[:200]!r}", status)
    return json.loads(body), hashlib.sha256(body).hexdigest()


# ---------------------------------------------------------------- markets

def markets(out, token_ids):
    """token id (decimal string) -> Gamma market fields; ids Gamma does not know are recorded as missing."""
    p = out / "markets.json.gz"
    cache = load_json(p, {"tokens": {}, "missing": [], "calls": [], "errors": []})
    cache.setdefault("errors", [])
    cache.setdefault("missing_since", {})
    retry = {t for t in cache["missing"] if t in token_ids and t not in cache.get("retried", [])}
    cache["retried"] = sorted(set(cache.get("retried", [])) | retry)
    want = sorted((set(token_ids) - set(cache["tokens"]) - set(cache["missing"])) | retry)

    def ask(batch, closed):
        """Gamma answers HTTP 500 on some heavy batches: halve until each id is answered or fails alone."""
        q = [("clob_token_ids", t) for t in batch] + [("closed", closed), ("limit", "100")]
        try:
            rows, sha = http_json(GAMMA + "?" + urllib.parse.urlencode(q))
        except net.SourceError as e:
            if e.status not in (500, 502, 503, 504) or len(batch) == 1:
                with lock:
                    cache["errors"].append({"ids": batch, "closed": closed, "error": str(e)[:200], "time_utc": now()})
                return []
            h = len(batch) // 2
            return ask(batch[:h], closed) + ask(batch[h:], closed)
        with lock:
            cache["calls"].append({"time_utc": now(), "closed": closed, "n_ids": len(batch), "n_rows": len(rows),
                                   "sha256": sha})
        time.sleep(0.4)
        return rows

    lock = threading.Lock()

    def one(batch, closed):
        rows = ask(batch, closed)
        with lock:
            for m in rows:
                take(m)

    def take(m):
        ids = json.loads(m.get("clobTokenIds") or "[]")
        outs = json.loads(m.get("outcomes") or "[]")
        prices = json.loads(m.get("outcomePrices") or "[]")
        for j, t in enumerate(ids):
            cache["tokens"][t] = {
                "condition_id": (m.get("conditionId") or "").lower(), "outcome_index": j,
                "outcome": outs[j] if j < len(outs) else None, "question": m.get("question"),
                "slug": m.get("slug"), "neg_risk": bool(m.get("negRisk")),
                "neg_risk_market_id": (m.get("negRiskMarketID") or "").lower() or None,
                "closed": bool(m.get("closed")), "end_date": m.get("endDate"),
                "closed_time": m.get("closedTime"), "uma_status": m.get("umaResolutionStatus"),
                "gamma_outcome_prices": prices, "observed_utc": now()}


    for closed in ("true", "false"):
        todo = [t for t in want if t not in cache["tokens"]]
        batches = [todo[i:i + 40] for i in range(0, len(todo), 40)]
        with ThreadPoolExecutor(4) as ex:
            for n, _ in enumerate(ex.map(lambda b: one(b, closed), batches)):
                if n % 25 == 0:
                    with lock:
                        save_json(p, cache)
        save_json(p, cache)
    failed = {i for e in cache["errors"] for i in e["ids"]}  # retried on the next run, never called missing
    newly = set(want) - set(cache["tokens"]) - failed
    for t in newly:
        cache["missing_since"].setdefault(t, now())
    cache["missing"] = sorted((set(cache["missing"]) - set(cache["tokens"])) | newly)
    save_json(p, cache)
    return cache


# ---------------------------------------------------------------- official payouts

def resolutions(out, conditions, lo, hi, provider=C.TENDERLY):
    """condition -> payout numerators, denominator and the resolving log, from ConditionResolution on CTF."""
    p = out / "resolutions.json.gz"
    cache = load_json(p, {"conditions": {}, "queried": [], "ranges": []})
    todo = sorted(set(conditions) - set(cache["queried"]))
    lock = threading.Lock()

    def group_run(i):
        group = todo[i:i + 100]
        flt = {"address": [B.CTF], "topics": [[CONDITION_RESOLUTION], group]}
        pos, span, found, ranges = lo, 8_000_000, {}, []
        while pos <= hi:
            end = min(pos + span - 1, hi)
            try:
                logs, sha = C.get_logs(provider, flt, pos, end)
            except C.TooMany:
                span = max(1, (end - pos + 1) // 2)
                continue
            for x in logs:
                if x.get("removed") or not C.matches(x, flt) or not pos <= int(x["blockNumber"], 16) <= end:
                    raise RuntimeError("resolution log outside the request")
                w = B.words(x["data"])
                slots, nums = w[0], w[3:3 + w[2]]
                cid = x["topics"][1].lower()
                if cid in found:
                    raise RuntimeError(f"condition {cid} resolved twice")
                found[cid] = {"payout_numerators": nums, "denominator": sum(nums), "slots": slots,
                              "block": int(x["blockNumber"], 16), "tx": x["transactionHash"],
                              "log_index": int(x["logIndex"], 16), "oracle": B.addr(x["topics"][2])}
            ranges.append({"group": i // 100, "from": pos, "to": end, "n": len(logs), "sha256": sha,
                           "time_utc": now()})
            pos = end + 1
            time.sleep(0.3)
        with lock:  # a group enters the cache only once complete, so an interrupted run resumes cleanly
            dup = set(found) & set(cache["conditions"])
            if dup:
                raise RuntimeError(f"conditions resolved twice: {sorted(dup)[:3]}")
            cache["conditions"].update(found)
            cache["ranges"] += ranges
            cache["queried"] += group
            if len(cache["queried"]) % 1000 == 0:
                save_json(p, cache)

    with ThreadPoolExecutor(3) as ex:
        list(ex.map(group_run, range(0, len(todo), 100)))
    save_json(p, cache)
    return cache


# ---------------------------------------------------------------- balances

def eth_calls(provider, calls):
    """calls: list of (to, data, block) -> list of int; batches of 10 (provider limit), errors raise."""
    out = []
    for i in range(0, len(calls), 5):
        body = [{"jsonrpc": "2.0", "id": j, "method": "eth_call", "params": [{"to": to, "data": data}, hex(b)]}
                for j, (to, data, b) in enumerate(calls[i:i + 5])]
        for attempt in range(8):  # the public gateway rate-limits bursts with HTTP 429: wait and retry, never skip
            status, raw = net.fetch(provider, data=body, timeout=60, tries=2)
            if status == 200:
                break
            time.sleep(10 * (attempt + 1))
        else:
            raise net.SourceError(f"eth_call batch failed: HTTP {status}")
        res = {r["id"]: r for r in json.loads(raw)}
        for j in range(len(body)):
            r = res.get(j)
            if not r or "error" in r:
                raise net.SourceError(f"eth_call error {r}")
            out.append(int(r["result"], 16) if r["result"] not in ("0x", "") else "NO_CODE")
        time.sleep(1.0)
    return out


def balances(out, plan, sample_pairs, provider=C.TENDERLY):
    p = out / "balances.json.gz"
    cache = load_json(p, {})
    lo, hi = plan["start_block"] - 1, plan["end_block"]
    if "collateral" not in cache:
        calls, keys = [], []
        for a in plan["accounts"]:
            for tok in B.COLLATERAL:
                for b in (lo, hi):
                    calls.append((tok, BALANCE_OF + "0" * 24 + a[2:], b))
                    keys.append(f"{a}|{tok}|{b}")
        cache["collateral"] = dict(zip(keys, eth_calls(provider, calls)))
        cache["collateral_read_utc"] = now()
        save_json(p, cache)
    if "positions" not in cache:
        calls, keys = [], []
        for a, contract, tid in sample_pairs:
            calls.append((contract, BALANCE_OF_1155 + "0" * 24 + a[2:] + "%064x" % int(tid), hi))
            keys.append(f"{a}|{contract}|{tid}|{hi}")
        cache["positions"] = dict(zip(keys, eth_calls(provider, calls)))
        cache["positions_read_utc"] = now()
        save_json(p, cache)
    return cache


# ---------------------------------------------------------------- marks for open inventory

CLOB_HISTORY = "https://clob.polymarket.com/prices-history"


def marks(out, tokens, at_ts):
    """token -> last CLOB prices-history point at or before at_ts (one-day window, one-minute fidelity)."""
    p = out / "marks.json.gz"
    cache = load_json(p, {"at_ts": at_ts, "tokens": {}, "calls": []})
    if cache["at_ts"] != at_ts:
        raise ValueError("marks cache was made for another valuation time")
    for t in sorted(set(tokens) - set(cache["tokens"])):
        q = {"market": t, "startTs": at_ts - 86400, "endTs": at_ts, "fidelity": 1}
        j, sha = http_json(CLOB_HISTORY + "?" + urllib.parse.urlencode(q))
        if not isinstance(j, dict) or not isinstance(j.get("history"), list):
            raise net.SourceError(f"prices-history answer without a history list for {t}: {str(j)[:120]}")
        pts = j["history"]
        best = B.select_mark(pts, at_ts)
        cache["tokens"][t] = {"price": best[1] if best else None, "point_ts": best[0] if best else None,
                              "points": len(pts), "sha256": sha, "observed_utc": now()}
        cache["calls"].append({"token": t, "n": len(pts), "time_utc": now()})
        time.sleep(0.3)
    save_json(p, cache)
    return cache


# ---------------------------------------------------------------- Data API control

def activity(out, accounts, end_ts):
    """Every /v2/activity page of each account up to end_ts (cursor paging, 1,000 per page)."""
    p = out / "activity.json.gz"
    cache = load_json(p, {"accounts": {}})
    for a in accounts:
        if cache["accounts"].get(a, {}).get("status") == "EXHAUSTED":
            continue
        rows, cursor, pages = [], None, []
        while True:
            q = {"user": a, "limit": 1000, "sort_by": "TIMESTAMP", "sort_direction": "ASC", "end": end_ts,
                 "exclude_deposits_withdrawals": "false"}
            if cursor:
                q["cursor"] = cursor
            j, sha = http_json(DATA_API + "?" + urllib.parse.urlencode(q))
            data, pg = j["data"], j["pagination"]
            if pg.get("has_more") != bool(pg.get("next_cursor")) or (pg.get("has_more") and not data):
                raise ValueError(f"ambiguous pagination for {a}")
            pages.append({"n": len(data), "sha256": sha, "time_utc": now()})
            for r in data:  # profile fields are dropped at read time
                if r["proxy_wallet"].lower() != a:
                    raise ValueError(f"activity row for another wallet: {r['proxy_wallet']}")
                rows.append({"type": r.get("type"), "ts": r.get("timestamp"), "side": r.get("side"),
                             "tx": (r.get("transaction_hash") or "").lower(), "token": r.get("token_id"),
                             "size": r.get("size"), "usdc": r.get("usdc_size"), "price": r.get("price"),
                             "condition": (r.get("condition_id") or "").lower()})
            cursor = pg.get("next_cursor")
            if not pg.get("has_more") or len(pages) > 500:
                break
            time.sleep(0.4)
        cache["accounts"][a] = {"status": "EXHAUSTED" if len(pages) <= 500 else "PAGE_CAP", "rows": rows,
                                "pages": pages}
        save_json(p, cache)
    return cache


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--raw", type=Path, required=True, help="collector output (plan.json, checkpoint.jsonl)")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--steps", default="markets,resolutions,balances,activity")
    a = ap.parse_args()
    plan, coverage, logs, problems = B.load(a.raw)
    recs, _ = B.account_txs(logs, plan["accounts"])
    tokens = sorted({str(k[1]) for r in recs.values() for k in r["shares"] if k[0] in (B.CTF, B.POSITION_MANAGER)})
    steps = a.steps.split(",")
    if "markets" in steps:
        m = markets(a.out, tokens)
        print("markets", len(m["tokens"]), "missing", len(m["missing"]))
    if "resolutions" in steps:
        m = load_json(a.out / "markets.json.gz", {"tokens": {}})
        conds = sorted({v["condition_id"] for v in m["tokens"].values() if v["condition_id"]})
        # a condition traded by the cohort resolves after the cohort's first transaction; an earlier resolution
        # (shares received after settlement) is left unresolved here, so its value stays UNKNOWN, never zero
        lo = min(r["block"] for r in recs.values())
        r = resolutions(a.out, conds, lo, plan["end_block"])
        print("resolved", len(r["conditions"]), "of", len(conds))
    if "balances" in steps:
        held = {}
        for r in recs.values():
            for k, v in r["shares"].items():
                held[(r["account"], k)] = held.get((r["account"], k), 0) + v
        keys = sorted(held, key=lambda k: hashlib.sha256(f"{k[0]}|{k[1][0]}|{k[1][1]}".encode()).digest())
        nonzero = [k for k in keys if held[k] != 0][:400]
        zero = [k for k in keys if held[k] == 0][:200]
        pairs = [(acc, k[0], k[1]) for acc, k in nonzero + zero]
        b = balances(a.out, plan, pairs)
        print("balances", len(b["collateral"]), len(b["positions"]))
    if "marks" in steps:
        m = load_json(a.out / "markets.json.gz", {"tokens": {}})
        res = load_json(a.out / "resolutions.json.gz", {"conditions": {}})
        inv = {}
        for r in recs.values():
            for k, v in r["shares"].items():
                inv[(r["account"], k)] = inv.get((r["account"], k), 0) + v
        open_tokens = sorted({str(k[1]) for (acc, k), q in inv.items() if q and k[0] == B.CTF
                              and m["tokens"].get(str(k[1]), {}).get("condition_id") not in res["conditions"]})
        at = int(datetime.fromisoformat(plan["end_block_time_utc"]).timestamp())
        mk = marks(a.out, open_tokens, at)
        print("marks", len(mk["tokens"]), "with a point", sum(1 for v in mk["tokens"].values() if v["price"] is not None))
    if "activity" in steps:
        end_ts = int(datetime.fromisoformat(plan["end_block_time_utc"]).timestamp())
        act = activity(a.out, plan["accounts"], end_ts)
        print("activity accounts", len(act["accounts"]))


if __name__ == "__main__":
    main()
