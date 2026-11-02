"""Turns the walk, the dossiers and the bridge records into the required CSV and GraphML files. No network except second-source checks already cached by verify.py."""
import csv
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).parent))
import evm
import labels
import net
import walk

ROOT = net.ROOT
STATE = ROOT / 'state'
INV = walk.INV
SOLANA = walk.SOLANA
CHAIN_NAME = {**evm.CHAIN, SOLANA: 'solana'}
COLLECTED = '2026-11-02'
COLUMNS = ['path_id', 'case', 'anchor_tx', 'anchor_usd', 'anchor_utc', 'hop', 'chain_id', 'chain', 'asset', 'token_contract', 'decimals', 'raw_amount', 'amount', 'source', 'target', 'tx', 'block', 'utc', 'event', 'source_class', 'target_class', 'service', 'service_category', 'attribution_level', 'attribution_source', 'evidence', 'confidence', 'alternatives', 'timing', 'fifo_allocated', 'primary_source', 'second_source', 'collected']
USD_CLASS = evm.STABLE | {'USDC', 'USDT'}


def utc(at):
    return datetime.fromtimestamp(at, timezone.utc).strftime('%Y-%m-%d %H:%M:%S') if at else ''


def is_evm(a):
    return bool(a) and a.startswith('0x') and len(a) == 42


def norm(a):
    return a.lower() if is_evm(a) else a


def class_of(address, chain):
    if address in (evm.ZERO, None, ''):
        return dict(cls='ZERO_ADDRESS')
    if not is_evm(address):
        return walk.classify_sol(address)
    if chain == SOLANA:  # a hop that crosses from Solana names an EVM address on its far side
        chain = 137
    return walk.classify_evm(norm(address), chain) if chain in net.RPC else dict(cls='UNREAD')


def evidence_level(cls_a, cls_b, event):
    if event.startswith('relay') or event in ('bridge_record',):
        return 'PROTOCOLE'
    for c in (cls_a, cls_b):
        lab = c.get('label') or {}
        if lab and (lab.get('category') not in ('bridge', 'polymarket_contract', 'dex_or_router', None) or str(lab.get('level', '')).startswith(('public_label', 'blockscout'))):
            return 'CHAINE+ATTRIBUTION'
    return 'CHAINE'


def row(path_id, case, anchor, hop, chain, asset, contract, decimals, raw, amount, src, dst, tx, block, at, event, alternatives='', fifo='', primary='', timing=''):
    a, b = class_of(src, chain), class_of(dst, chain)
    named = lambda c: (c.get('label') or c.get('contract_name')) and c.get('cls') != 'PERSONAL_SIZED' and c.get('contract_name') != 'DepositWallet'
    service = a if named(a) else b if named(b) else {}
    lab = service.get('label') or {}
    ev = evidence_level(a, b, event)
    return dict(path_id=path_id, case=case, anchor_tx=anchor['tx'], anchor_usd=round(anchor['usd'], 6), anchor_utc=utc(anchor['at']), hop=hop, chain_id=chain, chain=CHAIN_NAME.get(chain, str(chain)), asset=asset, token_contract=contract or '', decimals=decimals if decimals is not None else '', raw_amount=raw or '', amount=amount if amount is not None else '', source=src, target=dst, tx=tx or '', block=block or '', utc=utc(at), event=event, source_class=a.get('cls'), target_class=b.get('cls'), service=lab.get('name') or service.get('contract_name') or '', service_category=lab.get('category') or '', attribution_level=lab.get('level') or ('measured' if service else ''), attribution_source=lab.get('source') or '', evidence=ev, confidence={'CHAINE': 'haute', 'PROTOCOLE': 'haute', 'CHAINE+ATTRIBUTION': 'moyenne (flux haute, étiquette selon sa source)'}[ev], alternatives=alternatives, timing=timing, fifo_allocated=fifo, primary_source=primary, second_source='', collected=COLLECTED)


def fifo_ledger(flows, address):
    """FIFO by stablecoin dollars for one address on one chain: an accounting convention, never a proof that these exact dollars moved. Swaps and internal returns count as refills."""
    queue, out = [], {}
    for f in sorted(flows, key=lambda f: (f['at'], 0 if f['dst'] == address else 1)):
        if f['token'] not in USD_CLASS:
            continue
        amt = int(f['raw']) / 10 ** int(f['decimals'])
        if f['dst'] == address:
            queue.append([f, amt])
        elif f['src'] == address:
            need, used = amt, []
            while need > 1e-6 and queue:
                head = queue[0]
                take = min(head[1], need)
                used.append((head[0], take))
                head[1] -= take
                need -= take
                if head[1] <= 1e-6:
                    queue.pop(0)
            entry = out.setdefault(f['tx'], dict(used=[], uncovered=0.0))  # a relayed deposit also pays a gas fee in the same transaction
            entry['used'] += used
            entry['uncovered'] += max(need, 0)
    return out


def funding_rows(c, w):
    rows, unresolved = [], []
    rels = c['chain_relations']
    for i, h in enumerate(c['funding_chain']):
        dep = next(d for d in c['deposits'] if d['tx'] == h['deposit_tx'])
        pid = f"{c['slug']}-D{i + 1}"
        r = h.get('relay') or {}
        wallet = c['address'].lower()
        src = h['immediate_source'].lower()
        hop = 0
        rows.append(row(pid, c['slug'], dep, hop, 137, 'USDC.e→pUSD', evm.TOKENS[137] and '0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb', 6, round(dep['usd'] * 1e6), dep['usd'], src, wallet, dep['tx'], None, dep['at'], 'wrap_mint_pusd', primary='Polygon receipt; pUSD minted from the zero address, which is not a funder', timing=timing_of(dep['at'], c)))
        if not r:
            unresolved.append(dict(case=c['slug'], path=pid, where=src, reason='no public bridge record for this deposit', usd=dep['usd']))
            continue
        hop += 1
        in_chain, in_tx = (r.get('in_txs') or [[None, None]])[0]
        user = norm(r['user'])
        origin = user
        if src != user:  # UI deposit through a passage contract: the user is the sender on the origin chain
            rows.append(row(pid, c['slug'], dep, hop, in_chain or 137, r.get('in_symbol'), None, None, r.get('in_raw'), float(r['in_amount']) if r.get('in_amount') else None, user, src, in_tx, None, dep['at'], 'relay_escrow_to_payout', primary=f"Relay record {r.get('id')} (requests/v2) with the escrow id on chain"))
        else:  # bridge deposit address: same address on both chains, the real payer is the transfer into it on the origin chain
            rows.append(row(pid, c['slug'], dep, hop, in_chain, r.get('in_symbol'), None, None, r.get('in_raw'), float(r['in_amount']) if r.get('in_amount') else None, src, src, in_tx, None, dep['at'], 'relay_bridge_deposit_address', primary=f"Relay record {r.get('id')}"))
            payer = next((x for x in rels if x['target'].lower() == src and x['chain'] == in_chain and abs((x['amount'] or 0) - float(r['in_amount'] or 0)) < .01 and x['category'] == 'ONCHAIN_CONFIRMED'), None)
            if payer:
                hop += 1
                rows.append(row(pid, c['slug'], dep, hop, in_chain, r.get('in_symbol'), None, None, None, payer['amount'], payer['source'].lower(), src, payer['tx'], None, payer['at'], 'transfer_into_bridge_address', primary=f"Transfer log; investigation relation {payer['id']}"))
                origin = payer['source'].lower()
                in_tx = payer['tx']
            else:
                unresolved.append(dict(case=c['slug'], path=pid, where=src, chain=in_chain, reason='payer of the bridge deposit address not found', usd=dep['usd']))
                continue
        # upstream of the origin: FIFO over its own flows
        rows += upstream(pid, c, dep, origin, in_chain, in_tx, hop, unresolved, r.get('in_symbol'))
    return rows, unresolved


def timing_of(at, c):
    return 'avant_premier_achat' if at <= c['first_trade']['at'] else 'apres_premier_achat'


def upstream(pid, c, dep, origin, chain, in_tx, hop, unresolved, asset=None):
    rows = []
    if chain == SOLANA:
        flows, _ = walk.sol_rows(origin)
    elif chain in walk.EXPLORER_CHAINS:
        flows, _ = walk.evm_rows(origin, chain, 0)
    else:
        cls = class_of(origin, chain)
        if cls.get('cls') not in ('SERVICE', 'HIGH_VOLUME', 'CONTRACT'):
            unresolved.append(dict(case=c['slug'], path=pid, where=origin, chain=chain, reason='chain history not readable without a paid plan', usd=dep['usd']))
        return rows
    cls = class_of(origin, chain)
    if cls.get('cls') in ('SERVICE', 'HIGH_VOLUME', 'CONTRACT'):
        return rows  # the payer is itself a service: the hop above is the end of the public trail
    ledger = fifo_ledger(flows, origin)
    entry = ledger.get(in_tx)
    if not entry:
        unresolved.append(dict(case=c['slug'], path=pid, where=origin, chain=chain, reason='origin outflow not matched in its stablecoin ledger (native or swap funded)', usd=dep['usd']))
        for f in sorted((f for f in flows if f['dst'] == origin and f['at'] <= dep['at'] and walk.value_ok(f, 0) and not f.get('self_initiated') and (asset is None or f['token'] == asset)), key=lambda f: -f['at'])[:3]:
            rows.append(row(pid, c['slug'], dep, hop + 1, chain, f['token'], f.get('contract'), f['decimals'], f['raw'], walk.amount(f), f['src'], origin, f['tx'], f.get('block'), f['at'], 'candidate_inflow', alternatives='pooled: one of several inflows before the deposit', primary=f.get('source'), timing=timing_of(f['at'], c)))
        return rows
    for f, take in entry['used']:
        event = 'return_of_own_swap' if f.get('self_initiated') or (f['tx'], f['chain']) in walk.self_swaps(flows, origin) else 'transfer_in'
        rec = walk.known_relay().get(f['tx'])
        if rec and (rec.get('user') or '').lower() == c['address'].lower():
            event = 'own_withdrawal_returned'
        alt = '' if len(entry['used']) == 1 else 'pooled: FIFO split, other allocations possible'
        rows.append(row(pid, c['slug'], dep, hop + 1, chain, f['token'], f.get('contract'), f['decimals'], f['raw'], walk.amount(f), f['src'], origin, f['tx'], f.get('block'), f['at'], event, alternatives=alt, fifo=round(take, 6), primary=f.get('source'), timing=timing_of(f['at'], c)))
        src_cls = class_of(f['src'], chain) if f['src'] != evm.ZERO else dict(cls='ZERO_ADDRESS')
        if event == 'transfer_in' and src_cls.get('cls') == 'PERSONAL_SIZED' and hop < 5:
            rows += upstream(pid, c, dep, f['src'], chain, f['tx'], hop + 1, unresolved)
    if entry['uncovered'] > 1:
        unresolved.append(dict(case=c['slug'], path=pid, where=origin, chain=chain, reason=f"{entry['uncovered']:.2f} $ of this outflow not covered by earlier stablecoin inflows (native, swap or unlisted token)", usd=entry['uncovered']))
    return rows


def cashout_rows(c, w):
    rows, unresolved = [], []
    edges = [e for e in w['edges'] if e['direction'] == 'cashout']
    for i, x in enumerate(c['exit_chain']):
        wd = next(d for d in c['withdrawals'] if d['tx'] == x['tx'])
        pid = f"{c['slug']}-W{i + 1}"
        r = x.get('relay') or {}
        wallet = c['address'].lower()
        rows.append(row(pid, c['slug'], wd, 0, 137, 'pUSD', '0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb', 6, round(wd['usd'] * 1e6), wd['usd'], wallet, evm.ZERO, wd['tx'], None, wd['at'], 'burn_pusd_unwrap', primary='Polygon receipt: a burn, the zero address is not a destination'))
        out_chain, out_tx = (r.get('out_txs') or [[None, None]])[0]
        recipient = norm(x.get('recipient') or r.get('recipient') or '')
        if not r:
            unresolved.append(dict(case=c['slug'], path=pid, where=wallet, reason='no public bridge record for this withdrawal', usd=wd['usd']))
            continue
        out_amount = float(r['out_amount']) if r.get('out_amount') else None
        rows.append(row(pid, c['slug'], wd, 1, r.get('out_chain') or out_chain, r.get('out_symbol'), None, None, None, out_amount, wallet, recipient, out_tx or x['tx'], None, wd['at'], 'relay_payout_to_recipient' if out_tx else 'relay_same_tx_swap_native_log', primary=f"Relay record {r.get('id')}; payout read on the destination chain"))
        hop = 2
        for e in sorted((e for e in edges if e['src'] == recipient and (e['at'] or 0) >= wd['at'] - 60), key=lambda e: e['at'])[:12]:
            rows.append(row(pid, c['slug'], wd, hop, e['chain'], e['token'], e.get('contract'), e['decimals'], e['raw'], e['amount'], e['src'], e['dst'], e['tx'], e.get('block'), e['at'], 'onward_' + e['role'], alternatives='shared per address, not per withdrawal, when several withdrawals fed it', primary=e.get('source')))
            hop += 1
    return rows, unresolved


def attributions(all_rows, walks):
    """One line per service touched per dossier, with the interaction level asked for by the mission."""
    seen = defaultdict(lambda: dict(usd=0.0, n=0, txs=[], dirs=set()))
    for w in walks.values():
        for e in w['edges']:
            other = e['src'] if e['direction'] == 'funding' else e['dst']
            if other in w['own'] or other == evm.ZERO or e['role'] in ('return_of_own_transaction', 'internal_to_dossier', 'link_to_other_dossier', 'mint', 'burn'):
                continue
            if e.get('service') or e.get('other_cls') in ('HIGH_VOLUME', 'CONTRACT'):
                k = (w['case'], other, e['chain'])
                s = seen[k]
                s.update(name=e.get('service') or e.get('contract_name') or '', category=e.get('category') or '', level=e.get('label_level') or 'measured', source=e.get('label_source') or '', cls=e.get('other_cls'), nonce=e.get('other_nonce'))
                s['usd'] += walk.usdish(dict(token=e['token'], raw=e['raw'], decimals=e['decimals']))
                s['n'] += 1
                s['txs'].append(e['tx'])
                s['dirs'].add(e['direction'])
    out = []
    for (case, addr, chain), s in sorted(seen.items(), key=lambda kv: (kv[0][0], -kv[1]['usd'])):
        level = s['level'] or 'measured'
        if level in ('official_doc', 'verified_contract_name') or s['name'].startswith('Relay'):
            inter = 'Interaction directe confirmée'
        elif level == 'measured':
            inter = 'Service mutualisé mesuré, opérateur non attribué'
        else:
            inter = 'Attribution probable (étiquette publique)'
        out.append(dict(case=case, address=addr, chain_id=chain, chain=CHAIN_NAME.get(chain, str(chain)), name=s['name'], category=s['category'], interaction=inter, attribution_level=level, attribution_source=s['source'], address_class=s['cls'], nonce=s['nonce'] if s['nonce'] is not None else '', direction='+'.join(sorted(s['dirs'])), transfers=s['n'], usd_order_of_magnitude=round(s['usd']), example_tx=s['txs'][0], collected=COLLECTED))
    return out


def write_csv(path, rows, columns):
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def graphml(path, rows, title):
    nodes, edges = {}, []
    for r in rows:
        if r['event'].startswith(('burn', 'wrap')) and evm.ZERO in (r['source'], r['target']):
            pass
        for side in ('source', 'target'):
            a = r[side]
            if a and a != evm.ZERO:
                nodes.setdefault(a, dict(cls=r[f'{side}_class'] or '', label=''))
                if r['service'] and r[f'{side}_class'] not in ('PERSONAL_SIZED', None):
                    nodes[a]['label'] = r['service']
        if r['source'] and r['target'] and evm.ZERO not in (r['source'], r['target']):
            edges.append(r)
    with path.open('w') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<graphml xmlns="http://graphml.graphdrawing.org/xmlns">\n')
        for key, target, name in (('cls', 'node', 'class'), ('label', 'node', 'service'), ('case', 'edge', 'case'), ('path', 'edge', 'path_id'), ('chain', 'edge', 'chain'), ('asset', 'edge', 'asset'), ('amount', 'edge', 'amount'), ('tx', 'edge', 'tx'), ('utc', 'edge', 'utc'), ('event', 'edge', 'event'), ('evidence', 'edge', 'evidence')):
            f.write(f'  <key id="{key}" for="{target}" attr.name="{name}" attr.type="string"/>\n')
        f.write(f'  <graph id="{escape(title)}" edgedefault="directed">\n')
        for a, n in nodes.items():
            f.write(f'    <node id="{escape(a)}"><data key="cls">{escape(str(n["cls"]))}</data><data key="label">{escape(n["label"])}</data></node>\n')
        for r in edges:
            f.write(f'    <edge source="{escape(r["source"])}" target="{escape(r["target"])}"><data key="case">{escape(r["case"])}</data><data key="path">{escape(r["path_id"])}</data><data key="chain">{escape(str(r["chain"]))}</data><data key="asset">{escape(str(r["asset"]))}</data><data key="amount">{escape(str(r["amount"]))}</data><data key="tx">{escape(str(r["tx"]))}</data><data key="utc">{escape(str(r["utc"]))}</data><data key="event">{escape(r["event"])}</data><data key="evidence">{escape(r["evidence"])}</data></edge>\n')
        f.write('  </graph>\n</graphml>\n')


def save_relay_evidence(cases, walks):
    """Raw Relay answers kept as evidence: the v2 route retires on 24 Nov 2026. Cached answers only, no new request."""
    import gzip
    import hashlib
    out = ROOT / 'evidence/relay'
    out.mkdir(parents=True, exist_ok=True)
    txs = set()
    for c in cases.values():
        for h in list(c['funding_chain']) + list(c['exit_chain']):
            txs.add(h.get('deposit_tx') or h.get('tx'))
            r = h.get('relay') or {}
            txs |= {t for _, t in (r.get('in_txs') or []) + (r.get('out_txs') or []) if t}
    for w in walks.values():
        txs |= {l['local_tx'] for l in w['relay_links']}
    saved = 0
    for tx in txs:
        url = 'https://api.relay.link/requests/v2?hash=' + tx
        hit, value = net._load(hashlib.sha256(url.encode()).hexdigest())
        if hit and (value.get('requests') if isinstance(value, dict) else None):
            with gzip.open(out / f'{tx}.json.gz', 'wt') as f:
                json.dump(value, f)
            saved += 1
    print('relay answers saved', saved, 'of', len(txs))


def main():
    cases = {c['slug']: c for c in (json.loads(p.read_text()) for p in sorted((INV / 'cases').glob('*.json')))}
    walks = {p.stem[5:]: json.loads(p.read_text()) for p in sorted(STATE.glob('walk_*.json'))}
    fund, cash, unresolved = [], [], []
    for s, c in cases.items():
        r, u = funding_rows(c, walks[s])
        fund += r
        unresolved += u
        r, u = cashout_rows(c, walks[s])
        cash += r
        unresolved += u
    (ROOT / 'data').mkdir(exist_ok=True)
    (ROOT / 'graphs').mkdir(exist_ok=True)
    write_csv(ROOT / 'data/funding_paths.csv', fund, COLUMNS)
    write_csv(ROOT / 'data/cashout_paths.csv', cash, COLUMNS)
    attr = attributions(fund + cash, walks)
    write_csv(ROOT / 'data/service_attributions.csv', attr, list(attr[0]))
    graphml(ROOT / 'graphs/funding_network.graphml', fund, 'funding')
    graphml(ROOT / 'graphs/cashout_network.graphml', cash, 'cashout')
    (STATE / 'unresolved.json').write_text(json.dumps(unresolved))
    edges = [e for w in walks.values() for e in w['edges']]
    write_csv(ROOT / 'data/walk_edges.csv', edges, ['case', 'direction', 'depth', 'chain', 'kind', 'token', 'contract', 'decimals', 'raw', 'amount', 'src', 'dst', 'tx', 'block', 'utc', 'role', 'other_cls', 'other_kind', 'other_nonce', 'service', 'category', 'label_level', 'label_source', 'contract_name', 'source', 'method', 'note'])
    save_relay_evidence(cases, walks)
    print('funding rows', len(fund), 'cashout rows', len(cash), 'attributions', len(attr), 'unresolved', len(unresolved))


if __name__ == '__main__':
    main()
