"""Budgeted walk upstream and downstream of each dossier, through personal-sized addresses only; every stop is written with its reason.
Idempotent: re-running replays the HTTP cache and rewrites state/walk_<case>.json. One worker. `python3 walk.py [case ...]`."""
import json
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import evm
import labels
import net
import sol

INV = Path.home() / 'Projects/PolySentinel-investigation'
STATE = net.ROOT / 'state'
SOLANA = 792703809
EXPLORER_CHAINS = (1, 137, 42161, 10)
MAX_DEPTH = 4
NODE_BUDGET = 45
RELAY_BUDGET = 400
SOL_TX_BUDGET = 60
HIGH_NONCE = 1000
HIGH_PARTIES = 400
MIN = {  # (depth 0, deeper): below this a flow is dust for path purposes; it stays in the raw history
    'stable': (1, 20), 'ETH': (.0001, .002), 'WETH': (.0001, .002), 'POL': (1, 20), 'WPOL': (1, 20), 'BNB': (.0005, .01), 'WBNB': (.0005, .01), 'WBTC': (.00001, .0002), 'SOL': (.005, .05), 'WSOL': (.005, .05)}
EVM_CLASS_CACHE = {}
SOL_CLASS_CACHE = {}
RELAY_CALLS = [0]
DEAD = '0x000000000000000000000000000000000000dead'
OTHER_OWN = {}
now_utc = lambda at: datetime.fromtimestamp(at, timezone.utc).strftime('%Y-%m-%d %H:%M:%S')


def self_swaps(flows, address):
    """A transaction where the address both spends one asset and receives another is its own swap, even when a relayer sent it (EIP-7702, gas station): what it receives is not funding."""
    spent, got = defaultdict(set), defaultdict(set)
    for f in flows:
        if f['src'] == address:
            spent[(f['tx'], f['chain'])].add(f['token'])
        elif f['dst'] == address:
            got[(f['tx'], f['chain'])].add(f['token'])
    return {k for k in got if spent.get(k) and got[k] != spent[k]}


def is_evm(a):
    return a.startswith('0x') and len(a) == 42


def amount(r):
    return int(r['raw']) / 10 ** int(r['decimals'])


def value_ok(r, depth):
    key = 'stable' if r['token'] in evm.STABLE or r['token'] in ('USDC', 'USDT') else r['token']
    floor = MIN.get(key)
    return bool(floor) and amount(r) >= floor[0 if depth == 0 else 1]


def classify_evm(address, chain):
    k = (address, chain)
    if k in EVM_CLASS_CACHE:
        return EVM_CLASS_CACHE[k]
    lab = labels.lookup(address, chain)
    out = dict(address=address, chain=chain, label=lab)
    try:
        out.update(evm.probe(address, chain))
    except Exception as e:  # a failed probe stays visible, never becomes "personal"
        out.update(kind='UNREAD', nonce=None, probe_error=str(e)[:160])
    if lab and lab['category'] != 'other_labeled':
        out['cls'] = 'SERVICE'
    elif out['kind'] == 'CONTRACT':
        name = None
        try:
            name = evm.contract_name(address, chain)
        except Exception as e:
            out['name_error'] = str(e)[:120]
        out['contract_name'] = name
        cat = labels.category(name) if name else None
        out['cls'] = 'SERVICE' if cat and cat != 'other_labeled' else 'CONTRACT'
        if cat and cat != 'other_labeled':
            out['label'] = dict(name=name, category=cat, level='verified_contract_name', source=f'explorer verified source, chain {chain}', checked='2026-11-02')
    elif out['nonce'] is None:
        out['cls'] = 'UNREAD'
    elif out['nonce'] >= HIGH_NONCE:
        out['cls'] = 'HIGH_VOLUME'
    else:
        out['cls'] = 'PERSONAL_SIZED'
    EVM_CLASS_CACHE[k] = out
    return out


def classify_sol(address):
    if address in SOL_CLASS_CACHE:
        return SOL_CLASS_CACHE[address]
    lab = labels.lookup(address, SOLANA)
    out = dict(address=address, chain=SOLANA, label=lab)
    if lab and lab['category'] != 'other_labeled':
        out.update(cls='SERVICE', kind='SOLANA', nonce=None)
    else:
        try:
            sigs, complete = sol.signatures(address)
            out.update(kind='SOLANA', nonce=None, signatures=len(sigs), complete=complete, cls='HIGH_VOLUME' if not complete else 'PERSONAL_SIZED')
        except Exception as e:
            out.update(kind='SOLANA', nonce=None, cls='UNREAD', probe_error=str(e)[:160])
    SOL_CLASS_CACHE[address] = out
    return out


def classify(address, chain):
    return classify_sol(address) if chain == SOLANA else classify_evm(address, chain)


@lru_cache(maxsize=1)
def known_relay():
    out = {}
    for p in (INV / 'cases').glob('*.json'):
        c = json.loads(p.read_text())
        for h in list(c['funding_chain']) + list(c['exit_chain']):
            r = h.get('relay')
            if r:
                rec = {k: r.get(k) for k in ('id', 'status', 'user', 'recipient', 'in_txs', 'out_txs', 'in_symbol', 'in_amount', 'in_chain', 'out_symbol', 'out_amount', 'out_chain')}
                for _, t in (r.get('in_txs') or []) + (r.get('out_txs') or []):
                    if t:
                        out[t] = rec
                out[h.get('deposit_tx') or h.get('tx')] = rec
    return out


def relay_record(tx):
    """Relay's public record for a transaction, saved as evidence: the route retires on 24 Nov 2026."""
    if tx in known_relay():  # the investigation already read this record; its raw answer is cached there
        return known_relay()[tx]
    if RELAY_CALLS[0] >= RELAY_BUDGET:
        return None
    before = net.Stats.calls
    body = net.get('https://api.relay.link/requests/v2', dict(hash=tx), pause=12)
    RELAY_CALLS[0] += net.Stats.calls - before
    reqs = (body.get('requests') or []) if isinstance(body, dict) else []
    if not reqs:
        return None
    q = reqs[0]
    data, meta = q.get('data') or {}, (q.get('data') or {}).get('metadata') or {}
    cin, cout = meta.get('currencyIn') or {}, meta.get('currencyOut') or {}
    return dict(id=q.get('id'), status=q.get('status'), user=q.get('user'), recipient=q.get('recipient'), in_txs=[(t.get('chainId'), t.get('hash')) for t in data.get('inTxs') or []], out_txs=[(t.get('chainId'), t.get('hash')) for t in data.get('outTxs') or []],
                in_symbol=(cin.get('currency') or {}).get('symbol'), in_amount=cin.get('amountFormatted'), in_chain=(cin.get('currency') or {}).get('chainId'),
                out_symbol=(cout.get('currency') or {}).get('symbol'), out_amount=cout.get('amountFormatted'), out_chain=(cout.get('currency') or {}).get('chainId'))


def _b58(text):
    alphabet = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
    n = 0
    for ch in text:
        n = n * 58 + alphabet.index(ch)
    return n.to_bytes((n.bit_length() + 7) // 8, 'big').hex()


def relay_proof(rec):
    """The same 32-byte identifier on both chains, whatever the API calls its id: end of calldata or memo on the payout side, log, calldata or instruction data on the deposit side.
    True when found on both, False when read and absent, None when a side cannot be read."""
    if not rec.get('out_txs') or not rec.get('in_txs'):
        return None
    out_chain, out_tx = rec['out_txs'][0]
    in_chain, in_tx = rec['in_txs'][0]
    if not out_tx or not in_tx:
        return None
    try:
        if out_chain == SOLANA:
            memo = sol.memo(sol.transaction(out_tx))
            token = (memo if isinstance(memo, str) else json.dumps(memo or '')).lower().replace('0x', '')
        elif out_chain in net.RPC:
            token = net.rpc('eth_getTransactionByHash', [out_tx], out_chain)['input'][-64:].lower()
        else:
            return None
        if len(token) < 64:
            return None
        if in_chain == SOLANA:
            tx = sol.transaction(in_tx)
            blobs = [_b58(i['data']) for i in tx['transaction']['message']['instructions'] if i.get('data')]
            blobs += [_b58(i['data']) for inner in tx['meta'].get('innerInstructions') or [] for i in inner['instructions'] if i.get('data')]
        elif in_chain in net.RPC:
            t = net.rpc('eth_getTransactionByHash', [in_tx], in_chain)
            rc = net.rpc('eth_getTransactionReceipt', [in_tx], in_chain)
            blobs = [t['input'].lower()] + [(l['data'] + ''.join(l['topics'])).lower() for l in rc['logs']]
        else:
            return None
        return any(token in b for b in blobs)
    except Exception:
        return None


def evm_rows(address, chain, depth):
    rows, info = evm.history(address, chain)
    own_sent = {r['tx'] for r in rows if r['kind'] == 'native' and r['src'] == address}
    flows, unknown = [], 0
    for r in rows:
        if not r['ok'] or int(r['raw']) == 0 or r['src'] == r['dst']:
            continue
        if r['kind'] == 'erc20' and not r.get('known'):
            unknown += 1
            continue
        r['self_initiated'] = r['tx'] in own_sent
        flows.append(r)
    info['unknown_token_rows'], info['rows'] = unknown, len(rows)
    return flows, info


def sol_rows(address):
    sigs, complete = sol.signatures(address)
    # a transfer into an existing token account does not list the owner: the owner's own signatures miss those inflows, so read its token accounts too
    accounts = set()
    for s in sigs[:SOL_TX_BUDGET]:
        if not s.get('err'):
            tx = sol.transaction(s['signature'])
            keys = sol.keys_of(tx)
            for b in (tx['meta'].get('preTokenBalances') or []) + (tx['meta'].get('postTokenBalances') or []):
                if b.get('owner') == address and b.get('accountIndex') is not None:
                    accounts.add(keys[b['accountIndex']])
    known = {s['signature'] for s in sigs}
    for account in sorted(accounts):
        more, done = sol.signatures(account)
        complete = complete and done
        sigs += [s for s in more if s['signature'] not in known]
        known |= {s['signature'] for s in more}
    sigs = sorted(sigs, key=lambda s: -(s.get('blockTime') or 0))
    flows = []
    for s in sigs[:SOL_TX_BUDGET]:
        if s.get('err'):
            continue
        tx = sol.transaction(s['signature'])
        mv = sol.moves(tx)
        signed = sol.signers(tx)
        for m in mv:
            if m['owner'] != address or m['mint'] not in sol.MINTS and m['mint'] != 'SOL':
                continue
            token = 'SOL' if m['mint'] == 'SOL' else sol.MINTS[m['mint']]
            others = [o for o in mv if o['mint'] == m['mint'] and o['owner'] != address and (o['raw'] > 0) != (m['raw'] > 0)]
            counter = max(others, key=lambda o: abs(o['raw']))['owner'] if others else None
            flows.append(dict(chain=SOLANA, tx=s['signature'], block=s.get('slot'), at=s.get('blockTime'), kind='spl' if token != 'SOL' else 'sol', token=token, contract=m['mint'] if token != 'SOL' else None, decimals=m['decimals'], raw=str(abs(m['raw'])), src=counter if m['raw'] > 0 else address, dst=address if m['raw'] > 0 else counter, ok=True, method=None, source='solana-rpc:api.mainnet-beta', self_initiated=address in signed, signers=signed))
    flows = [f for f in flows if f['src'] and f['dst']]
    return flows, dict(address=address, chain=SOLANA, complete=complete and len(sigs) <= SOL_TX_BUDGET, signatures=len(sigs), source='solana-rpc')


class Case:
    def __init__(self, c):
        self.c, self.slug = c, c['slug']
        self.wallet = c['address'].lower()
        self.own = {self.wallet} | {o.lower() for o in c['wallet'].get('owners') or []}
        self.edges, self.stops, self.nodes = [], [], {}
        self.counts = dict(up=0, down=0)
        self.seen_edge = set()
        self.first_trade = c['first_trade']['at']
        self.first_exit = min((w['at'] for w in c['withdrawals']), default=None)
        for h in c['funding_chain']:
            if (h.get('kind') or {}).get('kind') == 'EIP7702_DELEGATED_EOA':
                self.own.add(h['immediate_source'].lower())
            user = (h.get('relay') or {}).get('user')
            if user:
                self.own.add(user.lower() if is_evm(user) else user)
        for r in c.get('recipients') or []:
            self.own.add(r['address'].lower() if is_evm(r['address']) else r['address'])

    def edge(self, direction, depth, r, role, other_cls, note=None):
        key = (direction, r['tx'], r['kind'], r.get('contract'), r['src'], r['dst'], r['raw'])
        if key in self.seen_edge:
            return
        self.seen_edge.add(key)
        lab = other_cls.get('label') or {}
        self.edges.append(dict(case=self.slug, direction=direction, depth=depth, chain=r['chain'], kind=r['kind'], token=r['token'], contract=r.get('contract'), decimals=r['decimals'], raw=r['raw'], amount=amount(r), src=r['src'], dst=r['dst'], tx=r['tx'], block=r.get('block'), at=r['at'], utc=now_utc(r['at']) if r['at'] else None, role=role, other_cls=other_cls.get('cls'), other_kind=other_cls.get('kind'), other_nonce=other_cls.get('nonce'), service=lab.get('name'), category=lab.get('category'), label_level=lab.get('level'), label_source=lab.get('source'), contract_name=other_cls.get('contract_name'), source=r.get('source'), note=note, method=r.get('method')))

    def stop(self, direction, address, chain, reason, **extra):
        self.stops.append(dict(case=self.slug, direction=direction, address=address, chain=chain, reason=reason, **extra))

    def read(self, address, chain, depth):
        key = (address, chain)
        if key not in self.nodes:
            flows, info = sol_rows(address) if chain == SOLANA else evm_rows(address, chain, depth)
            self.nodes[key] = info
            return flows
        return (sol_rows(address)[0] if chain == SOLANA else evm_rows(address, chain, depth)[0])

    def walk(self, direction, seeds):
        queue = list(seeds)  # (address, chain, time limit, depth)
        visited = set()
        while queue:
            queue.sort(key=lambda n: n[3])
            address, chain, limit, depth = queue.pop(0)
            if (address, chain) in visited:
                continue
            visited.add((address, chain))
            if len(visited) > NODE_BUDGET:
                self.stop(direction, address, chain, 'NODE_BUDGET')
                continue
            if chain not in EXPLORER_CHAINS and chain != SOLANA:
                self.stop(direction, address, chain, 'CHAIN_NOT_READABLE', detail='no free history source for this chain: BscScan and Base via Etherscan need a paid plan, base.blockscout.com sits behind a browser challenge that was not bypassed', nonce=_nonce(address, chain))
                continue
            try:
                flows = self.read(address, chain, depth)
            except net.Pause:
                raise
            except Exception as e:
                self.stop(direction, address, chain, 'READ_FAILED', detail=str(e)[:200])
                continue
            info = self.nodes[(address, chain)]
            # spam rows do not make a hub: count who really moved value with this address
            parties = {f['src'] if f['dst'] == address else f['dst'] for f in flows}
            info['value_counterparties'] = len(parties)
            if chain != SOLANA and depth > 0 and len(parties) >= HIGH_PARTIES:
                self.stop(direction, address, chain, 'HIGH_VOLUME_AT_READ', rows=info.get('rows'), value_counterparties=len(parties), complete=info['complete'])
                continue
            queue += self.expand(direction, address, chain, limit, depth, flows)

    def expand(self, direction, address, chain, limit, depth, flows):
        inbound = direction == 'funding'
        side = [f for f in flows if (f['dst'] == address if inbound else f['src'] == address)]
        side = [f for f in side if value_ok(f, depth) and (f['at'] is not None) and (f['at'] <= limit if inbound else f['at'] >= limit)]
        if not side:
            self.stop(direction, address, chain, 'NO_FLOW_IN_WINDOW' if inbound else 'NO_LATER_OUTFLOW', depth=depth)
            return []
        if depth > 0:  # deep nodes: the largest flows and the first ever
            ordered = sorted(side, key=lambda f: -usdish(f))[:8]
            first = min(side, key=lambda f: f['at'])
            side = ordered + ([first] if first not in ordered else [])
        next_nodes = []
        for f in sorted(side, key=lambda f: -usdish(f)):
            other = f['src'] if inbound else f['dst']
            if other in (evm.ZERO, DEAD):  # a mint or a burn, never a funder or a destination
                self.edge(direction, depth, f, 'mint' if inbound else 'burn', dict(cls='ZERO_ADDRESS'))
                continue
            if inbound and (f.get('self_initiated') or (f['tx'], chain) in self_swaps(flows, address)):
                self.edge(direction, depth, f, 'return_of_own_transaction', dict(cls='SELF'))
                continue
            cls = classify(other, chain)
            other_is_own = (other in self.own)
            if other_is_own:
                self.edge(direction, depth, f, 'internal_to_dossier', cls)
                continue
            if other in OTHER_OWN.get(self.slug, ()):  # stop here: walking on would book another dossier's funders as this one's
                self.edge(direction, depth, f, 'link_to_other_dossier', cls, note=json.dumps(dict(other_case=sorted(OTHER_OWN[self.slug][other]))))
                continue
            role = 'transfer'
            relay_id = None
            lab = cls.get('label') or {}
            maybe_relay = lab.get('name', '').startswith('Relay') or cls['cls'] == 'HIGH_VOLUME' or other == '0xc8a6871d4ec4dae64f605db0f8a0b3d9ef928d64'
            if maybe_relay and depth <= 2 and chain != SOLANA or (chain == SOLANA and lab.get('name', '').startswith('Relay')):
                rec = relay_record(f['tx'])
                if rec:
                    relay_id = rec['id']
                    role = 'relay_payout' if inbound else 'relay_deposit'
                    self.edge(direction, depth, f, role, cls, note=json.dumps(rec)[:900])
                    far = rec['user'] if inbound else rec['recipient']
                    far_chain = rec['in_chain'] if inbound else rec['out_chain']
                    far_tx = (rec['in_txs'] or [[None, None]])[0][1] if inbound else (rec['out_txs'] or [[None, None]])[0][1]
                    if far:
                        far_l = far.lower() if is_evm(far) else far
                        proof = relay_proof(rec)
                        self.relay_links.append(dict(case=self.slug, direction=direction, depth=depth, id=rec['id'], status=rec['status'], user=rec['user'], recipient=rec['recipient'], in_chain=rec['in_chain'], in_symbol=rec['in_symbol'], in_amount=rec['in_amount'], in_txs=rec['in_txs'], out_chain=rec['out_chain'], out_symbol=rec['out_symbol'], out_amount=rec['out_amount'], out_txs=rec['out_txs'], local_tx=f['tx'], local_chain=chain, onchain_id_proof=proof, at=f['at']))
                        if far_l in self.own or far_l == address:
                            pass  # the dossier's own deposit or withdrawal
                        elif far_chain is not None and depth < MAX_DEPTH:
                            next_nodes.append((far_l, far_chain, f['at'], depth + 1))
                    continue
            note = None
            if cls['cls'] != 'PERSONAL_SIZED' and depth <= 1 and chain in net.RPC:  # who sent the transaction says more than the contract that paid
                try:
                    t = net.rpc('eth_getTransactionByHash', [f['tx']], chain)
                    note = json.dumps(dict(tx_from=t['from'], tx_to=t['to'], selector=t['input'][:10]))
                except Exception as e:
                    note = json.dumps(dict(tx_read_error=str(e)[:100]))
            self.edge(direction, depth, f, role, cls, note=note)
            if cls['cls'] == 'PERSONAL_SIZED' and depth < MAX_DEPTH:
                # the same address on the other chains: a personal key reuses them, and a Polygon PoS mint means an Ethereum leg
                for c2 in (EXPLORER_CHAINS if depth <= 1 and is_evm(other) else (chain,)):
                    next_nodes.append((other, c2, f['at'], depth + 1))
            elif cls['cls'] != 'PERSONAL_SIZED':
                self.stop(direction, other, chain, 'SERVICE_OR_SHARED:' + cls['cls'], name=lab.get('name') or cls.get('contract_name'), category=lab.get('category'), nonce=cls.get('nonce'), kind=cls.get('kind'), via_tx=f['tx'], amount=amount(f), token=f['token'], depth=depth)
            elif depth >= MAX_DEPTH:
                self.stop(direction, other, chain, 'DEPTH_BUDGET', via_tx=f['tx'], amount=amount(f), token=f['token'])
        return next_nodes

    relay_links = None


def _nonce(address, chain):
    try:
        return int(net.rpc('eth_getTransactionCount', [address, 'latest'], chain), 16)
    except Exception:
        return None


def usdish(f):
    # shortcut: order of magnitude for ranking only, never reported as a value
    price = {'ETH': 2300, 'WETH': 2300, 'POL': .1, 'WPOL': .1, 'BNB': 700, 'WBNB': 700, 'WBTC': 90000, 'SOL': 150, 'WSOL': 150}.get(f['token'], 1)
    return amount(f) * price


def seeds_for(case):
    c = case.c
    up, down = [], []
    t_end = int(time.time())
    for o in c['wallet'].get('owners') or []:
        for chain in EXPLORER_CHAINS:
            up.append((o.lower(), chain, t_end, 0))
    for h in c['funding_chain']:
        r = h.get('relay') or {}
        if (h.get('kind') or {}).get('kind') == 'EIP7702_DELEGATED_EOA':
            for chain in EXPLORER_CHAINS:
                up.append((h['immediate_source'].lower(), chain, t_end, 0))
        user = r.get('user')
        if user and not is_evm(user):
            up.append((user, SOLANA, t_end, 0))
    # payers found earlier by bisection on chains without a free history source
    for rel in c['chain_relations']:
        if rel['category'] == 'ONCHAIN_CONFIRMED' and rel.get('tx') and is_evm(rel['source']) and rel['source'].lower() not in case.own and not rel.get('source_label'):
            if classify_evm(rel['source'].lower(), rel['chain'])['cls'] == 'PERSONAL_SIZED' and rel['target'].lower() in case.own:
                up.append((rel['source'].lower(), rel['chain'], rel['at'], 1))
    first_exit = case.first_exit or 0
    # keys first, from 30 days before the first deposit: a gas or funds transfer to someone else matters even before any withdrawal
    start = min(d['at'] for d in c['deposits']) - 30 * 86400
    for o in c['wallet'].get('owners') or []:
        for chain in EXPLORER_CHAINS:
            down.append((o.lower(), chain, start, 0))
    for r in c.get('recipients') or []:
        a = r['address'].lower() if is_evm(r['address']) else r['address']
        down.append((a, r['chain'], first_exit, 0))
    return up, down


def balances(address, chain):
    if chain == SOLANA:
        out = {}
        try:
            out['SOL'] = sol.rpc('getBalance', [address], cache=True)['value'] / 1e9
            for mint, name in ((sol.USDC, 'USDC'), (sol.USDT, 'USDT')):
                for acc in sol.rpc('getTokenAccountsByOwner', [address, dict(mint=mint), dict(encoding='jsonParsed')], cache=True)['value']:
                    amt = float(acc['account']['data']['parsed']['info']['tokenAmount']['uiAmount'] or 0)
                    if amt:
                        out[name] = out.get(name, 0) + amt
        except Exception as e:
            out['error'] = str(e)[:120]
        return out
    if chain not in net.RPC:
        return None
    out = {}
    try:
        out[evm.NATIVE[chain]] = int(net.rpc('eth_getBalance', [address, 'latest'], chain), 16) / 1e18
        for contract, name in evm.TOKENS[chain].items():
            if name in evm.STABLE:
                data = '0x70a08231' + address[2:].rjust(64, '0')
                bal = int(net.rpc('eth_call', [dict(to=contract, data=data), 'latest'], chain) or '0x0', 16)
                if bal:
                    out[name] = bal / 10 ** evm.decimals(chain, name)
    except Exception as e:
        out['error'] = str(e)[:120]
    return out


def run(c):
    case = Case(c)
    case.relay_links = []
    up, down = seeds_for(case)
    case.walk('funding', up)
    case.walk('cashout', down)
    holdings = []
    read = {(s['address'], s['chain']) for s in case.stops if s['reason'] == 'NO_LATER_OUTFLOW'} | {(a, chain) for a in case.own if is_evm(a) and a != case.wallet for chain in net.RPC} | {(a, SOLANA) for a in case.own if not is_evm(a)}
    for address, chain in sorted(read, key=str):  # what still sits on the dossier's own addresses at the read date
        bal = balances(address, chain)
        if bal and any(v for k, v in bal.items() if k != 'error'):
            holdings.append(dict(address=address, chain=chain, balances=bal, read_at=now_utc(time.time())))
    result = dict(case=case.slug, wallet=case.wallet, own=sorted(case.own), edges=case.edges, stops=case.stops, relay_links=case.relay_links, holdings=holdings, nodes=[dict(v) for v in case.nodes.values()], first_trade=case.first_trade, first_exit=case.first_exit, collected_at=now_utc(time.time()))
    tmp = STATE / f'walk_{case.slug}.json.tmp'
    tmp.write_text(json.dumps(result))
    tmp.replace(STATE / f'walk_{case.slug}.json')
    return result


def main(only):
    cases = [json.loads(p.read_text()) for p in sorted((INV / 'cases').glob('*.json'))]
    cases.sort(key=lambda c: -c['account']['deposits'])  # largest flows first
    owns = {c['slug']: Case(c).own for c in cases}
    for s in owns:
        OTHER_OWN[s] = defaultdict(set)
        for t, addrs in owns.items():
            if t != s:
                for a in addrs:
                    OTHER_OWN[s][a].add(t)
    for c in cases:
        if only and c['slug'] not in only:
            continue
        t = time.time()
        before = net.Stats.calls
        try:
            r = run(c)
            print(f"{c['slug']}: nodes {len(r['nodes'])} edges {len(r['edges'])} stops {len(r['stops'])} relay {len(r['relay_links'])} holdings {len(r['holdings'])} calls {net.Stats.calls - before} {time.time() - t:.0f}s", flush=True)
        except net.Pause as e:
            print(f"PAUSE on {c['slug']}: {e}; re-run resumes from cache", flush=True)
            sys.exit(3)
        except Exception as e:  # keep partial results of the others and move on
            print(f"FAILED {c['slug']}: {type(e).__name__} {str(e)[:300]}", flush=True)


if __name__ == '__main__':
    main(set(sys.argv[1:]))
