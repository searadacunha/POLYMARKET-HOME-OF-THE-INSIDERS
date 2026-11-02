"""Controls on the known hard cases. Run: python3 tests/test_forensics.py. Reads state/ and the HTTP cache; any uncached read goes to public nodes."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
sys.dont_write_bytecode = True
import evm
import net
import walk

STATE = ROOT / 'state'
ZERO = evm.ZERO
BRACE_KEY = '0xc852b0938f5ad79b640d105ed11c14499454af26'
KRABEN_KEY = '0x101b5f4dc0886c32e2b75972101aeaf9f338fb65'
OULD_KEY = '0x1b500b6c40a2ff0930e540e8f53c559a32e75f2c'
OULD_WD = '0x909d9602d5ad975b2f30c66d4a058592306e2468a002dd0a691170b61677a6f1'
DIRECT_TX = '0xd07bea20a22d9381e0ab364e7a7421776318c6f4aa7258799638472ad7092b98'
PUSD = '0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb'
TRANSFER = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
walks = {p.stem[5:]: json.loads(p.read_text()) for p in STATE.glob('walk_*.json')}
pairs = json.loads((STATE / 'pairs.json').read_text())
recon = {r['case']: r for r in json.loads((STATE / 'reconcile.json').read_text())}
results = []


def check(name, ok, detail=''):
    results.append((name, bool(ok), detail))
    print(('PASS' if ok else 'FAIL'), name, detail)


# 1. pUSD burn of OuldLm3alem: the zero address is never a destination or a funder.
rc = net.rpc('eth_getTransactionReceipt', [OULD_WD], 137)
burns = [l for l in rc['logs'] if l['address'].lower() == PUSD and l['topics'][0] == TRANSFER and l['topics'][2][-40:] == ZERO[2:]]
check('ould_burn_exists_on_chain', len(burns) == 1 and round(int(burns[0]['data'], 16) / 1e6, 2) == 77050.77, f'{len(burns)} burn, {int(burns[0]["data"], 16) / 1e6}')
bad = [(s, e['tx']) for s, w in walks.items() for e in w['edges'] if ZERO in (e['src'], e['dst']) and e['role'] not in ('mint', 'burn')]
check('zero_address_only_as_mint_or_burn', not bad, str(bad[:3]))
bad = [s for s, w in walks.items() for x in w['stops'] if x['address'] == ZERO]
check('zero_address_never_a_stop_or_node', not bad, str(bad[:3]))
ould = walks['ouldlm3alem']
check('ould_real_destination_is_the_key', any(l['local_tx'] == OULD_WD or l['recipient'].lower() == OULD_KEY for l in ould['relay_links']) or any(e['dst'] == OULD_KEY for e in ould['edges']))

# 2. brace227 -> kraben006: the positive control. The scan must find it, on two sources.
hits = [d for d in pairs['direct'] if d['tx'] == DIRECT_TX]
check('direct_link_found_by_the_scan', len(hits) == 1 and hits[0]['src'] == BRACE_KEY and hits[0]['dst'] == KRABEN_KEY, str(hits[:1])[:160])
t = net.rpc('eth_getTransactionByHash', [DIRECT_TX], 1)
check('direct_link_second_source_node', t['from'].lower() == BRACE_KEY and t['to'].lower() == KRABEN_KEY and int(t['value'], 16) == int(hits[0]['raw']), f"value {int(t['value'], 16) / 1e18}")

# 3. Mutualised funders must not create pairs.
services = {x['address'] for x in pairs['shared'] if x['cls'] != 'PERSONAL_SIZED'}
for a in ('0x4cd00e387622c35bddb9b4c962c136462338bc31', '0xf70da97812cb96acdf810712aa562db8dfa3dbef'):
    check(f'relay_never_personal_{a[:8]}', walk.classify_evm(a, 1)['cls'] != 'PERSONAL_SIZED')
personal = {x['address'] for x in pairs['shared'] if x['cls'] == 'PERSONAL_SIZED'}
for a in ('0xc8a6871d4ec4dae64f605db0f8a0b3d9ef928d64', '0xc1d13492285eb664951e201bf7c80c7c6318a1b5', '0x58f298e3bf930886ab7639f4d71f892d5f1f0214', '0x0ce9bdf38714143043b1d36de9bd90f7335bf06d', '0xee7ae85f2fe2239e27d9c1e23fffe168d63b4055', 'BmFdpraQhkiDQE6SnfG5omcA1VwzqfXrwtNYBwWTymy6', 'GxjcMTWWDcKx5sxnHkNfPtuTSfV9cLgVkw3G7KvMnvBW', '0xc066ac5d385419b1a8c43a0e146fa439837a8b8c', '0xe3478b0bb1a5084567c319096437924948be1964'):
    check(f'known_hub_not_a_personal_link_{a[:8]}', a not in personal)

# 4. Double counting.
for s, w in walks.items():
    keys = [(e['direction'], e['tx'], e['kind'], e.get('contract'), e['src'], e['dst'], e['raw']) for e in w['edges']]
    check(f'no_duplicate_edges_{s}', len(keys) == len(set(keys)))
all_dep = [d['tx'] for c in (json.loads(p.read_text()) for p in (walk.INV / 'cases').glob('*.json')) for d in c['deposits']]
all_wd = [d['tx'] for c in (json.loads(p.read_text()) for p in (walk.INV / 'cases').glob('*.json')) for d in c['withdrawals']]
check('no_deposit_counted_twice', len(all_dep) == len(set(all_dep)) == 46, str(len(all_dep)))
check('no_withdrawal_counted_twice', len(all_wd) == len(set(all_wd)) == 25, str(len(all_wd)))
check('no_tx_both_deposit_and_withdrawal', not set(all_dep) & set(all_wd))

# 5. Attribution: a contract or a bridge deposit address is not a person, and a deposit wallet's owner is read, not assumed.
check('vault_is_a_contract', walk.classify_evm('0xc8a6871d4ec4dae64f605db0f8a0b3d9ef928d64', 137)['kind'] == 'CONTRACT')
check('swftswap_is_a_service', walk.classify_evm('0xc1d13492285eb664951e201bf7c80c7c6318a1b5', 1)['cls'] == 'SERVICE')
check('7702_bridge_address_is_delegated', walk.classify_evm('0x8e43af995577339436e071990e524ebfe6c09865', 137)['kind'] == 'EIP7702_DELEGATED_EOA')
owner = net.rpc('eth_call', [dict(to='0x873848cd27784900e193611845fc3fd2c4716d03', data='0x8da5cb5b'), 'latest'], 137)
check('owner_read_on_chain', '0x' + owner[-40:] == BRACE_KEY)

# 6. Reconciliation: mints and burns equal the API, and the computed pUSD balance equals the balance now.
for s, r in recon.items():
    check(f'mints_match_api_{s}', r['deposits_matched'] == r['deposits_total'] and r['mints_outside_are_redeem'], f"{r['deposits_matched']}/{r['deposits_total']}, {len(r['mints_outside_api'])} others, all REDEEM")
    check(f'burns_match_api_{s}', r['withdrawals_matched'] == r['withdrawals_total'], f"{r['withdrawals_matched']}/{r['withdrawals_total']} outside {len(r['burns_outside_api'])}")
    check(f'balance_conserved_{s}', abs(r['computed_balance'] - r['balance_now']) < .01, f"computed {r['computed_balance']:.6f} now {r['balance_now']:.6f}")

# 7. The unnamed wallet funded by brace227's key: two sources, and nothing that rests on one explorer.
OTHER_KEY = '0x48ec106cf690edd58fcd6df1e8b6abfc16dab12d'
OTHER_WALLET = '0xa8e64a3c08d1e2a4e9f25a2dd33b8ac3458f74a5'
owner = net.rpc('eth_call', [dict(to=OTHER_WALLET, data='0x8da5cb5b'), 'latest'], 137)
check('other_wallet_owner_read_on_chain', '0x' + owner[-40:] == OTHER_KEY)
sends = [r for r in evm.history(BRACE_KEY, 1)[0] if r['dst'] == OTHER_KEY and r.get('known') and int(r['raw']) > 0]
check('brace_key_sends_two_usdc_transfers', sorted(int(r['raw']) for r in sends) == [2210000000, 2960000000], str([r['raw'] for r in sends]))
for r in sends:
    rc = net.rpc('eth_getTransactionReceipt', [r['tx']], 1)
    ok = any(l['topics'][0] == TRANSFER and l['topics'][1][-40:] == BRACE_KEY[2:] and l['topics'][2][-40:] == OTHER_KEY[2:] for l in rc['logs'] if len(l['topics']) == 3)
    check(f"brace_key_send_on_node_{r['tx'][:10]}", ok)
activity = json.loads((STATE / 'wallet_0xa8e6_activity.json').read_text())
trades = [r for r in activity if r['type'] == 'TRADE']
check('other_wallet_only_kane_yes', len(trades) == 16 and {(r['title'], r['outcome']) for r in trades} == {("Will Harry Kane win the 2026 Ballon d'Or?", 'Yes')}, str({(r['title'], r['outcome']) for r in trades}))
first_in = min(r['at'] for r in evm.history(OTHER_KEY, 1)[0] if r['dst'] == OTHER_KEY and r.get('known') and r['token'] == 'USDC')
check('other_key_first_value_comes_from_brace', first_in == min(r['at'] for r in sends))
personal = json.loads((STATE / 'personal_wallets.json').read_text())
check('only_one_other_active_wallet_around_the_eleven', [x['wallet'] for x in personal if x['activity_rows']] == [OTHER_WALLET], str(len(personal)))

# 8. No labelled mixer or privacy contract in any history read, and the label test itself works.
import labels as L
check('mixer_labels_work', L.lookup('0x910Cbd523D972eb0a6f4cAe4618aD62622b39DbF', 1)['category'] == 'mixer_or_privacy')
mixers = []
for s, w in walks.items():
    for n in w['nodes']:
        if n['chain'] == walk.SOLANA:
            continue
        for r in evm.history(n['address'], n['chain'])[0]:
            for a in (r['src'], r['dst']):
                lab = L.lookup(a, n['chain']) if a else None
                if lab and lab['category'] == 'mixer_or_privacy' and r.get('known', True):
                    mixers.append((s, a, r['tx']))
check('no_labelled_mixer_in_histories', not mixers, str(mixers[:3]))

failed = [r for r in results if not r[1]]
print(f'\n{len(results) - len(failed)} passed, {len(failed)} failed')
(ROOT / 'state/tests.json').write_text(json.dumps(results))
sys.exit(1 if failed else 0)
