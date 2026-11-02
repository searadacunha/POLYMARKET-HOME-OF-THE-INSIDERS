"""Synthetic end-to-end sensitivity and adversarial documentary controls."""
import copy, hashlib, json, random
from pathlib import Path
from vendor.signals import evaluate, group_fills
from ana_evaluate import evaluate_dataset
from col_extract import terminal_evidence, select_case_version
from registre import enregistrer

STUDY=Path(__file__).resolve().parents[1]
CONFIG=json.loads((STUDY/'data/config.json').read_text())

def wrap(p,at):
    return dict(payload=p,observed_at=at,content_id=hashlib.sha256(json.dumps(p,sort_keys=True).encode()).hexdigest(),key=str(p.get('id','synthetic')))

def fixture(seed,level):
    rng=random.Random(seed);now=100000
    e=dict(id='synthetic_event',title='Synthetic announcement',slug='synthetic-event',active=True,closed=False,
           observed_at=89000,end_date='1970-01-02T04:00:00+00:00',tags=['science'])
    m=dict(id='synthetic_market',event_id=e['id'],condition_id='synthetic_condition',active=True,closed=False,
           observed_at=89000,end_date=e['end_date'],tokens=[dict(token_id='yes',outcome='Yes'),dict(token_id='no',outcome='No')])
    order=list(range(6));rng.shuffle(order);trades=[]
    for j,w in enumerate(order):
        sync=level=='strong' or (level=='medium' and j<3)
        ts=91000+j*5 if sync else 91000+j*1000
        nominal=(1200+rng.randrange(20)) if level!='null' else 100
        trades.append(dict(id='trade'+str(w),wallet='wallet'+str(w),token_id='yes',event_id=e['id'],market_id=m['id'],
            condition_id=m['condition_id'],outcome='Yes',side='BUY',size=nominal/.5,price=.5,timestamp=ts,
            observed_at=ts+1,transaction_hash='tx'+str(w),fee=None))
    cs=evaluate(trades,[m],[e],now=now,config=CONFIG,wallet_history={})
    byid={t['id']:t for t in trades};records=[]
    for c in cs:
        r=wrap(c,now+1);r['event_at_calculation']=wrap(e,89000);r['alert_proofs']=[]
        for a in c['alerts']:
            r['alert_proofs'].append(dict(alert=a,trades=[wrap(byid[tid],byid[tid]['observed_at']) for tid in a['trade_ids']],market=wrap(m,89000)))
        records.append(r)
    pm=dict(first_public_information_verified=True,public_at=100100,timing_uncertainty_seconds=0,
        timestamp_basis='Synthetic exact clock',source_url='https://example.invalid/announcement',evidence_id='synthetic-public',
        contemporaneous_archive=dict(verified=True,evidence_id='synthetic-contemporaneous',observed_at=100100))
    ev=dict(event=wrap(e,89000),scheduled_end=100800,first_event_observed_at=89000,first_terminal_observed_at=100900,
        proxy_cycle_end=100050,source_url='https://example.invalid/event',public_milestone=wrap(pm,100110),
        cohort_complete=True,cohort_completeness_reason='Synthetic complete six-wallet universe',
        authoritative_target=dict(target_verified=True,winning_token_ids=['yes'],observed_at=100800,
          evidence_id='synthetic-target',source_url='https://example.invalid/target'),cases=records,activities=[],resolution_records=[])
    return dict(cutoff=101000,bot_first_cycle_start=88000,selected_events=[ev],catalogue_events=1,exclusions={}),trades

def main():
    if (STUDY/'PROTOCOL.lock').exists():raise RuntimeError('Controls are pre-freeze only; do not rewrite frozen evidence')
    rows=[]
    for seed in (11,29,47):
        for level,expected in (('null',0),('medium',3),('strong',6)):
            d,trades=fixture(seed,level);r=evaluate_dataset(d);e=r['events'][0]
            assert e['priority_cases']==expected,(seed,level,e['priority_cases'])
            assert e['verdict']==('NO_PRIORITY_SIGNAL' if level=='null' else 'DESCRIPTIVE_ONLY'),e
            assert all(not c['feature_reasons'] for c in e['cases'])
            row=dict(seed=seed,level=level,input_wallets=6,emitted_cases=e['archived_cases'],priority_cases=e['priority_cases'],
                priority_fraction=e['priority_cases']/6,verdict=e['verdict'],direction_precision=e['direction_precision'],economic_return=e['economic_return'])
            rows.append(row)
            rel='controles/synthetic_'+level+'_'+str(seed)+'.json'
            (STUDY/rel).write_text(json.dumps(row,sort_keys=True,indent=2)+'\n')
            enregistrer(str(STUDY),test='synthetic_'+level+'_'+str(seed),declare=True,n=6,n_effectif=1,
                agent='case_review',donnees='synthetiques',sortie=rel,params=dict(seed=seed,level=level),
                note='Synthetic sensitivity only, not real statistical power')
    base,trades=fixture(11,'strong');adversarial=[]
    def check(name,mutate,expected):
        d=copy.deepcopy(base);mutate(d);e=evaluate_dataset(d)['events'][0]
        assert e['verdict']==expected,(name,e['verdict'])
        adversarial.append(dict(name=name,expected=expected,observed=e['verdict'],pass_=True))
    check('official_resolution_is_not_first_public_information',lambda d:d['selected_events'][0].update(public_milestone=wrap(
        dict(verified=True,result_available=True,public_at=100100,proof_level='official resolution only'),100110)), 'NON_ESTIMABLE_PUBLIC_TIMING')
    check('publication_record_arriving_after_cutoff',lambda d:d['selected_events'][0]['public_milestone'].update(observed_at=101001),'NON_ESTIMABLE_PUBLIC_TIMING')
    check('missing_outcome_target',lambda d:d['selected_events'][0].update(authoritative_target=None),'NON_ESTIMABLE_TARGET')
    check('incomplete_cohort',lambda d:d['selected_events'][0].update(cohort_complete=False),'NON_ESTIMABLE_COHORT')
    check('late_feature_observation',lambda d:d['selected_events'][0]['cases'][0]['alert_proofs'][0]['trades'][0].update(observed_at=100001),'NON_ESTIMABLE_COHORT')
    check('target_observed_before_decision',lambda d:d['selected_events'][0]['authoritative_target'].update(observed_at=99999),'NON_ESTIMABLE_TARGET')
    a=group_fills(trades,now=100000);b=group_fills(trades+[copy.deepcopy(trades[0])],now=100000)
    assert a==b
    late=copy.deepcopy(trades[0]);late.update(id='future',transaction_hash='future',observed_at=100001)
    assert group_fills(trades+[late],now=100000)==a
    adversarial.extend([dict(name='duplicate_fill_not_double_counted',pass_=True),dict(name='future_observation_ignored',pass_=True)])
    pm=dict(verified=True,result_available=True,public_at=20,public_observed_at=20,
        source_url='https://data-api.polymarket.com/v2/resolutions',proof_level='affirmation officielle : toutes les conditions connues résolues')
    first=wrap(pm,20);late=wrap(pm,80);unverified=wrap(dict(pm,verified=False),5)
    refs=terminal_evidence([wrap(dict(closed=False),10),wrap(dict(closed=True),90)],[unverified,first,late])
    assert refs[0]['observed_at']==20 and refs[0]['content_id']==first['content_id'] and refs[0]['kind']=='public_milestone'
    assert all(r['observed_at']!=5 for r in refs)
    adversarial.append(dict(name='first_terminal_before_late_reemission_and_unverified_ignored',pass_=True))
    ledger=[]
    for name,vs,proxy,expected in (
        ('no_proxy',[wrap(dict(calculated_at=9),10)],None,'no_proxy'),
        ('not_observable',[wrap(dict(calculated_at=9),20)],15,'no_version_observable_at_proxy'),
        ('late_calculation',[wrap(dict(calculated_at=19),10)],15,'calculated_at_after_proxy_or_missing'),
        ('missing_calculation',[wrap({},10)],15,'calculated_at_after_proxy_or_missing'),
        ('retained',[wrap(dict(calculated_at=9),10)],15,None)):
        selected,item=select_case_version(name,vs,proxy)
        assert item['exclusion_reason']==expected and bool(selected)==(expected is None)
        ledger.append(item)
    assert len(ledger)==sum(x['exclusion_reason'] is None for x in ledger)+sum(x['exclusion_reason'] is not None for x in ledger)
    adversarial.append(dict(name='all_case_keys_reconciled_with_explicit_exclusion_reasons',pass_=True,ledger=ledger))
    medium,_=fixture(29,'medium');before=evaluate_dataset(medium)['events'][0]
    assert sum(len(m['controls']) for m in before['controls'])>0
    for c in medium['selected_events'][0]['cases']:
        if not c['payload']['priority']:c['payload']['quality'].pop('trade_groups')
    after=evaluate_dataset(medium)['events'][0]
    assert sum(len(m['controls']) for m in after['controls'])==0
    assert all(c['trade_groups'] is None for c in after['cases'] if not c['priority'])
    adversarial.append(dict(name='missing_control_coverage_not_imputed_zero',pass_=True))
    rel='controles/adversarial.json';(STUDY/rel).write_text(json.dumps(adversarial,indent=2)+'\n')
    enregistrer(str(STUDY),test='synthetic_adversarial_gates',declare=True,n=len(adversarial),n_effectif=1,n_comparaisons=len(adversarial),
        agent='case_review',donnees='synthetiques',sortie=rel,params=dict(tests=[r['name'] for r in adversarial]))
    lines=['# Contrôles synthétiques avant gel','',
      'Le module v1.2 copié et les portes documentaires ont été exécutés ensemble. Aucune donnée réelle utilisée.',
      'Sensibilité mécanique des scénarios, pas puissance statistique ni calibration sur marchés réels.','',
      '| Graine | Scénario | Wallets injectés | Dossiers émis | Prioritaires | Verdict |',
      '|---|---|---:|---:|---:|---|']
    lines.extend(f"| {r['seed']} | {r['level']} | 6 | {r['emitted_cases']} | {r['priority_cases']} | {r['verdict']} |" for r in rows)
    lines+=['','Nul : 0/6 à chacune des trois graines ; moyen : 3/6 ; fort : 6/6.',
      'Les labels synthétiques sont construits : leurs taux directionnels ne sont pas des preuves économiques.',
      f"{len(adversarial)} contrôles adverses PASS, inventaire dans `adversarial.json`. Toutes les rentabilités restent null.",
      'Le verdict ne qualifie jamais un wallet d’initié. Dix lignes synthétiques sont ajoutées par exécution ; les précédentes restent au registre.','']
    (STUDY/'controles/CONTROLES.md').write_text('\n'.join(lines))
    print(f'PASS: 9 scenarios / 3 seeds; {len(adversarial)} adversarial controls; null silent; full documentary verdict exercised')

if __name__=='__main__':main()
