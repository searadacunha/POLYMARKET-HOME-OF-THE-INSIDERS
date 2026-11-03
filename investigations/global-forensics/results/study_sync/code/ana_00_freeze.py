"""Builds the analytic table once from the archive. Streams market by market, one in memory. No rate is computed here, and `win` is only copied. Stops on any unreadable file."""
import gzip
import hashlib
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib_bursts as lib

ETUDE = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ARCHIVE = Path(os.environ.get('P8_DIR', Path.home() / 'Documents/Crypto/enquete_maduro_iran/donnees/brut_p8_p9/p8'))
DERIVED = ETUDE / 'derived'
SPLITS = (('TRAIN', '2026-03-01'), ('VALID', '2026-06-01'), ('TEST', '9999'))
PAGE = 500


def split_of(end):
    for name, before in SPLITS:
        if end[:10] < before:
            return name
    raise ValueError(end)


def parse(row, seq):
    return dict(wallet=row['proxyWallet'].lower(), side=row['side'], token=str(row['asset']), size=float(row['size']), price=float(row['price']), ts=int(row['timestamp']), seq=seq)


def rows_of(body):
    # the files run from newest to oldest, so a negative index keeps the true order inside one second
    return [parse(r, -i) for i, r in enumerate(body['rows'])]


def seconds(text):
    return int(datetime.fromisoformat(text.replace(' ', 'T').replace('+00', '+00:00').replace('Z', '+00:00')).timestamp())


def main():
    universe = json.loads((ARCHIVE / 'universe.json').read_text())
    events = json.loads((DERIVED / 'events.json').read_text())['events']
    counts, hashes, first_seen, markets, oldest_gap = Counter(), {}, {}, [], []
    for m in universe:
        counts['markets_universe'] += 1
        tokens, prices = json.loads(m['clobTokenIds']), json.loads(m['outcomePrices'])
        if sorted(float(p) for p in prices) != [0.0, 1.0]:
            counts['excluded_not_resolved_1_0'] += 1
            continue
        path = ARCHIVE / 'trades' / f"{m['conditionId']}.json"
        if not path.exists():
            counts['excluded_no_trade_file'] += 1
            continue
        raw = path.read_bytes()
        hashes[m['conditionId']] = hashlib.sha256(raw).hexdigest()
        body = json.loads(raw)
        closed = seconds(m.get('closedTime') or m['endDate'])
        rows = rows_of(body)
        for r in rows:
            if r['ts'] <= closed:
                first_seen[r['wallet']] = min(first_seen.get(r['wallet'], r['ts']), r['ts'])
        event = events.get(m['conditionId'])
        counts['group_event' if event else 'group_fallback_market_slug'] += 1
        flagged = bool(body.get('maybe_truncated'))
        suspect = not flagged and bool(rows) and len(rows) % PAGE == 0
        counts['files_flagged_truncated'] += flagged
        counts['files_suspect_partial_page_multiple'] += suspect
        if rows and m.get('startDate'):
            oldest_gap.append((min(r['ts'] for r in rows) - seconds(m['startDate'])) / 86400)
        markets.append(dict(condition=m['conditionId'], tokens=tokens, win={t: int(float(p) == 1.0) for t, p in zip(tokens, prices)}, end=m['endDate'], group=event['event_slug'] if event else m['slug'], volume=float(m['volumeNum']), closed=closed, partial=flagged or suspect))
    counts['wallets_first_seen'] = len(first_seen)
    with gzip.open(DERIVED / 'table.jsonl.gz', 'wt') as table, gzip.open(DERIVED / 'tokens.jsonl.gz', 'wt') as all_tokens:
        for m in markets:
            with (ARCHIVE / 'trades' / f"{m['condition']}.json").open() as f:
                rows = rows_of(json.load(f))
            counts['markets_read'] += 1
            counts['rows_read'] += len(rows)
            kept = [r for r in rows if r['ts'] <= m['closed']]
            counts['rows_after_close_dropped'] += len(rows) - len(kept)
            entries, history = lib.entrants(kept, first_seen, counts)
            counts['entrants'] += len(entries)
            split = split_of(m['end'])
            by_token = defaultdict(list)
            for e in entries:
                by_token[e['token']].append(e)
            for token in m['tokens']:
                all_tokens.write(json.dumps(dict(condition=m['condition'], token=token, group=m['group'], split=split, win=m['win'][token], partial=int(m['partial']), volume=m['volume'], closed=m['closed'], entrants=len(by_token.get(token, [])))) + '\n')
                counts['tokens_universe'] += 1
            for token, items in by_token.items():
                if token not in m['win']:
                    counts['tokens_unknown_dropped'] += 1
                    continue
                counts['tokens_with_entrants'] += 1
                items = sorted(items, key=lambda x: x['ts'])
                in_burst = {w: lib.bursts(items, w, history[token]) for w in lib.WINDOWS}
                common = dict(condition=m['condition'], token=token, group=m['group'], split=split, win=m['win'][token], partial=int(m['partial']), volume=m['volume'], closed=m['closed'])
                for w, (found, _) in in_burst.items():
                    counts[f'bursts_{w}'] += len(found)
                    for e in found:
                        table.write(json.dumps(dict(common, kind='burst', window=w, ts=e['ts'], start=e['start'], wallets=e['wallets'], usd=round(e['usd'], 2), vwap=round(e['vwap'], 6), cv=round(e['cv'], 4), fresh_share=round(e['fresh_share'], 4), shock=e['shock'])) + '\n')
                for i, e in enumerate(items):
                    table.write(json.dumps(dict(common, kind='entrant', ts=e['ts'], price=round(e['price'], 6), usd=round(e['usd'], 2), fresh=e['fresh'], burst_windows=[w for w, (_, members) in in_burst.items() if i in members])) + '\n')
    oldest_gap.sort()
    counts_out = dict(counts)
    counts_out['oldest_row_minus_market_start_days'] = dict(median=oldest_gap[len(oldest_gap) // 2], p90=oldest_gap[int(.9 * len(oldest_gap))], over_2_days=sum(g > 2 for g in oldest_gap), n=len(oldest_gap)) if oldest_gap else None
    (DERIVED / 'input_hashes.json').write_text(json.dumps(dict(universe=hashlib.sha256((ARCHIVE / 'universe.json').read_bytes()).hexdigest(), trades=hashes), indent=0))
    (DERIVED / 'freeze_counts.json').write_text(json.dumps(counts_out, indent=1, sort_keys=True))
    print(json.dumps(counts_out, indent=1, sort_keys=True))


if __name__ == '__main__':
    main()
