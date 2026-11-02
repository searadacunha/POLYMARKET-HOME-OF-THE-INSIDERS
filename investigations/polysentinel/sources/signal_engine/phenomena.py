"""Six phenomena kept apart, each with what supports it and the data it would need.

A price rise after a purchase does not make an insider, a large volume does not make a wash trade, and
spoofing cannot be said from executed trades alone. When the data is absent the answer is NOT_EVALUATED,
which is not a no. None of this is a probability or a finding about a person.
"""
OBSERVED, NOT_OBSERVED, NOT_EVALUATED = 'OBSERVED', 'NOT_OBSERVED', 'NOT_EVALUATED'
SIZE_AND_FREQUENCY = {'size_break', 'frequency_break', 'large_for_context', 'rapid_accumulation'}
DRIFT_BEFORE_ENTRY = 0.05


def assess_phenomena(pairs, collective, risk, market_open, timeline):
    findings = {k for p in pairs for k in list(p['wallet_findings']) + list(p['position_findings'])}
    size = sorted(findings & SIZE_AND_FREQUENCY)
    any_liquidity = any(p['position'].get('liquidity_fraction') is not None for p in pairs)
    together = {k: collective[k] for k in ('convergence', 'identical_amounts', 'repeated_across_events') if collective.get(k)}
    drifted = [p['wallet'] for p in pairs if (p['position'].get('drift_before_entry') or 0) > DRIFT_BEFORE_ENTRY]
    public_status = timeline['first_credible_public_information']['status']
    structural = risk['level'] in ('MEDIUM', 'HIGH')
    advantage = OBSERVED if findings and structural and market_open else NOT_OBSERVED if risk['level'] == 'LOW' or not market_open else NOT_EVALUATED
    if public_status not in ('unknown', None):
        reaction = dict(status=OBSERVED, basis=[f'First public information documented: {public_status}.'])
    elif drifted:
        reaction = dict(status=OBSERVED, basis=[f'Price already rising before the entry of {len(drifted)} wallet(s).'])
    else:
        reaction = dict(status=NOT_EVALUATED, basis=[], data_needed=['A public source covering this event, dated before the trades.'])
    return dict(
        size_or_frequency_anomaly=dict(status=OBSERVED if size else NOT_OBSERVED, basis=size),
        liquidity_anomaly=dict(status=OBSERVED if 'large_against_liquidity' in findings else NOT_OBSERVED if any_liquidity else NOT_EVALUATED, basis=sorted(findings & {'large_against_liquidity'}),
                               data_needed=[] if any_liquidity else ['Liquidity or order book depth dated at the trade.']),
        behavioral_coordination=dict(status=OBSERVED if together else NOT_OBSERVED, basis=sorted(together), not_established='Common owner; the same public information can explain it.'),
        market_manipulation=dict(status=NOT_EVALUATED, basis=[], data_needed=['Order creations and cancellations, for spoofing and layering.', 'Both sides of each fill with their controllers, for wash trading.', 'Book state around price moves.']),
        possible_information_advantage=dict(status=advantage, basis=dict(market_structure=risk['level'], unusual_purchases=sorted(findings), market_open=market_open),
                                            not_established='That anyone had access. Structure says who could know; behaviour says what was done; neither shows that a leak happened.'),
        reaction_to_public_information=reaction)
