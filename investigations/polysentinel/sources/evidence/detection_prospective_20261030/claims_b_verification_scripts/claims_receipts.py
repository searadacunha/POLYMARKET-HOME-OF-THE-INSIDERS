from pathlib import Path
import json,hashlib,itertools
root=Path('/Users/benjamindacunha/Projects/PolySentinel/evidence/detection_prospective_20261030')
for name in ['refusal_session_receipt.json','verification_session_receipt.json']:
 r=json.loads((root/name).read_bytes())
 with Path(r['source_path']).open('rb') as f:
  raw=next(itertools.islice(f,r['source_line']-1,r['source_line']))
 print(name,json.dumps({'line':r['source_line'],'sha_exact_line':hashlib.sha256(raw).hexdigest()==r['source_line_sha256'],'sha_without_newline':hashlib.sha256(raw.rstrip(b'\r\n')).hexdigest()==r['source_line_sha256'],'native_record_matches':json.loads(raw)==r['native_record'],'record_timestamp':r['native_record']['timestamp']},sort_keys=True))
report=(root/'OPERATIONAL_REPORT.md').read_text()
print('EM_DASH_COUNT',report.count('\u2014'))
for i,l in enumerate(report.splitlines(),1):
 if i in [7,11,24,28,30,34,36,38,40]:print(f'OPERATIONAL_REPORT.md:{i}:{l}')
