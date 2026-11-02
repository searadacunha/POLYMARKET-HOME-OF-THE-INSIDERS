"""Event-level statistics. Pure functions over rows: no name, no resolution, no account list."""
import bisect
from collections import defaultdict

from rows import DAY, H


def by_token(rows):
    """token -> BUY rows sorted by time, as (ts, wallet, usd)."""
    out = defaultdict(list)
    for r in rows:
        if r[4] == 'BUY':
            out[r[2]].append((r[8], r[3], r[5]))
    for v in out.values():
        v.sort()
    return out


def qualified(rows, t, hours, min_usd):
    """Wallets reaching min_usd in ]t - hours, t], with their first buy in that window and their sum. rows sorted by ts."""
    low = bisect.bisect_right(rows, (t - hours * H, '\xff', 0))
    high = bisect.bisect_right(rows, (t, '\xff', float('inf')))
    seen = {}
    for ts, w, usd in rows[low:high]:
        s = seen.get(w)
        if s:
            s[1] += usd
        else:
            seen[w] = [ts, usd]
    return {w: s for w, s in seen.items() if s[1] >= min_usd}


def fresh_cohort(rows, t, ages, hours=72, min_usd=1000, age_days=14):
    """N and U of E1. A wallet with no known age does not count, and is returned apart: an error is never an age."""
    n, u, members, unknown = 0, 0.0, [], 0
    for w, (first, total) in qualified(rows, t, hours, min_usd).items():
        born = ages.get(w)
        if born is None:
            unknown += 1
        elif first - born <= age_days * DAY:
            n += 1
            u += total
            members.append(w)
    return n, u, sorted(members), unknown


def hourly_ticks(start, end):
    first = start - start % H + H
    return range(first, end + 1, H)


def alerts(tokens, ages, end, start, hours=72, min_usd=1000, age_days=14, min_n=3, min_u=10000):
    """First alert of each token up to `end`, evaluated hourly, plus the last state. Only ticks where a buy sits in the window cost anything."""
    first, last = {}, {}
    for token, rows in tokens.items():
        if not rows or rows[0][0] > end:
            continue
        for t in hourly_ticks(max(start, rows[0][0]), end):
            if bisect.bisect_right(rows, (t, '\xff', float('inf'))) == bisect.bisect_right(rows, (t - hours * H, '\xff', 0)):
                continue
            n, u, members, unknown = fresh_cohort(rows, t, ages, hours, min_usd, age_days)
            if n >= min_n and u >= min_u:
                if token not in first:
                    first[token] = dict(t=t, n=n, u=round(u, 2), members=members, unknown=unknown)
                last[token] = dict(t=t, n=n, u=round(u, 2), members=members, unknown=unknown)
    return first, last


def bursts(rows, minutes, min_wallets=3, min_usd=250, max_top_share=.8):
    """Windows with several wallets each above min_usd, merged when they overlap. rows sorted by ts."""
    width = minutes * 60
    found = []
    low = 0
    for high in range(len(rows)):
        t = rows[high][0]
        while rows[low][0] <= t - width:
            low += 1
        spent = defaultdict(float)
        for _, w, usd in rows[low:high + 1]:
            spent[w] += usd
        big = {w: x for w, x in spent.items() if x >= min_usd}
        total = sum(big.values())
        if len(big) >= min_wallets and max(big.values()) <= max_top_share * total:
            if found and found[-1]['start'] <= t and rows[low][0] <= found[-1]['end']:
                found[-1]['end'] = t
                if total > found[-1]['usd']:
                    found[-1].update(usd=round(total, 2), wallets=len(big), members=sorted(big))
            else:
                found.append(dict(start=rows[low][0], end=t, usd=round(total, 2), wallets=len(big), members=sorted(big)))
    return found


def decisions(rows_for_wallet_token, gap=120):
    """Fills grouped by transaction, then consecutive groups within `gap` seconds. Input: (ts, tx, usd) of one wallet, one token, one side."""
    by_tx = {}
    for ts, tx, usd in sorted(rows_for_wallet_token):
        g = by_tx.setdefault(tx, [ts, 0.0])
        g[1] += usd
    groups = sorted(by_tx.values())
    merged = []
    for ts, usd in groups:
        if merged and ts - merged[-1][1] <= gap:
            merged[-1][1] = ts
            merged[-1][2] += usd
        else:
            merged.append([ts, ts, usd])
    return len(groups), [(a, c) for a, _, c in merged]


def small_then_large(decision_list, min_usd=1000, factor=5, min_decisions=3):
    """E3: a decision at min_usd or more and at least factor times the median of those before it."""
    if len(decision_list) < min_decisions:
        return None
    for i in range(2, len(decision_list)):
        before = sorted(x for _, x in decision_list[:i])
        median = before[len(before) // 2] if len(before) % 2 else (before[len(before) // 2 - 1] + before[len(before) // 2]) / 2
        if decision_list[i][1] >= min_usd and decision_list[i][1] >= factor * median:
            return dict(at=decision_list[i][0], usd=round(decision_list[i][1], 2), median_before=round(median, 2), index=i)
    return None
