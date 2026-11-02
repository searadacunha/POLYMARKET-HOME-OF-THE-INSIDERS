"""Wallet, market, network and global reports, written from the data only. Addresses and hashes are copied by this script, never typed. No report says insider."""
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gf import env, ledger_pnl
from gf.events import CHAIN_NAME

ROOT = env.data_root()
DAY = lambda t: datetime.fromtimestamp(int(t), timezone.utc).strftime('%Y-%m-%d %H:%M:%S') if t else 'unknown'
ALTERNATIVES = ['Money between two addresses says nothing of who holds them: a payment, a gift, a loan, a service or a resale give the same picture.', 'A service or an exchange pays thousands of people. A shared one proves no link.', 'An early, large or lucky bet can follow public signals, private analysis or chance.', 'Access to private information is not something on-chain data can show.']


def amount(e):
    return int(e['raw_amount']) / 10 ** int(e['decimals'] or 0)


def line(e):
    chain = CHAIN_NAME.get(e['chain_id'], e['chain_id'])
    who = e.get('service') or e.get('other_cls') or ''
    return f"| {DAY(e['timestamp'])} | {chain} | {e.get('role')} | {amount(e):,.6f} {e.get('token')} | `{e['from']}` | `{e['to']}` | {who} | {e.get('level')} / {e.get('data_class')} | `{e['transaction_hash']}` | {e.get('log_index') if e.get('log_index') is not None else ''} |"


def paths(result, direction, limit=40):
    """Branches, not one chosen funder. Each ends where the data says it ends."""
    edges = [e for e in result['edges'] if e['direction'] == direction]
    key_a, key_b = ('to', 'from') if direction == 'funding' else ('from', 'to')
    by = defaultdict(list)
    for e in edges:
        by[e[key_a]].append(e)
    stop = {}
    for s in result['stops']:
        if s['direction'] == direction:
            stop.setdefault(s['address'], s['reason'])
    out = []

    def walk(address, trail, seen):
        if len(out) >= limit:
            return
        steps = [e for e in by.get(address, []) if e[key_b] not in seen]
        if not steps:
            if trail:
                out.append((trail, stop.get(address, 'no further flow read')))
            return
        for e in sorted(steps, key=lambda x: -x.get('usd_rank', 0))[:12]:
            walk(e[key_b], trail + [e], seen | {e[key_b]})
    for start in sorted({result['wallet']} | set(result['own'])):
        walk(start, [], {start})
    return out


def wallet_report(result, rows, out_dir):
    a = result.get('account') or {}
    books = ledger_pnl.account(rows)
    wallet = result['wallet']
    lines = [f"# Account file: `{wallet}`", '', f"Group `{result.get('group')}`. Read {DAY(result.get('collected_at'))} UTC. Mode: {result.get('mode', 'full')}. An address is not a person. Ownership not established. This file is no finding of wrongdoing.", '', '## Activity', '']
    lines += [f"- API history complete: {a.get('history_complete')}, {a.get('rows')} rows, types {json.dumps(a.get('types'))}", f"- First activity {DAY(a.get('first_activity'))}, last {DAY(a.get('last_activity'))}", f"- First trade: {DAY((a.get('first_trade') or {}).get('timestamp'))} {(a.get('first_trade') or {}).get('title')}", f"- Deposits and withdrawals listed {a.get('money_listed')}, not read here {a.get('money_dropped', 0)}, unreadable {len(a.get('unread') or [])}"]
    lines += ['', '## Control', '']
    for tag in ('control_latest', 'control_at_first_money'):
        c = a.get(tag) or {}
        lines.append(f"- {tag}: form {c.get('form')}, owners {c.get('owners')}, {c.get('signer_status')}, read at block {c.get('block')}")
    lines.append('- A relayer submitting a transaction is not its owner, and an owner key is not a person.')
    lines += ['', '## Funding paths, branch by branch', '', 'Tokens are fungible: a path shows flows in sequence, never the same units.', '']
    for trail, why in paths(result, 'funding'):
        lines.append('- ' + ' <- '.join(f"`{(e['from'] if e['direction'] == 'funding' else e['to'])[:12]}…` ({amount(e):,.2f} {e.get('token')}, {e.get('role')})" for e in trail) + f" **stops: {why}**")
    lines += ['', '## Exit paths', '']
    for trail, why in paths(result, 'cashout'):
        lines.append('- ' + ' -> '.join(f"`{e['to'][:12]}…` ({amount(e):,.2f} {e.get('token')}, {e.get('role')})" for e in trail) + f" **stops: {why}**")
    lines += ['', '## Markets and positions', '', '| Market | Trades | First | Capital engaged | Cash result | Shares left, API |', '|---|---:|---|---:|---:|---:|']
    for m in books['markets'][:60]:
        lines.append(f"| {m['title']} | {m['trades']} | {DAY(m['first'])} | {Decimal(m['capital_engaged']):,.2f} | {Decimal(m['cash_result']):,.2f} | {Decimal(m['shares_left_by_api']):,.2f} |")
    lines += ['', '## Accounting', '', f"- Cash by type: {json.dumps(books['wallet'])}", f"- Unknown types: {json.dumps(books['unknown_types'])}", f"- Trading cash over the rows read: {Decimal(books['trading_cash']):,.2f}. Balance computed from the rows: {Decimal(books['computed_balance']):,.2f}.", f"- Held today: {json.dumps(a.get('balances_now'))}", '- Withdrawals minus deposits is not a profit. An unredeemed position counts for nothing in cash.']
    hold = a.get('balances_now') or {}
    if a.get('history_complete') and hold.get('pUSD') is not None:
        held = sum(hold.get(k) or 0 for k in ('pUSD', 'USDC.e', 'USDC'))
        lines.append(f"- Unexplained residual, collateral held minus computed balance: {held - float(books['computed_balance']):,.6f}. Shown, not absorbed.")
    lines += ['', '## Coverage', '', '| Address | Chain | Status | Rows | Source |', '|---|---|---|---:|---|']
    for n in result['nodes'][:80]:
        lines.append(f"| `{n['node']}` | {CHAIN_NAME.get(n['chain'], n['chain'])} | {n.get('status')} | {n.get('rows', '')} | {n.get('source')} |")
    lines += ['', '## Where reading stopped', '']
    for reason, count in Counter(s['reason'] for s in result['stops']).most_common():
        lines.append(f"- {reason}: {count}")
    lines.append(f"- Token rows outside the value list, not followed: {result.get('ignored_token_rows')} rows on {result.get('ignored_token_contracts')} contracts")
    lines += ['', '## Moves with their proof', '', '| UTC | Chain | Role | Amount | From | To | Other side | Level / data | Transaction | Log |', '|---|---|---|---:|---|---|---|---|---|---:|']
    lines += [line(e) for e in sorted(result['edges'], key=lambda x: x['timestamp'] or 0)[:300]]
    lines += ['', '## Other explanations', ''] + [f'- {x}' for x in ALTERNATIVES]
    (out_dir / f"{result['case']}.md").write_text('\n'.join(lines) + '\n')
    return dict(case=result['case'], wallet=wallet, group=result.get('group'), mode=result.get('mode', 'full'), rows=a.get('rows'), history_complete=a.get('history_complete'), first_activity=a.get('first_activity'), edges=len(result['edges']), stops=len(result['stops']), deposits=books['wallet'].get('deposit'), withdrawals=books['wallet'].get('withdrawal'), cash_by_markets=str(sum(Decimal(m['cash_result']) for m in books['markets'])), capital=str(sum(Decimal(m['capital_engaged']) for m in books['markets'])), markets=len(books['markets']))


def main(out):
    out = Path(out)
    (out / 'wallets').mkdir(parents=True, exist_ok=True)
    index = []
    for path in sorted((ROOT / 'wallets').glob('*/trace.json')):
        result = json.loads(path.read_text())
        rows = json.loads(path.with_name('activity.json').read_text())
        index.append(wallet_report(result, rows, out / 'wallets'))
    (out / 'wallets_index.json').write_text(json.dumps(index, indent=0))
    print('wallet files', len(index), Counter(i['group'] for i in index))


if __name__ == '__main__':
    main(sys.argv[1])
