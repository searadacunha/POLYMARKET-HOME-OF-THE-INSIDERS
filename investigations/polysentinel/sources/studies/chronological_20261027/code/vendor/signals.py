"""Exploratory point-in-time rules; a score is never an insider probability."""
import hashlib
import json
import math
from bisect import bisect_right
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from statistics import median

VERSION = 'exploratory-1.2'


def epoch(value):
    if value is None or value == '':
        return None
    if isinstance(value, (int, float)):
        return float(value) if math.isfinite(value) else None
    try:
        parsed = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        return parsed.timestamp() if parsed.tzinfo else None
    except (TypeError, ValueError):
        return None


def _number(value, name):
    try:
        value = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f'Invalid {name}: {value!r}') from exc
    if not math.isfinite(value):
        raise ValueError(f'Non-finite {name}')
    return value


def group_fills(trades, *, now):
    """One order per wallet/token/side; otherwise a conservative transaction group."""
    groups, seen = {}, {}
    for original in trades:
        at, observed = epoch(original.get('timestamp')), epoch(original.get('observed_at'))
        if at is None or observed is None:
            raise ValueError('Trade timestamp and observed_at are required')
        if at > now or observed > now:
            continue
        row = dict(original)
        size, price = _number(row.get('size'), 'size'), _number(row.get('price'), 'price')
        if size <= 0 or not 0 <= price <= 1 or row.get('side') not in ('BUY', 'SELL'):
            raise ValueError(f'Invalid trade economics: {row.get("id")}')
        if not row.get('id') or not row.get('wallet') or not row.get('token_id'):
            raise ValueError('Trade id, wallet and token_id are required')
        identity = (row['wallet'].lower(), row['token_id'], row['side'], at, size, price,
                    row.get('transaction_hash'), row.get('order_hash'))
        if row['id'] in seen:
            if seen[row['id']] != identity:
                raise ValueError(f'Conflicting duplicate trade: {row["id"]}')
            continue
        seen[row['id']] = identity
        row.update(wallet=row['wallet'].lower(), size=size, price=price, nominal=size*price)
        parent = row.get('order_hash') or row.get('transaction_hash') or row['id']
        key = (row['wallet'], str(row['token_id']), row['side'], parent)
        if key not in groups:
            groups[key] = dict(row, size=0.0, nominal=0.0, trade_ids=[], transactions=[],
                               log_indices=[], fee=0.0,
                               first_timestamp=at, timestamp=at, observed_at=observed,
                               grouping='order' if row.get('order_hash') else 'transaction')
        group = groups[key]
        group['size'] += size
        group['nominal'] += size*price
        group['price'] = group['nominal']/group['size']
        group['timestamp'] = max(group['timestamp'], at)
        group['first_timestamp'] = min(group['first_timestamp'], at)
        group['observed_at'] = max(group['observed_at'], observed)
        group['trade_ids'].append(str(row['id']))
        if (group['fee'] is not None and row.get('fee') is not None and
                row.get('fee_unit') == group.get('fee_unit') and row.get('fee_unit')):
            group['fee'] += _number(row['fee'], 'fee')
        else:
            group['fee'] = None
        if row.get('log_index') is not None:
            group['log_indices'].append(row['log_index'])
        if row.get('transaction_hash') and row['transaction_hash'] not in group['transactions']:
            group['transactions'].append(row['transaction_hash'])
        group['id'] = hashlib.sha256(json.dumps(key).encode()).hexdigest()[:24]
        if len(group['transactions']) > 1:
            group['transaction_hash'] = None
    return sorted(groups.values(), key=lambda r: (r['timestamp'], r['id']))


def bookkeeping(trades, *, history_complete=False):
    """Average-cost accounting, calculable only with a known empty opening inventory."""
    rows, seen = [], {}
    for row in trades:
        if row.get('id') and row.get('type', 'TRADE') == 'TRADE':
            signature = tuple(row.get(k) for k in ('wallet','token_id','side','size','price','timestamp'))
            if row['id'] in seen:
                if seen[row['id']] != signature:
                    raise ValueError('Conflicting duplicate trade in accounting')
                continue
            seen[row['id']] = signature
        rows.append(row)
    transform = any(r.get('type', 'TRADE') != 'TRADE' for r in rows)
    time_sides = defaultdict(set)
    for row in rows:
        if row.get('type', 'TRADE') == 'TRADE':
            time_sides[row.get('token_id'), row.get('timestamp')].add(row.get('side'))
    mixed_times = {key for key,sides in time_sides.items() if len(sides)>1}
    ordering_uncertain = any((r.get('token_id'),r.get('timestamp')) in mixed_times and
                             (r.get('log_index') is None or r.get('block_number') is None) for r in rows)
    ledger = defaultdict(lambda: dict(quantity=Decimal(0), cost=Decimal(0),
                                     fee_cost=Decimal(0), delta=Decimal(0),
                                     valid=True, fees_known=True))
    gross = net = volume = cash = Decimal(0)
    for row in sorted((r for r in rows if r.get('type', 'TRADE') == 'TRADE'),
                      key=lambda r: (r.get('timestamp', 0), r.get('block_number') or 0,
                                     r.get('log_index') or 0, str(r.get('id', '')))):
        size = Decimal(str(_number(row.get('size'), 'size')))
        price = Decimal(str(_number(row.get('price'), 'price')))
        if size <= 0 or not Decimal(0) <= price <= Decimal(1) or row.get('side') not in ('BUY', 'SELL'):
            raise ValueError('Invalid trade economics')
        token = ledger[str(row['token_id'])]
        amount = size*price
        volume += amount
        fee = row.get('fee')
        fee_known = fee is not None and row.get('fee_unit') in ('collateral', 'pUSD', 'USDC', 'USDC.e')
        fee = Decimal(str(_number(fee, 'fee'))) if fee_known else Decimal(0)
        if fee < 0:
            raise ValueError('Negative fee requires a separately identified rebate')
        token['fees_known'] &= fee_known
        if row['side'] == 'BUY':
            token['quantity'] += size
            token['delta'] += size
            token['cost'] += amount
            token['fee_cost'] += fee
            cash -= amount
        else:
            token['delta'] -= size
            cash += amount
            if token['quantity'] < size:
                token['valid'] = False
                continue
            fraction = size/token['quantity']
            cost, buy_fee = token['cost']*fraction, token['fee_cost']*fraction
            gross += amount-cost
            net += amount-cost-buy_fee-fee
            token['quantity'] -= size
            token['cost'] -= cost
            token['fee_cost'] -= buy_fee
    calculable = history_complete and not transform and not ordering_uncertain and all(t['valid'] for t in ledger.values())
    fees_known = all(t['fees_known'] for t in ledger.values())
    return {
        'status': 'calculable' if calculable and fees_known else 'non calculable',
        'basis': 'coût moyen; ouverture vide explicitement connue' if history_complete else 'historique censuré; inventaire initial inconnu',
        'realized_gross': float(gross) if calculable else None,
        'realized_net': float(net) if calculable and fees_known else None,
        'volume': float(volume), 'cash_flow_gross': float(cash),
        'unrealized_pnl': None, 'settlements': None, 'rebates': None,
        'transformations_present': transform,
        'ordering_uncertain': ordering_uncertain,
        'tokens': {k: {'observed_inventory_delta': float(v['delta']),
                       'actual_inventory': float(v['quantity']) if calculable else None}
                   for k, v in ledger.items()},
    }


def _signal(rule, family, value, reference, n, quality='exploratoire', weight=1):
    return dict(rule=rule, version=VERSION, family=family, value=value,
                reference=reference, n=n, quality=quality, weight=weight)


def _category(event, config):
    tags = event.get('tags', [])
    tags = [x.get('slug', '') if isinstance(x, dict) else str(x) for x in tags]
    return next((t for t in config.get('priority_tags', []) if t in tags),
                sorted(tags)[0] if tags else None)


def _cohort(group, market, event, first_seen, config):
    observed = epoch(market.get('observed_at'))
    liquidity = market.get('liquidity')
    end = epoch(market.get('end_date') or event.get('end_date'))
    category = _category(event, config)
    if (observed is None or not 0 <= group['timestamp']-observed <= 1800 or
            liquidity is None or not category or end is None or end < group['timestamp']):
        return None
    liquidity = _number(liquidity, 'liquidity')
    if liquidity <= 0:
        return None
    return (category, min(int(group['price']*5), 4),
            int(math.log10(max(1, end-group['timestamp']))),
            int(math.log10(liquidity)),
            int(math.log10(max(1, group['timestamp']-first_seen))))


def _versions(rows, now):
    versions = defaultdict(list)
    for row in rows:
        observed = epoch(row.get('observed_at'))
        if observed is not None and observed <= now:
            versions[str(row['id'])].append((observed, row))
    for key, values in versions.items():
        values.sort(key=lambda pair: pair[0])
        versions[key] = ([pair[0] for pair in values], [pair[1] for pair in values])
    return versions


def _at(versions, key, timestamp):
    times, values = versions.get(str(key), ([], []))
    index = bisect_right(times, timestamp)-1
    return values[index] if index >= 0 else {}


def _preliminary_exclusion(group, markets, events, now):
    for label, metadata in (('événement', events.get(str(group.get('event_id')), {})),
                            ('marché', markets.get(str(group.get('market_id')), {}))):
        public_at = epoch(metadata.get('public_at'))
        observed = epoch(metadata.get('public_observed_at'))
        if (public_at is not None and observed is not None and max(public_at, observed) <= now) or (
                metadata.get('result_available') is True and metadata.get('verified') is True):
            return label + ': résultat public connu'
        if metadata.get('closed') is True or metadata.get('resolved') is True or metadata.get('active') is False:
            return label + ': fermé, résolu ou inactif'
        end = epoch(metadata.get('end_date'))
        if end is not None and end <= now:
            return label + ': échéance passée'
    return None


def evaluate(trades, markets, events, *, now, config, wallet_history=None):
    """Return reproducible wallet/event dossiers, including retained learning candidates."""
    groups = group_fills(trades, now=now)
    market_versions, event_versions = _versions(markets, now), _versions(events, now)
    markets = {key: values[1][-1] for key, values in market_versions.items()}
    events = {key: values[1][-1] for key, values in event_versions.items()}
    by_wallet, by_case, comparable = defaultdict(list), defaultdict(list), defaultdict(list)
    for g in groups:
        market = markets.get(str(g.get('market_id')), {})
        if not g.get('event_id') and market.get('event_id'):
            g['event_id'] = str(market['event_id'])
        if not g.get('event_id'):
            g['event_id'] = 'unmapped:' + str(g.get('event_slug') or g.get('condition_id') or g['token_id'])
        by_wallet[g['wallet']].append(g)
        by_case[g['wallet'], str(g.get('event_id') or 'unknown')].append(g)
    exclusions = {g['id']: _preliminary_exclusion(g, markets, events, now) for g in groups}
    large = float(config.get('large_nominal', 1000))
    minimum = int(config.get('minimum_baseline', 20))
    window = float(config.get('signal_window_seconds', 86400))
    cutoff = now-window
    group_signals = defaultdict(list)
    for g in groups:
        if g['side'] != 'BUY':
            continue
        market = _at(market_versions, g.get('market_id'), g['first_timestamp'])
        event = _at(event_versions, g.get('event_id'), g['first_timestamp'])
        history = [r for r in by_wallet[g['wallet']] if r['timestamp'] < g['first_timestamp']]
        known=(wallet_history or {}).get(g['wallet'],{})
        first = min(by_wallet[g['wallet']][0]['timestamp'],known.get('first_timestamp',float('inf')))
        prior = [r['nominal'] for r in history if r['side'] == 'BUY']
        if g['timestamp'] >= cutoff and g['nominal'] >= large:
            if not history and first>=g['first_timestamp']:
                group_signals[g['id']].append(_signal('first_observed_large', 'exposure', g['nominal'],
                    {'threshold': large, 'age': 'première activité connue du bot ; âge réel inconnu',
                     'scope': 'toutes observations stockées disponibles au calcul' if wallet_history is not None else 'entrées fournies seulement',
                     'first_known_timestamp':first}, 0,
                    'historique censuré'))
            if len(prior) >= minimum:
                med = median(prior)
                mad = median(abs(x-med) for x in prior)
                threshold = max(5*med, med+6*1.4826*mad, large)
                if g['nominal'] >= threshold:
                    group_signals[g['id']].append(_signal('wallet_size_shift', 'size', g['nominal'],
                        {'median': med, 'mad': mad, 'threshold': threshold,
                         'from': history[0]['timestamp'], 'before': g['first_timestamp']}, len(prior)))
            observed = epoch(market.get('observed_at'))
            liquidity = market.get('liquidity')
            if observed is not None and 0 <= g['first_timestamp']-observed <= 1800 and liquidity is not None:
                liquidity = _number(liquidity, 'liquidity')
                if liquidity > 0 and g['nominal']/liquidity >= .1:
                    group_signals[g['id']].append(_signal('liquidity_fraction', 'size', g['nominal']/liquidity,
                        {'liquidity': liquidity, 'observed_at': observed, 'threshold': .1,
                         'meaning': 'liquidité Gamma, pas profondeur exécutable'}, 1))
            categories = {_category(_at(event_versions, r.get('event_id'), r['timestamp']), config) for r in history}
            category = _category(event, config)
            if len(history) >= minimum and category and category not in categories and None not in categories:
                group_signals[g['id']].append(_signal('specialization_shift', 'rotation', category,
                    {'previous_categories': sorted(categories), 'before': g['first_timestamp']}, len(history)))
        cohort = _cohort(g, market, event, first, config)
        if cohort is not None:
            peers = [r for r in comparable[cohort] if r['wallet'] != g['wallet'] and r['timestamp'] < g['first_timestamp']]
            if g['timestamp'] >= cutoff and g['nominal'] >= large and len(peers) >= minimum:
                amounts = [p['nominal'] for p in peers]
                med = median(amounts)
                mad = median(abs(x-med) for x in amounts)
                threshold = max(5*med, med+6*1.4826*mad, large)
                if g['nominal'] >= threshold:
                    group_signals[g['id']].append(_signal('cohort_size', 'size', g['nominal'],
                        {'cohort': list(cohort), 'median': med, 'mad': mad, 'threshold': threshold,
                         'unit': 'groupes de fills; wallets dépendants possibles'}, len(peers)))
            comparable[cohort].append(g)
    # Synchrony is a pattern of distinct transactions, never a shared-ownership conclusion.
    sync_groups = defaultdict(list)
    for g in groups:
        if g['side'] == 'BUY' and g['timestamp'] >= cutoff and g['nominal'] >= large/4:
            sync_groups[str(g.get('event_id')), str(g.get('market_id')), g['token_id']].append(g)
    synchronization = {}
    for rows in sync_groups.values():
        left = 0
        for right, g in enumerate(rows):
            while rows[left]['timestamp'] < g['timestamp']-90:
                left += 1
            batch = rows[left:right+1]
            tx_wallets = defaultdict(set)
            for r in batch:
                for tx in r['transactions']:
                    tx_wallets[tx].add(r['wallet'])
            distinct = {tx: next(iter(wallets)) for tx, wallets in tx_wallets.items() if len(wallets)==1}
            wallets = set(distinct.values())
            txs = set(distinct)
            if len(wallets) >= 3:
                for r in batch:
                    if r['wallet'] in wallets:
                        synchronization[r['id']] = dict(wallets=sorted(wallets), transactions=sorted(txs),
                            from_time=batch[0]['timestamp'], to_time=g['timestamp'])
    cases = []
    for (wallet, event_id), rows in by_case.items():
        recent = [g for g in rows if g['timestamp'] >= cutoff]
        buys = [g for g in recent if g['side'] == 'BUY']
        if not buys:
            continue
        event = events.get(event_id, {})
        history = by_wallet[wallet]
        active_rows = [g for g in rows if not exclusions[g['id']]]
        historical_rows = [g for g in rows if exclusions[g['id']]]
        active_recent = [g for g in recent if not exclusions[g['id']]]
        historical_recent = [g for g in recent if exclusions[g['id']]]
        buys = [g for g in active_recent if g['side']=='BUY']
        retrospective_buys = [g for g in historical_recent if g['side']=='BUY']
        active_history = [g for g in history if not exclusions[g['id']]]
        historical_history = [g for g in history if exclusions[g['id']]]
        signals, sync = _case_rules(active_rows, active_recent, buys, active_history,
            [g for g in active_history if g['timestamp'] >= cutoff], group_signals,
            synchronization, events, cutoff, now, large)
        retrospective_signals, _ = _case_rules(historical_rows, historical_recent,
            retrospective_buys, historical_history,
            [g for g in historical_history if g['timestamp'] >= cutoff], group_signals,
            synchronization, events, cutoff, now, large)
        if not signals and not retrospective_signals:
            continue
        cases.append(_case(wallet, event_id, rows, recent, buys, event, markets, signals,
            sync, now, config, retrospective_buys, retrospective_signals, exclusions))
    return sorted(cases, key=lambda c: (-c['score'], c['id']))


def _case_rules(rows, recent, buys, history, wallet_recent, group_signals,
                synchronization, events, cutoff, now, large):
    signals = [s for g in buys for s in group_signals[g['id']]]
    spend = sum(g['nominal'] for g in buys)
    total = sum(g['nominal'] for g in wallet_recent if g['side'] == 'BUY')
    if spend >= large and total and spend/total >= .8:
        signals.append(_signal('event_concentration', 'exposure', spend/total,
            {'threshold': .8, 'event_buy_nominal': spend, 'wallet_buy_nominal': total,
             'window_start': cutoff, 'window_end': now, 'scope': 'univers collecté seulement'},
            len([g for g in wallet_recent if g['side'] == 'BUY']), 'historique censuré'))
    old_markets = {str(g.get('market_id')) for g in rows if g['timestamp'] < cutoff}
    new_markets = {str(g.get('market_id')) for g in buys}-old_markets
    if old_markets and len(new_markets) >= 2 and spend >= large:
        signals.append(_signal('linked_market_rotation', 'rotation', sorted(new_markets),
            {'previous_markets': sorted(old_markets), 'relation': 'même événement Gamma',
             'independence_assumed': False}, len(rows)-len(recent)))
    sync = [synchronization[g['id']] for g in buys if g['id'] in synchronization]
    if sync:
        cluster = max(sync, key=lambda s: len(s['wallets']))
        signals.append(_signal('synchronized_entries', 'synchrony', len(cluster['wallets']),
            dict(cluster, maximum_seconds=90, minimum_nominal=large/4,
                 interpretation='rapprochement probabiliste; copie/arbitrage possibles'), len(cluster['wallets'])))
    repetitions = {str(g['event_id']) for g in history if g.get('event_id') and g['side']=='BUY' and g['nominal']>=large}
    if len(repetitions) >= 3 and spend >= large:
        known_groups = {events.get(e, {}).get('independence_group') for e in repetitions}
        independent = None not in known_groups and len(known_groups) >= 3
        signals.append(_signal('repeated_large_entries', 'recurrence', len(repetitions),
            {'events': sorted(repetitions), 'independence_established': independent,
             'meaning': 'répétition de taille, sans connaissance des résultats'}, len(repetitions),
            'exploratoire' if independent else 'indépendance des événements non établie', int(independent)))
    return signals, sync


def _case(wallet, event_id, rows, recent, buys, event, markets, signals, sync, now, config,
          retrospective_buys, retrospective_signals, exclusions):
    # One point per phenomenon, even when several labels describe the same exposure.
    score = len({s['family'] for s in signals if s['weight']})
    public_at, public_observed = epoch(event.get('public_at')), epoch(event.get('public_observed_at'))
    public = public_at is not None and public_observed is not None and max(public_at, public_observed) <= now
    end = epoch(event.get('end_date'))
    finished = event.get('closed') is True or event.get('active') is False
    past_due = end is not None and end <= now
    context_buys = buys + retrospective_buys
    event_markets = [markets.get(str(g.get('market_id')), {}) for g in context_buys]
    if event_markets and all(m.get('closed') is True or m.get('resolved') is True or m.get('active') is False for m in event_markets):
        finished = True
    known_open = event.get('active') is True or any(m.get('active') is True and m.get('closed') is not True for m in event_markets)
    limitations = ['seuils exploratoires non calibrés', 'ancienneté observée censurée',
                   'couverture portefeuille et univers partielle',
                   'ordre parent absent sauf preuve on-chain; groupes transactionnels de secours',
                   'lien de scénario entre marchés non démontré par le seul événement Gamma']
    if not public:
        limitations.append('première disponibilité publique inconnue')
    if not known_open:
        limitations.append('statut ouvert du catalogue non vérifié')
    if past_due and not finished and not public:
        limitations.append('échéance passée sans confirmation du résultat: alerte préalable suspendue')
    if retrospective_buys:
        limitations.append('opérations de marchés terminés, à échéance passée ou au résultat public exclues des déclencheurs préalables')
    if not any(s['rule']=='cohort_size' for s in signals):
        limitations.append('cohorte comparable insuffisante ou métadonnées contemporaines absentes')
    contradictions = ['expertise, chance, information publique, copie, automatisation, arbitrage et couverture restent possibles']
    inventory = defaultdict(float)
    for g in rows:
        inventory[str(g.get('market_id')), g['token_id']] += g['size']*(1 if g['side']=='BUY' else -1)
    outcome_counts = defaultdict(int)
    for (market_id, token), amount in inventory.items():
        if amount > 0:
            outcome_counts[market_id] += 1
    if any(n > 1 for n in outcome_counts.values()):
        contradictions.append('plusieurs issues du même marché acquises: couverture ou arbitrage possible')
    if any(g['side']=='SELL' for g in recent):
        contradictions.append('ventes observées: les achats bruts ne sont pas une exposition nette')
    cid = hashlib.sha256(f'{wallet}|{event_id}|{VERSION}'.encode()).hexdigest()[:24]
    signals = sorted(signals, key=lambda s: (s['rule'], json.dumps(s['value'], sort_keys=True)))
    retrospective_signals = sorted(retrospective_signals, key=lambda s: (s['rule'], json.dumps(s['value'], sort_keys=True)))
    active_recent = [g for g in recent if not exclusions[g['id']]]
    fields = ('wallet','event_id','market_id','token_id','outcome','side','price','size','nominal',
              'fee','fee_unit','transaction_hash','transactions','log_index','log_indices','order_hash',
              'timestamp','observed_at','trade_ids')
    case = dict(id=cid, wallet=wallet, event_id=event_id, event_title=event.get('title'),
        status='information publique retrouvée' if public else 'événement terminé' if finished else 'données insuffisantes',
        score=0 if public or finished else score,
        retrospective_score=len({s['family'] for s in retrospective_signals if s['weight']}) if retrospective_signals else None,
        preliminary=bool(signals) and known_open and not public and not finished and not past_due,
        priority=bool(signals) and known_open and not public and not finished and not past_due and score>=config.get('candidate_score',2),
        calibrated=False, rule_version=VERSION,
        quality=dict(history_left_censored=True, public_information='retrouvée' if public else 'inconnue',
                     baseline_phase='apprentissage', trade_groups=len(rows), raw_fills=sum(len(g['trade_ids']) for g in rows),
                     preliminary_buy_groups=len(buys), retrospective_buy_groups=len(retrospective_buys),
                     sampling='union du flux global filtré par taille et de marchés suivis; aucune représentativité garantie'),
        coordination=dict(ownership_established=False, synchrony_detected=bool(sync), verified_financial_links=[]),
        signals=signals, retrospective_signals=retrospective_signals,
        created_at=min(g['observed_at'] for g in rows), calculated_at=now,
        transaction_time=min(g['timestamp'] for g in context_buys), observation_time=max(g['observed_at'] for g in context_buys),
        public_milestone=public_at if public else None,
        evidence=[dict(transaction_hash=t, url=f'https://polygonscan.com/tx/{t}',
                       epistemic_status='affirmation Data API; reçu à rapprocher')
                  for t in sorted({t for g in active_recent for t in g['transactions']})],
        limitations=limitations, contradictions=contradictions,
        trade_ids=sorted({t for g in active_recent for t in g['trade_ids']}),
        alerts=[{k:g.get(k) for k in fields} for g in buys] if signals else [],
        retrospective_trade_ids=sorted({t for g in retrospective_buys for t in g['trade_ids']}),
        retrospective_trades=[dict({k:g.get(k) for k in fields},exclusion_reason=exclusions[g['id']]) for g in retrospective_buys],
        observed_net_cash_exposure=sum(g['nominal']*(1 if g['side']=='BUY' else -1) for g in rows),
        observed_inventory=[dict(market_id=m,token_id=t,shares=q) for (m,t),q in sorted(inventory.items())],
        related_scenarios=dict(observed_outcomes=sorted({(str(g.get('market_id')),str(g.get('outcome'))) for g in buys}),
                               coherence='non établie; règles de résolution à rapprocher', independence_assumed=False),
        actual_inventory='non calculable', realized_pnl='non calculable')
    material = {k:v for k,v in case.items() if k not in ('calculated_at','observation_time','created_at')}
    # Window boundaries do not constitute new evidence by themselves.
    for key in ('signals', 'retrospective_signals'):
        material[key] = [{**s, 'reference': {k:v for k,v in s['reference'].items()
                         if k not in ('window_start','window_end')}} for s in case[key]]
    case['material_fingerprint'] = hashlib.sha256(json.dumps(material, sort_keys=True).encode()).hexdigest()
    return case


def describe_scenarios(markets):
    """Describe conditional rank constraints from explicit labels, never score them."""
    import re
    import unicodedata

    patterns = [
        ('winner', r"^Will (?P<subject>.+?) (?:win|be the winner of) (?P<context>.+)$"),
        ('top_n', r"^Will (?P<subject>.+?) (?:finish|place)(?: in)? (?:the )?top (?P<rank>\d+)(?: (?:in|of|at))? (?P<context>.+)$"),
        ('exact_rank', r"^Will (?P<subject>.+?) (?:finish|place) (?P<rank>\d+)(?:st|nd|rd|th)(?: (?:in|of|at))? (?P<context>.+)$"),
        ('winner', r"^(?P<subject>.+?) (?:remportera|gagnera)-t-(?:il|elle) (?P<context>.+)$"),
        ('top_n', r"^(?P<subject>.+?) (?:terminera|finira)-t-(?:il|elle) (?:dans )?(?:le )?top (?P<rank>\d+)(?: (?:de|du|au))? (?P<context>.+)$"),
        ('exact_rank', r"^(?P<subject>.+?) (?:terminera|finira)-t-(?:il|elle) (?:exactement )?(?:à la )?(?P<rank>\d+)(?:er|e|ème|eme)(?: place)?(?: (?:de|du|au))? (?P<context>.+)$"),
    ]
    generic = [
        ('winner', r"^Who will win (?P<context>.+)$"),
        ('winner', r"^(?P<context>.+?) (?:winner|vainqueur)$"),
        ('top_n', r"^Who will (?:finish|place)(?: in)? (?:the )?top (?P<rank>\d+)(?: (?:in|of|at))? (?P<context>.+)$"),
        ('exact_rank', r"^Who will (?:finish|place) (?P<rank>\d+)(?:st|nd|rd|th)(?: (?:in|of|at))? (?P<context>.+)$"),
    ]
    def normalized(text):
        return ' '.join(unicodedata.normalize('NFC', text).casefold().split())
    latest = {}
    for market in markets:
        key = str(market.get('id', ''))
        if key and (key not in latest or (epoch(market.get('observed_at')) or 0) >= (epoch(latest[key].get('observed_at')) or 0)):
            latest[key] = market
    groups, unknown = {}, []
    for key, market in sorted(latest.items()):
        title = str(market.get('question') or market.get('title') or '').strip().rstrip('?').strip()
        event = str(market.get('event_id') or '')
        tokens = [t for t in market.get('tokens', []) if isinstance(t, dict) and t.get('outcome')]
        match = None
        named = False
        for relation, pattern in patterns + generic:
            match = re.fullmatch(pattern, title, re.IGNORECASE)
            if match:
                named = 'subject' not in match.groupdict()
                break
        reason = None
        if not event:
            reason = 'événement non identifié; aucun rapprochement inter-marchés'
        elif match is None:
            reason = 'relation de classement non explicite dans le titre'
        elif relation == 'winner' and re.match(
                r"^(?:the )?(?:at least|at most|more than|fewer than|over|under|any |a |an |one of |another |au moins|au plus|plus de|moins de|un |une |des |\d+ (?:games|matches|points|medals|awards)\b)",
                match['context'], re.IGNORECASE):
            reason = 'victoire portant sur une quantité ou une possibilité, pas un rang final explicite'
        entries = []
        if match and reason is None:
            rank = int(match.groupdict().get('rank') or 1)
            if rank < 1:
                reason = 'rang non positif'
            elif named:
                for token in tokens:
                    label = str(token['outcome']).strip()
                    if normalized(label) not in {'yes','no','oui','non','other','any other','autre','autres','0','1'}:
                        entries.append((label, token, None))
                if not entries:
                    reason = 'aucune issue nommée permettant de reconnaître le sujet'
            else:
                positive = [t for t in tokens if normalized(str(t['outcome'])) in {'yes','oui'}]
                negative = [t for t in tokens if normalized(str(t['outcome'])) in {'no','non'}]
                if len(positive)==1 and len(negative)==1:
                    entries = [(match['subject'].strip(), positive[0], negative[0])]
                else:
                    reason = 'libellés affirmatif/négatif non explicites; indices de tokens ignorés'
        if reason:
            unknown.append(dict(market_id=key, question=title, reason=reason))
            continue
        context = re.sub(r"^(?:the |le |la |les |l['’])", '', match['context'].strip(), flags=re.IGNORECASE)
        for subject, positive, negative in entries:
            group_key = (event, normalized(subject), normalized(context))
            group = groups.setdefault(group_key, dict(event_id=event, subject=subject, competition_text=context,
                interpretation='rapprochement textuel probabiliste', resolution_equivalence_verified=False,
                condition='Même compétition, même classement final et règles de résolution concordantes à vérifier.', markets=[]))
            group['markets'].append(dict(market_id=key, question=title, relation=relation, rank=rank,
                positive_token_id=positive.get('token_id'), positive_outcome=positive['outcome'],
                negative_token_id=negative.get('token_id') if negative else None,
                negative_outcome=negative.get('outcome') if negative else 'toute autre issue de ce marché',
                matched_subject=subject))
    for group in groups.values():
        boundaries = {1}
        for market in group['markets']:
            rank = market['rank']
            boundaries.add(rank+1)
            if market['relation'] != 'top_n':
                boundaries.add(rank)
        boundaries = sorted(boundaries)
        group['coherent_scenarios'] = []
        for i, start in enumerate(boundaries):
            end = boundaries[i+1]-1 if i+1 < len(boundaries) else None
            outcomes = {m['market_id']: (start <= m['rank'] if m['relation']=='top_n' else start == m['rank']) for m in group['markets']}
            group['coherent_scenarios'].append(dict(rank_interval=[start,end], affirmative_outcomes=outcomes,
                status='conditionnel; ne constitue ni une prédiction ni une garantie de règlement'))
    return dict(version='text-scenarios-1', interpretation='rapprochement textuel probabiliste',
                independence_assumed=False, score_bonus=0, groups=list(groups.values()), unclassified=unknown,
                limitations=['Le même événement Gamma ne prouve pas une règle de classement commune.',
                             'Égalités, ex aequo, annulations et règles propres doivent être vérifiés dans les sources.',
                             'Les formulations non reconnues restent non classées; aucune multiplication de probabilités.'])
