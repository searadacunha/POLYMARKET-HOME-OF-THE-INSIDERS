"""Every pUSD and position movement of each Polymarket wallet, split by what it really is: mint (deposit), burn (withdrawal), settlement with a Polymarket contract, or a direct transfer with someone else.
Compared with the Data API dossier and the balance read now. Writes state/reconcile.json."""
import gzip
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import evm
import labels
import net

INV = Path.home() / 'Projects/PolySentinel-investigation'
PUSD = '0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb'
ETHERSCAN = evm.ETHERSCAN


def pull(action, address):
    rows = []
    complete = False
    for page in range(1, 21):
        d = net.get(ETHERSCAN, dict(chainid=137, module='account', action=action, address=address, page=page, offset=evm.PAGE, sort='asc', startblock=0, endblock=999999999), pause=.3, secret=dict(apikey=net._key_from_env()))
        msg = str(d.get('message', ''))
        if d.get('status') != '1' and 'No ' not in msg:
            raise RuntimeError(f'{action} {address}: {msg} {str(d.get("result"))[:100]}')
        batch = d.get('result') or []
        rows += batch
        if len(batch) < evm.PAGE:
            complete = True
            break
    return rows, complete


def is_polymarket(a):
    lab = labels.lookup(a, 137)
    return bool(lab) and lab['category'] == 'polymarket_contract'


def activity(slug):
    with gzip.open(INV / f'evidence/activity/{slug}.jsonl.gz', 'rt') as f:
        by_tx = defaultdict(set)
        for line in f:
            x = json.loads(line)
            by_tx[x['transaction_hash']].add(x['type'])
    return by_tx


def reconcile(c, wallets):
    w = c['address'].lower()
    api = activity(c['slug'])
    tokens, c1 = pull('tokentx', w)
    positions, c2 = pull('token1155tx', w)
    out = dict(case=c['slug'], wallet=w, complete=c1 and c2, token_rows=len(tokens), position_rows=len(positions))
    pusd = Counter()
    mints, burns, others, foreign = [], [], Counter(), []
    for r in tokens:
        contract = r['contractAddress'].lower()
        src, dst, raw = r['from'].lower(), r['to'].lower(), int(r['value'])
        if contract != PUSD:
            sym = evm.TOKENS[137].get(contract)
            if sym and raw:
                others[sym + (':in' if dst == w else ':out')] += raw
                other = src if dst == w else dst
                if not is_polymarket(other):
                    foreign.append(dict(tx=r['hash'], at=int(r['timeStamp']), token=sym, raw=str(raw), src=src, dst=dst))
            continue
        if src == evm.ZERO:
            mints.append(dict(tx=r['hash'], at=int(r['timeStamp']), raw=raw))
            pusd['mint'] += raw
        elif dst == evm.ZERO:
            burns.append(dict(tx=r['hash'], at=int(r['timeStamp']), raw=raw))
            pusd['burn'] += raw
        else:
            other = src if dst == w else dst
            kind = 'polymarket' if is_polymarket(other) else 'other'
            pusd[f'{kind}:in' if dst == w else f'{kind}:out'] += raw
            if kind == 'other':
                foreign.append(dict(tx=r['hash'], at=int(r['timeStamp']), token='pUSD', raw=str(raw), src=src, dst=dst, other_case=wallets.get(other)))
    moved = Counter()
    direct_positions = []
    for r in positions:
        src, dst = r['from'].lower(), r['to'].lower()
        other = src if dst == w else dst
        if other == evm.ZERO:
            moved['mint_or_burn'] += 1
        elif is_polymarket(other):
            moved['polymarket_contract'] += 1
        else:
            moved['other_wallet'] += 1
            direct_positions.append(dict(tx=r['hash'], at=int(r['timeStamp']), src=src, dst=dst, token_id=r.get('tokenID'), value=r.get('tokenValue'), other_case=wallets.get(other), other_label=(labels.lookup(other, 137) or {}).get('name')))
    # A pUSD leg with a position leg going the other way in the same transaction is a fill on the book, not a transfer between people.
    pos_by_tx = defaultdict(set)
    for r in positions:
        pos_by_tx[r['hash']].add('in' if r['to'].lower() == w else 'out')
    fills, unexplained = 0, []
    for x in foreign:
        if x['token'] != 'pUSD':
            continue
        leg = 'in' if x['dst'] == w else 'out'
        opposite = 'out' if leg == 'in' else 'in'
        if opposite in pos_by_tx.get(x['tx'], ()):
            fills += 1
        else:
            unexplained.append(x)
    # Every position move that the API does not book as a trade, split, merge or redeem would be a transfer between people.
    position_only = [p for p in direct_positions if not api.get(p['tx'], set()) & {'TRADE', 'SPLIT', 'MERGE', 'REDEEM', 'CONVERSION'}]
    money_rows_outside_api = [x for x in unexplained if not api.get(x['tx'])]
    out_by_tx = defaultdict(int)
    for r in tokens:
        if r['contractAddress'].lower() == PUSD and r['from'].lower() == w:
            out_by_tx[r['hash']] += int(r['value'])
    balance = int(net.rpc('eth_call', [dict(to=PUSD, data='0x70a08231' + w[2:].rjust(64, '0')), 'latest'], 137), 16)
    api_dep = {d['tx']: round(d['usd'] * 1e6) for d in c['deposits']}
    api_wd = {d['tx']: round(d['usd'] * 1e6) for d in c['withdrawals']}
    mint_by_tx = defaultdict(int)
    burn_by_tx = defaultdict(int)
    for m in mints:
        mint_by_tx[m['tx']] += m['raw']
    for b in burns:
        burn_by_tx[b['tx']] += b['raw']
    out.update(
        pusd_mint=pusd['mint'] / 1e6, pusd_burn=pusd['burn'] / 1e6, pusd_from_polymarket=pusd['polymarket:in'] / 1e6, pusd_to_polymarket=pusd['polymarket:out'] / 1e6, pusd_other_in=pusd['other:in'] / 1e6, pusd_other_out=pusd['other:out'] / 1e6,
        computed_balance=(pusd['mint'] - pusd['burn'] + pusd['polymarket:in'] - pusd['polymarket:out'] + pusd['other:in'] - pusd['other:out']) / 1e6,
        balance_now=balance / 1e6,
        api_deposits=sum(api_dep.values()) / 1e6, api_withdrawals=sum(api_wd.values()) / 1e6,
        deposits_matched=sum(1 for t, v in api_dep.items() if abs(mint_by_tx.get(t, 0) - v) <= 2), deposits_total=len(api_dep),
        withdrawals_matched=sum(1 for t, v in api_wd.items() if abs(out_by_tx.get(t, 0) - v) <= 2), withdrawals_total=len(api_wd), book_fills=fills, pusd_unexplained=unexplained, position_only_moves=position_only, money_rows_outside_api=money_rows_outside_api, mints_outside_are_redeem=all('REDEEM' in api.get(t, ()) for t in mint_by_tx if t not in api_dep), reward_rows={k: sum(1 for x in unexplained if k in api.get(x['tx'], ())) for k in ('REWARD', 'MAKER_REBATE', 'TAKER_REBATE', 'REFERRAL_REWARD', 'TRADE')},
        mints_outside_api=[t for t in mint_by_tx if t not in api_dep], burns_outside_api=[t for t in burn_by_tx if t not in api_wd],
        other_tokens={k: v / 1e6 for k, v in others.items()}, foreign_token_rows=foreign, positions=dict(moved), direct_positions=direct_positions)
    return out


def main():
    cases = [json.loads(p.read_text()) for p in sorted((INV / 'cases').glob('*.json'))]
    wallets = {c['address'].lower(): c['slug'] for c in cases}
    rows = []
    for c in cases:
        r = reconcile(c, wallets)
        rows.append(r)
        print(c['slug'], 'mint', round(r['pusd_mint'], 2), 'burn', round(r['pusd_burn'], 2), 'computed', round(r['computed_balance'], 4), 'now', r['balance_now'], 'dep', r['deposits_matched'], '/', r['deposits_total'], 'wd', r['withdrawals_matched'], '/', r['withdrawals_total'], 'other', round(r['pusd_other_in'], 2), round(r['pusd_other_out'], 2), 'fills', r['book_fills'], 'non-fill', r['reward_rows'], 'outside api', len(r['money_rows_outside_api']), 'pure position moves', len(r['position_only_moves']), 'redeem ok', r['mints_outside_are_redeem'], 'complete', r['complete'], flush=True)
    (net.ROOT / 'state/reconcile.json').write_text(json.dumps(rows))


if __name__ == '__main__':
    main()
