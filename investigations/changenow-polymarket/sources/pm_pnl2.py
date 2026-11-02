#!/usr/bin/env python3
"""CORRECT lifetime PnL for the 158 CN-funded PM traders.
Cashflow PnL = (SELL + REDEEM + MERGE + current_value) - (BUY + SPLIT).
Previous pm_pnl.py was WRONG: it ignored SPLIT (a USDC outflow) and MERGE,
inflating split-then-redeem churners by ~their split volume.
Robust pagination: retries a failing offset, records incomplete fetches loudly."""
import json, os, csv, time, re, urllib.request, urllib.error
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor
UA={"User-Agent":"Mozilla/5.0","Accept":"application/json"}
def http(u,tries=8):
    last=None
    for a in range(tries):
        try: return json.loads(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=30).read())
        except urllib.error.HTTPError as e:
            last=e; time.sleep(0.5*(a+1))
        except Exception as e: last=e; time.sleep(0.4*(a+1))
    return None  # signal failure (loud)
def full_activity(addr,cap=20000):
    out=[];off=0;incomplete=False
    while off<cap:
        x=http(f"https://data-api.polymarket.com/activity?user={addr}&limit=500&offset={off}")
        if x is None: incomplete=True; break
        if not isinstance(x,list) or not x: break
        out+=x
        if len(x)<500: break
        off+=500
    return out,incomplete
def cur_value(addr):
    v=http(f"https://data-api.polymarket.com/value?user={addr}")
    if isinstance(v,list) and v: return float(v[0].get('value') or 0)
    return 0.0
CRYPTO=re.compile(r'(Bitcoin|Ethereum|Solana|XRP|Up or Down|BTC|ETH|Crude Oil|S&P|Nasdaq|Gold)',re.I)
SPORTS=re.compile(r'(vs\.?|NBA|NFL|NHL|MLB|UEFA|Wimbledon|WTA|ATP|Dota|CS2|CS:GO|LoL|Spread|Cup|Liga|Premier|Serie|Team to Advance|Rockets|Lakers|Spurs|Nuggets|Brazil|France|Spain)',re.I)
POLI=re.compile(r'(Trump|Biden|Election|President|Fed rate|Senate|Governor|Ukraine|Israel|nominee|approval|GTA)',re.I)
def style_of(acts):
    vol=defaultdict(float)
    for e in acts:
        if e.get('type')=='TRADE':
            t=e.get('title') or ''; v=float(e.get('usdcSize') or 0)
            if CRYPTO.search(t): vol['crypto']+=v
            elif SPORTS.search(t): vol['sports']+=v
            elif POLI.search(t): vol['politics']+=v
            else: vol['other']+=v
    if not vol: return 'none'
    return max(vol,key=vol.get)
def analyze(row):
    a=row['account']
    acts,incomplete=full_activity(a)
    agg=defaultdict(float); cnt=Counter()
    for e in acts:
        t=e.get('type'); v=float(e.get('usdcSize') or 0); cnt[t]+=1
        if t=='TRADE':
            agg['BUY' if e.get('side')=='BUY' else 'SELL']+=v
        else: agg[t]+=v
    cv=cur_value(a)
    cash_in = agg['SELL']+agg['REDEEM']+agg['MERGE']
    cash_out= agg['BUY']+agg['SPLIT']
    realized= cash_in - cash_out
    total_pnl= realized + cv
    return {"account":a,"account_type":row['account_type'],"cn_usd":row['cn_usd'],
            "market":row['market'],"max_market":row['max_market'],
            "buy":round(agg['BUY']),"sell":round(agg['SELL']),"split":round(agg['SPLIT']),
            "redeem":round(agg['REDEEM']),"merge":round(agg['MERGE']),"cur_value":round(cv),
            "realized_pnl":round(realized),"total_pnl":round(total_pnl),
            "style":style_of(acts),"n_events":len(acts),"incomplete":incomplete}
rows=list(csv.DictReader(open("state/pm_traders.csv")))
res=[]
with ThreadPoolExecutor(max_workers=8) as ex:
    for r in ex.map(analyze,rows): res.append(r)
inc=[r for r in res if r['incomplete']]
win=[r for r in res if r['total_pnl']>0]; los=[r for r in res if r['total_pnl']<0]
flat=[r for r in res if r['total_pnl']==0]
print(f"traders: {len(res)}   incomplete fetches: {len(inc)}")
print(f"WINNERS: {len(win)}   LOSERS: {len(los)}   flat: {len(flat)}")
print(f"sum total_pnl: ${sum(r['total_pnl'] for r in res):,}")
print(f"sum staked (BUY+SPLIT): ${sum(r['buy']+r['split'] for r in res):,}")
print(f"median total_pnl: ${sorted(r['total_pnl'] for r in res)[len(res)//2]:,}")
print("style:",dict(Counter(r['style'] for r in res)))
print("\nBIGGEST WINNERS (corrected):")
for r in sorted(res,key=lambda r:-r['total_pnl'])[:8]:
    print(f"  {r['account'][:12]} {r['account_type']} pnl=${r['total_pnl']:>8,} staked=${r['buy']+r['split']:>8,} style={r['style']:8} maxmkt=${float(r['max_market']):,.0f} {'INCOMPLETE' if r['incomplete'] else ''}")
print("BIGGEST LOSERS (corrected):")
for r in sorted(res,key=lambda r:r['total_pnl'])[:8]:
    print(f"  {r['account'][:12]} {r['account_type']} pnl=${r['total_pnl']:>8,} staked=${r['buy']+r['split']:>8,} style={r['style']:8} maxmkt=${float(r['max_market']):,.0f} {'INCOMPLETE' if r['incomplete'] else ''}")
print("\nLES 2 GROSSES MISES UNIQUES:")
for a in ["0x500F656bd8Cea0E77D404d4513515d0c92D2380A","0xe227610a1514a16c2d450094c8033c41b551e9d0"]:
    r=next((x for x in res if x['account'].lower()==a.lower()),None)
    if r: print(f"  {r['account'][:12]} {r['market'][:38]:38} maxmkt=${float(r['max_market']):,.0f} pnl=${r['total_pnl']:,} redeem=${r['redeem']:,} cur=${r['cur_value']:,}")
with open("state/pm_pnl2.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(res[0])); w.writeheader(); w.writerows(res)
print("-> state/pm_pnl2.csv")
