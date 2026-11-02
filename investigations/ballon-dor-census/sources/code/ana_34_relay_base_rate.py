"""How ordinary is Relay? Share of a random sample of the population whose Polymarket wallet sent to the Relay depository or received from a Relay solver. If most do, "all use Relay" links nobody."""
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import labels
import net

ROOT = net.ROOT


def main():
    d = json.load(open(ROOT / 'derived/stats_v2_table.json'))['wallets']
    fresh = sorted(w for w, v in d.items() if v['status'] == 'fresh')
    old = sorted(w for w, v in d.items() if v['status'] == 'old')
    rng = random.Random(20261102)
    relay = set(labels._load_relay())
    out = {}
    for g, pool in (('fresh', fresh), ('old', old)):
        n_any = n_out = n_in = read = 0
        for w in rng.sample(pool, 100):
            try:
                rows = net.es_all(137, 'tokentx', w)
            except net.FetchError:
                continue
            read += 1
            o = any(r['to'].lower() in relay for r in rows)
            i = any(r['from'].lower() in relay for r in rows)
            n_out += o
            n_in += i
            n_any += o or i
        out[g] = dict(read=read, any_relay=n_any, to_relay=n_out, from_relay=n_in)
    (ROOT / 'derived/relay_base_rate.json').write_text(json.dumps(out, indent=1))
    print(out)


if __name__ == '__main__':
    main()
