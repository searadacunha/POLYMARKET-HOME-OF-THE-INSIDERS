from pathlib import Path
import json,gzip,hashlib
from datetime import datetime,timezone
root=Path('/Users/benjamindacunha/Projects/PolySentinel');S=root/'studies/signal_validation_20261030'
p=Path('/Users/benjamindacunha/.codex/sessions/2026/10/30/rollout-2026-10-30T10-41-19-01a18c66-5743-7d11-a370-26fa9ce0d659.jsonl');lines=p.read_text().splitlines();ids=set()
for i,l in enumerate(lines,1):
 d=json.loads(l);x=d.get('payload',{});args=str(x.get('arguments',x.get('input','')))
 if x.get('type') in ('custom_tool_call','function_call') and 'write_stdin' in args and '50279' in args:
  ids.add(x['call_id']);print('WAIT_CALL',i,d['timestamp'],args)
 if x.get('type') in ('function_call_output','custom_tool_call_output') and x.get('call_id') in ids:print('COMPLETION',i,x['output'])
old=json.load(gzip.open(S/'data/prior_replay.json.gz','rt'));target=next(r for r in old['scenarios'][0]['wallet_events'] if r['wallet']=='0x8d3319c51520518ad01f6744486ceea29f376f5b' and r['event_id']=='1105364');f=target['first_signals']['event_concentration'];t=f['at'];rows=[json.loads(l) for l in gzip.open(S/'data/replay_input.jsonl.gz','rt')];buys=[r for r in rows if r['wallet']==target['wallet'] and r['side']=='BUY' and t-86400<=r['timestamp']<=t];num=sum(r['size']*r['price'] for r in buys if r['event_id']=='1105364');den=sum(r['size']*r['price'] for r in buys);assert abs(num/den-f['value'])<1e-10
print('FIRST_CONCENTRATION',datetime.fromtimestamp(t,timezone.utc),num,den,num/den,'recorded',f)
print('RULE_COUNTS',len(json.loads((S/'controles/synthetic.json').read_text())))
for n in ('runtime_1435.json','live_verification.json','prospective_monitor_two_runs.json'):
 d=json.loads((root/'evidence/signal_validation_20261030'/n).read_text());m=d.get('monitor',d.get('status'));print('OPERATIONAL',n,datetime.fromtimestamp(m['checked_at'],timezone.utc),m['used_bytes'],m['remaining_bytes'],m['source_status'],m['notification'])
print('FINAL_SHA',hashlib.sha256((S/'results.md').read_bytes()).hexdigest())
