"""Read-only coverage of catalogued markets; collection age is not trade age."""
from collections import Counter
import json
import time

RECENT_SECONDS = 600
MARKET_PREFIX = 'trades:market:'
STATUSES = ('collection_recent_complete', 'stale', 'error', 'backlogged',
            'never_attempted', 'incomplete_unknown')


def _age(now, at):
    return None if at is None else now - at


def _latest(*values):
    return max((v for v in values if isinstance(v, (int, float))), default=None)


def _scope(key):
    if key.startswith(MARKET_PREFIX) and key[len(MARKET_PREFIX):] and ':' not in key[len(MARKET_PREFIX):]:
        return 'market'
    if key == 'trades:global':
        return 'global'
    if key.startswith('catalog:') and key != 'catalog:tag_rotation':
        return 'catalog'
    parts = key.split(':')
    if len(parts) >= 3 and parts[0] == 'investigate' and parts[2] in ('trades', 'activity', 'positions'):
        tail=parts[3:]
        if len(tail)>=2 and tail[0]=='event' and tail[1].isdigit():tail=tail[2:]
        if not tail or tail[0] in ('head','gap'):
            return 'wallet'
    return None


def _flow(key, checkpoint, records, now, trade=None, gaps=None, rejections=None):
    state, checkpoint_at = checkpoint or ({}, None)
    metrics, metrics_at = max(records, key=lambda r: r[1], default=({}, None))
    scope = _scope(key)
    pending = [w for w in state.get('pending', []) if not w.get('done')]
    active = state.get('active')
    last_success = _latest(state.get('last_success'), *(r[0].get('last_success') for r in records))
    last_attempt = _latest(checkpoint_at, metrics_at, metrics.get('last_attempt'))
    # Catalogue/wallet checkpoints attest successful pages, not completed windows.
    if scope in ('catalog', 'wallet'):
        last_success = _latest(last_success, state.get('observed_at'), state.get('updated_at'))
    rejected = metrics.get('rejected', 0) or 0
    error = metrics.get('status') in ('error', 'degraded') or bool(metrics.get('errors')) or rejected > 0
    unfinished = bool(pending or (active and not active.get('done')) or state.get('cursor')
                      or metrics.get('pending_walks', 0) or metrics.get('status') == 'capped')
    if scope in ('catalog', 'wallet'):
        complete = state.get('complete') is True and not unfinished
    elif checkpoint:
        complete = last_success is not None and not active and not unfinished
    else:
        complete = metrics.get('status') in ('ok', 'empty') and metrics.get('pending_walks') == 0
    complete = complete and not error
    age = _age(now, last_success)
    if error:
        status = 'error'
    elif unfinished:
        status = 'backlogged'
    elif complete and age is not None and 0 <= age <= RECENT_SECONDS:
        status = 'collection_recent_complete'
    elif complete and age is not None and age > RECENT_SECONDS:
        status = 'stale'
    else:
        status = 'incomplete_unknown'
    walks = ([active] if active else []) + pending
    ranges = {name: metrics.get('range_' + name, metrics.get(name)) for name in ('oldest', 'newest')}
    if ranges['newest'] is None:
        ranges['newest'] = state.get('watermark')
    trade_measured = trade is not None
    trade = trade or {}
    return dict(stream=key, scope=scope, params=state.get('params', state.get('filters', metrics.get('params'))),
                status=status, source_status=metrics.get('status'), last_success=last_success,
                last_attempt=last_attempt, collection_age_seconds=age,
                complete_accessible_window=bool(complete), cutoff=metrics.get('cutoff', state.get('filters', {}).get('start')),
                **ranges, watermark=state.get('watermark'), window_end=state.get('window_end'),
                cache_age=metrics.get('cache_age', active.get('cache_age') if active else None),
                pending_walks=max(len(pending), metrics.get('pending_walks', 0) or 0),
                active_walk=bool(active), cursor=state.get('cursor'),
                walks=[{k: w.get(k) for k in ('params', 'cursor', 'cutoff', 'oldest', 'newest', 'done',
                                            'observed_at', 'cache_age', 'recovered')} for w in walks],
                recovered=bool(metrics.get('recovered') or any(w.get('recovered') for w in walks)),
                recoveries=state.get('recoveries'), gaps=(gaps or {}).get('count', 0),
                latest_gap_at=(gaps or {}).get('latest_at'),
                rejected_latest_attempt=rejected, rejected_rows_retained=(rejections or {}).get('count', 0),
                latest_rejection_at=(rejections or {}).get('latest_at'),
                ingested_trades=trade.get('count', 0) if trade_measured else None, latest_ingested_trade_at=trade.get('newest'),
                latest_ingested_trade_age_seconds=_age(now, trade.get('newest')))


def measure_coverage(store, now=None, include_streams=False):
    """Return small aggregate counts, optionally with every market and feed scope.

    Eligible status counts partition eligible markets; excluded reasons partition
    all other catalogued markets. Interrogated and ingested counts cover the whole
    catalogue, with eligible-only counterparts. A successful bounded collection
    says nothing about price freshness or completeness before its cutoff.
    Uses the supplied connection without opening, migrating, or writing a store.
    """
    now = time.time() if now is None else now
    cx = store.conn
    indexed = cx.execute("SELECT 1 FROM sqlite_master WHERE name='trade_index'").fetchone() is not None
    if indexed:
        trade_sql = 'SELECT condition_id,COUNT(*),MIN(trade_time),MAX(trade_time) FROM trade_index GROUP BY condition_id'
    else:
        trade_sql = """SELECT json_extract(payload,'$.condition_id'),COUNT(*),
            MIN(json_extract(payload,'$.timestamp')),MAX(json_extract(payload,'$.timestamp'))
            FROM objects WHERE kind='trade' GROUP BY 1"""
    trades = {r[0]: dict(count=r[1], oldest=r[2], newest=r[3]) for r in cx.execute(trade_sql)}
    checkpoints = {r[0]: (json.loads(r[1]), r[2]) for r in cx.execute(
        "SELECT key,value,updated_at FROM checkpoints WHERE key GLOB 'trades:*'" +
        (" OR key GLOB 'catalog:*' OR key GLOB 'investigate:*'" if include_streams else '')) if _scope(r[0])}
    records = {}
    coverage_keys = set()
    for kind, key, payload, at in cx.execute("SELECT kind,key,payload,observed_at FROM objects WHERE kind IN ('health','market_coverage')"):
        if kind == 'market_coverage':
            coverage_keys.add(key)
            key = MARKET_PREFIX + key
        scope = _scope(key)
        if scope and (include_streams or scope == 'market'):
            records.setdefault(key, []).append((json.loads(payload), at))
    from .priority import market_snapshots, market_exclusion_reason
    from .provenance import source_sets
    sources=source_sets(store,now)
    source_counts=Counter();eligible_sources=Counter()
    counts = dict(catalogued=0, eligible=0, individually_interrogated=0, with_ingested_trades=0,
                  eligible_interrogated=0, eligible_with_ingested_trades=0, excluded=0,
                  **{s: 0 for s in STATUSES})
    exclusions = Counter()
    status_all_interrogated = Counter({s: 0 for s in STATUSES if s != 'never_attempted'})
    market_rows, streams, catalog_keys = [], {}, set()
    gaps, rejections = {}, {}
    if include_streams:
        for kind, target in (('gap', gaps), ('rejected_trade', rejections)):
            for stream, n, at in cx.execute("""SELECT json_extract(payload,'$.stream'),COUNT(*),MAX(observed_at)
                    FROM objects WHERE kind=? GROUP BY 1""", (kind,)):
                target[stream] = dict(count=n, latest_at=at)
    for market,event,_,_ in market_snapshots(store,now):
        key=market['id']
        excluded_reason=market_exclusion_reason(market,event,now)
        catalog_keys.add(key)
        stream = MARKET_PREFIX + key
        attempted = stream in checkpoints or key in coverage_keys
        trade = trades.get(str(market.get('condition_id', '')).lower(), {})
        feeds=sources.get(str(market.get('condition_id','')).lower(),set())
        category=('both' if {'global','individual'}<=feeds else 'global_only' if 'global' in feeds else
                  'individual_only' if 'individual' in feeds else 'other_feed' if feeds else 'unattributed')
        if trade.get('count'):
            source_counts[category]+=1
            if not excluded_reason:eligible_sources[category]+=1
        counts['catalogued'] += 1
        counts['individually_interrogated'] += int(attempted)
        counts['with_ingested_trades'] += int(bool(trade.get('count')))
        flow = _flow(stream, checkpoints.get(stream), records.get(stream, []), now, trade,
                     gaps.get(stream), rejections.get(stream)) if attempted else None
        if flow:
            status_all_interrogated[flow['status']] += 1
        if excluded_reason:
            counts['excluded'] += 1
            exclusions[excluded_reason] += 1
            status = 'excluded'
        else:
            counts['eligible'] += 1
            counts['eligible_interrogated'] += int(attempted)
            counts['eligible_with_ingested_trades'] += int(bool(trade.get('count')))
            status = flow['status'] if flow else 'never_attempted'
            counts[status] += 1
        if include_streams:
            market_rows.append(dict(market_id=key, event_id=market.get('event_id'),
                                    condition_id=market.get('condition_id'), eligible=excluded_reason is None,
                                    excluded_reason=excluded_reason, status=status, individually_interrogated=attempted,
                                    ingested_trades=trade.get('count', 0),
                                    observed_feeds=sorted(feeds),history_complete_certified=False,
                                    last_success=flow['last_success'] if flow else None,
                                    collection_age_seconds=flow['collection_age_seconds'] if flow else None,
                                    latest_ingested_trade_at=trade.get('newest'),
                                    latest_ingested_trade_age_seconds=_age(now, trade.get('newest'))))
            if flow:
                streams[stream] = flow
    result = dict(generated_at=now, recent_window_seconds=RECENT_SECONDS, counts=counts,
                  source_presence=dict(all_catalogued_with_trades=dict(source_counts),
                      eligible_with_trades=dict(eligible_sources),history_complete_certified=0,
                      definition='One witness per condition/feed; historic first-ingestion attribution is a lower bound. Categories partition markets with retained trades; no claim of exhaustive global history.'),
                  excluded_reasons=dict(exclusions), interrogated_status_counts=dict(status_all_interrogated),
                  definitions=dict(eligible='shared market_exclusion_reason: known, open, active, mapped, not expired or publicly resolved; before queue limits',
                                   status_denominator='eligible catalogued markets; mutually exclusive',
                                   interrogated='exact trades:market:<id> checkpoint or market_coverage object',
                                   collection_recent_complete='successful bounded window <=600s old, completed cursor, no current errors/rejections',
                                   trade_age='age of latest retained trade, separate from collection age',
                                   ingested='condition-matched trades from any feed; null for streams without measured attribution',
                                   unknown='completion/success absent, interrupted finalization, or future success timestamp'))
    if include_streams:
        for key in sorted(checkpoints.keys() | records.keys()):
            if key not in streams:
                streams[key] = _flow(key, checkpoints.get(key), records.get(key, []), now,
                                     gaps=gaps.get(key), rejections=rejections.get(key))
        result.update(market_rows=market_rows, streams=[streams[key] for key in sorted(streams)],
                      stream_scope_counts=dict(Counter(flow['scope'] for flow in streams.values())),
                      uncatalogued_market_streams=sum(key[len(MARKET_PREFIX):] not in catalog_keys
                          for key, flow in streams.items() if flow['scope'] == 'market'),
                      unscoped_gaps=gaps.get(None, {}).get('count', 0))
    return result
