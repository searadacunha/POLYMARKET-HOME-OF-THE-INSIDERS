"""Read-only bridge from monitoring rows to this folder's evidence schema. No network, no store change.

A funding row records a collateral transfer seen in Polygon logs; it is money movement, not identity.
"""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

import ledger

POLYGON = 137
# The collateral tokens monitoring/phi_monitor/chain.py:transfers_to reads, each divided by 1e6 there (pinned by the test).
SIX_DECIMAL_TOKENS = {
    '0x3c499c542cef5e3811e1192ce70d8cc03d5c3359',  # USDC
    '0x2791bca1f2de4661ed88a30c99a7a9449aa84174',  # USDC.e
    '0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb',  # pUSD
}
FUNDING_FIELDS = ('tx', 'log_index', 'block', 'ts', 'proxy', 'payer', 'token', 'amount')
SOURCE = 'monitoring funding table (phi_monitor.collect.funding, Polygon ERC-20 Transfer logs)'


def _funding_edge(row):
    missing = [f for f in FUNDING_FIELDS if row.get(f) is None]
    if missing:
        raise ValueError(f'missing {", ".join(missing)}')
    token = str(row['token']).lower()
    if token not in SIX_DECIMAL_TOKENS:
        raise ValueError('token is not a collateral token read by phi_monitor.chain.transfers_to: decimals unknown')
    if type(row['amount']) is not float or type(row['ts']) is not int:
        raise ValueError('amount must be the stored float and ts an integer')
    # The table stores raw / 1e6 as a float; recover the integer only when it is exact.
    raw = Decimal(repr(row['amount'])).scaleb(6)
    if raw != raw.to_integral_value() or raw >= 2 ** 53:
        raise ValueError('amount is not an exact whole number of 6-decimal units')
    raw = str(int(raw))
    return ledger.validate_edge({
        'chain_id': POLYGON, 'transaction_hash': row['tx'], 'block_number': row['block'],
        'timestamp_utc': datetime.fromtimestamp(row['ts'], timezone.utc).isoformat(), 'log_index': row['log_index'],
        'from': row['payer'], 'to': row['proxy'], 'token_contract': token, 'token_decimals': 6,
        'raw_amount': raw, 'normalized_amount': str(ledger.normalized_units(raw, 6)), 'usd_value_when_supported': None,
        'protocol': None, 'source': SOURCE, 'relation_type': 'erc20_transfer', 'evidence_level': ledger.ONCHAIN,
    })


def funding_to_edges(rows):
    """Rows of the phi_monitor funding table -> (edges for ledger.canonical_edges, [(row, reason)] refused).

    Nothing is filled in: a row without a log index, token or amount (phi_engine deposits rows, alert summaries) is refused.
    """
    edges, refused = [], []
    for row in rows:
        try:
            edges.append(_funding_edge(dict(row)))
        except ValueError as exc:
            refused.append((row, str(exc)))
    return edges, refused
