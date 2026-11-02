"""Same readings on wallets nobody named, so a trait or a link can be read against a base rate. Full pagination, and an unreadable line leaves the denominator instead of counting as "no trait" (audit C2, C3).
Groups: non_surlignes, meme_token, token_oppose from the investigation's B_E6; fresh accounts drawn as in its baseline.py (same pool rule, same seed). Writes state/comparators.jsonl, one line per wallet, resumable."""
import gzip
import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import evm
import labels
import net
import reconcile
import sol
import walk

INV = Path.home() / 'Projects/PolySentinel-investigation'
OUT = net.ROOT / 'state/comparators.jsonl'
SEED = 20261101
OCT1 = 1790812800
READ_CHAINS = (1, 137, 42161)
VAULT = '0xc8a6871d4ec4dae64f605db0f8a0b3d9ef928d64'


def fresh_pool(n=40):
    """Census wallets first seen since 1 Oct with 5,000 $ of buys outside the family: same rule and seed as the investigation, without importing from its folder."""
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(INV / 'collective/code'))
    import rows as R
    ages = {}
    with gzip.open(INV / 'collective/data/ages.jsonl.gz', 'rt') as f:
        for line in f:
            a = json.loads(line)
            if 'first_ts' in a:
                ages[a['wallet']] = a['first_ts']
    family = {r[3] for r in R.family()}
    spent = defaultdict(float)
    for r in R.census({}):
        if r[4] == 'BUY':
            spent[r[3]] += r[5]
    pool = sorted(w for w, x in spent.items() if x >= 5000 and w in ages and ages[w] >= OCT1 and w not in family)
    random.Random(SEED).shuffle(pool)
    return pool[:n], len(pool)


def owner_of(wallet):
    try:
        out = net.rpc('eth_call', [dict(to=wallet, data='0x8da5cb5b'), 'latest'], 137)
        return '0x' + out[-40:] if out and len(out) >= 42 else None
    except Exception:
        return None


def api_deposits(wallet):
    """Every DEPOSIT row of the Data API, full cursor pagination. A failure raises and the line leaves the denominator."""
    rows, cursor = [], None
    for _ in range(40):
        params = dict(user=wallet, limit=500, sort_by='TIMESTAMP', sort_direction='ASC', exclude_deposits_withdrawals='false', type='DEPOSIT')
        if cursor:
            params['cursor'] = cursor
        body = net.get('https://data-api.polymarket.com/v2/activity', params, pause=.3)
        if '_http_error' in body:
            raise RuntimeError(f'activity {wallet}: {body}')
        rows += body.get('data', [])
        cursor = (body.get('pagination') or {}).get('next_cursor')
        if not cursor:
            return rows, True
    return rows, False


def first_payment(wallet):
    rows, complete = reconcile.pull('tokentx', wallet)
    pay = next((int(r['timeStamp']) for r in rows if r['contractAddress'].lower() == reconcile.PUSD and r['from'].lower() == wallet and r['to'].lower() != evm.ZERO), None)
    return pay, complete, len(rows), rows


def immediate(tx, wallet, token_rows, at):
    """Who brought the collateral: the first USDC or USDC.e sender of the transaction that is neither the wallet nor a Polymarket contract. Without one the wallet wrapped what it already held: then the last sender before this time."""
    rc = net.rpc('eth_getTransactionReceipt', [tx], 137)
    for l in rc['logs']:
        if l['topics'] and l['topics'][0] == '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef' and len(l['topics']) == 3 and evm.TOKENS[137].get(l['address'].lower()) in ('USDC.e', 'USDC'):
            source = '0x' + l['topics'][1][-40:]
            lab = labels.lookup(source, 137)
            if source not in (wallet, evm.ZERO) and not (lab and lab['category'] == 'polymarket_contract'):
                return source
    earlier = [r for r in token_rows if r['to'].lower() == wallet and int(r['timeStamp']) <= at and evm.TOKENS[137].get(r['contractAddress'].lower()) in ('USDC.e', 'USDC') and r['from'].lower() != evm.ZERO]
    earlier = [r for r in earlier if not (labels.lookup(r['from'].lower(), 137) or {}).get('category') == 'polymarket_contract']
    return earlier[-1]['from'].lower() if earlier else None


def inflows(key):
    """Labelled and unlabelled senders to one key, three chains, with the same dust floor as the walk."""
    senders, complete = [], True
    for chain in READ_CHAINS:
        flows, info = walk.evm_rows(key, chain, 0)
        complete &= info['complete']
        for f in flows:
            if f['dst'] == key and not f.get('self_initiated') and walk.value_ok(f, 0) and f['src'] != evm.ZERO:
                senders.append((f['src'], chain, f['token'], walk.amount(f), f['tx'], f['at']))
    return senders, complete


def counterparties(key):
    out = set()
    for chain in READ_CHAINS:
        flows, _ = walk.evm_rows(key, chain, 0)
        for f in flows:
            other = f['src'] if f['dst'] == key else f['dst']
            if other != evm.ZERO:
                out.add((other, chain))
    return out


def read(group, wallet, first_buy):
    row = dict(group=group, wallet=wallet)
    first_pay, complete_tokens, n_rows, token_rows = first_payment(wallet)
    deposits, complete_api = api_deposits(wallet)
    row.update(history_complete=complete_api and complete_tokens, token_rows=n_rows, deposits=len(deposits), usd=sum(float(d.get('usdc_size') or 0) for d in deposits))
    if not deposits:
        row['state'] = 'NO_DEPOSIT_IN_API'
        return row
    first_buy = first_buy or first_pay
    before = [d for d in deposits if first_buy and d['timestamp'] <= first_buy]
    d = before[-1] if before else deposits[0]
    pick = dict(hash=d['transaction_hash'], timeStamp=d['timestamp'], value=float(d.get('usdc_size') or 0) * 1e6)
    row.update(state='READ', pick_tx=pick['hash'], pick_at=int(pick['timeStamp']), pick_usd=int(pick['value']) / 1e6, first_buy=first_buy, gap_s=(first_buy - int(pick['timeStamp'])) if first_buy and before else None)
    payer = immediate(pick['hash'], wallet, token_rows, int(pick['timeStamp']))
    row['immediate'] = payer
    if payer:
        c = walk.classify_evm(payer, 137)
        row.update(immediate_kind=c.get('kind'), immediate_cls=c['cls'], immediate_name=c.get('contract_name') or (c.get('label') or {}).get('name'), via_vault=payer == VAULT, via_7702=c.get('kind') == 'EIP7702_DELEGATED_EOA')
    rec = walk.relay_record(pick['hash'])
    if not rec and payer and row.get('via_7702'):
        # a bridge deposit address: Relay's record sits on the payment into that address, not on the mint
        flows, _ = walk.evm_rows(payer, 137, 0)
        earlier = [f for f in flows if f['dst'] == payer and f['at'] <= int(pick['timeStamp']) and f['token'] in ('USDC.e', 'USDC')]
        if earlier:
            rec = walk.relay_record(earlier[-1]['tx'])
            row['bridge_payment_tx'] = earlier[-1]['tx']
            row['bridge_payment_from'] = earlier[-1]['src']
    if rec:
        row.update(relay=True, relay_user=rec['user'], origin_chain=rec['in_chain'], origin_symbol=rec['in_symbol'])
        if rec['user'] and not rec['user'].startswith('0x'):
            try:
                row['solana_funders'] = solana_funders(rec['user'], int(pick['timeStamp']))
            except Exception as e:
                row['solana_error'] = str(e)[:160]
    key = owner_of(wallet)
    row['key'] = key
    if key:
        senders, ok = inflows(key)
        row['key_history_complete'] = ok
        tally = Counter()
        row['key_senders_total'] = len(senders)
        # every sender checked against the labels offline; node calls only for the largest unlabelled ones, or an active key costs thousands of calls
        order = sorted(senders, key=lambda x: -x[3])
        probed = set()
        for s, chain, token, amt, tx, at in order:
            lab = labels.lookup(s, chain)
            if lab and lab['category'] != 'other_labeled':
                tally[(lab['category'], lab['name'])] += 1
            elif (s, chain) in probed or len(probed) < 25:
                probed.add((s, chain))
                c = walk.classify_evm(s, chain)
                lab = c.get('label') or {}
                tally[(lab.get('category') or c['cls'], lab.get('name') or c.get('contract_name') or '')] += 1
            else:
                tally[('NOT_PROBED', '')] += 1
        row['key_senders'] = [dict(kind=k[0], name=k[1], n=n) for k, n in tally.items()]
        row['counterparties'] = sorted(f'{a}:{c}' for a, c in counterparties(key))
    return row


def solana_funders(user, before):
    sigs, complete = sol.signatures(user)
    found = []
    for s in sigs[:walk.SOL_TX_BUDGET]:
        if s.get('err') or (s.get('blockTime') or 0) > before:
            continue
        for m in sol.moves(sol.transaction(s['signature'])):
            if m['owner'] != user and m['raw'] < 0 and m['mint'] in sol.MINTS:
                lab = labels.lookup(m['owner'], walk.SOLANA)
                found.append(dict(owner=m['owner'], label=(lab or {}).get('name'), usd=-m['raw'] / 10 ** m['decimals'], tx=s['signature']))
    return found[:6]


def named():
    """The eleven dossiers through the very same reader, so rates compare like with like."""
    e6 = json.loads((INV / 'collective/derived/B_E6.json').read_text())
    first_buy = {w: p.get('first_family_buy') for w, p in e6['per_wallet'].items()}
    out = net.ROOT / 'state/comparators_named.jsonl'
    with out.open('w') as f:
        for w in e6['groups']['named']:
            row = read('named', w.lower(), first_buy.get(w))
            f.write(json.dumps(row) + '\n')
            print('named', w[:10], row.get('state'), row.get('origin_chain'), row.get('via_vault'), row.get('via_7702'), row.get('gap_s'), flush=True)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'named':
        return named()
    e6 = json.loads((INV / 'collective/derived/B_E6.json').read_text())
    fresh, pool = fresh_pool()
    # the fresh accounts first: the only group comparable in age
    groups = dict(fraiches_recensement=fresh, **{k: v for k, v in e6['groups'].items() if k != 'named'})
    first_buy = {w: p.get('first_family_buy') for w, p in e6['per_wallet'].items()}
    (net.ROOT / 'state/comparators_meta.json').write_text(json.dumps(dict(pool=pool, sampled=len(fresh), seed=SEED, groups={k: len(v) for k, v in groups.items()})))
    done = {json.loads(l)['wallet'] for l in OUT.read_text().splitlines()} if OUT.exists() else set()
    for group, wallets in groups.items():
        for w in wallets:
            if w in done:
                continue
            try:
                row = read(group, w.lower(), first_buy.get(w))
            except net.Pause:
                raise
            except Exception as e:  # an unreadable line stays visible and leaves the denominator
                row = dict(group=group, wallet=w, state='ERROR', error=f'{type(e).__name__}: {str(e)[:200]}')
            with OUT.open('a') as f:
                f.write(json.dumps(row) + '\n')
            print(group, w[:10], row.get('state'), row.get('origin_chain'), row.get('via_vault'), row.get('via_7702'), row.get('gap_s'), row.get('error', '')[:120], flush=True)


if __name__ == '__main__':
    main()
