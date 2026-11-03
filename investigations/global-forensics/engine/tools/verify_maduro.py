"""Independent re-reading of the Maduro and Iran file: every edge of its graph table from nodes today, and each account's cash rebuilt from the current API. Hashes come from the file.

Writes edge_verification.csv and summary.json. A row that differs stays in the output: nothing is dropped.
"""
import csv
import json
import sys
from collections import Counter
from decimal import Decimal
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gf import bridges, env, ledger_pnl, pm, proof
from gf.events import SOLANA, TRON, amount
from gf.net import RPC, Net, Refused
from gf.solana import Solana

env.redirect_temp()
ROOT = Path.home() / 'Documents/Crypto/enquete_maduro_iran'
TRON_API = 'https://api.trongrid.io/wallet/gettransactioninfobyid'
TRANSFER = 'ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
B58 = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
NETWORK = {'0x168b100d7a6620a2f49a455344c2c006eaf1714b', '0x834079f62fa9b4b0bdfad5b8b7a841e8267da024', '0x5621116629c5d640c8186f577362478cc6605245', '0xbf32f7a77ccea8bba647fea63d438ce1778b1762', '0x56efadc9defe5b7a21af751e0d026f2cf54136db', '0x38745db27f7360a287f6ca3c9b6a6a9c76149801', '0xe9b80c387ba77a585423b13c850c2e126c3befd8', '0x60280beffdfeaf962de4e6397ab49ed05a1b99e1'}


def tron_hex_to_base58(hex_address):
    import hashlib
    raw = bytes.fromhex('41' + hex_address[-40:])
    data = raw + hashlib.sha256(hashlib.sha256(raw).digest()).digest()[:4]
    n, out = int.from_bytes(data, 'big'), ''
    while n:
        n, r = divmod(n, 58)
        out = B58[r] + out
    return out


def tron_moves(net, tx):
    body = net.tron_info(tx)
    moves = []
    for log in body.get('log') or []:
        topics = log.get('topics') or []
        if topics and topics[0] == TRANSFER and len(topics) >= 3:
            moves.append(dict(contract=tron_hex_to_base58(log['address']), source=tron_hex_to_base58(topics[1]), target=tron_hex_to_base58(topics[2]), raw=int(log['data'], 16)))
    return moves, body


def check_evm(net, chain, row):
    moves, record = proof.read_tx(net, chain, row['tx'])
    want = Decimal(row['amount'] or 0)
    src, dst = row['source'].lower(), row['destination'].lower()
    exact = [m for m in moves if m['from'] == src and m['to'] == dst and abs(amount(m) - want) <= Decimal('0.01') + want * Decimal('0.00001')]
    partial = [m for m in moves if m['from'] == src or m['to'] == dst]
    return ('AGREES' if exact and record['status'] == 1 else 'PARTIAL' if partial else 'NOT_IN_RECEIPT'), exact[0]['level'] if exact else (moves[0]['level'] if moves else None), dict(block=record['block_number'], block_hash=record['block_hash'], log_index=exact[0].get('log_index') if exact else None, second_host=record['second_host'])


def check_tron(net, row):
    moves, body = tron_moves(net, row['tx'])
    want = Decimal(row['amount'] or 0) * 10 ** 6
    hit = [m for m in moves if m['source'] == row['source'] and m['target'] == row['destination'] and abs(Decimal(m['raw']) - want) <= max(Decimal(20000), want * Decimal('0.00001'))]
    if not moves and row['asset'] == 'TRX':  # a native transfer leaves no log: it is in the transaction, not in the receipt
        value = ((net.tron_info(row['tx'], path='gettransactionbyid').get('raw_data') or {}).get('contract') or [{}])[0].get('parameter', {}).get('value', {})
        if value.get('amount') is not None:
            moves = [dict(source=tron_hex_to_base58(value['owner_address']), target=tron_hex_to_base58(value['to_address']), raw=value['amount'])]
            hit = [m for m in moves if m['source'] == row['source'] and m['target'] == row['destination'] and abs(Decimal(m['raw']) - want) <= max(Decimal(20000), want * Decimal('0.00001'))]
    return ('AGREES' if hit else 'PARTIAL' if moves else 'NOT_IN_RECEIPT'), 'ONCHAIN_CONFIRMED' if hit else None, dict(block=body.get('blockNumber'), block_hash=None, log_index=None, second_host=None)


def side_chain(text):
    return dict(ethereum=1, polygon=137, base=8453, arbitrum=42161, tron=TRON, solana=SOLANA).get(text) or (int(text) if text.isdigit() else None)


def read_side(net, sol, chain, tx, destination, want):
    """One side of a cross-chain row, read by its own hash on its own chain. Returns (level, block, reached the destination at about the amount)."""
    if chain == SOLANA:
        tx_body = sol.transaction(tx)
        return ('ONCHAIN_CONFIRMED' if tx_body else None), (tx_body or {}).get('slot'), None
    if chain == TRON:
        body = net.tron_info(tx)
        hit = any(m['target'] == destination for m in tron_moves(net, tx)[0])
        return 'ONCHAIN_CONFIRMED', body.get('blockNumber'), hit
    moves, record = proof.read_tx(net, chain, tx)
    near = any(m['to'] == destination.lower() and abs(amount(m) - want) <= want * Decimal('0.03') + Decimal('0.01') for m in moves)
    return (moves[0]['level'] if moves else ('REVERIFIED' if record.get('agree') else 'ONCHAIN_CONFIRMED')), record['block_number'], near


def check_cross(net, sol, row):
    """Rows `chainA->chainB` holding `hashA|hashB`. Each side is read apart; the two are tied only by the same Relay id, read on both chains."""
    sides, hashes = [side_chain(c) for c in row['chain'].split('->')], row['tx'].split('|')
    if len(sides) != 2 or len(hashes) != 2 or None in sides or not all(c in RPC or c in (SOLANA, TRON) for c in sides):
        return 'NOT_READ_CHAIN', None, {}
    want = Decimal(row['amount'] or 0)
    if hashes[1] == 'None':  # the archive holds one hash for a same-chain swap: there is no second side to tie
        level = read_side(net, sol, sides[0], hashes[0], row['destination'], want)
        return 'ONE_SIDE_READ', level[0], dict(block=level[1], detail=json.dumps(dict(reached_destination_near_amount=level[2])))
    first = read_side(net, sol, sides[0], hashes[0], row['destination'], want)
    second = read_side(net, sol, sides[1], hashes[1], row['destination'], want)
    same_id = bridges.relay_proof(net, dict(in_txs=[(sides[0], hashes[0])], out_txs=[(sides[1], hashes[1])]), sol)
    verdict = {True: 'CROSSCHAIN_SAME_ID', False: 'CROSSCHAIN_ID_ABSENT', None: 'CROSSCHAIN_BOTH_SIDES_READ'}[same_id]
    return verdict, second[0], dict(block=second[1], detail=json.dumps(dict(in_level=first[0], out_level=second[0], reached_destination_near_amount=second[2], same_relay_id=same_id)))


def main(out):
    net = Net()
    sol = Solana(net)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader((ROOT / 'phase2/TABLE1_graph.csv').open()))
    results = []
    with (out / 'edge_verification.csv').open('w', newline='') as f:
        writer = None
        for row in rows:
            chain_text = row['chain']
            result = dict(row, result=None, level=None, block=None, block_hash=None, log_index=None, second_host=None, detail=None)
            try:
                if chain_text in ('ethereum', 'polygon', 'base', 'arbitrum'):
                    verdict, level, extra = check_evm(net, dict(ethereum=1, polygon=137, base=8453, arbitrum=42161)[chain_text], row)
                elif chain_text == 'tron' and row['tx'] and not row['tx'].startswith('0x'):
                    verdict, level, extra = check_tron(net, row)
                elif '->' in chain_text and '|' in row['tx']:
                    verdict, level, extra = check_cross(net, sol, row)
                elif '->' in chain_text and row['tx'].startswith('0x'):
                    first = chain_text.split('->')[0]
                    chain = dict(ethereum=1, polygon=137, tron=None).get(first) or (int(first) if first.isdigit() else None)
                    if chain in (1, 137, 42161, 8453, 10, 56):
                        moves, record = proof.read_tx(net, chain, row['tx'])
                        verdict, level, extra = ('TX_EXISTS_CROSSCHAIN' if record['status'] == 1 else 'REVERTED'), (moves[0]['level'] if moves else None), dict(block=record['block_number'], block_hash=record['block_hash'], log_index=None, second_host=record['second_host'])
                    else:
                        verdict, level, extra = 'NOT_READ_CHAIN', None, {}
                else:
                    verdict, level, extra = 'NOT_READ_CHAIN', None, {}
                result.update(result=verdict, level=level, **extra)
            except Refused as exc:
                result.update(result='NOT_READ', detail=str(exc)[:160])
            results.append(result['result'])
            if writer is None:
                writer = csv.DictWriter(f, fieldnames=list(result))
                writer.writeheader()
            writer.writerow(result)
            f.flush()
    pnl_old = {r['account']: r for r in csv.DictReader((ROOT / 'phase2/pnl_summary.csv').open())}
    accounts = []
    for wallet, old in pnl_old.items():
        history = pm.activity(net, wallet)
        books = ledger_pnl.account(history['rows'])
        rebuilt = sum(Decimal(m['cash_result']) for m in books['markets'])
        accounts.append(dict(wallet=wallet, in_network=wallet in NETWORK, history_complete=history['complete'], rows=len(history['rows']), archived_pnl=old['PnL'], rebuilt_cash_by_market=str(rebuilt), difference=str(rebuilt - Decimal(old['PnL'])), wallet_books=books['wallet'], unknown_types=books['unknown_types']))
    network = [a for a in accounts if a['in_network']]
    summary = dict(edges=len(rows), by_result=Counter(results), accounts=accounts, network_accounts=len(network), network_archived_pnl=str(sum(Decimal(a['archived_pnl']) for a in network)), network_rebuilt=str(sum(Decimal(a['rebuilt_cash_by_market']) for a in network)), calls=net.calls, hits=net.hits)
    (out / 'summary.json').write_text(json.dumps(summary, indent=1, default=dict))
    print(json.dumps({k: summary[k] for k in ('edges', 'by_result', 'network_accounts', 'network_archived_pnl', 'network_rebuilt', 'calls')}, default=dict))
    for a in accounts:
        print(a['wallet'][:12], a['in_network'], a['rows'], a['archived_pnl'], a['rebuilt_cash_by_market'], a['difference'], a['unknown_types'])


if __name__ == '__main__':
    main(sys.argv[1])
