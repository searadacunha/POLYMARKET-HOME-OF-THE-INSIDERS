"""Build the published tables of this note from the raw archive (outside git) and copy the evidence the offline
verify.py needs into evidence/. Usage: python3 -I build_tables.py RAW   (RAW = ~/Projects/Polymarket-deep-raw-20261107/raw)"""
import csv, json, glob, sys, shutil, pathlib, datetime, statistics, collections
RAW = pathlib.Path(sys.argv[1]); HERE = pathlib.Path(__file__).resolve().parents[1]; DATA, EV = HERE / 'data', HERE / 'evidence'
ACC = json.load(open(RAW / 'kpmg_accounts.json')); BYP = {v.lower(): k for k, v in ACC.items()}
PUBLISHED = {'Youaregu', 'perlgrow', 'boosthero', 'bostonguy'}  # the four proxies linked in the Bitquery article
EXPANDED = {'perlgrow', 'boosthero', 'bostonguy'}
OFF = {'0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48', '0xdac17f958d2ee523a2206206994597c13d831ec7',  # Ethereum USDC, USDT
       '0x3c499c542cef5e3811e1192ce70d8cc03d5c3359', '0x2791bca1f2de4661ed88a30c99a7a9449aa84174', '0xc2132d05d31c914a87c6611c10748aeb04b58e8f'}
def n(a): return a.lower() if a.startswith('0x') else a
def utc(t): return datetime.datetime.fromtimestamp(int(t), datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
def wcsv(name, rows):
    with open(DATA / name, 'w', newline='') as f:
        w = csv.DictWriter(f, list(rows[0])); w.writeheader(); w.writerows(rows)
def copy(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(src, dst)
def relay_reqs(addrs):
    out = {}
    for a in addrs:
        for f in glob.glob(str(RAW / f'xl/relay/{a}/p[0-9][0-9][0-9].json')):
            for q in json.load(open(f))['requests']: out[q['id']] = q
    return out
def es(addr, chain, action):
    p = RAW / f'xl/etherscan/{addr}/{chain}_{action}_p1.json'
    return json.load(open(p))['result'] if p.exists() else []
# 1. accounts
rows = []
for name, proxy in ACC.items():
    prof = json.load(open(RAW / f'xl/polymarket/{proxy}/profile.json'))
    rows.append({'public_label': name, 'cohort_role': 'EXPANDED_3' if name in EXPANDED else 'ORIGINAL_19', 'polygon_proxy': proxy,
                 'profile_created_utc': prof.get('createdAt'), 'resolution': 'EXACT_NAME_UNIQUE_IN_GAMMA_PUBLIC_SEARCH',
                 'proxy_published_by_bitquery': name in PUBLISHED,
                 'search_url': f'https://gamma-api.polymarket.com/public-search?q={name}&search_profiles=true&limit_per_type=50'})
wcsv('kpmg_accounts.csv', rows)
# 2. verified handoffs (+ evidence)
V = json.load(open(RAW / '../out/kpmg_handoffs_verified.json')); H = json.load(open(RAW / 'handoffs_all.json'))
reqs = relay_reqs(list(ACC.values()))
rows = []
for v in sorted(V, key=lambda v: v['L1_in']['utc']):
    for leg in ('L1_in', 'L2_out'):
        copy(RAW / f"chain/polygon_{v[leg]['tx']}.json", EV / 'chain' / f"polygon_{v[leg]['tx']}.json")
    for leg in ('L1_out', 'L2_in'):
        copy(RAW / f"chain/solana_{v[leg]['sig']}.json", EV / 'chain' / f"solana_{v[leg]['sig']}.json")
    for rid in (v['withdraw_request'], v['deposit_request']):
        (EV / 'relay' / f'{rid}.json').write_text(json.dumps(reqs[rid], sort_keys=True))
    rows.append({'sender': v['sender'], 'recipient': v['recipient'], 'intermediary_solana': v['intermediary'], 'relay_format': v['relay_format'],
                 'withdraw_request_id': v['withdraw_request'], 'deposit_request_id': v['deposit_request'],
                 'chain_key_leg1': v['chain_key_leg1'], 'chain_key_leg2': v['chain_key_leg2'],
                 'L1_polygon_tx': v['L1_in']['tx'], 'L1_block': v['L1_in']['block'], 'L1_logIndex': v['L1_in']['logIndex'], 'L1_utc': v['L1_in']['utc'], 'L1_usdce_atomic': v['L1_in']['usdce_atomic'],
                 'L1_solana_sig': v['L1_out']['sig'], 'L1_slot': v['L1_out']['slot'], 'L1_solana_utc': v['L1_out']['utc'], 'intermediary_credit_usdc_atomic': v['L1_out']['usdc_atomic'],
                 'L2_solana_sig': v['L2_in']['sig'], 'L2_slot': v['L2_in']['slot'], 'L2_solana_utc': v['L2_in']['utc'], 'intermediary_debit_usdc_atomic': v['L2_in']['usdc_atomic'],
                 'intermediary_balance_after_atomic': v['L2_in']['intermediary_balance_after'],
                 'L2_polygon_tx': v['L2_out']['tx'], 'L2_block': v['L2_out']['block'], 'L2_logIndex': v['L2_out']['logIndex'], 'L2_utc': v['L2_out']['utc'], 'L2_usdce_atomic': v['L2_out']['usdce_atomic'],
                 'seconds_L1_to_L2': v['seconds_L1_in_to_L2_out'], 'seconds_on_intermediary': v['seconds_on_intermediary'],
                 'in_bitquery_table': (v['sender'], v['recipient']) in {tuple(l.split(',')[:2]) for l in open(HERE.parent / 'kpmg-election-integrity-2026-11-07/KPMG_HANDOFFS.csv').read().splitlines()[1:]},
                 'status': 'CONFIRMED' if v['all_checks_pass'] else 'FAILED_CHECK'})
wcsv('kpmg_handoffs_verified.csv', rows)
# 3. shared deposit addresses (Relay credits + sweep behaviour)
SHARED = {'0xabf9261806a71a46fe06a05b3a68820905cbdb9e': 1, '0x1cefcfe88d24379a989b90facc32b75efc4fb19f': 1, '0xd4e6b2ffbffcb7ff0b8af35b051c6b58f23817a7': 1,
          '0x48f446bc074ab4bda4a6b2fc8ace90ad607716da': 1, '8t5YL8j9ewWKE2giGi4NHe74mvxC7sk2P3ufdhdcDNZZ': 792703809,
          '89Tw8NBoxqDDJx9RhE2JbLaxgjuLoJoJyUzef4d3PonS': 792703809, 'Ay1oajpQ8hZUPRmVuGLAc9tEowidsrZx3sxG8brVQq3B': 792703809}
rows = []
for x, ch in SHARED.items():
    qs = relay_reqs([x]); pay = [q for q in qs.values() if n(q['recipient']) == n(x) and q['status'] == 'success']
    for q in pay: (EV / 'relay' / f"{q['id']}.json").write_text(json.dumps(q, sort_keys=True))
    snd = collections.defaultdict(list)
    for q in pay: snd[BYP.get(n(q['user']), 'OUTSIDE:' + q['user'])].append(float(q['data']['metadata']['currencyOut']['amountFormatted']))
    r = {'address': x, 'chain_id': ch, 'relay_orders_paying_it': len(pay), 'relay_senders': ';'.join(f'{k}:{len(v)}:{round(sum(v), 2)}' for k, v in sorted(snd.items())),
         'senders_outside_cohort': sum(1 for k in snd if k.startswith('OUTSIDE')), 'n_cohort_accounts': sum(1 for k in snd if not k.startswith('OUTSIDE'))}
    if ch == 1:
        for act in ('tokentx', 'txlist', 'txlistinternal'):
            copy(RAW / f'xl/etherscan/{x}/1_{act}_p1.json', EV / 'etherscan' / x / f'1_{act}_p1.json')
        tk = [t for t in es(x, 1, 'tokentx') if t['contractAddress'] in OFF]
        ins = [t for t in tk if t['to'] == x]; outs = [t for t in tk if t['from'] == x]
        t_in = sorted(int(t['timeStamp']) for t in ins)
        lags = [(int(t['timeStamp']) - max([s for s in t_in if s <= int(t['timeStamp'])])) / 60 for t in outs if any(s <= int(t['timeStamp']) for s in t_in)]
        outh = {t['hash'].lower() for q in pay for t in q['data'].get('outTxs', []) if t.get('hash')}
        um = [t for t in ins if t['hash'].lower() not in outh and int(t['value']) >= 10000]  # dust under 0.01 = poisoning (rule A12 of PR 36)
        r.update({'credits_matched_to_cohort_relay_payouts': sum(1 for t in ins if t['hash'].lower() in outh), 'unmatched_nonzero_credits': len(um),
                  'unmatched_usd': round(sum(int(t['value']) / 1e6 for t in um), 2), 'unmatched_senders': ';'.join(sorted({t['from'] for t in um})),
                  'dust_poison_credits': sum(1 for t in ins if int(t['value']) < 10000)})
        r.update({'official_stablecoin_in': round(sum(int(t['value']) / 1e6 for t in ins), 6), 'official_stablecoin_out': round(sum(int(t['value']) / 1e6 for t in outs), 6),
                  'distinct_senders_onchain': len({t['from'] for t in ins}), 'sweep_targets': ';'.join(sorted({t['to'] for t in outs})),
                  'median_minutes_credit_to_sweep': round(statistics.median(lags), 1) if lags else ''})
    else:
        prof = json.load(open(RAW / f'solana_profiles/{x}/profile.json'))
        for f in glob.glob(str(RAW / f'solana_profiles/{x}/*.json')):
            if not f.endswith('profile.json'): copy(f, EV / 'solana_profiles' / x / pathlib.Path(f).name)
        outs = collections.Counter()
        for row in prof['rows']:
            if row['self_usdc_delta'] < 0:
                for o, v in row['others'].items():
                    if v > 0: outs[o] += v
        r.update({'credits_matched_to_cohort_relay_payouts': '', 'unmatched_nonzero_credits': '', 'unmatched_usd': '', 'unmatched_senders': '', 'dust_poison_credits': ''})
        r.update({'official_stablecoin_in': 'NOT_COUNTED_SOLANA_ATA_CREDITS_ESCAPE_OWNER_SIGNATURES', 'official_stablecoin_out': round(sum(outs.values()), 6),
                  'distinct_senders_onchain': '', 'sweep_targets': ';'.join(outs), 'median_minutes_credit_to_sweep': ''})
    r['classification'] = ('EXCHANGE_STYLE_DEPOSIT_ADDRESS_' + ('SOLANA_CREDITS_NOT_ENUMERATED' if ch != 1 else 'NON_RELAY_CREDITS_UNATTRIBUTED' if r['unmatched_nonzero_credits'] else 'ALL_CREDITS_FROM_COHORT_RELAY')
                           if r['senders_outside_cohort'] == 0 else 'MIXED_WITH_OUTSIDE_RELAY_SENDERS')
    rows.append(r)
wcsv('kpmg_shared_deposit_addresses.csv', rows)
# 4. market table and statistics (computed by kpmg_markets.py)
copy(RAW / '../out/kpmg_earnings_markets.csv', DATA / 'kpmg_earnings_markets.csv'); copy(RAW / '../out/kpmg_market_stats.json', DATA / 'kpmg_market_stats.json')
copy(RAW / 'sec/sec_summary.json', EV / 'sec' / 'sec_summary.json')
for f in glob.glob(str(RAW / 'sec/fts2_*.json')) + [str(RAW / 'sec/submissions_0001390777.json')]: copy(f, EV / 'sec' / pathlib.Path(f).name)
print('tables written')
# 5. Railgun-funded Maduro accounts (lead MI-RAIL-*): unshield -> distributors -> children -> funding EOAs -> Relay -> accounts
RAIL4 = {'0x2577c59314e3efd45f9dd31067ea329d5a4ea5ec': 'FrostyFox', '0xdbddb8bc3d3dca058a8b19c539effab1363c7417': 'ThunderStrike99',
         '0xdcdd69a814ca1b2c8f0611fd4e10c9376fa61e87': 'W3tLdR9s', '0x86f2c4c9f2f81950d337647e188f77c4aea3c7a8': 'speedrinking'}
RG = '0x19b620929f97b7b990801496c3b361ca5def8c71'; USDC_N = '0x3c499c542cef5e3811e1192ce70d8cc03d5c3359'
HUBS = "0x9a04cbf8c5412d414cb52b8a8624e784bd34dbc0 0xb25ef7f2abf79e195ddebf068e3c61618746d826 0xcd1e7fb382ca615dab08ea49aca47a20eeedeadd 0xdf52757d584954e97b78bd7df472a188c5a4283a 0x340368d84d5f6bff34f06868980e2d4ccf6f1d84 0x4ec1158166477fce3bf9643dc32528eaf20f61a2".split()
rows = []
for h in HUBS:
    for act in ('tokentx', 'txlist'): copy(RAW / f'xl/etherscan/{h}/137_{act}_p1.json', EV / 'etherscan' / h / f'137_{act}_p1.json')
    for t in es(h, 137, 'tokentx'):
        if t['from'] == RG and t['to'] == h:
            rc = RAW / f"xl/polygon/{t['hash']}.eth_getTransactionReceipt.json"; copy(rc, EV / 'chain' / f"polygon_receipt_{t['hash']}.json")
            lg = [l for l in json.load(open(rc))['result']['logs'] if l['address'].lower() == RG and l['topics'][0].startswith('0xd93cf895')][0]
            d = lg['data'][2:]
            rows.append({'edge': 'RAILGUN_UNSHIELD', 'from': RG, 'to': h, 'tx': t['hash'], 'logIndex': int(lg['logIndex'], 16), 'block': int(t['blockNumber']), 'utc': utc(t['timeStamp']),
                         'token': '0x' + d[64 + 64 + 24:192], 'amount_atomic': int(d[256:320], 16), 'fee_atomic': int(d[320:384], 16), 'account': ''})
for eoa_, acct in [('0xe3fe57af4f5b09e6d0a37260aaa42d24c75de1ad', 'FrostyFox'), ('0xfd8cdaa5c6bf63d04d4dcd30f09bfbbfd17a6ef9', 'ThunderStrike99'),
                   ('0xe9ef042ad3507c9c9ebef2b61dcf048402331073', 'W3tLdR9s'), ('0x6bb4c31dc0754a6e0251b48fe1ceed924e849213', 'speedrinking')]:
    for act in ('tokentx', 'txlist'): copy(RAW / f'xl/etherscan/{eoa_}/137_{act}_p1.json', EV / 'etherscan' / eoa_ / f'137_{act}_p1.json')
    for t in es(eoa_, 137, 'tokentx'):
        if t['contractAddress'] != USDC_N or int(t['value']) < 10000: continue
        src = t['from']
        if t['to'] == eoa_:
            for act in ('tokentx', 'txlist'):
                if (RAW / f'xl/etherscan/{src}/137_{act}_p1.json').exists(): copy(RAW / f'xl/etherscan/{src}/137_{act}_p1.json', EV / 'etherscan' / src / f'137_{act}_p1.json')
            par = [u['from'] for u in es(src, 137, 'tokentx') if u['to'] == src and u['contractAddress'] == USDC_N and u['from'] in HUBS]
            rows.append({'edge': 'DISTRIBUTOR_CHILD_TO_FUNDING_EOA' if src not in HUBS else 'DISTRIBUTOR_TO_FUNDING_EOA', 'from': src, 'to': eoa_, 'tx': t['hash'], 'logIndex': '',
                         'block': int(t['blockNumber']), 'utc': utc(t['timeStamp']), 'token': USDC_N, 'amount_atomic': int(t['value']), 'fee_atomic': '',
                         'account': acct + (' parent=' + par[0] if par else '')})
        else:
            rows.append({'edge': 'FUNDING_EOA_TO_RELAY', 'from': eoa_, 'to': t['to'], 'tx': t['hash'], 'logIndex': '', 'block': int(t['blockNumber']), 'utc': utc(t['timeStamp']),
                         'token': USDC_N, 'amount_atomic': int(t['value']), 'fee_atomic': '', 'account': acct})
for p, acct in RAIL4.items():
    for f in glob.glob(str(RAW / f'xl/relay/{p}/p[0-9][0-9][0-9].json')):
        for q in json.load(open(f))['requests']:
            (EV / 'relay' / f"{q['id']}.json").write_text(json.dumps(q, sort_keys=True))
            rows.append({'edge': 'RELAY_ORDER_TO_ACCOUNT', 'from': n(q['user']), 'to': p, 'tx': q['data']['inTxs'][0]['hash'] + '>' + q['data']['outTxs'][0]['hash'], 'logIndex': '',
                         'block': '', 'utc': q['createdAt'], 'token': 'USDC->USDC.e', 'amount_atomic': int(q['data']['metadata']['currencyOut']['amount']), 'fee_atomic': '', 'account': acct})
    copy(RAW / f'positions/v2_{p}.json', EV / 'positions' / f'v2_{p}.json')
copy(RAW / 'positions/v2_0xc2dba869680b8c7a580ed7d1a9bfd9b329ca86cf.json', EV / 'positions' / 'v2_0xc2dba869680b8c7a580ed7d1a9bfd9b329ca86cf.json')  # fifth winner of the tree
wcsv('railgun_maduro_edges.csv', rows)
# 6. Biden-pardon shared deposit address (Bitquery C6), reproduced from receipts
KR = '0x0a65fdd872da9fc9a16a37a9c10be8e8362d8d7e'; POOL = '0xd36ec33c8bed5a9f7b6630855f1533455b98a418'
T = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
rows = []
for a, lab in [('0xd9be4e8f031a5beaa1f0d29ceff2826e3cc91d98', 'd9be'), ('0xa416a5c03381c90b94e4c1881b0494281e3e025e', 'a416')]:
    for f in sorted(glob.glob(str(RAW / f'xl/polymarket/{a}/v2activity_p*.json'))):
        if f.endswith('.meta.json'): continue
        for r in json.load(open(f))['data']:
            if r['type'] != 'WITHDRAWAL': continue
            rc = RAW / f"xl/polygon/{r['transaction_hash']}.eth_getTransactionReceipt.json"
            for l in json.load(open(rc))['result']['logs']:
                if l['topics'][0] == T and len(l['topics']) == 3 and '0x' + l['topics'][2][26:] == KR and '0x' + l['topics'][1][26:] in (a, POOL):
                    copy(rc, EV / 'chain' / f"polygon_receipt_{r['transaction_hash']}.json")
                    rows.append({'account': lab, 'proxy': a, 'tx': r['transaction_hash'], 'logIndex': int(l['logIndex'], 16), 'utc': utc(r['timestamp']), 'token': l['address'].lower(),
                                 'via': 'UNISWAP_V3_USDCe_USDC_POOL' if '0x' + l['topics'][1][26:] == POOL else 'DIRECT', 'amount_atomic': int(l['data'], 16), 'to': KR})
for act in ('tokentx', 'txlist'): copy(RAW / f'xl/etherscan/{KR}/137_{act}_p1.json', EV / 'etherscan' / KR / f'137_{act}_p1.json')
wcsv('biden_pardon_shared_deposit.csv', rows)
# 7. Snoorrason 14 Oct long-form text (two mirrors + X syndication object): text only, raw bodies stay outside git
fx = json.load(open(RAW / 'x/fxtwitter_2110285369748963671.json'))['tweet']; vx = json.load(open(RAW / 'x/vxtwitter_2110285369748963671.json'))
sy = json.load(open(RAW / 'x/syndication_2110285369748963671.json'))
(EV / 'x' / 'snoorrason_2110285369748963671.json').write_text(json.dumps({
    'id': '2110285369748963671', 'author': sy['user']['screen_name'], 'created_at': sy['created_at'], 'edit_tweet_ids': sy['edit_control']['edit_tweet_ids'],
    'note_tweet_id': sy['note_tweet']['id'], 'syndication_truncated_text': sy['text'], 'fxtwitter_text': fx['text'], 'vxtwitter_text': vx['text'],
    'raw_sha256': {k: json.load(open(RAW / f'x/{k}_2110285369748963671.meta.json'))['sha256'] for k in ('fxtwitter', 'vxtwitter', 'syndication')}}, indent=1, ensure_ascii=False))
print('railgun, biden and X tables written')
# 8. Every Polymarket account funded by the same Railgun-originated distribution tree (chain-only Relay resolution, then API for the rest)
M = {m['conditionId']: m for m in json.load(open(RAW / 'gamma/rail_markets.json'))}
copy(RAW / 'gamma/rail_markets.json', EV / 'gamma' / 'rail_markets.json')
kids = set(open(RAW / 'rail_kids.txt').read().split()); HUBSET = set(HUBS)
resolved = {r['deposit_tx']: dict(r, method='CHAIN_INPUT_TAIL') for r in json.load(open(RAW / 'relay_chain/resolved_all.json')) if r.get('recipient')}
for f in glob.glob(str(RAW / 'relay_by_hash/*.json')):
    if f.endswith('meta.json'): continue
    h = pathlib.Path(f).name[:-5]; q = (json.load(open(f)).get('requests') or [None])[0]
    if q and h not in resolved and q['data']['metadata']['currencyOut']['currency']['chainId'] == 137:
        (EV / 'relay' / f"{q['id']}.json").write_text(json.dumps(q, sort_keys=True))
        resolved[h] = {'deposit_tx': h, 'depositor': n(q['user']), 'recipient': n(q['recipient']), 'payout_tx': q['data']['outTxs'][0]['hash'], 'request_id_from_input_tail': q['id'],
                       'payout_atomic': int(q['data']['metadata']['currencyOut']['amount']), 'method': 'RELAY_API_BY_HASH'}
for h, r in resolved.items():
    if r['method'] == 'CHAIN_INPUT_TAIL':
        copy(RAW / f'relay_chain/deposit_tx_{h}.json', EV / 'relay_chain' / f'deposit_tx_{h}.json')
        copy(RAW / f"relay_chain/payout_tx_{r['payout_tx']}.json", EV / 'relay_chain' / f"payout_tx_{r['payout_tx']}.json")
rows = []
for h, r in resolved.items():
    a = r['recipient']; act = []
    for f in sorted(glob.glob(str(RAW / f'xl/polymarket/{a}/v2activity_p*.json'))):
        if not f.endswith('.meta.json'): act += json.load(open(f))['data']
    prof = json.load(open(RAW / f'xl/polymarket/{a}/profile.json')) if (RAW / f'xl/polymarket/{a}/profile.json').exists() else {}
    d = r['depositor'].lower()
    for t in [x for x in act if x['type'] == 'TRADE']:
        m = M.get(t['condition_id'])
        win = json.loads(m['outcomes'])[json.loads(m['outcomePrices']).index('1')] if m else None
        rows.append({'proxy': a, 'profile_created_utc': prof.get('createdAt'), 'funding_wallet': d, 'funding_lineage': 'DISTRIBUTOR_CHILD' if d in kids else 'DISTRIBUTOR' if d in HUBSET else 'OTHER',
                     'relay_deposit_tx': h, 'relay_payout_tx': r['payout_tx'], 'request_id': r['request_id_from_input_tail'], 'resolution_method': r['method'],
                     'credited_atomic': r['payout_atomic'], 'market': t['title'], 'condition_id': t['condition_id'], 'side': t['side'], 'outcome': t['outcome'], 'price': round(t['price'], 4),
                     'usdc': round(t['usdc_size'], 6), 'shares': round(t['size'], 6), 'trade_utc': utc(t['timestamp']), 'trade_tx': t['transaction_hash'],
                     'winning_outcome': win, 'won': t['side'] == 'BUY' and t['outcome'] == win, 'payout_if_redeemed': round(t['size'], 6) if (t['side'] == 'BUY' and t['outcome'] == win) else 0.0})
rows.sort(key=lambda x: x['profile_created_utc'] or '')
wcsv('railgun_tree_accounts.csv', rows)
un = [r for r in json.load(open(RAW / 'relay_chain/resolved_all.json')) if r['deposit_tx'] not in resolved]
wcsv('railgun_tree_unresolved_deposits.csv', [{'deposit_tx': r['deposit_tx'], 'depositor': r['depositor'], 'deposit_atomic': r['deposit_atomic'], 'request_id': r['request_id_from_input_tail'],
                                               'status': 'UNRESOLVED_NO_POLYGON_PAYOUT_FOUND_API_PENDING'} for r in un] or [{'deposit_tx': '', 'depositor': '', 'deposit_atomic': '', 'request_id': '', 'status': 'NONE'}])
print('railgun tree accounts', len({r['proxy'] for r in rows}), 'unresolved deposits', len(un))
