"""FUNDING_FLOWS.csv, WALLETS.csv, graph.html and funding_network.graphml, from the walks and the direct flows. Every row keeps tx hash, chain, block, raw amount, decimals, label and its source."""
import csv
import glob
import html
import json
import sys
import time
from collections import defaultdict
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).parent))
import labels
import net

ROOT = net.ROOT
EXPLORER = {'1': 'https://etherscan.io/tx/', '137': 'https://polygonscan.com/tx/', '42161': 'https://arbiscan.io/tx/', '10': 'https://optimistic.etherscan.io/tx/', '8453': 'https://basescan.org/tx/', '56': 'https://bscscan.com/tx/', 'solana': 'https://solscan.io/tx/', 'bitcoin': 'https://mempool.space/tx/'}
ADDR = {'1': 'https://etherscan.io/address/', '137': 'https://polygonscan.com/address/', '42161': 'https://arbiscan.io/address/', '10': 'https://optimistic.etherscan.io/address/', 'solana': 'https://solscan.io/account/', 'bitcoin': 'https://mempool.space/address/'}
FIELDS = ['account_wallet', 'account_labels', 'direction', 'hop', 'chain', 'tx_hash', 'block_or_slot', 'utc', 'src', 'dst', 'asset', 'token_contract', 'decimals', 'raw_amount', 'amount', 'usd_approx', 'kind', 'fee_native', 'tx_sender', 'src_service', 'dst_service', 'label_sources', 'evidence_level', 'confidence', 'alternatives', 'explorer_url']


def utc(ts):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(ts)) if ts else ''


def service(a, chain):
    if not a or '_inputs' in str(a):
        return None
    lab = labels.lookup(a, chain if str(chain).isdigit() else None)
    return lab


def main():
    rows = []
    nodes = {}
    relay_flow = json.load(open(ROOT / 'derived/relay.json'))
    for f in sorted(glob.glob(str(ROOT / 'derived/walk/*.json'))):
        w = json.load(open(f))
        tag = ' '.join(w['labels'])
        for n in w['nodes']:
            key = n['address']
            prev = nodes.get(key)
            if not prev or n['hop'] < prev['hop']:
                nodes[key] = dict(address=key, cls=n['cls'], reason=n.get('reason', ''), label=(n.get('label') or {}).get('name') if n.get('label') else None, hop=n['hop'], first_ts=n.get('first_ts'), last_ts=n.get('last_ts'), accounts=set((prev or {}).get('accounts', ())), n_in=n.get('n_in'), n_out=n.get('n_out'), contract=n.get('contract'), spam_rows=n.get('spam_rows'))
            nodes[key]['accounts'].add(w['wallet'])
        nodes.setdefault(w['wallet'], dict(address=w['wallet'], cls='POLYMARKET_WALLET', reason='', label=None, hop=-1, first_ts=None, last_ts=None, accounts=set(), n_in=None, n_out=None, contract=True, spam_rows=None))['accounts'].add(w['wallet'])
        for e in w['edges']:
            s, d = service(e['src'], e['chain']), service(e['dst'], e['chain'])
            srcs = [x['source'] + ':' + x['text'] for lab in (s, d) if lab for x in lab['sources'][:3]]
            conf = 'lecture directe de la chaine' if not (s or d) else 'flux sur la chaine, service selon etiquette ' + '+'.join(sorted(set(x for lab in (s, d) if lab for x in labels.lineages(lab['sources']))))
            alt = 'etiquette a source unique: possible erreur ou reattribution' if (s or d) and len(set(x for lab in (s, d) if lab for x in labels.lineages(lab['sources']))) < 2 else ''
            rows.append(dict(account_wallet=w['wallet'], account_labels=tag, direction=e['direction'], hop=e['hop'], chain=e['chain'], tx_hash=e['tx'], block_or_slot=e['block'], utc=utc(e['ts']), src=e['src'], dst=e['dst'], asset=e['asset'], token_contract=e.get('contract', ''), decimals=e['decimals'], raw_amount=e['raw'], amount=e['amount'], usd_approx=round(e['usd_approx'], 2) if e.get('usd_approx') else '', kind=e['kind'], fee_native=e.get('fee_native', ''), tx_sender=e.get('tx_from', ''), src_service=s['name'] if s else '', dst_service=d['name'] if d else '', label_sources=' | '.join(srcs)[:300], evidence_level='CHAINE' if not (s or d) else 'CHAINE+ATTRIBUTION', confidence=conf, alternatives=alt, explorer_url=EXPLORER.get(str(e['chain']), '') + e['tx']))
        for fl in w['direct_flows']:
            kind = 'polymarket_deposit' if fl['type'] == 'DEPOSIT' else 'polymarket_withdrawal'
            for p in (fl['relay'] or [None]):
                far = None
                if p:
                    far = (p['user'] or p['sender']) if fl['type'] == 'DEPOSIT' else (p['recipient'] or p['meta_recipient'])
                src, dst = ((far or fl['first_sender']), w['wallet']) if fl['type'] == 'DEPOSIT' else (w['wallet'], (far or fl['last_receiver']))
                rows.append(dict(account_wallet=w['wallet'], account_labels=tag, direction='upstream' if fl['type'] == 'DEPOSIT' else 'downstream', hop=0, chain='137', tx_hash=fl['tx'], block_or_slot='', utc=utc(fl['ts']), src=src, dst=dst, asset='pUSD', token_contract='0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb', decimals=6, raw_amount=int(round(fl['usdc'] * 1e6)), amount=fl['usdc'], usd_approx=round(fl['usdc'], 2), kind=kind + ('_relay' if p else '_direct'), fee_native='', tx_sender='', src_service='', dst_service='', label_sources=('relay requests/v2 id ' + str(p.get('id'))) if p else 'recu Polygon', evidence_level='PROTOCOLE' if p else 'CHAINE', confidence='enregistrement Relay, chaines d origine et d arrivee: ' + str([t['chain'] for t in p['in_txs']]) + ' -> ' + str([t['chain'] for t in p['out_txs']]) if p else 'lecture directe du recu', alternatives='', explorer_url=EXPLORER['137'] + fl['tx']))
    rows.sort(key=lambda r: (r['account_wallet'], r['utc']))
    with open(ROOT / 'FUNDING_FLOWS.csv', 'w', newline='') as f:
        wr = csv.DictWriter(f, fieldnames=FIELDS)
        wr.writeheader()
        wr.writerows(rows)
    with open(ROOT / 'WALLETS.csv', 'w', newline='') as f:
        wr = csv.DictWriter(f, fieldnames=['address', 'chain_family', 'classification', 'stop_reason', 'label', 'min_hop', 'first_activity_utc', 'last_activity_utc', 'n_in', 'n_out', 'unrecognized_token_rows', 'accounts'])
        wr.writeheader()
        for a, n in sorted(nodes.items(), key=lambda x: (x[1]['hop'], x[0])):
            fam = 'evm' if a.startswith('0x') else ('bitcoin' if a.startswith('bc1') or (a[0] in '13' and len(a) <= 35) else 'solana')
            wr.writerow(dict(address=a, chain_family=fam, classification=n['cls'], stop_reason=n['reason'], label=n['label'] or '', min_hop=n['hop'], first_activity_utc=utc(n['first_ts']), last_activity_utc=utc(n['last_ts']), n_in=n['n_in'], n_out=n['n_out'], unrecognized_token_rows=n['spam_rows'], accounts=' '.join(sorted(x[:10] for x in n['accounts']))))
    # graph: edges merged per (src, dst), each keeps every tx
    merged = defaultdict(lambda: dict(usd=0.0, txs=[]))
    for r in rows:
        m = merged[(r['src'], r['dst'])]
        m['usd'] += float(r['usd_approx'] or 0)
        if len(m['txs']) < 40:
            m['txs'].append(dict(h=r['tx_hash'][:14], u=r['explorer_url'], t=r['utc'][:16], a=r['asset'], v=round(float(r['amount']), 4), k=r['evidence_level']))
    gnodes = {}
    for (s, d) in merged:
        for a in (s, d):
            if a and a not in gnodes:
                lab = service(a, None)
                n = nodes.get(a)
                gnodes[a] = dict(id=a, label=(lab['name'] if lab else '')[:34], cat=(lab['category'] if lab else ''), cls=(n['cls'] if n else 'NON_LU'), accs=sorted(x[:10] for x in (n['accounts'] if n else ())), url=('https://mempool.space/address/' if a.startswith('bc1') else ('https://polygonscan.com/address/' if a.startswith('0x') else 'https://solscan.io/account/')) + a)
    wallets = {f[-47:-5] for f in glob.glob(str(ROOT / 'derived/walk/*.json'))}
    for a in wallets:
        if a in gnodes:
            gnodes[a]['cls'] = 'POLYMARKET_WALLET'
    data = dict(nodes=list(gnodes.values()), edges=[dict(s=s, d=d, usd=round(v['usd'], 2), txs=v['txs']) for (s, d), v in merged.items() if s and d])
    tpl = (Path(__file__).parent / 'graph_template.html').read_text()
    (ROOT / 'graph.html').write_text(tpl.replace('/*DATA*/', 'const DATA=' + json.dumps(data, separators=(',', ':')) + ';'))
    with open(ROOT / 'funding_network.graphml', 'w') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<graphml xmlns="http://graphml.graphdrawing.org/xmlns"><key id="c" for="node" attr.name="cls" attr.type="string"/><key id="l" for="node" attr.name="label" attr.type="string"/><key id="u" for="edge" attr.name="usd" attr.type="double"/><key id="x" for="edge" attr.name="txs" attr.type="string"/><graph edgedefault="directed">\n')
        for n in data['nodes']:
            f.write(f'<node id="{escape(n["id"])}"><data key="c">{escape(n["cls"])}</data><data key="l">{escape(n["label"])}</data></node>\n')
        for e in data['edges']:
            f.write(f'<edge source="{escape(e["s"])}" target="{escape(e["d"])}"><data key="u">{e["usd"]}</data><data key="x">{escape(" ".join(t["u"] for t in e["txs"][:6]))}</data></edge>\n')
        f.write('</graph></graphml>\n')
    print('flows', len(rows), 'wallets', len(nodes), 'graph nodes', len(data['nodes']), 'edges', len(data['edges']))


if __name__ == '__main__':
    main()
