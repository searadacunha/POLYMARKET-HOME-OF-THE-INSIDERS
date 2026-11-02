"""One hop further on the EVM side: who paid a wallet's owner before it funded Polymarket, and where a withdrawal's recipient sent the money next.

Usage: follow_next.py SLUG. Adds relations to cases/SLUG.json. Native coin moves are not visible in logs: stated as a limit in each report.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import case_chain as C
import net

ROOT = Path(__file__).resolve().parent.parent
STABLES = {137: [net.TOKENS['USDC.e'], net.TOKENS['USDC'], net.TOKENS['USDT']], 1: ['0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48', '0xdac17f958d2ee523a2206206994597c13d831ec7'],
           42161: ['0xaf88d065e77c8cc2239327c5edb3a432268e5831', '0xff970a61a04b1ca14834a43f5de4533ebddb5cc8', '0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9'], 8453: ['0x833589fcd6edb6e08f4c7c32d4f71b54bda02913'],
           10: ['0x0b2c639c533813f4aa9d7837caf62653d097ff85', '0x7f5c764cbc14f9669b88a8f7b2c5c5f7e5c1e6e3', '0x94b008aa00579c1307b0ef2c499ad98a8ce58e58']}
STEP = {137: 9000, 1: 5000, 42161: 9000, 8453: 5000, 10: 5000}
DECIMALS = {'0x8ac76a51cc950d9822d68b83fe1ad97b32cd580d': 18, '0x55d398326f99059ff775485246999027b3197955': 18}


def logs_touching(address, chain, low, high, inbound):
    rows = []
    for start in range(low, high + 1, STEP[chain]):
        args = dict(address=STABLES[chain], fromBlock=hex(start), toBlock=hex(min(high, start + STEP[chain] - 1)))
        topics = [net.TRANSFER, None, net.pad(address)] if inbound else [net.TRANSFER, net.pad(address)]
        for log in net.rpc('eth_getLogs', [dict(args, topics=topics)], chain):
            rows.append(dict(tx=log['transactionHash'], log_index=int(log['logIndex'], 16), block=int(log['blockNumber'], 16), token=log['address'].lower(), source='0x' + log['topics'][1][-40:], target='0x' + log['topics'][2][-40:], raw=int(log['data'], 16)))
    return sorted(rows, key=lambda r: (r['block'], r['log_index']))


def amount_of(row):
    return row['raw'] / 10 ** DECIMALS.get(row['token'], 6)


def add(case, row, chain, basis_extra=''):
    kind = C.address_kind(row['source'], chain), C.address_kind(row['target'], chain)
    at = net.block_time(row['block'], chain)
    labelled = C.label(row['source']) or C.label(row['target'])
    r = case.rel('SERVICE_INTERACTION' if labelled else 'ONCHAIN_CONFIRMED', row['source'], row['target'], chain, row['tx'], row['log_index'], row['token'], amount_of(row), at,
                 f"Transfer log of one confirmed transaction. Sender nonce {kind[0]['nonce']}, kind {kind[0]['kind']}. Receiver nonce {kind[1]['nonce']}, kind {kind[1]['kind']}.{basis_extra}", ['Either side may be a service holding funds for someone else.'])
    return r


def owner_upstream(case, hop):
    """A deposit whose Relay record names an EVM sender other than the bridge address: read what paid that sender in the 48 hours before."""
    record = hop.get('relay')
    if not record or not record.get('in_txs'):
        return None
    chain, tx = record['in_txs'][0]
    user = str(record['user']).lower()
    if chain not in STEP or user == hop['immediate_source'] or not user.startswith('0x'):
        return None
    block = int(net.rpc('eth_getTransactionReceipt', [tx], chain)['blockNumber'], 16)
    at = net.block_time(block, chain)
    low = C.block_at(chain, at - 48 * 3600)
    rows = [r for r in logs_touching(user, chain, low, block, True) if r['source'] != user]
    want = float(record['in_amount'] or 0)
    keep = [r for r in rows if amount_of(r) >= .5 * want] or rows[-3:]
    for r in keep[-3:]:
        add(case, r, chain, ' Inflow of the sender in the 48 hours before it funded Polymarket.')
    return dict(user=user, chain=chain, inflows_seen=len(rows), kept=[dict(source=r['source'], amount=amount_of(r), tx=r['tx']) for r in keep[-3:]], limit='Stablecoin logs only: native coin and other tokens are not read.')


def next_hop(case, recipient, chain, from_block, depth=0):
    """Where the money went after the recipient, from stablecoin logs. Stops at a label, a high nonce, a contract or depth 2."""
    if chain not in STEP or C.label(recipient):
        return dict(address=recipient, chain=chain, read=False, reason='BSC or Solana are read elsewhere, or the address is labelled.' if not C.label(recipient) else C.label(recipient)['name'])
    head = int(net.rpc('eth_blockNumber', [], chain), 16)
    rows = logs_touching(recipient, chain, from_block, head, False)
    big = [r for r in rows if amount_of(r) >= 100]
    out = dict(address=recipient, chain=chain, read=True, scanned_blocks=[from_block, head], outflows=len(rows), outflows_over_100=len(big), read_at=time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime()), hops=[])
    for r in big[:6]:
        add(case, r, chain)
        kind = C.address_kind(r['target'], chain)
        step = dict(target=r['target'], amount=amount_of(r), tx=r['tx'], kind=kind, label=C.label(r['target']))
        if depth < 1 and kind['kind'] == 'EOA' and kind['nonce'] < 1000 and not step['label']:
            step['next'] = next_hop(case, r['target'], chain, r['block'], depth + 1)
        out['hops'].append(step)
    return out


def run(slug):
    path = ROOT / f'cases/{slug}.json'
    c = json.loads(path.read_text())
    case = C.Case(slug)
    case.relations = list(c.get('chain_relations', []))
    c['owner_upstream'] = [u for u in (owner_upstream(case, h) for h in c.get('funding_chain', []) if h) if u]
    follows = []
    done = set()
    for hop in c.get('exit_chain', []):
        if not hop or not hop.get('recipient') or hop['recipient'] in done or hop.get('out_chain') == C.SOLANA:
            continue
        done.add(hop['recipient'])
        chain, tx = hop['relay']['out_txs'][0]
        if chain == 56 or chain not in STEP:
            follows.append(dict(address=hop['recipient'], chain=chain, read=False, reason='Node limits on this chain: stablecoin balance read only.'))
            continue
        block = int(net.rpc('eth_getTransactionByHash', [tx], chain)['blockNumber'], 16)
        follows.append(next_hop(case, hop['recipient'].lower(), chain, block))
    c['exit_follow'] = follows
    c['chain_relations'] = case.relations
    path.write_text(json.dumps(c, indent=1, ensure_ascii=False))
    print(slug, 'relations', len(case.relations), 'owner_upstream', len(c['owner_upstream']), 'follows', [(f['address'][:10], f.get('outflows')) for f in follows], 'calls', net.Stats.calls, flush=True)


if __name__ == '__main__':
    for slug in sys.argv[1:]:
        try:
            run(slug)
        except RuntimeError as e:
            print(slug, 'FAILED', str(e)[:200], flush=True)
