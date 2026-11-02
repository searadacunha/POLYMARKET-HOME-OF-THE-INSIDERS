"""A detection rule changes only if independent data shows a gain. Improving on the data used to tune it proves nothing.

The evaluator takes a rule's parameters and a dataset, and returns the units it flags. There is no ground truth on real data, so labels come from injected
cases and known controls; passing here shows mechanics on those cases, not detection of private information. The gate moves a pointer in the harness's own
database, and production's rules stay as they are until Benjamin decides otherwise.
"""
import json
import math
import time

from .store import dumps, sha


class HoldoutRefused(RuntimeError):
    pass


def score(flags, labels):
    tp = sum(1 for u, positive in labels.items() if positive and flags.get(u))
    fn = sum(1 for u, positive in labels.items() if positive and not flags.get(u))
    fp = sum(1 for u, positive in labels.items() if not positive and flags.get(u))
    tn = sum(1 for u, positive in labels.items() if not positive and not flags.get(u))
    return dict(tp=tp, fn=fn, fp=fp, tn=tn, recall=tp / (tp + fn) if tp + fn else None, false_positive_rate=fp / (fp + tn) if fp + tn else None)


def exact_mcnemar(better, worse):
    """One-sided: chance of at least this many wins among the units where the two rules disagree."""
    n = better + worse
    if n == 0:
        return 1.0
    return sum(math.comb(n, k) for k in range(better, n + 1)) / 2 ** n


def gate(h, name, candidate, evaluate, development, holdout, *, alpha=.05, max_uses=3, tolerance=0.0, baseline=None):
    """Every look at a holdout is counted, because a holdout used many times becomes training data. Returns the report; raises if the data cannot judge."""
    overlap = set(development['labels']) & set(holdout['labels'])
    if overlap:
        raise HoldoutRefused(f'{len(overlap)} units are in both the development and holdout sets')
    holdout_sha = sha(holdout['labels'])
    uses = h.cx.execute('SELECT COUNT(*) FROM holdout_uses WHERE holdout_sha=?', (holdout_sha,)).fetchone()[0]
    if uses >= max_uses:
        raise HoldoutRefused(f'This holdout was already used {uses} times; a new rule needs new data')
    active = h.cx.execute("SELECT * FROM rules WHERE name=? AND status='active'", (name,)).fetchone()
    current = json.loads(active['params']) if active else (baseline or {})
    with h.tx() as cx:
        rule = cx.execute("INSERT INTO rules(name, params, status, at) VALUES(?,?,'candidate',?)", (name, dumps(candidate), time.time())).lastrowid
        cx.execute('INSERT INTO holdout_uses VALUES(?,?,?)', (holdout_sha, rule, time.time()))
    old_flags, new_flags = evaluate(current, holdout), evaluate(candidate, holdout)
    old, new = score(old_flags, holdout['labels']), score(new_flags, holdout['labels'])
    better = sum(1 for u, positive in holdout['labels'].items() if bool(new_flags.get(u)) == positive and bool(old_flags.get(u)) != positive)
    worse = sum(1 for u, positive in holdout['labels'].items() if bool(new_flags.get(u)) != positive and bool(old_flags.get(u)) == positive)
    p = exact_mcnemar(better, worse)
    dev_old, dev_new = score(evaluate(current, development), development['labels']), score(evaluate(candidate, development), development['labels'])
    reasons = []
    if new['recall'] is None or new['false_positive_rate'] is None:
        reasons.append('holdout lacks positives or negatives')
    else:
        if new['recall'] < old['recall'] - tolerance:
            reasons.append(f"recall falls from {old['recall']:.3f} to {new['recall']:.3f}")
        if new['false_positive_rate'] > old['false_positive_rate'] + tolerance:
            reasons.append(f"false positive rate rises from {old['false_positive_rate']:.3f} to {new['false_positive_rate']:.3f}")
        if p > alpha:
            reasons.append(f'gain not shown: {better} units better, {worse} worse, p={p:.3f}')
    report = dict(rule=rule, name=name, candidate=candidate, current=current, holdout_sha=holdout_sha, holdout_use=uses + 1, development=dict(current=dev_old, candidate=dev_new), holdout=dict(current=old, candidate=new), better=better, worse=worse, p=p, alpha=alpha, passed=not reasons, reasons=reasons)
    digest = sha(report)
    with h.tx() as cx:
        h.put_artifact(report)
        cx.execute('INSERT INTO experiments(name, params, seed, code_sha, input_sha, metrics, outcome, at) VALUES(?,?,?,?,?,?,?,?)', (f'gate:{name}', dumps(candidate), '', '', holdout_sha, dumps(report['holdout']), 'accepted' if report['passed'] else 'refused', time.time()))
        if report['passed']:
            cx.execute("UPDATE rules SET status='retired' WHERE name=? AND status='active'", (name,))
            cx.execute("UPDATE rules SET report_sha=?, status='active', at=? WHERE id=?", (digest, time.time(), rule))
            h.log('info', 'rule_activated', rule=rule, name=name, report=digest)
        else:
            cx.execute("UPDATE rules SET report_sha=?, status='rejected', reason=?, at=? WHERE id=?", (digest, '; '.join(reasons), time.time(), rule))
            h.log('warning', 'rule_refused', rule=rule, name=name, reasons=reasons)
    from . import memory
    memory.remember(h, 'method_ok' if report['passed'] else 'method_bad', f'rule:{name}', sha(candidate), f"{dumps(candidate)}: {'; '.join(reasons) or 'accepted on holdout'}", status='verified', source_sha=digest)
    return report


def replay_engine(params, dataset, baseline_config):
    """Replays a dataset through the real engine with these parameters, in a throwaway store. `rows` are engine rows in order of observation; a unit is wallet|event."""
    import tempfile
    from signal_engine.prospective_detection import run_cycle
    from signal_engine.store import SignalStore
    config = dict(baseline_config, **params)
    flags = {}
    with tempfile.TemporaryDirectory(prefix='gate_') as folder:
        store = SignalStore(folder + '/state.sqlite3')
        try:
            for market in dataset['markets']:
                store.add_market(**market)
            for batch in dataset['batches']:
                outputs, _ = run_cycle(store, store.add_trades(batch), max(r['observed_at'] for r in batch), config)
                for output in outputs:
                    for pair in output['pairs']:
                        flags[f"{pair['wallet']}|{output['event_key']}"] = True
        finally:
            store.close()
    return flags
