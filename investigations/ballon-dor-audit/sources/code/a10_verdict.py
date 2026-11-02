"""Audit: the frozen verdict rule applied by code, since the study applied it by hand, and how far the burden shortcut could move it. Reads only."""
import json,sys,os,time
C='/Users/benjamindacunha/Projects/PolySentinel-investigation/'
sys.path.insert(0,C+'collective/code');sys.dont_write_bytecode=True
g=json.load(open(C+'collective/derived/A_E1G.json'));e1=json.load(open(C+'collective/derived/A_E1.json'))
print('rank keys',list(g['ranks']))
for name,rows in g['ranks'].items():
    m=[r for r in rows if r['universe']=='M']
    print(name,'listed',len(rows),'best M',[(r['rank'],r['n'],round(r['u'],2),r.get('question','')[:42] or r.get('event')) for r in m][:3])
print('burden G max per day',max(g['burden_new_tokens_per_day']['G'].values()))
print('a0_by_date',json.dumps({k:(v if not isinstance(v,(list,dict)) else (type(v).__name__,len(v))) for k,v in e1['a0_by_date'].items()})[:500])
print(json.dumps(e1['a0_by_date'],ensure_ascii=False)[:500])
fa=g['first_alerts'];print('first alerts',len(fa),'M',sum(1 for x in fa if x['universe']=='M'))
# tokens simultaneously in alert: a token stays in alert while its 72 h window holds; approximate with 72 h after the first alert, an underestimate of duration only if it re-alerts
from collections import Counter
active=Counter()
for x in fa:
    if x['universe'] in('M','W'):continue
    for k in range(0,4):
        active[(x['t']+k*86400)//86400]+=1
print('tokens outside M and W possibly in alert per day, 72 h persistence: max',max(active.values()),'days over 20',sum(1 for v in active.values() if v>20),'of',len(active))
