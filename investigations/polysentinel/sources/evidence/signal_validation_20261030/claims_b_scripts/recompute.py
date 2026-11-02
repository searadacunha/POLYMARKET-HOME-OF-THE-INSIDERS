import json,gzip,hashlib,math,re
from pathlib import Path
from collections import defaultdict,Counter
from statistics import median
from datetime import datetime,timezone
P=Path('/Users/benjamindacunha/Projects/PolySentinel/studies/signal_validation_20261030')
T='0x8d3319c51520518ad01f6744486ceea29f376f5b'; E='1105364'
load=lambda p: json.load(gzip.open(p,'rt')) if p.suffix=='.gz' else json.loads(p.read_text())
def utc(t):return datetime.fromtimestamp(t,timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
def close(a,b):assert math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-7),(a,b)
d=load(P/'derived/validation.json.gz'); old=load(P/'data/prior_replay.json.gz')
rows=[json.loads(l) for l in gzip.open(P/'data/replay_input.jsonl.gz','rt')]
assert len(rows)==15148
lock=load(P/'PROTOCOL.lock')
assert all(hashlib.sha256((P/k).read_bytes()).hexdigest()==v for k,v in lock['fichiers'].items())
print('HASHES frozen',len(lock['fichiers']),'output',hashlib.sha256((P/'derived/validation.json.gz').read_bytes()).hexdigest())

def features(at,delay,drop=None):
 available=[r for r in rows if r['timestamp']+delay<=at and not (r['wallet']==T and r['transaction_hash']==drop)]
 assert len(available)<=50000
 groups=defaultdict(list)
 for r in available:groups[(r['wallet'],r['token_id'],r['side'],r.get('order_hash') or r.get('transaction_hash') or r['id'])].append(r)
 gs=[]
 for k,v in groups.items():
  g=dict(v[0]);g.update(first_timestamp=min(x['timestamp'] for x in v),timestamp=max(x['timestamp'] for x in v),size=sum(x['size'] for x in v),nominal=sum(x['size']*x['price'] for x in v));gs.append(g)
 bywal=defaultdict(list); pairs=defaultdict(list)
 for g in gs:
  bywal[g['wallet']].append(g)
  if g['side']=='BUY' and g['timestamp']>=at-86400:pairs[g['wallet'],g['event_id']].append(g)
 out={}
 for k,recent in pairs.items():
  hist=bywal[k[0]];buys=[g for g in hist if g['side']=='BUY'];recentall=[g for g in buys if g['timestamp']>=at-86400]
  total=sum(g['nominal'] for g in recentall); spend=sum(g['nominal'] for g in recent);age=(at-min(g['first_timestamp'] for g in hist))/3600
  counts=[sum(g['timestamp']<x['first_timestamp'] for g in buys) for x in recent]
  price=spend/sum(g['size'] for g in recent)
  shift=False
  for x in recent:
   prior=[g['nominal'] for g in buys if g['timestamp']<x['first_timestamp']]
   if len(prior)>=20:
    med=median(prior);mad=median(abs(y-med) for y in prior)
    shift |= x['nominal']>=max(1000,5*med,med+6*1.4826*mad)
  concentration=spend>=1000 and spend/total>=.8
  out[k]=dict(wallet=k[0],event_id=k[1],age_observed_hours=age,buy_groups=len(buys),wallet_buy_nominal_24h=total,mean_price=price,
   maximum_prior_buy_groups=max(counts),baseline_capable=max(counts)>=20,bins=[math.floor(math.log2(max(1,x))) for x in (age,len(buys),total)]+[int(max(g['timestamp'] for g in recent)//86400),min(int(price*5),4)],joint=bool(concentration and shift),concentration=concentration,shift=bool(shift))
 return out,gs,available

def rate(fs):return dict(n=len(fs),joint=sum(f['joint'] for f in fs),baseline_capable=sum(f['baseline_capable'] for f in fs))
counts=Counter()
for s,prev in zip(d['scenarios'],old['scenarios']):
 delay=s['delay'];at=s['at']; f,gs,avail=features(at,delay);of=features(at-86400,delay)[0]
 for v in s['features']:
  mine=f[v['wallet'],v['event_id']]
  for key,x in mine.items():
   if key in ('concentration','shift'):continue
   if isinstance(x,float):close(x,v[key])
   else: assert x==v[key],(delay,key,x,v[key])
 assert len(f)==len(s['features'])
 for k,v in s['cohorts'].items():
  fs=[x for key,x in f.items() if key[1]==E and (k=='C0' or x['baseline_capable']) and (k!='C2' or x['bins']==f[T,E]['bins'])]
  assert rate(fs)==v['including_target'];assert rate([x for x in fs if x['wallet']!=T])==v['controls']
 common=f.keys()&of.keys(); transitions=Counter(f"{int(of[k]['joint'])}->{int(f[k]['joint'])}" for k in common)
 assert s['placebo_transition']==dict(common=len(common),lost=len(of.keys()-f.keys()),new=len(f.keys()-of.keys()),counts=dict(transitions))
 for tick in s['ticks']:
  tf=features(tick['at'],delay)[0]
  assert rate(list(tf.values()))==tick['summary'];assert rate([x for x in tf.values() if x['baseline_capable']])==tick['capable_summary']
  counts['V1_ticks']+=len(tf)
 counts['V3_cohorts']+=3*len(f)+len(common)+6
 for k,q in s['queues'].items():
  eligible=[r for r in prev[k] if r['evaluated_ever']]; queue=sorted([r for r in eligible if r['first_conditional_priority_at'] is not None],key=lambda r:(r['first_conditional_priority_at'],r['wallet'],r.get('event_id','')))
  tar=next(r for r in eligible if r['wallet']==T and r.get('event_id',E)==E)
  pos=next(i for i,r in enumerate(queue,1) if r is tar)
  earlier=sum(r['first_conditional_priority_at']<tar['first_conditional_priority_at'] for r in queue);ties=sum(r['first_conditional_priority_at']==tar['first_conditional_priority_at'] for r in queue)
  ahead=sum(r['best_score']>tar['best_score'] for r in eligible);equal=sum(r['best_score']==tar['best_score'] for r in eligible)
  assert (len(eligible),len(queue),pos,earlier,[earlier+1,earlier+ties],[ahead+1,ahead+equal])==(q['evaluated'],q['priority'],q['queue_position'],q['strictly_earlier'],q['queue_tie_interval'],q['peak_score_rank_interval'])
  assert {str(k):v for k,v in Counter(r['best_score'] for r in eligible).items()}==q['peak_score_distribution']
  assert [{key:r.get(key) for key in ('wallet','event_id','first_conditional_priority_at','best_score')} for r in queue]==q['queue']
  counts['V2_queue']+=len(eligible)
  print('QUEUE',delay,k,len(eligible),len(queue),pos,earlier,[ahead+1,ahead+equal],q['peak_score_distribution'])
 variants=Counter()
 for v in s['leave_one_transaction_out']:
  vf=features(at,delay,v['removed_transaction'])[0];own=vf.get((T,E));score=int(own['concentration'])+int(own['shift']) if own else None
  assert v['evaluated']==bool(own);assert score==v['score'];variants[score]+=1
 counts['V4_missing']+=len(s['leave_one_transaction_out'])+1
 own_groups=[g for g in gs if g['wallet']==T];buys=[g for g in own_groups if g['side']=='BUY'];trigger=max(buys,key=lambda g:g['timestamp']);baseline=[g['nominal'] for g in buys if g['timestamp']<trigger['first_timestamp']]
 med=median(baseline);mad=median(abs(x-med) for x in baseline);threshold=max(1000,5*med,med+6*1.4826*mad);recent=[g for g in buys if g['timestamp']>=at-86400];nom=sum(g['nominal'] for g in recent)
 close(nom/.8-nom,s['hidden_other_event_buy_strictly_greater_than'])
 sig={x['rule']:x for x in s['ticks'][-1]['target']['signals']};assert len(sig)==2;close(sig['wallet_size_shift']['reference']['median'],med);close(sig['wallet_size_shift']['reference']['mad'],mad);close(sig['wallet_size_shift']['reference']['threshold'],threshold);close(sig['event_concentration']['reference']['wallet_buy_nominal'],nom)
 assert s['ticks'][-1]['target']['score']==2 and not s['ticks'][-1]['target']['priority']
 assert all(r['observed_at']>at for r in avail)
 print('SCENARIO',delay,'at',utc(at),'pair',len(f),'baseline',rate([v for v in f.values() if v['baseline_capable']]),'cohorts',s['cohorts'],'transition',s['placebo_transition'],'removals',dict(variants),'target_groups',len(own_groups),Counter(g['side'] for g in own_groups),'median',med,'MAD',mad,'threshold',threshold,'nominal24h',nom,'dilution',nom/.8-nom)
assert dict(counts)==d['comparisons'];print('COMPARISONS',dict(counts),sum(counts.values()))
source=d['scenarios'][0]['target_source_rows'];mapping={r['transaction_hash']:r for r in source};seen=set()
for line in (P/'TRANSACTIONS.md').read_text().splitlines():
 if not line.startswith('| 2026-'):continue
 c=[x.strip() for x in line.strip('|').split('|')];h=re.search(r'/tx/(0x[0-9a-f]+)',c[-1]).group(1);r=mapping[h];seen.add(h)
 assert c[0]==utc(r['timestamp']);assert c[1].split(' / ')[0]==r['market_id'];assert c[2]==r['side'];assert c[3]==f"{r['size']:.8f}";assert c[4]==f"{r['price']:.10f}";assert c[5]==f"{r['price']*r['size']:.6f}"
assert seen==set(mapping);print('TRANSACTIONS all',len(seen),'exact display values; observed',utc(min(r['observed_at'] for r in source)),utc(max(r['observed_at'] for r in source)))
q=d['scenarios'][0]['queues']['wallets']['queue'];idx=0
for line in (P/'TEMOINS_ET_FILE.md').read_text().splitlines():
 if re.match(r'^\| \d+ \|',line):
  c=[x.strip() for x in line.strip('|').split('|')];r=q[idx];idx+=1
  assert int(c[0])==idx;assert c[1]==utc(r['first_conditional_priority_at']);assert c[2].strip('`')==r['wallet'];assert int(c[3])==r['best_score']
assert idx==len(q);print('WALLET_TABLE',idx,'exact')
for name in ('results.md','TRANSACTIONS.md','TEMOINS_ET_FILE.md'):
 for i,line in enumerate((P/name).read_text().splitlines(),1):
  if '\u2014' in line:print('EM_DASH',name,i,line)
regs=[json.loads(l) for l in (P/'registre/tests.jsonl').read_text().splitlines()];print('REGISTRY',Counter(x['donnees'] for x in regs),'real total',sum(x['n_comparaisons'] for x in regs if x['donnees']=='reelles'))
assert all(x['p'] is None for x in regs)
for x in regs:
 if x['donnees']=='reelles':assert x['sortie_sha']==hashlib.sha256((P/x['sortie']).read_bytes()).hexdigest() and x['code_gele'] and x['n_effectif']==1 and x['lock_sha']==hashlib.sha256((P/'PROTOCOL.lock').read_bytes()).hexdigest()
print('ALL RECOMPUTATION ASSERTIONS PASSED')
