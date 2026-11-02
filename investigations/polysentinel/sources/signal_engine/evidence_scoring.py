"""Separate axes of evidence and a category for review. Nothing here is a probability of anything.

Axes stay apart instead of being added into one number:
- market risk is a prior about structure and can never count as evidence about a trader;
- wallet and position findings usually describe the same purchases, so together they are one block;
- another wallet's anomaly and confirmed money movements are the only corroboration.
"""

EXPLORATORY = 'EXPLORATORY'
ANOMALOUS = 'ANOMALOUS'
CORROBORATED_BEHAVIOR = 'CORROBORATED_BEHAVIOR'
INSUFFICIENT_EVIDENCE = 'INSUFFICIENT_EVIDENCE'
CATEGORY_ORDER = {INSUFFICIENT_EVIDENCE: 0, EXPLORATORY: 1, ANOMALOUS: 2, CORROBORATED_BEHAVIOR: 3}
RISK_ORDER = {'LOW': 0, 'UNKNOWN': 1, 'MEDIUM': 2, 'HIGH': 3}


def smallest_tail(findings):
    tails = [f['comparator']['tail'] for f in findings.values() if f.get('comparator', {}).get('tail') is not None]
    return min(tails) if tails else None


def wallet_strength(pair):
    """Two findings on one wallet, or one beyond the extreme threshold, make a strong purchase block."""
    return len(pair['wallet_findings']) + len(pair['position_findings'])


def axes(pairs, collective, risk, funding_links, timeline, gaps, confirmed_trades, config):
    all_findings = [dict(p['wallet_findings'], **p['position_findings']) for p in pairs]
    tails = [t for t in (smallest_tail(f) for f in all_findings) if t is not None]
    unavailable = sorted({u for p in pairs for u in p['unavailable']})
    sources = {'market_rules': bool(risk.get('evidence')), 'comparators': bool(tails), 'funding_checked': funding_links is not None, 'public_timeline': timeline['first_credible_public_information']['status'] == 'documented',
               'trades_confirmed_on_chain': bool(confirmed_trades)}
    return dict(
        market_information_risk=dict(level=risk['level'], structure=risk['decision_structure'], confidence=risk['confidence'], role='Prior about structure; never evidence about a trader.'),
        wallet_anomaly=dict(wallets=sum(bool(p['wallet_findings']) for p in pairs), findings=sorted({k for p in pairs for k in p['wallet_findings']}), smallest_tail=min(tails) if tails else None),
        position_anomaly=dict(wallets=sum(bool(p['position_findings']) for p in pairs), findings=sorted({k for p in pairs for k in p['position_findings']})),
        synchrony=dict(converging_tokens=len(collective['convergence']), identical_amount_clusters=len(collective['identical_amounts']), repeated_pairs=len(collective['repeated_across_events'])),
        funding=dict(checked=funding_links is not None, corroborating_links=len([l for l in (funding_links or []) if l['kind'] in ('direct_transfer_between_wallets', 'shared_funder')]), status=None if funding_links is not None else 'NOT_CHECKED'),
        chronology_quality=dict(first_public_information=timeline['first_credible_public_information']['status'], observation_gaps=len(gaps), grade='documented' if sources['public_timeline'] else 'public date unknown'),
        evidence_completeness=dict(present=sorted(k for k, v in sources.items() if v), missing=sorted(k for k, v in sources.items() if not v), unavailable=unavailable))


def corroborated(pairs, collective, funding_links):
    strong = [p for p in pairs if wallet_strength(p) >= 2]
    other_wallet = len(strong) >= 2 or bool(collective['convergence'])
    money = any(l['kind'] in ('direct_transfer_between_wallets', 'shared_funder') for l in (funding_links or []))
    return bool(pairs) and (other_wallet or (money and bool(strong)))


def classify(pairs, collective, risk, funding_links, config):
    """A category describes evidence, never a person. Conclusions stay limited to what it names."""
    if not pairs:
        return None
    measured = [p for p in pairs if p['wallet_findings'] or p['position_findings']]
    # Several wallets on one outcome, each large for its context and new or concentrated.
    if collective['convergence']:
        return CORROBORATED_BEHAVIOR
    if not measured:
        return INSUFFICIENT_EVIDENCE if all(not p.get('candidate') for p in pairs) else EXPLORATORY
    if corroborated(measured, collective, funding_links):
        return CORROBORATED_BEHAVIOR
    tails = [t for t in (smallest_tail(dict(p['wallet_findings'], **p['position_findings'])) for p in measured) if t is not None]
    strong = any(wallet_strength(p) >= 2 for p in measured)
    extreme = bool(tails) and min(tails) <= config['extreme_tail']
    if strong or extreme:
        return ANOMALOUS
    return EXPLORATORY


def review_rank(category, risk, pairs, collective):
    """Sort key for a human queue: market structure first, then evidence. It orders reading, nothing else."""
    tails = [t for t in (smallest_tail(dict(p['wallet_findings'], **p['position_findings'])) for p in pairs) if t is not None]
    return (RISK_ORDER.get(risk['level'], 1), CATEGORY_ORDER.get(category, 0), len(collective['convergence']), sum(wallet_strength(p) >= 2 for p in pairs), -(min(tails) if tails else 1.0))


def needs_review_now(category, risk, nature_continuous, market_open):
    """What may notify. Everything else stays visible in the queue, excluded from nothing.

    Large bettors align on heavily traded matches or votes every day, so low-risk structures never
    notify by themselves. An unresolved structure is not low: only its corroborated cases notify.
    """
    if nature_continuous or not market_open or risk['level'] == 'LOW':
        return False
    return category == CORROBORATED_BEHAVIOR or (category == ANOMALOUS and risk['level'] == 'HIGH')
