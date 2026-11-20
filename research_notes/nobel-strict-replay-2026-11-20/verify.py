"""Offline check of this note: recomputes part C from the published inputs and checks parts A, B and D for consistency.

    python3 -I research_notes/nobel-strict-replay-2026-11-20/verify.py

No network and no file of the frozen study is needed (parts A and B were computed from it on the machine that holds it,
see README.md; their outputs are checked here for internal arithmetic). Exit code 0 when every check passes."""
import csv, hashlib, json, os, sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "monitoring")); sys.path.insert(0, os.path.join(HERE, "scripts"))
from phi_monitor import ignition          # noqa: E402
import analyse_timeline as AT             # noqa: E402
import analyse_queue as AQ                # noqa: E402

D = os.path.join(HERE, "data")
SRC = os.path.join(REPO, "investigations", "followup-20261113", "sources", "data")
FUNDER = "0xe206961002feebd9edb152eed9b630a351874043"
ANN = 1760086800
ok, bad = [], []


def check(name, cond):
    (ok if cond else bad).append(name)


def j(name):
    with open(os.path.join(D, name)) as f:
        return json.load(f)


def rows(path):
    with open(path) as f:
        return list(csv.DictReader(f))


# integrity of the published files
with open(os.path.join(HERE, "SHA256SUMS")) as f:
    for line in f:
        h, name = line.split()
        with open(os.path.join(HERE, name), "rb") as g:
            check(f"sha256 {name}", hashlib.sha256(g.read()).hexdigest() == h)

# part A: strict C4 and C5
s, flags = j("strict_summary.json"), j("strict_c4.json")
check("A links add up", s["links_strict"] == s["links_frozen"] + s["links_added"] - s["links_removed"])
check("A added links add up by reason", sum(s["added_by_reason"].values()) == s["links_added"])
check("A no link removed by reading the state at the block", s["links_removed"] == 0)
check("A no unresolved read", not s["unresolved_reads"])
check("A strict c4 entries = flags", s["c4_entries_strict"] == sum(v["c4"] for v in flags.values()) == sum(s["c4_events_strict"].values()))
check("A frozen c4 entries = 8 = flags", s["c4_entries_frozen"] == 8 == sum(v["frozen_c4"] for v in flags.values()))
check("A frozen c5 entries", s["c5_entries_frozen"] == sum(v["frozen_c5"] for v in flags.values()))
check("A every frozen c4 stays c4", all(v["c4"] for v in flags.values() if v["frozen_c4"]))
check("A described events match", {e["event_id"]: e["alert_entries"] for e in s["c4_events_described"]} == s["c4_events_strict"])
check("A Nobel event keeps its 8 alerts", s["c4_events_strict"].get("31406") == 8)
check("A decomposition is a subset", s["decomposition"]["block_state_today_tags"]["c4_entries"] <= s["c4_entries_strict"]
      and set(s["decomposition"]["block_state_today_tags"]["c4_events"]) <= set(s["c4_events_strict"]))
fed = next(e for e in s["c4_events_described"] if e["event_id"] == "45883")
check("A the Fed group's keys are all tagged Relay solvers today", all("Relay" in (r["public_tags_today"] or []) for r in fed["roots_today"].values()))

# part B: the queue of the night
q = j("queue.json")["classes"]
for k, v in q.items():
    if not v["alerts"]:
        continue
    check(f"B {k} on the eight <= alerts", v["on_the_eight"] <= v["alerts"])
    check(f"B {k} random rank", v["random_order_expected_rank"] == round((v["alerts"] + 1) / (v["on_the_eight"] + 1), 1))
    if v["first_on_eight_rank_by_time"]:
        check(f"B {k} rank within the queue", 1 <= v["first_on_eight_rank_by_time"] <= v["alerts"])
check("B strict c4 = frozen c4 on the night", q["INFO:c4"]["alerts"] == q["INFO:c4_strict"]["alerts"] == q["INFO:c4"]["on_the_eight"] == 8)
check("B c4 silent the seven days before", q["INFO:c4"]["per_day_7_days_before"] == [0] * 7 == q["INFO:c4_strict"]["per_day_7_days_before"])
AQ._selftest(); AT._selftest()

# part C recomputed from the published inputs
acc = rows(os.path.join(SRC, "nobel_accounts.csv")); group = {a["proxy"].lower(): a["handle"] for a in acc}
fund = rows(os.path.join(SRC, "nobel_funding_transfers.csv"))
tape = rows(os.path.join(D, "machado_tape.csv"))
act = rows(os.path.join(D, "accounts_activity.csv")); inflow = rows(os.path.join(D, "accounts_inflows.csv"))
tl = {t["handle"]: t for t in j("timeline.json")}
series = [tuple(x) for x in j("machado_yes_prices_10min.json")["history"]]
det = j("detectors.json")
check("C repricing point recomputed", ignition.first_ignition(sorted(series), "YES") == det["repricing"])
g, mkt, exp = 0.0, 0.0, []
for r in tape:
    t = int(r["t"])
    if r["outcome"] != "Yes" or t >= ANN:
        continue
    c = float(r["shares"]) * float(r["price"])
    if r["side"] == "BUY" and t >= AT.W0:
        mkt += c
    if r["wallet"] in group:
        g += c if r["side"] == "BUY" else -c
        exp.append((str(t), group[r["wallet"]], r["side"], round(g, 2), round(mkt, 2)))
pub = [(r["utc"], r["handle"], r["side"], float(r["group_cost_cum"]), float(r["market_buy_cost_since_21utc"])) for r in rows(os.path.join(D, "group_exposure.csv"))]
check("C group exposure recomputed", [(a, b, c, round(d, 2), round(e, 2)) for a, b, c, d, e in pub] == exp)
for h, t in tl.items():
    mine = sorted((r for r in act if r["handle"] == h), key=lambda r: int(r["t"]))
    trades = [r for r in mine if r["type"] == "TRADE"]
    big = [r for r in trades if r["side"] == "BUY" and float(r["usdc"] or 0) >= 1000]
    mach = [r for r in trades if r["side"] == "BUY" and r["market"] == "María Corina Machado"]
    check(f"C {h} first trade", int(trades[0]["t"]) == t["first_trade"])
    check(f"C {h} first buy of 1,000 USD", int(big[0]["t"]) == t["first_buy_1000"] and big[0]["market"].strip() == (t["first_buy_1000_market"] or "").strip())
    check(f"C {h} first Machado buy", int(mach[0]["t"]) == t["first_machado_buy"])
    buy = sum(float(r["usdc"]) for r in trades if r["side"] == "BUY")
    check(f"C {h} Machado share", round(sum(float(r["usdc"]) for r in mach) / buy, 4) == t["machado_share_of_event_buying"])
    ins = sorted((r for r in inflow if r["handle"] == h), key=lambda r: (int(r["block"]), int(r["log_index"])))
    check(f"C {h} first collateral from the funder", ins[0]["from"] == FUNDER and int(ins[0]["block"]) == t["first_collateral_block"] == t["first_funding_block"])
    f1 = min((f for f in fund if f["handle"] == h), key=lambda f: f["utc"])
    check(f"C {h} funding to first trade", round((t["first_trade"] - int(ins[0]["t"])) / 60, 2) == t["minutes_funding_to_first_trade"] and int(f1["block"]) == int(ins[0]["block"]))
    before = [r for r in tape if r["outcome"] == "Yes" and int(r["t"]) < t["first_machado_buy"]]
    check(f"C {h} last print before its first Machado buy", before and float(before[-1]["price"]) == t["last_print_before_first_machado_buy"]["price"])

import datetime as _dt
hms = lambda t: _dt.datetime.fromtimestamp(t, _dt.timezone.utc).strftime("%H:%M:%S")
with open(os.path.join(HERE, "REPORT.md")) as f:
    table = {l.split("|")[1].strip(): l for l in f if l.startswith("| ") and l.split("|")[1].strip() in tl}
for h, t in tl.items():
    line = table.get(h, "")
    check(f"report row {h}", f"{hms(t['first_trade'])}, {t['minutes_funding_to_first_trade']:.1f} min" in line
          and f"last print {t['last_print_before_first_machado_buy']['price']:.3f}" in line and hms(t["first_buy_1000"]) in line
          and f"{t['machado_share_of_event_buying']:.2f} |" in line)

# part D: the verdict follows from the numbers
first = min(det["detectors"].values(), key=lambda v: v["utc"])
check("D first alert is the earliest detector", first["utc"] == det["first_alert_on_eight"]["utc"])
check("D hours before the announcement", round((ANN - first["utc"]) / 3600, 2) == det["first_alert_on_eight"]["hours_before_announcement"])
word = ("NOT_DETECTED_BEFORE_ANNOUNCEMENT" if first["utc"] >= ANN else
        "DETECTED_BEFORE_PUBLIC_REPRICING" if first["utc"] < det["repricing"]["t1"] else "DETECTED_AFTER_REPRICING_BEFORE_ANNOUNCEMENT")
check("D verdict word", det["verdict"] == word and det["qualifier"] == "NOT_A_VALIDATION")
nn = j("ext_nn.json")
check("D EXT_NN counts", nn["flagged"] == sum(n for sc, n in nn["score_distribution"].items() if int(sc) >= 7) and nn["flagged_on_eight"] <= nn["flagged"])

# the report cites these values
with open(os.path.join(HERE, "REPORT.md")) as f:
    rep = f.read()
ce = s["code_at_end_of_payment_block"]
check("A code at the end of the block adds up", ce["pairs"] == ce["delegated_7702"] + ce["deployed"] + ce["still_no_code"])
check("A no read left in error", s["reads_left_in_error"] == 0)
fmt = lambda n: f"{n:,}"
cites = {"first alert": "22:45:07", "repricing": "23:00:15", "group alert": "00:55:11",
         "C1 queue": f"{q['INFO:c1']['alerts']} alerts", "strict C4": f"{s['c4_entries_strict']} alert entries",
         "links added": fmt(s["links_added"]), "delegated in the block": fmt(ce["delegated_7702"]), "archive reads": fmt(s["archive_reads"]),
         "Fed keys": fmt(min(r["sent_transactions_today"] for r in fed["roots_today"].values())),
         "unread keys": fmt(s["pass_through_keys_unread"]), "unread pairs": fmt(s["pass_through_at_block_hops_unread"])}
for name, text in cites.items():
    check(f"report cites {name} ({text})", text in rep)

print(f"{len(ok)} checks passed, {len(bad)} failed")
for b in bad:
    print("FAILED:", b)
sys.exit(1 if bad else 0)
