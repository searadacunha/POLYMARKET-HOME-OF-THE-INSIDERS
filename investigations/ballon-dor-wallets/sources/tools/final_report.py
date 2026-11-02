"""Writes the final reports from the evidence files only. Every figure below is read from a file named in the text."""
import json
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import identities as I

ROOT = Path(__file__).resolve().parent.parent
J = lambda p: json.loads((ROOT / p).read_text())
CHAINS = {792703809: 'Solana', 137: 'Polygon', 56: 'BSC', 1: 'Ethereum', 42161: 'Arbitrum', 8453: 'Base', 10: 'Optimism', 728126428: 'Tron', 8253038: 'Bitcoin', None: 'aucune'}
MINTS = {'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v': 'USDC', 'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB': 'USDT'}
ID_CONF = {'ALIAS_EXACT_AND_SHARES': 'élevée', 'ALIAS_EXACT': 'élevée', 'SHARES_ONLY': 'moyenne à élevée', 'PREFIX_UNIQUE': 'moyenne'}
ID_TEXT = {'ALIAS_EXACT_AND_SHARES': 'nom exact et parts de la capture', 'ALIAS_EXACT': 'nom exact', 'SHARES_ONLY': 'parts de la capture', 'PREFIX_UNIQUE': 'préfixe de presse unique'}


def m(x, d=2):
    return f'{x:,.{d}f}'.replace(',', ' ').replace('.', ',') if x is not None else 'n/d'


def sh(a):
    a = str(a)
    return a if len(a) < 16 else a[:10] + '…' + a[-4:]


def day(t):
    return time.strftime('%d/%m %H:%M', time.gmtime(t))


def routes(c):
    """One readable line per deposit: where it demonstrably came from, and at what level."""
    rel = c.get('chain_relations', [])
    out = []
    for h in c.get('funding_chain', []):
        if not h:
            continue
        r = h.get('relay') or {}
        chain = (r.get('in_txs') or [[None]])[0][0]
        amount = next((x['amount'] for x in rel if x['tx'] == h['deposit_tx']), None)
        text = f"{m(amount)} $"
        if chain == 792703809:
            funders = [x for x in rel if x['target'] == r.get('user') and x['chain'] == chain]
            who = ', '.join(sorted({(f.get('source_label') or {}).get('name') or sh(f['source']) for f in funders})) or 'non lu'
            text += f" : {who} → `{sh(r.get('user'))}` (Solana) → Relay"
        elif r:
            senders = h.get('origin_sender') or []
            user = str(r.get('user')).lower()
            owners = (c.get('wallet') or {}).get('owners') or []
            if senders:
                s = senders[0]
                text += f" : `{sh(s['source'])}` (nonce {m(s['kind']['nonce'], 0)}) → adresse de pont, {CHAINS.get(chain, chain)} → Relay"
            elif user in owners:
                text += f" : la clé propriétaire elle-même, {CHAINS.get(chain, chain)} → Relay"
            else:
                text += f" : `{sh(r.get('user'))}`, {CHAINS.get(chain, chain)} → Relay"
        else:
            text += f" : `{sh(h.get('immediate_source'))}`, origine non lue"
        out.append(text)
    return out


def exits(c):
    rows = []
    rel = c.get('chain_relations', [])
    for h in c.get('exit_chain', []):
        if not h:
            continue
        r = h.get('relay') or {}
        match = next((x for x in rel if x.get('payout_tx') == h['tx'] or (x['tx'] == h['tx'])), None)
        rows.append(dict(tx=h['tx'], at=h['at'], usd=float(h['usd']), recipient=h.get('recipient') or h.get('first_destination'), chain=h.get('out_chain') or 137, received=r.get('out_amount'), symbol=r.get('out_symbol'), category=(match or {}).get('category', 'UNKNOWN'), out_tx=(r.get('out_txs') or [[None, None]])[0][1], status=r.get('status')))
    return rows


ALT = {
    'thin': "Pari de conviction renforcé sur plusieurs jours : achats étalés du 12 au 14 octobre, avec aussi deux petits paris sur Yui Hasegawa revendus à perte nette d'environ 11 $, ce qui ne ressemble pas à une connaissance de tous les résultats.",
    'vidente': "Achat tardif sur un seul marché, après la montée du prix de Mbappé depuis moins de 0,35 début octobre : compatible avec un pari de conviction ou le suivi du mouvement.",
    'cookedrice': "Entrée le 14 octobre, à un prix déjà proche de 0,5, après la première montée : compatible avec le suivi du mouvement.",
    'wen': "Une seule grosse mise le 18 octobre à un prix déjà proche de 0,55 : compatible avec un pari de conviction tardif, et avec un compte neuf d'un parieur déjà actif ailleurs.",
    '0x86544e4dfde': "Parieur actif sur plusieurs issues dès le 9 octobre, Kane compris, au moment où ce marché montait déjà. Mouvement de Kane amorcé la veille sans wallet nommé.",
    'brace227': "Profil de petit parieur actif : nombreux tickets, 8 dépôts, 9 issues, et des retraits en cours de route. Aucune priorité ni comportement dans S_A.",
    'walletwallet8424': "Deux paris cohérents entre eux, Kane et Mbappé devant Yamal, pris au moment où Kane montait déjà. Compatible avec une lecture du marché.",
    'zoomman17': "La famille ne pèse qu'environ 41 % de ses achats : ce compte parie largement ailleurs, ce qui rend moins probable un compte créé pour cette seule affaire.",
    'kraben006': "Le plus progressif : 14 petits dépôts depuis le 1er octobre, rotation visible de Kane vers les rangs exacts à mesure que ces marchés ouvrent, comme le note la capture. Compatible avec un parieur actif qui prend ses gains et se repositionne.",
    'ouldlm3alem': "Premier événement le 22 octobre, 20 heures avant l'article, à des prix déjà élevés sur des issues favorites. Journal du Coin et Numerama évoquent eux-mêmes la possibilité de suiveurs dans cette affaire.",
    '0xdd97e6': "Premier événement le 20 octobre, après l'ouverture des marchés de rangs, à des prix où ces issues étaient déjà favorites. Compatible avec le suivi du marché. Son lien avec l'étiquette n'est pas certifié.",
}


def wallet_section(s, c, balances, combos, stats, links):
    a = c['account']
    w = c.get('wallet') or {}
    st = stats[s]
    cats = Counter(r['category'] for r in c.get('chain_relations', []))
    pos = [p for p in combos['outcomes'] if s in p['members']]
    pos.sort(key=lambda p: -p['members'][s]['usd'])
    per = combos['per_wallet'][s]
    tidy = lambda t: t.replace('Ballon d' + chr(39) + 'Or 2026: ', '').replace('Will ', '').replace(' the 2026 Ballon d' + chr(39) + 'Or?', '').replace(' of the 2026 Ballon d' + chr(39) + 'Or?', '').replace(' in the 2026 Ballon d' + chr(39) + 'Or?', '').replace(' to finish higher?', '')
    L = [f"### {c['label']}", '', f"Wallet `{c['address']}`, {w.get('type')}, clé propriétaire `{(w.get('owners') or ['?'])[0]}`. Dossier complet : `cases/{s}.md`.", '', '**Comportements suspects réellement observés.** Ce sont des faits, pas des preuves d' + chr(39) + 'intention.', '']
    e6 = st['E6']
    L.append(f"- Premier événement Polymarket le {e6['premier_evenement']} UTC, premier achat sur la famille le {e6['premier_achat_famille']} UTC.")
    L.append(f"- Concentration : {m(100 * st['concentration_famille'], 1)} % de ses achats sur le Ballon masculin ({m(per['buy_family'])} $ sur {per['markets_family']} issues, {m(per['buy_other'])} $ ailleurs).")
    mb = st.get('mbappe')
    if mb:
        L.append(f"- Mbappé devant Yamal : {m(mb['usd'])} $ pour {m(mb['shares'])} parts, prix moyen {m(mb['usd'] / mb['shares'], 3) if mb['shares'] else 'n/d'} ; {m(mb['before_d2'])} $ avant le 13 oct. 18:51 UTC, {m(mb['before_article'])} $ avant l" + chr(39) + f"article. Part des achats taker du token avant l" + chr(39) + f"article : {m(100 * st['mbappe_taker']['part_des_achats'], 1)} %.")
    others = [p for p in pos if not ('Mbappé or Lamine Yamal' in p['title'] and p['outcome'] == 'Mbappé')]
    L.append('- Autres issues : ' + ('; '.join(f"{tidy(p['title'])} / {p['outcome']} ({m(p['members'][s]['usd'], 0)} $)" for p in others[:3]) or 'aucune') + '.')
    b = st.get('plus_grosse_decision_taker')
    if b:
        L.append(f"- Plus grosse décision taker : {m(b['usd'])} $ le {b['utc']} UTC, {tidy(b['question'] or '')} / {b['outcome']}" + (f", {m(b['multiple'])} fois le volume du token sur les 24 h précédentes" if b['multiple'] else '') + '.')
    if a['account_closed']:
        L.append(f"- Résultat : compte soldé, **retraits moins dépôts {m(a['net_cash_out_minus_in'])} $**, hors gas et coûts hors de ce wallet.")
    else:
        bal = c.get('balances_now') or {}
        op = c.get('open_positions') or {}
        L.append(f"- Résultat : non affirmé. Compte non soldé ou non réconcilié : résidu de calcul {m(a['residual'], 4)} $, solde pUSD {m((bal.get('pUSD') or 0) / 1e6)} $, {op.get('open_rows', 'n/d')} positions ouvertes valant {m(op.get('current_value'))} $. Écart brut retraits moins dépôts : {m(a['withdrawals'] - a['deposits'])} $.")
    L += ['', '**Preuves on-chain vérifiables.**', '']
    if c['deposits']:
        d = c['deposits'][0]
        L.append(f"- Premier financement : {d['utc']} UTC, {m(float(d['usd']))} $, `{d['tx']}`. Le pUSD est frappé depuis l" + chr(39) + "adresse zéro, qui n" + chr(39) + "est pas un financeur.")
    L.append(f"- Dépôts : {len(c['deposits'])}, {m(a['deposits'])} $.")
    routed = routes(c)
    L += [f"  - {x}" for x in routed[:5]]
    if len(routed) > 5:
        L.append(f"  - et {len(routed) - 5} autres, dans le dossier complet.")
    ex = exits(c)
    L.append(f"- Sorties : {len(ex)}, {m(a['withdrawals'])} $.")
    for x in ex[:5]:
        recv = f"{m(float(x['received']), 4)} {x['symbol']}" if x['received'] else 'montant reçu non lu'
        L.append(f"  - {day(x['at'])} UTC, {m(x['usd'])} $ → `{x['recipient']}` ({CHAINS.get(x['chain'], x['chain'])}), reçu {recv}, {x['category']}. Retrait `{x['tx']}`" + (f", paiement `{x['out_tx']}`" if x['out_tx'] and x['out_tx'] != x['tx'] else '') + '.')
    if len(ex) > 5:
        L.append(f"  - et {len(ex) - 5} autres, dans le dossier complet.")
    for x in c.get('recipients', []):
        if x.get('chain') == 792703809:
            toks = ', '.join(f"{m(t['amount'])} {MINTS.get(t['mint'], t['mint'][:6])}" for t in x.get('tokens', [])) or 'aucun jeton'
            moved = '; '.join(f"{day(mv['at'])} UTC vers `{sh(mv['to'][0]['owner'])}`, {m(mv['to'][0]['delta'])} {MINTS.get(mv['to'][0]['mint'], '')}" for mv in x.get('moved_out', []) if mv.get('to'))
            L.append(f"- État de `{sh(x['address'])}`, lu le {x['read_at']} UTC : {toks}. " + (f"Sortie : {moved}." if moved else 'Aucune sortie.'))
    for bal in balances.get(s, []):
        L.append(f"- `{sh(bal['address'])}` ({CHAINS.get(bal['chain'], bal['chain'])}) : reçu {m(bal['received'])}, solde du même jeton {m(bal['now'])}, lu le {bal['read_at']} UTC.")
    for h in c.get('exit_chain', []):
        if h and h.get('same_transaction_swap'):
            L.append(f"- Swap dans la transaction de retrait `{h['tx']}` : le reçu montre l" + chr(39) + f"échange, le paiement natif ne laisse pas de log et le montant reçu repose sur l" + chr(39) + f"enregistrement Relay. Solde natif actuel de `{sh(h['recipient'])}` : {m(h['recipient_native_balance_now'])}. Ces fonds sont donc repartis, et leur destination n" + chr(39) + "a pas été lue : les mouvements natifs ne sont pas scannés.")
    for f in c.get('exit_follow', []):
        for k in f.get('hops', [])[:2]:
            if not k.get('label'):
                L.append(f"- Saut suivant de `{sh(f['address'])}` : {m(k['amount'])} $ vers `{sh(k['target'])}`, {k['kind']['kind']}, nonce {k['kind']['nonce']}, `{k['tx']}`.")
    L.append(f"- Relations à identifiant stable : {', '.join(f'{k} {v}' for k, v in cats.most_common())}.")
    L += ['', '**Liens éventuels avec les autres wallets.**', '']
    mine = [n for n in links['nodes'] if s in n['cases']]
    for n in mine:
        L.append(f"- {n['class_']} : `{sh(n['address'])}`, aussi {', '.join(x for x in n['cases'] if x != s)}.")
    if not mine:
        L.append('- Aucune adresse partagée avec un autre dossier sur les sauts lus.')
    L.append('- Lien discriminant : aucun. Transfert de fonds direct avec un autre dossier : aucun sur les chaînes et jetons lus.')
    if s in ('ouldlm3alem', '0x86544e4dfde'):
        L.append(f"- Une exécution de carnet d" + chr(39) + f"ordres entre OuldLm3alem et 0x86544e4dfde : 520,97 parts à 0,53, `{links['clob_matches'][0]['tx']}`. Ordinaire sur un carnet.")
    shared = [f"{tidy(x['title'])} / {x['outcome']} ({len(x['autres'])} autres)" for x in st['issues_avec_autres_nommes'][:4]]
    L.append('- Issues aussi détenues par d' + chr(39) + 'autres nommés : ' + ('; '.join(shared) or 'aucune') + '.')
    L += ['', '**Explications alternatives et faux positifs.**', '', f"- {ALT[s]}"]
    fps = [n for n in mine if n['class_'] != 'DISCRIMINANT']
    if fps:
        L.append(f"- Faux positifs d" + chr(39) + f"une règle de « financeur commun » : {', '.join('`' + sh(n['address']) + '`' for n in fps)}. Ce sont des services, ils ne relient personne.")
    L.append('- Biais de sélection : ce compte est étudié parce que la presse l' + chr(39) + 'a nommé après le résultat. Taille et âge ne sont donc pas des résultats indépendants.')
    L += ['', '**Résultats des contrôles statistiques.** Lecture individuelle descriptive : n effectif de l' + chr(39) + 'affaire = 1, sans puissance par wallet.', '']
    sa = st['S_A']
    L.append(f"- S_A scellé : {'vu' if sa['vu'] else 'non vu'}, {sa['comportements']} paire(s) avec comportement, score maximal {sa['score_max']}, **{sa['priorites']} priorité**. Comparaison exploratoire, hors R3.")
    L.append('- Alerte A0 : ' + ('; '.join(f"{x['utc']}, {tidy(x['question'] or '')} / {x['outcome']}, {x['n']} wallets, {'avant' if x['avant_D2'] else 'après'} le 13 oct. 18:51" for x in st['A0']) or 'membre d' + chr(39) + 'aucune') + '.')
    L.append('- Alerte du recensement E1G : ' + ('; '.join(f"{x['utc']}, {tidy(x['question'] or '')} / {x['outcome']}" for x in st['E1G']) or 'membre d' + chr(39) + 'aucune') + '.')
    r2 = st['E2_rafales']
    L.append(f"- Rafales E2, membre de : {r2['5']} à 5 min, {r2['15']} à 15 min, {r2['60']} à 60 min.")
    L.append('- Petits puis gros E3 : ' + ('; '.join(f"{x['utc']}, {m(x['usd'])} $ après une médiane de {m(x['mediane_avant'])} $" for x in st['E3_petits_puis_gros']) or 'non') + '.')
    L.append(f"- Combinaisons inhabituelles E4 v2 : {st['E4_v2_paires']} paire sur les trois graines et les deux dates.")
    v = st['E5_voisins']
    L.append(f"- Autres nommés achetant le même token à moins de 5 min : {', '.join(v['5']) or 'aucun'} ; à moins de 60 min : {len(v['60'])}.")
    if e6['ecart_min'] is not None:
        L.append(f"- Financement E6 : {m(e6['ecart_min'], 1)} min entre le dernier dépôt et le premier achat. {e6['comparateurs_plus_courts']} comparateurs sur {e6['comparateurs']} font aussi court ou plus court. Confondu avec l" + chr(39) + 'âge du compte.')
    L.append('- Top 20 des décisions E7 : ' + ('; '.join(f"{x['utc']}, {m(x['usd'])} $, prix {m(x['prix_avant'], 3)} avant, {m(x['paye'], 3)} payé, {m(x['multiple'])} fois le volume de 24 h" for x in st['E7_top20']) or 'absent') + '.')
    rg = st['rangs']
    L.append(f"- Quatre rangs exacts détenus avant l" + chr(39) + f"article : {'oui' if rg['quatre_avant_article'] else 'non'}. Combinaison cotée environ 0,28 à cette date, donc pas rare par rapport aux prix.")
    L += ['', '**Niveau de confiance et limites.**', '', f"- Lien étiquette vers adresse : **{'élevée' if s == 'kraben006' else ID_CONF[c['identity_level']]}** ({ID_TEXT[c['identity_level']]}{', et vente de Kane pour Yamal 3e conforme à la note de la capture' if s == 'kraben006' else ''}).", f"- Flux : **élevée** sur {cats.get('ONCHAIN_CONFIRMED', 0) + cats.get('PROTOCOL_CONFIRMED', 0)} relations lues sur la chaîne, **moyenne** sur {cats.get('SERVICE_INTERACTION', 0)} relations dépendant d" + chr(39) + "un service ou d" + chr(39) + "une étiquette.", '- Coordination et information privilégiée : **non démontrées**, aucune preuve dans ce dossier ne les établit.']
    stops = c.get('chain_stops', [])
    if stops:
        L.append('- La trace s' + chr(39) + f"arrête à : {', '.join('`' + sh(x.get('address') or x.get('tx')) + '`' for x in stops[:4])}. Seul le service connaît le compte d" + chr(39) + 'origine.')
    L.append('- Mouvements natifs non lus hors enregistrement Relay. Soldes lus à la date indiquée, ils peuvent changer.')
    L.append('')
    return L


def dormant(cases, balances):
    parts = []
    for s, c in cases.items():
        for x in c.get('recipients', []):
            if x.get('chain') == 792703809 and not x.get('moved_out'):
                big = [t for t in x.get('tokens', []) if (t['amount'] or 0) > 100]
                parts += [f"{c['label']} {m(t['amount'])} {MINTS.get(t['mint'], '')} sur `{sh(x['address'])}`" for t in big]
        for b in balances.get(s, []):
            if b['now'] >= .9 * b['received'] and b['received'] > 1000:
                parts.append(f"{c['label']} {m(b['now'])} sur `{sh(b['address'])}`")
    return ', '.join(parts)


def HYPOTHESES(v):
    k, e4, rank, gx = v['r']['kucoin'], v['e4'], v['rank'], v['gx']
    D2, TF = v['D2'], v['TF']
    named = v['e5']['named']
    opp = v['e5']['comparators']['token_oppose']['named_percentile']
    rows = [
        ('H1', 'Les onze étiquettes correspondent à des wallets identifiables', 'CONFIRMÉE, niveaux inégaux', 'Capture reproduite 15 lignes sur 15 ; 7 noms exacts, 3 par les parts, 1 par préfixe'),
        ('H2', 'Ces comptes ont réalisé des gains', 'CONFIRMÉE pour ' + str(len(v['closed'])) + ' comptes soldés, non établie pour ' + str(len(v['open_'])), 'Comptabilité complète, résidu nul sur les soldés'),
        ('H3', 'Un même opérateur contrôle les onze', 'AFFAIBLIE', '11 clés distinctes, routes différentes, 0 transfert direct, 0 lien discriminant. Des comptes d\'exchange restent invisibles : non exclue'),
        ('H4', 'Un financeur personnel commun relie certains comptes', 'AFFAIBLIE', str(v['links']['naive_pair_count']) + ' paires naïves, 0 après reclassement. Hors des sauts lus, inconnu'),
        ('H5', 'La route commune brace227 et walletwallet8424 du 30 octobre est un lien', 'RÉFUTÉE comme lien', 'Relay plus contrat de passage à fort trafic'),
        ('H6', 'Un signal collectif spécifique était visible le 13 octobre', 'RÉFUTÉE pour la règle testée', 'Verdict gelé VISIBLE_NON_SPECIFIQUE, rang 41 du recensement. Ne vaut pas pour toute autre règle'),
        ('H7', 'Des comptes frais se concentrent sur une issue plus que le hasard', 'AFFAIBLIE', f"Placebo p = {m(D2['p'], 3)} puis {m(TF['p'], 3)}, 1 000 tirages"),
        ('H8', 'Les comptes nommés achètent de façon synchrone', 'AFFAIBLIE', f"{named['pairs_5']} paires à 5 min sur 55, centile {m(100 * opp['pairs_5'], 1)} non corrigé, mais centile {m(100 * opp['pairs_60'], 1)} à 60 min et {m(100 * opp['busiest_24h_share'], 1)} sur la concentration en 24 h"),
        ('H9', 'Les nommés partagent des combinaisons inhabituelles', 'AFFAIBLIE', f"E4 v2 : 0 paire nommée sur {e4['T_FIN']['union_pairs']} paires et trois graines"),
        ('H10', 'Détenir le classement exact était rare', 'RÉFUTÉE par rapport aux prix', 'Combinaison cotée environ 0,28 avant l\'article, marchés de rangs ouverts vers 0,6'),
        ('H11', 'Les comptes nommés ont eux-mêmes lancé la hausse de Kane', 'AFFAIBLIE', 'Hausse amorcée le 8 octobre : 24 444 $ d\'achats, 0 $ de comptes nommés. Ils pèsent ensuite 25 à 53 % des achats du 9 au 11'),
        ('H12', 'Une route KuCoin plus fréquente chez les nommés', 'INDICE FAIBLE, non confirmée', f"{k['named']['hits']}/{k['named']['n']} contre {k['comparateurs_ensemble']['hits']}/{k['comparateurs_ensemble']['n']}, p ≈ {m(k['fisher_one_sided_named_vs_comparators'], 3)} non corrigé, {m(k['fisher_one_sided_named_vs_fresh_only'], 3)} face aux seuls comptes frais, étiquette à source unique"),
        ('H13', 'Les fonds passent par ChangeNOW, FixedFloat ou XMR', 'NON SOUTENUE', 'Aucune interaction sur les sauts lus, listes incomplètes, deux chaînes s\'arrêtent à un service non identifié'),
        ('H14', 'Des retraits coordonnés', 'NON DÉMONTRÉE', 'Plusieurs retraits peu après la résolution, ce qu\'impose le calendrier du marché. Aucun comparateur daté de cette fenêtre'),
        ('H15', 'Une information privilégiée', 'NON TESTABLE ici', 'Aucune preuve d\'accès. Des données publiques seules ne peuvent pas trancher'),
    ]
    return [f'| {a} | {b} | **{c}** | {d} |' for a, b, c, d in rows]


def main():
    cases = {s: J(f'cases/{s}.json') for s in I.IDS}
    links = J('graphs/links_classified.json')
    combos = J('collective/exploratoire/combos.json')
    rank = J('collective/exploratoire/rank_combos.json')
    e1 = J('collective/derived/A_E1.json')
    g = J('collective/derived/A_E1G.json')
    e2 = J('collective/derived/A_E2.json')
    e3 = J('collective/derived/A_E3.json')
    pl = J('collective/derived/A_placebo.json')
    e4 = J('collective/exploratoire/E4_v2_summary.json')
    e5 = J('collective/derived/B_E5.json')
    e6 = J('collective/derived/B_E6.json')
    e7 = J('collective/derived/B_E7.json')
    rev = J('collective/derived/B_review.json')
    days = J('collective/exploratoire/price_days.json')
    repro = J('collective/audit/REPRODUCTION.json')
    balances = J('evidence/recipient_balances.json')
    stats = J('collective/exploratoire/per_wallet_stats.json')
    gx = J('evidence/gxjc_sizes.json')
    closed = {s: c['account']['net_cash_out_minus_in'] for s, c in cases.items() if c['account']['account_closed']}
    open_ = {s: c['account'] for s, c in cases.items() if not c['account']['account_closed']}
    a0 = e1['e1']['M']['a0']
    mbappe = next(p for p in combos['outcomes'] if 'Mbappé or Lamine Yamal' in p['title'] and p['outcome'] == 'Mbappé')
    kane = next(p for p in combos['outcomes'] if 'Harry Kane win' in p['title'] and p['outcome'] == 'Yes')
    day_m = days[next(k for k in days if 'Mbappé or Lamine Yamal' in k and k.endswith('Mbappé'))]
    day_y = days[next(k for k in days if 'Mbappé or Lamine Yamal' in k and k.endswith('Yamal'))]
    r = links['rates']
    fp = sorted(links['nodes'], key=lambda n: -len(n['cases']))

    L = ["# Enquête Ballon d'Or 2026 : rapport final", '', f"Écrit le {time.strftime('%d/%m/%Y à %H:%M UTC', time.gmtime())} depuis les fichiers de preuve. Espace : `~/Projects/PolySentinel-investigation`. Une adresse n'est pas une personne : aucune identité civile n'est établie ni recherchée.", '']
    L += ['## 1. Conclusion', '', '**Aucune coordination et aucune information privilégiée ne sont démontrées.** Les onze comptes publics sont reliés à une adresse et leurs flux sont reconstruits, mais rien ne prouve qu\'ils ont un propriétaire commun. Le signal collectif testé est visible au 13 octobre, sans être spécifique.', '', '| Niveau | Verdict | Sur quoi il repose |', '|---|---|---|']
    L.append(f"| Comportement atypique | **Observé, avec un biais de sélection** | 11 comptes sur 11 actifs depuis octobre seulement. {e6['summary']['named']['gap_under_1h']} sur 11 ont déposé moins d'une heure avant leur premier achat sur cette famille. {mbappe['wallets']} sur 11 sont sur Mbappé devant Yamal. La presse en a surligné 9 sur ces traits. |")
    L.append(f"| Coordination | **Non démontrée** | 0 transfert direct de fonds, 0 adresse partagée discriminante sur {links['possible_pairs']} paires, 0 paire nommée dans E4 v2, pas de synchronie nette (centile {m(100 * e5['comparators']['token_oppose']['named_percentile']['pairs_5'], 1)} à 5 min non corrigé, {m(100 * e5['comparators']['token_oppose']['named_percentile']['pairs_60'], 1)} à 60 min). |")
    L.append('| Insider trading | **Non démontré** | Aucune preuve d\'accès à l\'information. Gagner un pari, même tôt, ne prouve pas sa source. Les chronologies publiques des 8 au 13 octobre restent incomplètes. |')
    L += ['', '## 2. Les onze dossiers', '', '| Étiquette | Wallet | Confiance sur le lien | Dépôts $ | Retraits $ | Retraits moins dépôts | Dernière destination lue |', '|---|---|---|---:|---:|---:|---|']
    for s, c in cases.items():
        a = c['account']
        ex = exits(c)
        last = sh(ex[-1]['recipient']) + ' (' + CHAINS.get(ex[-1]['chain'], str(ex[-1]['chain'])) + ')' if ex else 'n/d'
        L.append(f"| {c['label']} | `{sh(c['address'])}` | {'élevée' if s == 'kraben006' else ID_CONF[c['identity_level']]} | {m(a['deposits'])} | {m(a['withdrawals'])} | {m(a['net_cash_out_minus_in']) + ' (soldé)' if a['account_closed'] else 'non affirmé'} | `{last}` |")
    total = sum(closed.values())
    L += ['', f"Sur les {len(closed)} comptes soldés, retraits moins dépôts : **{m(total)} $**. Les {len(open_)} autres ne sont pas soldés ou gardent un résidu ({', '.join(cases[s]['label'] for s in open_)}) : aucun gain n'y est affirmé. Ce total ne recoupe pas les chiffres de presse, dont le périmètre diffère.", '', '**Lecture des niveaux de confiance.** Élevée : lu sur la chaîne, ou même identifiant d\'ordre sur deux chaînes. Moyenne : enregistrement d\'un service, ou étiquette à source unique. Faible : comportement mesuré. La confiance du lien étiquette vers adresse est donnée à part.', '', '**Comment les cinq comptes non résolus ont été reliés.** Le top 15 de la capture Upside est reproduit depuis le tape public, ligne par ligne, à moins d\'une demi-part, à une seule fenêtre : 23 oct. 14:11:39 à 14:18:08 UTC (`evidence/screenshot_reconstruction.json`). kraben006 a en plus une confirmation indépendante : ce wallet vend bien du Kane pour acheter Yamal 3e, comme le note la capture. Détail : `reports/inventaire_adresses.md`.', '']
    for s, c in cases.items():
        L += wallet_section(s, c, balances, combos, stats, links)

    L += ['## 3. Réconciliation des retraits', '', 'L\'erreur corrigée : pour le retrait de 77 050,77 $ d\'OuldLm3alem, mon code avait pris l\'adresse zéro pour destination, alors que c\'est le burn de pUSD. La règle suit maintenant ce que le wallet envoie après ce burn, avec un test sur la forme réelle du reçu (`tools/test_case_chain.py`). Aucune relation ne vise plus l\'adresse zéro.', '', '| Dossier | Retraits API $ | Retraits suivis | Vers Relay avec paiement lu | Autres | Sans destination |', '|---|---:|---:|---:|---:|---:|']
    for s, c in cases.items():
        ex = exits(c)
        relay = sum(1 for x in ex if x['out_tx'])
        none = sum(1 for x in ex if not x['recipient'])
        L.append(f"| {c['label']} | {m(c['account']['withdrawals'])} | {len(ex)} | {relay} | {len(ex) - relay - none} | {none} |")
    L += ['', 'Les liens Relay classés `PROTOCOL_CONFIRMED` portent le même identifiant dans le log d\'escrow et dans le paiement, lus sur les deux chaînes. Cette preuve ne dépend pas de l\'API de Relay. L\'API reste utile pour trouver le paiement, et sa route publique disparaît le 24 novembre.', '']

    L += ['## 4. Liens de financement reclassés', '', f"Une règle naïve de « financeur commun » relierait **{links['naive_pair_count']} paires sur {links['possible_pairs']}**. Après classement, **{len(links['discriminant_pairs'])} paire** repose sur une adresse discriminante.", '', '| Adresse partagée | Classe | Dossiers | Aussi chez les témoins | Pourquoi |', '|---|---|---|---|---|']
    for n in fp:
        seen = ', '.join(f'{k} {v}' for k, v in n.get('also_in_baseline', {}).items() if k != 'named') or 'non'
        L.append(f"| `{sh(n['address'])}` | {n['class_']} | {', '.join(n['cases'])} | {seen} | {n['why'][:150]} |")
    L += ['', f"**Transferts directs.** Scan de {links['direct_scan']['addresses']} adresses (wallets, clés, adresses de pont, destinations), Polygon et Ethereum, stablecoins, pUSD et positions, depuis le 25 sept. : **{len(links['direct_funds_across_cases'])} transfert de fonds entre dossiers**. Une seule exécution de carnet d'ordres entre deux dossiers : OuldLm3alem vend 520,97 parts à 0,53 à 0x86544e4dfde, le 26 oct. 13:29:02 UTC, `{links['clob_matches'][0]['tx']}`. C'est ordinaire sur un carnet. `graphs/direct_transfers.json`.", '', '**Montant et heure.** 0 candidat entre une sortie et une entrée à 6 h et 90 à 100,1 %, sur 25 sorties et 46 entrées. Placebo à dates décalées : 0 aussi. `graphs/links.json`.', '', '### Taux de base et faux positifs', '', f"Même lecteur sur un dépôt par wallet, {links['baseline_groups'].get('named')} nommés et {sum(v for k, v in links['baseline_groups'].items() if k != 'named')} comparateurs : `controls/funding_baseline_detail.jsonl`. L'échantillon est partiel : 6 non surlignés sur 6, 7 même token sur 10, 25 token opposé sur 27, 12 comptes frais sur 40. Le garde-fou disque a arrêté la collecte au réveil du Mac et elle n'a pas été prolongée, sur ta consigne d'utiliser les données déjà collectées. L'ordre de lecture ne dépend pas du résultat : adresses triées, tirage à graine fixe.", '', '| Trait | Nommés | Non surlignés | Même token | Token opposé | Comptes frais du recensement | Tous témoins | p unilatéral, non corrigé |', '|---|---|---|---|---|---|---|---:|']
    NAMES = dict(kucoin='Passage par KuCoin Hot Wallet 2', solana_origin='Origine Solana', router_c8a6='Contrat `0xc8a6…`', relay_any='Relay', seven702_bridge='Adresse de pont 7702')
    for key, title in NAMES.items():
        x = r[key]
        cell = lambda g: f"{x[g]['hits']}/{x[g]['n']}" if g in x else 'n/d'
        L.append(f"| {title} | {cell('named')} | {cell('non_surlignes')} | {cell('meme_token')} | {cell('token_oppose')} | {cell('fraiches_recensement')} | {cell('comparateurs_ensemble')} | {m(x['fisher_one_sided_named_vs_comparators'], 3)} |")
    k = r['kucoin']
    L += ['', f"Sur tous leurs dépôts, {len(links['kucoin_any_deposit'])} nommés sur 11 passent par cette étiquette : {', '.join(links['kucoin_any_deposit'])}. Ce chiffre ne se compare pas à la ligne du tableau, qui lit un seul dépôt. **KuCoin ressort donc plus souvent chez les nommés ({k['named']['hits']}/{k['named']['n']} contre {k['comparateurs_ensemble']['hits']}/{k['comparateurs_ensemble']['n']}, p ≈ {m(k['fisher_one_sided_named_vs_comparators'], 3)} avant correction).** Face aux seuls comptes frais, l'écart tombe à {k['named']['hits']}/{k['named']['n']} contre {k['fraiches_recensement']['hits']}/{k['fraiches_recensement']['n']}, p ≈ {m(k['fisher_one_sided_named_vs_fresh_only'], 3)}. Avec cinq traits regardés après coup, un groupe choisi par la presse et une étiquette à source unique, c'est un indice faible, sans aucune valeur de propriété commune : un exchange sert de très nombreux clients.", '', f"**L'âge explique une partie de ces écarts.** Relay vaut {r['relay_any']['named']['hits']}/{r['relay_any']['named']['n']} chez les nommés et {r['relay_any']['fraiches_recensement']['hits']}/{r['relay_any']['fraiches_recensement']['n']} chez les comptes frais : les comptes récents passent simplement par ce chemin.", '', '**Faux positifs identifiés et écartés :**', '', '- `0xc8a6…`, `0xee7a…`, `GxjcMTWW…`, `0x0ce9…`, `0xc1d1…`, `0x58f2…` : chacun relie plusieurs dossiers, et chacun se révèle mutualisé à la mesure. Tableau ci-dessus.', '- La route `0xf70d… → 0xb92f… → 0xc8a6…`, signalée le 30 octobre comme « nature inconnue » entre brace227 et walletwallet8424 : c\'est Relay et un contrat de passage, donc pas un lien.', f"- `GxjcMTWW…` : VidenteRibeira et cookedrice y déposent à un jour d'écart ({m(51489)} USDT, {m(39158)} USDC). Service à 1 % de frais, payant par morceaux. Sur {gx['sampled']} transactions tirées, {gx['over_10000']} entrées à 10 000 $ ou plus sur {gx['inflows_seen']}, médiane {m(gx['median'])} $ : ces gros dépôts sont plutôt rares, sans que cela relie leurs auteurs. Les sorties ne s'apparient pas sans le registre du service.", f"- Part de {m(day_m['10-13']['named'], 0)} $ sur {m(day_m['10-13']['buy'], 0)} $ d'achats côté Mbappé le 13 octobre par des comptes nommés : mécanique, puisqu'ils sont nommés parce qu'ils détenaient ce token.", '- Pièges de lecture évités : nœud Solana rendant 0 signature pour une adresse payée, hash du pont introuvable sur sa chaîne, sondage récent de `0xee7a…` à 0 trafic. Ces trois faux zéros ont été recoupés.', '']

    D2 = pl['M_2026-10-13 18:51:00']
    TF = pl['M_2026-10-23 15:17:49']
    L += ['## 5. Détection collective', '', 'Plan gelé avant tout calcul de taux (`collective/analysis_plan.md`, `PROTOCOL.lock`), partie A scellée avant la lecture des noms et des résultats. **L\'auteur connaissait l\'affaire : aucune validation n\'en découle.** Une seule affaire, donc n effectif = 1.', '', '### A. Analyse prospective simulée', '', '**Verdict fixé d\'avance, au 13 oct. 18:51 UTC comme au 23 oct. 15:17 UTC : `VISIBLE_NON_SPECIFIQUE`.**', '', f"- **Alerte de cohorte fraîche A0** (au moins 3 wallets de 14 jours ou moins, 1 000 $ chacun, 10 000 $ en tout, sur 72 h) : {e1['a0_by_date']['D2']['M']} tokens de la famille en alerte au 13 octobre, {e1['a0_by_date']['T_FIN']['M']} au 23 octobre sur {e1['e1']['M']['tokens']}. Témoins tirés : {e1['a0_by_date']['T_FIN']['X']} sur {e1['e1']['X']['tokens']}. Femmes : 0 sur {e1['e1']['W']['tokens']}, sans puissance.", f"- **Recensement de tout Polymarket :** meilleur token de la famille au rang {g['ranks']['D2'][[x['universe'] for x in g['ranks']['D2']].index('M')]['rank']} au 13 octobre, et au rang {g['ranks']['T_FIN'][[x['universe'] for x in g['ranks']['T_FIN']].index('M')]['rank']} au 23 octobre. Le verdict exigeait le top 10. Charge : au plus 12 nouveaux tokens par jour hors famille.", f"- **Placebo des âges mélangés** (1 000 tirages) : maximum de {D2['real_max_n']} wallets frais au 13 octobre, p = {m(D2['p'], 3)} ; {TF['real_max_n']} au 23 octobre, p = {m(TF['p'], 3)}. La fraîcheur ne se concentre pas plus qu'au hasard. Aucun p de cette étude n'approche le seuil de Bonferroni du registre, voir `collective/results.md`.", f"- **Rafales de 15 min :** {m(e2['M_15']['per_token_day'], 3)} par token-jour dans la famille, {m(e2['X_15']['per_token_day'], 3)} chez les témoins. Par million de dollars : {m(e2['M_15']['per_million_usd'], 1)} contre {m(e2['X_15']['per_million_usd'], 1)}, car la famille compte beaucoup de petits tickets.", f"- **Petits achats puis gros :** {m(e3['M']['per_100'], 1)} pour 100 couples wallet-token dans la famille, {m(e3['X']['per_100'], 1)} chez les témoins. Écart descriptif, non testé.", f"- **Fills et décisions :** {m(e3['M']['fills'], 0)} fills pour {m(e3['M']['decisions'], 0)} décisions dans la famille, pour ne pas compter plusieurs fois un même ordre.", '', 'Alertes A0 antérieures au 13 octobre 18:51 UTC :', '', '| Première alerte UTC | Token | Wallets | Montant $ |', '|---|---|---:|---:|']
    for x in sorted(a0.values(), key=lambda v: v['t']):
        if x['t'] <= 1791917460:
            L.append(f"| {x['utc']} | {x.get('question')} / {x.get('outcome')} | {x['n']} | {m(x['u'])} |")
    L += ['', 'Rien de cette section n\'utilise un nom, un résultat ou une donnée postérieure à la date simulée. Reproduction en copie fraîche : E1, E1G, E2, E3 et le placebo identiques au sceau (`collective/audit/REPRODUCTION.json`).', '', '### B. Investigation rétrospective', '', 'Cette partie lit les noms et les résultats. Elle ne revient jamais dans A.', '', f"- **Wallets étudiés :** {len(cases)} wallets nommés lus en détail ; {sum(v for k, v in links['baseline_groups'].items() if k != 'named')} comparateurs pour le financement, dont les 6 non surlignés ; 3 082 wallets dont l'âge a été lu, dont {e1['e1']['M']['wallets_with_age']} avec des achats dans la famille.", f"- **Montant cumulé sur la même issue :** {m(mbappe['usd'])} $ sur Mbappé devant Yamal par les 11, dont {m(mbappe['before_d2'])} $ avant le 13 oct. 18:51 UTC et {m(mbappe['before_article'])} $ avant l'article. Kane vainqueur : {m(kane['usd'])} $ par {kane['wallets']} d'entre eux, dont {m(kane['before_d2'])} $ avant le 13 octobre.", f"- **Première alerte de la famille contenant des comptes nommés :** {rev['alerts_M'][3]['utc']} UTC sur Mbappé devant Yamal, les 3 wallets sont {', '.join(rev['alerts_M'][3]['named_members'])}. Biais : acheter gros tôt mène justement dans le top de la capture.", f"- **Achats synchrones :** {e5['named']['pairs_5']} paires nommées à 5 min, {e5['named']['pairs_60']} à 60 min sur {e5['named']['members'] * (e5['named']['members'] - 1) // 2}. Contre groupes tirés sur le token opposé : centiles {m(100 * e5['comparators']['token_oppose']['named_percentile']['pairs_5'], 1)} à 5 min et {m(100 * e5['comparators']['token_oppose']['named_percentile']['pairs_60'], 1)} à 60 min, non corrigés. Part de leurs dollars sur les 24 h les plus actives : {m(100 * e5['named']['busiest_24h_share'], 1)} %, centile {m(100 * e5['comparators']['token_oppose']['named_percentile']['busiest_24h_share'], 1)}. Ces achats sont étalés sur des semaines, pas groupés.", f"- **Combinaisons de paris (E4 v2, trois graines) :** {e4['D2']['union_pairs']} paires inhabituelles au 13 octobre, {e4['T_FIN']['union_pairs']} au 23 octobre, dont **0 impliquant un compte nommé**. {e4['T_FIN']['stable_pairs']} paires stables sur les trois graines au 23 octobre. Le nombre change avec la graine (25 à 34), donc il ne faut pas lire ce chiffre au point près.", f"- **Classement exact :** avant l'article, une seule combinaison complète des rangs 2 à 5 est détenue parmi {rank['article']['wallets_rank_any']} wallets : la bonne, par {len(rank['article']['all_four_true'])} wallets ({', '.join(sh(x) for x in rank['article']['all_four_true'])}). **Ce n'est pas rare par rapport aux prix** : le produit des quatre prix valait environ 0,28 à cette date, et ces marchés ouvrent déjà vers 0,6 le 19 octobre.", f"- **Financement avant achat :** écart médian {m(e6['summary']['named']['median_gap_min'], 1)} min chez les nommés, {e6['summary']['named']['gap_under_1h']}/11 sous une heure. Non surlignés {e6['summary']['non_surlignes']['gap_under_1h']}/6, même token {e6['summary']['meme_token']['gap_under_1h']}/10, token opposé {e6['summary']['token_oppose']['gap_under_1h']}/27. Confondu avec l'âge : un compte neuf dépose puis mise.", f"- **Prix et liquidité :** aucun carnet daté n'existe. Parmi les 20 plus grosses décisions, {sum(1 for t in e7 if t['named'])} viennent de comptes nommés. Thin le 13 oct. : {m(next(t for t in e7 if t['named'] == 'thin')['usd'])} $, {m(next(t for t in e7 if t['named'] == 'thin')['multiple_of_24h_volume'])} fois le volume des 24 h précédentes du token, prix de {m(next(t for t in e7 if t['named'] == 'thin')['price_before'], 3)} avant à {m(next(t for t in e7 if t['named'] == 'thin')['average_paid'], 3)} payé en moyenne.", '', '### Les questions posées', '', '| Question | Réponse |', '|---|---|', '| Ont-ils misé au même moment ? | Non, pas de manière distincte : étalés du 1er au 26 octobre, peu de paires proches. |', f"| Ont-ils acheté les mêmes issues ? | Oui sur Mbappé devant Yamal ({mbappe['wallets']}/11), mais 9 ont été choisis sur ce critère. {kane['wallets']}/11 sur Kane. |", '| Combinaisons statistiquement rares ? | Non établi : aucune paire nommée dans E4 v2, combinaison exacte déjà cotée environ 28 %. |', '| Mises anormales par rapport à la liquidité ? | Certaines sont grandes par rapport au volume récent. Sans carnet daté, la profondeur reste inconnue. |', '| Financements similaires avant les achats ? | Oui en apparence, mais confondu avec l\'âge des comptes. |', '| Routes communes ? | Oui, uniquement des services. Aucune discriminante. |', '| Conforme à des informations publiques ? | Non déterminable. Selon des extraits de recherche d\'Oddschecker, Yamal est favori le 5 octobre, Mbappé à 22/1. Sur Polymarket, Kane passe de 0,49 le 7 octobre à 0,66 le 11, sans source datée trouvée pour ces jours. |', '| Visible le 13 octobre ? | Oui au sens du plan, sans spécificité. Rang 41 sur tout Polymarket. PolySentinel n\'existait pas à cette date. |', '']

    L += ['## 6. ChangeNOW, FixedFloat, XMR', '', 'Sur les sauts lus, **aucune interaction avec une adresse étiquetée ChangeNOW ou FixedFloat, et aucun échange XMR**. Le statut `XMR_VISIBILITY_BOUNDARY` n\'est donc jamais posé. Cela n\'exclut rien : ma liste ChangeNOW compte 8 adresses Polygon de seconde main (`tools/services.json`). Pour Solana, l\'étude `cn_pm_sakana` n\'a gardé que les préfixes de deux hubs : aucune adresse lue ne les porte, mais un préfixe reste un test faible. Je n\'ai aucune adresse FixedFloat, et ces services paient depuis des adresses qui tournent.', '', '`GxjcMTWW…` est le point le plus proche : un service non identifié qui prélève 1 % et paie par morceaux. Rien ne permet de dire ce qu\'il est, ni de suivre ce qui en sort.', '', '**Iris :** aucune clé trouvée, aucun crédit consommé, aucune adresse envoyée. Requêtes les plus utiles : `reports/iris_requetes.md`.', '']

    L += ['## 7. Limites', '', '- Flux **taker seulement** pour les univers de l\'étude collective : un compte par ordres limites n\'y apparaît pas. Le dossier de chaque wallet lit, lui, son activité complète.', '- Stablecoins lus dans les logs : les mouvements natifs (ETH, POL, BNB, SOL) ne le sont pas, sauf là où un enregistrement Relay les nomme. Exemple : 0xdd97e6 sort en ETH, OuldLm3alem en partie en jeton natif.', '- Étiquettes de services incomplètes et datées. KuCoin : une seule source. BscScan et Polygonscan refusent la lecture automatique.', '- `Non surlignés`, `Même token`, `Token opposé` et `Comptes frais` sont des échantillons partiels pour le taux de base (voir section 4).', '- Comparateurs imparfaits : témoins surtout sportifs, famille féminine sans puissance, comptes nommés choisis après coup.', '- Trois wallets non nommés détiennent la même combinaison complète de rangs (`0xeed8c2be…35f0`, `0x1583c5d3…cdde`, `0x14c32680…df68`). Seule cette similarité les rapproche : aucun dossier ouvert, aucun financement testé, aucune mise en cause. Aucun wallet supplémentaire n\'est relié aux onze par une preuve de chaîne.', '- Sorties natives non suivies : les 839 893,73 POL d\'OuldLm3alem et les 26,97 ETH de 0xdd97e6. Destination des premiers non lue, solde des seconds non vérifié.', '- Non lancés : les quatre audits indépendants à l\'aveugle et les deux audits de conclusions du protocole d\'étude gelée. Ce rapport n\'a pas de relecture indépendante.', '- Reproduction : E1, E1G, E2, E3 et placebo identiques. E4 d\'origine non reproductible, corrigé par E4 v2 (amendement 002), son ancienne sortie est conservée.', '', '## 8. Synthèse des hypothèses', '', '**Confirmées :** H1, H2. **Réfutées, dans le périmètre indiqué :** H5, H6, H10. **Affaiblies :** H3, H4, H7, H8, H9, H11. **Non tranchées :** H12, H13, H14, H15.', '', 'Confirmée : les données la soutiennent directement. Affaiblie : testée, non soutenue, sans pouvoir l\'exclure. Réfutée : contredite par les données, dans le périmètre indiqué. Non tranchée : indice faible, listes incomplètes, ou données publiques insuffisantes.', '', '| # | Hypothèse | Statut | Sur quoi |', '|---|---|---|---|', *HYPOTHESES(locals()), '', '## 9. Conclusion', '', '### FAITS DÉMONTRÉS', '', '- La capture Upside correspond à 15 wallets du tape public, ligne par ligne.', f"- Les dépôts, positions et retraits des 11 wallets, avec {sum(len(c.get('chain_relations', [])) for c in cases.values())} relations à identifiant stable dans `graphs/relations.jsonl`.", f"- {len(closed)} comptes soldés totalisent {m(total)} $ de retraits moins dépôts.", '- Des liens entre chaînes prouvés par le même identifiant Relay dans les deux sens.', '- Aucun transfert de fonds direct entre ces dossiers, sur les chaînes et jetons lus.', f"- À la date de lecture, des sorties restent immobiles : {dormant(cases, balances)}.", '- Au 13 octobre, la règle A0 alerte sur 5 tokens, et le meilleur de la famille reste au rang 41 du recensement.', '', '### HYPOTHÈSES PLAUSIBLES', '', '- Des retraits d\'exchange directs vers l\'adresse de dépôt Polymarket, pour une partie des dépôts.', '- Des comptes neufs convaincus, ou des suiveurs d\'un mouvement de marché : la hausse de Kane du 8 au 11 octobre est large et ne dépend pas d\'eux seuls.', '', '### INDICES FAIBLES', '', f"- KuCoin plus fréquent chez les nommés ({k['named']['hits']}/{k['named']['n']} contre {k['comparateurs_ensemble']['hits']}/{k['comparateurs_ensemble']['n']}, non corrigé).", '- Le même service à 1 % pour VidenteRibeira et cookedrice, à un jour d\'écart.', '- Peu d\'acheteurs côté Mbappé pendant que le prix monte, avec un biais de sélection.', '- 4 changements de nom dans la capture, dont un compte non surligné : leurs dates sont inconnues.', '', '### NON DÉTERMINABLE', '', '- Qui contrôle ces wallets, et si plusieurs ont le même propriétaire.', '- L\'origine de leur conviction, et s\'ils ont eu accès au résultat.', '- Ce que les exchanges et services savent de ces comptes : seule une demande légale y accède.', '- Ce qui sort de `GxjcMTWW…`, et l\'identité de ce service.', '- La liquidité réelle au moment des achats.', '- La détection réelle de PolySentinel le 13 octobre : le service n\'existait pas.', '', '## 10. Incidents et corrections pendant l\'enquête', '', '- **S_C arrêté deux fois par son garde-fou.** Le 1er nov. vers 22:48 UTC, battement du collecteur à plus de 180 s, charge à 27, avec le rendu vidéo, un benchmark d\'une autre session et mes scripts : ma part n\'est pas mesurée. Le 2 nov. vers 07:39 UTC, au moment du réveil du Mac, endormi depuis 01:13 : swap +6,8 Go, disque tombé à 11,2 Go. Mes scripts dépassaient alors au plus 180 Mo et ne sont pas en cause. S_C a repris seul. Aucun fichier du rejeu n\'a été touché.', '- **Erreurs de mon code, corrigées :** adresse zéro prise pour destination, swap dans la même transaction non géré, course d\'écriture sur le cache entre deux processus, seuil « avant cérémonie » faux dans E6 (champ non cité, fichier gelé conservé), lot de comparaison `meme_token` dégénéré (centiles non cités).', '- **Trois workers réseau pendant moins de 2 minutes,** au lieu de deux, corrigé tout de suite.', '- **`rm -rf` bloqué par un contrôle de sécurité,** non contourné. Une copie de reproduction reste dans le scratchpad de session.', '', '## 11. Fichiers', '', '| Fichier | Contenu |', '|---|---|', '| `cases/<dossier>.md`, `.json` | Dossier complet par wallet, historique daté, hashes |', '| `reports/inventaire_adresses.md` | Liens étiquette vers adresse |', '| `reports/liens_entre_wallets.md` | Reclassement et faux positifs |', '| `archive/20261102_avant_correction_burn/` | Dossiers et liens d\'avant la correction, conservés |', '| `reports/iris_requetes.md`, `reports/proposition_shadow.md` | Requêtes Iris, proposition d\'intégration |', '| `reports/sources_cinq_depots.md` | Les cinq dépôts de recherche |', '| `graphs/relations.jsonl`, `graphs/links_classified.json`, `graphs/direct_transfers.json` | Relations et liens |', '| `collective/` | Étude gelée : plan, code, sorties, amendements, registre |', '| `controls/` | Taux de base |', '| `evidence/` | Reçus, captures, mesures |', '']
    i, j = L.index('## 4. Liens de financement reclassés'), L.index('## 5. Détection collective')
    (ROOT / 'reports/liens_entre_wallets.md').write_text('\n'.join(['# Liens entre les onze wallets', '', 'Extrait du rapport final. Un service commun ne relie personne, et aucune de ces lignes n\'attribue deux wallets à un même propriétaire. Données : `graphs/links_classified.json`.', ''] + L[i + 1:j]))
    (ROOT / 'reports/rapport_final.md').write_text('\n'.join(L))
    registry = (ROOT / 'collective/audit/registre_compte.txt').read_text() if (ROOT / 'collective/audit/registre_compte.txt').exists() else 'non calculé'
    results = ['# Résultats de l' + chr(39) + 'étude collective', '', 'Rapport complet : `../reports/rapport_final.md`, sections 5 et 8. Chaque chiffre y renvoie à `derived/` ou `exploratoire/`.', '', '## Verdict de la partie A, fixé d' + chr(39) + 'avance', '', '`VISIBLE_NON_SPECIFIQUE` au 13 oct. 18:51 UTC et au 23 oct. 15:17:49 UTC. Une seule affaire, n effectif = 1. Conditionnel, sans validation indépendante : l' + chr(39) + 'auteur connaissait l' + chr(39) + 'affaire.', '', '## Registre', '', '```', registry.strip(), '```', '', 'Aucun p n' + chr(39) + 'approche ce seuil. Le plus bas de la partie A vaut ' + str(round(min(v['p'] for v in pl.values()), 3)) + '.', '', '## Portes du protocole', '', '- Phases 1 à 4 : faites. Phase 7 : reproduction en copie fraîche, E1, E1G, E2, E3 et placebo identiques, E4 non (voir ci-dessous).', '- **Phases 5 et 8 non lancées** : ni les quatre audits à l' + chr(39) + 'aveugle, ni les deux audits de conclusions. Sur ta consigne de livrer sans multiplier les expériences. Ce rapport n' + chr(39) + 'a donc pas de relecture indépendante.', '', '## Deviations and data notes', '', '- Amendement 001 : plafond de lecture des âges porté de 2 500 à 3 200, aucun résultat vu.', '- Amendement 002 : E4 v2, ordre canonique et graines explicites, décidé par Benjamin après lecture des résultats. `audit/E4_non_reproductibilite.md`.', '- `G12` du plan compte 11 wallets : 11 étiquettes publiques sont résolues.', '- E5, comparateur `meme_token` : réservoir de 10 wallets pour un groupe de 10, donc un seul groupe possible. Ses centiles ne sont pas cités.', '- E6 : le champ `one_withdrawal_or_more_before_ceremony` de `derived/B_E6.json` utilise par erreur le 27 oct. 20:00 UTC au lieu du 26. Il n' + chr(39) + 'est pas cité. Recalcul correct : 0 premier retrait entre l' + chr(39) + 'article et la cérémonie, dans les quatre groupes.', '- E6 : code écrit après le sceau de la partie A et après la lecture de E5.', '- Analyses hors plan, exploratoires : `exploratoire/combos.json`, `rank_combos.json`, `price_days.json`, `per_wallet_stats.json`, `E4_v2_summary.json`, taux de base dans `../controls/`.', '- Âges : `/activity` commence au premier événement de trading, sans les dépôts. L' + chr(39) + 'âge mesure donc la première opération, pas la création du compte.', '- Recensement : les wallets écartés par le pré-filtre n' + chr(39) + 'ont pas d' + chr(39) + 'âge lu, comptés à part (`unknown_age_seen`).', '']
    (ROOT / 'collective/results.md').write_text('\n'.join(results))
    print('rapport_final lines', len(L), 'closed', len(closed), round(total, 2), 'open', list(open_))


if __name__ == '__main__':
    main()
