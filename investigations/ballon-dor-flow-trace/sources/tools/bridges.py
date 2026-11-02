"""Resolve bridge steps found by the walk through each protocol's own public record, so a cross-chain link rests on an identifier and never on similar amounts or dates.
Writes state/bridges.json; every answer is cached and kept as evidence."""
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import hashlib
import evm
import net
import walk

STATE = net.ROOT / 'state'
CCTP_DOMAIN = {0: 'ethereum', 1: 'avalanche', 2: 'optimism', 3: 'arbitrum', 5: 'solana', 6: 'base', 7: 'polygon', 10: 'unichain', 11: 'linea', 13: 'sonic', 14: 'worldchain', 19: 'hyperevm'}
CHAIN_DOMAIN = {1: 0, 10: 2, 42161: 3, 8453: 6, 137: 7}
BRIDGE_WORDS = ('dln', 'debridge', 'cctp', 'tokenmessenger', 'stargate', 'across', 'spokepool', 'chainflip', 'swft', 'hyperliquid', 'hop ', 'layerzero', 'wormhole', 'mayan', 'portal', 'squid', 'lifi', 'li.fi', 'socket', 'bungee', 'orbiter', 'symbiosis', 'gas.zip', 'gaszip')


def debridge(tx):
    ids = net.get(f'https://dln.debridge.finance/v1.0/dln/tx/{tx}/order-ids', pause=.5).get('orderIds') or []
    out = []
    for oid in ids:
        o = net.get(f'https://dln.debridge.finance/v1.0/dln/order/{oid}', pause=.5)
        st = o.get('orderStruct') or o
        give, take = st.get('giveOffer') or {}, st.get('takeOffer') or {}
        out.append(dict(protocol='deBridge DLN', order_id=oid, state=o.get('status'), src_chain=give.get('chainId'), src_token=give.get('tokenAddress'), src_amount=give.get('amount'), dst_chain=take.get('chainId'), dst_token=take.get('tokenAddress'), dst_amount=take.get('amount'), maker_src=st.get('makerSrc'), receiver_dst=st.get('receiverDst'), taker_dst=st.get('allowedTakerDst'), source=f'https://dln.debridge.finance/v1.0/dln/order/{oid}'))
    return out


def cctp(tx, chain):
    domain = CHAIN_DOMAIN.get(chain)
    if domain is None:
        return []
    d = net.get(f'https://iris-api.circle.com/v2/messages/{domain}', dict(transactionHash=tx), pause=.5, accept=(400, 404))
    out = []
    for m in d.get('messages') or []:
        dec = m.get('decodedMessage') or {}
        body = dec.get('decodedMessageBody') or {}
        hook = (m.get('message') or '')
        out.append(dict(protocol='CCTP', status=m.get('status'), src_domain=dec.get('sourceDomain'), dst_domain=dec.get('destinationDomain'), dst_name=CCTP_DOMAIN.get(int(dec.get('destinationDomain') or -1)), mint_recipient=body.get('mintRecipient'), amount=body.get('amount'), sender=body.get('messageSender'), cctp_forward='636374702d666f7277617264' in hook, source=f'https://iris-api.circle.com/v2/messages/{domain}?transactionHash={tx}'))
    return out


def cctp_mint_source(tx, chain):
    """A CCTP mint carries its message in calldata: source domain, nonce and original sender are readable without any API."""
    t = net.rpc('eth_getTransactionByHash', [tx], chain)
    data = t['input']
    if not data.startswith('0x57ecfd28'):
        return None
    body = bytes.fromhex(data[10:])
    offset = int.from_bytes(body[:32], 'big')
    length = int.from_bytes(body[offset:offset + 32], 'big')
    msg = body[offset + 32:offset + 32 + length]
    src = int.from_bytes(msg[4:8], 'big')
    return dict(protocol='CCTP mint', src_domain=src, src_name=CCTP_DOMAIN.get(src), dst_domain=int.from_bytes(msg[8:12], 'big'), nonce='0x' + msg[12:44].hex(), sender='0x' + msg[44:76].hex()[-40:], caller=t['from'], source=f'calldata of {tx}')


def layerzero(tx):
    d = net.get(f'https://scan.layerzero-api.com/v1/messages/tx/{tx}', pause=.5, accept=(400, 404))
    out = []
    for m in d.get('data') or []:
        p = m.get('pathway') or {}
        out.append(dict(protocol='LayerZero', status=(m.get('status') or {}).get('name'), src_eid=p.get('srcEid'), dst_eid=p.get('dstEid'), sender=(p.get('sender') or {}).get('name') or (p.get('sender') or {}).get('address'), receiver=(p.get('receiver') or {}).get('name') or (p.get('receiver') or {}).get('address'), src_tx=(m.get('source') or {}).get('tx', {}).get('txHash'), dst_tx=(m.get('destination') or {}).get('tx', {}).get('txHash'), source=f'https://scan.layerzero-api.com/v1/messages/tx/{tx}'))
    return out


def across(tx, chain):
    d = net.get('https://app.across.to/api/deposit/status', dict(originChainId=chain, depositTxnRef=tx), pause=.5, accept=(400, 404))
    if d.get('status'):
        return [dict(protocol='Across', status=d.get('status'), src_chain=d.get('originChainId'), dst_chain=d.get('destinationChainId'), fill_tx=d.get('fillTx') or d.get('fillTxnRef'), deposit_id=d.get('depositId'), source=f'https://app.across.to/api/deposit/status?originChainId={chain}&depositTxnRef={tx}')]
    return []


def hyperliquid(address):
    """Public ledger of one Hyperliquid account. POST, read only, cached by address."""
    key = hashlib.sha256(json.dumps(['hl', address]).encode()).hexdigest()
    hit, value = net._load(key)
    if hit:
        return value
    net.guard()
    results = {}
    for name, body in (('ledger', dict(type='userNonFundingLedgerUpdates', user=address, startTime=0)), ('state', dict(type='clearinghouseState', user=address)), ('spot', dict(type='spotClearinghouseState', user=address)), ('fills', dict(type='userFills', user=address))):
        req = urllib.request.Request('https://api.hyperliquid.xyz/info', data=json.dumps(body).encode(), headers=net.UA)
        with urllib.request.urlopen(req, timeout=30) as r:
            results[name] = json.loads(r.read())
        net.note(kind='post', url='https://api.hyperliquid.xyz/info', body=name, address=address)
    net._store(key, results)
    return results


def resolve(e):
    """The record for one edge, whichever protocol answers. An empty list means 'no public record found', never 'not a bridge'."""
    name = ' '.join(str(e.get(k) or '') for k in ('service', 'contract_name', 'method')).lower()
    tx, chain = e['tx'], e['chain']
    out = []
    if chain == walk.SOLANA:
        return out
    if 'dln' in name or 'debridge' in name:
        out += debridge(tx)
    if 'cctp' in name or 'tokenmessenger' in name:
        out += cctp(tx, chain)
    if 'stargate' in name or 'layerzero' in name:
        out += layerzero(tx)
    if 'across' in name or 'spokepool' in name:
        out += across(tx, chain)
    if e['src'] == evm.ZERO:
        m = cctp_mint_source(tx, chain)
        if m:
            out.append(m)
    return out


def main():
    rows = []
    hl_accounts = set()
    for p in sorted(STATE.glob('walk_*.json')):
        w = json.loads(p.read_text())
        for e in w['edges']:
            name = ' '.join(str(e.get(k) or '') for k in ('service', 'contract_name', 'method')).lower()
            if e['role'] == 'mint' or any(b in name for b in BRIDGE_WORDS):
                try:
                    rec = resolve(e)
                except Exception as x:
                    rec = [dict(protocol='error', error=str(x)[:200])]
                rows.append(dict(case=w['case'], tx=e['tx'], chain=e['chain'], direction=e['direction'], src=e['src'], dst=e['dst'], token=e['token'], amount=e['amount'], at=e['at'], utc=e['utc'], service=e.get('service'), contract=e.get('contract_name'), records=rec))
                if any(r.get('dst_name') == 'hyperevm' or r.get('cctp_forward') for r in rec):
                    hl_accounts.add((w['case'], e['src']))
    hl = {}
    for case, addr in hl_accounts:
        res = hyperliquid(addr)
        ledger = res.get('ledger') or []
        fills = res.get('fills') or []
        coins = {}
        for x in fills:
            c = coins.setdefault(x.get('coin'), dict(fills=0, notional=0.0, closed_pnl=0.0, fees=0.0))
            c['fills'] += 1
            c['notional'] += float(x.get('px') or 0) * float(x.get('sz') or 0)
            c['closed_pnl'] += float(x.get('closedPnl') or 0)
            c['fees'] += float(x.get('fee') or 0)
        hl[addr] = dict(case=case, ledger=ledger, account_value=(res.get('state') or {}).get('marginSummary', {}).get('accountValue'), fills=len(fills), fills_first=min((x['time'] for x in fills), default=None), fills_last=max((x['time'] for x in fills), default=None), coins=coins, closed_pnl=sum(c['closed_pnl'] for c in coins.values()), fees=sum(c['fees'] for c in coins.values()), spot=(res.get('spot') or {}).get('balances'), read_at=walk.now_utc(__import__('time').time()))
    (STATE / 'bridges.json').write_text(json.dumps(dict(rows=rows, hyperliquid=hl)))
    print('bridge steps', len(rows), 'with a record', sum(1 for r in rows if r['records']), 'hyperliquid accounts', len(hl))
    for r in rows:
        print(r['case'], r['direction'][:4], r['chain'], r['token'], round(r['amount'], 2), r['service'] or r['contract'], [{k: v for k, v in x.items() if k in ('protocol', 'dst_chain', 'src_chain', 'dst_name', 'src_name', 'receiver_dst', 'maker_src', 'mint_recipient', 'state', 'status')} for x in r['records']])


if __name__ == '__main__':
    main()
