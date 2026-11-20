"""Offline check of this note: renders its tables from data/ and compares them with REPORT.md, recomputes part C from
the published inputs, and checks parts A, B and D for consistency and every figure the text quotes.

    python3 -I research_notes/nobel-strict-replay-2026-11-20/verify.py            # check (CI)
    python3 -I research_notes/nobel-strict-replay-2026-11-20/verify.py --write    # render the tables into REPORT.md

No network and no file of the frozen study is needed (parts A and B were computed from it on the machine that holds it,
see README.md). Exit code 0 when every check passes."""
import csv, datetime as dt, hashlib, json, os, sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "monitoring")); sys.path.insert(0, os.path.join(HERE, "scripts"))
from phi_monitor import ignition          # noqa: E402
import analyse_queue as AQ                # noqa: E402
import analyse_timeline as AT             # noqa: E402

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


hms = lambda t: dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%H:%M:%S")
ymdhm = lambda t: dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%Y-%m-%d %H:%M")
num = lambda x: f"{x:,}"
usd = lambda x: f"{x:,.2f}"
p3 = lambda x: f"{x:.3f}"
s, flags, q = j("strict_summary.json"), j("strict_c4.json"), j("queue.json")["classes"]
tl = {t["handle"]: t for t in j("timeline.json")}
det, nn, night, titles = j("detectors.json"), j("ext_nn.json"), j("night_summary.json"), j("c4_event_titles.json")
ORDER = ["6741", "fmaduro", "trumpdeservesit", "striketheboats", "aenews0", "madurowilllose", "pinkuniforms", "dirtycup"]


def t_accounts():
    out = ["| Account | Funded by the key | First trade | First buy of 1,000 USD or more | First \"Machado Yes\" buy, last print before it | Share of its event buying on Machado |",
           "|---|---|---|---|---|---|"]
    for h in ORDER:
        t = tl[h]
        mkt = (t["first_buy_1000_market"] or "").strip()
        big = (f"{hms(t['first_buy_1000'])} at {p3(t['first_buy_1000_price'])}" if mkt == "María Corina Machado"
               else f"{hms(t['first_buy_1000'])}, {mkt} \"{t['first_buy_1000_outcome']}\" at {p3(t['first_buy_1000_price'])}")
        out.append(f"| {h} | {t['first_funding_by_key_utc'][11:19]} | {hms(t['first_trade'])}, {t['minutes_funding_to_first_trade']:.1f} min | {big} | "
                   f"{hms(t['first_machado_buy'])} at {p3(t['first_machado_buy_price'])}, last print {p3(t['last_print_before_first_machado_buy']['price'])} | "
                   f"{t['machado_share_of_event_buying']:.2f} |")
    return "\n".join(out)


NAMES = [("frozen c1", "`C1` fresh funded bet (frozen study)"), ("frozen r1", "`R1` S_FRESH replication on entries (frozen)"),
         ("frozen ext_pc", "`EXT_PC`, four-signal flag of an external project, re-implemented (amendment 1)"),
         ("frozen c7", "`C7` heavy newcomer (frozen)"), ("phi_monitor LONELY_THIN (monitoring/tests/test_replay.py)", "`LONELY_THIN` (`phi_monitor`, `monitoring/tests/test_replay.py`)"),
         ("frozen c4", "`C4` cofunded group (frozen)"), ("frozen c4_strict", "`C4` cofunded group, payer state at the block (part A)"),
         ("frozen b2", "`B2` buying after a move (baseline)"), ("frozen b1", "`B1` size of 10,000 USD or more (baseline)")]


def t_detectors():
    out = ["| Detector | First alert on the eight | Price | Rank in the night's queue of that detector |", "|---|---|---|---|"]
    for key, name in NAMES:
        v = det["detectors"][key]
        out.append(f"| {name} | {hms(v['utc'])} | {'' if v['price'] is None else p3(v['price'])} | "
                   f"{'' if v['rank'] is None else str(v['rank']) + ' of ' + str(v['alerts_in_night'])} |")
    return "\n".join(out)


def t_partA():
    tags = s["decomposition"]["block_state_today_tags"]
    return "\n".join(["| | Frozen study | At the block, tags not used | At the block, today's tags kept |", "|---|---:|---:|---:|",
                      f"| Funding links | {num(s['links_frozen'])} | {num(s['links_strict'])} | {num(tags['links'])} |",
                      f"| `C4` alert entries | {s['c4_entries_frozen']} | {s['c4_entries_strict']} | {tags['c4_entries']} |",
                      f"| `C4` events | 1 | {len(s['c4_events_strict'])} | {len(tags['c4_events'])} |",
                      f"| `C5` alert entries | {s['c5_entries_frozen']} | {s['c5_entries_strict']} | {tags['c5_entries']} |"])


def keys_text(e):
    rs = list(e["roots_today"].values())
    if "documented funder" in e["roots_today"]:
        return f"the documented funder, {num(rs[0]['sent_transactions_today'])} transactions sent"
    if all(r["public_tags_today"] and any("Relay: Solver" in t for t in r["public_tags_today"]) for r in rs):
        n = [r["sent_transactions_today"] for r in rs]
        return f"{len(rs)} keys tagged \"Relay: Solver\", {num(min(n))} to {num(max(n))} transactions sent"
    r = rs[0]
    what = "delegated through EIP-7702 today" if r["eip7702_delegation_today"] else ("tagged" if r["public_tags_today"] else "no tag")
    return f"one key, {what}, {num(r['sent_transactions_today'])} transactions sent"


def t_events():
    out = ["| Event | Alert entries | Wallets | First alert | Funding keys as read today (context only, never used by the class) |", "|---|---:|---:|---|---|"]
    for e in s["c4_events_described"]:
        out.append(f"| {titles[e['event_id']]['title']} | {e['alert_entries']} | {e['wallets']} | {ymdhm(e['alerts'][0]['t'])} | {keys_text(e)} |")
    return "\n".join(out)


TABLES = {"accounts": t_accounts, "detectors": t_detectors, "partA": t_partA, "events": t_events}
path = os.path.join(HERE, "REPORT.md")
with open(path) as f:
    rep = f.read()
if "--write" in sys.argv:
    for name, fn in TABLES.items():
        a, b = rep.index(f"<!-- table:{name} -->") + len(f"<!-- table:{name} -->"), rep.index(f"<!-- /table:{name} -->")
        rep = rep[:a] + "\n" + fn() + "\n" + rep[b:]
    with open(path, "w") as f:
        f.write(rep)
    print("tables written"); sys.exit(0)
for name, fn in TABLES.items():
    a, b = rep.index(f"<!-- table:{name} -->") + len(f"<!-- table:{name} -->"), rep.index(f"<!-- /table:{name} -->")
    check(f"table {name} is the rendering of data/", rep[a:b] == "\n" + fn() + "\n")

# integrity of the published files (scripts and this file included)
with open(os.path.join(HERE, "SHA256SUMS")) as f:
    listed = [l.split() for l in f if l.strip()]
for h, name in listed:
    with open(os.path.join(HERE, name), "rb") as g:
        check(f"sha256 {name}", hashlib.sha256(g.read()).hexdigest() == h)
check("checksums cover the scripts and verify.py", {"verify.py"} | {f"scripts/{n}" for n in os.listdir(os.path.join(HERE, "scripts")) if n.endswith(".py")}
      <= {n for _, n in listed})

# part A
check("A links add up", s["links_strict"] == s["links_frozen"] + s["links_added"] - s["links_removed"])
check("A added links add up by reason", sum(s["added_by_reason"].values()) == s["links_added"])
check("A no link removed by reading the state at the block", s["links_removed"] == 0)
check("A no unresolved read and no read left in error", not s["unresolved_reads"] and s["reads_left_in_error"] == 0)
check("A strict c4 entries = flags", s["c4_entries_strict"] == sum(v["c4"] for v in flags.values()) == sum(s["c4_events_strict"].values()))
check("A frozen c4 entries = 8 = flags", s["c4_entries_frozen"] == 8 == sum(v["frozen_c4"] for v in flags.values()))
check("A frozen c5 entries", s["c5_entries_frozen"] == sum(v["frozen_c5"] for v in flags.values()))
check("A every frozen c4 stays c4", all(v["c4"] for v in flags.values() if v["frozen_c4"]))
check("A described events match", {e["event_id"]: e["alert_entries"] for e in s["c4_events_described"]} == s["c4_events_strict"])
check("A Nobel event keeps its 8 alerts on 7 wallets", next(e for e in s["c4_events_described"] if e["event_id"] == "31406")["wallets"] == 7)
tags, before2 = s["decomposition"]["block_state_today_tags"], s["decomposition"]["code_before_the_block_only"]
check("A decomposition is a subset", tags["c4_entries"] <= s["c4_entries_strict"] and set(tags["c4_events"]) <= set(s["c4_events_strict"]))
check("A the rule before amendment 2 gives the same C4", before2["c4_events"] == s["c4_events_strict"] and before2["c5_entries"] == s["c5_entries_strict"])
ce = s["code_at_end_of_payment_block"]
check("A code at the end of the block adds up", ce["pairs"] == ce["delegated_7702"] + ce["deployed"] + ce["still_no_code"])
fed = next(e for e in s["c4_events_described"] if e["event_id"] == "45883")
check("A the Fed group's keys are all tagged Relay solvers today", all("Relay" in (r["public_tags_today"] or []) for r in fed["roots_today"].values()))
biden = next(e for e in s["c4_events_described"] if e["event_id"] == "11322")
check("A the Biden group's key is delegated through EIP-7702 today", all(r["eip7702_delegation_today"] for r in biden["roots_today"].values()))

# part B
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
series = sorted(tuple(x) for x in j("machado_yes_prices_10min.json")["history"])
check("C repricing point recomputed", ignition.first_ignition(series, "YES") == det["repricing"])
g, mkt, exp = 0.0, 0.0, []
yes = [r for r in tape if r["outcome"] == "Yes" and int(r["t"]) < ANN]
for r in yes:
    t, c = int(r["t"]), float(r["shares"]) * float(r["price"])
    if r["side"] == "BUY" and t >= AT.W0:
        mkt += c
    if r["wallet"] in group:
        g += c if r["side"] == "BUY" else -c
        exp.append((str(t), group[r["wallet"]], r["side"], round(g, 2), round(mkt, 2)))
pub = [(r["utc"], r["handle"], r["side"], float(r["group_cost_cum"]), float(r["market_buy_cost_since_21utc"])) for r in rows(os.path.join(D, "group_exposure.csv"))]
check("C group exposure recomputed", [(a, b, c, round(d, 2), round(e, 2)) for a, b, c, d, e in pub] == exp)
buy = lambda lo, hi, who: round(sum(float(r["shares"]) * float(r["price"]) for r in yes if r["side"] == "BUY" and lo <= int(r["t"]) < hi and who(r["wallet"])), 2)
p6741 = next(a["proxy"].lower() for a in acc if a["handle"] == "6741"); t1 = det["repricing"]["t1"]
first6741 = min(int(r["t"]) for r in yes if r["wallet"] == p6741)
check("C night figures recomputed", (night["buy_21_to_confirmation_all"], night["buy_21_to_confirmation_6741"], night["buy_others_first_6741_fill_to_confirmation"],
                                     night["group_gross_buys_before_announcement"], night["market_buys_21_to_last_group_fill"]) ==
      (buy(AT.W0, t1, lambda w: True), buy(AT.W0, t1, lambda w: w == p6741), buy(first6741, t1, lambda w: w != p6741),
       buy(0, ANN, lambda w: w in group), buy(AT.W0, night["last_group_fill"] + 1, lambda w: True)))
for h, t in tl.items():
    mine = sorted((r for r in act if r["handle"] == h), key=lambda r: int(r["t"]))
    trades = [r for r in mine if r["type"] == "TRADE"]
    big = [r for r in trades if r["side"] == "BUY" and float(r["usdc"] or 0) >= 1000]
    mach = [r for r in trades if r["side"] == "BUY" and r["market"] == "María Corina Machado"]
    check(f"C {h} first trade", int(trades[0]["t"]) == t["first_trade"])
    check(f"C {h} first buy of 1,000 USD", int(big[0]["t"]) == t["first_buy_1000"] and big[0]["market"].strip() == (t["first_buy_1000_market"] or "").strip()
          and big[0]["outcome"] == t["first_buy_1000_outcome"] and float(big[0]["price"]) == t["first_buy_1000_price"])
    check(f"C {h} first Machado buy", int(mach[0]["t"]) == t["first_machado_buy"] and float(mach[0]["price"]) == t["first_machado_buy_price"])
    total = sum(float(r["usdc"]) for r in trades if r["side"] == "BUY")
    check(f"C {h} Machado share", round(sum(float(r["usdc"]) for r in mach) / total, 4) == t["machado_share_of_event_buying"])
    ins = sorted((r for r in inflow if r["handle"] == h), key=lambda r: (int(r["block"]), int(r["log_index"])))
    check(f"C {h} first collateral from the funder", ins[0]["from"] == FUNDER and int(ins[0]["block"]) == t["first_collateral_block"] == t["first_funding_block"])
    f1 = min((f for f in fund if f["handle"] == h), key=lambda f: f["utc"])
    check(f"C {h} funding time and delay", f1["utc"][11:19] == t["first_funding_by_key_utc"][11:19] and hms(int(ins[0]["t"])) == f1["utc"][11:19]
          and round((t["first_trade"] - int(ins[0]["t"])) / 60, 2) == t["minutes_funding_to_first_trade"])
    before = [r for r in yes if int(r["t"]) < t["first_machado_buy"]]
    check(f"C {h} last print before its first Machado buy", before and float(before[-1]["price"]) == t["last_print_before_first_machado_buy"]["price"])

# part D
first = min(det["detectors"].values(), key=lambda v: v["utc"])
check("D first alert is the earliest detector", first["utc"] == det["first_alert_on_eight"]["utc"])
check("D hours before the announcement", round((ANN - first["utc"]) / 3600, 2) == det["first_alert_on_eight"]["hours_before_announcement"])
word = ("NOT_DETECTED_BEFORE_ANNOUNCEMENT" if first["utc"] >= ANN else
        "DETECTED_BEFORE_PUBLIC_REPRICING" if first["utc"] < t1 else "DETECTED_AFTER_REPRICING_BEFORE_ANNOUNCEMENT")
check("D verdict word", det["verdict"] == word and det["qualifier"] == "NOT_A_VALIDATION" and f"`{word}`" in rep)
check("D EXT_NN counts", nn["flagged"] == sum(n for sc, n in nn["score_distribution"].items() if int(sc) >= 7) and nn["flagged_on_eight"] <= nn["flagged"])

# every figure the text quotes, built from the data
c4 = det["detectors"]["frozen c4"]; c1 = q["INFO:c1"]
quoted = [hms(first["utc"]), hms(t1), f"at {det['repricing']['x_t1']}", f"{det['first_alert_on_eight']['hours_before_announcement']} hours",
          f"{abs(det['first_alert_on_eight']['minutes_vs_repricing_confirmation'])} minutes", hms(c4["utc"]), f"at {p3(c4['price'])}",
          f"{round((ANN - c4['utc']) / 3600, 2)} hours", f"{c1['first_on_eight_rank_by_time']}th of **{c1['alerts']} alerts**", f"on {c1['events']} events",
          f"raised {c1['per_day_7_days_before'][-1]} in the 24 hours before, {c1['same_12_hours_the_night_before']} over the same 12 hours",
          f"{night['share_6741_to_confirmation'] * 100:.1f} %", f"{usd(night['buy_21_to_confirmation_6741'])} of {usd(night['buy_21_to_confirmation_all'])} USD",
          f"bought {usd(night['buy_others_first_6741_fill_to_confirmation'])} USD", f"{usd(night['group_gross_buys_before_announcement'])} USD",
          f"was {round(night['group_gross_share'] * 100)} %", f"{hms(night['last_group_fill'])} UTC", f"{usd(pub[-1][3])} USD",
          f"**{s['c4_entries_strict']} alert entries on four events**", num(s["archive_reads"]), num(s["reads_of_code_today"]), num(s["links_added"]),
          f"{num(s['added_by_reason']['tagged_today'])} through addresses tagged", f"{s['added_by_reason']['contract_today']} through addresses",
          f"{s['added_by_reason']['busy_today']} through keys", num(ce["pairs"]), num(ce["delegated_7702"]), f"{ce['still_no_code']} still had no code",
          f"{num(s['payers_delegated_7702_at_payment'])} payers", f"{num(before2['links'])} links, {before2['c4_entries']} `C4` entries",
          f"{num(s['pass_through_keys_unread'])} keys that were pass-through", f"{num(s['pass_through_at_block_hops_unread'])}\npairs",
          f"{num(before2['pass_through_keys_unread'])} keys and {num(before2['pass_through_pairs_unread'])} pairs",
          f"first of {nn['flagged']} flagged", f"{nn['entries_scored']} of its", num(s["classify_counters"]["entries"])]
for text in quoted:
    check(f"report quotes {text!r}", text in rep)

print(f"{len(ok)} checks passed, {len(bad)} failed")
for x in bad:
    print("FAILED:", x)
sys.exit(1 if bad else 0)
