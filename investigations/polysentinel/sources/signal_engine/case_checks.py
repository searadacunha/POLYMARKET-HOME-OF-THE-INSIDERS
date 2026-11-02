"""Deterministic checks of an investigation file against the rows it was built from.

Four outcomes, never merged: PASS, FAIL, INCOMPLETE (could be checked, not yet done), NOT_VERIFIABLE (no
public data can settle it). The overall result is PASS only if every check passes, so a failed or
skipped check cannot become a success.
"""
import hashlib
import re

PASS, FAIL, INCOMPLETE, NOT_VERIFIABLE = 'PASS', 'FAIL', 'INCOMPLETE', 'NOT_VERIFIABLE'
TX = re.compile(r'^0x[0-9a-f]{64}$', re.I)
ADDRESS = re.compile(r'^0x[0-9a-f]{40}$', re.I)
CONDITION = re.compile(r'^0x[0-9a-f]{64}$', re.I)
RELATIVE_TOLERANCE = 1e-6


def _check(status, detail, problems=()):
    return dict(status=status, detail=detail, problems=list(problems)[:20])


def transactions_exist(case, rows):
    known = {r['tx'].lower() for r in rows}
    named = [t['tx'] for t in case['chronology']]
    bad = [t for t in named if not TX.match(t or '') or t.lower() not in known]
    if bad:
        return _check(FAIL, 'Transactions absent from the source rows or malformed.', bad)
    confirmed = {r.get('tx', '').lower() for r in case['funding_and_transactions'].get('reconciled_transactions', []) if r.get('status') == 'matched'}
    if not named:
        return _check(FAIL, 'A file with no transaction checks nothing.')
    if confirmed & {t.lower() for t in named}:
        return _check(PASS, f'{len(confirmed & {t.lower() for t in named})} of {len(set(named))} transactions matched on a final receipt; the others are in the source rows.')
    return _check(INCOMPLETE, f'{len(set(named))} transactions in the source rows; none matched on a receipt yet.')


def amounts_match(case, rows):
    by_key = {(r['tx'].lower(), r['wallet'].lower(), r['token_id']): 0.0 for r in rows}
    for r in rows:
        by_key[r['tx'].lower(), r['wallet'].lower(), r['token_id']] += r['nominal']
    seen = {}
    for t in case['chronology']:
        key = (t['tx'].lower(), t['wallet'].lower(), t['token_id'])
        seen[key] = seen.get(key, 0.0) + t['nominal']
    bad = [k[0] for k, v in seen.items() if abs(v - by_key.get(k, float('inf'))) > max(1e-6, RELATIVE_TOLERANCE * abs(v))]
    wrong_product = [t['tx'] for t in case['chronology'] if abs(t['nominal'] - t['shares'] * t['price']) > max(.01, 1e-4 * t['nominal'])]
    if bad or wrong_product:
        return _check(FAIL, 'Amounts differ from the source rows, or nominal differs from shares times price.', bad + wrong_product)
    return _check(PASS, f'{len(seen)} amounts equal their source rows.')


def identifiers_valid(case):
    bad = [w['address'] for w in case['wallets'] if not ADDRESS.match(w['address'])] + [m for m in case['event']['markets'] if not CONDITION.match(m)]
    if case['case_id'] != hashlib.sha256(case['event']['key'].encode()).hexdigest()[:16]:
        bad.append('case_id')
    return _check(FAIL if bad else PASS, 'Wallet, market and case identifiers.', bad)


def timestamps_coherent(case):
    bad = [t['tx'] for t in case['chronology'] if t['at'] > t['first_observed'] or t['first_observed'] > case['decided_at']]
    return _check(FAIL if bad else PASS, 'Each trade happened before we saw it, and we saw it before the decision.', bad)


def wallet_links_verifiable(case):
    section = case['funding_and_transactions']
    wallets = {w['address'].lower() for w in case['wallets']}
    bad = []
    for link in section['links']:
        if any(w.lower() not in wallets for w in link.get('wallets', [])) and link.get('kind') in ('similar_timing', 'similar_behaviour_across_events'):
            bad.append(link.get('kind'))
        if link.get('kind') in ('direct_transfer_between_wallets', 'shared_funder', 'shared_infrastructure'):
            proofs = link.get('provenance') or []
            if not proofs or any(not TX.match(p.get('transaction_hash') or '') or p.get('log_index') is None for p in proofs):
                bad.append(link.get('kind'))
        if link.get('common_owner_established') is not False and 'kind' in link:
            bad.append('ownership asserted: ' + str(link.get('kind')))
    if bad:
        return _check(FAIL, 'A link without a transaction and log index, or asserting an owner.', bad)
    if section.get('funding_status') == 'not checked yet':
        return _check(INCOMPLETE, 'Behaviour links only; funding not looked up yet.')
    return _check(PASS, f"{len(section['links'])} links carry their proof.")


def comparators_have_denominators(case, config):
    bad, seen = [], 0
    for signal in case['signals']:
        for family in ('wallet_findings', 'position_findings'):
            for name, finding in (signal.get(family) or {}).items():
                comparator = finding.get('comparator')
                if comparator is None:
                    continue
                seen += 1
                if comparator.get('tail') is None or (comparator.get('n') or 0) < config['comparator_minimum']:
                    bad.append(f"{signal['wallet']}:{name}")
    if bad:
        return _check(FAIL, 'A finding rests on a comparator below its minimum size.', bad)
    return _check(PASS if seen else NOT_VERIFIABLE, f'{seen} comparators at or above {config["comparator_minimum"]} units.')


def public_information_dated(case):
    first = case['public_information']['timeline']['first_credible_public_information']
    if first.get('status') in ('unknown', None):
        return _check(NOT_VERIFIABLE, 'No configured source covers this event; absence of an article proves nothing.')
    return _check(PASS if first.get('at') and first.get('source') else FAIL, 'First public information has a date and a source.')


def missing_data_declared(case):
    missing = set(case['missing_data'])
    undeclared = sorted(set(case['evidence_axes']['evidence_completeness']['missing']) - missing)
    return _check(FAIL if undeclared or not missing else PASS, 'What is absent is written in the file.', undeclared)


def fund_flows_carry_proof(case):
    section = case.get('fund_flows') or {}
    if section.get('status') == 'NOT_TRACED':
        return _check(INCOMPLETE, 'Fund flows not traced yet.')
    bad = []
    for wallet in section.get('wallets', []):
        for edge in wallet.get('incoming', []) + wallet.get('outgoing', []) + wallet.get('upstream', []):
            if edge['state'] in ('ONCHAIN_CONFIRMED', 'SERVICE_INTERACTION') and (not TX.match(edge.get('tx') or '') or edge.get('log_index') is None):
                bad.append(str(edge.get('tx')))
        if wallet.get('ownership') != 'OWNERSHIP_NOT_ESTABLISHED':
            bad.append(str(wallet.get('wallet')))
    return _check(FAIL if bad else PASS, 'Each confirmed relation names its transaction and log; no owner is asserted.', bad)


def check_case(case, rows, config):
    checks = dict(transactions_exist=transactions_exist(case, rows), amounts_match=amounts_match(case, rows), identifiers_valid=identifiers_valid(case), timestamps_coherent=timestamps_coherent(case),
                  wallet_links_verifiable=wallet_links_verifiable(case), comparators_have_denominators=comparators_have_denominators(case, config), public_information_dated=public_information_dated(case), missing_data_declared=missing_data_declared(case), fund_flows_carry_proof=fund_flows_carry_proof(case))
    statuses = {c['status'] for c in checks.values()}
    overall = FAIL if FAIL in statuses else INCOMPLETE if INCOMPLETE in statuses else NOT_VERIFIABLE if NOT_VERIFIABLE in statuses else PASS
    return dict(overall=overall, checks=checks)
