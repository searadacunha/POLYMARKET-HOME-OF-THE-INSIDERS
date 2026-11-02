"""Follow one account's money both ways as far as public proof goes, and write down why each branch stopped.

Differences with the earlier walks, each from a demonstrated defect (see AUDIT.md): no silent "largest 8 flows" cut, a stop for
every branch left unfollowed; a cross-chain hop is followed only when the same identifier is read on both chains; histories run to
the end by block cursor; a hub is a measure, written beside any label. Nothing merges owners: an edge is money, not control.
"""
import json
import time
from collections import Counter, defaultdict

from . import explorer, labels, proxy
from .events import DEAD, NATIVE, TOKENS, ZERO, identity, rough_usd
from .net import BudgetSpent, Refused

EXPLORER_CHAINS = (1, 137, 42161, 10)
WINDOW_CHAINS = (8453, 56)
ALL_EVM = EXPLORER_CHAINS + WINDOW_CHAINS
DUST_USD = 1.0
RELAY_DEPOSITORY = '0x4cd00e387622c35bddb9b4c962c136462338bc31'
SOL_CHAIN = 792703809
STOP_CLASSES = (labels.SERVICE, labels.CONTRACT, labels.HUB, labels.UNREAD)


def is_value(e):
    """Native and the listed tokens. Anything else stays counted and unfollowed: most of it is poisoning."""
    if e['kind'] in ('native', 'internal'):
        return True
    return bool(e.get('token_known'))


def self_swaps(events, address):
    spent, got = defaultdict(set), defaultdict(set)
    for e in events:
        if e['from'] == address:
            spent[e['transaction_hash']].add(e['token'])
        elif e['to'] == address:
            got[e['transaction_hash']].add(e['token'])
    return {t for t in got if spent.get(t) and got[t] != spent[t]}


class Trace:
    def __init__(self, net, slug, wallet, own, relay=None, max_depth=8, node_budget=120, window_events=None, log=None, solana=None):
        self.net, self.slug, self.wallet = net, slug, wallet.lower()
        self.solana = solana
        self.own = {a.lower() if a.startswith('0x') else a for a in own} | {self.wallet}
        self.relay, self.max_depth, self.node_budget = relay, max_depth, node_budget
        self.window_events = window_events or (lambda address, chain: None)
        self.edges, self.stops, self.seen, self.nodes, self.classes = [], [], set(), {}, {}
        self.log = log or (lambda m: None)
        self.ignored_tokens = Counter()

    def stop(self, direction, address, chain, reason, **extra):
        self.stops.append(dict(case=self.slug, direction=direction, address=address, chain=chain, reason=reason, **extra))

    def cls(self, address, chain, parties=None):
        key = (address, chain)
        if chain == SOL_CHAIN:
            return self.classes.setdefault(key, self._cls_solana(address))
        if key not in self.classes or parties:
            self.classes[key] = labels.classify(self.net, address, chain, parties)
        return self.classes[key]

    def _cls_solana(self, address):
        """Label first, then measured size: all the signature pages ran out means a hub. Never personal by default when the read fails."""
        label = labels.lookup(address, SOL_CHAIN)
        out = dict(address=address, chain=SOL_CHAIN, label=label, kind='SOLANA', nonce=None)
        if label and label.get('category') != 'other_labeled':
            return dict(out, cls=labels.SERVICE)
        try:
            sigs, complete = self.solana.signatures(address, max_pages=1)
        except Refused as exc:
            return dict(out, cls=labels.UNREAD, probe_error=str(exc)[:160])
        return dict(out, cls=labels.PERSONAL if complete else labels.HUB, signatures=len(sigs))

    def read(self, address, chain):
        if chain in EXPLORER_CHAINS:
            return explorer.history(self.net, address, chain)
        window = self.window_events(address, chain)
        if window is not None:
            return window
        seen = explorer.presence(self.net, address, chain)
        if seen['nonce'] == 0 and not seen['native'] and not seen['tokens']:
            return [], dict(chain_id=chain, address=address, source='node presence', status='NO_SPEND_NOTHING_HELD', presence=seen, note='Nonce 0 and nothing held now: no spend, and no listed token or native ever stayed. An unlisted token is not excluded.')
        return None, dict(chain_id=chain, address=address, source='node presence', status='WINDOW_SCAN_NEEDED', presence=seen)

    def bridge(self, e, chain, info):
        """Relay's route allows one call per 12 s, so it is asked only for its own addresses, the fun.xyz passage contract and unnamed hubs. CCTP needs no call beyond the transaction."""
        if not self.relay or info['cls'] not in STOP_CLASSES:
            return None
        name = ((info.get('label') or {}).get('name') or '')
        ask_relay = name.startswith('Relay') or name.startswith('VaultDepositooor') or (not name and info['cls'] == labels.HUB)
        return self.relay(e, chain, ask_relay)

    def edge(self, direction, depth, e, role, other, note=None):
        key = (direction, identity(e))
        if key in self.seen:
            return
        self.seen.add(key)
        label = other.get('label') or {}
        self.edges.append(dict(case=self.slug, direction=direction, depth=depth, role=role, other_cls=other.get('cls'), other_kind=other.get('kind'), other_nonce=other.get('nonce'), service=label.get('name'), category=label.get('category'), label_level=label.get('level'), label_source=label.get('source'), label_lineages=label.get('independent_lineages'), note=note, usd_rank=round(rough_usd(e), 2), **{k: e.get(k) for k in ('chain_id', 'block_number', 'block_hash', 'transaction_hash', 'log_index', 'kind', 'contract', 'token', 'decimals', 'raw_amount', 'timestamp', 'from', 'to', 'source', 'decoding', 'level', 'data_class', 'success', 'method')}))

    def walk(self, direction, seeds):
        queue = sorted(seeds, key=lambda n: n[3])
        visited = set()
        while queue:
            queue.sort(key=lambda n: n[3])
            address, chain, limit, depth = queue.pop(0)
            if (address, chain) in visited:
                continue
            visited.add((address, chain))
            if len(visited) > self.node_budget:
                self.stop(direction, address, chain, 'NODE_BUDGET', depth=depth, budget=self.node_budget)
                continue
            if (chain == SOL_CHAIN or not address.startswith('0x')) and not self.solana:
                self.stop(direction, address, chain, 'NON_EVM_READ_SEPARATELY', depth=depth)
                continue
            try:
                events, coverage = self.solana.history(address) if chain == SOL_CHAIN else self.read(address, chain)
            except Refused as exc:
                self.stop(direction, address, chain, 'READ_FAILED', detail=str(exc)[:200], depth=depth)
                continue
            self.nodes[(address, chain)] = dict(coverage, depth=depth)
            self.log(f"{direction} depth {depth} {address[:12]} chain {chain} {coverage['status']} rows {coverage.get('rows')}")
            if events is None:
                self.stop(direction, address, chain, 'WINDOW_SCAN_NEEDED', depth=depth, nonce=coverage['presence']['nonce'], native=coverage['presence']['native'], tokens=coverage['presence']['tokens'], limit=limit)
                continue
            if coverage['status'] == explorer.INCOMPLETE:
                self.stop(direction, address, chain, 'HISTORY_INCOMPLETE', parts={k: v.get('reason') for k, v in coverage.get('parts', {}).items() if v.get('status') != explorer.COMPLETE}, depth=depth)
            flows = [e for e in events if e.get('success', True) and int(e['raw_amount']) > 0 and e['from'] != e['to']]
            for e in flows:
                if not is_value(e):
                    self.ignored_tokens[(chain, e.get('contract'))] += 1
            flows = [e for e in flows if is_value(e)]
            parties = {e['from'] if e['to'] == address else e['to'] for e in flows}
            times = [e['timestamp'] for e in events if e.get('timestamp')]
            inflows = [e for e in flows if e['to'] == address and e.get('timestamp')]
            self.nodes[(address, chain)].update(value_counterparties=len(parties), first_event_at=min(times, default=None), last_event_at=max(times, default=None), first_value_in=min(((e['timestamp'], e['token'], e['raw_amount'], e['from'], e['transaction_hash']) for e in inflows), default=None))
            if depth > 0 and len(parties) >= labels.HIGH_PARTIES:
                self.stop(direction, address, chain, 'HUB_AT_READ', value_counterparties=len(parties), status=coverage['status'], depth=depth)
                continue
            queue += self.expand(direction, address, chain, limit, depth, flows)

    def expand(self, direction, address, chain, limit, depth, flows):
        inbound = direction == 'funding'
        side = [e for e in flows if (e['to'] == address if inbound else e['from'] == address) and (e['timestamp'] <= limit if inbound else e['timestamp'] >= limit)]
        dust = [e for e in side if rough_usd(e) < DUST_USD and e['token'] in ('USDC', 'USDT', 'USDC.e', 'pUSD', 'DAI') ]
        if dust:
            self.stop(direction, address, chain, 'DUST_NOT_FOLLOWED', rows=len(dust), usd=round(sum(rough_usd(e) for e in dust), 4), depth=depth)
        side = [e for e in side if e not in dust]
        if not side:
            self.stop(direction, address, chain, 'NO_FLOW_IN_WINDOW' if inbound else 'NO_LATER_OUTFLOW', depth=depth)
            return []
        swaps = self_swaps(flows, address)
        sent_by_self = {e['transaction_hash'] for e in flows if e['kind'] == 'native' and e['from'] == address}
        next_nodes = []
        for e in sorted(side, key=lambda x: -rough_usd(x)):
            other = e['from'] if inbound else e['to']
            if not other:
                continue
            if other in (ZERO, DEAD):
                self.edge(direction, depth, e, 'mint' if inbound else 'burn', dict(cls='ZERO_ADDRESS'))
                continue
            if inbound and (e['transaction_hash'] in swaps or e['transaction_hash'] in sent_by_self):
                self.edge(direction, depth, e, 'return_of_own_transaction', dict(cls='SELF'))
                continue
            if other in self.own:
                self.edge(direction, depth, e, 'internal_to_dossier', dict(cls='OWN'))
                continue
            info = self.cls(other, chain)
            hop = self.bridge(e, chain, info)
            if hop:
                self.edge(direction, depth, e, 'bridge_payout' if inbound else 'bridge_deposit', info, note=json.dumps(hop)[:1200])
                far, far_chain = (hop.get('sender'), hop.get('origin_chain')) if inbound else (hop.get('recipient'), hop.get('destination_chain'))
                if hop.get('proof') is True and far and far_chain and depth < self.max_depth:
                    far = far.lower() if far.startswith('0x') else far
                    if far not in self.own and far != address:
                        next_nodes.append((far, far_chain, e['timestamp'], depth + 1))
                elif hop.get('proof') is not True:
                    self.stop(direction, far or other, far_chain or chain, 'BRIDGE_HOP_NOT_PROVEN', tx=e['transaction_hash'], proof=hop.get('proof'), depth=depth)
                continue
            self.edge(direction, depth, e, 'transfer', info)
            if info['cls'] == labels.PERSONAL and depth < self.max_depth:
                for c2 in (ALL_EVM if depth <= 2 and other.startswith('0x') else (chain,)):
                    next_nodes.append((other, c2, e['timestamp'], depth + 1))
            elif info['cls'] == labels.PERSONAL:
                self.stop(direction, other, chain, 'DEPTH_BUDGET', tx=e['transaction_hash'], usd_rank=round(rough_usd(e), 2), depth=depth)
            else:
                label = info.get('label') or {}
                self.stop(direction, other, chain, 'SERVICE_OR_SHARED:' + info['cls'], name=label.get('name'), category=label.get('category'), nonce=info.get('nonce'), kind=info.get('kind'), tx=e['transaction_hash'], usd_rank=round(rough_usd(e), 2), token=e['token'], depth=depth)
        return next_nodes

    def seed_account(self, account):
        """Deposits and withdrawals from whole receipts. Each path becomes an edge at the receipt's level, then the walk starts behind it."""
        funding, cashout = [], []
        for side, items in (('funding', account['deposits']), ('cashout', account['withdrawals'])):
            for item in items:
                for path in item['paths']:
                    far = path.get('origin') if side == 'funding' else path.get('destination')
                    if far is None or path.get('unclear'):
                        self.stop(side, far or 'UNKNOWN', 137, 'AMBIGUOUS_PATH', tx=item['tx'], reason_detail=path.get('reason'), raw=str(path.get('raw')))
                        if far is None:
                            continue
                    token = TOKENS[137].get(path['token'], (None, 6))
                    e = dict(chain_id=137, block_number=item['block'], block_hash=item['block_hash'], transaction_hash=item['tx'], log_index=path['log_index'], kind='erc20', contract=path['token'], token=token[0], token_known=bool(token[0]), decimals=token[1], raw_amount=str(path['raw']), timestamp=item['at'], source='rpc:137', decoding=f"equal amount followed through logs {path['hops']} of one receipt", level=item['level'] or 'ONCHAIN_CONFIRMED', data_class='fresh', success=item['success'], method=None, **({'from': far, 'to': self.wallet} if side == 'funding' else {'from': self.wallet, 'to': far}))
                    info = self.cls(far, 137)
                    hop = self.bridge(e, 137, info)
                    if hop:
                        self.edge(side, 0, e, 'bridge_payout' if side == 'funding' else 'bridge_deposit', info, note=json.dumps(hop)[:1200])
                        next_address, next_chain = (hop.get('sender'), hop.get('origin_chain')) if side == 'funding' else (hop.get('recipient'), hop.get('destination_chain'))
                        if hop.get('proof') is True and next_address and next_chain:
                            next_address = next_address.lower() if next_address.startswith('0x') else next_address
                            self.own.add(next_address)
                            (funding if side == 'funding' else cashout).append((next_address, next_chain, item['at'], 1))
                        else:
                            self.stop(side, next_address or far, next_chain or 137, 'BRIDGE_HOP_NOT_PROVEN', tx=item['tx'], proof=hop.get('proof'), depth=0)
                        continue
                    self.edge(side, 0, e, 'deposit_path' if side == 'funding' else 'withdrawal_path', info)
                    if info['cls'] == labels.PERSONAL:
                        self.own.add(far)
                        for c2 in ALL_EVM:
                            (funding if side == 'funding' else cashout).append((far, c2, item['at'], 1))
                    else:
                        label = info.get('label') or {}
                        self.stop(side, far, 137, 'SERVICE_OR_SHARED:' + info['cls'], name=label.get('name'), category=label.get('category'), nonce=info.get('nonce'), tx=item['tx'], usd_rank=round(rough_usd(e), 2), depth=0)
        first_money = min((i['at'] for i in account['deposits']), default=account.get('first_activity') or 0)
        for owner in account['control_latest'].get('owners') or []:
            if owner != self.wallet:
                self.own.add(owner)
                for chain in ALL_EVM:
                    funding.append((owner, chain, int(time.time()), 0))
                    cashout.append((owner, chain, first_money - 30 * 86400, 0))  # a key can fund another account before any withdrawal
        return funding, cashout

    def run(self, account):
        funding, cashout = self.seed_account(account)
        self.walk('funding', funding)
        self.walk('cashout', cashout)
        return self.result()

    def result(self):
        return dict(case=self.slug, wallet=self.wallet, own=sorted(self.own), edges=self.edges, stops=self.stops, nodes=[dict(v, node=k[0], chain=k[1]) for k, v in self.nodes.items()], ignored_token_rows=sum(self.ignored_tokens.values()), ignored_token_contracts=len(self.ignored_tokens), classes=[dict(v) for v in self.classes.values()], ownership='OWNERSHIP_NOT_ESTABLISHED', collected_at=int(time.time()))
