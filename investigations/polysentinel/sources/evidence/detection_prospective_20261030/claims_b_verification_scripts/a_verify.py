from pathlib import Path
import json,gzip,hashlib,datetime,collections,math
p=Path('/Users/benjamindacunha/Projects/PolySentinel/studies/detection_20261030')
def obj(f):
 b=(p/f).read_bytes();return json.loads(gzip.decompress(b) if f.endswith('.gz') else b)
def utc(t):return datetime.datetime.fromtimestamp(t,datetime.timezone.utc).strftime('%d/%m %H:%M:%S') if t is not None else 'aucun dans ce scénario'
def rank(r):return f"{r['rank']} / {r['denominator']}" if r else 'aucun'
def check(label,a,b):
 assert a==b,(label,a,b)
R=obj('derived/replay.json.gz');F=obj('derived/features.json.gz');L=obj('derived/label_comparison.json');labels=obj('data/labels_after.json');lock=obj('PROTOCOL.lock');manifest=obj('data/input_manifest.json')
report=(p/'results.md').read_text();reg=[json.loads(l) for l in (p/'registre/tests.jsonl').read_text().splitlines()]
for f,h in lock['fichiers'].items():check(f,hashlib.sha256((p/f).read_bytes()).hexdigest(),h)
for row in reg:
 if row.get('sortie'):check(row['test'],hashlib.sha256((p/row['sortie']).read_bytes()).hexdigest(),row['sortie_sha'])
for f,h in obj('derived/pre_label_seal.json')['files'].items():check('seal '+f,hashlib.sha256((p/f).read_bytes()).hexdigest(),h)
print('HASHES_PASS',len(lock['fichiers']),'registry_outputs',len(reg))
real=[r for r in reg if r['donnees']=='reelles'];N=sum(x['n_comparaisons'] for x in real)
print('REGISTER',len(real),N,.05/N,[(r['test'],r['n_comparaisons']) for r in real])
check('multiplicity',N,36459769)
for s in R['scenarios']:
 wallets=s['wallets'];pairs=s['wallet_events'];summary=[s['delay_seconds'],len(wallets),sum(w['context_present_final'] for w in wallets),sum(w['recent_buy_evaluated_ever'] for w in wallets),sum(w['first_signal_at'] is not None for w in wallets),sum(w['first_conditional_priority_at'] is not None for w in wallets)]
 print('SCENARIO',summary,'oracle',s['full_kernel_oracle_checks'])
 expected='| '+' | '.join(str(x) for x in summary)+' |'
 check('denominator table',expected in report,True)
check('kernel_oracles',sum(s['full_kernel_oracle_checks'] for s in R['scenarios']),256)
check('R1_count',sum(s['conceptual_comparisons_two_metadata_scenarios']+s['final_diagnostic_comparisons_two_scenarios'] for s in R['scenarios'])+1,R['n_comparisons'])
print('STRICT',R['strict_actual_observation_replay'])
# Compare every literal cell in the public-pair table against R3, including unknown labels.
lines=report.splitlines(); table=False;got=[]
for n,line in enumerate(lines,1):
 if line.startswith('| Alias actuel |'):table=True;continue
 if table and line.startswith('|---'):continue
 if table and not line.startswith('|'):break
 if table:got.append((n,[x.strip() for x in line.strip('|').split('|')]))
expected=[]
for label in L['rows']:
 s=label['scenarios'][0]
 if not s['resolved']:
  expected.append([label['public_label'],'identité non résolue','inconnu','inconnu','inconnu','inconnu','inconnu','aucun rapprochement supposé']);continue
 for x in s['wallet_event_records']:
  expected.append([label['public_label'],x['event_id'],str(x['best_score']),utc(x['first_signal_at']),rank(x['rank_at_first_signal']),utc(x['first_conditional_priority_at']),rank(x['rank_at_first_conditional_priority']),', '.join(x['best_score_reasons']) or 'aucune famille pondérée'])
check('public_pair_rows',[v for n,v in got],expected)
print('PUBLIC_TABLE_PASS',len(got),'rows',len(got)*8,'cells')
# All conditional priorities, in R1 output ordering.
table=False;got=[]
for n,line in enumerate(lines,1):
 if line.startswith('| Wallet |'):table=True;continue
 if table and line.startswith('|---'):continue
 if table and not line.startswith('|'):break
 if table:got.append((n,[x.strip() for x in line.strip('|').split('|')]))
pri=[x for x in R['scenarios'][0]['wallet_events'] if x['first_conditional_priority_at'] is not None]
expected=[[x['wallet'],x['event_id'],str(x['best_score']),utc(x['first_conditional_priority_at']),rank(x['rank_at_first_conditional_priority']),', '.join(x['best_score_reasons'])] for x in pri]
check('priorities_table',[v for n,v in got],expected)
print('PRIORITY_TABLE_PASS',len(got),'rows',len(got)*6,'cells')
for d in [0,60,300,900]:
 scenario=[x for x in L['rows'][0]['scenarios'] if x['delay_seconds']==d][0]
 thin=[x for x in scenario['wallet_event_records'] if x['event_id']=='1105364'][0]
 print('SUMMARY_THIN',d,utc(thin['first_signal_at']),rank(thin['rank_at_first_signal']),utc(thin['first_conditional_priority_at']),rank(thin['rank_at_first_conditional_priority']),thin['best_score_reasons'])
for g in sorted({x['source_group'] for x in labels['rows']}):
 a=[x for x in labels['rows'] if x['source_group']==g];print('LABEL_GROUP',g,len(a),sum(bool(x['wallet']) for x in a))
for key in ['resolved','present','recent_buy_evaluated','behavior_detected','conditional_priority']:
 print('LABELS',key,sum(x['scenarios'][0][key] is True for x in L['rows']))
public={x['wallet'] for x in L['rows'] if x['wallet']}; priority={x['wallet'] for x in pri};print('PRIORITY_LABEL_OVERLAP',len(priority),len(priority&public),len(priority-public))
rows=F['rows'];print('FEATURES',len(rows),len({x['wallet'] for x in rows}),sum(x['event_concentration_trigger'] for x in rows),sum(x['synchronized_buy_trigger'] for x in rows),sum(x['joint_concentration_and_synchrony'] for x in rows),sum(x['reference']['wallets']>0 for x in rows),sum(x['reference']['wallets']==0 for x in rows),sum(x['event_concentration_observed'] is not None for x in rows))
for x in rows:
 peers=[y for y in rows if y['match_stratum']==x['match_stratum'] and y['wallet']!=x['wallet']]
 check('peer_count',len(peers),x['reference']['wallets'])
 for trigger,count,fraction in [('synchronized_buy_trigger','synchronized_buy_count','synchronized_buy_fraction'),('joint_concentration_and_synchrony','joint_count','joint_fraction')]:
  z=sum(y[trigger] for y in peers);check(count,z,x['reference'][count]);check(fraction,z/len(peers) if peers else None,x['reference'][fraction])
print('REFERENCE_COUNTS_AND_FRACTIONS_PASS',len(rows))
source=[json.loads(x) for x in gzip.decompress(Path(manifest['source']).read_bytes()).splitlines()];inputs=[json.loads(x) for x in gzip.decompress((p/'data/replay_input.jsonl.gz').read_bytes()).splitlines()]
lo=manifest['lower'];hi=manifest['upper_exclusive'];oldlo=datetime.datetime(2026,9,26,20,tzinfo=datetime.timezone.utc).timestamp()
counts={'read':len(source),'before_window':sum(r['timestamp']<lo for r in source),'after_cutoff':sum(r['timestamp']>=hi for r in source),'kept':sum(lo<=r['timestamp']<hi for r in source),'duplicates':len(inputs)-len({r['id'] for r in inputs})}
check('input_partition',counts,manifest['counts'])
check('input_columns',set().union(*(set(r) for r in inputs)),set(manifest['fields']))
print('INPUT_RECALC',counts,'wallets',len({r['wallet'] for r in inputs}),'events',len({r['event_id'] for r in inputs}),'old_window',sum(oldlo<=r['timestamp']<hi for r in source),'extra_before_old',sum(lo<=r['timestamp']<oldlo for r in source),'all_observed_after_cutoff',all(r['observed_at']>hi for r in inputs))
print('FORM_EM_DASH',report.count('\u2014'))
print('ALL_ASSERTIONS_PASS')
