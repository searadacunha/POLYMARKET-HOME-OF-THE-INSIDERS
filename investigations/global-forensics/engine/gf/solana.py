"""Public Solana reads, through the same store. A failed read raises. An owner's signatures miss inflows to its existing token accounts, so token accounts are read too.

The owner is the party in a balance change, not the token account. A counterparty is read from the balance deltas of one transaction: when several
parties move the same mint, the largest opposite move is reported and marked `ambiguous`, since a transaction can carry several legs. publicnode has
answered 0 signatures for funded addresses, so it is not used.
"""
import base64
import json

from .events import ONCHAIN, SOLANA, FRESH, LISTED
from .net import Refused

ENDPOINTS = ('https://api.mainnet-beta.solana.com', 'https://solana-mainnet.gateway.tatum.io')
USDC, USDT, WSOL = 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v', 'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB', 'So11111111111111111111111111111111111111112'
MINTS = {USDC: ('USDC', 6), USDT: ('USDT', 6), WSOL: ('WSOL', 9)}
PAGE = 1000
ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'


def b58_to_hex(text):
    n = 0
    for ch in text:
        n = n * 58 + ALPHABET.index(ch)
    return n.to_bytes((n.bit_length() + 7) // 8, 'big').hex()


class Solana:
    def __init__(self, net):
        self.net = net

    def rpc(self, method, params):
        """Same on-disk store as EVM reads. A null answer from one endpoint hands over to the next."""
        errors = []
        for endpoint in ENDPOINTS:
            try:
                value, _ = self.net.post_json(endpoint, method, params)
            except Refused as exc:
                errors.append(str(exc)[:120])
                continue
            if value is not None:
                return value
            errors.append(f'{endpoint}: null')
        raise Refused(f'solana {method}: ' + '; '.join(errors))

    def signatures(self, address, max_pages=5):
        out, before = [], None
        for _ in range(max_pages):
            options = dict(limit=PAGE)
            if before:
                options['before'] = before
            page = self.rpc('getSignaturesForAddress', [address, options])
            out += page
            if len(page) < PAGE:
                return out, True
            before = page[-1]['signature']
        return out, False

    def transaction(self, signature):
        return self.rpc('getTransaction', [signature, dict(encoding='jsonParsed', maxSupportedTransactionVersion=0)])

    def memo(self, signature):
        """The id Relay writes in a payout's memo, as lowercase hex without a prefix. None when the transaction has no memo."""
        for ins in self.transaction(signature)['transaction']['message']['instructions']:
            if ins.get('program') == 'spl-memo':
                text = ins.get('parsed')
                return (text if isinstance(text, str) else json.dumps(text or '')).lower().replace('0x', '')
        return None

    def instruction_blobs(self, signature):
        tx = self.transaction(signature)
        blobs = [b58_to_hex(i['data']) for i in tx['transaction']['message']['instructions'] if i.get('data')]
        blobs += [b58_to_hex(i['data']) for inner in tx['meta'].get('innerInstructions') or [] for i in inner['instructions'] if i.get('data')]
        return blobs

    @staticmethod
    def keys(tx):
        keys = [k['pubkey'] if isinstance(k, dict) else k for k in tx['transaction']['message']['accountKeys']]
        loaded = tx['meta'].get('loadedAddresses') or {}
        return keys + loaded.get('writable', []) + loaded.get('readonly', [])

    @staticmethod
    def signers(tx):
        return [k['pubkey'] for k in tx['transaction']['message']['accountKeys'] if isinstance(k, dict) and k.get('signer')]

    @classmethod
    def moves(cls, tx):
        meta = tx['meta']
        before = {(b['accountIndex'], b['mint']): b for b in meta.get('preTokenBalances') or []}
        after = {(b['accountIndex'], b['mint']): b for b in meta.get('postTokenBalances') or []}
        out = []
        for key in set(before) | set(after):
            a, b = before.get(key), after.get(key)
            raw = int((b or {}).get('uiTokenAmount', {}).get('amount', 0)) - int((a or {}).get('uiTokenAmount', {}).get('amount', 0))
            if raw:
                out.append(dict(owner=(b or a).get('owner'), mint=key[1], raw=raw, decimals=(a or b)['uiTokenAmount']['decimals']))
        for k, x, y in zip(cls.keys(tx), meta['preBalances'], meta['postBalances']):
            if y != x:
                out.append(dict(owner=k, mint='SOL', raw=y - x, decimals=9))
        return out

    def history(self, address, max_tx=400):
        """(events, coverage). Reads the owner, then its token accounts. Everything past max_tx stays unread and the coverage says so."""
        sigs, complete = self.signatures(address)
        accounts = set()
        for s in sigs[:max_tx]:
            if s.get('err'):
                continue
            tx = self.transaction(s['signature'])
            keys = self.keys(tx)
            for b in (tx['meta'].get('preTokenBalances') or []) + (tx['meta'].get('postTokenBalances') or []):
                if b.get('owner') == address and b.get('accountIndex') is not None:
                    accounts.add(keys[b['accountIndex']])
        known = {s['signature'] for s in sigs}
        for account in sorted(accounts):
            more, done = self.signatures(account, max_pages=2)
            complete = complete and done
            sigs += [s for s in more if s['signature'] not in known]
            known |= {s['signature'] for s in more}
        sigs = sorted(sigs, key=lambda s: -(s.get('blockTime') or 0))
        events = []
        for s in sigs[:max_tx]:
            if s.get('err'):
                continue
            tx = self.transaction(s['signature'])
            moves = self.moves(tx)
            signed = self.signers(tx)
            for m in moves:
                if m['owner'] != address or (m['mint'] not in MINTS and m['mint'] != 'SOL'):
                    continue
                token, decimals = ('SOL', 9) if m['mint'] == 'SOL' else MINTS[m['mint']]
                others = [o for o in moves if o['mint'] == m['mint'] and o['owner'] != address and (o['raw'] > 0) != (m['raw'] > 0)]
                counter = max(others, key=lambda o: abs(o['raw']))['owner'] if others else None
                if not counter:
                    continue
                source, target = (counter, address) if m['raw'] > 0 else (address, counter)
                events.append({'chain_id': SOLANA, 'block_number': s.get('slot'), 'block_hash': None, 'transaction_hash': s['signature'], 'log_index': None, 'kind': 'spl' if token != 'SOL' else 'native', 'contract': m['mint'] if token != 'SOL' else None, 'token': token, 'token_known': True, 'decimals': decimals, 'raw_amount': str(abs(m['raw'])), 'timestamp': s.get('blockTime'), 'from': source, 'to': target, 'success': True, 'method': None, 'ambiguous': len(others) > 1, 'self_initiated': address in signed, 'source': 'solana-rpc', 'decoding': 'balance deltas of one transaction', 'level': LISTED, 'data_class': FRESH})
        return events, dict(chain_id=SOLANA, address=address, source='solana-rpc', status='COMPLETE' if complete and len(sigs) <= max_tx else 'INCOMPLETE', signatures=len(sigs), rows=len(events), parts=dict(all=dict(status='COMPLETE' if complete and len(sigs) <= max_tx else 'INCOMPLETE', reason=None if complete else 'signature pages ran out')))

    def owner_label_hint(self, address):
        """Read-only account info: owner program and whether it is executable. Says what kind of account it is, not whose."""
        return self.rpc('getAccountInfo', [address, dict(encoding='base64')])


__all__ = ['Solana', 'b58_to_hex', 'base64', 'ONCHAIN']
