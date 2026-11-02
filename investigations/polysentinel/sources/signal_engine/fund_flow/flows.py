"""What one confirmed transaction moved, read from all its logs and not just those naming the wallet.

A deposit's funder never touches the wallet: it pays USDC.e into pUSD, which mints to the wallet in the
same transaction. And one transaction can carry several people's deposits, so a net per address cannot
pair them. Value is therefore followed log by log, by exact amount in log order, and the net per address
is kept only as a check. Each transfer keeps chain, transaction and log index.
"""
import json
from collections import defaultdict
from pathlib import Path

from .keccak import topic

ZERO = '0x' + '0' * 40
PUSD = '0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb'
USDC_E = '0x2791bca1f2de4661ed88a30c99a7a9449aa84174'
USDC = '0x3c499c542cef5e3811e1192ce70d8cc03d5c3359'
COLLATERAL = {PUSD: 'pUSD', USDC_E: 'USDC.e', USDC: 'USDC'}
COLLATERAL_RESERVE = '0xc417fd8e96'
POL_SYSTEM = '0x0000000000000000000000000000000000001010'
TRANSFER = topic('Transfer(address,address,uint256)')
LOG_TRANSFER = '0xe6497e3ee548a3372136af2fcb0696db31fc6cf20260707645068bd3fe97f3c4'
TRANSFER_SINGLE = topic('TransferSingle(address,address,address,uint256,uint256)')
TRANSFER_BATCH = topic('TransferBatch(address,address,address,uint256[],uint256[])')
SPLIT = topic('PositionSplit(address,address,bytes32,bytes32,uint256[],uint256)')
MERGE = topic('PositionsMerge(address,address,bytes32,bytes32,uint256[],uint256)')
REDEEM = topic('PayoutRedemption(address,address,bytes32,bytes32,uint256[],uint256)')
ORDER_FILLED = {'0xd0a08e8c493f9c94f29311604c9de1b4e8c8d4c06bd0c789af57f2d65bfec0f6': 'v1', '0xd543adfd945773f1a62f74f0ee55a5e3b9b1a28262980ba90b1a89f2ea84d8ee': 'v2'}
RELAY_DEPOSITORY = '0x4cd00e387622c35bddb9b4c962c136462338bc31'
DEPOSITORY_EVENT = '0x49fed1d0b752ce30eee63c7a81133f3363b532fec5d4d7dd1ccfd005de4555e1'
_TOLERANCE_RAW = 1
LABELS = json.loads((Path(__file__).with_name('labels.json')).read_text())['addresses']


def label_of(address):
    return LABELS.get(address.lower())


def is_collateral_mechanics(address):
    a = address.lower()
    return a in (ZERO, PUSD) or a.startswith(COLLATERAL_RESERVE)


def transfers(receipt, chain_id=137):
    """ERC-20 and native moves of one receipt. A removed log cannot be evidence of anything."""
    out = []
    for log in receipt.get('logs', []):
        if log.get('removed'):
            raise ValueError('Removed log in a receipt')
        topics = log.get('topics') or []
        if not topics:
            continue
        common = dict(chain_id=chain_id, tx=log['transactionHash'].lower(), log_index=int(log['logIndex'], 16), block=int(log['blockNumber'], 16))
        if topics[0] == TRANSFER and len(topics) == 3 and len(log['data']) == 66:
            token = log['address'].lower()
            out.append(dict(common, token=token, symbol=COLLATERAL.get(token), source='0x' + topics[1][-40:], target='0x' + topics[2][-40:], raw=int(log['data'], 16)))
        elif topics[0] == LOG_TRANSFER and log['address'].lower() == POL_SYSTEM and len(topics) == 4:
            out.append(dict(common, token=POL_SYSTEM, symbol='POL', source='0x' + topics[2][-40:], target='0x' + topics[3][-40:], raw=int(log['data'][2:66], 16)))
    return out


def decode_events(receipt):
    """Protocol events that say what else happened, kept as they are. Unknown topics are counted, not guessed."""
    found = defaultdict(int)
    orders = []
    for log in receipt.get('logs', []):
        topics = log.get('topics') or []
        if not topics:
            continue
        name = {SPLIT: 'split', MERGE: 'merge', REDEEM: 'redeem', TRANSFER_SINGLE: 'position_transfer', TRANSFER_BATCH: 'position_transfer'}.get(topics[0]) or ('order_filled' if topics[0] in ORDER_FILLED else None)
        if name:
            found[name] += 1
        if topics[0] == DEPOSITORY_EVENT and log['address'].lower() == RELAY_DEPOSITORY and len(log['data']) == 2 + 64 * 4:
            data = log['data'][2:]
            orders.append(dict(service='Relay Depository', log_index=int(log['logIndex'], 16), depositor='0x' + data[24:64], token='0x' + data[88:128], raw=int(data[128:192], 16), order_id='0x' + data[192:256]))
    return dict(counts=dict(found), orders=orders)


def _follow(moves, start, amount, address, backward):
    """Walks equal-amount transfers through an address, nearest log first. Two possible steps stop the walk and say so."""
    hops, current, position, unclear = [], address, start, False
    while True:
        if backward:
            found = [i for i in range(position - 1, -1, -1) if moves[i]['target'] == current and moves[i]['raw'] == amount and moves[i]['source'] != current]
        else:
            found = [i for i in range(position + 1, len(moves)) if moves[i]['source'] == current and moves[i]['raw'] == amount and moves[i]['target'] != current]
        found = [i for i in found if not is_collateral_mechanics(moves[i]['source' if backward else 'target'])]
        if not found:
            return current, hops, unclear
        if len(found) > 1:
            unclear = True
        position = found[0]
        hops.append(moves[position]['log_index'])
        current = moves[position]['source' if backward else 'target']


def funders_behind(everything, address, wallet):
    """Who paid, if this address did not. A real payer only loses tokens in the transaction.

    One that nets zero is a router, and one that also gains another token is a pool. None or several behind them: nothing is concluded.
    """
    nets = defaultdict(lambda: defaultdict(int))
    for t in everything:
        nets[t['source']][t['token']] -= t['raw']
        nets[t['target']][t['token']] += t['raw']
    own = nets[address].values()
    if any(v < 0 for v in own) and not any(v > 0 for v in own):
        return None
    return sorted(a for a, tokens in nets.items() if a != wallet and not is_collateral_mechanics(a) and any(v < 0 for v in tokens.values()) and not any(v > 0 for v in tokens.values()))


def value_paths(moves, wallet, everything=()):
    """Where the collateral reaching or leaving this wallet came from and went, in this transaction only."""
    inflows, outflows = [], []
    everything = everything or moves
    for i, t in enumerate(moves):
        if t['target'] == wallet and t['source'] != wallet:
            hops, unclear = [t['log_index']], False
            if t['source'] == ZERO and t['token'] == PUSD:
                payers = [j for j in range(i - 1, -1, -1) if moves[j]['target'] == PUSD and moves[j]['raw'] == t['raw'] and moves[j]['token'] != PUSD]
                if not payers:
                    inflows.append(dict(origin=None, raw=t['raw'], token=t['token'], log_index=t['log_index'], hops=hops, unclear=True, reason='Mint with no visible payer of that amount in this transaction.'))
                    continue
                unclear = len(payers) > 1
                current, position = moves[payers[0]]['source'], payers[0]
                hops.insert(0, moves[position]['log_index'])
            elif is_collateral_mechanics(t['source']):
                continue
            else:
                current, position = t['source'], i
            origin, more, far = _follow(moves, position, t['raw'], current, True)
            path = dict(origin=origin, raw=t['raw'], token=t['token'], log_index=t['log_index'], hops=list(reversed(more)) + hops, unclear=unclear or far)
            behind = None if label_of(origin) else funders_behind(everything, origin, wallet)
            if behind is not None:
                path['passed_through'] = origin
                if len(behind) == 1:
                    path.update(origin=behind[0], paid=[dict(token=x['token'], symbol=x.get('symbol'), raw=str(x['raw']), log_index=x['log_index']) for x in everything if x['source'] == behind[0]])
                else:
                    path.update(origin=None, unclear=True, reason=f'{origin} only passed funds on, and {len(behind)} addresses could be behind it.')
            inflows.append(path)
        elif t['source'] == wallet and t['target'] != wallet and not is_collateral_mechanics(t['target']):
            final, more, far = _follow(moves, i, t['raw'], t['target'], False)
            outflows.append(dict(destination=final, first_receiver=t['target'], raw=t['raw'], token=t['token'], log_index=t['log_index'], hops=[t['log_index']] + more, unclear=far))
    return inflows, outflows


def tx_flow(receipt, wallet=None, chain_id=137):
    """One transaction's collateral: paths for the wallet, and the net per address as a cross-check."""
    wallet = wallet.lower() if wallet else None
    moves = [t for t in transfers(receipt, chain_id) if t['token'] in COLLATERAL]
    net = defaultdict(int)
    for t in moves:
        net[t['source']] -= t['raw']
        net[t['target']] += t['raw']
    outside = {a: v for a, v in net.items() if not is_collateral_mechanics(a)}
    sources = {a: -v for a, v in outside.items() if v < -_TOLERANCE_RAW}
    sinks = {a: v for a, v in outside.items() if v > _TOLERANCE_RAW}
    through = sorted(a for a in net if abs(net[a]) <= _TOLERANCE_RAW and a not in (ZERO, PUSD) and not is_collateral_mechanics(a) and any(t['source'] == a or t['target'] == a for t in moves))
    events = decode_events(receipt)
    wrapped = any(t['source'] == ZERO and t['token'] == PUSD for t in moves)
    unwrapped = any(t['target'] == ZERO and t['token'] == PUSD for t in moves)
    wallet_net = net.get(wallet, 0) if wallet else None
    moves = sorted(moves, key=lambda t: t['log_index'])
    inflows, outflows = value_paths(moves, wallet, transfers(receipt, chain_id)) if wallet else ([], [])
    unexplained = wallet_net - sum(p['raw'] for p in inflows) + sum(p['raw'] for p in outflows) if wallet else None
    return dict(chain_id=chain_id, tx=receipt['transactionHash'].lower(), block=int(receipt['blockNumber'], 16), success=int(receipt.get('status', '0x1'), 16) == 1, submitter=receipt.get('from', '').lower(),
                wallet=wallet, wallet_net_raw=wallet_net, inflows=inflows, outflows=outflows, unexplained_raw=unexplained, sources=dict(sorted(sources.items())), sinks=dict(sorted(sinks.items())), pass_through=through, ambiguous=len(sources) > 1 and len(sinks) > 1,
                conversions=dict(minted=wrapped, burned=unwrapped), services=sorted({label_of(a)['name'] for a in net if label_of(a)}), events=events, logs=[dict(log_index=t['log_index'], token=t['token'], symbol=t['symbol'], source=t['source'], target=t['target'], raw=str(t['raw'])) for t in moves])
