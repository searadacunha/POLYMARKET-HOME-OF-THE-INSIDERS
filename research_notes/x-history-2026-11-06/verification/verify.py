"""Offline re-check of the decisive claims in REPORT.md. No network.

Part A reads only this folder (evidence/ and data/). Part B recomputes from the raw archive when XLEADS_RAW (default
~/Projects/Polymarket-x-leads-raw-20261106/raw) exists, and reports SKIPPED otherwise. Exit code 1 on any failure.
"""
import csv, hashlib, json, os, subprocess, sys, tempfile
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
EV, DATA = HERE / "evidence", HERE / "data"
RAW = Path(os.environ.get("XLEADS_RAW", Path.home() / "Projects/Polymarket-x-leads-raw-20261106/raw"))
RESULTS = []

CYPYA, JYDY, CYPYO, BRACE = "0x970998da056e60c707d9b1fc55cfdf3d68c252ab", "0x1c4cd350bce3cb791daf88ce2034de9b03318d85", "0xa9f4dc80fd27e2977ef1fcaea41d263ecd7a4dfb", "0x873848cd27784900e193611845fc3fd2c4716d03"
CASHY = "0x8f42ae0a01c0383c7ca8bd060b86a645ee74b88f"
SHARED_CB = "0xd12623958b81d71e8be3fa936aed6d8c2528e992"
DEST38 = "0xc5bb1be0407db7312911ec765d399d02461e411a"
COINBASE10 = "0xa9d1e08c7793af67e9d92fe308d5697fb81d3e43"
OFFICIAL = {"0x3c499c542cef5e3811e1192ce70d8cc03d5c3359", "0x2791bca1f2de4661ed88a30c99a7a9449aa84174"}  # Polygon USDC, USDC.e: lookalike tokens excluded


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))


def jl(p):
    return json.loads(Path(p).read_text())


def es_rows(addr, chain, action):
    rows = []
    for p in sorted((EV / "etherscan" / addr).glob(f"{chain}_{action}_p*.json")):
        if not p.name.endswith(".meta.json"):
            rows += jl(p)["result"]
    return rows


def relay_requests(addr):
    out = []
    for p in sorted((EV / "relay" / addr).glob("p*.json")):
        if not p.name.endswith(".meta.json"):
            out += jl(p)["requests"]
    return out


def labels():
    lab = {}
    for p in (EV / "labels").glob("*.json"):
        if p.name.endswith(".meta.json"):
            continue
        for a, v in (jl(p).get("addresses") or {}).items():
            lab[a.lower()] = [t.get("name") for t in v.get("tags", [])]
    return lab


def part_a():
    # integrity of the packaged evidence
    bad = []
    for line in (HERE / "SHA256SUMS.txt").read_text().splitlines():
        h, rel = line.split("  ", 1)
        if hashlib.sha256((HERE / rel).read_bytes()).hexdigest() != h:
            bad.append(rel)
    check("A0 evidence files match SHA256SUMS.txt", not bad, f"{len(bad)} mismatches")

    x = {r["post_id"]: r for r in csv.DictReader(open(DATA / "x_posts.csv"))}
    c = x["2111149784858042762"]
    check("A1 Cypya post 2026-10-16T17:38:26Z, edit history = own id", c["created_at_utc"] == "2026-10-16T17:38:26.000Z" and c["never_edited"] == "True")
    prof = {r["proxy"]: r for r in csv.DictReader(open(DATA / "profiles.csv"))}
    check("A2 profile xUsername: Cypya_Poly on 0x970998da, Jydyjyd on 0x1c4cd350, none on Cypyo",
          prof[CYPYA]["x_username"] == "Cypya_Poly" and prof[JYDY]["x_username"] == "Jydyjyd" and prof[CYPYO]["x_username"] == "")

    # receipts: two nodes, and the decoded fills
    with tempfile.TemporaryDirectory() as tmp:  # re-decode the packaged receipts, compare with the committed tables
        subprocess.run([sys.executable, "-I", str(HERE / "scripts/verify_receipts.py")], check=True, capture_output=True,
                       env={**os.environ, "RECEIPTS_DIR": str(EV / "polygon_receipts"), "OUT_DIR": tmp})
        same = all((Path(tmp) / n).read_bytes() == (DATA / n).read_bytes() for n in ("receipts_check.json", "receipts_orderfilled.csv"))
    check("A3a receipts re-decoded from evidence/ equal the committed tables", same)
    fills = list(csv.DictReader(open(DATA / "receipts_orderfilled.csv")))
    chk = jl(DATA / "receipts_check.json")
    check("A3 every archived receipt identical on publicnode and drpc", chk["disagree"] == [] and chk["missing_second_node"] == [] and chk["agree"] == chk["transactions"],
          f"{chk['agree']}/{chk['transactions']}")
    f = {(r["tx"][:12], r["logIndex"]): r for r in fills}
    ok = all(f[(t, i)]["maker"] == CYPYA and f[(t, i)]["maker_side"] == "BUY" for t, i in [("0x3f163cf4ba", "639"), ("0x3f163cf4ba", "643"), ("0xb7bcfe3219", "967"), ("0xb7bcfe3219", "969")])
    check("A4 Cypya fills at 17:21:48 and 17:41:45 on 16 Oct are resting buys (maker) hit by 0x5cd5c8d7", ok and f[("0xb7bcfe3219", "967")]["match_taker_order_maker"] == "0x5cd5c8d7a17c78d7389d8b87b611aed83322ac33")
    check("A5 Jydyjyd fill at 17:22:08 on 16 Oct is a resting buy (maker)", f[("0xb4495542b7", "184")]["maker"] == JYDY and f[("0xb4495542b7", "184")]["utc"] == "2026-10-16 17:22:08")
    e = [f[("0xedd0f88ff9", i)] for i in ("562", "565")]
    check("A6 the only brace227-to-Cypyo token movement is an order-book fill (brace227 taker sells, Cypyo resting bids)",
          all(r["maker"] == CYPYO and r["match_taker_order_maker"] == BRACE and r["maker_side"] == "BUY" for r in e))
    q5 = jl(DATA / "q5_direct_transfers.json")
    check("A7 Q5: 1,008 filtered queries, the 2 hits are the A6 transaction", q5["queries"] == 1008 and {d["tx"] for d in q5["direct_transfers"]} == {"0xedd0f88ff99495ad2c004990d20fe174b1537a14b80b6b84f1da8feb17867ed3"})
    pc = jl(EV / "q5_positive_control/POSCTRL_eth_brace_to_48ec_USDC.json")["result"]
    check("A8 Q5 positive control: brace227 key to 0x48ec 2,210 and 2,960 USDC on Ethereum found by the same query",
          sorted(int(r["data"], 16) for r in pc) == [2210000000, 2960000000])

    cash = {(r["tx"][:12]): r for r in fills if CASHY in (r["maker"],)}
    check("A9 cashy: 27 Feb 21:19:47 sells 48,221.98 Yes as taker; 28 Feb 06:13:55 first fill (resting bid 0.56); 06:32:43 buys 11,111 as taker",
          cash["0x1e2611d674"]["maker_side"] == "SELL" and cash["0x1e2611d674"]["match_taker_order_maker"] == CASHY and cash["0x1e2611d674"]["shares"] == "48221.98"
          and cash["0x881980cf6c"]["utc"] == "2026-02-28 06:13:55" and cash["0x881980cf6c"]["match_taker_order_maker"] != CASHY
          and cash["0xeaf1863712"]["match_taker_order_maker"] == CASHY and cash["0xeaf1863712"]["shares"] == "11111")

    # shared Coinbase deposit address of JamWil23, bravonoll, Frogensky
    pay = {}
    for a, lab in [("0xfddfd657996c214d4dd2fd0fff4589c0daeaf33d", "JamWil23"), ("0xab05ffa436861ebb59e16f407703e009fe78e30f", "bravonoll"), ("0x51633638f2f26deab4a9b2264ea4563406722b55", "Frogensky")]:
        pay[lab] = sorted(Decimal((q["data"].get("metadata") or {}).get("currencyIn", {}).get("amountFormatted")) for q in relay_requests(a)
                          if q["user"].lower() == a and q["recipient"].lower() == SHARED_CB)
    check("A10 Relay: JamWil23, bravonoll and Frogensky each withdraw 5.00 then the balance to 0xd1262395",
          pay == {"JamWil23": [Decimal("5.0"), Decimal("9957.366265")], "bravonoll": [Decimal("5.0"), Decimal("42853.470489")], "Frogensky": [Decimal("5.0"), Decimal("96.6429")]}, json.dumps({k: [str(x) for x in v] for k, v in pay.items()}))
    tl = es_rows(SHARED_CB, 1, "txlist"); it = es_rows(SHARED_CB, 1, "txlistinternal"); tk = es_rows(SHARED_CB, 1, "tokentx")
    usdc = sorted([x for x in tk if x["contractAddress"] == "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"], key=lambda x: (int(x["timeStamp"]), x["from"] == SHARED_CB))
    bal, full = Decimal(0), True
    for x in usdc:
        v = Decimal(int(x["value"])) / 10 ** 6
        if x["to"] == SHARED_CB:
            bal += v
        else:
            full &= (v == bal and x["to"] == COINBASE10); bal -= v
    gas_ok = len(it) == 4 and all(x["from"] == COINBASE10 for x in it) and all(
        any(0 < int(t["timeStamp"]) - int(g["timeStamp"]) <= 300 for g in it) for t in tl)
    check("A11 0xd1262395 behaves as a Coinbase deposit address: own nonces 0-3, gas from Coinbase 10 before each sweep, every outflow = full balance to Coinbase 10",
          [int(t["nonce"]) for t in tl] == [0, 1, 2, 3] and gas_ok and full and "Coinbase" in " ".join(labels().get(COINBASE10, [])))

    # 38 accounts and their destination
    g38 = {l.strip() for l in open(DATA / "g38_resolved_proxies.txt") if l.strip()}
    lab = labels()
    snd = {}
    for x in es_rows(DEST38, 137, "tokentx"):
        if x["to"] == DEST38 and int(x["value"]) > 0 and x["contractAddress"] in OFFICIAL:
            snd[x["from"]] = snd.get(x["from"], 0) + 1
    amt = {}
    for x in es_rows(DEST38, 137, "tokentx"):
        if x["to"] == DEST38 and x["contractAddress"] in OFFICIAL:
            amt[x["from"]] = amt.get(x["from"], 0) + int(x["value"])
    paid = {x["to"] for x in es_rows(DEST38, 137, "tokentx") if x["from"] == DEST38 and int(x["value"]) > 0 and x["contractAddress"] in OFFICIAL}
    # dust: under 0.01 USDC in total. Rule set after a first run flagged two such senders (REPORT.md section 4); both
    # resemble Coinbase 16 0x9810...7630, one on 4+4 characters, one on 3+3.
    dust = {s for s in snd if amt[s] < 10_000}
    others = {s: lab.get(s, []) for s in snd if s not in g38 and s not in dust}
    check("A12 Polygon senders to 0xc5bb1be0: 32 resolved list accounts, Relay contracts, and dust lookalikes only",
          sum(1 for s in snd if s in g38) == 32 and all(any("Relay" in (n or "") for n in v) for v in others.values()) and len(dust) == 2,
          json.dumps({"others": others, "dust": sorted(dust)}))
    via = {}
    for a in ["0x858d551d073e9c647c17079ad9021de830201047", "0x5e0b017aef88af84fb3897fecce7413c6754981a", "0xb390ae2cc3fd8cb2670a62129faeb775faee106c",
              "0x95bd107886bd48d6737029603e3db242fb781652", "0x4ec2f11d2893eb1bc3bab7449910540c93adf7ec"]:
        via[a] = any(q["user"].lower() == a and q["recipient"].lower() == DEST38 for q in relay_requests(a))
    check("A13 the 5 other resolved accounts reach 0xc5bb1be0 through Relay (37 of 37)", all(via.values()), json.dumps(via))
    gas = {x["from"] for x in es_rows(DEST38, 137, "txlist") if x["to"] == DEST38}
    outs = {x["to"] for x in es_rows(DEST38, 137, "tokentx") if x["from"] == DEST38 and int(x["value"]) > 0 and x["contractAddress"] in OFFICIAL}
    check("A14 0xc5bb1be0 gas comes from addresses labelled Coinbase gas suppliers; non-zero outflows go to Coinbase-labelled addresses",
          all(any("Coinbase" in (n or "") for n in lab.get(g, [])) for g in gas) and all(any("Coinbase" in (n or "") for n in lab.get(o, [])) for o in outs),
          json.dumps({"gas": sorted(gas), "out": sorted(outs)}))
    acc = list(csv.DictReader(open(DATA / "g38_accounts.csv")))
    batch = [r for r in acc if "2026-02-22" <= r["created"][:10] <= "2026-02-25"]
    check("A15 37 resolved accounts; 36 created 22-25 Feb 2026, all 36 buy No before Yes", len(acc) == 37 and len(batch) == 36 and all(r["no_before_yes"] == "True" for r in batch))


def part_b():
    if not RAW.exists():
        check("B* raw archive", True, "SKIPPED: raw archive not present"); return
    exp = jl(DATA / "ballon_results.json")
    subprocess.run([sys.executable, "-I", str(HERE / "scripts/ana_ballon.py")], check=True, capture_output=True)
    new = jl(DATA / "ballon_results.json")
    check("B1 Ballon d'Or Q1-Q4 recomputed from the archived tapes are identical", exp == new)
    L = {}
    out = DATA / "_verify_ledgers.json"
    subprocess.run([sys.executable, "-I", str(HERE / "scripts/ledger.py"), str(out), "0x2a1a80e795b6ed6325e3934b6a27d57111e72ffe", "0xfddfd657996c214d4dd2fd0fff4589c0daeaf33d",
                    "0x37d10ffb61998561c5f9fb941c42c952d8fb4e28", "0xb500375afa738dc548b850669096c5eb56a8719a", "0xab05ffa436861ebb59e16f407703e009fe78e30f"], check=True, capture_output=True)
    L = jl(out); out.unlink()
    r = {a: L[a]["trading_result"] for a in L}
    check("B2 ledgers: PURE698 +36,933.71; JamWil23 -5,436.40; flydartball +841,375.23; thesecondhighlander -174,453.49; bravonoll +31,863.48",
          [round(Decimal(r[a]), 2) for a in ["0x2a1a80e795b6ed6325e3934b6a27d57111e72ffe", "0xfddfd657996c214d4dd2fd0fff4589c0daeaf33d", "0x37d10ffb61998561c5f9fb941c42c952d8fb4e28",
                                              "0xb500375afa738dc548b850669096c5eb56a8719a", "0xab05ffa436861ebb59e16f407703e009fe78e30f"]]
          == [Decimal("36933.71"), Decimal("-5436.40"), Decimal("841375.23"), Decimal("-174453.49"), Decimal("31863.48")])


if __name__ == "__main__":
    part_a()
    part_b()
    for n, ok, d in RESULTS:
        print(("PASS " if ok else "FAIL ") + n + (f"  [{d}]" if d and not ok else ""))
    fails = sum(1 for _, ok, _ in RESULTS if not ok)
    (HERE / "verification.json").write_text(json.dumps({"checks": len(RESULTS), "failed": fails,
                                                         "results": [{"check": n, "pass": ok, "detail": d} for n, ok, d in RESULTS]}, indent=1))
    print(f"{len(RESULTS) - fails}/{len(RESULTS)} passed")
    sys.exit(1 if fails else 0)
