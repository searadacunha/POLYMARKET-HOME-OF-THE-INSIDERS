"""Case data for one wallet: complete activity, positions by market, cash account, funding and exits. Public reads only, aliases never stored.

Usage: case_build.py SLUG. Re-running reads the cache, so a stopped run resumes. Uses the fund-flow trace saved in evidence/traces/ when present.
"""
import gzip
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import identities
import net

ROOT = Path(__file__).resolve().parent.parent
KEPT = ('timestamp', 'type', 'side', 'size', 'usdc_size', 'price', 'title', 'outcome', 'outcome_index', 'slug', 'event_slug', 'condition_id', 'asset', 'transaction_hash')
UTC = lambda t: time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(t))
T_POST = 1792768669
BRIDGE = 'https://bridge.polymarket.com/status/'
net.RPC[56] = ('https://bsc.drpc.org', 'https://bsc-dataseed.bnbchain.org', 'https://1rpc.io/bnb')


def activity(wallet, max_pages=40):
    rows, cursor, complete = [], None, False
    for _ in range(max_pages):
        params = dict(user=wallet, limit=500, sort_by='TIMESTAMP', sort_direction='ASC', exclude_deposits_withdrawals='false')
        if cursor:
            params['cursor'] = cursor
        body = net.get('https://data-api.polymarket.com/v2/activity', params)
        if not isinstance(body, dict) or '_http_error' in body:
            raise RuntimeError(f'activity {wallet}: {body}')
        rows += [{k: r.get(k) for k in KEPT} for r in body.get('data', [])]
        cursor = (body.get('pagination') or {}).get('next_cursor')
        if not cursor:
            complete = True
            break
    return rows, complete


def positions(rows):
    """Bought, sold and redeemed per market outcome, as the API reports them. Split and merge are listed apart, never netted by guess."""
    book = defaultdict(lambda: defaultdict(float))
    meta = {}
    for r in rows:
        if r['type'] not in ('TRADE', 'REDEEM', 'SPLIT', 'MERGE', 'CONVERSION'):
            continue
        key = (r.get('title') or '', r.get('outcome') or '')
        meta[key] = dict(condition_id=r.get('condition_id'), slug=r.get('slug'), event_slug=r.get('event_slug'))
        size, cash = float(r.get('size') or 0), float(r.get('usdc_size') or 0)
        tag = r['side'].lower() if r['type'] == 'TRADE' else r['type'].lower()
        book[key][tag + '_shares'] += size
        book[key][tag + '_usd'] += cash
        book[key]['first'] = min(book[key].get('first') or r['timestamp'], r['timestamp'])
        book[key]['last'] = max(book[key].get('last') or 0, r['timestamp'])
        if r['timestamp'] < T_POST:
            book[key]['net_shares_before_article'] += size if tag == 'buy' else -size if tag == 'sell' else 0
    return [dict(title=k[0], outcome=k[1], **{a: round(b, 4) if isinstance(b, float) else b for a, b in v.items()}, **meta[k]) for k, v in sorted(book.items(), key=lambda kv: -kv[1].get('buy_usd', 0))]


def account(rows, complete, balances=None, open_value=None):
    """Cash per type. A realised result is stated only when history is complete, nothing is left on the wallet and no position stays open."""
    signs = dict(DEPOSIT=1, WITHDRAWAL=-1, REDEEM=1, REWARD=1, MAKER_REBATE=1, TAKER_REBATE=1, TIP=1, SPLIT=-1, MERGE=1, CONVERSION=1)
    totals, unknown = defaultdict(float), defaultdict(int)
    for r in rows:
        cash = float(r.get('usdc_size') or 0)
        if r['type'] == 'TRADE':
            totals['TRADE_' + r['side']] += cash if r['side'] == 'SELL' else -cash
        elif r['type'] in signs:
            totals[r['type']] += signs[r['type']] * cash
        else:
            unknown[r['type']] += 1
    deposits, withdrawals = totals.get('DEPOSIT', 0.0), -totals.get('WITHDRAWAL', 0.0)
    residual = sum(totals.values())
    closed = bool(complete and not unknown and open_value == 0 and abs(residual) < .01 and balances and not any(v for k, v in balances.items() if k != 'POL'))
    return dict(by_type={k: round(v, 6) for k, v in totals.items()}, unknown_types=dict(unknown), deposits=round(deposits, 6), withdrawals=round(withdrawals, 6), residual=round(residual, 6), history_complete=complete, account_closed=closed,
                net_cash_out_minus_in=round(withdrawals - deposits, 6) if closed else None,
                note='Net is withdrawals minus deposits on this wallet, only when the account is closed. Fees are inside the trade cash. Gas and any cost off this wallet are not counted.' if closed else 'Account not closed or not reconciled: no realised result stated.')


def evm_kind(address, chain=137):
    code = net.rpc('eth_getCode', [address, 'latest'], chain)
    if code in ('0x', None):
        return dict(kind='EOA', nonce=net.nonce(address, chain))
    if code.startswith('0xef0100'):
        return dict(kind='EIP7702_DELEGATED_EOA', delegate='0x' + code[8:48], nonce=net.nonce(address, chain))
    return dict(kind='CONTRACT', code_bytes=(len(code) - 2) // 2)


def block_at(chain, moment):
    low, high = 1, int(net.rpc('eth_blockNumber', [], chain), 16)
    for _ in range(45):
        if high - low <= 1:
            break
        mid = (low + high) // 2
        if net.block_time(mid, chain) < moment:
            low = mid
        else:
            high = mid
    return high


def inflows(address, chain, start, end, step):
    """Every ERC-20 transfer into this address on this chain in a time window. A failed call raises."""
    low, high = block_at(chain, start), block_at(chain, end)
    logs = []
    for s in range(low, high + 1, step):
        logs += net.rpc('eth_getLogs', [dict(fromBlock=hex(s), toBlock=hex(min(high, s + step - 1)), topics=[net.TRANSFER, None, net.pad(address)])], chain)
    out = []
    for l in logs:
        if len(l['topics']) == 3 and l['data'] != '0x':
            block = int(l['blockNumber'], 16)
            out.append(dict(chain=chain, tx=l['transactionHash'], log_index=int(l['logIndex'], 16), block=block, at=net.block_time(block, chain), token=l['address'].lower(), source='0x' + l['topics'][1][-40:], raw=str(int(l['data'], 16))))
    return dict(chain=chain, blocks=[low, high], window=[start, end], rows=out)


STEPS = {137: 1500, 56: 4000, 1: 1000, 42161: 9000, 8453: 5000, 10: 5000}


def bridge_records(address):
    body = net.get(BRIDGE + address, dict(limit=50))
    return body.get('transactions', []) if isinstance(body, dict) else []


def upstream_of_bridge_address(address, deposit_at):
    """The bridge record names a chain. The address is the same on every EVM chain, so that chain's own logs show who paid it."""
    records = bridge_records(address)
    near = [r for r in records if abs(r.get('createdTimeMs', 0) / 1000 - deposit_at) <= 3 * 3600]
    chains = sorted({int(r['fromChainId']) for r in near if str(r.get('fromChainId')).isdigit() and int(r['fromChainId']) in STEPS}) or [137]
    found = []
    for chain in chains:
        try:
            found.append(inflows(address, chain, deposit_at - 2 * 3600, deposit_at + 120, STEPS[chain]))
        except RuntimeError as e:
            found.append(dict(chain=chain, error=str(e)[:200]))
    return dict(records_total=len(records), records_near=near, scans=found)


def relay_by_hash(tx):
    """Relay's public v2 route, retired on 24 Nov 2026 and throttled before that. Its answer is a service's record, checked against chain data where possible."""
    time.sleep(20)
    body = net.get('https://api.relay.link/requests/v2', dict(hash=tx), pause=2)
    out = []
    for q in (body.get('requests') or []) if isinstance(body, dict) else []:
        data, meta = q.get('data') or {}, (q.get('data') or {}).get('metadata') or {}
        out.append(dict(id=q.get('id'), status=q.get('status'), user=q.get('user'), recipient=q.get('recipient'), in_txs=[dict(chain=t.get('chainId'), hash=t.get('hash')) for t in data.get('inTxs') or []], out_txs=[dict(chain=t.get('chainId'), hash=t.get('hash')) for t in data.get('outTxs') or []],
                        currency_in=(meta.get('currencyIn') or {}).get('currency', {}).get('symbol'), amount_in=(meta.get('currencyIn') or {}).get('amountFormatted'), currency_out=(meta.get('currencyOut') or {}).get('currency', {}).get('symbol'), amount_out=(meta.get('currencyOut') or {}).get('amountFormatted'), out_chain=(meta.get('currencyOut') or {}).get('currency', {}).get('chainId')))
    return out


def build(slug):
    who = identities.IDS.get(slug) or dict(label=slug, address=identities.NOT_HIGHLIGHTED[slug], group='not_highlighted', basis=[identities.SHOT], level='ALIAS_EXACT_AND_SHARES')
    wallet = who['address']
    rows, complete = activity(wallet)
    (ROOT / 'evidence/activity').mkdir(parents=True, exist_ok=True)
    with gzip.GzipFile(ROOT / f'evidence/activity/{slug}.jsonl.gz', 'wb', mtime=0) as f:
        for r in rows:
            f.write((json.dumps(r, sort_keys=True) + '\n').encode())
    trace_path = ROOT / f'evidence/traces/{slug}.json'
    trace = json.loads(trace_path.read_text()) if trace_path.exists() else {}
    balances = trace.get('balances_now')
    open_value = (trace.get('positions') or {}).get('current_value')
    case = dict(slug=slug, label=who['label'], address=wallet, group=who['group'], identity_level=who['level'], identity_basis=who['basis'], wallet=trace.get('wallet'), ownership='OWNERSHIP_NOT_ESTABLISHED',
                first_activity=UTC(rows[0]['timestamp']) if rows else None, last_activity=UTC(rows[-1]['timestamp']) if rows else None, rows=len(rows), history_complete=complete,
                account=account(rows, complete, balances, open_value), balances_now=balances, open_positions=trace.get('positions'), positions=positions(rows),
                deposits=[dict(utc=UTC(r['timestamp']), at=r['timestamp'], usd=r['usdc_size'], tx=r['transaction_hash']) for r in rows if r['type'] == 'DEPOSIT'],
                withdrawals=[dict(utc=UTC(r['timestamp']), at=r['timestamp'], usd=r['usdc_size'], tx=r['transaction_hash']) for r in rows if r['type'] == 'WITHDRAWAL'],
                first_trade=next((dict(utc=UTC(r['timestamp']), at=r['timestamp'], title=r['title'], outcome=r['outcome'], side=r['side'], usd=r['usdc_size'], tx=r['transaction_hash']) for r in rows if r['type'] == 'TRADE'), None),
                funding_trace=trace.get('funding'), relations=trace.get('relations'), stops=trace.get('trace_stops'), trace_errors=trace.get('errors'))
    seen, up = set(), []
    for f in trace.get('funding') or []:
        address = f['address']
        if f.get('name') or (address, f['at'] // 3600) in seen:
            continue
        seen.add((address, f['at'] // 3600))
        up.append(dict(address=address, deposit_tx=f['tx'], deposit_at=f['at'], raw=f['raw'], kind=evm_kind(address), bridge=upstream_of_bridge_address(address, f['at'])))
    case['upstream'] = up
    case['owner_nonces'] = {}
    for owner in (trace.get('wallet') or {}).get('owners') or []:
        case['owner_nonces'][owner] = {name: net.nonce(owner, chain) for chain, name in ((137, 'polygon'), (1, 'ethereum'), (56, 'bsc'), (42161, 'arbitrum'), (8453, 'base'), (10, 'optimism'))}
    case['exits'] = [dict(w, relay=relay_by_hash(w['tx'])) for w in case['withdrawals']]
    out = ROOT / f'cases/{slug}.json'
    out.write_text(json.dumps(case, indent=1, ensure_ascii=False))
    print(slug, 'rows', len(rows), 'complete', complete, 'deposits', len(case['deposits']), 'withdrawals', len(case['withdrawals']), 'account', case['account']['net_cash_out_minus_in'], 'residual', case['account']['residual'], 'calls', net.Stats.calls)


if __name__ == '__main__':
    build(sys.argv[1])
