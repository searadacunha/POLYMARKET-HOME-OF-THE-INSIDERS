"""Behaviour shared between wallets on one event. Convergence never means common ownership."""
from collections import defaultdict
from itertools import combinations


def collective_signals(store, event_key, now, config):
    """Wallets already anomalous on this event decide what counts: shared activity alone is ordinary."""
    start = now - config['recent_window_s']
    rows = store.cx.execute('SELECT wallet, token_id, tx, ts, nominal FROM trades WHERE event_key=? AND is_buy=1 AND ts>=? AND observed_at<=?', (event_key, start, now)).fetchall()
    groups = defaultdict(float)
    for r in rows:
        groups[r['wallet'], r['token_id'], r['tx'], r['ts']] += r['nominal']
    flagged = {r['wallet'] for r in store.cx.execute("SELECT wallet FROM pairs WHERE event_key=? AND anomalies!='{}' AND evaluated_at>=?", (event_key, start))}
    by_token = defaultdict(set)
    timing = defaultdict(list)
    for (wallet, token, _, ts), _nominal in groups.items():
        if wallet in flagged:
            by_token[token].add(wallet)
            timing[token].append(ts)
    convergence = {t: sorted(w) for t, w in by_token.items() if len(w) >= config['convergence_wallets_minimum']}
    spread = {t: max(timing[t]) - min(timing[t]) for t in convergence}
    burst_start = now - config['burst_window_s']
    ordered = sorted((token, nominal, wallet) for (wallet, token, _, ts), nominal in groups.items() if ts >= burst_start and nominal >= config['identical_amount_minimum'])
    identical, i = [], 0
    while i < len(ordered):
        j = i
        while j + 1 < len(ordered) and ordered[j + 1][0] == ordered[i][0] and ordered[j + 1][1] <= ordered[i][1] * (1 + config['identical_amount_tolerance']):
            j += 1
        wallets = {x[2] for x in ordered[i:j + 1]}
        # Round sizes are common, so a cluster counts only if two of its wallets are already anomalous.
        if len(wallets) >= config['identical_amount_wallets_minimum'] and len(wallets & flagged) >= 2:
            identical.append(dict(token_id=ordered[i][0], amount=ordered[i][1], wallets=sorted(wallets)))
        i = j + 1
    return dict(convergence=convergence, convergence_spread_s=spread, identical_amounts=identical, repeated_across_events=repeated_pairs(store, flagged, event_key, now, config),
                meaning='Comparison of behaviours; common owner not established, public information not excluded.')


def repeated_pairs(store, wallets, event_key, now, config):
    """Pairs anomalous together on another event. One shared event is common; two is worth reading."""
    if len(wallets) < 2:
        return []
    marks = ','.join('?' * len(wallets))
    others = defaultdict(set)
    for r in store.cx.execute(f"SELECT wallet, event_key FROM pairs WHERE wallet IN ({marks}) AND event_key!=? AND anomalies!='{{}}' AND evaluated_at>=?", (*sorted(wallets), event_key, now - config['portfolio_window_s'] * 4)):
        others[r['event_key']].add(r['wallet'])
    pairs = defaultdict(list)
    for other, members in others.items():
        for a, b in combinations(sorted(members), 2):
            pairs[a, b].append(other)
    return [dict(wallets=list(p), events=[event_key] + sorted(e)) for p, e in sorted(pairs.items())]
