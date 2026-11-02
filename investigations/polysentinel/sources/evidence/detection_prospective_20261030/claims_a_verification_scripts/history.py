from pathlib import Path
import json
base=Path('/Users/benjamindacunha/.codex/sessions/2026/10/30')
for p in sorted(base.glob('*.jsonl')):
 hits=[]
 for n,line in enumerate(p.read_text().splitlines(),1):
  if 'replay_input.jsonl.gz' not in line:continue
  d=json.loads(line);x=d.get('payload',{})
  if x.get('type') not in ['function_call','custom_tool_call']:continue
  args=x.get('arguments',x.get('input',''))
  try:a=json.loads(args)
  except (TypeError,ValueError):a=args
  cmd=a.get('cmd',a.get('code','')) if isinstance(a,dict) else a
  if not cmd:continue
  if any(z in cmd for z in ['claims_a','claims_b','OPERATIONAL_REPORT.md']):continue
  lines=cmd.splitlines()
  matching=[k for k,s in enumerate(lines) if 'replay_input.jsonl.gz' in s]
  parts=[]
  for k in matching:parts.extend(lines[max(0,k-2):min(len(lines),k+4)])
  text='\n'.join(parts)
  if len(text)>5000:text=text[:5000]+' [TRUNCATED]'
  hits.append((n,x.get('name'),text))
 if hits:
  print('\nSESSION',p.name)
  for n,name,cmd in hits: print('CALL',n,name,'\n'+cmd)
