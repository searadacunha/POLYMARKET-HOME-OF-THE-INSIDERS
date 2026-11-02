"""Attribution of stolen funds along walked edges. Two bounds, per asset class, no swaps assumed: poison (every outgoing unit is stolen while any stolen unit remains) and haircut (each outgoing unit is stolen pro rata of the node's stock)."""
import collections
USD_LIKE = {'USDC', 'USDC.e', 'USDT', 'DAI', 'pUSD'}


def asset_class(symbol):
    return 'USD' if symbol in USD_LIKE else symbol


def propagate(edges, seeds, stop_nodes):
    """edges: time-ordered dicts with src, dst, cls, amount, ts. seeds: {node: {cls: stolen amount}}. Returns per-node received stolen amount, for both bounds, and what stays on each node."""
    order = sorted(edges, key=lambda e: (e['ts'], e['src'], e['dst']))
    result = {}
    for bound in ('poison', 'haircut'):
        stolen = collections.defaultdict(lambda: collections.defaultdict(float))
        stock = collections.defaultdict(lambda: collections.defaultdict(float))
        got = collections.defaultdict(lambda: collections.defaultdict(float))
        for n, m in seeds.items():
            for cls, q in m.items():
                stolen[n][cls] += q
                stock[n][cls] += q
        for e in order:
            s, d, cls, q = e['src'], e['dst'], e['cls'], e['amount']
            have = stolen[s][cls]
            if bound == 'poison':
                part = min(q, have)
            else:
                part = q * have / stock[s][cls] if stock[s][cls] > 0 else 0.0
                part = min(part, have, q)
            stolen[s][cls] -= part
            stock[s][cls] = max(stock[s][cls] - q, 0.0)
            stock[d][cls] += q
            if part > 0:
                stolen[d][cls] += part
                got[d][cls] += part
        result[bound] = dict(got={k: dict(v) for k, v in got.items()}, left={k: {c: q for c, q in v.items() if q > 1e-9} for k, v in stolen.items()})
    return result
