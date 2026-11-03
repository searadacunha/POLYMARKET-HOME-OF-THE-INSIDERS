"""Reads the ChangeNOW join, runs its two controls, and writes CHANGENOW.md figures to a JSON. No network. A positive control: keys of known wallets must hit. A negative control: random addresses must not."""
import gzip
import json
import random
import sys
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gf import env, proxy

ROOT = env.data_root()
HITS = Path(sys.argv[1])


def main():
    known = json.load(gzip.open(ROOT / 'catalog/known_wallets.json.gz', 'rt'))
    keys = [(c['slug'], o.lower()) for p in sorted((Path.home() / 'Projects/PolySentinel-investigation/cases').glob('*.json')) for c in [json.loads(p.read_text())] for o in c['wallet'].get('owners') or []]
    positive = [dict(case=slug, key=key, hit=proxy.deposit_wallet(key) in known or proxy.deposit_wallet(key, 'legacy') in known) for slug, key in keys]
    rng = random.Random(20261103)
    negative_hits, n_random = 0, 20000
    for _ in range(n_random):
        address = '0x' + rng.randbytes(20).hex()
        negative_hits += (address in known) + (proxy.deposit_wallet(address) in known) + (proxy.deposit_wallet(address, 'legacy') in known)
    rows = [json.loads(l) for l in HITS.open()]
    active_after = [r for r in rows if r['wallet_last_trade'] >= r['first_ts']]
    summary = dict(hits=len(rows), distinct_recipients=len({r['recipient'] for r in rows}), distinct_wallets=len({r['wallet'] for r in rows}), by_form=Counter(r['form'] for r in rows), by_tier=Counter(r['tier'] for r in rows), by_first_source=Counter(r['first_source'] for r in rows).most_common(8), usd_received_total=round(sum(r['usd'] for r in rows), 2), usd_received_max=round(max((r['usd'] for r in rows), default=0), 2), usd_over_100=sum(r['usd'] >= 100 for r in rows), payment_before_first_trade=sum(r['payment_before_first_trade'] for r in rows), wallet_traded_after_payment=len(active_after), positive_control=dict(keys=len(positive), hits=sum(p['hit'] for p in positive), missed=[p['case'] for p in positive if not p['hit']]), negative_control=dict(random_addresses=n_random, hits=negative_hits), rows=sorted(rows, key=lambda r: -r['usd']))
    Path(sys.argv[2]).write_text(json.dumps(summary, indent=1, default=dict))
    print(json.dumps({k: v for k, v in summary.items() if k != 'rows'}, default=dict)[:1500])
    for r in summary['rows'][:12]:
        print(r['recipient'], r['form'], r['wallet'], r['chain'], r['tier'], round(r['usd']), r['n_transfers'], r['payment_before_first_trade'], r['known_from'])


if __name__ == '__main__':
    main()
