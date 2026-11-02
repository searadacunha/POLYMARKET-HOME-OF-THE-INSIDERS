"""An investigation file an analyst can read and check, with its conclusion limited to its evidence."""
import gzip
import hashlib
import json

from polysentinel import reports

from .evidence_scoring import axes
from .funding_graph import behavioural_links
from .market_information_risk import information_timeline

CONCLUSIONS = {
    'EXPLORATORY': 'One unusual measurement. Nothing more can be said.',
    'ANOMALOUS': 'Behaviour unusual against its comparators on this event. This does not establish private information.',
    'CORROBORATED_BEHAVIOR': 'Unusual behaviour supported by another wallet or by observed funds. Common ownership and private information are not established.',
    'INSUFFICIENT_EVIDENCE': 'Too little history or too few comparators to conclude.'}
NOT_ESTABLISHED = ['Use of private information.', 'Identity of any person.', 'Common owner of several wallets.', 'Profit: a winning outcome is not a realized profit.', 'That no public information came earlier.']
ALTERNATIVES = ['Legal expertise or a private model.', 'Public information our sources do not cover.', 'Luck.', 'Copying another trader.', 'Automation or market making.', 'Arbitrage or a hedge outside our collection.', 'A conviction bet.']
SECTIONS = [('event', '1. Event and markets'), ('wallets', '2. Wallets'), ('chronology', '3. Chronology of operations'), ('positions', '4. Amounts and positions'), ('price_and_liquidity', '5. Price and liquidity'),
            ('signals', '6. Signals'), ('market_information_risk', '7. Market information risk'), ('comparators', '8. Statistical comparators'), ('funding_and_transactions', '9. Funding links and confirmed transactions'),
            ('public_information', '10. Public information at the observed time'), ('competing_explanations', '11. Competing explanations'), ('missing_data', '12. Missing data'), ('conclusion', '13. Conclusion')]


def build(output, rows, config, *, gaps=(), public_milestone=None, enrichment=None):
    pairs = output['pairs']
    timeline = information_timeline(public_milestone, None, None)
    funding_links = (enrichment or {}).get('links')
    confirmed = [f for f in (enrichment or {}).get('reconciled', []) if f.get('status') == 'matched']
    evidence = axes(pairs, output['collective'], output['risk'], funding_links, timeline, gaps, confirmed, config)
    contrary = list(ALTERNATIVES)
    for p in pairs:
        if p['profile']['sold_recently']:
            contrary.append(f"{p['wallet']} also sold within 24 h: gross buys are not net exposure.")
        if p['position']['outcomes_held'] > 1:
            contrary.append(f"{p['wallet']} holds several outcomes of this event: hedge or arbitrage possible.")
        if p['position']['drift_before_entry'] and p['position']['drift_before_entry'] > 0.05:
            contrary.append(f"The price was already rising before {p['wallet']} entered: possible reaction to public news.")
    if output['collective']['convergence']:
        contrary.append('Several wallets moving together can be reacting to the same public information.')
    missing = sorted(set(evidence['evidence_completeness']['missing']) | set(evidence['evidence_completeness']['unavailable']))
    if any(p['position']['depth_status'] != 'OBSERVED' for p in pairs):
        missing.append('Order book depth at trade time: not observed.')
    missing.append('Maker-side trades and small trades outside followed markets: partial coverage.')
    missing.append('Date when a restricted group knew the outcome: not observable.')
    return dict(
        schema='case-1', engine=config['version'], case_id=hashlib.sha256(output['event_key'].encode()).hexdigest()[:16], version=output['version'], decided_at=output['at'],
        category=output['category'], new_case=output['new_case'], needs_review=output['wants_review'], budget_held=output.get('budget_held', False), evidence_axes=evidence,
        event=dict(key=output['event_key'], title=output.get('title'), markets=sorted({r['condition_id'] for r in rows}), market_open=output['market_open'], contractual_end=output.get('end_at'), catalogued=not output['event_key'].startswith('unmapped:')),
        wallets=[dict(address=p['wallet'], observed_first_trade=p['profile']['observed_first_trade'], observed_age_h=p['profile']['observed_age_s'] / 3600, verified_first_chain_activity=p['profile']['verified_first_chain_activity'], markets_traded=p['profile']['markets_traded'], events_traded=p['profile']['events_traded'], baseline_status=p['profile']['baseline_status'],
                      first_trade_on_this_event=p['profile']['first_trade_on_this_event'], event_share_of_spend=p['profile']['event_share_of_spend'], url=f"https://polygonscan.com/address/{p['wallet']}") for p in pairs],
        chronology=[dict(at=r['ts'], first_observed=r['observed_at'], wallet=r['wallet'], side='BUY' if r['is_buy'] else 'SELL', shares=r['size'], price=r['price'], nominal=r['nominal'], token_id=r['token_id'], outcome=r.get('outcome'), market=r['condition_id'], tx=r['tx'], url=f"https://polygonscan.com/tx/{r['tx']}") for r in rows],
        positions=[dict(wallet=p['wallet'], tokens=p['position']['positions'], spend_largest_market=p['position']['max_market_spend'], gross_buys_event_24h=p['position']['event_buy_nominal_24h'], outcomes_held=p['position']['outcomes_held'], note='Observed in our collection; true inventory unknown.') for p in pairs],
        price_and_liquidity=[dict(wallet=p['wallet'], entry_vwap=p['position']['entry_vwap'], price_before=p['position']['price_before'], price_after_observed=p['position']['price_after_observed'], drift_before_entry=p['position']['drift_before_entry'], impact_observed=p['position']['impact_observed'], liquidity=p['position']['liquidity'], spread=p['position']['spread'], depth_status=p['position']['depth_status']) for p in pairs],
        signals=[dict(wallet=p['wallet'], wallet_findings=p['wallet_findings'], position_findings=p['position_findings'], unavailable=p['unavailable']) for p in pairs] + [dict(collective=output['collective'])],
        market_information_risk=output['risk'], comparators=[dict(wallet=p['wallet'], strata=p['keys'], measures=p['measures']) for p in pairs],
        funding_and_transactions=dict(links=(funding_links or []) + behavioural_links(output['collective']), reconciled_transactions=(enrichment or {}).get('reconciled', []), funding_status='checked' if funding_links is not None else 'not checked yet'),
        public_information=dict(timeline=timeline, availability=(enrichment or {}).get('public_availability'), note='What we could see at the decision time; absence of an article does not prove secrecy.'),
        competing_explanations=contrary, missing_data=sorted(set(missing)), gaps=list(gaps),
        conclusion=dict(category=output['category'], text=CONCLUSIONS[output['category']], not_established=NOT_ESTABLISHED, not_a_probability=True))


def write(case, directory):
    """Each version is a new file: a later enrichment never overwrites what was sealed before it."""
    stem = f"signal-case-{case['case_id']}-v{case['version']}"
    payload = json.dumps(case, ensure_ascii=False, sort_keys=True, separators=(',', ':'), default=str).encode()
    reports.atomic_write(directory / (stem + '.json.gz'), gzip.compress(payload, mtime=0))
    body = f'<article><p class="warn"><strong>{reports.esc(case["category"])}</strong>. {reports.esc(case["conclusion"]["text"])}</p><p>Version {reports.esc(case["version"])}, decided {reports.times(case["decided_at"])}. <a href="/reports/{stem}.json.gz">Complete evidence</a>.</p></article>'
    body += '<h2>1. Event and markets</h2>' + reports.detail(case['event'])
    body += '<h2>2. Wallets</h2><div class="scroll"><table><tr><th>Address</th><th>Observed age</th><th>Markets</th><th>Share of spend</th><th>Baseline</th></tr>'
    for w in case['wallets']:
        share = 'unknown' if w['event_share_of_spend'] is None else f"{w['event_share_of_spend']:.0%}"
        body += f'<tr><td><a href="{reports.esc(w["url"])}"><code>{reports.esc(w["address"])}</code></a></td><td>{w["observed_age_h"]:.0f} h</td><td>{w["markets_traded"]}</td><td>{share}</td><td>{reports.esc(w["baseline_status"])}</td></tr>'
    body += '</table></div><h2>3. Chronology of operations</h2><div class="scroll"><table><tr><th>UTC</th><th>Wallet</th><th>Side</th><th>Outcome</th><th>Price</th><th>Nominal</th><th>Transaction</th></tr>'
    for t in case['chronology'][:120]:
        body += f'<tr><td>{reports.times(t["at"])}</td><td><code>{reports.esc(t["wallet"])}</code></td><td>{t["side"]}</td><td>{reports.esc(t["outcome"])}</td><td>{t["price"]:.3f}</td><td>{t["nominal"]:.0f}</td><td><a href="{reports.esc(t["url"])}">{reports.esc(t["tx"][:12])}…</a></td></tr>'
    body += '</table></div>'
    for key, title in SECTIONS[3:]:
        body += f'<h2>{reports.esc(title)}</h2>' + reports.detail(case[key])
    reports.atomic_write(directory / (stem + '.html'), reports.page((case['event']['title'] or case['event']['key']) + ', investigation file', body))
    return stem
