"""Polymarket link of recipients: Polygon wallets are read in full over the 48 h target windows, Ethereum wallets on a seeded sample. Three levels, never added: P_DIRECT (same chain, the payout lands on the trading account or the recipient funds its own Deposit Wallet after it), P_ACCOUNT (the address has a Polymarket account, no path of funds read), none."""
import collections
import csv
import json
import random
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import chainlib as c
import cn_common as cc
import cn_windows as w
import pm
import tokens

ROOT = Path(__file__).resolve().parent.parent
ETH_SAMPLE = 150
SEED = 20261102
PUSD = '0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb'


def funded_own_wallet(a, wallet, ts, chain=137):
    """Did the address send a stablecoin to its own trading wallet in the 14 days after the payout?"""
    b0, b1 = c.block_at(ts, chain), c.block_at(ts + 14 * 86400, chain)
    rows, _ = c.history(a, chain, 'tokentx', b0, b1, cap=2000)
    return [e for e in c.token_edges(rows, chain) if e['src'] == a and e['dst'] == wallet and e['token'] in tokens.RECOGNIZED[137]]


def classify(a, ts, chain):
    accts = pm.accounts(a)
    if not accts:
        return 'none', '', None, None
    kinds = ','.join(k for k, _, _ in accts)
    first = accts[0][2]
    firsts = [x[2]['timestamp'] for x in accts if x[2]]
    active_after = bool(firsts) and min(firsts) is not None
    if chain == 137:
        for kind, wallet, _ in accts:
            if kind == 'self':
                return 'P_DIRECT', kinds, min(firsts) if firsts else None, 'payout lands on the trading account'
            hits = funded_own_wallet(a, wallet, ts)
            if hits:
                return 'P_DIRECT', kinds, min(firsts) if firsts else None, 'recipient funds its Deposit Wallet ' + hits[0]['tx']
    return 'P_ACCOUNT', kinds, min(firsts) if firsts else None, 'account exists, no path of funds read' if active_after else 'wallet deployed, no event indexed'


def main():
    pm.self_check()
    excluded = set(json.loads((ROOT / 'state/runs/cn_excluded.json').read_text()))
    rng = random.Random(SEED)
    rows = []
    for incident, cfg in w.INCIDENTS.items():
        for source in cfg['sources']:
            chain = w.SOURCES[source][1]
            target, _ = cc.payouts(incident, source, 'target48')
            first = {}
            for e in sorted(target or [], key=lambda x: x['ts']):
                if e['dst'] not in excluded and tokens.worth_following(chain, e):
                    first.setdefault(e['dst'], e['ts'])
            pool = sorted(first)
            read = pool if chain == 137 else rng.sample(pool, min(ETH_SAMPLE, len(pool)))
            tally = collections.Counter()
            for a in read:
                try:
                    level, kinds, first_event, note = classify(a, first[a], chain)
                except (RuntimeError, ValueError) as err:
                    level, kinds, first_event, note = 'UNREAD', '', None, str(err)[:120]
                tally[level] += 1
                rows.append(dict(incident=incident, source=source, chain=chain, recipient=a, first_payout_utc=c.utc(first[a]), level=level, accounts=kinds, first_pm_event=c.utc(first_event) if first_event else '', trades_before_payout=bool(first_event and first_event < first[a]), note=note))
            print(incident, source, 'pool', len(pool), 'read', len(read), dict(tally), flush=True)
            with (ROOT / 'state/runs/cn_pm.csv').open('w', newline='') as f:
                wr = csv.DictWriter(f, fieldnames=list(rows[0]))
                wr.writeheader()
                wr.writerows(rows)


if __name__ == '__main__':
    main()
