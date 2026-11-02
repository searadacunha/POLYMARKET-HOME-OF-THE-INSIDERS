from pathlib import Path
import json,hashlib
r=Path('/Users/benjamindacunha/Projects/PolySentinel')
e=r/'evidence/detection_prospective_20261030'
for name in ['refusal_session_receipt.json','verification_session_receipt.json']:
 obj=json.loads((e/name).read_bytes())
 lines=Path(obj['source_path']).read_bytes().splitlines(keepends=True)
 raw=lines[obj['source_line']-1]
 same=json.loads(raw)==obj['native_record']
 valid=hashlib.sha256(raw).hexdigest()==obj['source_line_sha256']
 print(name,'identical_record',same,'hash_including_newline_match',valid,'time',obj['native_record']['timestamp'])
 assert same and valid
captures=[]
for seq in range(7):captures.extend(json.loads((r/f'evidence/prospective_eval/{seq:08d}/data.json').read_bytes()).get('captures',[]))
print('n',len(captures))
for f in ['id','wallet','event_id']:print('distinct_'+f,len({c['source_alert']['payload'][f] for c in captures}))
text=(e/'OPERATIONAL_REPORT.md').read_text()
print('em_dash_count',text.count(chr(8212)))
print('report_sha',hashlib.sha256(text.encode()).hexdigest())
