"""Every Polymarket wallet created by the official factories, with its owner, from Polygon logs. Offline join later: a recipient that owns a wallet needs no per-address API call. Walks by block. Writes state/pm_wallets_<name>.csv.gz and a checkpoint. Etherscan getLogs caps at 1000 rows per page and 10 pages."""
import csv, gzip, json, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import es, net
FACTORIES = dict(deposit=('0x00000000000fb5c9adea0298d729a0cb3823cc07', None), safe=('0xaacfeea03eb1561c4e67d661e40682bd20e3541b', '0x4f51faf6c4561ff95f067657e43439f0f856d97c04d9ec9070a6199ad418e235'))
TOPIC_WD = None
sys.path.insert(0, str(Path(__file__).parent))
from keccak import keccak
TOPIC_WD = '0x' + keccak(b'WalletDeployed(address,address,bytes32,address)').hex()
FACTORIES['deposit'] = (FACTORIES['deposit'][0], TOPIC_WD)


def parse(name, lg):
    t, d = lg['topics'], lg['data'][2:]
    if name == 'deposit':
        return '0x' + t[1][-40:], '0x' + t[2][-40:]  # wallet, owner
    return '0x' + d[24:64], '0x' + d[88:128]  # proxy, owner


def run(name, end):
    factory, topic = FACTORIES[name]
    path, ck = net.ROOT / f'state/pm_wallets_{name}.csv.gz', net.ROOT / f'state/pm_wallets_{name}.ck.json'
    st = json.loads(ck.read_text()) if ck.exists() else dict(next=0, rows=0, done=False)
    while not st['done']:
        rows, full = [], False
        for page in range(1, 11):
            d = net.get(es.URL, dict(chainid=137, module='logs', action='getLogs', address=factory, topic0=topic, fromBlock=st['next'], toBlock=end, page=page, offset=1000), pause=.6, secret=dict(apikey=net._key_from_env()), store=False)
            msg = str(d.get('message'))
            if d.get('status') != '1' and not msg.startswith('No '):
                raise RuntimeError(f'{name}: {msg} {str(d.get("result"))[:120]}')
            batch = d.get('result') if d.get('status') == '1' else []
            rows += batch
            if len(batch) < 1000:
                break
        else:
            full = True
        if full:
            last = int(rows[-1]['blockNumber'], 16)
            rows = [r for r in rows if int(r['blockNumber'], 16) < last]
        with gzip.open(path, 'at', newline='') as f:
            w = csv.writer(f)
            for r in rows:
                wallet, owner = parse(name, r)
                w.writerow([wallet, owner, int(r['blockNumber'], 16), int(r['timeStamp'], 16), r['transactionHash']])
        st['rows'] += len(rows)
        st['next'] = last if full else end + 1
        st['done'] = not full
        tmp = ck.with_suffix('.tmp')
        tmp.write_text(json.dumps(st))
        os.replace(tmp, ck)
        print(name, 'rows', st['rows'], 'next', st['next'], flush=True)
    return st


if __name__ == '__main__':
    win = json.loads((net.ROOT / 'state/window.json').read_text())
    end = win['chains']['137'][1]
    for name in sys.argv[1:] or ('deposit', 'safe'):
        print(run(name, end))
