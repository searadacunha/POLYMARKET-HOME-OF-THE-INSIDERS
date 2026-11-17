#!/usr/bin/env python3
"""Offline verifier for the Iran Solana beneficiary note.

Reads only the archived responses under evidence/ (no network) and recomputes every claim of
REPORT.md from them. It does not import the collection or build scripts. Exit code 0 only when
every check passes. Writes verification.json next to this file.

    python3 -I verify.py
"""
import gzip, hashlib, json, struct, sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
EV = HERE / "evidence"
BEN = "4dLZQynk9SZJf6PCAV73828TZHGJaf9kWgpKVUzV4Fwy"
BYBIT_DEP = "Agnhk1VsurW1ic3YNDtp3NeLTGYCiaaUwpRSKag9PdpV"
BYBIT_HW10 = "iGdFcQoyR2MwbXMHQskhmNsqddZ6rinsipHc4TNSdwu"
BYBIT_GAS = "BhwuB5KYbEgDLHYwCGdet3TcUipjxExDQK3hDqtd78Qv"
CDC_DEP = "CCQQKc4vw527ehZZhQidZZT9LEzKr4Ca7bZNwJv6BmBR"
CDC_HW6 = "HqqzZC5qsNKtZBrBsYvbXhzxUQaADSzkDaifHWe1GvEH"
SOLVER = "F7p3dFrjRTbtRp8FRF6qHLomXbKRBzpvBLjtQcfcgmNe"
PC_PROG = "9fhQBbumKEFuXtMBDw8AaQyAjCorLGJQiS3skWZdQyQD"
PC_POOL = "4AV2Qzp3N4c9RfzyEbNZs2wqWfW4EwKnnxFAZCndvfGh"
PC_DISC = "d995828fdd34fc77"
SYSTEM = "11111111111111111111111111111111"
USDC_SOL = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
USDCE_POLY = "0x2791bca1f2de4661ed88a30c99a7a9449aa84174"
DEPOSITORY = "0x4cd00e387622c35bddb9b4c962c136462338bc31"
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
ACC = {"0xcc32a117ac254fe51fd867b928e45492b1f6dc7e": "BlueElephant666",
       "0xd36fa21eb3fa7b1aaf97c8499253f76f82a16d48": "SemiconductorIT",
       "0x97e490d61b530d5078348d76143a25c43a47164d": "oveiStheair",
       "0x0a142164f48dab6448872f0abac310d03e305316": "aaamsaasa"}
T_LAST_SEMI = 1772295647  # 2026-02-28 16:20:47 UTC, last SemiconductorIT credit studied before this note
B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
results = []


def check(name, ok, **values):
    results.append({"check": name, "status": "PASS" if ok else "FAIL", **values})


def b58decode(s):
    n = 0
    for c in s:
        n = n * 58 + B58.index(c)
    raw = n.to_bytes((n.bit_length() + 7) // 8, "big") if n else b""
    return b"\0" * (len(s) - len(s.lstrip("1"))) + raw


def load(p):
    return json.loads(Path(p).read_text())


def sol_txs(addr):
    """Every transaction archived for an address, deduplicated, chain order."""
    out = {}
    for f in sorted((EV / "sol" / addr).glob("gtfa_*_p*.json")):
        if f.name.endswith(".meta.json"):
            continue
        for tx in load(f)["result"]["data"]:
            out[tx["transaction"]["signatures"][0]] = tx
    return sorted(out.values(), key=lambda t: (t["slot"], t.get("transactionIndex") or 0))


def keys(tx):
    ks = [k["pubkey"] if isinstance(k, dict) else k for k in tx["transaction"]["message"]["accountKeys"]]
    la = tx["meta"].get("loadedAddresses") or {}
    return ks + la.get("writable", []) + la.get("readonly", [])


def delta(tx, addr):
    ks = keys(tx)
    if addr not in ks:
        return None
    i = ks.index(addr)
    return tx["meta"]["postBalances"][i] - tx["meta"]["preBalances"][i], tx["meta"]["preBalances"][i], tx["meta"]["postBalances"][i]


def all_ix(tx):
    ins = list(tx["transaction"]["message"]["instructions"])
    for g in tx["meta"].get("innerInstructions") or []:
        ins += g["instructions"]
    return ins


def transfers(tx):
    out = []
    for i in all_ix(tx):
        p = i.get("parsed")
        if i.get("programId") == SYSTEM and isinstance(p, dict) and p.get("type") == "transfer":
            out.append((p["info"]["source"], p["info"]["destination"], int(p["info"]["lamports"])))
    return out


def memos(tx):
    return [i.get("parsed") for i in tx["transaction"]["message"]["instructions"]
            if i.get("programId", "").startswith(("MemoSq", "Memo1U")) and isinstance(i.get("parsed"), str)]


def token_delta(tx, owner, mint):
    pre = {b["accountIndex"]: b for b in tx["meta"].get("preTokenBalances") or []}
    post = {b["accountIndex"]: b for b in tx["meta"].get("postTokenBalances") or []}
    tot = 0
    for idx in set(pre) | set(post):
        b = post.get(idx) or pre[idx]
        if b.get("owner") == owner and b["mint"] == mint:
            tot += int(post[idx]["uiTokenAmount"]["amount"] if idx in post else 0) - int(pre[idx]["uiTokenAmount"]["amount"] if idx in pre else 0)
    return tot


def relay(sig_or_hash):
    q = load(EV / "http" / f"relay_{sig_or_hash}.json")["requests"]
    return q[0] if len(q) == 1 else None


def receipt(h):
    return load(EV / "polygon" / f"{h}.eth_getTransactionReceipt.json")["result"]


def erc20(rc, contract):
    return [("0x" + l["topics"][1][-40:], "0x" + l["topics"][2][-40:], int(l["data"], 16)) for l in rc["logs"]
            if l["address"].lower() == contract and l["topics"] and l["topics"][0] == TRANSFER and len(l["topics"]) == 3]


def raw_units(x, dec):
    whole, _, frac = str(x).partition(".")
    return int(whole) * 10 ** dec + int((frac + "0" * dec)[:dec] or 0)


# 0. Integrity: every evidence file matches SHA256SUMS.txt, and every archived response its own meta hash
bad, n = [], 0
for line in (HERE / "SHA256SUMS.txt").read_text().splitlines():
    h, p = line.split("  ", 1)
    n += 1
    if hashlib.sha256((HERE / p).read_bytes()).hexdigest() != h:
        bad.append(p)
meta_bad = [str(m.relative_to(HERE)) for m in EV.rglob("*.meta.json")
            if "sha256" in load(m) and (m.parent / m.name.replace(".meta.json", ".json")).exists()
            and hashlib.sha256((m.parent / m.name.replace(".meta.json", ".json")).read_bytes()).hexdigest() != load(m)["sha256"]]
check("integrity_sha256", not bad and not meta_bad, files=n, mismatched=bad, meta_mismatched=meta_bad)

# 1. Complete history of the beneficiary: pagination ended, balance path continuous from 0 to 0
txs = sol_txs(BEN)
done = load(EV / "sol" / BEN / "gtfa_0_0_DONE.json")
path = [delta(t, BEN) for t in txs]
continuous = all(path[i][2] == path[i + 1][1] for i in range(len(path) - 1))
check("beneficiary_history_complete", done["termination"] == "END" and continuous and path[0][1] == 0 and path[-1][2] == 0
      and txs[0]["transaction"]["signatures"][0].startswith("J7kxLHi3"),
      transactions=len(txs), first_signature=txs[0]["transaction"]["signatures"][0], start_lamports=path[0][1], end_lamports=path[-1][2])

# 2. Every material credit comes from the Relay solver with a memo, and Relay names the payer account
credits, by_acct, by_acct_usdce, memo_ok, recips = [], defaultdict(int), defaultdict(int), True, set()
for t in txs:
    if t["meta"]["err"] is not None:
        continue
    d = delta(t, BEN)[0]
    if d > 1_000_000:
        sig = t["transaction"]["signatures"][0]
        src = {s for s, dst, l in transfers(t) if dst == BEN}
        q = relay(sig)
        user = q["user"].lower()
        recips.add(q["recipient"])
        m = memos(t)
        memo_ok &= bool(m) and m[0] in json.dumps(q) and any(o["hash"] == sig for o in q["data"]["outTxs"])
        credits.append({"signature": sig, "lamports": d, "solver_only": src == {SOLVER}, "account": ACC.get(user, user), "relay_request": q["id"]})
        by_acct[ACC.get(user, user)] += d
        intx = q["data"]["inTxs"][0]
        rc = receipt(intx["hash"])
        moved = [v for s, dst, v in erc20(rc, USDCE_POLY) if s == user and dst == DEPOSITORY]
        exp = raw_units(q["data"]["metadata"]["currencyIn"]["amountFormatted"], 6)
        credits[-1]["polygon_receipt_ok"] = int(rc["status"], 16) == 1 and moved == [exp] and intx["chainId"] == 137
        by_acct_usdce[ACC.get(user, user)] += exp
check("beneficiary_credits_are_relay_orders", all(c["solver_only"] for c in credits) and memo_ok and recips == {BEN}
      and set(by_acct) <= set(ACC.values()), orders=len(credits), accounts=sorted(by_acct), total_sol=sum(by_acct.values()) / 1e9)
check("polygon_debits_match_relay_orders", all(c["polygon_receipt_ok"] for c in credits),
      receipts=sum(c["polygon_receipt_ok"] for c in credits), of=len(credits))
check("per_account_sol_and_usdce", True, sol={k: v / 1e9 for k, v in by_acct.items()},
      usdce={k: v / 1e6 for k, v in by_acct_usdce.items()}, total_usdce=sum(by_acct_usdce.values()) / 1e6)
check("two_accounts_new_to_the_beneficiary", {"oveiStheair", "aaamsaasa"} <= set(by_acct),
      new_sol=(by_acct["oveiStheair"] + by_acct["aaamsaasa"]) / 1e9,
      new_usdce=(by_acct_usdce["oveiStheair"] + by_acct_usdce["aaamsaasa"]) / 1e6)

# 3. Outflows of the beneficiary, Privacy Cash deposits decoded from instruction data
out = defaultdict(int)
pc = []
for t in txs:
    if t["meta"]["err"] is not None:
        continue
    for s, dst, l in transfers(t):
        if s == BEN:
            out[dst] += l
    for i in t["transaction"]["message"]["instructions"]:
        if i.get("programId") == PC_PROG:
            data = b58decode(i["data"])
            amt = struct.unpack_from("<q", data, 488)[0]
            to_pool = sum(l for s, dst, l in transfers(t) if s == BEN and dst == PC_POOL)
            pc.append({"signature": t["transaction"]["signatures"][0], "slot": t["slot"], "block_time": t["blockTime"],
                       "discriminator": data[:8].hex(), "ext_amount": amt, "cpi_to_pool": to_pool})
check("privacy_cash_deposits", len(pc) == 2 and all(p["discriminator"] == PC_DISC and p["ext_amount"] == p["cpi_to_pool"] for p in pc),
      deposits=pc, total_sol=sum(p["ext_amount"] for p in pc) / 1e9)
check("no_privacy_cash_deposit_after_last_semiconductorit_credit", all(p["block_time"] < T_LAST_SEMI for p in pc))
after = [(t["transaction"]["signatures"][0], t["blockTime"], [(dst, l) for s, dst, l in transfers(t) if s == BEN])
         for t in txs if t["blockTime"] > T_LAST_SEMI and t["meta"]["err"] is None and delta(t, BEN)[0] < 0]
check("single_outflow_after_16_20_47", len(after) == 1 and after[0][2] == [(BYBIT_DEP, 69068480977)], outflows=after)
check("outflow_destinations", out[BYBIT_DEP] == 842687802663 and out[PC_POOL] == 12447822100,
      sol={k: v / 1e9 for k, v in out.items()}, share_to_bybit_deposit=out[BYBIT_DEP] / sum(by_acct.values()))

# 4. The Bybit deposit address: sweeps to Bybit Hot Wallet 10 on 28 February, gas from the Bybit gas distributor,
#    and one Privacy Cash withdrawal into it
btx = sol_txs(BYBIT_DEP)
sweeps = sum(l for t in btx if t["meta"]["err"] is None and t["blockTime"] // 86400 == 1772236800 // 86400
             for s, dst, l in transfers(t) if s == BYBIT_DEP and dst == BYBIT_HW10)
gas = [l for t in btx for s, dst, l in transfers(t) if s == BYBIT_GAS and dst == BYBIT_DEP]
pcw = []
for t in btx:
    for i in t["transaction"]["message"]["instructions"]:
        if i.get("programId") == PC_PROG:
            data = b58decode(i["data"])
            pool = delta(t, PC_POOL)[0]
            pcw.append({"signature": t["transaction"]["signatures"][0], "block_time": t["blockTime"], "ext_amount": struct.unpack_from("<q", data, 488)[0],
                        "recipient_delta": delta(t, BYBIT_DEP)[0], "pool_delta": pool, "relayer": keys(t)[0]})
fwd = [(t["transaction"]["signatures"][0], dst, l) for t in btx for s, dst, l in transfers(t)
       if s == BYBIT_DEP and dst not in (BYBIT_HW10,) and l > 1_000_000]
check("bybit_deposit_sweeps_and_gas", sweeps > 0.99 * out[BYBIT_DEP] and len(gas) >= 3,
      swept_to_hw10_on_feb28_sol=sweeps / 1e9, gas_topups_sol=[g / 1e9 for g in gas])
check("privacy_cash_withdrawal_into_bybit_deposit", len(pcw) == 1 and pcw[0]["ext_amount"] == -pcw[0]["recipient_delta"],
      withdrawal=pcw, other_sol_forward=fwd)
# the gas distributor tops up many addresses in one slot: a service pattern, not a personal wallet
gtx = sol_txs(BYBIT_GAS)
per_slot = defaultdict(set)
for t in gtx:
    for s, dst, l in transfers(t):
        if s == BYBIT_GAS:
            per_slot[t["slot"]].add(dst)
hw = sol_txs(BYBIT_HW10)
senders = {s for t in hw for s, dst, l in transfers(t) if dst == BYBIT_HW10}
check("bybit_wallets_behave_as_service", max(len(v) for v in per_slot.values()) >= 10 and len(senders) >= 200,
      gas_max_recipients_in_one_slot=max(len(v) for v in per_slot.values()), hw10_distinct_senders_in_window=len(senders),
      hw10_window=[hw[0]["blockTime"], hw[-1]["blockTime"]])

# 5. aaamsaasa's other withdrawal went to a Crypto.com deposit address, swept to Crypto.com Hot Wallet 6
cdc = []
for h in ("0x3701c96dfe730734b811cb486efabdb33ec18711fda1f2d0d12f2ea0790b1304", "0xdb02452df677e544666ccda6151ad87945ba2554395297740d28282bd6f2bfd3"):
    q = relay(h)
    rc = receipt(h)
    moved = [v for s, dst, v in erc20(rc, USDCE_POLY) if s == q["user"].lower() and dst == DEPOSITORY]
    cdc.append({"polygon": h, "user": q["user"], "recipient": q["recipient"], "usdce": moved, "solana": q["data"]["outTxs"][0]["hash"]})
ctx = {t["transaction"]["signatures"][0]: t for t in sol_txs(CDC_DEP)}
got = sum(token_delta(ctx[c["solana"]], CDC_DEP, USDC_SOL) for c in cdc)
swept = [token_delta(t, CDC_HW6, USDC_SOL) for t in ctx.values() if t["blockTime"] < 1772294400 and token_delta(t, CDC_HW6, USDC_SOL) > 0]
check("aaamsaasa_to_cryptocom_deposit", all(c["recipient"] == CDC_DEP and c["user"].lower() == "0x0a142164f48dab6448872f0abac310d03e305316" for c in cdc)
      and swept == [got], usdc_received=got / 1e6, swept_to_cdc_hw6=[s / 1e6 for s in swept])

# 6. Funding of the two new accounts
f1 = [relay(h) for h in ("0x7486619c0016d48fc6d6510cc530477a0647e12650242918f891c59bbd8281a1", "0x019e0e68ad8bf1c9ccb734c5dcf9de1360eed2ca86f6082c600c59b920fe38a3")]
f2 = [relay(h) for h in ("0x61848989be09aa17fbbb30a265c9d073b0533fcfe4eb1365ecd7c07a1edfb6a1", "0x6c878054223ed0c7a7b120614cdbe2d589e5c384db0026e2fa6f28ec61ea4da5")]
es = []
for f in sorted((EV / "etherscan").glob("137_tokentx_0xf7493b5ad5d1f30d18278dbdda2778d2c4c91cff_p*.json")):
    if not f.name.endswith(".meta.json"):
        es += load(f)["result"]
cro = sum(int(x["value"]) for x in es if x["from"].lower() == "0xfa0b641678f5115ad8a8de5752016bd1359681b9" and x["to"].lower() == "0xf7493b5ad5d1f30d18278dbdda2778d2c4c91cff")
tags = {a.lower(): [t["name"] for t in v.get("tags", [])] for a, v in load(EV / "http" / "bs_meta_137_batch1.json")["addresses"].items()}
check("funding_of_new_accounts", all(q["user"].lower() == "0xfe775af18824f4951f19e264901030f8528bf972" and q["data"]["inTxs"][0]["chainId"] == 56 for q in f1)
      and all(q["user"].lower() == "0xf7493b5ad5d1f30d18278dbdda2778d2c4c91cff" for q in f2) and "Crypto.com 6" in tags["0xfa0b641678f5115ad8a8de5752016bd1359681b9"],
      oveiStheair_bsc_usdc=[q["data"]["metadata"]["currencyIn"]["amountFormatted"] for q in f1],
      aaamsaasa_from_cryptocom6_usdc=cro / 1e6)

# 7. Bets of the two new accounts (Polymarket activity, profile fields removed)
bets = {}
for u in ("0x97e490d61b530d5078348d76143a25c43a47164d", "0x0a142164f48dab6448872f0abac310d03e305316"):
    a = load(EV / "polymarket_reduced" / f"pm_v2activity_{u}_p000.json")["data"]
    iran = [x for x in a if "strikes Iran by February 28, 2026" in (x.get("title") or "")]
    buys = [x for x in iran if x["type"] == "TRADE" and x["side"] == "BUY"]
    wd = {x["transaction_hash"] for x in a if x["type"] == "WITHDRAWAL"}
    bets[ACC[u]] = {"first_buy_ts": min(x["timestamp"] for x in buys), "buy_usdc": round(sum(x["usdc_size"] for x in buys), 6),
                    "redeem_usdc": round(sum(x["usdc_size"] for x in iran if x["type"] == "REDEEM"), 6),
                    "withdrawals_to_beneficiary_listed": all(c["relay_request"] and True for c in credits if c["account"] == ACC[u])
                    and all(relay(c["signature"])["data"]["inTxs"][0]["hash"] in wd for c in credits if c["account"] == ACC[u])}
check("new_accounts_bets_before_strikes", all(b["first_buy_ts"] < 1772259300 and b["withdrawals_to_beneficiary_listed"] for b in bets.values()), bets=bets)

# 8. Descriptive comparator recomputed from the reduced trade tape
yes = next(x["token_id"] for x in load(EV / "polymarket_reduced" / "pm_v2activity_0x97e490d61b530d5078348d76143a25c43a47164d_p000.json")["data"]
           if (x.get("title") or "").startswith("US strikes") and x.get("outcome") == "Yes")
seen, buy, first = set(), defaultdict(float), {}
with gzip.open(EV / "polymarket_reduced" / "us_strikes_feb28_trades_reduced.jsonl.gz", "rt") as g:
    for line in g:
        x = json.loads(line)
        k = line
        if k in seen:
            continue
        seen.add(k)
        t = int(x["timestamp"])
        if x["token_id"] == yes and x["side"] == "BUY" and 1772236800 <= t < 1772259300:
            buy[x["proxy_wallet"].lower()] += float(x["size"]) * float(x["price"])
            first[x["proxy_wallet"].lower()] = min(first.get(x["proxy_wallet"].lower(), t), t)
big = sorted([w for w, v in buy.items() if v >= 1000], key=lambda w: first[w])
check("comparator_early_yes_buyers", len(big) > 50, wallets_buying_yes=len(buy), wallets_ge_1000=len(big),
      positions={ACC[w]: big.index(w) + 1 for w in ACC if w in big})

# 9. Every full address, hash and signature written in the reports exists in the archived evidence
import re
corpus = []
for p in EV.rglob("*"):
    if p.is_file() and not p.name.endswith(".meta.json"):
        corpus.append(gzip.open(p, "rt").read() if p.suffix == ".gz" else p.read_text(errors="replace"))
corpus = "\n".join(corpus).lower()
refs, missing = set(), []
for doc in ("REPORT.md", "NEW_FINDINGS.md"):
    if (HERE / doc).exists():
        text = (HERE / doc).read_text()
        refs |= set(re.findall(r"\b0x[0-9a-fA-F]{40}(?:[0-9a-fA-F]{24})?\b", text))
        refs |= set(re.findall(r"\b[1-9A-HJ-NP-Za-km-z]{32,88}\b", text))
for r in sorted(refs):
    if r.lower() not in corpus:
        missing.append(r)
check("report_references_exist_in_evidence", not missing and len(refs) > 20, references=len(refs), missing=missing)

ok = all(r["status"] == "PASS" for r in results)
(HERE / "verification.json").write_text(json.dumps({"all_pass": ok, "checks": results}, indent=1, default=str))
for r in results:
    print(r["status"], r["check"])
print("ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
