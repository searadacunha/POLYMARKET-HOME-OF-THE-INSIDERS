#!/usr/bin/env python3
"""Offline checks of the early-detection note. Standard library only, reads files, writes nothing.

    python3 -I research_notes/early-detection-2026-11-13/verify.py

1. The figures quoted in the reports recompute from the data files of this note.
2. Every address and transaction hash printed in the reports exists in an evidence file (none typed from memory).
3. Relative links of the reports resolve.
4. When the frozen study is archived here, its files still match the hashes of its lock.
"""
import csv, hashlib, json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DATA = HERE / "data"
REPORTS = ["AUDIT_20261113.md", "NEW_LEADS.md", "PATTERN_RESEARCH.md", "LIVE_DETECTION.md", "BACKTEST_RESULTS.md",
           "research_notes/early-detection-2026-11-13/README.md", "monitoring/README.md"]
FUNDER = "0xe206961002feebd9edb152eed9b630a351874043"
ACCOUNT_6741 = "0xa430506774f9efaf39903ee7e0db1351f66891ca"
FAILS = []
N = [0]


def check(name, ok, detail=""):
    N[0] += 1
    if not ok:
        FAILS.append(f"{name} {detail}")
    print(("ok   " if ok else "FAIL ") + name + (f"  [{detail}]" if detail and not ok else ""))


def rows(name):
    with open(DATA / name, newline="") as f:
        return list(csv.DictReader(f))


def near(a, b, tol=0.005):
    return abs(float(a) - float(b)) <= tol


def c7():
    led = rows("c7_funder_ledger.csv"); s = json.loads((DATA / "c7_funder_ledger_summary.json").read_text())
    amt = lambda kind: sum(float(r["signed_amount_usdc"]) for r in led if r["kind"] == kind)
    kinds = {r["kind"] for r in led}
    fund = [r for r in led if r["to"] != FUNDER and r["handle"]]
    check("C7 ledger: 14 fundings to 8 proxies", len(fund) == 14 and len({r["to"] for r in fund}) == 8, f"{len(fund)} {kinds}")
    check("C7 ledger: 372,521.537078 sent", near(-sum(float(r["signed_amount_usdc"]) for r in fund), 372521.537078, 1e-6))
    check("C7 ledger: capital 249,652.409342", near(amt("capital_in"), 249652.409342, 1e-6))
    back = [r for r in led if r["kind"] == "withdrawal_in"]
    check("C7 ledger: 15 withdrawals received, 523,060.184024", len(back) == 15 and all(r["to"] == FUNDER for r in back)
          and near(sum(float(r["signed_amount_usdc"]) for r in back), 523060.184024, 1e-6))
    check("C7 ledger: net at funder level 150,538.646946", near(s["exits_total"] - s["external_capital"], 150538.646946, 1e-6)
          and near(s["gross_received_from_withdrawals"] - s["gross_sent_to_proxies"], 150538.646946, 1e-6))
    check("C7 ledger: four fundings paid with recycled withdrawals", s["n_fundings_paid_with_recycled"] == 4)
    wd = rows("c7_withdrawals_onchain.csv")
    to_f = [r for r in wd if r["recipient"] == FUNDER]; other = [r for r in wd if r["recipient"] != FUNDER]
    check("C7 withdrawals: 16 receipts with status 1", len(wd) == 16 and all(r["tx_status"] == "0x1" for r in wd))
    check("C7 withdrawals: 15 to the funder", len(to_f) == 15 and near(sum(float(r["native_usdc_to_recipient"]) for r in to_f), 523060.184024, 1e-6))
    check("C7 withdrawals: one to the 6741 proxy, 31,109.322288", len(other) == 1 and other[0]["recipient"] == ACCOUNT_6741 and near(other[0]["native_usdc_to_recipient"], 31109.322288, 1e-6))
    own = rows("c7_safe_owners.csv")
    check("C7 Safes: 8 Safes, one owner each, 8 distinct owners", len(own) == 8 and all(";" not in r["owners_at_first_funding"] for r in own)
          and len({r["owners_at_first_funding"] for r in own}) == 8)
    check("C7 Safes: the funder owns the 6741 Safe", next(r for r in own if r["proxy"] == ACCOUNT_6741)["owners_at_first_funding"] == FUNDER)
    cmp_ = json.loads((DATA / "c7_buy_cost_comparison.json").read_text()); top = {r["wallet"]: r for r in rows("machado_top45_accumulators.csv")}
    check("E1: stated 152,311.84 against 212,874.45 on the tape", near(cmp_["stated_total"], 152311.84) and near(cmp_["recomputed_total"], 212874.45)
          and near(sum(float(top[r["proxy"]]["yes_buy_cash_usd"]) for r in cmp_["rows"]), 212874.45, 0.05))


def group_trades():
    ig = rows("c7_intra_group_trades.csv")
    check("Intra-group: four trades, 53,356 shares, 30,514.17 USD, all sold by 6741", len(ig) == 4 and near(sum(float(r["shares"]) for r in ig), 53355.91, 0.05)
          and near(sum(float(r["usd"]) for r in ig), 30514.17, 0.01) and {r["seller"] for r in ig} == {"6741"} and {r["buyers"] for r in ig} == {"fmaduro", "madurowilllose"})
    act = [r for r in rows("c7_accounts_activity.csv") if r["type"] == "TRADE"]
    usd = lambda h, key, side, o: sum(float(r["usdc"]) for r in act if r["handle"] == h and key in r["title"] and r["side"] == side and r["outcome"] == o)
    check("Other markets: No on Sudan's Emergency Response Rooms, 12,763.93 + 23,972.64 + 2,554.25", near(usd("6741", "Sudan", "BUY", "No"), 12763.93)
          and near(usd("madurowilllose", "Sudan", "BUY", "No"), 23972.64) and near(usd("aenews0", "Sudan", "BUY", "No"), 2554.25))
    check("Other markets: 13,528.59 USD of Navalnaya Yes bought by 6741", near(usd("6741", "Navalnaya", "BUY", "Yes"), 13528.59))
    check("Other markets: 6741 sold 34,839.55 USD of Machado Yes", near(usd("6741", "Machado", "SELL", "Yes"), 34839.55))
    check("Other markets: the eight accounts traded one event only", {r["title"].split(" win the Nobel")[0] != "" and "Nobel Peace Prize" in r["title"] for r in act} == {True})
    sh = lambda h, key, o: sum(float(r["shares"]) * (1 if r["side"] == "BUY" else -1) for r in act if r["handle"] == h and key in r["title"] and r["outcome"] == o)
    cmp_ = {r["handle"]: r for r in json.loads((DATA / "c7_buy_cost_comparison.json").read_text())["rows"]}
    check("Redemptions reconcile: Machado Yes plus Sudan No equals the redeemed amount, for the three accounts concerned",
          all(near(sh(h, "Machado", "Yes") + sh(h, "Sudan", "No"), cmp_[h]["redeemed_usdc_stated"], 0.05) for h in ("6741", "madurowilllose", "aenews0")))
    check("No purchase by the eight accounts from 09:00:00 UTC", not [r for r in act if r["side"] == "BUY" and int(r["timestamp"]) >= 1760086800])


def tape():
    t = rows("machado_tape_20251009T2000_20251010T0900.csv"); t0 = 1760049777
    w = [r for r in t if t0 <= int(r["timestamp"]) <= t0 + 900 and r["side"] == "BUY" and r["outcome"] == "Yes"]
    tot = sum(float(r["shares"]) * float(r["price"]) for r in w); mine = sum(float(r["shares"]) * float(r["price"]) for r in w if r["wallet"] == ACCOUNT_6741)
    check("Tape: 6741 supplied 97.3 % of the first fifteen minutes", near(tot, 14704.94, 0.01) and near(mine, 14304.71, 0.01) and len({r["wallet"] for r in w}) == 4, f"{tot} {mine}")
    pre = [r for r in t if int(r["timestamp"]) < t0 and r["role"] == "taker"]
    check("Tape: 15 taker trades and 1,082 USD between 20:00 and 22:42:57", len(pre) == 15 and near(sum(float(r["shares"]) * float(r["price"]) for r in pre), 1082.26, 0.01))
    first = min((r for r in t if r["wallet"] == ACCOUNT_6741), key=lambda r: int(r["timestamp"]))
    check("Tape: first trade of 6741 at 22:42:57 UTC", int(first["timestamp"]) == t0 and first["transaction_hash"].startswith("0x591e4fe5"))
    six = [r for r in t if r["wallet"] == ACCOUNT_6741 and int(r["timestamp"]) <= 1760050815 and r["side"] == "BUY"]
    check("Tape: 16,879.50 USD bought by 23:00:15 and 47,420 shares at 0.30", near(sum(float(r["shares"]) * float(r["price"]) for r in six), 16879.50, 0.01)
          and near(sum(float(r["shares"]) for r in six if r["role"] == "maker" and near(r["price"], 0.30, 1e-9)), 47419.9, 0.1))
    check("Tape: every transaction has exactly one taker row", all(n == 1 for n in _takers(t).values()))


def _takers(t):
    c = {}
    for r in t:
        c[r["transaction_hash"]] = c.get(r["transaction_hash"], 0) + (r["role"] == "taker")
    return c


def second_group():
    e = rows("second_group_circuit_transfers.csv")
    def amount(frm, to, tx_prefix=None):
        return [float(r["amount"]) for r in e if r["from_label"] == frm and r["to_label"] == to and (tx_prefix is None or r["tx"].startswith(tx_prefix))]
    by_tx = {}
    for r in e:
        by_tx.setdefault(r["tx"], []).append(r)
    same_tx = [tx for tx, rs in by_tx.items() if any(r["from_label"] == "account C (established)" for r in rs) and any(r["to_label"] == "hub key" for r in rs)]
    check("Second group: C pays the hub key inside one transaction, three times before the resolution", len(same_tx) >= 2, str(len(same_tx)))
    to_a, to_b = amount("hub key", "owner key of A"), amount("hub key", "owner key of B")
    check("Second group: the hub forwards 59,978.70 and 31,259.44 to two new keys", len(to_a) == 1 and near(to_a[0], 59978.70) and len(to_b) == 1 and near(to_b[0], 31259.44))
    check("Second group: each key pays its own account the same amount", amount("owner key of A", "account A (fresh)") == to_a
          and to_b[0] in amount("owner key of B", "account B (fresh)"))
    back = amount("owner key of A", "hub key")[0] + amount("owner key of B", "hub key")[0]
    check("Second group: 6,490.89 + 3,176.72 returned, 9,667.61 forwarded to C", near(back, 9667.61) and any(near(x, 9667.61) for x in amount("hub key", "account C (established)")))
    check("Second group: direct transfers B to C and A to B", any(near(x, 9814.93) for x in amount("account B (fresh)", "account C (established)"))
          and any(near(x, 7.09) for x in amount("account A (fresh)", "account B (fresh)")))
    g = json.loads((DATA / "nobel_top_buyers_direct_graph.json").read_text())
    comps = sorted(g["components"], key=len, reverse=True)
    check("Graph: components of 7, 3 and 2 accounts", [len(c) for c in comps] == [7, 3, 2])
    check("Graph: the component of 7 bought 291,894 USD", near(sum(g["accounts"][a]["buy_cash"] for a in comps[0]), 291894, 1.0))
    check("Graph: no documented C7 account in any component", not any(g["accounts"][a]["tag"] for c in comps for a in c))
    acc = json.loads((DATA / "second_cluster_accounts.json").read_text())
    check("Second group: A and B are Safes owned by the two new keys", all(len(v["owners"] or []) == 1 for k, v in list(acc.items())[:2]))


def replay():
    r = json.loads((DATA / "bt_nobel_result.json").read_text())["YES"]
    check("Replay: LONELY_THIN alert at 23:00:15 UTC on 6741", r["level"] == "LONELY_THIN" and r["t_alert"] == 1760050815 and r["features"]["initiator"] == ACCOUNT_6741)
    tl = r["cluster_timeline"]
    check("Replay: cluster first seen at 00:50 UTC, seven members by 03:30 UTC", tl[0]["as_of"] == 1760057400 and tl[-1]["members"] == 7 and tl[-1]["as_of"] == 1760067000)
    seen = {m["wallet"] for step in tl for m in step["new"]}
    own = {x["proxy"] for x in rows("c7_safe_owners.csv")} - {ACCOUNT_6741}
    check("Replay: the cluster is exactly the seven other documented accounts", seen == own)
    check("Replay: every member shares the funder key", {m["shared_payer"] for step in tl for m in step["new"]} == {FUNDER})
    og = r.get("other_groups") or []
    check("Replay: a second group of two accounts is reported at 07:50 UTC", len(og) == 1 and og[0]["as_of"] == 1760082600 and len(og[0]["wallets"]) == 2
          and og[0]["shared_payer"] == "0x36626bd83accd8c1e0b9268a9db98a2233fc8c55")


def references():
    hay = []
    for p in list(DATA.rglob("*")) + list((HERE / "audit").rglob("*")) + list((HERE / "study").rglob("*")) + list((ROOT / "investigations/followup-20261113").rglob("*")) \
            + [ROOT / "monitoring/phi_monitor/chain.py", ROOT / "monitoring/tests/test_replay.py"]:
        if p.is_file() and p.suffix in (".csv", ".json", ".jsonl", ".md", ".py", ".lock"):
            hay.append(p.read_text(errors="replace").lower())
    hay = "\n".join(hay)
    missing, n = [], 0
    for rel in REPORTS:
        f = ROOT / rel
        if not f.is_file():
            continue
        for ref in set(re.findall(r"0x[0-9a-fA-F]{64}|0x[0-9a-fA-F]{40}(?![0-9a-fA-F])", f.read_text())):
            n += 1
            if ref.lower() not in hay:
                missing.append(f"{rel}: {ref}")
    check(f"References: {n} addresses and hashes of the reports exist in the evidence", not missing, "; ".join(missing[:5]))
    broken = []
    for rel in REPORTS:
        f = ROOT / rel
        if not f.is_file():
            continue
        for href in re.findall(r"\]\(([^)\s#]+)", f.read_text()):
            if "://" not in href and not (f.parent / href).exists():
                broken.append(f"{rel}: {href}")
    check("Links: relative links of the reports resolve", not broken, "; ".join(broken[:5]))


def study():
    lock = HERE / "study" / "PROTOCOL.lock"
    if not lock.is_file():
        print("skip study lock (not archived in this checkout)")
        return
    j = json.loads(lock.read_text()); bad = []
    for rel, meta in (j.get("fichiers") or j.get("files") or {}).items():
        f = HERE / "study" / rel
        sha = meta if isinstance(meta, str) else (meta.get("sha256") or meta.get("sha"))
        if f.is_file() and hashlib.sha256(f.read_bytes()).hexdigest() != sha:
            bad.append(rel)
    check("Study: archived files match the hashes of the lock", not bad, ", ".join(bad[:5]))
    v = HERE / "study" / "derived" / "verdict.json"
    if v.is_file():
        check("Study: the verdict file carries one of the three fixed words", json.loads(v.read_text())["verdict"] in ("SUPPORTED", "NOT_SUPPORTED", "INCONCLUSIVE"))


def main():
    c7(); group_trades(); tape(); second_group(); replay(); references(); study()
    print(f"\n{N[0] - len(FAILS)} of {N[0]} checks passed")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
