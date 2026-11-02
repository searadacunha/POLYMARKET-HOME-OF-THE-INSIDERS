"""Exercise the unchanged detector and audit gate on synthetic inputs only."""
import json
import random
from pathlib import Path

from ana_audit import analyze, ledger, strict_replay
from ana_compare import compare
from registre import enregistrer

STUDY = Path(__file__).resolve().parents[1]


def main():
    config = json.loads((STUDY / 'data/detector_config.json').read_text())
    outcomes = []
    for seed in (11, 29, 47):
        rng = random.Random(seed)
        now = 1800000000
        markets = [{'id': 'm', 'event_id': 'e', 'active': True, 'observed_at': now - 1000}]
        events = [{'id': 'e', 'active': True, 'observed_at': now - 1000}]
        for strength, number, size, expected in (('null', 3, 10, 0), ('medium', 1, 3000, 0), ('strong', 3, 3000, 3)):
            rows = [{'id': str(i), 'wallet': '0x' + str(i + 1) * 40, 'token_id': 't',
                     'market_id': 'm', 'event_id': 'e', 'condition_id': 'c', 'side': 'BUY',
                     'size': size, 'price': .5, 'timestamp': now - 70 + i * 5 + rng.randrange(3),
                     'observed_at': now - 10, 'transaction_hash': '0x' + str(i + 1) * 64}
                    for i in range(number)]
            inputs = {'trades': rows, 'markets': markets, 'events': events}
            replay = strict_replay(inputs, now, config)
            assert replay['priority_alerts'] == expected, (seed, strength, replay)
            future = {'trades': [dict(r, observed_at=now + 100) for r in rows], 'markets': markets, 'events': events}
            assert strict_replay(future, now, config)['cases'] == []
            counts = dict.fromkeys(('trade', 'market', 'event', 'public_milestone', 'public_condition', 'alert'), 0)
            local = {'first_cycle': {'id': 1, 'start': now + 100}, 'windows': {'a': {'cutoff': now, 'counts': counts}},
                     'historical_inputs': {'trades': [], 'markets': [], 'events': []}}
            result = analyze(local, config, rows)
            assert result['verdict'] == 'NOT_DEPLOYED_THEN_AND_COUNTERFACTUAL_NOT_ESTIMABLE'
            assert result['precision'] is None and result['recall'] is None and result['false_positives'] is None
            single = ledger(rows + rows, now)
            assert single['rows'] == len(rows)
            assert sum(float(w['gross_buy_claim']) for w in single['wallet_ledger']) == number * size * .5
            labels = {'rows': [dict(public_label='synthetic', source_group='fixture', wallet=rows[0]['wallet'],
                                    mapping_status='exact_current_profile_alias'),
                               dict(public_label='ambiguous', source_group='fixture', wallet=None,
                                    candidate_wallet=rows[0]['wallet'], mapping_status='unresolved')]}
            overlap = compare(result, labels)['a']['fixture']
            assert overlap['resolved_label_rows'] == 1 and overlap['present_distinct_wallets'] == 1
            assert overlap['detected_count'] is None and overlap['recall'] is None
            try:
                ledger(rows + [dict(rows[0], price=.25)], now)
            except ValueError:
                pass
            else:
                raise AssertionError('Economic conflict not rejected')
            outcomes.append({'seed': seed, 'strength': strength, 'wallets': number,
                             'priority_alerts': replay['priority_alerts'], 'expected': expected,
                             'future_excluded': True, 'duplicate_conflict_rejected': True,
                             'audit_verdict': result['verdict']})
    destination = STUDY / 'controles/synthetic.json'
    destination.write_text(json.dumps(outcomes, indent=2) + '\n')
    enregistrer(str(STUDY), test='synthetic_full_pipeline', declare=True, n=len(outcomes), n_effectif=3,
                n_comparaisons=9, agent='Codex', donnees='synthetiques', sortie='controles/synthetic.json')
    print('PASS nine synthetic fixtures; null/medium/strong and future/duplicate gates')


if __name__ == '__main__':
    main()
