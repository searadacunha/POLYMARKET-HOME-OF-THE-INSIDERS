#!/usr/bin/env python3
import json, os, datetime as dt
STATE="state"
rows=[json.loads(l) for l in open(os.path.join(STATE,"pm_sweep.jsonl")) if l.strip()]
def d(ts): return dt.datetime.fromtimestamp(int(ts),dt.timezone.utc).strftime('%Y-%m-%d') if ts else '?'
errs=[r for r in rows if r.get('error')]
traders=[r for r in rows if r.get('trader')]
non=[r for r in rows if not r.get('trader') and not r.get('error')]
print(f"TOTAL recipients: {len(rows)}   errors: {len(errs)}")
print(f"PM traders (EOA or DW): {len(traders)}   non-traders: {len(non)}")
# breakdown by account type
from collections import Counter
bt=Counter(r['trader']['account_type'] for r in traders)
print("  trader account type:",dict(bt))
# sizing
def V(r): return r['trader']['life_vol']
def M(r): return r['trader']['max_market']
traders.sort(key=lambda r:-V(r))
tot_cn_all=sum(r['cn_usd'] for r in rows)
tot_cn_traders=sum(r['cn_usd'] for r in traders)
print(f"\nCN$ paid to all recipients: ${tot_cn_all:,.0f}")
print(f"CN$ paid to PM-trader recipients: ${tot_cn_traders:,.0f} ({100*tot_cn_traders/tot_cn_all:.1f}%)")
print(f"\nlifetime PM volume tiers (traders):")
for lo in [0,100,1000,10000,100000]:
    n=len([r for r in traders if V(r)>=lo]); print(f"  life_vol >= ${lo:>7,}: {n}")
print(f"max single-market position tiers:")
for lo in [100,1000,5000,25000]:
    n=len([r for r in traders if M(r)>=lo]); print(f"  max_market >= ${lo:>6,}: {n}")
print(f"\nTOP 25 by lifetime PM volume:")
print(f"  {'owner':12} {'CN$':>9} {'acct':4} {'trades':>6} {'life_vol$':>11} {'maxmkt$':>9}  market / first-last")
for r in traders[:25]:
    t=r['trader']
    print(f"  {r['owner'][:12]} {r['cn_usd']:>9,.0f} {t['account_type']:4} {t['n_trades']:>6} {t['life_vol']:>11,.0f} {t['max_market']:>9,.0f}  {str(t['market'])[:32]}  {d(t['first_trade'])}->{d(t['last_trade'])}")
# causal: CN payout precedes first PM trade?
print(f"\nCAUSAL check (CN first payout vs first PM trade):")
caus=[r for r in traders if r['trader']['first_trade'] and r.get('cn_first')]
before=[r for r in caus if r['cn_first']<=r['trader']['first_trade']]
print(f"  traders with both timestamps: {len(caus)}")
print(f"  CN payout BEFORE first PM trade (fundable): {len(before)} ({100*len(before)/max(1,len(caus)):.0f}%)")
# save trader table
import csv
with open(os.path.join(STATE,"pm_traders.csv"),"w",newline="") as f:
    w=csv.writer(f); w.writerow(["owner","proxy","cn_usd","cn_first","cn_last","account","account_type","n_trades","life_vol","max_market","market","first_trade","last_trade"])
    for r in traders:
        t=r['trader']
        w.writerow([r['owner'],r['proxy'],r['cn_usd'],r.get('cn_first'),r.get('cn_last'),t['account'],t['account_type'],t['n_trades'],t['life_vol'],t['max_market'],t['market'],t['first_trade'],t['last_trade']])
print("\n-> state/pm_traders.csv")
if errs[:1]: print("sample error:",errs[0].get('error'))
