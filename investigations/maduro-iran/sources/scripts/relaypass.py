import sys,json,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from bfs2 import relay_edges, INFRA, norm, pm_count, isevm
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
seeds=[norm(s) for s in ['0x44b6f8de91e20953eb2c632062860338154ebe4e','0xe9a7230f874930827b87970a4fbb33a262f02442','TA4chMztaY6TW8dv7qnuqmJKvb4edZqwj5','TTt3h6D2sB3KMNZAH8w8z9xEqsfCTRo8nf','TJs1u6k8RWaqgLRZTxF9eKXojWv8HsbJwx']]
E=[json.loads(l) for l in open('bfs2/edges.jsonl')]
nb=defaultdict(set)
for e in E: nb[e['src']].add(e['dst']); nb[e['dst']].add(e['src'])
d1=set().union(*[nb[s] for s in seeds])-set(seeds)
d1={a for a in d1 if a not in INFRA}
d2=set().union(*[nb[a] for a in d1])-d1-set(seeds)
d2={a for a in d2 if a not in INFRA}
print('d1',len(d1),'d2',len(d2),flush=True)
res={}
def job(a):
    try: rr,n=relay_edges(a,maxpages=4); return a,rr,n
    except Exception as e: return a,[],-1
with ThreadPoolExecutor(6) as ex:
    for a,rr,n in ex.map(job, sorted(d1|d2)): res[a]=(rr,n)
pmcand=set()
for a,(rr,n) in res.items():
    for e in rr:
        for b in (e['src'],e['dst']):
            if b!=a and isevm(b): pmcand.add(b)
print('relay-connected evm endpoints',len(pmcand),flush=True)
pm={}
with ThreadPoolExecutor(6) as ex:
    for b,c in zip(sorted(pmcand), ex.map(pm_count, sorted(pmcand))): pm[b]=c
PM=[b for b,c in pm.items() if c>0]
out=dict(d1=sorted(d1),d2=sorted(d2),relay={a:[e for e in rr] for a,(rr,n) in res.items() if rr},pm_endpoints=PM)
json.dump(out,open('relaypass.json','w'))
print('PM accounts reachable via relay from d1/d2 nodes:',len(PM))
for b in PM:
    via=[(a,e['src'],e['dst'],round(e['amt'],2),e['ts']) for a,(rr,n) in res.items() for e in rr if b in (e['src'],e['dst'])]
    print(b, via[:3])
