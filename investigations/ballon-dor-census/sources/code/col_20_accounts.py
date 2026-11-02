"""One account, whole public record: profile, stats, activity with deposits and withdrawals, trades on both sides, positions, value. Raises on any failed page."""
import json
import sys
import net
import seed


def accounts():
    out = {}
    for n, a in seed.IRBOZ.items():
        out.setdefault(a['profile'].lower(), dict(address=a['profile'].lower(), labels=[], )).setdefault('labels', []).append(f'irboz_{n}')
    for name, addr in list(seed.UPSIDE_PRINTED.items()) + list(seed.UPSIDE_LATER.items()):
        out.setdefault(addr.lower(), dict(address=addr.lower(), labels=[]))['labels'].append(f'upside:{name}')
    return out


def read(addr):
    profile = net.get('https://gamma-api.polymarket.com/public-profile', dict(address=addr), accept=(404, 400))
    stats = net.get('https://data-api.polymarket.com/v2/user-stats', dict(user=addr))
    value = net.get('https://data-api.polymarket.com/v2/value', dict(user=addr))
    activity = list(net.v2_all('/v2/activity', dict(user=addr, limit=1000, start=1, sort_direction='ASC', exclude_deposits_withdrawals='false')))
    trades = list(net.v2_all('/v2/trades', dict(user=addr, limit=1000, start=1, taker_only='false')))
    positions = {}
    for status in ('OPEN', 'CLOSED'):
        positions[status] = list(net.v2_all('/v2/positions', dict(user=addr, limit=1000, status=status, filter_type='TOKENS', filter_amount=0)))
    pnl = net.get('https://data-api.polymarket.com/v2/user-pnl', dict(user=addr, interval='all', fidelity=1440), accept=(400, 404))
    return dict(address=addr, profile=profile, stats=stats, value=value, activity=activity, trades=trades, positions=positions, pnl=pnl)


def main():
    (net.ROOT / 'derived/accounts').mkdir(parents=True, exist_ok=True)
    acc = accounts()
    if len(sys.argv) > 1:
        acc = {a: acc.get(a, dict(address=a, labels=['manual'])) for a in sys.argv[1:]}
    for addr, meta in acc.items():
        d = read(addr)
        d['labels'] = meta['labels']
        (net.ROOT / f'derived/accounts/{addr}.json').write_text(json.dumps(d))
        print(addr, meta['labels'], (d['profile'] or {}).get('name'), (d['profile'] or {}).get('createdAt'), 'activity', len(d['activity']), 'trades', len(d['trades']), 'pos', len(d['positions']['OPEN']), len(d['positions']['CLOSED']), flush=True)
    print('calls', net.Stats.calls, 'hits', net.Stats.hits)


if __name__ == '__main__':
    main()
