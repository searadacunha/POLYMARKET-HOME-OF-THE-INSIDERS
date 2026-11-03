"""Written from results/changenow/dossiers.json only. Usage: cn_report.py <results dir>. Numbers, addresses and hashes are copied by this script."""
import json
import sys
import time
from collections import Counter
from pathlib import Path

READ = {
    'KEY_FUNDS_ACCOUNT_AFTER_PAYMENT': 'Within 30 days the key put at least half the payment into the account',
    'KEY_PAYS_LESS_THAN_HALF_OR_LATER': 'The key paid into the account, less than half within 30 days',
    'PAYMENT_LANDS_ON_THE_TRADING_ADDRESS': 'The payment reached the trading address itself, on Polygon',
    'PATH_THROUGH_OTHER_ADDRESSES_AFTER_PAYMENT': 'Later moves lead from this key to the account through other addresses, crossing no service',
    'NO_PATH_FOUND_IN_WHAT_WAS_READ': 'No path from this key to the account in what was read: an address match, and no funding shown',
    'NOT_TRACED': 'Account not traced',
}
DAY = lambda t: time.strftime('%Y-%m-%d %H:%M', time.gmtime(t)) if t else 'unknown'


def next_cell(row):
    cells = []
    for h in row.get('outflows_within_7_days', [])[:2]:
        amount = int(h['raw']) / 10 ** int(h['decimals'] or 0)
        name = h.get('next_label') or h.get('next_class')
        bridge = h.get('bridge')
        if bridge:
            name += f", to `{str(bridge.get('recipient'))[:12]}…` proof {bridge.get('proof')}"
        cells.append(f"{amount:,.2f} {h['token']} to `{h['to'][:10]}…` ({name})")
    return '; '.join(cells) or 'none in 7 days'


def main(results):
    results = Path(results)
    d = json.loads((results / 'changenow/dossiers.json').read_text())
    hits = {}
    for line in (results / 'changenow/cn_polymarket_hits.jsonl').read_text().splitlines():
        h = json.loads(line)
        hits[(h['wallet'], h['recipient'], h['first_tx'])] = h
    s = d['summary']
    readings = Counter(r['funding_reading'] for f in d['files'] for r in f['rows'])
    out = ['# The 26 ChangeNOW files', '', 'Written by `engine/tools/cn_report.py` from `results/changenow/dossiers.json`, itself from `engine/tools/cn_dossiers.py` and light traces. Each file starts from a payment by an address attributed to the service, or a candidate, to a key or address that reaches a trading wallet.', '', 'No one here is called an insider. A label says what a source wrote. Money is fungible, so a key paying its account after a payment shows order and amounts, never that those coins paid for a bet.', '', '## Labels and independence', '', '| Source address | Independent label lineages | Lineages | Names |', '|---|---:|---|---|']
    for address, v in s['sources'].items():
        out.append(f"| `{address}` | {v['independent_lineages']} | {', '.join(v['lineages']) or 'absent from the attribution table'} | {', '.join(v['names']) or 'none'} |")
    out += ['', 'Rows from an address with no or one weak lineage are candidates, not attributions.', '', '## Readings', '', f"Payments read again from nodes: {s['payments_found']} found of {s['payments_found'] + s['payments_not_found'] + s['payments_unread']}. Network calls for this file: {s['calls']}.", '', '| Reading | Rows |', '|---|---:|']
    for key, label in READ.items():
        if readings[key]:
            out.append(f'| {label} | {readings[key]} |')
    lineages = lambda r: '2 or more' if r['label']['independent_lineages'] >= 2 else str(r['label']['independent_lineages'])
    crossed = Counter((lineages(r), r['funding_reading']) for f in d['files'] for r in f['rows'])
    out += ['', '## Three separate questions', '', 'Is the label sound, did the payment happen, and did that money reach the account? One answer never stands in for another.', '', f"- Rows from a source with 2 or more independent label lineages: {sum(r['label']['independent_lineages'] >= 2 for f in d['files'] for r in f['rows'])}, with 1: {sum(r['label']['independent_lineages'] == 1 for f in d['files'] for r in f['rows'])}, with 0: {sum(r['label']['independent_lineages'] == 0 for f in d['files'] for r in f['rows'])}.", f"- Payment read on a node, by level: {dict(Counter(r['payment'].get('level') for f in d['files'] for r in f['rows']))}.", '', '| Label lineages | Reading | Rows |', '|---|---|---:|']
    out += [f'| {a} | {b} | {n} |' for (a, b), n in sorted(crossed.items())]
    out += ['', 'An empty path can come from what was read: light traces follow 8 addresses per direction, and a key can pay through an address it controls without any link in these reads. A deposit that reaches a wallet by a route other than these is not seen here.', '', '## Rows', '', '| Wallet | Key or address | Form | Tier | Paid, USD | When | Level | Next moves of the key within 7 days | Into the account within 30 days, USD | Reading | Wallet history complete |', '|---|---|---|---|---:|---|---|---|---:|---|---|']
    rows = sorted(((r['usd'] or 0, f, r) for f in d['files'] for r in f['rows']), key=lambda x: -x[0])
    for usd, f, r in rows:
        out.append(f"| `{f['wallet'][:12]}…` | `{r['recipient'][:12]}…` | {r['form']} | {r['tier']} | {usd:,.2f} | {DAY(r['first_ts'])} | {r['payment'].get('level')} | {next_cell(r)} | {r['usd_into_account_30_days']:,.2f} | {r['funding_reading']} | {f.get('history_complete')} |")
    services = Counter(x for f in d['files'] for x in f.get('cashout_services', []))
    paths = [(f, r) for f in d['files'] for r in f['rows'] if r.get('path_through_other_addresses')]
    if paths:
        out += ['', '## Paths through other addresses', '', 'Each line is one move. Other explanations: an address in between can be a person, a desk or a service nobody labelled, and money is fungible.', '', '| Wallet | Hop | UTC | Amount | Chain | From | To | Level | Transaction |', '|---|---:|---|---:|---|---|---|---|---|']
        for f, r in paths:
            for i, h in enumerate(r['path_through_other_addresses'], 1):
                out.append(f"| `{f['wallet'][:12]}…` | {i} | {DAY(h['t'])} | {int(h['raw']) / 10 ** int(h['decimals'] or 0):,.6f} {h['token']} | {h['chain']} | `{h['source']}` | `{h['target']}` | {h['level']} | `{h['tx']}` |")
    out += ['', '## Exits', '', 'Services where the exit walks of these files stop. Stops are the last point publicly observed: the walk does not cross a platform\'s internal ledger.', '', '| Service, by the label table | Files |', '|---|---:|']
    out += [f'| {name} | {n} |' for name, n in services.most_common(15)]
    stops = Counter(k for f in d['files'] for k, _ in f.get('cashout_stops', []))
    out += ['', 'Stop reasons on the exit side, count of files holding each: ' + ', '.join(f'{k} {v}' for k, v in stops.most_common()) + '.', '', '## Limits', '', '- Light traces: depth 2, few addresses and flows, three chains beyond the account. A larger read can find more.', '- Attribution is by public labels. The service has confirmed none.', '- No order inside the service can be matched from public data: `OFFCHAIN_RECORD_REQUIRED`.', '- `results/CHANGENOW.md` gives the base rate from other services.']
    (results / 'CHANGENOW_DOSSIERS.md').write_text('\n'.join(out) + '\n')
    print(readings)


if __name__ == '__main__':
    main(sys.argv[1])
