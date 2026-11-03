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
from gf import bridges, env, explorer, labels, proof
from gf.solana import Solana
from gf.events import rough_usd
from gf.net import BudgetSpent, Net, Refused

env.redirect_temp()
HERE = Path(__file__).resolve().parents[1].parent
SOURCES = Path.home() / 'Projects/PolySentinel-ChangeNOW-outflows/data/attribution_sources.csv'
SEVEN_DAYS = 7 * 86400
THIRTY_DAYS = 30 * 86400
RELAY_DEPOSITORY = '0x4cd00e387622c35bddb9b4c962c136462338bc31'


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


def into_account(edges, listed, recipient, wallet, since):
    """Moves from this key into the account after the payment: a deposit path, a proved bridge hop, or a listed transfer. The key is the wallet's owner, so its presence in the walk says nothing by itself. Money is fungible: this shows order and amounts, never that these coins paid for a bet."""
    out = []
    for e in edges:
        if e.get('direction') != 'funding' or (e.get('timestamp') or 0) < since or e.get('to') != wallet:
            continue
        usd = rough_usd(e)
        if e['role'] == 'deposit_path' and e.get('from') == recipient:
            out.append(dict(kind='deposit_path', t=e['timestamp'], usd=usd, tx=e['transaction_hash'], level=e.get('level'), token=e.get('token')))
        elif e['role'] == 'bridge_payout' and e.get('note'):
            try:
                hop = json.loads(e['note'])
            except ValueError:
                continue
            if (hop.get('sender') or '').lower() == recipient and hop.get('proof') is True:
                out.append(dict(kind='proved_bridge', t=e['timestamp'], usd=usd, tx=e['transaction_hash'], level=e.get('level'), token=e.get('token')))
        elif e['role'] in ('transfer', 'internal_to_dossier') and e.get('from') == recipient:
            out.append(dict(kind='direct_transfer', t=e['timestamp'], usd=usd, tx=e['transaction_hash'], level=e.get('level'), token=e.get('token')))
    seen = {x['tx'] for x in out}
    for x in listed:
        if x['tx'] not in seen and x['to'] == wallet:
            out.append(dict(kind='listed_transfer', t=x['t'], usd=int(x['raw']) / 10 ** int(x['decimals'] or 0) if x['token'] in ('USDC', 'USDC.e', 'USDT', 'pUSD', 'DAI') else 0.0, tx=x['tx'], level=x['level'], token=x['token']))
    return sorted(out, key=lambda x: x['t'])


def moves_of(edges):
    """Every move a walk read, as from, to, time. A proved bridge hop counts as a move across chains. An edge touching a shared address is left out, so no path crosses a service."""
    out = []
    for e in edges:
        if e.get('other_cls') in (labels.SERVICE, labels.HUB, labels.CONTRACT, labels.UNREAD) and e['role'] not in ('bridge_payout', 'bridge_deposit'):
            continue
        source, target = e.get('from'), e.get('to')
        if e['role'] in ('bridge_payout', 'bridge_deposit'):
            try:
                hop = json.loads(e.get('note') or '{}')
            except ValueError:
                continue
            if hop.get('proof') is not True:
                continue
            low = lambda a: a.lower() if a and a.startswith('0x') else a
            source, target = (low(hop.get('sender')) or source, target) if e['role'] == 'bridge_payout' else (source, low(hop.get('recipient')) or target)
        elif e['role'] not in ('transfer', 'deposit_path', 'withdrawal_path', 'internal_to_dossier'):
            continue
        if source and target and e.get('timestamp'):
            out.append((source, target, e['timestamp'], e))
    return out


def path_to_account(edges, start, wallet, since, max_hops=4):
    """Shortest chain of moves from this key to the account, each no earlier than the last, all after the payment. In the files' own edges, so no new read. Money is fungible: this shows order and amounts, never the same coins."""
    moves = moves_of(edges)
    frontier, best = [(start, since, [])], {start: since}
    for _ in range(max_hops):
        following = []
        for address, after, trail in frontier:
            for source, target, t, e in moves:
                if source != address or t < after:
                    continue
                step = trail + [dict(source=source, target=target, chain=e['chain_id'], tx=e['transaction_hash'], token=e.get('token'), raw=e['raw_amount'], decimals=e.get('decimals'), t=t, level=e.get('level'), role=e['role'], usd=rough_usd(e))]
                if target == wallet:
                    return step
                if t < best.get(target, float('inf')):
                    best[target] = t
                    following.append((target, t, step))
        frontier = following
    return None


def next_hop(net, sol, e, chain):
    """Where the key's money went next: the label or the size of the next address, and the bridge's far side when the same id can be read. A bridge's own record is a pointer until proof reads it on both chains."""
    info = labels.classify(net, e['to'], chain)
    out = dict(to=e['to'], token=e['token'], raw=e['raw_amount'], decimals=e['decimals'], t=e['timestamp'], tx=e['transaction_hash'], level=e['level'], usd_rough=round(rough_usd(e), 2), next_class=info.get('cls'), next_label=(info.get('label') or {}).get('name'))
    if (info.get('label') or {}).get('name', '').startswith('Relay') or e['to'] == RELAY_DEPOSITORY:
        record = bridges.relay_record(net, e['transaction_hash'])
        if record:
            recipient = (record.get('recipient') or '')
            out['bridge'] = dict(id=record.get('id'), recipient=recipient.lower() if recipient.startswith('0x') else recipient, destination_chain=record.get('destination_chain'), in_txs=record.get('in_txs'), out_txs=record.get('out_txs'), proof=bridges.relay_proof(net, record, sol))
    return out


def dossier(net, sol, wallet, hits, table):
    case = 'cn-' + wallet[:12]
    path = env.data_root() / 'wallets' / case / 'trace.json'
    trace = json.loads(path.read_text()) if path.exists() else None
    out = dict(wallet=wallet, case=case, trace_read=bool(trace), rows=[])
    deposits = (trace or {}).get('account', {}).get('deposits') or []
    origins = {p.get('origin') for d in deposits for p in d['paths']}
    edges = (trace or {}).get('edges') or []
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
            row['outflows_within_7_days'] = [next_hop(net, sol, e, int(hit['chain'])) for e in sorted(soon, key=lambda x: -rough_usd(x))[:6]]
            row['to_wallet_or_a_deposit_origin'] = [dict(to=e['to'], token=e['token'], raw=e['raw_amount'], decimals=e['decimals'], t=e['timestamp'], tx=e['transaction_hash'], level=e['level']) for e in to_wallet[:8]]
        except Refused as exc:
            row['recipient_history'] = dict(status='READ_FAILED', error=str(exc)[:160])
            row['to_wallet_or_a_deposit_origin'] = []
        into = into_account(edges, row.get('to_wallet_or_a_deposit_origin') or [], hit['recipient'], wallet, hit['first_ts'])
        known = {x['tx'] for x in into}
        into += [dict(kind='proved_bridge_from_key', t=h['t'], usd=h['usd_rough'], tx=h['tx'], level=h['level'], token=h['token']) for h in row.get('outflows_within_7_days', []) if (h.get('bridge') or {}).get('recipient') == wallet and h['bridge'].get('proof') is True and h['tx'] not in known]
        into.sort(key=lambda x: x['t'])
        row['into_account_after_payment'] = into[:8]
        total = sum(x['usd'] for x in into if x['t'] <= hit['first_ts'] + THIRTY_DAYS)
        row['usd_into_account_30_days'] = round(total, 2)
        path = path_to_account(edges, hit['recipient'], wallet, hit['first_ts']) if not into and trace else None
        row['path_through_other_addresses'] = path
        if not trace:
            row['funding_reading'] = 'NOT_TRACED'
        elif hit['form'] == 'itself' and int(hit['chain']) == 137:
            row['funding_reading'] = 'PAYMENT_LANDS_ON_THE_TRADING_ADDRESS'
        elif path:
            row['funding_reading'] = 'PATH_THROUGH_OTHER_ADDRESSES_AFTER_PAYMENT'
        elif not into:
            row['funding_reading'] = 'NO_PATH_FOUND_IN_WHAT_WAS_READ'
        elif total >= .5 * float(hit['usd'] or 0):
            row['funding_reading'] = 'KEY_FUNDS_ACCOUNT_AFTER_PAYMENT'
        else:
            row['funding_reading'] = 'KEY_PAYS_LESS_THAN_HALF_OR_LATER'
        out['rows'].append(row)
    if trace:
        account = trace['account']
        out.update(history_complete=account.get('history_complete'), first_trade=(account.get('first_trade') or {}).get('timestamp'), deposits=len(deposits), deposit_origins=sorted(o for o in origins if o), withdrawals=len(account.get('withdrawals') or []), mode=trace.get('mode'), cashout_stops=Counter(s['reason'].split(':')[0] for s in trace['stops'] if s['direction'] == 'cashout').most_common(), cashout_services=sorted({s.get('name') for s in trace['stops'] if s['direction'] == 'cashout' and s.get('name')}), funding_stops=Counter(s['reason'].split(':')[0] for s in trace['stops'] if s['direction'] == 'funding').most_common())
    return out


def main(out):
    budget = next((int(a.split('=', 1)[1]) for a in sys.argv[2:] if a.startswith('--budget=')), 1500)
    net = Net(budget=budget)
    sol = Solana(net)
    table = attribution()
    hits = {}
    for line in (HERE / 'results/changenow/cn_polymarket_hits.jsonl').read_text().splitlines():
        h = json.loads(line)
        hits.setdefault(h['wallet'], []).append(h)
    files = []
    try:
        for wallet, rows in hits.items():
            files.append(dossier(net, sol, wallet, rows, table))
            print(wallet[:12], [r.get('funding_reading') for r in files[-1]['rows']], net.calls, flush=True)
    except BudgetSpent:
        print('budget spent at', len(files), flush=True)
    summary = dict(wallets=len(files), of=len(hits), by_reading=Counter(r['funding_reading'] for f in files for r in f['rows']), payments_found=sum(r['payment'].get('found') is True for f in files for r in f['rows']), payments_not_found=sum(r['payment'].get('found') is False for f in files for r in f['rows']), payments_unread=sum(r['payment'].get('found') is None for f in files for r in f['rows']), sources={s: label_view(s, table) for s in sorted({h['first_source'] for rows in hits.values() for h in rows})}, calls=net.calls)
    Path(out).write_text(json.dumps(dict(summary=summary, files=files), indent=0, default=dict))
    print(json.dumps(summary, default=dict)[:800], flush=True)


if __name__ == '__main__':
    main(sys.argv[1])
