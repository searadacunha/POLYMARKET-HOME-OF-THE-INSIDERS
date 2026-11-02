"""Read-only, short SQLite observations; no checkpoint or vacuum side effect."""
import argparse
import ctypes
import datetime as dt
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import time
import zlib
from logging.handlers import RotatingFileHandler
import logging

def cycle_storage_start(store):
    return {table: store.conn.execute('SELECT COALESCE(MAX(rowid),0) FROM '+table).fetchone()[0]
            for table in ('contents','history_refs','response_refs','trade_index')}

def cycle_storage_delta(store, before):
    """Append-only rowids bound the scan to new records, not the whole evidence store."""
    count, compressed, raw = store.conn.execute(
        'SELECT COUNT(*),COALESCE(SUM(length(body)),0),COALESCE(SUM(raw_bytes),0) FROM contents WHERE rowid>?',
        (before['contents'],)).fetchone()
    counts = {table: store.conn.execute('SELECT COUNT(*) FROM '+table+' WHERE rowid>?',
                                      (before[table],)).fetchone()[0]
              for table in ('history_refs','response_refs','trade_index')}
    kinds = dict(store.conn.execute('SELECT kind,COUNT(*) FROM history_refs WHERE rowid>? GROUP BY kind',
                                   (before['history_refs'],)))
    return dict(unique_contents=count, compressed_content_bytes=compressed, raw_content_bytes=raw,
                history_observations=counts['history_refs'],response_observations=counts['response_refs'],
                new_trade_keys=counts['trade_index'],history_by_kind=kinds,
                note='Contents are inside DB/WAL, not additive to file growth. Excludes final cycle metrics and daily export. No physical SSD write claim.')

def runtime_status(root,payload=None):
    path=Path(root)/'metrics/heartbeat.json'
    if payload is None:
        try:return json.loads(path.read_text())
        except FileNotFoundError:return {}
    path.parent.mkdir(exist_ok=True)
    raw=json.dumps(payload,ensure_ascii=False)
    if len(raw.encode())>65536:raise ValueError('Heartbeat trop volumineux')
    temp=path.with_suffix('.tmp');temp.write_text(raw);temp.replace(path)
    return payload

def process_io(pid):
    # Field order from installed macOS SDK sys/resource.h, rusage_info_v2.
    fields = ('user_time system_time pkg_idle_wkups interrupt_wkups pageins wired_size '
              'resident_size phys_footprint proc_start_abstime proc_exit_abstime '
              'child_user_time child_system_time child_pkg_idle_wkups child_interrupt_wkups '
              'child_pageins child_elapsed_abstime diskio_bytesread diskio_byteswritten').split()
    class Usage(ctypes.Structure):
        _fields_ = [('uuid', ctypes.c_ubyte * 16)] + [(f, ctypes.c_uint64) for f in fields]
    if sys.platform != 'darwin': return {'available': False, 'reason': 'macOS only'}
    value = Usage()
    lib = ctypes.CDLL('/usr/lib/libproc.dylib', use_errno=True)
    if lib.proc_pid_rusage(int(pid), 2, ctypes.byref(value)):
        return {'available': False, 'errno': ctypes.get_errno()}
    return {'available': True, 'pid': pid, **{f: getattr(value, f) for f in fields},
            'meaning': 'Kernel-attributed process IO counters; not growth or physical drive writes'}

def measure(root):
    started = time.time()
    cx = sqlite3.connect(f'file:{root}/data/polysentinel.sqlite3?mode=ro', uri=True, timeout=10)
    cx.row_factory = sqlite3.Row
    cx.create_function('payload_text',1,lambda b:zlib.decompress(b).decode('utf-8'),deterministic=True)
    deadline=time.monotonic()+10
    cx.set_progress_handler(lambda:int(time.monotonic()>deadline),10000)
    try:
        hb = cx.execute("SELECT payload FROM objects WHERE kind='service' AND key='heartbeat'").fetchone()
        hb = json.loads(hb[0]) if hb else {}
        live=runtime_status(root)
        if live.get('at',0)>hb.get('at',0):hb=live
        v2=cx.execute('PRAGMA user_version').fetchone()[0]==2
        object_sql='SELECT kind,COUNT(*) rows,NULL payload_bytes,MIN(first_seen) first_seen,MAX(observed_at) last_observed FROM object_refs GROUP BY kind' if v2 else 'SELECT kind,COUNT(*) rows,SUM(length(CAST(payload AS BLOB))) payload_bytes,MIN(first_seen) first_seen,MAX(observed_at) last_observed FROM objects GROUP BY kind'
        history_sql='SELECT kind,COUNT(*) rows,NULL payload_bytes,MAX(observed_at) last_observed FROM history_refs GROUP BY kind' if v2 else 'SELECT kind,COUNT(*) rows,SUM(length(CAST(payload AS BLOB))) payload_bytes,MAX(observed_at) last_observed FROM history GROUP BY kind'
        data = {'at': started, 'utc': dt.datetime.fromtimestamp(started, dt.timezone.utc).isoformat(), 'heartbeat': hb,'schema_version':2 if v2 else 1,
                'objects': [dict(r) for r in cx.execute(object_sql)],
                'history': [dict(r) for r in cx.execute(history_sql)],
                'db_pages': None,
                'payload_size_note': 'Detailed content sizes and dbstat omitted from periodic monitor to avoid scanning the entire evidence store.',
                'page_count': cx.execute('PRAGMA page_count').fetchone()[0],
                'page_size': cx.execute('PRAGMA page_size').fetchone()[0],
                'freelist_count': cx.execute('PRAGMA freelist_count').fetchone()[0],
                'last_cycle': dict(cx.execute('SELECT * FROM cycles WHERE end IS NOT NULL ORDER BY id DESC LIMIT 1').fetchone()),
                'checkpoints': dict(cx.execute('SELECT COUNT(*) total,MAX(updated_at) latest FROM checkpoints').fetchone())}
    finally: cx.close()
    data['sqlite_read_seconds'] = time.time()-started
    data['process'] = process_io(hb['pid']) if hb.get('pid') else {'available': False}
    totals = {}
    for p in root.rglob('*'):
        if not p.is_file() or p.is_symlink(): continue
        try: s = p.stat()
        except FileNotFoundError: continue
        rel = p.relative_to(root)
        if p.name.endswith(('.sqlite3','.sqlite3.gz')) and 'review_20261027' in p.parts: kind='audit_backup'
        elif rel.as_posix()=='data/polysentinel.sqlite3': kind='sqlite_main'
        elif p.name.endswith('-wal'): kind='wal'
        elif p.name.endswith('-shm'): kind='shm'
        elif p.suffix=='.tmp': kind='temporary'
        elif '.venv' in rel.parts: kind='dependencies'
        elif '__pycache__' in rel.parts: kind='cache'
        elif rel.parts[0] in ('reports','logs','evidence','metrics'): kind=rel.parts[0]
        else: kind='code_config_other'
        item=totals.setdefault(kind,{'files':0,'logical_bytes':0,'allocated_bytes':0})
        item['files']+=1;item['logical_bytes']+=s.st_size;item['allocated_bytes']+=s.st_blocks*512
    data.update(files=totals,free_bytes=shutil.disk_usage(root).free,measurement_seconds=time.time()-started,
                byte_note='Payload totals/db_pages are inside SQLite, not additive to filesystem totals. APFS blocks are not write volume or exclusive physical extents.')
    return data

def record(root):
    root=Path(root);folder=root/'metrics';folder.mkdir(exist_ok=True)
    try:result=measure(root)
    except Exception as exc:result={'at':time.time(),'error':f'{type(exc).__name__}: {exc}'}
    handler=RotatingFileHandler(folder/'runtime.jsonl',maxBytes=5_000_000,backupCount=1,encoding='utf-8')
    try:handler.emit(logging.LogRecord('polysentinel.metrics',logging.INFO,'',0,json.dumps(result,ensure_ascii=False,separators=(',',':')),(),None))
    finally:handler.close()
    return result

def storage_trends(root):
    """Adjacent observations, not projections or exclusive physical SSD writes."""
    path=Path(root)/'metrics/runtime.jsonl'
    if not path.exists():return {'status':'unavailable','windows':[],'errors':['Mesures absentes']}
    rows=[];errors=[]
    for line in path.read_text().splitlines()[-13:]:
        try:
            row=json.loads(line)
            if row.get('error'):errors.append(row['error'])
            else:rows.append(row)
        except (ValueError,TypeError) as exc:errors.append(str(exc))
    windows=[]
    for a,b in zip(rows,rows[1:]):
        seconds=b['at']-a['at']
        if seconds<=0 or a.get('schema_version')!=b.get('schema_version'):
            errors.append('Intervalle ou schéma non comparable');continue
        delta={k:{m:b['files'].get(k,{}).get(m,0)-a['files'].get(k,{}).get(m,0)
                  for m in ('logical_bytes','allocated_bytes')}
               for k in a['files'].keys()|b['files'].keys()}
        def counts(row,name):return {r['kind']:r['rows'] for r in row.get(name,[])}
        ca,cb=counts(a,'objects'),counts(b,'objects');ha,hb=counts(a,'history'),counts(b,'history')
        unique={k:cb.get(k,0)-ca.get(k,0) for k in ca.keys()|cb.keys()}
        versions={k:hb.get(k,0)-ha.get(k,0) for k in ha.keys()|hb.keys()}
        runtime=('sqlite_main','wal','shm','reports','logs','cache','metrics','temporary')
        windows.append(dict(start=a['at'],end=b['at'],seconds=seconds,files=delta,
            runtime_logical_mb_per_min=sum(delta.get(k,{}).get('logical_bytes',0) for k in runtime)/1e6*60/seconds,
            runtime_allocated_mb_per_min=sum(delta.get(k,{}).get('allocated_bytes',0) for k in runtime)/1e6*60/seconds,
            unique_keys=unique,history_observations=versions,
            same_process=a.get('process',{}).get('pid')==b.get('process',{}).get('pid'),
            gap=seconds>900,resource_mode=b.get('heartbeat',{}).get('resource_mode')))
    return dict(status='partial' if errors else 'ok' if windows else 'learning',windows=windows,errors=errors,
                latest_at=rows[-1]['at'] if rows else None,
                note='Fenêtres observées; aucune projection. Taille logique, blocs alloués et E/S sont différents. Les captures et réponses sont dans SQLite.')

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--output',type=Path,required=True);p.add_argument('--samples',type=int,default=1);p.add_argument('--interval',type=float,default=60)
    args=p.parse_args()
    if not 1<=args.samples<=1440 or args.interval<1:p.error('samples 1..1440, interval >=1')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    for i in range(args.samples):
        start=time.monotonic()
        try:data=measure(args.root.resolve())
        except Exception as exc:data={'at':time.time(),'error':f'{type(exc).__name__}: {exc}'}
        with args.output.open('a') as f:f.write(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
        print(json.dumps({'sample':i+1,'at':data['at'],'seconds':data.get('measurement_seconds'),'error':data.get('error')}),flush=True)
        if i+1<args.samples:time.sleep(max(0,args.interval-(time.monotonic()-start)))

if __name__=='__main__':main()
