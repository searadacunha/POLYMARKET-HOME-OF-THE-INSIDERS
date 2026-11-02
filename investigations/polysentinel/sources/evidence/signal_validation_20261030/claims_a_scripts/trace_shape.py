from pathlib import Path
import json
p=Path('/Users/benjamindacunha/.codex/sessions/2026/10/30/rollout-2026-10-30T10-41-19-01a18c66-5743-7d11-a370-26fa9ce0d659.jsonl')
n=0
for i,l in enumerate(p.read_text().splitlines(),1):
 if 'replay_input.jsonl.gz' in l:
  o=json.loads(l);x=o.get('payload',{});print(i,o.get('type'),x.keys(),str(x)[:400]);n+=1
  if n==8:break
P=Path('/Users/benjamindacunha/Projects/PolySentinel/evidence/prospective_eval')
for name in ['00000000/data.json','00000001/data.json']:
 d=json.loads((P/name).read_text());print(name,[(k,type(v).__name__,len(v) if hasattr(v,'__len__') else None) for k,v in d.items()])
 print(str(d)[:2400])
