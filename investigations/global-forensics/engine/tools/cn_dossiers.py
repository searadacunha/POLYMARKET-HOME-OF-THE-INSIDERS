"""The 26 wallets that a ChangeNOW payout address reached, one by one: is the label sound, does the payment exist on a node, and did that money reach the trading account?

Usage: cn_dossiers.py <out.json> [--budget=N]. Reads hits from the join, traces from run_wallets (wallets_cn.json, --light). A payment only counts as funding when a walk of proved moves connects it to a deposit. Otherwise the file says what was seen and stops.
"""
import csv
import json
import sys
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gf import env, explorer, proof
from gf.net import BudgetSpent, Net, Refused

env.redirect_temp()
HERE = Path(__file__).resolve().parents[1].parent
SOURCES = Path.home() / 'Projects/PolySentinel-ChangeNOW-outflows/data/attribution_sources.csv'
SEVEN_DAYS = 7 * 86400


def attribution():
    out = {}
    with SOURCES.open() as f:
        for r in csv.DictReader(f):
            out.setdefault(r['address'].lower(), []).append(r)
    return out


def label_view(source, table):
    rows = table.get(source.lower(), [])
    lineages = sorted({r['lineage'] for r in rows})
    return dict(address=source, in_attribution_table=bool(rows), lineages=lineages, independent_lineages=len(lineages), names=sorted({r['label'] for r in rows})[:6])


def payment_read(net, hit):
    chain = int(hit['chain'])
    moves, record = proof.read_tx(net, chain, hit['first_tx'])
    source, recipient = hit['first_source'].lower(), hit['recipient'].lower()
    found = [m for m in moves if m['from'] == source and m['to'] == recipient]
    return dict(tx=hit['first_tx'], chain=chain, block=record['block_number'], status=record['status'], second_host=record.get('second_host'), level=found[0]['level'] if found else None, log_index=found[0].get('log_index') if found else None, token=found[0].get('token') if found else None, raw=found[0].get('raw_amount') if found else None, found=bool(found))


def outflows_after(net, recipient, chain, since):
    events, coverage = explorer.history(net, recipient, chain)
    later = [e for e in events if e['from'] == recipient and e.get('success', True) and int(e['raw_amount']) > 0 and (e.get('timestamp') or 0) >= since and (e.get('token_known') or e['kind'] != 'erc20')]
    later.sort(key=lambda e: e['timestamp'])
    return later, coverage


def dossier(net, wallet, hits, table):
    case = 'cn-' + wallet[:12]
    path = env.data_root() / 'wallets' / case / 'trace.json'
    trace = json.loads(path.read_text()) if path.exists() else None
    out = dict(wallet=wallet, case=case, trace_read=bool(trace), rows=[])
    deposits = (trace or {}).get('account', {}).get('deposits') or []
    origins = {p.get('origin') for d in deposits for p in d['paths']}
    edges = (trace or {}).get('edges') or []
    funding_addresses = {e['from'] for e in edges if e['direction'] == 'funding'} | {e['to'] for e in edges if e['direction'] == 'funding'}
    for hit in hits:
        row = dict(recipient=hit['recipient'], form=hit['form'], tier=hit['tier'], usd=hit['usd'], first_ts=hit['first_ts'], label=label_view(hit['first_source'], table), payment_before_first_trade=hit['payment_before_first_trade'])
        try:
            row['payment'] = payment_read(net, hit)
        except Refused as exc:
            row['payment'] = dict(found=None, error=str(exc)[:160])
        try:
            later, coverage = outflows_after(net, hit['recipient'], int(hit['chain']), hit['first_ts'])
            row['recipient_history'] = dict(status=coverage['status'], rows=coverage.get('rows'))
            soon = [e for e in later if e['timestamp'] <= hit['first_ts'] + SEVEN_DAYS]
            to_wallet = [e for e in later if e['to'] == wallet or e['to'] in origins]
            row['outflows_within_7_days'] = [dict(to=e['to'], token=e['token'], raw=e['raw_amount'], decimals=e['decimals'], t=e['timestamp'], tx=e['transaction_hash'], level=e['level']) for e in soon[:8]]
            row['to_wallet_or_a_deposit_origin'] = [dict(to=e['to'], token=e['token'], raw=e['raw_amount'], decimals=e['decimals'], t=e['timestamp'], tx=e['transaction_hash'], level=e['level']) for e in to_wallet[:8]]
        except Refused as exc:
            row['recipient_history'] = dict(status='READ_FAILED', error=str(exc)[:160])
            row['to_wallet_or_a_deposit_origin'] = []
        reached = bool(row.get('to_wallet_or_a_deposit_origin')) or hit['recipient'] in funding_addresses
        row['funding_reading'] = ('MONEY_FROM_RECIPIENT_REACHES_ACCOUNT' if reached else 'NO_PATH_FOUND_IN_WHAT_WAS_READ') if trace else 'NOT_TRACED'
        out['rows'].append(row)
    if trace:
        account = trace['account']
        out.update(history_complete=account.get('history_complete'), first_trade=(account.get('first_trade') or {}).get('timestamp'), deposits=len(deposits), deposit_origins=sorted(o for o in origins if o), withdrawals=len(account.get('withdrawals') or []), mode=trace.get('mode'), cashout_stops=Counter(s['reason'].split(':')[0] for s in trace['stops'] if s['direction'] == 'cashout').most_common(), cashout_services=sorted({s.get('name') for s in trace['stops'] if s['direction'] == 'cashout' and s.get('name')}), funding_stops=Counter(s['reason'].split(':')[0] for s in trace['stops'] if s['direction'] == 'funding').most_common())
    return out


def main(out):
    budget = next((int(a.split('=', 1)[1]) for a in sys.argv[2:] if a.startswith('--budget=')), 1500)
    net = Net(budget=budget)
    table = attribution()
    hits = {}
    for line in (HERE / 'results/changenow/cn_polymarket_hits.jsonl').read_text().splitlines():
        h = json.loads(line)
        hits.setdefault(h['wallet'], []).append(h)
    files = []
    try:
        for wallet, rows in hits.items():
            files.append(dossier(net, wallet, rows, table))
            print(wallet[:12], [r.get('funding_reading') for r in files[-1]['rows']], net.calls, flush=True)
    except BudgetSpent:
        print('budget spent at', len(files), flush=True)
    summary = dict(wallets=len(files), of=len(hits), by_reading=Counter(r['funding_reading'] for f in files for r in f['rows']), payments_found=sum(r['payment'].get('found') is True for f in files for r in f['rows']), payments_not_found=sum(r['payment'].get('found') is False for f in files for r in f['rows']), payments_unread=sum(r['payment'].get('found') is None for f in files for r in f['rows']), sources={s: label_view(s, table) for s in sorted({h['first_source'] for rows in hits.values() for h in rows})}, calls=net.calls)
    Path(out).write_text(json.dumps(dict(summary=summary, files=files), indent=0, default=dict))
    print(json.dumps(summary, default=dict)[:800], flush=True)


if __name__ == '__main__':
    main(sys.argv[1])
