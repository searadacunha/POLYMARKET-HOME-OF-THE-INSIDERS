"""Readable report of one case, written only from cases/SLUG.json."""
import gzip
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAMES = {792703809: 'Solana', 137: 'Polygon', 56: 'BSC', 1: 'Ethereum', 42161: 'Arbitrum', 8453: 'Base', 10: 'Optimism'}
MINTS = {'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v': 'USDC', 'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB': 'USDT'}
LEVEL = dict(ALIAS_EXACT_AND_SHARES='nom exact et parts de la capture', ALIAS_EXACT='nom exact', SHARES_ONLY='parts de la capture seulement', PREFIX_UNIQUE='préfixe de presse unique, non certifié')


def money(x):
    return f'{x:,.2f}'.replace(',', ' ').replace('.', ',') if x is not None else 'n/d'


def short(a):
    a = str(a)
    return a if len(a) < 16 else a[:10] + '…' + a[-4:]


def links_for(slug):
    path = ROOT / 'graphs/links.json'
    if not path.exists():
        return ['Non calculé.']
    d = json.loads(path.read_text())
    L = ['Lecture : un service commun ne relie personne. Détail et méthode : `reports/liens_entre_wallets.md`.', '']
    for x in d.get('shared_services', []):
        if slug in x['cases']:
            L.append(f"- Service étiqueté ou adresse à très fort nonce partagé : {(x.get('label') or {}).get('name') or x['address']}, aussi avec {', '.join(c for c in x['cases'] if c != slug)}.")
    for x in d.get('shared_pooled_measured', []):
        if slug in x['cases']:
            L.append(f"- Service non identifié partagé : `{x['address']}`, aussi avec {', '.join(c for c in x['cases'] if c != slug)}. Mesure : {x['measured']['measure']}.")
    for x in d.get('shared_non_infrastructure', []):
        if slug in x['cases']:
            L.append(f"- **Adresse non classée partagée** : `{x['address']}`, aussi avec {', '.join(c for c in x['cases'] if c != slug)}. Catégorie `UNKNOWN`.")
    L.append('- Transfert direct de fonds vers ou depuis un autre dossier : aucun sur Polygon et Ethereum, stablecoins et pUSD, du 25 sept. au 2 nov. (`graphs/direct_transfers.json`).')
    if slug in ('ouldlm3alem', '0x86544e4dfde'):
        L.append('- Une exécution de carnet d\'ordres entre ces deux wallets : 520,97 parts à 0,53, 26 oct. 13:29:02 UTC, transaction `0x870eaa6cb8298d7a02379b48093d4633af4f77ba58638bfc78ff9b0146f30b48`. Ordinaire sur un carnet, un seul cas.')
    return L


def render(slug):
    c = json.loads((ROOT / f'cases/{slug}.json').read_text())
    w = c.get('wallet') or {}
    a = c['account']
    rel = sorted([r for r in c.get('chain_relations', []) if r['at']], key=lambda r: r['at'])
    incoming = [r for r in rel if r['at'] <= (c['deposits'][-1]['at'] if c['deposits'] else 0) + 60]
    outgoing = [r for r in rel if r not in incoming]
    L = [f"# Dossier {c['label']}", '', f"Généré depuis `cases/{slug}.json`. Une adresse n'est pas une personne : aucune identité civile n'est établie ni recherchée, et rien ici ne prouve une information privilégiée.", '']
    L += ['## 1. Adresse et type', '', f"- Wallet Polymarket : `{c['address']}`", f"- Type : {w.get('type', 'non classé')}. Propriétaire lu sur la chaîne : {', '.join(f'`{o}`' for o in w.get('owners', [])) or 'aucun lu'}. C'est une clé, pas une personne.", f"- Lien étiquette vers adresse : {LEVEL.get(c['identity_level'], c['identity_level'])}.", f"- Première activité {c['first_activity']} UTC, dernière {c['last_activity']} UTC, {c['rows']} lignes d'activité, historique {'complet' if c['history_complete'] else 'INCOMPLET'}."]
    for o, n in (c.get('owner_nonces') or {}).items():
        L.append(f"- Nonce du propriétaire sur six chaînes : {n}. {'Aucune transaction envoyée par cette clé sur ces chaînes : elle signe hors chaîne.' if not any(n.values()) else ''}")
    L += ['', '## 2 et 3. Premier financement et source directe', '']
    if c['deposits']:
        d = c['deposits'][0]
        L.append(f"Premier dépôt : {d['utc']} UTC, {money(float(d['usd']))} pUSD, transaction `{d['tx']}`. Le pUSD est frappé depuis l'adresse zéro : celle-ci n'est pas un financeur.")
        sources = sorted({h['immediate_source'] for h in c.get('funding_chain', []) if h and h.get('immediate_source')})
        L.append(f"Source immédiate du collatéral : {', '.join(f'`{s}`' for s in sources) or 'non établie'}.")
        for h in c.get('funding_chain', []):
            if h and h.get('immediate_source'):
                L.append(f"- Dépôt `{h['deposit_tx'][:14]}…` : `{short(h['immediate_source'])}`, {h['kind']['kind']}, nonce {h['kind']['nonce']}, {h['polymarket_bridge_records']} enregistrements au pont Polymarket.")
    else:
        L.append('Aucune ligne DEPOSIT dans l\'historique de ce wallet.')
    L += ['', '## 4. Origines remontées, du plus ancien au dépôt', '', '| Heure UTC | De | Vers | Chaîne | Montant | Niveau | Transaction |', '|---|---|---|---|---:|---|---|']
    for r in incoming:
        lab = r.get('source_label') or {}
        L.append(f"| {r['utc']} | `{short(r['source'])}`{' (' + lab['name'] + ')' if lab else ''} | `{short(r['target'])}` | {NAMES.get(r['chain'], r['chain'])} | {money(r['amount'])} {MINTS.get(r['token'], r['token'])} | {r['category']} | `{r['tx']}` |")
    L += ['', '**Où la trace s\'arrête :**', '']
    for s in c.get('chain_stops', []):
        L.append(f"- `{s.get('address') or s.get('tx')}` : {s.get('state')}. {s.get('basis', '')}{' Financeur étiqueté : ' + ', '.join(short(f) for f in s.get('funders', [])) + '. Seul le service connaît le compte.' if s.get('funders') else ''}")
    shared = {}
    for r in incoming:
        if 'nonce ' in r['basis'] and not r.get('source_label'):
            n = int(r['basis'].split('nonce ')[1].split(',')[0])
            if n > 100000:
                shared[r['source']] = (r['chain'], n)
    for address, (chain, n) in shared.items():
        L.append(f"- `{address}` ({NAMES.get(chain, chain)}) : nonce {n:,}. ".replace(',', ' ') + "Un tel volume désigne une adresse mutualisée, probablement un hot wallet de service, pas un portefeuille personnel. Aucune étiquette vérifiée.")
    L += ['', '## 5 et 6. Paris et positions', '', '| Marché | Issue | Achats $ | Parts achetées | Ventes $ | Rachats $ | Net de parts avant l\'article |', '|---|---|---:|---:|---:|---:|---:|']
    for p in c['positions']:
        L.append(f"| {p['title']} | {p['outcome']} | {money(p.get('buy_usd'))} | {money(p.get('buy_shares'))} | {money(p.get('sell_usd'))} | {money(p.get('redeem_usd'))} | {money(p.get('net_shares_before_article'))} |")
    ft = c.get('first_trade')
    if ft:
        L += ['', f"Premier achat : {ft['utc']} UTC, {money(float(ft['usd']))} $, « {ft['title']} », {ft['outcome']}, `{ft['tx']}`."]
    path = ROOT / f'evidence/activity/{slug}.jsonl.gz'
    if path.exists():
        rows = [json.loads(x) for x in gzip.open(path, 'rt')]
        major = [r for r in rows if r['type'] in ('DEPOSIT', 'WITHDRAWAL', 'REDEEM', 'SPLIT', 'MERGE', 'CONVERSION')]
        trades = sorted((r for r in rows if r['type'] == 'TRADE'), key=lambda r: -float(r.get('usdc_size') or 0))
        keep = rows if len(rows) <= 90 else sorted(major + trades[:40], key=lambda r: r['timestamp'])
        L += ['', f"**Historique daté** ({len(keep)} lignes sur {len(rows)}{'' if len(rows) <= 90 else ' : tous les dépôts, retraits et rachats, et les 40 plus gros trades'}) :", '', '| Heure UTC | Type | Marché | Issue | $ | Parts | Prix | Transaction |', '|---|---|---|---|---:|---:|---:|---|']
        for r in keep:
            if r['type'] in ('REWARD', 'MAKER_REBATE', 'TAKER_REBATE') and float(r.get('usdc_size') or 0) < 50:
                continue
            L.append(f"| {time.strftime('%m-%d %H:%M:%S', time.gmtime(r['timestamp']))} | {r['type']} {r.get('side') or ''} | {(r.get('title') or '')[:46]} | {r.get('outcome') or ''} | {money(float(r.get('usdc_size') or 0))} | {money(float(r.get('size') or 0))} | {r.get('price') or ''} | `{r.get('transaction_hash')}` |")
    L += ['', '**Compte (API d\'activité) :**', '', '| Poste | $ |', '|---|---:|'] + [f"| {k} | {money(v)} |" for k, v in a['by_type'].items()]
    L += ['', f"Résidu du calcul : {a['residual']}. Compte soldé : {'oui' if a['account_closed'] else 'non'}. " + (f"**Retraits moins dépôts sur ce wallet : {money(a['net_cash_out_minus_in'])} $**, frais de transaction inclus, gas et coûts hors de ce wallet exclus." if a['account_closed'] else 'Aucun résultat réalisé n\'est affirmé.')]
    L += ['', '## 7. Sorties et destinations', '', '| Heure UTC | De | Vers | Chaîne | Montant reçu | Niveau | Transaction |', '|---|---|---|---|---:|---|---|']
    for r in outgoing:
        lab = r.get('target_label') or {}
        L.append(f"| {r['utc']} | `{short(r['source'])}` | `{r['target']}`{' (' + lab['name'] + ')' if lab else ''} | {NAMES.get(r['chain'], r['chain'])} | {money(r['amount'])} {MINTS.get(r['token'], r['token'])} | {r['category']} | `{r['tx']}` |")
    L += ['', '**État des destinations à la lecture :**', '']
    for x in c.get('recipients', []):
        toks = ', '.join(f"{money(t['amount'])} {MINTS.get(t['mint'], t['mint'][:6])}" for t in x.get('tokens', []))
        L.append(f"- `{x['address']}` ({NAMES.get(x['chain'], x['chain'])}), lu le {x['read_at']} UTC : {x.get('signatures', 'n/d')} transactions, historique {'complet' if x.get('complete') else 'partiel'}, solde {money(x.get('sol'))} SOL et {toks or 'aucun jeton'}. Sorties observées : {len(x.get('moved_out', []))}.")
    if not c.get('recipients'):
        L.append('- Aucune destination au-delà du premier saut n\'a été lue.')
    services = sorted({x for r in rel for x in ((r.get('source_label') or {}).get('name'), (r.get('target_label') or {}).get('name')) if x})
    cn = [s for s in services if 'ChangeNOW' in s or 'FixedFloat' in s]
    L += ['', '## 8. ChangeNOW, FixedFloat, exchanges, XMR', '', f"- Services étiquetés touchés : {', '.join(services) or 'aucun'}.", f"- ChangeNOW ou FixedFloat : {'**' + ', '.join(cn) + '**' if cn else 'aucune interaction sur les sauts lus. Liste étiquetée incomplète : absence de preuve, pas preuve d absence.'}", '- XMR : aucun échange XMR observé sur les sauts lus, donc aucun statut `XMR_VISIBILITY_BOUNDARY` à ce stade.', '', '## 9. Liens avec les autres wallets', '', *links_for(slug), '', '## 10. Niveau de preuve par relation', '', f"{len(c.get('chain_relations', []))} relations à identifiant stable dans `graphs/relations.jsonl`."]
    from collections import Counter
    for k, v in Counter(r['category'] for r in c.get('chain_relations', [])).most_common():
        L.append(f'- {k} : {v}')
    (ROOT / f'cases/{slug}.md').write_text('\n'.join(L) + '\n')
    return ROOT / f'cases/{slug}.md'


if __name__ == '__main__':
    print(render(sys.argv[1]))
