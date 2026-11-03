"""Trace accounts end to end. Usage: run_wallets.py <list.json> [slug ...] [--light] [--budget=N]. Each case file is written atomically: a re-run replays the store and costs no network."""
import json
import sys
import time
import traceback
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gf import account, env, windows
from gf.bridges import Bridges
from gf.net import BudgetSpent, Net, Refused
from gf.solana import Solana
from gf.tracer import Trace

env.redirect_temp()
ROOT = env.data_root() / 'wallets'


def main():
    light = '--light' in sys.argv
    entries = json.loads(Path(sys.argv[1]).read_text())
    only = {a for a in sys.argv[2:] if not a.startswith('--')}
    budget = next((int(a.split('=', 1)[1]) for a in sys.argv[2:] if a.startswith('--budget=')), 200_000)
    net = Net(budget=budget)
    solana = Solana(net)
    relay = Bridges(net, solana=solana, relay_budget=40 if light else 250)
    lookup = windows.Index()
    for entry in entries:
        slug, wallet = entry['slug'], entry['wallet'].lower()
        if only and slug not in only:
            continue
        started, before = time.time(), net.calls
        out = ROOT / slug
        out.mkdir(parents=True, exist_ok=True)
        if light and (out / 'trace.json').exists():  # resume: a finished light case costs nothing and is kept
            continue
        try:
            acct, rows = account.load(net, wallet, **(dict(max_rows=3000, max_money=30) if light else {}))
            trace = Trace(net, slug, wallet, entry.get('own', []), relay=relay, window_events=lookup.events, solana=solana, **(dict(max_depth=2, node_budget=14) if light else {}))
            trace.log = lambda m: print(slug, m, flush=True)
            result = trace.run(acct)
            result['account'] = acct
            result['group'] = entry.get('group')
            result['mode'] = 'light: depth 2, 14 nodes, 30 money rows' if light else 'full'
            for name, value in (('trace.json', result), ('activity.json', rows)):
                tmp = out / (name + '.tmp')
                tmp.write_text(json.dumps(value))
                tmp.replace(out / name)
            print(slug, 'edges', len(result['edges']), 'stops', len(result['stops']), 'nodes', len(result['nodes']), 'calls', net.calls - before, f'{time.time() - started:.0f}s', flush=True)
        except env.Stop:
            raise
        except BudgetSpent as exc:  # the unfinished case has no output file: the next batch resumes it from the store
            print('BUDGET_SPENT', slug, exc, flush=True)
            break
        except Exception as exc:  # one bad case must not lose the others; the failure stays in the log and the case has no output file
            print('FAILED', slug, type(exc).__name__, str(exc)[:300], flush=True)
            traceback.print_exc()
    print('done calls', net.calls, 'hits', net.hits, flush=True)


if __name__ == '__main__':
    main()
