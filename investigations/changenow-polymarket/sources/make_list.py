#!/usr/bin/env python3
import json, os
OUT = os.path.dirname(os.path.abspath(__file__))
def honest_conf(r):
    if not r.get('pm_link'): return 0.0
    p=0.75; tot=r.get('total_usd',0)
    if tot>=50000: p-=0.25
    elif tot>=10000: p-=0.08
    elif tot>=50: p+=0.03
    d=r.get('sec_payout_to_pm')
    if d is not None:
        if d<-30*24*3600: p-=0.10
        elif d<0: p-=0.04
        elif d<=7*24*3600: p+=0.05
    if r.get('pm_has_trade'): p+=0.02
    return round(max(0.05,min(0.85,p)),3)
rows=[]
for line in open(os.path.join(OUT,'wallets_enriched.jsonl')):
    line=line.strip()
    if not line: continue
    o=json.loads(line)
    if o.get('pm_link') is True:
        o['c']=honest_conf(o); rows.append(o)
rows.sort(key=lambda r:(-r['c'],-r['total_usd']))
tot=sum(r['total_usd'] for r in rows)
print(f"# {len(rows)} wallets PM CN-fundés (f2020, rail DIRECT_POLYGON) — total CN→ ${tot:,.0f}\n")
print('| # | wallet (lien PM) | conf | CN→$ | n |')
print('|--|--|--:|--:|--:|')
for i,r in enumerate(rows,1):
    w=r['wallet_pm']
    print(f"| {i} | [{w}](https://polymarket.com/profile/{w}) | {r['c']:.2f} | ${r['total_usd']:,.0f} | {r['n_payouts']} |")
