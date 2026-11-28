"""A small deterministic chain and API that the real readers can be pointed at, so the whole stack runs offline.

One scenario, written as data below, is the single truth. The HTTP answers (data API, catalogue, price history) and
the JSON-RPC answers (blocks, logs, balances, owners, receipts) are both derived from it, as the live sources are from
one chain. Switches on a World inject the failures the readers must survive or report. Figures the tests assert are
worked out by hand in the tests, never read back from here.

Block b has the time GENESIS + 2 b. The head is block 90 000 000. ledger.FIRST_GENERATION_UNTIL (1777374040) falls
at block 88 687 020: the trades of transactions 7 and 8 are before it, every later row after it.
"""
import io
import json
import urllib.error
import urllib.parse
import urllib.request
from unittest import mock

from monitoring.phi_monitor import chain, net
from phi_forensics import sources

GENESIS, HEAD = 1_600_000_000, 90_000_000
NOW = GENESIS + 2 * HEAD + 60
U = 1_000_000


def ts(block):
    return GENESIS + 2 * block


def tx(n):
    return "0x" + f"{n:064x}"


def _pad(address):
    return "0x" + "0" * 24 + address[2:]


def _word(value):
    return f"{value:064x}"


W = "0x" + "a1" * 20   # trading wallet, a Safe whose owner is K
K = "0x" + "a2" * 20
V = "0x" + "b1" * 20   # trading wallet, a plain key
F = "0x" + "f1" * 20   # personal funder of W, V and P
P = "0x" + "c1" * 20
D = "0x" + "d1" * 20   # destination of W, V and ten other addresses
X = "0x" + "e1" * 20   # sends W outcome tokens in a transaction the API does not list
S = "0xf70da97812cb96acdf810712aa562db8dfa3dbef"  # "Relay solver" in phi_forensics/data/service_labels.json
OTHERS = ["0x" + f"{i:02x}" * 20 for i in range(1, 11)]
EXCHANGE, NEG_EXCHANGE = chain.EXCHANGES[0], chain.EXCHANGES[1]
CTF = sources.POSITION_CONTRACTS[0]
ADAPTER = "0xd91e80cf2e7be2e162c6513ced06f1dd0da35296"  # Neg Risk Adapter
USDC_E, USDC, ZERO = chain.USDC_E, chain.USDC, chain.ZERO

C1, C2, C3, C4 = ("0x" + c * 32 for c in ("11", "22", "33", "44"))
E = "0x" + "e0" * 32   # neg-risk event of C3 and C4
T1Y, T1N, T2Y, T2N, T3Y, T3N, T4Y, T4N = "101", "102", "201", "202", "301", "302", "401", "402"


def _market(condition, question, tokens, prices, closed=False, event=None):
    return {"conditionId": condition, "question": question, "slug": question.lower().replace(" ", "-")[:40], "outcomes": '["Yes", "No"]',
            "clobTokenIds": json.dumps(tokens), "outcomePrices": json.dumps(prices), "closed": closed,
            "umaResolutionStatus": "resolved" if closed else None, "negRisk": event is not None, "negRiskMarketID": event,
            "startDate": "2026-04-01T00:00:00Z", "endDate": "2026-05-08T00:00:00Z", "closedTime": "2026-05-09 00:00:00+00" if closed else None,
            "volume": "1000"}


MARKETS = [_market(C1, "Market one resolved Yes", [T1Y, T1N], ["1", "0"], closed=True),
           _market(C2, "Market two still open", [T2Y, T2N], ["0.55", "0.45"]),
           _market(C3, "Event outcome A", [T3Y, T3N], ["0.4", "0.6"], event=E),
           _market(C4, "Event outcome B", [T4Y, T4N], ["0.6", "0.4"], event=E)]
TITLES = {m["conditionId"]: m["question"] for m in MARKETS}


def _trade(condition, side, token, index, size, cash, price):
    return {"type": "TRADE", "side": side, "condition_id": condition, "token_id": token, "outcome_index": index,
            "outcome": "Yes" if index == 0 else "No", "size": size, "usdc_size": cash, "price": price, "title": TITLES[condition]}


def _op(kind, condition, size, cash):
    return {"type": kind, "condition_id": condition, "size": size, "usdc_size": cash, "title": TITLES.get(condition, "Event of A and B")}


# n: (block, ERC-20 moves (token, from, to, raw), ERC-1155 moves (from, to, [(token, raw)]), OrderFilled (maker, side, token,
#     maker amount, taker amount) or None, API rows {wallet: row}).
TRANSACTIONS = {
    1: (70_000_000, [(USDC_E, F, W, 5 * U)], [], None, {}),                     # older than the default funding scan of W
    2: (88_000_000, [(USDC_E, F, W, 1000 * U)], [], None, {}),
    3: (88_010_000, [(USDC_E, F, P, 70 * U)], [], None, {}),
    4: (88_050_000, [(USDC_E, F, V, 200 * U)], [], None, {}),
    5: (88_060_000, [(USDC_E, S, V, 50 * U)], [], None, {}),
    6: (88_100_000, [(USDC, S, W, 500 * U)], [], None, {}),
    7: (88_200_000, [(USDC_E, W, EXCHANGE, 60 * U)], [(EXCHANGE, W, [(T1Y, 200 * U)])], (W, "BUY", T1Y, 60 * U, 200 * U),
        {W: _trade(C1, "BUY", T1Y, 0, 200, 60, 0.3)}),
    # A first-generation fill whose fee was taken in shares: the API shows 100 shares, the chain delivered 98.
    8: (88_300_000, [(USDC_E, W, EXCHANGE, 40 * U)], [(EXCHANGE, W, [(T2Y, 98 * U)])], None, {W: _trade(C2, "BUY", T2Y, 0, 100, 40, 0.4)}),
    9: (89_000_000, [(USDC_E, W, CTF, 50 * U)], [(ZERO, W, [(T2Y, 50 * U), (T2N, 50 * U)])], None, {W: _op("SPLIT", C2, 50, 50)}),
    10: (89_100_000, [(USDC_E, EXCHANGE, W, 22_500_000)], [(W, EXCHANGE, [(T2N, 50 * U)])], None, {W: _trade(C2, "SELL", T2N, 1, 50, 22.5, 0.45)}),
    11: (89_150_000, [(USDC_E, V, EXCHANGE, 25 * U)], [(EXCHANGE, V, [(T1Y, 100 * U)])], None, {V: _trade(C1, "BUY", T1Y, 0, 100, 25, 0.25)}),
    12: (89_200_000, [(USDC_E, CTF, W, 200 * U)], [(W, ZERO, [(T1Y, 200 * U)])], None, {W: _op("REDEEM", C1, 200, 200)}),
    13: (89_250_000, [(USDC_E, CTF, V, 100 * U)], [(V, ZERO, [(T1Y, 100 * U)])], None, {V: _op("REDEEM", C1, 100, 100)}),
    14: (89_300_000, [(USDC_E, W, NEG_EXCHANGE, 30 * U)], [(NEG_EXCHANGE, W, [(T3N, 50 * U)])], None, {W: _trade(C3, "BUY", T3N, 1, 50, 30, 0.6)}),
    # Neg-risk conversion: 50 No of outcome A become 50 Yes of outcome B. The API row names the event, not the markets.
    15: (89_400_000, [], [(W, ADAPTER, [(T3N, 50 * U)]), (ADAPTER, W, [(T4Y, 50 * U)])], None, {W: _op("CONVERSION", E, 50, 0)}),
    16: (89_500_000, [], [(X, W, [(T2Y, 10 * U)])], None, {}),
    17: (89_600_000, [(USDC_E, W, D, 300 * U)], [], None, {}),
    18: (89_650_000, [(USDC_E, V, D, 150 * U)], [], None, {}),
    **{19 + i: (89_700_000 + 1000 * i, [(USDC_E, other, D, U)], [], None, {}) for i, other in enumerate(OTHERS)},
}
CODE = {W: "0x608060405236", EXCHANGE: "0x6080", NEG_EXCHANGE: "0x6080", CTF: "0x6080", ADAPTER: "0x6080"}
NONCE = {F: 5, D: 3, V: 20, P: 1, K: 40, X: 2}
OWNERS = {W: [K]}
PROFILES = {W: {"proxyWallet": W, "createdAt": "2026-04-10T09:00:00Z", "name": "tester-one", "bio": "never returned",
                "profileImage": "https://example.invalid/x.png", "verifiedBadge": False}}
HOLDERS = {C1: [{"token_id": T1Y, "holders": [{"proxy_wallet": "0x" + "31" * 20, "amount": 300.0, "name": "first"},
                                              {"proxy_wallet": "0x" + "32" * 20, "amount": 100.0, "name": "second"}]},
                {"token_id": T1N, "holders": []}]}
PRICES = {T1Y: [(1_776_390_000, 0.30), (1_778_000_000, 0.80), (1_778_240_000, 0.90), (1_778_260_000, 0.95)],
          T2Y: [(1_778_100_000, 0.50), (1_778_249_000, 0.52)], T2N: [(1_778_249_000, 0.47)]}
SINGLE, BATCH = sources.TRANSFER_SINGLE, sources.TRANSFER_BATCH


def _logs():
    logs = []
    for n, (block, erc20, erc1155, fill, _) in sorted(TRANSACTIONS.items(), key=lambda kv: kv[1][0]):
        where = {"transactionHash": tx(n), "blockNumber": hex(block), "removed": False}
        for token, sender, receiver, raw in erc20:
            logs.append({"address": token, "topics": [chain.TRANSFER, _pad(sender), _pad(receiver)], "data": "0x" + _word(raw), **where})
        for sender, receiver, moved in erc1155:
            topics = [SINGLE if len(moved) == 1 else BATCH, _pad(CTF), _pad(sender), _pad(receiver)]
            if len(moved) == 1:
                data = _word(int(moved[0][0])) + _word(moved[0][1])
            else:
                count = len(moved)
                data = (_word(64) + _word(64 + 32 * (count + 1)) + _word(count) + "".join(_word(int(t)) for t, _ in moved)
                        + _word(count) + "".join(_word(v) for _, v in moved))
            logs.append({"address": CTF, "topics": topics, "data": "0x" + data, **where})
        if fill:
            maker, side, token, maker_amount, taker_amount = fill
            logs.append({"address": EXCHANGE, "topics": [chain.ORDER_FILLED, "0x" + _word(n), _pad(maker), _pad(EXCHANGE)],
                         "data": "0x" + _word(0 if side == "BUY" else 1) + _word(int(token)) + _word(maker_amount) + _word(taker_amount)
                                 + _word(0) * 3, **where})
    counter = {}
    for log in logs:  # one transaction per block here, so the index in the transaction is the index in the block
        counter[log["transactionHash"]] = counter.get(log["transactionHash"], -1) + 1
        log["logIndex"] = hex(counter[log["transactionHash"]])
    return logs


def _matches(value, wanted):
    return wanted is None or (value in [w.lower() for w in wanted] if isinstance(wanted, list) else value == wanted.lower())


class Response:
    def __init__(self, status, body):
        self.status, self.headers, self._body = status, {}, body

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class World:
    """The scenario served over HTTP and JSON-RPC. `activity` rows can be edited by a test before it reads them."""

    def __init__(self, page=3):
        self.page, self.logs = page, _logs()
        self.activity = {}
        for n, (block, _, _, _, rows) in sorted(TRANSACTIONS.items()):
            for wallet, row in rows.items():
                self.activity.setdefault(wallet, []).append({**row, "proxy_wallet": wallet, "timestamp": ts(block), "transaction_hash": tx(n)})
        self.markets = [dict(m) for m in MARKETS]
        self.profiles = {k: dict(v) for k, v in PROFILES.items()}
        self.urls, self.rpc_calls = [], []
        self.http_faults, self.rpc_faults = [], []
        self.max_log_range, self.unknown_on, self.tamper_on = None, set(), set()

    def row(self, wallet, n):
        return next(r for r in self.activity[wallet] if r["transaction_hash"] == tx(n))

    def clock(self):
        return float(NOW)

    def block_at(self, timestamp):
        return min(HEAD, (timestamp - GENESIS) // 2)

    # Switches

    def fail_http(self, part, status, body=b'{"error": "injected"}', times=1):
        """The next `times` URLs containing `part` get this answer instead of the scenario's."""
        self.http_faults.append([part, status, body, times])

    def fail_rpc(self, method, error=None, url=None, times=10 ** 9):
        """Calls of `method` (on `url`, or on every node) answer a JSON-RPC error object."""
        self.rpc_faults.append([method, url, error or {"code": -32000, "message": "injected failure"}, times])

    # HTTP

    def fetch(self, url):
        self.urls.append(url)
        for fault in self.http_faults:
            if fault[0] in url and fault[3] > 0:
                fault[3] -= 1
                return fault[1], fault[2]
        parts = urllib.parse.urlsplit(url)
        query = urllib.parse.parse_qs(parts.query, keep_blank_values=True)
        one = lambda key: query.get(key, [None])[0]
        route = (parts.hostname, parts.path)
        if route == ("data-api.polymarket.com", "/v2/activity"):
            rows = [r for r in self.activity.get(one("user"), []) if one("type") in (None, r["type"])]
            return self._page([r for r in rows if int(one("start") or 0) <= r["timestamp"] <= int(one("end") or NOW)], one("cursor"))
        if route == ("data-api.polymarket.com", "/v2/trades"):
            rows = sorted((r for rows in self.activity.values() for r in rows if r["type"] == "TRADE"
                           and one("user") in (None, r["proxy_wallet"]) and one("condition") in (None, r["condition_id"])),
                          key=lambda r: r["timestamp"])
            return self._page(rows, one("cursor"))
        if route == ("data-api.polymarket.com", "/v2/positions"):
            return self._page(self._positions(one("user")), one("cursor"))
        if route == ("data-api.polymarket.com", "/v2/holders"):
            return 200, json.dumps({"data": HOLDERS.get(one("condition"), [])}).encode()
        if route == ("gamma-api.polymarket.com", "/public-profile"):
            found = self.profiles.get(one("address"))
            return (200, json.dumps(found).encode()) if found else (404, b'{"error": "profile not found"}')
        if route == ("gamma-api.polymarket.com", "/markets"):
            conditions, tokens, closed = set(query.get("condition_ids", [])), set(query.get("clob_token_ids", [])), one("closed") == "true"
            return 200, json.dumps([m for m in self.markets if m["closed"] == closed and (m["conditionId"] in conditions
                                                                                         or tokens & set(json.loads(m["clobTokenIds"])))]).encode()
        if route == ("clob.polymarket.com", "/prices-history"):
            low, high = int(one("startTs") or 0), int(one("endTs") or NOW)
            return 200, json.dumps({"history": [{"t": t, "p": p} for t, p in PRICES.get(one("market"), []) if low <= t <= high]}).encode()
        return 404, b'{"error": "not found"}'

    def _page(self, rows, cursor):
        start = int(cursor or 0)
        more = start + self.page < len(rows)
        page = {"limit": self.page, "has_more": more, "next_cursor": str(start + self.page) if more else None}
        return 200, json.dumps({"data": rows[start:start + self.page], "pagination": page}).encode()

    def _positions(self, wallet):
        held = {}
        for log in self.logs:
            if log["address"] == CTF:
                for token, value, sign in self._moved(log, wallet):
                    held[token] = held.get(token, 0) + sign * value
        return [{"proxy_wallet": wallet, "token_id": t, "current_size": v / U} for t, v in sorted(held.items()) if v]

    @staticmethod
    def _moved(log, wallet):
        words = [int(log["data"][2:][i:i + 64], 16) for i in range(0, len(log["data"]) - 2, 64)]
        if log["topics"][0] == SINGLE:
            pairs = [(words[0], words[1])]
        else:
            ids, values = words[0] // 32, words[1] // 32
            pairs = list(zip(words[ids + 1:ids + 1 + words[ids]], words[values + 1:values + 1 + words[values]]))
        sign = (1 if "0x" + log["topics"][3][-40:] == wallet else 0) - (1 if "0x" + log["topics"][2][-40:] == wallet else 0)
        return [(str(t), v, sign) for t, v in pairs if sign]

    def urlopen(self, request, timeout=None):
        """urllib.request.urlopen over the scenario, for net.fetch: refusals come back as HTTPError, as from a server."""
        status, body = self.fetch(request.full_url)
        if status != 200:
            raise urllib.error.HTTPError(request.full_url, status, "refused", {}, io.BytesIO(body))
        return Response(status, body)

    # JSON-RPC

    def rpc(self, method, params, urls=None, **kw):
        """net.rpc over the scenario: each node is tried in turn and an error object moves to the next one."""
        error = None
        for url in urls or net.RPC_URLS:
            self.rpc_calls.append((method, url))
            answer = self._answer(url, method, params)
            if "error" in answer:
                error = net.SourceError(f"{url} {method}: {answer['error']}")
                continue
            return answer["result"]
        raise error

    def _answer(self, url, method, params):
        for fault in self.rpc_faults:
            if fault[0] == method and fault[1] in (None, url) and fault[3] > 0:
                fault[3] -= 1
                return {"error": fault[2]}
        if method == "eth_blockNumber":
            return {"result": hex(HEAD)}
        if method == "eth_getBlockByNumber":
            number = int(params[0], 16)
            return {"result": {"number": params[0], "timestamp": hex(ts(number))} if number <= HEAD else None}
        if method == "eth_getLogs":
            query = params[0]
            low, high = int(query["fromBlock"], 16), int(query["toBlock"], 16)
            if self.max_log_range and high - low + 1 > self.max_log_range:
                return {"error": {"code": -32005, "message": f"block range exceeds the limit of {self.max_log_range}"}}
            topics = query.get("topics") or []
            return {"result": [dict(log) for log in self.logs if low <= int(log["blockNumber"], 16) <= high
                               and _matches(log["address"], query.get("address"))
                               and all(_matches(log["topics"][i], t) for i, t in enumerate(topics) if i < len(log["topics"]))
                               and len(topics) <= len(log["topics"])]}
        if method == "eth_call":
            to, data = params[0]["to"].lower(), params[0]["data"]
            if data.startswith("0x70a08231"):
                holder, last = "0x" + data[-40:], HEAD if params[1] == "latest" else int(params[1], 16)
                balance = sum(int(log["data"], 16) * ((("0x" + log["topics"][2][-40:]) == holder) - (("0x" + log["topics"][1][-40:]) == holder))
                              for log in self.logs if log["address"] == to and log["topics"][0] == chain.TRANSFER
                              and int(log["blockNumber"], 16) <= last)
                return {"result": "0x" + _word(balance)}
            if data == chain.GET_OWNERS and to in OWNERS:
                return {"result": "0x" + _word(32) + _word(len(OWNERS[to])) + "".join(_pad(o)[2:] for o in OWNERS[to])}
            return {"result": "0x"}
        if method == "eth_getCode":
            return {"result": CODE.get(params[0].lower(), "0x")}
        if method == "eth_getTransactionCount":
            return {"result": hex(NONCE.get(params[0].lower(), 0))}
        if method == "eth_getTransactionReceipt":
            return {"result": None if url in self.unknown_on else self._receipt(params[0].lower(), tampered=url in self.tamper_on)}
        return {"error": {"code": -32601, "message": f"the method {method} does not exist"}}

    def _receipt(self, transaction, tampered=False):
        logs = [{k: v for k, v in log.items() if k != "removed"} for log in self.logs if log["transactionHash"] == transaction]
        if not logs:
            return None
        if tampered:
            logs[0] = {**logs[0], "data": "0x" + _word(int(logs[0]["data"], 16) + 1)}
        block = logs[0]["blockNumber"]
        return {"transactionHash": transaction, "blockNumber": block, "blockHash": "0x" + _word(int(block, 16)), "status": "0x1", "logs": logs}

    def sources(self):
        return REAL_SOURCES(fetch=self.fetch, rpc=self.rpc, clock=self.clock)


REAL_FETCH, REAL_SOURCES = net.fetch, sources.Sources  # kept before any test patches them


def _refuse(*args, **kwargs):
    raise AssertionError(f"a test tried to reach the network: {str(args[:1])[:120]}")


def offline(case, world):
    """For one test: the chain helpers read `world`, any real HTTP request fails, cached block times are dropped."""
    for patch in (mock.patch.object(net, "rpc", world.rpc), mock.patch.object(net, "fetch", _refuse),
                  mock.patch.object(urllib.request, "urlopen", _refuse)):
        patch.start()
        case.addCleanup(patch.stop)
    chain.block_ts.cache_clear()
    case.addCleanup(chain.block_ts.cache_clear)
