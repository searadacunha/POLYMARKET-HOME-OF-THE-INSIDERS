"""Run only after pre-label output seal; never mutate ranks or thresholds."""
import gzip
import hashlib
import json
from pathlib import Path
from budget import capacity, write_bytes

STUDY=Path(__file__).resolve().parents[1]

def compare(replay,labels):
    output=[]
    for label in labels['rows']:
        resolved=bool(label.get('wallet')) and label.get('mapping_status')=='exact_current_profile_alias'
        wallet=label['wallet'].lower() if resolved else None
        item=dict(public_label=label['public_label'],source_group=label['source_group'],wallet=wallet,
                  mapping_status=label['mapping_status'],historical_alias_continuity_proven=False,scenarios=[])
        for scenario in replay['scenarios']:
            row=next((r for r in scenario['wallets'] if r['wallet']==wallet),None)
            pairs=[r for r in scenario['wallet_events'] if r['wallet']==wallet]
            item['scenarios'].append(dict(delay_seconds=scenario['delay_seconds'],
                resolved=resolved,present=row is not None if resolved else None,
                recent_buy_evaluated=row['recent_buy_evaluated_ever'] if row else None,
                behavior_detected=row['first_signal_at'] is not None if row else None,
                conditional_priority=row['first_conditional_priority_at'] is not None if row else None,
                actual_historical_alert=None,wallet_record=row,wallet_event_records=pairs,
                unknowns=['historical alias continuity','historical eligibility','publication delay','missing trades and metadata'],
                false_negative_established=False))
        output.append(item)
    return dict(rows=output,n_public_labels=len(output),n_resolved_labels=sum(r['wallet'] is not None for r in output),
        n_effective_cases=1,n_comparisons=len(output)*len(replay['scenarios']),
        precision=None,recall=None,false_positive_rate=None,
        historical_global_verdict='NON_ESTIMABLE',
        meaning='Conditional behavior/priority, never actual historical emission or proved insider status')

def main():
    capacity()
    from registre import enregistrer
    seal=json.loads((STUDY/'derived/pre_label_seal.json').read_text())
    if set(seal.get('files',{}))!={'derived/replay.json.gz','derived/features.json.gz'}:
        raise ValueError('Seal must cover both complete pre-label outputs')
    for name,sha in seal['files'].items():
        if hashlib.sha256((STUDY/name).read_bytes()).hexdigest()!=sha:raise ValueError('Pre-label outputs changed')
    labels=json.loads((STUDY/'data/labels_after.json').read_text())
    replay=json.loads(gzip.decompress((STUDY/'derived/replay.json.gz').read_bytes()))
    result=compare(replay,labels)
    write_bytes(STUDY/'derived/label_comparison.json',(json.dumps(result,indent=2)+'\n').encode())
    enregistrer(str(STUDY),test='R3_post_seal_public_labels',declare=True,n=len(labels['rows']),n_effectif=1,
                n_comparaisons=result['n_comparisons'],agent='Codex',sortie='derived/label_comparison.json',
                note='Exact current alias mappings only, no re-ranking, real historical emission unknown')
    print('Post-seal comparison written')

if __name__=='__main__':main()
