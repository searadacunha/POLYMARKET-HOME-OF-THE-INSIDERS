from pathlib import Path
import json,gzip,datetime,collections,re,hashlib
p=Path('/Users/benjamindacunha/Projects/PolySentinel/studies/detection_20261030')
report=(p/'results.md').read_text()
R=json.loads(gzip.decompress((p/'derived/replay.json.gz').read_bytes()))
F=json.loads(gzip.decompress((p/'derived/features.json.gz').read_bytes()))
L=json.loads((p/'derived/label_comparison.json').read_bytes())
D=json.loads((p/'data/labels_after.json').read_bytes())
rows=[json.loads(x) for x in gzip.decompress((p/'data/replay_input.jsonl.gz').read_bytes()).decode().splitlines()]
tables=[];current=[]
for line in report.splitlines()+['']:
 if line.startswith('|'): current.append([x.strip() for x in line.strip('|').split('|')])
 elif current:tables.append(current);current=[]
def date(t):return datetime.datetime.fromtimestamp(t,datetime.timezone.utc).strftime('%d/%m %H:%M:%S') if t is not None else 'inconnu / aucun'
def rank(x):return f"{x['rank']} / {x['denominator']}" if x else 'aucun'
for table in tables:
 header=table[0];body=table[2:]
 if header[0]=='Délai hypothétique':
  expected=[[str(s[k]) for k in ['delay_seconds','n_wallets_present','n_wallets_available_by_final','n_wallets_evaluated','n_wallets_behavior_signal','n_wallets_conditional_priority']] for s in R['scenarios']]
 elif header[0]=='Alias actuel':
  expected=[]
  for l in L['rows']:
   s=l['scenarios'][0]
   if not s['resolved']:
    expected.append([l['public_label'],'identité non résolue']+['inconnu']*5+['aucun rapprochement supposé'])
   else:
    for pair in s['wallet_event_records']:
     expected.append([l['public_label'],pair['event_id'],str(pair['best_score']),date(pair['first_signal_at']),rank(pair['rank_at_first_signal']),date(pair['first_conditional_priority_at']),rank(pair['rank_at_first_conditional_priority']),', '.join(pair['best_score_reasons']) or 'aucune famille pondérée'])
 elif header[0]=='Wallet':
  expected=[]
  for pair in R['scenarios'][0]['wallet_events']:
   if pair['first_conditional_priority_at'] is not None:
    expected.append([pair['wallet'],pair['event_id'],str(pair['best_score']),date(pair['first_conditional_priority_at']),rank(pair['rank_at_first_conditional_priority']),', '.join(pair['best_score_reasons'])])
 else:continue
 mismatches=[(i+1,a,b) for i,(a,b) in enumerate(zip(body,expected)) if a!=b]
 print('TABLE',header[0],'rows',len(body),'expected',len(expected),'mismatches',mismatches)
 assert len(body)==len(expected) and not mismatches
print('INPUT',len(rows),'wallets',len({r['wallet'] for r in rows}),'events',len({r['event_id'] for r in rows}))
oldlow=datetime.datetime(2026,9,26,20,tzinfo=datetime.timezone.utc).timestamp()
print('INPUT_OLD_RANGE',sum(r['timestamp']>=oldlow for r in rows),'INPUT_EARLIER',sum(r['timestamp']<oldlow for r in rows))
print('STRICT',R['strict_actual_observation_replay'])
print('THIN_PRIORITY_DATES',[date(next(x for x in s['wallet_events'] if x['wallet']==L['rows'][0]['wallet'] and x['event_id']=='1105364')['first_conditional_priority_at']) for s in R['scenarios']])
for k in ['event_concentration_trigger','synchronized_buy_trigger','joint_concentration_and_synchrony']:
 print('FEATURE',k,sum(r[k] for r in F['rows']),len(F['rows']))
print('FEATURE_CONC_KNOWN',sum(r['event_concentration_observed'] is not None for r in F['rows']))
print('FEATURE_PEERS',sum(r['reference']['wallets']>0 for r in F['rows']),sum(r['reference']['wallets']==0 for r in F['rows']))
for g in ['initial_highlighted_holders','later_named_cases']:
 subset=[r for r in D['rows'] if r['source_group']==g]
 print('LABEL_GROUP',g,len(subset),'resolved',sum(r['wallet'] is not None for r in subset))
resolved={r['wallet'] for r in D['rows'] if r['wallet']}
prioritized={w['wallet'] for w in R['scenarios'][0]['wallets'] if w['first_conditional_priority_at'] is not None}
print('PRIORITY_RESOLVED',len(prioritized & resolved),'OTHER',len(prioritized-resolved))
print('FREEZE',len(json.loads((p/'PROTOCOL.lock').read_bytes())['fichiers']))
print('LINKS_MISSING',[link for link in re.findall(r'\]\(([^)]+)\)',report) if not link.startswith('http') and not (p/link).exists()])
print('EM_DASH',report.count(chr(8212)))
print('REPORT_SHA',hashlib.sha256(report.encode()).hexdigest())
