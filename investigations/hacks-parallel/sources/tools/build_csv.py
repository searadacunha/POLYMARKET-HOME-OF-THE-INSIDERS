"""Writes the CSV deliverables from the saved runs. Spoof tokens and dust never enter FUND_FLOW: recognized contracts and worth_following only. Hashes and addresses are copied from the data, never typed."""
import csv
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import chainlib as c
import cn_common as cc
import flows
import labels
import tokens

ROOT = Path(__file__).resolve().parent.parent
RUNS = ROOT / 'state/runs'
ADM, ATT = '0x91430cad2d3975766499717fa0d66a78d814e5c5', '0x8f98075db5d6c620e8d420a8c516e2f2059d9b91'
A871, F61 = '0x871d7c0f9e19001fc01e04e6cdfa7fa20f929082', '0xf61e39c7eb1e2ff5af3a24bca88d40fd11594805'
GAS = '0xff4c483c4c7f72f78077527521fce4b2595e454f'
F2020, H6976, H89C5 = '0xf2020cbfc13fd5d4cb2da0ff8ae2d2c093c1c423', '0x6976d8025229db5f54bc899dd3dbc9285423896b', '0x89c5151236de544d077fc69813a4db89224ee8a1'
SAFE, HOLD = '0x3dce0a29139a851da1dfca56af8e8a6440b4d952', '0x3cafc13213f9eed5ac1333ae3eb9c7d4e5d34188'
E65B = '0xe65b1c586757c5510b60f998eebb14c1ef71e1ed'
PUSD = '0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb'
OCT = '0x3f99139f1c5854bb628c2e576aaf638e99dffc18'
STAGING = {x.lower() for x in '0xE42640650C634ad300a47635856AafBbBA1d2222 0xC771A30a7c1aCA828eeEF7B822ac864a64cBaAe2 0x51Cf782223289C05568F9F7Dede8CB1bC2f9c5Ca 0x10366AdBB5C4101A65C840Da6639546179C5A107 0x2eb06B8d81c6f26d9cb26327878999aC7db3891B 0xC44F2Ca6B30A54d17a62ceF8FAdaF2e8C8632eC4 0x7BCECe0d8fd92ECCf39Bc35242c6D9aAc0aA75A6'.split()}
tokens.RECOGNIZED[137][PUSD] = 'pUSD'
FIELDS = ['incident', 'chain', 'utc', 'tx', 'block', 'src', 'dst', 'asset', 'token_contract', 'decimals', 'raw', 'amount', 'kind', 'log_or_trace', 'fee_wei', 'usd_day_price', 'note']


def load(name):
    return json.loads((RUNS / name).read_text())


def row(incident, e, note=''):
    chain = e['chain']
    sym = tokens.canonical_symbol(chain, e)
    usd = ''
    if sym in cc.PRICE_KEY:
        usd = round(c.amount(e) * cc.price(sym, e['ts']), 2)
    elif sym == 'pUSD':
        usd = round(c.amount(e) * cc.price('USDC', e['ts']), 2)
    return dict(incident=incident, chain=chain, utc=c.utc(e['ts']), tx=e['tx'], block=e['block'], src=e['src'], dst=e['dst'], asset=sym, token_contract=e['token'], decimals=e['decimals'], raw=e['raw'], amount=repr(c.amount(e)), kind=e['kind'], log_or_trace=e.get('log', ''), fee_wei=e.get('fee_wei', ''), usd_day_price=usd, note=note)


def key(r):
    return (r['incident'], r['chain'], r['tx'], r['kind'], str(r['log_or_trace']), r['src'], r['dst'], r['token_contract'], r['raw'])


def incident_a():
    w = load('may_polygon_full.json')
    rows = []
    for e in w['edges']:
        if tokens.worth_following(137, e):
            note = 'admin to attacker' if (e['src'], e['dst']) == (ADM, ATT) else 'gas of the attacker' if (e['src'], e['dst']) == (GAS, ATT) else ''
            if e['dst'] == ATT and not note:
                continue
            rows.append(row('A_0522', e, note))
    b0, b1 = c.block_at(c.ts_of('2026-05-15 00:00:00')), c.block_at(c.ts_of('2026-07-05 00:00:00'))
    admin, _ = c.all_edges(ADM, 137, b0, b1)
    day = c.ts_of('2026-05-22 00:00:00')
    for e in admin:
        if e['ts'] >= day and e['src'] in (A871, F61) and e['dst'] == ADM and tokens.worth_following(137, e):
            rows.append(row('A_0522', e, 'automatic top-up to the compromised key'))
    b0, b1 = c.block_at(c.ts_of('2026-05-22 00:00:00')), c.block_at(c.ts_of('2026-11-02 12:00:00'))
    hold, _ = c.all_edges(HOLD, 137, b0, b1, cap=200)
    for e in hold:
        if tokens.worth_following(137, e) or (e['kind'] != 'erc20' and c.amount(e) >= 1):
            rows.append(row('A_0522', e, 'isolation then return to the Polymarket admin Safe'))
    return rows


def incident_c():
    core = load('june_core.json')
    rows = []
    for k, edges in core.items():
        chain = int(k.split(':')[0])
        for e in edges:
            if not tokens.worth_following(chain, e):
                continue
            note = 'victim to staging wallet' if chain == 137 and e['token'] == PUSD and e['dst'] in STAGING and e['src'] not in STAGING else ''
            rows.append(row('C_0625', e, note))
    w = load('june_eth.json')
    t = load('june_taint.json')['poison']['got']
    for e in w['edges']:
        if e['chain'] == 1 and tokens.worth_following(1, e) and (e['src'] == E65B or e['src'] in t):
            rows.append(row('C_0625', e, 'downstream of the consolidation wallet'))
    return rows


def incident_d():
    o = load('oct_core.json')['137']
    rows = [row('D_1029', e) for e in o if e['kind'] != 'erc20' and c.amount(e) >= 1]
    w = load('oct_polygon.json')
    rows += [row('D_1029', e, 'downstream') for e in w['edges'] if tokens.worth_following(137, e)]
    return rows


def write(name, rows, fields):
    with (ROOT / name).open('w', newline='') as f:
        wr = csv.DictWriter(f, fieldnames=fields)
        wr.writeheader()
        wr.writerows(rows)


def main():
    seen, rows = set(), []
    for r in incident_a() + incident_c() + incident_d():
        k = key(r)
        if k not in seen:
            seen.add(k)
            rows.append(r)
    rows.sort(key=lambda r: (r['incident'], r['utc'], r['tx'], str(r['log_or_trace'])))
    write('FUND_FLOW.csv', rows, FIELDS)
    # deposits into ChangeNOW-tagged wallets and the unlabeled service, stolen share on both bounds
    taint = load('may_taint_full.json')
    dep, inbound = [], []
    for r in rows:
        if r['incident'] == 'A_0522' and r['dst'] in (F2020, H6976, H89C5):
            hub = dict([(F2020, 'f2020'), (H6976, '6976'), (H89C5, '89c5')])[r['dst']]
            attribution = 'unlabeled service, BitcoinVN by elimination only' if hub == '89c5' else 'ChangeNOW candidate: no public tag, on-chain treasury flows with ChangeNOW 22, weak OSINT, operator test swap (f2020 only)'
            inbound.append(dict(incident=r['incident'], chain=r['chain'], utc=r['utc'], tx=r['tx'], block=r['block'], from_wallet=r['src'], hub=r['dst'], hub_name=hub, asset=r['asset'], token_contract=r['token_contract'], decimals=r['decimals'], raw=r['raw'], amount=r['amount'], usd_day_price=r['usd_day_price'], attribution=attribution, counterargument='pooled service wallet: a transfer here says nothing about any payout; the sender may have sent a deposit for someone else'))
            if hub != '89c5' and r['usd_day_price']:
                dep.append(dict(incident='A_0522' if r['utc'] < '2026-10-01' else 'D_1029', ts=c.ts_of(r['utc']), usd=r['usd_day_price'], tx=r['tx'], hub=hub))
    write('CHANGENOW_INBOUND.csv', inbound, list(inbound[0]))
    (RUNS / 'deposits.json').write_text(json.dumps(dep))
    print(len(rows), 'flow rows', len(inbound), 'inbound rows', len(dep), 'deposits for matching')
    return taint


if __name__ == '__main__':
    main()
