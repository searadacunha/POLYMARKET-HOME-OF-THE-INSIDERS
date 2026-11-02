from pathlib import Path
import json,hashlib
p=Path('/Users/benjamindacunha/Projects/PolySentinel/studies/detection_20261030')
lock=json.loads((p/'PROTOCOL.lock').read_bytes())
bad=[]
for rel,h in lock['fichiers'].items():
 if hashlib.sha256((p/rel).read_bytes()).hexdigest()!=h:bad.append(rel)
print('frozen_files',len(lock['fichiers']),'mismatches',bad)
reg=[json.loads(x) for x in (p/'registre/tests.jsonl').read_text().splitlines()]
for row in reg:
 if row['donnees']!='reelles':continue
 out=p/row['sortie']
 print('real_row',row['test'],'n_comparaisons',row['n_comparaisons'],'output_hash',hashlib.sha256(out.read_bytes()).hexdigest()==row['sortie_sha'],'code_gele',row['code_gele'],'phase',row['phase'])
n=sum(r['n_comparaisons'] for r in reg if r['donnees']=='reelles')
print('n_comparaisons',n,'seuil',.05/n)
print('amendements',list((p/'amendements').glob('*')))
