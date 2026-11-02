"""One retained witness per condition/feed; presence is not exhaustive coverage."""
import json
import time


def feed_scope(query):
    if query.get('condition'):return 'individual'
    if any(query.get(k) for k in ('user','wallet','proxy_wallet')):return 'wallet'
    if query.get('event_id'):return 'event'
    return 'global'


def record_sources(store, trades, query, evidence_id, observed_at, conn, *, recovered=False):
    feed=feed_scope(query)
    written=0
    for trade in trades:
        condition=trade['condition_id'].lower()
        key=feed+':'+condition
        if conn.execute("SELECT 1 FROM object_refs WHERE kind='source_coverage' AND key=?",(key,)).fetchone():continue
        store.put('source_coverage',key,dict(condition_id=condition,feed=feed,
            trade_id=trade['id'],evidence_id=evidence_id,trade_at=trade['timestamp'],
            source_observed_at=observed_at,attributed_at=time.time(),
            filters={k:v for k,v in query.items() if k not in ('cursor','limit')},
            provenance='first_ingestion_recovered' if recovered else 'normalized_page_observation',
            completeness='presence_only'),conn=conn)
        written+=1
    return written


def source_sets(store, now):
    result={}
    for payload in store.conn.execute("SELECT payload FROM objects WHERE kind='source_coverage' AND observed_at<=?",(now,)):
        p=json.loads(payload[0])
        result.setdefault(p['condition_id'],set()).add(p['feed'])
    return result
