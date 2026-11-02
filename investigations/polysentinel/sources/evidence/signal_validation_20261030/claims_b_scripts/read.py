import sys,json,gzip
from pathlib import Path
p=Path(sys.argv[1]); mode=sys.argv[2] if len(sys.argv)>2 else 'lines'
s=gzip.open(p,'rt').read() if p.suffix=='.gz' else p.read_text()
if mode=='lines':
 a=int(sys.argv[3]) if len(sys.argv)>3 else 1; b=int(sys.argv[4]) if len(sys.argv)>4 else 10**9
 for i,x in enumerate(s.splitlines(),1):
  if a<=i<=b: print(f'{i}: {x}')
elif mode=='keys':
 d=json.loads(s)
 def walk(o,p='',depth=0):
  if depth>2:return
  if isinstance(o,dict):
   for k,v in o.items():
    print(p+'.'+k,type(v).__name__,len(v) if isinstance(v,(list,dict)) else str(v)[:300]);walk(v,p+'.'+k,depth+1)
  elif isinstance(o,list) and o: walk(o[0],p+'[0]',depth+1)
 walk(d)
else: print(json.dumps(json.loads(s),indent=2,ensure_ascii=False))
