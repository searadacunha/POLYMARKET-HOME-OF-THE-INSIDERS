"""Links between wallets, each with its nature, its provenance and an explicit confidence.

Nothing here merges owners. A link is an observation about money or behaviour; two wallets stay two
wallets, whatever their links. Shared infrastructure such as an exchange, a bridge or a relayer is
kept and labelled, and it never raises confidence.

One log is one event, keyed by chain, transaction and log index, whichever investigation read it. A
receipt shows what its transaction moved, not the address's whole history, and every link says so.
Stored receipts showed two false funders that labels alone miss: the zero address minting collateral,
and an address whose payment the wallet forwards within the same transaction.
"""
from collections import defaultdict

CONFIRMED_TRANSFER = 'confirmed_transfer'
DIRECT_LINK = 'direct_transfer_between_wallets'
SHARED_FUNDER = 'shared_funder'
SHARED_INFRASTRUCTURE = 'shared_infrastructure'
SIMILAR_TIMING = 'similar_timing'
SIMILAR_AMOUNT = 'similar_amount'
SIMILAR_MULTI_EVENT = 'similar_behaviour_across_events'
POSSIBLE_COORDINATION = 'possible_coordination'
CHAIN_ID = 137
ZERO_ADDRESS = '0x' + '0' * 40
OWNERSHIP = 'OWNERSHIP_NOT_ESTABLISHED'
COMPLETENESS = 'Receipts sampled for this case; the addresses have other transfers we did not read.'
ASSESSMENT = {DIRECT_LINK: 'COMMON_FUNDING_ROUTE', SHARED_FUNDER: 'COMMON_FUNDING_ROUTE', SHARED_INFRASTRUCTURE: 'SHARED_INFRASTRUCTURE', SIMILAR_TIMING: 'BEHAVIORAL_SIMILARITY', SIMILAR_AMOUNT: 'BEHAVIORAL_SIMILARITY', SIMILAR_MULTI_EVENT: 'BEHAVIORAL_SIMILARITY'}
CONFIDENCE = {DIRECT_LINK: 'medium', SHARED_FUNDER: 'low', SHARED_INFRASTRUCTURE: 'none', SIMILAR_TIMING: 'none', SIMILAR_AMOUNT: 'none', SIMILAR_MULTI_EVENT: 'low'}
ALTERNATIVES = {DIRECT_LINK: 'Payment between independent people, or a service that forwards funds.', SHARED_FUNDER: 'A service, a market maker or a person paying several unrelated people.',
                SHARED_INFRASTRUCTURE: 'Thousands of unrelated users pass through the same service.', SIMILAR_TIMING: 'Reaction to the same public information, or independent bots.',
                SIMILAR_AMOUNT: 'Round amounts are common and platform limits produce identical sizes.', SIMILAR_MULTI_EVENT: 'Same strategy or same interest, not the same owner.'}


def _edge_provenance(edge):
    return dict(chain_id=CHAIN_ID, source=edge['source'], target=edge['target'], transaction_hash=edge.get('transaction_hash'), log_index=edge.get('log_index'), block_number=edge.get('block_number'), block_hash=edge.get('block_hash'), timestamp=edge.get('timestamp'),
                url=f"https://polygonscan.com/tx/{edge.get('transaction_hash')}", token=edge.get('token'), symbol=edge.get('symbol'), amount=edge.get('amount'), amount_raw=edge.get('amount_raw'), role=edge.get('role'), service=edge.get('counterparty_label'), completeness=COMPLETENESS)


def unique_edges(edges):
    """Same log read twice is one edge. Two readings that disagree are both dropped and reported."""
    seen, conflicts = {}, set()
    for edge in edges:
        key = (str(edge.get('transaction_hash')).lower(), edge.get('log_index'))
        content = (edge['source'].lower(), edge['target'].lower(), edge.get('token'), edge.get('amount_raw', edge.get('amount')))
        if key in seen and seen[key][0] != content:
            conflicts.add(key)
        seen.setdefault(key, (content, edge))
    return [e for key, (_, e) in seen.items() if key not in conflicts], sorted(conflicts, key=str)


def economic_role(edge, transaction_edges):
    """What a transfer did for the receiving wallet, read from all the transfers of its transaction."""
    source, target = edge['source'].lower(), edge['target'].lower()
    if source == ZERO_ADDRESS:
        return 'mint'
    if target == ZERO_ADDRESS:
        return 'burn'
    if edge.get('infrastructure'):
        return 'protocol_settlement'
    token = edge.get('token') or edge.get('symbol')
    net = 0.0
    for other in transaction_edges:
        if (other.get('token') or other.get('symbol')) == token:
            net += other.get('amount', 0) * ((other['target'].lower() == target) - (other['source'].lower() == target))
    return 'pass_through' if net <= 1e-9 and edge.get('amount', 0) > 0 else 'transfer'


def build_funding_links(edges, wallets, window_s=86400):
    """Edges are ERC20 transfers already confirmed on a canonical block by the receipt decoder."""
    wallets = {w.lower() for w in wallets}
    confirmed = [e for e in edges if e.get('proof_level') == 'lien directement observable']
    confirmed, conflicts = unique_edges(confirmed)
    by_transaction = defaultdict(list)
    for e in confirmed:
        by_transaction[str(e.get('transaction_hash')).lower()].append(e)
    links, by_source = [], defaultdict(list)
    for key in conflicts:
        links.append(dict(kind='conflicting_records', confidence='none', wallets=[], transaction_hash=key[0], log_index=key[1], common_owner_established=False, ownership=OWNERSHIP, alternative='Two readings of one log disagree; neither is used.'))
    for e in confirmed:
        e = dict(e, role=economic_role(e, by_transaction[str(e.get('transaction_hash')).lower()]))
        source, target = e['source'].lower(), e['target'].lower()
        if source in wallets and target in wallets and source != target and e['role'] == 'transfer':
            links.append(dict(kind=DIRECT_LINK, assessment=ASSESSMENT[DIRECT_LINK], confidence=CONFIDENCE[DIRECT_LINK], wallets=sorted((source, target)), provenance=[_edge_provenance(e)], alternative=ALTERNATIVES[DIRECT_LINK], common_owner_established=False, ownership=OWNERSHIP))
        if target in wallets and source not in wallets:
            by_source[source].append(e)
    for source, received in by_source.items():
        recipients = sorted({e['target'].lower() for e in received})
        if len(recipients) < 2:
            continue
        roles = sorted({e['role'] for e in received})
        kind = SHARED_FUNDER if roles == ['transfer'] else SHARED_INFRASTRUCTURE
        times = sorted(e['timestamp'] for e in received if e.get('timestamp'))
        label = next((e.get('counterparty_label') for e in received if e.get('counterparty_label')), None) or (f"Not a funder: {', '.join(roles)}" if kind == SHARED_INFRASTRUCTURE else None)
        links.append(dict(kind=kind, assessment=ASSESSMENT[kind], confidence=CONFIDENCE[kind], wallets=recipients, counterparty=source, counterparty_label=label, roles=roles,
                          close_in_time=(times[-1] - times[0] <= window_s) if len(times) >= 2 else None, provenance=[_edge_provenance(e) for e in received], alternative=ALTERNATIVES[kind], common_owner_established=False, ownership=OWNERSHIP))
    return links


def behavioural_links(collective):
    """Behaviour is recorded in the same vocabulary, and it stays at the lowest confidence."""
    links = []
    common = dict(assessment='BEHAVIORAL_SIMILARITY', ownership=OWNERSHIP)
    for token, wallets in collective.get('convergence', {}).items():
        links.append(dict(common, kind=SIMILAR_TIMING, confidence=CONFIDENCE[SIMILAR_TIMING], wallets=wallets, token_id=token, alternative=ALTERNATIVES[SIMILAR_TIMING], common_owner_established=False))
    for cluster in collective.get('identical_amounts', []):
        links.append(dict(common, kind=SIMILAR_AMOUNT, confidence=CONFIDENCE[SIMILAR_AMOUNT], wallets=cluster['wallets'], token_id=cluster['token_id'], amount=cluster['amount'], alternative=ALTERNATIVES[SIMILAR_AMOUNT], common_owner_established=False))
    for repeat in collective.get('repeated_across_events', []):
        links.append(dict(common, kind=SIMILAR_MULTI_EVENT, confidence=CONFIDENCE[SIMILAR_MULTI_EVENT], wallets=repeat['wallets'], events=repeat['events'], alternative=ALTERNATIVES[SIMILAR_MULTI_EVENT], common_owner_established=False))
    return links


def possible_coordination(links):
    """A funding route and similar behaviour over the same wallets: worth reading, still no owner."""
    routes = [l for l in links if l.get('kind') in (DIRECT_LINK, SHARED_FUNDER)]
    similar = [l for l in links if l.get('kind') in (SIMILAR_TIMING, SIMILAR_AMOUNT, SIMILAR_MULTI_EVENT)]
    found = []
    for route in routes:
        for behaviour in similar:
            both = sorted(set(route['wallets']) & set(behaviour['wallets']))
            if len(both) >= 2:
                found.append(dict(kind=POSSIBLE_COORDINATION, assessment='POSSIBLE_COORDINATION', confidence='low', wallets=both, basis=[route['kind'], behaviour['kind']], common_owner_established=False, ownership=OWNERSHIP,
                                  alternative='One service paying several unrelated customers who react to the same news.'))
    return found


def corroborating_funding(links):
    """Only money moving outside shared infrastructure can corroborate; behaviour cannot corroborate itself."""
    return [l for l in links if l['kind'] in (DIRECT_LINK, SHARED_FUNDER)]
