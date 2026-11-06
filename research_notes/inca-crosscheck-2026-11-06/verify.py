"""Independent verifier of the Inca cross-check. Needs only this folder and PR 27's accounts.csv next to it.
It does not import the note's scripts: transfers, flows, measures and tests are re-implemented here.

  python3 -I verify.py            prints one line per check and writes verification.json
"""
import csv, gzip, hashlib, json, math, re, sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

N = Path(__file__).resolve().parent
EV = N / "evidence"
PR27 = N.parent / "iran-cluster-e-network-2026-11-05"
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
USDC = {"0x2791bca1f2de4661ed88a30c99a7a9449aa84174": "USDC.e", "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359": "USDC"}
POOL = "0xd36ec33c8bed5a9f7b6630855f1533455b98a418"
# Inca Digital, "Insider Detection on Polymarket", section 3.1, page 9 (PDF sha256 in REPORT.md)
INCA = {"0x6c2c072a0aa8fb8b4faf9aecae5520541f3b2d2a": ("9TungSahur", 36790.56),
        "0xd5de5cad9ef22b16317fe30a4234c72ece3eac1a": ("PorcoRosso", 85120.83),
        "0x0afc7ce56285bde1fbe3a75efaffdfc86d6530b2": ("ricosuave666", 128736.79),
        "0xcb18ea2923d957bd9cf049cce60a87638722f867": ("DonkeyDonkey999", 34996.87),
        "0xa3a6fa49a39a4bf84cf510b7c8a2ab8be8508c44": ("truthlord", 52329.69)}
MARKET = "0x7f39808829da93cfd189807f13f6d86a0e604835e6f9482d8094fac46b3abaac"
RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append({"check": name, "ok": bool(ok), "detail": detail})
    print(("PASS " if ok else "FAIL ") + name + (f" | {detail}" if detail else ""))


def load(p):
    b = p.read_bytes()
    return json.loads(gzip.decompress(b) if p.suffix == ".gz" else b)


def iso(t):
    return datetime.fromtimestamp(int(t), timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def logs(receipt):
    out = []
    for lg in receipt["logs"]:
        if lg["address"].lower() in USDC and lg["topics"] and lg["topics"][0] == TRANSFER and len(lg["topics"]) == 3:
            out.append(("0x" + lg["topics"][1][26:].lower(), "0x" + lg["topics"][2][26:].lower(), int(lg["data"], 16) / 1e6))
    return out


def es(addr, action):
    p = EV / "etherscan" / f"{addr}_{action}.json.gz"
    return load(p)["rows"] if p.exists() else None


def real_usd(r):
    return r["contractAddress"].lower() in USDC or r["tokenSymbol"] == "USDT0" and r["contractAddress"].lower() == USDT0


USDT0 = "0xc2132d05d31c914a87c6611c10748aeb04b58e8f"
A267, F3F77, EFCE = ("0xa26792e288079f9ee81d09e81058a5edbca522e4", "0x3f77a673a29e8cea345f0ed1f4f40a914156fc32",
                     "0xefce5b1cd37a24b752308c93e51fb7da69e220da")
W529, SINK, RELAYER = ("0x529c2eef349edaf657cb23c2493bfd4369eb09bf", "0x852dc1c875f0117ea0808610010893e4c576b6a9",
                       "0x80e54311d48127cb66df9d65bf430796c8cf42be")
B0913, BINANCE_HOT = "0x09133414aa940fbe81a81d9c936275685c2aea88", "0xe7804c37c13166ff0b37f5ae0bb07a3aebb6e245"
TS9, DD = "0x6c2c072a0aa8fb8b4faf9aecae5520541f3b2d2a", "0xcb18ea2923d957bd9cf049cce60a87638722f867"
WETH = "0x7ceb23fd6bc0add59e62ac25578270cff1b9f619"


def behaviour(tok, rec, act, net):
    # 0xa26792e2 forwards every real inflow within 30 s, each time just after a gas top-up from a service hot wallet
    t = [r for r in es(A267, "tokentx") if int(r["value"]) > 0 and r["contractAddress"].lower() in set(USDC) | {WETH}]
    ins = [r for r in t if r["to"].lower() == A267]
    outs = [r for r in t if r["from"].lower() == A267]
    gas = [r for r in es(A267, "txlist") if r["to"].lower() == A267 and int(r["value"]) > 0]
    fw = all(any(o["contractAddress"] == i["contractAddress"] and o["value"] == i["value"]
                 and 0 <= int(o["timeStamp"]) - int(i["timeStamp"]) <= 30 for o in outs) for i in ins)
    gs = all(any(g["from"].lower() in (F3F77, EFCE) and 0 <= int(o["timeStamp"]) - int(g["timeStamp"]) <= 20 for g in gas) for o in outs)
    check("0xa26792e2 forwards each of its 4 inflows within 30 s after a gas top-up by 0x3f77a673 or 0xefce5b1c",
          len(ins) == 4 and fw and gs, f"{len(ins)} inflows, {len(outs)} forwards, {len(gas)} gas top-ups")
    # every deposit of 9TungSahur follows an inflow of 0xa26792e2
    deps = sorted((r["timestamp"], r["usdc_size"]) for k, r in act.items() if k[0] == TS9 and k[2] == "DEPOSIT")
    ins_t = sorted(int(i["timeStamp"]) for i in ins)
    lag = [ts - t for (ts, _), t in zip(deps, ins_t)]  # k-th deposit against k-th inflow
    check("9TungSahur's 4 deposits are its only deposits and come, in order, 40 s to 20 min after the 4 inflows of 0xa26792e2",
          len(deps) == 4 and len(ins_t) == 4 and all(0 < x <= 1200 for x in lag), f"lags in s: {lag}")
    fees = [round(u / (int(i["value"]) / 1e6), 4) for (ts, u), i in zip(deps[:3], sorted(ins, key=lambda r: int(r["timeStamp"]))[:3])]
    check("the three USDC legs of 11 June 2025 are credited at 98.7 % to 98.9 %", all(0.987 <= f <= 0.989 for f in fees), f"{fees}")
    # 0x529c2eef: one gas funder (the relayer of PR 27's EIP-7702 wallet), every outflow to the same sink
    tx = es(W529, "txlist")
    funders = {r["from"].lower() for r in tx if r["to"].lower() == W529 and int(r["value"]) > 0}
    t = [r for r in es(W529, "tokentx") if int(r["value"]) > 0 and real_usd(r)]
    outs = {r["to"].lower() for r in t if r["from"].lower() == W529}
    code = lambda a: load(EV / "polygon_code" / f"{a}.json")["body"]["result"]
    check("0x529c2eef and PR 27's 0xa6c22144 carry the same EIP-7702 delegation",
          code(W529) == code("0xa6c221448af73af8350291c5cdcd877b39683766") == "0xef01000000fb7702036ff9f76044a501ac1aa74cbab16b", code(W529))
    check("0x529c2eef: its only gas funder is relayer 0x80e54311 and all its outflows go to 0x852dc1c8",
          funders == {RELAYER} and outs == {SINK}, f"gas funders {sorted(funders)}, outflow destinations {sorted(outs)}")
    # 0x09133414: every USDC inflow swept to a Binance hot wallet within 10 minutes
    t = [r for r in es(B0913, "tokentx") if int(r["value"]) > 0 and r["contractAddress"].lower() in USDC]
    ins = [r for r in t if r["to"].lower() == B0913]
    outs = [r for r in t if r["from"].lower() == B0913]
    swept = all(any(o["to"].lower() == BINANCE_HOT and 0 <= int(o["timeStamp"]) - int(i["timeStamp"]) <= 600 for o in outs) for i in ins)
    tot_in, tot_out = sum(int(r["value"]) for r in ins), sum(int(r["value"]) for r in outs if r["to"].lower() == BINANCE_HOT)
    check("0x09133414: every USDC inflow is swept to 0xe7804c37 within 10 minutes, amounts equal",
          swept and tot_in == tot_out, f"{len(ins)} inflows, {tot_in / 1e6:,.6f} in, {tot_out / 1e6:,.6f} out")
    # 0xbfaa1d49: gas from Stake.com 9, then the whole USDC balance to Stake.com 9
    BF, STAKE = "0xbfaa1d49144c84dac4163704e5ba3e876a7c345a", "0x019d0706d65c4768ec8081ed7ce41f59eef9b86c"
    gas = [r for r in es(BF, "txlist") if r["to"].lower() == BF and int(r["value"]) > 0]
    t = [r for r in es(BF, "tokentx") if r["contractAddress"].lower() in USDC and int(r["value"]) > 0]
    tin = sum(int(r["value"]) for r in t if r["to"].lower() == BF); tout = sum(int(r["value"]) for r in t if r["to"].lower() == STAKE)
    check("0xbfaa1d49: its only gas comes from Stake.com 9 and its whole USDC inflow goes to Stake.com 9",
          {g["from"].lower() for g in gas} == {STAKE} and tin == tout > 0, f"in {tin / 1e6:.6f}, out to Stake.com 9 {tout / 1e6:.6f}")
    # 0xe559eb45: first inflow 74,680.134173 USDC from ricosuave666's exit wallet on 26 June 2025, gas from the same wallet
    E5, F09 = "0xe559eb45d13e9a2e0e5d69c181de790f38e4b9a0", "0xf09366c69108ddad2305ee1764a60efe92b48477"
    t = sorted(es(E5, "tokentx"), key=lambda r: int(r["timeStamp"]))
    first = next(r for r in t if r["to"].lower() == E5 and int(r["value"]) > 0)
    tx = sorted(es(E5, "txlist"), key=lambda r: int(r["timeStamp"]))
    first_out = next(r for r in tx if r["from"].lower() == E5)
    gas = [r for r in tx if r["to"].lower() == E5 and int(r["value"]) > 0 and r["from"].lower() == F09]
    check("0xe559eb45: first inflow 74,680.134173 USDC from 0xf09366c6 on 26 June 2025, gas from the same wallet, first own tx nonce 0",
          first["from"].lower() == F09 and int(first["value"]) == 74680134173 and iso(first["timeStamp"]).startswith("2025-06-26")
          and first_out["nonce"] == "0" and int(first_out["timeStamp"]) > int(first["timeStamp"]) and len(gas) >= 1,
          f"first inflow {iso(first['timeStamp'])}, first own tx {iso(first_out['timeStamp'])}, gas from 0xf09366c6: {len(gas)}")
    rows = load(EV / "polymarket_full" / "0x0afc7ce56285bde1fbe3a75efaffdfc86d6530b2.json")["rows"]
    red = [r for r in rows if r["type"] == "REDEEM" and r["condition_id"] == MARKET]
    check("ricosuave666 redeemed 162,663.94 USDC on the market on 13 June 2025",
          len(red) == 1 and abs(red[0]["usdc_size"] - 162663.94) < 0.01 and iso(red[0]["timestamp"]).startswith("2025-06-13"),
          f"{[(iso(r['timestamp']), r['usdc_size']) for r in red]}")
    # key labels (Blockscout metadata, single source)
    want = {"0xf89d7b9c864f589bbf53a82105107622b35eaa40": "Bybit 5", "0xfa0b641678f5115ad8a8de5752016bd1359681b9": "Crypto.com 6",
            "0x019d0706d65c4768ec8081ed7ce41f59eef9b86c": "Stake.com 9", "0xe7804c37c13166ff0b37f5ae0bb07a3aebb6e245": "Binance 48",
            "0xc38e4e6a15593f908255214653d3d947ca1c2338": "Mayan Swift", "0x1929347e025d4f5f8d6b2bd2261e2f4efcacd215": "CheckoutPool",
            "0x4b6f17856215eab57c29ebfa18b0a0f74a3627bb": "Kraken 72", "0xa85c29b94f8a22a7268facee89ef4eca051be2ce": "Bybit: Wallet 131"}
    tags = defaultdict(set)
    for p in (EV / "blockscout").glob("*.json"):
        for k, v in (load(p)["body"].get("addresses") or {}).items():
            tags[k.lower()] |= {x["name"] for x in v.get("tags", [])}
    miss = [f"{a[:10]} {n}" for a, n in want.items() if not any(n in x for x in tags.get(a, ()))]
    check("Blockscout labels of the exchange and service wallets cited", not miss, f"missing: {miss}")
    # the three other Inca accounts are in no file of PR 27's network notes
    found = []
    for d in ("iran-cluster-e-network-2026-11-05", "iran-solana-beneficiary-2026-11-05"):
        for p in (N.parent / d).rglob("*"):
            if p.is_file():
                b = p.read_bytes().lower()
                found += [f"{a[:10]} in {p.name}" for a in ("0xd5de5cad9ef22b16317fe30a4234c72ece3eac1a", "0x0afc7ce56285bde1fbe3a75efaffdfc86d6530b2",
                                                             "0xa3a6fa49a39a4bf84cf510b7c8a2ab8be8508c44") if a.encode() in b]
    check("PorcoRosso, ricosuave666 and truthlord appear in no file of PR 27's two network notes", not found, f"{found[:3]}")
    # the three other Inca accounts: no counterparty among the PR 27 network, its customer-specific addresses or the other Inca accounts
    plan = (N / "PLAN_CONTROLS.md").read_text().split("## N27")[1].split("## Comparison")[0]
    n27 = {x.lower() for x in re.findall(r"0x[0-9a-fA-F]{40}", plan)} | set(re.findall(r"`([1-9A-HJ-NP-Za-km-z]{32,44})`", plan)) | set(net)
    own = {"0xd5de5cad9ef22b16317fe30a4234c72ece3eac1a": "0xfefea9427bef554cc572bc4e887a0b9642fd8f4e",
           "0x0afc7ce56285bde1fbe3a75efaffdfc86d6530b2": "0xf09366c69108ddad2305ee1764a60efe92b48477",
           "0xa3a6fa49a39a4bf84cf510b7c8a2ab8be8508c44": "0x4d1489edf5236653ae36db319f5267e1a921a6de"}
    for a, wallet in own.items():
        cps = set()
        for (w, h, typ), r in act.items():
            if w == a and h in rec:
                cps |= {x for f, to, _ in logs(rec[h]["receipt"]) for x in (f, to)}
        for q in load(EV / "relay" / f"{a}.json.gz")["requests"]:
            cps |= {q["user"], q["user"].lower(), q["recipient"], q["recipient"].lower()}
        for r in es(wallet, "tokentx") or []:
            cps |= {r["from"].lower(), r["to"].lower()}
        hits = sorted((cps & (n27 | set(INCA))) - {a})
        check(f"{INCA[a][0]}: no funder or recipient (account, exit wallet {wallet[:10]}, Relay) in N27 or among the other Inca accounts",
              not hits, f"{len(cps)} counterparties read; hits {hits}")


def controls():
    """Recomputes M1 to M3 of PLAN_CONTROLS.md from evidence/ with this file's own code."""
    pop = json.loads((N / "data" / "population.json").read_text())
    ctrl, inca3 = pop["controls"], ["0xd5de5cad9ef22b16317fe30a4234c72ece3eac1a", "0x0afc7ce56285bde1fbe3a75efaffdfc86d6530b2",
                                    "0xa3a6fa49a39a4bf84cf510b7c8a2ab8be8508c44"]
    S = sorted(set(ctrl) | set(INCA))
    tape = load(next(EV.glob("trades_*.json.gz")))["rows"]
    yes = "19456040549238228129383854351183747737493394931814797928509171842469189313430"
    T = min(int(r["timestamp"]) for r in tape if r["token_id"] == yes and float(r["price"]) >= 0.90)
    buy = defaultdict(float)
    for r in tape:
        if r["token_id"] == yes and r["side"] == "BUY" and 1749672625 <= int(r["timestamp"]) < T and float(r["price"]) <= 0.50:
            buy[r["proxy_wallet"].lower()] += float(r["size"]) * float(r["price"])
    P = sorted(w for w, v in buy.items() if v >= 1000)
    net = {r["address"] for r in csv.DictReader(open(PR27 / "accounts.csv")) if r["group"] == "cluster E network"}
    check("population and controls rebuilt from the archived tape", P == [r["wallet"] for r in pop["population"]]
          and sorted(set(P) - set(INCA) - net) == sorted(ctrl) and T == pop["T_utc"], f"P = {len(P)}, controls = {len(ctrl)}, T = {iso(T)}")
    rec = {r["hash"]: r["receipt"] for r in load(EV / "polygon_receipts.json.gz")}
    flows, legs = [], {}
    for w in S:
        for r in load(EV / "polymarket_dw" / f"{w}.json")["rows"]:
            h = r["transaction_hash"].lower()
            legs[(w, h)] = (w, r["type"], int(r["timestamp"]), float(r["usdc_size"]), h)
            lg = logs(rec[h])
            if r["type"] == "WITHDRAWAL":
                for f, t, _ in lg:
                    if f == w and t != w:
                        flows += [(w, "W", t2, h) for f2, t2, _ in lg if f2 == POOL and t2 not in (w, POOL)] if t == POOL else [(w, "W", t, h)]
            else:
                for f, t, _ in lg:
                    if t == w and f != w:
                        flows += [(w, "D", f2, h) for f2, t2, _ in lg if t2 == POOL and f2 not in (w, POOL)] if f == POOL else [(w, "D", f, h)]
        for q in load(EV / "relay" / f"{w}.json.gz")["requests"]:
            u, rc = q["user"].lower(), q["recipient"] if not q["recipient"].startswith("0x") else q["recipient"].lower()
            if q["status"] == "success" and u == w and rc != w:
                flows.append((w, "RW", rc, q["id"]))
            elif q["status"] == "success" and rc == w and u != w:
                flows.append((w, "RD", u if u.startswith("0x") else q["user"], q["id"]))
    plan = (N / "PLAN_CONTROLS.md").read_text().split("## N27")[1].split("## Comparison")[0]
    n27 = {x.lower() for x in re.findall(r"0x[0-9a-fA-F]{40}", plan)} | set(re.findall(r"`([1-9A-HJ-NP-Za-km-z]{32,44})`", plan)) | net
    m1 = {w for w, _, x, _ in flows if x in n27}
    tagged = set()
    for p in (EV / "blockscout").glob("rcpt_S_137_*.json"):
        tagged |= {k.lower() for k, v in (load(p)["body"].get("addresses") or {}).items() if v.get("tags")}
    code = {p.stem: load(p)["body"]["result"] for p in (EV / "polygon_code").glob("0x*.json")}
    rcpts = defaultdict(set)
    for w, k, x, _ in flows:
        if k in ("W", "RW"):
            rcpts[x].add(w)
    svc = {POOL, "0xd216153c06e857cd7f72665e0af1d7d82172f494"} | tagged | {a for a, c in code.items() if c not in ("0x", "0x0")}
    unchecked = [a for a in rcpts if a.startswith("0x") and a not in code]
    check("every Polygon recipient of S has an archived eth_getCode", not unchecked, f"{len(rcpts)} recipients, {len(unchecked)} unchecked")
    m2 = {w for a, ws in rcpts.items() if a not in svc and len(ws) > 1 for w in ws}
    L = sorted(legs.values(), key=lambda x: x[2])
    deps = defaultdict(list)
    for x in L:
        if x[1] == "DEPOSIT":
            deps[x[4]].append(x)
    m3, used, pair = set(), set(), defaultdict(int)
    for x in L:
        if x[1] != "WITHDRAWAL":
            continue
        same = [d for d in deps.get(x[4], []) if d[0] != x[0]]
        m3 |= {x[0]} | {d[0] for d in same} if same else set()
        if x[4] in deps:  # a leg whose hash is also a deposit is never matched (plan: direct legs are not matched)
            continue
        for d in L:
            if (d[1] == "DEPOSIT" and d[0] != x[0] and d[4] not in used and 0 < d[2] - x[2] <= 3600
                    and 0.97 * x[3] <= d[3] <= x[3]):
                used.add(d[4]); pair[(x[0], d[0])] += 1; break
    m3 |= {w for k, v in pair.items() if v >= 2 for w in k}
    res = json.loads((N / "data" / "results.json").read_text())["measures"]
    for name, m in (("M1", m1), ("M2", m2), ("M3", m3)):
        kc, k3 = sum(w in m for w in ctrl), sum(w in m for w in inca3)
        k2 = sum(w in m for w in (TS9, DD))
        K, n1, n2 = kc + k3, 3, len(ctrl)
        p = sum(math.comb(K, x) * math.comb(n1 + n2 - K, n1 - x) for x in range(k3, min(K, n1) + 1)) / math.comb(n1 + n2, n1)
        got = res[name]
        check(f"{name} recomputed: controls {kc}/{n2}, Inca three {k3}/3, Inca two {k2}/2, one-sided p {p:.4f}",
              got["controls"][0] == kc and got["inca3"][0] == k3 and got["inca2"][0] == k2
              and abs(got["p_one_sided_inca3_vs_controls"] - p) < 1e-12,
              f"results.json: controls {got['controls'][0]}, Inca three {got['inca3'][0]}, p {got['p_one_sided_inca3_vs_controls']:.4f}")


def main():
    # 1. integrity
    sums = [l.split("  ", 1) for l in (N / "SHA256SUMS.txt").read_text().splitlines() if l]
    bad = [n for h, n in sums if hashlib.sha256((N / n).read_bytes()).hexdigest() != h]
    listed = {n for _, n in sums}
    extra = [str(p.relative_to(N)) for p in EV.rglob("*") if p.is_file() and str(p.relative_to(N)) not in listed]
    check("evidence files match SHA256SUMS.txt", not bad and not extra, f"{len(sums)} files, {len(bad)} changed, {len(extra)} unlisted")

    # 2. the five Inca addresses, PR 27 intersection, per-market cash against Inca's realized profit
    net = {r["address"]: r["account"] for r in csv.DictReader(open(PR27 / "accounts.csv")) if r["group"] == "cluster E network"}
    inter = sorted(a for a in INCA if a in net)
    check("exactly two Inca addresses are PR 27 network accounts", inter == ["0x6c2c072a0aa8fb8b4faf9aecae5520541f3b2d2a",
          "0xcb18ea2923d957bd9cf049cce60a87638722f867"], ", ".join(f"{INCA[a][0]} = {net[a]}" for a in inter))
    for a, (name, profit) in INCA.items():
        rows = load(EV / "polymarket_full" / f"{a}.json")["rows"]
        cash = sum((r["usdc_size"] if r["type"] == "REDEEM" or r["side"] == "SELL" else -r["usdc_size"])
                   for r in rows if r["condition_id"] == MARKET and r["type"] in ("TRADE", "REDEEM"))
        check(f"{name}: cash on the market equals Inca's realized profit within 2 USDC", abs(cash - profit) <= 2,
              f"recomputed {cash:,.2f}, Inca {profit:,.2f}, current username {rows[0].get('name')}")

    # 3. every row of EVIDENCE_INDEX.csv against the archived sources
    rec = {r["hash"]: r for r in load(EV / "polygon_receipts.json.gz")}
    tok, tok_h = {}, {}
    for p in (EV / "etherscan").glob("*_tokentx.json.gz"):
        for r in load(p)["rows"]:
            tok[(r["hash"].lower(), r["from"].lower(), r["to"].lower())] = r
            tok_h[r["hash"].lower()] = r
    rel = {}
    for p in (EV / "relay").glob("*.json.gz"):
        for q in load(p)["requests"]:
            rel[q["id"]] = q
    act = {}
    for d in ("polymarket_full", "polymarket_dw"):
        for p in (EV / d).glob("*.json"):
            for r in load(p)["rows"]:
                act[(r["proxy_wallet"].lower(), r["transaction_hash"].lower(), r["type"])] = r
    n_ok = 0
    rows = list(csv.DictReader(open(N / "EVIDENCE_INDEX.csv")))
    for row in rows:
        f, t, amt, h = row["from_address"].lower(), row["to_address"].lower(), float(row["amount"]), row["tx_hash"].lower()
        ok, why = False, ""
        if row["source"] == "receipt":
            r = rec.get(h)
            lg = logs(r["receipt"]) if r else []
            if row["via"] == POOL:  # Polymarket withdrawal or deposit through the USDC/USDC.e pool: two legs, one receipt
                hit = (any(a == f and b == POOL for a, b, _ in lg)
                       and any(a == POOL and b == t and abs(x - amt) < 1e-6 for a, b, x in lg))
            else:
                hit = any(a == f and b == t and abs(x - amt) < 1e-6 for a, b, x in lg)
            e = tok_h.get(h)
            ts_ok = e is not None and iso(e["timeStamp"]) == row["timestamp_utc"]
            pm = act.get((f, h, "WITHDRAWAL")) or act.get((t, h, "DEPOSIT"))
            ts_ok = ts_ok or (pm is not None and iso(pm["timestamp"]) == row["timestamp_utc"])
            ok, why = bool(hit and ts_ok), f"log {'found' if hit else 'MISSING'}, time {'ok' if ts_ok else 'NOT CHECKED'}"
        elif row["source"] == "etherscan":
            e = tok.get((h, f, t))
            ok = e is not None and abs(int(e["value"]) / 10 ** int(e["tokenDecimal"]) - amt) < 1e-6 and iso(e["timeStamp"]) == row["timestamp_utc"]
            why = "token transfer row" + ("" if ok else " MISSING or different")
        elif row["source"] == "relay":
            q = rel.get(row["relay_id"])
            ok = (q is not None and q["status"] == "success" and q["user"].lower() == f and q["recipient"].lower() == t
                  and abs(float(q["data"]["metadata"]["currencyIn"]["amountFormatted"]) - amt) < 1e-6
                  and q["createdAt"][:19].replace("T", " ") == row["timestamp_utc"]
                  and any(x.get("hash", "").lower() == h for x in q["data"].get("inTxs") or []))
            why = "Relay order" + ("" if ok else " MISSING or different")
        n_ok += ok
        if not ok:
            check(f"index row {row['row_id']}", False, why)
    check("every EVIDENCE_INDEX.csv row is found in its archived source", n_ok == len(rows), f"{n_ok} of {len(rows)}")
    behaviour(tok, rec, act, net)
    controls()
    (N / "verification.json").write_text(json.dumps({"checks": RESULTS, "passed": sum(r["ok"] for r in RESULTS),
                                                     "total": len(RESULTS)}, indent=1))
    print(f"{sum(r['ok'] for r in RESULTS)}/{len(RESULTS)} checks passed")
    return all(r["ok"] for r in RESULTS)


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
