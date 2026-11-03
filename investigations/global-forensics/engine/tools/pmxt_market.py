"""One market's order-book rows from the hourly public archive, by row group, then the book at each large entry of the catalogue. Never downloads a whole file, never uses a book later than the trade it describes.

Usage: pmxt_market.py <market id> <first hour> <last hour> <out dir>. Hours as 2026-02-28T05. A missing hour is reported, never filled. The archive is one third party's capture: its terms were not confirmed, and it is read by range for research.
"""
import gzip
import json
import sys
import time
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pmxt_probe import RangeFile

HOSTS = ('https://r2.pmxt.dev', 'https://r2v2.pmxt.dev')


def hours(first, last):
    at = datetime.strptime(first, '%Y-%m-%dT%H').replace(tzinfo=timezone.utc)
    end = datetime.strptime(last, '%Y-%m-%dT%H').replace(tzinfo=timezone.utc)
    while at <= end:
        yield at.strftime('%Y-%m-%dT%H')
        at += timedelta(hours=1)


def open_hour(hour):
    for host in HOSTS:
        try:
            return RangeFile(f'{host}/polymarket_orderbook_{hour}.parquet')
        except OSError:
            continue
    return None


def read_hour(hour, condition, sink, counts):
    f = open_hour(hour)
    if f is None:
        counts['hours_missing'] += 1
        return dict(hour=hour, status='MISSING')
    p = pq.ParquetFile(f)
    index = p.schema_arrow.names.index('market_id')
    groups = []
    for i in range(p.metadata.num_row_groups):
        stats = p.metadata.row_group(i).column(index).statistics
        if stats is None or not stats.has_min_max or stats.min <= condition <= stats.max:
            groups.append(i)
    rows = 0
    for g in groups:
        table = p.read_row_group(g, columns=['timestamp_received', 'timestamp_created_at', 'market_id', 'update_type', 'data'])
        ids = table.column('market_id').to_pylist()
        keep = [i for i, m in enumerate(ids) if m == condition]
        if keep:
            part = table.take(keep).to_pylist()
            for r in part:
                sink.write(json.dumps(dict(received=r['timestamp_received'].timestamp(), created=r['timestamp_created_at'].timestamp(), kind=r['update_type'], data=json.loads(r['data'])), default=str) + '\n')
            rows += len(part)
        del table
    counts['hours_read'] += 1
    counts['rows'] += rows
    counts['bytes_fetched'] += f.fetched
    return dict(hour=hour, status='READ', rows=rows, row_groups_read=len(groups), row_groups=p.metadata.num_row_groups, bytes_fetched=f.fetched, file_bytes=f.size)


def main():
    market, first, last, out = sys.argv[1:5]
    condition = json.loads(Path(sys.argv[5]).read_text()) if len(sys.argv) > 5 else None
    catalog = {m['id']: m for m in json.loads((Path(__file__).resolve().parents[2] / 'catalog/markets.json').read_text())}
    condition = catalog[market]['condition']
    out = Path(out) / market
    out.mkdir(parents=True, exist_ok=True)
    counts, log = Counter(), []
    with gzip.open(out / 'book_rows.tmp.gz', 'wt') as sink:
        for hour in hours(first, last):
            started = time.time()
            log.append(read_hour(hour, condition, sink, counts))
            print(log[-1], f'{time.time() - started:.0f}s', flush=True)
    (out / 'book_rows.tmp.gz').replace(out / 'book_rows.jsonl.gz')
    (out / 'coverage.json').write_text(json.dumps(dict(market=market, condition=condition, first=first, last=last, hours=log, counts=counts), indent=1, default=dict))
    print(dict(counts))


if __name__ == '__main__':
    main()
