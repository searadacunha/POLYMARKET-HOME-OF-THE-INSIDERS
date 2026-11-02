from pathlib import Path
import json,re
root=Path('/Users/benjamindacunha/.codex/sessions/2026/10/30')
for p in sorted(root.glob('*.jsonl')):
 matches=[]
 with p.open() as f:
  for n,line in enumerate(f,1):
   try:d=json.loads(line)
   except ValueError:continue
   a=d.get('payload',{})
   if d.get('type')!='response_item' or a.get('type') not in ('function_call','custom_tool_call'):continue
   if not any(v in a.get('name','') for v in ('exec','shell','command')):continue
   s=a.get('arguments',a.get('input',''))
   if not isinstance(s,str):s=json.dumps(s)
   if not any(k in s for k in ('replay_input.jsonl.gz','run_replay(', 'runtime_size_profile','replay_core')):continue
   matches.append((n,d.get('timestamp'),a.get('name'),s.replace('\n',' ')[:600]))
 if matches:
  print('SESSION',p.name)
  for m in matches:print(*m,sep=' | ')
