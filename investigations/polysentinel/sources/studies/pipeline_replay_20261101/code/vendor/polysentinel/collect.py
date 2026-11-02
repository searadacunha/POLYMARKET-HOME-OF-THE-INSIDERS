"""Incremental catalogue and trade feeds with explicit bounded coverage."""
import hashlib
import json
import math
import re
import time
from urllib.parse import quote

from .net import SourceError, ResponseTooLarge

GAMMA = 'https://gamma-api.polymarket.com'
DATA = 'https://data-api.polymarket.com'
ADDRESS = re.compile(r'^0x[0-9a-fA-F]{40}$')
HASH = re.compile(r'^0x[0-9a-fA-F]{64}$')


def _array(value, name):
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError as exc:
            raise SourceError(f'{name}: tableau JSON invalide') from exc
    if not isinstance(value, list):
        raise SourceError(f'{name}: tableau absent ou invalide')
    return value


def _number(value, name):
    try:
        n = float(value)
    except (TypeError, ValueError) as exc:
        raise SourceError(f'{name}: nombre invalide') from exc
    if not math.isfinite(n):
        raise SourceError(f'{name}: nombre non fini')
    return n


def normalize_event(raw, at, priority_tags):
    if not isinstance(raw, dict) or not raw.get('id'):
        raise SourceError('Événement sans id')
    tags = [str(t['slug']) for t in raw.get('tags', []) if isinstance(t, dict) and t.get('slug')]
    return dict(id=str(raw['id']), title=str(raw.get('title', '')), slug=str(raw.get('slug', '')),
                active=raw.get('active'), closed=raw.get('closed'), end_date=raw.get('endDate'),
                priority=bool(set(tags) & set(priority_tags)), tags=tags, observed_at=at,
                version=raw.get('version'), raw={k:v for k,v in raw.items() if k != 'markets'})


def normalize_market(raw, event, at):
    if not isinstance(raw, dict) or not raw.get('id'):
        raise SourceError('Marché sans id')
    tokens = _array(raw.get('clobTokenIds') or [], 'clobTokenIds')
    outcomes = _array(raw.get('outcomes') or [], 'outcomes')
    mapping_ok = bool(tokens) and len(tokens) == len(outcomes)
    mapping_reason = None if mapping_ok else 'Correspondance tokens/issues indisponible; marché non suivi'
    liquidity = raw.get('liquidityNum', raw.get('liquidity'))
    return dict(id=str(raw['id']), event_id=event['id'], condition_id=str(raw.get('conditionId') or ''),
                question=str(raw.get('question', '')), active=raw.get('active'), closed=raw.get('closed'),
                end_date=raw.get('endDate', event['end_date']),
                liquidity=_number(liquidity, 'liquidity') if liquidity is not None else None,
                tokens=[dict(token_id=str(t), outcome=str(o)) for t,o in zip(tokens,outcomes)] if mapping_ok else [],
                mapping_quality='mapped' if mapping_ok else 'unavailable', coverage_reason=mapping_reason,
                priority=event['priority'], observed_at=at, version=raw.get('version'),
                raw={k:v for k,v in raw.items() if k != 'events'})


def normalize_trade(raw, at, markets, events, ordinal=1):
    if not isinstance(raw, dict):
        raise SourceError('Ligne trade invalide')
    wallet = str(raw.get('proxy_wallet', '')).lower()
    transaction = str(raw.get('transaction_hash', '')).lower()
    condition = str(raw.get('condition_id', '')).lower()
    token = str(raw.get('token_id', ''))
    side = raw.get('side')
    if not ADDRESS.fullmatch(wallet) or not HASH.fullmatch(transaction) or not HASH.fullmatch(condition):
        raise SourceError('Trade: wallet/transaction/condition invalide')
    if side not in ('BUY', 'SELL') or not token.isdecimal():
        raise SourceError('Trade: sens/token invalide')
    size, price = _number(raw.get('size'), 'size'), _number(raw.get('price'), 'price')
    timestamp = _number(raw.get('timestamp'), 'timestamp')
    if size <= 0 or not 0 <= price <= 1 or timestamp <= 0 or timestamp > at + 300:
        raise SourceError('Trade: montant/prix/horodatage hors domaine')
    market = markets.get(condition)
    event = events.get(str(raw.get('event_slug', '')))
    identity = [wallet, transaction, token, side, format(size,'.17g'), format(price,'.17g'), int(timestamp)]
    signature = hashlib.sha256(json.dumps(identity, separators=(',', ':')).encode()).hexdigest()
    return dict(id=f'{signature}:{ordinal}', wallet=wallet, event_id=market['event_id'] if market else (event['id'] if event else ''),
                market_id=market['id'] if market else '', condition_id=condition, token_id=token,
                outcome=str(raw.get('outcome', '')), side=side, timestamp=int(timestamp), observed_at=at,
                size=size, price=price, nominal=size*price, transaction_hash=transaction, fee=None,
                signature=signature, occurrence=ordinal, identity_quality='API sans logIndex; multiplicité conservée',
                event_slug=str(raw.get('event_slug', '')), market_slug=str(raw.get('slug', '')), raw=raw)


class Collector:
    def __init__(self, store, net, config):
        self.store, self.net, self.config = store, net, config

    def _save_events(self, rows, response, key, checkpoint):
        normalized = []
        for raw in rows:
            event = normalize_event(raw, response.observed_at, self.config.get('priority_tags', []))
            markets = [normalize_market(m, event, response.observed_at) for m in raw.get('markets', [])]
            normalized.append((event, markets))
        with self.store.transaction() as cx:
            for event, markets in normalized:
                self.store.put('event', event['id'], event, response.observed_at, conn=cx)
                for market in markets:
                    self.store.put('market', market['id'], market, response.observed_at, conn=cx)
            self.store.checkpoint(key, checkpoint, conn=cx)
        return len(normalized), sum(len(markets) for _,markets in normalized)

    async def _catalog_page(self, params, key, resume=False):
        state = self.store.checkpoint(key) or {}
        query = dict(params)
        if resume and state.get('cursor'):
            query['after_cursor'] = state['cursor']
        query['limit'] = max(1,min(100,int(query.get('limit',20)),int(state.get('page_limit',query.get('limit',20)))))
        recovered = False
        size_reductions = 0
        # Seven sizes at most (100 -> 1), plus one existing invalid-cursor recovery.
        while True:
            try:
                response = await self.net.request(GAMMA + '/events/keyset', query)
                break
            except ResponseTooLarge as exc:
                if exc.status != 200 or query['limit'] <= 1:
                    raise
                query['limit'] = max(1,query['limit']//2)
                size_reductions += 1
            except SourceError as exc:
                # Do not restart or skip a cursor rejected after changing its page size.
                if exc.status != 422 or 'after_cursor' not in query or recovered or size_reductions:
                    raise
                self.store.put('gap', f'{key}:{time.time_ns()}', dict(stream=key,reason='Curseur Gamma invalide; balayage repris depuis le début',
                                                                    old_cursor=state['cursor'], observed_at=time.time()))
                query.pop('after_cursor')
                recovered = True
        body = response.body
        if not isinstance(body, dict) or not isinstance(body.get('events'), list) :
            raise SourceError('Schéma Gamma keyset invalide', response.status, response.evidence_id)
        cursor = body.get('next_cursor')
        if cursor is not None and not isinstance(cursor, str):
            raise SourceError('Curseur Gamma non textuel')
        if cursor and cursor == query.get('after_cursor'):
            raise SourceError('Curseur Gamma immobile')
        checkpoint = dict(cursor=cursor, params=dict(params,limit=query['limit']), page_limit=query['limit'],
                          size_reductions=state.get('size_reductions',0)+size_reductions, observed_at=response.observed_at,
                          rows=len(body['events']), complete=not cursor, recoveries=state.get('recoveries',0)+int(recovered))
        events, markets = self._save_events(body['events'], response, key, checkpoint)
        status = 'capped' if cursor else ('ok' if events else 'empty')
        self.store.health(key, status, 'Catalogue partiel, curseur conservé' if cursor else 'Fin de cette pagination',
                          events=events, markets=markets, observed_at=response.observed_at, recovered=recovered,
                          page_limit=query['limit'],size_reductions=size_reductions)
        return dict(events=events, markets=markets, status=status,page_limit=query['limit'],size_reductions=size_reductions)

    async def catalog(self):
        output = dict(events=0, markets=0, errors=[], streams=[])
        base = dict(closed='false', limit=min(100,self.config.get('catalog_page_size',50)))
        tag_state = self.store.checkpoint('catalog:tag_rotation') or {'index':0}
        tags = self.config.get('priority_tags', [])
        tag = tags[tag_state['index'] % len(tags)] if tags else None
        tasks = []
        for version in ('v1', 'v2'):
            tasks.append((dict(base,version=version,order='createdAt',ascending='false'), f'catalog:new:{version}',False))
            for _ in range(max(1,self.config.get('catalog_pages',4)//2)):
                tasks.append((dict(base,version=version,order='createdAt',ascending='true'), f'catalog:sweep:{version}',True))
            if tag:
                tasks.append((dict(base,version=version,tag_slug=tag,order='createdAt',ascending='false'),f'catalog:tag:{version}:{tag}',True))
        for params,key,resume in tasks:
            try:
                result = await self._catalog_page(params,key,resume)
                output['events'] += result['events']; output['markets'] += result['markets']
                output['streams'].append(dict(stream=key,**result))
            except (SourceError,ValueError,KeyError,TypeError) as exc:
                output['errors'].append(f'{key}: {exc}')
                self.store.health(key,'error',str(exc))
        self.store.checkpoint('catalog:tag_rotation', {'index':tag_state['index']+1})
        # Refresh previously watched events too, including newly closed events.
        rows = self.store.conn.execute("SELECT key FROM objects WHERE kind='event' ORDER BY observed_at LIMIT 2").fetchall()
        for row in rows:
            try:
                await self.resolve_event(row['key'])
            except (SourceError,ValueError,KeyError,TypeError) as exc:
                output['errors'].append(f"refresh:{row['key']}: {exc}")
        output['status'] = 'degraded' if output['errors'] else 'ok'
        return output

    async def resolve_event(self, identifier):
        identifier = str(identifier).strip()
        if identifier.isdecimal():
            path = '/events/' + identifier
        elif re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9-]{0,200}',identifier):
            path = '/events/slug/' + quote(identifier,safe='')
        else:
            raise SourceError('Identifiant événement invalide: id ou slug attendu')
        response = await self.net.request(GAMMA + path)
        if not isinstance(response.body,dict):
            raise SourceError('Schéma événement invalide',response.status,response.evidence_id)
        event = normalize_event(response.body,response.observed_at,self.config.get('priority_tags',[]))
        n,m = self._save_events([response.body],response,'catalog:resolve:'+identifier,
                                {'observed_at':response.observed_at,'evidence_id':response.evidence_id})
        return dict(events=n,markets=m,event_id=event['id'],status='ok')

    def _maps(self):
        markets = {}
        for row in self.store.conn.execute("SELECT payload FROM objects WHERE kind='market'"):
            m=json.loads(row[0]);markets[m['condition_id'].lower()]=dict(id=m['id'],event_id=m['event_id'])
        events = {}
        for row in self.store.conn.execute("SELECT payload FROM objects WHERE kind='event'"):
            e=json.loads(row[0]);events[e['slug']]=dict(id=e['id'])
        return markets,events

    async def _walk_trades(self,key,params,state,walk,pages,maps):
        result = dict(rows=0, matched_rows=0, outside_window=0, inserted=0, rejected=0, pages=0, lag_seconds=None, recovered=False)
        if walk.get('done'):
            return result
        seen_cursors = set()
        for _ in range(pages):
            query = dict(walk.get('params', params))
            if walk.get('cursor'):
                query['cursor']=walk['cursor']
            try:
                response = await self.net.request(DATA+'/v2/trades',query)
            except SourceError as exc:
                if exc.status != 400 or 'cursor' not in query or walk.get('recovered'):
                    raise
                self.store.put('gap',f'{key}:{time.time_ns()}',dict(stream=key,reason='Curseur trades invalide; récupération depuis la tête',
                                                                 cutoff=walk['cutoff'],observed_at=time.time()))
                walk.update(cursor=None,counts={},count_timestamp=None,recovered=True)
                self.store.checkpoint(key,state)
                result['recovered']=True
                query.pop('cursor')
                response=await self.net.request(DATA+'/v2/trades',query)
            body=response.body
            if not isinstance(body,dict) or not isinstance(body.get('data'),list) or not isinstance(body.get('pagination'),dict):
                raise SourceError('Schéma trades v2 invalide',response.status,response.evidence_id)
            paging=body['pagination'];rows=body['data'];cursor=paging.get('next_cursor')
            if not isinstance(paging.get('has_more'),bool) or bool(cursor) != paging['has_more'] or (cursor is not None and not isinstance(cursor,str)):
                raise SourceError('Pagination trades incohérente',response.status,response.evidence_id)
            if cursor and (cursor==walk.get('cursor') or cursor in seen_cursors):
                raise SourceError('Curseur trades immobile ou cyclique')
            if not rows and cursor:
                raise SourceError('Page vide avec suite: couverture inconnue')
            # Validate the whole page before advancing any durable checkpoint.
            counts=dict(walk.get('counts',{}));count_ts=walk.get('count_timestamp');normalized=[];rejected=[]
            oldest=walk.get('oldest');newest=walk.get('newest')
            for row in rows:
                try:
                    trade=normalize_trade(row,response.observed_at,*maps)
                except SourceError as exc:
                    rejected.append(dict(raw=row,reason=str(exc),stream=key,evidence_id=response.evidence_id,observed_at=response.observed_at))
                    continue
                timestamp=trade['timestamp']
                if count_ts is not None and timestamp>count_ts:
                    raise SourceError('Trades désordonnés: le curseur ne décrit plus un parcours DESC')
                if count_ts != timestamp:
                    counts={};count_ts=timestamp
                signature=trade['signature'];counts[signature]=counts.get(signature,0)+1
                trade['occurrence']=counts[signature];trade['id']=f'{signature}:{counts[signature]}'
                trade['evidence_id']=response.evidence_id
                if getattr(self,'_selection_id',None):trade['collection_selection_id']=self._selection_id
                if timestamp>=walk['cutoff']:
                    normalized.append(trade)
                else:
                    result['outside_window']+=1
                oldest=timestamp if oldest is None else min(oldest,timestamp)
                newest=timestamp if newest is None else max(newest,timestamp)
            done=not cursor or (oldest is not None and oldest<walk['cutoff'])
            walk.update(cursor=None if done else cursor,counts=counts,count_timestamp=count_ts,
                        oldest=oldest,newest=newest,done=done,observed_at=response.observed_at,
                        cache_age=response.headers.get('age'),last_evidence_id=response.evidence_id)
            with self.store.transaction() as cx:
                for trade in normalized:
                    if not self.store.get('trade',trade['id']):
                        self.store.put('trade',trade['id'],trade,response.observed_at,conn=cx)
                        result['inserted']+=1
                from .provenance import record_sources
                record_sources(self.store,normalized,query,response.evidence_id,response.observed_at,cx)
                for bad in rejected:
                    bad_id=hashlib.sha256(json.dumps(bad['raw'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
                    self.store.put('rejected_trade',bad_id,bad,response.observed_at,conn=cx)
                self.store.checkpoint(key,state,conn=cx)
            result['rejected']+=len(rejected)
            result['matched_rows']+=len(normalized)
            result['rows']+=len(rows);result['pages']+=1
            if newest is not None:
                result['lag_seconds']=max(0,response.observed_at-newest)
            if done:
                break
            seen_cursors.add(cursor)
        return result

    async def _trade_stream(self,key,params,pages,maps):
        state=self.store.checkpoint(key)
        initial_cutoff=max(1,time.time()-self.config.get('initial_lookback_seconds',3600)-self.config.get('overlap_seconds',180))
        if state is None:
            state={'watermark':None,'pending':[],'initial_cutoff':initial_cutoff}
        prior_params=state.get('params',params)
        pending=state.setdefault('pending',[])
        interrupted=state.pop('active',None)
        if interrupted:
            interrupted.setdefault('params',prior_params)
            if interrupted.get('newest') is not None:
                state['watermark']=max(state.get('watermark') or 0,interrupted['newest'])
            if not interrupted.get('done'):
                pending.append(interrupted)
        pending[:]=[w for w in pending if not w.get('done')]
        for walk in pending:
            walk.setdefault('params',prior_params)
        if prior_params != params:
            self.store.put('gap',f'{key}:{time.time_ns()}',dict(stream=key,reason='Filtres modifiés: nouvelle fenêtre, arriérés gardant leurs filtres initiaux',
                                                             previous_params=prior_params,params=params,observed_at=time.time()))
            state['watermark']=None
            state['initial_cutoff']=initial_cutoff
        state['params']=dict(params)
        cutoff=(state.get('watermark') or time.time()-self.config.get('initial_lookback_seconds',3600))-self.config.get('overlap_seconds',180)
        cutoff=max(state.get('initial_cutoff',1),cutoff)
        active=dict(cursor=None,cutoff=max(1,cutoff),counts={},count_timestamp=None,done=False,params=dict(params))
        state['active']=active
        self.store.checkpoint(key,state)
        result=await self._walk_trades(key,params,state,active,pages,maps)
        if active.get('newest') is not None:
            state['watermark']=max(state.get('watermark') or 0,active['newest'])
        if not active.get('done'):
            pending.append(active)
        state.pop('active',None)
        self.store.checkpoint(key,state)
        if pending:
            continuation=await self._walk_trades(key,params,state,pending[0],1,maps)
            for metric in ('rows','matched_rows','outside_window','inserted','rejected','pages'):
                result[metric]+=continuation[metric]
            result['recovered']=result['recovered'] or continuation['recovered']
            if pending[0].get('done'):
                pending.pop(0)
        # Bound queue memory; dropped walks remain explicit gaps, never a claim of zero trades.
        while len(pending)>24:
            abandoned=pending.pop(0)
            self.store.put('gap',f'{key}:{time.time_ns()}',dict(stream=key,reason='Retard supérieur au budget de 24 parcours',
                                                             cutoff=abandoned['cutoff'],oldest=abandoned.get('oldest'),
                                                             cursor=abandoned.get('cursor'),observed_at=time.time()))
        state['params']=params;state['last_success']=time.time()
        self.store.checkpoint(key,state)
        result.update(pending_walks=len(pending),cutoff=cutoff,range_oldest=active.get('oldest'),range_newest=active.get('newest'),
                      cache_age=active.get('cache_age'),head_page_budget=pages,continuation_page_budget=1,
                      last_page_observed_at=active.get('observed_at'),initial_cutoff=state.get('initial_cutoff'),
                      status='degraded' if result['rejected'] else ('capped' if pending else ('ok' if result['matched_rows'] else 'empty')))
        self.store.health(key,result['status'],'Parcours borné; retard explicite' if pending else 'Chevauchement atteint',
                          **{k:v for k,v in result.items() if k!='status'},params=params,last_success=state['last_success'])
        return result

    def _fair_markets(self):
        from .priority import select_markets
        limit=self.config.get('market_batches',2)*self.config.get('markets_per_batch',5)
        markets,self._queue_summary=select_markets(self.store,self.config,time.time(),limit)
        self._selection_id=hashlib.sha256(json.dumps(self._queue_summary,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        self._queue_summary['selection_id']=self._selection_id
        with self.store.transaction() as cx:
            self.store.put('collection_selection',self._selection_id,self._queue_summary,conn=cx)
            self.store.checkpoint('collect:queue',self._queue_summary,conn=cx)
        return markets

    async def trades(self):
        maps=self._maps()
        result=dict(rows=0,matched_rows=0,outside_window=0,inserted=0,rejected=0,pages=0,errors=[],streams=[],markets_followed=0)
        scopes=[('trades:global',dict(limit=self.config.get('trade_page_size',250),taker_only='true',filter_type='CASH',
                                     filter_amount=self.config.get('global_min_nominal',1000)),None,self.config.get('trade_pages',3))]
        for market in self._fair_markets():
            scopes.append(('trades:market:'+market['id'],dict(limit=self.config.get('trade_page_size',250),taker_only='true',
                                                             condition=market['condition_id']),market,1))
        result['queue']=self._queue_summary
        for key,params,market,pages in scopes:
            try:
                stream=await self._trade_stream(key,params,pages,maps)
                for metric in ('rows','matched_rows','outside_window','inserted','rejected','pages'):result[metric]+=stream[metric]
                result['streams'].append(dict(stream=key,**stream))
                if market:
                    result['markets_followed']+=1
                    self.store.put('market_coverage',market['id'],dict(market_id=market['id'],event_id=market['event_id'],
                                                                     collection_selection_id=self._selection_id,last_success=time.time(),**stream))
            except (SourceError,ValueError,KeyError,TypeError) as exc:
                result['errors'].append(f'{key}: {exc}')
                self.store.health(key,'error',str(exc))
                if market:
                    self.store.put('market_coverage',market['id'],dict(market_id=market['id'],event_id=market['event_id'],
                                                                     collection_selection_id=self._selection_id,status='error',detail=str(exc),last_attempt=time.time()))
        result['status']='degraded' if result['errors'] or result['rejected'] else ('capped' if any(s['status']=='capped' for s in result['streams']) else 'ok')
        return result
