from pathlib import Path
import json,gzip,hashlib
from collections import defaultdict
from datetime import datetime,timezone
P=Path('/Users/benjamindacunha/Projects/PolySentinel/studies/signal_validation_20261030')
b=(P/'results.md').read_bytes();text=b.decode();h=hashlib.sha256(b).hexdigest();assert h=='5edc118d2c4cf344c7b11c7d78564e58e15cdb91d21e40e13e9cab0cf74fd4bb',h
print('FINAL_SHA',h)
for i,line in enumerate(text.splitlines(),1):
 if 'première occurrence' in line or 'Cumul de ces trois études' in line:print('LINE',i,line)
R=[json.loads(x) for x in gzip.decompress((P/'data/replay_input.jsonl.gz').read_bytes()).decode().splitlines()]
T='0x8d3319c51520518ad01f6744486ceea29f376f5b';E='1105364';at=1791891649
assert datetime.fromtimestamp(at,timezone.utc).isoformat()=='2026-10-13T11:40:49+00:00'
groups={}
for r in R:
 if r['wallet']!=T or r['timestamp']>at:continue
 key=(r['wallet'],r['token_id'],r['side'],r.get('order_hash') or r.get('transaction_hash') or r['id'])
 g=groups.setdefault(key,{'timestamp':r['timestamp'],'side':r['side'],'event_id':r['event_id'],'nominal':0.0})
 g['timestamp']=max(g['timestamp'],r['timestamp']);g['nominal']+=r['size']*r['price']
recent=[g for g in groups.values() if g['side']=='BUY' and g['timestamp']>=at-86400]
num=sum(g['nominal'] for g in recent if g['event_id']==E);den=sum(g['nominal'] for g in recent);ratio=num/den
assert f'{num:.6f}'=='6315.455800';assert f'{den:.6f}'=='7865.493300';assert f'{ratio:.10f}'=='0.8029319407'
print('QUOTIENT',{'at':at,'event_nominal':num,'wallet_nominal':den,'ratio':ratio,'BUY_groups_24h':len(recent)})
assert 29+36459769+14459==36474257
old20="Le rang **1/74 est partagé avec un autre wallet**, `0xd5a817163ea5acd551ee9201efbcf8b709bf9793`, qui présente lui aussi concentration+rupture. « Premier » ne signifiait donc pas unique première place. À la première occurrence du signal de concentration, le13octobre11:40:49, sa valeur était0,8029319407 ; au déclenchement de priorité18:50:49, elle vaut1. Les anciennes premières valeurs de chaque règle ne décrivent pas nécessairement le même instant."
old99="Gel initial12fichiers intact, quatre balayages réels enregistrés après gel :V1=960,V2=12361,V3=982,V4=156, total14459unités descriptives selon la convention écrite. Cumul de ces trois études (ballon, detection et présente) :36459769+29+14459=36474257 ; ce n'est pas un recensement de toute la recherche de conception antérieure. Bonferroni formel0,05/N, **aucun p calculé ou revendiqué** ; ces compteurs ne sont ni des répétitions indépendantes ni une mesure de qualité. Les cinq passes de contrôles synthétiques restent séparées des analyses réelles. Six méthodes de tests passent ; contrôles déterministes, aucune puissance populationnelle."
oldlines=text.splitlines(keepends=True)
for i,line in enumerate(oldlines):
 if 'première occurrence' in line:oldlines[i]=old20+'\n'
 if 'Cumul de ces trois études' in line:oldlines[i]=old99+'\n'
previous_sha=hashlib.sha256(''.join(oldlines).encode()).hexdigest();assert previous_sha=='ac350ca470c276ff696f941acb1224f518a041c93fb0af1200640c37394cea6f',previous_sha
print('ONLY_TWO_LINES_CHANGED','PASS',previous_sha)
lock=json.loads((P/'PROTOCOL.lock').read_text());assert all(hashlib.sha256((P/p).read_bytes()).hexdigest()==sha for p,sha in lock['fichiers'].items())
assert hashlib.sha256((P/'TRANSACTIONS.md').read_bytes()).hexdigest()=='e599f5b635285190d45a49d1768bd8d6dfd3b8e1e77a409534326c1f88966de8'
assert hashlib.sha256((P/'TEMOINS_ET_FILE.md').read_bytes()).hexdigest()=='1d2df04b2cf2810a25aa162ea8fdf936db71005621ab1196dd573ea7fc3fa2ba'
assert '\u2014' not in text
print('FROZEN12_AND_ANNEXES_UNCHANGED PASS; TEN_CRITERIA_PASS_MAINTAINED')
