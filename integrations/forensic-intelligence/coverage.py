"""Read-only coverage checks for EVM event scans; no network, RPC, or API keys.

A complete *reported interval* is not independent proof that the provider returned
all events. The result explicitly distinguishes provider claims from verified logs.
All block intervals are half-open [from_block, to_block_exclusive).
"""
from __future__ import annotations

import re
from collections import defaultdict
from ledger import utc_seconds

EVM_ADDR = re.compile(r'0x[0-9a-fA-F]{40}\Z')
TOPIC0 = re.compile(r'0x[0-9a-fA-F]{64}\Z')
TXHASH = TOPIC0


def _integer(value, label, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError(f'{label} must be an integer >= {minimum}')
    return value


def _identity(row):
    chain = _integer(row['chain_id'], 'chain_id', 1)
    address = row['contract_address']
    topic = row['topic0']
    variant = row['protocol_variant']
    if not isinstance(address, str) or not EVM_ADDR.fullmatch(address):
        raise ValueError('Invalid contract_address')
    if not isinstance(topic, str) or not TOPIC0.fullmatch(topic):
        raise ValueError('Invalid topic0')
    if not isinstance(variant, str) or not variant.strip():
        raise ValueError('Explicit protocol_variant required; V1/V2 must never merge')
    return chain, address.lower(), topic.lower(), variant


def _range(row):
    start = _integer(row['from_block'], 'from_block')
    end = _integer(row['to_block_exclusive'], 'to_block_exclusive')
    if start >= end:
        raise ValueError('Invalid empty/backwards half-open block interval')
    return start, end


def coverage_report(scope, scans, as_of_utc):
    """Report gaps by contract, topic and protocol variant without pretending chain certainty.

    A scan contributes only when the provider reported a completed, nontruncated
    window with exhausted pagination before as_of_utc. Provider reliability and
    finality are outside this function's ability to verify.
    """
    wanted = _identity(scope)
    low, high = _range(scope)
    cutoff = utc_seconds(as_of_utc)
    intervals, rejected = [], []
    provider_names = set()
    for n, row in enumerate(scans):
        key = _identity(row)
        if key != wanted:
            rejected.append({'index': n, 'reason': 'OTHER_CHAIN_CONTRACT_TOPIC_OR_PROTOCOL'})
            continue
        start, end = _range(row)
        for field in ('completed', 'cursor_exhausted', 'truncated'):
            if type(row.get(field)) is not bool:
                raise ValueError(f'Scan {n}: {field} must be a bool')
        observed = utc_seconds(row['observed_at_utc'])
        if observed > cutoff:
            rejected.append({'index': n, 'reason': 'OBSERVED_AFTER_CUTOFF'})
        elif not row['completed'] or not row['cursor_exhausted'] or row['truncated']:
            rejected.append({'index': n, 'reason': 'INCOMPLETE_OR_TRUNCATED'})
        elif end <= low or start >= high:
            rejected.append({'index': n, 'reason': 'OUTSIDE_REQUESTED_RANGE'})
        else:
            intervals.append((max(start, low), min(end, high)))
            provider_names.add(str(row.get('provider', 'UNKNOWN')))
    merged = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    gaps, position = [], low
    for start, end in merged:
        if position < start:
            gaps.append([position, start])
        position = max(position, end)
    if position < high:
        gaps.append([position, high])
    observed_blocks = sum(end - start for start, end in merged)
    return {
        'chain_id': wanted[0], 'contract_address': wanted[1],
        'topic0': wanted[2], 'protocol_variant': wanted[3],
        'from_block': low, 'to_block_exclusive': high,
        'reported_covered_blocks': observed_blocks,
        'requested_blocks': high-low,
        'reported_fraction': f'{observed_blocks/(high-low):.9f}',
        'merged_covered_intervals': [list(p) for p in merged],
        'missing_ranges': gaps, 'rejected_scans': rejected,
        'providers': sorted(provider_names),
        'status': 'REPORTED_RANGE_COVERED' if not gaps else 'REPORTED_RANGE_INCOMPLETE',
        'independent_event_completeness': 'NOT_VERIFIED',
        'note': 'Provider completion is not proof of complete RPC logs, finality or historical account coverage',
    }


def deduplicate_logs(logs):
    """One EVM log per (chain_id, transaction_hash, log_index).

    Reject conflicting payloads instead of silently double-counting fills.
    Disallow missing log indices: unindexed historical feeds may be used as
    descriptive trade observations but cannot certify distinct on-chain logs.
    """
    found = {}
    for row in logs:
        chain = _integer(row['chain_id'], 'chain_id', 1)
        tx, ix = row['transaction_hash'], row['log_index']
        if not isinstance(tx, str) or not TXHASH.fullmatch(tx):
            raise ValueError('Invalid EVM transaction hash')
        _integer(ix, 'log_index')
        address = row['contract_address']
        if not isinstance(address, str) or not EVM_ADDR.fullmatch(address):
            raise ValueError('Invalid contract address')
        topic = row['topic0']
        if not isinstance(topic, str) or not TOPIC0.fullmatch(topic):
            raise ValueError('Invalid topic')
        block = _integer(row['block_number'], 'block_number')
        fingerprint = (address.lower(), topic.lower(), block, row['payload_sha256'].lower())
        if not re.fullmatch(r'[0-9a-fA-F]{64}', row['payload_sha256']):
            raise ValueError('Invalid evidence payload SHA256')
        k = chain, tx.lower(), ix
        if k in found and found[k][0] != fingerprint:
            raise ValueError(f'Conflicting on-chain log identity: {k}')
        found.setdefault(k, (fingerprint, dict(row)))
    return [found[k][1] for k in sorted(found)]
