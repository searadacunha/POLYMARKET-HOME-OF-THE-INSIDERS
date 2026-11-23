"""Matched-pair analysis of a separately frozen, point-in-time wallet panel."""

import math
import random
from datetime import date
from .common import SERVICES, bounds, read, week_date

ENDPOINTS = {
    "concentration": "7-day market buy notionals",
    "pre_move": "pre-trade midpoint and 6-hour price paths",
    "coordination": "signed exposure and contemporaneous peer exposure",
    "holdout_return": "30-day cash flows, fees and executable inventory marks",
    "incremental_brier": "held-out outcomes and frozen causal price/large-bet probability forecasts",
}
HOLDOUT = {"holdout_return", "incremental_brier"}


def endpoint(r, k):
    if k == "incremental_brier":
        y = r["outcome"]
        ps = [r[x] for x in ("market_probability", "large_bet_probability", "augmented_probability")]
        if y not in (0, 1) or any(not math.isfinite(v) or not 0 <= v <= 1 for v in ps):
            raise ValueError("invalid probabilistic forecast")
        return [(p - y) ** 2 for p in ps]
    if k == "concentration":
        stakes = r["market_buys"]
        if not stakes or any(not math.isfinite(v) or v < 0 for v in stakes) or not sum(stakes):
            raise ValueError("missing/invalid buy notionals")
        return sum((v / sum(stakes)) ** 2 for v in stakes)
    val = r[k]
    if not math.isfinite(val) or (k in {"pre_move", "coordination"} and not 0 <= val <= 1):
        raise ValueError("invalid outcome")
    return val


def matches(rows, service, k):
    remaining = {
        r["wallet"]: r for r in rows if r["service"] == "CONTROL" and r["ascertainment_complete"]
    }
    cases = sorted(
        (r for r in rows if r["service"] == service and r["ascertainment_complete"]),
        key=lambda r: (r["week"], r["wallet"]),
    )
    used, groups = set(), set()
    paired = []
    matched_fields = ("prior_volume", "age_days", "funding_usd")
    for a in cases:
        if a["wallet"] in used or (
            k in HOLDOUT and week_date(a["week"]) < date.fromisocalendar(2026, 45, 1)
        ):
            continue
        if not a.get("complete", {}).get(k) or a["dependency_group"] in groups:
            continue
        options = []
        for w, b in remaining.items():
            if (
                w in used
                or w == a["wallet"]
                or b["week"] != a["week"]
                or b["liquidity_quintile"] != a["liquidity_quintile"]
                or not b.get("complete", {}).get(k)
                or b["dependency_group"] in groups
            ):
                continue
            if any(
                min(a[f], b[f]) <= 0 or max(a[f], b[f]) / min(a[f], b[f]) > 2 for f in matched_fields
            ):
                continue
            options.append((sum(abs(math.log(a[f] / b[f])) for f in matched_fields), w))
        if options:
            _, w = min(options)
            b = remaining.pop(w)
            used.update([a["wallet"], w])
            groups.update([a["dependency_group"], b["dependency_group"]])
            paired.append((endpoint(a, k), endpoint(b, k)))
    return paired


def sign_flip(differences):
    obs = abs(sum(differences))
    rng = random.Random(20261122)
    extreme = sum(
        abs(sum(v if rng.getrandbits(1) else -v for v in differences)) >= obs for _ in range(19999)
    )
    return (extreme + 1) / 20000


def analyze(rows, case_counts):
    results = []
    for service in SERVICES.values():
        for k, missing in ENDPOINTS.items():
            pairs = matches(rows, service, k)
            r = dict(
                service=service,
                endpoint=k,
                observed_funded_accounts=case_counts[service],
                eligible_pairs=len(pairs),
                status="NOT_TESTABLE",
                p=None,
                p_holm=None,
            )
            if len(pairs) >= 20:
                if k == "incremental_brier":
                    # Intersection-union test: improvement must beat each comparator.
                    ds = [[((a[i] - a[2]) + (b[i] - b[2])) / 2 for a, b in pairs] for i in (0, 1)]
                    r.update(effect=min(sum(d) / len(d) for d in ds), p=max(sign_flip(d) for d in ds))
                else:
                    d = [a - b for a, b in pairs]
                    r.update(effect=sum(d) / len(d), p=sign_flip(d))
                r["status"] = "TESTED"
            else:
                r["reason"] = (
                    "Fewer than 20 independent matched pairs with known funding size, age, prior volume, liquidity and "
                    + missing
                )
            results.append(r)
    ordered = sorted(results, key=lambda r: 1 if r["p"] is None else r["p"])
    adjusted = 0.0
    for rank, r in enumerate(ordered):
        if r["p"] is not None:
            adjusted = max(adjusted, min(1.0, (len(results) - rank) * r["p"]))
            r["p_holm"] = adjusted
    return results


def eligible_panel(path, membership, lock, asof):
    """Validate the frozen input and time ordering before any outcome enters a test."""
    if not path.exists():
        return []
    panel = read(path)
    if panel["protocol_sha256"] != lock or not asof:
        raise ValueError("panel is not bound to the frozen study")
    chosen = []
    unique = set()
    for r in panel["rows"]:
        if r["week"] not in membership:
            continue
        account = r["wallet"]
        key = (account, r["week"])
        if key in unique:
            raise ValueError("duplicate panel wallet-week")
        unique.add(key)
        t0, t1 = bounds(r["week"])
        if not t0 <= r["funded_at"] < t1 or not r["feature_asof"] < r["funded_at"]:
            raise ValueError("post-funding matching feature")
        verified = membership[r["week"]]
        if r["service"] == "CONTROL":
            if account in verified["union"] or not r["independent_funding_ref"]:
                raise ValueError("ineligible matched control")
        elif r["service"] not in SERVICES.values() or account not in verified[r["service"]]["funded"]:
            raise ValueError("unverified exposed wallet-week")
        for k in ENDPOINTS:
            if not r["complete"].get(k):
                continue
            if not r["funded_at"] < r["outcome_observed_at"][k] < asof:
                raise ValueError("outcome outside observation period")
            horizon = (30 if k == "holdout_return" else 7 if k == "concentration" else 0) * 86400
            if r["outcome_observed_at"][k] < r["funded_at"] + horizon:
                raise ValueError("immature outcome")
            if (
                k == "incremental_brier"
                and not r["training_labels_until"]
                < bounds("2026-W44")[0]
                <= r["quote_asof"]
                < r["funded_at"]
            ):
                raise ValueError("forecast baseline leakage")
        chosen.append(r)
    return chosen
