"""Fix the study window once, then read every active labelled address and hub on each free chain, outgoing only, 90 days. Re-run resumes from checkpoints. Writes state/window.json and state/out_full/."""
import csv, json, os, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import es, net, outflows
ROOT = net.ROOT
WIN = ROOT / 'state/window.json'
# Hubs first suspected from their flows with 0x4778, then read as KuCoin on Blockscout (state/hubs_probe.py); 0x2458 stays unknown, 5 recipients, not a payout shape
KUCOIN_OR_UNRELATED = {'0xd91efec7e42f80156d1d9f660a69847188950747', '0x58edf78281334335effa23101bbe3371b6a36a51', '0x83c41363cbee0081dab75cb841fa24f3db46627e', '0x45300136662dd4e58fc0df61e6290dffd992b785', '0x41e457717052a9f80fb2a5a06caccda18469fb17', '0x2458b3ad07e88b78d0204525d9cbf445c22843e7'}


def block_at(chain, ts, closest):
    d = net.get(es.URL, dict(chainid=chain, module='block', action='getblocknobytime', timestamp=ts, closest=closest), pause=.6, secret=dict(apikey=net._key_from_env()))
    return int(d['result'])


if WIN.exists():
    win = json.loads(WIN.read_text())
else:
    t_end = int(time.time())
    win = dict(t_end=t_end, t_start=t_end - 90 * 86400, chains={})
    for c in (1, 137, 42161):
        win['chains'][str(c)] = [block_at(c, win['t_start'], 'after'), block_at(c, t_end, 'before')]
    WIN.write_text(json.dumps(win))
print(win, flush=True)
outflows.OUT.mkdir(parents=True, exist_ok=True)
todo = {}
for r in csv.DictReader(open(ROOT / 'state/registry_behaviour.csv')):
    if r['active_90d'] == 'True' and int(r['n_out']) > 0 and r['address'] not in KUCOIN_OR_UNRELATED:
        todo.setdefault((int(r['chain']), r['address']), r['labels'])
extra = sys.argv[1:]  # chain:address pairs added after reading the first results, written in PLAN.md
for x in extra:
    c, a = x.split(':')
    todo.setdefault((int(c), a.lower()), 'ajout')
print(len(todo), 'chain-address pairs', flush=True)
for (c, a), lab in sorted(todo.items(), key=lambda kv: (kv[0][0], kv[0][1])):
    start, end = win['chains'][str(c)]
    print('==', c, a, lab[:50], flush=True)
    res = {act: outflows.walk(c, a, act, start, end) for act in ('txlist', 'tokentx', 'txlistinternal')}
    (outflows.OUT / f'{c}_{a}.json').write_text(json.dumps(res))
print('done')
