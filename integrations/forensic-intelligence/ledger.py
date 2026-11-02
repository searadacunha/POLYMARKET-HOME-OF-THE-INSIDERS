"""Read-only, stdlib forensic evidence interchange; no RPC, keys, or wallet attribution.

Transactions are observations, never automatic proof of identity or the same economic funds
across a bridge, swap, exchange, or privacy boundary.
"""
from __future__ import annotations

import csv
import json
import re
from decimal import Decimal, InvalidOperation
from itertools import combinations
from pathlib import Path
from xml.etree import ElementTree as ET

FIELDS = (
    'chain_id', 'transaction_hash', 'block_number', 'timestamp_utc', 'log_index',
    'from', 'to', 'token_contract', 'token_decimals', 'raw_amount',
    'normalized_amount', 'usd_value_when_supported', 'protocol', 'source',
    'relation_type', 'evidence_level',
)
ONCHAIN = 'ONCHAIN_CONFIRMED'
PROTOCOL = 'PROTOCOL_LINK_CONFIRMED'
VALID_PROOF = {ONCHAIN, PROTOCOL, 'SERVICE_INTERACTION', 'CANDIDATE', 'OFFCHAIN_REQUIRED', 'INSUFFICIENT_EVIDENCE'}
FINANCIAL = {'native_transfer', 'erc20_transfer', 'erc1155_transfer', 'internal_transfer'}
VALID_TYPES = FINANCIAL | {'mint', 'burn', 'split', 'merge', 'redemption', 'bridge_ledger', 'fee', 'contract_control'}
SERVICE_ROLES = {'SERVICE', 'EXCHANGE', 'BRIDGE', 'OMNIBUS', 'CONTRACT'}
EVM_ADDRESS = re.compile(r'0x[0-9a-fA-F]{40}\Z')


def decimal_value(value):
    if isinstance(value, (float, bool)):
        raise ValueError('Float/bool forbidden for monetary values; use integer strings or Decimal')
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError('Invalid decimal') from exc
    if not result.is_finite():
        raise ValueError('Nonfinite decimal')
    return result


def utc_seconds(value):
    from datetime import datetime, timezone
    try:
        parsed = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        if parsed.tzinfo is None or parsed.utcoffset().total_seconds() != 0:
            raise ValueError('Must be explicit UTC')
        return parsed.timestamp()
    except (TypeError, AttributeError) as exc:
        raise ValueError('Invalid timestamp') from exc


def validate_edge(edge):
    missing = set(FIELDS) - edge.keys()
    if missing:
        raise ValueError(f'Missing evidence fields: {sorted(missing)}')
    for field in ('chain_id', 'block_number', 'token_decimals'):
        if type(edge[field]) is not int or edge[field] < 0:
            raise ValueError(f'Invalid {field}')
    if edge['chain_id'] == 0 or edge['token_decimals'] > 36:
        raise ValueError('Invalid chain or decimals')
    if edge['log_index'] is not None and (type(edge['log_index']) is not int or edge['log_index'] < 0):
        raise ValueError('log_index must be nonnegative or null (native/trace)')
    tx = edge['transaction_hash']
    if not isinstance(tx, str) or not tx.startswith('0x') or len(tx) != 66 or any(c not in '0123456789abcdefABCDEF' for c in tx[2:]):
        raise ValueError('Expected EVM transaction hash: non-EVM adapters must provide separate schema')
    if not all(isinstance(edge[f], str) and EVM_ADDRESS.fullmatch(edge[f]) for f in ('from', 'to')):
        raise ValueError('Invalid EVM from/to address')
    if not isinstance(edge['source'], str) or not edge['source'].strip():
        raise ValueError('Missing evidence source')
    utc_seconds(edge['timestamp_utc'])
    if edge['evidence_level'] not in VALID_PROOF or edge['relation_type'] not in VALID_TYPES:
        raise ValueError('Unknown proof or relation type')
    if edge['token_contract'] is not None and (not isinstance(edge['token_contract'], str) or not EVM_ADDRESS.fullmatch(edge['token_contract'])):
        raise ValueError('Invalid EVM token contract')
    if edge['relation_type'] in ('erc20_transfer', 'erc1155_transfer') and edge['token_contract'] is None:
        raise ValueError('Token transfer must identify its token contract')
    raw = decimal_value(edge['raw_amount'])
    if raw < 0 or raw != raw.to_integral_value():
        raise ValueError('Raw amount must be a nonnegative integer')
    norm = decimal_value(edge['normalized_amount'])
    if norm != raw / (Decimal(10) ** edge['token_decimals']):
        raise ValueError('Normalized amount inconsistent with raw units')
    if edge['usd_value_when_supported'] is not None and decimal_value(edge['usd_value_when_supported']) < 0:
        raise ValueError('USD valuation cannot be negative')
    return dict(edge)


def id_of(edge):
    """Economic event identity; do not include amount in the event ID.

    For native transfers and legacy documentary rows without a log index,
    the route and asset are a fallback, not evidence of complete log coverage.
    """
    prefix = (edge['chain_id'], edge['transaction_hash'].lower())
    if edge['log_index'] is not None:
        return prefix + ('log', edge['log_index'])
    return prefix + ('unindexed', edge['relation_type'], edge['from'].lower(),
                     edge['to'].lower(), str(edge['token_contract']).lower())


def canonical_edges(rows):
    seen = {}
    for row in rows:
        edge = validate_edge(row)
        key = id_of(edge)
        if key in seen:
            old = seen[key]
            # A single on-chain log cannot simultaneously transfer two amounts,
            # tokens, or counterparties. Reject cache poisoning and mismatched decoders.
            material = set(FIELDS) - {'source', 'protocol'}
            if any(str(old[k]).lower() != str(edge[k]).lower() for k in material):
                raise ValueError(f'Conflicting evidence for one on-chain event: {key}')
        else:
            seen[key] = edge
    return sorted(seen.values(), key=lambda e: (utc_seconds(e['timestamp_utc']), e['chain_id'], e['transaction_hash'], e['log_index'] if e['log_index'] is not None else -1))


def financial_graph(rows):
    """Only actual transfers, never inferred bridges, minting from zero or suspicious similarities."""
    return [e for e in canonical_edges(rows)
            if e['evidence_level'] == ONCHAIN and e['relation_type'] in FINANCIAL
            and e['from'].lower() != e['to'].lower()
            and e['from'].lower() != '0x' + '0' * 40]


def control_graph(rows):
    return [e for e in canonical_edges(rows)
            if e['evidence_level'] == ONCHAIN and e['relation_type'] == 'contract_control']


def pair_links(rows, targets, node_roles):
    """Direct payments are links of money only. A common funder counts only when
    non-custodial status is independently established; unknown and service are not links.
    """
    transfers = financial_graph(rows)
    target = {w.lower() for w in targets}
    roles = {k.lower(): v for k, v in node_roles.items()}
    direct = []
    funding = {}
    for e in transfers:
        a, b = e['from'].lower(), e['to'].lower()
        if a in target and b in target:
            direct.append({'wallet_a': a, 'wallet_b': b, 'relation': 'direct_transfer', 'transaction_hash': e['transaction_hash'], 'ownership': 'NOT_ESTABLISHED'})
        if b in target and a not in target:
            funding.setdefault(a, set()).add(b)
    common = []
    unresolved = []
    for origin, receivers in sorted(funding.items()):
        if len(receivers) < 2:
            continue
        role = roles.get(origin, 'UNKNOWN')
        for a, b in combinations(sorted(receivers), 2):
            item = {'wallet_a': a, 'wallet_b': b, 'funder': origin, 'ownership': 'NOT_ESTABLISHED'}
            if role == 'PERSONAL_NONCUSTODIAL_CONFIRMED':
                common.append({**item, 'relation': 'shared_noncustodial_funder'})
            else:
                unresolved.append({**item, 'relation': 'shared_service_or_unclassified', 'source_class': role})
    return {'financial_links': direct + common, 'excluded_or_unresolved': unresolved}


def save_exports(rows, directory):
    """Explicit-only export; never opens a network connection or mutates source evidence."""
    directory = Path(directory)
    if directory.exists() and any(directory.iterdir()):
        raise FileExistsError('Output directory must be new or empty; never overwrite prior work')
    directory.mkdir(parents=True, exist_ok=True)
    valid = canonical_edges(rows)
    (directory / 'financial_graph.json').write_text(json.dumps({'edges': financial_graph(valid), 'meaning': 'financial transfers, not common ownership'}, indent=2) + '\n')
    with (directory / 'evidence_edges.csv').open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows({f: e[f] for f in FIELDS} for e in valid)
    graphml = ET.Element('graphml', xmlns='http://graphml.graphdrawing.org/xmlns')
    # Every graph edge retains its complete provenance rather than only its endpoints.
    for field in FIELDS:
        ET.SubElement(graphml, 'key', id=field, **{'for': 'edge', 'attr.name': field, 'attr.type': 'string'})
    graph = ET.SubElement(graphml, 'graph', edgedefault='directed', id='financial')
    nodes = sorted({v for e in financial_graph(valid) for v in (e['from'], e['to'])})
    for node in nodes:
        ET.SubElement(graph, 'node', id=node)
    for n, e in enumerate(financial_graph(valid)):
        item = ET.SubElement(graph, 'edge', id=f'e{n}', source=e['from'], target=e['to'])
        for field in FIELDS:
            ET.SubElement(item, 'data', key=field).text = '' if e[field] is None else str(e[field])
    ET.ElementTree(graphml).write(directory / 'financial.graphml', encoding='utf-8', xml_declaration=True)
    return {'input_edges': len(rows), 'unique_edges': len(valid), 'financial_edges': len(financial_graph(valid)), 'nodes': len(nodes)}
