from pathlib import Path
import json,gzip,collections
p=Path('/Users/benjamindacunha/Projects/PolySentinel/studies/detection_20261030')
f=json.loads(gzip.decompress((p/'derived/features.json.gz').read_bytes()))
print('FEATURES nominal',len(f['rows']),'wallets',len({r['wallet'] for r in f['rows']}),'effective',f['n_effective_cases'])
for k in ['event_concentration_trigger','synchronized_buy_trigger','joint_concentration_and_synchrony','account_creation_recent','first_bet_after_creation_seconds','amount_over_historical_liquidity','logically_coherent_positions','shared_or_synchronized_funding','precedes_this_publication']:
 print(k,dict(collections.Counter(str(r[k]) for r in f['rows'])))
l=json.loads((p/'derived/label_comparison.json').read_bytes())
print('LABELS',len(l['rows']),len([r for r in l['rows'] if r['wallet']]),dict(collections.Counter(r['mapping_status'] for r in l['rows'])))
for row in l['rows']:
 print('LABEL',row['public_label'],'wallet',row['wallet'],'historical_alias',row['historical_alias_continuity_proven'])
 for s in row['scenarios']:
  print(' ',json.dumps(s,ensure_ascii=False)[:3000])
