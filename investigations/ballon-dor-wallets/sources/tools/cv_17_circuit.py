"""Contre-vérification : circuit 7XUJs -> Relay -> clé brace227 -> clé kraben006 -> 0x7e67 -> 0x3f3E, en wei exacts, depuis les fichiers déjà sauvegardés. Trois nœuds publics seulement pour recouper les soldes aux blocs (Ethereum). Sépare ce qui est démontré de la simple succession."""
import json, time, urllib.request
from collections import defaultdict
from pathlib import Path
OUT = Path(__file__).resolve().parent.parent / 'evidence/contre_verification_20261102'
d = json.load(open(OUT / 'transfert_brace_kraben_blockscout.json'))
idr = json.load(open(OUT / 'identifiant_relay_7xujs.json'))
vois = json.load(open(OUT / 'voisinage_transfert.json'))
sol = json.load(open(OUT / 'payeur_solana_7xujs.json'))
B, K = d['brace227_key'], d['kraben006_key']
U = lambda t: time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(t))
hist = lambda x: {int(h['block_number']): int(h['value']) for h in x['coin-balance-history']}
hb, hk = hist(B), hist(K)
tx = lambda x, pre: next(t for t in x['transactions'] if t['hash'].startswith(pre))
pay, tr = tx(B, '0xb17e1c'), tx(B, '0xd07bea')
out_k = tx(K, '0x1a39308b')
next_ = next(t for t in vois['next_hop_transactions'] if t['from']['hash'].lower().startswith('0x7e67'))
wei = lambda t: int(t['value'])
fee = lambda t: int(t.get('fee', {}).get('value') or 0)


def bal(node, addr, block):
    req = urllib.request.Request(node, data=json.dumps(dict(jsonrpc='2.0', id=1, method='eth_getBalance', params=[addr, hex(block)])).encode(), headers={'User-Agent': 'read-only', 'Content-Type': 'application/json'})
    try:
        time.sleep(.4)
        r = json.load(urllib.request.urlopen(req, timeout=30))
        return int(r['result'], 16) if 'result' in r else None
    except Exception:
        return None


b_before_pay = hb[22368521]
b_after_pay = hb[26119411]
b_after_tr = hb[26119420]
assert b_before_pay + wei(pay) == b_after_pay, 'solde clé brace avant et après le paiement Relay'
assert b_after_pay - wei(tr) - fee(tr) == b_after_tr, 'solde clé brace après le transfert'
assert not [h for h in hb if 22368521 < h < 26119411], 'mouvement inattendu entre avril 2025 et le paiement'
k_before = hk[26112297]
k_after_in = hk[26119420]
k_after_out = hk[26122383]
assert k_before + wei(tr) == k_after_in
assert k_after_in - wei(out_k) - fee(out_k) == k_after_out
node = 'https://eth.drpc.org'  # sert les vieux blocs, publicnode non
rpc_chk = {f'{n}_{blk}': bal(node, a, blk) for n, a, blk in (('brace', B['address'], 26119411), ('brace', B['address'], 26119420), ('kraben', K['address'], 26119420), ('kraben', K['address'], 26122383))}
share = lambda a, b: round(100 * a / b, 3)
res = dict(
    maillons=[
        dict(n=1, de='7XUJs (Solana)', vers='Relay Depository Solana', tx=idr['solana_sig'], utc=U(next(s['blockTime'] for s in sol['signatures'] if s['signature'] == idr['solana_sig'])), montant='4,62476 USDT plus 0,0298 de frais, débit 4,6545 USDT', preuve='signature Solana relue', niveau='DEMONTRE_SUR_LA_CHAINE'),
        dict(n=2, de='Relay Depository Solana', vers='solveur 0xadA5bb90 puis clé brace227', tx=pay['hash'], utc=pay['timestamp'][:19], eth=wei(pay) / 1e18, preuve=f"même identifiant {idr['calldata']} dans l'instruction Solana et le calldata du paiement ; enregistrement Relay concordant", niveau='DEMONTRE_PAR_IDENTIFIANT', limite="Le solveur paie sur son stock : c'est une équivalence de valeur du protocole, pas les mêmes jetons"),
        dict(n=3, de='clé brace227', vers='clé kraben006', tx=tr['hash'], utc=tr['timestamp'][:19], eth=wei(tr) / 1e18, preuve='transaction relue sur 2 nœuds publics, envoi simple, 21 000 gas, sans données', niveau='DEMONTRE_SUR_LA_CHAINE'),
        dict(n=4, de='clé kraben006', vers='0x7e67dF45', tx=out_k['hash'], utc=out_k['timestamp'][:19], eth=wei(out_k) / 1e18, preuve='transaction lue, Blockscout seul', niveau='TRANSACTION_DEMONTREE_CONTINUITE_PARTIELLE'),
        dict(n=5, de='0x7e67dF45', vers='0x3f3Ee0a9', tx=next_['hash'], utc=next_['timestamp'][:19], eth=wei(next_) / 1e18, preuve='0x7e67 : 1 entrée, 1 sortie listées, nonce 0 sur cette sortie', niveau='CONTINUITE_A_L_ADRESSE', limite="0x3f3Ee0a9 : étiquette Blockscout « ChangeNOW Dep », source unique, compteur dans etiquettes_blockscout.json"),
    ],
    solde_cle_brace=dict(avant_paiement_eth=b_before_pay / 1e18, apres_paiement_eth=b_after_pay / 1e18, transfert_eth=wei(tr) / 1e18, gas_eth=fee(tr) / 1e18, apres_transfert_eth=b_after_tr / 1e18, part_envoyee_pct=share(wei(tr), b_after_pay), part_gas_pct=share(fee(tr), b_after_pay), part_restante_pct=share(b_after_tr, b_after_pay), delai_s=108),
    continuite_maillon_3=dict(minimum_issu_du_paiement_eth=(wei(tr) - b_before_pay) / 1e18, minimum_pct_du_transfert=share(wei(tr) - b_before_pay, wei(tr)), maximum_ancien_solde_eth=b_before_pay / 1e18, raison="Le solde d'avant ne peut couvrir que ce montant. Aucune autre entrée entre les deux transactions : la comptabilité oblige le reste à venir du paiement."),
    solde_cle_kraben=dict(avant_reception_eth=k_before / 1e18, apres_reception_eth=k_after_in / 1e18, envoi_0x7e67_eth=wei(out_k) / 1e18, gas_eth=fee(out_k) / 1e18, apres_eth=k_after_out / 1e18, delai_s=int(time.mktime(time.strptime(out_k['timestamp'][:19], '%Y-%m-%dT%H:%M:%S')) - time.mktime(time.strptime(tr['timestamp'][:19], '%Y-%m-%dT%H:%M:%S')))),
    continuite_maillon_4=dict(minimum_force_eth=max(0, wei(out_k) + fee(out_k) - k_before) / 1e18, minimum_pct_de_la_reception=share(max(0, wei(out_k) + fee(out_k) - k_before), wei(tr)), raison="Seule cette part dépasse ce que la clé détenait déjà. Le reste dépend d'une convention de traçage (premier entré, dernier entré) : l'ETH est fongible, c'est de la succession, pas une preuve."),
    usd=dict(prix_eth_relay=float(idr['usd_out']) / float(idr['out_eth']), transfert_usd=round(wei(tr) / 1e18 * float(idr['usd_out']) / float(idr['out_eth']), 2), depots_brace=10032.98, depots_kraben=5689.47),
    recoupement_rpc=rpc_chk,
    recoupement_rpc_ok={k: (v == dict(brace_26119411=b_after_pay, brace_26119420=b_after_tr, kraben_26119420=k_after_in, kraben_26122383=k_after_out)[k]) if v is not None else None for k, v in rpc_chk.items()},
)
res['usd']['part_depots_brace_pct'] = share(res['usd']['transfert_usd'], 10032.98)
res['usd']['part_depots_kraben_pct'] = share(res['usd']['transfert_usd'], 5689.47)
# Gas consommé ensuite par la clé kraben : la réception était-elle nécessaire ?
res['gas_kraben_apres'] = dict(solde_fin_eth=int(K['balance_wei']) / 1e18, consomme_apres_envoi_eth=(k_after_out - int(K['balance_wei'])) / 1e18)
# Entrées USDT du payeur Solana avant le circuit, et ce qui lui reste
res['payeur'] = dict(signatures=len(sol['signatures']), solde_sol=sol['balance']['value'] / 1e9, usdt_restant=[a['account']['data']['parsed']['info']['tokenAmount']['uiAmount'] for a in sol['tokens']['value']], recu_usdt_06_2026=304.6996, envoye_usdt_06_2026=300.0)
# Tout lien direct et toutes les contreparties communes, sur l'historique complet Ethereum des deux clés
def parties(x):
    me, out = x['address'].lower(), defaultdict(set)
    for kind in ('transactions', 'internal-transactions', 'token-transfers'):
        for t in x[kind]:
            for side in ('from', 'to'):
                a = ((t.get(side) or {}).get('hash') or '').lower()
                if a and a != me:
                    out[a].add(t.get('hash') or t.get('transaction_hash'))
    return out
pb, pk = parties(B), parties(K)
res['direct_historique_complet'] = dict(k_vers_b=len(pb.get(K['address'].lower(), ())), b_vers_k=len(pk.get(B['address'].lower(), ())), hash=sorted(pk.get(B['address'].lower(), ())))
res['contreparties_communes'] = {a: dict(cle_brace=len(pb[a]), cle_kraben=len(pk[a])) for a in sorted(set(pb) & set(pk))}
res['histoires_completes'] = {n: {k: x[k + '_complete'] for k in ('transactions', 'internal-transactions', 'token-transfers', 'coin-balance-history')} for n, x in (('brace', B), ('kraben', K))}
(OUT / 'circuit_7xujs_brace_kraben.json').write_text(json.dumps(res, indent=1, ensure_ascii=False))
print(json.dumps({k: v for k, v in res.items() if k != 'maillons'}, indent=0, ensure_ascii=False))
for m in res['maillons']:
    print(m['n'], m['utc'], m['niveau'], m.get('eth'))
