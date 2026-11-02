"""INCIDENT_TIMELINE.csv, ADDRESSES.csv and MATCH_CANDIDATES.csv. Roles are written here, every other value is read from the data."""
import csv
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import chainlib as c
import labels
import tokens

ROOT = Path(__file__).resolve().parent.parent
RUNS = ROOT / 'state/runs'
STATEMENTS = [
    ('2026-05-22 08:22:00', 'A_0522', 'ZachXBT: community alert, admin address compromised, >$520K (last edit time shown by t.me, timezone of the page not established)', 'https://t.me/investigations/327'),
    ('2026-05-22 08:49:39', 'A_0522', 'PeckShield: 2 addresses drained ~$520K, part deposited into ChangeNOW', 'https://x.com/PeckShieldAlert/status/2057745696674218049'),
    ('2026-05-22 09:01:39', 'A_0522', 'Josh Stevens: not a contract hack, very old private key', 'https://x.com/devjoshstevens/status/2057748715314598034'),
    ('2026-05-22 13:06:45', 'A_0522', 'Josh Stevens: $164,000 of the $573,200 frozen with ZachXBT, Bitcoin Vietnam, ChangeNOW; 6-year-old key in the top-up config', 'https://x.com/devjoshstevens/status/2057810397990724009'),
    ('2026-06-25 14:43:18', 'C_0625', 'Polymarket: third-party vendor compromised, malicious script, refunds in full', 'https://x.com/PolymarketTrade/status/2070155882906730671'),
    ('2026-06-25 17:37:57', 'C_0625', 'Bubblemaps: fewer than 15 accounts, $3M, list of 8 accounts and 6 wallets', 'https://x.com/bubblemaps/status/2070199833755799892'),
    ('2026-10-29 17:38:00', 'D_1029', 'Polymarket status: unauthorized activity affecting user wallets', 'https://status.polymarket.com/cmvvek1i90eme14ruga1z6tuj'),
    ('2026-10-30 20:07:00', 'D_1029', 'Polymarket postmortem: $3.9M returned, $2.7M plus $1.2M pause-related', 'https://status.polymarket.com/cmvvek1i90eme14ruga1z6tuj'),
]
ROLES = {
    '0x91430cad2d3975766499717fa0d66a78d814e5c5': ('A_0522', 137, 'Compromised admin EOA', 'Sends all stolen funds to the attacker; tag UMA CTF Adapter Admin + Compromised', 'CHAINE+ATTRIBUTION'),
    '0x8f98075db5d6c620e8d420a8c516e2f2059d9b91': ('A_0522', 137, 'Attacker wallet (May)', 'Receives 175 POL and 74 USDC.e transfers from the admin; named by ZachXBT', 'CHAINE'),
    '0x871d7c0f9e19001fc01e04e6cdfa7fa20f929082': ('A_0522', 137, 'Automatic POL top-up wallet', '244 transfers of 5000 POL to the admin on 22/05, same 5000 unit to other wallets later', 'CHAINE'),
    '0xf61e39c7eb1e2ff5af3a24bca88d40fd11594805': ('A_0522', 137, 'Automatic USDC.e top-up wallet', '88 transfers of 5000 USDC.e to the admin on 22/05', 'CHAINE'),
    '0x2d507657ca4ebcc8f9a38f6764c07310b66dea54': ('A_0522', 137, 'Treasury-like Polymarket wallet', 'Refills both top-up wallets and funds the June refund payer; behaviour, no tag', 'CHAINE+INFERENCE'),
    '0xf43d55f3a8b7484ed4b6931f93cb6f9ef5dd369d': ('A_0522', 137, 'Replacement of the admin', 'Takes the same top-ups and the same adapter payments from 22/05 10:13', 'CHAINE+INFERENCE'),
    '0xff4c483c4c7f72f78077527521fce4b2595e454f': ('A_0522', 137, 'Gas funder of the attacker', '332.76 POL at 05:55:56; since January 389 resolve calls on UMA adapters; owner unknown', 'CHAINE'),
    '0xc0126535cbc6f70fc71d41bbc266d76321159efe': ('A_0522', 137, 'Funder of the gas funder', '200 POL 21/01, 333 POL 13/05', 'CHAINE'),
    '0x8669debfa2b60f73300a95140b02408263cece01': ('A_0522', 137, 'Funder of the gas funder', '599.91 POL 01/06; 318012.53 POL to the treasury-like wallet 13/01; immediate funder of Ballon comparator 0xf797d4d1c038d1eb0593edae0e66bf8e4b2e0bf2', 'CHAINE'),
    '0x6656680f7992c6dab0975ef7bdaf4693a24519ee': ('A_0522', 137, 'Receives admin dust on 19/06', '128 USDC.e and 0.9567 POL from the admin, 599.85 POL from the gas funder within 13 s', 'CHAINE'),
    '0x7b83d2b5bca3b52c75651369c1cd926ff52aa651': ('A_0522', 137, 'Receives admin funds in September', '5 and 201.41 POL, 50 USDC.e', 'CHAINE'),
    '0xf2020cbfc13fd5d4cb2da0ff8ae2d2c093c1c423': ('A_0522', 137, 'ChangeNOW candidate hub', 'No public tag read; treasury flows with ChangeNOW 22; weak OSINT; operator test swap reported in cn_pm_sakana', 'CHAINE+ATTRIBUTION FAIBLE'),
    '0x6976d8025229db5f54bc899dd3dbc9285423896b': ('A_0522', 137, 'ChangeNOW candidate hub (POL)', 'No public tag read; 1196570 POL to ChangeNOW 22 in 3 days; weak OSINT', 'CHAINE+ATTRIBUTION FAIBLE'),
    '0x4958f6c329b61404b1cfd0ec8a44600a9486bd0a': ('A_0522', 137, 'ChangeNOW 22', 'PolygonScan name tag reported second-hand, Blockscout metadata empty on 02/11', 'ATTRIBUTION SECONDE MAIN'),
    '0x89c5151236de544d077fc69813a4db89224ee8a1': ('A_0522', 137, 'Unlabeled service', 'Takes 120006.14 USDC.e and 104954.99 POL; isolates 70000 USDC.e that reach the Polymarket admin Safe; BitcoinVN by elimination only', 'CHAINE+INFERENCE'),
    '0x3cafc13213f9eed5ac1333ae3eb9c7d4e5d34188': ('A_0522', 137, 'Isolation wallet of the return', 'Fresh; 100 POL + 70000 USDC.e from 0x89c5, then 70000 USDC.e to the Safe', 'CHAINE'),
    '0x3dce0a29139a851da1dfca56af8e8a6440b4d952': ('A_0522', 137, 'Polymarket admin Safe', '3-of-7 Safe; addAdmin/removeAdmin/addOperator on tagged Polymarket contracts; declares itself in on-chain messages of 30/10', 'CHAINE'),
    '0x9c23eddf6f2a0fd7b738b1c4a1de35b84292f8f9': ('D_1029', 137, 'Signer of the Safe, sends the on-chain message', 'Owner of the Safe; 0.025 POL with text to each of the 4 October wallets', 'CHAINE'),
    '0xdd5535163619aeae882532a9a6393d18a309fff7': ('A_0522', 137, 'Dormant stolen USDC.e', '35000 USDC.e, nonce 0', 'CHAINE'),
    '0x0a804f680640be6228d4ce0d73c8f5fb5f9a2e68': ('A_0522', 137, 'Dormant stolen USDC.e', '30000 USDC.e, nonce 0', 'CHAINE'),
    '0x2ed3e9cc75aa5a2e7d7f4b2f006a2e0fd08e7e04': ('A_0522', 137, 'Dormant stolen USDC.e', '2900 USDC.e, nonce 0', 'CHAINE'),
    '0x0fb2f44ecad0d1b798a7317629acb85a7fcdcad8': ('A_0522', 137, 'Dormant stolen POL', '344934.87 POL, nonce 0', 'CHAINE'),
    '0xca07efe820838bfc70f489a60eed9cb09c4cfd76': ('A_0522', 137, 'Dormant stolen POL', '79907.95 POL, nonce 0', 'CHAINE'),
    '0xe65b1c586757c5510b60f998eebb14c1ef71e1ed': ('C_0625', 1, 'Consolidation wallet (June)', '1892.9167 ETH from 6 wallets; 1788.516 ETH leaves 26/06', 'CHAINE'),
    '0x71d4249079684479f2651745fa2fcd79c9b45f53': ('C_0625', 137, 'FixedFloat 3', 'Pays POL gas of 3 staging wallets at 00:09-00:11 UTC; also takes 544 POL of the May trail; tag only', 'CHAINE+ATTRIBUTION'),
    '0xb92fe925dc43a0ecde6c8b1a2709c170ec4fff4f': ('C_0625', 137, 'Relay Router', 'Tag; takes pUSD in June, pays POL to the October attacker', 'CHAINE+ATTRIBUTION'),
    '0x4cd00e387622c35bddb9b4c962c136462338bc31': ('C_0625', 137, 'Relay Depository', 'Tag; Relay requests/v2 records', 'CHAINE+PROTOCOLE'),
    '0xf70da97812cb96acdf810712aa562db8dfa3dbef': ('C_0625', 1, 'Relay Solver', 'Tag', 'CHAINE+ATTRIBUTION'),
    '0x9008d19f58aabd9ed0d60971565aa8510560ab41': ('C_0625', 1, 'CoW Protocol settlement', 'Tag; USDC to ETH', 'CHAINE+ATTRIBUTION'),
    '0xd90e2f925da726b50c4ed8d0fb90ad053324f31b': ('C_0625', 1, 'Tornado.Cash Router', 'Tags Blockscout and dawsbot', 'CHAINE+ATTRIBUTION'),
    '0xac9f360ae85469b27aeddeafc579ef2d052ad405': ('C_0625', 1, 'Railgun Relay Adapt', 'Tag', 'CHAINE+ATTRIBUTION'),
    '0x71a7b22d671c93a7a40edff2ffed52dd64ed3235': ('C_0625', 137, 'Refund payer', 'Funded in pUSD by the treasury-like wallet; pays amounts rounded up from the losses', 'CHAINE+INFERENCE'),
    '0x3f99139f1c5854bb628c2e576aaf638e99dffc18': ('D_1029', 137, 'Attacker wallet (October)', '981 Relay inflows; named in Polymarket on-chain message', 'CHAINE'),
    '0xe4c4c39c1733e1c7c06b79f97ed442b68df41ec6': ('D_1029', 137, 'October exit wallet', '18613584 POL; named in Polymarket on-chain message', 'CHAINE'),
    '0x5392587814ce8c6af6789764f88e5e9ab0b9962c': ('D_1029', 137, 'October exit wallet', '4295442 POL; named in Polymarket on-chain message', 'CHAINE'),
    '0xc91ee0574a14446de200923729c349b9cae19b60': ('D_1029', 137, 'October exit wallet', '5727258.45 POL; named in Polymarket on-chain message', 'CHAINE'),
    '0xdd3d72c53ff982ff59853da71158bf1538b3ceee': ('', 1, 'ChangeNOW: Hot Wallet 3 (study target)', 'Blockscout tag, on-chain links per ChangeNOW-proof; chain 1 only, nonce 0 on Polygon; no outflow 29/10', 'ATTRIBUTION CORROBOREE'),
    '0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b': ('', 1, 'ChangeNOW Dep: 0x3f3...07B (study target)', 'Etherscan name tag, service wallet not a deposit address per ChangeNOW-proof; first tx 10/08, so absent in May and June', 'ATTRIBUTION CORROBOREE'),
    '0xeba88149813bec1cccccfdb0dacefaaa5de94cb1': ('', 1, 'ChangeNOW: Hot Wallet 4', 'Etherscan and Blockscout tags per ChangeNOW-proof', 'ATTRIBUTION CORROBOREE'),
}


def write(name, rows):
    with (ROOT / name).open('w', newline='') as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0]))
        wr.writeheader()
        wr.writerows(rows)


def timeline():
    rows = []
    for r in csv.DictReader((ROOT / 'FUND_FLOW.csv').open()):
        rows.append(dict(utc=r['utc'], incident=r['incident'], type='transfer', event=r['note'], chain=r['chain'], tx=r['tx'], block=r['block'], src=r['src'], dst=r['dst'], asset=r['asset'], raw=r['raw'], decimals=r['decimals'], amount=r['amount'], fee_wei=r['fee_wei'], source=''))
    for utc, inc, text, url in STATEMENTS:
        rows.append(dict(utc=utc, incident=inc, type='statement', event=text, chain='', tx='', block='', src='', dst='', asset='', raw='', decimals='', amount='', fee_wei='', source=url))
    rows.sort(key=lambda r: (r['utc'], r['incident'], r['tx']))
    write('INCIDENT_TIMELINE.csv', rows)
    return len(rows)


def addresses():
    rows = {}
    for a, (inc, chain, role, why, level) in ROLES.items():
        meta = labels.metadata([a], chain)
        tags = labels.lookup(a, chain, meta)
        rows[a] = dict(address=a, chain=chain, incident=inc, role=role, justification=why, evidence_level=level, labels=' | '.join(sorted({x['name'] for x in tags})), label_sources=' | '.join(sorted({x['source'] for x in tags})))
    for name, inc, chain in (('may_polygon_full.json', 'A_0522', 137), ('june_eth.json', 'C_0625', 1), ('oct_polygon.json', 'D_1029', 137)):
        for a, n in json.loads((RUNS / name).read_text()).get('nodes', {}).items():
            if a in rows or n.get('kind') == 'unread':
                continue
            tags = n.get('labels', [])
            rows[a] = dict(address=a, chain=chain, incident=inc, role='service reached by the walk' if labels.is_service(tags) else 'intermediate on the walk', justification=f"depth {n.get('depth')}, nonce {n.get('nonce')}, stop: {n.get('stop', '')}", evidence_level='CHAINE' if not tags else 'CHAINE+ATTRIBUTION', labels=' | '.join(sorted({x['name'] for x in tags})), label_sources=' | '.join(sorted({x['source'] for x in tags})))
    core = json.loads((RUNS / 'june_core.json').read_text())
    pusd = '0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb'
    staging = {k.split(':')[1] for k in core if k.startswith('137:')} - {'0xe65b1c586757c5510b60f998eebb14c1ef71e1ed'}
    for a in sorted(staging):
        rows.setdefault(a, dict(address=a, chain='137;1', incident='C_0625', role='Staging wallet (June)', justification='Receives pUSD from victims or from a staging wallet', evidence_level='CHAINE', labels='', label_sources=''))
    for a in sorted(staging):
        for e in core['137:' + a]:
            if e['dst'] == a and e['token'] == pusd and e['src'] not in staging and c.amount(e) >= 100:
                rows.setdefault(e['src'], dict(address=e['src'], chain=137, incident='C_0625', role='Drained Polymarket account', justification='Sends pUSD to a staging wallet on 25/06', evidence_level='CHAINE', labels='', label_sources=''))
    write('ADDRESSES.csv', sorted(rows.values(), key=lambda r: (r['incident'], r['role'], r['address'])))
    return len(rows)


def candidates():
    cands = json.loads((RUNS / 'match_cands.json').read_text())
    big = {x['payout_tx']: x for x in json.loads((RUNS / 'big_cands.json').read_text())}
    tests = {(r['deposit_tx']): r for r in csv.DictReader((RUNS / 'match_tests.csv').open()) if r['band'] == 'main' and r['hours'] == '48'}
    rows = []
    for x in cands:
        d, r = x['d'], x['r']
        e = r['e']
        t = tests[d['tx']]
        b = big.get(e['tx'], {})
        against = ['pooled service wallets: inventory pays any client', f"same rule in calendar controls gives {t['calendar_mean']} on average, placebo amounts {t['placebo_mean']}"]
        if d['usd'] < 1000:
            against.append('deposit too small for any amount match to mean anything')
        if b.get('status') == 'ALREADY_ACTIVE':
            against.append('recipient active before the payout')
        if b.get('next_hops'):
            against.append('next hops ' + ', '.join(n[0] for n in b['next_hops']))
        rows.append(dict(incident=d['incident'], deposit_tx=d['tx'], deposit_usd=round(d['usd'], 2), hub=d['hub'], payout_tx=e['tx'], payout_block=e['block'], payout_utc=c.utc(e['ts']), payout_source=r['source'], chain=r['chain'], recipient=e['dst'], asset=tokens.canonical_symbol(r['chain'], e), raw=e['raw'], decimals=e['decimals'], amount=c.amount(e), usd=round(r['usd'], 2), delay_h=round((e['ts'] - d['ts']) / 3600, 2), implied_fee=round(1 - r['usd'] / d['usd'], 4), link_level='4 statistical similarity only', recipient_status=b.get('status', 'not read'), placebo_p_48h=t['placebo_p'], counterarguments='; '.join(against)))
    rows.sort(key=lambda r: (-r['deposit_usd'], -r['usd']))
    write('MATCH_CANDIDATES.csv', rows)
    return len(rows)


if __name__ == '__main__':
    print('timeline', timeline(), 'addresses', addresses(), 'candidates', candidates())
