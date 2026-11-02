"""Audit: published figures of the collective part and the exploratory files, read back from the outputs. Reads only."""
import json,math
C='/Users/benjamindacunha/Projects/PolySentinel-investigation/collective/'
J=lambda p:json.load(open(C+p))
e1=J('derived/A_E1.json');g=J('derived/A_E1G.json');e2=J('derived/A_E2.json');e3=J('derived/A_E3.json');e6=J('derived/B_E6.json');e7=J('derived/B_E7.json');rc=J('exploratoire/rank_combos.json');cb=J('exploratoire/combos.json');pd=J('exploratoire/price_days.json')
print('E1 keys',list(e1)[:12]);print(json.dumps(e1,ensure_ascii=False)[:1100])
print('E1G ranks',json.dumps(g['ranks'],ensure_ascii=False)[:900]);print('burden',g['burden_new_tokens_per_day'])
print('E2',json.dumps(e2,ensure_ascii=False)[:700]);print('E3',json.dumps(e3,ensure_ascii=False)[:500])
print('E6 summary',json.dumps(e6['summary'],ensure_ascii=False)[:1200]);print('E6 groups',{k:(len(v) if hasattr(v,'__len__') else v) for k,v in e6['groups'].items()},'per_wallet',len(e6['per_wallet']))
vals=[v for k,v in e6['per_wallet'].items()]
print('per wallet sample',json.dumps(vals[0])[:300])
print('rank_combos',list(rc)[:12]);print(json.dumps(rc,ensure_ascii=False)[:1700])
print('price_days keys',list(pd)[:14])
print('ages',open(C+'data/ages_counts.json').read())
print('E7',json.dumps(e7,ensure_ascii=False)[:500])
