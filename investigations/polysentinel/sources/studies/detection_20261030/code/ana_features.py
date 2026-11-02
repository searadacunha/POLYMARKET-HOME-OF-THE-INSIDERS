"""Pre-specified descriptive matrix; no labels, no inferential p-values."""
from collections import defaultdict
import gzip
import json
from pathlib import Path
from statistics import median

from replay_core import CUTOFF, prepare, kernel, event_key, read_rows
from budget import capacity, write_bytes

STUDY=Path(__file__).resolve().parents[1]

def features(trades, config, now=CUTOFF-1):
    rows,_=prepare(trades)
    available=[r for r in rows if r['timestamp']<=now]
    selected=sorted(available,key=lambda r:(-r['timestamp'],r['id']))[:config.get('analysis_trade_limit',50000)]
    adapted=[dict(r,observed_at=r['timestamp']) for r in selected]
    engine=kernel(); groups=engine.group_fills(adapted,now=now)
    history={}
    for r in available:
        h=history.setdefault(r['wallet'],dict(first_timestamp=r['timestamp'],observations=0))
        h['first_timestamp']=min(h['first_timestamp'],r['timestamp']);h['observations']+=1
    cases=engine.evaluate(adapted,[],[],now=now,config=config,wallet_history=history)
    signals={(c['wallet'],c['event_id']):{s['rule'] for s in c['signals']} for c in cases}
    wallet_buys=defaultdict(float); pairs=defaultdict(list)
    window=config.get('signal_window_seconds',86400)
    for g in groups:
        if g['side']=='BUY' and g['timestamp']>=now-window:
            wallet_buys[g['wallet']]+=g['nominal'];pairs[g['wallet'],event_key(g)].append(g)
    output=[]
    for (wallet,event), buys in sorted(pairs.items()):
        spend=sum(g['nominal'] for g in buys);shares=sum(g['size'] for g in buys)
        ratio=spend/wallet_buys[wallet] if wallet_buys[wallet] else None
        rules=signals.get((wallet,event),set())
        concentrated=spend>=config['large_nominal'] and ratio is not None and ratio>=.8
        if concentrated != ('event_concentration' in rules):raise ValueError('Kernel concentration mismatch')
        sync='synchronized_entries' in rules
        last=max(g['timestamp'] for g in buys)
        output.append(dict(wallet=wallet,event_id=event,at=now,delay_assumption_seconds=0,
            account_creation_recent=None,first_bet_after_creation_seconds=None,
            first_observed_age_seconds=now-history[wallet]['first_timestamp'],
            event_concentration_observed=ratio,event_concentration_trigger=concentrated,
            synchronized_buy_trigger=sync,amount_over_historical_liquidity=None,
            logically_coherent_positions=None,shared_or_synchronized_funding=None,
            precedes_this_publication=True,last_buy_seconds_before_cutoff=CUTOFF-last,
            no_prior_public_information=None,joint_concentration_and_synchrony=concentrated and sync,
            observed_event_buy_nominal=spend,observed_wallet_buy_nominal=wallet_buys[wallet],
            observed_tokens_bought=len({g['token_id'] for g in buys}),
            observed_markets_bought=len({g.get('market_id') for g in buys}),
            match_stratum=[event,int(last//86400),min(int(spend/shares*5),4)],
            native_rules=sorted(rules)))
    strata=defaultdict(list)
    for r in output:strata[tuple(r['match_stratum'])].append(r)
    for r in output:
        peers=[p for p in strata[tuple(r['match_stratum'])] if p['wallet']!=r['wallet']]
        values=[p['event_concentration_observed'] for p in peers if p['event_concentration_observed'] is not None]
        r['reference']=dict(wallets=len(peers),concentration_known_wallets=len(values),concentration_median=median(values) if values else None,
            concentration_min=min(values) if values else None,concentration_max=max(values) if values else None,
            synchronized_buy_count=sum(p['synchronized_buy_trigger'] for p in peers),
            joint_count=sum(p['joint_concentration_and_synchrony'] for p in peers),
            synchronized_buy_fraction=sum(p['synchronized_buy_trigger'] for p in peers)/len(peers) if peers else None,
            joint_fraction=sum(p['joint_concentration_and_synchrony'] for p in peers)/len(peers) if peers else None,
            scope='same event/UTC last-buy day/fixed width .2 share-weighted price band; unknown labels; dependent and censored')
    return dict(at=now,delay_assumption_seconds=0,unit='wallet-event with recent BUY',
        n_units=len(output),n_wallets=len({r['wallet'] for r in output}),n_effective_cases=1,
        n_comparisons=9*len(output),rows=output,p_value=None,corrected_p_value=None,
        missing=['true account creation','first-ever bet','historical liquidity','logical resolution compatibility',
                 'full positions','universe-wide funding','first public information','historical real-time observability'],
        meaning='Internal descriptive references, not insider controls or precision/false-positive estimates')

def main():
    capacity()
    from registre import enregistrer
    from ana_replay import verified_input
    config=json.loads((STUDY/'code/vendor/config.json').read_text())
    result=features(verified_input(),config)
    out=STUDY/'derived/features.json.gz';out.parent.mkdir(exist_ok=True)
    write_bytes(out,gzip.compress(json.dumps(result,sort_keys=True,separators=(',',':')).encode(),mtime=0))
    enregistrer(str(STUDY),test='R2_eight_dimensions_and_joint_descriptive',declare=True,
                n=result['n_units'],n_effectif=1,n_comparaisons=result['n_comparisons'],agent='Codex',
                sortie='derived/features.json.gz',note='Eight dimensions plus conjunction; unknowns not zeros; no p-value; dependent matched references')
    print(json.dumps({k:result[k] for k in ('n_units','n_wallets','n_comparisons')}))

if __name__=='__main__':main()
