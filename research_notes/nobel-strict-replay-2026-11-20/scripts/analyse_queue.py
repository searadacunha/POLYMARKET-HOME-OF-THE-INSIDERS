"""Part B of PLAN.md (and EXT_PC of amendment 1): the queue of alerts an analyst would have received during the night.

    python3 -I analyse_queue.py STUDY_DIR OUT_JSON [STRICT_C4_JSON]

Reads the frozen study read-only: `derived/analytic_table.jsonl` (class flags and alert moments) and
`derived/wallet_features.sqlite` (point-in-time age and markets traded, for EXT_PC). The outcome field `win` and the
close time are deleted from every row as it is read: nothing below can use them. The identity of the eight accounts
is used only to count how many alerts fall on them."""
import collections, csv, json, os, sqlite3, sys

W0, W1 = 1760043600, 1760086800          # 2025-10-09 21:00:00 and 2025-10-10 09:00:00 UTC (announcement)
DAY = 86400
CLASSES = ["c1", "c2", "c3", "c4", "c5", "c6", "c7", "r1", "m1", "m2", "b1", "b2", "b3", "ext_pc"]
HERE = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS = os.path.join(HERE, "..", "..", "..", "investigations", "followup-20261113", "sources", "data", "nobel_accounts.csv")


def eight():
    with open(ACCOUNTS) as f:
        return {r["proxy"].lower(): r["handle"] for r in csv.DictReader(f)}


def ext_pc(age_h, other_markets, price, cash):
    """Amendment 1: age <= 14 days, <= 15 other markets before, price <= 0.30, entry >= 1,000 USD (all four)."""
    if age_h is None or other_markets is None:
        return None
    return int(age_h <= 14 * 24 and other_markets <= 15 and price <= 0.30 and cash >= 1000)


def alerts(study, strict_c4=None):
    wf = sqlite3.connect(f"file:{study}/derived/wallet_features.sqlite?mode=ro&immutable=1", uri=True)
    feat = {r[0]: r[1:] for r in wf.execute("select id, age_h, prior_other_markets from wf")}
    out, unknown_pc = [], 0
    with open(os.path.join(study, "derived", "analytic_table.jsonl")) as f:
        for line in f:
            r = json.loads(line)
            for k in ("win", "closed_ts"):            # the outcome is never read
                r.pop(k, None)
            base = {"id": r["id"], "set": r["set"], "grp": r["grp"], "event": r["event_id"], "wallet": r["address"].lower(),
                    "cash": r["cash"], "documented": r.get("documented", 0)}
            for c in CLASSES:
                if c == "c7":
                    if r.get("c7_t") is not None:
                        out.append(dict(base, cls=c, t=r["c7_t"], price=r["c7_p"]))
                    continue
                if c == "ext_pc":
                    a, m = feat.get(r["id"], (None, None))
                    v = ext_pc(a, m, r["price"], r["cash"]) if r.get("evaluated") else None
                    unknown_pc += v is None and W0 - 8 * DAY <= r["t"] < W1
                    if v:
                        out.append(dict(base, cls=c, t=r["t"], price=r["price"]))
                    continue
                if r.get(c):
                    out.append(dict(base, cls=c, t=r["t"], price=r["price"]))
            s = (strict_c4 or {}).get(str(r["id"])) or {}
            for c in ("c4", "c5"):                       # part A: the same classes with the payer state read at the block
                if s.get(c):
                    out.append(dict(base, cls=c + "_strict", t=r["t"], price=r["price"]))
    return out, unknown_pc


def summarise(rows, group):
    res = {}
    for grp in ("INFO", "PUBLIC_PROCESS"):
        for cls in sorted({r["cls"] for r in rows}):
            a = sorted((r for r in rows if r["cls"] == cls and r["grp"] == grp and W0 <= r["t"] < W1), key=lambda r: (r["t"], r["id"]))
            k = [i for i, r in enumerate(a) if r["wallet"] in group]
            by_size = sorted(a, key=lambda r: -r["cash"])
            ks = [i for i, r in enumerate(by_size) if r["wallet"] in group]
            load = []
            for d in range(7, 0, -1):
                lo, hi = W0 - d * DAY, W0 - (d - 1) * DAY
                load.append(sum(1 for r in rows if r["cls"] == cls and r["grp"] == grp and lo <= r["t"] < hi))
            res[f"{grp}:{cls}"] = {
                "alerts": len(a), "wallets": len({r["wallet"] for r in a}), "events": len({r["event"] for r in a}),
                "on_the_eight": len(k), "eight_wallets": sorted({group[a[i]["wallet"]] for i in k}),
                "first_on_eight_rank_by_time": (k[0] + 1) if k else None,
                "first_on_eight_utc": a[k[0]]["t"] if k else None, "first_on_eight_price": a[k[0]]["price"] if k else None,
                "random_order_expected_rank": round((len(a) + 1) / (len(k) + 1), 1) if a else None,
                "largest_on_eight_rank_by_size": (ks[0] + 1) if ks else None,
                "first_alert_utc": a[0]["t"] if a else None,
                "per_day_7_days_before": load,
                "same_12_hours_the_night_before": sum(1 for r in rows if r["cls"] == cls and r["grp"] == grp and W0 - DAY <= r["t"] < W1 - DAY),
                "by_set": dict(collections.Counter(r["set"] for r in a)),
            }
    return res


def main(study, out_path, strict_path=None):
    group = eight()
    strict = json.load(open(strict_path)) if strict_path else None
    rows, unknown_pc = alerts(study, strict)
    res = {"window_utc": [W0, W1], "classes": summarise(rows, group), "ext_pc_entries_without_wallet_view_in_8_days": unknown_pc,
           "inputs": {"analytic_table": "derived/analytic_table.jsonl", "wallet_features": "derived/wallet_features.sqlite",
                      "strict_c4": strict_path and os.path.basename(strict_path)}}
    json.dump(res, open(out_path, "w"), indent=1, sort_keys=True)
    for k, v in res["classes"].items():
        if v["alerts"]:
            print(f"{k:24s} N={v['alerts']:5d} wallets={v['wallets']:5d} events={v['events']:4d} on8={v['on_the_eight']} "
                  f"rank1={v['first_on_eight_rank_by_time']} exp={v['random_order_expected_rank']} load7d={v['per_day_7_days_before']}")


def _selftest():
    assert ext_pc(10, 0, 0.05, 2000) == 1 and ext_pc(400, 0, 0.05, 2000) == 0 and ext_pc(10, 16, 0.05, 2000) == 0
    assert ext_pc(10, 0, 0.31, 2000) == 0 and ext_pc(None, 0, 0.1, 2000) is None
    g = {"0xa": "A"}
    rows = [{"id": 1, "set": "DISCOVERY", "grp": "INFO", "event": "e", "wallet": "0xb", "cash": 5000, "cls": "c1", "t": W0 + 10, "price": .1},
            {"id": 2, "set": "DISCOVERY", "grp": "INFO", "event": "e", "wallet": "0xa", "cash": 9000, "cls": "c1", "t": W0 + 20, "price": .2},
            {"id": 3, "set": "DISCOVERY", "grp": "INFO", "event": "e", "wallet": "0xc", "cash": 100, "cls": "c1", "t": W0 - 3600, "price": .2}]
    s = summarise(rows, g)["INFO:c1"]
    assert (s["alerts"], s["on_the_eight"], s["first_on_eight_rank_by_time"], s["largest_on_eight_rank_by_size"]) == (2, 1, 2, 1), s
    assert s["per_day_7_days_before"][-1] == 1 and s["random_order_expected_rank"] == 1.5
    print("analyse_queue selftest ok")


if __name__ == "__main__":
    _selftest() if sys.argv[1:] == ["selftest"] else main(*sys.argv[1:4])
