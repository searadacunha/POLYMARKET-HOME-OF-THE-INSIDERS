"""Descriptive review of a fixed saved population; no score changes or hypothesis tests."""
import asyncio
from collections import Counter
import json
from pathlib import Path
import time
from polysentinel.config import load_config
from polysentinel.db import Store
from polysentinel.engine import resource_mode, resources
from polysentinel.quality import case_quality
from polysentinel.review import case_scope
from polysentinel.investigation import Budget
from polysentinel.chain import inspect_receipt
from polysentinel.net import Net

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'evidence/restoration_20261029'


def comparison(store, case):
    at=case['calculated_at']; peers={}; groups=[]
    for alert in case['alerts']:
        market=store.get('market',alert.get('market_id',''))
        condition=alert.get('condition_id') or (market['payload'].get('condition_id') if market else None)
        if not condition: continue
        rows=store.conn.execute("""SELECT o.key,o.payload FROM trade_index t CROSS JOIN objects o
            ON o.kind='trade' AND o.key=t.key WHERE t.condition_id=? AND t.wallet!=?
            AND t.trade_time>=? AND t.trade_time<? AND t.observed_at<=? AND o.observed_at<=?
            ORDER BY t.trade_time,t.key LIMIT 1001""",(condition,case['wallet'],at-86400,at,at,at)).fetchall()
        capped=len(rows)>1000
        for row in rows[:1000]:
            p=json.loads(row['payload'])
            if p.get('token_id')==alert.get('token_id') and p.get('side')==alert.get('side'):
                peers[row['key']]=p
        groups.append(dict(token_id=alert.get('token_id'),condition_id=condition,scan_capped=capped))
    return dict(sufficient=False,description='Descriptive pre-signal same-token/side controls, other wallets; incomplete collected universe.',
        window=[at-86400,at],rows=len(peers),wallets=len({p['wallet'] for p in peers.values()}),
        trade_ids=sorted(peers),groups=groups,statistical_test=None,
        blockers=['Population collected non-exhaustively; wallet clusters and selection probabilities of retained trades not established.',
                  'No independent historical opening inventory or matched liquidity/age strata certified.'])


async def main():
    config=load_config(ROOT);store=Store(ROOT)
    population=json.loads((OUT/'priority_before.json').read_text())
    selectors=[('Fed décembre',lambda c:'Fed Decision in December' in c.get('event_title','')),
               ('Lancement token',lambda c:'Predict.fun' in c.get('event_title','')),
               ('Dirigeante ECB',lambda c:'Lagarde' in c.get('event_title','')),
               ('Sport témoin',lambda c:'Dota 2' in c.get('event_title','')),
               ('Prix continu témoin',lambda c:any(x in c.get('event_title','').lower() for x in ('bitcoin','ethereum','solana')))]
    selected=[]
    for label,predicate in selectors:
        choices=sorted((c for c in population if predicate(c)),key=lambda c:(len(c['alerts']),c['id']))
        if choices:selected.append((label,choices[0]))
    (OUT/'selection.json').write_text(json.dumps([dict(stratum=l,case=c) for l,c in selected],indent=2))
    results=[]
    async with Net(store,config) as net:
        for label,case in selected:
            net.begin_cycle();budget=Budget(net,config);context={};errors=[]
            transactions=list(dict.fromkeys(tx for a in case['alerts'] for tx in a.get('transactions',[])))
            for tx in transactions:
                receipt=store.get('receipt',tx)
                if receipt and receipt['payload'].get('status')=='confirmed':continue
                try:await inspect_receipt(store,budget,config,tx,case['wallet'],context=context)
                except Exception as exc:
                    errors.append(dict(transaction_hash=tx,error=str(exc)))
                    break
            quality=case_quality(store,case)
            local_inventory=store.conn.execute("SELECT COUNT(*),MIN(trade_time),MAX(trade_time) FROM trade_index WHERE wallet=? AND observed_at<=? AND trade_time<=?",(case['wallet'],case['calculated_at'],case['calculated_at'])).fetchone()
            results.append(dict(stratum=label,case_id=case['id'],wallet=case['wallet'],title=case.get('event_title'),
                signal_at=case['calculated_at'],score_unchanged=case['score'],transactions=transactions,
                quality=quality,scope=case_scope(store,case),comparator=comparison(store,case),
                historical_exposure=dict(verified=False,at_signal=False,local_trade_rows=local_inventory[0],
                    first_known_trade=local_inventory[1],last_known_trade=local_inventory[2],
                    blockers=['Opening inventory, ERC1155 transfers, splits/merges, conversions and collateral across ledgers not reconstructed.',
                              'Archive balance queries blocked while volume reserve is insufficient; availability remains unknown.']),
                enrichment_errors=errors,network_attempts=net.requests_used,
                verdict='Données insuffisantes'))
    all_quality=[case_quality(store,c) for c in population]
    audit=dict(at=time.time(),denominator=len(population),missing_counts=dict(Counter(k for q in all_quality for k in q['missing'])),
               receipt_issues=dict(Counter(i for q in all_quality for g in q['receipt_groups'] for i in g['issues'])),
               receipt_groups=sum(len(q['receipt_groups']) for q in all_quality),
               matched_groups=sum(g['matched'] for q in all_quality for g in q['receipt_groups']),
               assessed_cases=results,resource_mode=resource_mode(config,resources(ROOT)))
    (OUT/'case_reviews.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))
    store.close()
    print(json.dumps({k:v for k,v in audit.items() if k!='assessed_cases'},indent=2))
    print([(r['case_id'],r['comparator']['rows'],r['network_attempts']) for r in results])


if __name__=='__main__':asyncio.run(main())
