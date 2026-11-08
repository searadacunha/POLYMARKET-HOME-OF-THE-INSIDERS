#!/usr/bin/env python3
"""Offline C1/C7 evidence ledger check; optional strict replay of a C7 ERC-20 log.

This file never claims an explorer snippet is a locally collected RPC receipt.
The --receipt-c7 and --block-c7 arguments are JSON files exported separately
from eth_getTransactionReceipt and eth_getBlockByNumber (full object or {result}).
"""
import argparse
import csv
import datetime as dt
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
EVM = re.compile(r"0x[0-9a-f]{40}\Z")
TX = re.compile(r"0x[0-9a-f]{64}\Z")
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
TOKEN = "0x2791bca1f2de4661ed88a30c99a7a9449aa84174"
EXCHANGE = "0xc5d563a36ae78145c45a50134d48a1215220f80a"


def require(condition, msg):
    if not condition:
        raise AssertionError(msg)


def read_csv(filename):
    with (HERE / 'data' / filename).open(newline='', encoding='utf-8') as fh:
        return list(csv.DictReader(fh))


def validate_inventory():
    accounts = read_csv('accounts.csv')
    anchors = read_csv('onchain_anchors.csv')
    require(len(accounts) == 2 and len(anchors) == 2, 'Expected two accounts and two transaction anchors')
    require({r['case'] for r in accounts} == {'C1', 'C7'}, 'Cases changed')
    require({r['handle'] for r in accounts} == {'Burdensome-Mix', '6741'}, 'Handles changed')
    require(len({r['polygon_proxy'] for r in accounts}) == 2, 'Duplicate proxy')
    by_case = {r['case']: r for r in accounts}
    for r in accounts:
        require(bool(EVM.fullmatch(r['polygon_proxy'])), 'Invalid address')
        require(r['chain_link_status'] == 'NOT_ESTABLISHED', 'Unsupported financial attribution')
        require(r['source_first'].startswith('https://') and r['source_second'].startswith('https://'), 'Source URLs missing')
    require({a['anchor_id'] for a in anchors} == {'C1_PROXY_CREATION', 'C7_ORDERBOOK_TRANSFER'}, 'Changed anchor IDs')
    for a in anchors:
        require(a['chain_id'] == '137' and a['case'] in by_case, 'Chain/case mismatch')
        require(a['polygon_proxy'] == by_case[a['case']]['polygon_proxy'], 'Account mismatch')
        require(bool(TX.fullmatch(a['tx_hash'])), 'Invalid transaction hash')
        require(a['source_url'] == 'https://polygonscan.com/tx/' + a['tx_hash'], 'Source/transaction mismatch')
        require(int(a['block_number']) > 0, 'Invalid block')
        require(dt.datetime.fromisoformat(a['utc'].replace('Z', '+00:00')).tzinfo is not None, 'UTC missing')
        require('NOT_RPC_REPLAYED' in a['evidence_tier'], 'Do not promote explorer-only evidence')
    c1 = next(a for a in anchors if a['case'] == 'C1')
    c7 = next(a for a in anchors if a['case'] == 'C7')
    require(c1['kind'] == 'PROXY_CREATE_EXPLORER' and not c1['log_index'] and not c1['amount_atomic'], 'C1 is not a token funding event')
    require(c7['kind'] == 'ERC20_TRANSFER_IN_TRADE', 'C7 kind mismatch')
    require(c7['token_contract'] == TOKEN and c7['to_address'] == EXCHANGE, 'C7 exchange/token mismatch')
    require(c7['from_address'] == c7['polygon_proxy'] and c7['amount_atomic'] == '2500000', 'C7 sender/amount mismatch')
    require(c7['log_index'] == '107' and c7['utc'] == '2025-10-10T00:31:55Z', 'C7 indexed log changed')
    return c7


def rpc_result(path):
    with Path(path).open(encoding='utf-8') as fh:
        obj = json.load(fh)
    return obj.get('result', obj) if isinstance(obj, dict) else obj


def as_int(v):
    return int(v, 16) if isinstance(v, str) and v.startswith('0x') else int(v)


def check_receipt(c7, receipt, block):
    require(isinstance(receipt, dict) and isinstance(block, dict), 'RPC JSON objects required')
    require(str(receipt.get('transactionHash', '')).lower() == c7['tx_hash'], 'Wrong transaction hash')
    require(as_int(receipt.get('status', 0)) == 1, 'Transaction failed')
    require(as_int(receipt.get('blockNumber', 0)) == int(c7['block_number']), 'Wrong receipt block')
    require(as_int(block.get('number', 0)) == int(c7['block_number']), 'Wrong block number')
    when = dt.datetime.fromtimestamp(as_int(block['timestamp']), dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    require(when == c7['utc'], 'Block timestamp mismatch')
    target = None
    for log in receipt.get('logs', []):
        if as_int(log.get('logIndex', -1)) == int(c7['log_index']):
            target = log
            break
    require(target is not None, 'Indexed log missing')
    require(str(target.get('address', '')).lower() == TOKEN, 'Wrong token contract')
    topics = [str(s).lower() for s in target.get('topics', [])]
    require(len(topics) == 3 and topics[0] == TRANSFER, 'Not an ERC-20 Transfer')
    require(topics[1] == '0x' + '0' * 24 + c7['from_address'][2:], 'Wrong transfer sender')
    require(topics[2] == '0x' + '0' * 24 + EXCHANGE[2:], 'Wrong transfer recipient')
    require(as_int(target.get('data', '0x0')) == int(c7['amount_atomic']), 'Wrong atomic amount')
    return True


def self_test(c7):
    transfer = dict(address=TOKEN, logIndex=hex(107), topics=[TRANSFER, '0x' + '0' * 24 + c7['from_address'][2:], '0x' + '0' * 24 + EXCHANGE[2:]], data=hex(2_500_000))
    receipt = dict(transactionHash=c7['tx_hash'], status='0x1', blockNumber=hex(int(c7['block_number'])), logs=[transfer])
    block = dict(number=hex(int(c7['block_number'])), timestamp=hex(int(dt.datetime.fromisoformat(c7['utc'].replace('Z', '+00:00')).timestamp())))
    require(check_receipt(c7, receipt, block), 'Positive-control failed')
    cases = [
        (dict(receipt, status='0x0'), block),
        (dict(receipt, transactionHash='0x' + '0' * 64), block),
        (dict(receipt, logs=[dict(transfer, data=hex(3_000_000))]), block),
        (dict(receipt, logs=[dict(transfer, address='0x' + '0' * 40)]), block),
        (dict(receipt, logs=[dict(transfer, topics=[TRANSFER, '0x' + '0' * 64, transfer['topics'][2]])]), block),
        (receipt, dict(block, timestamp=hex(as_int(block['timestamp']) + 1))),
    ]
    for altered_receipt, altered_block in cases:
        try:
            check_receipt(c7, altered_receipt, altered_block)
        except AssertionError:
            continue
        raise AssertionError('Negative control was incorrectly accepted')
    print('SELF_TEST_OK: one positive and six negative receipt controls')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--receipt-c7', type=Path)
    parser.add_argument('--block-c7', type=Path)
    args = parser.parse_args()
    c7 = validate_inventory()
    print('INVENTORY_OK: two exact proxies; two non-replayed Polygon anchors; zero asserted funding links')
    if args.self_test:
        self_test(c7)
    require(bool(args.receipt_c7) == bool(args.block_c7), 'Pass both raw RPC files together')
    if args.receipt_c7:
        check_receipt(c7, rpc_result(args.receipt_c7), rpc_result(args.block_c7))
        print('RPC_C7_TRANSFER_REPLAY_OK: chain receipt and block fields match the indexed anchor')
    else:
        print('RPC_NOT_RUN: no original receipt/block supplied; explorer-only tier unchanged')


if __name__ == '__main__':
    main()
