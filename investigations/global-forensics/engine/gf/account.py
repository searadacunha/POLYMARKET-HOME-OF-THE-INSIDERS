"""One Polymarket account from its address alone: control, deposits, withdrawals, positions, and the seeds of the trace.

A deposit's funder never touches the wallet (it pays USDC.e into pUSD, which mints to the wallet), so each deposit and withdrawal is read
from its whole receipt with PolySentinel's log-by-log reader, unmodified. Control is read at a historical block as well as today: an owner
today is not proof of an owner then. A relayer submitting a transaction says nothing about who owns the wallet.
"""
import sys
from pathlib import Path

from . import pm, proof
from .keccak import selector
from .net import Refused

ZERO = '0x' + '0' * 40


def _fund_flow():
    here = Path(__file__).resolve()
    for p in list(here.parents) + [Path.home() / 'Projects/Polymarket-Home-of-the-Insiders']:
        path = p / 'investigations/polysentinel/sources'
        if (path / 'signal_engine/fund_flow/flows.py').exists():
            sys.dont_write_bytecode = True
            if str(path) not in sys.path:
                sys.path.insert(0, str(path))
            if 'httpx' not in sys.modules:
                import types
                fake = types.ModuleType('httpx')
                fake.HTTPError = Exception
                fake.Client = object
                sys.modules['httpx'] = fake
            from signal_engine.fund_flow import flows
            return flows
    raise FileNotFoundError('fund_flow not found')


def control(net, wallet, block=None):
    """Owner read at a block. Deposit wallets answer owner(), Safes getOwners(), an EOA has no code. Anything else stays SIGNER_UNKNOWN."""
    tag = hex(block) if block else 'latest'
    code = net.rpc('eth_getCode', [wallet, tag], 137)[0]
    out = dict(wallet=wallet, block=block or 'latest', has_code=code not in ('0x', '0x0', None))
    if not out['has_code']:
        out.update(form='EOA_OR_NOT_DEPLOYED', owners=[wallet] if block is None else [], signer_status='ADDRESS_IS_ITS_OWN_KEY' if block is None else 'NOT_DEPLOYED_AT_BLOCK')
        return out
    if code.lower().startswith('0xef0100'):
        out.update(form='EIP7702_EOA', owners=[wallet], signer_status='ADDRESS_IS_ITS_OWN_KEY')
        return out
    for signature, form in (('owner()', 'DEPOSIT_WALLET_OR_OWNABLE'), ('getOwners()', 'SAFE')):
        try:
            value = net.rpc('eth_call', [dict(to=wallet, data=selector(signature)), tag], 137)[0]
        except Refused:
            continue
        if not value or value == '0x':
            continue
        if form == 'SAFE':
            raw = value[2:]
            if len(raw) >= 128:
                count = int(raw[64:128], 16)
                if 0 < count <= 64:
                    out.update(form=form, owners=['0x' + raw[128 + i * 64 + 24:128 + (i + 1) * 64].lower() for i in range(count)], signer_status='OWNERS_READ_ONCHAIN')
                    return out
        elif len(value) >= 42 and int(value, 16):
            out.update(form=form, owners=['0x' + value[-40:].lower()], signer_status='OWNERS_READ_ONCHAIN')
            return out
    out.update(form='CLONE_OR_OTHER', owners=[], signer_status='SIGNER_UNKNOWN')
    return out


def read_money(net, wallet, tx):
    """Paths of one deposit or withdrawal. Reverted or unreadable transactions come back marked, never as zero."""
    flows = _fund_flow()
    moves, record = proof.read_tx(net, 137, tx)
    receipt = net.rpc('eth_getTransactionReceipt', [tx], 137)[0]
    flow = flows.tx_flow(receipt, wallet)
    return flow, moves, record


def balances_now(net, wallet):
    """Collateral held today, read from a node, and open positions from the API. Valued by the API, so it is a snapshot, not a realized figure."""
    out = {}
    for name, token in (('pUSD', '0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb'), ('USDC.e', '0x2791bca1f2de4661ed88a30c99a7a9449aa84174'), ('USDC', '0x3c499c542cef5e3811e1192ce70d8cc03d5c3359')):
        value = net.rpc('eth_call', [dict(to=token, data=selector('balanceOf(address)') + wallet[2:].rjust(64, '0')), 'latest'], 137, cache=False)[0]
        out[name] = int(value, 16) / 1e6 if value not in (None, '0x') else None
    body, _ = net.get(pm.DATA + '/v2/positions', dict(user=wallet, limit=100), pause=.15, fresh=True)
    rows = body.get('data') or [] if isinstance(body, dict) else []
    out['open_positions'] = dict(rows=len(rows), capped=len(rows) >= 100, current_value=sum(float(p.get('current_value') or 0) for p in rows))
    return out


def load(net, wallet, read_receipts=True, max_rows=50_000, max_money=None):
    """max_money keeps the earliest deposits and withdrawals of a very active account. What it drops is counted in `money_dropped`."""
    wallet = wallet.lower()
    history = pm.activity(net, wallet, max_rows=max_rows)
    rows = history['rows']
    tx_of = lambda r: r.get('transaction_hash') or r.get('transactionHash')
    money = [r for r in rows if r.get('type') in ('DEPOSIT', 'WITHDRAWAL') and tx_of(r)]
    out = dict(wallet=wallet, history_complete=history['complete'], rows=len(rows), origins=history['origins'], first_activity=rows[0]['timestamp'] if rows else None, last_activity=rows[-1]['timestamp'] if rows else None, deposits=[], withdrawals=[], unread=[], first_trade=next((r for r in rows if r.get('type') == 'TRADE'), None), types={})
    for r in rows:
        out['types'][r.get('type')] = out['types'].get(r.get('type'), 0) + 1
    out['control_latest'] = control(net, wallet)
    try:
        out['balances_now'] = balances_now(net, wallet)
    except Refused as exc:
        out['balances_now'] = dict(error=str(exc)[:160])
    out['money_listed'] = len(money)
    out['money_dropped'] = 0
    if max_money and len(money) > max_money:
        out['money_dropped'] = len(money) - max_money
        money = money[:max_money]
    if not read_receipts:
        return out, rows
    first_block = None
    for r in money:
        tx = tx_of(r)
        try:
            flow, moves, record = read_money(net, wallet, tx)
        except Refused as exc:
            out['unread'].append(dict(tx=tx, type=r['type'], error=str(exc)[:160]))
            continue
        first_block = first_block or record['block_number']
        item = dict(tx=tx, block=record['block_number'], block_hash=record['block_hash'], at=record['timestamp'], submitter=record['submitter'], api_usd=r.get('usdc_size') or r.get('usdcSize'), level=moves[0]['level'] if moves else None, second_host=record['second_host'], success=flow['success'], unexplained_raw=flow['unexplained_raw'], paths=flow['inflows'] if r['type'] == 'DEPOSIT' else flow['outflows'], services=flow['services'], conversions=flow['conversions'])
        out['deposits' if r['type'] == 'DEPOSIT' else 'withdrawals'].append(item)
    if first_block:
        out['control_at_first_money'] = control(net, wallet, first_block)
    return out, rows
