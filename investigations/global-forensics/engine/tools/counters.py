"""Real counts, from the files and nothing else. Usage: counters.py <results dir>. Writes COUNTERS.json and COUNTERS.md. A file written is not a file finished."""
import json
import sys
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gf import env, state

LISTS = (("Ballon d'Or", 'lists_ballon_dor.json'), ('Documented accounts', 'lists_documented.json'), ('ChangeNOW', 'changenow/wallets_cn.json'), ('Discovery', 'discovery/wallets.json'))


def count(row, s):
    """Reconciled is a question of its own: a file can be reconciled and in any trace state."""
    row['generated'] += 1
    row['with_wallet_history'] += 'TRADING_WALLET_HISTORY_NOT_READ' not in s['work_left']
    row['reconciled'] += s['accounting'] == state.ACCOUNTING_RECONCILED
    row[{state.TRACE_COMPLETE: 'trace_complete', state.BLOCKED_BY_DATA: 'blocked', state.WORK_LEFT: 'work_left'}[s['processing']]] += 1


def main(results):
    results = Path(results)
    root = env.data_root() / 'wallets'
    table, files, named_wallets = [], {}, {}
    for name, listing in LISTS:
        entries = json.loads((results / listing).read_text())
        row = dict(group=name, listed=len(entries), generated=0, reconciled=0, trace_complete=0, blocked=0, work_left=0, not_processed=0, same_wallet_as_a_named_file=0, with_wallet_history=0, history=Counter(), funding=Counter(), exits=Counter(), work_reasons=Counter(), blocked_reasons=Counter(), frontiers=Counter())
        for entry in entries:
            if name == 'Discovery' and entry['wallet'] in named_wallets:
                row['same_wallet_as_a_named_file'] += 1
                continue
            named_wallets.setdefault(entry['wallet'], entry['slug'])
            path = root / entry['slug'] / 'trace.json'
            if not path.exists():
                row['not_processed'] += 1
                continue
            activity = path.with_name('activity.json')
            s = state.file_state(json.loads(path.read_text()), json.loads(activity.read_text()) if activity.exists() else None)
            files[entry['slug']] = dict(group=name, wallet=entry['wallet'], written_at=int(path.stat().st_mtime), **s)
            count(row, s)
            row['history'][s['polymarket_history']['state']] += 1
            row['funding'][s['funding']['state']] += 1
            row['exits'][s['exits']['state']] += 1
            row['work_reasons'].update(s['work_left'].keys())
            row['blocked_reasons'].update(s['blocked_by'])
            row['frontiers'].update({k: v for k, v in s['frontiers'].items() if v})
        table.append(row)
    (results / 'COUNTERS.json').write_text(json.dumps(dict(table=table, files=files), indent=0, default=dict))
    join = lambda c: ', '.join(f'{k} {v}' for k, v in c.most_common()) or 'none'
    lines = ['# Counts', '', 'Written by `engine/tools/counters.py` from `wallets/*/trace.json`, by the rules of `engine/gf/state.py`.', '', '- **Accounting reconciled:** on a complete activity list, the money rows close within 1 USD against the balance read on chain. It says nothing about who paid or who was paid, so it can overlap with every state below.', '- **Traced to public frontiers:** every deposit and withdrawal row has its path, the books close, and every branch ended on a complete history, at a named service or verified contract, or at a hub measured in the file. A branch stopped by a budget never counts.', '- **Work left:** a read, a budget, a branch or a check is open.', '- **Blocked by data:** nothing left to read here, and what is needed is not public. The motives are below.', '', 'The last four columns add up to the accounts listed once the same-wallet column is taken out. No state asks for a civil identity or a platform\'s internal records.', '', '| Group | Listed | Same wallet as a named file | Accounting reconciled | Traced to public frontiers | Work left | Blocked by data | Not yet processed |', '|---|---:|---:|---:|---:|---:|---:|---:|']
    for r in table:
        lines.append(f"| {r['group']} | {r['listed']} | {r['same_wallet_as_a_named_file']} | {r['reconciled']} | {r['trace_complete']} | {r['work_left']} | {r['blocked']} | {r['not_processed']} |")
    lines += ['', '## State by group', '', '| Group | Polymarket history | Funding | Exits | Branches at a frontier, in files | With the wallet\'s own history | Blocked by |', '|---|---|---|---|---|---:|---|']
    for r in table:
        lines.append(f"| {r['group']} | {join(r['history'])} | {join(r['funding'])} | {join(r['exits'])} | {join(r['frontiers'])} | {r['with_wallet_history']} | {join(r['blocked_reasons'])} |")
    lines += ['', '## Work left', '', 'Number of files holding each reason.', '', '| Group | Reasons |', '|---|---|']
    for r in table:
        lines.append(f"| {r['group']} | {join(r['work_reasons'])} |")
    queue = json.loads((results / 'discovery/queue.json').read_text()) if (results / 'discovery/queue.json').exists() else None
    if queue:
        lines += ['', '## Discovery queue', '', f"From `results/discovery/queue.json`, {queue['read']} of {queue['of']} wallets read for the pass and {len(queue['failed'])} not read. A priority is a reading order, no finding, and every wallet stays in the queue.", '', '| Tier | Why | Listed | File written | Left |', '|---:|---|---:|---:|---:|']
        why = {1: 'same owner key, shared private funder, direct move with a listed address, or money already seen in a traced file', 2: 'shared private destination, or several markets', 3: 'no hint in this pass, largest entry first'}
        for tier in (1, 2, 3):
            items = [r for r in queue['queue'] if r['tier'] == tier]
            have = sum((root / r['slug'] / 'trace.json').exists() for r in items)
            lines.append(f'| {tier} | {why[tier]} | {len(items)} | {have} | {len(items) - have} |')
    (results / 'COUNTERS.md').write_text('\n'.join(lines) + '\n')
    for r in table:
        print(r['group'], 'listed', r['listed'], 'reconciled', r['reconciled'], 'traced_to_frontiers', r['trace_complete'], 'work_left', r['work_left'], 'blocked_by_data', r['blocked'], 'not_processed', r['not_processed'], flush=True)
    print('ALL', *(f"{k} {sum(r[k] for r in table)}" for k in ('reconciled', 'trace_complete', 'work_left', 'blocked', 'not_processed')), flush=True)


if __name__ == '__main__':
    main(sys.argv[1])
