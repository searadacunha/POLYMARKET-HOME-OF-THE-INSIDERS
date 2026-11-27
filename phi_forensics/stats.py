"""Statistics used across the toolkit: exact tests, resampling, multiple-comparison control, validation splits.

Standard library only, deterministic under a seed. Every function returns what it computed and never a verdict:
deciding what a p-value means belongs to a protocol written before the data are seen.
"""
import math
import random
from collections import defaultdict


def wilson(successes, n, z=1.959963984540054):
    """Wilson score interval of a proportion (95% by default). (None, None) when n is 0."""
    if n <= 0:
        return None, None
    p, z2 = successes / n, z * z
    centre, half = p + z2 / (2 * n), z * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n))
    return max(0.0, (centre - half) / (1 + z2 / n)), min(1.0, (centre + half) / (1 + z2 / n))


def poisson_binomial_pmf(probabilities):
    """Exact distribution of the number of successes of independent trials with different probabilities."""
    pmf = [1.0]
    for p in probabilities:
        if not 0.0 <= p <= 1.0:
            raise ValueError(f"probability out of range: {p}")
        nxt = [0.0] * (len(pmf) + 1)
        for k, mass in enumerate(pmf):
            nxt[k] += mass * (1 - p)
            nxt[k + 1] += mass * p
        pmf = nxt
    return pmf


def poisson_binomial_tail(wins, probabilities):
    """P(W >= wins) when bet i wins with probability probabilities[i], for example the price paid.

    The null model of a track record: a wallet that pays 0.90 and wins proves nothing, one that pays 0.05 and
    wins repeatedly does. Independence between bets is assumed and must be argued by the caller.
    """
    return min(1.0, sum(poisson_binomial_pmf(probabilities)[max(0, wins):]))


def binomial_tail(k, n, p):
    """P(X >= k) for X ~ Binomial(n, p), exact."""
    return poisson_binomial_tail(k, [p] * n)


def _log_choose(n, k):
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)


def fisher_exact(a, b, c, d, alternative="greater"):
    """Fisher's exact test of the table [[a, b], [c, d]]. alternative: 'greater' (a larger than chance), 'less', 'two-sided'."""
    if min(a, b, c, d) < 0:
        raise ValueError("counts must not be negative")
    row, col, n = a + b, a + c, a + b + c + d
    low, high = max(0, row + col - n), min(row, col)
    logp = {x: _log_choose(col, x) + _log_choose(n - col, row - x) - _log_choose(n, row) for x in range(low, high + 1)}
    if alternative == "greater":
        chosen = [v for x, v in logp.items() if x >= a]
    elif alternative == "less":
        chosen = [v for x, v in logp.items() if x <= a]
    elif alternative == "two-sided":
        chosen = [v for v in logp.values() if v <= logp[a] + 1e-9]
    else:
        raise ValueError(f"unknown alternative: {alternative}")
    return min(1.0, sum(math.exp(v) for v in chosen))


def _mean(values):
    return sum(values) / len(values)


def permutation_test(treated, control, statistic=None, draws=10_000, seed=0, alternative="greater"):
    """Label-permutation test of a difference between two samples.

    Returns the observed statistic, the Monte Carlo p-value (hits + 1) / (draws + 1), which is never 0, and the
    number of hits, so that a result with no hit is reported as a bound (p < 1 / draws) and not as an estimate.
    """
    if not treated or not control:
        raise ValueError("both samples must be non-empty")
    statistic = statistic or (lambda a, b: _mean(a) - _mean(b))
    observed = statistic(treated, control)
    pool, k, rng, hits = list(treated) + list(control), len(treated), random.Random(seed), 0
    for _ in range(draws):
        rng.shuffle(pool)
        value = statistic(pool[:k], pool[k:])
        if (alternative == "greater" and value >= observed) or (alternative == "less" and value <= observed) \
                or (alternative == "two-sided" and abs(value) >= abs(observed)):
            hits += 1
    return {"observed": observed, "p": (hits + 1) / (draws + 1), "hits": hits, "draws": draws, "seed": seed, "alternative": alternative}


def _percentile(ordered, q):
    position = q * (len(ordered) - 1)
    lower, upper = math.floor(position), math.ceil(position)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def bootstrap_ci(values, statistic=_mean, draws=5_000, level=0.95, seed=0):
    """Percentile bootstrap interval of a statistic of independent observations."""
    if not values:
        raise ValueError("no observation")
    rng, n = random.Random(seed), len(values)
    estimates = sorted(statistic([values[rng.randrange(n)] for _ in range(n)]) for _ in range(draws))
    alpha = (1 - level) / 2
    return {"estimate": statistic(values), "low": _percentile(estimates, alpha), "high": _percentile(estimates, 1 - alpha),
            "level": level, "draws": draws, "seed": seed, "n": n}


def cluster_bootstrap_ci(rows, cluster_of, statistic, draws=5_000, level=0.95, seed=0):
    """Bootstrap that resamples whole clusters (one operator, one funder, one event), not rows.

    Rows of one cluster are not independent: resampling rows would understate the interval. The effective sample
    size is the number of clusters, returned as n_clusters.
    """
    groups = defaultdict(list)
    for row in rows:
        groups[cluster_of(row)].append(row)
    clusters = list(groups.values())
    if not clusters:
        raise ValueError("no observation")
    rng, n, estimates = random.Random(seed), len(clusters), []
    for _ in range(draws):
        sample = [row for _ in range(n) for row in clusters[rng.randrange(n)]]
        estimates.append(statistic(sample))
    estimates.sort()
    alpha = (1 - level) / 2
    return {"estimate": statistic(list(rows)), "low": _percentile(estimates, alpha), "high": _percentile(estimates, 1 - alpha),
            "level": level, "draws": draws, "seed": seed, "n_rows": len(rows), "n_clusters": n}


def bonferroni(pvalues):
    return [min(1.0, p * len(pvalues)) for p in pvalues]


def holm(pvalues):
    """Holm step-down adjusted p-values (family-wise error), in the input order."""
    order, m, adjusted, running = sorted(range(len(pvalues)), key=lambda i: pvalues[i]), len(pvalues), [0.0] * len(pvalues), 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (m - rank) * pvalues[i]))
        adjusted[i] = running
    return adjusted


def benjamini_hochberg(pvalues):
    """Benjamini-Hochberg adjusted p-values (false discovery rate under independence or positive dependence)."""
    order, m, adjusted, running = sorted(range(len(pvalues)), key=lambda i: pvalues[i], reverse=True), len(pvalues), [0.0] * len(pvalues), 1.0
    for position, i in enumerate(order):
        running = min(running, pvalues[i] * m / (m - position))
        adjusted[i] = max(running, pvalues[i])  # p * m / m can round one ulp under p
    return adjusted


def _normal_cdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def _normal_quantile(q):
    low, high = -10.0, 10.0
    for _ in range(80):  # bisection: exact enough for a design calculation, no table needed
        mid = (low + high) / 2
        low, high = (mid, high) if _normal_cdf(mid) < q else (low, mid)
    return (low + high) / 2


def power_two_proportions(p_control, p_treated, n_control, n_treated, alpha=0.05):
    """Power of the one-sided two-proportion z-test to detect p_treated > p_control (normal approximation)."""
    pooled = (p_control * n_control + p_treated * n_treated) / (n_control + n_treated)
    se_null = math.sqrt(pooled * (1 - pooled) * (1 / n_control + 1 / n_treated))
    se_alt = math.sqrt(p_control * (1 - p_control) / n_control + p_treated * (1 - p_treated) / n_treated)
    if se_alt == 0:
        return 1.0 if p_treated > p_control else 0.0
    return _normal_cdf(((p_treated - p_control) - _normal_quantile(1 - alpha) * se_null) / se_alt)


def minimum_detectable_effect(p_control, n_control, n_treated, alpha=0.05, power=0.80):
    """Smallest increase over p_control detected with the given power, to state what a null result excludes."""
    low, high = 0.0, 1.0 - p_control
    if power_two_proportions(p_control, p_control + high, n_control, n_treated, alpha) < power:
        return None  # even a jump to certainty would not be detected at this sample size
    for _ in range(60):
        mid = (low + high) / 2
        low, high = (low, mid) if power_two_proportions(p_control, p_control + mid, n_control, n_treated, alpha) >= power else (mid, high)
    return high


def walk_forward_splits(times, folds=4, embargo=0.0, min_train=1):
    """Expanding-window splits: train strictly before each test block, with an embargo between them.

    Yields (train_indices, test_indices) over the positions of `times`. A row whose time falls within `embargo`
    before a test block is in neither set, so a label that needs `embargo` seconds to be known cannot leak.
    """
    order = sorted(range(len(times)), key=lambda i: times[i])
    if folds < 1 or len(order) < folds + 1:
        raise ValueError("not enough observations for the requested folds")
    block = len(order) // (folds + 1)
    for fold in range(1, folds + 1):
        test = order[fold * block:(fold + 1) * block if fold < folds else len(order)]
        start = times[test[0]]
        train = [i for i in order[:fold * block] if times[i] < start - embargo]
        if len(train) >= min_train:
            yield train, test


def precision_recall(true_positive, false_positive, false_negative):
    """Precision and recall with Wilson intervals. A rate with an empty denominator is None, never 0."""
    flagged, positives = true_positive + false_positive, true_positive + false_negative
    return {"precision": true_positive / flagged if flagged else None, "precision_ci": wilson(true_positive, flagged),
            "recall": true_positive / positives if positives else None, "recall_ci": wilson(true_positive, positives),
            "flagged": flagged, "positives": positives}


def pair_confusion(truth, predicted):
    """Pairwise agreement between two partitions of the same items, given as {item: cluster label}.

    Returns the pair counts, pairwise precision and recall, and the adjusted Rand index (1 identical, about 0 at
    chance). Items missing from `predicted` are singletons: a method is not rewarded for ignoring an item.
    """
    items = sorted(truth)
    labels = {item: predicted.get(item, ("singleton", item)) for item in items}
    both = same_truth = same_predicted = 0
    for i, a in enumerate(items):
        for b in items[i + 1:]:
            t, q = truth[a] == truth[b], labels[a] == labels[b]
            both, same_truth, same_predicted = both + (t and q), same_truth + t, same_predicted + q
    pairs = len(items) * (len(items) - 1) // 2
    expected = same_truth * same_predicted / pairs if pairs else 0.0
    ceiling = (same_truth + same_predicted) / 2
    ari = 1.0 if ceiling == expected else (both - expected) / (ceiling - expected)
    return {"pairs": pairs, "true_pairs": same_truth, "predicted_pairs": same_predicted, "agreeing_pairs": both,
            "precision": both / same_predicted if same_predicted else None, "recall": both / same_truth if same_truth else None,
            "adjusted_rand_index": ari}
