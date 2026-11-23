"""Offline: turn the collected logs into an integer-unit position ledger and per-market, per-wallet PnL.

Ground truth is what each account actually sent and received in each transaction: ERC-20 collateral transfers and
ERC-1155 position transfers. OrderFilled and the split / merge / redeem / convert events only classify a transaction
and give execution prices, so a fee is never counted twice (it is already inside the transfers; V1 fee refunds too).
Amounts are integers in 1e-6 units (collateral and shares alike). PnL uses exact fractions.

Per account and market (condition): cash_pnl = sum of the collateral the account received minus what it paid in the
transactions attributed to that market; inventory = position tokens still held; net_position_pnl = cash_pnl + the
value of that inventory (official payout vector when resolved, a timestamped mark when open, else UNKNOWN).
Realized and unrealized parts use average cost per outcome token. Exact identity checked for every position:
    realized + unrealized - transfer_out_cost == cash_pnl + inventory_value
Deposits, withdrawals and wraps (transactions that move only collateral) never enter trading PnL.
"""

import gzip
import hashlib
import json
from collections import defaultdict
from fractions import Fraction
from pathlib import Path

USDC_E = "0x2791bca1f2de4661ed88a30c99a7a9449aa84174"
PUSD = "0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb"
USDC = "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359"
WCOL = "0x3a3bd7bb9528e159577f7c2e685cc81a765002e2"
COLLATERAL = {USDC_E: "USDC.e", PUSD: "pUSD", USDC: "USDC", WCOL: "WrappedCollateral"}
CTF = "0x4d97dcd97ec945f40cf65f87097ace5ea0476045"
POSITION_MANAGER = "0x006f54f7f9a22e0000cc2ab60031000000ae9fef"
POSITIONS = {CTF: "CTF", POSITION_MANAGER: "PositionManager"}
EXCHANGES = {
    "0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e": ("v1", CTF),
    "0xc5d563a36ae78145c45a50134d48a1215220f80a": ("v1", CTF),
    "0xe111180000d2663c0091e4f400237545b87b996b": ("v2", CTF),
    "0xe2222d279d744050d28e00520010520000310f59": ("v2", CTF),
    "0xe3333700ca9d93003f00f0f71f8515005f6c00aa": ("v3", POSITION_MANAGER),
}
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
TRANSFER_SINGLE = "0xc3d58168c5ae7397731d063d5bbf3d657854427343f4c083240f7aacaa2d0f62"
TRANSFER_BATCH = "0x4a39dc06d4c0dbc64b70af90fd698a233a518aa5d07e595d983b8c0526c8f7fb"
V1_FILL = "0xd0a08e8c493f9c94f29311604c9de1b4e8c8d4c06bd0c789af57f2d65bfec0f6"
V2_FILL = "0xd543adfd945773f1a62f74f0ee55a5e3b9b1a28262980ba90b1a89f2ea84d8ee"
# topic0 -> (kind, layout); the account is always topic 1
EVENTS = {
    "0x2e6bb91f8cbcda0c93623c54d0403a43514fabc40084ec96b6d5379a74786298": ("SPLIT", "ctf"),
    "0x6f13ca62553fcc2bcd2372180a43949c1e4cebba603901ede2f4e14f36b282ca": ("MERGE", "ctf"),
    "0x2682012a4a4f1973119f1c9b90745d1bd91fa2bab387344f044cb3586864d18d": ("REDEEM", "ctf_redeem"),
    "0xbbed930dbfb7907ae2d60ddf78345610214f26419a0128df39b6cc3d9e5df9b0": ("SPLIT", "nra"),
    "0xba33ac50d8894676597e6e35dc09cff59854708b642cd069d21eb9c7ca072a04": ("MERGE", "nra"),
    "0xb03d19dddbc72a87e735ff0ea3b57bef133ebe44e1894284916a84044deb367e": ("CONVERT", "nra_convert"),
    "0x9140a6a270ef945260c03894b3c6b3b2695e9d5101feef0ff24fec960cfd3224": ("REDEEM", "nra_redeem"),
    "0x1b8b64a5dd5755bb862006962dbcd07c11ab463091508bcaa350192a43022319": ("CONVERT", "nra_convert"),
    "0x08c15f31e413dbd9bbd3b4c01b191db840e1657ab4f8d1d7d448a9a5083ba255": ("MERGE", "nra"),
    "0x1daec0b1f629de29b749a189499f43104a80df46a9f34d9ccf73aa59b85fc0c0": ("REDEEM", "nra_redeem"),
}
SIX = Fraction(1, 10**6)
# A share outflow without collateral whose only counterparties are these is a destruction (redemption or write-off at
# zero), not a transfer to another owner. Burn sinks, the CTF and Neg Risk Adapter, and the 2026 collateral adapters.
DISPOSAL_COUNTERPARTIES = {
    "0x" + "0" * 40, "0x000000000000000000000000000000000000dead", CTF, "0xd91e80cf2e7be2e162c6513ced06f1dd0da35296",
    "0xada100db00ca00073811820692005400218fce1f", "0xada2005600dec949baf300f4c6120000bdb6eaab",
    "0xada100874d00e3331d00f2007a9c336a65009718", "0xada200001000ef00d07553cee7006808f895c6f1"}


def words(data):
    h = data[2:] if data.startswith("0x") else data
    return [int(h[i:i + 64], 16) for i in range(0, len(h), 64)]


def addr(topic):
    return "0x" + topic[-40:].lower()


def fmt(x):
    """Exact fraction of 1e-6 units -> decimal string with six places (rounded half away from zero)."""
    if x is None:
        return "UNKNOWN"
    q = x * SIX
    sign = "-" if q < 0 else ""
    q = abs(q)
    n = (q.numerator * 10**6 * 2 + q.denominator) // (2 * q.denominator)
    return f"{sign}{n // 10**6}.{n % 10**6:06d}"


# ---------------------------------------------------------------- loading

def load(raw):
    """Read every accepted range listed in checkpoint.jsonl; verify files, coverage and duplicates."""
    plan = json.loads((raw / "plan.json").read_text())
    cks = [json.loads(line) for line in (raw / "checkpoint.jsonl").read_text().splitlines() if line.strip()]
    streams = defaultdict(list)
    for c in cks:
        streams[(c["filter"], c["chunk"])].append(c)
    coverage = {}
    for k, cs in sorted(streams.items()):
        cs.sort(key=lambda c: c["from"])
        pos, contiguous = plan["start_block"], True
        for c in cs:
            if c["from"] != pos:
                contiguous = False
                break
            pos = c["to"] + 1
        coverage[f"{k[0]}/{k[1]}"] = {"ranges": len(cs), "logs": sum(c["n"] for c in cs),
                                      "reached_block": pos - 1,
                                      "complete": contiguous and pos == plan["end_block"] + 1}
    logs, problems, hashes = {}, [], {}
    for c in cks:
        blob = (raw / c["file"]).read_bytes()
        if hashlib.sha256(blob).hexdigest() != c["sha256"]:
            problems.append({"kind": "FILE_HASH_MISMATCH", "file": c["file"]})
            continue
        for x in json.loads(gzip.decompress(blob))["logs"]:
            key = (x["transactionHash"].lower(), int(x["logIndex"], 16))
            norm = {"address": x["address"].lower(), "topics": [t.lower() for t in x["topics"]],
                    "data": x["data"].lower(), "block": int(x["blockNumber"], 16),
                    "block_hash": x["blockHash"].lower(), "ts": int(x["blockTimestamp"], 16),
                    "tx": key[0], "log_index": key[1], "removed": bool(x.get("removed"))}
            if norm["removed"]:
                problems.append({"kind": "REMOVED_LOG", "tx": key[0], "log_index": key[1]})
                continue
            h = hashes.setdefault(norm["block"], norm["block_hash"])
            if h != norm["block_hash"]:
                problems.append({"kind": "BLOCK_HASH_CONFLICT", "block": norm["block"], "hashes": [h, norm["block_hash"]]})
            old = logs.get(key)
            if old is None:
                logs[key] = norm
            elif old != norm:
                problems.append({"kind": "DUPLICATE_DIFFERS", "tx": key[0], "log_index": key[1]})
    return plan, coverage, logs, problems


def canonical(logs, canonical_hash):
    """Keep only logs whose block hash is the canonical one (reorg guard; canonical_hash: block -> hash)."""
    kept, dropped = {}, []
    for k, x in logs.items():
        want = canonical_hash.get(x["block"])
        (kept.__setitem__(k, x) if want in (None, x["block_hash"]) else dropped.append(k))
    return kept, dropped


# ---------------------------------------------------------------- decoding

def batch_pairs(data):
    w = words(data)
    oi, ov = w[0] // 32, w[1] // 32
    ids, vals = w[oi + 1:oi + 1 + w[oi]], w[ov + 1:ov + 1 + w[ov]]
    if len(ids) != len(vals):
        raise ValueError("TransferBatch ids and values differ in length")
    return list(zip(ids, vals))


def decode_fill(x):
    version, pos = EXCHANGES[x["address"]]
    t, w = x["topics"], words(x["data"])
    f = {"exchange": x["address"], "version": version, "position_contract": pos, "order_hash": t[1],
         "maker": addr(t[2]), "taker": addr(t[3]), "log_index": x["log_index"]}
    if version == "v1":
        maker_asset, taker_asset, mamt, tamt, fee = w[:5]
        if maker_asset == 0:
            f.update(side="BUY", token=taker_asset, cash=mamt, shares=tamt, fee=fee)
        elif taker_asset == 0:
            f.update(side="SELL", token=maker_asset, cash=tamt, shares=mamt, fee=fee)
        else:
            f.update(side="UNKNOWN", token=None, cash=0, shares=0, fee=fee)
    else:
        side, token, mamt, tamt, fee = w[:5]
        if side == 0:
            f.update(side="BUY", token=token, cash=mamt, shares=tamt, fee=fee)
        else:
            f.update(side="SELL", token=token, cash=tamt, shares=mamt, fee=fee)
    return f


def expected_cash(f):
    """Signed collateral the owner should see for one fill under the verified fee rules (before V1 refunds)."""
    if f["side"] == "BUY":
        return -(f["cash"] + (f["fee"] if f["version"] != "v1" else 0))
    if f["side"] == "SELL":
        return f["cash"] - f["fee"]
    return 0


def decode_event(x):
    kind, layout = EVENTS[x["topics"][0]]
    t, w = x["topics"], words(x["data"])
    e = {"kind": kind, "emitter": x["address"], "account": addr(t[1]), "log_index": x["log_index"],
         "condition": None, "market": None, "amount": None, "payout": None}
    if layout == "ctf":
        e.update(condition=t[3], amount=w[2])
    elif layout == "ctf_redeem":
        e.update(condition="0x%064x" % w[0], payout=w[2])
    elif layout == "nra":
        e.update(condition=t[2], amount=w[0])
    elif layout == "nra_convert":
        e.update(market=t[2], amount=w[0])
    elif layout == "nra_redeem":
        e.update(condition=t[2], payout=w[1])
    return e


def account_txs(logs, accounts):
    """(account, tx) -> record of net collateral and position deltas, fills and events (fully deterministic)."""
    acct = set(accounts)
    recs = {}

    def rec(a, x):
        k = (a, x["tx"])
        if k not in recs:
            recs[k] = {"account": a, "tx": x["tx"], "block": x["block"], "ts": x["ts"], "first_log": x["log_index"],
                       "cash": defaultdict(int),
                       "shares": defaultdict(int), "fills": [], "events": [], "counterparties": set(),
                       "other_tokens": defaultdict(int)}
        return recs[k]

    unknown_topics = defaultdict(int)
    for x in sorted(logs.values(), key=lambda x: (x["block"], x["log_index"])):
        t0 = x["topics"][0] if x["topics"] else None
        a = x["address"]
        if t0 == TRANSFER and len(x["topics"]) == 3:
            frm, to, v = addr(x["topics"][1]), addr(x["topics"][2]), int(x["data"] or "0x0", 16)
            for side, who, other in ((-1, frm, to), (1, to, frm)):
                if who in acct and frm != to:
                    r = rec(who, x)
                    if a in COLLATERAL:
                        r["cash"][a] += side * v
                        r["counterparties"].add(other)
                    else:
                        r["other_tokens"][a] += side * v
        elif t0 in (TRANSFER_SINGLE, TRANSFER_BATCH) and len(x["topics"]) == 4:
            frm, to = addr(x["topics"][2]), addr(x["topics"][3])
            pairs = [tuple(words(x["data"])[:2])] if t0 == TRANSFER_SINGLE else batch_pairs(x["data"])
            for side, who, other in ((-1, frm, to), (1, to, frm)):
                if who in acct and frm != to:
                    r = rec(who, x)
                    for tid, v in pairs:
                        if a in POSITIONS:
                            r["shares"][(a, tid)] += side * v
                            r["counterparties"].add(other)
                        else:
                            r["other_tokens"][f"{a}:{tid}"] += side * v
        elif t0 in (V1_FILL, V2_FILL) and a in EXCHANGES and len(x["topics"]) == 4:
            f = decode_fill(x)
            if f["maker"] in acct:
                rec(f["maker"], x)["fills"].append(f)
        elif t0 in EVENTS and len(x["topics"]) >= 2 and addr(x["topics"][1]) in acct:
            e = decode_event(x)
            rec(e["account"], x)["events"].append(e)
        else:
            unknown_topics[f"{a}:{t0}"] += 1
    for r in recs.values():
        r["cash"] = {k: v for k, v in r["cash"].items() if v}
        r["shares"] = {k: v for k, v in r["shares"].items() if v}
        r["kinds"] = classify(r)
    return recs, dict(unknown_topics)


def classify(r):
    kinds = set()
    if r["fills"]:
        kinds.add("TRADE")
    kinds |= {e["kind"] for e in r["events"]}
    if not kinds:
        cash = sum(r["cash"].values())
        if r["shares"] and not r["cash"]:
            if all(v < 0 for v in r["shares"].values()) and r["counterparties"] <= DISPOSAL_COUNTERPARTIES:
                kinds.add("BURN_FOR_COLLATERAL")   # destroyed for zero collateral
            else:
                kinds.add("SHARE_TRANSFER")
        elif r["shares"] and all(v < 0 for v in r["shares"].values()) and cash > 0:
            kinds.add("BURN_FOR_COLLATERAL")   # redemption or merge through a contract that does not name the user
        elif r["shares"] and all(v > 0 for v in r["shares"].values()) and cash < 0:
            kinds.add("MINT_FOR_COLLATERAL")   # split through such a contract
        elif r["shares"]:
            kinds.add("SHARE_AND_CASH_UNEXPLAINED")
        elif r["cash"]:
            kinds.add("CASH_ONLY")
        else:
            kinds.add("NO_NET_CHANGE")
    return sorted(kinds)


# ---------------------------------------------------------------- accounting

class Position:
    """Average-cost book of one outcome token for one account (exact fractions of 1e-6 units)."""

    def __init__(self):
        self.qty, self.cost = 0, Fraction(0)
        self.realized, self.transfer_out_cost = Fraction(0), Fraction(0)
        self.bought = self.sold = self.split_in = self.merged_out = self.redeemed = 0
        self.transfer_in = self.transfer_out = 0
        self.buy_cash, self.sell_cash, self.fees = Fraction(0), Fraction(0), 0
        self.first_entry = None
        self.negative_inventory = False

    def trading_pnl(self, value):
        """realized + unrealized: shares transferred out leave at cost, so a transfer is never a trading loss."""
        return None if value is None else self.realized + value - self.cost

    def acquire(self, shares, cost, how, ts):
        self.qty += shares
        self.cost += cost
        if self.first_entry is None:
            self.first_entry = ts
        setattr(self, how, getattr(self, how) + shares)

    def dispose(self, shares, proceeds, how):
        if shares > self.qty:
            self.negative_inventory = True
        held = max(self.qty, 0)
        out_cost = self.cost * Fraction(min(shares, held), held) if held else Fraction(0)
        self.qty -= shares
        self.cost -= out_cost
        if how == "transfer_out":
            self.transfer_out_cost += out_cost
        else:
            self.realized += proceeds - out_cost
        setattr(self, how, getattr(self, how) + shares)


def legs(r, cond_of, payout):
    """Split one (account, tx) into per-token legs with their share of the collateral delta.
    Returns (legs, flags); legs: list of (token_key, share_delta, cash Fraction, how)."""
    cash = sum(r["cash"].values())
    kinds = set(r["kinds"])
    toks = dict(r["shares"])
    flags = []
    if not toks:
        return [], flags
    if "TRADE" in kinds:
        exp = defaultdict(int)
        for f in r["fills"]:
            if f["token"] is not None:
                exp[(f["position_contract"], f["token"])] += expected_cash(f)
        for k in toks:
            exp.setdefault(k, 0)
        # a token bought and sold in the same transaction (no net change) keeps its own fills' cash in its market
        flat = [k for k in exp if k not in toks and exp[k]]
        resid = cash - sum(exp[k] for k in toks) - sum(exp[k] for k in flat)
        if flat:
            flags.append("FILL_WITHOUT_NET_TRANSFER")
        weight = {k: abs(exp[k]) for k in toks}
        tot = sum(weight.values())
        out = []
        for k, ds in toks.items():
            share = Fraction(weight[k], tot) if tot else Fraction(abs(ds), sum(abs(v) for v in toks.values()))
            how = "bought" if ds > 0 else "sold"
            out.append((k, ds, exp[k] + resid * share, how))
        out += [(k, 0, Fraction(exp[k]), "flat_fill") for k in flat]
        if resid:
            flags.append("TRADE_CASH_RESIDUAL")
        if kinds - {"TRADE"}:
            flags.append("TRADE_WITH_OTHER_EVENT")
        return out, flags
    if kinds & {"SPLIT", "MERGE", "REDEEM", "CONVERT", "SHARE_AND_CASH_UNEXPLAINED", "BURN_FOR_COLLATERAL",
                "MINT_FOR_COLLATERAL"}:
        conds = {cond_of.get(k, (k,))[0] for k in toks}
        if all(ds < 0 for ds in toks.values()):
            # burns: a token with a known official payout receives exactly that value; only the remainder is spread,
            # by share count, over the tokens whose payout is unknown (a losing token earns nothing)
            known, unknown = {}, {}
            for k, ds in toks.items():
                c = cond_of.get(k)
                pv = payout.get(c[0]) if c else None
                if pv and c[1] is not None and c[1] < len(pv[0]):
                    known[k] = Fraction(payout_units(abs(ds), pv, c[1]))
                else:
                    unknown[k] = abs(ds)
            rest = Fraction(cash) - sum(known.values(), Fraction(0))
            alloc = dict(known)
            if unknown:
                n = sum(unknown.values())
                alloc.update({k: rest * Fraction(v, n) for k, v in unknown.items()})
                if len({cond_of.get(k, (k,))[0] for k in unknown}) > 1 or known:
                    flags.append("BURN_PARTLY_UNKNOWN_PAYOUT")
            elif rest:
                n = sum(abs(ds) for ds in toks.values())  # collateral differs from the payout value: keep it visible
                alloc = {k: v + rest * Fraction(abs(toks[k]), n) for k, v in known.items()}
                flags.append("BURN_CASH_NOT_PAYOUT")
            how = "redeemed" if kinds & {"REDEEM", "BURN_FOR_COLLATERAL"} else "merged_out"
            if "BURN_FOR_COLLATERAL" in kinds:
                flags.append("BURN_WITHOUT_USER_EVENT")
            return [(k, ds, alloc[k], how) for k, ds in toks.items()], flags
        if len(conds) > 1:
            flags.append("MULTI_CONDITION_PRO_RATA")
        n = sum(abs(ds) for ds in toks.values())
        out = []
        for k, ds in toks.items():
            how = "split_in" if ds > 0 else "merged_out"
            out.append((k, ds, Fraction(cash) * Fraction(abs(ds), n), how))
        if "CONVERT" in kinds:
            flags.append("CONVERSION")
        if kinds & {"SHARE_AND_CASH_UNEXPLAINED", "MINT_FOR_COLLATERAL"}:
            flags.append("MINT_WITHOUT_USER_EVENT" if "MINT_FOR_COLLATERAL" in kinds else "SHARE_AND_CASH_UNEXPLAINED")
        return out, flags
    return [(k, ds, Fraction(0), "transfer_in" if ds > 0 else "transfer_out") for k, ds in toks.items()], flags


def book(recs, cond_of, payout, marks):
    """Per (account, market) positions from the per-transaction records, in chronological order."""
    pos = defaultdict(lambda: defaultdict(Position))   # (account, market) -> token -> Position
    market_cash = defaultdict(Fraction)
    flags = defaultdict(lambda: defaultdict(int))
    fills = defaultdict(lambda: defaultdict(int))
    wallet = defaultdict(lambda: defaultdict(int))
    ledger = []
    # chain order: block, then position in the block (the first log index of the transaction), never the hash
    for r in sorted(recs.values(), key=lambda r: (r["block"], r["first_log"], r["account"])):
        a = r["account"]
        if not r["shares"]:
            if r["cash"]:
                wallet[a]["non_trading_cash_in" if sum(r["cash"].values()) > 0 else "non_trading_cash_out"] += \
                    sum(r["cash"].values())
                wallet[a]["non_trading_txs"] += 1
            if r["fills"]:
                wallet[a]["fills_without_position_change"] += len(r["fills"])
            continue
        lg, fl = legs(r, cond_of, payout)
        for k, ds, c, how in lg:
            market = cond_of.get(k, ("token:%s:%d" % k,))[0]
            p = pos[(a, market)][k]
            if ds == 0:                       # cash of a fill with no net share change (spread of a round trip)
                p.realized += c
            elif ds > 0:
                p.acquire(ds, -c if how in ("bought", "split_in") else Fraction(0), how, r["ts"])
                if how in ("bought", "split_in") and c > 0:
                    flags[(a, market)]["ACQUIRED_WITH_CASH_IN"] += 1
            else:
                p.dispose(-ds, c if how != "transfer_out" else Fraction(0), how)
            if how == "bought":
                p.buy_cash += -c
            elif how == "sold":
                p.sell_cash += c
            market_cash[(a, market)] += c
            ledger.append({"account": a, "market": market, "position_contract": k[0], "token_id": str(k[1]),
                           "tx": r["tx"], "block": r["block"], "ts": r["ts"], "kinds": "|".join(r["kinds"]),
                           "leg": how, "share_delta": ds, "cash_delta": fmt(c)})
        for f in r["fills"]:
            if f["token"] is None:
                continue
            k = (f["position_contract"], f["token"])
            market = cond_of.get(k, ("token:%s:%d" % k,))[0]
            fills[(a, market)]["fills"] += 1
            fills[(a, market)][f["side"].lower() + "_fills"] += 1
            fills[(a, market)]["fee_nominal"] += f["fee"]
            pos[(a, market)][k].fees += f["fee"] if f["version"] != "v1" else 0
        for x in fl:
            for k in r["shares"]:
                flags[(a, cond_of.get(k, ("token:%s:%d" % k,))[0])][x] += 1
    return pos, market_cash, flags, fills, wallet, ledger


def payout_units(shares, pv, index):
    """Collateral units Conditional Tokens pays for `shares` of outcome `index`: integer division, rounded down."""
    nums, den = pv
    return shares * nums[index] // den


def select_mark(points, at_ts):
    """Last price point at or before at_ts (never a later one: no future information). None when there is none."""
    best = None
    for pt in points:
        t, price = int(pt["t"]), pt["p"]
        if t <= at_ts and (best is None or t > best[0]):
            best = (t, price)
    return best


def value_inventory(positions, cond_of, payout, marks):
    """(value Fraction or None, source) for the remaining inventory of one market."""
    total, sources = Fraction(0), set()
    for k, p in positions.items():
        if p.qty == 0:
            continue
        c = cond_of.get(k)
        pv = payout.get(c[0]) if c else None
        if pv and c[1] is not None and c[1] < len(pv[0]):
            total += payout_units(p.qty, pv, c[1]) if p.qty > 0 else Fraction(p.qty * pv[0][c[1]], pv[1])
            sources.add("RESOLUTION_PAYOUT")
        elif k in marks and marks[k].get("price") is not None:
            total += p.qty * Fraction(str(marks[k]["price"]))
            sources.add(f"MARK:{marks[k]['source']}@{marks[k]['time_utc']}")
        else:
            return None, "UNKNOWN"
    return total, "|".join(sorted(sources)) or "NO_INVENTORY"
