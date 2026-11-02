from pathlib import Path
import json
root=Path('/Users/benjamindacunha/.codex/sessions/2026/10/30')
for p in sorted(root.glob('*.jsonl')):
 if p.name>='rollout-2026-10-30T14-43':continue
 for i,line in enumerate(p.read_text().splitlines(),1):
  if 'replay_input.jsonl.gz' not in line and 'validation.json.gz' not in line:continue
  o=json.loads(line)
  if o.get('timestamp','')>='2026-10-30T14:43':continue
  x=o.get('payload',{})
  if x.get('type')!='custom_tool_call' or x.get('name')!='exec':continue
  cmd=x.get('input','')
  if 'exec_command' not in cmd or 'apply_patch' in cmd:continue
  if ('cat ' in cmd or 'rg ' in cmd) and not ('python' in cmd):continue
  print('\nCALL',p.name,i,o.get('timestamp'),cmd[:5000])
