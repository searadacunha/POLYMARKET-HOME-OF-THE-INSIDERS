"""Re-read from nodes, today, every reference transaction of the Ballon d'Or and ChangeNOW files. Hashes come from the files, never typed by hand.

Each row: what the earlier report said, what the nodes say now, and whether they agree. Writes one CSV and one JSON next to it.
"""
import csv
import glob
import json
import sys
from decimal import Decimal
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gf import proof
from gf.env import redirect_temp
from gf.events import amount
from gf.net import Net, Refused

HOME = Path.home() / 'Projects'
OUT = Path(sys.argv[1])
PUSD = '0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb'
ZERO = '0x' + '0' * 40


def targets():
    for path in sorted(glob.glob(str(HOME / 'PolySentinel-investigation/cases/*.json'))):
        c = json.load(open(path))
        wallet = c['address'].lower()
        for d in c['deposits']:
            yield dict(group='ballon-dor', case=c['slug'], ref='deposit', chain=137, tx=d['tx'], wallet=wallet, expect_usd=str(d['usd']), expect_to=wallet, src_report=f"PolySentinel-investigation/cases/{c['slug']}.json")
        for w in c['withdrawals']:
            yield dict(group='ballon-dor', case=c['slug'], ref='withdrawal', chain=137, tx=w['tx'], wallet=wallet, expect_usd=str(w['usd']), expect_from=wallet, src_report=f"PolySentinel-investigation/cases/{c['slug']}.json")
    for r in csv.DictReader(open(HOME / 'PolySentinel-ChangeNOW-proof/data/verified_transfers.csv')):
        yield dict(group='changenow', case=r['case'], ref=r['event'], chain=int(r['chain_id']), tx=r['tx'], expect_from=r['src'].lower(), expect_to=r['dst'].lower(), expect_raw=r['raw'], expect_contract=(r['contract'] or '').lower(), expect_log=r['log_index'], src_report='PolySentinel-ChangeNOW-proof/data/verified_transfers.csv')
    for r in csv.DictReader(open(HOME / 'PolySentinel-flow-trace/data/walk_edges.csv')):
        if r['case'] == 'brace227' and r['token'] == 'USDC' and r['dst'] == '0x48ec106cf690edd58fcd6df1e8b6abfc16dab12d':
            yield dict(group='ballon-dor-link', case='brace227', ref='key_to_unnamed_wallet_owner', chain=int(r['chain']), tx=r['tx'], expect_from=r['src'], expect_to=r['dst'], expect_raw=r['raw'], expect_contract=r['contract'], src_report='PolySentinel-flow-trace/data/walk_edges.csv')
    for line in open(HOME / 'PolySentinel-flow-trace/data/followups.csv'):
        pass


def check(t, moves, record):
    tx_ok = record['status'] == 1
    if t['ref'] == 'deposit':
        hits = [m for m in moves if m['contract'] == PUSD and m['to'] == t['wallet'] and m['from'] != t['wallet']]
        got = sum((amount(m) for m in hits), Decimal(0))
        return tx_ok and bool(hits) and abs(got - Decimal(t['expect_usd'])) < Decimal('0.000002'), f'pUSD into wallet {got}', hits
    if t['ref'] == 'withdrawal':
        hits = [m for m in moves if m['contract'] == PUSD and m['from'] == t['wallet'] and m['to'] != t['wallet']]
        got = sum((amount(m) for m in hits), Decimal(0))
        return tx_ok and bool(hits) and abs(got - Decimal(t['expect_usd'])) < Decimal('0.000002'), f'pUSD out of wallet {got}', hits
    wanted = [m for m in moves if m['from'] == t['expect_from'] and m['to'] == t['expect_to'] and str(m['raw_amount']) == t['expect_raw'] and (m.get('contract') or '') == t.get('expect_contract', '')]
    if t.get('expect_log') and wanted:
        wanted = [m for m in wanted if str(m.get('log_index')) == t['expect_log']] or wanted
    return tx_ok and bool(wanted), f'{len(wanted)} exact move(s)', wanted


def main():
    redirect_temp()
    net = Net()
    rows = []
    for t in targets():
        row = dict(t)
        try:
            moves, record = proof.read_tx(net, t['chain'], t['tx'])
            ok, detail, hits = check(t, moves, record)
            row.update(result='AGREES' if ok else 'DIFFERS', detail=detail, level=hits[0]['level'] if hits else None, log_indices=';'.join(str(m.get('log_index')) for m in hits), **{k: record[k] for k in ('block_number', 'block_hash', 'timestamp', 'submitter', 'to', 'selector', 'first_host', 'second_host', 'agree', 'receipt_sha256', 'logs')})
        except Refused as e:
            row.update(result='NOT_READ', detail=str(e)[:200])
        rows.append(row)
        print(row['group'], row['case'], row['ref'], row['tx'][:12], row['result'], row.get('level'), row['detail'][:70], flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    fields = sorted({k for r in rows for k in r})
    with (OUT / 'reference_verification.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    from collections import Counter
    summary = dict(rows=len(rows), by_result=Counter(r['result'] for r in rows), by_level=Counter(str(r.get('level')) for r in rows), by_group={g: Counter(r['result'] for r in rows if r['group'] == g) for g in {r['group'] for r in rows}}, calls=net.calls, hits=net.hits)
    (OUT / 'reference_verification.json').write_text(json.dumps(summary, indent=1, default=dict))
    print(json.dumps(summary, default=dict))


if __name__ == '__main__':
    main()
