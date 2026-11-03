"""Write the list of checks the claims auditor runs. Values for `tx` come from the claim's own output file, and the auditor re-reads them from other nodes. Usage: build_checks.py <results dir> <out.json>."""
import csv
import json
import random
import sys
from pathlib import Path

USDT = '0xdac17f958d2ee523a2206206994597c13d831ec7'
TEXTS = ('FINDINGS.md', 'STATUS.md', 'README.md', 'results/SHADOW.md', 'results/CHANGENOW.md', 'results/links/neodbs_planktonbets.md', 'results/MADURO_REREAD.md', 'results/CHANGENOW_DOSSIERS.md', 'results/GRAPH.md')
ACCUSATIONS = (r'\b(?:is|are|was|were) (?:an? )?insiders?\b', r'\bconfirmed insiders?\b', r'\b(?:proves?|shows?|establish(?:es)?) (?:that )?(?:insider|the same (?:owner|person|holder))', r'\binsider wallets?\b', r'\bsame (?:owner|person|holder) (?:is|was) (?:proved|proven|established|confirmed)')


def main(results, out):
    results = Path(results)
    checks = []
    link = json.loads((results / 'links/neodbs_planktonbets.json').read_text())
    for h in link['hops']:
        c = dict(claim='F-009', kind='tx', chain=h['chain'], tx=h['tx'], raw=h['raw_amount'], **{'from': h['from'], 'to': h['to']})
        c.update(contract=None) if h['token'] == 'ETH' else c.update(contract=USDT, log_index=h['log_index'])
        checks.append(c)
    with (results / 'references/reference_verification.csv').open() as f:
        rows = [r for r in csv.DictReader(f) if r['expect_from'] and r['expect_to'] and r['expect_raw'] and r['expect_contract'] and r['expect_log'] and int(r['chain']) in (1, 137, 42161, 8453, 10, 56)]
    for r in random.Random(20261103).sample(rows, min(25, len(rows))):
        checks.append(dict(claim='F-001', kind='tx', chain=int(r['chain']), tx=r['tx'], contract=r['expect_contract'], log_index=int(r['expect_log']), raw=r['expect_raw'], **{'from': r['expect_from'], 'to': r['expect_to']}))
    checks += [
        dict(claim='F-005', kind='json', file='results/study_sync/tables/verdict.json', path=['global_verdict'], value='NOT_SUPPORTED'),
        dict(claim='F-006', kind='json', file='results/changenow/cn_join_summary.json', path=['counts', 'rows'], value=431444),
        dict(claim='F-006', kind='json', file='results/changenow/cn_join_summary.json', path=['known_wallets'], value=309565),
        dict(claim='F-008', kind='json', file='results/shadow/status.json', path=['alerts'], value=283),
        dict(claim='F-011', kind='json', file='results/shadow/latency_sources.json', path=['alerts', 'by_cause', 'normal_poll', 'n'], value=111),
        dict(claim='F-011', kind='json', file='results/shadow/latency_sources.json', path=['gaps', 'total_hours'], value=88.5),
        dict(claim='F-012', kind='json', file='results/shadow/latency_sources.json', path=['alerts', 'spread_wider_than_stated_window'], value=100),
        dict(claim='F-012', kind='json', file='results/shadow_v2/status.json', path=['alerts'], value=241),
    ]
    summary = results / 'maduro_iran/summary.json'
    if summary.exists():
        d = json.loads(summary.read_text())
        for key, n in d['by_result'].items():
            checks.append(dict(claim='F-010', kind='csv_count', file='results/maduro_iran/edge_verification.csv', where=dict(result=key), n=n))
    for name in TEXTS:
        if (results.parent / name).exists():
            for pattern in ACCUSATIONS:
                checks.append(dict(claim='no accusation', kind='forbid', file=name, pattern=pattern))
    Path(out).write_text(json.dumps(checks, indent=0))
    print(len(checks))


if __name__ == '__main__':
    main(*sys.argv[1:])
