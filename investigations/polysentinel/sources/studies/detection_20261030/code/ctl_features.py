"""Small end-to-end controls for presence, missingness and internal references."""
import json
from pathlib import Path
from ana_features import features
from ana_labels import compare
from col_prepare import sanitize
from replay_core import CUTOFF

def controls():
    config=json.loads((Path(__file__).parent/'vendor/config.json').read_text())
    rows=[]
    for i in range(3):
        rows.append(dict(id=str(i),wallet='0x'+str(i+1)*40,token_id='token',market_id='m',event_id='e',
            condition_id='c',transaction_hash='tx'+str(i),side='BUY',price=.5,size=2400,
            timestamp=CUTOFF-100+i,observed_at=CUTOFF+1000))
    r=features(rows,config)
    assert r['n_units']==3 and r['n_comparisons']==27
    for x in r['rows']:
        assert x['event_concentration_trigger'] and x['synchronized_buy_trigger'] and x['joint_concentration_and_synchrony']
        assert x['reference']['wallets']==2 and x['reference']['synchronized_buy_count']==2
        assert x['account_creation_recent'] is None and x['shared_or_synchronized_funding'] is None
    null=features([dict(x,size=2) for x in rows],config)
    assert all(not x['joint_concentration_and_synchrony'] and not x['event_concentration_trigger'] for x in null['rows'])
    assert len(null['rows'])==3
    free=features([dict(x,price=0) for x in rows],config)
    assert len(free['rows'])==3 and all(x['event_concentration_observed'] is None for x in free['rows'])
    assert all(x['reference']['concentration_known_wallets']==0 for x in free['rows'])
    alone=features(rows[:1],config)['rows'][0]['reference']
    assert alone['wallets']==0 and alone['synchronized_buy_fraction'] is None and alone['joint_fraction'] is None
    try:sanitize(dict(rows[0],market_id=None))
    except ValueError:pass
    else:raise AssertionError('unknown market must not become a rotation category')
    fixture=dict(scenarios=[dict(delay_seconds=0,wallets=[],wallet_events=[])])
    labels=dict(rows=[dict(public_label='synthetic',source_group='fixture',wallet=None,mapping_status='unresolved')])
    compared=compare(fixture,labels)
    assert compared['rows'][0]['scenarios'][0]['present'] is None
    return dict(status='PASS',fixtures=7,n_effective_synthetic=1,
                cases=['strong_concentration_and_synchrony','null_keeps_zeros','zero_price_kept_unknown','unknowns_not_zero','missing_identity_refused','unresolved_label_not_negative','no_peers_unknown_frequencies'])

if __name__=='__main__':
    print(json.dumps(controls(),indent=2))
