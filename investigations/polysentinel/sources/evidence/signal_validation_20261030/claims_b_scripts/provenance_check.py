from pathlib import Path
import json,hashlib,zipfile,re
P=Path('/Users/benjamindacunha/Projects/PolySentinel')
profile=P/'research_notes/PolySentinel et le Ballon 2026/labels_after/profile_search_0x8d3319c51520518ad01f6744486ceea29f376f5b.json'
x=json.loads(profile.read_text());print('PROFILE',json.dumps(x,ensure_ascii=False)[:3500])
base=Path('/Users/benjamindacunha/.codex/sessions/2026/10/27')
refs=[(base/'rollout-2026-10-27T16-51-07-01a17e45-d11a-77b0-abe6-457e9f914835.jsonl',[95,98,1183,1187,3932]),(base/'rollout-2026-10-27T16-56-37-01a17e4a-d973-7873-ba6b-aa9290817cdc.jsonl',[131,134,136,139,424,428]),(Path('/Users/benjamindacunha/.claude/projects/-Users-benjamindacunha/b8021738-91d9-4454-bab2-56441d617ca4.jsonl'),[11])]
for p,indices in refs:
 ls=p.read_text().splitlines()
 for i in indices:
  d=json.loads(ls[i-1]);payload=d.get('payload',d);s=json.dumps(payload,ensure_ascii=False)
  print('NATIVE',p.name,i,d.get('timestamp'),'terms',[k for k in ('Ballon','MISSION','signals.py','exploratory-1.1','exploratory-1.2','large_nominal','minimum_baseline','candidate_score','1000','20','0.8','exit_code','exit code') if k in s],'start',s[:180])
for z in ('evidence/releases/pilot-20261027T182643Z-source.zip','evidence/releases/polysentinel-review-20261027-source-evidence.zip','evidence/continuous_20261027/dossiers/source_v12.zip'):
 with zipfile.ZipFile(P/z) as arc:
  names=[n for n in arc.namelist() if n.endswith('/signals.py')]
  for n in names:
   body=arc.read(n);t=body.decode();print('ARCHIVE',z,n,hashlib.sha256(body).hexdigest(),'versions',re.findall('VERSION = (.*)',t))
# Original real invocation and successful tool response.
p=Path('/Users/benjamindacunha/.codex/sessions/2026/10/30/rollout-2026-10-30T10-41-19-01a18c66-5743-7d11-a370-26fa9ce0d659.jsonl');lines=p.read_text().splitlines();ids=set()
for i,line in enumerate(lines,1):
 d=json.loads(line);x=d.get('payload',{});arg=x.get('arguments',x.get('input',''))
 if x.get('type') in ('function_call','custom_tool_call') and 'PYTHONDONTWRITEBYTECODE=1 .venv/bin/python studies/signal_validation_20261030/code/ana_signal.py' in str(arg):
  print('REAL_CALL',i,d.get('timestamp'),str(arg)[:2500]);ids.add(x['call_id'])
 if x.get('type') in ('function_call_output','custom_tool_call_output') and x.get('call_id') in ids: print('REAL_OUTPUT',i,str(x.get('output'))[:4000])
