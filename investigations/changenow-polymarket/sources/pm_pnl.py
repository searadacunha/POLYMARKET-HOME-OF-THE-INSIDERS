#!/usr/bin/env python3
"""For each of the 158 CN-funded PM traders: lifetime realized PnL (cashflow),
current holdings value, win/loss, and betting style. Loud on errors."""
import json, os, csv, time, re, urllib.request, urllib.error
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor
UA={"User-Agent":"Mozilla/5.0","Accept":"application/json"}
def http(u,tries=4):
    last=None
    for a in range(tries):
        try: return json.loads(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=25).read())
        except urllib.error.HTTPError as e:
            if e.code==400: return []
            last=e; time.sleep(0.3*(a+1))
        except Exception as e: last=e; time.sleep(0.3*(a+1))
    raise RuntimeError(f"HTTP {u[:80]} {last}")
def full_activity(addr,cap=8000):
    out=[];off=0
    while off<cap:
        a=http(f"https://data-api.polymarket.com/activity?user={addr}&limit=500&offset={off}")
        if not isinstance(a,list) or not a: break
        out+=a
        if len(a)<500: break
        off+=500
    return out
def cur_value(addr):
    v=http(f"https://data-api.polymarket.com/value?user={addr}")
    if isinstance(v,list) and v: return float(v[0].get('value') or 0)
    return 0.0
CRYPTO=re.compile(r'(Bitcoin|Ethereum|Solana|XRP|Up or Down|BTC|ETH)',re.I)
SPORTS=re.compile(r'(vs\.?|NBA|NFL|NHL|MLB|UEFA|Wimbledon|WTA|ATP|Dota|CS2|LoL|Spread|Cup|Liga|Premier|Serie|Team to Advance|Rockets|Lakers|Spurs|Nuggets)',re.I)
POLI=re.compile(r'(Trump|Biden|Election|President|Fed|Senate|Governor|War|Ukraine|Israel|nominee|approval)',re.I)
def style_of(acts):
    vol=defaultdict(float)
    for e in acts:
        if e.get('type')=='TRADE':
            t=e.get('title') or ''
            v=float(e.get('usdcSize') or 0)
            if CRYPTO.search(t): vol['crypto']+=v
            elif SPORTS.search(t): vol['sports']+=v
            elif POLI.search(t): vol['politics']+=v
            else: vol['other']+=v
    if not vol: return 'none',{}
    dom=max(vol,key=vol.get)
    return dom,{k:round(v) for k,v in vol.items()}
def analyze(row):
    a=row['account']
    acts=full_activity(a)
    tr=[e for e in acts if e.get('type')=='TRADE']
    buys=sum(float(e.get('usdcSize') or 0) for e in tr if e.get('side')=='BUY')
    sells=sum(float(e.get('usdcSize') or 0) for e in tr if e.get('side')=='SELL')
    redeems=sum(float(e.get('usdcSize') or 0) for e in acts if e.get('type')=='REDEEM')
    cv=cur_value(a)
    realized=sells+redeems-buys           # cash out minus cash in on trades
    total_pnl=realized+cv                 # add current holdings value
    style,mix=style_of(acts)
    return {**row,"buys":round(buys),"sells":round(sells),"redeems":round(redeems),
            "cur_value":round(cv),"realized_pnl":round(realized),"total_pnl":round(total_pnl),
            "style":style,"mix":mix,"n_trades":len(tr)}
rows=list(csv.DictReader(open("state/pm_traders.csv")))
res=[]
with ThreadPoolExecutor(max_workers=10) as ex:
    for r in ex.map(analyze,rows): res.append(r)
# aggregate
winners=[r for r in res if r['total_pnl']>0]
losers=[r for r in res if r['total_pnl']<0]
print(f"traders analysed: {len(res)}")
print(f"WINNERS (total_pnl>0): {len(winners)}   LOSERS: {len(losers)}   flat: {len(res)-len(winners)-len(losers)}")
print(f"sum total_pnl across all: ${sum(r['total_pnl'] for r in res):,}")
print(f"sum buys (total staked): ${sum(r['buys'] for r in res):,}")
print("style counts:",dict(Counter(r['style'] for r in res)))
print("\nBIGGEST WINNERS:")
for r in sorted(res,key=lambda r:-r['total_pnl'])[:8]:
    print(f"  {r['account'][:12]} {r['account_type']} pnl=${r['total_pnl']:>8,} staked=${r['buys']:>8,} style={r['style']:8} maxmkt=${float(r['max_market']):,.0f}")
print("BIGGEST LOSERS:")
for r in sorted(res,key=lambda r:r['total_pnl'])[:8]:
    print(f"  {r['account'][:12]} {r['account_type']} pnl=${r['total_pnl']:>8,} staked=${r['buys']:>8,} style={r['style']:8} maxmkt=${float(r['max_market']):,.0f}")
# the two big single bets
print("\nLES 2 GROSSES MISES UNIQUES:")
for a in ["0x500F656bd8Cea0E77D404d4513515d0c92D2380A","0xe227610a1514a16c2d450094c8033c41b551e9d0"]:
    r=next((x for x in res if x['account'].lower()==a.lower()),None)
    if r: print(f"  {r['account'][:12]} {r['market'][:40]} maxmkt=${float(r['max_market']):,.0f} total_pnl=${r['total_pnl']:,} redeems=${r['redeems']:,} cur_value=${r['cur_value']:,} n_trades={r['n_trades']}")
with open("state/pm_pnl.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=[k for k in res[0] if k!='mix']); w.writeheader()
    for r in res: w.writerow({k:v for k,v in r.items() if k!='mix'})
print("\n-> state/pm_pnl.csv")
