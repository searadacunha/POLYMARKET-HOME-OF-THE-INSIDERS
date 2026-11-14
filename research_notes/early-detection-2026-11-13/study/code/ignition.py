"""Ignition detection on a 10-minute price series. Pure functions, no I/O, no look-ahead:
the decision at grid time t uses only points at or before t (p_post is a later LABEL-side quantity, kept apart).

An ignition of side S ('YES' or 'NO') at grid time t1 requires, with x = price of S:
  baseline window B = [t1 - 7h, t1 - 1h): at least MIN_BASE points, median(B) <= BASE_MAX and max(B) <= QUIET_MAX
  jump: x(t1) >= max(MULT * median(B), median(B) + ABS_STEP)
Only the first ignition of each side of a market is kept. t0 = first grid time in [t1 - 1h, t1] with x > 1.5 * median(B).
"""
from statistics import median

GRID = 600           # seconds between points (fidelity 10 minutes)
BASE_FROM = 7 * 3600
BASE_TO = 1 * 3600
MIN_BASE = 18        # of the 36 possible points
BASE_MAX = 0.15
QUIET_MAX = 0.20
MULT = 3.0
ABS_STEP = 0.10
START_MULT = 1.5
POST_DELAY = 3600    # p_post is read at the first point at or after t0 + 60 min
POST_MAX = 0.90      # above this the jump is treated as a public resolution, not a pre-reveal move
MIN_OPEN_AFTER = 2 * 3600


def first_ignition(series, side):
    """series: list of (t, p_yes) sorted by t. Returns a dict or None. Uses a sliding window; O(n)."""
    xs = [(t, p if side == "YES" else 1.0 - p) for t, p in series]
    n = len(xs); lo = 0; hi = 0  # window indices [lo, hi) over points with t1-7h <= t < t1-1h
    for i in range(n):
        t1, x1 = xs[i]
        while hi < n and xs[hi][0] < t1 - BASE_TO: hi += 1
        while lo < hi and xs[lo][0] < t1 - BASE_FROM: lo += 1
        if hi - lo < MIN_BASE: continue
        if x1 < ABS_STEP or xs[hi - 1][1] > QUIET_MAX: continue   # exact shortcuts: the jump needs x1 >= median + ABS_STEP, quiet needs every point <= QUIET_MAX
        base = [x for _, x in xs[lo:hi]]
        b = median(base)
        if b > BASE_MAX or max(base) > QUIET_MAX: continue
        if x1 < max(MULT * b, b + ABS_STEP): continue
        t0 = t1
        for j in range(hi, i + 1):
            if xs[j][0] >= t1 - BASE_TO and xs[j][1] > START_MULT * b:
                t0 = xs[j][0]; break
        return {"side": side, "t1": t1, "t0": t0, "base": round(b, 6), "base_max": round(max(base), 6), "x_t1": round(x1, 6),
                "n_base": hi - lo}
    return None


def post_price(series, side, t0):
    """LABEL-SIDE helper (uses the future of t0): price of S at the first point at or after t0 + POST_DELAY, or None."""
    for t, p in series:
        if t >= t0 + POST_DELAY:
            return (t, p if side == "YES" else 1.0 - p)
    return None


def _selftest():
    quiet = [(i * GRID, 0.03) for i in range(60)]
    jump = quiet + [(60 * GRID, 0.05), (61 * GRID, 0.11), (62 * GRID, 0.31), (63 * GRID, 0.39)] + [((64 + k) * GRID, 0.40) for k in range(12)]
    ig = first_ignition(jump, "YES")
    assert ig and ig["t1"] == 62 * GRID and ig["t0"] == 60 * GRID and abs(ig["base"] - 0.03) < 1e-9, ig  # 0.11 < base + 0.10
    assert first_ignition(quiet, "YES") is None and first_ignition(jump, "NO") is None
    assert first_ignition([(t, 1 - p) for t, p in jump], "NO")["t1"] == 62 * GRID          # symmetric on the NO side
    noisy = [(i * GRID, 0.03 if i % 7 else 0.25) for i in range(60)] + [(60 * GRID, 0.4)]
    assert first_ignition(noisy, "YES") is None                                           # a spiky baseline is not quiet
    sparse = [(i * GRID, 0.03) for i in range(0, 60, 4)] + [(61 * GRID, 0.4)]
    assert first_ignition(sparse, "YES") is None                                          # too few baseline points
    assert post_price(jump, "YES", 60 * GRID) == (66 * GRID, 0.40)
    slow = [(i * GRID, 0.03 + 0.002 * i) for i in range(100)]
    assert first_ignition(slow, "YES") is None                                            # a slow drift never triples within the window
    print("ignition selftest ok")


if __name__ == "__main__":
    _selftest()
