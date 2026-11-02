"""Accounting, pagination, units, dedup and time matching. No network. Run: python3 tests/test_accounting.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'tools'))
import chainlib as c
import tokens


def row(block, h, frm='0xa', to='0xb', value='1', **kw):
    return dict(blockNumber=str(block), hash=h, **{'from': frm}, to=to, value=value, timeStamp='1779429356', isError='0', **kw)


def test_walk_pages_crosses_page_cap_and_dedups():
    pages = {0: [row(i, f'h{i}') for i in range(1000)], 999: [row(999, 'h999')] + [row(1000 + i, f'k{i}') for i in range(50)]}
    out = c.walk_pages(lambda a, b: pages[a], 'txlist', 0, 99)
    assert len(out) == 1050, len(out)
    assert len({r['hash'] for r in out}) == 1050


def test_full_block_raises_instead_of_losing_rows():
    full = [row(5, f'h{i}') for i in range(1000)]
    try:
        c.walk_pages(lambda a, b: full, 'txlist', 5, 99)
    except RuntimeError:
        return
    raise AssertionError('a block fuller than a page must raise')


def test_token_rows_of_one_tx_stay_distinct():
    a = dict(hash='h', logIndex='1', contractAddress='0xt', value='1', blockNumber='1', timeStamp='1', tokenSymbol='X', tokenDecimal='6', **{'from': '0xa'}, to='0xb')
    b = dict(a, logIndex='2')
    assert c.row_key('tokentx', a) != c.row_key('tokentx', b)
    assert c.row_key('tokentx', a) == c.row_key('tokentx', dict(a))


def test_units():
    e = dict(raw='458671452174', decimals=6)
    assert abs(c.amount(e) - 458671.452174) < 1e-9
    assert abs(c.amount(dict(raw='1246542045768124500000000', decimals=18)) - 1246542.0457681245) < 1e-6


def test_native_edges_drop_failed_and_zero():
    rows = [row(1, 'ok', value='5'), dict(row(2, 'failed', value='5'), isError='1'), row(3, 'zero', value='0')]
    assert [e['tx'] for e in c.native_edges(rows, 137)] == ['ok']


def test_spoof_symbol_is_not_recognized():
    spoof = dict(kind='erc20', token='0xa1a33d444eecde5b866e6ecd65e0d0ab5e9d7105', symbol='PỌL', raw='1000000000000000000000', decimals=18)
    real = dict(kind='erc20', token='0x2791bca1f2de4661ed88a30c99a7a9449aa84174', symbol='USDC.e', raw='5000000', decimals=6)
    assert not tokens.recognized(137, spoof) and not tokens.worth_following(137, spoof)
    assert tokens.recognized(137, real) and tokens.worth_following(137, real)
    assert not tokens.worth_following(137, dict(real, raw='1000'))  # poisoning dust on a real token


def test_retry_variant_cannot_widen_the_window():
    import es
    rows = [row(90, 'before'), row(100, 'first'), row(200, 'last'), row(201, 'after')]
    assert [r['hash'] for r in es.in_range(rows, 100, 200)] == ['first', 'last']


def test_flows_conserve_stolen_amount_on_both_bounds():
    import flows
    edges = [dict(src='a', dst='b', cls='USD', amount=60.0, ts=1), dict(src='a', dst='c', cls='USD', amount=40.0, ts=2), dict(src='b', dst='d', cls='USD', amount=100.0, ts=3), dict(src='x', dst='b', cls='USD', amount=40.0, ts=0)]
    r = flows.propagate(edges, dict(a=dict(USD=100.0)), set())
    for bound in r.values():
        kept = sum(v.get('USD', 0) for v in bound['left'].values())
        assert abs(kept - 100.0) < 1e-9, kept
    assert abs(r['poison']['got']['d']['USD'] - 60.0) < 1e-9  # all stolen units on b leave first
    assert abs(r['haircut']['got']['d']['USD'] - 60.0) < 1e-9  # 100 of b's 100 units leave
    assert r['poison']['got']['c']['USD'] == 40.0


def test_flows_haircut_splits_mixed_node():
    import flows
    edges = [dict(src='x', dst='m', cls='USD', amount=50.0, ts=0), dict(src='a', dst='m', cls='USD', amount=50.0, ts=1), dict(src='m', dst='t', cls='USD', amount=10.0, ts=2)]
    r = flows.propagate(edges, dict(a=dict(USD=50.0)), set())
    assert abs(r['haircut']['got']['t']['USD'] - 5.0) < 1e-9
    assert abs(r['poison']['got']['t']['USD'] - 10.0) < 1e-9


def test_time_match_excludes_the_deposit_instant_and_past_the_horizon():
    import cn_match
    rows = [dict(ts=100, usd=97.0), dict(ts=101, usd=97.0), dict(ts=100 + 3600, usd=97.0), dict(ts=101 + 3600, usd=97.0), dict(ts=500, usd=50.0)]
    hits = cn_match.count(100.0, 100, 1, rows, cn_match.BANDS['main'])
    assert [r['ts'] for r in hits] == [101, 3700]


def test_amount_band_keeps_a_fee_and_refuses_a_payout_above_the_deposit():
    import cn_match
    band = cn_match.BANDS['main']
    assert cn_match.in_band(975.0, 1000.0, band)
    assert not cn_match.in_band(1000.0, 1000.0, band)
    assert not cn_match.in_band(900.0, 1000.0, band)


def test_utc_roundtrip():
    assert c.ts_of(c.utc(1779429356)) == 1779429356


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    for t in tests:
        t()
    print(len(tests), 'tests passed')
