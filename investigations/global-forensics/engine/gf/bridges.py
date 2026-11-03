"""A cross-chain hop rests on an identifier read on both chains, or on a message the destination contract itself verified. Never on amounts or dates.

Relay: the 32-byte id at the end of the payout's calldata (or its Solana memo) must also be in the deposit's log or calldata; the API record only says
where to look, and retires on 2026-11-24. CCTP: the mint's calldata holds the attested message, with source domain, nonce and original sender.
No proof, no walk: the hop stays listed with proof False or None, and the tracer writes a stop.
"""
import json

from .events import SOLANA
from .net import RPC, Refused

RELAY = 'https://api.relay.link/requests/v2'
CCTP_DOMAIN = {0: 1, 2: 10, 3: 42161, 6: 8453, 7: 137, 5: SOLANA}
CCTP_MINT = '0x57ecfd28'


def relay_record(net, tx, budget=None):
    if budget is not None and budget['left'] <= 0:
        return None
    before = net.calls
    body, _ = net.get(RELAY, dict(hash=tx), pause=12, accept=(400, 404))
    if budget is not None:
        budget['left'] -= net.calls - before
    found = body.get('requests') or [] if isinstance(body, dict) else []
    if not found:
        return None
    q = found[0]
    data, meta = q.get('data') or {}, (q.get('data') or {}).get('metadata') or {}
    cin, cout = meta.get('currencyIn') or {}, meta.get('currencyOut') or {}
    return dict(protocol='Relay', id=q.get('id'), status=q.get('status'), sender=q.get('user'), recipient=q.get('recipient'), in_txs=[(t.get('chainId'), t.get('hash')) for t in data.get('inTxs') or []], out_txs=[(t.get('chainId'), t.get('hash')) for t in data.get('outTxs') or []], in_symbol=(cin.get('currency') or {}).get('symbol'), in_amount=cin.get('amountFormatted'), origin_chain=(cin.get('currency') or {}).get('chainId'), out_symbol=(cout.get('currency') or {}).get('symbol'), out_amount=cout.get('amountFormatted'), destination_chain=(cout.get('currency') or {}).get('chainId'))


def relay_proof(net, rec, solana=None):
    """True: same id read on both chains. False: both read, id absent. None: a side cannot be read here (a same-chain swap has no payout hash)."""
    if not rec.get('in_txs') or not rec.get('out_txs'):
        return None
    out_chain, out_tx = rec['out_txs'][0]
    in_chain, in_tx = rec['in_txs'][0]
    if not out_tx or not in_tx:
        return None
    try:
        if out_chain == SOLANA:
            if not solana:
                return None
            token = solana.memo(out_tx)
        else:
            token = net.rpc('eth_getTransactionByHash', [out_tx], out_chain)[0]['input'][-64:].lower()
        if not token or len(token) < 64:
            return None
        if in_chain == SOLANA:
            if not solana:
                return None
            blobs = solana.instruction_blobs(in_tx)
        else:
            tx = net.rpc('eth_getTransactionByHash', [in_tx], in_chain)[0]
            receipt = net.rpc('eth_getTransactionReceipt', [in_tx], in_chain)[0]
            blobs = [tx['input'].lower()] + [(l['data'] + ''.join(l['topics'])).lower() for l in receipt['logs']]
        return any(token in b for b in blobs)
    except (Refused, KeyError, TypeError, ValueError):
        return None


def cctp_message(transaction):
    """Source domain, nonce and original burner from a mint's calldata. v1 and v2 lay the message out differently."""
    data = transaction.get('input') or ''
    if not data.startswith(CCTP_MINT):
        return None
    body = bytes.fromhex(data[10:])
    offset = int.from_bytes(body[:32], 'big')
    length = int.from_bytes(body[offset:offset + 32], 'big')
    msg = body[offset + 32:offset + 32 + length]
    version = int.from_bytes(msg[:4], 'big')
    src, dst = int.from_bytes(msg[4:8], 'big'), int.from_bytes(msg[8:12], 'big')
    if version == 0:
        nonce, cursor, inner = msg[12:20].hex(), 20, 96 + 4 + 32 + 32 + 32
    elif version == 1:
        nonce, cursor, inner = msg[12:44].hex(), 44, 96 + 8 + 4 + 32 + 32 + 32
    else:
        return None
    sender = msg[cursor + inner:cursor + inner + 32]
    recipient = msg[cursor + inner - 64:cursor + inner - 32]
    amount = msg[cursor + inner - 32:cursor + inner]
    return dict(protocol='CCTP', version=version, source_domain=src, destination_domain=dst, origin_chain=CCTP_DOMAIN.get(src), nonce=nonce, sender='0x' + sender[-20:].hex(), recipient='0x' + recipient[-20:].hex(), raw=int.from_bytes(amount, 'big'), proof=True, basis='Attested message verified by the destination contract, read from calldata.')


RELAY_DEPOSITORY = '0x4cd00e387622c35bddb9b4c962c136462338bc31'
ORIGIN_CHAINS = (1, 42161, 8453, 10, 56, 137)
SECONDS_PER_BLOCK = {1: 12.0, 42161: .25, 8453: 2.0, 10: 2.0, 56: .75, 137: 2.0}


def block_near(net, chain, moment, tolerance_s=300):
    """A block within minutes of a time, by secant steps, since block rates drift."""
    high = int(net.rpc('eth_blockNumber', [], chain, cache=False)[0], 16)
    guess, rate = high, SECONDS_PER_BLOCK[chain]
    at = int(net.rpc('eth_getBlockByNumber', [hex(guess), False], chain)[0]['timestamp'], 16)
    for _ in range(6):
        if abs(at - moment) <= tolerance_s:
            break
        other = max(1, min(high, guess - int((at - moment) / rate)))
        other_at = int(net.rpc('eth_getBlockByNumber', [hex(other), False], chain)[0]['timestamp'], 16)
        if other != guess and other_at != at:
            rate = abs((at - other_at) / (guess - other)) or rate
        guess, at = other, other_at
    return guess, rate


def relay_onchain_origin(net, payout_tx, at, chain=137):
    """The id at the end of a payout's calldata, found in the Relay Depository's log on the origin chain. Public chain data on both sides, no API.

    Returns a hop with proof True, or None if no origin chain read here holds that id: Solana and unread chains stay open for the API record.
    """
    transaction = net.rpc('eth_getTransactionByHash', [payout_tx], chain)[0]
    token = (transaction or {}).get('input', '')[-64:].lower()
    if len(token) != 64 or int(token, 16) < 2 ** 128:
        return None
    for origin in ORIGIN_CHAINS:
        try:
            block, rate = block_near(net, origin, at)
            span_back, span_on = int(3600 / rate), int(600 / rate)
            step = 2000 if origin != 42161 else 20000
            for low in range(max(1, block - span_back), block + span_on, step):
                logs = net.rpc('eth_getLogs', [dict(fromBlock=hex(low), toBlock=hex(min(low + step - 1, block + span_on)), address=RELAY_DEPOSITORY)], origin)[0]
                for log in logs:
                    if token in log['data'][2:].lower():
                        data = log['data'][2:]
                        sender = '0x' + data[24:64] if len(data) >= 64 else None
                        return dict(protocol='Relay', id='0x' + token, origin_chain=origin, destination_chain=chain, in_txs=[(origin, log['transactionHash'])], out_txs=[(chain, payout_tx)], sender=sender, recipient=None, in_amount=None, proof=True, basis='Same id in the calldata of the payout and in the Relay Depository log on the origin chain, read from nodes.')
        except Refused:
            continue
    return None


class Bridges:
    """What the tracer calls on a flow touching a shared address. Returns a hop, or None when no protocol record exists."""

    def __init__(self, net, relay_budget=250, solana=None, onchain_first=True, solvers=('0xf70da97812cb96acdf810712aa562db8dfa3dbef', '0xa67d7eb4dc68fa6ce8e34ef8cadaf075b9893fbb', '0x56c262027e0de4aea31d2489529cb25d23e58a8b')):
        self.net, self.budget, self.solana, self.cache = net, dict(left=relay_budget), solana, {}
        self.onchain_first, self.solvers = onchain_first, set(solvers)

    def __call__(self, e, chain, ask_relay=True):
        tx = e['transaction_hash']
        key = (chain, tx, ask_relay)
        if key in self.cache:
            return self.cache[key]
        hop = None
        try:
            transaction = self.net.rpc('eth_getTransactionByHash', [tx], chain)[0] if chain in RPC else None  # no EVM read on Solana: the Relay record below still works by signature
            hop = cctp_message(transaction) if transaction else None
            if not hop and ask_relay and e.get('to') and e.get('timestamp'):
                hop = relay_onchain_origin(self.net, tx, e['timestamp'], chain) if self.onchain_first and e.get('from') in self.solvers else None
            if not hop and ask_relay:
                rec = relay_record(self.net, tx, self.budget)
                if rec and rec.get('sender') and (rec.get('recipient') or rec.get('out_txs')):
                    rec['proof'] = relay_proof(self.net, rec, self.solana)
                    hop = rec
        except Refused:
            hop = None
        self.cache[key] = hop
        return hop
