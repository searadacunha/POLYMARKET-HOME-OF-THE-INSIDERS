"""Writes the five reports from data/ and state/. Every table is computed; the sentences in narrative.py are hand-written and checked by tests/test_claims.py."""
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import evm
import net
import narrative as N
import walk

ROOT = net.ROOT
STATE = ROOT / 'state'
INV = walk.INV
SOLANA = walk.SOLANA
CHAIN = {**evm.CHAIN, SOLANA: 'solana'}
ORDER = ['thin', 'vidente', 'cookedrice', 'wen', '0x86544e4dfde', 'brace227', 'walletwallet8424', 'zoomman17', 'kraben006', 'ouldlm3alem', '0xdd97e6']
FUNDER_EVENTS = ('transfer_in', 'transfer_into_bridge_address', 'candidate_inflow')
NOTE = "Une adresse n'est pas une personne. Ces comptes sont des sujets d'investigation : rien ici ne démontre ni un propriétaire commun, ni un délit d'initié."


def usd(x):
    return f'{float(x):,.2f}'.replace(',', ' ').replace('.', ',')


def short(a):
    if not a:
        return ''
    return f'`{a[:10]}…{a[-4:]}`' if len(a) > 16 else f'`{a}`'


def rows(name):
    return list(csv.DictReader((ROOT / f'data/{name}.csv').open()))


def table(head, lines):
    out = ['| ' + ' | '.join(head) + ' |', '|' + '---|' * len(head)]
    out += ['| ' + ' | '.join(str(x) for x in line) + ' |' for line in lines]
    return '\n'.join(out)


def load():
    cases = {c['slug']: c for c in (json.loads(p.read_text()) for p in sorted((INV / 'cases').glob('*.json')))}
    walks = {p.stem[5:]: json.loads(p.read_text()) for p in sorted(STATE.glob('walk_*.json'))}
    recon = {r['case']: r for r in json.loads((STATE / 'reconcile.json').read_text())}
    pairs = json.loads((STATE / 'pairs.json').read_text())
    bridges = json.loads((STATE / 'bridges.json').read_text())
    rates = json.loads((STATE / 'compare_rates.json').read_text()) if (STATE / 'compare_rates.json').exists() else None
    verify = json.loads((STATE / 'verify.json').read_text()) if (STATE / 'verify.json').exists() else {}
    tests = json.loads((STATE / 'tests.json').read_text()) if (STATE / 'tests.json').exists() else []
    return cases, walks, recon, pairs, bridges, rates, verify, tests


def origin_table(slug, fund):
    """Dollars of each deposit allocated to the last public source of its branch."""
    by = defaultdict(lambda: dict(usd=0.0, service='', cat='', cls='', txs=set(), level='', chain=''))
    special = dict(return_of_own_swap="Échange fait par l'adresse elle-même (voir le récit)", own_withdrawal_returned='Ses propres retraits, redéposés')
    for r in fund:
        if r['case'] != slug or r['event'] == 'candidate_inflow' or (r['event'] not in FUNDER_EVENTS and r['event'] not in special):
            continue
        if r['event'] not in special and r['source_class'] == 'PERSONAL_SIZED':
            continue
        key = (r['event'], r['chain']) if r['event'] in special else (r['source'], r['chain'])
        amount = float(r['fifo_allocated'] or r['amount'] or 0)
        b = by[key]
        b['usd'] += amount
        b['service'] = special.get(r['event'], r['service'])
        b['cat'] = r['service_category']
        b['cls'] = r['source_class']
        b['level'] = r['evidence']
        b['chain'] = r['chain']
        b['txs'].add(r['tx'])
    lines = []
    for (addr, _), b in sorted(by.items(), key=lambda kv: -kv[1]['usd']):
        lines.append([short(addr) if addr.startswith(('0x', 'B', 'G', '5', '7', '9')) and len(addr) > 30 else '—', b['chain'], b['service'] or f"non étiquetée ({b['cls']})", b['cat'] or '—', usd(b['usd']), len(b['txs'])])
    return table(['Dernière source publique', 'Chaîne', 'Service', 'Catégorie', 'Dollars alloués', 'Tx'], lines) if lines else 'Aucune source retenue : voir le récit.'


def path_table(slug, rs, limit=40):
    lines = []
    seen = set()
    for r in rs:
        if r['case'] != slug:
            continue
        k = (r['tx'], r['source'], r['target'], r['event'])
        if k in seen or not r['tx']:
            continue
        seen.add(k)
        amount = float(r['amount'] or 0)
        lines.append((r['utc'] or r['anchor_utc'], [r['utc'] or r['anchor_utc'], r['chain'], r['asset'], usd(amount) if amount >= 1 else f'{amount:.6f}', short(r['source']), short(r['target']), r['event'], r['service'][:44], r['evidence'], f"`{r['tx']}`"]))
    lines.sort(key=lambda x: x[0])
    shown = [x[1] for x in lines[:limit]]
    extra = f'\n\n{len(lines) - limit} autres lignes dans le CSV.' if len(lines) > limit else ''
    return table(['UTC', 'Chaîne', 'Actif', 'Montant', 'De', 'Vers', 'Événement', 'Service', 'Preuve', 'Transaction'], shown) + extra


def holdings_table(w):
    lines = []
    for h in w['holdings']:
        vals = [f'{v:,.6f} {k}'.replace(',', ' ') for k, v in h['balances'].items() if k != 'error' and v]
        if vals:
            lines.append([short(h['address']), CHAIN.get(h['chain'], h['chain']), ' ; '.join(vals), h['read_at']])
    return table(['Adresse du dossier', 'Chaîne', 'Solde lu', 'Lu à (UTC)'], lines) if lines else 'Aucun solde notable.'


def recon_line(r):
    return f"Solde pUSD calculé {r['computed_balance']:.6f}, lu {r['balance_now']:.6f}. Dépôts {r['deposits_matched']}/{r['deposits_total']} et retraits {r['withdrawals_matched']}/{r['withdrawals_total']} rapprochés de l'API. Frappes hors dépôts : {len(r['mints_outside_api'])}, toutes des remboursements (`REDEEM`) : {'oui' if r['mints_outside_are_redeem'] else 'non'}. Transferts de positions hors transaction de marché : {len(r['position_only_moves'])}. Mouvements de pUSD absents de l'API : {len(r['money_rows_outside_api'])}."


def case_section(slug, c, w, r, fund, cash, unresolved):
    n = N.CASES[slug]
    a = c['account']
    pnl = a['withdrawals'] - a['deposits']
    owner = (c['wallet'].get('owners') or [''])[0]
    parts = [f"### {c['label']}", '', f"Wallet `{c['address']}`. Clé propriétaire lue sur la chaîne : `{owner}`. Lien étiquette vers adresse : {c['identity_level']}. {len(c['deposits'])} dépôts pour {usd(a['deposits'])} $, {len(c['withdrawals'])} retraits pour {usd(a['withdrawals'])} $, soit {usd(pnl)} $ de retraits moins dépôts.", '', f"**En bref.** {n['bref']}", '']
    parts += [table(['Question', 'Réponse', 'Niveau'], n['table']), '']
    parts += ['**Sources de l\'argent, par dépôt** (répartition PEPS quand plusieurs entrées se mêlent, convention comptable) :', '', origin_table(slug, fund), '']
    parts += ['**Soldes lus le 2 nov.** :', '', holdings_table(w), '']
    parts += [f"**Rapprochement.** {recon_line(r)}", '']
    if n.get('chemins'):
        parts += ['**Chemins non résolus** :', ''] + [f'- {x}' for x in n['chemins']] + ['']
    parts += [f"**Confiance et explications alternatives.** {n['confiance']}", '']
    parts += ['**Transactions vérifiables, financement :**', '', path_table(slug, fund), '', '**Transactions vérifiables, sorties :**', '', path_table(slug, cash), '']
    return '\n'.join(parts)


def matrix(pairs):
    labels = {s: s[:9] for s in ORDER}
    head = [''] + [labels[s] for s in ORDER]
    lines = []
    for a in ORDER:
        line = [labels[a]]
        for b in ORDER:
            if a == b:
                line.append('·')
                continue
            v = pairs['pairs'].get('|'.join(sorted((a, b))))
            if v['direct']:
                line.append('**D**')
            elif v['shared_unattributed']:
                line.append('h')
            elif v['shared_service']:
                line.append('s')
            else:
                line.append('')
        lines.append(line)
    return table(head, lines)


def comparison(cases, walks, fund):
    lines = []
    for s in ORDER:
        lines.append([cases[s]['label']] + N.COMPARE[s])
    return table(['Compte', 'Origine la plus proche', 'Service d\'entrée', 'Destination des retraits', 'Sorti de la première adresse ?', 'XMR', 'Où la trace devient incertaine'], lines)


def main():
    cases, walks, recon, pairs, bridges, rates, verify, tests = load()
    fund, cash = rows('funding_paths'), rows('cashout_paths')
    unresolved = json.loads((STATE / 'unresolved.json').read_text())
    final = [N.FINAL_HEAD, '', NOTE, '', '## 1. Résultat', '', N.RESULT, '', comparison(cases, walks, fund), '', '## 2. Matrice de liens entre les 11 comptes', '', 'D : transfert direct entre clés. h : hub non attribué partagé (pas un lien). s : seulement des services nommés partagés (pas un lien). Vide : aucune adresse partagée dans les historiques lus.', '', matrix(pairs), '', N.MATRIX_READING, '', N.BRACE_KRABEN, '', '## 3. Les 11 comptes', '']
    for s in ORDER:
        final.append(case_section(s, cases[s], walks[s], recon[s], fund, cash, unresolved))
    final += ['## 4. Couverture et contrôles', '', N.coverage(fund, cash, recon, unresolved, verify, tests, cases), '', '## 5. Limites', '', N.LIMITS, '']
    (ROOT / 'reports').mkdir(exist_ok=True)
    (ROOT / 'reports/FUNDING_FORENSICS_FINAL.md').write_text('\n'.join(final))
    (ROOT / 'reports/COMMON_FUNDERS.md').write_text(N.common_funders(pairs, rates, cases, walks))
    (ROOT / 'reports/EXCHANGE_AND_PRIVACY_EXPOSURE.md').write_text(N.exposure(rows('service_attributions'), cases))
    (ROOT / 'reports/CASHOUT_PATHS.md').write_text(N.cashout(cases, walks, cash, bridges))
    (ROOT / 'reports/UNKNOWN_PATHS.md').write_text(N.unknown(unresolved, walks, cases))
    print('reports written')


if __name__ == '__main__':
    main()
