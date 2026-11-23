"""Independent Polygon order-owner frame and daily USD quotes, both frozen on capture."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlencode
from .collect import net, rpc, header, boundary
from .common import ETH_TOKENS, PUBLICNODE, RPC, SNAP, TOKENS, bounds, hexstr, save, weeks
from monitoring.phi_monitor.chain import EXCHANGES, ORDER_FILLED, decode_fill

PRICE_IDS = {"137:native": "coingecko:polygon-ecosystem-token", "1:native": "coingecko:ethereum"}
PRICE_IDS.update({"137:" + a: "polygon:" + a for a in TOKENS})
PRICE_IDS.update({"1:" + a: "ethereum:" + a for a in ETH_TOKENS})


def capture_frame(week, dest):
    file = dest / week / "frame.json.gz"
    if file.exists():
        return
    t0, t1 = bounds(week)
    a, b = boundary(t0)[1][0], boundary(t1)[1][0]
    rows, spans = [], []
    for k in (1, 3, 5):
        lo = a + (b - a) * k // 6
        hi = lo + 7
        filt = dict(address=EXCHANGES, topics=[ORDER_FILLED], fromBlock=hex(lo), toBlock=hex(hi))
        endpoint = RPC
        try:
            logs = rpc(endpoint, "eth_getLogs", [filt])
        except net.SourceError:
            endpoint = PUBLICNODE
            logs = rpc(endpoint, "eth_getLogs", [filt])
        if not isinstance(logs, list) or len(logs) >= 10000:
            raise ValueError("ambiguous fill page")
        for raw in logs:
            f = decode_fill(raw)
            if not f or f["exchange"] not in EXCHANGES or not lo <= f["block"] <= hi:
                raise ValueError("invalid sample fill")
            t = f["ts"] or header(f["block"])[1]
            if not t0 <= t < t1:
                raise ValueError("outside sample week")
            rows.append(
                [
                    t,
                    f["block"],
                    hexstr(f["tx"], 64),
                    f["log_index"],
                    f["exchange"],
                    f["wallet"],
                    f["token_id"],
                    f["side"],
                    f["cash"],
                ]
            )
        spans.append([lo, hi, len(logs), endpoint])
    save(file, dict(week=week, chain=137, ranges=spans, fills=sorted(rows)))


def prices(start, end, dest):
    t0, t1 = bounds(start)[0], bounds(end)[1]
    args = urlencode(dict(start=t0 - 86400, span=(t1 - t0) // 86400 + 2, period="1d"))
    series, urls = {}, {}
    for ident in PRICE_IDS.values():
        urls[ident] = "https://coins.llama.fi/chart/" + ident + "?" + args
        series.update(net.get_json(urls[ident], timeout=45)["coins"])
    # Retain timestamps, confidence and the series identifier. No stablecoin peg substitution.
    save(dest / "prices.json.gz", dict(urls=urls, ids=PRICE_IDS, series=series))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--from-week", required=True)
    p.add_argument("--to-week", required=True)
    p.add_argument("--dest", type=Path, default=SNAP)
    args = p.parse_args()
    prices(args.from_week, args.to_week, args.dest)
    with ThreadPoolExecutor(3) as pool:
        list(pool.map(lambda w: capture_frame(w, args.dest), weeks(args.from_week, args.to_week)))


if __name__ == "__main__":
    main()


def frame_members(pack, week):
    if pack["chain"] != 137 or pack["week"] != week or len(pack["ranges"]) != 3:
        raise ValueError("invalid independent trading sample")
    counts = [0, 0, 0]
    seen = set()
    accounts = set()
    lo, hi = bounds(week)
    for t, n, tx, idx, exchange, wallet, token, side, cash in pack["fills"]:
        attested = [i for i, (a, b, *_) in enumerate(pack["ranges"]) if a <= n <= b and b - a == 7]
        if (
            len(attested) != 1
            or not lo <= t < hi
            or exchange not in EXCHANGES
            or side not in {"BUY", "SELL"}
            or int(token) < 0
            or cash < 0
            or (tx, idx) in seen
        ):
            raise ValueError("invalid sampled fill identity, time or exchange")
        hexstr(tx, 64)
        counts[attested[0]] += 1
        seen.add((tx, idx))
        accounts.add(hexstr(wallet, 40))
    if counts != [s[2] for s in pack["ranges"]]:
        raise ValueError("incomplete independent trading sample")
    return accounts
