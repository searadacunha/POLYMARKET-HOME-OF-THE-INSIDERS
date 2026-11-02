from pathlib import Path
import json,re,os
root=Path('/Users/benjamindacunha/.codex/sessions/2026/10/30')
for p in sorted(root.glob('*.jsonl')):
 # Do not consult current claims-auditor sessions or their messages.
 if p.name>='rollout-2026-10-30T14-43':continue
 hits=[]
 for i,line in enumerate(p.read_text().splitlines(),1):
  if 'replay_input.jsonl.gz' not in line and 'validation.json.gz' not in line:continue
  try:o=json.loads(line)
  except ValueError:continue
  payload=o.get('payload',{})
  if payload.get('type')!='function_call':continue
  name=payload.get('name','')
  if 'exec' not in name:continue
  args=payload.get('arguments','')
  # Show only invocation metadata, never peer conclusions.
  hits.append((i,name,args[:1800]))
 if hits:
  print('\nSESSION',p.name)
  for h in hits:print(h)
print('\nTEMP SOURCE REFERENCES')
for base in ['/private/tmp','/private/var/folders/ym/llyxpdnn5b95whw2zh5tl81h0000gn/T']:
 for p in Path(base).glob('*/*.py'):
  if 'signal-claims' in str(p) or p.stat().st_mtime>=1793371400:continue
  try:text=p.read_text()
  except (OSError,UnicodeError):continue
  if 'replay_input.jsonl.gz' in text or 'validation.json.gz' in text:
   print(str(p),len(text), 'read/recount' if any(x in p.name for x in ['claim','read','recalc','check','verify','trace']) else 'REVIEW')
