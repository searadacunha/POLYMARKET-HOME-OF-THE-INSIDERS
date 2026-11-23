"""Read the existing paged native-transfer archive, where a root transaction has no log index."""

import csv
import gzip
from collections import defaultdict
from .common import ETH_HOT, REPO, ZERO, bounds, hexstr, read, week_of
from .events import Credit

STATE = REPO / "investigations/changenow-outflows/sources/state"
DEP = "0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b"
NATIVE_SOURCES = sorted(ETH_HOT | {DEP})
LABELS = STATE.parent / "data/attribution_sources.csv"


def native_archive():
    window = read(STATE / "window.json")
    lo, hi = window["chains"]["1"]
    out = defaultdict(list)
    seen = {}
    for addr in NATIVE_SOURCES:
        stem = STATE / "out_full" / ("1_" + addr + "_txlist")
        ck = read(str(stem) + ".ck.json")
        if not ck["done"] or ck["end"] != hi or ck["next"] != hi + 1:
            raise ValueError("incomplete archive checkpoint")
        with gzip.open(str(stem) + ".csv.gz", "rt", newline="") as f:
            count = 0
            for block, ts, tx, sender, to, units, err, _, _ in csv.reader(f):
                count += 1
                if (
                    sender.lower() != addr
                    or err != "0"
                    or not to
                    or to.lower() in {ZERO, addr}
                    or int(units) <= 0
                ):
                    continue
                block, ts = int(block), int(ts)
                if not lo <= block <= hi or not window["t_start"] <= ts <= window["t_end"]:
                    raise ValueError("archived native payment outside checkpoint")
                obj = Credit(
                    1,
                    "changenow",
                    block,
                    ts,
                    hexstr(tx, 64),
                    -1,
                    addr,
                    hexstr(to, 40),
                    "native",
                    int(units),
                    "labelled_hot_wallet",
                )
                if obj.key in seen and seen[obj.key] != obj:
                    raise ValueError("conflicting native transaction copies")
                if obj.key not in seen:
                    out[week_of(ts)].append(obj)
                    seen[obj.key] = obj
            if count != ck["rows"]:
                raise ValueError("archive checkpoint row count mismatch")
    return out, window


def native_coverage(week, window):
    t0, t1 = bounds(week)
    lo, hi = window["t_start"], window["t_end"] + 1
    if max(t0, lo) >= min(t1, hi):
        return {"status": "UNKNOWN", "reason": "outside archived txlist window"}
    return {
        "status": "ARCHIVED_OBSERVATIONS",
        "start": max(t0, lo),
        "end_exclusive": min(t1, hi),
        "entire_week_in_archive_window": lo <= t0 and t1 <= hi,
        "limit": "explorer checkpoints, root transactions only; no independent range manifest",
    }


def infrastructure():
    labels = {}
    with LABELS.open() as f:
        for r in csv.DictReader(f):
            if str(r["chain"]).isdigit():
                labels[(int(r["chain"]), r["address"].lower())] = "service_label"
    # Mechanically observed roles can be more specific than a registry name.
    from .common import CN22, CN_HOT, ETH_POOLS, F2020, POOLS
    from monitoring.phi_monitor.chain import EXCHANGES

    for chain, addrs, kind in [
        (137, CN_HOT, "hot_wallet"),
        (1, ETH_HOT | {DEP}, "hot_wallet"),
        (137, [CN22], "consolidation"),
        (137, [F2020], "commingled_route"),
        (137, POOLS, "pool"),
        (1, ETH_POOLS, "pool"),
        (137, EXCHANGES, "exchange_contract"),
    ]:
        labels.update({(chain, a): kind for a in addrs})
    with (STATE / "recipient_tags.jsonl").open() as f:
        import json

        for line in f:
            r = json.loads(line)
            tags = {t.get("slug", "") for t in r.get("tags", [])}
            if tags & {"binance", "deposit-address", "burn"}:
                labels[(r["chain"], r["address"].lower())] = "custody_or_burn"
    return labels


def historic_cohort():
    path = REPO / "investigations/changenow-polymarket/sources"
    with (path / "state/pm_traders.csv").open() as f:
        rows = list(csv.DictReader(f))
    with (path / "state/pm_pnl2.csv").open() as f:
        incomplete = sum(r["incomplete"].lower() == "true" for r in csv.DictReader(f))
    return {
        "payees": len(read(path / "f2020_recipients.json")),
        "bettor_records": len(rows),
        "distinct_trading_addresses": len({r["account"].lower() for r in rows}),
        "eoa_records": sum(r["account_type"] == "EOA" for r in rows),
        "deposit_wallet_records": sum(r["account_type"] == "DW" for r in rows),
        "incomplete_pnl_records": incomplete,
    }
