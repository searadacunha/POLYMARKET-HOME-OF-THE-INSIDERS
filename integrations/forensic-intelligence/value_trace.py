#!/usr/bin/env python3
"""Bounded, read-only value walk: public indexer pages in, ledger.py evidence edges out.

A case folder holds case.json. `walk` saves every indexer page it reads (gzip, SHA-256 in an
append-only manifest) and writes evidence_edges.csv, path.csv, nodes.json, labels.json and package.json.
`replay` re-reads the followed transfers as transaction receipts on two JSON-RPC endpoints that
must agree, which raises those edges from CANDIDATE to ONCHAIN_CONFIRMED. `check` recomputes
everything offline from the saved pages and compares bytes, replay.json included, so a package can be verified by a
third party without any network access.

Followed value is never asserted from one accounting convention. Tokens are fungible, so every
transfer out of a wallet is valued twice: tracked_others_first (the wallet spends its other funds
first, the lowest-intermediate-balance reading) and tracked_first (it spends the followed funds
first). Where the two agree, the attribution holds under any convention; where they part, the
followed value is commingled and the amount is a convention, not a fact.
An edge records a token movement, never who controls an address. Standard library only.

case.json: {"chain": "ethereum", "token": "USDT", "start": "0x...", "seed_transactions": ["0x..."],
            "min_follow": "10000", "max_depth": 4, "max_addresses": 30,
            "max_pages_per_address": 400, "stop_fan_in": 25, "dust": "1"}
stop_fan_in: a wallet with more senders than this (senders of at most `dust` in total are ignored,
which keeps address-poisoning baits out of the count) is read, but its recipients are not.
usage: value_trace.py walk|replay|check CASE_DIR
"""
import csv
import gzip
import hashlib
import io
import json
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ledger import FIELDS, canonical_edges, normalized_units  # noqa: E402

CHAINS = {  # name: (chain id, Blockscout API v2 base, two default JSON-RPC endpoints)
    'ethereum': (1, 'https://eth.blockscout.com/api/v2', ['https://ethereum-rpc.publicnode.com', 'https://eth.drpc.org']),
    'polygon': (137, 'https://polygon.blockscout.com/api/v2', ['https://polygon-bor-rpc.publicnode.com', 'https://polygon.drpc.org']),
}
TOKENS = {  # official contracts only, so that look-alike tokens are never counted: (contract, decimals)
    ('ethereum', 'USDT'): ('0xdAC17F958D2ee523a2206206994597C13D831ec7', 6),
    ('ethereum', 'USDC'): ('0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48', 6),
    ('polygon', 'USDC'): ('0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359', 6),
    ('polygon', 'USDC.e'): ('0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174', 6),
    ('polygon', 'USDT'): ('0xc2132D05D31c914a87C6611C10748AEb04B58e8F', 6),
}
TRANSFER_TOPIC = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
HEADERS = {'User-Agent': 'forensic-intelligence-value-trace/1.0 (read-only research client)', 'Accept': 'application/json', 'Content-Type': 'application/json'}
PATH_FIELDS = ('depth', 'timestamp_utc', 'block_number', 'log_index', 'transaction_hash', 'from', 'to',
               'amount', 'tracked_others_first', 'tracked_first', 'recipient_status', 'evidence_level')
STOP_ORDER = ('public_tag', 'sender_commingled', 'max_depth', 'address_budget', 'below_min_follow')


class Store:
    """Raw responses, gzip-compressed, each with its SHA-256 in an append-only manifest."""

    def __init__(self, folder):
        self.dir = Path(folder)
        (self.dir / 'raw').mkdir(parents=True, exist_ok=True)
        self.manifest = self.dir / 'manifest.jsonl'
        self.index = {}
        if self.manifest.exists():
            for line in self.manifest.read_text().splitlines():
                entry = json.loads(line)
                self.index[entry['name']] = entry

    def has(self, name):
        return name in self.index

    def save(self, name, url, body):
        (self.dir / 'raw' / f'{name}.json.gz').write_bytes(gzip.compress(body, mtime=0))
        entry = {'name': name, 'url': url, 'sha256_body': hashlib.sha256(body).hexdigest(), 'bytes': len(body),
                 'fetched_utc': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}
        with self.manifest.open('a') as handle:
            handle.write(json.dumps(entry) + '\n')
        self.index[name] = entry

    def load(self, name):
        body = gzip.decompress((self.dir / 'raw' / f'{name}.json.gz').read_bytes())
        if hashlib.sha256(body).hexdigest() != self.index[name]['sha256_body']:
            raise ValueError(f'{name}: saved page does not match its manifest hash')
        return json.loads(body)


def http(url, payload=None, tries=4):
    """One request. A failure is raised, never returned as an empty answer."""
    data = json.dumps(payload).encode() if payload is not None else None
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=HEADERS), timeout=60) as response:
                return response.read()
        except Exception as exc:  # retried, then raised below
            last = exc
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f'{url}: {last!r}')


def rpc(store, name, url, method, params, tries=4, offline=False):
    """Result of one JSON-RPC call, saved once. A null result (a node that lost the record) is retried, never saved.

    offline=True raises on a response that is not saved, so an offline check fails closed instead of fetching."""
    for attempt in range(tries):
        if store.has(name):
            return store.load(name)['result']
        if offline:
            raise FileNotFoundError(f'{name}: response needed but not saved')
        body = http(url, {'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params})
        if json.loads(body).get('result') is not None:
            store.save(name, url, body)
            return store.load(name)['result']
        time.sleep(2 * (attempt + 1))
    return {}


def pages(store, chain, token, address, max_pages, offline):
    """Transfer pages of one address, newest first. complete is False when the page cap stops the reading."""
    base, contract = CHAINS[chain][1], TOKENS[(chain, token)][0]
    out, params = [], {'type': 'ERC-20', 'token': contract}
    for number in range(max_pages):
        name = f'{chain}_{address.lower()}_{token}_p{number:03d}'
        if not store.has(name):
            if offline:
                raise FileNotFoundError(f'{name}: page needed but not saved')
            url = f'{base}/addresses/{address}/token-transfers?' + urllib.parse.urlencode(params)
            store.save(name, url, http(url))
            time.sleep(0.3)
        page = store.load(name)
        out.append((name, page))
        following = page.get('next_page_params')
        if not following:
            return out, True
        params = {'type': 'ERC-20', 'token': contract, **following}
    return out, False


def edges_from(named_pages, chain, token, labels):
    """ledger.py edges of the official token only; also collects the indexer's public labels of each address."""
    chain_id, (contract, decimals) = CHAINS[chain][0], TOKENS[(chain, token)]
    rows, spoofed = [], 0
    for name, page in named_pages:
        for item in page.get('items', []):
            if ((item.get('token') or {}).get('address_hash') or '').lower() != contract.lower():
                spoofed += 1
                continue
            for side in ('from', 'to'):
                party = item[side]
                tags = sorted({t.get('name', '') for t in ((party.get('metadata') or {}).get('tags') or [])})
                labels[party['hash'].lower()] = {'name': party.get('name'), 'tags': tags, 'is_contract': bool(party.get('is_contract')),
                                                 'proxy_type': party.get('proxy_type')}
            raw = int(item['total']['value'])
            rows.append({'chain_id': chain_id, 'transaction_hash': item['transaction_hash'], 'block_number': int(item['block_number']),
                         'timestamp_utc': item['timestamp'][:19] + 'Z', 'log_index': int(item['log_index']),
                         'from': item['from']['hash'], 'to': item['to']['hash'], 'token_contract': contract,
                         'token_decimals': decimals, 'raw_amount': str(raw), 'normalized_amount': str(normalized_units(raw, decimals)),
                         'usd_value_when_supported': None, 'protocol': None, 'source': f'blockscout:{name}',
                         'relation_type': 'erc20_transfer', 'evidence_level': 'CANDIDATE'})
    return rows, spoofed


def edge_id(edge):
    return f"{edge['chain_id']}:{edge['transaction_hash'].lower()}:{edge['log_index']}"


def propagate(edges, complete, seeds, start):
    """One chronological pass over every positive transfer. Returns the transfers that may carry seed value.

    Per fully read wallet the state is [tracked, other] under "others first" then [tracked, other] under
    "tracked first", in raw units. Both conventions always hold the same total balance.
    """
    state = defaultdict(lambda: [0, 0, 0, 0])
    path, overdrawn = [], set()
    for edge in sorted(edges, key=lambda e: (e['block_number'], e['log_index'])):
        sender, recipient, amount = edge['from'].lower(), edge['to'].lower(), int(edge['raw_amount'])
        if amount == 0 or sender == recipient:
            continue
        if edge['transaction_hash'].lower() in seeds and recipient == start:
            low = high = amount
            path.append({**edge, 'others_first': low, 'tracked_first': high, 'seed': True})
        elif complete.get(sender):
            s = state[sender]
            if amount > s[0] + s[1]:  # spends more than the ledger ever received: an inflow is missing
                overdrawn.add(sender)
            low = min(max(amount - s[1], 0), s[0])
            high = min(amount, s[2])
            s[0], s[1] = s[0] - low, max(s[1] - (amount - low), 0)
            s[2], s[3] = s[2] - high, max(s[3] - (amount - high), 0)
            if low or high:
                path.append({**edge, 'others_first': low, 'tracked_first': high, 'seed': False})
        else:
            low = high = 0
        if recipient in complete:
            s = state[recipient]
            s[0], s[1], s[2], s[3] = s[0] + low, s[1] + amount - low, s[2] + high, s[3] + amount - high
    return path, state, overdrawn


def compute(case_dir, offline):
    """Read (or fetch) the ledgers the walk needs and derive every output as bytes, deterministically."""
    case_dir = Path(case_dir)
    case = json.loads((case_dir / 'case.json').read_text())
    store = Store(case_dir)
    chain, token = case['chain'], case['token']
    decimals = TOKENS[(chain, token)][1]
    start, seeds = case['start'].lower(), {t.lower() for t in case['seed_transactions']}
    min_follow = int(Decimal(case['min_follow']) * 10 ** decimals)
    dust = int(Decimal(case.get('dust', '1')) * 10 ** decimals)
    depth, complete, labels, rows, spoofed = {}, {}, {}, [], 0

    def read(address, level):
        nonlocal spoofed
        named, done = pages(store, chain, token, address, case['max_pages_per_address'], offline)
        new_rows, bad = edges_from(named, chain, token, labels)
        rows.extend(new_rows)
        spoofed += bad
        depth[address], complete[address] = level, done

    read(start, 0)
    while True:
        edges = canonical_edges(rows)
        positive = [e for e in edges if int(e['raw_amount']) > 0 and e['from'].lower() != e['to'].lower()]
        sent_to = defaultdict(Counter)
        for e in positive:
            sent_to[e['to'].lower()][e['from'].lower()] += int(e['raw_amount'])
        fan_in = {address: sum(1 for total in senders.values() if total > dust) for address, senders in sent_to.items()}
        path, state, overdrawn = propagate(positive, complete, seeds, start)
        status, chosen = {}, []
        for step in path:
            sender, recipient = step['from'].lower(), step['to'].lower()
            if step['seed'] or recipient in depth:
                continue
            if max(step['others_first'], step['tracked_first']) < min_follow:
                reason = 'below_min_follow'
            elif labels[recipient]['tags']:
                reason = 'public_tag'
            elif fan_in.get(sender, 0) > case['stop_fan_in']:
                reason = 'sender_commingled'
            elif depth[sender] + 1 > case['max_depth']:
                reason = 'max_depth'
            elif len(depth) + len(chosen) >= case['max_addresses']:
                reason = 'address_budget'
            else:
                reason = None
                if recipient not in [c[0] for c in chosen]:
                    chosen.append((recipient, depth[sender] + 1))
            if reason and (recipient not in status or STOP_ORDER.index(reason) < STOP_ORDER.index(status[recipient])):
                status[recipient] = reason
        if not chosen:
            break
        for address, level in chosen:
            read(address, level)

    replayed = json.loads((case_dir / 'replay.json').read_text()) if (case_dir / 'replay.json').exists() else {}
    for e in edges:
        if replayed.get(edge_id(e), {}).get('ok'):
            e['evidence_level'] = 'ONCHAIN_CONFIRMED'

    def units(raw):
        return ('-' if raw < 0 else '') + str(normalized_units(abs(raw), decimals))

    def table(fields, records):
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(records)
        return buffer.getvalue().encode()

    level_of = {edge_id(e): e['evidence_level'] for e in edges}
    path_rows = [{'depth': 0 if p['seed'] else depth[p['from'].lower()] + 1, 'timestamp_utc': p['timestamp_utc'],
                  'block_number': p['block_number'], 'log_index': p['log_index'], 'transaction_hash': p['transaction_hash'],
                  'from': p['from'], 'to': p['to'], 'amount': units(int(p['raw_amount'])),
                  'tracked_others_first': units(p['others_first']), 'tracked_first': units(p['tracked_first']),
                  'recipient_status': 'seed' if p['seed'] else (('followed' if complete[p['to'].lower()] else 'ledger_incomplete')
                                                              if p['to'].lower() in depth else status.get(p['to'].lower(), '')),
                  'evidence_level': level_of[edge_id(p)]} for p in path]
    nodes = []
    for address in sorted(depth, key=lambda a: (depth[a], a)):
        inflow = [e for e in positive if e['to'].lower() == address]
        outflow = [e for e in positive if e['from'].lower() == address]
        top_in, top_out, seen = Counter(), Counter(), sorted({e['timestamp_utc'] for e in inflow + outflow})
        for e in inflow:
            top_in[e['from'].lower()] += int(e['raw_amount'])
        for e in outflow:
            top_out[e['to'].lower()] += int(e['raw_amount'])
        counterparties, alike = set(top_in) | set(top_out), defaultdict(list)
        for other in sorted(counterparties):
            alike[(other[2:6], other[-4:])].append(other)
        nodes.append({
            'address': address, 'depth': depth[address], 'ledger_complete': complete[address], 'label': labels.get(address),
            'transfers': len(inflow) + len(outflow), 'senders': len(top_in), 'senders_above_dust': fan_in.get(address, 0),
            'recipients': len(top_out),
            'in_total': units(sum(top_in.values())), 'out_total': units(sum(top_out.values())),
            'balance_from_ledger': units(sum(top_in.values()) - sum(top_out.values())),
            'first_utc': seen[0] if seen else None, 'last_utc': seen[-1] if seen else None,
            'top_in': [[a, units(v)] for a, v in top_in.most_common(5)], 'top_out': [[a, units(v)] for a, v in top_out.most_common(5)],
            'tracked_left_others_first': units(state[address][0]), 'tracked_left_tracked_first': units(state[address][2]),
            'overdrawn': address in overdrawn,  # True means the ledger misses an inflow: do not trust its bounds
            'lookalike_counterparties': [group for group in alike.values() if len(group) > 1],
        })
    ends = defaultdict(lambda: [0, 0, 0])  # where followed value stops: amount received, under each convention
    for p in path:
        if not p['seed'] and p['to'].lower() not in depth:
            for i, value in enumerate((int(p['raw_amount']), p['others_first'], p['tracked_first'])):
                ends[p['to'].lower()][i] += value
    terminals = [{'address': a, 'status': status.get(a, ''), 'label': labels.get(a), 'received': units(v[0]),
                  'tracked_others_first': units(v[1]), 'tracked_first': units(v[2])}
                 for a, v in sorted(ends.items(), key=lambda kv: (-max(kv[1][1], kv[1][2]), kv[0]))]
    tagged = {a: label for a, label in sorted(labels.items()) if label['tags']}  # every public tag met in the pages read
    outputs = {
        'evidence_edges.csv': table(FIELDS, [{f: e[f] for f in FIELDS} for e in edges]),
        'path.csv': table(PATH_FIELDS, path_rows),
        'nodes.json': (json.dumps({'read': nodes, 'terminals': terminals}, indent=1) + '\n').encode(),
        'labels.json': (json.dumps(tagged, indent=1) + '\n').encode(),
    }
    package = {'case': case, 'chain_id': CHAINS[chain][0], 'token_contract': TOKENS[(chain, token)][0],
               'addresses_read': len(depth), 'pages_read': sum(1 for n in store.index if n.startswith(chain + '_')),
               'edges': len(edges), 'path_edges': len(path_rows), 'spoofed_token_items_skipped': spoofed,
               'receipts_replayed_ok': sum(1 for r in replayed.values() if r.get('ok')), 'receipts_replayed_failed': sum(1 for r in replayed.values() if not r.get('ok')),
               'outputs_sha256': {name: hashlib.sha256(body).hexdigest() for name, body in sorted(outputs.items())},
               'meaning': 'token movements valued under two accounting conventions; not ownership, not identity'}
    outputs['package.json'] = (json.dumps(package, indent=1) + '\n').encode()
    return outputs


def write(case_dir, outputs):
    for name, body in outputs.items():
        (Path(case_dir) / name).write_bytes(body)
    return json.loads(outputs['package.json'])


def replay(case_dir, write=True, offline=False):
    """Receipts of every followed transfer, read on two endpoints that must both show the exact Transfer log.

    With every response already saved no network call is made; offline=True raises on a missing response, so
    write=False, offline=True re-derives replay.json offline and fails closed."""
    case_dir = Path(case_dir)
    case = json.loads((case_dir / 'case.json').read_text())
    store = Store(case_dir)
    chain, token = case['chain'], case['token']
    endpoints, contract = case.get('rpc') or CHAINS[chain][2], TOKENS[(chain, token)][0].lower()
    edges = {edge_id(e): e for e in csv.DictReader((case_dir / 'evidence_edges.csv').read_text().splitlines())}
    wanted = [f"{CHAINS[chain][0]}:{row['transaction_hash'].lower()}:{row['log_index']}" for row in csv.DictReader((case_dir / 'path.csv').read_text().splitlines())]

    def call(index, name, method, params):
        return rpc(store, name, endpoints[index], method, params, offline=offline)

    def topic(address):
        return '0x' + address.lower()[2:].rjust(64, '0')

    result = {}
    for key in sorted(set(wanted)):
        e = edges[key]
        expect = ('0x1', int(e['block_number']), contract, [TRANSFER_TOPIC, topic(e['from']), topic(e['to'])], int(e['raw_amount']), e['timestamp_utc'])
        seen, signer, called = [], None, None
        for i in range(len(endpoints)):
            receipt = call(i, f"rpc{i}_{chain}_{e['transaction_hash'].lower()}", 'eth_getTransactionReceipt', [e['transaction_hash']])
            signer, called = signer or receipt.get('from'), called or receipt.get('to')
            log = next((l for l in receipt.get('logs', []) if int(l['logIndex'], 16) == int(e['log_index'])), None)
            block = call(i, f"rpc{i}_{chain}_block_{e['block_number']}", 'eth_getBlockByNumber', [hex(int(e['block_number'])), False])
            stamp = datetime.fromtimestamp(int(block['timestamp'], 16), timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ') if block.get('timestamp') else None
            seen.append(None if log is None else (receipt.get('status'), int(receipt['blockNumber'], 16), log['address'].lower(),
                                                  [t.lower() for t in log['topics']], int(log['data'], 16), stamp))
        result[key] = {'ok': all(s == expect for s in seen), 'endpoints': len(endpoints), 'signer': signer, 'called': called,
                       'holder_signed': bool(signer) and signer.lower() == e['from'].lower()}
    if write:
        (case_dir / 'replay.json').write_text(json.dumps(result, indent=1, sort_keys=True) + '\n')
    return result


def main(argv):
    if len(argv) != 3 or argv[1] not in ('walk', 'replay', 'check'):
        sys.exit(__doc__)
    command, case_dir = argv[1], argv[2]
    if command == 'walk':
        print(json.dumps(write(case_dir, compute(case_dir, offline=False)), indent=1))
    elif command == 'replay':
        result = replay(case_dir)
        write(case_dir, compute(case_dir, offline=True))
        failed = [k for k, v in result.items() if not v['ok']]
        print(f'{len(result) - len(failed)} of {len(result)} followed transfers confirmed by receipt on every endpoint')
        sys.exit(1 if failed else 0)
    else:
        different = [name for name, body in compute(case_dir, offline=True).items()
                     if not (Path(case_dir) / name).exists() or (Path(case_dir) / name).read_bytes() != body]
        saved = Path(case_dir) / 'replay.json'
        if saved.exists() and saved.read_bytes() != (json.dumps(replay(case_dir, write=False, offline=True), indent=1, sort_keys=True) + '\n').encode():
            different.append('replay.json')
        print('package differs from its saved pages: ' + ', '.join(different) if different else 'package reproduced byte for byte from the saved pages')
        sys.exit(1 if different else 0)


if __name__ == '__main__':
    main(sys.argv)
