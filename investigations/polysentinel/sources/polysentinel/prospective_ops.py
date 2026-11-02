"""Bounded recovery and monitoring; source SQLite is opened query-only."""
import argparse
from contextlib import contextmanager
import hashlib
from itertools import islice
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import signal
import threading
import time
import zlib

from .db import encode
from .prospective import Journal, POLICY, RESERVE, Refusal, file_digest, json_file
from .prospective_bridge import policy, source_bundle, runtime_source_version

_VERIFICATION_WITNESSES = {}

def verification_witnesses(root):
    allocation=policy(root) or {}
    expected=allocation.get('verification_witness_sha256')
    if not expected:return {}
    path=Path(root)/'evidence/prospective_deployment_20261030/verification_witness.json'
    if path.is_symlink() or file_digest(path)!=expected:
        raise Refusal('Pre-deployment verification witness changed or unavailable')
    key=(str(Path(root).resolve()),expected)
    if key not in _VERIFICATION_WITNESSES:
        _VERIFICATION_WITNESSES[key]=json_file(path,2_000_000)['observations']
    return _VERIFICATION_WITNESSES[key]


def archive(root):
    allocation = policy(root)
    if allocation is None:
        raise Refusal('Prospective allocation is not enabled and authorized')
    return Journal(root, {key: allocation[key] for key in POLICY if key in allocation})


def legacy(root):
    path = Path(root)/'evidence/prospective_eval/state.json'
    state = json_file(path, 1_000_000)
    anchor = {key: state[key] for key in ('head_sha256', 'sequence', 'cursor', 'epoch')}
    anchor['state_sha256'] = file_digest(path)
    return state, anchor


@contextmanager
def source(root, original):
    path = Path(root)/'data/polysentinel.sqlite3'
    if path.is_symlink() or not path.is_file():
        raise Refusal('Source database missing or symlink')
    conn = sqlite3.connect(path.resolve().as_uri()+'?mode=ro', uri=True, timeout=2)
    conn.row_factory = sqlite3.Row
    deadline = time.monotonic()+5
    conn.set_progress_handler(lambda: int(time.monotonic() > deadline), 10000)
    try:
        conn.execute('PRAGMA query_only=ON')
        conn.execute('PRAGMA temp_store=MEMORY')
        if conn.execute('PRAGMA user_version').fetchone()[0] != 2:
            raise Refusal('Unsupported source schema')
        info = path.stat()
        schema = [tuple(row) for row in conn.execute('SELECT type,name,sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY type,name')]
        identity = dict(device=info.st_dev, inode=info.st_ino,
                        schema_sha256=hashlib.sha256(encode(schema).encode()).hexdigest())
        if identity != original['source_identity']:
            raise Refusal('Source database identity changed; manual continuity review required')
        row = conn.execute('SELECT rowid,id,kind,key,content_id,observed_at FROM history_refs WHERE rowid=?',
                           (original['cursor'],)).fetchone()
        if row is None or dict(row) != original['anchor']:
            raise Refusal('Legacy source cursor anchor changed or disappeared')
        if 'alert_count' in original:
            count = conn.execute("SELECT COUNT(*) FROM history_refs WHERE kind='alert' AND rowid<=?", (original['cursor'],)).fetchone()[0]
            if count != original['alert_count']:
                raise Refusal('Source observations before the legacy cursor changed')
        yield conn
    finally:
        conn.close()


def content(conn, identity):
    row = conn.execute('SELECT body,raw_bytes FROM contents WHERE id=?', (identity,)).fetchone()
    if row is None or not 0 <= row['raw_bytes'] <= 1_000_000:
        raise Refusal('Missing or oversized source content')
    inflater = zlib.decompressobj()
    raw = inflater.decompress(row['body'], 1_000_001)
    if not inflater.eof or inflater.unused_data or len(raw) != row['raw_bytes'] or hashlib.sha256(raw).hexdigest() != identity:
        raise Refusal('Source content hash, compression or length mismatch')
    value = json.loads(raw)
    if not isinstance(value, dict) or encode(value).encode() != raw:
        raise Refusal('Source payload is not a canonical object')
    return value, raw


def observation(conn, row):
    record = dict(row)
    value, raw = content(conn, record['content_id'])
    expected = hashlib.sha256(encode([record['kind'], record['key'], raw.decode(), record['observed_at']]).encode()).hexdigest()
    if expected != record['id']:
        raise Refusal('Source observation identity mismatch')
    record['payload'] = value
    return record


def inspect(root):
    original, anchor = legacy(root)
    with source(root, original) as conn:
        row = conn.execute("SELECT COUNT(*) n,MIN(observed_at) first,MAX(observed_at) last FROM history_refs WHERE kind='alert' AND rowid>?",
                           (original['cursor'],)).fetchone()
    return dict(checked_at=time.time(), legacy_anchor=anchor, pending_observations=row['n'],
                first_pending_observed_at=row['first'], last_pending_observed_at=row['last'],
                meaning='Source observations after legacy cursor; no new sealing performed')


def recover(root, journal=None, limit=25):
    if not 1 <= limit <= 25:
        raise Refusal('Recovery batch must contain 1 to 25 source observations')
    original, anchor = legacy(root)
    journal = journal or archive(root)
    with source(root, original): pass
    journal.init(anchor, source_bundle(root))
    state = journal.status()
    cursor = state.get('source_cursor')
    if cursor is None: cursor = original['cursor']
    records, confirmed = [], []
    witnesses=verification_witnesses(root)
    recovery_started_at = time.time()
    with source(root, original) as conn:
        rows = conn.execute("SELECT rowid,id,kind,key,content_id,observed_at FROM history_refs WHERE kind='alert' AND rowid>? ORDER BY rowid LIMIT ?",
                            (cursor, limit)).fetchall()
        for row in rows:
            record = observation(conn, row)
            if record['id'] in journal.observations:
                old = journal.read_observation(record['id'])['record']
                if any(old.get(key) != record[key] for key in ('kind', 'key', 'content_id', 'observed_at', 'payload')):
                    raise Refusal('Already sealed observation conflicts with source')
                if journal.observations[record['id']]['origin'] == 'live_decision':
                    confirmed.append(record['id'])
                continue
            recovered_at = time.time()
            witness=witnesses.get(record['id'])
            if witness and (witness['content_id']!=record['content_id'] or witness['source_observed_at']!=record['observed_at']):
                raise Refusal('Pre-deployment source verification conflicts with recovery')
            record.update(recovery_started_at=recovery_started_at, recovered_at=recovered_at,
                          source_committed_observed_at=recovered_at,
                          first_observed_by_polysentinel_at=record['observed_at'],
                          first_verifiable_observation_at=witness['verified_no_later_than'] if witness else recovered_at,
                          first_verification_basis=witness or dict(verified_no_later_than=recovered_at,
                              meaning='First documented integrity check in retained recovery evidence; not proof of historical sealing'),
                          source_commit_status='verified_at_backfill',
                          original_decision_inputs='not_retained',
                          availability='source_alert_payload_verified; original full decision frame absent',
                          chronology='Late recovery; source observed_at predates SQLite commit and is not a historical seal',
                          post_activation_capture_gap=record['observed_at'] >= state['activated_at'])
            records.append(record)
    receipt = journal.append(records, origin='backfill', source_cursor=rows[-1]['rowid']) if rows else None
    # A crash after source commit may precede the confirmation or cursor update.
    confirmed_source_ids = journal.confirmed_source_ids
    observation_ids = tuple(journal.observations)
    confirmation_deadline = time.monotonic()+5
    def unconfirmed_ids():
        for identity in observation_ids:
            if time.monotonic() > confirmation_deadline:
                raise Refusal('Source confirmation scan exceeded five seconds; coverage unknown')
            meta = journal.observations[identity]
            if meta['kind']=='alert' and meta['origin']=='live_decision' and identity not in confirmed_source_ids:
                yield identity
    unconfirmed = unconfirmed_ids()
    confirmed = set(confirmed)-confirmed_source_ids
    absent, checked_ids, scan_complete = 0, 0, False
    with source(root, original) as conn:
        while len(confirmed) < 25:
            identities = list(islice(unconfirmed, 200))
            if not identities:
                scan_complete = True
                break
            if time.monotonic() > confirmation_deadline:
                raise Refusal('Source confirmation scan exceeded five seconds; coverage unknown')
            rows_found = conn.execute('SELECT rowid,id,kind,key,content_id,observed_at FROM history_refs WHERE id IN ('+
                                      ','.join('?' for _ in identities)+')', identities).fetchall()
            checked_ids += len(identities)
            absent += len(identities)-len(rows_found)
            for row in rows_found:
                if time.monotonic() > confirmation_deadline:
                    raise Refusal('Source confirmation scan exceeded five seconds; coverage unknown')
                current = observation(conn, row)
                old = journal.read_observation(row['id'])['record']
                if any(old.get(key) != current[key] for key in ('kind', 'key', 'content_id', 'observed_at', 'payload')):
                    raise Refusal('Source commit confirmation conflicts with sealed alert')
                confirmed.add(row['id'])
                if len(confirmed) >= 25: break
    confirmed = sorted(confirmed)
    if confirmed: journal.mark_source_commit(confirmed, time.time())
    return dict(status=receipt['status'] if receipt else 'caught_up_at_read', recovered=len(records),
                already_sealed=len(rows)-len(records), newly_confirmed=len(confirmed),
                source_ids_checked_for_confirmation=checked_ids, source_absent_at_check=absent,
                source_confirmation_scan_complete=scan_complete,
                source_cursor=rows[-1]['rowid'] if rows else cursor, receipt=receipt,
                original_decision_inputs='not_reconstructed')


def status(root, journal=None, persist=True):
    checked = time.time()
    result = dict(checked_at=checked, state='error', pending_observations=None,
                  seal_lag_seconds=None, continuity='unknown', capture_failure_count_unknown=None)
    authorized = journal is not None
    try:
        original, _ = legacy(root)
        journal = journal or archive(root)
        authorized = True
        state = journal.status()
        result.update(state)
        result['state'] = 'ok'
        result['checked_at'] = checked
        cursor = state.get('source_cursor')
        if cursor is None: cursor = original['cursor']
        pending, oldest, latest = 0, None, None
        source_deadline = time.monotonic()+5
        with source(root, original) as conn:
            row = conn.execute("SELECT MAX(observed_at) FROM history_refs WHERE kind='alert'").fetchone()
            latest = row[0]
            for row in conn.execute("SELECT id,observed_at FROM history_refs WHERE kind='alert' AND rowid>? ORDER BY rowid", (cursor,)):
                if time.monotonic() > source_deadline:
                    raise Refusal('Source status scan exceeded five seconds; coverage unknown')
                if row['id'] not in journal.observations:
                    pending += 1
                    oldest = min(oldest or row['observed_at'], row['observed_at'])
            health = conn.execute("SELECT content_id FROM object_refs WHERE kind='health' AND key='prospective'").fetchone()
            if health:
                result['producer_health'] = content(conn, health[0])[0]
            failure_count_unknown = False
            for row in conn.execute("SELECT rowid,id,kind,key,content_id,observed_at FROM history_refs WHERE kind='health' AND key='prospective' AND observed_at>=? ORDER BY observed_at", (state['activated_at'],)):
                if time.monotonic() > source_deadline:
                    raise Refusal('Prospective health history scan exceeded five seconds; capture loss unknown')
                historical = observation(conn, row)
                if historical['payload'].get('capture_failure_metadata_unavailable') is True:
                    failure_count_unknown = True
                    result['capture_failure_metadata_unavailable_source_id'] = historical['id']
                    result['capture_failure_metadata_unavailable_observed_at'] = historical['observed_at']
                    break
            result['capture_failure_count_unknown'] = failure_count_unknown
        confirmed_source_ids = journal.confirmed_source_ids
        gaps, unconfirmed, last_alert_sealed = 0, 0, None
        index_deadline = time.monotonic()+5
        for identity, meta in journal.observations.items():
            if time.monotonic() > index_deadline:
                raise Refusal('Journal status index scan exceeded five seconds; coverage unknown')
            if meta['kind'] != 'alert': continue
            gaps += meta['origin']=='backfill' and meta['observed_at'] >= state['activated_at']
            unconfirmed += meta['origin']=='live_decision' and identity not in confirmed_source_ids
            last_alert_sealed = max(last_alert_sealed or meta['sealed_at'], meta['sealed_at'])
        result.update(pending_observations=pending, first_pending_observed_at=oldest,
                      source_pending_observations=pending,
                      last_observed_at=latest,
                      last_alert_sealed_at=last_alert_sealed,
                      seal_lag_seconds=max(0, checked-oldest) if oldest is not None else 0,
                      post_activation_capture_gaps=gaps,
                      source_commit_unconfirmed=unconfirmed,
                      continuity='historical_gap; current_source_pending' if pending else 'historical_gap; current_source_caught_up',
                      detail='Legacy decision inputs were not retained; local hashes are not independent timestamps')
        failures = state.get('capture_failure_count', 0)
        if failures:
            result['continuity'] += '; capture_failures_recorded'
        if pending or gaps or unconfirmed or failures or state.get('error') or state.get('checkpoint_stale'):
            result['state'] = 'degraded'
        if result.get('producer_health', {}).get('status') == 'error':
            result['state'] = 'error'
            result['detail'] = 'Producer reports a prospective conservation error'
            result['pending_observations'] = None
            result['continuity'] = 'historical_gap; producer_capture_gap'
        if failure_count_unknown:
            result.update(state='error', pending_observations=None,
                          continuity='historical_gap; capture_loss_unknown',
                          detail='Operational health history records a capture failure whose counter could not be persisted')
        reasons = []
        if state['remaining_bytes'] < journal.policy['max_segment_bytes']+RESERVE:
            reasons.append('ROOM_FOR_MAX_SEGMENT_UNAVAILABLE')
        if state['used_bytes'] >= state['cap_bytes']:
            reasons.append('CAP_REACHED')
        elif state['used_bytes'] >= .9*state['cap_bytes']:
            reasons.append('CAPACITY_90_PERCENT')
        elif state['used_bytes'] >= .8*state['cap_bytes']:
            reasons.append('CAPACITY_80_PERCENT')
        result['capacity_warnings'] = reasons
        if reasons and result['state']=='ok': result['state']='degraded'
    except Exception as exc:
        result.update(state='error', detail=str(exc)[:1000], pending_observations=None, continuity='unknown')
    cache = Path(root)/'evidence/prospective_v2_status.json'
    try:
        previous = json_file(cache) if cache.exists() else {}
        notification = previous.get('notification', {})
        if not isinstance(notification, dict) or not isinstance(notification.get('last_attempt_at', 0), (int, float)):
            raise Refusal('Notification cooldown metadata invalid')
        result['notification'] = notification
    except Exception as exc:
        result['notification'] = {}
        result['notification_state_error'] = str(exc)[:300]
    if persist and authorized:
        journal.write_status(result)
    return result


def notify(message):
    script = 'on run argv\n display notification (item 1 of argv) with title "PolySentinel — conservation"\nend run'
    try:
        proc = subprocess.run(['/usr/bin/osascript', '-e', script, '--', message],
                              capture_output=True, text=True, timeout=5)
        return dict(attempted=True, exit_code=proc.returncode,
                    error=proc.stderr[:300], human_reception_verified=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return dict(attempted=True, error=str(exc)[:300], human_reception_verified=False)


def monitor(root, journal=None):
    error = None
    journal = journal or archive(root)
    try:
        recovery = recover(root, journal)
    except Exception as exc:
        recovery, error = None, str(exc)[:1000]
    result = status(root, journal, persist=False)
    result['recovery'] = recovery
    if error:
        result.update(state='error', recovery_error=error,
                      continuity=result['continuity']+'; recovery_blocked')
    reasons = list(result.get('capacity_warnings', []))
    if error: reasons.append('RECOVERY_ERROR')
    if result.get('capture_failure_count_unknown'): reasons.append('CAPTURE_LOSS_UNKNOWN')
    if result.get('capture_failure_count'): reasons.append('CAPTURE_FAILURE_COUNT='+str(result['capture_failure_count']))
    if result['state']=='error': reasons.append('STATUS_ERROR')
    if result.get('notification_state_error'): reasons.append('NOTIFICATION_STATE_UNREADABLE')
    result['notification_key'] = '|'.join(reasons)
    now = time.time()
    previous = result.get('notification', {})
    try:
        journal.write_status(result)
        # Sealed capture failures never disappear: notify on a change of reasons, then remind every 6 h.
        if reasons and (previous.get('key')!=result['notification_key'] or now-previous.get('last_attempt_at', 0)>=21600):
            result['notification'] = dict(key=result['notification_key'], last_attempt_at=now,
                result=notify('Conservation prospective à examiner : '+', '.join(reasons)+'. Voir le dashboard PolySentinel.'))
            journal.write_status(result)
        elif not reasons and previous.get('key'):
            result['notification'] = dict(previous, key='')  # a later recurrence is a change again
            journal.write_status(result)
    except Exception as exc:
        result.update(state='error', status_persistence_error=str(exc)[:500],
                      continuity=result['continuity']+'; status_persistence_failed')
        result['persistence_error_notification'] = notify('Impossible de conserver le statut prospectif : '+str(exc)[:200])
    return result


def watch(root):
    stop = threading.Event()
    previous = {sig: signal.signal(sig, lambda *_: stop.set()) for sig in (signal.SIGTERM, signal.SIGINT)}
    try:
        journal = archive(root)
        while not stop.is_set():
            monitor(root, journal)
            stop.wait(60)
        return dict(state='stopped', detail='Graceful prospective monitor shutdown')
    finally:
        for sig, handler in previous.items(): signal.signal(sig, handler)


def replay(root, identity, journal=None):
    journal = journal or archive(root)
    journal.verify()
    observation = journal.read_observation(identity)
    if observation['origin'] != 'live_decision' or not observation.get('frame_id'):
        raise Refusal('Original decision frame unavailable; retrospective reconstruction is not exact replay')
    frame = journal.reconstruct_frame(observation['frame_id'])
    if frame['source_version'] != runtime_source_version(root) or frame['source_version'] != journal.source_versions():
        raise Refusal('Installed source/config differs from sealed frame; use the matching trusted release')
    from . import signals
    installed = Path(signals.__file__).resolve()
    if installed != (Path(root)/'polysentinel/signals.py').resolve():
        raise Refusal('Loaded detector is not the requested trusted release')
    if file_digest(installed) != frame['source_version']['polysentinel/signals.py']:
        raise Refusal('Loaded detector source fingerprint differs')
    cases = signals.evaluate(frame['trades'], frame['markets'], frame['events'], now=frame['now'],
                             config=frame['config'], wallet_history=frame['wallet_history'])
    target = observation['record']['payload']['id']
    matches = [case for case in cases if case['id'] == target]
    actual = hashlib.sha256(encode(matches[0]).encode()).hexdigest() if len(matches)==1 else None
    expected = observation['record']['native_case_sha256']
    if actual != expected:
        raise Refusal('Replayed detector result differs from sealed native case')
    return dict(id=identity, frame_id=observation['frame_id'], replay_sha256=actual,
                native_case_sha256=expected, exact_native_case_match=True,
                limitation='Software replay, not independent validation of predictions or source truth')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('command', choices=('inspect', 'init', 'recover', 'status', 'monitor', 'watch', 'replay'))
    parser.add_argument('--id')
    args = parser.parse_args(argv)
    try:
        if args.command == 'inspect': result = inspect(args.root)
        elif args.command == 'status': result = status(args.root)
        elif args.command == 'recover': result = recover(args.root)
        elif args.command == 'monitor': result = monitor(args.root)
        elif args.command == 'watch': result = watch(args.root)
        elif args.command == 'replay':
            if not args.id: raise Refusal('Replay requires --id')
            result = replay(args.root, args.id)
        else:
            original, anchor = legacy(args.root)
            with source(args.root, original): pass
            result = archive(args.root).init(anchor, source_bundle(args.root))
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return int(result.get('state') == 'error')
    except Exception as exc:
        if args.command == 'watch':
            notify('Moniteur prospectif arrêté : '+str(exc)[:200])
        print(json.dumps(dict(state='error', error=str(exc)), ensure_ascii=False))
        return 1


if __name__ == '__main__':
    sys.exit(main())
