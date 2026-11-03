"""Market and network reports from discovery lists, traces and the graph. Both tokens, winners and losers. Written by script: no address or hash typed. No report says insider."""
import gzip
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gf import env

ROOT = env.data_root()
DAY = lambda t: datetime.fromtimestamp(int(t), timezone.utc).strftime('%Y-%m-%d %H:%M:%S') if t else 'unknown'


def traces():
    out = {}
    for path in (ROOT / 'wallets').glob('*/trace.json'):
        t = json.loads(path.read_text())
        a = t.get('account') or {}
        out[t['wallet']] = dict(case=t['case'], first_activity=a.get('first_activity'), rows=a.get('rows'), complete=a.get('history_complete'), first_deposit=min((d['at'] for d in a.get('deposits') or []), default=None), funders=sorted({p.get('origin') for d in a.get('deposits') or [] for p in d.get('paths') or [] if p.get('origin')}), stops=Counter(s['reason'].split(':')[0] for s in t['stops']), edges=len(t['edges']))
    return out


def market_report(discovery, seen, winners, links_by_wallet, out):
    d = json.loads(discovery.read_text())
    won = winners.get(d['market'], {})
    lines = [f"# Market file: {d['market']}", '', f"{d['question']}", '', f"Public event {d['event_utc']}: {d['event_time_basis']}. Selection: {d['selection']}. Status: {d['status']}.", '', 'This market is in the catalogue because of public reports, which are leads, not ground truth. Nothing here says a wallet knew anything.', '', '## Data covered', '', f"- Taker rows of `/v2/trades` in the window: {d['rows']}. Entrant buyers before the event: {d['entrants']}. Maker fills are not read.", f"- Reading list: {d['chosen_rule']}.", '', '## Largest group of entrants inside each window, by token', '', '| Token | 5 s | 30 s | 90 s | 300 s | 900 s | 3600 s |', '|---|---:|---:|---:|---:|---:|---:|']
    for token, g in d['largest_group_of_entrants_by_window'].items():
        lines.append(f"| `{token[:14]}…` | " + ' | '.join(str(g[str(w)]) for w in (5, 30, 90, 300, 900, 3600)) + ' |')
    lines += ['', 'A group can be a reaction to public news or a bot. Compared with other markets in `study_sync/`, not here.', '', '## Largest entrant buyers, both tokens', '', '| Wallet | Outcome bought | USD | Price | Before event | First activity | Age at entry | Funders read | Shared address with another file |', '|---|---|---:|---:|---:|---|---:|---|---|']
    for e in sorted(d['chosen'], key=lambda x: -x['usd']):
        t = seen.get(e['wallet'])
        age = f"{(e['ts'] - t['first_activity']) / 3600:.1f} h" if t and t['first_activity'] else 'not read'
        funders = ', '.join(f'`{f[:10]}…`' for f in (t['funders'][:3] if t else []))
        shared = ', '.join(f'`{a[:10]}…`' for a in sorted(links_by_wallet.get(e['wallet'], []))[:3])
        lines.append(f"| `{e['wallet']}` | {e.get('outcome')} | {e['usd']:,.0f} | {e['price']:.3f} | {e['seconds_before_event'] / 3600:.1f} h | {DAY(t['first_activity']) if t else 'not read'} | {age} | {funders or ('none' if t else 'not read')} | {shared} |")
    read = sum(1 for e in d['chosen'] if e['wallet'] in seen)
    lines += ['', '## Coverage and limits', '', f"- Of {len(d['chosen'])} chosen buyers, {read} have a trace at this date. Light traces stop at depth 2 and 14 nodes, and they say so in each file.", '- Selected on size and timing, on both tokens, so the list holds losers. It is still conditioned on a suspected market, so a trait seen here is not shown to be rare.', '', '## Reports', ''] + [f'- {u}' for u in d['reports']]
    (out / f"{d['market']}.md").write_text('\n'.join(lines) + '\n')
    return dict(market=d['market'], rows=d['rows'], entrants=d['entrants'], chosen=len(d['chosen']), read=read)


def main(out_root):
    out_root = Path(out_root)
    (out_root / 'markets').mkdir(parents=True, exist_ok=True)
    seen = traces()
    links = json.loads((out_root / 'graphs/shared_addresses.json').read_text()) if (out_root / 'graphs/shared_addresses.json').exists() else []
    case_to_wallet = {v['case']: k for k, v in seen.items()}
    links_by_wallet = defaultdict(set)
    for link in links:
        for case in link['cases']:
            if case in case_to_wallet:
                links_by_wallet[case_to_wallet[case]].add(link['address'])
    index = [market_report(p, seen, {}, links_by_wallet, out_root / 'markets') for p in sorted((out_root / 'discovery').glob('*.json')) if p.name != 'wallets.json']
    groups = defaultdict(set)
    for link in links:
        groups[tuple(link['cases'])].add(link['address'])
    lines = ['# Networks: addresses shared between files', '', 'A shared address means money touched it in both files. Services, hubs and contracts cannot appear here. Common ownership, coordination and access to information are not established by any line of this file.', '', f'{len(links)} shared personal-sized addresses across {len(seen)} files read at this date.', '', '| Files | Address | Class | Evidence |', '|---|---|---|---|']
    for link in links:
        evidence = '; '.join(f"{c}: " + ', '.join(f"`{x['tx'][:14]}…` chain {x['chain']} {x['level']}" for x in rows[:3]) for c, rows in link['evidence'].items())
        lines.append(f"| {', '.join(link['cases'])} | `{link['address']}` | {link['cls']} | {evidence} |")
    lines += ['', '## Arguments against a single operator, each time', '', '- A personal-sized address can be a small service, a friend, or a shared OTC contact.', '- The class comes from a nonce and counterparties at read time. A small service looks personal.', '- Files were selected after the fact, by press or by largest entries in a suspected market.', '- There is no positive control of common ownership in this data.']
    (out_root / 'NETWORKS.md').write_text('\n'.join(lines) + '\n')
    (out_root / 'markets_index.json').write_text(json.dumps(index, indent=0))
    print(index, len(links))


if __name__ == '__main__':
    main(sys.argv[1])
