"""Who paid each account and where its money went, with transactions, amounts, levels and what is still open. Usage: money_report.py <results dir>. Writes FUNDERS_AND_EXITS.md and .json, from wallets/*/trace.json and nothing else.

A payer or destination is the address one hop from the account or its keys. A frontier is where a branch further out stopped. Tokens are fungible: a flow at a frontier passed through an address on the way, and is not shown to be the same units.
"""
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gf import env, state

GROUPS = (("Ballon d'Or", 'lists_ballon_dor.json'), ('Documented accounts', 'lists_documented.json'), ('ChangeNOW', 'changenow/wallets_cn.json'))
ROLES = {'funding': ('deposit_path', 'bridge_payout', 'transfer'), 'cashout': ('withdrawal_path', 'bridge_deposit', 'transfer')}
MIN_USD = 1.0  # gas top-ups and dust stay in the file, not on this page
ROUGH = 'USD at list rates: exact for dollar tokens, an estimate for the others.'


def far_side(e):
    """The address behind a bridge when the record names it, with what proves it. A solver or a depository pays everybody and says nothing."""
    near = e['from'] if e['direction'] == 'funding' else e['to']
    if e['role'] not in ('bridge_payout', 'bridge_deposit'):
        return near, e['chain_id'], None
    try:
        hop = json.loads(e.get('note') or '')
    except ValueError:  # a record too long for the file: the bridge stays the answer, and the file holds the transaction
        return near, e['chain_id'], 'bridge record not kept'
    far, chain = (hop.get('sender'), hop.get('origin_chain')) if e['direction'] == 'funding' else (hop.get('recipient'), hop.get('destination_chain'))
    if not far:
        return near, e['chain_id'], f"{hop.get('protocol')}, no address in the record"
    far = far.lower() if far.startswith('0x') else far
    return far, chain, f"{hop.get('protocol')}, same id on both chains" if hop.get('proof') is True else f"{hop.get('protocol')}, API record only"


def counterparties(result, direction):
    """One row per address one hop out: what moved, in how many transactions, the first proof, and the weakest level read."""
    rows = defaultdict(lambda: dict(usd=0.0, txs=set(), levels=set(), tokens=defaultdict(float), first=None, proof=None, name=None, cls=None, via=set()))
    for e in result['edges']:
        if e['direction'] != direction or e['role'] not in ROLES[direction] or e.get('depth') != 0 or (e.get('usd_rank') or 0) < MIN_USD:
            continue
        if e.get('note') == 'SELF_SWAP':  # the wallet's own dollars: its own history names who paid them in
            continue
        address, chain, via = far_side(e)
        r = rows[(address, chain)]
        r['usd'] += e['usd_rank']
        r['txs'].add(e['transaction_hash'])
        r['levels'].add(e.get('level') or 'UNKNOWN')
        r['tokens'][e.get('token')] += state.value(e)
        if via:
            r['via'].add(via)
        else:
            r['name'], r['cls'] = r['name'] or e.get('service'), r['cls'] or e.get('other_cls')
        if r['first'] is None or (e['timestamp'] or 0) < r['first']:
            r['first'], r['proof'] = e['timestamp'], e['transaction_hash']
    out = [dict(address=k[0], chain=k[1], usd=round(v['usd'], 2), txs=len(v['txs']), levels=sorted(v['levels']), tokens={t: round(a, 6) for t, a in v['tokens'].items()}, first=v['first'], proof=v['proof'], name=v['name'], cls=v['cls'], via=sorted(v['via'])) for k, v in rows.items()]
    return sorted(out, key=lambda x: -x['usd'])


def frontiers(result, direction):
    """Named services, verified contracts and measured hubs where this direction's branches stopped, largest first. A stop that is not a frontier for state.py stays out."""
    rows = defaultdict(lambda: dict(usd=0.0, branches=0, proof=None, category=None))
    for s in result['stops']:
        if s['direction'] != direction or state.sort_stop(s)[0] != 'frontier':
            continue
        r = rows[s.get('name') or 'Measured hub, unnamed']
        r['usd'] += s.get('usd_rank') or 0
        r['branches'] += 1
        r['category'] = r['category'] or s.get('category')
        r['proof'] = r['proof'] or s.get('tx')
    return sorted(({'name': k, 'usd': round(v['usd'], 2), 'branches': v['branches'], 'category': v['category'], 'proof': v['proof']} for k, v in rows.items()), key=lambda x: -x['usd'])


def sheet(result, rows):
    s = state.file_state(result, rows)
    return dict(case=result['case'], wallet=result['wallet'], group=result.get('group'), trace=s['processing'], books=s['accounting'], chain=s['chain'], work_left=s['work_left'], blocked_by=s['blocked_by'], payers=counterparties(result, 'funding'), destinations=counterparties(result, 'cashout'), funding_frontiers=frontiers(result, 'funding'), exit_frontiers=frontiers(result, 'cashout'), untraced_deposit_usd=s['funding']['untraced_row_usd'], untraced_withdrawal_usd=s['exits']['untraced_row_usd'])


def day(t):
    return time.strftime('%Y-%m-%d %H:%M', time.gmtime(t)) if t else ''


def cell(c):
    tag = c['name'] or c['cls'] or 'read through a bridge'
    tokens = ', '.join(f'{a:,.2f} {t}' for t, a in c['tokens'].items())
    return f"| `{c['address']}` | {c['chain']} | {tag} | {tokens} | {c['usd']:,.2f} | {c['txs']} | {day(c['first'])} | `{c['proof']}` | {', '.join(c['levels'])} | {', '.join(c['via']) or 'direct'} |"


def write_sheet(lines, x):
    chain = x['chain'] or {}
    money = f"deposits {chain.get('deposits', 0):,.2f}, withdrawals {chain.get('withdrawals', 0):,.2f}, residual {chain.get('residual')}"
    lines += ['', f"### {x['case']}", '', f"`{x['wallet']}`. Trace **{x['trace']}**, books **{x['books']}**: {money}. Deposit rows with no path: {x['untraced_deposit_usd']:,.2f} USD. Withdrawal rows with no path: {x['untraced_withdrawal_usd']:,.2f} USD.", '', f"Still open: {json.dumps(x['work_left']) if x['work_left'] else 'nothing'}. Blocked by data: {json.dumps(x['blocked_by']) if x['blocked_by'] else 'nothing'}."]
    for title, rows in (('Who paid in', x['payers']), ('Where it went', x['destinations'])):
        lines += ['', f'{title}, one hop out:', '']
        if rows:
            lines += ['| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |', '|---|---:|---|---|---:|---:|---|---|---|---|'] + [cell(c) for c in rows[:12]]
            if len(rows) > 12:
                lines.append(f'\n{len(rows) - 12} smaller addresses are in the JSON.')
        else:
            lines.append('None read at this hop.')
    for title, rows in (('Funding branches stopped at', x['funding_frontiers']), ('Exit branches stopped at', x['exit_frontiers'])):
        if rows:
            lines += ['', f'{title}: ' + '; '.join(f"{f['name']} ({f['branches']} branches, {f['usd']:,.2f} USD)" for f in rows[:10]) + '.']


def main(results):
    results = Path(results)
    root = env.data_root() / 'wallets'
    sheets, lines = [], ['# Who paid each account, and where its money went', '', 'Written by `engine/tools/money_report.py` from `wallets/*/trace.json`. An address is not a person, and money between two addresses does not show a common owner. Ownership is not established for any address here. No finding of wrongdoing.', '', 'A payer or destination is one hop from the account or its keys. A branch further out shows flows through an address, and tokens are fungible, so they are not shown to be the same units. ' + ROUGH, '', 'Levels: `ONCHAIN_CONFIRMED` is a log read in a receipt. `LISTED` is an explorer row not yet confirmed by a receipt. A bridge hop is shown with its own proof in the file.']
    for name, listing in GROUPS:
        lines += ['', f'## {name}']
        for entry in json.loads((results / listing).read_text()):
            path = root / entry['slug'] / 'trace.json'
            activity = path.with_name('activity.json')
            if not path.exists() or not activity.exists():
                lines += ['', f"### {entry['slug']}", '', 'No file yet.']
                continue
            x = dict(sheet(json.loads(path.read_text()), json.loads(activity.read_text())), group=name)
            sheets.append(x)
            write_sheet(lines, x)
    (results / 'FUNDERS_AND_EXITS.md').write_text('\n'.join(lines) + '\n')
    (results / 'FUNDERS_AND_EXITS.json').write_text(json.dumps(sheets, indent=0))
    print('sheets', len(sheets), flush=True)


if __name__ == '__main__':
    main(sys.argv[1])
