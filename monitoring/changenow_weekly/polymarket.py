"""Polymarket side: is an address a trading wallet, does it own one, and what does the public API say of the account.

Ownership here is a fact about keys, read on-chain: `owner()` of a Deposit Wallet, `getOwners()` of a Safe, or the
official exchange's own derivation for a legacy proxy. It is never a statement about a person. Wallet formulas and
contract names are reused from the archived fund-flow tools of this repository rather than written again.
"""
import importlib.util
import json
import sys
import time
from pathlib import Path

from phi_monitor import net

from . import chainio as io

REPO = Path(__file__).resolve().parents[2]
_bytecode, sys.dont_write_bytecode = sys.dont_write_bytecode, True   # the archived folders are evidence: importing must not leave a cache file in them
sys.path.insert(0, str(REPO / "investigations/polysentinel/sources/signal_engine"))
from fund_flow import flows as ff_flows      # noqa: E402  documented Polymarket and Relay contracts, receipt decoding
from fund_flow import wallets as ff_wallets  # noqa: E402  wallet types and factory constants



def _strict_read(client, to, signature, argument=None):
    """The archived classifier's view read, except that only an EVM revert means "no such view". Any other failure
    (a refused or throttled call on every endpoint) raises, so a real wallet is never filed as another contract."""
    data = ff_wallets.selector(signature) + (ff_wallets.word(argument).hex() if argument else "")
    try:
        return client.call(to, data)
    except Exception as exc:
        if "revert" in str(exc).lower():
            return None
        raise


ff_wallets._read = _strict_read             # the archived file stays unchanged; this package reads views strictly

_spec = importlib.util.spec_from_file_location("cn_keccak", REPO / "investigations/changenow-outflows/sources/tools/keccak.py")
kk = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(kk)                 # keccak and the two Deposit Wallet templates, self-checked in that file
sys.dont_write_bytecode = _bytecode

POLYGON = 137
PUSD, USDC_E, USDC = ff_flows.PUSD, ff_flows.USDC_E, ff_flows.USDC
COLLATERAL = {PUSD: ("pUSD", 6), USDC_E: ("USDC.e", 6), USDC: ("USDC", 6)}
OWNER = "8da5cb5b"                                                      # owner()
GET_OWNERS = "a0e67e2b"                                                 # getOwners()
SAFE_OF = kk.keccak(b"computeProxyAddress(address)")[:4].hex()
PROXY_OF = kk.keccak(b"getPolyProxyWalletAddress(address)")[:4].hex()
DATA_API = "https://data-api.polymarket.com/v2/activity"
GAMMA = "https://gamma-api.polymarket.com/public-profile"
KINDS = dict(deposit="DEPOSIT_WALLET", safe="GNOSIS_SAFE", proxy="POLYMARKET_PROXY")


def _word(address):
    return "0" * 24 + address[2:].lower()


def _tail_address(data_hex):
    return "0x" + data_hex[-40:] if len(data_hex) >= 40 and int(data_hex[-40:] or "0", 16) else None


def owned_wallets(owners, say=print):
    """Trading wallets that exist on Polygon for each key in `owners`: {owner: [dict(wallet, kind, proof)]}.
    Deposit Wallets are derived offline (both templates) and proven by their own owner(); Safes and legacy proxies
    are derived by the official contracts, then proven by getOwners() or by deployed clone code."""
    owners = sorted({o.lower() for o in owners})
    found = {}

    def add(owner, wallet, kind, proof):
        found.setdefault(owner, []).append(dict(wallet=wallet, kind=kind, proof=proof))

    derived = []
    for o in owners:
        derived += [(o, kk.deposit_wallet(o, kk.BEACON)), (o, kk.deposit_wallet(o, kk.TEMPLATE))]
    answers = io.aggregate3(POLYGON, [(w, OWNER) for _, w in derived])
    for (o, w), (ok, data) in zip(derived, answers):
        if ok and len(data) == 64 and "0x" + data[-40:] == o:
            add(o, w, KINDS["deposit"], "owner() of the derived Deposit Wallet returns this key")
    say(f"  deposit wallets: {len(owners)} keys tested, {sum(len(v) for v in found.values())} wallets exist")

    safes = [(o, _tail_address(data)) for o, (ok, data) in zip(owners, io.aggregate3(POLYGON, [(ff_wallets.SAFE_FACTORY, SAFE_OF + _word(o)) for o in owners])) if ok and len(data) == 64]
    safes = [(o, w) for o, w in safes if w]
    for (o, w), (ok, data) in zip(safes, io.aggregate3(POLYGON, [(w, GET_OWNERS) for _, w in safes], size=150)):
        if ok and len(data) >= 192 and _word(o) in [data[128 + 64 * i:192 + 64 * i] for i in range(int(data[64:128], 16))]:
            add(o, w, KINDS["safe"], "getOwners() of the Safe predicted by the official factory lists this key")
    proxies = [(o, _tail_address(data)) for o, (ok, data) in zip(owners, io.aggregate3(POLYGON, [(ff_wallets.LEGACY_EXCHANGE, PROXY_OF + _word(o)) for o in owners])) if ok and len(data) == 64]
    proxies = [(o, w) for o, w in proxies if w]
    codes = io.get_codes(POLYGON, [w for _, w in proxies])
    for o, w in proxies:
        if codes[w][2:].lower().startswith(ff_wallets.CLONE_PREFIX):
            add(o, w, KINDS["proxy"], "clone deployed at the address the legacy exchange derives for this key")
    say(f"  safes and legacy proxies tested: {len(safes)} and {len(proxies)}; keys owning a wallet: {len(found)}")
    return found


class _Client:
    """The two reads the archived classifier needs, served by this package's endpoints."""

    def rpc(self, method, params):
        return io.rpc(POLYGON, method, params, state=True)

    def call(self, to, data):
        return io.rpc(POLYGON, "eth_call", [dict(to=to, data=data), "latest"], state=True)


def classify(address):
    """Wallet type of one Polygon address by the archived classifier (bytecode, official factories, owners read on-chain)."""
    return ff_wallets.classify_wallet(_Client(), address)


def trading_wallets(addresses, say=print):
    """Among Polygon addresses, those that are themselves Polymarket trading wallets: {address: classification}."""
    addresses = sorted({a.lower() for a in addresses})
    codes = io.get_codes(POLYGON, addresses)
    shaped = [a for a in addresses if codes[a] not in ("0x", "0x0") and not codes[a][2:].lower().startswith(ff_wallets.EIP7702_PREFIX)]
    out = {}
    for a in shaped:
        c = classify(a)
        if c["type"] in (ff_wallets.DEPOSIT, ff_wallets.PROXY) or (c["type"] == ff_wallets.SAFE and c.get("polymarket_factory")):
            out[a] = c
    say(f"  trading wallets: {len(addresses)} addresses, {len(shaped)} with contract code, {len(out)} Polymarket wallets")
    return out, {a: codes[a][:48] for a in shaped}


def profile(wallet):
    """Public profile fields the service itself publishes for an address. Free text and images are not read."""
    status, body = net.fetch(f"{GAMMA}?address={wallet}")
    if status == 404:
        return None
    if status != 200:
        raise net.SourceError(f"gamma public-profile HTTP {status}", status)
    p = json.loads(body)
    return dict(wallet=(p.get("proxyWallet") or "").lower(), name=p.get("name") if p.get("displayUsernamePublic") else None,
                pseudonym=p.get("pseudonym"), created_utc=(p.get("createdAt") or "")[:19].replace("T", " "))


def activity(wallet, kind=None, start=None, end=None, ascending=True, limit=500, max_pages=40):
    """Rows of the public activity feed, paged by cursor. Returns (rows, complete): `complete` is False when the page
    cap stopped the read, and the caller must say so. TIP rows are served only when asked for by type."""
    rows, cursor = [], None
    for _ in range(max_pages):
        query = f"{DATA_API}?user={wallet}&limit={limit}&sort_by=TIMESTAMP&sort_direction={'ASC' if ascending else 'DESC'}&exclude_deposits_withdrawals=false"
        query += (f"&type={kind}" if kind else "") + (f"&start={start}" if start else "") + (f"&end={end}" if end else "") + (f"&cursor={cursor}" if cursor else "")
        body = net.get_json(query)
        time.sleep(0.15)
        if not isinstance(body, dict) or "data" not in body:
            raise net.SourceError(f"activity of {wallet}: unexpected answer")
        rows += [{k: v for k, v in r.items() if k in ("timestamp", "type", "side", "size", "usdc_size", "price", "transaction_hash", "condition_id", "title", "slug", "outcome")} for r in body["data"]]
        cursor = (body.get("pagination") or {}).get("next_cursor")
        if not cursor or limit < 500:
            return rows, True
    return rows, False


def around(wallet, moments, horizon, span=86400):
    """Public activity next to each confirmed movement of one wallet: trades in the day after a funding reached it,
    and redemptions (payouts of resolved markets) in the day before a withdrawal left it. Descriptive only.
    moments: [(direction, timestamp)]. `horizon` is the time the chain data stop: a day that runs past it is marked
    as not over. Returns dict(after_funding, before_withdrawal, complete)."""
    credits = sorted({ts for kind, ts in moments if kind == "FUNDING"})
    debits = sorted({ts for kind, ts in moments if kind == "WITHDRAWAL"})
    out, complete = dict(after_funding=[], before_withdrawal=[]), True

    def largest(rows):
        by = {}
        for r in rows:
            name = r.get("title") or r.get("slug") or r.get("condition_id") or ""
            by[name] = by.get(name, 0.0) + float(r.get("usdc_size") or 0)
        name = max(sorted(by), key=by.get) if by else ""
        return name, round(by.get(name, 0.0), 2)

    if credits:
        trades, ok = activity(wallet, "TRADE", credits[0], min(credits[-1] + span, horizon))
        complete = complete and ok
        for ts in credits:
            rows = [t for t in trades if ts <= t["timestamp"] <= ts + span]
            name, usd = largest(rows)
            out["after_funding"].append(dict(ts=ts, day_over=ts + span <= horizon, trades=len(rows), usd=round(sum(float(t.get("usdc_size") or 0) for t in rows) + 0.0, 2),
                                             first_trade_ts=min((t["timestamp"] for t in rows), default=None), largest_market=name, largest_market_usd=usd))
    if debits:
        paid, ok = activity(wallet, "REDEEM", debits[0] - span, debits[-1])
        complete = complete and ok
        for ts in debits:
            rows = [r for r in paid if ts - span <= r["timestamp"] <= ts]
            name, usd = largest(rows)
            out["before_withdrawal"].append(dict(ts=ts, redemptions=len(rows), usd=round(sum(float(r.get("usdc_size") or 0) for r in rows) + 0.0, 2), largest_market=name, largest_market_usd=usd))
    return dict(out, complete=complete)


def account_summary(wallet, start, end):
    """What the API shows of one account: first and last trade ever, trades and cash movements inside the week."""
    first, _ = activity(wallet, "TRADE", ascending=True, limit=1)
    last, _ = activity(wallet, "TRADE", ascending=False, limit=1)
    trades, complete = activity(wallet, "TRADE", start, end - 1)
    moves = []
    for kind in ("DEPOSIT", "WITHDRAWAL", "TIP"):
        got, ok = activity(wallet, kind, start, end - 1)
        complete = complete and ok
        moves += got
    markets = {}
    for t in trades:
        m = markets.setdefault(t.get("slug") or t.get("condition_id"), dict(title=t.get("title"), slug=t.get("slug"), condition_id=t.get("condition_id"), trades=0, usd=0.0, first_ts=t["timestamp"], last_ts=t["timestamp"]))
        m["trades"] += 1
        m["usd"] = round(m["usd"] + float(t.get("usdc_size") or 0), 6)
        m["first_ts"], m["last_ts"] = min(m["first_ts"], t["timestamp"]), max(m["last_ts"], t["timestamp"])
    return dict(first_trade_ts=first[0]["timestamp"] if first else None, last_trade_ts=last[0]["timestamp"] if last else None,
                week_trades=len(trades), week_trade_usd=round(sum(float(t.get("usdc_size") or 0) for t in trades), 2), week_complete=complete,
                markets=sorted(markets.values(), key=lambda m: -m["usd"]), cash_rows=sorted(moves, key=lambda r: r["timestamp"]))
