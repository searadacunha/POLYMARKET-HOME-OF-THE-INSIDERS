"""Node proof of every cited transfer: transaction, receipt and block read from public RPC, compared with the explorer rows, archived with SHA-256. A mismatch stops the row from entering data/verified_transfers.csv."""
import csv, datetime, gzip, hashlib, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import net
ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / 'evidence/onchain'
DIR.mkdir(parents=True, exist_ok=True)
TRANSFER = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
KEY, BRACE, FUNDER, RELAY, HTX = '0x101b5f4dc0886c32e2b75972101aeaf9f338fb65', '0xc852b0938f5ad79b640d105ed11c14499454af26', '0x3eaef6d5e91ecf7b7623eb19978e145ebd417013', '0x7e67df45e0a0bab092cbb2ff045f8aa8dfab6e23', '0x66d582e5e0670bd99153199f179733c6ee5d19be'
HOT3, DEP, HOT4, WATCH = '0xdd3d72c53ff982ff59853da71158bf1538b3ceee', '0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b', '0xeba88149813bec1cccccfdb0dacefaaa5de94cb1', '0xcc0f311eb2c688f30bc9aadb42781e46899723f7'
want = {}
with gzip.open(ROOT / 'state/study_rows.jsonl.gz', 'rt') as f:
    for l in f:
        r = json.loads(l)
        pair = (r['src'], r['dst'])
        ok = pair in {(HOT3, KEY), (KEY, RELAY), (RELAY, DEP), (HOT3, FUNDER), (HOT4, FUNDER), (FUNDER, BRACE), (BRACE, KEY), (HOT4, WATCH), (KEY, HTX)}
        if ok and r['raw'] not in (None, 'None') and int(r['raw']) > 0 and (r['contract'] in (None, '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48', '0xdac17f958d2ee523a2206206994597c13d831ec7')):
            want[(r['tx'], r['src'], r['dst'], str(r['raw']))] = r
print('cited rows', len(want), flush=True)
out, bad = [], []
blocks = {}
for (tx, src, dst, raw), r in sorted(want.items(), key=lambda kv: str(kv[1]['block'])):
    t = net.rpc('eth_getTransactionByHash', [tx], 1)
    rc = net.rpc('eth_getTransactionReceipt', [tx], 1)
    bn = t['blockNumber']
    if bn not in blocks:
        blocks[bn] = net.rpc('eth_getBlockByNumber', [bn, False], 1)
    ts = int(blocks[bn]['timestamp'], 16)
    proof = dict(tx=t, receipt=rc, block=dict(number=bn, timestamp=ts, hash=blocks[bn]['hash']))
    body = json.dumps(proof, sort_keys=True).encode()
    (DIR / f'{tx}.json').write_bytes(body)
    status = int(rc['status'], 16)
    if r['kind'] == 'erc20':
        logs = [l for l in rc['logs'] if l['address'].lower() == r['contract'] and l['topics'][0] == TRANSFER and '0x' + l['topics'][1][-40:] == src and '0x' + l['topics'][2][-40:] == dst and int(l['data'], 16) == int(raw)]
        good = status == 1 and len(logs) >= 1
        ev = 'erc20_transfer_log'
        log_index = int(logs[0]['logIndex'], 16) if logs else None
    else:
        good = status == 1 and t['from'].lower() == src and (t['to'] or '').lower() == dst and int(t['value'], 16) == int(raw)
        ev = 'native_transaction'
        log_index = None
    row = dict(chain_id=1, tx=tx, block=int(bn, 16), utc=datetime.datetime.fromtimestamp(ts, datetime.UTC).strftime('%Y-%m-%d %H:%M:%S'), event=ev, log_index=log_index, token='ETH' if r['kind'] != 'erc20' else r['token'], contract=r['contract'] or '', decimals=18 if r['kind'] != 'erc20' else int(r['decimals']), raw=raw, amount=f"{int(raw) / 10 ** (18 if r['kind'] != 'erc20' else int(r['decimals'])):.18f}".rstrip('0').rstrip('.'), src=src, dst=dst, node_proof_sha256=hashlib.sha256(body).hexdigest(), node_ok=good)
    (out if good else bad).append(row)
    print(row['utc'], row['token'], row['amount'], src[:10], dst[:10], tx[:12], 'OK' if good else 'MISMATCH', flush=True)
(ROOT / 'state/p12.json').write_text(json.dumps(dict(ok=out, bad=bad), indent=0))
print('ok', len(out), 'bad', len(bad))
