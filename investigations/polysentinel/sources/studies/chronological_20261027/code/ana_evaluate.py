"""Frozen documentary gates; historical emissions are not a full score replay."""
import collections, gzip, hashlib, json, math
from pathlib import Path
from vendor.signals import group_fills
from registre import enregistrer

STUDY=Path(__file__).resolve().parents[1]

def finite_number(x):
    return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x)

def count_or_missing(x):
    return x if isinstance(x,int) and not isinstance(x,bool) and x>=0 else None

def public_information(record,cutoff):
    if not record:return False
    p=record['payload'];archive=p.get('contemporaneous_archive',{})
    return (record['observed_at']<=cutoff and p.get('first_public_information_verified') is True
        and finite_number(p.get('public_at')) and p['public_at']<=cutoff
        and p.get('timing_uncertainty_seconds')==0 and bool(p.get('timestamp_basis'))
        and str(p.get('source_url','')).startswith('https://') and bool(p.get('evidence_id'))
        and archive.get('verified') is True and bool(archive.get('evidence_id'))
        and archive.get('observed_at')==p['public_at'])

def focal(case):
    buys=[a for a in case.get('alerts',[]) if a.get('side')=='BUY']
    return sorted(buys,key=lambda a:(-a['nominal'],a['timestamp'],a.get('transaction_hash') or ''))[0] if buys else None

def feature_reasons(record,cutoff,start,proxy):
    c=record['payload'];t=c.get('calculated_at');reasons=[]
    if not finite_number(t):return ['missing_calculation_time']
    if not(start<=t<=cutoff) or proxy is None or t>proxy:reasons.append('calculation_outside_known_window')
    if record['observed_at']>cutoff or proxy is None or record['observed_at']>proxy:reasons.append('emission_not_known_at_proxy')
    if c.get('rule_version')!='exploratory-1.2':reasons.append('historical_rule_version_not_1_2')
    if c.get('current',True) is not True or c.get('preliminary') is not True:reasons.append('not_current_preliminary_case')
    event=record.get('event_at_calculation')
    if not event or event['observed_at']>t:reasons.append('event_metadata_missing_at_calculation')
    if len(record.get('alert_proofs',[]))!=len(c.get('alerts',[])):reasons.append('missing_alert_proof')
    for proof in record.get('alert_proofs',[]):
        a=proof['alert'];market=proof.get('market')
        if max(a['timestamp'],a['observed_at'])>t:reasons.append('alert_after_calculation')
        if not market or market['observed_at']>t:reasons.append('market_metadata_missing_at_calculation')
        ts=proof['trades']
        if len(ts)!=len(a.get('trade_ids',[])) or not ts or any(p is None for p in ts):
            reasons.append('underlying_trade_not_archived_at_calculation');continue
        if any(max(p['observed_at'],p['payload']['timestamp'],p['payload'].get('observed_at',p['observed_at']))>t for p in ts):
            reasons.append('underlying_trade_after_calculation');continue
        gs=group_fills([p['payload'] for p in ts],now=t)
        if len(gs)!=1 or set(gs[0]['trade_ids'])!=set(a['trade_ids']):reasons.append('fill_group_mismatch');continue
        if any(not math.isclose(gs[0][k],a[k],rel_tol=1e-8,abs_tol=1e-6) for k in ('nominal','size','price')):
            reasons.append('fill_economics_mismatch')
    return sorted(set(reasons))

def match_controls(records):
    targets=[r for r in records if r['priority'] and not r['feature_reasons'] and r['focal']]
    controls=[r for r in records if not r['priority'] and not r['feature_reasons'] and r['focal']]
    matches=[]
    for t in targets:
        a=t['focal'];pool=[]
        if t['trade_groups'] is None:
            matches.append(dict(target_id=t['id'],controls=[],candidate_matches=0,matching_exclusion='missing_target_coverage'))
            continue
        for c in controls:
            b=c['focal']
            if c['trade_groups'] is None:continue
            if (t['wallet']==c['wallet'] or a['token_id']!=b['token_id'] or not a.get('condition_id')
                    or a.get('condition_id')!=b.get('condition_id')):continue
            dt=abs(a['timestamp']-b['timestamp']);dp=abs(a['price']-b['price'])
            if a['nominal']<=0:continue
            nr=b['nominal']/a['nominal'];hr=(c['trade_groups']+1)/(t['trade_groups']+1)
            if dt>3600 or dp>.1 or not 1/3<=nr<=3 or not 1/3<=hr<=3:continue
            distance=dt/3600+dp/.1+abs(math.log(nr))+abs(math.log(hr))
            pool.append(dict(control_id=c['id'],wallet=c['wallet'],distance=distance,seconds_gap=dt,price_gap=dp,
                             nominal_ratio=nr,coverage_group_ratio=hr,score=c['score']))
        pool.sort(key=lambda p:(p['distance'],p['wallet'],p['control_id']))
        selected=[];seen=set()
        for p in pool:
            if p['wallet'] not in seen:selected.append(p);seen.add(p['wallet'])
            if len(selected)==3:break
        matches.append(dict(target_id=t['id'],controls=selected,candidate_matches=len(pool)))
    return matches

def evaluate_event(event,cutoff,start):
    pm=event.get('public_milestone');public_ok=public_information(pm,cutoff)
    public_at=pm['payload']['public_at'] if public_ok else None
    cases=[]
    for r in event['cases']:
        c=r['payload'];a=focal(c);reasons=feature_reasons(r,cutoff,start,event['proxy_cycle_end'])
        if public_ok and c['calculated_at']>=public_at:reasons.append('calculation_not_before_verified_public_information')
        # condition_id is absent from some archived alert summaries; recover only from PIT market proof.
        if a is not None:
            a=dict(a)
            proof=next((p for p in r['alert_proofs'] if p['alert']==focal(c)),None)
            if proof and proof.get('market'):a['condition_id']=proof['market']['payload'].get('condition_id')
        cases.append(dict(id=c['id'],wallet=c['wallet'],score=c['score'],priority=c['priority'],rule_version=c['rule_version'],
            calculated_at=c['calculated_at'],emission_observed_at=r['observed_at'],feature_reasons=reasons,focal=a,
            trade_groups=count_or_missing(c.get('quality',{}).get('trade_groups')),raw_fills=count_or_missing(c.get('quality',{}).get('raw_fills')),
            history_left_censored=c.get('quality',{}).get('history_left_censored',True),
            contradictions=c.get('contradictions',[]),signals=c.get('signals',[]),
            all_alerts=c.get('alerts',[]),content_id=r['content_id']))
    # Controls are fixed entirely from features before the result target is examined.
    matches=match_controls(cases)
    valid_cases=[c for c in cases if not c['feature_reasons']]
    cohort_ok=event.get('cohort_complete') is True and len(valid_cases)==len(cases) and public_ok
    target=event.get('authoritative_target') or {}
    latest_decision=max((c['calculated_at'] for c in valid_cases),default=start)
    target_ok=(target.get('target_verified') is True and bool(target.get('winning_token_ids'))
        and finite_number(target.get('observed_at')) and latest_decision<target['observed_at']<=cutoff
        and bool(target.get('evidence_id'))
        and str(target.get('source_url','')).startswith('https://'))
    priority=[c for c in valid_cases if c['priority'] and c['focal']]
    if not public_ok:verdict='NON_ESTIMABLE_PUBLIC_TIMING'
    elif not cohort_ok:verdict='NON_ESTIMABLE_COHORT'
    elif not target_ok:verdict='NON_ESTIMABLE_TARGET'
    elif not priority:verdict='NO_PRIORITY_SIGNAL'
    else:verdict='DESCRIPTIVE_ONLY'
    precision=None
    if verdict=='DESCRIPTIVE_ONLY':
        winners=set(map(str,target['winning_token_ids']))
        correct=sum(str(c['focal']['token_id']) in winners for c in priority)
        precision=dict(correct_direction_buy_cases=correct,priority_cases=len(priority),fraction=correct/len(priority),
                       meaning='Correct token direction among retained priority BUY cases; not insider detection accuracy')
    activities=[]
    first_activity={}
    for a in event.get('activities',[]):
        row=a['payload'].get('row',{})
        if row.get('type') not in ('CONVERSION','MERGE','SPLIT','REDEEM'):continue
        k=a['key']
        if k not in first_activity or a['observed_at']<first_activity[k]['first_observed_at']:
            first_activity[k]=dict(type=row.get('type'),timestamp=row.get('timestamp'),first_observed_at=a['observed_at'],
              size=row.get('size'),transaction_hash=row.get('transaction_hash'),wallet=a['payload'].get('wallet'),
              known_at_proxy=event['proxy_cycle_end'] is not None and a['observed_at']<=event['proxy_cycle_end'])
    activities=list(first_activity.values())
    return dict(event_id=event['event']['payload']['id'],title=event['event']['payload']['title'],url=event['source_url'],
        scheduled_end=event['scheduled_end'],first_event_observed_at=event['first_event_observed_at'],
        first_terminal_observed_at=event['first_terminal_observed_at'],proxy_cycle_end=event['proxy_cycle_end'],
        first_public_information_verified=public_ok,first_public_information_at=public_at,
        official_resolution_observations=len(event.get('resolution_records',[])),
        public_record_proof_level=pm['payload'].get('proof_level') if pm else None,
        public_record_note=pm['payload'].get('note') if pm else None,
        bot_coverage_started_after_scheduled_end=start>event['scheduled_end'],
        cohort_complete=event.get('cohort_complete') is True,cohort_reason=event.get('cohort_completeness_reason'),
        case_key_counts=event.get('case_key_counts'),case_key_inventory=event.get('case_key_inventory',[]),
        target_verified=target_ok,archived_cases=len(cases),point_in_time_proven_cases=len(valid_cases),
        priority_cases=sum(c['priority'] for c in cases),rule_versions=dict(collections.Counter(c['rule_version'] for c in cases)),
        cases=cases,controls=matches,activities=activities,
        direction_precision=precision,economic_return=None,verdict=verdict,
        limitations=['No earliest public time inferred from official resolution','No full-universe negative cohort',
            'Archived score, not full independent replay','Wallet and market dependence unresolved',
            'History and inventory censored; no common ownership established'])

def evaluate_dataset(data):
    events=[evaluate_event(e,data['cutoff'],data['bot_first_cycle_start']) for e in data['selected_events']]
    estimable=[e for e in events if e['verdict']=='DESCRIPTIVE_ONLY']
    return dict(schema_version=1,cutoff=data['cutoff'],bot_first_cycle_start=data['bot_first_cycle_start'],
        catalogue_events=data.get('catalogue_events'),population_exclusions=data.get('exclusions',{}),
        case_key_selection=data.get('case_key_selection'),
        selected_events=len(events),effective_event_upper_bound=len(events),
        archived_cases=sum(e['archived_cases'] for e in events),priority_cases=sum(e['priority_cases'] for e in events),
        first_public_information_verified_events=sum(e['first_public_information_verified'] for e in events),
        direction_evaluable_events=len(estimable),economic_evaluable_events=0,
        estimability_exclusions=dict(collections.Counter(e['verdict'] for e in events)),
        verdict='DESCRIPTIVE_ONLY' if estimable else 'NON_ESTIMABLE',events=events)

def main():
    if not (STUDY/'PROTOCOL.lock').exists():raise RuntimeError('Real calculation requires frozen protocol')
    inp=STUDY/'data/extraction_v2.json.gz';data=json.loads(gzip.decompress(inp.read_bytes()))
    data['case_key_selection']=json.loads((STUDY/'data/case_key_scope_v2.json').read_text())
    if data['case_key_selection']['extraction_sha256']!=hashlib.sha256(inp.read_bytes()).hexdigest():raise RuntimeError('Scope/extraction mismatch')
    output=evaluate_dataset(data)
    output['input_sha256']=hashlib.sha256(inp.read_bytes()).hexdigest()
    destination=STUDY/'derived/evaluation.json'
    destination.write_text(json.dumps(output,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    enregistrer(str(STUDY),test='chronological_documentary_gates',declare=True,n=output['archived_cases'],
        n_effectif=output['selected_events'],n_comparaisons=max(1,output['selected_events']),agent='case_review',
        params=dict(scope='descriptive',cutoff=data['cutoff'],thresholds_changed=False),
        sortie='derived/evaluation.json',note='No p-value, no insider or return claim; documentary estimability only')
    print(json.dumps({k:v for k,v in output.items() if k!='events'},ensure_ascii=False))

if __name__=='__main__':main()
