from pathlib import Path
import json,gzip,hashlib,stat,re
from collections import Counter
from datetime import datetime,timezone
P=Path('/Users/benjamindacunha/Projects/PolySentinel');S=P/'studies/signal_validation_20261030';V=json.load(gzip.open(S/'derived/validation.json.gz','rt'))
# Companion covariates and token identity mappings.
f={x['wallet']:x for x in V['scenarios'][0]['features'] if x['event_id']=='1105364'};n=0
for l in (S/'TEMOINS_ET_FILE.md').read_text().splitlines():
 if l.startswith('| `0x'):
  c=[x.strip() for x in l.strip('|').split('|')];r=f[c[0].strip('`')]
  assert c[1:]==[f"{r['age_observed_hours']:.6f}",str(r['buy_groups']),f"{r['wallet_buy_nominal_24h']:.6f}",f"{r['mean_price']:.8f}",str(r['score']),str(r['joint'])];n+=1
print('C1_TABLE',n,'all cells exact')
catp=P/'studies/ballon_2026_20261030/data/catalog_refreshed.json';catalog=json.loads(catp.read_text());markets={str(m['id']):m for e in catalog['events'] for m in e['event'].get('markets',[])}
source={r['transaction_hash']:r for r in V['scenarios'][0]['target_source_rows']}
for l in (S/'TRANSACTIONS.md').read_text().splitlines():
 if l.startswith('| 2026-'):
  c=[x.strip() for x in l.strip('|').split('|')];h=re.search(r'/tx/(0x[0-9a-f]+)',c[-1]).group(1);r=source[h];m=markets[r['market_id']]
  assert c[1].split(' / ')[1]==json.loads(m['outcomes'])[json.loads(m['clobTokenIds']).index(r['token_id'])]
print('CATALOG',hashlib.sha256(catp.read_bytes()).hexdigest(),'all 38 token outcomes match')
# Verify local chain directly without importing its writer.
spool=P/'evidence/prospective_eval';prev='0'*64;caps=[];snap=json.loads((P/'evidence/signal_validation_20261030/prospective_snapshot.json').read_text())
paths=sorted(p for p in spool.iterdir() if p.is_dir() and p.name.isdigit())
for i,p in enumerate(paths):
 db=(p/'data.json').read_bytes();rb=(p/'receipt.json').read_bytes();d=json.loads(db);r=json.loads(rb)
 assert d['sequence']==i and d['previous_sha256']==prev
 assert hashlib.sha256(db).hexdigest()==r['data_sha256']
 assert r['persisted_at']<=r['emitted_at']<=r['sealed_at']
 for name in ('data.json','receipt.json'):
  st=(p/name).stat();assert not(st.st_mode&0o222);assert st.st_flags&stat.UF_IMMUTABLE
 prev=hashlib.sha256(rb).hexdigest()
 if i<56:
  assert prev==snap['receipt_hashes'][str(i)];caps+=d.get('captures',[])
print('CHAIN',len(paths),'records','first56',len(caps),'read-only/uchg/hash/order PASS')
print('CAPTURE_KEYS',caps[0]['source_alert'].keys(),'payload_type',type(caps[0]['source_alert']['payload']).__name__)
payloads=[c['source_alert']['payload'] for c in caps]
print('PAYLOAD_KEYS',payloads[0].keys())
pairs={(x['wallet'],x['event_id']) for x in payloads};cases=Counter(x['id'] for x in payloads)
print('PROSPECTIVE',len(caps),len(pairs),len({x['wallet'] for x in payloads}),len({x['event_id'] for x in payloads}),len(caps)-len(cases),'preactivation',sum(x['created_at']<snap['activated_at'] for x in payloads),'missing',sum(bool(c['missing_inputs']) for c in caps),'public_null',sum(c['public_knowledge']['first_public_at'] is None for c in caps))
assert (len(caps),len(pairs),len({x['wallet'] for x in payloads}),len({x['event_id'] for x in payloads}),len(caps)-len(cases))==(275,41,35,21,234)
assert sum(x['created_at']<snap['activated_at'] for x in payloads)==265
for name in ('results.md','TRANSACTIONS.md','TEMOINS_ET_FILE.md'):
 text=(S/name).read_text(); print('FINAL_HASH',name,hashlib.sha256(text.encode()).hexdigest(),'em_dash',text.count(chr(8212)))
print('AMENDMENTS',list((S/'amendements').iterdir()))
