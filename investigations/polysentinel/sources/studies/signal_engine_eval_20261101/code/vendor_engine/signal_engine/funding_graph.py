"""Links between wallets, each with its nature, its provenance and an explicit confidence.

Nothing here merges owners. A link is an observation about money or behaviour; two wallets stay two
wallets, whatever their links. Shared infrastructure such as an exchange, a bridge or a relayer is
kept and labelled, and it never raises confidence.
"""
from collections import defaultdict

CONFIRMED_TRANSFER = 'confirmed_transfer'
DIRECT_LINK = 'direct_transfer_between_wallets'
SHARED_FUNDER = 'shared_funder'
SHARED_INFRASTRUCTURE = 'shared_infrastructure'
SIMILAR_TIMING = 'similar_timing'
SIMILAR_AMOUNT = 'similar_amount'
SIMILAR_MULTI_EVENT = 'similar_behaviour_across_events'
CONFIDENCE = {DIRECT_LINK: 'medium', SHARED_FUNDER: 'low', SHARED_INFRASTRUCTURE: 'none', SIMILAR_TIMING: 'none', SIMILAR_AMOUNT: 'none', SIMILAR_MULTI_EVENT: 'low'}
ALTERNATIVES = {DIRECT_LINK: 'Payment between independent people, or a service that forwards funds.', SHARED_FUNDER: 'A service, a market maker or a person paying several unrelated people.',
                SHARED_INFRASTRUCTURE: 'Thousands of unrelated users pass through the same service.', SIMILAR_TIMING: 'Reaction to the same public information, or independent bots.',
                SIMILAR_AMOUNT: 'Round amounts are common and platform limits produce identical sizes.', SIMILAR_MULTI_EVENT: 'Same strategy or same interest, not the same owner.'}


def _edge_provenance(edge):
    return dict(transaction_hash=edge.get('transaction_hash'), log_index=edge.get('log_index'), block_number=edge.get('block_number'), url=f"https://polygonscan.com/tx/{edge.get('transaction_hash')}", symbol=edge.get('symbol'), amount=edge.get('amount'))


def build_funding_links(edges, wallets, window_s=86400):
    """Edges are ERC20 transfers already confirmed on a canonical block by the receipt decoder."""
    wallets = {w.lower() for w in wallets}
    links, by_source = [], defaultdict(list)
    for e in edges:
        if e.get('proof_level') != 'lien directement observable':
            continue
        source, target = e['source'].lower(), e['target'].lower()
        if source in wallets and target in wallets and source != target:
            links.append(dict(kind=DIRECT_LINK, confidence=CONFIDENCE[DIRECT_LINK], wallets=sorted((source, target)), provenance=[_edge_provenance(e)], alternative=ALTERNATIVES[DIRECT_LINK], common_owner_established=False))
        if target in wallets and source not in wallets:
            by_source[source].append(e)
    for source, received in by_source.items():
        recipients = sorted({e['target'].lower() for e in received})
        if len(recipients) < 2:
            continue
        infrastructure = any(e.get('infrastructure') for e in received)
        kind = SHARED_INFRASTRUCTURE if infrastructure else SHARED_FUNDER
        times = sorted(e['timestamp'] for e in received if e.get('timestamp'))
        links.append(dict(kind=kind, confidence=CONFIDENCE[kind], wallets=recipients, counterparty=source, counterparty_label=next((e.get('counterparty_label') for e in received if e.get('counterparty_label')), None),
                          close_in_time=(times[-1] - times[0] <= window_s) if len(times) >= 2 else None, provenance=[_edge_provenance(e) for e in received], alternative=ALTERNATIVES[kind], common_owner_established=False))
    return links


def behavioural_links(collective):
    """Behaviour is recorded in the same vocabulary, and it stays at the lowest confidence."""
    links = []
    for token, wallets in collective.get('convergence', {}).items():
        links.append(dict(kind=SIMILAR_TIMING, confidence=CONFIDENCE[SIMILAR_TIMING], wallets=wallets, token_id=token, alternative=ALTERNATIVES[SIMILAR_TIMING], common_owner_established=False))
    for cluster in collective.get('identical_amounts', []):
        links.append(dict(kind=SIMILAR_AMOUNT, confidence=CONFIDENCE[SIMILAR_AMOUNT], wallets=cluster['wallets'], token_id=cluster['token_id'], amount=cluster['amount'], alternative=ALTERNATIVES[SIMILAR_AMOUNT], common_owner_established=False))
    for repeat in collective.get('repeated_across_events', []):
        links.append(dict(kind=SIMILAR_MULTI_EVENT, confidence=CONFIDENCE[SIMILAR_MULTI_EVENT], wallets=repeat['wallets'], events=repeat['events'], alternative=ALTERNATIVES[SIMILAR_MULTI_EVENT], common_owner_established=False))
    return links


def corroborating_funding(links):
    """Only money moving outside shared infrastructure can corroborate; behaviour cannot corroborate itself."""
    return [l for l in links if l['kind'] in (DIRECT_LINK, SHARED_FUNDER)]
