"""Positions and P&L of a trading wallet, rebuilt from its activity rows.

Cash is what actually moved (`usdc_size`, fees included), so the cash result of a market does not depend on any
fee model. Holdings are signed: a complete set from a SPLIT is kept as a set, worth exactly one unit of collateral
whatever the outcome, and selling one side of it leaves a negative count on that side. The value of what remains is
then  sets + sum(shares x payout)  with no need to know every token of the market.

Realised and unrealised P&L use signed average cost and always satisfy, per market:

    realised + unrealised == cash + value of the remaining inventory

Amounts are exact: integers of 1e-6 inside, fractions for averages, six-decimal strings outside. What the rows
cannot establish is flagged, never guessed: a neg-risk conversion, an unknown row type, a valuation that is missing.
"""
from collections import defaultdict
from fractions import Fraction

UNIT = 1_000_000
INCOME = {"REWARD", "MAKER_REBATE", "TAKER_REBATE", "REFERRAL_REWARD", "YIELD"}  # cash received that is not a trading result
# Last fill seen on the first-generation exchanges: block 86126998, 2026-04-28T11:00:40Z (contract_semantics.json of the
# data-completion investigation). Until then a fee could be taken in shares, and the API rows show the amounts before it.
FIRST_GENERATION_UNTIL = 1777374040
GROSS = "API_AMOUNTS_MAY_BE_GROSS_OF_FEES"
CHAIN_ONLY = "CHAIN_TRANSACTION_WITHOUT_API_ROW"


def units(value):
    """A six-decimal API number as an exact integer of 1e-6."""
    return round(float(value) * UNIT)


def amount(value):
    """Exact units or fraction as a six-decimal string (half away from zero)."""
    scaled = Fraction(value) * 1  # value is already in 1e-6 units
    whole = int(abs(scaled) + Fraction(1, 2))
    sign = "-" if scaled < 0 and whole else ""
    return f"{sign}{whole // UNIT}.{whole % UNIT:06d}"


class Market:
    def __init__(self, condition):
        self.condition, self.title, self.slug = condition, "", ""
        self.cash = 0                              # collateral received minus paid, trading only
        self.sets = 0                              # complete sets held (split minus merged)
        self.shares = defaultdict(int)             # token -> signed shares from trades
        self.cost = defaultdict(Fraction)          # token -> signed cost basis of those shares
        self.outcome = {}                          # token -> outcome index, name
        self.realised = Fraction(0)
        self.counts = defaultdict(int)
        self.first_ts = self.last_ts = self.first_trade = None
        self.flags = set()

    def trade(self, token, quantity, flow):
        """quantity > 0 buys, < 0 sells; flow is the cash received (negative when paid)."""
        held, basis = self.shares[token], self.cost[token]
        if held == 0 or (held > 0) == (quantity > 0):
            self.shares[token], self.cost[token] = held + quantity, basis - flow
            return
        closing = min(abs(quantity), abs(held))
        share_of_trade = Fraction(closing, abs(quantity))
        released = basis * Fraction(closing, abs(held))
        self.realised += flow * share_of_trade - released
        self.shares[token], self.cost[token] = held + quantity, basis - released - flow * (1 - share_of_trade)

    def merge(self, size, received):
        """Sets go first (cost one, value one: no result). The rest is one share of each side handed back for one unit."""
        self.realised += received - size  # zero unless the row's cash and size differ
        from_sets = max(0, min(size, self.sets))
        self.sets -= from_sets
        rest = size - from_sets
        if not rest:
            return
        sides = [t for t, held in self.shares.items() if held >= rest]
        if len(sides) < 2:
            self.sets -= rest  # the other side never appeared in the rows: keep the count, say so
            self.flags.add("MERGE_OF_SHARES_NOT_SEEN_IN_ROWS")
            return
        self.realised += rest
        for token in sides:
            released = self.cost[token] * Fraction(rest, self.shares[token])
            self.realised -= released
            self.shares[token] -= rest
            self.cost[token] -= released

    def redeem_exactly(self, received, burned):
        """Settle only the shares the chain shows burned, when they are fewer than those held: what is left stays held.

        Returns False, and does nothing, when the burn is not a plain part of known holdings (a complete set, a token the
        rows never showed, more shares than held): `redeem` then settles everything, which is right for the result.
        """
        if self.sets or not burned or any(t not in self.outcome or not 0 < q <= self.shares[t] for t, q in burned.items()) \
                or all(q == self.shares[t] for t, q in burned.items()):
            return False
        tokens = sorted(burned)
        for token, cash in zip(tokens, _allocate(received, [burned[t] for t in tokens])):
            self.trade(token, -burned[token], cash)
        return True

    def redeem(self, received):
        """A redemption burns the whole balance of the market: everything held is settled against the cash received."""
        self.realised += received - self.sets - sum(self.cost.values(), Fraction(0))
        self.sets = 0
        self.shares.clear()
        self.cost.clear()

    def value(self, prices):
        """Value of the remaining inventory given {outcome index: price or payout}, or None when one is missing."""
        total = Fraction(self.sets)
        for token, held in self.shares.items():
            if held == 0:
                continue
            price = (prices or {}).get(self.outcome.get(token, {}).get("index"))
            if price is None:
                return None
            total += held * Fraction(price)
        return total

    def summary(self, prices, source, valued=True):
        value = self.value(prices) if valued else None
        holdings = {token: held for token, held in self.shares.items() if held}
        status = ("FLAT" if not holdings and not self.sets else "INVENTORY_VALUED" if value is not None else "INVENTORY_NOT_VALUED")
        row = {"condition_id": self.condition, "title": self.title, "slug": self.slug, "first_utc_ts": self.first_ts, "last_utc_ts": self.last_ts,
               "rows": dict(sorted(self.counts.items())), "cash": amount(self.cash), "complete_sets": amount(self.sets),
               "shares": [{"token_id": t, "outcome": self.outcome.get(t, {}).get("name"), "outcome_index": self.outcome.get(t, {}).get("index"),
                           "signed_shares": amount(h), "held_with_sets": amount(h + self.sets)} for t, h in sorted(holdings.items())],
               "status": status, "valuation": source if value is not None and status != "FLAT" else None,
               "inventory_value": amount(value) if value is not None else None,
               "realised": amount(self.realised), "flags": sorted(self.flags)}
        if value is not None:
            unrealised = value - self.sets - sum(self.cost.values(), Fraction(0))
            row.update(unrealised=amount(unrealised), net=amount(self.cash + value))
            if self.realised + unrealised != self.cash + value:  # the identity of the module docstring
                raise AssertionError(f"ledger identity broken for {self.condition}")
        else:
            row.update(unrealised=None, net=None)
        return row


TRADING = ("TRADE", "SPLIT", "MERGE", "REDEEM", "CONVERSION")
UNLISTED = "unlisted-outcome:"   # prefix of the market id given to an outcome token the catalogue does not know


def chain_deltas(collateral_in, collateral_out, tokens_in, tokens_out):
    """Per transaction, what a wallet really received (+) and sent (-): collateral and outcome tokens, in 1e-6 units.

    Inputs are the rows of `Sources.transfers` and `Sources.position_transfers`. This is the ground truth of an
    account: fees are already inside, whichever way an exchange version charged them. `ts` is the time of the
    transaction when the rows carry one: a transaction the API does not list can then be booked in its place.
    """
    deltas = {}
    for sign, rows, kind in ((1, collateral_in, "cash"), (-1, collateral_out, "cash"), (1, tokens_in, "tokens"), (-1, tokens_out, "tokens")):
        for row in rows:
            entry = deltas.setdefault(row["tx"].lower(), {"cash": 0, "tokens": defaultdict(int), "ts": None})
            if row.get("ts") is not None:
                entry["ts"] = row["ts"] if entry["ts"] is None else min(entry["ts"], row["ts"])
            if kind == "cash":
                entry["cash"] += sign * row["amount_raw"]
            else:
                entry["tokens"][row["token_id"]] += sign * row["amount_raw"]
    return deltas


def _allocate(total, weights):
    """Split an integer total across rows in proportion to their weights, exactly (largest remainders)."""
    if not any(weights):
        weights = [1] * len(weights)
    scale = sum(weights)
    shares = [total * w // scale for w in weights]
    for index in sorted(range(len(weights)), key=lambda i: -(total * weights[i] % scale))[:total - sum(shares)]:
        shares[index] += 1
    return shares


def with_chain_amounts(rows, deltas, token_markets=None):
    """Activity rows with their cash and share amounts replaced by what the chain shows for the same transaction.

    The API classifies a transaction (trade, split, merge, redemption) and names its market; the transfers say how
    much moved. Rows the chain cannot confirm keep their API amounts and are counted, never silently trusted.
    A neg-risk conversion is one API row for shares that moved in many markets: with `token_markets` (where each
    token belongs, from `Sources.markets_by_tokens`) each movement is placed in its own market.
    Returns (rows, report).
    """
    report = {"rows_checked": 0, "cash_rows_corrected": 0, "share_rows_corrected": 0, "cash_correction_abs": 0,
              "rows_without_chain_record": 0, "transactions_with_mixed_directions": 0, "transactions_cash_direction_differs": 0,
              "conversions_placed": 0, "conversion_tokens_not_in_catalogue": 0}
    by_tx = defaultdict(list)
    out = [dict(r) for r in rows]
    for row in out:
        if row.get("type") in TRADING and row.get("transaction_hash"):
            by_tx[row["transaction_hash"].lower()].append(row)
    for tx, group in by_tx.items():
        report["rows_checked"] += len(group)
        delta = deltas.get(tx)
        if delta is None:
            report["rows_without_chain_record"] += len(group)
            continue
        conversion = next((r for r in group if r["type"] == "CONVERSION"), None)
        moved = {t: d for t, d in delta["tokens"].items() if d} if conversion is not None else {}
        if moved and token_markets is not None:
            conversion["placed"] = True
            report["conversions_placed"] += 1
            for token, quantity in moved.items():
                # A neg-risk event keeps unnamed spare outcomes the catalogue does not list: each gets a market of its own here.
                home = token_markets.get(token) or {"condition_id": UNLISTED + token, "outcome_index": 0, "outcome": None, "unlisted": True,
                                                    "title": f"Outcome not listed in the catalogue (neg-risk event {conversion['condition_id']})"}
                report["conversion_tokens_not_in_catalogue"] += bool(home.get("unlisted"))
                out.append({"type": "CONVERT_IN" if quantity > 0 else "CONVERT_OUT", "condition_id": home["condition_id"], "token_id": token,
                            "size": abs(quantity) / UNIT, "usdc_size": 0, "outcome_index": home["outcome_index"], "outcome": home.get("outcome"),
                            "title": home.get("title") or "", "timestamp": conversion["timestamp"], "transaction_hash": tx,
                            "unlisted": bool(home.get("unlisted"))})
        if len(group) == 1 and group[0]["type"] == "REDEEM":  # the adapter of neg-risk markets can redeem less than the balance
            group[0]["burned_raw"] = {t: -q for t, q in delta["tokens"].items() if q < 0}
        paying = [r for r in group if (r["type"] == "TRADE" and r.get("side") == "BUY") or r["type"] == "SPLIT"]
        receiving = [r for r in group if r not in paying]
        if paying and receiving:
            report["transactions_with_mixed_directions"] += 1
        elif (paying and delta["cash"] > 0) or (receiving and delta["cash"] < 0):
            report["transactions_cash_direction_differs"] += 1
        else:
            api = [units(r.get("usdc_size") or 0) for r in group]
            for row, was, now in zip(group, api, _allocate(abs(delta["cash"]), api)):
                if now != was:
                    report["cash_rows_corrected"] += 1
                    report["cash_correction_abs"] += abs(now - was)
                    row["usdc_size"] = now / UNIT
                    if row["type"] in ("SPLIT", "MERGE"):
                        row["size"] = now / UNIT
        by_token = defaultdict(list)
        for row in group:
            if row["type"] == "TRADE" and row.get("token_id"):
                by_token[str(row["token_id"])].append(row)
        for token, trades in by_token.items():
            moved = delta["tokens"].get(token, 0)
            signed = sum(units(r.get("size") or 0) * (1 if r.get("side") == "BUY" else -1) for r in trades)
            if moved == 0 or signed == 0 or (moved > 0) != (signed > 0) or len({r.get("side") for r in trades}) > 1:
                continue  # nothing to compare, or a transaction too mixed to apportion: API sizes stay
            api = [units(r.get("size") or 0) for r in trades]
            for row, was, now in zip(trades, api, _allocate(abs(moved), api)):
                if now != was:
                    report["share_rows_corrected"] += 1
                    row["size"] = now / UNIT
    orphans = {tx: d for tx, d in deltas.items() if tx not in by_tx}
    report["chain_transactions_without_api_row"] = len(orphans)
    report["of_which_moving_outcome_tokens"] = report["chain_only_transactions_placed"] = report["chain_only_transactions_not_placed"] = 0
    for tx, delta in orphans.items():
        moved = {t: q for t, q in delta["tokens"].items() if q}
        if not moved:
            continue  # collateral alone is a deposit or a withdrawal, not trading
        report["of_which_moving_outcome_tokens"] += 1
        homes = {t: (token_markets or {}).get(t) for t in moved}
        if delta.get("ts") is None or None in homes.values() or len({h["condition_id"] for h in homes.values()}) != 1:
            report["chain_only_transactions_not_placed"] += 1  # no date, an unknown token or several markets: counted, never guessed
            continue
        # The API misses this transaction of the wallet. What moved is booked as it moved: the net result of the market
        # needs the cash and the shares, not the name of the operation.
        report["chain_only_transactions_placed"] += 1
        tokens = sorted(moved)
        for token, cash in zip(tokens, _allocate(abs(delta["cash"]), [abs(moved[t]) for t in tokens])):
            out.append({"type": "CHAIN_ONLY", "condition_id": homes[token]["condition_id"], "token_id": token, "quantity_raw": moved[token],
                        "cash_raw": cash if delta["cash"] > 0 else -cash, "outcome_index": homes[token]["outcome_index"],
                        "outcome": homes[token].get("outcome"), "title": homes[token].get("title") or "", "timestamp": delta["ts"],
                        "transaction_hash": tx})
    report["cash_correction_abs"] = amount(report["cash_correction_abs"])
    return out, report


ORDER = {"CONVERT_OUT": 0, "CONVERT_IN": 2}  # inside one conversion: shares leave, cash settles, shares arrive


def build(rows, prices=None, as_of=None, chain=None, token_markets=None, unreliable=None):
    """Ledger of one wallet.

    rows:   activity rows (type, side, condition_id, token_id, size, usdc_size, outcome, outcome_index, timestamp).
    prices: {condition_id: {"prices": {outcome index: payout or mark}, "source": "RESOLUTION_PAYOUT" | "MARK ..."}}.
    as_of:  keep only rows at or before this UTC timestamp, to rebuild the position as it was.
    chain:  the result of `chain_deltas`; amounts then come from the chain and the answer carries a `chain` report.
    token_markets: with `chain`, where each outcome token belongs, to place the shares moved by neg-risk conversions.
    unreliable: {condition_id: reason} for markets whose inventory the rows cannot establish; they are not valued.
    """
    chain_report = None
    if chain is not None:
        rows, chain_report = with_chain_amounts([r for r in rows if as_of is None or r["timestamp"] <= as_of], chain, token_markets)
    markets, income, unknown, counted = {}, defaultdict(int), defaultdict(int), 0
    rows = sorted((r for r in rows if as_of is None or r["timestamp"] <= as_of), key=lambda r: (r["timestamp"], ORDER.get(r.get("type"), 1)))
    pool, arriving = defaultdict(Fraction), defaultdict(int)   # per conversion: cost basis in transit, shares due to arrive
    for row in rows:
        if row.get("type") == "CONVERT_IN":
            arriving[row["transaction_hash"]] += units(row["size"])
    for row in rows:
        kind = row.get("type")
        if kind in ("CONVERT_OUT", "CONVERT_IN"):
            m = markets.setdefault(row["condition_id"], Market(row["condition_id"]))
            m.title = m.title or row.get("title") or ""
            m.first_ts = row["timestamp"] if m.first_ts is None else m.first_ts
            m.last_ts, token, quantity, tx = row["timestamp"], str(row["token_id"]), units(row["size"]), row["transaction_hash"]
            m.outcome.setdefault(token, {"index": row.get("outcome_index"), "name": row.get("outcome")})
            m.counts[kind] += 1
            m.flags.add("CONVERSION")
            if row.get("unlisted"):
                m.flags.add("OUTCOME_NOT_IN_CATALOGUE")
            if kind == "CONVERT_OUT":
                held = m.shares[token]
                moved = m.cost[token] * Fraction(min(quantity, held), held) if held > 0 else Fraction(0)
                if held < quantity:
                    m.flags.add("CONVERTED_MORE_THAN_HELD")
                m.shares[token], m.cost[token] = held - quantity, m.cost[token] - moved
                m.realised -= moved
                pool[tx] += moved
            else:
                basis = max(pool[tx], Fraction(0)) * Fraction(quantity, arriving[tx])
                m.shares[token] += quantity
                m.cost[token] += basis
                m.realised += basis
            continue
        if kind == "CHAIN_ONLY":
            m = markets.setdefault(row["condition_id"], Market(row["condition_id"]))
            m.title = m.title or row.get("title") or ""
            m.first_ts = row["timestamp"] if m.first_ts is None else m.first_ts
            m.last_ts, token = row["timestamp"], str(row["token_id"])
            m.outcome.setdefault(token, {"index": row.get("outcome_index"), "name": row.get("outcome")})
            m.counts[kind] += 1
            m.flags.add(CHAIN_ONLY)
            m.cash += row["cash_raw"]
            m.trade(token, row["quantity_raw"], row["cash_raw"])
            continue
        if kind in INCOME:
            income[kind] += units(row.get("usdc_size") or 0)
            continue
        condition = row.get("condition_id") or ""
        if kind not in TRADING or not condition:
            unknown[str(kind)] += 1
            continue
        counted += 1
        m = markets.setdefault(condition, Market(condition))
        m.title, m.slug = m.title or row.get("title") or "", m.slug or row.get("slug") or ""
        m.first_ts = row["timestamp"] if m.first_ts is None else m.first_ts
        m.last_ts = row["timestamp"]
        cash, size, token = units(row.get("usdc_size") or 0), units(row.get("size") or 0), str(row.get("token_id") or "")
        if kind == "TRADE":
            side = row.get("side")
            if side not in ("BUY", "SELL") or not token:
                m.flags.add("TRADE_ROW_WITHOUT_SIDE_OR_TOKEN")
                continue
            m.outcome[token] = {"index": row.get("outcome_index"), "name": row.get("outcome")}
            m.counts[side] += 1
            m.first_trade = row["timestamp"] if m.first_trade is None else m.first_trade
            m.cash += -cash if side == "BUY" else cash
            m.trade(token, size if side == "BUY" else -size, -cash if side == "BUY" else cash)
        elif kind == "SPLIT":
            m.counts[kind] += 1
            m.cash -= cash
            m.sets += size
            m.realised += size - cash  # zero unless the row's cash and size differ
        elif kind == "MERGE":
            m.counts[kind] += 1
            m.cash += cash
            m.merge(size, cash)
        elif kind == "REDEEM":
            m.counts[kind] += 1
            m.cash += cash
            if not m.redeem_exactly(cash, row.get("burned_raw")):
                m.redeem(cash)
        else:  # CONVERSION: neg-risk shares of several markets exchanged at once; one row cannot place them
            m.counts[kind] += 1
            m.cash += cash
            m.realised += cash
            pool[row.get("transaction_hash")] -= cash
            m.flags.add("CONVERSION" if row.get("placed") else "CONVERSION_INVENTORY_NOT_RECONSTRUCTED")
    out, totals = [], {"cash": 0, "realised": Fraction(0), "unrealised": Fraction(0), "inventory_value": Fraction(0), "not_valued": 0}
    for condition, m in sorted(markets.items(), key=lambda kv: (kv[1].first_ts, kv[0])):
        if chain is None and m.first_trade is not None and m.first_trade <= FIRST_GENERATION_UNTIL:
            m.flags.add(GROSS)  # the figures of this market may differ from the chain by a fee: said per market, not only per wallet
        quote = (prices or {}).get(condition) or {}
        doubt = (unreliable or {}).get(condition) if m.sets or any(m.shares.values()) else None
        if doubt:
            m.flags.add(doubt)  # an inventory the rows cannot establish is not valued
        row = m.summary(quote.get("prices"), quote.get("source"), valued=not doubt)
        out.append(row)
        totals["cash"] += m.cash
        totals["realised"] += m.realised
        value = None if doubt else m.value(quote.get("prices"))
        if value is None:
            totals["not_valued"] += 1
        else:
            totals["inventory_value"] += value
            totals["unrealised"] += value - m.sets - sum(m.cost.values(), Fraction(0))
    complete = totals["not_valued"] == 0
    return {"markets": out, "rows_counted": counted, "unknown_row_types": dict(unknown), "amounts": "CHAIN" if chain is not None else "API",
            "chain": chain_report,
            "totals": {"markets": len(out), "trading_cash": amount(totals["cash"]), "realised": amount(totals["realised"]),
                       "unrealised_on_valued_inventory": amount(totals["unrealised"]),
                       "inventory_value_known": amount(totals["inventory_value"]), "markets_not_valued": totals["not_valued"],
                       "net_trading_result": amount(totals["cash"] + totals["inventory_value"]) if complete else None,
                       "net_is_complete": complete,
                       "other_income": {k: amount(v) for k, v in sorted(income.items())}}}
