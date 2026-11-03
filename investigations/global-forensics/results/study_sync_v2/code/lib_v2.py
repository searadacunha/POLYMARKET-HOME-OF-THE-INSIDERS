"""Pure functions of study_sync_v2. Same code for real and synthetic tables. Independent of study_sync: nothing is imported from it. See ../analysis_plan.md.

A table is a dict of numpy arrays, one row per entrant, sorted by token, then ts, then order in the tape:
token, fact, wallet, ts, price, usd, prior_volume, mom, tte_s, guard_ok, part, win.
`win` is read by h1() only, through the excess it is given. No feature here uses it.
"""
import bisect
from collections import Counter, deque

import numpy as np

WINDOWS = (30, 90, 300, 900)
PRIMARY = 300
MIN_WALLETS = 3
COOLDOWN_S = 21600
DAY = 86400
PRICE_MIN, PRICE_MAX = 0.01, 0.35
MIN_USD = 100.0
MIN_PRIOR_VOLUME = 25_000.0
TOUCH_PRICE, GUARD_S = 0.90, 60
MOVE_UP, MOVE_S = 0.10, 1800
STRICT_UP, STRICT_S = 0.05, 43200
HOLDOUT_FROM = 1789516800  # 2026-09-16 00:00 UTC: no row of the first study's period is scored
BAND_EDGES = (0.05, 0.10, 0.20)
CROWD_EDGES = (3, 6, 11, 31)
TTE_EDGES = (DAY, 7 * DAY, 30 * DAY)
MOM_UNKNOWN, MOM_DOWN, MOM_FLAT, MOM_UP, MOM_STRONG = range(5)
MOM_FLAT_BELOW, MOM_STRONG_FROM = 0.02, 0.05
ALPHA = 0.05
BOUND = 0.10
SEED = 20261103
MIN_MATCHED_SHARE = 0.80
MIN_CLUSTERS = 100
INFLUENCE_DROP = 5
MIN_NCE_ROWS = 50
MIN_KISH = 60
WALLET_DROP = 5
WEEK = 7 * DAY


def momentum_code(before, now):
    """Last trade of the token strictly before t0, against the last trade at or before t0 - 3600 s. Either absent: unknown."""
    if before is None or now is None:
        return MOM_UNKNOWN
    change = now - before
    if change <= -MOM_FLAT_BELOW:
        return MOM_DOWN
    if change < MOM_FLAT_BELOW:
        return MOM_FLAT
    return MOM_STRONG if change >= MOM_STRONG_FROM else MOM_UP


def entrants_of_market(rows, end_ts, close_ts):
    """rows: every taker row of one market, dicts wallet, side, token, size, price, ts. Tape order is not trusted.

    An entrant is a wallet's first row in the market, a BUY at 0.01 to 0.35 of at least $100. Inside one second, rows run by rising price, then wallet: a sweep climbs, so a set's last row is its dearest, the cautious reading. Same-second rows never feed a feature of each other: state moves one second at a time.
    Returns rows with features known at t0, plus two guards. `guard_ok` is False after close, at or after 60 s before the token first trades at 0.90 or above, and when a later row of the token within 1,800 s trades 0.10 or more above this row. That removes stale-ask sweeps and first reactions to a public move, and true sets close before one. `strict_ok` also needs no later row within 12 hours at 0.05 or more above. Both read later rows, only to remove rows, in both arms.
    """
    ordered = sorted(rows, key=lambda r: (r['ts'], r['price'], r['wallet']))
    by_token, touch = {}, {}
    for r in ordered:
        by_token.setdefault(r['token'], []).append(r)
        if r['price'] >= TOUCH_PRICE and r['token'] not in touch:
            touch[r['token']] = r['ts']
    ahead, ahead_strict, position = {}, {}, {}
    for token, token_rows in by_token.items():
        times, prices = [x['ts'] for x in token_rows], [x['price'] for x in token_rows]
        ahead[token], ahead_strict[token] = future_max(times, prices, MOVE_S), future_max(times, prices, STRICT_S)
        for k, x in enumerate(token_rows):
            position[id(x)] = k
    seen, prior_volume, history, out, i = set(), 0.0, {}, [], 0
    while i < len(ordered):
        j = i
        while j < len(ordered) and ordered[j]['ts'] == ordered[i]['ts']:
            j += 1
        group = ordered[i:j]
        for r in group:
            first = r['wallet'] not in seen
            seen.add(r['wallet'])
            usd = r['size'] * r['price']
            if first and r['side'] == 'BUY' and PRICE_MIN <= r['price'] <= PRICE_MAX and usd >= MIN_USD:
                times, prices = history.get(r['token'], ([], []))
                now = prices[-1] if prices else None
                back = bisect.bisect_right(times, r['ts'] - 3600) - 1
                before = prices[back] if back >= 0 else None
                k = position[id(r)]
                soon, later = ahead[r['token']][k], ahead_strict[r['token']][k]
                touched = r['token'] in touch and r['ts'] >= touch[r['token']] - GUARD_S
                guard_ok = r['ts'] <= close_ts and not touched and (soon is None or soon < r['price'] + MOVE_UP)
                strict_ok = guard_ok and (later is None or later < r['price'] + STRICT_UP)
                out.append(dict(wallet=r['wallet'], token=r['token'], ts=r['ts'], price=r['price'], usd=usd, prior_volume=prior_volume, mom=momentum_code(before, now), tte_s=end_ts - r['ts'], guard_ok=guard_ok, strict_ok=strict_ok))
        for r in group:
            prior_volume += r['size'] * r['price']
            times, prices = history.setdefault(r['token'], ([], []))
            times.append(r['ts'])
            prices.append(r['price'])
        i = j
    return out


def future_max(times, prices, span):
    """For each row, the highest price among later seconds within `span`. Rows are in time order. One pass, so dense tokens stay cheap."""
    out, window, head, n = [None] * len(times), deque(), 0, len(times)
    for i in range(n):
        while head < n and times[head] <= times[i] + span:
            while window and prices[window[-1]] <= prices[head]:
                window.pop()
            window.append(head)
            head += 1
        while window and times[window[0]] <= times[i]:
            window.popleft()
        out[i] = prices[window[0]] if window else None
    return out


def sort_table(t):
    order = np.lexsort((np.arange(len(t['ts'])), t['ts'], t['token']))
    return {k: v[order] for k, v in t.items()}


def _keys(t, extra=None):
    ts = t['ts'] if extra is None else extra
    low = ts.min() if len(ts) else 0
    big = int(ts.max() - low) + 40 * DAY + 2 if len(ts) else 1
    return t['token'].astype(np.int64) * big + (ts - low).astype(np.int64)


def trailing_counts(t, window):
    """Entrants of the same token in (ts - window, ts], this row included, by tape order. A wallet is an entrant once per market, so counts are wallets."""
    key = _keys(t)
    left = np.searchsorted(key, key - window, side='right')
    return np.arange(len(key)) - left + 1


def roles(t, window):
    """1 trigger: this row completes a set, outside the token's cooldown. 0 control: no set at this row's own time. -1: a set inside a cooldown, dropped from both arms and counted. Decided at the row's time, no later row is read."""
    count = trailing_counts(t, window)
    role = np.zeros(len(count), dtype=np.int8)
    hits = np.nonzero(count >= MIN_WALLETS)[0]
    last = {}
    for i in hits:
        token, ts = int(t['token'][i]), int(t['ts'][i])
        if ts - last.get(token, -10 ** 12) < COOLDOWN_S:
            role[i] = -1
        else:
            role[i] = 1
            last[token] = ts
    return role, count


def crowd(t, window):
    """Entrants of the token over the 24 hours that end where the window starts. The window itself never enters, so a control can exist at every window."""
    key = _keys(t)
    return np.searchsorted(key, key - window, side='right') - np.searchsorted(key, key - window - DAY, side='left')


def cells(t, window):
    band = np.searchsorted(BAND_EDGES, t['price'], side='right')
    crowd_bucket = np.searchsorted(CROWD_EDGES, crowd(t, window), side='right')
    tte = np.searchsorted(TTE_EDGES, t['tte_s'], side='right')
    return band + 4 * crowd_bucket + 20 * t['mom'].astype(np.int64) + 100 * tte


def eligible(t):
    return t['guard_ok'] & (t['prior_volume'] >= MIN_PRIOR_VOLUME) & (t['ts'] >= HOLDOUT_FROM)


def _matrices(fact_idx, cell_idx, arm, excess, n_facts):
    """Per fact and cell: trigger count and excess sum, control count and excess sum."""
    kept = np.unique(cell_idx[arm == 1])
    kept = kept[np.isin(kept, cell_idx[arm == 0])]
    position = np.full(cell_idx.max() + 1 if len(cell_idx) else 1, -1)
    position[kept] = np.arange(len(kept))
    k = position[cell_idx]
    use = k >= 0
    out = [np.zeros((n_facts, len(kept))) for _ in range(4)]
    for mat, mask, values in ((out[0], arm == 1, None), (out[1], arm == 1, excess), (out[2], arm == 0, None), (out[3], arm == 0, excess)):
        m = use & mask
        np.add.at(mat, (fact_idx[m], k[m]), 1.0 if values is None else values[m])
    return out, len(kept)


def _stat(weights, nt, st, nc, sc):
    """Each trigger is scored against controls of the same cell from OTHER facts. A control of the same token or the same world fact shares the outcome, so it would copy a true effect and hide it.
    weights: draws by facts. Returns (statistic per draw, matched triggers per draw)."""
    facts, cells_ = np.nonzero(nt)
    total_c, total_s = weights @ nc, weights @ sc
    w = weights[:, facts]
    n_other = total_c[:, cells_] - w * nc[facts, cells_]
    s_other = total_s[:, cells_] - w * sc[facts, cells_]
    ok = (w > 0) & (n_other > 0)
    with np.errstate(divide='ignore', invalid='ignore'):
        part = np.where(ok, w * (st[facts, cells_] - nt[facts, cells_] * s_other / n_other), 0.0)
    matched = np.where(ok, w * nt[facts, cells_], 0.0).sum(axis=1)
    with np.errstate(divide='ignore', invalid='ignore'):
        return part.sum(axis=1) / matched, matched


def h1(fact, cell, arm, excess, draws, seed=SEED, batch=250):
    """Mean excess of triggers minus the mean excess of controls of the same cell from other facts, weighted by triggers. Percentile interval and two-sided p from a cluster bootstrap on facts. Excess at the row's own paid price."""
    facts, fact_idx = np.unique(fact, return_inverse=True)
    use_rows = arm >= 0
    triggers = int((arm == 1).sum())
    empty = dict(diff=None, n_triggers=triggers, matched=0, matched_share=0.0, facts_triggers=0, kish_facts=0.0, facts_all=int(len(facts)), p=None, ci=[None, None], draws=0)
    if not use_rows.any() or triggers == 0:
        return empty
    (nt, st, nc, sc), n_cells = _matrices(fact_idx[use_rows], cell[use_rows], arm[use_rows], excess[use_rows], len(facts))
    if n_cells == 0 or nt.sum() == 0:
        return empty
    observed, matched = _stat(np.ones((1, len(facts))), nt, st, nc, sc)
    if not np.isfinite(observed[0]):
        return empty
    per_fact = nt.sum(1)
    base = dict(diff=float(observed[0]), n_triggers=triggers, matched=int(matched[0]), matched_share=float(matched[0] / triggers), facts_triggers=int((per_fact > 0).sum()), kish_facts=float(per_fact.sum() ** 2 / (per_fact ** 2).sum()), facts_all=int(len(facts)))
    if not draws:
        return dict(base, p=None, ci=[None, None], draws=0)
    rng = np.random.default_rng(seed)
    values = []
    n = len(facts)
    for start in range(0, draws, batch):
        weights = rng.multinomial(n, np.full(n, 1 / n), size=min(batch, draws - start)).astype(float)
        values.append(_stat(weights, nt, st, nc, sc)[0])
    values = np.concatenate(values)
    values = values[np.isfinite(values)]
    p = min(1.0, 2 * min((1 + (values <= 0).sum()) / (len(values) + 1), (1 + (values >= 0).sum()) / (len(values) + 1)))
    return dict(base, p=float(p), ci=[float(np.quantile(values, ALPHA / 2)), float(np.quantile(values, 1 - ALPHA / 2))], draws=int(len(values)))


def influence(fact, cell, arm, excess, top=INFLUENCE_DROP):
    """The difference once the `top` facts adding most to it are removed. A result that lives on a few world facts does not pass."""
    facts, fact_idx = np.unique(fact, return_inverse=True)
    use_rows = arm >= 0
    if not use_rows.any():
        return None
    (nt, st, nc, sc), n_cells = _matrices(fact_idx[use_rows], cell[use_rows], arm[use_rows], excess[use_rows], len(facts))
    if n_cells == 0 or nt.sum() == 0:
        return None
    total_nc, total_sc = nc.sum(0), sc.sum(0)
    with np.errstate(divide='ignore', invalid='ignore'):
        base = np.where(total_nc > 0, total_sc / total_nc, 0.0)
    share = (st - nt * base).sum(1)
    keep = np.ones((1, len(facts)))
    keep[0, np.argsort(share)[-top:]] = 0.0
    value = _stat(keep, nt, st, nc, sc)[0][0]
    return float(value) if np.isfinite(value) else None


def raw_excess(fact, arm, excess, draws, seed=SEED, batch=500):
    """Mean excess of triggers against the paid price, with no control. If every token of the market holds sets, a difference with controls shows nothing, so a bound must also hold here."""
    facts, fact_idx = np.unique(fact, return_inverse=True)
    n, s = np.zeros(len(facts)), np.zeros(len(facts))
    use = arm == 1
    if not use.any():
        return dict(mean=None, ci=[None, None])
    np.add.at(n, fact_idx[use], 1.0)
    np.add.at(s, fact_idx[use], excess[use])
    rng = np.random.default_rng(seed)
    values = []
    for start in range(0, draws, batch):
        weights = rng.multinomial(len(facts), np.full(len(facts), 1 / len(facts)), size=min(batch, draws - start)).astype(float)
        with np.errstate(divide='ignore', invalid='ignore'):
            values.append((weights @ s) / (weights @ n))
    values = np.concatenate(values) if values else np.array([])
    values = values[np.isfinite(values)]
    return dict(mean=float(s.sum() / n.sum()), ci=[float(np.quantile(values, ALPHA / 2)), float(np.quantile(values, 1 - ALPHA / 2))] if len(values) else [None, None])


def without_top_wallets(t, arm, count, top=WALLET_DROP):
    """Triggers left once sets holding any of the wallets most often in sets are removed. A result that rests on a few wallets is about them, not about sets."""
    triggers = np.nonzero(arm == 1)[0]
    seen = Counter()
    for i in triggers:
        seen.update(int(w) for w in t['wallet'][i - count[i] + 1:i + 1])
    worst = {w for w, _ in seen.most_common(top)}
    out = arm.copy()
    for i in triggers:
        if worst & {int(w) for w in t['wallet'][i - count[i] + 1:i + 1]}:
            out[i] = -1
    return out


def member_count(token, ts, window):
    """Rows inside any set of 3 in the window, no cooldown. Rises with the window by construction, unlike a count of triggers. Input sorted by token then ts."""
    if len(ts) < MIN_WALLETS:
        return 0
    span = (token[2:] == token[:-2]) & (ts[2:] - ts[:-2] < window)
    member = np.zeros(len(ts), dtype=bool)
    idx = np.nonzero(span)[0]
    member[idx] = member[idx + 1] = member[idx + 2] = True
    return int(member.sum())


def h2(t, window, draws, seed=SEED, reach=5):
    """Do entrants group more than local intensity allows? Each wallet moves by one offset per UTC day, within reach times the window, in all its markets together, so wallets that act across markets stay together in the null."""
    token, ts, wallet = t['token'], t['ts'].astype(float), t['wallet']
    observed = member_count(token, ts, window)
    day = (ts // DAY).astype(np.int64)
    _, group = np.unique(np.stack([wallet.astype(np.int64), day]), axis=1, return_inverse=True)
    group = group.ravel()
    n_groups = group.max() + 1 if len(group) else 0
    rng = np.random.default_rng(seed)
    null = np.empty(draws)
    for d in range(draws):
        moved = ts + rng.uniform(-reach * window, reach * window, n_groups)[group]
        order = np.lexsort((moved, token))
        null[d] = member_count(token[order], moved[order], window)
    return dict(observed=observed, null_median=float(np.median(null)), p=float((1 + (null >= observed).sum()) / (draws + 1)), draws=draws)


def near_set_arm(t, role, count):
    """Negative control exposure: pairs that never became a set. A row with exactly one other entrant in the window, in a token that holds no set at any time, against rows alone in their window of such tokens.
    The mechanism under test needs three wallets, so this exposure cannot carry it, and it shares the busy day, the momentum and the token size. A difference here is confounding left after matching.
    A row of a token that holds a set cannot serve: its outcome is the token's, so it would copy a true effect and veto it, the first study's placebo fault. This reads the token's later rows, for this control only."""
    has_set = np.isin(t['token'], np.unique(t['token'][role != 0]))
    arm = np.full(len(role), -1, dtype=np.int8)
    arm[~has_set & (count == 2)] = 1
    arm[~has_set & (count == 1)] = 0
    return arm


def analyse_window(t, window, boot_draws, h2_draws, seed=SEED):
    role, count = roles(t, window)
    ok = eligible(t)
    arm = np.where(ok, role, -1)
    excess = t['win'] - t['price']
    cell = cells(t, window)
    primary = h1(t['fact'], cell, arm, excess, boot_draws, seed)
    weeks = (t['ts'] // WEEK).astype(np.int64)
    by_week = h1(weeks, cell, arm, excess, boot_draws, seed + 3)
    nce = h1(t['fact'], cell, np.where(ok, near_set_arm(t, role, count), -1), excess, boot_draws, seed + 2)
    strict = h1(t['fact'], cell, np.where(ok & t['strict_ok'], role, -1), excess, boot_draws, seed + 4)
    wallets = h1(t['fact'], cell, without_top_wallets(t, arm, count), excess, 0, seed)
    raw = raw_excess(t['fact'], arm, excess, boot_draws, seed + 5)
    by_part = {}
    for part in (0, 1):
        mask = t['part'] == part
        by_part[part] = h1(t['fact'][mask], cell[mask], arm[mask], excess[mask], 0, seed)['diff'] if mask.sum() and (arm[mask] == 1).any() else None
    scored = {k: v[ok] for k, v in t.items()}
    return dict(window=window, h1=primary, by_week=by_week, strict=strict, raw=raw, without_top_wallets=wallets['diff'], h2=h2(scored, window, h2_draws, seed), nce=nce, by_part=by_part, influence=influence(t['fact'], cell, arm, excess), counts=dict(rows=int(len(arm)), eligible=int(ok.sum()), triggers=int((arm == 1).sum()), controls=int((arm == 0).sum()), cooldown_dropped=int(((role == -1) & ok).sum())))


def verdict(result):
    """Fixed before any real number. An association says timing carried information past the paid price, on this data. It names nobody and shows no private information."""
    h, h2r, nce = result['h1'], result['h2'], result['nce']
    week = result.get('by_week') or {}
    raw = result.get('raw') or {}
    strict = result.get('strict') or {}
    if h['diff'] is None or h['matched_share'] < MIN_MATCHED_SHARE:
        return 'INCONCLUSIVE', ['matched share under the floor']
    small = []
    if h['facts_triggers'] < MIN_CLUSTERS:
        small.append('fewer than %d facts with a trigger' % MIN_CLUSTERS)
    if h['kish_facts'] < MIN_KISH:
        small.append('fewer than %d effective facts' % MIN_KISH)
    if h['p'] < ALPHA and h['diff'] > 0:
        reasons = list(small)
        if h2r['p'] >= ALPHA:
            reasons.append('no alignment beyond local intensity')
        if nce['diff'] is None or nce['matched'] < MIN_NCE_ROWS:
            reasons.append('negative control too small to read')
        elif nce['ci'][0] > 0 or nce['diff'] >= 0.5 * h['diff']:
            reasons.append('pairs that never became a set show it too: confounding left after matching')
        if week.get('diff') is None or week['p'] >= ALPHA or week['diff'] <= 0:
            reasons.append('does not hold with whole weeks as clusters')
        if strict.get('diff') is None or strict['p'] >= ALPHA or strict['diff'] <= 0:
            reasons.append('gone once rows within 12 hours before a rise of 0.05 are removed: a slow public reaction explains it as well')
        parts = [v for v in result['by_part'].values() if v is not None]
        if len(parts) == 2 and min(parts) <= 0:
            reasons.append('sign differs between the two holdout parts')
        if result['influence'] is None or result['influence'] <= 0:
            reasons.append('lives on the five most influential facts')
        if result.get('without_top_wallets') is None or result['without_top_wallets'] <= 0:
            reasons.append('lives on the five wallets most often in sets')
        return ('TIMING_ASSOCIATION', []) if not reasons else ('POSITIVE_NOT_INTERPRETABLE', reasons)
    if small:
        return 'INCONCLUSIVE', small
    if h['ci'][1] < 0:
        return 'INCONCLUSIVE', ['significantly negative: the matching or the guard is suspect, and no bound is claimed']
    limits = [('difference', h['ci'][1]), ('weeks as clusters', week.get('ci', [None, None])[1]), ('raw excess', (raw.get('ci') or [None, None])[1])]
    over = [f'{name} reaches {value:.4f}' if value is not None else f'{name} unread' for name, value in limits if value is None or value >= BOUND]
    if over:
        return 'INCONCLUSIVE', over
    return 'BOUNDED_NULL', [f"upper ends {h['ci'][1]:.4f}, {week['ci'][1]:.4f}, {raw['ci'][1]:.4f} under {BOUND}"]
