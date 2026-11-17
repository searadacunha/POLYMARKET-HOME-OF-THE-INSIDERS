"""Builds the publishable note from the archived raw responses (offline).

python3 -I build.py <work_dir> <out_dir>
Copies on-chain evidence verbatim, reduces Polymarket API data (drops third-party profile fields),
writes SHA256SUMS, then derives transactions.csv, chronology.csv, graph.json, graph.mmd, comparator.json.
"""
import csv, glob, gzip, hashlib, json, shutil, sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

W, OUT = Path(sys.argv[1]), Path(sys.argv[2])
sys.path.insert(0, str(W / "scripts"))
from flows import rows as sol_rows  # noqa: E402
from poly_decode import decode as poly  # noqa: E402

ACC = {"0xcc32a117ac254fe51fd867b928e45492b1f6dc7e": "BlueElephant666",
       "0xd36fa21eb3fa7b1aaf97c8499253f76f82a16d48": "SemiconductorIT",
       "0xd109e93d5a86a68982c0b5e94323d01ab728de03": "carltiosway",
       "0x3e44cfbf234a9616c5f9edddd6bd6bd068854d4a": "yellowtop1",
       "0x75f23439b88c30ff00b07dcc1a93961780d47c82": "Momentumgod",
       "0x97e490d61b530d5078348d76143a25c43a47164d": "oveiStheair",
       "0x0a142164f48dab6448872f0abac310d03e305316": "aaamsaasa"}
NEW = {"oveiStheair", "aaamsaasa"}
BEN = "4dLZQynk9SZJf6PCAV73828TZHGJaf9kWgpKVUzV4Fwy"
BYBIT_DEP = "Agnhk1VsurW1ic3YNDtp3NeLTGYCiaaUwpRSKag9PdpV"
CDC_DEP = "CCQQKc4vw527ehZZhQidZZT9LEzKr4Ca7bZNwJv6BmBR"
PC_POOL = "4AV2Qzp3N4c9RfzyEbNZs2wqWfW4EwKnnxFAZCndvfGh"
SOLVER = "F7p3dFrjRTbtRp8FRF6qHLomXbKRBzpvBLjtQcfcgmNe"
DEPOSITORY = "0x4cd00e387622c35bddb9b4c962c136462338bc31"
YES_US = None
DROP = {"bio", "pseudonym", "profile_image", "profile_image_optimized", "users", "icon"}

# Labels: (chain, address) -> (label, kind, source)
ORB = "Orb explorer (orbmarkets.io, built by Helius), address page read 2026-11-05"
BSM = "raw/http/bs_meta_137_batch1.json (metadata.services.blockscout.com)"
LABELS = {
    ("solana", BEN): ("Common Solana beneficiary (closed account, created by the Relay solver on 2026-02-28)", "wallet", ORB),
    ("solana", BYBIT_DEP): ("Bybit Deposit (Agnhk)", "exchange_deposit", ORB),
    ("solana", "iGdFcQoyR2MwbXMHQskhmNsqddZ6rinsipHc4TNSdwu"): ("Bybit Hot Wallet 10", "exchange_hot_wallet", ORB),
    ("solana", "BhwuB5KYbEgDLHYwCGdet3TcUipjxExDQK3hDqtd78Qv"): ("Bybit Gas Distributor", "exchange_hot_wallet", ORB),
    ("solana", "Gem2VAypSg7Ai7vjDKPTtqFahpoQWkfgVkyzx3rPoTka"): ("Bybit Hot Wallet 6", "exchange_hot_wallet", ORB),
    ("solana", "2qo8jvuc49pFmTjmUHLiARSV6ppPTaE7gw27ZJ6DnNZy"): ("Bybit Hot Wallet 2", "exchange_hot_wallet", ORB),
    ("solana", CDC_DEP): ("Crypto.com Deposit (CCQQK)", "exchange_deposit", ORB),
    ("solana", "HqqzZC5qsNKtZBrBsYvbXhzxUQaADSzkDaifHWe1GvEH"): ("Crypto.com Hot Wallet 6", "exchange_hot_wallet", ORB),
    ("solana", "6K5fZXQshgcWw9ZAFxMVDLDukrsA24fLiZCW17wLZA8V"): ("Crypto.com Gas Supplier", "exchange_hot_wallet", ORB),
    ("solana", "AobVSwdW9BbpMdJvTqeCN4hPAmh4rHm7vwLnQ5ATSyrS"): ("Crypto.com Hot Wallet 1 (an older local library says Robinhood)", "exchange_hot_wallet", ORB),
    ("solana", "5tzFkiKscXHK5ZXCGbXZxdw7gTjjD1mBwuoFbhUvuAi9"): ("Binance Hot Wallet 2", "exchange_hot_wallet", ORB),
    ("solana", "6LY1JzAFVZsP2a2xKrtU6znQMQ5h4i7tocWdgrkZzkzF"): ("Kraken Hot Wallet 1", "exchange_hot_wallet", ORB),
    ("solana", "BmFdpraQhkiDQE6SnfG5omcA1VwzqfXrwtNYBwWTymy6"): ("KuCoin Hot Wallet 2", "exchange_hot_wallet", ORB),
    ("solana", SOLVER): ("Relay Solver", "bridge", ORB),
    ("solana", "7uTT8Xi5RWXzy7h9XL244GRgEycDYDhLjr3ZyNdXi8pZ"): ("Relay", "bridge", ORB),
    ("solana", PC_POOL): ("Privacy Cash SOL Pool", "privacy_pool", ORB),
    ("solana", "AWexibGxNFKTa1b5R5MN4PJr9HWnWRwf8EW9g8cLx3dM"): ("Privacy Cash Auth (fee recipient)", "privacy_pool", ORB),
    ("solana", "CN5kywyqAzQD7bN6SPTB5r8r6UL6GKfpDvujYBdqv5j9"): ("Unlabeled high-traffic relay (funded by Binance Hot Wallet 2 in 2023)", "unlabeled_service_like", ORB),
    ("solana", "98jocp4jVAkpnD9uuhFYrwPksirqg3dDTnMMSd7bm5PG"): ("Unlabeled wallet", "wallet", ORB),
    ("solana", "GJrHw6wSnrMUN9hqgui6cjy9ZR7gbXjA8md8Bd8rHLrK"): ("Unlabeled trading wallet (funded by Bybit Hot Wallet 10)", "wallet", ORB),
    ("solana", "CfbJH31xEo3nWD31YfG6eSCs3Ddqga7h8hDnFmNB6AGW"): ("Polymarket bridge deposit address of BlueElephant666", "bridge_deposit", "raw/http (ext_relay in maduro-iran phase 3) and its USDC history"),
    ("solana", "GwK2P6e9LRN8F6nkHLSL8maXtcrZbdCJSKh7ymRVt2fd"): ("Polymarket bridge deposit address of carltiosway", "bridge_deposit", "idem"),
    ("polygon", DEPOSITORY): ("Relay: Depository", "bridge", BSM),
    ("polygon", "0xf70da97812cb96acdf810712aa562db8dfa3dbef"): ("Relay: Solver", "bridge", BSM),
    ("polygon", "0xfa0b641678f5115ad8a8de5752016bd1359681b9"): ("Crypto.com 6", "exchange_hot_wallet", BSM),
    ("polygon", "0xee7ae85f2fe2239e27d9c1e23fffe168d63b4055"): ("Binance: Hot Wallet 34", "exchange_hot_wallet", BSM),
    ("polygon", "0xe7804c37c13166ff0b37f5ae0bb07a3aebb6e245"): ("Binance 48 / Binance: Hot Wallet", "exchange_hot_wallet", BSM),
    ("polygon", "0xd36ec33c8bed5a9f7b6630855f1533455b98a418"): ("UniswapV3Pool", "dex", BSM),
    ("polygon", "0xf7493b5ad5d1f30d18278dbdda2778d2c4c91cff"): ("Polymarket bridge deposit address of aaamsaasa (Relay user of its deposits)", "bridge_deposit", "raw/http/relay_0x6184...json"),
    ("polygon", "0x519fa16e9897132b7633f634b76306a327839e06"): ("Unlabeled transit wallet forwarding to Binance", "wallet", "no label in raw/http/bs_meta_137_batch2.json"),
    ("polygon", "0xa6c221448af73af8350291c5cdcd877b39683766"): ("Unlabeled wallet forwarding to 0x852dc1c8", "wallet", "no label in raw/http/bs_meta_137_batch2.json"),
    ("polygon", "0x852dc1c875f0117ea0808610010893e4c576b6a9"): ("Unlabeled very active EOA (>10,000 token transfers since 2023)", "unlabeled_service_like", "no label in raw/http/bs_meta_137_batch2.json"),
    ("polygon", "0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb"): ("pUSD, Polymarket collateral token", "polymarket_contract", "repository note reference-polymarket-lots-redemption"),
    ("polygon", "0xfe775af18824f4951f19e264901030f8528bf972"): ("Unlabeled BSC sender funding oveiStheair via Relay", "wallet", "raw/http/relay_0x7486...json"),
    ("bsc", "0xfe775af18824f4951f19e264901030f8528bf972"): ("Unlabeled BSC sender funding oveiStheair via Relay", "wallet", "raw/http/relay_0x7486...json"),
}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def utc(ts):
    return datetime.fromtimestamp(int(ts), timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def reduce(obj, keep_name=True):
    if isinstance(obj, dict):
        return {k: reduce(v, keep_name) for k, v in obj.items() if k not in DROP and (keep_name or k != "name")}
    if isinstance(obj, list):
        return [reduce(v, keep_name) for v in obj]
    return obj


def copy_evidence():
    ev = OUT / "evidence"
    if ev.exists():
        shutil.rmtree(ev)
    keep_sol = {  # address -> glob of pages kept (windows that the report uses)
        BEN: "gtfa_*", BYBIT_DEP: "gtfa_*", CDC_DEP: "gtfa_*",
        "CfbJH31xEo3nWD31YfG6eSCs3Ddqga7h8hDnFmNB6AGW": "gtfa_*", "GwK2P6e9LRN8F6nkHLSL8maXtcrZbdCJSKh7ymRVt2fd": "gtfa_*",
        "iGdFcQoyR2MwbXMHQskhmNsqddZ6rinsipHc4TNSdwu": "gtfa_*", "BhwuB5KYbEgDLHYwCGdet3TcUipjxExDQK3hDqtd78Qv": "gtfa_*",
        "CN5kywyqAzQD7bN6SPTB5r8r6UL6GKfpDvujYBdqv5j9": "gtfa_177*", "5tzFkiKscXHK5ZXCGbXZxdw7gTjjD1mBwuoFbhUvuAi9": "gtfa_*",
        "6LY1JzAFVZsP2a2xKrtU6znQMQ5h4i7tocWdgrkZzkzF": "gtfa_*", "BmFdpraQhkiDQE6SnfG5omcA1VwzqfXrwtNYBwWTymy6": "gtfa_*",
        "GJrHw6wSnrMUN9hqgui6cjy9ZR7gbXjA8md8Bd8rHLrK": "gtfa_*", "98jocp4jVAkpnD9uuhFYrwPksirqg3dDTnMMSd7bm5PG": "gtfa_*"}
    for a, g in keep_sol.items():
        for f in (W / "raw/sol" / a).glob(g):
            d = ev / "sol" / a
            d.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, d / f.name)
    for f in (W / "raw/polygon").glob("*"):
        (ev / "polygon").mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, ev / "polygon" / f.name)
    for f in (W / "raw/etherscan").glob("137_*"):
        if "0x852dc1c8" in f.name and "_p1." not in f.name:
            continue  # pages 2-10 of the busy EOA: hashes in local_only, page 1 is enough to show the activity
        (ev / "etherscan").mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, ev / "etherscan" / f.name)
    for f in (W / "raw/http").glob("*"):
        n = f.name
        if n.startswith(("relay_", "bs_meta_")):
            (ev / "http").mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, ev / "http" / n)
    # Polymarket API: reduced copies, originals listed with their hash
    red, orig = ev / "polymarket_reduced", []
    red.mkdir(parents=True, exist_ok=True)
    for f in sorted((W / "raw/http").glob("pm_*.json")):
        if f.name.endswith(".meta.json") or ".HTTP" in f.name or f.name.startswith("pm_v2trades"):
            continue
        orig.append({"file": f.name, "sha256": sha(f), "meta": json.loads(f.with_suffix(".meta.json").read_text())})
        (red / f.name).write_text(json.dumps(reduce(json.loads(f.read_text())), indent=1))
    trades, pages = [], []
    for f in sorted((W / "raw/http").glob("pm_v2trades_us_strikes_p*.json")):
        if f.name.endswith(".meta.json"):
            continue
        pages.append({"file": f.name, "sha256": sha(f), "meta": json.loads(f.with_suffix(".meta.json").read_text())})
        for x in json.loads(f.read_text())["data"]:
            trades.append({k: x[k] for k in ("proxy_wallet", "side", "token_id", "size", "price", "timestamp", "transaction_hash")})
    with gzip.open(red / "us_strikes_feb28_trades_reduced.jsonl.gz", "wt") as g:
        for t in trades:
            g.write(json.dumps(t, sort_keys=True) + "\n")
    (red / "ORIGINALS.json").write_text(json.dumps({"note": "Original API responses kept outside git. Fields dropped: "
                                                    + ", ".join(sorted(DROP)) + "; trade rows keep 7 fields only.",
                                                    "activity_and_profiles": orig, "trade_pages": pages}, indent=1))
    lines = [f"{sha(p)}  {p.relative_to(OUT)}" for p in sorted(ev.rglob("*")) if p.is_file()]
    (OUT / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n")
    return ev


def relay_requests(ev):
    out = {}
    for f in sorted((ev / "http").glob("relay_*.json")):
        if f.name.endswith(".meta.json"):
            continue
        for q in json.loads(f.read_text()).get("requests", []):
            out[q["id"]] = (q, f.name)
    return out


def main():
    global YES_US
    OUT.mkdir(parents=True, exist_ok=True)
    ev = copy_evidence()
    T = []  # transaction table

    def add(step, net, ts, tx, src, dst, asset, amount, account, kind, evidence, note=""):
        T.append({"step": step, "network": net, "utc": utc(ts) if isinstance(ts, int) else ts, "tx": tx, "from": src, "to": dst,
                  "asset": asset, "amount": amount, "account": account, "relation": kind, "evidence": evidence, "note": note})

    RQ = relay_requests(ev)
    for rid, (q, fn) in sorted(RQ.items(), key=lambda x: x[1][0]["createdAt"]):
        d, user = q["data"], q["user"].lower()
        m = d["metadata"]
        ci, co = m["currencyIn"], m["currencyOut"]
        acct = ACC.get(user) or ACC.get(q["recipient"].lower(), "")
        intx, outtx = d["inTxs"][0], d["outTxs"][0]
        net_in = {137: "polygon", 56: "bsc", 792703809: "solana"}.get(intx["chainId"], str(intx["chainId"]))
        net_out = {137: "polygon", 56: "bsc", 792703809: "solana"}.get(outtx["chainId"], str(outtx["chainId"]))
        step = ("A_withdrawal_to_beneficiary" if q["recipient"] == BEN else
                "D_withdrawal_to_cryptocom" if q["recipient"] == CDC_DEP else
                "E_funding" if q["recipient"].lower() in ACC else "E_other_withdrawal")
        add(step, net_in, intx["timestamp"], intx["hash"], user, DEPOSITORY if net_in == "polygon" and step != "E_funding" else "Relay",
            ci["currency"]["symbol"], ci["amountFormatted"], acct, "via_service:Relay", f"evidence/http/{fn}", f"Relay request {rid}")
        add(step, net_out, outtx.get("timestamp") or intx["timestamp"], outtx["hash"], "Relay solver", q["recipient"],
            co["currency"]["symbol"], co["amountFormatted"], acct, "via_service:Relay", f"evidence/http/{fn}", f"Relay request {rid}")

    def sol_out(addr, step, account, min_lamports=1_000_000):
        for r in sol_rows(ev / "sol" / addr, addr):
            if r["err"] is not None:
                continue
            for t in r["sol_transfers"]:
                if t["from"] == addr and t["lamports"] >= min_lamports:
                    lab = LABELS.get(("solana", t["to"]), ("", "", ""))[1]
                    kind = "direct_transfer" if lab in ("wallet", "") else f"to_service:{lab}"
                    add(step, "solana", r["block_time"], r["signature"], addr, t["to"], "SOL", f'{t["lamports"] / 1e9:.9f}',
                        account, kind, f'evidence/sol/{addr}/{r["source_file"]}', f'balance {r["pre_lamports"] / 1e9:.9f} -> {r["post_lamports"] / 1e9:.9f}')
            for t in r["token_deltas"]:
                if t["owner"] == addr and t["delta_raw"] < 0:
                    dst = next((x["owner"] for x in r["token_deltas"] if x["mint"] == t["mint"] and x["delta_raw"] > 0), "")
                    add(step, "solana", r["block_time"], r["signature"], addr, dst, t["mint"], f'{-t["delta_raw"] / 10 ** t["decimals"]}',
                        account, "to_service:exchange_hot_wallet" if LABELS.get(("solana", dst)) else "token_transfer",
                        f'evidence/sol/{addr}/{r["source_file"]}')

    sol_out(BEN, "B_beneficiary_outflow", "")
    sol_out(BYBIT_DEP, "C_bybit_deposit_movement", "")
    sol_out(CDC_DEP, "D_cryptocom_deposit_sweep", "aaamsaasa")
    # inflows to the Bybit deposit address other than the beneficiary (exchange withdrawals, trading wallet, Privacy Cash)
    for r in sol_rows(ev / "sol" / BYBIT_DEP, BYBIT_DEP):
        if r["err"] is not None:
            continue
        pc = "9fhQBbumKEFuXtMBDw8AaQyAjCorLGJQiS3skWZdQyQD" in r["programs"]
        for t in r["sol_transfers"]:
            if t["to"] == BYBIT_DEP and t["from"] != BEN and t["lamports"] >= 1_000_000:
                add("C_bybit_deposit_inflow", "solana", r["block_time"], r["signature"], t["from"], BYBIT_DEP, "SOL", f'{t["lamports"] / 1e9:.9f}',
                    "", "from_service" if LABELS.get(("solana", t["from"])) else "direct_transfer", f'evidence/sol/{BYBIT_DEP}/{r["source_file"]}')
        if pc:
            add("C_privacy_cash_withdrawal", "solana", r["block_time"], r["signature"], PC_POOL, BYBIT_DEP, "SOL",
                f'{r["sol_deltas"][BYBIT_DEP] / 1e9:.9f}', "", "via_service:Privacy Cash", f'evidence/sol/{BYBIT_DEP}/{r["source_file"]}',
                f'pool delta {r["sol_deltas"][PC_POOL] / 1e9:.9f} SOL, relayer {r["fee_payer"]}')
        for t in r["token_deltas"]:
            if t["owner"] == BYBIT_DEP and t["delta_raw"] > 0:
                src = next((x["owner"] for x in r["token_deltas"] if x["mint"] == t["mint"] and x["delta_raw"] < 0), "")
                if t["delta_raw"] >= 10 ** t["decimals"]:
                    add("C_bybit_deposit_inflow", "solana", r["block_time"], r["signature"], src, BYBIT_DEP, t["mint"],
                        f'{t["delta_raw"] / 10 ** t["decimals"]}', "", "from_service" if LABELS.get(("solana", src)) else "direct_transfer",
                        f'evidence/sol/{BYBIT_DEP}/{r["source_file"]}')
    # Solana funders of two cluster-E bridge deposit addresses
    for a, acct in (("CfbJH31xEo3nWD31YfG6eSCs3Ddqga7h8hDnFmNB6AGW", "BlueElephant666"), ("GwK2P6e9LRN8F6nkHLSL8maXtcrZbdCJSKh7ymRVt2fd", "carltiosway")):
        for r in sol_rows(ev / "sol" / a, a):
            for t in r["token_deltas"]:
                if t["owner"] == a and t["delta_raw"] > 0:
                    src = next(x["owner"] for x in r["token_deltas"] if x["mint"] == t["mint"] and x["delta_raw"] < 0)
                    add("F_cluster_E_funding", "solana", r["block_time"], r["signature"], src, a, "USDC", f'{t["delta_raw"] / 1e6}',
                        acct, "from_service:exchange_hot_wallet", f'evidence/sol/{a}/{r["source_file"]}')
    # Polygon: aaamsaasa bridge deposit address and the two recurring addresses (token rows from Etherscan)
    def es(addr):
        rows = []
        for f in sorted((ev / "etherscan").glob(f"137_tokentx_{addr}_p*.json")):
            if not f.name.endswith(".meta.json"):
                rows += [(x, f.name) for x in json.loads(f.read_text())["result"] or []]
        return rows
    for addr, step, lo, hi in (("0xf7493b5ad5d1f30d18278dbdda2778d2c4c91cff", "E_aaamsaasa_bridge_deposit", 0, 2 ** 40),
                               ("0x519fa16e9897132b7633f634b76306a327839e06", "G_recurring_0x519f", 1780876800, 1781049600),
                               ("0xa6c221448af73af8350291c5cdcd877b39683766", "G_recurring_0xa6c2", 1772323200, 1772496000)):
        for x, fn in es(addr):
            if x["tokenSymbol"] in ("USDC", "USDC.e") and lo <= int(x["timeStamp"]) < hi and int(x["value"]) > 0:
                lab = LABELS.get(("polygon", (x["to"] if x["from"].lower() == addr else x["from"]).lower()), ("", "", ""))[1]
                add(step, "polygon", int(x["timeStamp"]), x["hash"], x["from"].lower(), x["to"].lower(), x["tokenSymbol"],
                    f'{int(x["value"]) / 10 ** int(x["tokenDecimal"])}', "", lab or "direct_transfer", f"evidence/etherscan/{fn}")
    SYM = {"EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": "USDC", "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB": "USDT"}
    for r in T:
        r["asset"] = SYM.get(r["asset"], r["asset"])
    T.sort(key=lambda r: (r["utc"], r["step"]))
    with open(OUT / "transactions.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(T[0]))
        w.writeheader()
        w.writerows(T)

    # Chronology of the seven accounts from the reduced activity
    red = ev / "polymarket_reduced"
    chron = []
    for u, name in ACC.items():
        act = json.loads((red / f"pm_v2activity_{u}_p000.json").read_text())["data"]
        prof = red / f"pm_profile_{u}.json"
        created = json.loads(prof.read_text()).get("createdAt") if prof.exists() else ""
        iran = [x for x in act if "strikes Iran by February 28, 2026" in (x.get("title") or "")]
        buys = [x for x in iran if x["type"] == "TRADE" and x["side"] == "BUY"]
        sells = [x for x in iran if x["type"] == "TRADE" and x["side"] == "SELL"]
        red_ = [x for x in iran if x["type"] == "REDEEM"]
        dep = [x for x in act if x["type"] == "DEPOSIT"]
        wd = [x for x in act if x["type"] == "WITHDRAWAL"]
        b = sum(x["usdc_size"] for x in buys)
        sh = sum(x["size"] for x in buys)
        fb = min(buys, key=lambda x: x["timestamp"]) if buys else None
        chron.append({"account": name, "proxy_wallet": u, "new_in_this_note": name in NEW, "profile_created_utc": created or "",
                      "first_activity_utc": utc(min(x["timestamp"] for x in act)),
                      "deposits_usdc": round(sum(x["usdc_size"] for x in dep), 6), "first_deposit_utc": utc(min(x["timestamp"] for x in dep)) if dep else "",
                      "first_iran_buy_utc": utc(fb["timestamp"]) if fb else "", "first_iran_buy_market": fb["title"] if fb else "",
                      "first_iran_buy_price": fb["price"] if fb else "", "first_iran_buy_usdc": round(fb["usdc_size"], 6) if fb else "",
                      "iran_buy_usdc": round(b, 6), "iran_vwap": round(b / sh, 4) if sh else "", "iran_sell_usdc": round(sum(x["usdc_size"] for x in sells), 6),
                      "iran_redeem_usdc": round(sum(x["usdc_size"] for x in red_), 6),
                      "iran_cash_pnl_usdc": round(sum(x["usdc_size"] for x in red_ + sells) - b, 6),
                      "first_withdrawal_utc": utc(min(x["timestamp"] for x in wd)) if wd else "",
                      "first_withdrawal_usdc": round(min(wd, key=lambda x: x["timestamp"])["usdc_size"], 6) if wd else "",
                      "withdrawals_usdc": round(sum(x["usdc_size"] for x in wd), 6), "activity_rows": len(act)})
    with open(OUT / "chronology.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(chron[0]))
        w.writeheader()
        w.writerows(chron)

    # Descriptive comparator (exploratory, not a frozen test)
    YES_US = next(x["token_id"] for x in json.loads((red / "pm_v2activity_0x97e490d61b530d5078348d76143a25c43a47164d_p000.json").read_text())["data"]
                  if (x.get("title") or "").startswith("US strikes") and x.get("outcome") == "Yes")
    seen, buy, first, before = set(), defaultdict(float), {}, defaultdict(float)
    with gzip.open(red / "us_strikes_feb28_trades_reduced.jsonl.gz", "rt") as g:
        for line in g:
            x = json.loads(line)
            k = tuple(sorted(x.items()))
            if k in seen:
                continue
            seen.add(k)
            t = int(x["timestamp"])
            if x["token_id"] == YES_US and x["side"] == "BUY" and 1772236800 <= t < 1772259300:
                wlt = x["proxy_wallet"].lower()
                buy[wlt] += float(x["size"]) * float(x["price"])
                first[wlt] = min(first.get(wlt, t), t)
                if t < 1772255700:
                    before[wlt] += float(x["size"]) * float(x["price"])
    big = sorted([w for w, v in buy.items() if v >= 1000], key=lambda w: first[w])
    comp = {"population": "proxy wallets with BUY rows on the Yes token of 'US strikes Iran by February 28, 2026?', 2026-02-28 00:00-06:15 UTC, maker and taker rows",
            "unique_trade_rows": len(seen), "wallets_buying_yes": len(buy), "wallets_ge_1000_usdc": len(big),
            "wallets_ge_1000_usdc_before_0515": sum(1 for v in before.values() if v >= 1000),
            "accounts": {ACC[w]: {"yes_buy_usdc_0000_0615": round(buy.get(w, 0), 2), "yes_buy_usdc_before_0515": round(before.get(w, 0), 2),
                                  "first_yes_buy_in_window_utc": utc(first[w]) if w in first else "",
                                  "position_by_first_buy_among_ge_1000": big.index(w) + 1 if w in big else None} for w in ACC},
            "status": "EXPLORATORY descriptive comparison; window and threshold chosen after seeing the cluster, no test statistic"}
    (OUT / "comparator.json").write_text(json.dumps(comp, indent=1))

    # Graph: nodes and aggregated edges from the transaction table
    nodes, edges = {}, defaultdict(lambda: {"amount": defaultdict(float), "n": 0, "relation": set(), "first_utc": "z"})
    def node(a, net):
        key = a.lower() if a.startswith("0x") else a
        lab = LABELS.get((net, a.lower() if a.startswith("0x") else a))
        if a.lower() in ACC:
            nodes[key] = {"id": key, "network": "polygon", "label": f"Polymarket {ACC[a.lower()]}", "kind": "polymarket_account",
                          "new_in_this_note": ACC[a.lower()] in NEW}
        elif key not in nodes:
            nodes[key] = {"id": key, "network": net, "label": lab[0] if lab else "unlabeled", "kind": lab[1] if lab else "unlabeled", "label_source": lab[2] if lab else ""}
        return key
    for r in T:
        if r["from"] in ("Relay solver",) or r["to"] == "Relay":
            continue
        s, d = node(r["from"], r["network"]), node(r["to"], r["network"])
        e = edges[(s, d)]
        e["amount"][r["asset"]] += float(r["amount"])
        e["n"] += 1
        e["relation"].add(r["relation"])
        e["first_utc"] = min(e["first_utc"], r["utc"])
    for rid, (q, fn) in RQ.items():  # cross-chain edges: account -> Relay -> recipient
        s, d = node(q["user"].lower(), "polygon"), node(q["recipient"].lower() if q["recipient"].startswith("0x") else q["recipient"], "solana" if not q["recipient"].startswith("0x") else "polygon")
        e = edges[(s, d)]
        e["amount"][q["data"]["metadata"]["currencyOut"]["currency"]["symbol"] + " (via Relay)"] += float(q["data"]["metadata"]["currencyOut"]["amountFormatted"])
        e["n"] += 1
        e["relation"].add("via_service:Relay (cross-chain, order id on both chains)")
        e["first_utc"] = min(e["first_utc"], q["createdAt"][:19] + "Z")
    G = {"nodes": list(nodes.values()), "edges": [{"from": s, "to": d, "n": e["n"], "amounts": {k: round(v, 9) for k, v in e["amount"].items()},
                                                    "relation": sorted(e["relation"]), "first_utc": e["first_utc"]} for (s, d), e in edges.items()]}
    (OUT / "graph.json").write_text(json.dumps(G, indent=1))
    short = lambda a: a[:6] + "…" + a[-4:]
    shape = {"polymarket_account": ('(["', '"])'), "wallet": ('["', '"]'), "unlabeled": ('["', '"]')}
    mm = ["flowchart LR", "classDef acct fill:#1f6feb,color:#fff", "classDef newacct fill:#d29922,color:#000",
          "classDef svc fill:#6e7681,color:#fff", "classDef wal fill:#2ea043,color:#fff"]
    focus = {n["id"] for n in G["nodes"]}
    for n in G["nodes"]:
        o, c = shape.get(n["kind"], ('[("', '")]'))
        cls = "newacct" if n.get("new_in_this_note") else "acct" if n["kind"] == "polymarket_account" else "wal" if n["kind"] in ("wallet", "unlabeled") else "svc"
        mm.append(f'  {n["id"][:12]}{o}{n["label"]}<br/>{short(n["id"])}{c}:::{cls}')
    for e in G["edges"]:
        if e["from"] in focus and e["to"] in focus:
            amt = ", ".join(f"{v:,.2f} {k}" for k, v in e["amounts"].items())
            mm.append(f'  {e["from"][:12]} -->|"{e["n"]}× {amt}"| {e["to"][:12]}')
    (OUT / "graph.mmd").write_text("\n".join(mm) + "\n")
    with open(OUT / "labels.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["network", "address", "label", "kind", "source"])
        for (net, a), (l, k, s) in sorted(LABELS.items()):
            w.writerow([net, a, l, k, s])
    print("transactions", len(T), "chronology", len(chron), "nodes", len(G["nodes"]), "edges", len(G["edges"]))


if __name__ == "__main__":
    main()
