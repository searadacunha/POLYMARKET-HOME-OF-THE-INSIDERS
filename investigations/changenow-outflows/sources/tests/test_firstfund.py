"""FIRST_FUNDED must follow PLAN.md on built histories: fake token never counts, an earlier real entry does, a signed transaction does, a cut read gives E."""
import csv, sys, tempfile
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'tools'))
import es, firstfund as F
A = '0x' + 'a' * 40
OTHER = '0x' + 'b' * 40
REAL, FAKE = '0x' + '1' * 40, '0x' + '2' * 40
F.RECOGNISED = {(1, REAL)}
F.HUB_SET = {'0x' + 'c' * 40}


def tx(ts, frm, to, val='5', h=None):
    return dict(timeStamp=str(ts), hash=h or f'0x{ts:064x}', to=to, value=val, isError='0', **{'from': frm})


def tk(ts, frm, to, contract, h=None):
    return dict(timeStamp=str(ts), hash=h or f'0x{ts + 1:064x}', to=to, value='9', contractAddress=contract, **{'from': frm})


def run(txs=(), toks=(), internals=()):
    es.rows = lambda action, *a, **k: {'txlist': list(txs), 'tokentx': list(toks), 'txlistinternal': list(internals)}[action]
    return F.classify(1, A, 1000, '0xpay')['status']


assert run(txs=[tx(1000, OTHER, A, h='0xpay')]) == 'C_FIRST_FUNDED'
assert run(toks=[tk(10, OTHER, A, FAKE)], txs=[tx(1000, OTHER, A, h='0xpay')]) == 'C_FIRST_FUNDED'  # poison before does not count
assert run(toks=[tk(10, OTHER, A, REAL)]) == 'D_DEJA_ACTIVE'
assert run(txs=[tx(10, OTHER, A)]) == 'D_DEJA_ACTIVE'
assert run(txs=[tx(10, A, OTHER, val='0')]) == 'D_DEJA_ACTIVE'  # signed before
assert run(txs=[tx(1, OTHER, A, val='0')] * 30) == 'E_INCONNU'  # 30 zero-value rows, read cut before the payout
assert run(internals=[dict(timeStamp='10', hash='0xi', to=A, value='5', **{'from': OTHER})]) == 'D_DEJA_ACTIVE'
print('ok')
