"""Offline re-check of the decisive claims in REPORT.md, from evidence/ and data/ only. No network. Exit code 1 on any failure.

A  KPMG: each of the 14 handoffs is re-derived from the archived Polygon receipts, Solana transactions and Relay records.
B  KPMG: Ethereum shared deposit addresses sweep their whole balance, and every Relay order paying them comes from the cohort.
C  KPMG: market-level exact tails recomputed from data/kpmg_earnings_markets.csv.
D  Railgun lead: the six distributor wallets are funded by Railgun Unshield events (0.25 % fee); the four funding EOAs are fed
   by distributor children and pay Relay; the five winning accounts of the tree hold unredeemed Maduro shares.
G  Railgun lead: every account funded by the same tree (Relay id equal on deposit and payout calldata), one bet each.
E  Biden-pardon accounts: withdrawals of both proxies reach the same deposit address, which sweeps everything it receives.
F  Snoorrason 14 Oct: two mirrors return the same long-form text, which extends X's truncated text and lists the five names.
"""
import csv, glob, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EV, DATA = HERE / "evidence", HERE / "data"
T = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
USDCE, USDC_POL = "0x2791bca1f2de4661ed88a30c99a7a9449aa84174", "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359"
SOLVER, DEPOSITORY = "0xf70da97812cb96acdf810712aa562db8dfa3dbef", "0x4cd00e387622c35bddb9b4c962c136462338bc31"
USDC_SOL = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))


def jl(p):
    return json.loads(Path(p).read_text())


def rows(name):
    with open(DATA / name, newline="") as f:
        return list(csv.DictReader(f))


def transfers(receipt):
    return [(l["address"].lower(), "0x" + l["topics"][1][26:], "0x" + l["topics"][2][26:], int(l["data"], 16))
            for l in receipt["logs"] if l["topics"][0] == T and len(l["topics"]) == 3]


B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def b58d(x):
    n = 0
    for ch in x:
        n = n * 58 + B58.index(ch)
    return b"\x00" * (len(x) - len(x.lstrip("1"))) + n.to_bytes((n.bit_length() + 7) // 8, "big")


def sol_delta(tx, owner):
    m = tx["meta"]
    bal = lambda xs: {b["accountIndex"]: int(b["uiTokenAmount"]["amount"]) for b in xs if b["owner"] == owner and b["mint"] == USDC_SOL}
    pre, post = bal(m["preTokenBalances"]), bal(m["postTokenBalances"])
    return sum(post.get(k, 0) - pre.get(k, 0) for k in set(pre) | set(post))


def tail(ps, k):
    d = [1.0]
    for p in ps:
        d = [a * (1 - p) + b * p for a, b in zip(d + [0.0], [0.0] + d)]
    return sum(d[k:])


# A. handoffs
acc = {r["public_label"]: r["polygon_proxy"].lower() for r in rows("kpmg_accounts.csv")}
check("A0 22 accounts with distinct proxies", len(acc) == 22 and len(set(acc.values())) == 22)
H = rows("kpmg_handoffs_verified.csv")
check("A0 14 handoffs, 11 of them in the Bitquery table", len(H) == 14 and sum(h["in_bitquery_table"] == "True" for h in H) == 11)
for h in H:
    a = jl(EV / "chain" / f"polygon_{h['L1_polygon_tx']}.json")
    b = jl(EV / "chain" / f"polygon_{h['L2_polygon_tx']}.json")
    s1 = jl(EV / "chain" / f"solana_{h['L1_solana_sig']}.json")["result"]
    s2 = jl(EV / "chain" / f"solana_{h['L2_solana_sig']}.json")["result"]
    wq, dq = jl(EV / "relay" / f"{h['withdraw_request_id']}.json"), jl(EV / "relay" / f"{h['deposit_request_id']}.json")
    sp, rp, x = acc[h["sender"]], acc[h["recipient"]], h["intermediary_solana"]
    t1 = [t for t in transfers(a["receipt"]) if t[0] == USDCE and t[1] == sp and t[2] in (SOLVER, DEPOSITORY)]
    t4 = [t for t in transfers(b["receipt"]) if t[0] == USDCE and t[1] == SOLVER and t[2] == rp]
    key1 = h["chain_key_leg1"]
    in_key = key1[2:] in a["tx"]["input"] or any(l["address"].lower() == DEPOSITORY and l["data"][-64:] == key1[2:] and l["data"][2:66][-40:] == sp[2:]
                                                 for l in a["receipt"]["logs"])
    memos1 = [i.get("parsed") for i in s1["transaction"]["message"]["instructions"] if i.get("program") == "spl-memo"]
    key2 = "0x" + b["tx"]["input"][-64:]
    memos2 = [i.get("parsed") for i in s2["transaction"]["message"]["instructions"] if i.get("program") == "spl-memo"]
    data2 = [b58d(i["data"]).hex() for i in s2["transaction"]["message"]["instructions"] if i.get("data")]
    signers2 = [k["pubkey"] for k in s2["transaction"]["message"]["accountKeys"] if k.get("signer")]
    d1, d2 = sol_delta(s1, x), sol_delta(s2, x)
    ok = (bool(t1) and t1[0][3] == int(h["L1_usdce_atomic"]) and in_key and key1 in memos1 and d1 == int(h["intermediary_credit_usdc_atomic"]) > 0
          and d2 == -d1 and (key2 in memos2 or any(key2[2:] in d for d in data2)) and x in signers2 and bool(t4) and t4[0][3] == int(h["L2_usdce_atomic"])
          and s1["blockTime"] <= s2["blockTime"] and wq["recipient"] == x and dq["user"] == x
          and wq["user"].lower() == sp and dq["recipient"].lower() == rp and a["receipt"]["status"] == "0x1" == b["receipt"]["status"])
    check(f"A1 {h['sender']} -> {h['recipient']} via {x[:8]}", ok, f"{h['seconds_L1_to_L2']} s, {int(h['intermediary_credit_usdc_atomic']) / 1e6} USDC")
yl = [h for h in H if h["sender"] == "Youaregu"][0]
check("A2 Bitquery's 0xafed93e1 is the Relay request id (Solana memo), not the Polygon withdrawal tx",
      yl["withdraw_request_id"].startswith("0xafed93e1") and yl["L1_polygon_tx"].startswith("0xea5ae0d2"))
check("A3 new edge KARLSON1970 -> perlgrow (not in the Bitquery table)", any(h["sender"] == "KARLSON1970" and h["recipient"] == "perlgrow" and h["in_bitquery_table"] == "False" for h in H))

# B. shared deposit addresses
OFF = {"0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48", "0xdac17f958d2ee523a2206206994597c13d831ec7"}
cohort = set(acc.values())
for r in rows("kpmg_shared_deposit_addresses.csv"):
    x = r["address"]
    relay = [jl(p) for p in glob.glob(str(EV / "relay" / "*.json"))]
    pay = [q for q in relay if q["recipient"].lower() == x.lower() and q["status"] == "success"]
    senders = {q["user"].lower() for q in pay}
    ok = len(pay) == int(r["relay_orders_paying_it"]) and senders <= cohort and len({q["user"].lower() for q in pay}) == int(r["n_cohort_accounts"])
    if r["chain_id"] == "1":
        tk = [t for t in jl(EV / "etherscan" / x / "1_tokentx_p1.json")["result"] if t["contractAddress"] in OFF]
        i = sum(int(t["value"]) for t in tk if t["to"] == x); o = sum(int(t["value"]) for t in tk if t["from"] == x)
        ok = ok and abs(i - o) <= 1000 and len({t["to"] for t in tk if t["from"] == x}) == 1  # whole balance swept to one wallet (dust tolerance 0.001)
    check(f"B1 {x[:10]} paid by {r['n_cohort_accounts']} cohort accounts only, swept", ok, r["classification"])

# C. market statistics
M = [r for r in rows("kpmg_earnings_markets.csv") if r["scope"] == "core19" and r["auditor"] == "KPMG" and r["held_at_cutoff"] == "True" and r["winner"]]
ps = [float(r["p_main_side_cost_weighted"]) for r in M]
k_main, k_all = sum(r["main_side_won"] == "True" for r in M), sum(r["every_account_side_won"] == "True" for r in M)
check("C1 21 KPMG markets held at the SEC stamp, expected wins 14.34", len(M) == 21 and round(sum(ps), 2) == 14.34)
check("C2 main-side rule 20/21, exact tail 0.00116 (Bitquery 'biggest stake' 0.0012)", k_main == 20 and abs(tail(ps, 20) - 0.0011563) < 1e-6)
check("C3 every-account rule 18/21, exact tail 0.0398 (Bitquery headline 19/21, 0.0084, not reproduced)", k_all == 18 and abs(tail(ps, 18) - 0.03979) < 1e-4)
check("C4 no buy after the Item 2.02 stamp in these 21 markets", all(r["stake_after_filing_usdc"] in ("0.0", "") for r in M))

# D. Railgun lead
E = rows("railgun_maduro_edges.csv")
un = [e for e in E if e["edge"] == "RAILGUN_UNSHIELD"]
ok = len(un) == 6
for e in un:
    rc = jl(EV / "chain" / f"polygon_receipt_{e['tx']}.json")["result"]
    lg = [l for l in rc["logs"] if l["address"].lower() == "0x19b620929f97b7b990801496c3b361ca5def8c71" and l["topics"][0].startswith("0xd93cf895")]
    d = lg[0]["data"][2:] if lg else ""
    amt, fee = int(d[256:320], 16), int(d[320:384], 16)
    ok = ok and "0x" + d[24:64] == e["to"] and "0x" + d[152:192] == USDC_POL and amt == int(e["amount_atomic"]) and round(fee / (amt + fee), 6) == 0.0025
check("D1 six distributors funded by Railgun Unshield events, fee 0.25 %", ok, f"{sum(int(e['amount_atomic']) for e in un) / 1e6} USDC")
hubs = {e["to"] for e in un}
kids_ok = True
for e in [e for e in E if e["edge"] == "DISTRIBUTOR_CHILD_TO_FUNDING_EOA"]:
    par = [t["from"] for t in jl(EV / "etherscan" / e["from"] / "137_tokentx_p1.json")["result"] if t["to"] == e["from"] and t["contractAddress"] == USDC_POL]
    kids_ok = kids_ok and bool(set(par) & hubs)
check("D2 every child feeding a funding EOA was itself paid by a Railgun-funded distributor", kids_ok)
fe = {e["from"] for e in E if e["edge"] == "FUNDING_EOA_TO_RELAY"}
ro = [e for e in E if e["edge"] == "RELAY_ORDER_TO_ACCOUNT"]
check("D3 the four funding EOAs pay Relay, which credits the four accounts", len(fe) == 4 and {e["from"] for e in ro} == fe and len({e["to"] for e in ro}) == 4)
pos = [jl(p)["data"][0] for p in sorted(glob.glob(str(EV / "positions" / "v2_*.json")))]
check("D4 the five winning tree accounts hold unredeemed Maduro shares", len(pos) == 5 and all(p["status"] == "REDEEMABLE" and abs(p["realized_pnl"]) < 0.01 for p in pos),
      f"cost {round(sum(p['entry_cost_usdc'] for p in pos), 2)}, value {round(sum(p['current_value'] for p in pos), 2)}")

# G. every account funded by the same tree
A = rows("railgun_tree_accounts.csv")
kids = set()
for h in hubs:
    kids |= {t["to"] for t in jl(EV / "etherscan" / h / "137_tokentx_p1.json")["result"] if t["from"] == h and t["contractAddress"] == USDC_POL}
ok = bool(A)
for r in A:
    ok = ok and r["funding_wallet"] in kids
    if r["resolution_method"] == "CHAIN_INPUT_TAIL":
        dep = jl(EV / "relay_chain" / f"deposit_tx_{r['relay_deposit_tx']}.json")
        pay = jl(EV / "relay_chain" / f"payout_tx_{r['relay_payout_tx']}.json")
        ok = ok and dep["tx"]["from"].lower() == r["funding_wallet"] and dep["tx"]["input"][-64:] == pay["input"][-64:] == r["request_id"][2:]
    else:
        q = jl(EV / "relay" / f"{r['request_id']}.json")
        ok = ok and q["user"].lower() == r["funding_wallet"] and q["recipient"].lower() == r["proxy"]
GM = {m["conditionId"]: m for m in jl(EV / "gamma" / "rail_markets.json")}
won = [r for r in A if r["won"] == "True"]
ok = ok and all(json.loads(GM[r["condition_id"]]["outcomes"])[json.loads(GM[r["condition_id"]]["outcomePrices"]).index("1")] == r["winning_outcome"] for r in A)
check("G1 each tree-funded account: funder is a distributor child, Relay id matches on both legs, outcome from Gamma", ok,
      f"{len({r['proxy'] for r in A})} accounts, {len(won)} winners, stake {round(sum(float(r['usdc']) for r in A), 2)}")
check("G2 every tree-funded account made a single bet", len(A) == len({r["proxy"] for r in A}))

# E. Biden-pardon shared deposit address
KR = "0x0a65fdd872da9fc9a16a37a9c10be8e8362d8d7e"
B = rows("biden_pardon_shared_deposit.csv")
ok = True
for r in B:
    rc = jl(EV / "chain" / f"polygon_receipt_{r['tx']}.json")["result"]
    ok = ok and any(t[2] == KR and t[3] == int(r["amount_atomic"]) for t in transfers(rc))
tot = {lab: sum(int(r["amount_atomic"]) for r in B if r["account"] == lab) / 1e6 for lab in ("d9be", "a416")}
tk = [t for t in jl(EV / "etherscan" / KR / "137_tokentx_p1.json")["result"] if t["contractAddress"] in (USDC_POL, USDCE, "0xc2132d05d31c914a87c6611c10748aeb04b58e8f")]
i, o = sum(int(t["value"]) for t in tk if t["to"] == KR), sum(int(t["value"]) for t in tk if t["from"] == KR)
check("E1 both pardon proxies' withdrawals reach one deposit address that sweeps all it receives", ok and tot["d9be"] > 337000 and tot["a416"] > 146000 and i == o, json.dumps(tot))

# F. Snoorrason
X = jl(EV / "x" / "snoorrason_2110285369748963671.json")
pre = X["syndication_truncated_text"].split("https://t.co")[0].strip()
check("F1 two mirrors agree, extend X's truncated text, list the five names; never edited",
      X["fxtwitter_text"] == X["vxtwitter_text"] and X["fxtwitter_text"].startswith(pre) and "1)kane 2)mbappe 3)yamal 4)rodri 5)messi" in X["fxtwitter_text"]
      and X["edit_tweet_ids"] == [X["id"]])

w = max(len(n) for n, _, _ in RESULTS)
for n, ok, d in RESULTS:
    print(("PASS " if ok else "FAIL ") + n.ljust(w), d)
fails = sum(not ok for _, ok, _ in RESULTS)
print(f"{len(RESULTS) - fails}/{len(RESULTS)} checks pass")
sys.exit(1 if fails else 0)
