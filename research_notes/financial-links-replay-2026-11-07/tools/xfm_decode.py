"""Decode the nine XFM receipts: OrderFilled makers/takers, ERC-1155 TransferSingle recipients and amounts, collateral payers,
and whether the match created new YES+NO pairs (PositionSplit). Usage: xfm_decode.py RECEIPT_DIR hashes.txt out.json"""
import json, sys, pathlib
D = pathlib.Path(sys.argv[1])
T20, TS, PS, OF, OM = '0xddf252ad', '0xc3d58168', '0x2e6bb91f', '0xd543adfd', '0x174b3811'
EX, CTF, PUSD = '0xe2222d279d744050d28e00520010520000310f59', '0x4d97dcd97ec945f40cf65f87097ace5ea0476045', '0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb'
a = lambda t: '0x' + t[26:]
out = []
for h in open(sys.argv[2]).read().split():
    rc = json.load(open(D / f'{h}.eth_getTransactionReceipt.json'))['result']
    L = rc['logs']
    fills = [{'maker': a(l['topics'][2]), 'taker': a(l['topics'][3]), 'words': [int(l['data'][2 + 64 * i:66 + 64 * i], 16) for i in range((len(l['data']) - 2) // 64)], 'logIndex': int(l['logIndex'], 16)}
             for l in L if l['topics'][0].startswith(OF) and l['address'].lower() == EX]
    ts = [{'to': a(l['topics'][3]), 'token_id': str(int(l['data'][2:66], 16)), 'amount': int(l['data'][66:130], 16) / 1e6, 'logIndex': int(l['logIndex'], 16)}
          for l in L if l['topics'][0].startswith(TS) and l['address'].lower() == CTF and a(l['topics'][2]) == EX]
    pay = [{'from': a(l['topics'][1]), 'amount': int(l['data'], 16) / 1e6} for l in L if l['topics'][0].startswith(T20) and l['address'].lower() == PUSD and a(l['topics'][2]) == EX]
    split = any(l['topics'][0].startswith(PS) and l['address'].lower() == CTF for l in L)
    parties = sorted({f['maker'] for f in fills} | {f['taker'] for f in fills} - {EX})
    out.append({'tx': h, 'block': int(rc['blockNumber'], 16), 'status': rc['status'], 'position_split': split, 'fills': fills, 'outcome_transfers': ts, 'collateral_payers': pay,
                'parties': parties, 'two_party_mint_match': split and len(parties) == 2 and len(ts) == 2 and {t['to'] for t in ts} == set(parties) and len({t['token_id'] for t in ts}) == 2,
                'equal_shares': len(ts) == 2 and ts[0]['amount'] == ts[1]['amount']})
json.dump(out, open(sys.argv[3], 'w'), indent=1)
for o in out:
    print(o['tx'][:12], 'split', o['position_split'], 'parties', [p[:10] for p in o['parties']], 'shares', [t['amount'] for t in o['outcome_transfers']],
          'paid', [(p['from'][:10], p['amount']) for p in o['collateral_payers']], 'two-party mint', o['two_party_mint_match'])
