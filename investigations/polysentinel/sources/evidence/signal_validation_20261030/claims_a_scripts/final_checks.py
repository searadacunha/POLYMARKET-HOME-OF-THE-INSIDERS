import json,hashlib,unicodedata,zipfile
from pathlib import Path
P=Path('/Users/benjamindacunha/Projects/PolySentinel');S=P/'studies/signal_validation_20261030'
lock=json.loads((S/'PROTOCOL.lock').read_text());assert all(hashlib.sha256((S/p).read_bytes()).hexdigest()==h for p,h in lock['fichiers'].items());print('FROZEN_HASHES',len(lock['fichiers']),'PASS','CONFIG',hashlib.sha256((S/'data/config.json').read_bytes()).hexdigest())
raw=(S/'registre/tests.jsonl').read_text().splitlines();last='0'*64
for line in raw:
 r=json.loads(line);assert r['prec']==last;last=hashlib.sha256(line.encode()).hexdigest()
name=hashlib.sha1(unicodedata.normalize('NFC',str(S.resolve())).encode()).hexdigest()[:16]+'.json'
print('WITNESS_CANDIDATE',name)
for w in Path('/Users/benjamindacunha/.claude/etudes-gelees').rglob(name):
 d=json.loads(w.read_text());assert d['n']==len(raw) and d['tete']==last;print('WITNESS',w,len(raw),'PASS')
for rel,expected in [('evidence/releases/pilot-20261027T182643Z-source.zip','accda584e59de188c628a4979f8b4b356f4c550011cd462ec0eb05e83adfb1ef'),('evidence/releases/polysentinel-review-20261027-source-evidence.zip','cd103f41b9a0c17f313534e40cb9a6bf72edc20c91759efc28e99c7a5596732e'),('evidence/continuous_20261027/dossiers/source_v12.zip','cd103f41b9a0c17f313534e40cb9a6bf72edc20c91759efc28e99c7a5596732e')]:
 with zipfile.ZipFile(P/rel) as z:
  names=[n for n in z.namelist() if n.endswith('polysentinel/signals.py')];assert len(names)==1
  assert hashlib.sha256(z.read(names[0])).hexdigest()==expected
 print('ARCHIVE_HASH_PASS',rel)
for name in ['results.md','TRANSACTIONS.md','TEMOINS_ET_FILE.md']:
 b=(S/name).read_bytes();assert '\u2014' not in b.decode();print('FINAL_DOCUMENT',name,hashlib.sha256(b).hexdigest())
root=Path('/Users/benjamindacunha/.codex/sessions/2026/10/30/rollout-2026-10-30T10-41-19-01a18c66-5743-7d11-a370-26fa9ce0d659.jsonl')
for i,l in enumerate(root.read_text().splitlines(),1):
 o=json.loads(l)
 if not ('2026-10-30T14:30'<=o.get('timestamp','')<'2026-10-30T14:31'):continue
 p=o.get('payload',{});item=p.get('item',{})
 if item.get('type')=='CommandExecution':
  cmd=str(item.get('command'))
  if 'ana_signal.py' in cmd and 'repro.py' not in cmd:print('REAL_RUN',i,{k:v for k,v in item.items() if k in ['command','status','exit_code','aggregated_output']})
mem=Path('/Users/benjamindacunha/.codex/memories/MEMORY.md')
for i,line in enumerate(mem.read_text().splitlines(),1):
 if 101<=i<=114:print('MEMORY',i,line)
