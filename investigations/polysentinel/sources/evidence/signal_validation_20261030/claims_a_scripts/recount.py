import json,gzip,hashlib,math,re
from pathlib import Path
from statistics import median
from collections import Counter,defaultdict
from datetime import datetime,timezone
P=Path('/Users/benjamindacunha/Projects/PolySentinel/studies/signal_validation_20261030')
D=json.loads(gzip.decompress((P/'derived/validation.json.gz').read_bytes()))
R=[json.loads(x) for x in gzip.decompress((P/'data/replay_input.jsonl.gz').read_bytes()).decode().splitlines()]
OLD=json.loads(gzip.decompress((P/'data/prior_replay.json.gz').read_bytes()))
T='0x8d3319c51520518ad01f6744486ceea29f376f5b'; E='1105364'
assert len(R)==len({r['id'] for r in R})==15148

def groups(rows):
 out={}
 for r in rows:
  key=(r['wallet'].lower(),str(r['token_id']),r['side'],r.get('order_hash') or r.get('transaction_hash') or r['id'])
  g=out.setdefault(key,dict(wallet=r['wallet'].lower(),event_id=r['event_id'],side=r['side'],timestamp=r['timestamp'],first_timestamp=r['timestamp'],nominal=0,size=0,transaction_hash=r['transaction_hash']))
  g['timestamp']=max(g['timestamp'],r['timestamp']);g['first_timestamp']=min(g['first_timestamp'],r['timestamp']);g['nominal']+=r['size']*r['price'];g['size']+=r['size']
 return list(out.values())
def features(at,delay,rows=R):
 rows=[r for r in rows if r['timestamp']+delay<=at]
 assert len(rows)<50000
 gs=groups(rows); wallet=defaultdict(list);pairs=defaultdict(list);first={}
 for r in rows:first[r['wallet']]=min(first.get(r['wallet'],float('inf')),r['timestamp'])
 for g in gs:
  wallet[g['wallet']].append(g)
  if g['side']=='BUY' and g['timestamp']>=at-86400:pairs[g['wallet'],g['event_id']].append(g)
 out={}
 for k,recent in pairs.items():
  buys=[g for g in wallet[k[0]] if g['side']=='BUY']
  recentwallet=[g for g in buys if g['timestamp']>=at-86400]
  nominal=sum(g['nominal'] for g in recentwallet);spend=sum(g['nominal'] for g in recent)
  capable=max(sum(x['timestamp']<g['first_timestamp'] for x in buys) for g in recent)>=20
  shift=False
  for g in recent:
   before=[x['nominal'] for x in buys if x['timestamp']<g['first_timestamp']]
   if len(before)>=20:
    med=median(before);mad=median(abs(x-med) for x in before)
    if g['nominal']>=max(1000,5*med,med+6*1.4826*mad):shift=True
  age=(at-first[k[0]])/3600
  price=spend/sum(g['size'] for g in recent)
  bins=[math.floor(math.log2(max(1,x))) for x in (age,len(buys),nominal)]+[int(max(g['timestamp'] for g in recent)//86400),min(int(price*5),4)]
  conc=spend>=1000 and spend/nominal>=.8
  out[k]=dict(baseline_capable=capable,joint=bool(conc and shift),bins=bins,age_observed_hours=age,buy_groups=len(buys),wallet_buy_nominal_24h=nominal,mean_price=price,independent_two_family_score=int(conc)+int(shift))
 return out
counts=Counter()
for s,prev in zip(D['scenarios'],OLD['scenarios']):
 at=s['at'];delay=s['delay'];calc=features(at,delay)
 for f in s['features']:
  x=calc[f['wallet'],f['event_id']]
  for k in ('baseline_capable','joint','bins','buy_groups'):assert x[k]==f[k],(delay,k,x[k],f[k])
  for k in ('age_observed_hours','wallet_buy_nominal_24h','mean_price'):assert math.isclose(x[k],f[k],rel_tol=1e-12,abs_tol=1e-9),(delay,k)
 cs={}
 for name in ['C0','C1','C2']:
  vals={k:x for k,x in calc.items() if k[1]==E and (name=='C0' or x['baseline_capable']) and (name!='C2' or x['bins']==calc[T,E]['bins'])}
  joint=sum(x['joint'] for x in vals.values());n=len(vals)
  assert (joint,n)==(s['cohorts'][name]['including_target']['joint'],s['cohorts'][name]['including_target']['n'])
  assert sorted(k[0] for k in vals if k[0]!=T)==s['cohorts'][name]['wallets']
  cs[name]=(joint,n,joint-1,n-1)
 tick_features=[]
 for tick in s['ticks']:
  f=features(tick['at'],delay);tick_features.append(f)
  summary={'n':len(f),'joint':sum(x['joint'] for x in f.values()),'baseline_capable':sum(x['baseline_capable'] for x in f.values())}
  assert summary==tick['summary'];counts['V1_ticks']+=max(1,len(f))
 old,new=tick_features[0],calc;common=old.keys()&new.keys()
 transition={'common':len(common),'lost':len(old.keys()-new.keys()),'new':len(new.keys()-old.keys()),'counts':dict(Counter(f"{int(old[k]['joint'])}->{int(new[k]['joint'])}" for k in common))}
 assert transition==s['placebo_transition']
 assert (T,E) in common
 counts['V3_cohorts']+=3*len(calc)+len(common)+6
 queuechecks={}
 for kind in ['wallets','wallet_events']:
  evaluated=[r for r in prev[kind] if r['evaluated_ever']]
  queue=sorted([r for r in evaluated if r['first_conditional_priority_at'] is not None],key=lambda r:(r['first_conditional_priority_at'],r['wallet'],r.get('event_id','')))
  target=next(r for r in queue if r['wallet']==T and r.get('event_id',E)==E)
  q=s['queues'][kind]
  assert q['queue_position']==queue.index(target)+1
  assert q['priority']==len(queue)
  assert q['evaluated']==len(evaluated)
  assert q['peak_score_distribution']=={str(k):v for k,v in Counter(r['best_score'] for r in evaluated).items()}
  assert q['peak_score_rank_interval']==[1+sum(r['best_score']>2 for r in evaluated),sum(r['best_score']>=2 for r in evaluated)]
  assert [r['wallet'] for r in queue]==[r['wallet'] for r in q['queue']]
  queuechecks[kind]=(len(evaluated),len(queue),queue.index(target)+1,q['peak_score_distribution'])
  counts['V2_queue']+=len(evaluated)
 rows=[r for r in R if r['wallet']==T and r['timestamp']+delay<=at]
 assert sorted(r['id'] for r in rows)==sorted(r['id'] for r in s['target_source_rows'])
 gs=groups(rows);buys=[g for g in gs if g['side']=='BUY'];trigger=max(buys,key=lambda g:g['timestamp'])
 baseline=[g['nominal'] for g in buys if g['timestamp']<trigger['first_timestamp']]
 med=median(baseline);mad=median(abs(x-med) for x in baseline);threshold=max(1000,5*med,med+6*1.4826*mad)
 recent=[g for g in buys if g['timestamp']>=at-86400]
 nominal=sum(g['nominal'] for g in recent);event=sum(g['nominal'] for g in recent if g['event_id']==E)
 assert math.isclose(event/.8-nominal,s['hidden_other_event_buy_strictly_greater_than'],rel_tol=1e-12)
 variants=Counter()
 for v in s['leave_one_transaction_out']:
  tx=v['removed_transaction'];reduced=[r for r in rows if r['transaction_hash']!=tx]
  fx=features(at,delay,reduced).get((T,E));assert bool(fx)==v['evaluated']
  assert fx['independent_two_family_score']==v['score'],(delay,tx)
  assert set(v['rules'])<=set(['event_concentration','wallet_size_shift'])
  variants[v['score']]+=1
 assert len(s['leave_one_transaction_out'])==len({r['transaction_hash'] for r in rows})==38
 counts['V4_missing']+=len(variants.elements().__iter__().__class__.__name__) if False else 39
 print('SCENARIO',delay,'joint/n',sum(x['joint'] for x in calc.values()),len(calc),'cohorts',cs,'transition',transition,'queues',queuechecks,'variants',dict(variants))
 if delay==0: print('TARGET',dict(rows=len(rows),groups=len(gs),buy=len(buys),sell=len(gs)-len(buys),baseline=len(baseline),median=med,mad=mad,threshold=threshold,nominal=trigger['nominal'],recent_groups=len(recent),event=event,total=nominal,age=calc[T,E]['age_observed_hours'],tie=[k for k,x in calc.items() if x['joint']],actual_observed_min=min(r['observed_at'] for r in rows),actual_observed_max=max(r['observed_at'] for r in rows)))
assert dict(counts)==D['comparisons'];print('COMPARISONS',dict(counts),sum(counts.values()))
# Full documentary projections, not new analyses.
s=D['scenarios'][0];txlines=[line for line in (P/'TRANSACTIONS.md').read_text().splitlines() if line.startswith('| 2026-')]
assert len(txlines)==38
for line,r in zip(txlines,s['target_source_rows']):
 fields=[x.strip() for x in line.strip('|').split('|')]
 assert fields[0]==datetime.fromtimestamp(r['timestamp'],timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
 assert fields[1].split(' / ')[0]==r['market_id'];assert fields[2]==r['side']
 assert fields[3]==f"{r['size']:.8f}";assert fields[4]==f"{r['price']:.10f}";assert fields[5]==f"{r['size']*r['price']:.6f}"
 assert r['transaction_hash'] in fields[7]
qlines=[line for line in (P/'TEMOINS_ET_FILE.md').read_text().splitlines() if re.match(r'\| \d+ \|',line)]
assert len(qlines)==23
for i,(line,r) in enumerate(zip(qlines,s['queues']['wallets']['queue']),1):
 fields=[x.strip() for x in line.strip('|').split('|')]
 assert int(fields[0])==i;assert fields[1]==datetime.fromtimestamp(r['first_conditional_priority_at'],timezone.utc).strftime('%Y-%m-%d %H:%M:%S');assert fields[2].strip('`')==r['wallet'];assert int(fields[3])==r['best_score']
c1lines=[line for line in (P/'TEMOINS_ET_FILE.md').read_text().splitlines() if line.startswith('| `0x')]
for line in c1lines:
 fields=[x.strip() for x in line.strip('|').split('|')];f=next(f for f in s['features'] if f['wallet']==fields[0].strip('`') and f['event_id']==E)
 assert fields[1]==f"{f['age_observed_hours']:.6f}";assert fields[2]==str(f['buy_groups']);assert fields[3]==f"{f['wallet_buy_nominal_24h']:.6f}";assert fields[4]==f"{f['mean_price']:.8f}";assert fields[5]==str(f['score']);assert fields[6]==str(f['joint'])
print('PROJECTIONS',len(txlines),'transactions;',len(qlines),'queue rows;',len(c1lines),'C1 rows: all fields checked PASS')
for name in ['results.md','TRANSACTIONS.md','TEMOINS_ET_FILE.md']:
 b=(P/name).read_bytes();print('DOCUMENT_SHA',name,hashlib.sha256(b).hexdigest())
 for i,line in enumerate(b.decode().splitlines(),1):
  if '\u2014' in line:print('EM_DASH',name,i,line)
