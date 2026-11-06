"""Experiment B: reconcile a Polymarket proxy's on-chain ERC-20 transfers with its data-api activity rows.

python3 -I -B experiment_b.py collect <raw_dir> <address> ...     # Etherscan v2 tokentx and token1155tx on Polygon, all pages, one worker
python3 -I -B experiment_b.py score <raw_dir> <activity_dir> <cutoff_unix> <out.json> <address> ...

Unit: the transaction hash. Each on-chain ERC-20 Transfer whose `from` or `to` is the proxy, before the cutoff, is
matched to the activity rows that carry the same hash. Reported per proxy: on-chain hashes absent from the activity
feed (with token, direction, amount and counterparty), activity rows whose hash moves no ERC-20 of the proxy, and
for matched hashes whether the row type agrees with the direction of the money. No address is labelled from memory:
counterparties are reported as they are, with the activity types seen on the same hashes.
"""
import json, sys, time, urllib.error, urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import hashlib

UA = {"user-agent": "polymarket-reconcile-research/1.0", "accept": "application/json"}
POLYGON = 137


def etherscan_key():
    for line in (Path.home() / "Downloads/.env").read_text().splitlines():
        if line.startswith("ETHERSCAN_API_KEY="):
            return line.split("=", 1)[1].strip().strip("\"'")
    raise SystemExit("no Etherscan key")


def collect(raw: Path, addr: str, action="tokentx"):
    key, page, rows = etherscan_key(), 1, 0
    while True:
        q = f"chainid={POLYGON}&module=account&action={action}&address={addr}&page={page}&offset=1000&sort=asc"
        if not addr.startswith("0x") or len(addr) != 42 or not all(c in "0123456789abcdef" for c in addr[2:]):
            raise SystemExit(f"not an address: {addr[:50]!r}")
        for i in range(6):
            try:
                with urllib.request.urlopen(urllib.request.Request(f"https://api.etherscan.io/v2/api?{q}&apikey={key}", headers=UA), timeout=60) as r:
                    b = r.read()
            except Exception as e:  # never let a URL with the key reach a message
                raise SystemExit(f"etherscan {action} {addr}: {type(e).__name__} {str(e).replace(key, '<KEY>')[:200]}")
            d = json.loads(b)
            if d.get("status") == "1" or "No transactions found" in str(d.get("message")):
                break
            time.sleep(3 * (i + 1))  # busy or rate-limited: never read as an empty list
        else:
            raise SystemExit(f"{addr}: {str(d)[:200]}")
        out = raw / f"{action}_{addr}_p{page}.json"
        raw.mkdir(parents=True, exist_ok=True)
        out.write_bytes(b)
        out.with_suffix(".meta.json").write_text(json.dumps({"url": f"https://api.etherscan.io/v2/api?{q}&apikey=<KEY>",
                                                            "sha256": hashlib.sha256(b).hexdigest(), "bytes": len(b),
                                                            "fetched_utc": datetime.now(timezone.utc).isoformat()}))
        res = d.get("result") or []
        rows += len(res)
        if len(res) < 1000:
            break
        page += 1; time.sleep(0.4)
    print(addr, "transfers", rows, "pages", page)


def transfers(raw: Path, addr: str, action="tokentx"):
    seen, out = set(), []
    for f in sorted(raw.glob(f"{action}_{addr}_p*.json")):
        if f.name.endswith(".meta.json"):
            continue
        for t in json.loads(f.read_text())["result"]:
            k = (t["hash"].lower(), t.get("logIndex"), t["contractAddress"].lower(), t.get("tokenID"))
            if k in seen:
                continue
            seen.add(k)
            out.append(t)
    return out


def activity(adir: Path, addr: str):
    rows = []
    for f in sorted(adir.glob(f"pm_v2activity_{addr}_p*.json")):
        if not f.name.endswith(".meta.json"):
            rows += json.loads(f.read_text())["data"]
    return rows


def score(raw, adir, cutoff, addrs):
    res = {}
    for a in addrs:
        a = a.lower()
        tx = [t for t in transfers(raw, a) if int(t["timeStamp"]) < cutoff]
        act = [r for r in activity(adir, a) if int(r["timestamp"]) < cutoff]
        by_hash_act = defaultdict(list)
        for r in act:
            by_hash_act[(r.get("transaction_hash") or "").lower()].append(r)
        by_hash_tx = defaultdict(list)
        for t in tx:
            by_hash_tx[t["hash"].lower()].append(t)

        def leg(t):
            sign = -1 if t["from"].lower() == a else 1
            return {"token": t["tokenSymbol"], "contract": t["contractAddress"].lower(), "direction": "out" if sign < 0 else "in",
                    "amount": int(t["value"]) / 10 ** int(t["tokenDecimal"]), "counterparty": (t["to"] if sign < 0 else t["from"]).lower(),
                    "time": int(t["timeStamp"])}
        missing = [{"hash": h, "legs": [leg(t) for t in ts]} for h, ts in by_hash_tx.items() if h not in by_hash_act]
        no_money = [{"hash": h, "types": sorted({r["type"] for r in rs}), "usdc": round(sum(float(r.get("usdc_size") or 0) for r in rs), 6)}
                    for h, rs in by_hash_act.items() if h and h not in by_hash_tx]
        # direction check on matched hashes: net ERC-20 flow of the proxy against the row type
        disagree = []
        for h in set(by_hash_tx) & set(by_hash_act):
            net = sum((-1 if t["from"].lower() == a else 1) * int(t["value"]) / 10 ** int(t["tokenDecimal"]) for t in by_hash_tx[h])
            types = {r["type"] for r in by_hash_act[h]}
            sides = {r.get("side") for r in by_hash_act[h] if r["type"] == "TRADE"}
            expect = None
            if types <= {"DEPOSIT"} or types <= {"REDEEM"} or types <= {"REWARD"} or (types == {"TRADE"} and sides == {"SELL"}):
                expect = 1
            elif types <= {"WITHDRAWAL"} or (types == {"TRADE"} and sides == {"BUY"}):
                expect = -1
            if expect is not None and net * expect < 0:
                disagree.append({"hash": h, "types": sorted(types), "sides": sorted(s for s in sides if s), "net_erc20": round(net, 6)})
        cp = Counter(leg(t)["counterparty"] for t in tx)
        types_by_cp = defaultdict(Counter)
        for t in tx:
            for r in by_hash_act.get(t["hash"].lower(), []):
                types_by_cp[leg(t)["counterparty"]][r["type"]] += 1
        e1155 = [t for t in transfers(raw, a, "token1155tx") if int(t["timeStamp"]) < cutoff]
        h1155 = defaultdict(list)
        for t in e1155:
            h1155[t["hash"].lower()].append(t)
        miss1155 = [{"hash": h, "legs": [{"direction": "out" if t["from"].lower() == a else "in", "tokens": int(t["tokenValue"]),
                                           "counterparty": (t["to"] if t["from"].lower() == a else t["from"]).lower(), "contract": t["contractAddress"].lower(),
                                           "time": int(t["timeStamp"])} for t in ts]} for h, ts in h1155.items() if h not in by_hash_act]
        res[a] = {"erc1155_transfers": len(e1155), "erc1155_hashes": len(h1155), "erc1155_hashes_missing_from_activity": miss1155,
                  "erc20_transfers": len(tx), "erc20_hashes": len(by_hash_tx), "activity_rows": len(act),
                  "activity_hashes": len([h for h in by_hash_act if h]), "activity_rows_without_hash": len(by_hash_act.get("", [])),
                  "activity_types": dict(Counter(r["type"] for r in act)),
                  "tokens": dict(Counter(t["tokenSymbol"] for t in tx)),
                  "onchain_hashes_missing_from_activity": missing, "activity_hashes_without_erc20": no_money,
                  "direction_disagreements": disagree,
                  "counterparties": [{"address": c, "transfers": n, "activity_types_on_same_hashes": dict(types_by_cp[c])} for c, n in cp.most_common()]}
    return res


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "collect":
        for x in a[2:]:
            for action in ("tokentx", "token1155tx"):
                if not list(Path(a[1]).glob(f"{action}_{x.lower()}_p*.json")):
                    collect(Path(a[1]), x.lower(), action); time.sleep(0.4)
    elif a[0] == "score":
        r = score(Path(a[1]), Path(a[2]), int(a[3]), a[5:])
        Path(a[4]).write_text(json.dumps(r, indent=1))
        for k, v in r.items():
            print(k[:10], "erc20 hashes", v["erc20_hashes"], "activity hashes", v["activity_hashes"], "missing from activity", len(v["onchain_hashes_missing_from_activity"]),
                  "activity without erc20", len(v["activity_hashes_without_erc20"]), "direction disagreements", len(v["direction_disagreements"]),
                  "erc1155 hashes", v["erc1155_hashes"], "erc1155 missing", len(v["erc1155_hashes_missing_from_activity"]))
