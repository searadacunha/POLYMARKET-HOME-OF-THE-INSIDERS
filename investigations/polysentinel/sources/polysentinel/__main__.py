import argparse
import asyncio
import datetime as dt
import json
import logging
from logging.handlers import RotatingFileHandler
import platform
import subprocess
import sys
import time
from pathlib import Path

from .config import load_config
from .db import Store
from .dashboard import snapshot
from .engine import instance, resources, payloads, metadata_history, apply_public_knowledge, map_trades, wallet_history, serve, run_cycle
from .reports import atomic_write, daily_report, export_dossier
from . import service

def output(value):print(json.dumps(value,ensure_ascii=False,indent=2))

async def scan(config):
    from .net import Net
    store=Store(config['root'])
    try:
        async with Net(store,config) as net:return await run_cycle(store,config,net,force_catalog=True)
    finally:store.close()

async def investigate_now(config,target):
    from .net import Net
    from .investigation import investigate
    store=Store(config['root'])
    try:
        async with Net(store,config) as net:
            result=await investigate(store,net,config,target)
            stem=export_dossier(store.root,dict(id=result.get('id',str(target)),wallet=target,status=result.get('status','données insuffisantes'),calculated_at=time.time()),result)
            return dict(report=str(store.root/'reports'/f'{stem}.html'),investigation=result)
    finally:store.close()

def main(argv=None):
    parser=argparse.ArgumentParser(description='PolySentinel — surveillance publique locale en lecture seule')
    parser.add_argument('command',choices=['doctor','start','stop','restart','status','logs','dashboard','scan-once','investigate','replay','report','uninstall','run'])
    parser.add_argument('target',nargs='?')
    parser.add_argument('--as-of',help='Replay: date ISO UTC ou epoch, données observées à cette date seulement')
    args=parser.parse_args(argv)
    config=load_config();root=Path(config['root'])
    (root/'logs').mkdir(exist_ok=True)
    handler=RotatingFileHandler(root/'logs/polysentinel.log',maxBytes=5_000_000,backupCount=4)
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    logging.getLogger('polysentinel').addHandler(handler)
    logging.getLogger('polysentinel').setLevel(logging.INFO)
    cmd=args.command
    if cmd=='start':output(service.start(config))
    elif cmd=='stop':output(service.stop())
    elif cmd=='restart':service.stop();output(service.start(config))
    elif cmd=='uninstall':output(service.uninstall())
    elif cmd=='run':
        with instance(root):asyncio.run(serve(config))
    elif cmd=='scan-once':
        with instance(root):output(asyncio.run(scan(config)))
    elif cmd=='logs':
        path=root/'logs/polysentinel.log'
        if path.exists():
            with path.open('rb') as f:
                f.seek(max(0,path.stat().st_size-30000));print(f.read().decode(errors='replace'))
    elif cmd=='dashboard':
        url=f'http://127.0.0.1:{config["port"]}'
        print(url);subprocess.run(['open',url],check=True)
    else:
        store=Store(root)
        try:local_command(args,parser,store,config)
        finally:store.close()

def local_command(args,parser,store,config):
    root=store.root;cmd=args.command
    if cmd=='status':output(dict(service=service.status(),**snapshot(store)))
    elif cmd=='doctor':
        import importlib.metadata
        output(dict(python=sys.version,platform=platform.platform(),root=str(root),
            dependencies={n:importlib.metadata.version(n) for n in ('httpx','networkx')},
            sqlite_integrity=store.conn.execute('PRAGMA quick_check').fetchone()[0],
            resources=resources(root),service=service.status(),configuration=config,
            sources=[r['payload'] for r in store.list('health',100)],
            note='Diagnostic local ; disponibilité réseau attestée par les collectes horodatées.'))
    elif cmd=='report':print(daily_report(store,snapshot(store)))
    elif cmd=='investigate':
        if not args.target:parser.error('investigate exige une adresse, un événement ou un identifiant de dossier')
        existing=store.get('case',args.target)
        target=existing['payload'] if existing else args.target
        if service.status()['loaded']:
            key=str(time.time_ns());store.put('task',key,dict(target=target,status='pending',created_at=time.time()))
            output(dict(task=key,status='pending',message='Enquête mise en file du service'))
        else:
            with instance(root):output(asyncio.run(investigate_now(config,target)))
    elif cmd=='replay':
        from .signals import evaluate
        cutoff=args.as_of
        if cutoff:
            try:at=float(cutoff)
            except ValueError:
                parsed=dt.datetime.fromisoformat(cutoff.replace('Z','+00:00'))
                if parsed.tzinfo is None:parser.error('--as-of doit préciser le fuseau, par exemple Z')
                at=parsed.timestamp()
        else:at=time.time()
        markets=metadata_history(store,'market',as_of=at);events=metadata_history(store,'event',as_of=at)
        trades=payloads(store,'trade',as_of=at)
        apply_public_knowledge(store,events,markets,at)
        trades=map_trades(trades,markets,events,at)
        result=evaluate(trades,markets,events,now=at,config=config,wallet_history=wallet_history(store,at))
        file=root/'reports'/f'replay-{int(at)}.json'
        atomic_write(file,json.dumps(dict(as_of=at,limits=dict(trades_used=len(trades),trades_max=50000,market_snapshots_used=len(markets),event_snapshots_used=len(events),metadata_max=30000),limitations='Données réellement observées seulement. Historique incomplet ; aucune évaluation de performance ou de culpabilité.',cases=result),ensure_ascii=False,indent=2))
        output(dict(file=str(file),cases=len(result),alerts_emitted=0))

if __name__=='__main__':
    try:main()
    except (RuntimeError,subprocess.CalledProcessError) as exc:
        print(str(exc),file=sys.stderr)
        if isinstance(exc,subprocess.CalledProcessError) and exc.stderr:print(exc.stderr,file=sys.stderr)
        raise SystemExit(1)
