"""Chain-only verification of Relay handoffs (Polygon <-> Solana). For each handoff with equal intermediary amounts:
L1-in  Polygon: USDC.e Transfer sender proxy -> Relay solver (2025 format, withdraw request id inside tx input)
               or -> Relay Depository with a RelayErc20Deposit log whose depositor is the proxy (2026 format, key = log id)
L1-out Solana : memo == that key, intermediary USDC balance +amount
L2-in  Solana : key2 (tail of the L2-out input) in the memo or in the Relay depository instruction data,
               intermediary USDC balance -amount, intermediary signs the transaction
L2-out Polygon: USDC.e Transfer Relay solver -> recipient proxy
Raw chain responses are archived (with sha256) under RAW/chain/. Usage: verify_handoffs.py RAW handoffs.json accounts.json out.json"""
import json, sys, time, hashlib, pathlib, urllib.request, datetime
sys.path.insert(0, str(pathlib.Path(__file__).parent)); import rpc
RAW = pathlib.Path(sys.argv[1]); H = json.load(open(sys.argv[2])); ACC = {k: v.lower() for k, v in json.load(open(sys.argv[3])).items()}
DEPOSITORY = '0x4cd00e387622c35bddb9b4c962c136462338bc31'
USDCE, SOLVER, USDC_SOL = '0x2791bca1f2de4661ed88a30c99a7a9449aa84174', '0xf70da97812cb96acdf810712aa562db8dfa3dbef', 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'
T = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
C = RAW / 'chain'; C.mkdir(exist_ok=True)
def keep(name, obj):
    b = json.dumps(obj, sort_keys=True).encode(); (C / name).write_bytes(b)
    (C / (name + '.sha256')).write_text(hashlib.sha256(b).hexdigest())
def poly(h):
    p = C / f'polygon_{h}.json'
    if p.exists(): return json.loads(p.read_bytes())
    t = rpc.call('polygon', 'eth_getTransactionByHash', [h]); r = rpc.call('polygon', 'eth_getTransactionReceipt', [h])
    b = rpc.call('polygon', 'eth_getBlockByNumber', [r['blockNumber'], False])
    o = {'tx': t, 'receipt': r, 'block': {'number': b['number'], 'hash': b['hash'], 'timestamp': b['timestamp']}, 'endpoint': rpc.ENDPOINTS['polygon'][0]}
    keep(p.name, o); return o
def sol(sig):
    p = C / f'solana_{sig}.json'
    if p.exists(): return json.loads(p.read_bytes())
    body = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'getTransaction', 'params': [sig, {'encoding': 'jsonParsed', 'maxSupportedTransactionVersion': 0}]}).encode()
    for i in range(8):
        try:
            r = json.load(urllib.request.urlopen(urllib.request.Request('https://api.mainnet-beta.solana.com', data=body, headers={'content-type': 'application/json'}), timeout=60))
            if r.get('result'): break
        except Exception as e:
            r = {'error': str(e)}
        time.sleep(3 * (i + 1))
    else:
        raise RuntimeError(f'solana {sig}: {r}')
    o = {'result': r['result'], 'endpoint': 'https://api.mainnet-beta.solana.com'}; keep(p.name, o); time.sleep(0.6); return o
def transfers(o):
    return [(l['address'].lower(), '0x' + l['topics'][1][26:], '0x' + l['topics'][2][26:], int(l['data'], 16), int(l['logIndex'], 16))
            for l in o['receipt']['logs'] if l['topics'][0] == T and len(l['topics']) == 3]
def sol_view(o, owner):
    r = o['result']; m = r['meta']
    pre = {b['accountIndex']: int(b['uiTokenAmount']['amount']) for b in m['preTokenBalances'] if b['owner'] == owner and b['mint'] == USDC_SOL}
    post = {b['accountIndex']: int(b['uiTokenAmount']['amount']) for b in m['postTokenBalances'] if b['owner'] == owner and b['mint'] == USDC_SOL}
    delta = sum(post.get(k, 0) - pre.get(k, 0) for k in set(pre) | set(post))
    memos = [i.get('parsed') for i in r['transaction']['message']['instructions'] if i.get('program') == 'spl-memo']
    auth = [i['parsed']['info'].get('authority') for i in r['transaction']['message']['instructions']
            if i.get('program') == 'spl-token' and isinstance(i.get('parsed'), dict) and i['parsed'].get('type', '').startswith('transfer')]
    data = [b58d(i['data']).hex() for i in r['transaction']['message']['instructions'] if i.get('data')]
    signers = [k['pubkey'] for k in r['transaction']['message']['accountKeys'] if k.get('signer')]
    return {'slot': r['slot'], 'blockTime': r['blockTime'], 'err': m['err'], 'delta_atomic': delta, 'post_atomic': sum(post.values()), 'memos': memos,
            'authorities': auth, 'instruction_data_hex': data, 'signers': signers}
B58 = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
def b58d(x):
    n = 0
    for ch in x: n = n * 58 + B58.index(ch)
    return b'\x00' * (len(x) - len(x.lstrip('1'))) + n.to_bytes((n.bit_length() + 7) // 8, 'big')
def atomic(x): return int(round(float(x) * 1e6))
res = []
for h in [h for h in H if h['amount_out_equals_amount_in']]:
    sp, rp, x = ACC[h['sender']], ACC[h['recipient']], h['intermediary']
    a, b = poly(h['withdraw_inTxs'][0][1]), poly(h['deposit_outTxs'][0][1])
    s1, s2 = sol(h['withdraw_outTxs'][0][1]), sol(h['deposit_inTxs'][0][1])
    v1, v2 = sol_view(s1, x), sol_view(s2, x)
    t1 = [t for t in transfers(a) if t[0] == USDCE and t[1] == sp and t[2] in (SOLVER, DEPOSITORY)]
    dep_ids = ['0x' + l['data'][-64:] for l in a['receipt']['logs'] if l['address'].lower() == DEPOSITORY and l['topics'][0].startswith('0x49fed1d0')
               and l['data'][2:66][-40:] == sp[2:]]
    key1 = h['withdraw_request'] if h['withdraw_request'][2:] in a['tx']['input'] else (dep_ids[0] if dep_ids else None)
    key2 = '0x' + b['tx']['input'][-64:]
    t4 = [t for t in transfers(b) if t[0] == USDCE and t[1] == SOLVER and t[2] == rp]
    chk = {
        'L1_in_status_ok': a['receipt']['status'] == '0x1',
        'L1_in_transfer_from_sender_proxy': bool(t1) and t1[0][3] == atomic(h['withdraw_in'][0]),
        'L1_in_chain_key_found': key1 is not None,
        'L1_out_memo_is_chain_key': key1 in v1['memos'] and v1['err'] is None,
        'L1_out_intermediary_credited': v1['delta_atomic'] == atomic(h['withdraw_out'][0]),
        'L2_in_carries_L2_out_key': (key2 in v2['memos'] or any(key2[2:] in d for d in v2['instruction_data_hex'])) and v2['err'] is None,
        'L2_in_intermediary_debited_same_amount': v2['delta_atomic'] == -v1['delta_atomic'],
        'L2_in_intermediary_signs': x in v2['signers'],
        'L2_out_status_ok': b['receipt']['status'] == '0x1',
        'L2_out_transfer_to_recipient_proxy': bool(t4) and t4[0][3] == atomic(h['deposit_out'][0]),
        'order_solana_credit_before_debit': v1['blockTime'] <= v2['blockTime'],
    }
    ta, tb = int(a['block']['timestamp'], 16), int(b['block']['timestamp'], 16)
    utc = lambda s: datetime.datetime.fromtimestamp(s, datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    res.append({'sender': h['sender'], 'recipient': h['recipient'], 'intermediary': x, 'withdraw_request': h['withdraw_request'], 'deposit_request': h['deposit_request'], 'chain_key_leg1': key1, 'chain_key_leg2': key2,
                'relay_format': 'request_id_in_calldata' if key1 == h['withdraw_request'] else 'depository_log_id',
                'L1_in': {'chain_id': 137, 'tx': h['withdraw_inTxs'][0][1], 'block': int(a['receipt']['blockNumber'], 16), 'utc': utc(ta), 'logIndex': t1[0][4] if t1 else None, 'usdce_atomic': t1[0][3] if t1 else None},
                'L1_out': {'chain_id': 792703809, 'sig': h['withdraw_outTxs'][0][1], 'slot': v1['slot'], 'utc': utc(v1['blockTime']), 'usdc_atomic': v1['delta_atomic']},
                'L2_in': {'chain_id': 792703809, 'sig': h['deposit_inTxs'][0][1], 'slot': v2['slot'], 'utc': utc(v2['blockTime']), 'usdc_atomic': -v2['delta_atomic'], 'intermediary_balance_after': v2['post_atomic']},
                'L2_out': {'chain_id': 137, 'tx': h['deposit_outTxs'][0][1], 'block': int(b['receipt']['blockNumber'], 16), 'utc': utc(tb), 'logIndex': t4[0][4] if t4 else None, 'usdce_atomic': t4[0][3] if t4 else None},
                'seconds_L1_in_to_L2_out': tb - ta, 'seconds_on_intermediary': v2['blockTime'] - v1['blockTime'], 'checks': chk, 'all_checks_pass': all(chk.values())})
    print(h['sender'], '->', h['recipient'], 'pass' if all(chk.values()) else [k for k, v in chk.items() if not v], tb - ta, 's', flush=True)
json.dump(res, open(sys.argv[4], 'w'), indent=1)
print(sum(r['all_checks_pass'] for r in res), 'of', len(res), 'handoffs pass every chain check')
