"""Family-wise false alarm rate of T1 to T4 under the synthetic null, 30 seeds, 500 permutations each. Holm at 5 %."""
import json
import numpy as np
import ana_50_stats as S
import net

out = []
for seed in range(1000, 1030):
    w, r = S.synthetic(0.0, seed)
    res = S.all_tests(w, r, np.random.default_rng(seed), 500)
    out.append({x['test']: x['p_holm'] for x in res})
    print(seed, out[-1], flush=True)
tests = ('T1', 'T2', 'T3', 'T4')
summary = dict(seeds=len(out), any_alarm=sum(any(o[t] < .05 for t in tests) for o in out), per_test={t: sum(o[t] < .05 for o in out) for t in tests})
(net.ROOT / 'derived/stats_null_rate.json').write_text(json.dumps(dict(summary=summary, rows=out), indent=1))
print(summary)
