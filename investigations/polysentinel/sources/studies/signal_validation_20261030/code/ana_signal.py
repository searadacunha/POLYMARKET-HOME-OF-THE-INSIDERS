"""Exploratory, registered reconstruction; no inference about insider knowledge."""
from collections import Counter, defaultdict
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import signals
from budget import capacity, write_bytes
from registre import enregistrer, lire, _nom_temoin

STUDY = Path(__file__).resolve().parents[1]
TARGET = '0x8d3319c51520518ad01f6744486ceea29f376f5b'
EVENT = '1105364'
JOINT = {'event_concentration', 'wallet_size_shift'}

def read(path):
    with gzip.open(path, 'rt') as f:
        return json.load(f)

def verify_registry():
    lines, errors = lire(str(STUDY))
    witness = json.loads(Path(_nom_temoin(str(STUDY))).read_text())
    if errors or witness['n']!=len(lines):
        raise RuntimeError('Registry/witness verification failed: '+repr(errors))

def registered(**kwargs):
    result = enregistrer(str(STUDY), **kwargs)
    if not result.get('repro'):
        verify_registry()
    return result

def snapshot(rows, at, delay, config):
    if any(not math.isfinite(r['timestamp']) for r in rows):
        raise ValueError('Nonfinite source timestamp')
    available = [r for r in rows if r['timestamp'] + delay <= at]
    selected = sorted(available, key=lambda r: (-r['timestamp'], r['id']))[:config['analysis_trade_limit']]
    adapted = [dict(r, observed_at=r['timestamp'] + delay) for r in selected]
    history = {}
    for r in available:
        h = history.setdefault(r['wallet'], {'first_timestamp': r['timestamp'], 'observations': 0})
        h['first_timestamp'] = min(h['first_timestamp'], r['timestamp'])
        h['observations'] += 1
    diag = {}
    cases = signals.evaluate(adapted, [], [], now=at, config=config, wallet_history=history, diagnostics=diag)
    diag.update(available_rows=len(available),selected_rows=len(selected),clipped_rows=len(available)-len(selected))
    return cases, diag, selected, adapted, history

def pair_features(adapted, cases, at, config, history):
    groups = signals.group_fills(adapted, now=at)
    by_wallet, recent_pairs = defaultdict(list), defaultdict(list)
    for g in groups:
        by_wallet[g['wallet']].append(g)
        if g['side'] == 'BUY' and g['timestamp'] >= at-86400:
            recent_pairs[g['wallet'], g['event_id']].append(g)
    by_case = {(c['wallet'], c['event_id']): c for c in cases}
    output = []
    for (wallet, event), recent in sorted(recent_pairs.items()):
        hist = by_wallet[wallet]
        buys = [g for g in hist if g['side'] == 'BUY']
        counts = [sum(g['timestamp'] < x['first_timestamp'] for g in buys) for x in recent]
        nominal = sum(g['nominal'] for g in buys if g['timestamp'] >= at-86400)
        age_hours = (at-history[wallet]['first_timestamp'])/3600
        mean_price = sum(g['nominal'] for g in recent)/sum(g['size'] for g in recent)
        bins = [math.floor(math.log2(max(1,x))) for x in (age_hours, len(buys), nominal)]
        bins += [int(max(g['timestamp'] for g in recent)//86400), min(int(mean_price*5),4)]
        case = by_case.get((wallet,event), {})
        rules = sorted({s['rule'] for s in case.get('signals', [])})
        output.append(dict(wallet=wallet,event_id=event,age_observed_hours=age_hours,
            buy_groups=len(buys),wallet_buy_nominal_24h=nominal,mean_price=mean_price,bins=bins,
            maximum_prior_buy_groups=max(counts),baseline_capable=max(counts)>=config['minimum_baseline'],
            rules=rules,joint=JOINT.issubset(rules),score=case.get('score',0)))
    return output

def rate(rows):
    return dict(n=len(rows),joint=sum(r['joint'] for r in rows),baseline_capable=sum(r['baseline_capable'] for r in rows))

def queue(records):
    eligible = [r for r in records if r['evaluated_ever']]
    priority = sorted((r for r in eligible if r['first_conditional_priority_at'] is not None),
        key=lambda r: (r['first_conditional_priority_at'], r['wallet'], r.get('event_id','')))
    target = next(r for r in eligible if r['wallet']==TARGET and r.get('event_id',EVENT)==EVENT)
    at = target['first_conditional_priority_at']
    earlier = sum(r['first_conditional_priority_at'] < at for r in priority)
    equal = sum(r['first_conditional_priority_at'] == at for r in priority)
    ahead = sum(r['best_score'] > target['best_score'] for r in eligible)
    tied = sum(r['best_score'] == target['best_score'] for r in eligible)
    return dict(evaluated=len(eligible),priority=len(priority),strictly_earlier=earlier,
        peak_score_distribution=dict(sorted(Counter(r['best_score'] for r in eligible).items())),
        queue_tie_interval=[earlier+1,earlier+equal],queue_position=priority.index(target)+1,
        peak_score_rank_interval=[ahead+1,ahead+tied],target=target,
        queue=[{k:r.get(k) for k in ('wallet','event_id','first_conditional_priority_at','best_score')} for r in priority])

def target_case(cases):
    return next((c for c in cases if c['wallet']==TARGET and c['event_id']==EVENT), None)

def drop_target_transaction(rows, tx):
    return [r for r in rows if not (r['wallet']==TARGET and r['transaction_hash']==tx)]

def main():
    capacity()
    if not os.environ.get('ETUDE_REPRO_DIR'):
        verify_registry()
    manifest = json.loads((STUDY/'data/input_manifest.json').read_text())
    for p, record in manifest.items():
        if hashlib.sha256((STUDY/p).read_bytes()).hexdigest()!=record['sha256']:
            raise ValueError('Source hash mismatch: '+p)
    with gzip.open(STUDY/'data/replay_input.jsonl.gz','rt') as f:
        rows = [json.loads(line) for line in f]
    if len({r['id'] for r in rows}) != len(rows):
        raise ValueError('Duplicate source IDs')
    config = json.loads((STUDY/'data/config.json').read_text())
    previous = read(STUDY/'data/prior_replay.json.gz')
    output, comparisons = [], Counter()
    for scenario in previous['scenarios']:
        capacity()
        delay = scenario['delay_seconds']
        queues = {key:queue(scenario[key]) for key in ('wallets','wallet_events')}
        comparisons['V2_queue'] += sum(q['evaluated'] for q in queues.values())
        at = queues['wallet_events']['target']['first_conditional_priority_at']
        ticks = []
        all_features = []
        for tick in (at-86400, at-60, at):
            cases, diag, selected, adapted, history = snapshot(rows,tick,delay,config)
            if diag['clipped_rows']: raise ValueError('Audit requires no 50000-row clipping; do not silently change V4 population')
            features = pair_features(adapted,cases,tick,config,history)
            assert len(features)==diag['examined_recent_buy_pairs']
            all_features.append(features)
            comparisons['V1_ticks'] += max(1,len(features))
            ticks.append(dict(at=tick,diagnostics=diag,target=target_case(cases),summary=rate(features),
                              capable_summary=rate([r for r in features if r['baseline_capable']])))
        target = ticks[-1]['target']
        assert target is not None and target['score']==2 and JOINT.issubset(s['rule'] for s in target['signals'])
        prior = queues['wallet_events']['target']
        assert prior['best_score_at']==at and target['score']==prior['best_score']
        assert sorted({s['rule'] for s in target['signals']})==prior['best_score_reasons']
        assert not ticks[-2]['target'] or ticks[-2]['target']['score']<config['candidate_score']
        features = all_features[-1]
        own = next(r for r in features if r['wallet']==TARGET and r['event_id']==EVENT)
        same = [r for r in features if r['event_id']==EVENT]
        cohorts = {'C0':same,'C1':[r for r in same if r['baseline_capable']],
                   'C2':[r for r in same if r['baseline_capable'] and r['bins']==own['bins']]}
        cohort_results = {k:dict(including_target=rate(v),controls=rate([r for r in v if r['wallet']!=TARGET]),
                                  wallets=[r['wallet'] for r in v if r['wallet']!=TARGET]) for k,v in cohorts.items()}
        old = {(r['wallet'],r['event_id']):r for r in all_features[0]}
        new = {(r['wallet'],r['event_id']):r for r in features}
        common = old.keys() & new.keys()
        transition = Counter(str(int(old[k]['joint']))+'->'+str(int(new[k]['joint'])) for k in common)
        comparisons['V3_cohorts'] += 3*len(features)+len(common)+6
        own_rows = [r for r in selected if r['wallet']==TARGET]
        own_adapted = [r for r in adapted if r['wallet']==TARGET]
        isolated = target_case(signals.evaluate(own_adapted,[],[],now=at,config=config,wallet_history={TARGET:history[TARGET]}))
        if isolated is None or (isolated['score'],isolated['signals']) != (target['score'],target['signals']):
            raise ValueError('Cannot isolate wallet without altering signals')
        transactions = sorted({r['transaction_hash'] for r in own_adapted})
        if not all(transactions): raise ValueError('Missing transaction identity')
        variants=[]
        for tx in transactions:
            remaining=drop_target_transaction(selected,tx)
            vc,vd,_,va,vh=snapshot(remaining,at,delay,config)
            case=target_case(vc)
            vf=pair_features(va,vc,at,config,vh)
            feature=next((r for r in vf if r['wallet']==TARGET and r['event_id']==EVENT),{})
            variants.append(dict(removed_transaction=tx,removed_fills=len(selected)-len(remaining),
                evaluated=bool(feature),score=(case['score'] if case else 0) if feature else None,
                rules=sorted({s['rule'] for s in case['signals']}) if case else [],
                baseline_capable=feature.get('baseline_capable'),
                signals=case['signals'] if case else []))
        concentration = next(s for s in target['signals'] if s['rule']=='event_concentration')
        ref=concentration['reference']
        dilution=ref['event_buy_nominal']/.8-ref['wallet_buy_nominal']
        comparisons['V4_missing'] += len(variants)+1
        output.append(dict(delay=delay,at=at,ticks=ticks,queues=queues,features=features,cohorts=cohort_results,
            placebo_transition=dict(common=len(common),lost=len(old.keys()-new.keys()),new=len(new.keys()-old.keys()),counts=dict(transition)),
            target_source_rows=sorted(own_rows,key=lambda r:(r['timestamp'],r['id'])),
            target_groups=signals.group_fills(own_adapted,now=at),leave_one_transaction_out=variants,
            hidden_other_event_buy_strictly_greater_than=dilution))
    result=dict(status='EXPLORATORY_CONDITIONAL_AUDIT',independent_rarity='NON_ESTIMABLE',
        independent_external_n=1,scenarios=output,comparisons=dict(comparisons))
    dest=STUDY/'derived/validation.json.gz'
    write_bytes(dest,gzip.compress(json.dumps(result,sort_keys=True,separators=(',',':'),allow_nan=False).encode(),mtime=0))
    for test,n in comparisons.items():
        registered(test=test,declare=True,n=len(rows),n_effectif=1,n_comparaisons=n,
            agent='root-signal-audit',sortie='derived/validation.json.gz',
            note='Exploratoire après résultat; descriptif, aucun p ni performance prédictive')
    print(json.dumps(dict(output=str(dest),comparisons=dict(comparisons))))

if __name__=='__main__': main()
