"""Offline re-check of the decisive claims in REPORT.md, from evidence/ and data/ only. No network. Exit code 1 on any failure.

A  KPMG: each of the 14 handoffs is re-derived from the archived Polygon receipts, Solana transactions and Relay records.
B  KPMG: Ethereum shared deposit addresses sweep their whole balance, and every Relay order paying them comes from the cohort.
C  KPMG: market-level exact tails recomputed from data/kpmg_earnings_markets.csv.
D  Railgun lead: the six distributor wallets are funded by Railgun Unshield events (0.25 % fee); the four funding EOAs are fed
   by distributor children and pay Relay; the five winning accounts of the tree hold unredeemed Maduro shares.
G  Railgun lead: every account funded by the same tree (Relay id equal on deposit and payout calldata), one bet each.
E  Biden-pardon accounts: 25 proxy withdrawals reach one deposit address and one sweep sink; an extra unrelated-on-chain funder exits separately.
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

FW = rows("kpmg_funding_wallet_relay_orders.csv")
fw_ok = len({r["funding_wallet"] for r in FW}) == 23 and all(r["counterparty_label"] != "OUTSIDE_COHORT" for r in FW)
for r in FW:
    q = jl(EV / "relay" / f"{r['relay_request_id']}.json")
    party = q["recipient"] if r["role"] == "PAYS" else q["user"]
    fw_ok = fw_ok and (party.lower() if party.startswith("0x") else party) == r["counterparty"] and r["counterparty"] in set(acc.values())
check("A4 the 23 funding wallets' Relay orders involve only the 22 cohort accounts (expansion test, funding side)", fw_ok, f"{len(FW)} orders")

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

# D5. closure of the tree: distributors pass on exactly what Railgun sent; children send only to other children or to Relay solvers
RELAY_SOLVERS = {"0xf70da97812cb96acdf810712aa562db8dfa3dbef", "0x56c262027e0de4aea31d2489529cb25d23e58a8b", "0xa67d7eb4dc68fa6ce8e34ef8cadaf075b9893fbb",
                 "0xabb2acd3be814a80e502575d6c1dc5f789e9cd10", "0xca7ded7e4f4ba8ab3b10009236ae6d1b95094589"}
STABLE = {USDC_POL, USDCE}
kid_set, hub_in, hub_out = set(), 0, 0
for h in hubs:
    tk = jl(EV / "etherscan" / h / "137_tokentx_p1.json")["result"]
    hub_in += sum(int(t["value"]) for t in tk if t["to"] == h and t["contractAddress"] in STABLE)
    hub_out += sum(int(t["value"]) for t in tk if t["from"] == h and t["contractAddress"] in STABLE)
    kid_set |= {t["to"] for t in tk if t["from"] == h and t["contractAddress"] in STABLE}
to_relay, residual, outside, leak = 0, 0, 0, []
for k in kid_set:
    tk = [t for t in jl(EV / "etherscan" / k / "137_tokentx_p1.json")["result"] if t["contractAddress"] in STABLE]
    residual += sum(int(t["value"]) for t in tk if t["to"] == k) - sum(int(t["value"]) for t in tk if t["from"] == k)
    outside += sum(int(t["value"]) for t in tk if t["to"] == k and t["from"] not in kid_set and t["from"] not in hubs)  # poisoning dust
    for t in tk:
        if t["from"] == k and int(t["value"]) >= 10000:
            if t["to"] in RELAY_SOLVERS: to_relay += int(t["value"])
            elif t["to"] not in kid_set: leak.append(t["hash"])
unshield = sum(int(e["amount_atomic"]) for e in un)
check("D5 tree closed: Railgun out = distributors out = Relay deposits + residual, nothing leaves elsewhere",
      hub_in == hub_out == unshield and to_relay + residual - outside == unshield and outside < 10000 and not leak and len(kid_set) == 384,
      f"to Relay {to_relay / 1e6}, residual {residual / 1e6}, outside dust {outside / 1e6}")

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
MAIN_SINK = "0x4b6f17856215eab57c29ebfa18b0a0f74a3627bb"
EXTRA_FUNDER = "0xf5042e6ffac5a625d4e7848e0b01373d8eb9e222"
EXTRA_SINK = "0x0853ea40b121f9135d7e0c07fae35d59aedb4d0b"
B = rows("biden_pardon_shared_deposit.csv")
ok = len(B) == 25 and len({r["tx"] for r in B}) == 25
for r in B:
    rc = jl(EV / "chain" / f"polygon_receipt_{r['tx']}.json")["result"]
    ok = ok and r["token"].lower() == USDC_POL and r["to"].lower() == KR
    ok = ok and any(t[0] == USDC_POL and t[2] == KR and t[3] == int(r["amount_atomic"]) for t in transfers(rc))
tot = {lab: sum(int(r["amount_atomic"]) for r in B if r["account"] == lab) for lab in ("d9be", "a416")}
tk = [t for t in jl(EV / "etherscan" / KR / "137_tokentx_p1.json")["result"] if t["contractAddress"].lower() == USDC_POL]
incoming = [t for t in tk if t["to"].lower() == KR]
outgoing = [t for t in tk if t["from"].lower() == KR]
cashout_hashes = {r["tx"].lower() for r in B}
cashout_in = [t for t in incoming if t["hash"].lower() in cashout_hashes]
cashout_out = [t for t in outgoing if t["to"].lower() == MAIN_SINK]
other_in = [t for t in incoming if t["hash"].lower() not in cashout_hashes]
other_out = [t for t in outgoing if t["to"].lower() != MAIN_SINK]
cashout_amounts = sorted(int(r["amount_atomic"]) for r in B)
ok = (ok and tot["d9be"] == 337487344081 and tot["a416"] == 146504524142
      and len(incoming) == len(outgoing) == 26 and len(cashout_in) == len(cashout_out) == 25
      and sorted(int(t["value"]) for t in cashout_in) == cashout_amounts
      and sorted(int(t["value"]) for t in cashout_out) == cashout_amounts
      and len(other_in) == len(other_out) == 1
      and other_in[0]["from"].lower() == EXTRA_FUNDER
      and other_out[0]["to"].lower() == EXTRA_SINK
      and int(other_in[0]["value"]) == int(other_out[0]["value"]) == 453947234
      and sum(int(t["value"]) for t in incoming) == sum(int(t["value"]) for t in outgoing)
      == sum(cashout_amounts) + 453947234)
check("E1 25 pardon-proxy cashouts sweep to one sink; third-party 453.947234 USDC enters and exits separately", ok,
      f"proxies {(sum(cashout_amounts) / 1e6):.6f}, extra 453.947234 USDC")

# F. Snoorrason
X = jl(EV / "x" / "snoorrason_2110285369748963671.json")
pre = X["syndication_truncated_text"].split("https://t.co")[0].strip()
check("F1 two mirrors agree, extend X's truncated text, list the five names; never edited",
      X["fxtwitter_text"] == X["vxtwitter_text"] and X["fxtwitter_text"].startswith(pre) and "1)kane 2)mbappe 3)yamal 4)rodri 5)messi" in X["fxtwitter_text"]
      and X["edit_tweet_ids"] == [X["id"]])

# H. XFM paired wallets: nine two-party mint matches, then two collector wallets for the numbered accounts
REG = {}
with open(HERE.parent / "kpmg-election-integrity-2026-11-07" / "XFM_NINE_SPLITS.csv", newline="") as f:
    for r in csv.DictReader(f):
        REG[r["polygon_tx_hash"]] = r
XD = rows("xfm_nine_receipts_decoded.csv")
EXV2 = "0xe2222d279d744050d28e00520010520000310f59"
ok = len(XD) == 9 and set(r["tx"] for r in XD) == set(REG)
for r in XD:
    rc = jl(EV / "chain" / f"polygon_receipt_{r['tx']}.json")["result"]
    fills = [("0x" + l["topics"][2][26:], "0x" + l["topics"][3][26:]) for l in rc["logs"] if l["topics"][0].startswith("0xd543adfd") and l["address"].lower() == EXV2]
    parties = {x for f in fills for x in f} - {EXV2}
    ok = ok and parties == {r["yes_wallet"], r["no_wallet"]} and r["two_party_mint_match"] == "True" and r["yes_name"] == REG[r["tx"]]["yes_wallet_alias"] and r["no_name"] == REG[r["tx"]]["no_wallet_alias"]
check("H1 nine XFM receipts: two-party mint matches, YES/NO names equal MSR's labels", ok, f"shares {round(sum(float(r['shares_each']) for r in XD), 2)} each side")
XC = rows("xfm_collectors.csv")
names_ok = all(r["profile_name"] and r["profile_name"].startswith("xfm-") for r in XC)
import collections as _c
by_c = _c.Counter(r["collector"] for r in XC)
relay_ok = all(jl(EV / "relay" / f"{r['relay_request_id']}.json")["recipient"].lower() == r["collector"] for r in XC)
check("H2 37 numbered xfm accounts withdraw to two wallets on 15 Oct 2026 within 46 minutes", len(XC) == 37 and len({r["account"] for r in XC}) == 37 and names_ok and relay_ok
      and min(r["created_utc"] for r in XC) >= "2026-10-15T14:34" and max(r["created_utc"] for r in XC) <= "2026-10-15T15:21", json.dumps(dict(by_c)))
col = jl(EV / "etherscan" / "0x91243b658072dc08218b9868cc55e7cdc2cbfadc" / "137_tokentx_p1.json")["result"]
funded = [t for t in col if t["from"] == "0x91243b658072dc08218b9868cc55e7cdc2cbfadc" and t["to"] == "0xf5042e6ffac5a625d4e7848e0b01373d8eb9e222" and t["timeStamp"] < "1768100000"]
check("H3 the series-5/6 collector also paid the RelayRouter for xfm-6-1's first deposit (10 Jan 2026)", len(funded) == 1 and int(funded[0]["value"]) == 45500494)

# I. Iran, 14 Jan 2026: the YES whale and X34 share no fill; the whale is funded from Base, not from the eight-account network
I = jl(EV / "iran14" / "tape_rows_mutualdelta_x34.json")
MD, X34 = "0xaa6a2beda1ad8d5b40b6af71c4b6d075fa783c59", "0x60280beffdfeaf962de4e6397ab49ed05a1b99e1"
md = [r for r in I["rows"] if r["proxy_wallet"] == MD]; x34 = [r for r in I["rows"] if r["proxy_wallet"] == X34]
check("I1 mutualdelta: 201 YES buys for 40,021.35 USDC, no sale", len(md) == 201 and all(r["side"] == "BUY" and r["token_id"] == I["tokens"]["YES"] for r in md)
      and abs(sum(r["size"] * r["price"] for r in md) - 40021.35) < 0.01)
check("I2 X34 bought 30,000 USDC of NO and shares no fill transaction with mutualdelta",
      abs(sum(r["size"] * r["price"] for r in x34 if r["side"] == "BUY" and r["token_id"] == I["tokens"]["NO"]) - 30000) < 0.01
      and not ({r["transaction_hash"] for r in md} & {r["transaction_hash"] for r in x34}))
fo = jl(EV / "iran14" / "base_funder_origin.json")
mdq = [jl(p) for p in glob.glob(str(EV / "relay" / "*.json")) if jl(p)["recipient"].lower() == MD]
NETWORK = {"0xe9a7230f874930827b87970a4fbb33a262f02442", "0x44b6f8de91e20953eb2c632062860338154ebe4e", "0xefaa882c1eb8253a65a3a194f08063693a13f565"}
check("I3 mutualdelta funded from Base by a one-use key paid by 0x899ecb22, none of them in the eight-account network",
      len(mdq) == 2 and all(q["user"].lower() == fo["funder"] for q in mdq) and all("0x" + l["topics"][1][26:] == "0x899ecb2221489d0c76f6f214f3ccf197e0525dc8" for l in fo["usdc_logs"])
      and fo["funder"] not in NETWORK and "0x899ecb2221489d0c76f6f214f3ccf197e0525dc8" not in NETWORK)

# J. deposit side of the 38-account cohort
GD = rows("g38_deposit_origins.csv")
fw = _c.defaultdict(set)
for r in GD:
    fw[r["funding_wallet"]].add(r["account"])
check("J1 38 accounts, 39 funding wallets, none shared by two accounts", len({r["account"] for r in GD}) == 38 and len(fw) == 39 and all(len(s) == 1 for s in fw.values()))
check("J2 upstream of the Polygon/Ethereum funding wallets is Robinhood or Coinbase hot wallets for 15 of them",
      sum(1 for w, s in fw.items() if any(("Robinhood" in r["funding_wallet_upstream_polygon_or_ethereum"] or "Coinbase" in r["funding_wallet_upstream_polygon_or_ethereum"]) for r in GD if r["funding_wallet"] == w)) == 15)

w = max(len(n) for n, _, _ in RESULTS)
for n, ok, d in RESULTS:
    print(("PASS " if ok else "FAIL ") + n.ljust(w), d)
fails = sum(not ok for _, ok, _ in RESULTS)
print(f"{len(RESULTS) - fails}/{len(RESULTS)} checks pass")
sys.exit(1 if fails else 0)
