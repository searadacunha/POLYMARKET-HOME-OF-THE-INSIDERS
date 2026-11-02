"""Does grouping wallets by funding add links, and at what cost in false ones? On receipts already stored.

No owner is known, so false links cannot be counted. What is counted: links that pass through a mint, a
protocol or a forwarding address, which are known to prove nothing, before and after the role rules.
Reads the collector's database read-only. Usage: python -m signal_engine.experimental.funding_bench [--out FILE]
"""
import argparse
import json
import sqlite3
import zlib
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

from ..funding_graph import ZERO_ADDRESS, economic_role, unique_edges
from .splits import Groups

DATABASE = Path(__file__).resolve().parents[2] / 'data/polysentinel.sqlite3'
HUB_LIMITS = (None, 10, 5, 3)


def stored_edges():
    cx = sqlite3.connect(f'file:{DATABASE}?mode=ro', uri=True, timeout=10)
    edges, wallets, receipts = [], set(), 0
    for (body,) in cx.execute("SELECT c.body FROM object_refs r JOIN contents c ON c.id=r.content_id WHERE r.kind='investigation'"):
        case = json.loads(zlib.decompress(body))
        wallets |= {w.lower() for w in case.get('wallets') or []}
        for receipt in case.get('receipts', []):
            receipts += 1
            edges += [dict(t, timestamp=receipt.get('timestamp')) for t in receipt.get('transfers', []) if t.get('proof_level') == 'lien directement observable']
    cx.close()
    return edges, wallets, receipts


def funder_pairs(edges, wallets, hub_limit):
    """Wallet pairs sharing a sender. Without roles every sender counts, which is what a naive graph does."""
    senders = defaultdict(set)
    for e in edges:
        if e['target'].lower() in wallets and e['source'].lower() not in wallets:
            senders[e['source'].lower()].add(e['target'].lower())
    pairs, used = set(), {}
    for sender, recipients in senders.items():
        if len(recipients) >= 2 and (hub_limit is None or len(recipients) < hub_limit):
            pairs |= set(combinations(sorted(recipients), 2))
            used[sender] = len(recipients)
    return pairs, used


def components(pairs):
    groups = Groups()
    for a, b in pairs:
        groups.link(a, b, 'shared sender')
    members = defaultdict(set)
    for a, b in pairs:
        members[groups.find(a)] |= {a, b}
    return sorted((len(v) for v in members.values()), reverse=True)


def confirmed_transfer_pairs():
    """Pairs of studied wallets sharing a real sender or a direct transfer, with one transaction as the reason."""
    raw, wallets, _ = stored_edges()
    edges, _ = unique_edges(raw)
    by_tx = defaultdict(list)
    for e in edges:
        by_tx[e['transaction_hash'].lower()].append(e)
    transfers = [e for e in edges if economic_role(e, by_tx[e['transaction_hash'].lower()]) == 'transfer']
    tx_of = {}
    for e in transfers:
        tx_of.setdefault(e['source'].lower(), e['transaction_hash'])
    pairs = [(a, b, tx_of.get(a) or tx_of.get(b)) for a, b in funder_pairs(transfers, wallets, None)[0]]
    pairs += [(e['source'].lower(), e['target'].lower(), e['transaction_hash']) for e in transfers if e['source'].lower() in wallets and e['target'].lower() in wallets and e['source'].lower() != e['target'].lower()]
    return pairs


def run():
    raw, wallets, receipts = stored_edges()
    edges, conflicts = unique_edges(raw)
    by_tx = defaultdict(list)
    for e in edges:
        by_tx[e['transaction_hash'].lower()].append(e)
    roles = Counter()
    transfers = []
    for e in edges:
        role = economic_role(e, by_tx[e['transaction_hash'].lower()])
        roles[role] += 1
        if role == 'transfer':
            transfers.append(e)
    naive = {}
    rule = {}
    labelled = [e for e in edges if not e.get('infrastructure')]
    for limit in HUB_LIMITS:
        key = str(limit)
        pairs, used = funder_pairs(labelled, wallets, limit)
        kept, kept_used = funder_pairs(transfers, wallets, limit)
        naive[key] = dict(pairs=len(pairs), senders=len(used), through_zero_address=sum(1 for s in used if s == ZERO_ADDRESS), largest_groups=components(pairs)[:5], top_sender_recipients=sorted(used.values(), reverse=True)[:3])
        rule[key] = dict(pairs=len(kept), senders=len(kept_used), largest_groups=components(kept)[:5], top_sender_recipients=sorted(kept_used.values(), reverse=True)[:3], pairs_not_in_naive=len(kept - pairs))
    direct = {tuple(sorted((e['source'].lower(), e['target'].lower()))) for e in transfers if e['source'].lower() in wallets and e['target'].lower() in wallets and e['source'].lower() != e['target'].lower()}
    return dict(investigated_wallets=len(wallets), receipts_read=receipts, edges_read=len(raw), unique_logs=len(edges), read_twice=len(raw) - len(edges), conflicts=len(conflicts), roles=dict(roles), direct_transfers_between_investigated_wallets=len(direct),
                labels_only=naive, with_roles=rule, limit='Receipts of sampled trades, not address histories: most deposits and withdrawals are not here.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out')
    a = p.parse_args()
    result = run()
    text = json.dumps(result, indent=1, sort_keys=True)
    if a.out:
        Path(a.out).write_text(text)
    print(text)


if __name__ == '__main__':
    main()
