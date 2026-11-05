"""Offline readers for this note's evidence/ (Relay pages, Polymarket activity, Etherscan, BSC, Solana).

Used by build.py to write the tables. verify.py does not import this file.
"""
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

PREV = Path(__file__).resolve().parents[2] / "iran-solana-beneficiary-2026-11-05" / "evidence"
PM_REF = "funxyz|su4gnoxz14"
BINANCE_DEP = "0x519fa16e9897132b7633f634b76306a327839e06"
W7702 = "0xa6c221448af73af8350291c5cdcd877b39683766"
BEN = "4dLZQynk9SZJf6PCAV73828TZHGJaf9kWgpKVUzV4Fwy"
REAL = {"0x3c499c542cef5e3811e1192ce70d8cc03d5c3359": "USDC", "0x2791bca1f2de4661ed88a30c99a7a9449aa84174": "USDC.e"}
LABELS = {
    BINANCE_DEP: "0x519fa16e (Binance customer deposit address)",
    W7702: "0xa6c22144 (EIP-7702 wallet, all outflows to 0x852dc1c8)",
    BEN: "4dLZQynk (Solana beneficiary, to Bybit deposit Agnhk1Vs)",
    "0x20bd758daa8d5c2a51e95370079d34f38d91f8b2": "0x20bd758d (deposit address of ALLOWMETOSHOWU1)",
    "0xfe775af18824f4951f19e264901030f8528bf972": "0xfe775af1 (deposit address of oveiStheair)",
    "0x200b195893faf4da3f431125afc17d0903fc8ea6": "0x200b1958 (withdrawal relay of ALLOWMETOSHOWU1)",
    "0x9063493a4233006be654da772ef4dc38720cac55": "0x9063493a (Crypto.com customer deposit address)",
}


def iso(t):
    return datetime.fromtimestamp(int(t), timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def relay_orders(ev):
    out = {}
    for p in sorted((ev / "relay").glob("relay_user_*_p*.json")):
        if p.name.endswith(".meta.json"):
            continue
        for r in json.loads(p.read_text()).get("requests", []):
            out[r["id"]] = r
    return out


def flat(r):
    d = r.get("data") or {}
    m = d.get("metadata") or {}
    ci, co = m.get("currencyIn") or {}, m.get("currencyOut") or {}
    low = lambda a: a.lower() if (a or "").startswith("0x") else a
    return {"id": r["id"], "status": r["status"], "created": r["createdAt"], "user": low(r["user"]),
            "recipient": low(r["recipient"]), "referrer": r.get("referrer"),
            "o": (ci.get("currency") or {}).get("chainId"), "d": (co.get("currency") or {}).get("chainId"),
            "in_sym": (ci.get("currency") or {}).get("symbol"), "in_amt": ci.get("amountFormatted"),
            "out_sym": (co.get("currency") or {}).get("symbol"), "out_amt": co.get("amountFormatted"),
            "in_tx": [x.get("hash") for x in d.get("inTxs") or []], "out_tx": [x.get("hash") for x in d.get("outTxs") or []]}


def activity(ev):
    acts = {}
    for base in (ev / "polymarket_reduced", PREV / "polymarket_reduced"):  # this note's copy wins over the previous one
        got = defaultdict(list)
        for p in sorted(base.glob("pm_v2activity_*_p*.json")):
            got[p.name.split("pm_v2activity_")[1].split("_p")[0].lower()] += json.loads(p.read_text()).get("data", [])
        for a, xs in got.items():
            acts.setdefault(a, xs)
    return acts


def names(acts):
    return {a: next((x["name"] for x in xs if x.get("name")), a) for a, xs in acts.items()}


def label(a, nm):
    return LABELS.get(a) or nm.get(a) or a


def links(ev):
    """One row per transfer that connects two accounts or an account to a shared destination."""
    acts = activity(ev)
    nm = names(acts)
    orders = [flat(r) for r in relay_orders(ev).values()]
    rows = []
    proxies = set(acts)
    for o in sorted(orders, key=lambda x: x["created"]):
        if o["status"] != "success" or o["referrer"] != PM_REF or o["user"] == o["recipient"]:
            continue
        if o["user"] in proxies and o["recipient"] in LABELS or (o["user"] in LABELS and o["recipient"] in proxies) \
                or (o["user"] in proxies and o["recipient"] in proxies):
            rows.append({"kind": "relay_order", "utc": o["created"][:19].replace("T", " "), "from_label": label(o["user"], nm),
                         "from_address": o["user"], "to_label": label(o["recipient"], nm), "to_address": o["recipient"],
                         "route": f'{o["o"]}->{o["d"]}', "amount": o["in_amt"], "symbol": o["in_sym"],
                         "evidence": f'relay {o["id"]}; in {",".join(h or "null" for h in o["in_tx"])}; out {",".join(h or "null" for h in o["out_tx"])}'})
    # Direct Polymarket withdrawals that reach the two exits without Relay (Uniswap swap or transfer), matched by hash
    wd = {}
    for a, xs in acts.items():
        for x in xs:
            if x["type"] == "WITHDRAWAL" and x.get("transaction_hash"):
                wd[x["transaction_hash"].lower()] = (a, x)
    for exit_, base in ((BINANCE_DEP, PREV), (W7702, PREV), ("0x9063493a4233006be654da772ef4dc38720cac55", ev)):
        for t in json.loads((base / "etherscan" / f"137_tokentx_{exit_}_p1.json").read_text())["result"]:
            if t["to"] == exit_ and t["contractAddress"] in REAL and int(t["value"]) > 0 and t["hash"].lower() in wd:
                a, x = wd[t["hash"].lower()]
                rows.append({"kind": "direct_withdrawal", "utc": iso(t["timeStamp"]), "from_label": nm[a], "from_address": a,
                             "to_label": label(exit_, nm), "to_address": exit_, "route": "137", "amount": str(int(t["value"]) / 1e6),
                             "symbol": REAL[t["contractAddress"]], "evidence": f'polygon {t["hash"]} (activity WITHDRAWAL {x["usdc_size"]})'})
    # Account-to-account transfers seen as a WITHDRAWAL of one account and a DEPOSIT of another with the same hash
    dep = defaultdict(list)
    for a, xs in acts.items():
        for x in xs:
            if x["type"] == "DEPOSIT" and x.get("transaction_hash"):
                dep[x["transaction_hash"].lower()].append((a, x))
    for h, (a, x) in sorted(wd.items()):
        for b, y in dep.get(h, []):
            if b != a:
                rows.append({"kind": "same_transaction", "utc": iso(x["timestamp"]), "from_label": nm[a], "from_address": a,
                             "to_label": nm[b], "to_address": b, "route": "137", "amount": str(x["usdc_size"]), "symbol": "USDC.e",
                             "evidence": f"polygon {h} (WITHDRAWAL of {nm[a]} and DEPOSIT of {nm[b]})"})
    rows += chain_rows(ev, nm)
    return sorted(rows, key=lambda r: r["utc"])


BSC_USDC = "0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d"
BSC_LABELS = {"0x8894e0a0c962cb723c1976a4421c95949be2d4e3": "Binance 51 (hot wallet)",
              "0xe2fc31f816a9b94326492132018c3aecc4a93ae1": "Binance Hot Wallet 7",
              "0xf70da97812cb96acdf810712aa562db8dfa3dbef": "Relay solver",
              "0x4cd00e387622c35bddb9b4c962c136462338bc31": "Relay Depository",
              "0x937db5b193b367425919de9c08ed78f9119a883c": "0x937db5b1 (deposit address of SemiconductorIT)",
              "0x9028a9e6545e76e74b26f832ec501d63b80b44e7": "0x9028a9e6 (deposit address of Domariocarios)",
              "0x5b1323e6f7ebb4643e6d61da582adac8097c64ab": "0x5b1323e6 (deposit address of yellowtop1)",
              BINANCE_DEP: LABELS[BINANCE_DEP]}
SOL_LABELS = {"AobVSwdW9BbpMdJvTqeCN4hPAmh4rHm7vwLnQ5ATSyrS": "Crypto.com Hot Wallet 1 (Orb)",
              "Agnhk1VsurW1ic3YNDtp3NeLTGYCiaaUwpRSKag9PdpV": "Agnhk1Vs (Bybit customer deposit address)",
              "Gem2VAypSg7Ai7vjDKPTtqFahpoQWkfgVkyzx3rPoTka": "Bybit Hot Wallet 6 (Orb)",
              "4H4WacXekz1eGebGTQanvcNytAxiei4uBzJy36h9qj1g": "4H4WacXe (Solana deposit address of TBFMM)",
              "F7p3dFrjRTbtRp8FRF6qHLomXbKRBzpvBLjtQcfcgmNe": "Relay solver (Solana)"}
USDC_SOL = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"


def chain_rows(ev, nm):
    """BSC USDC transfers of 28 Feb 2026 and the Solana USDC path of 14 Jan 2026, read from the archived node responses."""
    out, seen = [], set()
    for p in sorted((ev / "bsc").glob("*.json")):
        if p.name.endswith(".meta.json"):
            continue
        res = json.loads(p.read_text())["result"]
        logs = res["logs"] if isinstance(res, dict) else res
        for lg in logs:
            if lg["address"].lower() != BSC_USDC or len(lg["topics"]) != 3 or (lg["transactionHash"], lg["logIndex"]) in seen:
                continue
            seen.add((lg["transactionHash"], lg["logIndex"]))
            a, b = "0x" + lg["topics"][1][-40:], "0x" + lg["topics"][2][-40:]
            if a not in BSC_LABELS or b not in BSC_LABELS:
                continue
            out.append({"kind": "bsc_transfer", "utc": f'block {int(lg["blockNumber"], 16)}', "from_label": BSC_LABELS[a],
                        "from_address": a, "to_label": BSC_LABELS[b], "to_address": b, "route": "56",
                        "amount": str(int(lg["data"], 16) / 1e18), "symbol": "USDC (BSC)", "evidence": f'bsc {lg["transactionHash"]}'})
    for base, addr in ((ev / "sol", "4H4WacXekz1eGebGTQanvcNytAxiei4uBzJy36h9qj1g"), (PREV / "sol", "Agnhk1VsurW1ic3YNDtp3NeLTGYCiaaUwpRSKag9PdpV")):
        for p in sorted((base / addr).glob("gtfa_*_p*.json")):
            if p.name.endswith(".meta.json"):
                continue
            for tx in json.loads(p.read_text())["result"]["data"]:
                if not (1768391000 <= tx["blockTime"] <= 1768393000):  # 14 Jan 2026, 11:43 to 12:16 UTC
                    continue
                m = tx["meta"]
                pre = {x["accountIndex"]: x for x in m.get("preTokenBalances") or [] if x["mint"] == USDC_SOL}
                post = {x["accountIndex"]: x for x in m.get("postTokenBalances") or [] if x["mint"] == USDC_SOL}
                d = {}
                for i in set(pre) | set(post):
                    own = (post.get(i) or pre[i])["owner"]
                    d[own] = d.get(own, 0) + int((post.get(i) or {"uiTokenAmount": {"amount": "0"}})["uiTokenAmount"]["amount"]) \
                        - int((pre.get(i) or {"uiTokenAmount": {"amount": "0"}})["uiTokenAmount"]["amount"])
                src = [k for k, v in d.items() if v < 0]
                dst = [k for k, v in d.items() if v > 0]
                sig = tx["transaction"]["signatures"][0]
                if len(src) == 1 and len(dst) == 1 and sig not in seen and src[0] in SOL_LABELS and dst[0] in SOL_LABELS:
                    seen.add(sig)
                    out.append({"kind": "solana_transfer", "utc": iso(tx["blockTime"]), "from_label": SOL_LABELS[src[0]],
                                "from_address": src[0], "to_label": SOL_LABELS[dst[0]], "to_address": dst[0], "route": "solana",
                                "amount": str(d[dst[0]] / 1e6), "symbol": "USDC", "evidence": f"solana {sig}"})
    return out


def accounts(ev):
    acts = activity(ev)
    nm = names(acts)
    prof = {}
    for base in (ev / "polymarket_reduced", PREV / "polymarket_reduced"):
        for p in base.glob("pm_profile_*.json"):
            prof.setdefault(p.name[len("pm_profile_"):-5].lower(), json.loads(p.read_text()))
    out = []
    for a, xs in sorted(acts.items(), key=lambda kv: (prof.get(kv[0], {}).get("createdAt") or "9")):
        if not xs:  # intermediate or deposit addresses: no Polymarket activity of their own
            continue
        iran = [x for x in xs if x["type"] == "TRADE" and x.get("side") == "BUY" and "Iran" in (x.get("title") or "")]
        out.append({"account": nm[a], "address": a, "profile_created": prof.get(a, {}).get("createdAt", "not served"),
                    "activity_rows": len(xs), "iran_buy_usdc": round(sum(float(x["usdc_size"]) for x in iran), 2),
                    "deposits": sum(x["type"] == "DEPOSIT" for x in xs), "withdrawals": sum(x["type"] == "WITHDRAWAL" for x in xs)})
    return out


def rarity(ev, population):
    """PLAN_RARITY.md, computed only from the user-side Relay pages of the population wallets."""
    pop = [w.lower() for w in population]
    done = {p.name[len("relay_user_"):-len("_DONE.json")].lower(): json.loads(p.read_text())
            for p in (ev / "relay").glob("relay_user_*_DONE.json")}
    collected = [w for w in pop if w in done]
    orders = [flat(r) for r in relay_orders(ev).values()]
    D = defaultdict(set)
    first = defaultdict(dict)
    for o in orders:  # only wallets whose own pages were collected to the end of their history
        if o["user"] in collected and o["o"] == 137 and o["status"] == "success" and o["referrer"] == PM_REF and o["recipient"] != o["user"]:
            D[o["user"]].add(o["recipient"])
            first[o["recipient"]].setdefault(o["user"], []).append(o["created"])
    truncated = [w for w in collected if done[w]["termination"] != "END"]
    shared = {r: sorted(us) for r, us in first.items() if len(us) >= 2}
    # connected components over shared recipients
    parent = {w: w for w in collected}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for r, us in shared.items():
        for u in us[1:]:
            parent[find(u)] = find(us[0])
    comp = defaultdict(list)
    for w in collected:
        if any(w in us for us in shared.values()):
            comp[find(w)].append(w)
    gaps = []
    for r, us in shared.items():
        for i, u in enumerate(us):
            for v in us[i + 1:]:
                ts = lambda w: [datetime.fromisoformat(t.replace("Z", "+00:00")).timestamp() for t in first[r][w]]
                gaps.append({"recipient": r, "a": u, "b": v, "min_gap_s": int(min(abs(x - y) for x in ts(u) for y in ts(v)))})
    return {"population": len(pop), "collected": len(collected), "truncated": truncated,
            "wallets_with_relay_withdrawals": sum(1 for w in collected if D[w]),
            "wallets_without_relay_withdrawals": sum(1 for w in collected if not D[w]),
            "shared_recipients": shared, "groups": sorted((sorted(g) for g in comp.values()), key=len, reverse=True),
            "pair_gaps": sorted(gaps, key=lambda g: g["min_gap_s"])}
