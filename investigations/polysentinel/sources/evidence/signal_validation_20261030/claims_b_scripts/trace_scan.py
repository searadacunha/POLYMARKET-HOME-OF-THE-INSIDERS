from pathlib import Path
import json,re
root=Path('/Users/benjamindacunha')
paths=list((root/'.codex/sessions/2026/10/30').glob('*.jsonl'))+list((root/'.claude/projects').glob('*/*.jsonl'))
for p in paths:
 text=p.read_text(errors='replace')
 if 'replay_input.jsonl.gz' not in text:continue
 lines=text.splitlines(); meta=json.loads(lines[0]); date=meta.get('timestamp','');payload=meta.get('payload',{})
 # Never examine current co-reviewer conversations.
 if date>='2026-10-30T14:43:00':
  print('EXCLUDED_CURRENT_REVIEW',p.name);continue
 print('SESSION',p.name,'started',date)
 for i,line in enumerate(lines,1):
  try:d=json.loads(line)
  except ValueError:continue
  pl=d.get('payload',{}); typ=pl.get('type')
  if d.get('type')=='response_item' and typ in ('function_call','custom_tool_call'):
   arg=pl.get('arguments',pl.get('input',''))
   if not isinstance(arg,str):arg=json.dumps(arg)
   if 'replay_input.jsonl.gz' in arg:
    print('CALL',i,d.get('timestamp'),pl.get('name'),arg[:12000].replace('\\n','\n'))
