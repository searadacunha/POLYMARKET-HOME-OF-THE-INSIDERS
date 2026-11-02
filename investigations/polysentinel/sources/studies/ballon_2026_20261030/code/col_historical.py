"""Bounded public reconstruction; receipt time is never backdated."""
import argparse
import collections
import gzip
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

import httpx

STUDY = Path(__file__).resolve().parents[1]
ROOT = STUDY.parents[1]
sys.path.insert(0, str(ROOT))
from polysentinel.collect import normalize_trade, SourceError

CUTOFF = 1793044800  # 2026-10-26T20:00:00Z
PUBLIC_CUTOFF = 1792768669  # 2026-10-23T15:17:49Z
START = CUTOFF - 30 * 86400
MAX_REQUESTS = 100
MAX_BYTES = 150_000_000


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def search_pagination(value):
    paging = value.get('pagination')
    if not isinstance(paging, dict) or not isinstance(paging.get('hasMore'), bool):
        raise ValueError('search pagination missing or invalid')
    return paging


class Acquisition:
    def __init__(self):
        self.base = STUDY / 'data'
        self.raw = self.base / 'raw'
        self.raw.mkdir(parents=True, exist_ok=True)
        self.log = self.base / 'requests.jsonl'
        self.requests = [json.loads(x) for x in self.log.read_text().splitlines()] if self.log.exists() else []
        self.client = httpx.Client(timeout=30, follow_redirects=False, trust_env=False,
                                   headers={'User-Agent': 'PolySentinelHistoricalStudy/1.0 public-read-only'})

    def get(self, url, params):
        if len(self.requests) >= MAX_REQUESTS:
            raise RuntimeError('request budget exhausted')
        if sum(x.get('bytes', 0) for x in self.requests) + 8_000_000 > MAX_BYTES:
            raise RuntimeError('byte budget exhausted')
        if shutil.disk_usage(STUDY).free < 12_008_000_000:
            raise RuntimeError('12 GB free-space floor')
        time.sleep(0.6)
        row = dict(request=len(self.requests) + 1, url=url, params=params, started_at=time.time())
        try:
            with self.client.stream('GET', url, params=params) as response:
                row.update(status=response.status_code, headers=dict(response.headers))
                chunks = []
                size = 0
                for chunk in response.iter_bytes():
                    size += len(chunk)
                    if size > 8_000_000:
                        raise RuntimeError('response exceeds 8 MB ceiling')
                    chunks.append(chunk)
                body = b''.join(chunks)
            row.update(observed_at=time.time(), bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
            destination = self.raw / f'{row["request"]:03d}.json'
            with destination.open('xb') as stream:
                stream.write(body)
            row['path'] = str(destination.relative_to(STUDY))
            if row['status'] != 200:
                raise RuntimeError(f'HTTP {row["status"]}')
            value = json.loads(body)
            row['valid_json'] = True
            return value, row
        except Exception as exc:
            row['error'] = f'{type(exc).__name__}: {exc}'
            raise
        finally:
            self.requests.append(row)
            with self.log.open('a') as stream:
                stream.write(json.dumps(row, ensure_ascii=False) + '\n')


def search(acquisition):
    found = {}
    pages = []
    for query in ('Ballon', "Ballon d'Or 2026", 'Ballon 2026'):
        for page in range(1, 5):
            value, receipt = acquisition.get('https://gamma-api.polymarket.com/public-search',
                dict(q=query, limit_per_type=100, page=page, keep_closed_markets=1,
                     search_profiles='false', search_tags='false'))
            if not isinstance(value, dict) or not isinstance(value.get('events'), list):
                raise ValueError('search envelope lacks events array')
            paging = search_pagination(value)
            pages.append(dict(query=query, page=page, count=len(value['events']),
                              pagination=paging, evidence=receipt['path']))
            for event in value['events']:
                title = str(event.get('title', ''))
                if 'ballon' in title.lower() and '2026' in title:
                    found[str(event['id'])] = dict(event=event, observed_at=receipt['observed_at'], evidence=receipt['path'])
            if not paging['hasMore']:
                break
        else:
            pages[-1]['stop_reason'] = 'four-page search budget; incomplete'
    dump(acquisition.base / 'catalog_search.json', dict(events=list(found.values()), pages=pages,
        completeness='Search results only; query matching is not proof of an exhaustive market universe.'))
    print(json.dumps(dict(events=len(found), pages=pages, titles=[(k,v['event']['title'],len(v['event'].get('markets',[]))) for k,v in found.items()]),ensure_ascii=False))


def collect(acquisition):
    if (acquisition.base / 'collection_summary.json').exists():
        raise RuntimeError('Completed bounded acquisition exists; use validate-export without refetching')
    catalog = json.loads((acquisition.base / 'catalog_search.json').read_text())
    all_events = {}
    all_markets = {}
    refreshed = []
    for item in catalog['events']:
        event_id = str(item['event']['id'])
        event, receipt = acquisition.get('https://gamma-api.polymarket.com/events/' + event_id, {})
        if not isinstance(event, dict) or str(event.get('id')) != event_id or not isinstance(event.get('markets'), list):
            raise ValueError('event shape or identity mismatch')
        refreshed.append(dict(event=event, observed_at=receipt['observed_at'], evidence=receipt['path']))
        all_events[str(event['slug'])] = dict(id=event_id)
        for market in event['markets']:
            condition = str(market.get('conditionId', '')).lower()
            if condition in all_markets and all_markets[condition] != dict(id=str(market['id']), event_id=event_id):
                raise ValueError('condition mapping conflict')
            all_markets[condition] = dict(id=str(market['id']), event_id=event_id)
    dump(acquisition.base / 'catalog_refreshed.json', dict(events=refreshed,observed_at=time.time()))
    streams = {}
    for event_id in sorted({v['id'] for v in all_events.values()}):
        streams[event_id] = dict(params=dict(event_id=event_id, limit=1000, taker_only='true'),
            pages=0, rows=0, raw_rows_received=0, valid_rows=0, rejected_rows=0, min_timestamp=None,max_timestamp=None,
            done=False, count_timestamp=None, counts={}, cursor=None, seen_cursors=[])
    trades = []
    rejected = []
    # Round robin avoids letting one busy event consume the entire request budget.
    while any(not s['done'] for s in streams.values()) and len(acquisition.requests) < MAX_REQUESTS:
        for event_id, state in streams.items():
            if state['done'] or len(acquisition.requests) >= MAX_REQUESTS:
                continue
            params = dict(state['params'])
            if state['cursor']:
                params['cursor'] = state['cursor']
            try:
                value, receipt = acquisition.get('https://data-api.polymarket.com/v2/trades', params)
                if not isinstance(value,dict) or not isinstance(value.get('data'),list) or not isinstance(value.get('pagination'),dict):
                    raise ValueError('trade envelope invalid')
                paging = value['pagination']
                cursor = paging.get('next_cursor')
                if not isinstance(paging.get('has_more'),bool) or bool(cursor) != paging['has_more']:
                    raise ValueError('trade pagination incoherent')
                if cursor is not None and (not isinstance(cursor,str) or cursor in state['seen_cursors']):
                    raise ValueError('trade cursor invalid or repeated')
                if not value['data'] and cursor:
                    raise ValueError('empty page with continuation')
                state['raw_rows_received'] += len(value['data'])
                for raw in value['data']:
                    state['rows'] += 1
                    try:
                        trade = normalize_trade(raw, receipt['observed_at'], all_markets, all_events)
                        timestamp = trade['timestamp']
                        if state['count_timestamp'] is not None and timestamp > state['count_timestamp']:
                            raise ValueError('trade feed not descending')
                        if timestamp != state['count_timestamp']:
                            state['counts'] = {}
                            state['count_timestamp'] = timestamp
                        signature = trade['signature']
                        occurrence = state['counts'].get(signature,0) + 1
                        state['counts'][signature] = occurrence
                        trade.update(id=f'{signature}:{occurrence}',occurrence=occurrence,evidence_path=receipt['path'],
                                     reconstruction=True,actually_observed_at=receipt['observed_at'])
                        if trade['event_id'] != event_id:
                            raise ValueError('trade outside requested event')
                        trades.append(trade)
                        state['valid_rows'] += 1
                        state['min_timestamp'] = timestamp if state['min_timestamp'] is None else min(timestamp,state['min_timestamp'])
                        state['max_timestamp'] = timestamp if state['max_timestamp'] is None else max(timestamp,state['max_timestamp'])
                    except SourceError as exc:
                        state['rejected_rows'] += 1
                        rejected.append(dict(event_id=event_id, raw=raw, reason=str(exc), evidence_path=receipt['path']))
                state['pages'] += 1
                state['cursor'] = cursor
                if cursor:
                    state['seen_cursors'].append(cursor)
                if not cursor:
                    state.update(done=True, stop_reason='API pagination exhausted; taker-side only')
                elif state['min_timestamp'] is not None and state['min_timestamp'] < START:
                    state.update(done=True, stop_reason='30-day lower boundary crossed')
            except Exception as exc:
                state.update(done=True, stop_reason='error', error=f'{type(exc).__name__}: {exc}')
            dump(acquisition.base / 'collection_progress.json', streams)
    for state in streams.values():
        state['unprocessed_rows'] = state['raw_rows_received'] - state['valid_rows'] - state['rejected_rows']
        state.pop('counts',None)
        state.pop('seen_cursors',None)
        if not state['done']:
            state['stop_reason'] = 'request or byte budget; incomplete'
    (acquisition.base / 'trades_normalized.jsonl').write_text(''.join(json.dumps(t,ensure_ascii=False)+'\n' for t in trades))
    dump(acquisition.base / 'trades_rejected.json', rejected)
    summary = dict(cutoff=CUTOFF,lower_boundary=START,streams=streams,normalized_rows=len(trades),rejected_rows=len(rejected),
        pre_ceremony_rows=sum(START<=t['timestamp']<CUTOFF for t in trades),
        requests=len(acquisition.requests),responses=sum('status' in x for x in acquisition.requests),
        empty_trade_responses=sum(json.loads((STUDY/x['path']).read_text()).get('data')==[] for x in acquisition.requests if x.get('status')==200 and '/v2/trades' in x['url']),
        errors=sum('error' in x for x in acquisition.requests),http_429=sum(x.get('status')==429 for x in acquisition.requests),
        stream_errors=sum('error' in x for x in streams.values()),
        raw_bytes=sum(x.get('bytes',0) for x in acquisition.requests),
        limitations=['Current metadata never certifies pre-event open/liquidity/status.',
        'Receipt timestamp remains actual present collection time.', 'No press wallets or results used to select events.',
        'Search universe is not externally certified exhaustive.', 'Taker-side feed does not include all maker accounts.'])
    dump(acquisition.base/'collection_summary.json',summary)
    print(json.dumps(summary,ensure_ascii=False))


def validate_export():
    """Reconcile every saved row against its raw response; never fetch or backdate."""
    base = STUDY / 'data'
    receipts = [json.loads(line) for line in (base/'requests.jsonl').read_text().splitlines()]
    if [r['request'] for r in receipts] != list(range(1, len(receipts)+1)):
        raise ValueError('request sequence is not contiguous')
    paths = {r['path'] for r in receipts if 'path' in r}
    if paths != {str(p.relative_to(STUDY)) for p in (base/'raw').glob('*.json')}:
        raise ValueError('orphan or missing raw response')
    catalogue = json.loads((base/'catalog_refreshed.json').read_text())
    markets, events = {}, {}
    for item in catalogue['events']:
        event = item['event']; event_id = str(event['id'])
        if event != json.loads((STUDY/item['evidence']).read_text()):
            raise ValueError('catalogue differs from raw event response')
        events[event['slug']] = dict(id=event_id)
        for market in event['markets']:
            condition = str(market['conditionId']).lower()
            target = dict(id=str(market['id']), event_id=event_id)
            if condition in markets and markets[condition] != target:
                raise ValueError('ambiguous condition mapping')
            markets[condition] = target
    normalized = iter((base/'trades_normalized.jsonl').open())
    counters, states = collections.defaultdict(lambda: collections.Counter(
        requested=0,responses=0,empty_responses=0,transport_or_http_errors=0,http_429=0)), {}
    economic_counts = collections.Counter()
    fields = ('id','wallet','side','size','price','timestamp','observed_at','actually_observed_at',
              'transaction_hash','condition_id','token_id','event_id','market_id','evidence_path')
    output = base/'trades_minimal.jsonl.gz'
    if output.exists():
        raise RuntimeError('Minimal export already exists; preserve it')
    partial = output.with_suffix(output.suffix+'.partial')
    with partial.open('xb') as target, gzip.GzipFile(filename='trades_minimal.jsonl',fileobj=target, mode='wb', mtime=0) as out:
        for receipt in receipts:
            count = counters[receipt['url'].split('?')[0]]
            count['requested'] += 1
            count['responses'] += int('status' in receipt)
            count['http_429'] += int(receipt.get('status') == 429)
            count['transport_or_http_errors'] += int('error' in receipt)
            if 'path' not in receipt:
                continue
            raw_bytes = (STUDY/receipt['path']).read_bytes()
            if hashlib.sha256(raw_bytes).hexdigest() != receipt['sha256']:
                raise ValueError('raw response checksum mismatch')
            value = json.loads(raw_bytes)
            if '/public-search' in receipt['url']:
                search_pagination(value)
                count['empty_responses'] += int(not value['events'])
            if not receipt['url'].endswith('/v2/trades') or receipt.get('status') != 200:
                continue
            event_id = receipt['params']['event_id']
            state = states.setdefault(event_id, dict(cursor=None,last_timestamp=None,counts={}))
            if receipt['params'].get('cursor') != state['cursor']:
                raise ValueError('request cursor does not follow previous response')
            paging = value['pagination']; rows = value['data']
            if not isinstance(rows,list) or not isinstance(paging.get('has_more'),bool) or bool(paging.get('next_cursor')) != paging['has_more']:
                raise ValueError('invalid saved trade pagination')
            count['raw_rows_received'] += len(rows)
            count['empty_responses'] += int(not rows)
            state['cursor'] = paging.get('next_cursor')
            for raw in rows:
                trade = normalize_trade(raw,receipt['observed_at'],markets,events)
                timestamp = trade['timestamp']
                if state['last_timestamp'] is not None and timestamp > state['last_timestamp']:
                    raise ValueError('saved feed order violation')
                if timestamp != state['last_timestamp']:
                    state.update(last_timestamp=timestamp,counts={})
                signature = trade['signature']; occurrence = state['counts'].get(signature,0)+1
                state['counts'][signature] = occurrence
                trade.update(id=f'{signature}:{occurrence}',occurrence=occurrence,evidence_path=receipt['path'],
                             reconstruction=True,actually_observed_at=receipt['observed_at'])
                if trade['event_id'] != event_id or trade != json.loads(next(normalized)):
                    raise ValueError('normalized row differs from raw reconstruction')
                out.write((json.dumps({k:trade[k] for k in fields},separators=(',',':'))+'\n').encode())
                count['normalized_rows'] += 1
                economic_counts['before_public'] += int(START <= timestamp < PUBLIC_CUTOFF)
                economic_counts['before_ceremony'] += int(START <= timestamp < CUTOFF)
                economic_counts['before_lower_boundary'] += int(timestamp < START)
                economic_counts['at_or_after_ceremony'] += int(timestamp >= CUTOFF)
                economic_counts['actually_observed_before_public'] += int(trade['observed_at'] < PUBLIC_CUTOFF)
                economic_counts['actually_observed_before_ceremony'] += int(trade['observed_at'] < CUTOFF)
        if next(normalized,None) is not None:
            raise ValueError('normalized rows without raw counterpart')
    partial.rename(output)
    summary = json.loads((base/'collection_summary.json').read_text())
    validation = dict(status='PASS',validation_errors=0,raw_checksums_verified=len(paths),sources=dict(counters),
        catalogue_raw_reconciled_events=len(catalogue['events']),
        economic_counts=dict(economic_counts),primary_cutoff=PUBLIC_CUTOFF,secondary_cutoff=CUTOFF,
        lower_boundary=START,stream_errors={k:v['error'] for k,v in summary['streams'].items() if 'error' in v},
        incomplete_streams=[k for k,v in summary['streams'].items() if not v['done'] or 'error' in v],
        minimal_export=str(output.relative_to(STUDY)),minimal_sha256=hashlib.sha256(output.read_bytes()).hexdigest(),
        dependency_sha256={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ('polysentinel/collect.py','polysentinel/net.py')},
        note='Reconciliation verifies saved rows, not historical universe completeness or on-chain execution.')
    dump(base/'collection_validation.json',validation)
    print(json.dumps(validation,ensure_ascii=False))


def self_check():
    from datetime import datetime,timezone
    assert datetime.fromtimestamp(CUTOFF,timezone.utc).isoformat() == '2026-10-26T20:00:00+00:00'
    assert datetime.fromtimestamp(PUBLIC_CUTOFF,timezone.utc).isoformat() == '2026-10-23T15:17:49+00:00'
    for value in ({},{'pagination':{}},{'pagination':{'hasMore':'false'}}):
        try:search_pagination(value)
        except ValueError:pass
        else:raise AssertionError('missing pagination accepted')
    assert search_pagination({'pagination':{'hasMore':False}})['hasMore'] is False
    raw=dict(proxy_wallet='0x'+'1'*40, transaction_hash='0x'+'2'*64, condition_id='0x'+'3'*64,
             token_id='123', side='BUY', size=2, price=.5, timestamp=CUTOFF-1)
    t=normalize_trade(raw,CUTOFF+86400,{}, {})
    assert t['observed_at']>CUTOFF and t['timestamp']<CUTOFF and t['nominal']==1
    for key,bad in [('price',float('nan')),('side','invalid'),('proxy_wallet','not-address')]:
        try:normalize_trade(dict(raw,**{key:bad}),CUTOFF+86400,{}, {})
        except SourceError:pass
        else:raise AssertionError(key)
    print('PASS cutoff, two clocks, amount, malformed rows')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['search','collect','self-check','validate-export']);args=p.parse_args()
    if args.mode=='self-check':self_check()
    elif args.mode=='validate-export':validate_export()
    else:
        a=Acquisition()
        try:(search if args.mode=='search' else collect)(a)
        finally:a.client.close()
