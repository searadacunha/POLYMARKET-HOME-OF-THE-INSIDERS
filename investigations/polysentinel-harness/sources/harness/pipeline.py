"""ACT: the deterministic steps of an investigation. The engine's own code detects; this module orders the work, stores it, and hands raw rows to the verifier.

No model is called here. Each step commits its output with its checkpoint, so a crash repeats at most the part after the last commit.
"""
import json
import math
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from polysentinel.news import milestone_kind
from polysentinel.signals import epoch
from signal_engine import dossiers
from signal_engine.prospective_detection import load_config, run_cycle
from signal_engine.service import event_rows

from . import memory, recover
from .recover import InvalidResponse, LeaseLost, Pause, Permanent, Transient, enqueue
from .sources import CollectorSource, Receipts
from .store import BudgetExceeded, ROOT, dumps, sha

ACTIONS = {}
RISK_WEIGHT = dict(HIGH=3.0, MEDIUM=2.0, LOW=1.0, UNKNOWN=1.0)
ROW_FIELDS = ('wallet', 'ts', 'observed_at', 'event_key', 'market_id', 'condition_id', 'token_id', 'is_buy', 'size', 'price', 'nominal', 'tx', 'outcome')
CAVEAT = 'Compatible with several explanations; not a finding about any person.'


def action(fn):
    ACTIONS[fn.__name__] = fn
    return fn


class Context:
    def __init__(self, h, task, config):
        self.h, self.task, self.config = h, task, config
        self.id, self.owner, self.attempt = task['id'], task['owner'], task['attempts']
        self.checkpoint = recover.load_json(task['checkpoint'])

    def _fault(self, moment):
        """Test hook, one shot: HARNESS_KILL_ONCE=marker:kind:moment kills this worker at that point."""
        marker, _, rest = os.environ.get('HARNESS_KILL_ONCE', '').partition(':')
        if marker and rest == f"{self.task['kind']}:{moment}" and Path(marker).exists():
            Path(marker).unlink()
            os.kill(os.getpid(), signal.SIGKILL)

    def commit(self, checkpoint, write=None):
        if os.getppid() == 1:  # the supervisor died: stop before doing more, its successor owns this work now
            raise LeaseLost('supervisor gone')
        def both(cx):
            if write:
                write(cx)
            self._fault('inside')
        recover.commit(self.h, self.id, self.owner, self.attempt, checkpoint, both)
        self.checkpoint = checkpoint
        self._fault('after')

    def spend(self, resource, amount):
        limit = self.config['budgets'].get(f'{resource}_per_day')
        if limit is not None and amount > limit:  # no new day would ever make room, so waiting would never end
            raise Permanent(f'{resource}: {amount:g} exceeds the whole daily limit of {limit:g}')
        try:
            with self.h.tx():
                self.h.spend(resource, amount, limit)
        except BudgetExceeded as exc:
            raise Pause(str(exc), delay=3600) from exc


def engine_config():
    return load_config()


def case_priority(output, now):
    """Utility times urgency: an open market closing soon loses its prospective value first. Cost is alike across cases, so it does not enter."""
    utility = RISK_WEIGHT.get(output['risk'].get('level'), 1.0) * (2.0 if output['category'] == 'CORROBORATED_BEHAVIOR' else 1.0)
    end = output.get('end_at')
    if not output.get('market_open', True):
        urgency = .5
    elif end is None:
        urgency = 1.0
    else:
        urgency = 1 + 3 * math.exp(-max(0, end - now) / (7 * 86400))
    return round(utility * urgency, 4)


def add_case_tasks(h, hypothesis, payload, priority, suffix=''):
    prefix = f'case:{hypothesis}{suffix}:'
    previous = []
    for stage in ('case_dossier', 'case_funding', 'case_receipts', 'case_bundle', 'case_verify', 'case_conclude'):
        task, _ = enqueue(h, prefix + stage, stage, dict(payload, hypothesis=hypothesis, suffix=suffix), priority, needs=previous, why=f'hypothesis {hypothesis}')
        previous = [task]


def known_at(milestone, moment):
    """A public source only counts from the moment we could have seen it."""
    if not milestone or (epoch(milestone.get('public_observed_at')) or moment) > moment:
        return None
    return milestone


def screened_in_24h(store, now):
    """Pairs evaluated in the 24 hours before this decision. Frozen with the case: a count read later would include pairs from after it."""
    hour = int(now // 3600)
    return sum(store.get(f'harness:screened:{h}') or 0 for h in range(hour - 23, hour + 1))


def open_case(h, output, now, screened):
    wallets = sorted(p['wallet'] for p in output['pairs'])
    spec = dict(event_key=output['event_key'], version=output['version'], wallets=wallets, category=output['category'])
    statement = f"Unusual purchases on event {output['event_key']} by {len(wallets)} wallets, category {output['category']}. {CAVEAT}"
    hypothesis, _, duplicate = memory.propose(h, 'case', statement, spec, f"engine:{output.get('engine', 'signal-engine')}")
    if duplicate:
        return False
    add_case_tasks(h, hypothesis, dict(output=h.put_artifact(output), as_of=now, screened=screened), case_priority(output, now))
    return True


@action
def discover(ctx):
    """Reads what the collector already stored; never a second collection. A trade, its evaluation, the cases it opens and the cursor all commit as one, so the stored cursor is the only truth about where reading stopped."""
    h, store = ctx.h, ctx.h.signal
    settings = ctx.config['source']
    engine = engine_config()
    state = ctx.checkpoint or dict(batches=0, rows=0, cases=0)
    source = CollectorSource(settings)
    try:
        while state['batches'] < settings.get('batches_per_task', 5):
            trades = source.new_trades(store.get('harness:cursor') or 0)
            if not trades:
                break
            # A replay and a live run decide at the time the rows were known; the wall clock would change the result.
            now = max(t['observed_at'] for t in trades)
            seen = (store.get('harness:rows') or 0) + len(trades)
            lag = ctx.config['pipeline']['max_lag_s']
            # Catalogue facts are read as the collector knows them now. Long behind live, they could carry the future, so these rows only warm the comparators.
            late = lag is not None and now < time.time() - lag
            emit = seen > ctx.config['pipeline']['warmup_rows'] and not late
            added = 0

            def write(cx):
                nonlocal added
                touched = store.add_trades(trades)
                source.refresh_markets(store, trades, now)
                outputs, summary = run_cycle(store, touched, now, engine, emit=emit, commit=False, public_known=lambda e: known_at(source.milestone(e), now) is not None)
                day, hour = int(now // 86400), int(now // 3600)
                store.put(f'harness:screened:{hour}', (store.get(f'harness:screened:{hour}') or 0) + summary['pairs'])
                if late:
                    store.put('harness:rows_too_late_for_cases', (store.get('harness:rows_too_late_for_cases') or 0) + len(trades))
                for output in outputs:
                    output['engine'] = engine['version']
                    output['at'] = now
                    added += open_case(h, output, now, screened_in_24h(store, now))
                store.put('harness:cursor', trades[-1]['observed_at'])
                store.put('harness:rows', seen)
                if store.get('harness:purged') != day:
                    store.purge(now, engine['retention_days'], engine['comparator_days'])
                    store.put('harness:purged', day)
                    cx.execute("DELETE FROM kv WHERE key LIKE 'harness:screened:%' AND CAST(substr(key, 18) AS INTEGER)<?", (hour - 48,))
            state = dict(batches=state['batches'] + 1, rows=state['rows'] + len(trades), cases=state['cases'])
            ctx.commit(state, write)
            state['cases'] += added
    finally:
        source.close()
    return state


def known_rows(h, event_key, as_of):
    rows = h.cx.execute('SELECT * FROM trades WHERE event_key=? AND observed_at<=? ORDER BY ts, tx', (event_key, as_of)).fetchall()
    return [{k: r[k] for k in ROW_FIELDS} for r in rows]


@action
def case_dossier(ctx, hypothesis, output, as_of, screened=1, suffix=''):
    """The engine's own dossier: wallets, positions, chronology, comparators, public timeline, competing explanations."""
    h = ctx.h
    found = h.get_artifact(output)
    wallets = [p['wallet'] for p in found['pairs']]
    rows = [r for r in event_rows(h.signal, found['event_key'], wallets) if r['observed_at'] <= as_of]
    for r in rows:
        r.pop('key', None)
    source = CollectorSource(ctx.config['source'])
    try:
        milestone = known_at(source.milestone(found['event_key']), as_of)
        gaps = source.gaps(min((r['ts'] for r in rows), default=as_of), as_of)
    finally:
        source.close()
    case = dossiers.build(found, rows, engine_config(), gaps=gaps, public_milestone=milestone)
    digest = sha(case)
    ctx.commit(dict(dossier=digest), lambda cx: h.put_artifact(case))
    return dict(dossier=digest, engine_checks=case['verification']['overall'])


def relations_from_flows(flows, wallets):
    """Only links between flagged wallets become claims, each at the level its state allows. A candidate by time and amount is never a funding route."""
    wallets = {w.lower() for w in wallets}
    out, seen = [], set()
    for section in flows.get('wallets', []):
        for link in section.get('incoming', []) + section.get('outgoing', []):
            ends = {str(link.get('source', '')).lower(), str(link.get('target', '')).lower()}
            key = (link.get('tx'), link.get('log_index'), tuple(sorted(ends)))
            if len(ends & wallets) < 2 or key in seen or link.get('source_is_service'):  # a service paying two people links nobody
                continue
            seen.add(key)
            state = link.get('state')
            if state == 'ONCHAIN_CONFIRMED':
                out.append(dict(wallets=sorted(ends), kind='direct_transfer_between_wallets', claimed='COMMON_FUNDING_ROUTE', transaction_hash=link.get('tx'), log_index=link.get('log_index')))
            elif state == 'CROSSCHAIN_CANDIDATE':
                out.append(dict(wallets=sorted(ends), kind='similar_amount', claimed='BEHAVIORAL_SIMILARITY', note='time and amount only'))
    return out


@action
def case_funding(ctx, hypothesis, output, as_of, screened=1, suffix=''):
    """Bounded. A wallet that cannot be traced stays in the file with its error and stops nothing, and the status says how far tracing got: an outage never reads as no link found."""
    h = ctx.h
    found = h.get_artifact(output)
    pairs = sorted(found['pairs'], key=lambda p: -p.get('measures', {}).get('max_market_spend', 0))
    settings = ctx.config.get('funding', dict(type='none'))
    wallets = [p['wallet'] for p in pairs][:settings.get('max_wallets', 3)]
    if settings['type'] == 'none':
        return dict(status='not_traced', relations=[])
    if settings['type'] == 'file':
        flows = json.loads(Path(settings['path']).read_text()).get(found['event_key'])
        if flows is None:
            return dict(status='not_traced', relations=[])
    elif settings['type'] == 'trace':
        ctx.spend('api_requests', len(wallets) * 72)  # per-wallet ceilings of the tracer
        from signal_engine.service import trace_fund_flows
        flows = trace_fund_flows(wallets, engine_config())
    else:
        raise Permanent(f"Unknown funding source {settings['type']}")
    relations = relations_from_flows(flows, wallets)
    failed = sorted(s.get('wallet', '?') for s in flows.get('wallets', []) if s.get('errors'))
    digest = sha(flows)
    ctx.commit(dict(flows=digest), lambda cx: h.put_artifact(flows))
    return dict(status='partial' if failed else 'traced', flows=digest, relations=relations, traced=len(wallets) - len(failed), untraced=failed, of_wallets=len(pairs))


@action
def case_receipts(ctx, hypothesis, output, as_of, screened=1, suffix=''):
    """One receipt per commit: an outage after 40 of 50 does not read the 40 again."""
    h = ctx.h
    found = h.get_artifact(output)
    wallets = {p['wallet'] for p in found['pairs']}
    wanted = sorted({r['tx'].lower() for r in known_rows(h, found['event_key'], as_of) if r['wallet'] in wallets and r['is_buy']})
    state = ctx.checkpoint or dict(receipts={}, missing=[])
    source = Receipts(ctx.config.get('chain', dict(type='none')))
    if source.type == 'none':
        return dict(receipts=None, status='no_chain_source', wanted=len(wanted))
    for tx in wanted:
        if tx in state['receipts'] or tx in state['missing']:
            continue

        def read():
            if source.type != 'file':
                ctx.spend('api_requests', 1)  # each try is a request, and an outage must not read as free
            return source.get(tx)
        try:
            receipt = recover.retry_call(read, attempts=ctx.config['recovery'].get('read_attempts', 3), base=ctx.config['recovery'].get('read_backoff_s', .5), seed=tx)
        except InvalidResponse:
            raise  # a source that keeps answering nonsense spends attempts and ends in quarantine
        except Transient as exc:
            raise Pause(f'Source unavailable: {exc}', delay=ctx.config['recovery'].get('outage_delay_s', 300)) from exc  # an outage is not the task's fault and costs it no attempt
        if receipt is None:
            state = dict(state, missing=state['missing'] + [tx])
            ctx.commit(state)
        else:
            digest = sha(receipt)
            state = dict(state, receipts=dict(state['receipts'], **{tx: digest}))
            ctx.commit(state, lambda cx, r=receipt: h.put_artifact(r))
    return dict(receipts=state['receipts'], missing=state['missing'], status='read', wanted=len(wanted))


def needed_result(h, hypothesis, stage, suffix=''):
    row = h.cx.execute('SELECT result FROM tasks WHERE dedupe_key=?', (f'case:{hypothesis}{suffix}:{stage}',)).fetchone()
    return recover.load_json(row['result']) if row else None


def build_case_bundle(ctx, hypothesis, output, as_of, screened, suffix):
    h = ctx.h
    found = h.get_artifact(output)
    limits = ctx.config['pipeline']
    wallets = sorted(p['wallet'] for p in found['pairs'])
    event = found['event_key']
    rows = known_rows(h, event, as_of)
    flagged = [r for r in rows if r['wallet'] in wallets]
    metrics = {p['wallet']: p['measures']['max_market_spend'] for p in found['pairs']}  # the engine's number, for the verifier to contradict
    since = as_of - limits['control_window_s']
    history, cut = {}, []
    for wallet in wallets:
        history[wallet] = [{k: r[k] for k in ROW_FIELDS} for r in h.cx.execute('SELECT * FROM trades WHERE wallet=? AND observed_at<=? AND event_key<>? ORDER BY ts DESC LIMIT 5000', (wallet, as_of, event))]
        if len(history[wallet]) == 5000:
            cut.append(wallet)
    totals = {r['wallet']: r['total'] for r in h.cx.execute('SELECT wallet, SUM(nominal) total FROM trades WHERE is_buy=1 AND observed_at<=? AND ts>=? GROUP BY wallet', (as_of, since))}
    cap = limits['control_units_cap']
    groups = h.cx.execute('''SELECT wallet, event_key, SUM(nominal) spend, SUM(size) shares FROM trades WHERE is_buy=1 AND observed_at<=? AND ts>=? AND event_key<>? GROUP BY wallet, event_key ORDER BY wallet, event_key LIMIT ?''', (as_of, since, event, cap + 1)).fetchall()
    controls = [dict(wallet=g['wallet'], event_key=g['event_key'], spend=g['spend'], shares=g['shares'], total=totals.get(g['wallet'], g['spend'])) for g in groups if g['wallet'] not in wallets]
    source = CollectorSource(ctx.config['source'])
    try:
        milestone = source.milestone(event)
        gaps = source.gaps(min((r['ts'] for r in flagged), default=as_of) - 3600, as_of)
    finally:
        source.close()
    if milestone:
        milestone = dict(public_at=epoch(milestone.get('public_at')), public_observed_at=epoch(milestone.get('public_observed_at')), source_url=milestone.get('source_url'), kind=milestone_kind(milestone))
    funding = needed_result(h, hypothesis, 'case_funding', suffix) or {}
    read = needed_result(h, hypothesis, 'case_receipts', suffix) or {}
    receipts = {tx: h.get_artifact(digest) for tx, digest in (read.get('receipts') or {}).items()}
    claim = dict(level=found['category'], wallets=wallets, metrics=metrics, relations=funding.get('relations', []))
    statement = h.cx.execute('SELECT statement FROM hypotheses WHERE id=?', (hypothesis,)).fetchone()[0]
    dossier = needed_result(h, hypothesis, 'case_dossier', suffix) or {}
    return dict(kind='case', as_of=as_of, event_key=event, statement=statement, claim=claim, event_rows=rows, wallet_history=history, history_truncated=cut, history_window_days=engine_config()['retention_days'], gaps=gaps, wallet_totals={w: totals.get(w, metrics.get(w, 0)) for w in wallets},
                controls=controls[:cap], controls_truncated=len(groups) > cap, milestone=milestone, receipts=receipts, screened=screened, dossier_overall=dossier.get('engine_checks'),
                funding={k: funding.get(k) for k in ('status', 'traced', 'untraced', 'of_wallets')}, config=ctx.config['verify'])


@action
def case_bundle(ctx, hypothesis, output, as_of, screened=1, suffix=''):
    bundle = build_case_bundle(ctx, hypothesis, output, as_of, screened, suffix)
    digest = sha(bundle)
    ctx.commit(dict(bundle=digest), lambda cx: ctx.h.put_artifact(bundle))
    return dict(bundle=digest, rows=len(bundle['event_rows']), controls=len(bundle['controls']))


def run_verifier(root, bundle, timeout=600):
    """Two separate processes, different hash seeds. Bytes that differ mean the result is not reproducible, whatever it says."""
    folder = Path(root) / 'bundles'
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f'{sha(bundle)}.json'
    path.write_text(dumps(bundle))
    outputs = []
    for seed in ('1', '2'):
        done = subprocess.run([sys.executable, '-m', 'harness.verify', str(path)], capture_output=True, text=True, timeout=timeout, cwd=ROOT, env=dict(os.environ, PYTHONHASHSEED=seed))
        if done.returncode != 0:
            raise Permanent(f'Verifier failed: {done.stderr[-400:]}')
        outputs.append(done.stdout)
    path.unlink()  # the bundle stays as an artifact; this file was only the verifier's door
    if outputs[0] != outputs[1]:
        report = json.loads(outputs[0])
        report['overall'] = 'INCOMPLETE'
        report['checks']['reproducible'] = dict(status='INCOMPLETE', detail='Two runs of the verifier disagree.')
        return report
    return json.loads(outputs[0])


def record_verification(ctx, hypothesis, report, write=None):
    digest = sha(report)

    def both(cx):
        ctx.h.put_artifact(report)
        cx.execute('INSERT INTO verifications(hypothesis, verifier, verdict, report_sha, input_sha, code_sha, at) VALUES(?,?,?,?,?,?,?)',
                   (hypothesis, f"harness.verify:{report['code_sha'][:12]}", report['overall'], digest, report['input_sha'], report['code_sha'], time.time()))
        if write:
            write(cx)
    return digest, both


@action
def case_verify(ctx, hypothesis, output, as_of, screened=1, suffix=''):
    h = ctx.h
    if ctx.checkpoint:  # recorded before a crash: a second row would change nothing
        return ctx.checkpoint
    bundle = h.get_artifact((needed_result(h, hypothesis, 'case_bundle', suffix) or {})['bundle'])
    report = run_verifier(h.root, bundle, ctx.config['resources']['task_timeout_s'])
    digest, write = record_verification(ctx, hypothesis, report)
    ctx.commit(dict(report=digest), write)
    return dict(report=digest, verdict=report['overall'])


def failure_reason(report):
    return '; '.join(f"{name}: {c['detail']}" for name, c in sorted(report['checks'].items()) if c['status'] in ('FAIL', 'INCOMPLETE'))[:800]


def alert_body(hypothesis, statement, bundle, report, dossier):
    wallets = report['checks']['alternatives']['surviving']
    transactions = [dict(tx=r['tx'], wallet=r['wallet'], ts=r['ts'], first_observed=r['observed_at'], side='BUY' if r['is_buy'] else 'SELL', nominal=r['nominal'], price=r['price'], token_id=r['token_id'], url=f"https://polygonscan.com/tx/{r['tx']}")
                    for r in bundle['event_rows'] if r['wallet'] in wallets]
    if not transactions:
        raise Permanent('An alert needs transactions a reader can check')
    return dict(hypothesis=hypothesis, event_key=bundle['event_key'], as_of=bundle['as_of'], statement=statement, wallets=wallets, transactions=transactions,
                checks={k: c['status'] for k, c in report['checks'].items()}, rarity={k: report['checks']['controls'].get(k) for k in ('hits', 'controls', 'tail', 'expected_false_positives')},
                not_testable=report['checks']['alternatives'].get('not_testable', []), report=report['input_sha'], dossier=dossier, screened_24h=bundle['screened'], funding=bundle['funding'], history_days_read=bundle['history_window_days'], collection_gaps_in_period=len(bundle['gaps']),
                not_established=['Identity of any wallet owner.', 'Possession of private information.', 'Common ownership of these wallets.'])


def conclude(ctx, hypothesis, suffix=''):
    """Memory and status change together. The database refuses `validated` without a passing verification by another party, so this code cannot talk it round."""
    h = ctx.h
    row = h.cx.execute('SELECT * FROM hypotheses WHERE id=?', (hypothesis,)).fetchone()
    verification = h.cx.execute('SELECT * FROM verifications WHERE hypothesis=? ORDER BY id DESC LIMIT 1', (hypothesis,)).fetchone()
    report = h.get_artifact(verification['report_sha'])
    verdict = report['overall']
    topic = f"hypothesis:{row['kind']}"
    alert = None
    if verdict == 'PASS' and row['kind'] == 'case':
        bundle = h.get_artifact(needed_result(h, hypothesis, 'case_bundle', suffix)['bundle'])
        dossier = (needed_result(h, hypothesis, 'case_dossier', suffix) or {}).get('dossier')
        alert = alert_body(hypothesis, row['statement'], bundle, report, dossier)

    def write(cx):
        now = time.time()
        status = dict(PASS='validated', FAIL='rejected', INCOMPLETE='needs_data')[verdict]
        reason = None if verdict == 'PASS' else failure_reason(report)
        cx.execute('UPDATE hypotheses SET status=?, reason=?, updated_at=? WHERE id=?', (status, reason, now, hypothesis))
        if verdict == 'PASS':
            memory.remember(h, 'result', topic, row['fingerprint'], row['statement'], status='verified', source_sha=verification['report_sha'], hypothesis=hypothesis)
        elif verdict == 'FAIL':
            memory.remember(h, 'rejected', topic, row['fingerprint'], f"{row['statement']} Rejected: {reason}", status='verified', source_sha=verification['report_sha'], hypothesis=hypothesis)
        else:
            memory.remember(h, 'limit', topic, row['fingerprint'] + f":{verification['id']}", f"{row['statement']} Missing: {reason}", source_sha=verification['report_sha'], hypothesis=hypothesis)
        if alert:
            spec = json.loads(row['spec'])
            cx.execute('INSERT OR IGNORE INTO alerts(dedupe_key, hypothesis, event_key, body, sha, at) VALUES(?,?,?,?,?,?)', (f"{spec['event_key']}:{spec['version']}", hypothesis, spec['event_key'], dumps(alert), sha(alert), now))
    ctx.commit(dict(verdict=verdict), write)
    if alert:
        folder = h.root / 'alerts'
        folder.mkdir(exist_ok=True)
        (folder / f'{sha(alert)[:16]}.json').write_text(json.dumps(alert, ensure_ascii=False, indent=1))
    return dict(verdict=verdict, alert=bool(alert))


@action
def case_conclude(ctx, hypothesis, output, as_of, screened=1, suffix=''):
    return conclude(ctx, hypothesis, suffix)


FEATURES = dict(new_wallet=lambda e: e['age_s'] <= e['threshold'], large_entry=lambda e: e['nominal'] >= e['threshold'], low_price=lambda e: e['price'] <= e['threshold'],
                late_entry=lambda e: e['end_at'] is not None and e['end_at'] - e['ts'] <= e['threshold'])


def population_rows(h, source, spec, cap):
    """One row per wallet and event, at its first purchase. Features use only rows known then. The label comes later by nature and is held apart for the verifier."""
    feature = FEATURES[spec['feature']]
    winners, rows, dropped, seen = {}, [], 0, 0
    for r in h.cx.execute('SELECT wallet, event_key, market_id, condition_id, token_id, MIN(ts) ts, price, nominal, observed_at FROM trades WHERE is_buy=1 GROUP BY wallet, event_key ORDER BY wallet, event_key LIMIT ?', (cap + 1,)).fetchall()[:cap + 1]:
        seen += 1
        if seen > cap:
            return rows, dropped, True
        if r['market_id'] not in winners:
            winners[r['market_id']] = source.winners(r['market_id'])
        won = winners[r['market_id']]
        if won is None:
            dropped += 1
            continue
        first, _ = h.signal.first_trade(r['wallet'], r['observed_at'])
        market = h.cx.execute('SELECT end_at FROM markets WHERE condition_id=?', (r['condition_id'],)).fetchone()
        entry = dict(r, age_s=r['ts'] - first if first is not None else 0, end_at=market['end_at'] if market else None, threshold=spec['threshold'])
        rows.append(dict(wallet=r['wallet'], event_key=r['event_key'], ts=r['ts'], observed_at=r['observed_at'], x=bool(feature(entry)), y=(1 - r['price']) / r['price'] if str(r['token_id']) in won else -1.0))
    return rows, dropped, False


def population_bundle(ctx, hypothesis, spec, statement):
    h = ctx.h
    source = CollectorSource(ctx.config['source'])
    try:
        rows, dropped, truncated = population_rows(h, source, spec, ctx.config['pipeline']['population_rows_cap'])
    finally:
        source.close()
    if not rows:
        raise Pause('No settled market yet', delay=86400)
    times = sorted(r['ts'] for r in rows)
    tests = h.cx.execute("SELECT COUNT(DISTINCT hypothesis) FROM verifications v JOIN hypotheses p ON p.id=v.hypothesis WHERE p.kind='population'").fetchone()[0] + 1
    return dict(kind='population', as_of=max(r['observed_at'] for r in rows), rows=rows, statement=statement, direction=spec.get('direction', 1), split_ts=times[len(times) // 2], embargo_s=spec.get('embargo_s', 86400),
                n_tests=tests, salt=spec.get('salt', 'harness'), unsettled_dropped=dropped, rows_truncated=truncated, config=ctx.config['verify'])


@action
def population_test(ctx, hypothesis):
    """The number of tests comes from the registry, never from the proposer: every idea tried makes the next one harder to accept."""
    h = ctx.h
    row = h.cx.execute('SELECT * FROM hypotheses WHERE id=?', (hypothesis,)).fetchone()
    if not ctx.checkpoint:
        report = run_verifier(h.root, population_bundle(ctx, hypothesis, json.loads(row['spec']), row['statement']), ctx.config['resources']['task_timeout_s'])
        digest, write = record_verification(ctx, hypothesis, report)
        ctx.commit(dict(report=digest), write)
    return conclude(ctx, hypothesis)


@action
def run_tests(ctx, module='tests'):
    """Runs a test suite and keeps the verdict; a long output goes through Stop-Bullshiting and the original stays recoverable."""
    done = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', module], capture_output=True, text=True, cwd=ROOT)  # the supervisor's timeout stops the whole group
    text = done.stdout + done.stderr
    view = memory.compress_output(text, ctx.h.root, source='run_tests')
    status = 'method_ok' if done.returncode == 0 else 'method_bad'
    memory.remember(ctx.h, status, 'tests', module, view['view'][-500:])
    return dict(returncode=done.returncode, chars=view['original_chars'], visible=view['visible_chars'], tool=view['tool'])


@action
def propose_hypotheses(ctx):
    """The only place a model is called. Its answer is data: it cannot write, run or validate anything, and a schema decides what enters the queue."""
    from . import agent
    query = ' '.join(FEATURES) + ' hypothesis population rejected'
    pack = memory.context_pack(ctx.h, query, ctx.config['llm']['context_chars'])
    answer = agent.ask_for_hypotheses(ctx, pack['text'])
    added = 0
    for item in answer['hypotheses']:
        spec = dict(feature=item['feature'], threshold=item['threshold'], direction=item.get('direction', 1))
        new, status, duplicate = memory.propose(ctx.h, 'population', f"{item['statement']} {CAVEAT}", spec, f"llm:{ctx.config['llm']['model']}")
        if duplicate:
            memory.remember(ctx.h, 'decision', 'proposal_refused', new and str(new), f'Proposed again while {status}; dropped without a test.')
            continue
        enqueue(ctx.h, f'population:{new}', 'population_test', dict(hypothesis=new), .2, why='proposed by the model')
        added += 1
    return dict(added=added, proposed=len(answer['hypotheses']), usage=answer['usage'], context_chars=pack['chars'])
