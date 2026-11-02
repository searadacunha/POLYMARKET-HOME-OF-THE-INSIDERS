"""The collector must never take a cut page for the end of a history: fake Etherscan pages, one block split across a page boundary."""
import csv, gzip, sys, tempfile
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'tools'))
import es, outflows
ADDR = '0x' + 'a' * 40
# rows 500 to 1711 sit in one block, as block 25726012 does for 0x30077396
ALL = [dict(blockNumber=str(100 + (i if i < 500 else 500 if i < 1712 else i)), timeStamp='1', hash=f'0x{i:064x}', to='0x' + 'b' * 40, value='5', isError='0', input='0x') | {'from': ADDR if i % 2 == 0 else '0x' + 'c' * 40} for i in range(3500)]


def fake(action, addr, chain, start, end, page, offset, sort, store=False):
    return [r for r in ALL if start <= int(r['blockNumber']) <= end][(page - 1) * 1000:page * 1000]


with tempfile.TemporaryDirectory() as d:
    outflows.OUT = Path(d)
    es.rows = fake
    st = outflows.walk(1, ADDR, 'txlist', 0, 10 ** 6)
    with gzip.open(Path(d) / f'1_{ADDR}_txlist.csv.gz', 'rt', newline='') as f:
        got = [r[2] for r in csv.reader(f)]
    want = [r['hash'] for r in ALL]
    assert got == want, (len(got), len(want))
    assert st['done'] and st['pages'] > 3
    before = st['rows']
    assert outflows.walk(1, ADDR, 'txlist', 0, 10 ** 6)['rows'] == before  # a resumed run adds nothing
print('ok', len(got), 'rows over', st['pages'], 'pages')
