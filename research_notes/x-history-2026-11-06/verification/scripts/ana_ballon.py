"""Ballon d'Or 2026 tests Q1-Q4 of ANALYSIS_PLAN.md, from the archived event tapes (both sides of each fill).

Reads:  RAW/tapes/<event>/p*.json.gz, the repository market list, data/focus_wallets.csv
Writes: data/ballon_results.json, data/ballon_focus_positions.csv, data/ballon_event_windows.csv,
        data/ballon_followers_e1.csv
Money is Decimal from the API's decimal text. Tape sizes are rounded to 0.01 share by the API: exact amounts
come from activity rows and receipts, not from here.
"""
import csv, gzip, json, os, sys
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
REPO = HERE.parents[2]
RAW = Path(os.environ.get("XLEADS_RAW", Path.home() / "Projects/Polymarket-x-leads-raw-20261106/raw"))
MARKETS = REPO / "investigations/ballon-dor-census/sources/derived/markets.csv"


def ts(s):
    return int(datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).timestamp())


def utc(t):
    return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


E1, E2, E3 = ts("2026-10-16 17:38:26"), ts("2026-10-21 14:25:48"), ts("2026-10-23 15:17:49")
EVENTS = {"E1_cypya": E1, "E2_jydyjyd": E2, "E3_upside": E3}
P23_OPEN = ts("2026-10-19 14:47:34")
INFORMATIVE = Decimal("0.60")
MIN_FACT = Decimal(100)
WINDOW = 6 * 3600

FACTS = {  # fact: (condition id prefix, outcome index) as fixed in ANALYSIS_PLAN.md
    "F_W": ("0x12dc2b6172", 0), "F_MY": ("0xa3cf5e6b27", 0), "F_RM": ("0xc41091c021", 0), "F_KY": ("0xbf812967da", 0),
    "F_T2M": ("0x080e4da516", 0), "F_T3Y": ("0xcfdf93623a", 0), "F_T3M": ("0x61c85ceb5e", 0),
    "F_T5R": ("0x143b8a8710", 0), "F_T5M": ("0x40ff65a753", 0), "F_P2": ("0xc09dcd5b04", 0),
    "F_P3": ("0x1864c9203c", 0), "F_P4": ("0x2e8512d2ef", 0), "F_P5": ("0x5d55f32e24", 0),
    "F_MM": ("0x34765d781c", 0), "F_YM": ("0x715d645bb3", 0),
}
EVENT_IDS = ["48361", "811116", "811117", "1105185", "1105364", "1105369", "1105379", "1105380", "1105381", "1189431",
             "1218178", "1218179", "1225367", "1225368", "1226675", "1226676"]


def load_markets():
    rows = list(csv.DictReader(open(MARKETS)))
    fact_token, fact_start, token_fact = {}, {}, {}
    for f, (pref, oi) in FACTS.items():
        m = [r for r in rows if r["condition_id"].startswith(pref)]
        assert len(m) == 1, (f, len(m))
        tok = m[0]["tokens"].split("|")[oi]
        fact_token[f] = tok
        token_fact[tok] = f
        fact_start[f] = int(datetime.fromisoformat(m[0]["start"].replace("Z", "+00:00")).timestamp())
    return fact_token, fact_start, token_fact


def load_tapes():
    rows, seen, dup, done = [], set(), 0, {}
    for eid in EVENT_IDS:
        d = RAW / "tapes" / eid
        done[eid] = json.loads((d / "DONE.json").read_text())
        for p in sorted(d.glob("p*.json.gz")):
            for r in json.loads(gzip.decompress(p.read_bytes()), parse_float=Decimal)["data"]:
                k = (r["transaction_hash"], r["proxy_wallet"], r["token_id"], r["side"], r["size"], r["price"], r["timestamp"])
                if k in seen:
                    dup += 1  # same wallet, token, side, size and price in one transaction: kept, counted
                seen.add(k)
                rows.append({"ts": int(r["timestamp"]), "w": r["proxy_wallet"].lower(), "side": r["side"],
                             "token": r["token_id"], "cond": r["condition_id"], "size": Decimal(r["size"]),
                             "price": Decimal(r["price"]), "tx": r["transaction_hash"], "eid": eid, "name": r.get("name") or ""})
    rows.sort(key=lambda r: r["ts"])
    return rows, dup, done


def main():
    fact_token, fact_start, token_fact = load_markets()
    rows, dup, done = load_tapes()
    focus = list(csv.DictReader(open(HERE / "data/focus_wallets.csv")))
    fw = {f["proxy"]: f["label"] for f in focus if f["case"].startswith("ballon")}
    out = {"tape_rows": len(rows), "same_key_rows_in_one_tx": dup, "tape_termination": done,
           "events_utc": {k: utc(v) for k, v in EVENTS.items()}, "fact_start_utc": {f: utc(t) for f, t in fact_start.items()}}

    # check: no fill on a fact token before its market's listing time
    early = [(token_fact[r["token"]], utc(r["ts"])) for r in rows if r["token"] in token_fact and r["ts"] < fact_start[token_fact[r["token"]]] - 60]
    out["fills_before_listing"] = len(early)

    # Q1: net shares per fact token at E1 for every focus wallet, plus all tokens with a nonzero position
    net_e1 = defaultdict(Decimal)
    for r in rows:
        if r["ts"] >= E1:
            break
        if r["w"] in fw:
            net_e1[(r["w"], r["token"])] += r["size"] if r["side"] == "BUY" else -r["size"]
    with open(HERE / "data/ballon_focus_positions.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["label", "proxy", "fact", "net_shares_at_E1"])
        for (wal, tok), v in sorted(net_e1.items(), key=lambda kv: (fw[kv[0][0]], token_fact.get(kv[0][1], "zz"))):
            if tok in token_fact and v != 0:
                w.writerow([fw[wal], wal, token_fact[tok], str(v)])

    # Q2: facts supported by informative purchases (price <= 0.60, >= 100 USDC per fact) before each cutoff
    cutoffs = {"before_E1": E1, "before_exact_places_19oct": P23_OPEN, "before_E3": E3}
    q2 = {}
    for cname, cut in cutoffs.items():
        per = defaultdict(lambda: defaultdict(Decimal))
        spend = defaultdict(Decimal)
        for r in rows:
            if r["ts"] >= cut:
                break
            if r["side"] != "BUY":
                continue
            spend[r["w"]] += r["size"] * r["price"]
            f = token_fact.get(r["token"])
            if f and r["price"] <= INFORMATIVE:
                per[r["w"]][f] += r["size"] * r["price"]
        count = {wal: sum(1 for v in per[wal].values() if v >= MIN_FACT) for wal in spend}
        controls = [count[wal] for wal in spend if wal not in fw and spend[wal] >= MIN_FACT]
        res = {"controls_n": len(controls), "controls_dist": {str(k): controls.count(k) for k in sorted(set(controls))}, "focus": {}}
        for wal, lab in fw.items():
            c = count.get(wal, 0)
            res["focus"][lab] = {"facts": c, "fact_list": sorted(f for f, v in per[wal].items() if v >= MIN_FACT),
                                 "spend_usdc": str(round(spend.get(wal, Decimal(0)), 2)),
                                 "controls_at_or_above": sum(1 for x in controls if x >= c) if c else None}
        q2[cname] = res
    out["Q2"] = q2

    # Q3: buy notional and distinct buyers on each listed fact token in [E, E+6h) against same-clock placebo days
    day = 86400
    q3, lines = {}, []
    by_token = defaultdict(list)
    for r in rows:
        if r["side"] == "BUY" and r["token"] in token_fact:
            by_token[r["token"]].append(r)
    first_family_buy = {}
    for r in rows:
        if r["side"] == "BUY":
            first_family_buy.setdefault(r["w"], r["ts"])
    for ename, et in EVENTS.items():
        q3[ename] = {}
        for f, tok in fact_token.items():
            if fact_start[f] > et:
                continue
            def window(t0):
                rs = [r for r in by_token[tok] if t0 <= r["ts"] < t0 + WINDOW]
                return (sum((r["size"] * r["price"] for r in rs), Decimal(0)), len({r["w"] for r in rs}),
                        len({r["w"] for r in rs if t0 <= first_family_buy[r["w"]] < t0 + WINDOW}))
            ev = window(et)
            plac = []
            for k in range(-14, 15):
                t0 = et + k * day
                if k == 0 or t0 < fact_start[f] or t0 < ts("2026-10-12 00:00:00") or t0 + WINDOW > ts("2026-10-26 00:00:00"):
                    continue
                plac.append(window(t0))
            rank = 1 + sum(1 for p in plac if p[0] > ev[0])
            q3[ename][f] = {"notional": str(round(ev[0], 2)), "buyers": ev[1], "new_family_buyers": ev[2],
                            "placebo_days": len(plac), "rank_by_notional": rank,
                            "placebo_notional_max": str(round(max((p[0] for p in plac), default=Decimal(0)), 2)),
                            "placebo_notional_median": str(round(sorted(p[0] for p in plac)[len(plac) // 2], 2)) if plac else None}
            lines.append([ename, f, q3[ename][f]["notional"], ev[1], ev[2], len(plac), rank,
                          q3[ename][f]["placebo_notional_median"], q3[ename][f]["placebo_notional_max"]])
    out["Q3"] = q3
    with open(HERE / "data/ballon_event_windows.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["event", "fact", "buy_notional_6h", "buyers", "first_family_buyers", "placebo_days", "rank_of_event_among_days",
                    "placebo_median", "placebo_max"])
        w.writerows(lines)

    # buyers of ranking facts in the 24 h after E1: who, how much, first family buy, in the focus set or not
    fol = defaultdict(lambda: [Decimal(0), set(), None])
    for r in rows:
        if E1 <= r["ts"] < E1 + 86400 and r["side"] == "BUY" and r["token"] in token_fact:
            x = fol[r["w"]]
            x[0] += r["size"] * r["price"]; x[1].add(token_fact[r["token"]]); x[2] = x[2] or r["ts"]
    with open(HERE / "data/ballon_followers_e1.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["proxy", "focus_label", "fact_buy_usdc_24h", "facts", "first_buy_after_E1_utc", "first_family_buy_utc"])
        for wal, (v, fs, t) in sorted(fol.items(), key=lambda kv: -kv[1][0]):
            w.writerow([wal, fw.get(wal, ""), str(round(v, 2)), "|".join(sorted(fs)), utc(t), utc(first_family_buy[wal])])

    # Q4: split of each focus wallet's fact purchases between periods
    q4 = {}
    for wal, lab in fw.items():
        s = {"before_E1": Decimal(0), "E1_to_E3": Decimal(0), "after_E3": Decimal(0)}
        for r in rows:
            if r["w"] == wal and r["side"] == "BUY" and r["token"] in token_fact:
                k = "before_E1" if r["ts"] < E1 else ("E1_to_E3" if r["ts"] < E3 else "after_E3")
                s[k] += r["size"] * r["price"]
        q4[lab] = {k: str(round(v, 2)) for k, v in s.items()}
    out["Q4"] = q4
    (HERE / "data/ballon_results.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({k: out[k] for k in ("tape_rows", "same_key_rows_in_one_tx", "fills_before_listing")}))


if __name__ == "__main__":
    main()
