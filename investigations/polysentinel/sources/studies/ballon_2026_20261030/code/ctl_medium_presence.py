"""Supplement the existing fixture assertion without changing detector rules."""
import json
from pathlib import Path
from vendor.signals import evaluate
from registre import enregistrer

STUDY = Path(__file__).resolve().parents[1]


if __name__ == '__main__':
    now = 1800000000
    config = json.loads((STUDY / 'data/detector_config.json').read_text())
    trade = dict(id='medium', wallet='0x'+'1'*40, token_id='t', event_id='e', market_id='m',
                 timestamp=now-60, observed_at=now-10, side='BUY', size=3000, price=.5,
                 transaction_hash='0x'+'2'*64)
    cases = evaluate([trade], [{'id':'m','event_id':'e','active':True,'observed_at':now-1000}],
                     [{'id':'e','active':True,'observed_at':now-1000}], now=now, config=config)
    assert len(cases) == 1 and cases[0]['score'] == 1 and cases[0]['priority'] is False
    output = {'status':'PASS','cases':len(cases),'score':cases[0]['score'],'priority':cases[0]['priority'],
              'note':'One synthetic missing assertion; no real-data sensitivity claim.'}
    (STUDY/'controles/medium_presence.json').write_text(json.dumps(output,indent=2))
    enregistrer(str(STUDY), test='synthetic_medium_presence_supplement', declare=True,
                donnees='synthetiques', n=1, n_effectif=1, n_comparaisons=1,
                agent='Codex', sortie='controles/medium_presence.json')
    print('PASS medium fixture is one candidate, score one, not priority')
