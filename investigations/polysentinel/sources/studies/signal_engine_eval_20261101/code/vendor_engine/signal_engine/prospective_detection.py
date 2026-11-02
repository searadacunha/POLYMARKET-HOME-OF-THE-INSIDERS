"""Engine A: detection from what was observable at the decision time, and nothing later.

It cannot see outcomes, future prices, profit or win rates: those live in post_event_investigation,
which this module does not import, and a test enforces that boundary.
"""
import hashlib
import json
from collections import defaultdict
from pathlib import Path

from .collective_behavior import collective_signals
from .comparators import Comparators, strata, STRUCTURE_FAMILY
from .evidence_scoring import ANOMALOUS, CATEGORY_ORDER, classify, needs_review_now, review_rank
from .market_information_risk import assess_market
from .position_anomalies import position_anomalies, position_profile
from .wallet_behavior import wallet_anomalies, wallet_profile

METRICS = ('size_ratio', 'frequency_ratio', 'max_market_spend', 'market_share_24h', 'liquidity_fraction', 'burst_nominal')


def load_config(path=None):
    return json.loads(Path(path or Path(__file__).with_name('config.json')).read_text())


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), default=str).encode()).hexdigest()


def market_context(store, condition_id, now, cache):
    if condition_id not in cache:
        row = store.cx.execute('SELECT * FROM markets WHERE condition_id=?', (condition_id,)).fetchone()
        tags = json.loads(row['tags']) if row and row['tags'] else []
        risk = assess_market(row['title'] if row else None, row['rules'] if row else None, tags, bool(row and row['sports']))
        cache[condition_id] = dict(title=row['title'] if row else None, end_at=row['end_at'] if row else None, closed_at=row['closed_at'] if row else None, cataloged=bool(row and row['cataloged']), risk=risk.as_dict())
    return cache[condition_id]


def is_open(market, now):
    return (market['end_at'] is None or market['end_at'] > now) and (market['closed_at'] is None or market['closed_at'] > now)


def evaluate_pair(store, comparators, wallet, event_key, now, config, cache):
    profile = wallet_profile(store, wallet, event_key, now, config)
    if profile is None:
        return None
    position = position_profile(store, profile, now, config)
    market = market_context(store, profile['largest']['condition_id'], now, cache)
    keys = strata(market['risk']['decision_structure'], position['entry_vwap'], market['end_at'], now, profile['observed_age_s'], position['liquidity'])
    wallet_findings, position_findings, unavailable = {}, {}, []
    if position['max_market_spend'] >= config['minimum_spend']:
        wallet_findings, gaps_w = wallet_anomalies(profile, position, comparators, keys, config)
        position_findings, gaps_p = position_anomalies(profile, position, comparators, keys, config)
        unavailable = sorted(set(gaps_w) | set(gaps_p))
    measures = dict(size_ratio=profile['size_ratio'], frequency_ratio=profile['frequency_ratio'], max_market_spend=position['max_market_spend'], market_share_24h=position['market_share_24h'],
                    liquidity_fraction=position['liquidity_fraction'], burst_nominal=position['burst_nominal'])
    largest = profile.pop('largest')
    profile.pop('event_recent')
    return dict(wallet=wallet, event_key=event_key, evaluated_at=now, market=market, keys=keys, measures=measures, profile=profile, position=position, largest=largest,
                wallet_findings=wallet_findings, position_findings=position_findings, unavailable=unavailable)


def run_cycle(store, touched, now, config, emit=True, commit=True, public_known=lambda event_key: False):
    """Evaluates changed pairs, then keeps one case per event. A warm-up (emit=False) can never open a case."""
    comparators = Comparators(store, config['comparator_minimum'], config['comparator_tail'])
    comparators.begin_cycle()
    cache, by_event = {}, defaultdict(list)
    summary = dict(pairs=0, with_findings=0, no_comparator=0, baseline_insufficient=0, exploratory=0, insufficient=0, opened=0, updated=0, reobserved=0)
    evaluated = []
    for wallet, event_key in sorted(touched):
        record = evaluate_pair(store, comparators, wallet, event_key, now, config, cache)
        if record is None:
            continue
        summary['pairs'] += 1
        findings = dict(record['wallet_findings'], **record['position_findings'])
        summary['with_findings'] += bool(findings)
        summary['no_comparator'] += any(u.startswith('COMPARATOR') for u in record['unavailable'])
        summary['baseline_insufficient'] += 'BASELINE_INSUFFICIENT' in record['unavailable']
        store.cx.execute('INSERT INTO pairs VALUES(?,?,?,?,?) ON CONFLICT(wallet,event_key) DO UPDATE SET evaluated_at=excluded.evaluated_at, anomalies=excluded.anomalies, record=excluded.record',
                         (wallet, event_key, now, json.dumps(sorted(findings)) if findings else '{}', json.dumps(record, default=str)))
        evaluated.append(record)
        by_event[event_key].append(record)
    # After the whole batch: wallets converging within one cycle must not dilute each other's tail.
    for record in evaluated:
        if record['measures']['max_market_spend'] >= config['comparator_floor']:
            unit = record['wallet'] + '|' + record['event_key']
            for metric in METRICS:
                comparators.remember(record['keys'], metric, unit, now, record['measures'][metric])
    outputs = []
    if emit:
        for event_key in sorted(by_event):
            output = assess_event(store, event_key, now, config, public_known, summary)
            if output:
                outputs.append(output)
    if commit:
        store.cx.commit()
    return outputs, summary


def assess_event(store, event_key, now, config, public_known, summary):
    start = now - config['recent_window_s']
    pairs = [json.loads(r['record']) for r in store.cx.execute("SELECT record FROM pairs WHERE event_key=? AND anomalies!='{}' AND evaluated_at>=?", (event_key, start))]
    if not pairs:
        return None
    reference = max(pairs, key=lambda p: p['measures']['max_market_spend'])
    market = reference['market']
    collective = collective_signals(store, event_key, now, config)
    known = store.get('funding:' + event_key)
    category = classify(pairs, collective, market['risk'], known, config)
    if category == 'EXPLORATORY':
        summary['exploratory'] += 1
    elif category == 'INSUFFICIENT_EVIDENCE':
        summary['insufficient'] += 1
    material = fingerprint(dict(category=category, wallets=sorted((p['wallet'], sorted(p['wallet_findings']), sorted(p['position_findings'])) for p in pairs), tokens=sorted(collective['convergence']), amounts=len(collective['identical_amounts'])))
    before = store.cx.execute('SELECT * FROM cases WHERE event_key=?', (event_key,)).fetchone()
    if before and before['fingerprint'] == material:
        store.cx.execute('UPDATE cases SET reobservations=reobservations+1, updated_at=? WHERE event_key=?', (now, event_key))
        summary['reobserved'] += 1
        return None
    if CATEGORY_ORDER.get(category, 0) < CATEGORY_ORDER[ANOMALOUS]:
        return None
    version = (before['version'] + 1) if before else 1
    continuous = STRUCTURE_FAMILY.get(market['risk']['decision_structure']) == 'continuous'
    open_now = is_open(market, now) and not public_known(event_key)
    wants_review = needs_review_now(category, market['risk'], continuous, open_now)
    store.cx.execute('''INSERT INTO cases VALUES(?,?,?,?,?,?,0,?) ON CONFLICT(event_key) DO UPDATE SET version=excluded.version, category=excluded.category, fingerprint=excluded.fingerprint,
                        updated_at=excluded.updated_at, priority=MAX(priority, excluded.priority)''', (event_key, version, category, material, now, now, int(wants_review)))
    summary['opened' if not before else 'updated'] += 1
    return dict(event_key=event_key, version=version, new_case=not before, category=category, category_before=before['category'] if before else None, wants_review=wants_review, already_review=bool(before and before['priority']), continuous_market=continuous, market_open=open_now, at=now, title=market['title'],
                end_at=market['end_at'], risk=market['risk'], pairs=pairs, collective=collective, rank=list(review_rank(category, market['risk'], pairs, collective)))


def apply_review_budget(outputs, already_today, config):
    """A daily ceiling keeps the queue human. Beyond it, cases wait unnotified, and they say so."""
    room = max(0, config['review_budget_per_day'] - already_today)
    kept = 0
    for output in sorted(outputs, key=lambda o: o['rank'], reverse=True):
        if output['wants_review'] and not output['already_review']:
            if kept < room:
                kept += 1
            else:
                output.update(wants_review=False, budget_held=True)
    return outputs
