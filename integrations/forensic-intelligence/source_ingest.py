"""Import published ChangeNOW forensic CSV without re-labeling providers as proven.

This reads existing investigation outputs. It never contacts a chain or silently
infers payin-payout linkage, service ownership or realized profits. Any import
must be described as documentary until the node receipts have been replayed.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

from ledger import canonical_edges, decimal_value, normalized_units

EV_TYPES = {'native_transaction': 'native_transfer', 'erc20_transfer_log': 'erc20_transfer'}
HEX64 = re.compile(r'[0-9a-fA-F]{64}\Z')


def read_changenow_transfers(path, relative_source=None):
    path = Path(path)
    source = relative_source or str(path)
    output, warnings = [], []
    with path.open(encoding='utf-8', newline='') as fh:
        for line_no, row in enumerate(csv.DictReader(fh), 2):
            if row['event'] not in EV_TYPES:
                warnings.append({'row': line_no, 'kind': 'UNKNOWN_EVENT', 'value': row['event']})
                continue
            if row['node_ok'].strip().lower() != 'true':
                warnings.append({'row': line_no, 'kind': 'UNVERIFIED_NODE_RECORD'})
                continue
            if not HEX64.fullmatch(row.get('node_proof_sha256', '')):
                raise ValueError(f'Row {line_no}: invalid node receipt digest')
            log = int(row['log_index']) if row['log_index'] else None
            if row['event'] == 'erc20_transfer_log' and log is None:
                warnings.append({'row': line_no, 'kind': 'EVENT_LOG_INDEX_MISSING',
                                 'tx': row['tx'], 'completeness': 'NOT_CERTIFIABLE'})
            raw, decimals = int(row['raw']), int(row['decimals'])
            amount = normalized_units(raw, decimals)
            if amount != decimal_value(row['amount']):
                raise ValueError(f'Row {line_no}: raw/normalized money mismatch')
            # Source attribution and money movement are separate axes. A label
            # is never used as an edge's proof level or an established protocol.
            output.append({
                'chain_id': int(row['chain_id']), 'transaction_hash': row['tx'],
                'block_number': int(row['block']),
                'timestamp_utc': row['utc'].replace(' ', 'T') + 'Z',
                'log_index': log, 'from': row['src'], 'to': row['dst'],
                'token_contract': row['contract'] or None,
                'token_decimals': decimals, 'raw_amount': str(raw),
                'normalized_amount': str(amount),
                'usd_value_when_supported': None, 'protocol': None,
                'source': f'{source}:row={line_no};node_sha256={row["node_proof_sha256"]}',
                'relation_type': EV_TYPES[row['event']], 'evidence_level': 'ONCHAIN_CONFIRMED',
            })
    # Reject contradictory duplicate logs even if each individual node_ok says true.
    edges = canonical_edges(output)
    return {'edges': edges, 'warnings': warnings,
            'scope': 'DOCUMENTARY_NODE_OK_CLAIMS_NOT_REVALIDATED',
            'source_rows_accepted': len(output)}
