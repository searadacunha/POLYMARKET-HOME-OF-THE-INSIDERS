#!/usr/bin/env python3
"""Where does PM activity live? Query data-api /activity on raw EOA vs resolved proxy."""
import json, os, random, urllib.request
from concurrent.futures import ThreadPoolExecutor
from proxy_resolver import resolve
UA={"User-Agent":"Mozilla/5.0","Accept":"application/json"}
def http(u,tries=3):
    last=None
    for _ in range(tries):
        try: return json.loads(urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=25).read())
        except Exception as e: last=e
    return {"__err__":str(last)}
def act_count(addr):
    a=http(f"https://data-api.polymarket.com/activity?user={addr}&limit=100")
    if isinstance(a,list): return len(a)
    return -1
d=json.load(open("f2020_recipients.json")); owners=list(d.keys())
random.seed(1); sample=random.sample(owners,120)
def check(o):
    return {"o":o,"eoa_act":act_count(o),"proxy_act":act_count(resolve(o))}
res=[]
with ThreadPoolExecutor(max_workers=10) as ex:
    for r in ex.map(check,sample): res.append(r)
eoa_hits=[r for r in res if r['eoa_act']>0]
proxy_hits=[r for r in res if r['proxy_act']>0]
print(f"sample=120")
print(f"EOA has activity   : {len(eoa_hits)}")
print(f"PROXY has activity : {len(proxy_hits)}")
for r in eoa_hits[:10]: print("  EOA hit:",r['o'],"n=",r['eoa_act'])
for r in proxy_hits[:10]: print("  PROXY hit:",r['o'],"n=",r['proxy_act'])
