"""Read-only access to the public sources, with provenance.

Every HTTP answer goes through one recorder: URL, time, status, size and SHA-256 of the body. A result can
therefore name what it was computed from, and a later reader can tell whether a source changed. A failure raises:
an unreachable or refusing source is never an empty result, and a list that was not read to its end says so.

Transport and chain decoding are those of `monitoring.phi_monitor` (bounded retries, per-host counters, public
keyless endpoints). Nothing here signs, sends a transaction or needs a credential.
"""
import hashlib
import json
import re
import time
import urllib.parse
from datetime import datetime, timezone

from monitoring.phi_monitor import chain, net

from .text import clean_text

DATA_API = "https://data-api.polymarket.com/v2"
GAMMA = "https://gamma-api.polymarket.com"
CLOB = "https://clob.polymarket.com"
HOSTS = {"data-api.polymarket.com", "gamma-api.polymarket.com", "clob.polymarket.com"}
# Profile text and images are personal data unrelated to money flows, and free text is an injection surface.
PROFILE_FIELDS = {"bio", "pseudonym", "profile_image", "profile_image_optimized", "icon", "image", "profileImage", "x_username"}
FREE_TEXT = {"title", "name", "slug", "event_slug", "event_title", "group_item_title", "outcome", "opposite_outcome", "question",
             "description", "user_name"}
ADDRESS = re.compile(r"0x[0-9a-fA-F]{40}")
HASH = re.compile(r"0x[0-9a-fA-F]{64}")
PAGE = 1000  # the data API refuses a larger limit
PRICE_WINDOW = 14 * 86400  # the price history refuses a longer span in one request
FIRST_CHUNK, SMALLEST_CHUNK = 10_000_000, 2_000
TRANSFER_SINGLE = "0xc3d58168c5ae7397731d063d5bbf3d657854427343f4c083240f7aacaa2d0f62"
TRANSFER_BATCH = "0x4a39dc06d4c0dbc64b70af90fd698a233a518aa5d07e595d983b8c0526c8f7fb"
# Conditional Tokens and, for Protocol V2 markets, the PositionManager: the two contracts that hold outcome tokens.
POSITION_CONTRACTS = ["0x4d97dcd97ec945f40cf65f87097ace5ea0476045", "0x006f54f7f9a22e0000cc2ab60031000000ae9fef"]
TOO_WIDE = re.compile(r"limit|range|too many|exceed|more than|response size|timed? ?out", re.I)

SourceError = net.SourceError


def utc(seconds):
    return datetime.fromtimestamp(seconds, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def clean_row(row):
    """One API row without profile fields, its free text stripped of control characters and bounded."""
    return {k: (clean_text(v, 300) if k in FREE_TEXT and isinstance(v, str) else v) for k, v in row.items() if k not in PROFILE_FIELDS}


def _address(value):
    if not isinstance(value, str) or not ADDRESS.fullmatch(value):
        raise ValueError(f"not an address: {clean_text(value, 60)}")
    return value.lower()


class Sources:
    def __init__(self, fetch=net.fetch, rpc=net.rpc, clock=time.time):
        self.fetch, self.rpc, self.clock = fetch, rpc, clock
        self.requests = []  # provenance of every HTTP answer, in order

    # HTTP

    def get(self, url):
        if urllib.parse.urlsplit(url).hostname not in HOSTS:
            raise SourceError(f"host not on the allowlist: {url}")
        status, body = self.fetch(url)
        self.requests.append({"url": url, "status": status, "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest(),
                              "fetched_utc": utc(self.clock())})
        if status != 200:
            raise SourceError(f"HTTP {status} for {url}: {body[:160]!r}", status)
        try:
            return json.loads(body)
        except ValueError:
            raise SourceError(f"answer of {url} is not JSON", status) from None

    def pages(self, path, params, max_rows):
        """All rows of a cursor-paginated list. Returns (rows, complete, pages): complete is False when max_rows stopped it."""
        rows, cursor, count = [], None, 0
        while True:
            query = {k: v for k, v in {**params, "limit": PAGE, "cursor": cursor}.items() if v is not None}
            body = self.get(f"{DATA_API}/{path}?{urllib.parse.urlencode(query)}")
            if not isinstance(body, dict) or not isinstance(body.get("data"), list):
                raise SourceError(f"unexpected shape from {path}")
            count += 1
            rows += [clean_row(r) for r in body["data"]]
            page = body.get("pagination") or {}
            if not page.get("has_more"):
                return rows, True, count
            cursor = page.get("next_cursor")
            if not cursor:
                raise SourceError(f"{path} announces more rows without a cursor")
            if len(rows) >= max_rows:
                return rows, False, count

    # Polymarket data API

    def activity(self, wallet, start=None, end=None, kind=None, max_rows=200_000):
        """Every activity row of a trading wallet, oldest first: trades, splits, merges, redemptions, conversions, rewards.

        `usdc_size` is the cash that moved, fees included. `complete` is False when max_rows cut the read.
        """
        rows, complete, pages = self.pages("activity", {"user": _address(wallet), "start": start, "end": end, "type": kind,
                                                        "sort_direction": "ASC"}, max_rows)
        return {"rows": rows, "complete": complete, "pages": pages}

    def trades(self, wallet=None, condition=None, start=None, end=None, max_rows=200_000):
        """Fills of a wallet or of a market, maker fills included.

        The endpoint returns taker fills only unless told otherwise; a wallet that rests orders would lose most of its
        history. This reader always asks for both sides.
        """
        if (wallet is None) == (condition is None):
            raise ValueError("give a wallet or a condition, not both")
        if condition is not None and not HASH.fullmatch(condition):
            raise ValueError("condition must be a 32-byte hex id")
        params = {"user": _address(wallet) if wallet else None, "condition": condition, "taker_only": "false", "start": start, "end": end}
        rows, complete, pages = self.pages("trades", params, max_rows)
        return {"rows": rows, "complete": complete, "pages": pages}

    def positions(self, wallet, max_rows=50_000):
        rows, complete, pages = self.pages("positions", {"user": _address(wallet)}, max_rows)
        return {"rows": rows, "complete": complete, "pages": pages}

    def holders(self, condition):
        if not HASH.fullmatch(condition):
            raise ValueError("condition must be a 32-byte hex id")
        body = self.get(f"{DATA_API}/holders?{urllib.parse.urlencode({'condition': condition, 'limit': 100})}")
        return [{"token_id": side.get("token_id"), "holders": [clean_row(h) for h in side.get("holders", [])]} for side in body.get("data", [])]

    def profile(self, wallet):
        """Creation time and public name of a trading wallet, or None when it has no public profile. No bio, no image."""
        try:
            body = self.get(f"{GAMMA}/public-profile?address={_address(wallet)}")
        except SourceError as err:
            if err.status == 404:
                return None
            raise
        return {"proxy_wallet": (body.get("proxyWallet") or "").lower(), "created_at": body.get("createdAt"),
                "name": clean_text(body.get("name") or "", 80), "verified": bool(body.get("verifiedBadge") or body.get("verified"))}

    # Markets

    def market(self, condition):
        """Catalogue record of one market, open or closed, or None when the catalogue does not know the id."""
        if not HASH.fullmatch(condition):
            raise ValueError("condition must be a 32-byte hex id")
        for closed in ("false", "true"):  # the catalogue lists closed markets only when asked
            found = self.get(f"{GAMMA}/markets?{urllib.parse.urlencode({'condition_ids': condition, 'closed': closed})}")
            if found:
                return clean_row(found[0])
        return None

    def markets(self, conditions):
        """Catalogue records of several markets, {condition id: record}. Ids the catalogue does not know are absent."""
        wanted = sorted({c.lower() for c in conditions})
        if any(not HASH.fullmatch(c) for c in wanted):
            raise ValueError("every condition must be a 32-byte hex id")
        found = {}
        for start in range(0, len(wanted), 40):  # larger batches are sometimes refused
            ids = "&".join(f"condition_ids={c}" for c in wanted[start:start + 40])
            for closed in ("false", "true"):
                for record in self.get(f"{GAMMA}/markets?{ids}&closed={closed}&limit=100"):
                    found[str(record.get("conditionId", "")).lower()] = clean_row(record)
        return found

    def markets_by_tokens(self, token_ids):
        """Where outcome tokens belong: {token id: {"condition_id", "outcome_index", "outcome", "title", "neg_risk_event"}}."""
        wanted = sorted({str(t) for t in token_ids})
        if any(not t.isdigit() for t in wanted):
            raise ValueError("every token id must be a decimal string")
        found = {}
        for start in range(0, len(wanted), 40):
            ids = "&".join(f"clob_token_ids={t}" for t in wanted[start:start + 40])
            for closed in ("false", "true"):
                for record in self.get(f"{GAMMA}/markets?{ids}&closed={closed}&limit=100"):
                    try:
                        tokens, names = json.loads(record["clobTokenIds"]), json.loads(record["outcomes"])
                    except (KeyError, TypeError, ValueError):
                        continue
                    resolved = bool(record.get("closed")) and record.get("umaResolutionStatus") == "resolved"
                    for index, token in enumerate(tokens):
                        found[str(token)] = {"condition_id": str(record.get("conditionId", "")).lower(), "outcome_index": index,
                                             "outcome": clean_text(names[index], 80) if index < len(names) else None,
                                             "title": clean_text(record.get("question") or "", 300),
                                             "neg_risk_event": str(record.get("negRiskMarketID") or "").lower() or None,
                                             "resolved": resolved, "outcome_prices": record.get("outcomePrices")}
        return {t: found[t] for t in wanted if t in found}

    def price_history(self, token_id, start=None, end=None, fidelity=60):
        """Price points [{t, p}] of one outcome token, oldest first. `fidelity` is the spacing in minutes.

        Give `start` and `end`: the source refuses a span of more than about two weeks, so a longer one is read window
        by window. Without them the source chooses the span, and for an old market it returns nothing at a fine spacing.
        """
        if not str(token_id).isdigit():
            raise ValueError("token_id must be a decimal string")
        if start is None or end is None:
            windows = [{"startTs": start, "endTs": end} if start is not None or end is not None else {"interval": "max"}]
        else:
            windows = [{"startTs": a, "endTs": min(end, a + PRICE_WINDOW)} for a in range(start, max(end, start + 1), PRICE_WINDOW)]
        points = {}
        for window in windows:
            query = {k: v for k, v in {"market": token_id, "fidelity": fidelity, **window}.items() if v is not None}
            history = self.get(f"{CLOB}/prices-history?{urllib.parse.urlencode(query)}").get("history")
            if not isinstance(history, list):
                raise SourceError("unexpected shape from prices-history")
            points.update({p["t"]: p for p in history})
        return [points[t] for t in sorted(points)]

    # Polygon

    def logs(self, query, from_block, to_block):
        """Logs matching `query` over a block range, split into ranges the public node accepts. Returns (logs, calls).

        A range the node refuses for its width or its number of results is narrowed and asked again, never skipped;
        an unreachable node and a range that still fails at the smallest width raise.
        """
        out, start, chunk, calls = [], from_block, FIRST_CHUNK, 0
        while start <= to_block:
            stop = min(to_block, start + chunk - 1)
            try:
                found = self.rpc("eth_getLogs", [{**query, "fromBlock": hex(start), "toBlock": hex(stop)}], urls=chain.WIDE_RPC)
            except SourceError as err:
                if chunk <= SMALLEST_CHUNK or not TOO_WIDE.search(str(err)):
                    raise  # an unreachable node is a failure, not a reason to retry eight narrower ranges
                chunk //= 4
                continue
            calls += 1
            out += [log for log in found if not log.get("removed")]
            start = stop + 1
        return out, calls

    def _dated(self, rows, from_block, to_block, calls):
        for row in rows:
            if row["ts"] is None:
                row["ts"] = self.block_time(row["block"])
        return {"rows": sorted(rows, key=lambda r: (r["block"], r["log_index"], r.get("position", 0))), "from_block": from_block,
                "to_block": to_block, "calls": calls}

    @staticmethod
    def _where(log):
        return {"tx": log["transactionHash"], "log_index": int(log["logIndex"], 16), "block": int(log["blockNumber"], 16),
                "ts": int(log["blockTimestamp"], 16) if log.get("blockTimestamp") else None}

    def transfers(self, address, direction, from_block=0, to_block=None, tokens=None):
        """Collateral transfers received (`in`) or sent (`out`) by an address, from logs, in chain order.

        Only the official collateral contracts count (USDC, USDC.e, pUSD), so look-alike tokens never enter.
        Amounts are exact integers of 6 decimals in `amount_raw`.
        """
        if direction not in ("in", "out"):
            raise ValueError("direction must be 'in' or 'out'")
        topic = "0x" + "0" * 24 + _address(address)[2:]
        topics = [chain.TRANSFER, None, topic] if direction == "in" else [chain.TRANSFER, topic]
        to_block = self.head() if to_block is None else to_block
        logs, calls = self.logs({"address": tokens or chain.STABLES, "topics": topics}, from_block, to_block)
        rows = [{**self._where(log), "from": "0x" + log["topics"][1][-40:], "to": "0x" + log["topics"][2][-40:],
                 "token": log["address"].lower(), "amount_raw": int(log["data"], 16)} for log in logs if int(log["data"], 16)]
        return self._dated(rows, from_block, to_block, calls)

    def position_transfers(self, address, direction, from_block=0, to_block=None):
        """Outcome-token transfers (ERC-1155) received or sent by an address: what it really holds, fees already taken.

        One row per token id moved; a batch transfer gives several rows with the same log index and a `position`.
        """
        if direction not in ("in", "out"):
            raise ValueError("direction must be 'in' or 'out'")
        topic = "0x" + "0" * 24 + _address(address)[2:]
        topics = [[TRANSFER_SINGLE, TRANSFER_BATCH], None, None, topic] if direction == "in" else [[TRANSFER_SINGLE, TRANSFER_BATCH], None, topic]
        to_block = self.head() if to_block is None else to_block
        logs, calls = self.logs({"address": POSITION_CONTRACTS, "topics": topics}, from_block, to_block)
        rows = []
        for log in logs:
            words = [int(log["data"][2:][i:i + 64], 16) for i in range(0, len(log["data"]) - 2, 64)]
            if log["topics"][0] == TRANSFER_SINGLE:
                pairs = [(words[0], words[1])]
            else:  # two dynamic arrays: offsets, then length and items of each
                ids, values = words[0] // 32, words[1] // 32
                pairs = list(zip(words[ids + 1:ids + 1 + words[ids]], words[values + 1:values + 1 + words[values]]))
                if words[ids] != words[values]:
                    raise SourceError(f"malformed batch transfer in {log['transactionHash']}")
            for position, (token_id, value) in enumerate(pairs):
                if value:
                    rows.append({**self._where(log), "position": position, "from": "0x" + log["topics"][2][-40:],
                                 "to": "0x" + log["topics"][3][-40:], "contract": log["address"].lower(),
                                 "token_id": str(token_id), "amount_raw": value})
        return self._dated(rows, from_block, to_block, calls)

    def collateral_balance(self, address, block="latest"):
        """Balance of each collateral token held by an address, {token: integer of 1e-6}."""
        data = "0x70a08231" + "0" * 24 + _address(address)[2:]  # balanceOf(address)
        tag = block if block == "latest" else hex(block)
        return {token: int(self.rpc("eth_call", [{"to": token, "data": data}, tag], urls=chain.WIDE_RPC), 16) for token in chain.STABLES}

    def head(self):
        return int(self.rpc("eth_blockNumber", []), 16)

    def block_time(self, number):
        return int(self.rpc("eth_getBlockByNumber", [hex(number), False])["timestamp"], 16)

    def receipt(self, tx, endpoint):
        """Receipt of one transaction as one named endpoint reports it, or None when that endpoint does not know it."""
        if not HASH.fullmatch(tx):
            raise ValueError("not a transaction hash")
        return self.rpc("eth_getTransactionReceipt", [tx], urls=[endpoint])
