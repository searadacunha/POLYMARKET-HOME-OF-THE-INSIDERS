"""A wallet's cash, computed twice: from transfer logs against on-chain balances, and from the activity API.

Neither figure is a profit. A deposit is money in, a withdrawal is money out, and the balance sheet below
says only how much collateral moved. What the two sides cannot explain stays visible as a residual.
"""
from collections import defaultdict

from .client import ChainError
from .flows import COLLATERAL, POL_SYSTEM, TRANSFER, transfers
from .keccak import selector, word

CHUNK_BLOCKS = 9000
SIGNS = dict(SPLIT=-1, MERGE=1, REDEEM=1, DEPOSIT=1, WITHDRAWAL=-1, REWARD=1, MAKER_REBATE=1, TAKER_REBATE=1, REFERRAL_REWARD=1, YIELD=1, CONVERSION=0)
KEPT_FIELDS = ('type', 'timestamp', 'usdc_size', 'size', 'side', 'transaction_hash', 'condition_id', 'token_id', 'price')  # the API's name, bio and image stay out


def balances(client, wallet, block='latest'):
    out = {}
    data = selector('balanceOf(address)') + word(wallet).hex()
    for token, symbol in COLLATERAL.items():
        out[symbol] = int(client.call(token, data, block) or '0x0', 16)
    out['POL'] = int(client.rpc('eth_getBalance', [wallet, block]), 16)
    return out


def scan_collateral(client, wallet, start, end, chunk=CHUNK_BLOCKS):
    """Every collateral transfer naming the wallet in a block range. A failed window is reported as a gap, never skipped quietly."""
    wallet = wallet.lower()
    padded = '0x' + word(wallet).hex()
    seen, gaps = {}, []
    tokens = sorted(COLLATERAL)
    for first in range(start, end + 1, chunk):
        last = min(first + chunk - 1, end)
        for filters in ([TRANSFER, padded], [TRANSFER, None, padded]):
            try:
                logs = client.rpc('eth_getLogs', [dict(fromBlock=hex(first), toBlock=hex(last), address=tokens, topics=filters)])
            except ChainError as exc:
                gaps.append(dict(start=first, end=last, error=str(exc)[:120]))
                continue
            for t in transfers(dict(logs=logs)):
                seen[t['chain_id'], t['tx'], t['log_index']] = t
    return dict(transfers=sorted(seen.values(), key=lambda t: (t['block'], t['log_index'])), start=start, end=end, gaps=gaps, complete=not gaps)


def by_log_key(items):
    """Chain, transaction and log index: several transfers of one transaction stay several."""
    return {(t['chain_id'], t['tx'], t['log_index']): t for t in items}


def reconcile_chain(moved, wallet, opening, closing):
    """Opening balance plus logs against closing balance, per token, in raw units. Exact, or a stated residual."""
    wallet = wallet.lower()
    out = {}
    for token, symbol in COLLATERAL.items():
        received = sum(t['raw'] for t in moved if t['token'] == token and t['target'] == wallet and t['source'] != wallet)
        sent = sum(t['raw'] for t in moved if t['token'] == token and t['source'] == wallet and t['target'] != wallet)
        out[symbol] = dict(opening=opening[symbol], received=received, sent=sent, computed_closing=opening[symbol] + received - sent, closing=closing[symbol], residual_raw=closing[symbol] - (opening[symbol] + received - sent))
    return out


def activity(client, wallet, pages=5, limit=500):
    """Stored without the API's personal profile fields. A capped history says it is capped."""
    rows, cursor, complete = [], None, False
    for _ in range(pages):
        params = dict(user=wallet, limit=limit, sort_by='TIMESTAMP', sort_direction='ASC', exclude_deposits_withdrawals='false')
        if cursor:
            params['cursor'] = cursor
        status, body = client.get_json('https://data-api.polymarket.com/v2/activity', params)
        if status != 200 or not isinstance(body, dict):
            raise ChainError(f'Activity API answered {status}')
        rows += [{k: r.get(k) for k in KEPT_FIELDS} for r in body.get('data', [])]
        cursor = (body.get('pagination') or {}).get('next_cursor')
        if not cursor:
            complete = True
            break
    return dict(rows=rows, complete=complete)


def cash_from_activity(rows):
    """The API's own account of cash, by type. An unknown type is counted apart instead of being signed by guess."""
    by_type, unknown = defaultdict(float), defaultdict(int)
    for r in rows:
        kind = r['type']
        size = float(r.get('usdc_size') or 0)
        if kind == 'TRADE':
            by_type['TRADE_' + str(r.get('side'))] += size * (1 if r.get('side') == 'SELL' else -1)
        elif kind in SIGNS:
            by_type[kind] += SIGNS[kind] * size
        else:
            unknown[kind] += 1
    trading = sum(v for k, v in by_type.items() if k not in ('DEPOSIT', 'WITHDRAWAL'))
    return dict(by_type=dict(by_type), unknown_types=dict(unknown), deposits=by_type.get('DEPOSIT', 0.0), withdrawals=-by_type.get('WITHDRAWAL', 0.0), computed_balance=sum(by_type.values()), trading_cash_flow=trading,
                note='Trading cash flow counts buys, sales, redemptions and rewards in cash. Open positions are not valued here, so it is not a profit.')


def consolidate(moved_by_wallet):
    """Several wallets as one account: a transfer between two of them is one internal move, never an inflow and an outflow."""
    members = {w.lower() for w in moved_by_wallet}
    unique = by_log_key(t for items in moved_by_wallet.values() for t in items)
    internal = [t for t in unique.values() if t['source'] in members and t['target'] in members]
    external_in = [t for t in unique.values() if t['target'] in members and t['source'] not in members]
    external_out = [t for t in unique.values() if t['source'] in members and t['target'] not in members]
    return dict(members=sorted(members), internal_raw=sum(t['raw'] for t in internal), internal_count=len(internal), received_raw=sum(t['raw'] for t in external_in), sent_raw=sum(t['raw'] for t in external_out))
