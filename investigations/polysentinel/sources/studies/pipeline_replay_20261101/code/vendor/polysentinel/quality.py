"""Descriptive evidence completeness, independent of exploratory signal scores."""
from collections import Counter
from decimal import Decimal, InvalidOperation
import json
import time

from .news import public_timing
from .review import case_scope

_CACHE = {}
MISSING = {
    'receipt': 'Propriétaire et montants de chaque groupe d’opérations non rapprochés de reçus confirmés.',
    'public_time': 'Signal émis avant une information publique vérifiée non établi ; une résolution ou un achat découvert après annonce ne suffit pas.',
    'comparator': 'Comparateur documenté suffisant manquant.',
    'inventory_at_signal': 'Exposition historique au signal non documentée ; les positions actuelles ne suffisent pas.',
}


def case_quality(store, case, now=None, cache=None, scope=None):
    now = time.time() if now is None else now
    cache = {} if cache is None else cache

    def known(kind, key):
        identity = kind, str(key)
        if identity not in cache:
            cache[identity] = store.get(*identity)
        row = cache[identity]
        return row if row and row['observed_at'] <= now else None

    alerts = case.get('alerts') or []
    receipt_ok = bool(alerts)
    used_logs = set()
    timings = []
    receipt_groups = []
    milestone = known('public_milestone', case.get('event_id', ''))
    for alert in alerts:
        verified_fills = []
        transactions = alert.get('transactions') or ([alert['transaction_hash']] if alert.get('transaction_hash') else [])
        group_ok = bool(transactions)
        issues = []
        for tx in transactions:
            row = known('receipt', tx.lower())
            receipt = row['payload'] if row else {}
            # A receipt is shared by all wallets: its last row reconciliation is not this group's proof.
            owned = [f for f in receipt.get('fills', [])
                     if f.get('maker') == str(case.get('wallet','')).lower()
                     and str(f.get('token_id')) == str(alert.get('token_id'))
                     and f.get('side') == alert.get('side') and not f.get('removed')]
            identities = {(tx.lower(), f.get('contract'), f['log_index']) for f in owned}
            if used_logs & identities or len(identities) != len(owned):
                group_ok = False
                issues.append('duplicate_fill_identity')
            used_logs.update(identities)
            final = receipt.get('status') == 'confirmed'
            group_ok = group_ok and final and bool(owned)
            if not final: issues.append('receipt_'+receipt.get('status','not_collected'))
            elif not owned: issues.append('wallet_token_side_unmatched')
            verified_fills.extend(owned)
        try:
            shares = sum(Decimal(f['shares_raw']) for f in verified_fills)/Decimal(1000000)
            nominal = sum(Decimal(f['nominal_raw']) for f in verified_fills)/Decimal(1000000)
            tolerance = max(Decimal('0.00001'), abs(Decimal(str(alert['nominal'])))*Decimal('0.000001'))
            amounts_ok = abs(shares-Decimal(str(alert['size']))) <= Decimal('0.00001') and abs(nominal-Decimal(str(alert['nominal']))) <= tolerance
            if group_ok and not amounts_ok: issues.append('group_amount_mismatch')
            group_ok = group_ok and amounts_ok
        except (KeyError, TypeError, InvalidOperation):
            group_ok = False
            issues.append('group_amounts_invalid')
        receipt_ok = receipt_ok and group_ok
        receipt_groups.append(dict(transactions=transactions, matched=bool(group_ok), issues=sorted(set(issues)),
                                   verified_fill_count=len(verified_fills),
                                   amount_policy='Same API rounding tolerance as chain.reconcile; full group, confirmed owned fills only.'))
        at = alert.get('timestamp')
        public = milestone
        if not public:
            market = known('market', alert.get('market_id', ''))
            condition = alert.get('condition_id') or ((market['payload'].get('condition_id')) if market else None)
            public = known('public_condition', condition) if condition else None
        timings.append(public_timing(public, at, now) if isinstance(at, (int, float)) else {'status': 'unknown'})
    calculated = case.get('calculated_at')
    public_ok = bool(timings) and isinstance(calculated, (int, float)) and all(
        t['status'] == 'before_verified_public_information' and calculated < t['first_public_at'] for t in timings)
    comparator = case.get('comparator') or {}
    exposure = case.get('historical_exposure') or {}
    # Explicit sourced assessments only; API positions and observed deltas are not opening inventory.
    comparator_ok = isinstance(comparator, dict) and comparator.get('sufficient') is True and bool(comparator.get('evidence_ids'))
    inventory_ok = isinstance(exposure, dict) and exposure.get('verified') is True and exposure.get('at_signal') is True and bool(exposure.get('evidence_ids'))
    requirements = dict(receipt=bool(receipt_ok), public_time=public_ok,
                        comparator=bool(comparator_ok), inventory_at_signal=bool(inventory_ok))
    missing = [key for key, ready in requirements.items() if not ready]
    scope = case_scope(store, case, now=now, cache=cache) if scope is None else scope
    eligible = bool(scope['eligible_for_automatic_investigation'] and case.get('current', True) and case.get('preliminary'))
    return dict(assessed_at=now, score_calculated_at=case.get('calculated_at'), requirements=requirements,
                missing=missing, missing_explanations={key: MISSING[key] for key in missing},
                blockers=dict(receipt=receipt_groups, public_time=timings,
                    comparator='sourced_assessment_present' if comparator else 'not_implemented_in_automatic_investigation',
                    inventory_at_signal='sourced_assessment_present' if exposure else 'historical_inventory_not_reconstructed'),
                receipt_groups=receipt_groups, public_timing=timings, documentary_complete=not missing, scope_eligible=eligible, exploitable=not missing,
                definition='Complétude documentaire pour examiner un signal émis avant une information publique vérifiée : preuve transactionnelle, comparateur documenté suffisant et exposition historique. L’éligibilité à une enquête automatique courante reste distincte ; aucune infraction établie.',
                historical_score_unchanged=True)


def measure_quality(store, now=None):
    """Decode cases only, never the global trade payloads; cache at most 15 seconds."""
    now = time.time() if now is None else now
    started = time.perf_counter()
    revision = store.conn.execute('SELECT MAX(rowid) FROM history_refs').fetchone()[0]
    key = str(store.root.resolve())
    cached = _CACHE.get(key)
    if cached and cached['revision'] == revision and 0 <= now-cached['generated_at'] < 15:
        return cached
    total = current_count = 0
    priorities = []
    for row in store.conn.execute("SELECT payload FROM objects WHERE kind='case'"):
        case = json.loads(row[0])
        total += 1
        if case.get('current', True):
            current_count += 1
            if case.get('priority'): priorities.append(case)
    candidates = sorted(priorities, key=lambda c: (c.get('score') or 0, c.get('calculated_at') or 0), reverse=True)[:250]
    cache = {}; missing = Counter(); reasons = Counter(); focused = []; timing = Counter(); exploitable = 0
    for case in candidates:
        scope = case_scope(store, case, now=now, cache=cache)
        quality = case_quality(store, case, now=now, cache=cache, scope=scope)
        missing.update(quality['missing'])
        timing.update(t['status'] for t in quality['public_timing'])
        exploitable += int(quality['exploitable'])
        if not scope['eligible_for_automatic_investigation']:
            reasons[scope['reason']] += 1
        else:
            focused.append(dict(id=case['id'], wallet=case.get('wallet'), event_id=case.get('event_id'),
                                event_title=case.get('event_title'), score=case.get('score'), status=case.get('status'),
                                quality=quality, review_context=scope))
    rejected = Counter()
    for row in store.conn.execute("SELECT payload FROM objects WHERE kind='rejected_trade'"):
        payload = json.loads(row[0]); rejected[str(payload.get('reason') or 'Motif non renseigné')] += 1
    analysis = store.get('health', 'analysis')
    diagnostics = (analysis['payload'].get('diagnostics') or {}) if analysis else {}
    result = dict(generated_at=now, revision=revision,
                  counts=dict(all_cases=total, current_cases=current_count, current_priority=len(priorities),
                              current_nonpriority=current_count-len(priorities), historical_cases=total-current_count,
                              assessed_priority=len(candidates), unassessed_priority=len(priorities)-len(candidates),
                              focused_announcements=len(focused), exploitable=exploitable, documentary_complete=exploitable,
                              rejected_rows=sum(rejected.values())),
                  latest_analysis=dict(observed_at=analysis['observed_at'] if analysis else None, diagnostics=diagnostics),
                  missing_counts=dict(missing), missing_explanations=MISSING, public_timing_counts=dict(timing),
                  scope_exclusion_reasons=dict(reasons), rejected_reasons=dict(rejected), focused_cases=focused[:5],
                  denominators=dict(case_counts='Toutes les dernières identités de dossiers conservées ; current absent vaut vrai.',
                      quality='Au plus 250 dossiers courants prioritaires, triés par score puis calcul ; les autres restent non évalués.',
                      missing='Dossiers prioritaires évalués ; catégories non exclusives.',
                      public_timing='Opérations des dossiers prioritaires évalués, pas dossiers ou wallets indépendants.',
                      rejected='Lignes rejetées conservées, pas totalité des requêtes ni des trades publics.'),
                  limitations=['Comptages descriptifs ; aucune précision/rappel sans vérité terrain.',
                               'Exploitable signifie preuves suffisantes pour examen, pas infraction ni validation statistique.',
                               'Les preuves ajoutées maintenant ne modifient pas le score historique.'],
                  cache_max_age_seconds=15, calculation_seconds=time.perf_counter()-started)
    _CACHE[key] = result
    return result


def targeted_context(root, case):
    """Attach only this case's wallet evidence, preserving its observation dates."""
    path = root/'evidence/targeted_20261027/inquiries/display.json'
    if not path.is_file() or path.is_symlink():
        return None
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError):
        return {'status': 'unavailable', 'reason': 'Export ciblé illisible ; aucune preuve substituée.'}
    wallet = case.get('wallet')
    receipts = [r for r in data.get('receipts', []) if r.get('case_id') == case.get('id') and r.get('wallet') == wallet]
    if not receipts:
        return None
    return dict(receipts=receipts, balances=[b for b in data.get('balances', []) if b.get('wallet') == wallet],
                balance_observed_utc_start=data.get('balance_observed_utc_start'),
                balance_observed_utc_end=data.get('balance_observed_utc_end'), balance_block_tag=data.get('balance_block_tag'),
                balance_block_number=data.get('balance_block_number'), balance_scope=data.get('balance_scope'),
                historical_net_inventory_reconstructed=False, historical_score_unchanged=True)
