import sqlite3, datetime as dt, collections, json
con = sqlite3.connect("work/tapes.sqlite")
C = "0x14a3dfeba8b22a32feb0f10763db68bc4d2abeb5bff90e9ae20de53793b35a1d"
U = lambda s: int(dt.datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=dt.timezone.utc).timestamp())
f = lambda t: dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%m-%d %H:%M:%S") if t else "-"
KNOWN = {"0xa430506774f9efaf39903ee7e0db1351f66891ca":"6741","0x1973177faa69b94b4afab818e612a7c05b3c01a9":"fmaduro","0x03f8aae7ae1687ef7e2d55e4429e72e9a95d8541":"trumpdeservesit","0xa9c57a20cb8433a269976bb35eb872bd11380bd9":"striketheboats","0x4bac00c61a02275d681f3857cdc5ae315f1f7075":"aenews0","0x8507124d416dd181ea552e01a0dfed19ab0b1086":"madurowilllose","0x2612496ab8f1d774f116f28b50769971936c92de":"pinkuniforms","0x234cc49e43dff8b3207bbd3a8a2579f339cb9867":"dirtycup"}
ANN = U("2025-10-10 09:00:00"); T0 = U("2025-10-09 22:42:57"); D0 = U("2025-10-09 00:00:00")
A = con.execute("select ts,wallet,side,outcome,size,price,tx,rank from trades where run=? order by rank desc", (C+":A",)).fetchall()
T = con.execute("select ts,wallet,side,outcome,size,price,tx,rank from trades where run=?", (C+":T",)).fetchall()
tkc = collections.Counter((r[6], r[1], r[2], r[3], round(r[4],4), round(r[5],6)) for r in T)
W = collections.defaultdict(lambda: dict(yes=0.0, no=0.0, yes_pre=0.0, no_pre=0.0, buy_yes_cash=0.0, buy_yes_sh=0.0, sell_yes_cash=0.0, buy_no_cash=0.0, sell_no_cash=0.0, first_yes_buy=None, first_yes_px=None, taker_buy_yes_cash=0.0, n=0, first_any=None, yes_before_t0=0.0, cash_before_t0=0.0))
for ts, w, side, o, size, price, tx, rk in A:
    if ts >= ANN: continue
    d = W[w]; d["n"] += 1
    if d["first_any"] is None: d["first_any"] = ts
    key = (tx, w, side, o, round(size,4), round(price,6)); taker = tkc.get(key, 0) > 0
    if taker: tkc[key] -= 1
    sg = 1 if side == "BUY" else -1
    if o == "Yes":
        d["yes"] += sg * size
        if ts < D0: d["yes_pre"] += sg * size
        if side == "BUY" and ts >= D0:
            d["buy_yes_cash"] += size * price; d["buy_yes_sh"] += size
            if taker: d["taker_buy_yes_cash"] += size * price
            if d["first_yes_buy"] is None: d["first_yes_buy"] = ts; d["first_yes_px"] = price
            if ts < T0: d["yes_before_t0"] += size; d["cash_before_t0"] += size * price
        if side == "SELL" and ts >= D0: d["sell_yes_cash"] += size * price
    else:
        d["no"] += sg * size
        if ts < D0: d["no_pre"] += sg * size
        if side == "BUY" and ts >= D0: d["buy_no_cash"] += size * price
        if side == "SELL" and ts >= D0: d["sell_no_cash"] += size * price
rows = []
for w, d in W.items():
    net_yes_gain = (d["yes"] - d["yes_pre"])
    rows.append((w, d))
print("wallets active before announcement:", len(W))
tot_buy = sum(d["buy_yes_cash"] for _, d in rows)
print(f"total YES buy cash Oct 9 00:00 -> Oct 10 09:00: {tot_buy:,.0f} (both maker and taker buys)")
big = sorted(rows, key=lambda x: -(x[1]["yes"] - x[1]["yes_pre"]))
print("\nTop 45 by net YES shares gained Oct 9 00:00 -> announcement")
print("wallet      tag             netYESgain  YESatAnn   buyCash  avgBuy  1stYESbuy       1stPx  takerShare  sellYEScash  buyNOcash")
out = []
for w, d in big[:45]:
    g = d["yes"] - d["yes_pre"]
    avg = d["buy_yes_cash"] / d["buy_yes_sh"] if d["buy_yes_sh"] else 0
    tsh = d["taker_buy_yes_cash"] / d["buy_yes_cash"] if d["buy_yes_cash"] else 0
    print(w[:10], KNOWN.get(w, "").ljust(15), f"{g:>11,.0f} {d['yes']:>9,.0f} {d['buy_yes_cash']:>9,.0f}  {avg:.3f}  {f(d['first_yes_buy'])}  {d['first_yes_px'] or 0:.3f}  {tsh:>6.0%}  {d['sell_yes_cash']:>10,.0f} {d['buy_no_cash']:>10,.0f}")
    out.append({"wallet": w, "tag": KNOWN.get(w, ""), "net_yes_gain": g, "yes_at_ann": d["yes"], "buy_cash": d["buy_yes_cash"], "avg_buy": avg, "first_yes_buy": d["first_yes_buy"], "first_px": d["first_yes_px"]})
json.dump(out, open("work/nobel_top45.json", "w"), indent=1)
c7 = sum(d["buy_yes_cash"] for w, d in rows if w in KNOWN)
c7g = sum(d["yes"] - d["yes_pre"] for w, d in rows if w in KNOWN)
print(f"\nC7 eight accounts: YES buy cash {c7:,.0f} = {c7/tot_buy:.1%} of all YES buy cash in window; net YES gained {c7g:,.0f}")
print("\nBuyers of YES between Oct 9 00:00 and T0 (22:42:57), i.e. before 6741's first trade:")
for w, d in sorted(rows, key=lambda x: -x[1]["yes_before_t0"]):
    if d["yes_before_t0"] > 0:
        print("  ", w, f"shares {d['yes_before_t0']:>9,.1f} cash {d['cash_before_t0']:>8,.1f} first {f(d['first_yes_buy'])} px {d['first_yes_px']:.4f} | YES at ann {d['yes']:>9,.1f} sellYEScash(window) {d['sell_yes_cash']:,.1f} | first trade ever in market {f(d['first_any'])}")
