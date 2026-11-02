import json,sys,collections
sys.path.insert(0,'.')
import chainlib as c, es, labels
SAFE='0x3dce0a29139a851da1dfca56af8e8a6440b4d952'
ADM='0x91430cad2d3975766499717fa0d66a78d814e5c5'
tx=es.rows('txlist',SAFE,chain=137,offset=400)
rows=[]
for r in tx:
    i=r['input']
    if not i.startswith('0x6a761202'): continue
    to='0x'+i[10+24:10+64]
    off=int(i[10+64*2:10+64*3],16)*2
    ln=int(i[10+off:10+off+64],16)*2
    data=i[10+off+64:10+off+64+ln]
    rows.append(dict(utc=c.utc(r['timeStamp']),tx=r['hash'],signer_sender=r['from'],to=to,sel=data[:8],data=data[:200],ok=r['isError']=='0'))
cnt=collections.Counter(x['to'] for x in rows)
m=labels.metadata(list(cnt),137)
print(len(rows))
for a,n in cnt.most_common(14): print(a,n,[y['name'] for y in labels.lookup(a,137,m)][:3],collections.Counter(x['sel'] for x in rows if x['to']==a).most_common(4))
hits=[x for x in rows if ADM[2:] in x['data']]
print('calls naming the compromised admin in their data:',len(hits))
for x in hits: print(x['utc'],x['tx'],x['to'],x['sel'],x['data'][8:72])
print('May 2026 calls:')
for x in rows:
    if '2026-05-15'<=x['utc'][:10]<='2026-06-10': print(x['utc'],x['tx'][:16],x['to'],x['sel'],x['data'][8:72])
json.dump(rows,open('../state/runs/safe_calls.json','w'))
