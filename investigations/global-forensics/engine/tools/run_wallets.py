"""Trace accounts end to end. Usage: run_wallets.py <list.json> [slug ...] [--light] [--budget=N] [--redo-before=EPOCH] [--only-lost]. An entry with "mode": "full" is read in full even under --light. --only-lost reads again only the files that hold a failed read. Each case file is written atomically: a re-run replays the store and costs no network."""
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
NARROW = dict(max_depth=2, node_budget=9, max_flows=6, chains=(1, 137, 42161))  # 9: the 8 of the first runs plus the wallet's own history
NARROW_MODE = 'light: depth 2, 9 nodes per direction, 6 largest flows per node, Ethereum, Polygon and Arbitrum, 30 money rows'


def lost_reads(done):
    """A file written during a network outage holds failed reads: keep it, and read it again at the next batch."""
    return any(x['reason'] in ('READ_FAILED', 'SERVICE_OR_SHARED:UNREAD') for x in json.loads(done.read_text())['stops'])


def light_profile(done):
    """A file first traced wider keeps its width on a redo: the store holds those reads, and narrowing would drop proved relations."""
    mode = json.loads(done.read_text()).get('mode', '') if done.exists() else ''
    if '14 nodes' not in mode:
        return NARROW, NARROW_MODE
    return dict(max_depth=2, node_budget=14, max_flows=12 if '12 largest' in mode else None), mode


def main():
    light_list, only_lost = '--light' in sys.argv, '--only-lost' in sys.argv
    entries = json.loads(Path(sys.argv[1]).read_text())
    only = {a for a in sys.argv[2:] if not a.startswith('--')}
    budget = next((int(a.split('=', 1)[1]) for a in sys.argv[2:] if a.startswith('--budget=')), 200_000)
    net = Net(budget=budget)
    solana = Solana(net)
    redo_before = next((float(a.split('=', 1)[1]) for a in sys.argv[2:] if a.startswith('--redo-before=')), None)
    relay = Bridges(net, solana=solana)
    lookup = windows.Index()
    for entry in entries:
        slug, wallet = entry['slug'], entry['wallet'].lower()
        if only and slug not in only:
            continue
        light = light_list and entry.get('mode') != 'full'
        started, before = time.time(), net.calls
        out = ROOT / slug
        out.mkdir(parents=True, exist_ok=True)
        done = out / 'trace.json'
        if only_lost and not (done.exists() and lost_reads(done)):
            continue
        if light and done.exists() and (redo_before is None or done.stat().st_mtime >= redo_before) and not lost_reads(done):  # resume: a finished light case costs nothing and is kept
            continue
        relay.budget['left'] = 8 if light else 60  # each case its own: a shared budget ran out early and later cases lost their bridges
        try:
            profile, mode = light_profile(done) if light else ({}, 'full')
            acct, rows = account.load(net, wallet, **(dict(max_rows=3000, max_money=30) if light else {}))
            trace = Trace(net, slug, wallet, entry.get('own', []), relay=relay, window_events=lookup.events, solana=solana, **profile)
            trace.log = lambda m: print(slug, m, flush=True)
            result = trace.run(acct, rows)
            result['account'] = acct
            result['group'] = entry.get('group')
            result['mode'] = mode
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
