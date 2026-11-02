"""How often did the other investigations keep an empty Etherscan answer that is really false? Their ledgers are read, their caches are not written. Random sample, seed fixed, re-read with the retries of es.rows."""
import json,random,re,sys,urllib.parse
from pathlib import Path
sys.path.insert(0,'.')
import es,net,collections
out=[]
for proj in ('PolySentinel-flow-trace','PolySentinel-ChangeNOW-proof','PolySentinel-investigation','PolySentinel-ChangeNOW-outflows'):
    p=Path.home()/'Projects'/proj/'state/requests.jsonl'
    if not p.exists(): continue
    seen=set()
    for line in p.read_text().splitlines():
        try: d=json.loads(line)
        except ValueError: continue
        u=d.get('url','')
        if 'etherscan.io/v2' in u and d.get('status')==200 and d.get('bytes',9999)<120 and 'action=' in u:
            q=dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(u).query))
            if q.get('module')=='account' and q.get('action') in ('txlist','tokentx','txlistinternal') and int(q.get('page','1'))==1 and int(q.get('startblock','0'))==0:
                k=(q['chainid'],q['address'].lower(),q['action'])
                if k not in seen:
                    seen.add(k); out.append((proj,)+k)
print('empty answers kept, full-history reads',collections.Counter(x[0] for x in out),collections.Counter(x[3] for x in out))
rng=random.Random(20261102); rng.shuffle(out)
sample=out[:60]; res=[]
for proj,chain,a,act in sample:
    rows=es.rows(act,a,chain=int(chain),offset=5)
    res.append(dict(proj=proj,chain=chain,address=a,action=act,rows_now=len(rows)))
    print(proj[13:],chain,a,act,len(rows),flush=True)
json.dump(res,open('../state/runs/empty_audit.json','w'))
print('false empties',sum(r['rows_now']>0 for r in res),'of',len(res))
