"""Every row, in and out, of one source on one chain inside a block range, in compact gz files. Walks by block, never by page. Measured on 02/11: the free plan returns 1000 rows per call whatever `offset` says, so anything at or above PAGE is treated as cut, and a full page may split a block, so the last block is dropped and re-read. A failed read raises, the checkpoint keeps what is done.
Usage: outflows.py <chain> <address> <start_block> <end_block>
Writes state/out_full/<chain>_<address>_<action>.csv.gz, one row per transfer, and state/out_full/<chain>_<address>.json with pages, rows and completeness per action."""
import csv, gzip, json, os, resource, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import es, net
OUT = net.ROOT / 'state/out_full'  # state/out holds an early truncated read, never used
RSS_CAP = 700 * 1024 * 1024
FIELDS = dict(txlist=['blockNumber', 'timeStamp', 'hash', 'from', 'to', 'value', 'isError', 'contractAddress', 'input4'],
              tokentx=['blockNumber', 'timeStamp', 'hash', 'from', 'to', 'value', 'contractAddress', 'tokenSymbol', 'tokenDecimal', 'nonce'],
              txlistinternal=['blockNumber', 'timeStamp', 'hash', 'from', 'to', 'value', 'isError', 'traceId', 'type'])
PAGE = 1000


def walk(chain, addr, action, start, end):
    """Append-only: a resumed run starts after the last block fully written."""
    path = OUT / f'{chain}_{addr}_{action}.csv.gz'
    ck = OUT / f'{chain}_{addr}_{action}.ck.json'
    state = json.loads(ck.read_text()) if ck.exists() else dict(next=start, rows=0, pages=0, done=False, end=end)
    if state['done'] and state['end'] >= end:
        return state
    state.update(done=False, end=end)
    while True:
        batch = es.rows(action, addr, chain, state['next'], end, 1, PAGE, 'asc', store=False)
        full = len(batch) >= PAGE
        after = None
        if full:
            last = int(batch[-1]['blockNumber'])
            if last == state['next']:  # one block fills a page (seen: 1 211 rows, a mass dust sweep): read its pages, then step over it
                page = 2
                while True:
                    more = es.rows(action, addr, chain, last, last, page, PAGE, 'asc', store=False)
                    batch += more
                    if len(more) < PAGE:
                        break
                    page += 1
                after = last + 1
            else:
                batch = [r for r in batch if int(r['blockNumber']) < last]
        keep = batch  # both directions: senders into a hub are how its deposit addresses are told from clients
        with gzip.open(path, 'at', newline='') as f:
            w = csv.writer(f)
            for r in keep:
                r['input4'] = (r.get('input') or r.get('methodId') or '')[:10]
                w.writerow([r.get(k, '') for k in FIELDS[action]])
        state['rows'] += len(keep)
        state['pages'] += 1
        state['next'] = after or (last if full else end + 1)
        state['done'] = not full
        tmp = ck.with_suffix('.tmp')
        tmp.write_text(json.dumps(state))
        os.replace(tmp, ck)
        print(chain, addr[:10], action, 'page', state['pages'], 'rows', state['rows'], 'next', state['next'], flush=True)
        if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss > RSS_CAP:
            raise SystemExit('rss cap, stop: nothing lost, rerun')
        if state['done']:
            return state


if __name__ == '__main__':
    chain, addr, start, end = int(sys.argv[1]), sys.argv[2].lower(), int(sys.argv[3]), int(sys.argv[4])
    OUT.mkdir(parents=True, exist_ok=True)
    res = {a: walk(chain, addr, a, start, end) for a in ('txlist', 'tokentx', 'txlistinternal')}
    (OUT / f'{chain}_{addr}.json').write_text(json.dumps(res))
