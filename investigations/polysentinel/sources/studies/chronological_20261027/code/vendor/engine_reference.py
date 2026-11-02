import asyncio
import contextlib
import fcntl
import hashlib
import json
import logging
import os
import resource
import shutil
import signal
import subprocess
import threading
import time
from pathlib import Path

from .db import Store, encode
from .dashboard import server, snapshot
from .reports import export_dossier, daily_report
from .storage_budget import storage_usage, reserve_bytes

LOG = logging.getLogger('polysentinel')

@contextlib.contextmanager
def instance(root):
    path = Path(root)/'data/instance.lock'
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a+') as f:
        try:
            fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError('PolySentinel fonctionne déjà ; utilisez status ou investigate pour mettre une tâche en file.') from exc
        f.seek(0); f.truncate(); f.write(str(os.getpid())); f.flush()
        try: yield
        finally: fcntl.flock(f,fcntl.LOCK_UN)

def resources(root):
    r = resource.getrusage(resource.RUSAGE_SELF)
    return dict(**storage_usage(root),max_rss_bytes=r.ru_maxrss,cpu_seconds=r.ru_utime+r.ru_stime)

def resource_mode(config, metrics):
    used=metrics.get('quota_accounted_bytes',metrics['project_data_bytes'])
    margin=reserve_bytes(config)
    if metrics['free_bytes']-margin<config['min_free_bytes'] or used+margin>=config['data_quota_bytes']:
        return 'paused'
    if metrics['free_bytes']<config['min_free_bytes']+500_000_000 or used>=config['data_quota_bytes']*.9:
        return 'reduced'
    return 'normal'

def payloads(store,kind,limit=50000,as_of=None):
    if kind=='trade' and as_of is None:
        at=time.time()
        # Keep the time index first: sorting decoded history spilled ~236 MB per cycle.
        rows=[dict(r) for r in store.conn.execute("""SELECT o.kind,o.key,json_remove(o.payload,'$.raw') payload,o.first_seen,o.observed_at
            FROM trade_index t CROSS JOIN objects o ON o.kind='trade' AND o.key=t.key
            WHERE t.trade_time<=? AND t.observed_at<=? ORDER BY t.trade_time DESC,t.key LIMIT ?""",(at,at,limit))]
        for r in rows:r['payload']=json.loads(r['payload'])
    elif as_of is None:
        rows = [dict(r) for r in store.conn.execute("SELECT kind,key,json_remove(payload,'$.raw') payload,first_seen,observed_at FROM objects WHERE kind=? ORDER BY observed_at DESC LIMIT ?",(kind,limit))]
        for r in rows:r['payload']=json.loads(r['payload'])
    else:
        ordering="json_extract(payload,'$.timestamp') DESC" if kind=='trade' else 'observed_at DESC'
        rows = [dict(r) for r in store.conn.execute('''SELECT kind,key,json_remove(payload,'$.raw') payload,observed_at FROM
            (SELECT *,ROW_NUMBER() OVER (PARTITION BY key ORDER BY observed_at DESC) n
             FROM history WHERE kind=? AND observed_at<=?) WHERE n=1 ORDER BY '''+ordering+' LIMIT ?',(kind,as_of,limit))]
        for r in rows:r['payload']=json.loads(r['payload'])
    result = []
    for row in rows:
        p = dict(row['payload'])
        p.setdefault('observed_at',row.get('first_seen',row['observed_at']) if kind=='trade' else row['observed_at'])
        result.append(p)
    return result

def material(case):
    if case.get('material_fingerprint'): return case['material_fingerprint']
    fields = {k:case.get(k) for k in ('wallet','event_id','score','status','quality','signals','trade_ids','evidence','contradictions')}
    return hashlib.sha256(encode(fields).encode()).hexdigest()

def metadata_history(store,kind,as_of=None,limit=30000):
    at=time.time() if as_of is None else as_of
    rows=store.conn.execute("SELECT json_remove(payload,'$.raw') payload,observed_at FROM history WHERE kind=? AND observed_at<=? ORDER BY observed_at DESC LIMIT ?",(kind,at,limit)).fetchall()
    result=[]
    for row in rows:
        p=json.loads(row['payload']);p.setdefault('observed_at',row['observed_at']);result.append(p)
    return result

def wallet_history(store,as_of):
    return {r['wallet']:dict(first_timestamp=r['first_timestamp'],observations=r['observations'])
            for r in store.conn.execute('''SELECT wallet,MIN(trade_time) first_timestamp,COUNT(*) observations
                FROM trade_index WHERE observed_at<=? AND trade_time<=? GROUP BY wallet''',(as_of,as_of))}

def notify(root,count):
    store=Store(root)
    script = 'on run argv\ndisplay notification (item 1 of argv) with title "PolySentinel"\nend run'
    try:
        r = subprocess.run(['/usr/bin/osascript','-e',script,f'{count} dossier(s) nouveau(x) ou modifié(s), à examiner dans le tableau de bord.'],capture_output=True,text=True,timeout=10)
        store.health('notifications','ok' if r.returncode==0 else 'degraded','Commande de notification locale acceptée ; affichage soumis aux réglages macOS' if r.returncode==0 else r.stderr[:300])
    except (OSError,subprocess.TimeoutExpired) as exc:
        store.health('notifications','degraded',str(exc))
    finally:store.close()

def apply_public_knowledge(store,events,markets,as_of=None):
    at=time.time() if as_of is None else as_of
    milestones={p['event_id']:p for p in payloads(store,'public_milestone',as_of=at) if p.get('event_id')}
    # Some adapters use the object key as identity; retain it when not repeated in payload.
    for row in store.conn.execute('SELECT key,payload,observed_at FROM history WHERE kind=? AND observed_at<=? ORDER BY observed_at',('public_milestone',at)):
        milestones[row['key']]=json.loads(row['payload'])
    for event in events:
        p=milestones.get(event['id'])
        if p and p.get('verified') and p.get('result_available'):
            event.update(public_at=p.get('public_at'),public_observed_at=p.get('public_observed_at'))
    conditions={}
    for row in store.conn.execute('SELECT key,payload FROM history WHERE kind=? AND observed_at<=? ORDER BY observed_at',('public_condition',at)):
        conditions[row['key']]=json.loads(row['payload'])
    for market in markets:
        p=conditions.get(market.get('condition_id'))
        if p and p.get('result_available') and p.get('verified'):
            market['closed']=True

def expire_cases(store,current_ids,at):
    for row in store.conn.execute("SELECT key,payload FROM objects WHERE kind='case'").fetchall():
        c=json.loads(row['payload'])
        if row['key'] not in current_ids and c.get('current',True):
            c.update(current=False,priority=False,preliminary=False,inactive_reason='Absent de la fenêtre courante ou périmètre remappé',last_evaluated_at=at)
            store.put('case',row['key'],c)

def map_trades(trades,markets,events,at):
    by_condition={};by_slug={}
    for m in sorted(markets,key=lambda p:p['observed_at']):
        if m['observed_at']<=at and m.get('condition_id'):by_condition[m['condition_id'].lower()]=m
    for e in sorted(events,key=lambda p:p['observed_at']):
        if e['observed_at']<=at and e.get('slug'):by_slug[e['slug']]=e
    mapped=[]
    for original in trades:
        trade=dict(original)
        m=by_condition.get(str(trade.get('condition_id','')).lower())
        if m and any(str(t['token_id'])==str(trade.get('token_id')) for t in m.get('tokens',[])):
            trade.update(market_id=m['id'],event_id=m['event_id'],mapping_observed_at=m['observed_at'])
        elif not trade.get('event_id') and trade.get('event_slug') in by_slug:
            e=by_slug[trade['event_slug']]
            trade.update(event_id=e['id'],mapping_observed_at=e['observed_at'])
        mapped.append(trade)
    return mapped

async def run_cycle(store,config,net,force_catalog=False):
    from .collect import Collector
    from .signals import evaluate, describe_scenarios
    start = time.time()
    usage=resources(store.root)
    mode=resource_mode(config,usage)
    if mode=='paused':
        # A prolonged quota pause must not append heartbeat/history/cycle rows forever.
        return dict(start=start,end=time.time(),resource_mode=mode,resources=usage,
                    errors=['resource_limit'],coverage_state='degraded')
    store.conn.execute('INSERT INTO cycles(start,status) VALUES(?,?)',(start,'running'))
    cycle_id = store.conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    store.conn.commit()
    metrics = dict(cycle_id=cycle_id,start=start,errors=[])
    metrics.update(resources=usage,resource_mode=mode)
    store.health('resources','ok' if mode=='normal' else 'degraded','Réserve et quota respectés' if mode=='normal' else 'Enrichissements réduits' if mode=='reduced' else 'Collecte suspendue : réserve disque ou quota atteint',**usage)
    if mode=='paused':
        metrics['errors'].append('resource_limit')
    else:
        net.begin_cycle()
        collection_config = dict(config)
        if mode=='reduced':
            normal_slots=config.get('market_batches',2)*config.get('markets_per_batch',5)
            collection_config.update(market_batches=1,markets_per_batch=min(2,normal_slots),
                catalog_pages=min(2,config.get('catalog_pages',4)),
                catalog_page_size=min(25,config.get('catalog_page_size',50)))
        metrics['collection_budget']={k:collection_config.get(k) for k in
            ('market_batches','markets_per_batch','catalog_pages','catalog_page_size')}
        collector = Collector(store,net,collection_config)
        last = store.checkpoint('engine:last_catalog') or 0
        if force_catalog or start-last>=config['catalog_interval']:
            try:
                metrics['catalog'] = await collector.catalog()
                metrics['errors'].extend(metrics['catalog'].get('errors',[]))
                store.checkpoint('engine:last_catalog',time.time())
            except Exception as exc:
                LOG.exception('catalogue')
                metrics['errors'].append('catalog: '+str(exc))
                store.health('catalog','error',str(exc))
        try:
            metrics['trades'] = await collector.trades()
            metrics['errors'].extend(metrics['trades'].get('errors',[]))
        except Exception as exc:
            LOG.exception('trades')
            metrics['errors'].append('trades: '+str(exc))
            store.health('trades','error',str(exc))
        # Discover metadata for bounded, rotating unknown events from the live feed.
        unresolved=store.conn.execute("""SELECT json_extract(t.payload,'$.event_slug') slug,MIN(t.first_seen) first_seen,
            MAX(COALESCE(c.updated_at,0)) attempted FROM objects t LEFT JOIN checkpoints c
            ON c.key='resolve_attempt:'||json_extract(t.payload,'$.event_slug')
            WHERE t.kind='trade' AND json_extract(t.payload,'$.event_id')='' AND json_extract(t.payload,'$.event_slug')!=''
            GROUP BY slug HAVING attempted<? ORDER BY attempted,first_seen LIMIT ?""",(time.time()-3600,config.get('on_demand_events',2))).fetchall()
        for row in unresolved:
            try:await collector.resolve_event(row['slug'])
            except Exception as exc:store.health('resolve:'+row['slug'],'error',str(exc))
            finally:store.checkpoint('resolve_attempt:'+row['slug'],time.time())
        now = time.time()
        trades = payloads(store,'trade',config.get('analysis_trade_limit',50000))
        markets = metadata_history(store,'market')
        events = metadata_history(store,'event')
        apply_public_knowledge(store,events,markets,now)
        trades=map_trades(trades,markets,events,now)
        diagnostics={}
        cases = evaluate(trades,markets,events,now=now,config=config,wallet_history=wallet_history(store,now),diagnostics=diagnostics)
        latest_markets={}
        for market in sorted(markets,key=lambda p:p['observed_at']):latest_markets[market['id']]=market
        scenarios={}
        for case in cases:
            eid=case['event_id']
            if eid not in scenarios:
                scenarios[eid]=describe_scenarios([m for m in latest_markets.values() if m['event_id']==eid])
            case['scenarios']=scenarios[eid]
        expire_cases(store,{c['id'] for c in cases},now)
        changed = 0
        for case in cases:
            previous = store.get('case',case['id'])
            if previous and previous['payload'].get('current',True) and material(previous['payload'])==material(case):continue
            if previous:
                for key in ('investigation_id','report','created_at'):
                    if key in previous['payload']:case[key]=previous['payload'][key]
            case['current']=True
            if case.get('priority'):
                try:
                    case['report'] = export_dossier(store.root,case)
                    changed += 1
                except RuntimeError as exc:
                    metrics['errors'].append('report: '+str(exc))
                    store.health('reports','degraded',str(exc))
            with store.transaction() as conn:
                store.put('case',case['id'],case,conn=conn)
                if case.get('priority'):
                    store.put('alert',case['id']+':'+str(time.time_ns()),case,conn=conn)
        metrics.update(analysis_trades=len(trades),analysis_total_trades=store.count('trade'),cases=len(cases),alerts_changed=changed,analysis_diagnostics=diagnostics)
        store.health('analysis','capped' if store.count('trade')>len(trades) else 'ok','Seuils exploratoires ; références en apprentissage ; aucune calibration statistique',used_trades=len(trades),stored_trades=store.count('trade'),cases=len(cases),diagnostics=diagnostics)
        for kind,used in [('market',markets),('event',events)]:
            total=store.conn.execute('SELECT COUNT(*) FROM history WHERE kind=?',(kind,)).fetchone()[0]
            store.health('analysis_metadata:'+kind,'capped' if total>len(used) else 'ok','Snapshots disponibles au moment du trade ; limite mémoire explicite',used=len(used),total=total,oldest_used=min((p['observed_at'] for p in used),default=None))
        if changed and config['notifications']:await asyncio.to_thread(notify,store.root,changed)
        if mode=='normal':await investigations(store,config,net,metrics)
        metrics['requests']=net.requests_used
    end = time.time()
    metrics.update(end=end,duration_seconds=end-start)
    coverage_degraded=any(metrics.get(k,{}).get('status') in ('degraded','capped') for k in ('catalog','trades'))
    state = 'degraded' if metrics['errors'] or coverage_degraded else 'ok'
    metrics['coverage_state']=state
    store.conn.execute('UPDATE cycles SET end=?,status=?,metrics=? WHERE id=?',(end,state,encode(metrics),cycle_id))
    store.conn.commit()
    store.put('service','last_cycle',metrics)
    store.health('engine',state,'Cycle terminé ; couverture bornée' if state=='degraded' else 'Cycle terminé',cycle_id=cycle_id,duration_seconds=end-start)
    if mode!='paused' and end-(store.checkpoint('engine:last_report') or 0)>=300:
        try:
            daily_report(store,snapshot(store));store.checkpoint('engine:last_report',end)
        except RuntimeError as exc:store.health('reports','degraded',str(exc))
    LOG.info('Cycle %s: %s',cycle_id,encode(metrics))
    return metrics

async def investigations(store,config,net,metrics):
    from .investigation import investigate
    now=time.time()
    manual = store.conn.execute("SELECT key,payload FROM objects WHERE kind='task' AND json_extract(payload,'$.status')='pending' ORDER BY first_seen LIMIT 2").fetchall()
    due=now-(store.checkpoint('engine:last_auto_investigation') or 0)>=config.get('automatic_investigation_interval',0)
    selection_sql = """SELECT c.payload FROM objects c LEFT JOIN checkpoints p ON p.key='investigated:'||c.key
        WHERE c.kind='case' AND COALESCE(json_extract(c.payload,'$.current'),1)=1
        AND json_extract(c.payload,'$.priority')=1 AND json_extract(c.payload,'$.preliminary')=1
        AND (p.value IS NULL OR CAST(p.value AS REAL)<?)
        ORDER BY COALESCE(CAST(p.value AS REAL),0),json_extract(c.payload,'$.score') DESC,c.first_seen,c.key LIMIT 250 OFFSET ?"""
    offset=int(store.checkpoint('engine:investigation_scan') or 0)
    pending=store.conn.execute(selection_sql,(now-3600,offset)).fetchall() if due else []
    if due and offset and not pending:
        offset=0;pending=store.conn.execute(selection_sql,(now-3600,offset)).fetchall()
    if due:
        # Excluded scopes must not permanently occupy the bounded scan head.
        store.checkpoint('engine:investigation_scan',offset+len(pending) if len(pending)==250 else 0)
    metrics['automatic_investigation_deferred']=not due
    from .review import case_scope
    cache={};eligible=[]
    for row in pending:
        case=json.loads(row['payload'])
        if case_scope(store,case,now,cache)['eligible_for_automatic_investigation']:
            eligible.append(case)
    metrics['investigation_selection']=dict(scanned=len(pending),scan_offset=offset,scan_cap=250,eligible=len(eligible),
        policy='annonce documentée future, dossier prioritaire et préalable; pas de secret présumé')
    jobs = [(json.loads(r['payload'])['target'],r['key']) for r in manual]
    jobs += [(case,None) for case in eligible]
    for target,task_id in jobs[:config['investigations_per_cycle']]:
        if net.requests_used+config['investigation_max_requests']>config['requests_per_cycle']:
            store.health('investigation_budget','capped','Enquête reportée : budget du cycle insuffisant')
            break
        try:
            result = await investigate(store,net,config,target)
            key = result.get('id') or (target['id'] if isinstance(target,dict) else str(target))
            store.health('investigation','degraded' if result.get('errors') or result.get('truncated') else 'ok',
                         'Enquête terminée ; limites et sources dans le dossier',investigation_id=key)
            if isinstance(target,dict):
                target['investigation_id']=key
                target['report']=export_dossier(store.root,target,result)
                store.put('case',target['id'],target)
                store.checkpoint('investigated:'+target['id'],time.time())
            else:export_dossier(store.root,dict(id=key,wallet=target,status=result.get('status','données insuffisantes'),calculated_at=time.time()),result)
            if task_id:store.put('task',task_id,dict(target=target,status='done',investigation_id=key))
        except Exception as exc:
            LOG.exception('enquête')
            metrics['errors'].append('investigation: '+str(exc))
            store.health('investigation','error',str(exc))
            if task_id:store.put('task',task_id,dict(target=target,status='error',error=str(exc)))
        finally:
            if isinstance(target,dict):store.checkpoint('investigated:'+target['id'],time.time())
            if task_id is None:store.checkpoint('engine:last_auto_investigation',time.time())

async def serve(config):
    from .net import Net
    store = Store(config['root'])
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT,signal.SIGTERM):loop.add_signal_handler(sig,stop.set)
    httpd = server(store.root,config['port'])
    threading.Thread(target=httpd.serve_forever,daemon=True).start()
    previous = store.get('service','heartbeat')
    if previous and time.time()-previous['payload'].get('at',0)>config['trade_interval']*2:
        store.put('gap',str(time.time()),dict(start=previous['payload'].get('at'),end=time.time(),reason='Interruption service, veille ou arrêt ; reprise avec chevauchement, rattrapage borné'))
    store.conn.execute("UPDATE cycles SET status='interrupted' WHERE end IS NULL")
    store.conn.commit()
    async def heartbeat():
        from .monitoring import runtime_status
        last_resources = 0
        measured = {}
        while not stop.is_set():
            now=time.time()
            if now-last_resources>30:
                measured=resources(store.root);last_resources=now
            payload=dict(at=now,pid=os.getpid(),running=True,resource_mode=resource_mode(config,measured),**measured)
            runtime_status(store.root,payload)
            if payload['resource_mode']!='paused':store.put('service','heartbeat',payload)
            try:await asyncio.wait_for(stop.wait(),timeout=5)
            except asyncio.TimeoutError:pass
    hb = asyncio.create_task(heartbeat())
    async def monitor():
        from .monitoring import record
        while not stop.is_set():
            await asyncio.to_thread(record,store.root)
            try:await asyncio.wait_for(stop.wait(),timeout=300)
            except asyncio.TimeoutError:pass
    observer=asyncio.create_task(monitor())
    try:
        async with Net(store,config) as net:
            while not stop.is_set():
                started=time.monotonic()
                work=asyncio.create_task(run_cycle(store,config,net))
                stopper=asyncio.create_task(stop.wait())
                done,_=await asyncio.wait([work,stopper],return_when=asyncio.FIRST_COMPLETED)
                if stopper in done and not work.done():
                    work.cancel()
                    with contextlib.suppress(asyncio.CancelledError):await work
                else:
                    stopper.cancel()
                    try:await work
                    except Exception as exc:
                        LOG.exception('Cycle interrompu')
                        store.conn.execute("UPDATE cycles SET end=?,status='error' WHERE end IS NULL",(time.time(),))
                        store.conn.commit()
                        store.health('engine','error',str(exc))
                delay=max(1,config['trade_interval']-(time.monotonic()-started))
                try:await asyncio.wait_for(stop.wait(),timeout=delay)
                except asyncio.TimeoutError:pass
    finally:
        stop.set();await hb;await observer
        httpd.shutdown();httpd.server_close()
        from .monitoring import runtime_status
        payload=dict(at=time.time(),pid=os.getpid(),running=False)
        runtime_status(store.root,payload)
        if resource_mode(config,resources(store.root))!='paused':store.put('service','heartbeat',payload)
        store.close()
