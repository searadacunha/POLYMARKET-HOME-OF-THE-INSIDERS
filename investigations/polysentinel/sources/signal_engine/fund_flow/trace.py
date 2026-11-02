"""Follows one wallet's money in both directions, from its own API history and confirmed receipts. Read-only.

Usage: python -m signal_engine.fund_flow.trace WALLET [--scan-days N] [--out FILE] [--rpc N] [--http N]
"""
import argparse
import json
import os
import time
from pathlib import Path

from . import graph as graphs
from . import ledger, links, wallets
from .client import BudgetExhausted, ChainError, Client, FINAL_DEPTH
from .flows import PUSD, ZERO, label_of, tx_flow

STATE = Path(os.environ.get('SIGNAL_ENGINE_STATE', Path.home() / '.local/state/polysentinel-signal-engine')) / 'fund_flow'
MAX_RECEIPTS = 40
BLOCKS_PER_DAY = 43200  # about two seconds a block; only sizes the scan window, which then states its exact range


def wallet_block_near(client, timestamp):
    """A block at or before this time, by walking: only used to bound a scan."""
    head = client.head()
    now = client.block_time(head)
    return max(1, head - int(max(0, now - timestamp) / 2) - 2000)


def inspect_flow(client, tx, wallet, known_type, relations, found, stops):
    receipt = client.receipt(tx)
    if not receipt:
        stops.append(dict(tx=tx, state=links.INSUFFICIENT_EVIDENCE, basis='Receipt unavailable on the public nodes tried.'))
        return None
    flow = tx_flow(receipt, wallet)
    at = client.block_time(flow['block'])
    flow['at'] = at
    flow['final'] = client.head() - flow['block'] >= FINAL_DEPTH
    if not flow['success']:
        flow['note'] = 'Reverted transaction: moved nothing.'
        return flow
    if flow['unexplained_raw']:
        flow['note'] = 'The paths below do not add up to the net of this transaction; the difference is stated.'
    for path in flow['inflows']:
        origin = path['origin']
        if origin is None or path['unclear']:
            relations.append(links.relation(links.INSUFFICIENT_EVIDENCE, origin or 'UNKNOWN', wallet, tx=flow['tx'], log_index=path['log_index'], token=path['token'], raw=path['raw'], at=at, basis=path.get('reason') or 'Several transfers of this amount in one transaction: the pairing is not shown.'))
            stops.append(dict(tx=flow['tx'], log_index=path['log_index'], state=links.INSUFFICIENT_EVIDENCE, basis=path.get('reason') or 'Ambiguous pairing inside the transaction.'))
            continue
        label = label_of(origin)
        via = sorted({label_of(l['source'])['name'] for l in flow['logs'] if l['log_index'] in path['hops'] and label_of(l['source'])} - {(label or {}).get('name')}) + ([path['passed_through']] if path.get('passed_through') else [])
        relations.append(links.relation(links.SERVICE_INTERACTION if label and label['kind'] in ('bridge', 'exchange') else links.ONCHAIN_CONFIRMED, origin, wallet, tx=flow['tx'], log_index=path['log_index'], token=path['token'], raw=path['raw'], at=at, via=via,
                                        basis=(f"Paid another token through {path['passed_through']}, which kept no ERC-20 token, in one confirmed transaction." if path.get('passed_through') else f"Same amount followed through logs {path['hops']} of one confirmed transaction.") + (f" {label['name']}, per {label['source']}: a service paid, so the funder is not shown here." if label else ''), source_is_service=bool(label), alternatives=['The sender may be a service, an exchange or a bridge paying for someone else.'] if not label else []))
        found['origins'].append(dict(address=origin, name=label['name'] if label else None, raw=str(path['raw']), tx=flow['tx'], log_index=path['log_index'], at=at, hops=path['hops'], paid=path.get('paid'), passed_through=path.get('passed_through')))
    for path in flow['outflows']:
        destination = path['destination']
        label = label_of(destination) or label_of(path['first_receiver'])
        state = links.SERVICE_INTERACTION if label and label['kind'] in ('bridge', 'exchange') else links.ONCHAIN_CONFIRMED
        kind = (label or {}).get('kind')
        if kind in ('protocol', 'router', 'factory', 'collateral_contract'):
            continue
        relations.append(links.relation(state, wallet, destination, tx=flow['tx'], log_index=path['log_index'], token=path['token'], raw=path['raw'], at=at, basis=f"Reached {label['name']}, per {label['source']}." if label else f"Same amount followed through logs {path['hops']} of one confirmed transaction.",
                                        alternatives=['The receiver may be a service holding funds for someone else.'] if not label else []))
        found['destinations'].append(dict(address=destination, name=label['name'] if label else None, raw=str(path['raw']), tx=flow['tx'], log_index=path['log_index'], at=at, state=state))
    found['services'].update(flow['services'])
    return flow


def last_origin(origins):
    """How far back the latest funding can be shown. A service that paid is not called the funder."""
    if not origins:
        return None
    latest = origins[-1]
    upstream = latest.get('upstream') or {}
    if upstream.get('origin_sender'):
        return dict(address=upstream['origin_sender'], chain_id=upstream['origin_chain'], tx=upstream['origin_tx'], state=upstream['state'], via=latest['name'], is_service=False)
    return dict(address=latest['address'], chain_id=137, tx=latest['tx'], name=latest['name'], is_service=bool(latest['name']), state=links.SERVICE_INTERACTION if latest['name'] else links.ONCHAIN_CONFIRMED, funder_shown=not latest['name'], upstream_state=upstream.get('state'))


def trace_wallet(client, wallet, scan_days=None, activity_pages=3, follow_bridges=True, max_receipts=MAX_RECEIPTS):
    wallet = wallet.lower()
    started = time.time()
    identity = wallets.classify_wallet(client, wallet)
    relations, stops, errors = [], [], []
    found = dict(origins=[], destinations=[], services=set())
    flows = []
    report = dict(schema='fund-flow-1', chain_id=137, wallet=identity, shadow_mode=True, ownership=links.OWNERSHIP, not_a_profit=True)
    try:
        history = ledger.activity(client, wallet, activity_pages)
        rows = history['rows']
        cash = ledger.cash_from_activity(rows)
        cash.update(history_complete=history['complete'], rows=len(rows), first_activity=min((r['timestamp'] for r in rows), default=None), last_activity=max((r['timestamp'] for r in rows), default=None))
        report['cash_per_activity_api'] = cash
        money = [r for r in rows if r['type'] in ('DEPOSIT', 'WITHDRAWAL') and r.get('transaction_hash')]
        chosen = [r['transaction_hash'] for r in money][-max_receipts:]
        report['flows_examined'] = dict(listed=len(money), examined=len(set(chosen)), capped=len(money) > max_receipts)
        if scan_days:
            end = client.head()
            start = wallet_block_near(client, (rows[0]['timestamp'] if rows else time.time()) - scan_days * 86400)
            needed = 2 * ((end - start) // ledger.CHUNK_BLOCKS + 1) + 8
            if needed > .7 * (client.rpc_limit - client.rpc_used):
                report['balance_from_logs'] = dict(status='NOT_SCANNED', estimated_requests=needed, budget_left=client.rpc_limit - client.rpc_used, reason='A log scan of this wallet would pass the request budget; public nodes serve under 10,000 blocks a call.')
            else:
                opening, closing = ledger.balances(client, wallet, hex(start - 1)), ledger.balances(client, wallet, hex(end))
                scan = ledger.scan_collateral(client, wallet, start, end)
                report['balance_from_logs'] = dict(block_start=start, block_end=end, transfers=len(scan['transfers']), complete=scan['complete'], gaps=scan['gaps'], tokens=ledger.reconcile_chain(scan['transfers'], wallet, opening, closing))
                counterparties = {t['tx'] for t in scan['transfers'] if not label_of(t['source']) and not label_of(t['target']) and t['source'] != ZERO and t['target'] != ZERO}
                chosen = sorted(set(chosen) | counterparties)[:max_receipts]
                report['flows_examined'].update(from_scan=len(counterparties), examined=len(set(chosen)))
        report['balances_now'] = ledger.balances(client, wallet)
        if cash.get('computed_balance') is not None and report['balances_now']:
            onchain = (report['balances_now']['pUSD'] + report['balances_now']['USDC.e'] + report['balances_now']['USDC']) / 1e6
            report['residual_api_vs_chain'] = dict(onchain_collateral=onchain, api_computed=cash['computed_balance'], residual=onchain - cash['computed_balance'], applies=history['complete'], note='Only meaningful with the whole history; fees and unlisted transfers land here.')
        for tx in dict.fromkeys(chosen):
            flow = inspect_flow(client, tx, wallet, identity['type'], relations, found, stops)
            if flow:
                flows.append(flow)
        if identity['type'] == wallets.PROXY:
            sample = [client.rpc('eth_getTransactionByHash', [f['tx']]) for f in flows[:6]]
            identity.update(wallets.resolve_proxy_signer(client, wallet, [s for s in sample if s]))
        if follow_bridges:
            asked = 0
            for origin in found['origins']:
                if asked >= 6:
                    break
                if label_of(origin['address']):
                    answer = links.relay_origin_from_payout(client, origin['tx'], origin['at'], wallet, origin['raw']) or links.relay_fill_origin(client, origin['tx'], wallet)
                    relations += answer.pop('relations', [])
                    origin['upstream'] = answer
                else:
                    answer = links.bridge_upstream(client, origin['address'], int(origin['raw']), origin['at'])
                    relations += answer.pop('relations', [])
                    origin['upstream'] = answer
                asked += 1
            seen = set()
            for flow in flows:
                for order in flow['events']['orders']:
                    if order['order_id'] not in seen and len(seen) < 6:
                        seen.add(order['order_id'])
                        answer = links.relay_order_status(client, order)
                        answer.update(tx=flow['tx'], log_index=order['log_index'], service=order['service'], depositor=order['depositor'], raw=str(order['raw']))
                        stops.append(answer)
    except (BudgetExhausted, ChainError) as exc:
        errors.append(f'{type(exc).__name__}: {str(exc)[:200]}')
    positions = None
    try:
        status, body = client.get_json('https://data-api.polymarket.com/v2/positions', dict(user=wallet, limit=100))
        if status == 200 and isinstance(body, dict):
            data = body.get('data', [])
            positions = dict(open_rows=len(data), capped=len(data) >= 100, current_value=sum(float(p.get('current_value') or 0) for p in data))
    except (BudgetExhausted, ChainError) as exc:
        errors.append(f'{type(exc).__name__}: {str(exc)[:200]}')
    known = {wallet: 'STUDIED_WALLET'}
    control = [dict(owner=o, wallet=wallet, basis=identity['signer_status']) for o in identity.get('owners', []) if o != wallet]
    if identity.get('signer'):
        control.append(dict(owner=identity['signer'], wallet=wallet, basis=identity['signer_status']))
    built = graphs.build_graph(relations, known)
    report.update(flows=flows, relations=relations, graph=built, clusters=graphs.clusters(built, control), funding=found['origins'], withdrawals=found['destinations'], services=sorted(found['services']), trace_stops=stops, positions=positions,
                  errors=errors, requests=dict(rpc=client.rpc_used, http=client.http_used), seconds=time.time() - started)
    report['last_demonstrable_origin'] = last_origin(found['origins'])
    report['last_demonstrable_destination'] = found['destinations'][-1] if found['destinations'] else None
    return report


def dossier_section(report):
    """What an investigation file shows for one wallet: both directions, the level of each relation, and where the trail stops."""
    wallet = report['wallet']['address']
    edges = report['relations']
    keep = ('state', 'source', 'source_is_service', 'funder_shown', 'target', 'chain_id', 'tx', 'log_index', 'token', 'raw', 'raw_meaning', 'received_raw', 'payout_tx', 'order_id', 'at', 'basis', 'alternatives', 'via', 'url')
    return dict(wallet=wallet, type=report['wallet']['type'], signer_status=report['wallet']['signer_status'], owners=report['wallet']['owners'], signer=report['wallet'].get('signer'), wallet_evidence=report['wallet']['evidence'],
                incoming=[{k: e.get(k) for k in keep} for e in edges if e['target'] == wallet], outgoing=[{k: e.get(k) for k in keep} for e in edges if e['source'] == wallet], upstream=[{k: e.get(k) for k in keep} for e in edges if wallet not in (e['source'], e['target'])],
                last_demonstrable_origin=report.get('last_demonstrable_origin'), last_demonstrable_destination=report.get('last_demonstrable_destination'), services=report['services'], wallet_links=report['clusters'], trace_stops=report['trace_stops'],
                accounting=dict(api=report.get('cash_per_activity_api'), balances_now=report.get('balances_now'), residual=report.get('residual_api_vs_chain'), logs=report.get('balance_from_logs'), flows_examined=report.get('flows_examined')), positions=report.get('positions'), errors=report['errors'],
                shadow_mode=True, not_a_profit=True, ownership=links.OWNERSHIP)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('wallet')
    p.add_argument('--scan-days', type=float, default=None, help='Also scan transfers from this many days before the first activity')
    p.add_argument('--rpc', type=int, default=300)
    p.add_argument('--http', type=int, default=60)
    p.add_argument('--pages', type=int, default=3)
    p.add_argument('--out')
    a = p.parse_args()
    client = Client(a.rpc, a.http, ledger=STATE / 'requests.jsonl')
    try:
        result = trace_wallet(client, a.wallet, a.scan_days, a.pages)
    finally:
        client.close()
    text = json.dumps(result, indent=1, sort_keys=True, ensure_ascii=False, default=str)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text)
    print(text if not a.out else json.dumps(dict(out=a.out, requests=result['requests'], errors=result['errors'])))


if __name__ == '__main__':
    main()
