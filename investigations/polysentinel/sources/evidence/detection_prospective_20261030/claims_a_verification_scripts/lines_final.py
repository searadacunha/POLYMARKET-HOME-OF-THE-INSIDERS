from pathlib import Path
p=Path('/Users/benjamindacunha/Projects/PolySentinel')
for rel in ['studies/detection_20261030/results.md','evidence/detection_prospective_20261030/OPERATIONAL_REPORT.md']:
 print('FILE',rel)
 for n,line in enumerate((p/rel).read_text().splitlines(),1):
  if not line.startswith('|') and line:print(f'{n}: {line}')
