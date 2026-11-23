"""Confirmed PM account evidence, deterministic ascertainment and bounded activity collection."""

import argparse
import csv
import hashlib
import re
from decimal import Decimal
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlencode
from .collect import net
from .common import CN22, CN_HOT, F2020, REPO, SNAP, STREAMS, hexstr, read, save, weeks
from .events import load_stream
from .archive import native_archive

TRADERS = REPO / "investigations/changenow-polymarket/sources/state/pm_traders.csv"
PRIOR_PNL = REPO / "investigations/changenow-polymarket/sources/state/pm_pnl2.csv"
TRADES = REPO / "investigations/ballon-dor-census/sources/TRADES.csv"
API = "https://data-api.polymarket.com/v2/"


def registry(snap):
    """Exact trading endpoints only; a derived address never credits its signer."""
    members, owners = {}, {}
    with TRADERS.open() as f:
        for r in csv.DictReader(f):
            a = hexstr(r["account"], 40)
            members[a] = "pm_traders.csv#" + a
            if r["account_type"] == "DW":
                owners[r["owner"].lower()] = a
    with TRADES.open() as f:
        for r in csv.DictReader(f):
            members[hexstr(r["wallet"], 40)] = "TRADES.csv#" + r["tx"]
    for p in sorted(snap.glob("*/frame.json.gz")):
        for r in read(p)["fills"]:
            members[hexstr(r[5], 40)] = p.parent.name + "/frame#" + r[2] + "/" + str(r[3])
    return members, owners


def targets(snap, first, last):
    members, owners = registry(snap)
    archived, _ = native_archive()
    selected = set()
    funding = defaultdict(set)
    for w in weeks(first, last):
        possible = set()
        for stream in STREAMS:
            rows, _ = load_stream(snap, w, 137, stream)
            for x in rows:
                a = x.recipient
                if x.role in {"withdrawal_pool", "labelled_hot_wallet"}:
                    selected.add(a)
                elif x.role == "commingled_route":
                    possible.add(a)
                funding[a].add(x.ts)
        # Known traders plus 64 reproducibly chosen recipients per week on the ambiguous rail.
        selected.update(possible & members.keys())
        ranked = sorted(possible, key=lambda a: hashlib.sha256((w + a).encode()).digest())
        selected.update(ranked[:64])
        remote = list(archived.get(w, []))
        for stream in STREAMS:
            remote.extend(load_stream(snap, w, 1, stream)[0])
        for x in remote:
            if x.recipient in members:
                selected.add(x.recipient)
                funding[x.recipient].add(x.ts)
        for a in possible & owners.keys():
            selected.add(owners[a])
            funding[owners[a]].update(funding[a])
    route_file = snap / "routes.json.gz"
    if route_file.exists():
        for r in read(route_file)["accounts"].values():
            for candidate in r["proofs"]:
                proof = candidate["proof"]
                terminal = proof["tx"]["to"]
                selected.add(terminal)
                funding[terminal].add(int(proof["header"]["timestamp"], 16))
    return {a: sorted(funding[a]) for a in sorted(selected - {CN22, F2020, *CN_HOT})}


def market_ref(raw, token):
    if isinstance(raw, str) and re.fullmatch(r"0x[0-9a-fA-F]{64}", raw):
        return raw.lower()
    if isinstance(raw, str) and re.fullmatch(r"0x[0-9a-fA-F]{1,63}", raw):
        return "api:" + raw.lower()
    if str(token).isdigit():
        return "token:" + str(token)
    raise ValueError("no usable market or token witness")


def activity_page(a, lo, hi, limit=100, cursor=None, side=None):
    params = dict(
        user=a, type="TRADE", start=lo, end=hi, limit=limit, sort_by="TIMESTAMP", sort_direction="ASC"
    )
    if cursor:
        params["cursor"] = cursor
    if side:
        params["side"] = side
    v = net.get_json(API + "activity?" + urlencode(params), tries=2, timeout=18)
    pg = v["pagination"]
    nxt = pg.get("next_cursor")
    if not isinstance(pg["has_more"], bool) or pg["has_more"] != bool(nxt):
        raise ValueError("ambiguous activity pagination")
    rows = []
    for r in v["data"]:
        ts = r["timestamp"]
        if (
            r["proxy_wallet"].lower() != a
            or r["type"] != "TRADE"
            or not lo <= ts <= hi
            or r["side"] not in {"BUY", "SELL"}
            or side
            and r["side"] != side
        ):
            raise ValueError("activity endpoint did not honor the wallet/time/type filter")
        notional = Decimal(str(r["usdc_size"]))
        if not notional.is_finite() or notional < 0:
            raise ValueError("invalid trade notional")
        rows.append(
            [
                ts,
                hexstr(r["transaction_hash"], 64),
                r["side"],
                market_ref(r.get("condition_id"), r["token_id"]),
                str(r["token_id"]),
                str(r["usdc_size"]),
                r.get("title", ""),
            ]
        )
    if [r[0] for r in rows] != sorted(r[0] for r in rows) or (nxt and not rows):
        raise ValueError("nonmonotone/empty continuation")
    return rows, nxt


def profile(a, times, end):
    result = {
        "asof_exclusive": end,
        "address": a,
        "first_trade": None,
        "status": "UNKNOWN",
        "buys": [],
        "intervals": [],
        "first_after": {},
        "pnl": None,
        "errors": [],
    }
    try:
        first, _ = activity_page(a, 1, end - 1, 1)
        if not first:
            result["status"] = "NO_INDEXED_TRADE"
            return result
        result["status"] = "TRADE_OBSERVED"
        result["first_trade"] = first[0]
        times = sorted({t for t in times if t + 1 < end})
        # For each distinct uncovered receipt, request the earliest strictly subsequent BUY.
        # One sorted page supplies the first buy for any receipt before its last timestamp.
        cursor_end = 0
        for t in times:
            if t + 1 <= cursor_end:
                continue
            rows, nxt = activity_page(a, t + 1, end - 1, 16, side="BUY")
            upper = rows[-1][0] if nxt else end - 1
            result["intervals"].append([t + 1, upper, not bool(nxt)])
            result["buys"].extend(rows)
            cursor_end = upper
        for t in times:
            if first[0][0] > t:
                result["first_after"][str(t)] = first[0]
            elif any(r[0] > t for r in result["buys"]):
                # A buy already proves later trading; no second API call needed.
                continue
            else:
                rows, _ = activity_page(a, t + 1, end - 1, 1)
                result["first_after"][str(t)] = rows[0] if rows else None
    except (net.SourceError, KeyError, ValueError, TypeError) as e:
        result["errors"].append(str(e)[:350])
    if result["status"] == "TRADE_OBSERVED":
        try:
            payload = net.get_json(
                API + "user-pnl?" + urlencode(dict(user=a, interval="max", fidelity="1d")),
                tries=2,
                timeout=20,
            )["data"]
            if payload["proxy_wallet"].lower() != a:
                raise ValueError("PnL wallet mismatch")
            old = [
                p
                for p in payload["points"]
                if p["timestamp"] < end and p.get("economic_pnl") is not None
            ]
            if old:
                p = max(old, key=lambda r: r["timestamp"])
                result["pnl"] = {
                    k: p.get(k)
                    for k in (
                        "timestamp",
                        "source_block",
                        "economic_pnl",
                        "realized_pnl",
                        "unrealized_pnl",
                        "volume_usdc",
                    )
                }
        except (net.SourceError, ValueError, KeyError, TypeError) as e:
            result["errors"].append("PnL: " + str(e)[:300])
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--from-week", required=True)
    p.add_argument("--to-week", required=True)
    p.add_argument("--asof", required=True, help="exclusive UTC cutoff as Unix seconds", type=int)
    p.add_argument("--work", required=True, type=Path, help="resumable local cache")
    p.add_argument("--dest", type=Path, default=SNAP)
    p.add_argument("--workers", type=int, choices=range(1, 9), default=5)
    args = p.parse_args()
    wanted = targets(args.dest, args.from_week, args.to_week)
    print("selected", len(wanted), flush=True)

    def one(item):
        a, times = item
        key = hashlib.sha256(str([a, times, args.asof]).encode()).hexdigest()
        cache = args.work / (key + ".json.gz")
        if cache.exists():
            return read(cache)
        r = profile(a, times, args.asof)
        if not r["errors"]:
            save(cache, r)
        return r

    with ThreadPoolExecutor(args.workers) as pool:
        profiles = list(pool.map(one, wanted.items()))
    save(
        args.dest / "accounts.json.gz",
        dict(
            asof_exclusive=args.asof,
            first=args.from_week,
            last=args.to_week,
            profiles={r["address"]: r for r in profiles},
        ),
    )


if __name__ == "__main__":
    main()
