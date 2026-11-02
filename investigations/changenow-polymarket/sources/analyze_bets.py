#!/usr/bin/env python3
"""
For the CN-funded PM wallets: split crypto-updown vs the rest, categorize the rest,
and compute WR + realized ROI on the NON-updown subset.
Realized PnL reconstructed from /activity (BUY/SELL + redemption of net winning shares),
resolution from Gamma. Winners redeemed disappear from /positions, so we rebuild.
"""
import json, os, sys, time, urllib.request, urllib.error
from collections import defaultdict, Counter

OUT = os.path.dirname(os.path.abspath(__file__))
H = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0 Safari/537.36", "Accept": "application/json"}
ACT_CACHE = os.path.join(OUT, "activity_cache"); os.makedirs(ACT_CACHE, exist_ok=True)
GAMMA_CACHE = os.path.join(OUT, "gamma_cache.json")

def _get(url, retries=4):
    for a in range(retries):
        try:
            return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=30).read())
        except urllib.error.HTTPError as e:
            if e.code == 429: time.sleep(1.5*(a+1)); continue
            return None
        except Exception:
            time.sleep(0.6*(a+1))
    return None

def all_activity(wallet, cap=4000):
    cf = os.path.join(ACT_CACHE, wallet+".json")
    if os.path.exists(cf):
        return json.load(open(cf))
    out, off = [], 0
    while off < cap:
        a = _get(f"https://data-api.polymarket.com/activity?user={wallet}&limit=500&offset={off}")
        if not a: break
        out.extend(a)
        if len(a) < 500: break
        off += 500
    json.dump(out, open(cf, "w"))
    return out

def is_updown(e):
    s = ((e.get("slug") or "")+" "+(e.get("eventSlug") or "")).lower()
    t = (e.get("title") or "").lower()
    return ("updown" in s) or ("up-or-down" in s) or ("up or down" in t)

# ---- Gamma resolution cache ----
_gamma = json.load(open(GAMMA_CACHE)) if os.path.exists(GAMMA_CACHE) else {}
def resolve_market(cid):
    """Resolution via CLOB /markets/<cid> -> tokens[].winner (corpus-proven path)."""
    if cid in _gamma:
        return _gamma[cid]
    d = _get(f"https://clob.polymarket.com/markets/{cid}")
    info = {"closed": None, "win": None, "title": None}
    if isinstance(d, dict) and d.get("tokens"):
        info["closed"] = d.get("closed")
        info["title"] = d.get("question")
        toks = d.get("tokens", [])
        for i, t in enumerate(toks):
            if t.get("winner") is True or (t.get("price") in (1, "1", 1.0)):
                info["win"] = i; break
    _gamma[cid] = info
    return info

def main():
    wallets = [json.loads(l)["wallet_pm"] for l in open(os.path.join(OUT,"wallets_enriched.jsonl"))
               if l.strip() and json.loads(l).get("pm_link") is True]
    sys.stderr.write(f"[wallets] {len(wallets)}\n")

    ud_trades = nonud_trades = 0
    ud_vol = nonud_vol = 0.0
    # per (wallet, cid)
    mk = defaultdict(lambda: {"buy":0.0,"sell":0.0,"shares":defaultdict(float),"title":"","slug":""})
    theme_vol = Counter()
    for i, w in enumerate(wallets):
        for e in all_activity(w):
            if e.get("type") != "TRADE": continue
            usd = float(e.get("usdcSize") or 0); sz = float(e.get("size") or 0)
            side = e.get("side"); oi = e.get("outcomeIndex")
            if is_updown(e):
                ud_trades += 1; ud_vol += usd; continue
            nonud_trades += 1; nonud_vol += usd
            key = (w, e.get("conditionId"))
            d = mk[key]; d["title"]=e.get("title") or d["title"]; d["slug"]=e.get("slug") or d["slug"]
            if side == "BUY":  d["buy"]+=usd;  d["shares"][oi]+=sz
            elif side == "SELL": d["sell"]+=usd; d["shares"][oi]-=sz
        if i % 20 == 0:
            sys.stderr.write(f"[{i}/{len(wallets)}] ud_tr={ud_trades} nonud_tr={nonud_trades}\n")
            json.dump(_gamma, open(GAMMA_CACHE,"w"))

    # resolve non-updown markets, compute PnL/WR
    rows=[]; cids=set(cid for (_,cid) in mk if cid)
    sys.stderr.write(f"[non-updown markets to resolve] {len(mk)} positions, {len(cids)} distinct cids\n")
    for (w,cid),d in mk.items():
        if not cid: continue
        info = resolve_market(cid)
        cost=d["buy"]; proceeds=d["sell"]; redemption=0.0
        if info["win"] is not None:
            redemption = max(0.0, d["shares"].get(info["win"],0.0))  # winning shares * $1
        pnl = proceeds + redemption - cost
        resolved = info["closed"] is True and info["win"] is not None
        rows.append({"wallet":w,"cid":cid,"title":d["title"] or info["title"],"slug":d["slug"],
                     "cost":cost,"pnl":pnl,"resolved":resolved,"win_idx":info["win"]})
    json.dump(_gamma, open(GAMMA_CACHE,"w"))

    # theme categorization from title/slug keywords
    def theme(t):
        t=(t or "").lower()
        if any(k in t for k in ["nba","nfl","mlb","soccer","ufc","fight","epl","laliga","tennis","nhl","match","vs ","cup","league","f1","boxing","game"]): return "sport"
        if any(k in t for k in ["trump","election","president","senate","governor","poll","vote","democrat","republican","congress","minister","government"]): return "politique"
        if any(k in t for k in ["bitcoin","btc","ethereum","eth","solana","sol ","crypto","price","$"]): return "crypto (non-updown)"
        return "autre"
    for r in rows: r["theme"]=theme(r["title"])

    res=[r for r in rows if r["resolved"]]
    tot_cost=sum(r["cost"] for r in res); tot_pnl=sum(r["pnl"] for r in res)
    wins=sum(1 for r in res if r["pnl"]>0)
    print("="*60)
    print(f"CN-funded PM wallets analysed: {len(wallets)}")
    print(f"TRADES: updown={ud_trades} (vol ${ud_vol:,.0f}) | NON-updown={nonud_trades} (vol ${nonud_vol:,.0f})")
    print(f"NON-updown positions: {len(rows)} | resolved: {len(res)}")
    print(f"--- NON-UPDOWN performance (resolved markets) ---")
    print(f"WR = {wins}/{len(res)} = {100*wins/len(res):.1f}%" if res else "WR = n/a (0 resolved)")
    print(f"ROI = ${tot_pnl:,.0f} / ${tot_cost:,.0f} = {100*tot_pnl/tot_cost:+.1f}%" if tot_cost>0 else "ROI n/a")
    print(f"--- NON-updown bet themes (by # positions) ---")
    tc=Counter(r["theme"] for r in rows)
    for th,c in tc.most_common(): print(f"  {th:22s} {c} positions")
    print(f"--- by theme: resolved WR / ROI ---")
    for th in tc:
        rr=[r for r in res if r["theme"]==th]
        if not rr: continue
        c=sum(r['cost'] for r in rr); p=sum(r['pnl'] for r in rr); ww=sum(1 for r in rr if r['pnl']>0)
        print(f"  {th:22s} WR {ww}/{len(rr)}={100*ww/len(rr):.0f}%  ROI {100*p/c:+.0f}% (cost ${c:,.0f})" if c>0 else f"  {th}: n/a")
    print(f"--- top non-updown markets by volume ---")
    by_mk=Counter()
    for r in rows: by_mk[r["title"] or r["cid"]]+=r["cost"]
    for t,v in by_mk.most_common(20): print(f"  ${v:,.0f}  {str(t)[:65]}")
    json.dump(rows, open(os.path.join(OUT,"nonupdown_positions.json"),"w"), indent=2)

if __name__ == "__main__":
    main()
