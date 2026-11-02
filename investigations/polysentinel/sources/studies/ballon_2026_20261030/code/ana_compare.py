"""Post-output exact public-alias overlap; never call this detection or insider recall."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from registre import enregistrer

STUDY = Path(__file__).resolve().parents[1]


def compare(audit, labels):
    groups = defaultdict(list)
    for label in labels['rows']:
        groups[label['source_group']].append(label)
    output = {}
    for window, data in audit['windows'].items():
        ledger = {r['wallet']: r for r in data['reconstructed_descriptive_ledger']['wallet_ledger']}
        output[window] = {}
        for group, rows in groups.items():
            resolved = [r for r in rows if r.get('wallet') and r['mapping_status'] == 'exact_current_profile_alias']
            matches = []
            for label in resolved:
                wallet = label['wallet'].lower()
                matches.append({'public_label': label['public_label'], 'wallet': wallet,
                                'present_in_retrieved_trades': wallet in ledger,
                                'ledger': ledger.get(wallet),
                                'historical_alias_continuity_proven': label.get('historical_alias_continuity_proven', False)})
            output[window][group] = {'published_label_rows': len(rows), 'resolved_label_rows': len(resolved),
                                     'resolved_distinct_wallets': len({r['wallet'].lower() for r in resolved}),
                                     'present_distinct_wallets': len({r['wallet'] for r in matches if r['present_in_retrieved_trades']}),
                                     'matches': matches, 'detected_count': None, 'false_positives': None,
                                     'recall': None, 'precision': None,
                                     'meaning': 'Exact current profile mapping only; presence is not detection.'}
    return output


def main():
    audit_path = STUDY / 'derived/audit.json'
    sealed = json.loads((STUDY / 'derived/pre_label_output_sha256.json').read_text())
    if hashlib.sha256(audit_path.read_bytes()).hexdigest() != sealed['sha256']:
        raise RuntimeError('Detector output changed after sealing')
    labels = json.loads((STUDY / 'data/labels_after.json').read_text())
    audit = json.loads(audit_path.read_text())
    output = compare(audit, labels)
    destination = STUDY / 'derived/public_overlap.json'
    destination.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
    enregistrer(str(STUDY), test='T2_public_label_documentary_overlap', declare=True,
                n=len(labels['rows']), n_effectif=1, agent='Codex',
                n_comparaisons=sum(len(v) for v in output.values()), sortie='derived/public_overlap.json',
                params={'not_a_detection_metric': True})
    print('Public overlap saved; detection performance remains non-estimable')


if __name__ == '__main__':
    main()
