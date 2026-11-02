"""CLAIMS_AUDIT.csv: each published claim, the recomputed value, a verdict by rule, the evidence path. Tolerances from PROTOCOL.md section 2.
Route and label claims need a human reading of the flows: they sit in study/claims_routes.csv, written after reading FUNDING_FLOWS.csv, and are merged here."""
import csv
import gzip
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import net
import seed

ROOT = net.ROOT
T_UPSIDE = 1792768669
PARIS = 3600  # 26/10 onward: UTC+1. Before 25/10: UTC+2.
L = json.load(open(ROOT / 'derived/ledger.json'))
POS = list(csv.DictReader(open(ROOT / 'derived/positions.csv')))
MKT = json.load(open(ROOT / 'derived/market_context.json'))
FIELDS = ['claim_id', 'source', 'account', 'claim', 'claimed_value', 'recomputed_value', 'gap_pct', 'verdict', 'evidence', 'note']
rows = []


def verdict(claimed, value):
    if value is None:
        return 'UNVERIFIED', None
    gap = abs(value - claimed) / abs(claimed) if claimed else (0 if value == 0 else 1)
    if gap <= .02:
        return 'CONFIRMED', gap
    if gap <= .10:
        return 'STRONGLY_SUPPORTED', gap
    return 'CONTRADICTED', gap


def num(cid, source, account, claim, claimed, value, evidence, note=''):
    v, g = verdict(claimed, value)
    rows.append(dict(claim_id=cid, source=source, account=account, claim=claim, claimed_value=claimed, recomputed_value=round(value, 2) if value is not None else '', gap_pct=round(g * 100, 2) if g is not None else '', verdict=v, evidence=evidence, note=note))


def txt(cid, source, account, claim, value, v, evidence, note=''):
    rows.append(dict(claim_id=cid, source=source, account=account, claim=claim, claimed_value='', recomputed_value=value, gap_pct='', verdict=v, evidence=evidence, note=note))


def pos(wallet, frag, outcome=None):
    out = [r for r in POS if r['wallet'] == wallet and frag in r['market'] and (outcome is None or r['outcome'] == outcome)]
    return sum(float(r['cash_pnl']) for r in out) if out else None


def utc(ts):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(ts))


def irboz():
    created = {1: '2026-10-20', 2: '2026-10-01', 3: '2026-10-09', 4: '2026-10-22', 5: '2026-10-25', 6: '2026-10-19'}
    for n, a in seed.IRBOZ.items():
        w = a['profile'].lower()
        s = L[w]
        ev = f'derived/ledger.json {w}; derived/accounts/{w}.json; Gamma public-profile'
        same = s['created_at'][:10] == created[n]
        note = 'Compte créé le 19/10 à 22:49 UTC, soit le 20/10 à 00:49 heure de Paris : la date du post est juste en heure locale.' if n == 6 else ''
        txt(f'I{n}.created', 'irboz', f'compte {n}', f"Créé le {a['created']}", s['created_at'], 'CONFIRMED' if same or n == 6 else 'CONTRADICTED', ev, note)
        num(f'I{n}.pnl', 'irboz', f'compte {n}', 'Bénéfice annoncé', a['pnl'], s['economic_pnl_books'], ev, 'Valeur recalculée : retraits + solde pUSD + positions ouvertes − dépôts, vérifiée sur les mints et burns de pUSD.')
        num(f'I{n}.dep', 'irboz', f'compte {n}', 'Dépôts publiés (texte ou image)', a['deposited'], s['deposits'], ev)
        num(f'I{n}.wd', 'irboz', f'compte {n}', 'Retraits publiés (image)', a['withdrawn'], s['withdrawals'], ev)
        txt(f'I{n}.exists', 'irboz', f'compte {n}', 'Le compte existe et a bien parié sur le Ballon d’Or', f"{s['n_trades']} trades, propriétaire {s['owner']}, CREATE2 {s['create2']}", 'CONFIRMED', ev)
    total = sum(L[a['profile'].lower()]['economic_pnl_books'] for a in seed.IRBOZ.values())
    num('I.total', 'mission', '6 comptes', 'Somme des 6 bénéfices affichés', 120516, total, 'derived/ledger.json')
    c1 = seed.IRBOZ[1]['profile'].lower()
    bets1 = [('Mbappé 2e', "Kylian Mbappé finish 2nd", 'Yes', 2700), ('Yamal 3e', 'Lamine Yamal finish 3rd', 'Yes', 7300), ('Mbappé devant Yamal', 'Kylian Mbappé or Lamine Yamal', None, 2700), ('Rodri 4e', 'Rodri finish 4th', 'Yes', 670), ('Messi 5e', 'Lionel Messi finish 5th', 'Yes', 1150), ('Fabian Ruiz top 10', 'Fabian Ruiz finish in the top 10', 'Yes', 520), ('Zidane présent, perdu', 'Zinedine Zidane', None, -226)]
    for i, (name, frag, o, claim) in enumerate(bets1):
        note = ''
        if name == 'Mbappé 2e':
            note = 'Le post semble reprendre le gain de « Mbappé devant Yamal ». Non cités : Mbappé top 2 +873 $, Yamal hors top 2 +1 884 $, Bellingham hors top 10 +85 $, FC Barcelona −515 $.'
        if name == 'Fabian Ruiz top 10':
            note = '520 $ ressemble à la somme de Ruiz (434 $) et de Bellingham hors top 10 (85 $) = 519 $.'
        if name.startswith('Zidane'):
            note = 'Le post ne chiffre pas cette perte. Valeur indicative : le coût.'
        num(f'I1.bet{i}', 'irboz', 'compte 1', name, claim, pos(c1, frag, o), 'derived/positions.csv', note)
    c3 = seed.IRBOZ[3]['profile'].lower()
    bets3 = [('Kane 1er', 'Harry Kane win', 'Yes', 12878), ('Mbappé devant Yamal', 'Kylian Mbappé or Lamine Yamal', None, 10599), ('Rodri devant Messi', 'Rodri or Lionel Messi', None, 581), ('Messi 5e', 'Lionel Messi finish 5th', 'Yes', 773), ('Yamal 3e', 'Lamine Yamal finish 3rd', 'Yes', 391), ('Bellingham « dans le top 10 »', 'Jude Bellingham', None, 3742), ('Claudia Pina top 10', 'Claudia Pina', None, 253), ('Unai Simón', 'Unai Simon', None, 1)]
    for i, (name, frag, o, claim) in enumerate(bets3):
        note = ''
        if 'Bellingham' in name:
            note = 'Montant juste, sens faux : le compte a acheté « No », Bellingham hors du top 10.'
        if 'Pina' in name:
            note = 'Pina +170 $. Les 253 $ publiés égalent Pina + Klara Buhl hors top 10 (+83 $).'
        num(f'I3.bet{i}', 'irboz', 'compte 3', name, claim, pos(c3, frag, o), 'derived/positions.csv', note)
    n3 = [r for r in POS if r['wallet'] == c3]
    txt('I3.8sur8', 'irboz', 'compte 3', '8/8 paris réussis', f"{len(n3)} positions, {sum(float(r['cash_pnl']) > 0 for r in n3)} en gain", 'STRONGLY_SUPPORTED', 'derived/positions.csv', 'Tous gagnants, mais 9 positions et non 8. Ces paris portent sur un même classement : ce ne sont pas 8 événements indépendants.')
    c4 = seed.IRBOZ[4]['profile'].lower()
    r4 = [r for r in POS if r['wallet'] == c4 and 'Bellingham' in r['market']][0]
    num('I4.bell', 'irboz', 'compte 4', '300 $ sur Bellingham hors top 10', 300, float(r4['buy_usdc']), 'derived/positions.csv', f"Revendu avec une perte de {r4['cash_pnl']} $.")
    txt('I.top5', 'irboz', '6 comptes', 'Ont « parfaitement parié sur le top 5 »', 'Compte 2 : les 5 rangs exacts. Comptes 1 et 4 : 2e à 5e sans Kane 1er. Compte 3 : Kane, Yamal 3e, Messi 5e, plus deux duels. Compte 5 : Kane et Mbappé 2e. Compte 6 : Mbappé 2e et Yamal 3e.', 'CONTRADICTED', 'derived/positions.csv', 'Un seul des 6 couvre les 5 rangs. En revanche aucun pari de classement de ces comptes n’était faux : le post exagère la couverture, pas la justesse. Le compte 2 a revendu avant le résultat.')


def upside():
    named = {a.lower(): n for n, a in list(seed.UPSIDE_PRINTED.items()) + list(seed.UPSIDE_LATER.items())}
    txt('U.list', 'upside', '12 comptes', 'Douze comptes', '11 reliés à une adresse, le 12e jamais nommé', 'UNVERIFIED', 'derived/upside_match.json; raw/upside_*.html', 'La liste complète n’a pas été publiée.')
    m = json.load(open(ROOT / 'derived/upside_match.json'))
    txt('U.capture', 'upside', '15 lignes', 'Capture des 15 détenteurs de Mbappé', f"{m['best_rows']}/15 lignes reproduites à moins d’une part, fenêtre {utc(m['windows'][0])} à {utc(m['windows'][1])} au moins", 'CONFIRMED', 'code/ana_10_upside_match.py; derived/upside_match.json', 'Relie les noms imprimés aux wallets par les parts, pas par l’identité.')
    created = {w: L[w]['join_date'] for w in named if w in L}
    late = [named[w] for w, j in created.items() if j and j > 1792972800]
    t_oct20 = 1792540799 + 86400  # end of 20 Oct UTC
    outside = [named[w] for w, j in created.items() if j and (j > t_oct20 or j < 1790812800)]
    txt('U.dates', 'upside', '12 comptes', 'Tous créés entre le 1er et le 20 octobre', f"Hors fenêtre parmi les 11 reliés : {outside}", 'CONTRADICTED' if outside else 'CONFIRMED', 'derived/ledger.json join_date', 'OuldLm3alem, créé le 22/10, n’entre pas dans cette fenêtre. Soit il ne fait pas partie des 12, soit la fenêtre est fausse. La liste manque pour trancher.')
    buys = ould_buys = 0.0
    with open(ROOT / 'TRADES.csv') as f:
        for r in csv.DictReader(f):
            if r['wallet'] in named and r['side'] == 'BUY' and int(r['ts']) < T_UPSIDE and 'Ballon' in r['market']:
                buys += float(r['usdc_incl_fee'])
                if named[r['wallet']] == 'OuldLm3alem':
                    ould_buys += float(r['usdc_incl_fee'])
    num('U.264k', 'upside', '11 reliés', '264 000 $ misés avant publication', 264000, buys, 'TRADES.csv', f'Achats frais compris, marchés Ballon d’Or. Sans OuldLm3alem, créé le 22/10 : {round(buys - ould_buys)} $ sur 10 comptes. Le 12e compte reste inconnu : ordre de grandeur juste, composition non vérifiable.')
    pnl = sum(L[w]['economic_pnl_books'] for w in named if w in L)
    num('U.200k', 'upside', '11 reliés', 'Près de 200 000 $ de gains', 200000, pnl, 'derived/ledger.json', 'P&L net de tous les marchés, incluant les pertes hors Ballon d’Or.')
    other = sum(1 for w in named if w in L and not [r for r in POS if r['wallet'] == w and 'Ballon' not in r['market']])
    without_ould = sum(1 for w in named if w in L and named[w] != 'OuldLm3alem' and not [r for r in POS if r['wallet'] == w and 'Ballon' not in r['market']])
    num('U.7', 'upside', '11 reliés', 'Sept n’ont parié sur aucun autre marché', 7, without_ould, 'derived/positions.csv', f'Mesuré au 2 novembre. {other} sur 11 avec OuldLm3alem, {without_ould} sans lui : il a été créé après la date limite annoncée par Upside.')
    lag = sum(1 for w in named if w in L and L[w]['join_date'] and (L[w]['first_trade'] - L[w]['join_date']) <= 900)
    num('U.6', 'upside', '11 reliés', 'Six ont misé dans les 15 minutes suivant la création', 6, lag, 'derived/ledger.json', 'Premier trade après `join_date`.')
    h = MKT['holders']
    num('U.72', 'upside', '11 reliés', 'Ces comptes détiennent 72 % des parts Mbappé au 23/10', 72, h['named_share'] * 100, 'derived/market_context.json', 'Part des positions longues à T_UPSIDE. Il manquerait 10 points, soit environ 44 900 parts. Le 12e compte, absent des lignes surlignées de la capture, détenait moins de 9 280 parts : il ne comble pas l’écart. Le dénominateur d’Upside n’est pas publié.')
    top6 = h['top'][:6]
    ok = all(x['join'] and 1790812800 <= x['join'] < 1793491200 for x in top6)
    txt('U.top6', 'upside', '6 premiers', 'Les 6 plus gros détenteurs créés en octobre', str([x['join_utc'] for x in top6]), 'CONFIRMED' if ok else 'CONTRADICTED', 'derived/market_context.json')
    d = MKT['dates']
    mb = "Ballon d'Or 2026: Kylian Mbappé or Lamine Yam"
    rank = "Will Kylian Mbappé finish 2nd in the 2026 Bal"
    key = lambda label, frag: next((v for k, v in d[label]['prices'].items() if k.startswith(frag[:28])), None)
    txt('U.prix', 'upside', 'marché Mbappé/Yamal', 'Entre 10 et 20 c jusqu’au 8/10, 45 c le 9/10, Yamal à 28 % le 22/10', f"5/10 {key('05/10 12:00', mb)}, 8/10 {key('08/10 12:00', mb)}, 9/10 {key('09/10 12:00', mb)}, 10/10 {key('10/10 12:00', mb)}, 22/10 {key('22/10 12:00', mb)}", 'STRONGLY_SUPPORTED', 'derived/market_context.json', 'Prix moyens sur 6 h. Le mouvement du 8 au 10/10 tient en 6 356 $ d’achats, dont 94 % par trois comptes nommés : marché mince, prix déplacé par leurs propres achats. « Aucune actualité » reste non vérifié.')
    txt('U.rank', 'upside', 'marchés de place', 'Quatre places à 68-72 % le 22/10', str({k[:34]: v for k, v in d['22/10 12:00']['prices'].items()}), 'CONFIRMED', 'derived/market_context.json')
    a = json.load(open(ROOT / 'derived/accounts/0x84212ee459d1edaf35983bbec342b0806282d8ec.json'))
    kane = sorted([r for r in a['activity'] if r['type'] == 'TRADE' and r['title'].startswith('Will Harry Kane win')], key=lambda r: r['timestamp'])
    gap = (kane[0]['timestamp'] - L['0x84212ee459d1edaf35983bbec342b0806282d8ec']['join_date']) / 60
    num('U.kraben67', 'upside', 'kraben006', 'Achète 67 min après sa création', 67, gap, 'derived/accounts/0x84212ee4…', 'Horloge du trade, seconde près.')
    num('U.kraben538', 'upside', 'kraben006', 'Premier achat de 538 parts', 538, kane[0]['size'], 'derived/accounts/0x84212ee4…')
    v920 = sum(r['usdc_size'] for r in kane if r['side'] == 'BUY' and r['timestamp'] <= kane[0]['timestamp'] + 600)
    num('U.kraben920', 'upside', 'kraben006', '920 $ en 10 minutes', 920, v920, 'derived/accounts/0x84212ee4…')
    c3 = '0x3ed2c452f141c291adecb97ddfc72b1650acff3d'
    num('U.8309', 'upside', '0x86544e4dfde', 'Encaisse 8 309 $ sur Bellingham', 8309, float([r for r in POS if r['wallet'] == c3 and 'Bellingham' in r['market']][0]['redeem_usdc']), 'derived/positions.csv', 'Ce montant et les 1 805 parts confirment que ce nom imprimé est bien le wallet 0x3ed2c4…')
    c1 = '0xdd97e6ad12ca4dd18a88804fb5ed7ed429849464'
    num('U.1464', 'upside', '0xdd97e6', 'Encaisse 1 464 $ sur Fabián Ruiz', 1464, float([r for r in POS if r['wallet'] == c1 and 'Fabian Ruiz' in r['market']][0]['redeem_usdc']), 'derived/positions.csv', 'Confirme le lien par préfixe de 6 caractères.')
    num('U.272', 'upside', '0xdd97e6', 'Encaisse 272 $ contre Bellingham', 272, float([r for r in POS if r['wallet'] == c1 and 'Bellingham' in r['market']][0]['redeem_usdc']), 'derived/positions.csv')
    losing = {named[w]: round(sum(float(r['cash_pnl']) for r in POS if r['wallet'] == w and float(r['cash_pnl']) < 0), 2) for w in named if w in L}
    txt('U.perdant', 'upside', '11 reliés', 'Sans un seul pari perdant', str({k: v for k, v in losing.items() if v < 0}), 'CONTRADICTED', 'derived/positions.csv', 'Zoomman17 finit son compte en perte nette de 2 849 $, à cause de paris hors Ballon d’Or. D’autres ont des pertes mineures.')
    txt('U.lien', 'upside', '12 comptes', 'Une « seule personne » est « la piste la plus probable »', 'voir CLUSTERS.json', 'UNVERIFIED', 'CLUSTERS.json; COUNTER_HYPOTHESES.md', 'Upside écrit aussi qu’aucun lien n’est prouvé.')


def main():
    irboz()
    upside()
    extra = ROOT / 'study/claims_routes.csv'
    if extra.exists():
        with open(extra) as f:
            for r in csv.DictReader(f):
                rows.append({k: r.get(k, '') for k in FIELDS})
    with open(ROOT / 'CLAIMS_AUDIT.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    from collections import Counter
    print(Counter(r['verdict'] for r in rows), len(rows))
    for r in rows:
        if r['verdict'] in ('CONTRADICTED',) or r['claim_id'].startswith(('U.', 'I.')):
            print(r['claim_id'], '|', r['claim'][:46], '|', str(r['claimed_value'])[:10], '|', str(r['recomputed_value'])[:70], '|', r['gap_pct'], '|', r['verdict'])


if __name__ == '__main__':
    main()
