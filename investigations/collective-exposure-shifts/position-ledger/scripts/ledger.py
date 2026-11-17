#!/usr/bin/env python3
"""Point-in-time position ledger for Polymarket conditional tokens. Reads no outcome label.

Core facts this module relies on (all tested in tests/test_ledger.py):

* A binary condition has two tokens, outcome index 0 (YES) and 1 (NO). One YES plus one NO always pays exactly 1 USDC.
* SPLIT adds the same amount to both tokens, MERGE removes the same amount from both. So the directional exposure
  X = q0 - q1 is unchanged by splits and merges: it is observable from fills alone, while the raw inventory is not.
* A neg-risk CONVERSION burns NO of one market and mints YES of every other market of the same event. The payoff
  vector of the whole event (one entry per mutually exclusive world) is unchanged up to a constant (cash) vector.
* A snapshot at T is computed only from events with ts <= T AND seen_ts <= T, including the transaction checks.
  Later data never moves a past snapshot.

Three readings are kept apart, never mixed:
  observable : signed flows from the events the source can see (exact, with provenance);
  bounds     : what those flows prove about the true inventory, given which event classes the source covers;
  status     : EXACT / OBSERVABLE / UNKNOWN, with the reasons. Nothing is filled in when a reason applies.

v2 (2026-11-17) after an adversarial review: as-of transaction checks, intra-second order, coverage of redemptions
and conversions in the bounds, fee paid in shares, class rules (B from held legs, market-making marked per token,
complete sets by residue, D verified only when merges are visible), partitions by observation time.
"""
import bisect
import datetime as _dt
import json
import math
import re
from collections import defaultdict

YES, NO = 0, 1
TRADE_KINDS = ("BUY", "SELL")
PROTOCOL_KINDS = ("SPLIT", "MERGE", "REDEEM", "CONVERT_OUT", "CONVERT_IN", "TRANSFER_IN", "TRANSFER_OUT",
                  "REWARD", "FEE")
KINDS = TRADE_KINDS + PROTOCOL_KINDS
EPS = 1e-6

# Declared before any outcome is read; inherited from the frozen plan where one exists (analysis_plan.md):
MIN_PAYOUT = 500.0   # material change, in payout dollars (1 share = 1 USD at payout); frozen plan used 500 marked USD
MM_RATIO = 5.0       # two-sided: traded notional >= 5x the marked net change (frozen plan rule)
MAX_FEE_RATE = 0.10  # cap on the implied fee rate (fee = rate x min(p, 1-p) x shares) accepted as a fee; declared
                     # above the 0.06 seen in the first fee-enabled tapes; every implied rate is reported

# Reasons that make a reading UNKNOWN. Others (transfers, conversions, redemptions not covered) leave it OBSERVABLE:
# exact unless an invisible event of that class happened, which the reason names. Nothing is ever filled in.
HARD_REASONS = {"INITIAL_POSITION_UNKNOWN", "TX_UNBALANCED", "NEGATIVE_INVENTORY_WITH_FULL_COVERAGE"}

# What a source can see. A class that is not covered makes the matching inventory component unknown.
TAPE_COVERAGE = {"trades": True, "split_merge": False, "convert": False, "transfer": False, "redeem": False,
                 "fees": False}
FULL_COVERAGE = {k: True for k in TAPE_COVERAGE}


class ChronologyError(ValueError):
    pass


def _f(x):
    return None if x is None else float(x)


def make_event(ts, wallet, cid, kind, oi=None, qty=0.0, price=None, usdc=None, fee=None, tx=None, seq=0,
               src="", seen_ts=None):
    """Normalise one event. Raises ChronologyError / ValueError on input that must not enter the ledger."""
    if kind not in KINDS:
        raise ValueError(f"unknown kind {kind}")
    if ts is None or not isinstance(ts, (int, float)) or ts < 0 or math.isnan(ts):
        raise ChronologyError(f"invalid timestamp {ts!r} ({src})")
    if seen_ts is not None and seen_ts < ts:
        raise ChronologyError(f"seen before it happened: ts={ts} seen_ts={seen_ts} ({src})")
    qty = float(qty)
    if qty < 0 or math.isnan(qty):
        raise ValueError(f"negative or NaN quantity {qty} ({src})")
    if kind in ("BUY", "SELL", "TRANSFER_IN", "TRANSFER_OUT") and oi not in (YES, NO):
        raise ValueError(f"{kind} needs an outcome index ({src})")
    if kind == "REDEEM" and oi not in (YES, NO, None):
        raise ValueError(f"{kind} needs an outcome index ({src})")
    if kind in ("BUY", "SELL") and (price is None or not (0.0 <= float(price) <= 1.0)):
        raise ValueError(f"trade price outside [0,1]: {price} ({src})")
    return {"ts": int(ts), "seen_ts": int(seen_ts if seen_ts is not None else ts), "wallet": wallet.lower(),
            "cid": cid.lower(), "kind": kind, "oi": oi, "qty": qty, "price": _f(price), "usdc": _f(usdc),
            "fee": _f(fee), "tx": (tx or "").lower() or None, "seq": int(seq), "src": src}


def order_key(e):
    """Deterministic total order. The order inside one second is not observable (no log index in the tape): it is
    only a stable tie-break, and nothing computed by this module depends on it (running minima are taken at
    second boundaries)."""
    return (e["ts"], e["tx"] or "", e["seq"], e["wallet"], e["kind"], -1 if e["oi"] is None else e["oi"], e["qty"])


def token_delta(e, held=(0.0, 0.0)):
    """(d_q0, d_q1, d_cash) the event applies to its own condition. Cash is None when the source does not say.
    held = the wallet's ledger position just before the event (used only by REDEEM without an outcome index, which
    burns every token of the condition the wallet holds, as the CTF contract does)."""
    k, q, oi = e["kind"], e["qty"], e["oi"]
    d = [0.0, 0.0]
    cash = None
    if k == "BUY":
        d[oi] = q
        cash = -q * e["price"]
    elif k == "SELL":
        d[oi] = -q
        cash = q * e["price"]
    elif k == "SPLIT":
        d = [q, q]
        cash = -q
    elif k == "MERGE":
        d = [-q, -q]
        cash = q
    elif k == "REDEEM":
        if oi is None:
            d = [-max(held[0], 0.0), -max(held[1], 0.0)]
        else:
            d[oi] = -q
        cash = e["usdc"]
    elif k == "CONVERT_OUT":      # neg-risk: NO of this market burned
        d[NO] = -q
        cash = e["usdc"]
    elif k == "CONVERT_IN":       # neg-risk: YES of this market received
        d[YES] = q
    elif k == "TRANSFER_IN":
        d[oi] = q
    elif k == "TRANSFER_OUT":
        d[oi] = -q
    elif k in ("REWARD", "FEE"):
        cash = e["usdc"]
    if cash is not None and e["fee"]:
        cash -= e["fee"]
    return d[0], d[1], cash


# ---------------------------------------------------------------------------------------------------------------
# Transaction conservation (fills only): within one tx, supply change of YES must equal supply change of NO.
# A regular match moves tokens between wallets (both zero); a mint match buys YES and NO (+m, +m); a merge match
# sells both (-m, -m). Any other result means a fill is missing or counted twice (or a fee was paid in shares).
# ---------------------------------------------------------------------------------------------------------------

def tx_balance(rows):
    """rows: events of one (tx, condition). Returns (d_yes_supply, d_no_supply, gross)."""
    s = [0.0, 0.0]
    gross = 0.0
    for e in rows:
        sg = 1.0 if e["kind"] == "BUY" else -1.0
        s[e["oi"]] += sg * e["qty"]
        gross += e["qty"]
    return s[0], s[1], gross


def balanced(rows, rel=1e-6):
    a, b, g = tx_balance(rows)
    return abs(a - b) <= EPS + rel * g


def implied_fee_rate(rows):
    """Fee taken in shares from the buyer leaves a token gap: rate = gap / sum(min(p, 1-p) x shares) over the
    BUY rows of the short side. None if there is no such row."""
    a, b, _ = tx_balance(rows)
    short = NO if a > b else YES
    base = sum(min(e["price"], 1 - e["price"]) * e["qty"] for e in rows if e["kind"] == "BUY" and e["oi"] == short)
    return abs(a - b) / base if base > EPS else None


def reconcile_tx(rows, fees_enabled=False):
    """Decide what to do with one (tx, condition) group of trade rows.

    Returns (kept_rows, verdict) with verdict in
      BALANCED                 all rows kept;
      DUPLICATES_DROPPED       balanced only after collapsing exact duplicate rows -> duplicates removed;
      FEE_IN_SHARES            fee-enabled market, gap explained by a buyer fee paid in shares (0 < rate <=
                               MAX_FEE_RATE): the tape already shows the shares the payer received, positions stand;
      MULTI_TIMESTAMP          rows of one tx carry different timestamps: one block cannot, rows flagged;
      UNBALANCED               none of these -> rows kept, every wallet touched is flagged (fill missing or doubled);
      NO_TX                    the rows carry no transaction hash: cannot be checked (flagged TX_UNCHECKED).
    Exact duplicates that balance are kept: two identical fills inside one tx are possible and the check says so.
    """
    if not rows[0]["tx"]:
        return rows, "NO_TX"
    if len({e["ts"] for e in rows}) > 1:
        return rows, "MULTI_TIMESTAMP"
    if balanced(rows):
        return rows, "BALANCED"
    seen, dedup = set(), []
    for e in rows:
        k = (e["wallet"], e["kind"], e["oi"], e["qty"], e["price"], e["ts"])
        if k not in seen:
            seen.add(k)
            dedup.append(e)
    if len(dedup) < len(rows) and balanced(dedup):
        return dedup, "DUPLICATES_DROPPED"
    if fees_enabled:
        r = implied_fee_rate(rows)
        if r is not None and 0 < r <= MAX_FEE_RATE:
            return rows, "FEE_IN_SHARES"
    return rows, "UNBALANCED"


def coverage_flags(cov, neg_risk):
    """(inflows_covered, all_covered). Conversions matter only on neg-risk markets (or when the flag is unknown)."""
    conv_ok = bool(cov.get("convert")) or neg_risk is False
    inflows = all(cov.get(k) for k in ("trades", "split_merge", "transfer")) and conv_ok
    return inflows, inflows and bool(cov.get("redeem"))


# ---------------------------------------------------------------------------------------------------------------
# Ledger
# ---------------------------------------------------------------------------------------------------------------

class Ledger:
    """Event ledger for a set of conditions. Build once, then query snapshots as of any T.

    market_info[cid] = {"history_complete": bool, "neg_risk": bool|None, "coverage": dict, "fees_enabled": bool|None,
                        "wallet_coverage": {wallet: coverage dict} (optional, e.g. a wallet whose activity feed
                        was read)}
    history_complete is False when the source tape does not reach the market's first fill (initial position unknown).

    When some event is seen after it happened (seen_ts > ts), a snapshot at T is computed on a ledger rebuilt from
    the events seen by T only, so transaction checks, flags and prices are as known at T.
    """

    def __init__(self, events, market_info, check_tx=True):
        self.info = {c.lower(): dict(v) for c, v in market_info.items()}
        self._all_input = list(events)
        self._check_tx = check_tx
        self.tx_verdicts = {}
        self.fee_rates = {}           # (tx, cid) -> implied fee rate, for FEE_IN_SHARES and UNBALANCED groups
        self.no_tx_rows = defaultdict(int)
        self.quarantine = []          # events refused at build time, with the reason
        self.wallet_flags = defaultdict(lambda: defaultdict(set))   # (wallet,cid) -> ts -> {flags}
        evs = []
        for e in events:
            if e["cid"] not in self.info:
                self.quarantine.append((e, "UNKNOWN_MARKET"))
                continue
            evs.append(e)
        self.has_late = any(e["seen_ts"] > e["ts"] for e in evs)
        self._asof_cache = {}
        if check_tx:
            evs = self._check_transactions(evs)
        else:
            for e in evs:
                if e["kind"] in TRADE_KINDS:
                    self.wallet_flags[(e["wallet"], e["cid"])][e["ts"]].add("TX_UNCHECKED")
        evs.sort(key=order_key)
        self.events = evs
        self.by_book = defaultdict(list)
        for e in evs:
            self.by_book[(e["wallet"], e["cid"])].append(e)
        self._build()

    def _check_transactions(self, evs):
        groups = defaultdict(list)
        out = []
        for e in evs:
            if e["kind"] in TRADE_KINDS:
                groups[(e["tx"], e["cid"])].append(e)
            else:
                out.append(e)
        for (tx, cid), rows in groups.items():
            kept, verdict = reconcile_tx(rows, fees_enabled=self.info[cid].get("fees_enabled") is True)
            if tx:
                self.tx_verdicts[(tx, cid)] = verdict
                if verdict in ("FEE_IN_SHARES", "UNBALANCED"):
                    self.fee_rates[(tx, cid)] = implied_fee_rate(rows)
            else:
                self.no_tx_rows[cid] += len(rows)
            if verdict == "DUPLICATES_DROPPED":
                kept_ids = {id(x) for x in kept}
                for x in rows:
                    if id(x) not in kept_ids:
                        self.quarantine.append((x, "DUPLICATE_ROW"))
            flag = {"UNBALANCED": "TX_UNBALANCED", "MULTI_TIMESTAMP": "TX_UNBALANCED", "NO_TX": "TX_UNCHECKED"}.get(verdict)
            if flag:
                for x in rows:
                    self.wallet_flags[(x["wallet"], cid)][x["ts"]].add(flag)
            out.extend(kept)
        return out

    def _build(self):
        """Running state per (wallet, cid), one entry per applied event. Running minima are taken at the end of each
        second only: the order of fills inside one second is unknown, so it must not create a negative trough."""
        self.books = {}
        for e in self.events:
            key = (e["wallet"], e["cid"])
            b = self.books.get(key)
            if b is None:
                b = self.books[key] = {"ts": [], "q0": [], "q1": [], "cash": [], "min0": [], "min1": [],
                                       "cash_known": []}
            p0 = b["q0"][-1] if b["q0"] else 0.0
            p1 = b["q1"][-1] if b["q1"] else 0.0
            d0, d1, dc = token_delta(e, (p0, p1))
            pc = b["cash"][-1] if b["cash"] else 0.0
            ck = b["cash_known"][-1] if b["cash_known"] else True
            b["ts"].append(e["ts"])
            b["q0"].append(p0 + d0)
            b["q1"].append(p1 + d1)
            b["cash"].append(pc + (dc or 0.0))
            b["cash_known"].append(ck and (dc is not None or e["kind"] in ("CONVERT_IN", "TRANSFER_IN",
                                                                             "TRANSFER_OUT")))
        for b in self.books.values():
            m0 = m1 = 0.0
            n = len(b["ts"])
            for i in range(n):
                if i == n - 1 or b["ts"][i + 1] != b["ts"][i]:      # last event of its second
                    m0, m1 = min(m0, b["q0"][i]), min(m1, b["q1"][i])
                b["min0"].append(m0)
                b["min1"].append(m1)
        self.prices = defaultdict(lambda: ([], []))
        for e in self.events:
            if e["kind"] in TRADE_KINDS:
                ts_l, p_l = self.prices[(e["cid"], e["oi"])]
                ts_l.append(e["ts"])
                p_l.append(e["price"])

    def _asof(self, T):
        """Ledger rebuilt from what was seen by T (only when some data arrived late)."""
        if not self.has_late:
            return self
        lg = self._asof_cache.get(T)
        if lg is None:
            lg = Ledger([e for e in self._all_input if e["seen_ts"] <= T], self.info, self._check_tx)
            self._asof_cache[T] = lg
        return lg

    def coverage(self, wallet, cid):
        info = self.info[cid]
        return info.get("wallet_coverage", {}).get(wallet, info.get("coverage", TAPE_COVERAGE))

    # -----------------------------------------------------------------------------------------------------------
    def snapshot(self, wallet, cid, T):
        """Position of one wallet in one condition as known at T. Never uses anything after T."""
        lg = self._asof(T)
        wallet, cid = wallet.lower(), cid.lower()
        info = lg.info[cid]
        cov = lg.coverage(wallet, cid)
        neg_risk = info.get("neg_risk")
        b = lg.books.get((wallet, cid))
        n = bisect.bisect_right(b["ts"], T) if b else 0
        if n == 0:
            q0 = q1 = cash = m0 = m1 = 0.0
            cash_known = True
        else:
            i = n - 1
            q0, q1, cash = b["q0"][i], b["q1"][i], b["cash"][i]
            m0, m1, cash_known = b["min0"][i], b["min1"][i], b["cash_known"][i]
        reasons = []
        if not info.get("history_complete", False):
            reasons.append("INITIAL_POSITION_UNKNOWN")
        flags = set()
        for ts, fl in lg.wallet_flags.get((wallet, cid), {}).items():
            if ts <= T:
                flags |= fl
        reasons += sorted(flags)

        inflows_cov, all_cov = coverage_flags(cov, neg_risk)
        neg_inventory = m0 < -EPS or m1 < -EPS
        x_reasons = []
        if not cov.get("transfer"):
            x_reasons.append("TRANSFERS_NOT_COVERED")
        if neg_risk and not cov.get("convert"):
            x_reasons.append("CONVERSIONS_NOT_COVERED")
        if neg_risk is None and not cov.get("convert"):
            x_reasons.append("NEG_RISK_FLAG_UNKNOWN")
        if not cov.get("redeem"):
            x_reasons.append("REDEMPTIONS_NOT_COVERED")       # burns tokens; possible only after resolution
        if neg_inventory:
            # sold more than held: with every inflow class covered an event is missing; otherwise a split, transfer
            # or conversion the source cannot see brought the tokens in
            x_reasons.append("NEGATIVE_INVENTORY_WITH_FULL_COVERAGE" if inflows_cov else "UNOBSERVED_INFLOW_PROVEN")
        allr = set(reasons + x_reasons)
        if allr & HARD_REASONS:
            x_status = "UNKNOWN"
        elif allr:
            x_status = "OBSERVABLE"
        else:
            x_status = "EXACT"

        if x_status == "UNKNOWN":
            inv_status, lo, hi = "UNKNOWN", None, None
        elif all_cov:
            inv_status, lo, hi = "EXACT", [q0, q1], [q0, q1]
        elif inflows_cov:
            # only invisible class left burns tokens (redemption): flows are an upper bound, 0 the lower one
            inv_status, lo, hi = "BOUNDED", [0.0, 0.0], [q0, q1]
        else:
            # true q_i = flow_i + s + u_i, s = net split-merge (common), u_i = unobserved transfers/conversions/
            # redemptions. With u = 0 assumed, q >= 0 forces s >= -min(q0, q1): lower bound = directional part.
            # Proven unconditionally: q_i >= 0. No upper bound without split coverage.
            x = q0 - q1
            inv_status, lo, hi = "BOUNDED", [max(x, 0.0), max(-x, 0.0)], None
        return {
            "wallet": wallet, "cid": cid, "as_of": int(T), "events_used": n,
            "observable": {"flow_yes": q0, "flow_no": q1, "x_yes_equiv": q0 - q1,
                           # fees not in the source on a market that may charge them: the cash leg is not known
                           "cash_flow": cash if cash_known and (cov.get("fees") or info.get("fees_enabled") is False
                                                                 or n == 0) else None,
                           "proven_unobserved_inflow": [max(0.0, -m0), max(0.0, -m1)]},
            "x_status": x_status,
            "inventory": {"status": inv_status, "lo": lo, "hi": hi,
                          "lo_assumes": ("no unobserved transfer, conversion or redemption"
                                         if inv_status == "BOUNDED" and hi is None else None)},
            "reasons": sorted(allr),
            "fees": "UNKNOWN" if not cov.get("fees") and info.get("fees_enabled") is not False else "NONE_OR_COVERED",
        }

    def window_events(self, wallet, cid, t0, t1):
        """Events of one wallet in (t0, t1], in ledger order, as known at t1."""
        lg = self._asof(t1)
        wallet, cid = wallet.lower(), cid.lower()
        return [e for e in lg.by_book.get((wallet, cid), ()) if t0 < e["ts"] <= t1]

    def wallets(self, cid=None):
        return sorted({w for (w, c) in self.books if cid is None or c == cid.lower()})

    def last_price(self, cid, oi, T):
        """Last executed price of token (cid, oi) at or before T, as known at T (never a later price)."""
        lg = self._asof(T)
        ts_l, p_l = lg.prices.get((cid.lower(), oi), ([], []))
        i = bisect.bisect_right(ts_l, T)
        return p_l[i - 1] if i else None


# ---------------------------------------------------------------------------------------------------------------
# Families and payoff vectors
# ---------------------------------------------------------------------------------------------------------------

def family_binary(cid):
    return {"type": "binary", "worlds": ["YES", "NO"], "members": [cid.lower()],
            "payoff": {(cid.lower(), YES): [1, 0], (cid.lower(), NO): [0, 1]}, "proof": "single condition"}


def family_exclusive(cids, exhaustive=False, proof=""):
    """Neg-risk event: exactly one member resolves YES (or none of the listed ones, world OTHER)."""
    cids = [c.lower() for c in cids]
    worlds = list(cids) + ([] if exhaustive else ["OTHER"])
    pay = {}
    for i, c in enumerate(cids):
        pay[(c, YES)] = [1 if j == i else 0 for j in range(len(worlds))]
        pay[(c, NO)] = [0 if j == i else 1 for j in range(len(worlds))]
    return {"type": "exclusive", "worlds": worlds, "members": cids, "payoff": pay, "proof": proof}


def family_ladder(cids_by_deadline, proof):
    """Nested deadlines D1 < ... < Dk of the SAME event (proof required). Worlds are realisation intervals."""
    cids = [c.lower() for c, _ in cids_by_deadline]
    ds = [d for _, d in cids_by_deadline]
    if any(ds[i] >= ds[i + 1] for i in range(len(ds) - 1)):
        raise ValueError("deadlines must be strictly increasing")
    k = len(cids)
    worlds = [f"<= {ds[0]}"] + [f"({ds[i - 1]}, {ds[i]}]" for i in range(1, k)] + [f"> {ds[-1]}"]
    pay = {}
    for i, c in enumerate(cids):
        pay[(c, YES)] = [1 if w <= i else 0 for w in range(k + 1)]   # happened by D_i
        pay[(c, NO)] = [0 if w <= i else 1 for w in range(k + 1)]
    return {"type": "ladder", "worlds": worlds, "members": cids, "payoff": pay, "proof": proof, "deadlines": ds}


def payoff_vector(ledger, wallet, fam, T):
    """Q(T): payout per world from the wallet's flows in every member. Shape = Q - min(Q) is invariant to splits,
    merges and (inside a complete exclusive family) conversions; the level min(Q) is not observable from fills."""
    n = len(fam["worlds"])
    q = [0.0] * n
    lo, hi = [0.0] * n, [0.0] * n
    reasons = set()
    for c in fam["members"]:
        s = ledger.snapshot(wallet, c, T)
        reasons |= set(s["reasons"])
        inv = s["inventory"]
        for oi, f in ((YES, s["observable"]["flow_yes"]), (NO, s["observable"]["flow_no"])):
            row = fam["payoff"][(c, oi)]
            for j in range(n):
                q[j] += f * row[j]
                if lo is not None:
                    lo = None if inv["lo"] is None else lo
                if lo is not None:
                    lo[j] += inv["lo"][oi] * row[j]
                if hi is not None:
                    hi = None if inv["hi"] is None else hi
                if hi is not None:
                    hi[j] += inv["hi"][oi] * row[j]
    if fam["type"] == "exclusive" and "OTHER" not in fam["worlds"]:
        reasons.discard("CONVERSIONS_NOT_COVERED")   # conversion inside a complete event leaves the shape unchanged
    if reasons & HARD_REASONS:
        status = "UNKNOWN"
    elif reasons:
        status = "OBSERVABLE"
    else:
        status = "EXACT"
    m = min(q)
    # q_flow is implied by flows, not holdings; the payout level per world is bounded by the member inventories
    return {"worlds": fam["worlds"], "q_flow": q, "shape": [v - m for v in q], "status": status,
            "payout_lo": lo, "payout_hi": hi, "reasons": sorted(reasons), "as_of": int(T)}


def vector_change(v0, v1):
    return {"worlds": v0["worlds"], "d_shape": [b - a for a, b in zip(v0["shape"], v1["shape"])],
            "d_q_flow": [b - a for a, b in zip(v0["q_flow"], v1["q_flow"])],
            "status": "UNKNOWN" if "UNKNOWN" in (v0["status"], v1["status"]) else
            ("OBSERVABLE" if "OBSERVABLE" in (v0["status"], v1["status"]) else "EXACT")}


# ---------------------------------------------------------------------------------------------------------------
# Classification of a wallet's change between two instants (A / B / C / D, strictly separated)
# ---------------------------------------------------------------------------------------------------------------

CLASSES = ("UNRESOLVED_FAMILY", "UNKNOWN", "NONE", "C_TECHNICAL", "C_MARKET_MAKING", "C_COMPLETE_SET",
           "B_INTERVAL_PACKAGE", "A_TRUE_INVERSION", "D_YES_ACCUM_KEEP_NO", "D_UNVERIFIED_NO_RETENTION",
           "C_HEDGE_REBALANCE", "DIRECTIONAL_ADD")


def classify(ledger, wallet, fam, t0, t1, min_payout=MIN_PAYOUT, mm_ratio=MM_RATIO):
    """Classify the change of one wallet's family position over (t0, t1]. First matching rule wins; the order is
    part of the definition (see POSITION_SCHEMA.md). Returns {"class", "evidence"}."""
    if fam["type"] == "unproven":
        return {"class": "UNRESOLVED_FAMILY", "evidence": {"why": fam.get("proof")}}
    wallet = wallet.lower()
    v0 = payoff_vector(ledger, wallet, fam, t0)
    v1 = payoff_vector(ledger, wallet, fam, t1)
    ev = {"v0": v0, "v1": v1}
    if "UNKNOWN" in (v0["status"], v1["status"]):
        return {"class": "UNKNOWN", "evidence": ev}
    win = []
    for c in fam["members"]:
        win += ledger.window_events(wallet, c, t0, t1)
    if not win:
        return {"class": "NONE", "evidence": ev}
    trades = [e for e in win if e["kind"] in TRADE_KINDS]
    if not trades:
        return {"class": "C_TECHNICAL", "evidence": {**ev, "kinds": sorted({e["kind"] for e in win})}}
    s0, s1 = v0["shape"], v1["shape"]
    d = [b - a for a, b in zip(s0, s1)]
    dmax = max(abs(x) for x in d)
    ev["d_shape"] = d
    notional = sum(e["qty"] * e["price"] for e in trades)
    ev["traded_notional"] = notional

    by_tok = defaultdict(lambda: [0.0, 0.0])   # (cid, oi) -> [bought, sold] in the window
    for e in trades:
        by_tok[(e["cid"], e["oi"])][0 if e["kind"] == "BUY" else 1] += e["qty"]
    # C, market making: same token bought and sold, traded notional >= MM_RATIO x the net change marked per token
    two_sided = any(b > EPS and s > EPS for b, s in by_tok.values())
    marked_net = 0.0
    for (c, oi), (b_, s_) in by_tok.items():
        p = ledger.last_price(c, oi, t1)
        marked_net += abs(b_ - s_) * (p if p is not None else 1.0)   # unknown price: marked at the 1.0 payout cap
    ev["marked_net_change"] = marked_net
    if two_sided and notional >= mm_ratio * max(marked_net, EPS):
        return {"class": "C_MARKET_MAKING", "evidence": ev}
    if dmax < min_payout:
        # material trading that leaves the payoff shape unchanged: complete set (pair of a member, or YES / NO on
        # every member of an exclusive event): arbitrage or a synthetic split/merge
        tokens = [k for k, (b_, s_) in by_tok.items() if b_ + s_ > EPS]
        shares = sum(b_ + s_ for b_, s_ in by_tok.values())
        if len(tokens) >= 2 and shares >= min_payout:
            return {"class": "C_COMPLETE_SET", "evidence": ev}
        return {"class": "NONE", "evidence": ev}

    sold_any = any(s_ > EPS for _, s_ in by_tok.values())
    if fam["type"] == "ladder" and not sold_any:
        # B: NO on an earlier deadline and YES on a later one, both held at t1, at least one leg bought in the
        # window, no sale and no buy against a side already held on the same deadline (that would be a disposal).
        k = len(fam["members"])
        snap0 = {c: ledger.snapshot(wallet, c, t0)["observable"] for c in fam["members"]}
        snap1 = {c: ledger.snapshot(wallet, c, t1)["observable"] for c in fam["members"]}
        opposite = any((by_tok[(c, YES)][0] > EPS and snap0[c]["x_yes_equiv"] <= -min_payout) or
                       (by_tok[(c, NO)][0] > EPS and snap0[c]["x_yes_equiv"] >= min_payout) for c in fam["members"])
        if not opposite:
            m = fam["members"]
            pairs = [(i, j) for i in range(k) for j in range(i + 1, k)
                     if -snap1[m[i]]["x_yes_equiv"] >= min_payout and snap1[m[j]]["x_yes_equiv"] >= min_payout
                     and (by_tok[(m[i], NO)][0] >= min_payout or by_tok[(m[j], YES)][0] >= min_payout)]
            if pairs:
                return {"class": "B_INTERVAL_PACKAGE", "evidence": {**ev, "pairs": pairs}}
    # A: the payoff difference between the same two worlds changes sign, both sides material.
    n = len(s0)
    for j in range(n):
        for k2 in range(j + 1, n):
            a, b = s0[j] - s0[k2], s1[j] - s1[k2]
            if abs(a) >= min_payout and abs(b) >= min_payout and (a > 0) != (b > 0):
                return {"class": "A_TRUE_INVERSION", "evidence": {**ev, "worlds": [fam["worlds"][j],
                                                                                    fam["worlds"][k2]]}}
    if fam["type"] == "binary":
        c = fam["members"][0]
        no0 = ledger.snapshot(wallet, c, t0)["observable"]["flow_no"]
        no1 = ledger.snapshot(wallet, c, t1)["observable"]["flow_no"]
        bought_yes, sold_no = by_tok[(c, YES)][0], by_tok[(c, NO)][1]
        if bought_yes >= min_payout and no0 >= min_payout and no1 >= min_payout and sold_no <= EPS:
            win_kinds = {e["kind"] for e in win}
            merges_visible = bool(ledger.coverage(wallet, c).get("split_merge"))
            if merges_visible:
                # NO flow already nets merges; retention is proven up to transfers
                return {"class": "D_YES_ACCUM_KEEP_NO", "evidence": {**ev, "no_t0": no0, "no_t1": no1}}
            return {"class": "D_UNVERIFIED_NO_RETENTION",
                    "evidence": {**ev, "no_flow_t0": no0, "no_flow_t1": no1, "kinds": sorted(win_kinds),
                                 "why": "NO kept on fills only; a merge, invisible in the tape, can remove NO"}}
    if max(s1) < max(s0) - min_payout:
        return {"class": "C_HEDGE_REBALANCE", "evidence": ev}
    return {"class": "DIRECTIONAL_ADD", "evidence": ev}


# ---------------------------------------------------------------------------------------------------------------
# Deadline nesting proof (conservative): same event, same rules text once dates are masked, cumulative wording.
# ---------------------------------------------------------------------------------------------------------------

_MONTHS = "january|february|march|april|may|june|july|august|september|october|november|december"
_DATE = re.compile(rf"\b(?:{_MONTHS})\s+\d{{1,2}}(?:st|nd|rd|th)?(?:,?\s+\d{{4}})?|\b\d{{4}}-\d{{2}}-\d{{2}}\b|"
                   rf"\b(?:{_MONTHS})\b(?:\s+\d{{4}})?|\b\d{{1,2}}:\d{{2}}\s*(?:am|pm)?\b|\b20\d\d\b", re.I)
_CUMULATIVE = re.compile(r"\b(by|before|on or before|by end of|no later than)\b", re.I)
_DISJOINT = re.compile(r"\b(on|in|during)\s+(?:" + _MONTHS + r")\b", re.I)


def mask_dates(text):
    return re.sub(r"\s+", " ", _DATE.sub("<DATE>", text or "")).strip().lower()


def parse_deadline(question):
    """'... by February 28, 2026?' -> date. None if the question does not carry one explicit full date."""
    m = re.findall(rf"\b({_MONTHS})\s+(\d{{1,2}})(?:st|nd|rd|th)?,?\s+(\d{{4}})", question or "", re.I)
    if len(m) != 1:
        return None
    mon, day, yr = m[0]
    try:
        return _dt.date(int(yr), _MONTHS.split("|").index(mon.lower()) + 1, int(day))
    except ValueError:
        return None


def prove_ladder(metas):
    """metas: Gamma rows of markets of one event. Returns a family (ladder) or {"type": "unproven", ...}.

    Proof = (i) not neg-risk, (ii) every question has cumulative wording ('by', 'before') and no 'on/in <month>'
    wording, (iii) questions identical once dates are masked, (iv) descriptions identical once dates are masked,
    (v) one explicit full deadline date per question, all distinct. Titles alone are never enough."""
    if len(metas) < 2:
        return {"type": "unproven", "proof": "fewer than two markets"}
    if any(m.get("negRisk") for m in metas):
        return {"type": "unproven", "proof": "neg-risk event: exclusive outcomes, not a deadline ladder"}
    qs = [m.get("question") or "" for m in metas]
    if not all(_CUMULATIVE.search(q) for q in qs) or any(_DISJOINT.search(q) for q in qs):
        return {"type": "unproven", "proof": "wording is not cumulative ('by'/'before') for every member"}
    if len({mask_dates(q) for q in qs}) != 1:
        return {"type": "unproven", "proof": "questions differ beyond the date"}
    if len({mask_dates(m.get("description")) for m in metas}) != 1:
        return {"type": "unproven", "proof": "rules text differs beyond the date"}
    ds = [parse_deadline(q) for q in qs]
    if any(d is None for d in ds) or len(set(ds)) != len(ds):
        return {"type": "unproven", "proof": "no single explicit deadline date per question"}
    order = sorted(zip([m["conditionId"] for m in metas], ds), key=lambda x: x[1])
    return family_ladder([(c, d.isoformat()) for c, d in order],
                         proof="same event, cumulative wording, question and rules identical modulo date")


# ---------------------------------------------------------------------------------------------------------------
# Partitions. Observations are assigned by their own time (t1 of the window), which no outcome can move. The frozen
# study's rule (market close time) is kept for reference only: close time depends on the outcome for 'by date'
# markets (early YES closes early). Iran cohort and Iran event never in VALID or TEST.
# ---------------------------------------------------------------------------------------------------------------

BOUNDS = (("TRAIN", "2025-01-01T00:00:00", "2025-12-31T23:59:59"),
          ("VALID", "2026-01-01T00:00:00", "2026-06-30T23:59:59"),
          ("TEST", "2026-07-01T00:00:00", "2026-10-31T23:59:59"))
IRAN_SLUG_PREFIXES = ("us-strikes-iran",)


def _epoch(s):
    return int(_dt.datetime.fromisoformat(s).replace(tzinfo=_dt.timezone.utc).timestamp())


def period_of(t):
    if t is None:
        return "UNKNOWN_TIME"
    for name, lo, hi in BOUNDS:
        if _epoch(lo) <= t <= _epoch(hi):
            return name
    return "EXCLUDED_PERIOD"


def partition_of(cid, closed_ts, event_slug="", iran_cids=(), iran_slug_prefixes=IRAN_SLUG_PREFIXES):
    """Frozen study's market-level rule (by close time), for reference and comparison."""
    if cid.lower() in {c.lower() for c in iran_cids} or any((event_slug or "").startswith(p)
                                                             for p in iran_slug_prefixes):
        return "EXPLORATORY_IRAN"
    return "UNKNOWN_CLOSE" if closed_ts is None else period_of(closed_ts)


def observation_partition(t1, wallet="", event_slug="", cids=(), iran_wallets=(), iran_cids=(),
                          iran_slug_prefixes=IRAN_SLUG_PREFIXES):
    """Partition of one observation (wallet, family, window ending at t1). Iran cohort wallets and Iran markets are
    exploratory whatever the period: they never enter TRAIN, VALID or TEST."""
    if any((event_slug or "").startswith(p) for p in iran_slug_prefixes) or \
            {c.lower() for c in cids} & {c.lower() for c in iran_cids}:
        return "EXPLORATORY_IRAN"
    if wallet.lower() in iran_wallets:
        return "EXPLORATORY_IRAN"
    return period_of(t1)


def usable_for_training(market_close_ts, partition):
    """Purge rule for later missions: an observation can be trained on only if its market's label existed by the end
    of the observation's own partition (the trainer could not have known it otherwise)."""
    for name, _, hi in BOUNDS:
        if name == partition:
            return market_close_ts is not None and market_close_ts <= _epoch(hi)
    return False


def window_index(ts, w=3600):
    """Index k of the window (k*w, (k+1)*w] that contains ts (windows are open on the left, closed on the right)."""
    return (ts - 1) // w


def events_from_tape_rows(rows, src_prefix):
    """rows: (rowid, condition_id, ts, wallet, side, outcome, outcome_index, size, price, tx). Tape order kept as seq."""
    out = []
    for rowid, cid, ts, w, side, oc, oi, size, price, tx in rows:
        out.append(make_event(ts, w, cid, side, oi=int(oi), qty=size, price=price, tx=tx, seq=rowid,
                              src=f"{src_prefix}#rowid={rowid}"))
    return out


if __name__ == "__main__":
    print(json.dumps({"kinds": KINDS, "classes": CLASSES, "min_payout": MIN_PAYOUT}, indent=1))
