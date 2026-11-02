from pathlib import Path
import json
p=Path('/Users/benjamindacunha/.codex/sessions/2026/10/30/rollout-2026-10-30T10-41-19-01a18c66-5743-7d11-a370-26fa9ce0d659.jsonl')
for i,line in enumerate(p.read_text().splitlines(),1):
 d=json.loads(line);x=d.get('payload',{})
 if d.get('type')!='response_item' or x.get('type') not in ('function_call','custom_tool_call'):continue
 arg=x.get('arguments',x.get('input',''))
 if not isinstance(arg,str) or 'replay_input.jsonl.gz' not in arg:continue
 if 'apply_patch' in arg or 'cat >' in arg: print('WRITE_ONLY',i,d['timestamp']);continue
 print('CALL',i,d['timestamp'],arg[:10000])
