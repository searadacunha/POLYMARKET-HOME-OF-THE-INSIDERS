"""Bounded, restartable investigations; enrichments never rewrite an emitted score."""
import asyncio
import hashlib
import json
import math
import re
import time
from collections import defaultdict

import networkx as nx

from .chain import ADDRESS, HASH, inspect_receipt
from .news import collect_news, resolution_state

DATA = 'https://data-api.polymarket.com/v2/'


class BudgetExceeded(RuntimeError):
    budget_exhausted = True


class Budget:
    def __init__(self, net, config):
        self.net, self.config = net, config
        self.started = time.monotonic()
        self.calls = 0
        self.evidence_ids = []

    async def request(self, *args, **kwargs):
        remaining = self.config['investigation_max_seconds'] - (time.monotonic() - self.started)
        if self.calls >= self.config['investigation_max_requests'] or remaining <= 0:
            raise BudgetExceeded('Budget de requêtes ou durée de l’enquête atteint')
        self.calls += 1
        try:
            response = await asyncio.wait_for(self.net.request(*args, **kwargs), timeout=remaining)
        except asyncio.TimeoutError as exc:
            raise BudgetExceeded('Durée maximale de l’enquête atteinte') from exc
        self.evidence_ids.append(response.evidence_id)
        return response


def _fingerprint(row):
    # These feeds do not expose logIndex: identical rows remain an identity ambiguity, not independent fills.
    fields = ('proxy_wallet', 'transaction_hash', 'timestamp', 'token_id', 'condition_id', 'type', 'side', 'size', 'price')
    return hashlib.sha256(json.dumps([row.get(k) for k in fields], sort_keys=True).encode()).hexdigest()


def _validate_page(body, wallet, route, end):
    if not isinstance(body, dict) or not isinstance(body.get('data'), list) or not isinstance(body.get('pagination'), dict):
        raise ValueError('Invalid Data API v2 page envelope')
    pagination = body['pagination']
    if not isinstance(pagination.get('has_more'), bool):
        raise ValueError('Pagination has_more missing')
    cursor = pagination.get('next_cursor')
    if pagination['has_more'] and (not isinstance(cursor, str) or not cursor):
        raise ValueError('has_more without cursor')
    if not pagination['has_more'] and cursor:
        raise ValueError('Contradictory terminal cursor')
    for row in body['data']:
        if not isinstance(row, dict) or str(row.get('proxy_wallet', '')).lower() != wallet:
            raise ValueError('Wallet scope mismatch')
        if route != 'positions':
            timestamp = row.get('timestamp')
            if not isinstance(timestamp, (int, float)) or not math.isfinite(timestamp) or timestamp <= 0 or timestamp > end:
                raise ValueError('Timestamp outside fixed user window')
            if not row.get('transaction_hash'):
                raise ValueError('Transaction identity missing')
        if route == 'trades' and (row.get('side') not in ('BUY', 'SELL') or not str(row.get('token_id', '')).isdigit()):
            raise ValueError('Invalid trade side/token')
    return body['data'], cursor, pagination['has_more']


def _new_walk(filters, cutoff):
    return {'filters': filters, 'cursor': None, 'complete': False, 'pages': 0, 'rows': 0,
            'window_end': int(cutoff), 'updated_at': time.time(), 'recoveries': []}


async def _walk_pages(store, net, wallet, route, key, cp, limit, gap_prefix=None):
    errors, pages, rows = [], 0, 0
    seen_cursors = {cp['cursor']} if cp.get('cursor') else set()
    while pages < limit and not cp.get('complete'):
        params = dict(cp['filters'])
        if cp.get('cursor'):
            params['cursor'] = cp['cursor']
        try:
            response = await net.request(DATA + route, params=params)
            items, cursor, more = _validate_page(response.body, wallet, route, cp['window_end'])
            scope=cp['filters'].get('event_id')
            if scope and any(r.get('event_id') is not None and str(r['event_id'])!=str(scope) for r in items):
                raise ValueError('Event scope mismatch')
            if route != 'positions' and any(t['timestamp'] < cp['filters']['start'] for t in items):
                raise ValueError('Timestamp below fixed user window')
        except Exception as exc:
            if getattr(exc, 'status', None) == 400 and cp.get('cursor'):
                cp['recoveries'].append({'at': time.time(), 'reason': str(exc)[:200], 'previous_cursor': cp['cursor']})
                cp.update(cursor=None, complete=False, pages=0, rows=0)
                store.checkpoint(key, cp)
                errors.append('Curseur refusé : reprise explicite à la première page, mêmes filtres')
            else:
                errors.append(f'{type(exc).__name__}: {str(exc)[:240]}')
            break
        if cursor and cursor in seen_cursors:
            errors.append('Curseur répété : progression arrêtée sans avancer le checkpoint')
            break
        if more and not items:
            errors.append('Page vide annonçant une suite : progression arrêtée')
            break
        new_cp = dict(cp, cursor=cursor, complete=not more, pages=cp['pages'] + 1,
                      rows=cp['rows'] + len(items), updated_at=response.observed_at)
        with store.transaction() as conn:
            for item in items:
                row_key = f'{wallet}:{item["token_id"]}' if route == 'positions' else wallet + ':' + _fingerprint(item)
                store.put('wallet_' + route, row_key, {'wallet': wallet, 'row': item,
                          'evidence_id': response.evidence_id, 'observed_at': response.observed_at,
                          'event_scope': cp['filters'].get('event_id'),
                          'snapshot_end': cp['window_end']}, observed_at=response.observed_at, conn=conn)
            store.checkpoint(key, new_cp, conn=conn)
            if gap_prefix and more:
                # The fresh head may move on only after its unread tail has a durable independent cursor.
                gap_key = f"{gap_prefix}{cp['filters']['start']}:{cp['window_end']}"
                store.checkpoint(gap_key, new_cp, conn=conn)
        cp = new_cp
        pages += 1
        rows += len(items)
        if cursor:
            seen_cursors.add(cursor)
    return cp, errors, pages, rows


def _pending_gaps(store, prefix):
    return store.conn.execute(
        "SELECT key,value FROM checkpoints WHERE key LIKE ? AND json_extract(value,'$.complete')=0 ORDER BY CAST(json_extract(value,'$.window_end') AS INTEGER)",
        (prefix + '%',)).fetchall()


async def wallet_feed(store, net, config, wallet, route, cutoff, event_id=None):
    """Keep a fresh bounded head alongside fixed historical and catch-up windows."""
    wallet = wallet.lower()
    if not ADDRESS.fullmatch(wallet) or route not in ('trades', 'activity', 'positions'):
        raise ValueError('Invalid wallet/feed')
    key = f'investigate:{wallet}:{route}'
    if event_id is not None:
        if not str(event_id).isdigit() or int(event_id)<=0:raise ValueError('Invalid event scope')
        key += ':event:'+str(event_id)
    gap_prefix = key + ':gap:'
    cp = store.checkpoint(key) or {}
    if cp.get('complete') and route == 'positions':
        cp = {}
    if not cp:
        filters = {'user': wallet, 'limit': 100}
        if event_id is not None:filters['event_id']=str(event_id)
        if route == 'positions':
            filters.update(status='OPEN', sort_by='CURRENT_VALUE', sort_direction='DESC')
        else:
            filters.update(start=1, end=int(cutoff))
        if route == 'trades':
            filters['taker_only'] = 'false'
        if route == 'activity':
            filters.update(sort_by='TIMESTAMP', sort_direction='DESC', exclude_deposits_withdrawals='false')
        cp = _new_walk(filters, cutoff)
    errors, pages, rows = [], 0, 0
    limit = 1 if route == 'positions' else config['investigation_history_pages']
    recent = None
    if route != 'positions' and int(cutoff) > cp['window_end']:
        previous_head = store.checkpoint(key + ':head') or cp
        filters = dict(cp['filters'], start=max(1, previous_head['window_end'] - config.get('overlap_seconds', 180)), end=int(cutoff))
        head = _new_walk(filters, cutoff)
        head, head_errors, head_pages, head_rows = await _walk_pages(
            store, net, wallet, route, key + ':head', head, 1, gap_prefix=gap_prefix)
        errors.extend(head_errors); pages += head_pages; rows += head_rows
        recent = {'window_start': filters['start'], 'window_end': int(cutoff),
                  'status': 'error' if head_errors else 'complete' if head['complete'] else 'capped',
                  'rows': head_rows, 'checkpoint_key': key + ':head'}
        # A failed attempt still consumed its page allowance; reserve the remaining budget for saved cursors.
        limit = max(0, limit - 1)
    gaps = _pending_gaps(store, gap_prefix)
    if gaps and limit:
        turn = store.checkpoint(key + ':fairness') or {'turn': 0}
        serve_gap = cp.get('complete') or limit >= 2 or turn['turn'] % 2 == 1
        if serve_gap:
            gap_row = gaps[0]
            gap = json.loads(gap_row['value'])
            gap, gap_errors, gap_pages, gap_rows = await _walk_pages(
                store, net, wallet, route, gap_row['key'], gap, 1)
            errors.extend(gap_errors); pages += gap_pages; rows += gap_rows
            limit -= 1
        store.checkpoint(key + ':fairness', {'turn': turn['turn'] + 1})
    cp, old_errors, old_pages, old_rows = await _walk_pages(store, net, wallet, route, key, cp, limit)
    errors.extend(old_errors); pages += old_pages; rows += old_rows
    pending = _pending_gaps(store, gap_prefix)
    complete = cp.get('complete', False) and not pending and not errors
    if recent and recent['status'] == 'capped':
        recent['tail_recovered'] = not pending
    status = 'error' if errors else 'complete' if complete else 'capped'
    if status == 'complete' and cp['rows'] == 0 and (not recent or not recent['rows']):
        status = 'empty'
    return {'route': route, 'wallet': wallet, 'status': status, 'pages_this_run': pages,
            'event_scope': str(event_id) if event_id is not None else None,
            'rows_this_run': rows, 'total_pages': cp['pages'], 'raw_rows_total': cp['rows'],
            'window_start': 1 if route != 'positions' else None, 'window_end': cp['window_end'],
            'recent_head': recent, 'pending_recent_windows': len(pending),
            'complete_accessible_window': complete, 'historical_window_complete': cp.get('complete', False), 'errors': errors,
            'left_censored': True, 'age_note': 'Ancienneté observée uniquement ; indexation antérieure et transferts hors API non garantis.',
            'checkpoint_key': key, 'identity_note': 'API sans logIndex : lignes identiques potentiellement ambiguës, réponses brutes conservées.'}


def _wallet_rows(store, kind, wallet, limit=1000, event_id=None):
    params = ('wallet_' + kind, wallet + ':%')
    where='kind=? AND key LIKE ?'
    if event_id is not None:
        where+=" AND json_extract(payload,'$.event_scope')=?";params+= (str(event_id),)
    total = store.conn.execute('SELECT COUNT(*) FROM objects WHERE '+where, params).fetchone()[0]
    rows = store.conn.execute('SELECT payload FROM objects WHERE '+where+' ORDER BY observed_at DESC LIMIT ?',
                              (*params, limit))
    return [json.loads(r['payload']) for r in rows], total


def funding_graph(edges, wallets, max_addresses):
    graph = nx.MultiDiGraph()
    for wallet in wallets[:max_addresses]:
        graph.add_node(wallet, kind='wallet_observed')
    dropped = 0
    for edge in edges:
        needed = set((edge['source'], edge['target'])) - set(graph)
        if len(graph) + len(needed) > max_addresses:
            dropped += 1
            continue
        graph.add_edge(edge['source'], edge['target'], key=f'{edge["transaction_hash"]}:{edge["log_index"]}', **edge)
    shared = []
    for source in graph:
        recipients = sorted(set(graph.successors(source)) & set(wallets))
        if len(recipients) > 1:
            outgoing = [d for _, _, d in graph.out_edges(source, data=True)]
            shared.append({'address': source, 'wallets': recipients, 'infrastructure': any(d.get('infrastructure') for d in outgoing),
                           'coordination_proven': False, 'common_control_inferred': False,
                           'interpretation': 'Financeur direct commun ; service/bridge/relayer et contrôle distinct possibles.'})
    return {'nodes': [{'address': n, **d} for n, d in graph.nodes(data=True)],
            'edges': [d for _, _, d in graph.edges(data=True)], 'shared_counterparties': shared,
            'dropped_edges_budget': dropped, 'depth': 1, 'ownership_clusters': [],
            'proof_level': 'liens directement observables, sans fusion des portefeuilles'}


def activity_sequences(rows):
    relevant = [x['row'] for x in rows if x['row'].get('type') in ('DEPOSIT', 'WITHDRAWAL', 'TRADE')]
    relevant.sort(key=lambda x: x['timestamp'])
    patterns = []
    for index, action in enumerate(relevant):
        if action['type'] != 'TRADE':
            continue
        previous = next((x for x in reversed(relevant[:index]) if x['type'] == 'DEPOSIT'), None)
        following = next((x for x in relevant[index + 1:] if x['type'] == 'WITHDRAWAL'), None)
        if previous and following:
            patterns.append({'deposit_tx': previous['transaction_hash'], 'trade_tx': action['transaction_hash'],
                             'withdrawal_tx': following['transaction_hash'],
                             'deposit_to_trade_seconds': action['timestamp'] - previous['timestamp'],
                             'trade_to_withdrawal_seconds': following['timestamp'] - action['timestamp'],
                             'interpretation': 'Séquence observée, affectation des fonds et information privilégiée non établies.'})
        if len(patterns) == 10:
            break
    return patterns


def _local_trades(store, wallet, event_id, event_slug, limit=20000):
    clauses, params = ["kind='trade'"], []
    if wallet:
        # Filter indexed identities before inflating payloads from the objects view.
        clauses.append("key IN (SELECT key FROM trade_index WHERE wallet=?)")
        params.append(wallet.lower())
    if event_id:
        clauses.append("(CAST(json_extract(payload,'$.event_id') AS TEXT)=? OR json_extract(payload,'$.event_slug')=?)")
        params.extend((event_id, event_slug))
    where = ' AND '.join(clauses)
    total = store.conn.execute('SELECT COUNT(*) FROM objects WHERE ' + where, params).fetchone()[0]
    rows = [json.loads(r['payload']) for r in store.conn.execute(
        'SELECT payload FROM objects WHERE ' + where + ' ORDER BY observed_at DESC LIMIT ?', [*params, limit])]
    return rows, total


def pending_signal_receipts(store, case, samples):
    """Advance across signal transactions instead of repeatedly inspecting the largest later trade."""
    by_tx = {t['transaction_hash'].lower(): t for t in samples if t.get('transaction_hash')}
    transactions = list(dict.fromkeys(tx.lower() for alert in case.get('alerts', [])
                        for tx in (alert.get('transactions') or ([alert['transaction_hash']] if alert.get('transaction_hash') else []))))
    for tx in transactions:
        known = store.get('receipt', tx)
        if not known or known['payload'].get('status') != 'confirmed':
            return [(tx, by_tx.get(tx))]
    return []


async def investigate(store, net, config, target):
    budget = Budget(net, config)
    started = time.time()
    case = target if isinstance(target, dict) else {}
    wallet = case.get('wallet', '') if case else (target if isinstance(target, str) and ADDRESS.fullmatch(target) else '')
    event_id = str(case.get('event_id') or '') if case else (str(target) if not wallet else '')
    input_event_id = event_id
    mapping_errors = []
    if wallet and not ADDRESS.fullmatch(wallet):
        raise ValueError('Adresse invalide')
    if wallet and event_id.startswith('unmapped:'):
        suffix = event_id.removeprefix('unmapped:')
        if HASH.fullmatch(suffix) or suffix.isdecimal() or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9-]{0,200}', suffix):
            event_id = ''
            mapping_errors.append({'stage': 'event_mapping', 'error': 'Identifiant condition/token sans événement Gamma ; enquête portefeuille conservée.'})
        else:
            event_id = suffix
    if not wallet and (not event_id or event_id.startswith('0x') or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9-]{0,200}', event_id) or (event_id.isdecimal() and int(event_id) == 0)):
        raise ValueError('Cible invalide : adresse complète, identifiant Gamma positif ou slug attendu')
    event_obj = store.get('event', event_id) if event_id else None
    lookup_identifier = event_id
    if event_id and not event_obj:
        try:
            row = store.conn.execute("SELECT key FROM objects WHERE kind='event' AND json_extract(payload,'$.slug')=?", (event_id,)).fetchone()
            if row:
                event_id = row['key']
            else:
                from .collect import Collector
                resolved = await Collector(store, budget, config).resolve_event(event_id)
                event_id = resolved['event_id']
            event_obj = store.get('event', event_id)
        except Exception as exc:
            if not wallet:
                raise
            mapping_errors.append({'stage': 'event_mapping', 'identifier': lookup_identifier,
                                   'error': f'{type(exc).__name__}: {str(exc)[:240]} ; enquête portefeuille conservée.'})
            event_id = ''
    event = event_obj['payload'] if event_obj else {}
    local, local_total = _local_trades(store, wallet, event_id, event.get('slug') or lookup_identifier)
    if wallet:
        if not event and local and not input_event_id:
            event_id = str(local[0].get('event_id', ''))
            event_obj = store.get('event', event_id)
            event = event_obj['payload'] if event_obj else {}
    result = {'id': str(case.get('id') or (wallet.lower() if wallet else event_id)), 'target': wallet or event_id,
              'event_id': event_id, 'event': event, 'wallet': wallet.lower() if wallet else None,
              'event_mapping': {'input': input_event_id, 'lookup': lookup_identifier,
                                'canonical_id': event_id or None, 'status': 'resolved' if event else 'unknown',
                                'scope': 'event_and_wallet' if event and wallet else 'wallet_only' if wallet else 'event'},
              'created_at': started, 'calculated_at': started, 'status': 'données insuffisantes',
              'proof_level': 'hypothèse d’information privilégiée non établie',
              'histories': [], 'positions': [], 'receipts': [], 'activity_sequences': [], 'errors': list(mapping_errors),
              'coverage': {'local_trades': {'total': local_total, 'used': len(local), 'capped': local_total > len(local)}, 'wallet_cache': []},
              'limitations': ['Enquête exploratoire bornée ; aucune probabilité de délit ni identité civile.',
                              'Coût de revient indépendant : non calculable sans historique comptable complet.',
                              'Positions et PnL API sont des affirmations de source observées maintenant, exclues du score préalable.',
                              'Marchés d’un même événement liés : observations non indépendantes.'],
              'contradictions': ['Expertise, chance, information publique, arbitrage, couverture, copie et automatisation restent possibles.'],
              'score_snapshot': case.get('score'), 'signals_snapshot': case.get('signals', []),
              'signal_calculated_at': case.get('calculated_at'), 'public_availability': 'première disponibilité publique inconnue'}
    if event:
        try:
            result['resolution'] = await resolution_state(store, budget, event)
        except Exception as exc:
            result['errors'].append({'stage': 'resolution', 'error': f'{type(exc).__name__}: {str(exc)[:240]}'})
    if not wallet and not local and event_id:
        try:
            response = await budget.request(DATA + 'trades', params={'event_id': event_id, 'limit': 100, 'taker_only': 'true'})
            body = response.body
            if not isinstance(body, dict) or not isinstance(body.get('data'), list):
                raise ValueError('Invalid event trade page')
            for t in body['data']:
                local.append(dict(t, wallet=t['proxy_wallet'], event_id=event_id,
                                  nominal=float(t['size']) * float(t['price']), observed_at=response.observed_at))
            result['limitations'].append('Sélection par les 100 trades les plus récents de l’événement, page bornée.')
        except Exception as exc:
            result['errors'].append({'stage': 'event_trades', 'error': f'{type(exc).__name__}: {str(exc)[:240]}'})
    weights = defaultdict(float)
    for trade in local:
        address = trade.get('wallet', '').lower()
        if ADDRESS.fullmatch(address):
            weights[address] += abs(float(trade.get('nominal', 0)))
    wallets = [wallet.lower()] if wallet else sorted(weights, key=weights.get, reverse=True)[:min(2, config['investigation_max_addresses'])]
    result['wallets'] = wallets
    scoped_event=event_id if event and str(event_id).isdigit() else None
    if scoped_event:
        result['limitations'].append('Historiques wallet ciblés sur cet événement ; financement sans événement et activité ailleurs non rafraîchis. Ancienneté globale non déduite.')
    if not wallets:
        result['limitations'].append('Aucun portefeuille attribuable dans le périmètre accessible.')
    context, edges, checked = {}, [], set()
    for address in wallets:
        for route in ('trades', 'activity', 'positions'):
            try:
                history = await wallet_feed(store, budget, config, address, route, started,scoped_event)
                result['histories'].append(history)
                result['errors'].extend({'stage': route, 'wallet': address, 'error': e} for e in history['errors'])
            except Exception as exc:
                result['errors'].append({'stage': route, 'wallet': address, 'error': f'{type(exc).__name__}: {str(exc)[:240]}'})
        positions, positions_total = _wallet_rows(store, 'positions', address, 200,scoped_event)
        scope_suffix=':event:'+str(scoped_event) if scoped_event else ''
        position_checkpoint = store.checkpoint(f'investigate:{address}:positions'+scope_suffix) or {}
        cached_positions_used = len(positions)
        positions = [p for p in positions if p.get('snapshot_end') == position_checkpoint.get('window_end')]
        result['positions'].extend(positions)
        activity, activity_total = _wallet_rows(store, 'activity', address, 1000,scoped_event)
        result['coverage']['wallet_cache'].extend([
            {'wallet': address, 'route': 'positions', 'total': positions_total, 'cache_read': cached_positions_used,
             'current_snapshot_used': len(positions), 'older_snapshot_excluded': cached_positions_used - len(positions),
             'capped': positions_total > cached_positions_used},
            {'wallet': address, 'route': 'activity', 'total': activity_total, 'used': len(activity), 'capped': activity_total > len(activity)}])
        result['activity_sequences'].append({'wallet': address, 'sequences': activity_sequences(activity)})
        samples = [t for t in local if t.get('wallet', '').lower() == address]
        if not samples:
            sample_rows, sample_total = _wallet_rows(store, 'trades', address, 3,scoped_event)
            samples = [dict(x['row'], wallet=address) for x in sample_rows]
            result['coverage']['wallet_cache'].append({'wallet': address, 'route': 'trade_receipt_sample',
                'total': sample_total, 'used': len(samples), 'capped': sample_total > len(samples)})
        samples.sort(key=lambda t: float(t.get('nominal', float(t.get('size', 0)) * float(t.get('price', 0)))), reverse=True)
        funding = [x['row'] for x in activity if x['row'].get('type') in ('DEPOSIT', 'WITHDRAWAL')]
        receipt_jobs = pending_signal_receipts(store, case, samples) if case.get('alerts') else [(t['transaction_hash'], t) for t in samples[:1] if t.get('transaction_hash')]
        receipt_jobs += [(t['transaction_hash'], None) for t in funding[:1] if t.get('transaction_hash')]
        for tx, trade in receipt_jobs:
            if (address, tx) in checked:
                continue
            checked.add((address, tx))
            try:
                receipt = await inspect_receipt(store, budget, config, tx, address, trade, context)
                result['receipts'].append(receipt)
                if receipt['status'] == 'confirmed':
                    edges.extend(receipt['transfers'])
                else:
                    result['limitations'].append(f'Reçu {tx}: {receipt["status"]}, preuve non finale.')
            except Exception as exc:
                result['errors'].append({'stage': 'receipt', 'transaction_hash': tx,
                                         'error': f'{type(exc).__name__}: {str(exc)[:240]}'})
    result['graph'] = funding_graph(edges, wallets, config['investigation_max_addresses'])
    try:
        result['news'] = await collect_news(store, budget, config, event)
        result['public_availability'] = result['news']['availability']
        for source in result['news']['sources']:
            if source['status'] in ('error', 'uncovered', 'degraded', 'capped'):
                result['errors'].append({'stage': 'news:' + source['source'],
                    'error': source.get('detail', 'Couverture documentaire ' + source['status']), 'status': source['status']})
        if result['news']['items']:
            result['contradictions'].append('Mentions publiques pertinentes retrouvées ; leur portée exacte et antériorité demandent examen.')
        if result['news']['public_result']:
            result['status'] = 'information publique retrouvée'
        elif result['news'].get('official_resolution_known'):
            result['status'] = 'résolution officielle observée ; date publique inconnue'
        elif event.get('closed'):
            result['status'] = 'événement terminé'
    except Exception as exc:
        result['errors'].append({'stage': 'news', 'error': f'{type(exc).__name__}: {str(exc)[:240]}'})
    if any(p['row'].get('mergeable') for p in result['positions']):
        result['contradictions'].append('Positions complémentaires signalées par la source : couverture/arbitrage plausible.')
    incomplete = [h for h in result['histories'] if not h['complete_accessible_window']]
    if incomplete:
        result['limitations'].append(f'{len(incomplete)} parcours de données incomplets, curseurs conservés pour reprise.')
    result['budget'] = {'logical_requests': budget.calls, 'logical_request_limit': config['investigation_max_requests'],
                        'transport_attempt_ceiling': config['investigation_max_requests'] * config.get('request_attempts', 3),
                        'elapsed_seconds': round(time.monotonic() - budget.started, 3),
                        'address_limit': config['investigation_max_addresses'], 'depth_limit': 1}
    result['evidence_ids'] = list(dict.fromkeys(budget.evidence_ids))
    result['completed_at'] = time.time()
    cache_capped = result['coverage']['local_trades']['capped'] or any(x['capped'] for x in result['coverage']['wallet_cache'])
    result['truncated'] = bool(incomplete or result['graph']['dropped_edges_budget'] or cache_capped or
                               result.get('news', {}).get('truncated') or any('Budget' in x['error'] for x in result['errors']))
    store.put('investigation', result['id'], result)
    store.health('investigation:' + result['id'], 'degraded' if result['errors'] or result['truncated'] else 'ok',
                 'Enquête bornée enregistrée ; pertinence statistique non validée', requests=budget.calls)
    return result
