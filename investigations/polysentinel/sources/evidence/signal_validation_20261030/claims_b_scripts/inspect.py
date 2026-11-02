from pathlib import Path
import gzip,json
p=Path('/Users/benjamindacunha/Projects/PolySentinel/studies/signal_validation_20261030')
d=json.load(gzip.open(p/'derived/validation.json.gz','rt'));s=d['scenarios'][0]
for k in ('ticks','target_groups','target_source_rows','features','leave_one_transaction_out','cohorts','queues','placebo_transition'):
 v=s[k]; print(k,json.dumps(v[0] if isinstance(v,list) else ({a:{b:c for b,c in x.items() if b not in ('queue',)} for a,x in v.items()} if k=='queues' else v),ensure_ascii=False))
print('last_tick',json.dumps(s['ticks'][-1]))
past=json.load(gzip.open(p/'data/prior_replay.json.gz','rt'));print('prior keys',past.keys());print('prior scenario keys',past['scenarios'][0].keys());print('prior wallets example',json.dumps(past['scenarios'][0]['wallets'][0]));print('config', (p/'data/config.json').read_text())
