"""Independent verification, in its own process: reads one bundle of raw rows and recomputes everything.

It imports nothing from the detector, the planner or the proposer, and trusts no number it is handed: a
claimed metric is only something to compare with. Same four outcomes as signal_engine.case_checks: PASS only
if every required check passes, so a skipped check cannot become a success. The report has no clock, so two
runs on one bundle must give the same bytes, and the caller checks that they do.

Usage: python -m harness.verify BUNDLE.json
"""
import hashlib
import json
import random
import re
import sys
from collections import defaultdict
from pathlib import Path

PASS, FAIL, INCOMPLETE, NOT_VERIFIABLE = 'PASS', 'FAIL', 'INCOMPLETE', 'NOT_VERIFIABLE'
SUPPORTED, NOT_SUPPORTED, NOT_TESTABLE = 'SUPPORTED', 'NOT_SUPPORTED', 'NOT_TESTABLE'
TX = re.compile(r'^0x[0-9a-f]{64}$', re.I)
ADDRESS = re.compile(r'^0x[0-9a-f]{40}$', re.I)
# What a score may never say about a person, in the languages the reports use.
OVERCLAIM = re.compile(r"\binsiders?\b|\binitiés?\b|\bsame owner\b|\bmême propriétaire\b|\bprove[sd]?\b|\bprouve[nt]?\b|\bguilty\b|\bcoupable\b", re.I)
# The strongest claim each kind of evidence can carry. Common control has no public evidence kind at all.
CEILING = dict(similar_timing='BEHAVIORAL_SIMILARITY', similar_amount='BEHAVIORAL_SIMILARITY', similar_behaviour_across_events='BEHAVIORAL_SIMILARITY', possible_coordination='BEHAVIORAL_SIMILARITY',
               shared_infrastructure='SHARED_INFRASTRUCTURE', shared_funder='COMMON_FUNDING_ROUTE', direct_transfer_between_wallets='COMMON_FUNDING_ROUTE')
STRENGTH = dict(SHARED_INFRASTRUCTURE=0, BEHAVIORAL_SIMILARITY=1, COMMON_FUNDING_ROUTE=2, SWAP_MATCH=3, COMMON_CONTROL=4)


def check(status, detail, **extra):
    return dict(status=status, detail=detail, **extra)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def overall(checks):
    statuses = {c['status'] for c in checks.values()}
    return FAIL if FAIL in statuses else INCOMPLETE if INCOMPLETE in statuses else PASS


def integrity(rows):
    if not rows:
        return check(FAIL, 'No rows: nothing can be verified.')
    bad = []
    for r in rows:
        if not TX.match(r.get('tx') or '') or not ADDRESS.match(r.get('wallet') or ''):
            bad.append(['identifier', r.get('tx')])
        elif r['observed_at'] < r['ts']:
            bad.append(['observed_before_it_happened', r['tx']])
        elif abs(r['nominal'] - r['size'] * r['price']) > max(.01, 1e-4 * abs(r['nominal'])):
            bad.append(['nominal_differs_from_size_times_price', r['tx']])
        elif not 0 < r['price'] <= 1:
            bad.append(['price_outside_0_1', r['tx']])
    if bad:
        return check(FAIL, f'{len(bad)} rows malformed.', problems=bad[:20])
    return check(PASS, f'{len(rows)} rows well formed.')


def no_future(bundle):
    as_of = bundle['as_of']
    rows = bundle['event_rows'] + [r for rows in bundle.get('wallet_history', {}).values() for r in rows]
    late = [r['tx'] for r in rows if r['observed_at'] > as_of or r['ts'] > as_of]
    if late:
        return check(FAIL, f'{len(late)} rows known only after the decision time.', problems=late[:20])
    return check(PASS, f'All {len(rows)} rows were known at the decision time.')


def chain(bundle, wallets):
    """Amounts come from decoded on-chain fills, not from the trade feed that raised the signal."""
    wanted = defaultdict(float)
    for r in bundle['event_rows']:
        if r['wallet'] in wallets and r['is_buy']:
            wanted[r['tx'].lower(), r['wallet'], r['token_id']] += r['nominal']
    receipts, missing, bad = bundle.get('receipts') or {}, [], []
    for (tx, wallet, token), nominal in sorted(wanted.items()):
        receipt = receipts.get(tx)
        if receipt is None:
            missing.append(tx)
            continue
        if receipt.get('status', 1) != 1:
            bad.append(['failed_transaction', tx])
            continue
        # A log's maker owns that order, and its taker may be the counterparty: counting both doubles a taker's amount.
        fills = [f for f in receipt.get('fills', []) if f.get('transaction_hash', '').lower() == tx and str(f.get('token_id')) == str(token) and f.get('maker', '').lower() == wallet and f.get('side') == 'BUY' and not f.get('removed')]
        moved = sum(int(f['nominal_raw']) for f in fills) / 1e6
        if not fills:
            bad.append(['no_matching_fill', tx])
        elif abs(moved - nominal) > max(.01, .01 * nominal):
            bad.append(['amount_differs', tx, moved, nominal])
    if bad:
        return check(FAIL, f'{len(bad)} trades contradicted by their receipts.', problems=bad[:20])
    if missing:
        return check(INCOMPLETE, f'{len(missing)} of {len(wanted)} trades have no receipt yet.', missing=sorted(set(missing))[:20])
    if not wanted:
        return check(FAIL, 'No purchase to check.')
    return check(PASS, f'{len(wanted)} trades match their receipts.')


def relations(claim):
    """Similar behaviour, a probable common route and common control stay three different claims."""
    bad, seen = [], claim.get('relations') or []
    for relation in seen:
        claimed = relation.get('claimed')
        if claimed == 'COMMON_CONTROL':
            bad.append(['common_control_has_no_public_evidence', relation.get('wallets')])
        elif claimed == 'SWAP_MATCH':
            # A swap's deposit and withdrawal link only through the service's own record, verified on both chains.
            if relation.get('tier') != 3 or not relation.get('record_verified'):
                bad.append(['swap_match_without_a_verified_record', relation.get('wallets')])
        else:
            ceiling = CEILING.get(relation.get('kind'))
            if ceiling is None or STRENGTH.get(claimed, 9) > STRENGTH[ceiling]:
                bad.append(['claim_above_its_evidence', relation.get('kind'), claimed])
            elif ceiling == 'COMMON_FUNDING_ROUTE' and (not TX.match(relation.get('transaction_hash') or '') or relation.get('log_index') is None):
                bad.append(['funding_claim_without_transaction_and_log', relation.get('wallets')])
    if bad:
        return check(FAIL, f'{len(bad)} relations claim more than their evidence.', problems=bad[:20])
    return check(PASS, f'{len(seen)} relations within their evidence.' if seen else 'No relation claimed.')


def language(statement):
    found = OVERCLAIM.findall(statement or '')
    if found:
        return check(FAIL, 'The statement says more than a score can.', words=sorted(set(found)))
    return check(PASS, 'Wording stays within the evidence.')


def wallet_stats(rows, totals):
    spend, shares = defaultdict(float), defaultdict(float)
    for r in rows:
        if r['is_buy']:
            spend[r['wallet']] += r['nominal']
            shares[r['wallet']] += r['size']
    return {w: dict(spend=s, vwap=s / shares[w] if shares[w] else 0, share=min(1.0, s / max(s, totals.get(w, s)))) for w, s in spend.items()}


def zone(vwap):
    return 0 if vwap < .1 else 1 if vwap < .3 else 2 if vwap < .7 else 3


def rarity(stats, controls, screened, needed=1):
    """Joint tail against units in the same price zone, times what was screened. A claim about two wallets rests on the second rarest: one extreme wallet does not corroborate itself."""
    found = []
    for wallet, s in sorted(stats.items()):
        peers = [c for c in controls if zone(c['vwap']) == zone(s['vwap'])]
        hits = sum(c['spend'] >= s['spend'] and c['share'] >= s['share'] for c in peers)
        tail = (1 + hits) / (1 + len(peers))
        found.append(dict(tail=tail, expected_false_positives=tail * screened, controls=len(peers), wallet=wallet, hits=hits))
    found.sort(key=lambda f: (f['tail'], f['wallet']))
    if len(found) < needed:
        return dict(tail=1.0, expected_false_positives=float(screened), controls=found[-1]['controls'] if found else 0, wallet=None, hits=None)
    return found[needed - 1]


def control_units(bundle):
    return [dict(c, vwap=c['spend'] / c['shares'] if c['shares'] else 0, share=min(1.0, c['spend'] / max(c['spend'], c['total']))) for c in bundle['controls']]


def wallets_needed(claim):
    return 2 if claim.get('level') == 'CORROBORATED_BEHAVIOR' else 1


def controls_check(stats, units, bundle, limits):
    if bundle.get('controls_truncated'):
        return check(INCOMPLETE, 'The control population was cut at its cap, so it may be biased.')
    screened = max(1, bundle['screened'])
    found = rarity(stats, units, screened, wallets_needed(bundle['claim']))
    if found['controls'] < limits['min_controls']:
        return check(INCOMPLETE, f"{found['controls']} controls in this price zone, {limits['min_controls']} required.", **found)
    if screened / (1 + found['controls']) > limits['max_expected_false_positives']:
        return check(INCOMPLETE, f"With {found['controls']} controls and {screened} screened, even the rarest value could not pass.", **found)
    if found['expected_false_positives'] > limits['max_expected_false_positives']:
        return check(FAIL, f"{found['expected_false_positives']:.3g} false positives expected at this rarity among {screened} screened.", **found)
    return check(PASS, f"{found['hits']} of {found['controls']} controls as extreme; {found['expected_false_positives']:.3g} expected among {screened} screened.", **found)


def placebo_events(stats, units, limits):
    """How many other events hold a unit this extreme: a single surprising wallet is not rare if most events have one."""
    events = defaultdict(list)
    for u in units:
        events[u['event_key']].append(u)
    if len(events) < limits['min_control_events']:
        return check(INCOMPLETE, f"{len(events)} control events, {limits['min_control_events']} required.")
    if not stats:
        return check(FAIL, 'No purchase to compare.')
    top = max(stats.values(), key=lambda s: s['spend'])
    hits = sum(any(u['spend'] >= top['spend'] and u['share'] >= top['share'] for u in group) for group in events.values())
    rate = (1 + hits) / (1 + len(events))
    if rate > limits.get('max_placebo_rate', .1):
        return check(FAIL, f'{hits} of {len(events)} control events hold a unit this extreme.', rate=rate)
    return check(PASS, f'{hits} of {len(events)} control events hold a unit this extreme.', rate=rate)


def alternatives(bundle, limits):
    """Each competing explanation is tested per wallet. The absence of an article is not evidence: without a dated source it stays untestable."""
    flagged = set(bundle['claim']['wallets'])
    rows = [r for r in bundle['event_rows'] if r['wallet'] in flagged]
    milestone = bundle.get('milestone')
    known = milestone if milestone and (milestone.get('public_observed_at') or bundle['as_of']) <= bundle['as_of'] else None
    truncated = set(bundle.get('history_truncated', ()))
    per_wallet = {}
    for wallet in sorted(flagged):
        mine = [r for r in rows if r['wallet'] == wallet]
        entry = min((r['ts'] for r in mine if r['is_buy']), default=bundle['as_of'])
        if not known:
            public = NOT_TESTABLE
        elif known['public_at'] <= entry:
            public = SUPPORTED
        else:  # after entry, only a dated public source excludes news: a resolution date says nothing about when the news came out
            public = NOT_SUPPORTED if known.get('kind') == 'public_information' else NOT_TESTABLE
        spent_by_token, sold_by_token, by_condition = defaultdict(float), defaultdict(float), defaultdict(lambda: defaultdict(float))
        for r in mine:
            if r['is_buy']:
                spent_by_token[r['token_id']] += r['nominal']
                by_condition[r['condition_id']][r['token_id']] += r['nominal']
            else:
                sold_by_token[r['token_id']] += r['nominal']
        both_sides = any(len(t) > 1 and min(t.values()) / max(t.values()) >= .5 for t in by_condition.values())
        sold_back = any(sold_by_token[t] >= .5 * s for t, s in spent_by_token.items())
        basket = len(by_condition) >= 3
        total = sum(spent_by_token.values())
        before = defaultdict(float)
        for r in bundle.get('wallet_history', {}).get(wallet, []):
            if r['is_buy'] and r['ts'] < entry and r['event_key'] != bundle['event_key']:
                before[r['event_key']] += r['nominal']
        habit = total > 0 and sum(v >= .5 * total for v in before.values()) >= limits['habit_events']
        habitual = SUPPORTED if habit else NOT_TESTABLE if wallet in truncated else NOT_SUPPORTED
        reaction = False
        for r in sorted((m for m in mine if m['is_buy']), key=lambda m: m['ts'])[:1]:
            earlier = [o for o in bundle['event_rows'] if o['token_id'] == r['token_id'] and o['is_buy'] and r['ts'] - 3600 <= o['ts'] < r['ts'] and o['wallet'] not in flagged]
            if len({o['wallet'] for o in earlier}) >= limits['reaction_wallets']:
                reaction = r['price'] - min(o['price'] for o in earlier) >= limits['drift_public_reaction']
        per_wallet[wallet] = dict(public_before_entry=public, two_sided_or_sold_back=SUPPORTED if both_sides or sold_back else NOT_SUPPORTED, basket_or_hedge=SUPPORTED if basket else NOT_SUPPORTED,
                                  habitual_size=habitual, reaction_to_visible_move=SUPPORTED if reaction else NOT_SUPPORTED)
    surviving = sorted(w for w, a in per_wallet.items() if SUPPORTED not in a.values())
    needed = wallets_needed(bundle['claim'])
    limits_named = sorted({k for a in per_wallet.values() for k, v in a.items() if v == NOT_TESTABLE})
    if len(surviving) < needed:
        reasons = sorted({k for a in per_wallet.values() for k, v in a.items() if v == SUPPORTED})
        return check(FAIL, f'{len(surviving)} of {len(per_wallet)} wallets left once alternatives are applied, {needed} required: {", ".join(reasons)}.', per_wallet=per_wallet, surviving=surviving, reasons=reasons)
    return check(PASS, f'{len(surviving)} of {len(per_wallet)} wallets not explained by the tested alternatives.', per_wallet=per_wallet, surviving=surviving, not_testable=limits_named)


def robustness(bundle, wallets, units, totals, screened, limits, seed):
    """Does the finding survive losing rows, a smaller measure, its largest fill, or any one wallet?"""
    rows = [r for r in bundle['event_rows'] if r['wallet'] in wallets]
    needed = wallets_needed(bundle['claim'])
    variants = {}
    for k in range(5):
        rng = random.Random(f'{seed}:{k}')
        variants[f'drop_10pct_{k}'] = wallet_stats([r for r in rows if rng.random() >= .1], totals)
    variants['measure_times_0_8'] = {w: dict(s, spend=s['spend'] * .8) for w, s in wallet_stats(rows, totals).items()}
    largest = {w: max((r for r in rows if r['wallet'] == w and r['is_buy']), key=lambda r: (r['nominal'], r['tx']), default=None) for w in wallets}
    variants['without_largest_fill'] = wallet_stats([r for r in rows if r is not largest.get(r['wallet'])], totals)
    if needed > 1:
        for wallet in sorted(wallets):
            variants[f'without_{wallet}'] = wallet_stats([r for r in rows if r['wallet'] != wallet], totals)
    kept = {name: rarity(stats, units, screened, needed - 1 if name.startswith('without_0x') else needed)['expected_false_positives'] <= limits['max_expected_false_positives'] for name, stats in variants.items()}
    share = sum(kept.values()) / len(kept)
    status = PASS if share >= limits['robustness_keep'] else FAIL
    return check(status, f'{sum(kept.values())} of {len(kept)} variants keep the finding.', variants=kept)


def coverage(bundle, wallets):
    """A collection gap around the entry hides what the alternatives look at, so their silence means nothing there."""
    times = [r['ts'] for r in bundle['event_rows'] if r['wallet'] in wallets and r['is_buy']]
    if not times:
        return check(FAIL, 'No purchase to check.')
    start, end = min(times) - 3600, max(times)
    near = [g for g in bundle.get('gaps', []) if g['end'] >= start and g['start'] <= end]
    if near:
        return check(INCOMPLETE, f'{len(near)} collection gaps overlap the entry window.', gaps=near[:5])
    return check(PASS, f"No collection gap around the entry; {len(bundle.get('gaps', []))} elsewhere in the case's period.")


def verify_case(bundle, seed):
    limits, claim = bundle['config'], bundle['claim']
    flagged = set(claim['wallets'])
    totals = bundle.get('wallet_totals', {})
    checks = dict(integrity=integrity(bundle['event_rows']), no_future=no_future(bundle), language=language(bundle.get('statement')), relations=relations(claim))
    if checks['integrity']['status'] == FAIL or checks['no_future']['status'] == FAIL:
        return checks  # numbers from bad rows would mislead
    stats = wallet_stats([r for r in bundle['event_rows'] if r['wallet'] in flagged], totals)
    # The engine reports its largest single market, which the raw rows of the event must be able to account for.
    wrong = [w for w, spend in claim.get('metrics', {}).items() if spend > stats.get(w, {}).get('spend', 0) * (1 + limits['claim_tolerance'])]
    checks['claim_matches'] = check(FAIL, f'{len(wrong)} claimed metrics exceed what the rows show.', wallets=sorted(wrong)) if wrong else check(PASS, f'{len(claim.get("metrics", {}))} claimed metrics within the rows.')
    overall_of_dossier = bundle.get('dossier_overall')
    checks['dossier'] = check(FAIL, "The engine's own file checks found a contradiction.") if overall_of_dossier == FAIL else check(PASS, f'Dossier checks: {overall_of_dossier}.') if overall_of_dossier else check(INCOMPLETE, 'No dossier result.')
    checks['coverage'] = coverage(bundle, flagged)
    checks['alternatives'] = alternatives(bundle, limits)
    surviving = set(checks['alternatives']['surviving'])
    kept = {w: s for w, s in stats.items() if w in surviving}
    units = control_units(bundle)
    checks['controls'] = controls_check(kept, units, bundle, limits)
    checks['placebo_events'] = placebo_events(kept, units, limits)
    checks['chain'] = chain(bundle, surviving or flagged)
    # Without enough controls nothing can be measured, so nothing can be called fragile either.
    checks['robustness'] = check(INCOMPLETE, 'Waits for enough controls.') if checks['controls']['status'] == INCOMPLETE else robustness(bundle, surviving or flagged, units, totals, max(1, bundle['screened']), limits, seed)
    return checks


def event_effects(rows):
    grouped = defaultdict(lambda: ([], []))
    for r in rows:
        grouped[r['event_key']][0 if r['x'] else 1].append(r['y'])
    return [sum(a) / len(a) - sum(b) / len(b) for a, b in (grouped[k] for k in sorted(grouped)) if a and b]


def sign_flip_p(effects, permutations, rng):
    """One-sided, with events as the unit: wallets within an event share one outcome and are not independent."""
    observed = sum(effects)
    hits = 0
    for _ in range(permutations):
        if sum(e if rng.random() < .5 else -e for e in effects) >= observed:
            hits += 1
    return (1 + hits) / (1 + permutations)


def verify_population(bundle, seed):
    """A feature that predicts returns: tested out of sample, on wallets and dates its proposer did not see, at the cost of every test ever run."""
    from signal_engine.experimental.splits import assert_no_leak, temporal_group_split
    limits = bundle['config']
    rng = random.Random(seed)
    direction = bundle.get('direction', 1)
    rows = [dict(r, y=r['y'] * direction) for r in bundle['rows']]
    tests = max(1, bundle['n_tests'])
    threshold = limits['population_alpha'] / tests
    permutations = min(20000, max(limits['population_permutations'], int(20 / threshold)))
    split = temporal_group_split(rows, bundle['split_ts'], bundle['embargo_s'], salt=bundle.get('salt', 'harness'))
    checks = dict(language=language(bundle.get('statement')))
    try:
        assert_no_leak(split, bundle['split_ts'], bundle['embargo_s'])
        checks['split'] = check(PASS, f"{len(split['dev'])} development rows, {len(split['test'])} test rows, separate wallets and dates.")
    except AssertionError as exc:
        return dict(checks, split=check(FAIL, str(exc)))
    if bundle.get('rows_truncated'):
        return dict(checks, sample=check(INCOMPLETE, 'The sample was cut at its cap and sorted by wallet, so it is not representative.'))
    dev, test = event_effects(split['dev']), event_effects(split['test'])
    if len(test) < limits['population_min_events']:
        return dict(checks, out_of_sample=check(INCOMPLETE, f"{len(test)} test events with both groups, {limits['population_min_events']} required."))
    p = sign_flip_p(test, permutations, rng)
    power_rows = [dict(r, y=r['y'] + limits['population_positive_effect']) if r['x'] else r for r in split['test']]
    power = sign_flip_p(event_effects(power_rows), permutations, rng)
    checks['positive_control'] = check(PASS, f"An injected effect of {limits['population_positive_effect']} would reach p={power:.4f}.") if power <= threshold else check(INCOMPLETE, f'Too little data: even an injected effect reaches only p={power:.4f}, threshold {threshold:.5f}.')
    false_hits = 0
    for k in range(20):
        shuffled = []
        by_event = defaultdict(list)
        for r in split['test']:
            by_event[r['event_key']].append(r)
        for key in sorted(by_event):
            xs = [r['x'] for r in by_event[key]]
            rng.shuffle(xs)
            shuffled += [dict(r, x=x) for r, x in zip(by_event[key], xs)]
        false_hits += sign_flip_p(event_effects(shuffled), 199, rng) <= .05
    checks['negative_control'] = check(PASS if false_hits <= 4 else FAIL, f'{false_hits} of 20 shuffles reach p<=0.05.')
    mean = sum(test) / len(test)
    checks['out_of_sample'] = check(PASS if p <= threshold and mean > 0 else FAIL, f'{len(test)} events, mean effect {mean:.4f}, p={p:.4f}, threshold {threshold:.5f} after {tests} tests ever run.', p=p, effect=mean, events=len(test), tests=tests)
    checks['development_agrees'] = check(PASS if dev and sum(dev) > 0 else FAIL, f'Development effect over {len(dev)} events: {sum(dev) / len(dev) if dev else 0:.4f}.')
    return checks


def run(bundle):
    raw = canonical(bundle).encode()
    input_sha = hashlib.sha256(raw).hexdigest()
    checks = (verify_case if bundle['kind'] == 'case' else verify_population)(bundle, input_sha)
    return dict(kind=bundle['kind'], overall=overall(checks), checks=checks, input_sha=input_sha, code_sha=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())


if __name__ == '__main__':
    print(canonical(run(json.loads(Path(sys.argv[1]).read_text()))))
