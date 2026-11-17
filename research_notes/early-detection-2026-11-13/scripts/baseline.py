"""Wallet baseline AS OF a reference time (no look-ahead): everything is read with end < t_ref.
Derived fields only; profile text fields are never stored."""
import json, statistics, datetime as dt
from net import fetch

def _act(user, **params):
    q = "&".join(f"{k}={v}" for k, v in params.items())
    s, b, m = fetch(f"https://data-api.polymarket.com/v2/activity?user={user}&{q}", tag="activity", pause=0.12)
    if s != 200: raise RuntimeError(f"activity HTTP {s} {user} {b[:150]!r}")
    j = json.loads(b); return j.get("data") or [], j.get("pagination") or {}

def profile_created(user):
    s, b, m = fetch(f"https://gamma-api.polymarket.com/public-profile?address={user}", tag="profile", pause=0.12)
    if s == 404: return None
    if s != 200: raise RuntimeError(f"profile HTTP {s} {user}")
    c = json.loads(b).get("createdAt")
    return dt.datetime.fromisoformat(c.replace("Z", "+00:00")).timestamp() if c else None

def baseline(user, t_ref, deposit_window=72 * 3600):
    """Features of `user` using only activity strictly before t_ref."""
    out = {"wallet": user, "t_ref": t_ref}
    pc = profile_created(user); out["profile_created"] = pc
    out["profile_age_h"] = None if pc is None else round((t_ref - pc) / 3600, 2)
    first, _ = _act(user, limit=1, sort_by="TIMESTAMP", sort_direction="ASC", exclude_deposits_withdrawals="false")
    out["first_activity"] = int(first[0]["timestamp"]) if first else None
    prior, pg = _act(user, limit=500, sort_by="TIMESTAMP", sort_direction="DESC", exclude_deposits_withdrawals="false", end=int(t_ref) - 1)
    bad = [r for r in prior if int(r["timestamp"]) >= t_ref]
    if bad: raise RuntimeError(f"end filter not honoured for {user}: {len(bad)} rows at/after t_ref")
    out["prior_rows"] = len(prior); out["prior_rows_capped"] = bool(pg.get("has_more"))
    tr = [r for r in prior if r.get("type") == "TRADE"]
    cash = [float(r.get("usdc_size") or 0) for r in tr]
    out["prior_trades"] = len(tr); out["prior_markets"] = len({r.get("condition_id") for r in tr})
    out["prior_trade_cash"] = round(sum(cash), 2)
    out["prior_trade_median"] = round(statistics.median(cash), 2) if cash else None
    out["prior_trade_max"] = round(max(cash), 2) if cash else None
    dep = [r for r in prior if r.get("type") == "DEPOSIT" and int(r["timestamp"]) >= t_ref - deposit_window]
    out["deposits_72h"] = [{"ts": int(r["timestamp"]), "usdc": float(r.get("usdc_size") or 0), "tx": r.get("transaction_hash")} for r in dep]
    out["deposit_72h_usdc"] = round(sum(d["usdc"] for d in out["deposits_72h"]), 2)
    out["last_prior_trade"] = max((int(r["timestamp"]) for r in tr), default=None)
    return out

if __name__ == "__main__":
    import sys
    print(json.dumps(baseline(sys.argv[1], int(sys.argv[2])), indent=1))
