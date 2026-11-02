from pathlib import Path
import json,gzip,collections,datetime
p=Path('/Users/benjamindacunha/Projects/PolySentinel/studies/detection_20261030')
r=json.loads(gzip.decompress((p/'derived/replay.json.gz').read_bytes()))
for s in r['scenarios']:
 ws=s['wallets'];units=s['wallet_events']
 print('DELAY',s['delay_seconds'],'wallets',len(ws),'present',sum(x['present_in_corpus'] for x in ws),'evaluated',sum(x['recent_buy_evaluated_ever'] for x in ws),'behavior',sum(x['first_signal_at'] is not None for x in ws),'priority',sum(x['first_conditional_priority_at'] is not None for x in ws),'wallet_event_evaluated',sum(x['recent_buy_evaluated_ever'] for x in units),'unique_events',len({x['event_id'] for x in units}))
l=json.loads((p/'derived/label_comparison.json').read_bytes())
for j,delay in enumerate([0,60,300,900]):
 rows=[x['scenarios'][j] for x in l['rows']]
 print('LABEL_DELAY',delay, {k:dict(collections.Counter(str(s[k]) for s in rows)) for k in ['resolved','present','recent_buy_evaluated','behavior_detected','conditional_priority']})
for row in l['rows']:
 s=row['scenarios'][0];w=s['wallet_record']
 print('LABEL',row['public_label'],'mapping',row['mapping_status'],'present',s['present'],'behavior',s['behavior_detected'],'priority',s['conditional_priority'])
 if w:
  print('score',w['best_score'],'wallet_rank',w['peak_score_rank'],'wallet_den',w['peak_score_rank_denominator'],'first_signal',w['first_signal_at'],'first_priority',w['first_conditional_priority_at'])
  for pair in s['wallet_event_records']:
   if pair['recent_buy_evaluated_ever']:print(' pair',pair['event_id'],'score',pair['best_score'],'rank',pair['peak_score_rank'],'den',pair['peak_score_rank_denominator'],'first_signal',pair['first_signal_at'],'first_priority',pair['first_conditional_priority_at'])
