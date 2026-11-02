"""Explicit offline conversion, retaining exact observations and logical digests."""
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import time
import zlib
from .db import create_schema, register_functions, save_content, encode, index_trade

TABLES={'objects':'kind,key','history':'id','responses':'id','checkpoints':'key','cycles':'id'}

def logical_digest(path):
    cx=sqlite3.connect(f'file:{Path(path).resolve()}?mode=ro',uri=True)
    register_functions(cx)
    output={}
    try:
        for table,order in TABLES.items():
            h=hashlib.sha256();n=0
            for row in cx.execute(f'SELECT * FROM {table} ORDER BY {order}'):
                row=list(row)
                if table=='responses':row[4]=zlib.decompress(row[4]).hex()
                h.update(encode(row).encode()+b'\n');n+=1
            output[table]={'rows':n,'sha256':h.hexdigest()}
    finally:cx.close()
    return output

def build_migration(source,destination,min_free_bytes=10_000_000_000,capacity_check=None):
    source,destination=Path(source).resolve(),Path(destination).resolve()
    if destination.exists():raise FileExistsError(destination)
    if capacity_check:capacity_check()
    if shutil.disk_usage(destination.parent).free<min_free_bytes+100_000_000:
        raise RuntimeError('Réserve insuffisante pour la migration')
    old=sqlite3.connect(f'file:{source}?mode=ro',uri=True)
    new=sqlite3.connect(destination)
    started=time.time()
    try:
        new.execute('PRAGMA synchronous=FULL');create_schema(new)
        count=0
        for table in ('history','objects','responses','checkpoints','cycles'):
            for row in old.execute('SELECT * FROM '+table):
                if table=='history':
                    identity,kind,key,raw,at=row
                    content=save_content(new,raw.encode())
                    new.execute('INSERT INTO history_refs VALUES(?,?,?,?,?)',(identity,kind,key,content,at))
                elif table=='objects':
                    kind,key,raw,first,at=row
                    content=save_content(new,raw.encode())
                    new.execute('INSERT INTO object_refs VALUES(?,?,?,?,?)',(kind,key,content,first,at))
                    if kind=='trade':index_trade(new,key,json.loads(raw),first)
                elif table=='responses':
                    identity,source_url,params,status,body,at=row
                    content=save_content(new,zlib.decompress(body))
                    new.execute('INSERT INTO response_refs VALUES(?,?,?,?,?,?)',(identity,source_url,params,status,content,at))
                else:
                    new.execute('INSERT INTO '+table+' VALUES('+','.join('?' for _ in row)+')',row)
                count+=1
                if count%2000==0:
                    new.commit()
                    if capacity_check:capacity_check()
                    if shutil.disk_usage(destination.parent).free<min_free_bytes+50_000_000:
                        raise RuntimeError('Migration interrompue avant la réserve ; source intacte, cible partielle conservée')
            new.commit()
        if new.execute('PRAGMA integrity_check').fetchone()[0]!='ok' or new.execute('PRAGMA foreign_key_check').fetchall():
            raise RuntimeError('Intégrité de la cible refusée ; source intacte')
    finally:old.close();new.close()
    before,after=logical_digest(source),logical_digest(destination)
    if before!=after:raise RuntimeError('Empreintes logiques différentes ; aucune substitution autorisée')
    return {'started_at':started,'completed_at':time.time(),'identical':True,'tables':before,
            'source_bytes':source.stat().st_size,'destination_bytes':destination.stat().st_size}
