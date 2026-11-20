"""Part C and part D of PLAN.md, and EXT_NN of amendment 1. Offline: reads what collect_event.py saved.

    python3 -I -B analyse_timeline.py RAW_DIR STUDY_DIR QUEUE_JSON OUT_DIR

Writes `timeline.json` (per account), `group_exposure.csv` (the group's cumulative cost on "Machado Yes" at each of its
fills), `detectors.json` (first alert on the eight per detector, the confirmation point of the public repricing, the
verdict word of part D) and `ext_nn.json`. Profile fields of the data API (name, pseudonym, bio, images) are never
copied. Wallets other than the eight appear only as counts."""
import collections, csv, gzip, json, os, sqlite3, statistics, sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "monitoring"))
from phi_monitor import ignition  # noqa: E402  (the confirmation rule of the monitor, unchanged)

DATA = os.path.join(REPO, "investigations", "followup-20261113", "sources", "data")
MACHADO = "0x14a3dfeba8b22a32feb0f10763db68bc4d2abeb5bff90e9ae20de53793b35a1d"
W0, ANN = 1760043600, 1760086800          # 2025-10-09 21:00 UTC; announcement 2025-10-10 09:00 UTC (11:00 in Oslo)
DAY = 86400
NN = {"fresh_days": 30, "min_bet": 1000, "mult": 3, "conc": 0.6, "niche": 50000, "alert": 7}   # defaults of the original config.py


class Raw:
    def __init__(self, d):
        self.d = d; self.idx = [json.loads(l) for l in open(os.path.join(d, "index.jsonl"))]

    def all(self, prefix):
        return [(r["key"], json.loads(gzip.open(os.path.join(self.d, r["file"])).read())) for r in self.idx if r["key"].startswith(prefix)]

    def sha(self, prefix):
        return sorted(r["sha256"] for r in self.idx if r["key"].startswith(prefix))


def tape(raw, cid):
    """Every row of every cursor page, once per page. One row is one OrderFilled log (doctor of phi_monitor): two identical
    rows in a page are two fills (one taker matched against several makers at one size and price) and are both kept."""
    out = []
    pages = raw.all(f"trades:{cid}:")
    assert len({k for k, _ in pages}) == len(pages), "a cursor page was stored twice"
    for _, j in pages:
        for r in j.get("data") or []:
            out.append({"tx": r["transaction_hash"], "token": r["token_id"], "wallet": r["proxy_wallet"].lower(), "side": r["side"],
                        "size": float(r["size"]), "price": float(r["price"]), "t": int(r["timestamp"]), "cid": cid})
    # the API gives no log index: trades of one second are ordered by transaction, token, wallet, side, size and price,
    # the same order as the published data/machado_tape.csv
    return sorted(out, key=lambda r: (r["t"], r["tx"], r["token"], r["wallet"], r["side"], str(r["size"]), str(r["price"])))


def nn_score(age_days, cash, mkt_mean, mkt_vol, conc, trades, markets, p=NN):
    """0-10 score of the external rule (amendment 1), with its default thresholds."""
    s = 0
    if age_days is not None:
        s += 2 if age_days < 1 else 1 if age_days < p["fresh_days"] else 0
    if cash > p["min_bet"]:
        s += 3 if mkt_mean > 0 and cash > mkt_mean * p["mult"] else 2 if cash > p["min_bet"] * 10 else 1 if cash > p["min_bet"] * 5 else 0
    s += 2 if conc >= p["conc"] else 1 if conc >= p["conc"] * 0.7 else 0
    if mkt_vol < p["niche"]:
        s += 2 if mkt_vol < p["niche"] / 5 else 1
    s += 1 if trades > 5 and markets < 3 else 0
    return min(s, 10)


def main(raw_dir, study, queue_json, out):
    raw = Raw(raw_dir); os.makedirs(out, exist_ok=True)
    ev = raw.all("gamma:")[0][1]
    mk = {m["conditionId"]: {"title": m.get("groupItemTitle") or m["question"], "yes": json.loads(m["clobTokenIds"])[0], "no": json.loads(m["clobTokenIds"])[1]} for m in ev["markets"]}
    acc = list(csv.DictReader(open(os.path.join(DATA, "nobel_accounts.csv"))))
    fund = list(csv.DictReader(open(os.path.join(DATA, "nobel_funding_transfers.csv"))))
    group = {a["proxy"].lower(): a["handle"] for a in acc}
    tapes = {cid: tape(raw, cid) for cid in {k.split(":")[1] for k, _ in raw.all("trades:")}}
    blocks = {int(k.split(":")[1]): int(j["result"]["timestamp"], 16) for k, j in raw.all("block:")}
    # D. the public repricing: first point of the 10-minute series meeting the phi_monitor rule
    yes = mk[MACHADO]["yes"]
    series = sorted((int(p["t"]), float(p["p"])) for p in raw.all(f"prices:{yes}:10")[0][1]["history"])
    ig = ignition.first_ignition(series, "YES")
    # C. per account
    m_tape = [r for r in tapes[MACHADO] if r["token"] == yes]
    timeline = []
    for a in acc:
        p = a["proxy"].lower()
        pages = raw.all(f"activity:{p}:")
        assert len(pages) == 1 and len((pages[0][1].get("data") if isinstance(pages[0][1], dict) else pages[0][1])) < 500, \
            f"{a['handle']}: history read in more than one page; the end= paging can skip rows of one second"
        rows = sorted((r for r in (pages[0][1].get("data") if isinstance(pages[0][1], dict) else pages[0][1]) if int(r["timestamp"]) < ANN),
                      key=lambda r: int(r["timestamp"]))
        logs = []
        for k, j in raw.all("logs:"):
            if k.split(":")[2].endswith(p[2:]):
                logs += [(blocks.get(int(l["blockNumber"], 16)), int(l["blockNumber"], 16), "0x" + l["topics"][1][-40:], int(l["data"], 16) / 1e6, l["address"].lower()) for l in j["result"]]
        logs.sort(key=lambda x: (x[1], x[0] or 0))
        trades = [r for r in rows if r["type"] == "TRADE"]
        big = [r for r in trades if float(r.get("usdc_size") or 0) >= 1000 and r.get("side") == "BUY"]
        buy_event = sum(float(r["usdc_size"]) for r in trades if r.get("side") == "BUY")
        buy_machado = sum(float(r["usdc_size"]) for r in trades if r.get("side") == "BUY" and r.get("condition_id") == MACHADO)
        f1 = min((f for f in fund if f["to"].lower() == p), key=lambda f: f["utc"])
        first_m = next((r for r in trades if r.get("condition_id") == MACHADO and r.get("side") == "BUY"), None)
        prev = None
        if first_m:
            before = [r for r in m_tape if r["t"] < int(first_m["timestamp"])]
            prev = before[-1] if before else None
        timeline.append({
            "handle": a["handle"], "proxy": p,
            "first_collateral_received": logs[0][0] if logs else None, "first_collateral_block": logs[0][1] if logs else None,
            "first_collateral_from_funder": bool(logs and logs[0][2] == "0xe206961002feebd9edb152eed9b630a351874043"),
            "first_funding_by_key_utc": f1["utc"], "first_funding_block": int(f1["block"]),
            "first_activity": int(rows[0]["timestamp"]) if rows else None, "first_trade": int(trades[0]["timestamp"]) if trades else None,
            "first_trade_market": mk.get(trades[0]["condition_id"], {}).get("title") if trades else None,
            "first_trade_price": trades[0].get("price") if trades else None,
            "first_buy_1000": int(big[0]["timestamp"]) if big else None, "first_buy_1000_price": big[0].get("price") if big else None,
            "first_buy_1000_market": mk.get(big[0]["condition_id"], {}).get("title") if big else None,
            "first_buy_1000_outcome": big[0].get("outcome") if big else None, "first_buy_1000_usd": float(big[0]["usdc_size"]) if big else None,
            "first_trade_usd": float(trades[0]["usdc_size"]) if trades else None,
            "first_machado_buy": int(first_m["timestamp"]) if first_m else None, "first_machado_buy_price": first_m.get("price") if first_m else None,
            "last_print_before_first_machado_buy": prev and {"t": prev["t"], "price": prev["price"]},
            "minutes_funding_to_first_trade": round((int(trades[0]["timestamp"]) - blocks_or_csv(f1, blocks)) / 60, 2) if trades else None,
            "event_buy_cost_before_announcement": round(buy_event, 2), "machado_share_of_event_buying": round(buy_machado / buy_event, 4) if buy_event else None,
            "markets_bought": sorted({mk.get(r["condition_id"], {}).get("title", r["condition_id"]) for r in trades if r.get("side") == "BUY"}),
            "activity_rows_before_announcement": len(rows),
        })
    # the group's cumulative cost on Machado Yes at each of its fills, and the market's cumulative buying
    with open(os.path.join(out, "group_exposure.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["utc", "handle", "side", "shares", "price", "group_cost_cum", "market_buy_cost_since_21utc", "group_share_of_buying"])
        g = mkt = 0.0
        for r in m_tape:
            if r["t"] >= ANN:
                break
            c = r["size"] * r["price"]
            if r["side"] == "BUY" and r["t"] >= W0:
                mkt += c
            if r["wallet"] in group:
                g += c if r["side"] == "BUY" else -c
                w.writerow([r["t"], group[r["wallet"]], r["side"], r["size"], r["price"], round(g, 2), round(mkt, 2), round(g / mkt, 4) if mkt else ""])
    # EXT_NN on the frozen entries of the event during the night (amendment 1)
    wf = sqlite3.connect(f"file:{study}/derived/wallet_features.sqlite?mode=ro&immutable=1", uri=True)
    feat = {r[0]: r[1:] for r in wf.execute("select id, age_h, prior_trades, prior_other_trades, prior_other_markets from wf")}
    ext, skipped = [], collections.Counter()
    with open(os.path.join(study, "derived", "analytic_table.jsonl")) as f:
        for line in f:
            r = json.loads(line); r.pop("win", None); r.pop("closed_ts", None)
            if r["event_id"] != str(ev["id"]) or not (W0 <= r["t"] < ANN):
                continue
            if r["condition_id"] not in tapes:
                skipped["market_without_tape"] += 1; continue
            fe = feat.get(r["id"])
            if not fe or fe[0] is None:
                skipped["no_wallet_view"] += 1; continue
            age_h, pt, pot, pom = fe
            win = [x for x in tapes[r["condition_id"]] if r["t"] - DAY <= x["t"] < r["t"]]
            sizes = [x["size"] * x["price"] for x in win]
            here = (pt or 0) - (pot or 0)          # earlier trades on this market
            conc = (here + 1) / ((pt or 0) + 1)    # lower bound of the largest share of its trades in one market (amendment 1)
            s = nn_score(age_h / 24, r["cash"], statistics.mean(sizes) if sizes else 0, sum(sizes), conc, (pt or 0) + 1, (pom or 0) + 1)
            ext.append({"t": r["t"], "score": s, "flag": s >= NN["alert"], "on_eight": r["address"].lower() in group,
                        "handle": group.get(r["address"].lower()), "market": mk[r["condition_id"]]["title"], "price": r["price"], "cash": r["cash"]})
    ext.sort(key=lambda x: x["t"])
    flagged = [x for x in ext if x["flag"]]
    k = [i for i, x in enumerate(flagged) if x["on_eight"]]
    nn = {"entries_scored": len(ext), "skipped": dict(skipped), "flagged": len(flagged), "flagged_on_eight": len(k),
          "first_on_eight_rank_by_time": k[0] + 1 if k else None, "first_on_eight": flagged[k[0]] if k else None,
          "first_flag": flagged[0] if flagged else None,
          "score_distribution": dict(collections.Counter(x["score"] for x in ext)),
          "eight": [x for x in ext if x["on_eight"]]}
    json.dump(nn, open(os.path.join(out, "ext_nn.json"), "w"), indent=1, sort_keys=True)
    # D. first alert on the eight per detector
    q = json.load(open(queue_json))["classes"]
    det = {f"frozen {k.split(':')[1]}": {"utc": v["first_on_eight_utc"], "price": v["first_on_eight_price"], "rank": v["first_on_eight_rank_by_time"], "alerts_in_night": v["alerts"]}
           for k, v in q.items() if k.startswith("INFO:") and v["first_on_eight_utc"]}
    det["phi_monitor LONELY_THIN (monitoring/tests/test_replay.py)"] = {"utc": 1760050815, "price": None, "rank": None, "alerts_in_night": None}
    if k:
        det["EXT_NN"] = {"utc": flagged[k[0]]["t"], "price": flagged[k[0]]["price"], "rank": k[0] + 1, "alerts_in_night": len(flagged)}
    first = min(det.items(), key=lambda kv: kv[1]["utc"])
    t1 = ig["t1"] if ig else None
    verdict = ("NOT_DETECTED_BEFORE_ANNOUNCEMENT" if first[1]["utc"] >= ANN else
               "DETECTED_BEFORE_PUBLIC_REPRICING" if t1 is not None and first[1]["utc"] < t1 else "DETECTED_AFTER_REPRICING_BEFORE_ANNOUNCEMENT")
    res = {"announcement_utc": ANN, "repricing_rule": "phi_monitor.ignition.first_ignition on the CLOB 10-minute series of Machado Yes",
           "repricing": ig, "first_alert_on_eight": {"detector": first[0], **first[1], "hours_before_announcement": round((ANN - first[1]["utc"]) / 3600, 2),
                                                      "minutes_vs_repricing_confirmation": round((first[1]["utc"] - t1) / 60, 1) if t1 else None},
           "detectors": det, "verdict": verdict, "qualifier": "NOT_A_VALIDATION",
           "sources_sha256": {"prices_10": raw.sha(f"prices:{yes}:10"), "gamma": raw.sha("gamma:")}}
    json.dump(res, open(os.path.join(out, "detectors.json"), "w"), indent=1, sort_keys=True)
    json.dump(timeline, open(os.path.join(out, "timeline.json"), "w"), indent=1, sort_keys=True)
    # figures of the night quoted by the report, from the tape of "Machado Yes"
    t1, p6741 = ig["t1"], next(a["proxy"].lower() for a in acc if a["handle"] == "6741")
    first6741 = min(r["t"] for r in m_tape if r["wallet"] == p6741)
    buy = lambda lo, hi, who: round(sum(r["size"] * r["price"] for r in m_tape if r["side"] == "BUY" and lo <= r["t"] < hi and who(r["wallet"])), 2)
    last_g = max(r["t"] for r in m_tape if r["wallet"] in group and r["t"] < ANN)
    night = {"buy_21_to_confirmation_all": buy(W0, t1, lambda w: True), "buy_21_to_confirmation_6741": buy(W0, t1, lambda w: w == p6741),
             "buy_others_first_6741_fill_to_confirmation": buy(first6741, t1, lambda w: w != p6741),
             "group_gross_buys_before_announcement": buy(0, ANN, lambda w: w in group),
             "market_buys_21_to_last_group_fill": buy(W0, last_g + 1, lambda w: True), "last_group_fill": last_g}
    night["share_6741_to_confirmation"] = round(night["buy_21_to_confirmation_6741"] / night["buy_21_to_confirmation_all"], 4)
    night["group_gross_share"] = round(night["group_gross_buys_before_announcement"] / night["market_buys_21_to_last_group_fill"], 4)
    json.dump(night, open(os.path.join(out, "night_summary.json"), "w"), indent=1, sort_keys=True)
    print(json.dumps({"repricing": ig, "first": res["first_alert_on_eight"], "verdict": verdict, "ext_nn": {k2: nn[k2] for k2 in ("entries_scored", "flagged", "flagged_on_eight", "first_on_eight_rank_by_time", "skipped")}}, indent=1))


def blocks_or_csv(f1, blocks):
    """Block time of the first funding: the header read from the chain, else the time written in the funding table."""
    import datetime as dt
    t = blocks.get(int(f1["block"]))
    return t if t is not None else int(dt.datetime.fromisoformat(f1["utc"].replace("Z", "+00:00")).timestamp())


def _selftest():
    assert nn_score(0.5, 20000, 1000, 1e6, 1.0, 1, 1) == 2 + 3 + 2          # brand new, 20x the mean, all in one market
    assert nn_score(400, 1500, 1000, 1e6, 0.1, 50, 20) == 0
    assert nn_score(0.5, 12000, 5000, 30000, 1.0, 1, 1) == 2 + 2 + 2 + 1     # a niche market under 50,000 but over 10,000
    print("analyse_timeline selftest ok")


if __name__ == "__main__":
    _selftest() if sys.argv[1:] == ["selftest"] else main(*sys.argv[1:5])
