import json,hashlib,stat
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
P=Path('/Users/benjamindacunha/Projects/PolySentinel'); S=P/'evidence/prospective_eval'; E=P/'evidence/signal_validation_20261030'
snap=json.loads((E/'prospective_snapshot.json').read_text());captures=[];receipts=[];previous='0'*64;hashes={}
for n in range(64):
 folder=S/f'{n:08d}';file=folder/'data.json';b=file.read_bytes();d=json.loads(b);r=json.loads((folder/'receipt.json').read_text());h=hashlib.sha256(b).hexdigest()
 assert d['sequence']==n;assert d['previous_sha256']==previous;assert r['data_sha256']==h;previous=h
 assert not(file.stat().st_mode&0o222);assert file.stat().st_flags&stat.UF_IMMUTABLE
 assert r['persisted_at']<=r['emitted_at']<=r['sealed_at'];receipts.append(r)
 if n==0:activation=d['next_state']['activated_at'];fingerprints=d['next_state']['fingerprints']
 if n<56:
  captures+=d.get('captures',[]);hashes[str(n)]=hashlib.sha256((folder/'receipt.json').read_bytes()).hexdigest()
assert hashes==snap['receipt_hashes']
payloads=[c['source_alert']['payload'] for c in captures]
recount={'observations':len(captures),'distinct_cases':len({x['id'] for x in payloads}),'distinct_wallets':len({x['wallet'] for x in payloads}),'distinct_events':len({x['event_id'] for x in payloads}),'observations_of_cases_created_before_activation':sum(x['created_at']<activation for x in payloads),'observations_without_first_public_at':sum(c['public_knowledge']['first_public_at'] is None for c in captures),'observations_with_missing_inputs':sum(bool(c['missing_inputs']) for c in captures),'distinct_case_material_fingerprints':len({(x['id'],x['material_fingerprint']) for x in payloads})}
recount['additional_observations_of_same_case']=recount['observations']-recount['distinct_cases']
for k,v in recount.items():assert v==snap[k],(k,v,snap[k])
assert Counter(x['id'] for x in payloads)=={x['case_id']:x['observations'] for x in snap['cases']}
assert len(fingerprints)==26
for rel,h in fingerprints.items():assert hashlib.sha256((P/rel).read_bytes()).hexdigest()==h
print('PROSPECTIVE',recount,'CHAIN64_PASS','FINGERPRINTS26_PASS')
runtime=json.loads((E/'runtime_1435.json').read_text());m=runtime['monitor'];assert m['cap_bytes']-m['used_bytes']==m['remaining_bytes']==85248;assert m['sequence']+1==64;assert m['source_status']=='REFUSED';print('REFUSAL_TIME',datetime.fromtimestamp(m['checked_at'],timezone.utc).isoformat(),'sequence',m['sequence'],'cursor',m['cursor'])
cat=P/'studies/ballon_2026_20261030/data/catalog_refreshed.json';assert hashlib.sha256(cat.read_bytes()).hexdigest()=='fc7e7b11fb3e973a484b984387a91f962b06f96231635d8904b64572d1d1ccbe'
c=json.loads(cat.read_text());markets={str(m['id']):m for e in c['events'] for m in e['event'].get('markets',[])}
import gzip
s=json.loads(gzip.decompress((P/'studies/signal_validation_20261030/derived/validation.json.gz').read_bytes()))['scenarios'][0]
lines=[x for x in (P/'studies/signal_validation_20261030/TRANSACTIONS.md').read_text().splitlines() if x.startswith('| 2026-')]
for line,r in zip(lines,s['target_source_rows']):
 m=markets[r['market_id']];outcome=json.loads(m['outcomes'])[json.loads(m['clobTokenIds']).index(r['token_id'])];assert f"{r['market_id']} / {outcome}" in line
print('CATALOG_IDENTITIES_ALL38_PASS')
profile=P/'research_notes/PolySentinel et le Ballon 2026/labels_after/profile_search_0x8d3319c51520518ad01f6744486ceea29f376f5b.json';o=json.loads(profile.read_text());print('ALIAS_KEYS',list(o));print(str(o)[:1800])
for name in ['results.md','TRANSACTIONS.md','TEMOINS_ET_FILE.md']:
 file=P/'studies/signal_validation_20261030'/name;print('FINAL_SHA',name,hashlib.sha256(file.read_bytes()).hexdigest())
for i,line in enumerate((P/'studies/signal_validation_20261030/results.md').read_text().splitlines(),1):
 if any(x in line for x in ['fragment','300/900','noyau `','Gel initial','MAJEURE','## Deviations']):print('FINAL_LINE',i,line)
