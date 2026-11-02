"""Decision-time capture and source publication; detection rules stay unchanged."""
import hashlib
import json
from pathlib import Path
import time

from .db import encode

_JOURNALS = {}

class PublicationFailure(RuntimeError):
    def __init__(self, message, decision_sealed):
        super().__init__(message)
        self.decision_sealed=decision_sealed

def runtime_source_version(root):
    from . import STARTUP_CODE_HASHES,_PACKAGE_DIRECTORY
    current={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(_PACKAGE_DIRECTORY.glob('*.py'))}
    if current!=STARTUP_CODE_HASHES:
        raise RuntimeError('Package changed since process startup; cold restart required')
    versions=source_version(root)
    archived={Path(k).name:v for k,v in versions.items() if k.startswith('polysentinel/')}
    if archived!=STARTUP_CODE_HASHES:
        raise RuntimeError('Requested source release differs from loaded process')
    return versions

def policy(root):
    path = Path(root)/'config/prospective.json'
    if not path.exists(): return None
    if path.is_symlink() or path.stat().st_size > 16384:
        raise RuntimeError('Invalid prospective allocation file')
    value = json.loads(path.read_text())
    if value.get('enabled') is not True: return None
    if not value.get('authorization_reference'):
        raise RuntimeError('Prospective allocation needs an explicit authorization reference')
    return value

def source_bundle(root):
    root=Path(root)
    paths=sorted((root/'polysentinel').glob('*.py'))+[root/'config.json']
    paths+=sorted((root/'config').glob('*.json'))
    result={}
    for path in paths:
        if path.is_symlink(): raise RuntimeError('Source symlink rejected')
        result[str(path.relative_to(root))]=path.read_text()
    return result

def source_version(root):
    return {name:hashlib.sha256(text.encode()).hexdigest() for name,text in source_bundle(root).items()}

def journal(root, allocation):
    from .prospective import Journal, POLICY
    key=(str(Path(root).resolve()),encode(allocation))
    if key not in _JOURNALS:
        _JOURNALS[key]=Journal(root,{k:v for k,v in allocation.items() if k in POLICY})
    return _JOURNALS[key]

def publish_cases(store, cases, frame, native_hashes, allocation):
    if not allocation:
        for case in cases:
            with store.transaction() as conn:
                store.put('case',case['id'],case,conn=conn)
                if case.get('priority'):
                    store.put('alert',case['id']+':'+str(time.time_ns()),case,conn=conn)
        return None
    if not cases: return None
    archive=journal(store.root,allocation)
    records=[]
    for case in cases:
        at=time.time()
        key=case['id']+':'+str(time.time_ns())
        raw=encode(case)
        identity=hashlib.sha256(encode(['alert',key,raw,at]).encode()).hexdigest()
        records.append(dict(id=identity,kind='alert',key=key,content_id=hashlib.sha256(raw.encode()).hexdigest(),
            observed_at=at,payload=case,first_observed_by_polysentinel_at=at,
            native_case_sha256=native_hashes[case['id']],source_commit_status='pending',
            source_committed_observed_at=None,original_decision_inputs='complete_arguments',
            detector_version=case.get('rule_version'),
            availability=dict(decision_arguments='retained_exactly',
                network_response_bodies='not_copied_or_rechecked; references retained where present',
                source_coverage='bounded source collection; not exhaustive',
                clock='local Mac clock; no independent timestamp authority'),
            observation_time_meaning='Producer observation assigned before source SQLite commit'))
    frame=dict(frame,source_version=runtime_source_version(store.root))
    try:
        receipt=archive.append(records,frame=frame,origin='live_decision')
    except Exception as exc:
        try:
            found=[archive.read_observation(r['id']) for r in records]
            already_sealed=all(encode(p['record'])==encode(r) for p,r in zip(found,records))
        except KeyError:
            already_sealed=False
        except Exception:
            already_sealed=None
        raise PublicationFailure(str(exc),decision_sealed=already_sealed) from exc
    try:
        with store.transaction() as conn:
            for case,record in zip(cases,records):
                store.put('case',case['id'],case,conn=conn)
                identity=store.put('alert',record['key'],case,observed_at=record['observed_at'],conn=conn)
                if identity!=record['id']: raise RuntimeError('Source identity differs from sealed observation')
    except Exception as exc:
        raise PublicationFailure(str(exc),decision_sealed=True) from exc
    try:
        archive.mark_source_commit([r['id'] for r in records],time.time())
    except Exception as exc:
        # The decision proof and SQLite commit survived; reconciliation can add this receipt later.
        try:
            store.health('prospective','degraded','Source committed; confirmation pending: '+str(exc),
                         source_ids=[r['id'] for r in records],decision_sealed=True)
        except Exception as health_error:
            raise PublicationFailure(str(health_error),decision_sealed=True) from health_error
        return dict(receipt,source_confirmation_pending=True)
    try:
        store.health('prospective','ok','Decision sealed and source commit confirmed',
                     source_ids=[r['id'] for r in records],decision_sealed=True)
    except Exception as exc:
        raise PublicationFailure(str(exc),decision_sealed=True) from exc
    return receipt

def dashboard_status(root):
    path=Path(root)/'evidence/prospective_v2_status.json'
    if not path.exists():
        return dict(state='unknown',detail='État prospectif V2 non disponible',pending_observations=None)
    if path.is_symlink() or path.stat().st_size>65536:
        return dict(state='error',detail='État prospectif invalide',pending_observations=None)
    try:
        value=json.loads(path.read_text())
        if not isinstance(value,dict): raise ValueError('Status is not an object')
        age=time.time()-value['checked_at']
        value['status_age_seconds']=age
        if age>180 or age< -5:
            value['state']='stale';value['detail']='État prospectif périmé ou horloge incohérente'
        return value
    except (ValueError,KeyError,TypeError,OSError) as exc:
        return dict(state='error',detail=str(exc),pending_observations=None)
