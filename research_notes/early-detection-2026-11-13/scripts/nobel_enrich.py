import json, datetime as dt, os
from baseline import baseline
top = json.load(open("work/nobel_top45.json"))
KNOWN = {"0xa430506774f9efaf39903ee7e0db1351f66891ca":"6741","0x1973177faa69b94b4afab818e612a7c05b3c01a9":"fmaduro","0x03f8aae7ae1687ef7e2d55e4429e72e9a95d8541":"trumpdeservesit","0xa9c57a20cb8433a269976bb35eb872bd11380bd9":"striketheboats","0x4bac00c61a02275d681f3857cdc5ae315f1f7075":"aenews0","0x8507124d416dd181ea552e01a0dfed19ab0b1086":"madurowilllose","0x2612496ab8f1d774f116f28b50769971936c92de":"pinkuniforms","0x234cc49e43dff8b3207bbd3a8a2579f339cb9867":"dirtycup"}
OUT = "work/nobel_top45_baseline.json"
done = {r["wallet"]: r for r in json.load(open(OUT))} if os.path.exists(OUT) else {}
f = lambda t: dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%m-%d %H:%M") if t else "-"
for r in top:
    w = r["wallet"]
    if w in done or not r["first_yes_buy"]: continue
    try:
        b = baseline(w, r["first_yes_buy"])
    except Exception as e:
        b = {"wallet": w, "error": repr(e)}
    b.update({"tag": KNOWN.get(w, ""), "net_yes_gain": r["net_yes_gain"], "buy_cash": r["buy_cash"], "avg_buy": r["avg_buy"], "first_yes_buy": r["first_yes_buy"], "first_px": r["first_px"]})
    done[w] = b
    json.dump(list(done.values()), open(OUT, "w"), indent=1)
print("wallet      tag             1stBuy       px    buyCash  profAge_h  priorTr priorMk  priorCash  dep72h      medTr   ratio(buy/med)")
for b in sorted(done.values(), key=lambda x: -x.get("net_yes_gain", 0)):
    if "error" in b: print(b["wallet"][:10], "ERROR", b["error"][:80]); continue
    age = b["profile_age_h"]; med = b["prior_trade_median"]
    print(b["wallet"][:10], b["tag"].ljust(15), f(b["first_yes_buy"]), f"{b['first_px']:.3f}", f"{b['buy_cash']:>9,.0f}",
          (f"{age:>9,.1f}" if age is not None else "     none"), f"{b['prior_trades']:>6}{'+' if b['prior_rows_capped'] else ' '}", f"{b['prior_markets']:>6}",
          f"{b['prior_trade_cash']:>10,.0f}", f"{b['deposit_72h_usdc']:>9,.0f}", (f"{med:>8,.0f}" if med else "       -"),
          (f"{b['buy_cash']/med:>8,.0f}x" if med else "    new"))
