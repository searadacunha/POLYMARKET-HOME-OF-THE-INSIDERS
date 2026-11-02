"""Shadow run: reads the collector's database read-only, keeps its own state, seals its own journal.

Commands: seal, warmup, once, status, verify. One run then exit, so a stuck run cannot accumulate.
Nothing here trades, holds a key, or changes a production table, threshold or alert.
"""
import argparse
import asyncio
import hashlib
import json
import os
import resource
import shutil
import sqlite3
import subprocess
import sys
import time
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from polysentinel import reports  # noqa: E402
from polysentinel.signals import epoch  # noqa: E402
from signal_engine import dossiers  # noqa: E402
from signal_engine.funding_graph import build_funding_links  # noqa: E402
from signal_engine.prospective_detection import apply_review_budget, fingerprint, load_config, run_cycle  # noqa: E402
from signal_engine.store import SignalStore  # noqa: E402

DATABASE = ROOT / 'data/polysentinel.sqlite3'
STATE = Path(os.environ.get('SIGNAL_ENGINE_STATE', Path.home() / '.local/state/polysentinel-signal-engine'))
EVIDENCE = ROOT / 'evidence/signal_engine_v1'
JOURNAL = EVIDENCE / 'journal.jsonl'
STATUS = EVIDENCE / 'status.json'
REPORTS = ROOT / 'reports'
POST_EVENT_JOURNAL = EVIDENCE / 'post_event.jsonl'
DISK_FLOOR = 13_500_000_000
DATA_API = 'https://data-api.polymarket.com/v2/'
LATE_ROW_REACH = 7 * 86400
BATCH = 20000
ENRICHMENT_STORE_LIMIT = 300_000_000
STATE_LIMIT = 500_000_000


def code_fingerprints():
    package = Path(__file__).parent
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(package.glob('*.py')) + [package / 'config.json']}


def append_link(journal, kind, content, at):
    """Append-only and hash-chained. The clock is local: this orders events, it is not a notary."""
    journal = Path(journal)
    journal.parent.mkdir(parents=True, exist_ok=True)
    previous, n = None, 0
    if journal.exists():
        with journal.open('rb') as f:
            for line in f:
                previous, n = json.loads(line)['sha256'], n + 1
    body = dict(n=n, previous=previous, kind=kind, at=at, content=content)
    body['sha256'] = hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(',', ':'), default=str).encode()).hexdigest()
    with journal.open('a') as f:
        f.write(json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(',', ':'), default=str) + '\n')
        f.flush()
        os.fsync(f.fileno())
    return body


def verify_chain(journal):
    previous, n = None, 0
    with Path(journal).open('rb') as f:
        for line in f:
            body = json.loads(line)
            seal = body.pop('sha256')
            if body['previous'] != previous or body['n'] != n:
                raise RuntimeError(f'Chain broken at link {n}')
            if hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(',', ':'), default=str).encode()).hexdigest() != seal:
                raise RuntimeError(f'Link {n} altered')
            previous, n = seal, n + 1
    return dict(links=n, head=previous)


def require_sealed_version(journal):
    """A changed rule needs a dated amendment; it cannot slip silently into running detection."""
    sealed = None
    with Path(journal).open('rb') as f:
        for line in f:
            body = json.loads(line)
            if body['kind'] in ('genesis', 'amendment'):
                sealed = body['content']['fingerprints']
    if sealed != code_fingerprints():
        raise RuntimeError('Code or configuration differs from the sealed version; a dated amendment is required')


def open_collector():
    return sqlite3.connect(f'file:{DATABASE}?mode=ro', uri=True, timeout=10)


def collector_object(cx, kind, key):
    row = cx.execute('SELECT c.body FROM object_refs r JOIN contents c ON c.id=r.content_id WHERE r.kind=? AND r.key=?', (kind, str(key))).fetchone()
    return json.loads(zlib.decompress(row[0])) if row else None


def read_new_trades(cx, cursor, limit=BATCH):
    """By observation time. The trade-time bound uses the index and still reaches late rows."""
    rows = cx.execute('''SELECT t.key, t.observed_at, c.body FROM trade_index t JOIN object_refs r ON r.kind='trade' AND r.key=t.key JOIN contents c ON c.id=r.content_id
                         WHERE t.trade_time>=? AND t.observed_at>? ORDER BY t.observed_at LIMIT ?''', (max(0, cursor - LATE_ROW_REACH), cursor, limit)).fetchall()
    if len(rows) == limit:
        # One API page shares one observed_at, and the next read is strict: never cut inside it.
        last = rows[-1][1]
        whole = [r for r in rows if r[1] < last]
        if not whole:
            raise RuntimeError(f'{limit} rows share one observation; raise the batch')
        rows = whole
    trades = []
    for key, observed, body in rows:
        p = json.loads(zlib.decompress(body))
        raw = p.get('raw') or {}
        event_key = str(p.get('event_id') or '') or 'unmapped:' + str(p.get('event_slug') or p.get('condition_id'))
        trades.append(dict(key=key, wallet=p['wallet'].lower(), ts=int(p['timestamp']), observed_at=observed, event_key=event_key, market_id=str(p.get('market_id') or ''), condition_id=str(p.get('condition_id') or '').lower(),
                           token_id=str(p['token_id']), is_buy=p['side'] == 'BUY', size=float(p['size']), price=float(p['price']), tx=p['transaction_hash'], outcome=p.get('outcome'), title=raw.get('title')))
    return trades


def refresh_markets(store, cx, trades, now):
    """Catalogue facts as the collector knows them now, which is the point of a prospective run."""
    seen = set()
    for t in trades:
        if t['condition_id'] in seen:
            continue
        seen.add(t['condition_id'])
        market = collector_object(cx, 'market', t['market_id']) if t['market_id'] else None
        if not market:
            store.add_market(t['condition_id'], title=t['title'], event_key=t['event_key'], market_id=t['market_id'])
            continue
        raw = market.get('raw') or {}
        event = collector_object(cx, 'event', market.get('event_id')) or {}
        closed = market.get('closed') is True or market.get('active') is False or str(raw.get('umaResolutionStatus', '')).lower() == 'resolved'
        store.add_market(t['condition_id'], title=t['title'] or market.get('question'), event_key=t['event_key'], market_id=t['market_id'], end_at=epoch(market.get('end_date')), closed_at=now if closed else None,
                         rules=raw.get('description'), tags=event.get('tags') or (), sports=bool(raw.get('sportsMarketType') or raw.get('gameId')), neg_risk=bool(raw.get('negRisk')), liquidity=market.get('liquidity'),
                         liquidity_observed_at=market.get('observed_at'), spread=raw.get('spread'), group_title=raw.get('groupItemTitle'), cataloged=True)


def coverage_gaps(cx, start, end):
    gaps = []
    for body, in cx.execute("SELECT c.body FROM object_refs r JOIN contents c ON c.id=r.content_id WHERE r.kind='gap' AND r.observed_at>=? ORDER BY r.observed_at DESC LIMIT 200", (start - 86400,)):
        g = json.loads(zlib.decompress(body))
        if g.get('start') and g.get('end') and g['end'] >= start and g['start'] <= end:
            gaps.append(dict(start=g['start'], end=g['end'], reason=g.get('reason')))
    return gaps


def public_milestone(cx, event_key):
    known = collector_object(cx, 'public_milestone', event_key)
    return known if known and known.get('verified') and known.get('result_available') else None


def event_rows(store, event_key, wallets):
    marks = ','.join('?' * len(wallets))
    return [dict(r) for r in store.cx.execute(f'SELECT * FROM trades WHERE event_key=? AND wallet IN ({marks}) ORDER BY ts', (event_key, *wallets))]


def notify(output):
    script = 'on run argv\ndisplay notification (item 1 of argv) with title "PolySentinel, shadow engine"\nend run'
    text = f"{output['category']}: {output.get('title') or output['event_key']}"
    try:
        r = subprocess.run(['/usr/bin/osascript', '-e', script, text], capture_output=True, text=True, timeout=10)
        return dict(exit_code=r.returncode, human_reception_verified=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return dict(error=str(exc)[:200], human_reception_verified=False)


def enrich(output, config):
    """Bounded public lookups, once receipts can be final: trades reconciled on-chain, funding links, public news."""
    from polysentinel.chain import reconcile
    from polysentinel.db import Store
    from polysentinel.investigation import investigate
    from polysentinel.net import Net
    directory = STATE / 'enrichment'
    if directory.exists() and sum(f.stat().st_size for f in directory.rglob('*') if f.is_file()) > ENRICHMENT_STORE_LIMIT:
        return dict(links=None, reconciled=[], errors=[dict(stage='capacity', error='Private enrichment store full; nothing fetched')])
    collector_config = dict(json.loads((ROOT / 'config.json').read_text()), root=str(ROOT))
    ordered = sorted(output['pairs'], key=lambda p: -p['measures']['max_market_spend'])[:3]

    async def lookups():
        store = Store(directory)
        results = []
        try:
            async with Net(store, collector_config) as net:
                for pair in ordered:
                    net.begin_cycle()
                    target = dict(id=hashlib.sha256(f"{pair['wallet']}|{output['event_key']}".encode()).hexdigest()[:24], wallet=pair['wallet'], event_id=output['event_key'],
                                  alerts=[dict(transaction_hash=pair['position']['largest_tx'])], score=len(pair['wallet_findings']) + len(pair['position_findings']), signals=[])
                    results.append(await investigate(store, net, collector_config, target))
        finally:
            store.close()
        return results

    results = asyncio.run(lookups())
    edges, reconciled = [], []
    for pair, result in zip(ordered, results):
        for receipt in result.get('receipts', []):
            if receipt.get('status') != 'confirmed':
                reconciled.append(dict(tx=receipt.get('transaction_hash'), status=receipt.get('status'), wallet=pair['wallet']))
                continue
            for edge in receipt.get('transfers', []):
                edges.append(dict(edge, timestamp=receipt.get('timestamp')))
            largest = pair['largest']
            if receipt['transaction_hash'].lower() == largest['tx'].lower():
                trade = dict(wallet=pair['wallet'], token_id=largest['token_id'], side='BUY', size=largest['size'], price=largest['price'])
                reconciled.append(dict(tx=largest['tx'], wallet=pair['wallet'], block=receipt.get('block_number'), url=receipt.get('url'), **reconcile(trade, receipt.get('fills', []))))
    wallets = [p['wallet'] for p in ordered]
    return dict(links=build_funding_links(edges, wallets), reconciled=reconciled, public_availability=next((r.get('public_availability') for r in results), None),
                errors=[e for r in results for e in r.get('errors', [])], scope=dict(wallets=wallets, requests=sum(r.get('budget', {}).get('logical_requests', 0) for r in results)))


def fetch_resolved_case(case, wallets, conditions, tokens_by_condition, first_buy_by_token):
    """Public reads for Engine B. A resolution that cannot be read leaves the case for a later run."""
    from polysentinel.db import Store
    from polysentinel.net import Net
    collector_config = dict(json.loads((ROOT / 'config.json').read_text()), root=str(ROOT))

    async def lookups():
        store = Store(STATE / 'post_event')
        try:
            async with Net(store, collector_config) as net:
                net.begin_cycle()
                resolution = {}
                for condition in conditions[:3]:
                    body = (await net.request(DATA_API + 'resolutions', params=dict(condition=condition))).body
                    for r in body.get('data', []) if isinstance(body, dict) else []:
                        tokens = tokens_by_condition.get(condition, [])
                        if r.get('status') == 'resolved' and r.get('payouts') and len(r['payouts']) == len(tokens):
                            total = sum(float(x) for x in r['payouts']) or 1.0
                            resolution.update({t: float(x) / total for t, x in zip(tokens, r['payouts'])})
                if not resolution:
                    return None
                activity, trades, complete = {}, {}, {}
                for wallet in wallets[:3]:
                    body = (await net.request(DATA_API + 'activity', params=dict(user=wallet, event_id=case['event_key'], limit=500, sort_direction='ASC'))).body
                    rows = body.get('data', []) if isinstance(body, dict) else []
                    complete[wallet] = not (body.get('pagination') or {}).get('has_more') if isinstance(body, dict) else False
                    activity[wallet] = rows
                    trades[wallet] = [dict(ts=r['timestamp'], size=float(r['size']), price=float(r['price']), is_buy=r.get('side') == 'BUY', token_id=str(r.get('token_id')), tx=r.get('transaction_hash')) for r in rows if r.get('type') == 'TRADE']
                prices = {}
                for token, start in list(first_buy_by_token.items())[:3]:
                    body = (await net.request(DATA_API + 'prices-history', params=dict(token_id=token, start=int(start), end=int(start) + 8 * 86400))).body
                    prices[token] = [(p['timestamp'], p['price']) for p in (body.get('data', []) if isinstance(body, dict) else [])]
                return dict(resolution=resolution, activity=activity, trades=trades, complete=complete, prices=prices)
        finally:
            store.close()

    return asyncio.run(lookups())


def run_post_event(store, cx, now, config, journal=POST_EVENT_JOURNAL, fetcher=fetch_resolved_case):
    """Engine B, for cases whose markets have ended. It appends its own journal and leaves Engine A's alone."""
    from signal_engine.post_event_investigation import investigate_resolved_case
    done = 0
    for case in store.cx.execute('SELECT * FROM cases WHERE priority>=0 ORDER BY opened_at').fetchall():
        if done >= config['post_event_per_run'] or store.get('post_event:' + case['event_key']):
            continue
        if (store.get('post_event_try:' + case['event_key']) or 0) > now - 86400:
            continue
        markets = store.cx.execute('SELECT * FROM markets WHERE event_key=?', (case['event_key'],)).fetchall()
        if not markets or not all((m['closed_at'] and m['closed_at'] <= now) or (m['end_at'] and m['end_at'] <= now) for m in markets):
            continue
        store.put('post_event_try:' + case['event_key'], now)
        pairs = store.cx.execute("SELECT wallet FROM pairs WHERE event_key=? AND anomalies!='{}'", (case['event_key'],)).fetchall()
        wallets = sorted(r['wallet'] for r in pairs)
        rows = event_rows(store, case['event_key'], wallets) if wallets else []
        first_buy = {}
        for r in rows:
            if r['is_buy']:
                first_buy[r['token_id']] = min(first_buy.get(r['token_id'], r['ts']), r['ts'])
        tokens_by_condition = {}
        for m in markets:
            known = collector_object(cx, 'market', m['market_id']) if m['market_id'] else None
            tokens_by_condition[m['condition_id']] = [str(t['token_id']) for t in (known or {}).get('tokens', [])]
        data = fetcher(dict(case), wallets, sorted(tokens_by_condition), tokens_by_condition, first_buy)
        if not data:
            continue
        sealed = dict(event_key=case['event_key'], fingerprint=case['fingerprint'], category=case['category'])
        report = investigate_resolved_case(sealed, data['trades'], data['activity'], data['prices'], data['resolution'])
        report['history_complete'] = data['complete']
        append_link(journal, 'post_event', report, now)
        store.put('post_event:' + case['event_key'], now)
        done += 1
    store.cx.commit()
    return done


def queue_page(store, path=REPORTS / 'signal-engine-queue.html'):
    """One line per event, review first; new cases and re-observations stay visibly apart."""
    today = int(time.time() // 86400)
    new_today = store.cx.execute('SELECT COUNT(*) FROM cases WHERE opened_at>=?', (today * 86400,)).fetchone()[0]
    reobserved = store.cx.execute('SELECT SUM(reobservations) FROM cases').fetchone()[0] or 0
    body = f'<p>Experimental engine in shadow mode. It does not replace production alerts. A category describes evidence, never a person.</p><p><strong>{new_today}</strong> new cases today. <strong>{reobserved}</strong> re-observations of known cases, which are not new cases.</p>'
    body += '<div class="scroll"><table><tr><th>Category</th><th>Review</th><th>Event</th><th>Version</th><th>Opened</th><th>Updated</th><th>Re-observed</th><th>File</th></tr>'
    for c in store.cx.execute('SELECT * FROM cases ORDER BY priority DESC, updated_at DESC LIMIT 100').fetchall():
        title = store.cx.execute('SELECT title FROM markets WHERE event_key=? AND title IS NOT NULL LIMIT 1', (c['event_key'],)).fetchone()
        stem = f"signal-case-{hashlib.sha256(c['event_key'].encode()).hexdigest()[:16]}-v{c['version']}"
        body += f'<tr><td>{reports.esc(c["category"])}</td><td>{"yes" if c["priority"] else ""}</td><td>{reports.esc(title[0] if title else c["event_key"])}</td><td>{c["version"]}</td><td>{reports.times(c["opened_at"])}</td><td>{reports.times(c["updated_at"])}</td><td>{c["reobservations"]}</td><td><a href="/reports/{stem}.html">open</a></td></tr>'
    body += '</table></div>'
    reports.atomic_write(path, reports.page('Shadow engine queue', body))


def write_status(store, started, summary, config, error=None):
    now = time.time()
    day = int(now // 86400)
    counts = {r[0]: r[1] for r in store.cx.execute('SELECT category, COUNT(*) FROM cases GROUP BY category')}
    cursor = store.get('cursor') or 0
    state_file = STATE / 'state.sqlite3'
    value = dict(at=now, engine=config['version'], state_bytes=state_file.stat().st_size if state_file.exists() else 0, cursor=cursor, collection_lag_s=now - cursor, cases_by_category=counts, warmup_finished=store.get('warmup_finished'),
                 cases_today=store.get(f'emitted:{day}') or 0, reviews_today=store.get(f'review:{day}') or 0, enrichments_today=store.get(f'enriched:{day}') or 0, continuous_market_cases_today=store.get(f'placebo:{day}') or 0,
                 unsealed_cases=max(0, sum(r[0] for r in store.cx.execute('SELECT version FROM cases')) - (store.get('sealed') or 0) - (store.get('placebo_total') or 0)), state_rows=store.cx.execute('SELECT COUNT(*) FROM trades').fetchone()[0],
                 max_rss_mb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1048576, duration_s=now - started, free_disk_gb=shutil.disk_usage('/').free / 1e9, last_run=summary, error=error)
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    temp = STATUS.with_suffix('.tmp')
    temp.write_text(json.dumps(value, indent=1, ensure_ascii=False))
    temp.replace(STATUS)
    return value


def process(store, cx, trades, now, config, emit=True, journal=JOURNAL, report_dir=REPORTS):
    touched = store.add_trades(trades)
    refresh_markets(store, cx, trades, now)
    outputs, summary = run_cycle(store, touched, now, config, emit=emit, commit=False, public_known=lambda e: public_milestone(cx, e) is not None)
    day = int(now // 86400)
    placebo = [o for o in outputs if o['continuous_market']]
    if placebo:
        store.put(f'placebo:{day}', (store.get(f'placebo:{day}') or 0) + len(placebo))
        store.put('placebo_total', (store.get('placebo_total') or 0) + sum(1 for _ in placebo))
    real = [o for o in outputs if not o['continuous_market']]
    apply_review_budget(real, store.get(f'review:{day}') or 0, config)
    for output in real:
        wallets = [p['wallet'] for p in output['pairs']]
        rows = event_rows(store, output['event_key'], wallets)
        gaps = coverage_gaps(cx, min((r['ts'] for r in rows), default=now), now)
        case = dossiers.build(output, rows, config, gaps=gaps, public_milestone=public_milestone(cx, output['event_key']))
        stem = dossiers.write(case, report_dir)
        seal = append_link(journal, 'case', dict(event_key=output['event_key'], version=output['version'], category=output['category'], new_case=output['new_case'], wallets=wallets, file=stem, fingerprint=fingerprint(case),
                                                 observed_to_decision_s=now - max(r['observed_at'] for r in rows), trade_to_decision_s=now - max(r['ts'] for r in rows)), now)
        store.put(f'emitted:{day}', (store.get(f'emitted:{day}') or 0) + 1)
        store.put('sealed', (store.get('sealed') or 0) + 1)
        if output['wants_review'] and not output['already_review']:
            store.put(f'review:{day}', (store.get(f'review:{day}') or 0) + 1)
            append_link(journal, 'notification', dict(event_key=output['event_key'], result=notify(output), case=seal['sha256']), now)
            pending = store.get('enrichment_queue') or []
            pending.append(dict(event_key=output['event_key'], due=now + config['enrichment_delay_s'], case_sha=seal['sha256'], output=output))
            store.put('enrichment_queue', pending[-10:])
    store.cx.commit()
    return summary


def run_due_enrichment(store, cx, now, config, journal=JOURNAL, report_dir=REPORTS, enricher=enrich):
    """Evidence arrives after the alert and in its own version: the sealed one stays as it was."""
    day = int(now // 86400)
    pending = store.get('enrichment_queue') or []
    due = next((p for p in pending if p['due'] <= now), None)
    if due is None or (store.get(f'enriched:{day}') or 0) >= config['enrichments_per_day']:
        return None
    pending.remove(due)
    store.put('enrichment_queue', pending)
    store.put(f'enriched:{day}', (store.get(f'enriched:{day}') or 0) + 1)
    store.cx.commit()
    result = enricher(due['output'], config)
    if result.get('links') is not None:
        store.put('funding:' + due['event_key'], result['links'])
    output = dict(due['output'], version=f"{due['output']['version']}-enriched", new_case=False, at=now)
    wallets = [p['wallet'] for p in output['pairs']]
    rows = event_rows(store, output['event_key'], wallets)
    case = dossiers.build(output, rows, config, gaps=coverage_gaps(cx, min((r['ts'] for r in rows), default=now), now), public_milestone=public_milestone(cx, output['event_key']), enrichment=result)
    stem = dossiers.write(case, report_dir)
    append_link(journal, 'enrichment', dict(event_key=output['event_key'], alert=due['case_sha'], file=stem, fingerprint=fingerprint(case), reconciled=len(result.get('reconciled', [])), funding_links=len(result.get('links') or []), errors=len(result.get('errors') or [])), now)
    store.cx.commit()
    return stem


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('seal', 'amend', 'warmup', 'once', 'status', 'verify'))
    parser.add_argument('--reason')
    args = parser.parse_args()
    if args.command == 'verify':
        print(json.dumps(verify_chain(JOURNAL)))
        return 0
    config = load_config()
    if args.command == 'seal':
        if JOURNAL.exists():
            raise SystemExit('Already sealed; a change needs an amendment')
        link = append_link(JOURNAL, 'genesis', dict(engine=config['version'], fingerprints=code_fingerprints(), config=config, mode='shadow'), time.time())
        print(json.dumps({k: link[k] for k in ('n', 'kind', 'at', 'sha256')}))
        return 0
    if args.command == 'amend':
        if not args.reason:
            raise SystemExit('An amendment needs a dated reason: --reason')
        link = append_link(JOURNAL, 'amendment', dict(engine=config['version'], fingerprints=code_fingerprints(), config=config, reason=args.reason), time.time())
        print(json.dumps({k: link[k] for k in ('n', 'kind', 'at', 'sha256')}))
        return 0
    require_sealed_version(JOURNAL)
    store = SignalStore(STATE / 'state.sqlite3')
    started = time.time()
    if args.command == 'status':
        print(json.dumps(write_status(store, started, {}, config), ensure_ascii=False, indent=1))
        return 0
    free = shutil.disk_usage('/').free
    if free < DISK_FLOOR:
        write_status(store, started, dict(refused=f'{free / 1e9:.2f} GB free, under the shared floor'), config)
        return 0
    if (STATE / 'state.sqlite3').stat().st_size > STATE_LIMIT:
        write_status(store, started, dict(refused='State over its size limit; run stopped, nothing deleted'), config)
        return 0
    cx = open_collector()
    summary = dict(pairs=0, rows=0, no_comparator=0)
    ceiling = config['memory_ceiling_mb'] * 1048576
    try:
        if args.command == 'warmup':
            # Past rows build state and comparators hour by hour. They can never open a case.
            cursor = store.get('cursor') or 0
            while True:
                trades = read_new_trades(cx, cursor, 6000)
                if not trades:
                    store.put('warmup_finished', time.time())
                    break
                hour_end = trades[0]['observed_at'] - trades[0]['observed_at'] % 3600 + 3600
                batch = [t for t in trades if t['observed_at'] < hour_end] or trades
                result = process(store, cx, batch, hour_end, config, emit=False)
                cursor = batch[-1]['observed_at']
                store.put('cursor', cursor)
                store.cx.commit()
                summary['rows'] += len(batch)
                summary['pairs'] += result['pairs']
                if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss > ceiling or time.time() - started > 3000:
                    summary['stopped'] = 'memory or time ceiling; rerun to continue'
                    break
        else:
            if not store.get('warmup_finished'):
                raise RuntimeError('Warm-up not finished')
            cursor = store.get('cursor') or 0
            for _ in range(5):
                trades = read_new_trades(cx, cursor)
                if not trades:
                    break
                now = time.time()
                result = process(store, cx, trades, now, config)
                cursor = trades[-1]['observed_at']
                store.put('cursor', cursor)
                store.cx.commit()
                summary['rows'] += len(trades)
                summary['pairs'] += result['pairs']
                summary['no_comparator'] += result['no_comparator']
                if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss > ceiling:
                    summary['stopped'] = 'memory ceiling'
                    break
            run_due_enrichment(store, cx, time.time(), config)
            run_post_event(store, cx, time.time(), config)
            if store.get('purged') != int(time.time() // 86400):
                store.purge(time.time(), config['retention_days'], config['comparator_days'])
                store.put('purged', int(time.time() // 86400))
                store.cx.commit()
            queue_page(store)
        write_status(store, started, summary, config)
    except Exception as exc:
        write_status(store, started, summary, config, error=f'{type(exc).__name__}: {exc}'[:500])
        raise
    finally:
        cx.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
