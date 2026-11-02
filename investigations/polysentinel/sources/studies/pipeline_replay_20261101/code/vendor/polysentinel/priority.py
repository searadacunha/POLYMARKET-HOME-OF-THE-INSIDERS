"""Operational announcement scope and bounded, fair polling; no detection scores."""
from bisect import bisect_right
from collections import Counter, defaultdict
from datetime import datetime
import hashlib
import json
import math
import random
import re
import secrets
import sys
from urllib.parse import urlsplit


def _epoch(value):
    try:
        result=float(value)
    except (TypeError,ValueError):
        try:
            parsed=datetime.fromisoformat(str(value).replace('Z','+00:00'))
            if parsed.tzinfo is None:return None
            result=parsed.timestamp()
        except (TypeError,ValueError,OverflowError):return None
    return result if math.isfinite(result) else None


def _end(market,event):
    return _epoch(market.get('end_date') or market.get('raw',{}).get('endDate') or
                  event.get('end_date') or event.get('raw',{}).get('endDate'))


def _public(metadata,now):
    public_at=_epoch(metadata.get('public_at'))
    observed=_epoch(metadata.get('public_observed_at'))
    return (metadata.get('_public_result_known') is True or
            (metadata.get('verified') is True and metadata.get('result_available') is True and
             (public_at is None or public_at<=now)) or
            (public_at is not None and public_at<=now and observed is not None and observed<=now))


def market_exclusion_reason(market,event,now):
    """Shared coverage denominator. Missing end dates remain general exploration."""
    observed=_epoch(market.get('observed_at'))
    if observed is None:return 'market_not_observed'
    if observed>now:return 'market_future'
    if event and _epoch(event.get('observed_at')) is None:return 'event_not_observed'
    if event and _epoch(event.get('observed_at'))>now:return 'event_future'
    if market.get('closed')==True or event.get('closed')==True:return 'closed'
    if market.get('closed')!=False:return 'inactive_or_unknown'
    if market.get('active')!=True or event.get('active')==False:return 'inactive'
    if _public(market,now) or _public(event,now):return 'public_result'
    for metadata in (market,event):
        end=_epoch(metadata.get('end_date') or metadata.get('raw',{}).get('endDate'))
        if end is not None and end<=now:return 'expired'
        if str(metadata.get('raw',{}).get('umaResolutionStatus','')).lower()=='resolved':return 'public_result'
    if not re.fullmatch(r'0x[0-9a-fA-F]{64}',str(market.get('condition_id',''))) or not market.get('tokens'):
        return 'unmapped'
    return None


_RULES=[
    ('awards',r"\b(?:ballon d['’]or|oscars?|academy awards?|grammys?|emmys?|nobel|awards? (?:winner|nomination)|(?:win|winner|nomina\w*)[^?]{0,100}\b(?:award|oscar|grammy|emmy))\b"),
    ('earnings',r'\b(?:earnings|quarterly results|financial results|revenue|EPS)\b'),
    ('economic_data',r'\b(?:CPI|PCE|GDP|non.?farm payrolls?|unemployment rate|jobs report|inflation (?:report|release|rate))\b'),
    ('central_bank',r'\b(?:fed|FOMC|ECB|BCE|Bank of England|Bank of Japan)\b.*\b(?:rate|decision|meeting|cut|hike|interest)\b'),
    ('nomination',r'\b(?:nominat(?:e|ed|es|ion)|appoint(?:ed|ment|s)?|named as)\b'),
    ('regulatory',r'\b(?:FDA|SEC|FTC|court|European Commission)\b.*\b(?:approv\w*|ruling|decision|authoriz\w*)\b'),
    ('token_launch',r'\b(?:launch|release|airdrop|generation)\b.*\b(?:token|mainnet|coin|TGE)\b|\b(?:token|mainnet|TGE)\b.*\b(?:launch|release|airdrop)\b'),
    ('listing',r'\b(?:IPO|initial public offering|listed on|listing on)\b'),
    ('announcement',r'\b(?:announc(?:e|es|ed|ement)|acquisition|merger)\b'),
]
_RULES=[(category,re.compile(pattern,re.I)) for category,pattern in _RULES]
_PRICE=re.compile(r'\b(?:price|market cap|FDV|fully diluted valuation|up or down)\b|\b(?:bitcoin|BTC|ethereum|ETH|solana|gold|silver|oil|Nasdaq|S&P)\b.*\b(?:above|below|between|reach|hit|over|under)\b',re.I)
_SPORT=re.compile(r'\b(?:vs\.?|Premier League|Champions League|World Cup|NBA|NFL|MLB|NHL|Grand Prix|La Liga|Serie A|Super Bowl)\b',re.I)


def announcement_scope(market,event,now):
    """Conservative metadata hypothesis, never an assertion of private knowledge."""
    result=dict(eligible=False,reason='',reason_code='',category=None,source=None,end_at=None,
                observed_at=_epoch(market.get('observed_at')),
                interpretation='Hypothèse de marché d’annonce ; information privilégiée non établie.')
    def reject(code,reason):
        result.update(reason_code=code,reason=reason);return result
    excluded=market_exclusion_reason(market,event,now)
    if excluded:return reject(excluded,'Marché hors périmètre courant : '+excluded)
    result['end_at']=_end(market,event)
    title=str(market.get('question') or event.get('title') or '')
    category=next((name for name,pattern in _RULES if pattern.search(title)),None)
    if _PRICE.search(title):return reject('continuous_price','Prix ou valorisation suivis en continu.')
    raw=market.get('raw',{})
    if category!='awards' and (_SPORT.search(title) or raw.get('sportsMarketType') or raw.get('gameId')):
        return reject('continuous_sport','Match ou compétition sportive ; hors enquête automatique.')
    if not category:return reject('no_announcement','Aucune annonce discrète explicitement identifiable dans le titre ; tags seuls insuffisants.')
    result['category']=category
    if result['end_at'] is None:return reject('missing_date','Date de fin explicite indisponible.')
    for metadata in (market,event):
        source=metadata.get('resolution_source') or metadata.get('raw',{}).get('resolutionSource')
        if not isinstance(source,str):continue
        try:
            parsed=urlsplit(source.strip())
            if parsed.scheme in ('http','https') and parsed.hostname and not parsed.username:
                result['source']=source.strip();break
        except ValueError:continue
    if not result['source']:return reject('missing_source','URL explicite de la source de résolution indisponible.')
    result.update(eligible=True,reason_code='announcement_hypothesis',
                  reason='Annonce identifiable, source de résolution et date future ; hypothèse opérationnelle à vérifier.')
    return result


def _objects(store,kind,now):
    # CASE prevents decompressing a snapshot that was not known at selection time.
    for key,payload,observed_at,first_seen in store.conn.execute('SELECT key,CASE WHEN observed_at<=? THEN payload END payload,observed_at,first_seen FROM objects WHERE kind=?',(now,kind)):
        value=json.loads(payload) if payload else {}
        value.setdefault('id',key)
        value['observed_at']=max(_epoch(value.get('observed_at')) or observed_at,observed_at)
        yield key,value,first_seen


def market_snapshots(store,now):
    """Yield (market,event,last_attempt,first_seen), sharing current coverage policy."""
    events={key:value for key,value,_ in _objects(store,'event',now)}
    public_conditions=set()
    for kind in ('public_condition','public_milestone'):
        for key,value,_ in _objects(store,kind,now):
            if value['observed_at']<=now and _public(value,now):
                if kind=='public_condition':public_conditions.add(key.lower())
                elif key in events:events[key]['_public_result_known']=True
    attempts=dict(store.conn.execute(
        "SELECT key,observed_at FROM objects WHERE kind='market_coverage' AND observed_at<=?",(now,)))
    for key,market,first_seen in _objects(store,'market',now):
        if str(market.get('condition_id','')).lower() in public_conditions:market['_public_result_known']=True
        yield market,events.get(str(market.get('event_id','')),{}),attempts.get(key),first_seen


TARGETING_VERSION='targeting-v2-announcements'
HISTORY_LIMIT=5000
ACTIVITY_LIMIT=5000


def _number(value):
    if isinstance(value,bool):return None
    try:value=float(value)
    except (TypeError,ValueError):return None
    return value if math.isfinite(value) else None


def _observation(market):
    raw=market.get('raw') or {};tokens=market.get('tokens') or []
    prices=raw.get('outcomePrices')
    if isinstance(prices,str):
        try:prices=json.loads(prices)
        except ValueError:prices=None
    identity=tuple(sorted((str(t.get('token_id','')),str(t.get('outcome',''))) for t in tokens))
    valid=isinstance(prices,list) and len(prices)==len(tokens) and bool(tokens)
    numbers=[_number(p) for p in prices] if valid else []
    if not valid or any(p is None or not 0<=p<=1 for p in numbers) or len({t[0] for t in identity})!=len(identity):
        price_map=None
    else:price_map={str(t['token_id']):p for t,p in zip(tokens,numbers)}
    field='volumeNum' if raw.get('volumeNum') is not None else 'volume'
    volume=_number(raw.get(field))
    if volume is not None and volume<0:volume=None
    return dict(observed_at=_epoch(market.get('observed_at')),identity=identity,prices=price_map,
                volume=volume,volume_field=field,version=market.get('version'),history_id=market.get('_history_id'),
                unusable=market.get('closed')==True or market.get('active')==False or
                str(raw.get('umaResolutionStatus','')).lower()=='resolved')


def _changes(current,previous,now):
    result=dict(price_rate_600s=None,volume_rate_600s=None,price_delta=None,cumulative_volume_delta=None,
                current_observed_at=current['observed_at'],previous_observed_at=previous['observed_at'] if previous else None,
                previous_history_id=previous.get('history_id') if previous else None,span_seconds=None,
                price_unknown='missing_comparator',volume_unknown='missing_comparator')
    if previous is None:return result
    at,before=current['observed_at'],previous['observed_at']
    reason=None
    if at is None or before is None:reason='unknown_observation_time'
    elif at>now or before>now:reason='future_observation'
    elif current['unusable'] or previous['unusable']:reason='inactive_or_resolved_snapshot'
    elif current['version']!=previous['version']:reason='protocol_changed'
    elif now-at>900:reason='stale_current_snapshot'
    elif not 300<=at-before<=900:reason='span_outside_5_15_minutes'
    if reason:
        result.update(price_unknown=reason,volume_unknown=reason);return result
    span=at-before;result['span_seconds']=span
    if current['identity']!=previous['identity']:
        result['price_unknown']='token_identity_changed'
    elif current['prices'] is None or previous['prices'] is None:
        result['price_unknown']='missing_prices'
    else:
        delta=max(abs(current['prices'][token]-previous['prices'][token]) for token in current['prices'])
        result.update(price_delta=delta,price_rate_600s=delta*600/span,price_unknown=None)
    if current['volume'] is None or previous['volume'] is None:result['volume_unknown']='missing_cumulative_counter'
    elif current['volume_field']!=previous['volume_field']:result['volume_unknown']='counter_field_changed'
    elif current['volume']<previous['volume']:result['volume_unknown']='counter_reset'
    else:
        delta=current['volume']-previous['volume']
        rate=_number(delta*(600/span))
        result.update(cumulative_volume_delta=delta,volume_rate_600s=rate,volume_unknown=None if rate is not None else 'rate_overflow')
    return result


def market_changes(current,previous,now):
    """Observed endpoint rates, never a rolling-24h volume relabelled as 10 minutes."""
    return _changes(_observation(current),_observation(previous) if previous else None,now)


def _history_samples(store,now):
    # Fetch bounded identities first: the overflow sentinel is never decompressed.
    refs=store.conn.execute("SELECT id,key,observed_at FROM history WHERE kind='market' AND observed_at>=? AND observed_at<=? ORDER BY observed_at DESC,id DESC LIMIT ?",
                            (now-7200,now-300,HISTORY_LIMIT+1)).fetchall()
    usable=refs[:HISTORY_LIMIT];payloads={}
    for start in range(0,len(usable),500):
        ids=[row[0] for row in usable[start:start+500]]
        marks=','.join('?' for _ in ids)
        for key,payload in store.conn.execute('SELECT id,payload FROM history WHERE id IN ('+marks+')',ids):
            payloads[key]=json.loads(payload)
    by_market=defaultdict(list);future=0
    for key,market_id,at in usable:
        value=payloads[key];value['observed_at']=max(_epoch(value.get('observed_at')) or at,at)
        if value['observed_at']>now:future+=1;continue
        value['_history_id']=key
        by_market[market_id].append(_observation(value))
    return by_market,dict(status='capped' if len(refs)>HISTORY_LIMIT else 'bounded',references_read=len(refs),
                         snapshots_loaded=len(usable),snapshots_used=len(usable)-future,future_observations_excluded=future,
                         limit=HISTORY_LIMIT,start=now-7200,end=now-300,
                         history_complete=False)


def _recent_activity(store,now):
    exists=store.conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='trade_index'").fetchone()
    bounds=dict(previous=[now-1200,now-600],current=[now-600,now],limit=ACTIVITY_LIMIT,
                unit='locally ingested API rows, not nominal exposure',history_complete=False)
    if not exists:return {},dict(bounds,status='missing_index',rows_read=0)
    rows=store.conn.execute('SELECT wallet,trade_time,observed_at,condition_id FROM trade_index WHERE trade_time>=? AND trade_time<? ORDER BY trade_time DESC,key DESC LIMIT ?',
                            (now-1200,now,ACTIVITY_LIMIT+1)).fetchall()
    if len(rows)>ACTIVITY_LIMIT:return {},dict(bounds,status='capped',rows_read=len(rows),rows_used=0)
    counts=defaultdict(lambda:[Counter(),Counter()]);future=0
    for wallet,at,observed,condition in rows:
        if observed>now:future+=1;continue
        counts[str(condition).lower()][int(at>=now-600)][wallet]+=1
    result={}
    for condition,(previous,current) in counts.items():
        a,b=sum(previous.values()),sum(current.values())
        hhi_a=sum(n*n for n in previous.values())/(a*a) if a>=2 else None
        hhi_b=sum(n*n for n in current.values())/(b*b) if b>=2 else None
        result[condition]=dict(previous_count=a,current_count=b,activity_change=b-a,
                               previous_hhi=hhi_a,current_hhi=hhi_b,
                               concentration_change=hhi_b-hhi_a if hhi_a is not None and hhi_b is not None else None)
    return result,dict(bounds,status='bounded',rows_read=len(rows),rows_used=len(rows)-future,future_observations_excluded=future)


def _category(market,event,scope):
    if scope['eligible']:return scope['category']
    if scope['reason_code']=='continuous_price':return 'price'
    if scope['reason_code']=='continuous_sport':return 'sport'
    tags=set(event.get('tags') or [])
    for name,values in [('sport',{'sports','soccer','basketball','football'}),
                        ('politics',{'politics','elections','geopolitics'}),
                        ('economy',{'economics','economy','finance','fed','economic-data'}),
                        ('business_science',{'business','science','technology','crypto'})]:
        if tags&values:return name
    return 'other'


def _age_band(at,now):
    if at is None:return 'never'
    age=now-at
    return 'under_1h' if age<3600 else '1h_24h' if age<86400 else 'over_24h'


def stratified_sample(strata,slots,seed):
    """Random balanced allocation + SRS; exact marginal per-cycle inclusion."""
    strata={key:sorted(values) for key,values in sorted(strata.items()) if values}
    slots=min(max(0,int(slots)),sum(map(len,strata.values())))
    rng=random.Random(str(seed));q=0
    if strata:
        while q<max(map(len,strata.values())) and sum(min(q+1,len(v)) for v in strata.values())<=slots:q+=1
    base={key:min(q,len(values)) for key,values in strata.items()}
    extra=slots-sum(base.values());available=[key for key,values in strata.items() if len(values)>q]
    bonus=set(rng.sample(available,extra));drawn=[];design=[]
    for key,values in strata.items():
        n=base[key]+int(key in bonus)
        probability=(base[key]+(extra/len(available) if key in available else 0))/len(values)
        selected=rng.sample(values,n)
        drawn.extend((market_id,key,probability) for market_id in selected)
        design.append(dict(stratum=key,population=len(values),sample_size=n,
                           inclusion_probability=probability,conditional_probability=n/len(values),
                           members_sha256=hashlib.sha256(json.dumps(values,separators=(',',':')).encode()).hexdigest()))
    rng.shuffle(drawn)
    return drawn,dict(seed=str(seed),algorithm='python.Random.sample(seed=str,version=2)',python_version=sys.version.split()[0],
                      allocation_base=q,extra_strata=extra,extra_eligible_strata=len(available),strata=design,
                      probability_scope='Marginal for this cycle, conditional on the discovered frame and deterministic targeting.')


def _select_markets(store,config,now,limit):
    limit=min(10,max(0,int(limit)))
    previous=store.checkpoint('collect:queue') or {}
    if previous.get('observed_at',0)>now:previous={}
    turn=int(previous.get('turn',0))
    tables={r[0] for r in store.conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    revision={table:store.conn.execute('SELECT MAX(rowid) FROM '+table).fetchone()[0]
              for table in ('history_refs','trade_index') if table in tables}
    history,history_info=_history_samples(store,now)
    activity,activity_info=_recent_activity(store,now)
    candidates=[];excluded=Counter();categories=Counter();catalog_count=0;unknown=Counter()
    components=('price_rate_600s','volume_rate_600s','activity_change','concentration_change')
    for market,event,attempt,first_seen in market_snapshots(store,now):
        catalog_count+=1
        reason=market_exclusion_reason(market,event,now)
        if reason:excluded[reason]+=1;continue
        scope=announcement_scope(market,event,now)
        if scope['eligible']:categories[scope['category']]+=1
        current=_observation(market)
        comparator=next((p for p in history.get(market['id'],[]) if p['observed_at'] is not None and
                         300<=current['observed_at']-p['observed_at']<=900),None)
        features=_changes(current,comparator,now)
        local=activity.get(market['condition_id'].lower(),dict(previous_count=0,current_count=0,
                           previous_hhi=None,current_hhi=None,activity_change=0,concentration_change=None))
        if activity_info['status']!='bounded':
            local=dict(previous_count=None,current_count=None,previous_hhi=None,current_hhi=None,
                       activity_change=None,concentration_change=None)
        features.update(local)
        features['activity_unknown']=None if activity_info['status']=='bounded' else activity_info['status']
        features['concentration_unknown']=features['activity_unknown'] or (
            'fewer_than_two_rows_per_window' if local['concentration_change'] is None else None)
        for name in components:
            if features[name] is None:unknown[name]+=1
        category=_category(market,event,scope)
        candidates.append(dict(id=market['id'],last_attempt=attempt,announcement=scope['eligible'],category=category,
                               stratum=category+'|'+_age_band(attempt,now),features=features))
    references={name:sorted(c['features'][name] for c in candidates if c['features'][name] is not None) for name in components}
    for candidate in candidates:
        ranks={name:bisect_right(references[name],candidate['features'][name])/len(references[name])
               for name in components if candidate['features'][name] is not None and candidate['features'][name]>0}
        candidate['component_ranks']=ranks;candidate['operational_priority']=max(ranks.values(),default=0)
    budget=min(limit,len(candidates));target_budget=budget//2
    pools=defaultdict(list)
    for candidate in candidates:
        if candidate['announcement'] and (candidate['last_attempt'] is None or candidate['last_attempt']<=now-600):
            pools[candidate['category']].append(candidate)
    for values in pools.values():values.sort(key=lambda c:(-c['operational_priority'],c['last_attempt'] or 0,c['id']))
    served=dict(previous.get('target_category_turns') or {});before_served=dict(served);targeted=[]
    while len(targeted)<target_budget and any(pools.values()):
        category=min((key for key,values in pools.items() if values),key=lambda key:(served.get(key,0),key))
        targeted.append(pools[category].pop(0));served[category]=(turn+1)*10+len(targeted)
    target_ids={c['id'] for c in targeted};strata=defaultdict(list)
    for candidate in candidates:
        if candidate['id'] not in target_ids:strata[candidate['stratum']].append(candidate['id'])
    seed=config.get('targeting_seed')
    if seed is None:seed=secrets.token_hex(16)
    drawn,sampling=stratified_sample(strata,budget-len(targeted),seed)
    frame=dict(targeted=sorted(target_ids),strata={key:sorted(values) for key,values in sorted(strata.items())})
    sampling['frame_sha256']=hashlib.sha256(json.dumps(frame,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    sampling['as_of']=now;sampling['input_revision']=revision
    sampling['reconstruction']='Latest observations by immutable history rowid at revision; apply policy and verify frame hash.'
    sampling['target_category_turns_before']=before_served
    by_id={c['id']:c for c in candidates};exploration=[dict(by_id[key],inclusion_probability=p) for key,_,p in drawn]
    ordered=[]
    for i in range(max(len(exploration),len(targeted))):
        if i<len(exploration):ordered.append((exploration[i],'exploration'))
        if i<len(targeted):ordered.append((targeted[i],'targeting'))
    markets=[];selection=[]
    for rank,(item,lane) in enumerate(ordered,1):
        markets.append(store.get('market',item['id'])['payload'])
        row=dict(rank=rank,market_id=item['id'],lane=lane,coverage_state='never_queried' if item['last_attempt'] is None else 'revisit',
                 last_attempt=item['last_attempt'],announcement_eligible=item['announcement'],category=item['category'],stratum=item['stratum'],
                 inclusion_probability=item.get('inclusion_probability',1.0),
                 selection_reason='Tirage aléatoire stratifié sans remise.' if lane=='exploration' else 'Annonce documentée : rotation de catégories, puis changements observés ; sans score de détection.')
        if lane=='targeting':row.update(operational_priority=item['operational_priority'],component_ranks=item['component_ranks'],features=item['features'])
        selection.append(row)
    summary=dict(observed_at=now,turn=turn+1,limit=limit,policy_version=TARGETING_VERSION,catalog_count=catalog_count,
                 eligible_count=len(candidates),excluded=dict(excluded),announcement_categories=dict(categories),
                 never_queried=sum(c['last_attempt'] is None for c in candidates),revisits=sum(c['last_attempt'] is not None for c in candidates),
                 announcement_eligible=sum(c['announcement'] for c in candidates),selected=selection,selected_count=len(markets),
                 exploration_selected=len(exploration),targeting_selected=len(targeted),
                 announcement_selected=sum(c['announcement'] for c in targeted),deferred_count=len(candidates)-len(markets),
                 target_category_turns={key:value for key,value in served.items() if key in {c['category'] for c in candidates}},
                 sampling=sampling,targeting=dict(history=history_info,activity=activity_info,unknown_components=dict(unknown),
                     component_reference_counts={key:len(values) for key,values in references.items()},cooldown_seconds=600,
                     rank_definition='Maximum empirical component rank, operational only; missing is unknown, not normal.'),
                 bounded=True,history_complete=False,selection_is_not_poll_success=True,
                 policy='Au moins la moitié en tirage aléatoire à deux étages ; annonces documentées pour le reste ; plafond 10.')
    return markets,summary


def select_markets(store,config,now,limit):
    """Read a consistent frame; the caller archives its decision before any polling."""
    store.conn.execute('SAVEPOINT targeting_selection')
    try:return _select_markets(store,config,now,limit)
    finally:store.conn.execute('RELEASE targeting_selection')

