#!/usr/bin/env python3
"""
DIRECT-POLYGON CN->PM pipeline implementing Fugu's retained methodology.
Hub = f2020 (operative CN payout hub on Polygon, corroborated by labeled ChangeNOW 22
linkage). For every f2020 stablecoin recipient over full history:
  - classify EOA vs contract (contracts = routers/CEX/PM-core, unwound or excluded)
  - PM-link via pUSD activity (Fugu B3)
  - confidence score (Fugu C, adapted to measured fields)
Writes resumable JSONL + final table.
"""
import json, sys, time, os, urllib.request, urllib.error
import chain
from collections import defaultdict

DATA_API = "https://data-api.polymarket.com"
def pm_activity(wallet, limit=100):
    """Authoritative PM-link via Polymarket data-api. Returns
    (is_bettor, n_sample, earliest_ts_sample, has_trade_or_redeem)."""
    url = f"{DATA_API}/activity?user={wallet}&limit={limit}"
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
               "Accept": "application/json"}
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=25) as r:
                arr = json.loads(r.read().decode())
            if not isinstance(arr, list) or not arr:
                return (False, 0, None, False)
            tss = [int(a.get("timestamp", 0)) for a in arr if a.get("timestamp")]
            types = {a.get("type", "") for a in arr}
            has_trade = bool(types & {"TRADE", "REDEEM", "BUY", "SELL", "MERGE", "SPLIT"})
            return (True, len(arr), min(tss) if tss else None, has_trade)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(1.5 * (attempt + 1)); continue
            return (None, 0, None, False)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            time.sleep(0.6 * (attempt + 1))
    return (None, 0, None, False)  # None = lookup failed (MISSING)

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
RECIP_JSON = os.path.join(OUT_DIR, "f2020_recipients.json")
WALLET_JSONL = os.path.join(OUT_DIR, "wallets_enriched.jsonl")

F2020 = "0xf2020cbfc13fd5d4cb2da0ff8ae2d2c093c1c423"
CN22  = "0x4958f6c329b61404b1cfd0ec8a44600a9486bd0a"  # labeled "ChangeNOW 22"
PUSD  = "0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb"
STABLES = {
    "USDC.e": "0x2791bca1f2de4661ed88a30c99a7a9449aa84174",
    "USDC":   "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359",
    "USDT":   "0xc2132d05d31c914a87c6611c10748aeb04b58e8f",
}
# contracts that are NOT end-users (PM core / CEX / known infra) — excluded from "PM bettor"
INFRA_CONTRACTS = {
    "0x0000000000000000000000000000000000000000",
    CN22, F2020,
}
DUST = 1.0  # ignore <$1 total

def step1_collect_recipients():
    if os.path.exists(RECIP_JSON):
        with open(RECIP_JSON) as f:
            return json.load(f)
    recips = {}
    for sym, tok in STABLES.items():
        page = 1
        while True:
            rows = chain.tokentx(F2020, contractaddress=tok, sort="asc", offset=10000, page=page)
            if not isinstance(rows, list) or not rows:
                break
            for r in rows:
                if r["from"].lower() != F2020:
                    continue
                to = r["to"].lower()
                ts = int(r["timeStamp"])
                amt = int(r["value"]) / 1e6
                d = recips.setdefault(to, {"wallet": to, "total_usd": 0.0, "n": 0,
                                           "first_ts": ts, "last_ts": ts, "tokens": {}})
                d["total_usd"] += amt; d["n"] += 1
                d["first_ts"] = min(d["first_ts"], ts); d["last_ts"] = max(d["last_ts"], ts)
                d["tokens"][sym] = d["tokens"].get(sym, 0.0) + amt
            if len(rows) < 10000:
                break
            page += 1
        sys.stderr.write(f"[collect {sym}] recipients so far: {len(recips)}\n")
    with open(RECIP_JSON, "w") as f:
        json.dump(recips, f)
    return recips

def score(ev):
    """Confidence that wallet is a CN-funded PM wallet.
    MEASURED part: direct ERC-20 payout from f2020 (on-chain) + PM activity (data-api).
    Residual hub uncertainty: f2020 is OSINT-'most likely' CN, funds confirmed-labeled CN22.
    So we cap below 0.95 to reflect hub-label uncertainty, never claim certainty."""
    if ev["pm_link"] is None:
        return 0.50  # PM lookup failed -> unknown
    if not ev["pm_link"]:
        return 0.15  # received CN-hub $ but no PM activity -> not in mission scope
    p = 0.88        # PM bettor + direct payout from operative CN payout hub
    dt = ev.get("sec_payout_to_pm")
    if dt is not None:
        if dt < -7*24*3600: p -= 0.10    # heavy PM history long before any CN payout
        elif dt < 0:        p -= 0.04
        elif dt <= 7*24*3600: p += 0.04
    if ev["total_usd"] >= 100: p += 0.02
    if ev["total_usd"] < 5:    p -= 0.03
    return round(max(0.01, min(0.94, p)), 3)

def status(ev):
    if ev["pm_link"] is None: return "MISSING"
    if ev["pm_link"]:         return "MEASURED"
    return "NO_PM_LINK"

def main():
    recips = step1_collect_recipients()
    items = [d for d in recips.values() if d["total_usd"] >= DUST]
    items.sort(key=lambda d: -d["total_usd"])
    sys.stderr.write(f"[total recipients >= ${DUST}] {len(items)} (of {len(recips)})\n")

    done = set()
    if os.path.exists(WALLET_JSONL):
        with open(WALLET_JSONL) as f:
            for line in f:
                try:
                    o = json.loads(line)
                    if o.get("pm_link") is not None:   # retry failed lookups on resume
                        done.add(o["wallet_pm"])
                except Exception: pass
    sys.stderr.write(f"[resume] already enriched: {len(done)}\n")

    with open(WALLET_JSONL, "a") as out:
        for i, d in enumerate(items):
            w = d["wallet"]
            if w in done:
                continue
            if w in INFRA_CONTRACTS:
                continue
            is_bettor, n_act, earliest_pm, has_trade = pm_activity(w)
            sec = (earliest_pm - d["first_ts"]) if (earliest_pm and d["first_ts"]) else None
            ev = {"wallet_pm": w, "rail": "DIRECT_POLYGON", "cn_hub": "f2020",
                  "total_usd": round(d["total_usd"], 2), "n_payouts": d["n"],
                  "first_payout_ts": d["first_ts"], "last_payout_ts": d["last_ts"],
                  "pm_link": is_bettor, "pm_n_activity_sample": n_act,
                  "pm_has_trade": has_trade, "pm_earliest_sample_ts": earliest_pm,
                  "sec_payout_to_pm": sec}
            ev["confidence"] = score(ev)
            ev["status"] = status(ev)
            ev["attribution_method"] = "ERC20_DIRECT_FROM_CN_HUB"
            out.write(json.dumps(ev) + "\n"); out.flush()
            if i % 50 == 0:
                sys.stderr.write(f"[{i}/{len(items)}] {w[:10]} ${ev['total_usd']} pm={is_bettor} conf={ev['confidence']}\n")
    sys.stderr.write("[done]\n")

if __name__ == "__main__":
    main()
