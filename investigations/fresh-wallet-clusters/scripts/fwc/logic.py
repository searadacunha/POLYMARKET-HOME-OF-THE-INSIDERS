"""Pure rules for the fresh-wallet cluster study.

The thresholds live in preregistration.json. This module does not read the network
and does not decide that two addresses have one owner.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = ROOT / "preregistration.json"


def load_spec(path: Path | None = None) -> dict:
    return json.loads((path or SPEC_PATH).read_text())


def sample_indices(n: int, target: int) -> list[int]:
    """Systematic indices across a sorted stratum. See preregistration sample_rule."""
    if target <= 0 or n <= 0:
        return []
    if n <= target:
        return list(range(n))
    if target == 1:
        return [0]
    raw = [min(n - 1, int(round(i * (n - 1) / (target - 1)))) for i in range(target)]
    picked: list[int] = []
    seen: set[int] = set()
    for i in raw:
        if i not in seen:
            picked.append(i)
            seen.add(i)
    if len(picked) < target:
        for i in range(n):
            if i not in seen:
                picked.append(i)
                seen.add(i)
            if len(picked) >= target:
                break
    return sorted(picked)


def commitment(fills: list[tuple], min_usd: float = 1000.0) -> dict:
    """fills are (ts, side, price, size) for one outcome, any order.

    capital_committed is the high-water mark of buy notional minus sell proceeds.
    A wallet that buys, fully exits, and buys again is not credited twice.
    """
    ordered = sorted(fills, key=lambda r: (r[0], 0 if r[1] == "BUY" else 1))
    buy = sell = peak = 0.0
    cross_ts = None
    cross_price = None
    spent_cash = 0.0
    spent_shares = 0.0
    n_buy = n_sell = 0
    for ts, side, price, size in ordered:
        notion = float(price) * float(size)
        if side == "BUY":
            buy += notion
            n_buy += 1
            if cross_ts is None:
                spent_cash += notion
                spent_shares += float(size)
        elif side == "SELL":
            sell += notion
            n_sell += 1
        else:
            raise ValueError(f"bad side {side}")
        net = buy - sell
        if net > peak + 1e-9:
            peak = net
        if cross_ts is None and net + 1e-9 >= min_usd:
            cross_ts = int(ts)
            cross_price = float(price)
    vwap = (spent_cash / spent_shares) if spent_shares and cross_ts is not None else None
    return {
        "gross_buy_usd": buy,
        "sell_proceeds_usd": sell,
        "capital_committed_usd": peak,
        "threshold_ts": cross_ts,
        "threshold_price": cross_price,
        "vwap_to_threshold": vwap,
        "n_buys": n_buy,
        "n_sells": n_sell,
        "eligible": peak + 1e-9 >= min_usd and cross_ts is not None,
    }


def opposing_outcomes_do_not_sum(yes_committed: float, no_committed: float, min_usd: float = 1000.0) -> bool:
    """True when neither outcome reaches the threshold, even if their sum does."""
    return yes_committed < min_usd and no_committed < min_usd


def freshness(activity: list[tuple], condition_id: str, first_trade_ts: int | None,
              threshold_ts: int | None, history_ok: bool, address_kind: str,
              nonce_before_funding: int | None, activity_before_funding: bool,
              gap_censored: bool = False) -> dict:
    """activity rows are (ts, type, condition_id), oldest first. type TRADE is a trade.

    history_ok False means the read failed or was capped before the start of history.
    The caller only sets history_ok when the oldest page is complete (ascending, first page
    is the start). has_more on an ascending read means later rows exist, not earlier ones.
    """
    labels: list[str] = []
    if not history_ok or first_trade_ts is None or threshold_ts is None:
        return {"labels": [], "qualifying": False, "history": "unresolved", "F0": False}
    prior_trade = False
    last_before = None
    first_any = activity[0][0] if activity else None
    for ts, typ, cond in activity:
        if ts >= first_trade_ts:
            break
        last_before = ts
        if typ == "TRADE" and cond and cond != condition_id:
            prior_trade = True
    if not prior_trade:
        labels.append("F1")
    if first_any is not None:
        delta = threshold_ts - int(first_any)
        if 0 <= delta <= 24 * 3600:
            labels.append("F2_24h")
        if 0 <= delta <= 72 * 3600:
            labels.append("F2_72h")
        if 0 <= delta <= 7 * 86400:
            labels.append("F2_7d")
        if 0 <= delta <= 30 * 86400:
            labels.append("F2_30d")
    if prior_trade and last_before is not None and not gap_censored:
        gap = first_trade_ts - int(last_before)
        if gap >= 30 * 86400:
            labels.append("F3_30")
        if gap >= 60 * 86400:
            labels.append("F3_60")
        if gap >= 90 * 86400:
            labels.append("F3_90")
        if gap >= 180 * 86400:
            labels.append("F3_180")
    f0 = (address_kind == "eoa" and nonce_before_funding == 0 and not activity_before_funding)
    qualifying = any(x in labels for x in ("F1", "F2_7d", "F3_30", "F3_60", "F3_90", "F3_180"))
    return {"labels": labels, "qualifying": qualifying, "history": "ok", "F0": f0,
            "prior_trade": prior_trade, "first_activity_ts": first_any}


def has_tight_group(times: list[int], window: int, minimum: int = 2) -> bool:
    if len(times) < minimum:
        return False
    ordered = sorted(times)
    j = 0
    for i, ts in enumerate(ordered):
        while ts - ordered[j] > window:
            j += 1
        if i - j + 1 >= minimum:
            return True
    return False


def tight_subset(records: list[dict], window: int) -> list[dict] | None:
    """Earliest subset whose threshold times fit in `window` and whose size is at least 2.

    records need wallet and threshold_ts. Returns None when no such subset exists.
    """
    ordered = sorted(records, key=lambda r: (r["threshold_ts"], r["wallet"]))
    best = None
    for i, start in enumerate(ordered):
        members = [start]
        for nxt in ordered[i + 1:]:
            if nxt["threshold_ts"] - start["threshold_ts"] <= window:
                members.append(nxt)
            else:
                break
        if len(members) >= 2 and (best is None or len(members) > len(best)):
            best = members
        if best and len(best) == len(ordered):
            break
    return best


def classify_address(code_present: bool, nonce: int | None, infra: bool, fanout: int | None,
                     fanout_max: int = 10, busy_at: int = 1000, passthrough_at: int = 5) -> str:
    if infra:
        return "service_infra"
    if code_present:
        return "contract"
    if nonce is None:
        return "unresolved"
    if fanout is not None and fanout > fanout_max:
        return "high_fanout_service"
    if nonce >= busy_at:
        return "busy_eoa"
    if nonce <= passthrough_at:
        return "passthrough_eoa"
    return "plain_eoa"


def is_private_link(kind: str) -> bool:
    return kind == "plain_eoa"


def evidence_class(has_private_funder: bool, has_private_cashout: bool, amounts_similar: bool,
                   nonces_consecutive: bool, within_one_hour: bool, only_shared_service: bool,
                   trace_complete: bool, contradicted: bool) -> str:
    if contradicted:
        return "REFUTED"
    if not trace_complete:
        return "UNRESOLVED"
    if has_private_funder or has_private_cashout:
        extra = amounts_similar or nonces_consecutive or within_one_hour or (
            has_private_funder and has_private_cashout)
        if extra:
            return "CORROBORATED COORDINATION"
        return "VERIFIED FINANCIAL LINK"
    if only_shared_service:
        return "SHARED SERVICE ONLY"
    return "BEHAVIORAL SIMILARITY"


def forward_destination(moves: list[dict], wallet: str, infra: set[str]) -> dict | None:
    """Largest stable transfer out of `wallet`, following same-amount relays.

    `moves` items are {token, from, to, value}. A relay that lands on an address in
    `infra` stops on the previous address: infrastructure is not a private destination.
    """
    wallet = wallet.lower()
    outs = [t for t in moves if t["from"] == wallet and t["value"] > 0 and t["to"] != wallet]
    if not outs:
        return None
    current = max(outs, key=lambda t: t["value"])
    dest = current["to"]
    path: list[str] = []
    for _ in range(6):
        if dest in infra:
            break
        nxt = next((t for t in moves if t["from"] == dest and t["value"] == current["value"]
                    and t["to"] != dest and t["to"] != wallet), None)
        if nxt is None:
            break
        path.append(dest)
        dest = nxt["to"]
        if dest in infra:
            dest = path.pop() if path else current["to"]
            break
    if dest in infra:
        return {"destination": None, "value": current["value"], "token": current["token"],
                "path": path, "stopped": "infra"}
    return {"destination": dest, "value": current["value"], "token": current["token"],
            "path": path, "stopped": None}


def month_key(ts: int) -> str:
    import datetime as dt
    return dt.datetime.fromtimestamp(int(ts), dt.timezone.utc).strftime("%Y-%m")


def shuffle_labels(assignments: list[dict], permutations: int, seed: int, stat):
    """assignments: {id, month, label or None, ...payload used by stat}.

    Labels that are None stay None. Non-null labels are shuffled inside each month.
    Returns (observed, p_value, null_mean).
    """
    observed = stat(assignments)
    rng = random.Random(seed)
    by_month: dict[str, list[int]] = {}
    for i, row in enumerate(assignments):
        if row.get("label") is not None:
            by_month.setdefault(row["month"], []).append(i)
    ge = 0
    total = 0.0
    for _ in range(permutations):
        labels = [row.get("label") for row in assignments]
        for idxs in by_month.values():
            pool = [labels[i] for i in idxs]
            rng.shuffle(pool)
            for i, lab in zip(idxs, pool):
                labels[i] = lab
        shuffled = []
        for row, lab in zip(assignments, labels):
            nxt = dict(row)
            nxt["label"] = lab
            shuffled.append(nxt)
        value = stat(shuffled)
        total += value
        if value >= observed:
            ge += 1
    p = (1 + ge) / (1 + permutations)
    return {"observed": observed, "p": p, "null_mean": total / permutations, "permutations": permutations}


def family_permutation(markets: list[dict], permutations: int, seed: int):
    """markets: {family, quintile, hit}. D = mean(hit|INFO) - mean(hit|PUBLIC_PROCESS).

    Families are permuted inside each quintile. One-sided p for D_perm >= D.
    """
    def diff(rows):
        info = [r["hit"] for r in rows if r["family"] == "INFO"]
        ctrl = [r["hit"] for r in rows if r["family"] == "PUBLIC_PROCESS"]
        if not info or not ctrl:
            return None
        return sum(info) / len(info) - sum(ctrl) / len(ctrl)

    observed = diff(markets)
    if observed is None:
        return {"observed": None, "p": None, "null_mean": None, "permutations": permutations,
                "reason": "one family is empty"}
    rng = random.Random(seed)
    by_q: dict = {}
    for i, row in enumerate(markets):
        by_q.setdefault(row["quintile"], []).append(i)
    ge = 0
    total = 0.0
    for _ in range(permutations):
        fams = [r["family"] for r in markets]
        for idxs in by_q.values():
            pool = [fams[i] for i in idxs]
            rng.shuffle(pool)
            for i, fam in zip(idxs, pool):
                fams[i] = fam
        rows = []
        for row, fam in zip(markets, fams):
            nxt = dict(row)
            nxt["family"] = fam
            rows.append(nxt)
        value = diff(rows)
        if value is None:
            continue
        total += value
        if value >= observed:
            ge += 1
    p = (1 + ge) / (1 + permutations)
    return {"observed": observed, "p": p, "null_mean": total / permutations, "permutations": permutations}


def h1_stat(group_wallets: list[dict], label_of: dict[str, str | None]) -> int:
    """group_wallets rows: {market, outcome, wallet, threshold_ts}. label_of maps wallet to funder.

    Counts market-outcomes where some 7-day subset shares one non-null label.
    """
    window = 7 * 86400
    buckets: dict[tuple, list] = {}
    for row in group_wallets:
        buckets.setdefault((row["market"], row["outcome"]), []).append(row)
    hit = 0
    for members in buckets.values():
        ordered = sorted(members, key=lambda r: r["threshold_ts"])
        found = False
        for i, start in enumerate(ordered):
            counts: dict[str, int] = {}
            for nxt in ordered[i:]:
                if nxt["threshold_ts"] - start["threshold_ts"] > window:
                    break
                lab = label_of.get(nxt["wallet"])
                if not lab:
                    continue
                counts[lab] = counts.get(lab, 0) + 1
                if counts[lab] >= 2:
                    found = True
                    break
        if found:
            hit += 1
    return hit


def quintiles(values: list[float]) -> list[int]:
    """Return quintile index 0-4 for each value. Ties stay in the lower bin."""
    if not values:
        return []
    ordered = sorted(values)
    n = len(ordered)
    out = []
    for v in values:
        # rank of the first equal value
        rank = next(i for i, x in enumerate(ordered) if x == v)
        q = min(4, (rank * 5) // n)
        out.append(q)
    return out


def verdict_h1(p: float | None, control_p: float | None, observed: int, n_markets: int,
               groups: int, groups_traced: int, alpha: float) -> str:
    if n_markets < 20:
        return "INCONCLUSIVE_COVERAGE"
    if groups and groups_traced / groups < 0.5:
        return "INCONCLUSIVE_COVERAGE"
    if p is None:
        return "INCONCLUSIVE_COVERAGE"
    if observed == 0:
        return "NOT_OBSERVED"
    if p < alpha and control_p is not None and control_p < alpha:
        return "NOT_SPECIFIC"
    if p < alpha:
        return "PRIMARY_SUPPORTED"
    return "NOT_SUPPORTED"


def central_answer(h1: str, h2_p: float | None, h3_p: float | None, alpha: float) -> str:
    """One sentence key. The caller writes the prose around the counts."""
    hits = []
    if h1 == "PRIMARY_SUPPORTED":
        hits.append("H1")
    if h2_p is not None and h2_p < alpha:
        hits.append("H2")
    if h3_p is not None and h3_p < alpha:
        hits.append("H3")
    if h1 == "INCONCLUSIVE_COVERAGE" and not hits:
        return "INCONCLUSIVE_COVERAGE"
    if not hits:
        return "NO"
    return "YES:" + ",".join(hits)
