"""Blockscout tags and contract code of every recipient of the sources, per chain. Tag answers list only tagged addresses: an address absent from the answer has no tag there, and a failed batch raises. Checkpoints by batch. Writes state/recipient_tags.jsonl, state/recipient_code.csv."""
import csv, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import net, rpcbatch
ROOT = net.ROOT
BASE = 'https://metadata.services.blockscout.com/api/v1/metadata'
addrs = {}
for r in csv.DictReader(open(ROOT / 'state/recipients.csv')):
    addrs.setdefault(int(r['chain']), set()).add(r['recipient'])
print({c: len(v) for c, v in addrs.items()}, flush=True)


def tags():
    path = ROOT / 'state/recipient_tags.jsonl'
    ck = ROOT / 'state/recipient_tags.ck.json'
    done = json.loads(ck.read_text()) if ck.exists() else {}
    with path.open('a') as f:
        for c, s in addrs.items():
            lst = sorted(s)
            i = done.get(str(c), 0)
            while i < len(lst):
                d = net.get(BASE, dict(chainId=c, addresses=','.join(lst[i:i + 200])), pause=.3, store=False, accept=())
                if 'addresses' not in d:
                    raise RuntimeError(f'metadata {c} {i}: {str(d)[:160]}')
                for a, v in d['addresses'].items():
                    f.write(json.dumps(dict(chain=c, address=a.lower(), tags=[dict(slug=t['slug'], name=t['name'], type=t['tagType']) for t in v.get('tags', [])])) + '\n')
                i += 200
                done[str(c)] = i
                ck.write_text(json.dumps(done))
                f.flush()
                if i % 20000 == 0:
                    print('tags', c, i, len(lst), flush=True)


def code():
    path = ROOT / 'state/recipient_code.csv'
    ck = ROOT / 'state/recipient_code.ck.json'
    done = json.loads(ck.read_text()) if ck.exists() else {}
    with path.open('a', newline='') as f:
        w = csv.writer(f)
        for c, s in addrs.items():
            lst = sorted(s)
            i = done.get(str(c), 0)
            while i < len(lst):
                part = lst[i:i + 100]
                res = rpcbatch.call(c, [('eth_getCode', [a, 'latest']) for a in part])
                for a, x in zip(part, res):
                    w.writerow([c, a, 'EOA' if x == '0x' else 'EOA_7702' if x.startswith('0xef0100') else 'CONTRAT'])
                i += 100
                done[str(c)] = i
                ck.write_text(json.dumps(done))
                f.flush()
                if i % 20000 == 0:
                    print('code', c, i, len(lst), flush=True)


for job in sys.argv[1:] or ('tags', 'code'):
    {'tags': tags, 'code': code}[job]()
print('done')
