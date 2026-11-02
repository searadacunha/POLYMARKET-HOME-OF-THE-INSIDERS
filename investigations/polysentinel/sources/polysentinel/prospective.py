"""Local append-only decision evidence, with a budget shared with the legacy store.

No database writes or detector rules live here. A receipt records local persistence;
neither the clock nor the owner's ability to remove uchg is independently anchored.
"""
from contextlib import contextmanager
from collections import defaultdict
import fcntl
import gzip
import hashlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import re
import shutil
import stat
import time
import uuid

ZERO = '0' * 64
FORMAT = 'polysentinel-prospective-2'
RESERVE = 65_536
SMALL = 16_384
HASH = re.compile(r'^[0-9a-f]{64}$')
POLICY = dict(cap_bytes=20_000_000, min_free_bytes=12_000_000_000,
              max_segment_bytes=32_000_000, max_raw_segment_bytes=256_000_000,
              max_object_bytes=2_000_000)
SCATTERED_CHUNKS = (4, 16, 64)  # minimum rows, average rows (boundary modulus), maximum rows
# Configuration keys a maintenance release may change (explicit capacity decisions); every other key, and so
# every detector setting, must stay byte-for-byte equal in value.
CAPACITY_KEYS = {'config.json': {'data_quota_bytes'}, 'config/prospective.json': {'cap_bytes', 'authorization_reference'}}
FAILURE_EVENTS = 'capture_failure_events.jsonl'  # append-only details of every failed batch, sealed at the next append
RELEASE_FILES = {'polysentinel/'+name+'.py' for name in
                 ('__init__','engine','dashboard','prospective','prospective_bridge','prospective_ops')}


class Refusal(RuntimeError):
    pass


def encoded(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(',', ':'), allow_nan=False).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def file_digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for part in iter(lambda: stream.read(1 << 20), b''):
            h.update(part)
    return h.hexdigest()


def fsync_dir(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def seal(path):
    if not hasattr(os, 'chflags') or not hasattr(stat, 'UF_IMMUTABLE'):
        raise Refusal('macOS uchg required; no silent downgrade')
    path.chmod(0o400)
    os.chflags(path, path.stat().st_flags | stat.UF_IMMUTABLE)
    if not sealed(path):
        raise Refusal('File sealing failed')
    with path.open('rb') as stream:
        os.fsync(stream.fileno())


def sealed(path):
    info = path.stat()
    return not path.is_symlink() and not info.st_mode & 0o222 and bool(info.st_flags & stat.UF_IMMUTABLE)


def accounted(path):
    if path.is_symlink():
        raise Refusal('Symlink in budget perimeter: '+str(path))
    if not path.exists():
        return 0
    paths = [path] if path.is_file() else [path, *path.rglob('*')]
    total = 0
    for item in paths:
        if item.is_symlink():
            raise Refusal('Symlink in budget perimeter: '+str(item))
        info = item.stat()
        total += max(info.st_size, info.st_blocks * 512)
    return total


def json_file(path, limit=SMALL):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > limit:
        raise Refusal('Missing, unsafe or oversized file: '+str(path))
    try:
        return json.loads(path.read_bytes())
    except (ValueError, UnicodeError) as exc:
        raise Refusal('Invalid JSON: '+str(path)) from exc


def write_new(path, raw):
    with path.open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def atomic_small(path, value):
    raw = encoded(value)
    if len(raw) > SMALL:
        raise Refusal('State exceeds bounded size')
    temporary = path.with_suffix(path.suffix+'.pending')
    if path.is_symlink() or temporary.is_symlink():
        raise Refusal('Unsafe state path')
    with temporary.open('wb') as stream:
        stream.write(raw+b' '*(SMALL-len(raw)))
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    fsync_dir(path.parent)


class Journal:
    """One owner lock, immutable segments, rebuildable bounded checkpoints."""
    def __init__(self, root, policy=None, *, clock=time.time, fault=None, budget_check=None):
        self.root = Path(root).resolve()
        self.policy = dict(POLICY, **(policy or {}))
        if set(self.policy) != set(POLICY):
            raise Refusal('Unknown allocation policy field')
        if any(isinstance(v, bool) or not isinstance(v, int) or v <= 0 for v in self.policy.values()):
            raise Refusal('Allocation values must be positive integer bytes')
        if self.policy['min_free_bytes'] < 12_000_000_000:
            raise Refusal('Common 12 GB floor cannot be lowered')
        self.out = self.root/'evidence/prospective_v2'
        self.legacy = self.root/'evidence/prospective_eval'
        self.clock, self.fault = clock, fault or (lambda stage: None)
        self.budget_check = budget_check or self._external_capacity
        self._reserve_common = budget_check is None
        self._guard_module = None
        self.objects, self.observations, self.frames = {}, {}, {}
        self.source_committed=set();self.alert_keys=set();self.case_ids=set()
        self.state = dict(sequence=-1, head_sha256=ZERO, observation_count=0,
                          last_observed_at=None, last_sealed_at=None, source_cursor=None)
        self.checked = {}

    def _paths(self):
        return (self.legacy, self.out, self.root/'evidence/prospective_monitor',
                self.root/'evidence/prospective_recovery_20261030',
                self.root/'evidence/prospective_deployment_20261030',
                self.root/'evidence/detection_prospective_20261030/latest_status.json',
                self.root/'evidence/prospective_v2_status.json',
                self.root/'evidence/prospective_v2_status.json.pending',
                self.root/'config/prospective.json')

    def used_bytes(self):
        return sum(accounted(p) for p in self._paths())

    def _external_capacity(self, extra):
        config = json_file(self.root/'config.json', 1_000_000)
        reserve = 3*config.get('response_max_bytes',8_000_000)+36_000_000
        floor = max(self.policy['min_free_bytes'], config['min_free_bytes']+reserve)
        if shutil.disk_usage(self.root).free-extra < floor:
            raise Refusal('Disk floor would be crossed')
        used = 0
        for folder, dirs, files in os.walk(self.root, followlinks=False):
            dirs[:] = [d for d in dirs if d not in ('.git','.venv') and not (Path(folder)/d).is_symlink()]
            for name in files:
                path = Path(folder)/name
                if not path.is_symlink():
                    try:
                        info=path.stat();used+=max(info.st_size,info.st_blocks*512)
                    except FileNotFoundError:
                        continue
        if used+extra+reserve >= config['data_quota_bytes']:
            raise Refusal('Existing project quota would be crossed')

    def _capacity(self, extra):
        if self.used_bytes()+extra+RESERVE > self.policy['cap_bytes']:
            raise Refusal('Global prospective cap reached; no deletion or cursor advance')
        self.budget_check(extra+RESERVE)

    def _common_guard(self):
        if self._guard_module is None:
            path=Path.home()/'.local/lib/disk-guard/diskguard.py'
            if not path.is_file() or path.is_symlink():raise Refusal('Common disk guard unavailable')
            spec=importlib.util.spec_from_file_location('polysentinel_common_diskguard',path)
            guard=importlib.util.module_from_spec(spec)
            spec.loader.exec_module(guard)
            if guard.STATE.resolve()!=(Path.home()/'.local/state/disk-guard').resolve():
                raise Refusal('Common disk guard uses a different reservation state')
            self._guard_module=guard
        return self._guard_module

    @contextmanager
    def _reserved_write(self, extra):
        self._capacity(extra)
        if not self._reserve_common:
            yield
            return
        guard=self._common_guard()
        cfg=guard.config()
        # Sealing keeps its own 12 GB floor; the higher common floor of other operations (13.5 GB since 31/10)
        # leaves this band free for alerts.
        cfg['floor_bytes']=self.policy['min_free_bytes']
        reservation,info=guard.reserve(cfg,guard.STATE,extra+RESERVE,'PolySentinel prospective sealing',
                                       owners=[guard.owner(os.getpid())])
        if reservation is None:raise Refusal('Common disk guard refused reservation: '+str(info))
        failure=None
        try:
            yield
        except BaseException as exc:
            failure=exc
            raise
        finally:
            try:
                if not guard.release(guard.STATE,reservation):
                    raise Refusal('Reservation disappeared before release')
            except Exception as exc:
                detail='' if failure is None else '; write failure: '+str(failure)
                raise Refusal('Common disk reservation release failed: '+str(exc)+detail) from exc

    @contextmanager
    def _lock(self):
        for path in (self.root/'evidence',self.out):
            if path.is_symlink():
                raise Refusal('Unsafe journal directory')
        self.out.mkdir(parents=True,exist_ok=True)
        path = self.out/'.lock'
        if path.is_symlink():
            raise Refusal('Unsafe journal lock')
        with path.open('a') as stream:
            fcntl.flock(stream,fcntl.LOCK_EX)
            yield

    def _now(self):
        now = self.clock()
        if isinstance(now,bool) or not isinstance(now,(int,float)) or not math.isfinite(now):
            raise Refusal('Invalid local clock')
        if self.state.get('last_sealed_at') is not None and now < self.state['last_sealed_at']:
            raise Refusal('Local clock moved backwards')
        return now

    def _legacy_check(self, anchor):
        if not isinstance(anchor,dict) or not HASH.fullmatch(str(anchor.get('state_sha256',''))):
            raise Refusal('Explicit legacy anchor required')
        state = json_file(self.legacy/'state.json',1_000_000)
        if file_digest(self.legacy/'state.json') != anchor['state_sha256']:
            raise Refusal('Legacy checkpoint differs from approved anchor')
        for key in ('head_sha256','sequence','cursor','epoch'):
            if anchor.get(key) != state.get(key):
                raise Refusal('Legacy anchor mismatch: '+key)
        receipt = self.legacy/f"{state['sequence']:08d}"/'receipt.json'
        if file_digest(receipt) != state['head_sha256'] or not sealed(receipt):
            raise Refusal('Legacy head receipt is invalid or unsealed')
        return state

    def _pack(self, frame, records, origin, bundle=None, failure_events=()):
        with io.BytesIO() as compressed:
            with gzip.GzipFile(fileobj=compressed,mode='wb',mtime=0) as stream:
                added,obs,frame_id,bundle_id,raw_total=self._pack_objects(stream,compressed,frame,records,origin,bundle,failure_events)
            raw=compressed.getvalue()
        if len(raw)>self.policy['max_segment_bytes']:raise Refusal('Compressed segment limit reached')
        return raw,added,obs,frame_id,bundle_id,raw_total

    def _pack_objects(self, stream, compressed, frame, records, origin, bundle, failure_events=()):
        added=[];local=set();raw_total=0
        def put(value):
            nonlocal raw_total
            raw=encoded(value)
            if len(raw)>self.policy['max_object_bytes']:
                raise Refusal('Evidence object exceeds bounded size')
            key=digest(raw)
            if key in self.objects or key in local:return key
            line=key.encode()+b' '+raw+b'\n';raw_total+=len(line)
            if raw_total>self.policy['max_raw_segment_bytes']:
                raise Refusal('Uncompressed segment limit reached')
            stream.write(line)
            if compressed.tell()>self.policy['max_segment_bytes']:
                raise Refusal('Compressed segment limit reached')
            added.append(key);local.add(key)
            return key
        def chunks(values, minimum=16, average=128, maximum=256):
            result=[];chunk=[];size=0
            for value in values:
                raw=encoded(value)
                if len(raw)+128>self.policy['max_object_bytes']:
                    raise Refusal('A decision row exceeds object limit')
                if chunk and (size+len(raw)>min(524288,self.policy['max_object_bytes']-128) or len(chunk)>=maximum):
                    result.append(put(dict(type='rows',values=chunk)));chunk=[];size=0
                chunk.append(value);size+=len(raw)+1
                identity=(str(value.get('id',''))+'|'+str(value.get('observed_at',''))) if isinstance(value,dict) else str(value[0]) if isinstance(value,list) and value else digest(raw)
                if len(chunk)>=minimum and int(hashlib.sha256(identity.encode()).hexdigest()[:8],16)%average==0:
                    result.append(put(dict(type='rows',values=chunk)));chunk=[];size=0
            if chunk:result.append(put(dict(type='rows',values=chunk)))
            return result
        frame_id=None;bundle_id=None
        if bundle is not None:
            if not isinstance(bundle,dict) or not all(isinstance(k,str) and isinstance(v,str) for k,v in bundle.items()):
                raise Refusal('Source bundle must map names to UTF-8 text')
            bundle_id=put(dict(type='source_bundle',files=bundle))
        if frame is not None:
            if not isinstance(frame,dict) or not all(k in frame for k in ('now','config','trades','markets','events','wallet_history','source_version')):
                raise Refusal('Incomplete exact decision frame')
            if not all(isinstance(frame[k],list) for k in ('trades','markets','events')) or not isinstance(frame['wallet_history'],dict):
                raise Refusal('Invalid decision frame collections')
            bundle=self._get_objects([self.state['source_bundle_id']])[self.state['source_bundle_id']]
            versions={path:digest(text.encode()) for path,text in bundle['files'].items()}
            if frame['source_version']!=versions:
                raise Refusal('Decision frame source version differs from activated bundle')
            # Trades and wallet histories change in scattered rows: small chunks re-store fewer unchanged rows
            # (measured 31/10 on 133 real frames: -41 % bytes). Readers only concatenate chunks.
            lists={k:chunks(frame[k],*SCATTERED_CHUNKS) if k=='trades' else chunks(frame[k]) for k in ('trades','markets','events')}
            wallet=chunks([[k,v] for k,v in frame['wallet_history'].items()],*SCATTERED_CHUNKS)
            scalars={k:v for k,v in frame.items() if k not in ('trades','markets','events','wallet_history')}
            frame_id=put(dict(type='decision_frame',lists=lists,wallet_history=wallet,scalars=scalars))
        obs=[]
        for record in records:
            value=dict(type='observation',record=record,frame_id=frame_id,origin=origin)
            key=put(value);obs.append(dict(id=record['id'],object_sha256=key,kind=record['kind'],observed_at=record.get('observed_at')))
        for entry in failure_events:
            put(dict(entry,type='capture_failure_event'))
        return added,obs,frame_id,bundle_id,raw_total

    def _pending_failure_events(self):
        """Details of the failures since the last sealed counter: the exact rolling chain, walked back from the
        current counter. Orphans of a crash and torn lines are ignored; an incomplete chain seals nothing."""
        path=self.out/FAILURE_EVENTS
        start=self.state.get('sealed_failure_metadata',{}).get('rolling_sha256',ZERO)
        target=self._failure_metadata()['rolling_sha256']
        if target==start or not path.exists():return []
        by_rolling={}
        with path.open('rb') as stream:
            for line in stream:
                try:entry=json.loads(line)
                except ValueError:continue
                if isinstance(entry,dict):by_rolling[entry.get('rolling_sha256')]=entry
        chain=[];link=target
        while link!=start:
            entry=by_rolling.get(link)
            if entry is None or len(chain)>=1000:return []
            chain.append(entry);link=entry.get('previous_rolling_sha256')
        return chain[::-1]

    def _check_failure_events(self, events, previous, manifest):
        """A segment carries either no failure details or the exact chain from the previous counter to its own."""
        target=manifest.get('capture_failures',{}).get('rolling_sha256',previous)
        if not events:
            if target!=previous:self.state['failure_detail_gaps']=self.state.get('failure_detail_gaps',0)+1
            return
        link=previous
        for value in events:
            event=value.get('event') or {}
            omitted='details_omitted_bytes' in value
            if (value.get('previous_rolling_sha256')!=link or value.get('rolling_sha256')!=digest(encoded([link,event]))
                    or (not omitted and event.get('details_sha256')!=digest(encoded(value.get('details'))))):
                raise Refusal('Sealed capture failure event breaks the failure chain')
            link=value['rolling_sha256']
        if link!=target:raise Refusal('Sealed capture failure events do not reach the sealed counter')
        self.state.update(failure_events_sealed=self.state.get('failure_events_sealed',0)+len(events),
                          failed_attempts_with_details=self.state.get('failed_attempts_with_details',0)
                          +sum(v['event']['count'] for v in events))

    def _objects_in(self, path):
        if path.stat().st_size>self.policy['max_segment_bytes']:
            raise Refusal('Oversized compressed segment')
        total=0
        try:
            with gzip.open(path,'rb') as stream:
                while True:
                    line=stream.readline(self.policy['max_object_bytes']+67)
                    if not line:break
                    total+=len(line)
                    if len(line)>self.policy['max_object_bytes']+66 or not line.endswith(b'\n') or total>self.policy['max_raw_segment_bytes']:
                        raise Refusal('Oversized or truncated object stream')
                    key,raw=line[:64].decode('ascii'),line[65:-1]
                    if line[64:65]!=b' ' or not HASH.fullmatch(key) or digest(raw)!=key:
                        raise Refusal('Content hash mismatch')
                    value=json.loads(raw)
                    if encoded(value)!=raw:raise Refusal('Noncanonical content')
                    yield key,value
        except (OSError,ValueError,UnicodeError,EOFError) as exc:
            raise Refusal('Corrupt compressed evidence') from exc

    def _header(self, folder, sequence, previous, require_receipt=True):
        names={p.name for p in folder.iterdir()}
        expected={'objects.jsonl.gz','manifest.json','receipt.json'} if require_receipt else {'objects.jsonl.gz','manifest.json'}
        if folder.is_symlink() or names!=expected:
            raise Refusal('Incomplete or unexpected segment files: '+folder.name)
        for name in expected:
            if not sealed(folder/name):raise Refusal('Unsealed segment file: '+name)
        manifest=json_file(folder/'manifest.json',4_000_000)
        if manifest.get('format')!=FORMAT or manifest.get('sequence')!=sequence or manifest.get('previous_sha256')!=previous:
            raise Refusal('Segment sequence/hash chain mismatch')
        if manifest['objects_sha256']!=file_digest(folder/'objects.jsonl.gz'):
            raise Refusal('Compressed payload hash mismatch')
        if require_receipt:
            receipt=json_file(folder/'receipt.json')
            if receipt['manifest_sha256']!=file_digest(folder/'manifest.json') or receipt['sequence']!=sequence:
                raise Refusal('Receipt hash mismatch')
            if not manifest['prepared_at']<=receipt['published_at']<=receipt['sealed_at']:
                raise Refusal('Invalid local chronology')
            return manifest,receipt
        return manifest,None

    def _receipt(self, folder, manifest, recovered=False):
        published=self._now()
        fsync_dir(self.out)
        receipt=dict(format=FORMAT,sequence=manifest['sequence'],manifest_sha256=file_digest(folder/'manifest.json'),
                     published_at=published,sealed_at=self._now(),recovered_publication=recovered,
                     external_anchor=False,meaning='payload and manifest already immutable; local publication receipt follows')
        write_new(folder/'receipt.json',encoded(receipt));seal(folder/'receipt.json');fsync_dir(folder)
        return receipt

    def _recover(self):
        pending=self.out/'.pending'
        folders=sorted(p for p in self.out.iterdir() if p.name.isdigit())
        unfinished=folders and (not (folders[-1]/'receipt.json').exists() or not sealed(folders[-1]/'receipt.json'))
        if not pending.exists() and not unfinished:return
        with self._reserved_write(4*SMALL):
            if pending.exists():
                names={p.name for p in pending.iterdir()}
                if names=={'objects.jsonl.gz','manifest.json'} and all(sealed(pending/n) for n in names):
                    manifest,_=self._header(pending,self.state['sequence']+1,self.state['head_sha256'],False)
                    target=self.out/f"{manifest['sequence']:08d}"
                    if target.exists():raise Refusal('Conflicting pending sequence')
                    os.rename(pending,target);fsync_dir(self.out);self._receipt(target,manifest,True)
                else:
                    quarantine=self.out/('quarantine-'+uuid.uuid4().hex)
                    os.rename(pending,quarantine);fsync_dir(self.out)
                    self.state['recovery_warning']='Incomplete unpublished write retained in '+quarantine.name
            folders=sorted(p for p in self.out.iterdir() if p.name.isdigit())
            if folders and (not (folders[-1]/'receipt.json').exists() or not sealed(folders[-1]/'receipt.json')):
                folder=folders[-1];seq=int(folder.name)
                partial=folder/'receipt.json'
                if partial.exists() or partial.is_symlink():
                    # An unpublished receipt never asserts an earlier durable seal.
                    # Retain even an incomplete receipt outside the sealed segment.
                    if partial.is_symlink():raise Refusal('Unsafe partial receipt')
                    quarantine=self.out/('quarantine-'+uuid.uuid4().hex)
                    quarantine.mkdir();os.rename(partial,quarantine/'receipt.pending')
                    fsync_dir(folder);fsync_dir(quarantine);fsync_dir(self.out)
                    self.state['recovery_warning']='Unpublished receipt retained in '+quarantine.name
                manifest,_=self._header(folder,seq,self.state['head_sha256'],False)
                if seq!=self.state['sequence']+1:raise Refusal('Unreceipted segment is not the next sequence')
                self._receipt(folder,manifest,True)

    def _refresh(self, verify_all=False):
        if verify_all:
            self.objects={};self.observations={};self.frames={};self.checked={}
            self.source_committed=set();self.alert_keys=set();self.case_ids=set()
            self.state=dict(sequence=-1,head_sha256=ZERO,observation_count=0,last_observed_at=None,last_sealed_at=None,source_cursor=None)
        folders=sorted(p for p in self.out.iterdir() if p.name.isdigit())
        if len(folders)<self.state['sequence']+1:raise Refusal('Sealed tail disappeared')
        incomplete=False
        for i,folder in enumerate(folders):
            if folder.name!=f'{i:08d}':raise Refusal('Missing segment')
            if not (folder/'receipt.json').exists() or not sealed(folder/'receipt.json'):
                if i<=self.state['sequence'] or i!=len(folders)-1:
                    raise Refusal('Previously verified receipt disappeared or lost its seal')
                checkpoint=self.out/'state.json'
                if checkpoint.exists() and json_file(checkpoint).get('sequence',-1)>=i:
                    raise Refusal('Acknowledged receipt disappeared or lost its seal')
                incomplete=True  # recovery receipts it first; the allocation check waits for a complete chain
                break
            signature=tuple((name,(folder/name).stat().st_size,(folder/name).stat().st_mtime_ns,(folder/name).stat().st_ino,(folder/name).stat().st_mode,(folder/name).stat().st_flags) for name in ('manifest.json','objects.jsonl.gz','receipt.json'))
            if i<=self.state['sequence']:
                if self.checked.get(i)!=signature:raise Refusal('Previously verified sealed segment changed')
                continue
            manifest,receipt=self._header(folder,i,self.state['head_sha256'])
            found=[];failure_events=[]
            values={}
            needed={x['object_sha256'] for x in manifest['observations']}
            for key,value in self._objects_in(folder/'objects.jsonl.gz'):
                if key in self.objects:raise Refusal('Duplicate packed object')
                self.objects[key]=i;found.append(key)
                if key in needed:values[key]=value
                if value.get('type')=='decision_frame':
                    refs=[h for hs in value['lists'].values() for h in hs]+value['wallet_history']
                    if any(h not in self.objects for h in refs):raise Refusal('Frame chunk missing')
                    self.frames[key]=i
                elif value.get('type')=='capture_failure_event':
                    failure_events.append(value)
            if found!=manifest['objects']:raise Refusal('Object manifest differs from compressed content')
            if manifest['kind']=='init':
                if i!=0:raise Refusal('Duplicate activation')
                self.state['policy']=manifest['policy']  # compared with the configured allocation after the chain
                self._legacy_check(manifest['legacy_anchor'])
                if manifest['source_bundle_id'] not in self.objects:raise Refusal('Source bundle missing')
                self.state.update(activated_at=manifest['prepared_at'],legacy_anchor=manifest['legacy_anchor'],source_bundle_id=manifest['source_bundle_id'],epoch=manifest['epoch'])
            elif i==0:raise Refusal('Activation segment missing')
            elif manifest['kind']=='release':
                if manifest['observations'] or manifest['frame_id'] is not None or manifest['source_cursor'] is not None:
                    raise Refusal('Release cannot contain observations or advance the source cursor')
                previous=manifest['previous_source_bundle_id']
                if previous!=self.state['source_bundle_id']:
                    raise Refusal('Release predecessor differs from active source bundle')
                policy=self._amended_policy(self._check_release(previous,manifest['source_bundle_id'],manifest['release_reason']))
                if manifest.get('policy',self.state['policy'])!=policy:
                    raise Refusal('Release allocation differs from its sealed configuration')
                self.state['policy']=policy
                self.state.update(source_bundle_id=manifest['source_bundle_id'],previous_source_bundle_id=previous,
                                  source_release_sequence=i,source_release_reason=manifest['release_reason'])
            elif manifest['kind']!='data':raise Refusal('Unknown segment kind')
            failures=manifest.get('capture_failures',{'count':0,'rolling_sha256':ZERO})
            if failures['count']<self.state.get('capture_failure_count',0):
                raise Refusal('Sealed capture failure counter regressed')
            self._check_failure_events(failure_events,self.state.get('sealed_failure_metadata',{}).get('rolling_sha256',ZERO),manifest)
            self.state.update(capture_failure_count=failures['count'],sealed_failure_metadata=failures)
            for item in manifest['observations']:
                if item['id'] in self.observations:raise Refusal('Duplicate observation identity')
                value=values.get(item['object_sha256'])
                if value is None:value=self._get_objects([item['object_sha256']])[item['object_sha256']]
                if value.get('type')!='observation' or value['record']['id']!=item['id'] or value['record']['kind']!=item['kind']:
                    raise Refusal('Observation identity mismatch')
                frame_id=value.get('frame_id')
                if frame_id is not None and frame_id not in self.frames:raise Refusal('Decision frame missing')
                self.observations[item['id']]=dict(item,sequence=i,origin=value['origin'],sealed_at=receipt['sealed_at'])
                if item['kind']=='alert':
                    self.state['observation_count']+=1
                    self.state['last_observed_at']=max(self.state['last_observed_at'] or 0,item['observed_at'])
                    self.state['last_alert_sealed_at']=receipt['sealed_at']
                    self.alert_keys.add(value['record'].get('key',item['id']))
                    case_id=value['record']['payload'].get('id')
                    if isinstance(case_id,str) and case_id:self.case_ids.add(case_id)
                    else:self.state['observations_missing_case_id']=self.state.get('observations_missing_case_id',0)+1
                    if value['record'].get('source_commit_status')=='verified_at_backfill':self.source_committed.add(item['id'])
                elif item['kind']=='commit_confirmation':
                    ids=value['record']['source_ids']
                    if any(x not in self.observations or self.observations[x]['kind']!='alert' for x in ids):
                        raise Refusal('Commit confirmation references missing source alert')
                    self.source_committed.update(ids)
            if manifest.get('source_cursor') is not None:
                if self.state.get('source_cursor') is not None and manifest['source_cursor']<self.state['source_cursor']:
                    raise Refusal('Source cursor moved backwards')
                self.state['source_cursor']=manifest['source_cursor']
            self.state.update(sequence=i,head_sha256=file_digest(folder/'receipt.json'),last_sealed_at=receipt['sealed_at'])
            self.state.update(distinct_alert_keys=len(self.alert_keys),
                              distinct_source_keys=len(self.alert_keys),distinct_cases=len(self.case_ids),
                              observations_missing_case_id=self.state.get('observations_missing_case_id',0),
                              repeat_observations=None if self.state.get('observations_missing_case_id',0) else self.state['observation_count']-len(self.case_ids),
                              source_commit_confirmed_count=len(self.source_committed),
                              source_commit_unconfirmed_count=self.state['observation_count']-len(self.source_committed))
            self.checked[i]=signature
        if not incomplete and self.state.get('policy') is not None and self.state['policy']!=self.policy:
            raise Refusal('Allocation differs from activated epoch')

    def _get_objects(self, keys):
        wanted=set(keys);by_segment=defaultdict(set)
        for key in wanted:
            if key not in self.objects:raise Refusal('Referenced content missing: '+key)
            by_segment[self.objects[key]].add(key)
        result={}
        for seq,selected in by_segment.items():
            for key,value in self._objects_in(self.out/f'{seq:08d}'/'objects.jsonl.gz'):
                if key in selected:result[key]=value
        if result.keys()!=wanted:raise Refusal('Referenced content unavailable')
        return result

    def _state_write(self, error=None):
        metadata=self._failure_metadata()
        state=dict(self.state,format=FORMAT,updated_at=self.clock(),cap_bytes=self.policy['cap_bytes'],
                   used_bytes=self.used_bytes(),error=error,continuity='blocked' if error else 'local_chain_intact')
        state.update(self._failure_status(metadata))
        if metadata['count'] and not error:state['continuity']='local_chain_intact_with_capture_failures'
        state['remaining_bytes']=state['cap_bytes']-state['used_bytes']
        self._small_write(self.out/'state.json',state)
        # The first checkpoint allocates a physical block; subsequent replacements
        # have the same padded size. Include that first allocation in the status.
        state['used_bytes']=self.used_bytes()
        state['remaining_bytes']=state['cap_bytes']-state['used_bytes']
        self._small_write(self.out/'state.json',state)
        return state

    def _small_write(self, path, value):
        """Health writes consume reserved space, never expand the global cap."""
        if len(encoded(value))>SMALL:raise Refusal('Bounded status/metadata exceeds size limit')
        if self.used_bytes()+SMALL>self.policy['cap_bytes']:
            raise Refusal('No reserved capacity remains to persist health/failure metadata')
        atomic_small(path,value)

    def _failure_metadata(self):
        sealed_metadata=self.state.get('sealed_failure_metadata',{'count':0,'rolling_sha256':ZERO})
        path=self.out/'capture_failures.json'
        metadata=json_file(path) if path.exists() else sealed_metadata
        count=metadata.get('count')
        if isinstance(count,bool) or not isinstance(count,int) or count<sealed_metadata['count'] or not HASH.fullmatch(str(metadata.get('rolling_sha256',''))):
            raise Refusal('Missing, corrupt or regressed capture failure metadata')
        checkpoint=self.out/'state.json'
        if checkpoint.exists() and json_file(checkpoint).get('capture_failure_count',0)>count:
            raise Refusal('Unsealed capture failure metadata disappeared; count is unknown')
        return metadata

    def _failure_status(self, metadata):
        sealed_metadata=self.state.get('sealed_failure_metadata',{'count':0,'rolling_sha256':ZERO})
        return dict(capture_failure_count=metadata['count'],
                    capture_failure_first_at=metadata.get('first_calculated_at'),
                    capture_failure_last_at=metadata.get('last_calculated_at'),
                    capture_failure_metadata_sha256=digest(encoded(metadata)),
                    failure_metadata_unsealed=metadata['rolling_sha256']!=sealed_metadata['rolling_sha256'],
                    failure_metadata_missing=bool(metadata['count'] and not (self.out/'capture_failures.json').exists()))

    def record_failure(self, count, calculated_at, details):
        """Persist a lower bound of failed captures; does not fabricate their inputs.

        Explicit caller responsibility: invoke once per failed live capture, not
        for a post-seal DB error or a repeated attempt at the same failed batch.
        """
        with self._lock():
            self._refresh()
            if isinstance(count,bool) or not isinstance(count,int) or count<=0:
                raise Refusal('Capture failure count must be a positive integer')
            now=self._now()
            if isinstance(calculated_at,bool) or not isinstance(calculated_at,(int,float)) or not math.isfinite(calculated_at) or calculated_at>now:
                raise Refusal('Invalid failed-decision time')
            previous=self._failure_metadata();raw=encoded(details)
            event=dict(count=count,calculated_at=calculated_at,recorded_at=now,details_sha256=digest(raw))
            entry=encoded(dict(previous_rolling_sha256=previous['rolling_sha256'],
                               rolling_sha256=digest(encoded([previous['rolling_sha256'],event])),event=event,details=details))
            if len(entry)>self.policy['max_object_bytes']//2:
                entry=encoded(dict(previous_rolling_sha256=previous['rolling_sha256'],
                                   rolling_sha256=digest(encoded([previous['rolling_sha256'],event])),event=event,
                                   details_omitted_bytes=len(raw)))
            if self.used_bytes()+len(entry)+2*SMALL>self.policy['cap_bytes']:
                raise Refusal('No reserved capacity remains to persist health/failure metadata')
            events=self.out/FAILURE_EVENTS
            with events.open('ab') as stream:  # written before the counter: never a count without details
                if stream.tell() and events.read_bytes()[-1:]!=b'\n':stream.write(b'\n')  # close a line torn by a crash
                stream.write(entry+b'\n');stream.flush();os.fsync(stream.fileno())
            metadata=dict(count=previous['count']+count,
                          first_calculated_at=min(previous.get('first_calculated_at',calculated_at),calculated_at),
                          last_calculated_at=max(previous.get('last_calculated_at',calculated_at),calculated_at),
                          first_recorded_at=previous.get('first_recorded_at',now),last_recorded_at=now,
                          previous_sha256=previous['rolling_sha256'],
                          rolling_sha256=digest(encoded([previous['rolling_sha256'],event])),
                          last_failure=event,
                          last_details=details if len(raw)<=4096 else {'details_omitted_bytes':len(raw)})
            self._small_write(self.out/'capture_failures.json',metadata)
            self._state_write('Live captures failed; evidence for these decisions is incomplete')
            return self._failure_status(metadata)

    def write_status(self, value):
        """Serialize the bounded dashboard cache with every archive writer."""
        with self._lock():
            path=self.root/'evidence/prospective_v2_status.json'
            self._small_write(path,value)
            return dict(path=str(path),used_bytes=self.used_bytes(),cap_bytes=self.policy['cap_bytes'])

    def _append(self, records, frame, origin, source_cursor, kind='data', legacy_anchor=None, source_bundle=None,
                release_reason=None, release_policy=None):
        self._refresh();self._recover();self._refresh()
        if kind!='init' and self.state['sequence']<0:raise Refusal('Journal not initialized')
        current=self.state.get('source_cursor')
        if source_cursor is not None and (isinstance(source_cursor,bool) or not isinstance(source_cursor,int) or source_cursor<0 or (current is not None and source_cursor<current)):
            raise Refusal('Invalid or backwards source cursor')
        if not records and kind=='data' and (origin!='backfill' or frame is not None or source_cursor is None or (current is not None and source_cursor<=current)):
            raise Refusal('Empty append requires a strictly advancing backfill cursor')
        now=self._now();ids=set()
        for record in records:
            if not isinstance(record,dict) or not isinstance(record.get('id'),str) or not record['id'] or len(record['id'])>256 or record['id'] in ids:
                raise Refusal('Missing or duplicate observation identity in batch')
            ids.add(record['id'])
            if record.get('kind') not in ('alert','commit_confirmation'):raise Refusal('Unsupported record kind')
            at=record.get('observed_at')
            if isinstance(at,bool) or not isinstance(at,(float,int)) or not math.isfinite(at) or at>now:
                raise Refusal('Invalid or future source observation time')
            if record['kind']=='alert':
                if not isinstance(record.get('payload'),dict) or digest(encoded(record['payload']))!=record.get('content_id'):
                    raise Refusal('Source alert content hash mismatch')
                if origin=='live_decision' and (frame is None or at<self.state.get('activated_at',now)):
                    raise Refusal('Live alert requires contemporaneous decision frame')
        raw,objects,observations,frame_id,bundle_id,raw_size=self._pack(frame,records,origin,source_bundle,
                                                                         self._pending_failure_events())
        existing=[x for x in observations if x['id'] in self.observations]
        for item in existing:
            if self.observations[item['id']]['object_sha256']!=item['object_sha256']:
                raise Refusal('Conflicting reuse of observation ID')
        if existing:
            if len(existing)!=len(records):raise Refusal('Mixed committed/new batch; retry only uncommitted IDs')
            return dict(status='already_sealed',ids=[r['id'] for r in records],frame_id=frame_id,
                        receipts=[self.observations[r['id']] for r in records])
        sequence=self.state['sequence']+1
        manifest=dict(format=FORMAT,kind=kind,sequence=sequence,previous_sha256=self.state['head_sha256'],
            prepared_at=now,objects=objects,objects_sha256=digest(raw),raw_object_bytes=raw_size,
            observations=observations,frame_id=frame_id,source_cursor=source_cursor,
            capture_failures=self._failure_metadata())
        if kind=='init':
            manifest.update(policy=self.policy,legacy_anchor=legacy_anchor,source_bundle_id=bundle_id,epoch=str(uuid.uuid4()))
        elif kind=='release':
            manifest.update(source_bundle_id=bundle_id,previous_source_bundle_id=self.state['source_bundle_id'],
                            release_reason=release_reason)
            if release_policy is not None:manifest.update(policy=release_policy)
        body=encoded(manifest)
        if len(body)>4_000_000:raise Refusal('Manifest exceeds bounded size')
        if len(raw)+len(body)+SMALL>self.policy['max_segment_bytes']:
            raise Refusal('Complete segment exceeds bounded size')
        with self._reserved_write(len(raw)+len(body)+4*SMALL):
            pending=self.out/'.pending'
            pending.mkdir()
            write_new(pending/'objects.jsonl.gz',raw);self.fault('after_payload_write')
            seal(pending/'objects.jsonl.gz')
            write_new(pending/'manifest.json',body);seal(pending/'manifest.json');fsync_dir(pending)
            self.fault('after_pending_complete')
            final=self.out/f'{sequence:08d}'
            os.rename(pending,final);fsync_dir(self.out);self.fault('after_publish')
            if release_policy is not None:self.policy=release_policy  # the sealed amendment is now the allocation
            receipt=self._receipt(final,manifest);self.fault('after_receipt')
            self._refresh();self._state_write();self.fault('after_checkpoint')
        return dict(status='sealed',ids=[r['id'] for r in records],sequence=sequence,
                    head_sha256=self.state['head_sha256'],sealed_at=receipt['sealed_at'],frame_id=frame_id)

    def init(self, legacy_anchor, source_bundle):
        with self._lock():
            self._refresh();self._recover();self._refresh()
            if self.state['sequence']>=0:
                if self.state['legacy_anchor']!=legacy_anchor:raise Refusal('Different legacy anchor')
                bundle=self._get_objects([self.state['source_bundle_id']])[self.state['source_bundle_id']]
                if bundle['files']!=source_bundle:raise Refusal('Different model/source bundle')
                return self._state_write()
            self._legacy_check(legacy_anchor)
            return self._append([],None,'activation',legacy_anchor['cursor'],'init',legacy_anchor,source_bundle)

    def _check_release(self, previous_id, next_id, reason, next_bundle=None):
        if not isinstance(reason,str) or not reason.strip() or len(reason)>1000:
            raise Refusal('Release requires a bounded, explicit reason')
        keys=[previous_id] if next_bundle is not None else [previous_id,next_id]
        bundles=self._get_objects(keys)
        previous=bundles[previous_id]
        following=next_bundle if next_bundle is not None else bundles[next_id]
        for bundle in (previous,following):
            if (bundle.get('type')!='source_bundle' or not isinstance(bundle.get('files'),dict)
                    or not all(isinstance(k,str) and isinstance(v,str) for k,v in bundle['files'].items())):
                raise Refusal('Invalid release source bundle')
        if set(previous['files'])!=set(following['files']):
            raise Refusal('Release cannot add or remove source/config files')
        changed={key for key in previous['files'] if previous['files'][key]!=following['files'][key]}
        # A maintenance release cannot silently replace the detector or its configuration.
        configuration=changed-RELEASE_FILES
        if not changed or configuration-set(CAPACITY_KEYS):
            raise Refusal('Release must change only prospective integration files')
        for name in configuration:
            try:old,new=json.loads(previous['files'][name]),json.loads(following['files'][name])
            except ValueError as exc:raise Refusal('Capacity release needs valid JSON: '+name) from exc
            if (not isinstance(old,dict) or not isinstance(new,dict) or set(old)!=set(new)
                    or any(old[k]!=new[k] for k in old if k not in CAPACITY_KEYS[name])):
                raise Refusal('Release may change only capacity keys of '+name)
        allocation=following['files'].get('config/prospective.json')
        # Same derivation as prospective_bridge.journal: defaults, then the allocation's policy keys.
        return dict(POLICY,**{k:v for k,v in json.loads(allocation).items() if k in POLICY}) if allocation else None

    def _amended_policy(self, policy):
        """Active policy after a release: unchanged, or with only cap_bytes amended."""
        active=self.state['policy']
        if policy is None or policy==active:return active
        if {k for k in POLICY if policy.get(k)!=active[k]}-{'cap_bytes'}:
            raise Refusal('A release may amend only the prospective cap')
        if isinstance(policy['cap_bytes'],bool) or not isinstance(policy['cap_bytes'],int) or policy['cap_bytes']<=0:
            raise Refusal('Invalid amended cap')
        return policy

    def register_release(self, source_bundle, *, previous_bundle_id, reason):
        """Explicit compare-and-swap registration; never rewrites an earlier segment."""
        with self._lock():
            self._refresh();self._recover();self._refresh()
            if self.state['sequence']<0:raise Refusal('Journal not initialized')
            bundle=dict(type='source_bundle',files=source_bundle)
            identity=digest(encoded(bundle))
            if identity==self.state['source_bundle_id']:
                if (self.state.get('previous_source_bundle_id')==previous_bundle_id
                        and self.state.get('source_release_reason')==reason):
                    return dict(status='already_registered',source_bundle_id=identity,
                                sequence=self.state['source_release_sequence'])
                raise Refusal('Release already active with a different predecessor or reason')
            if previous_bundle_id!=self.state['source_bundle_id']:
                raise Refusal('Release predecessor differs from active source bundle')
            policy=self._amended_policy(self._check_release(previous_bundle_id,identity,reason,bundle))
            if policy!=self.state['policy'] and policy['cap_bytes']<self.used_bytes()+RESERVE:
                raise Refusal('Amended cap is below the bytes already used')
            return self._append([],None,'release',None,'release',source_bundle=source_bundle,release_reason=reason,
                                release_policy=None if policy==self.state['policy'] else policy)

    def append(self, records, frame=None, *, origin='live_decision', source_cursor=None):
        if origin not in ('live_decision','backfill','commit_confirmation'):
            raise Refusal('Unknown observation provenance')
        with self._lock():
            try:return self._append(records,frame,origin,source_cursor)
            except Exception as exc:
                self._state_write(str(exc)[:1000])
                raise

    def mark_source_commit(self, ids, observed_after_commit):
        ids=sorted(set(ids));identity='commit:'+digest(encoded(ids))
        with self._lock():
            self._refresh();self._recover();self._refresh()
            if not ids or any(i not in self.observations or self.observations[i]['kind']!='alert' for i in ids):
                raise Refusal('Cannot confirm unsealed source alert IDs')
            if identity in self.observations:
                return dict(status='already_sealed',ids=[identity],receipts=[self.observations[identity]])
            if observed_after_commit<max(self.observations[x]['sealed_at'] for x in ids):
                raise Refusal('Commit confirmation predates evidence sealing')
            record=dict(id=identity,kind='commit_confirmation',observed_at=observed_after_commit,
                        source_ids=ids,source_committed_observed_at=observed_after_commit,
                        meaning='durability observed after commit, not exact internal commit timestamp')
            try:return self._append([record],None,'commit_confirmation',None)
            except Exception as exc:
                self._state_write(str(exc)[:1000]);raise

    def source_versions(self):
        with self._lock():
            self._refresh()
            identity=self.state.get('source_bundle_id')
            if identity is None:raise Refusal('Journal not initialized')
            bundle=self._get_objects([identity])[identity]
            return {path:digest(text.encode()) for path,text in bundle['files'].items()}

    @property
    def confirmed_source_ids(self):
        """Snapshot refreshed by status/verify/append; do not mutate the return value."""
        return frozenset(self.source_committed)

    def verify(self):
        with self._lock():
            self._refresh(verify_all=True)
            if (self.out/'.pending').exists() or any(p.name.isdigit() and not (p/'receipt.json').exists() for p in self.out.iterdir()):
                raise Refusal('Unfinished publication; recover through init or append')
            if self.state['sequence']<0:raise Refusal('No activation evidence')
            self._legacy_check(self.state['legacy_anchor'])
            if self.used_bytes()>self.policy['cap_bytes']:raise Refusal('Global cap exceeded')
            return dict(self.state,used_bytes=self.used_bytes(),cap_bytes=self.policy['cap_bytes'],
                        records=len(self.observations),objects=len(self.objects),external_anchor=False,
                        **self._failure_status(self._failure_metadata()))

    def read_observation(self, identity):
        with self._lock():
            self._refresh()
            if identity not in self.observations:raise KeyError(identity)
            meta=self.observations[identity]
            return dict(self._get_objects([meta['object_sha256']])[meta['object_sha256']],receipt=meta,
                        source_commit_confirmed=identity in self.source_committed)

    def reconstruct_frame(self, identity):
        with self._lock():
            self._refresh()
            frame=self._get_objects([identity])[identity]
            if frame.get('type')!='decision_frame':raise Refusal('Object is not a decision frame')
            keys=[h for values in frame['lists'].values() for h in values]+frame['wallet_history']
            objects=self._get_objects(keys)
            result=dict(frame['scalars'])
            for name,values in frame['lists'].items():
                result[name]=[r for h in values for r in objects[h]['values']]
            result['wallet_history']=dict(r for h in frame['wallet_history'] for r in objects[h]['values'])
            return result

    def status(self):
        with self._lock():
            self._refresh()
            saved=json_file(self.out/'state.json') if (self.out/'state.json').exists() else {}
            used=self.used_bytes()
            return dict(self.state,cap_bytes=self.policy['cap_bytes'],used_bytes=used,
                        remaining_bytes=self.policy['cap_bytes']-used,error=saved.get('error'),
                        updated_at=saved.get('updated_at'),
                        continuity=saved.get('continuity','not_initialized'),
                        checkpoint_stale=saved.get('head_sha256')!=self.state['head_sha256'],
                        **self._failure_status(self._failure_metadata()))
