"""Contre-vérification sans réseau : le paiement ETH et le dépôt Solana portent-ils le même identifiant dans leurs données brutes ? Relit les fichiers déjà sauvegardés."""
import json
from pathlib import Path
OUT = Path(__file__).resolve().parent.parent / 'evidence/contre_verification_20261102'
A = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'


def b58(s):
    n = 0
    for c in s:
        n = n * 58 + A.index(c)
    return n.to_bytes((n.bit_length() + 7) // 8, 'big').hex()


assert b58('2g') == '61'  # valeur de référence du format base58
d = json.load(open(OUT / 'transfert_brace_kraben_blockscout.json'))
pay = next(t for t in d['brace227_key']['transactions'] if t['hash'].startswith('0xb17e1c'))
sol = json.load(open(OUT / 'payeur_solana_7xujs.json'))
tx = next(t for s, t in sol['txs'].items() if s.startswith('3XaPp5kR'))
rel = json.load(open(OUT / 'voisinage_transfert.json'))['relay_0xb17e1c4627']['requests'][0]
calldata = pay['raw_input'][2:]
print('calldata paiement', calldata, 'id Relay', rel['id'])
hits = []
for loc, ins in [('top', i) for i in tx['transaction']['message']['instructions']] + [('inner', i) for g in tx['meta'].get('innerInstructions', []) for i in g['instructions']]:
    if 'data' in ins:
        h = b58(ins['data']) if ins['data'] else ''
        print(loc, ins.get('programId', '')[:12], len(h) // 2, 'octets', h[:120], 'calldata_dedans', calldata in h, 'id_dedans', rel['id'][2:] in h)
        if calldata in h or rel['id'][2:] in h:
            hits.append(dict(loc=loc, program=ins.get('programId'), hex=h))
res = dict(payment_tx=pay['hash'], calldata=pay['raw_input'], relay_request_id=rel['id'], solana_sig=[s for s in sol['txs'] if s.startswith('3XaPp5kR')][0], same_id_in_solana_instruction=bool(hits), hits=hits, relay_user=rel['user'], relay_recipient=rel['recipient'], in_usdt=rel['data']['metadata']['currencyIn']['amountFormatted'], out_eth=rel['data']['metadata']['currencyOut']['amountFormatted'], usd_in=rel['data']['metadata']['currencyIn']['amountUsd'], usd_out=rel['data']['metadata']['currencyOut']['amountUsd'])
(OUT / 'identifiant_relay_7xujs.json').write_text(json.dumps(res, indent=1))
print(json.dumps({k: v for k, v in res.items() if k != 'hits'}, indent=0))
print('logs Solana', [l for l in tx['meta'].get('logMessages', []) if 'Memo' in l or 'memo' in l][:4])
