"""How often the amount-and-time rule matches by accident, on real rows. Reproducible with a fixed seed.

Three controls, none using a label: other wallets' stored deposits for each withdrawal, the same bridge
records against deposits moved by days, and every USDC.e transfer of sampled Polygon windows. A wallet set
already under investigation is sparse, so the first is a low estimate; the third shows the whole chain.
Usage: python -m signal_engine.fund_flow.controls --out FILE [--deposits N] [--windows N]
"""
import argparse
import json
import os
import random
import sqlite3
import time
import zlib
from pathlib import Path

from . import links
from .client import ChainError, Client
from .flows import PUSD, TRANSFER, USDC_E, transfers

ROOT = Path(__file__).resolve().parents[2]
STATE = Path(os.environ.get('SIGNAL_ENGINE_STATE', Path.home() / '.local/state/polysentinel-signal-engine')) / 'fund_flow'
WINDOW_BLOCKS = 100
TOLERANCES = (.001, .01, .1)


def stored_money_rows():
    cx = sqlite3.connect(f"file:{ROOT / 'data/polysentinel.sqlite3'}?mode=ro", uri=True, timeout=10)
    out = []
    for (body,) in cx.execute("SELECT c.body FROM object_refs r JOIN contents c ON c.id=r.content_id WHERE r.kind='wallet_activity'"):
        row = json.loads(zlib.decompress(body)).get('row') or {}
        if row.get('type') in ('DEPOSIT', 'WITHDRAWAL') and row.get('transaction_hash'):
            out.append(dict(kind=row['type'], owner=row['proxy_wallet'].lower(), at=row['timestamp'], amount=float(row['usdc_size']), tx=row['transaction_hash']))
    cx.close()
    return sorted(out, key=lambda r: (r['at'], r['tx']))


def stored_rate(rows, seed):
    withdrawals = [r for r in rows if r['kind'] == 'WITHDRAWAL' and r['amount'] > 0]
    deposits = [r for r in rows if r['kind'] == 'DEPOSIT']
    return {f'ratio_{low:.2f}_to_{high}': links.chance_rate(withdrawals, deposits, seed=seed, min_ratio=low, max_ratio=high) for low, high in ((.90, 1.001), (.99, 1.001), (.999, 1.001))}


def bridge_rule(client, rows, n, seed):
    """Each deposit against its own sender's bridge records, on the real date and moved by days."""
    rng = random.Random(seed)
    deposits = [r for r in rows if r['kind'] == 'DEPOSIT' and r['amount'] > 0]
    rng.shuffle(deposits)
    tested = with_records = real = control = 0
    pools = []
    for d in deposits:
        if tested >= n or client.rpc_used >= client.rpc_limit - 2 or client.http_used >= client.http_limit - 1:
            break
        receipt = client.receipt(d['tx'])
        sender = next((t['source'] for t in transfers(receipt or dict(logs=[])) if t['token'] == USDC_E and t['target'] == PUSD), None)
        if not sender:
            continue
        status, body = client.get_json(f'https://bridge.polymarket.com/status/{sender}', dict(limit=50))
        tested += 1
        records = [r for r in (body or {}).get('transactions', []) if r.get('status') == 'COMPLETED' and str(r.get('fromChainId')) != '137'] if status == 200 and isinstance(body, dict) else []
        with_records += bool(records)
        pool = [dict(owner='record', at=r['createdTimeMs'] / 1000, amount=int(r['fromAmountBaseUnit']) / 10 ** (18 if str(r['fromChainId']) == '56' else 6)) for r in records]
        # candidate_matches reads later rows, so the deposit is mirrored: records before it become rows after it.
        mirrored = [dict(p, at=2 * d['at'] - p['at']) for p in pool]
        target = dict(owner='deposit', at=d['at'], amount=d['amount'])
        rule = dict(min_ratio=1 / links.BRIDGE_MAX_RATIO, max_ratio=1 / links.BRIDGE_MIN_RATIO)
        real += bool(links.candidate_matches(target, mirrored, **rule))
        pools.append((target, pool, sender))
        moved_at = d['at'] + rng.choice((3, 5, 7, 11)) * 86400 * rng.choice((-1, 1))
        control += bool(links.candidate_matches(dict(target, at=moved_at), [dict(p, at=2 * moved_at - p['at']) for p in pool], **rule))
    # Another sender's records on the real date: these share no address with the deposit, so any fit is an accident.
    other = [(t, next((q for _, q, s in pools[i + 1:] + pools[:i] if s != sender and q), []), sender) for i, (t, _, sender) in enumerate(pools)]
    foreign = sum(bool(links.candidate_matches(t, [dict(p, at=2 * t['at'] - p['at']) for p in q], min_ratio=1 / links.BRIDGE_MAX_RATIO, max_ratio=1 / links.BRIDGE_MIN_RATIO)) for t, q, _ in other)
    return dict(deposits_tested=tested, senders_with_cross_chain_records=with_records, real_date_with_candidate=real, moved_date_with_candidate=control, control_rate=control / tested if tested else None, other_sender_records_with_candidate=foreign, other_sender_rate=foreign / tested if tested else None)


def population(client, rows, windows, seed):
    """All USDC.e transfers in short random windows: how many unrelated ones look like each real amount."""
    rng = random.Random(seed)
    head = client.head()
    amounts = [r['amount'] for r in rows if r['kind'] == 'WITHDRAWAL' and r['amount'] > 0]
    start_range = (head - 400000, head - 1000)
    counts = {t: 0 for t in TOLERANCES}
    trials, transfers_seen, read = 0, 0, 0
    hits = {t: 0 for t in TOLERANCES}
    for _ in range(windows):
        first = rng.randrange(*start_range)
        try:
            logs = client.rpc('eth_getLogs', [dict(fromBlock=hex(first), toBlock=hex(first + WINDOW_BLOCKS - 1), address=USDC_E, topics=[TRANSFER])])
        except ChainError:
            continue
        read += 1
        values = sorted(t['raw'] / 1e6 for t in transfers(dict(logs=logs)))
        transfers_seen += len(values)
        for amount in rng.sample(amounts, min(50, len(amounts))):
            trials += 1
            for tolerance in TOLERANCES:
                matched = sum(1 for v in values if abs(v - amount) <= tolerance * amount)
                counts[tolerance] += matched
                hits[tolerance] += bool(matched)
    return dict(windows_read=read, blocks_per_window=WINDOW_BLOCKS, minutes_per_window=WINDOW_BLOCKS * 2 / 60, transfers_seen=transfers_seen, trials=trials,
                by_tolerance={str(t): dict(share_with_at_least_one_match=hits[t] / trials if trials else None, mean_matches=counts[t] / trials if trials else None) for t in TOLERANCES},
                scope='USDC.e on Polygon only, about three minutes per window. A real search over hours and chains would meet far more.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', required=True)
    p.add_argument('--deposits', type=int, default=40)
    p.add_argument('--windows', type=int, default=8)
    p.add_argument('--seed', type=int, default=20261101)
    a = p.parse_args()
    client = Client(rpc_limit=120, http_limit=60, ledger=STATE / 'requests.jsonl')
    rows = stored_money_rows()
    result = dict(seed=a.seed, stored_rows=len(rows), stored_wallets=len({r['owner'] for r in rows}), stored_withdrawal_vs_other_wallets_deposits=stored_rate(rows, a.seed))
    try:
        result['bridge_records_rule'] = bridge_rule(client, rows, a.deposits, a.seed)
        result['chain_population'] = population(client, rows, a.windows, a.seed)
    finally:
        client.close()
    result['requests'] = dict(rpc=client.rpc_used, http=client.http_used)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(result, indent=1, sort_keys=True))
    print(json.dumps(result, indent=1, sort_keys=True))


if __name__ == '__main__':
    main()
