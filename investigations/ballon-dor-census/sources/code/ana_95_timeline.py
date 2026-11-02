"""TIMELINE.md: UTC chronology of funding, bets, public information and resolutions. Account rows come from derived/ledger.json and the activity files. Public rows carry their source and how far it was checked."""
import csv
import glob
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import net

ROOT = net.ROOT
PUBLIC = [
    ('2026-09-28', 'Clôture du vote du jury, selon la presse', 'Upside 27/10, Bourse Inside. Aucune source primaire de France Football lue : **non vérifié**.'),
    ('2026-10-19 14:47:34', 'Ouverture du marché « 2e place » et, à 14:48:36, « 3e place »', 'Gamma `startDate`, `derived/markets.csv`'),
    ('2026-10-19', 'Presse : Kane à 67,6 % sur Polymarket', 'yen.com.gh, repris en recherche web, non archivé ici'),
    ('2026-10-20 19:32:36', 'Ouverture des marchés « 4e » et « 5e place »', 'Gamma `startDate`, `derived/markets.csv`'),
    ('2026-10-23 15:17:49', '**Upside publie** : 264 000 $, 12 comptes, scénario Kane, Mbappé, Yamal, Rodri, Messi', '`raw/upside_initial_20261102.html`, champ `datePublished`'),
    ('2026-10-26 17:15', 'Le site du Ballon d’Or laisse paraître trois articles nommant Kane, Yamal, Mbappé', 'Presse, heure GMT rapportée, non archivée ici'),
    ('2026-10-26 20:00:00', 'Début annoncé de la cérémonie à Londres', 'Page UEFA du 19/10, citée par `research_notes/.../public_case.md`, non relue ici'),
    ('2026-10-26 22:30', 'Le prix de Kane atteint 0,999 dans la demi-heure qui suit', 'Tape, `derived/census_trades.jsonl.gz`'),
    ('2026-10-27 01:57:50', 'Marché « Kane vainqueur » fermé, résolu', 'Gamma `closedTime`, `derived/markets.csv`'),
    ('2026-10-27 18:07:00', 'Upside publie sa suite, nomme OuldLm3alem et 0xdd97e6', '`raw/upside_suivi_20261102.html`'),
    ('2026-10-30', 'France Football : enquête ouverte, police prévenue, selon la presse', 'britbrief, foot-africa, non archivés ici'),
    ('2026-10-31 18:26:36', '**@irboz publie** son enquête sur 6 comptes', '`raw/x_post/irboz_fxtwitter.json`'),
]


def utc(ts):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(ts))


def main():
    L = json.load(open(ROOT / 'derived/ledger.json'))
    ev = [(d, f'Public : {t}', s) for d, t, s in PUBLIC]
    for w, s in L.items():
        name = (s['labels'][-1].replace('upside:', '') if s['labels'] != ['manual'] else (s.get('name') or w[:10]))
        tag = ' + '.join(x for x in s['labels'] if x.startswith('irboz')) if any(x.startswith('irboz') for x in s['labels']) else ('non nommé' if s['labels'] == ['manual'] else 'Upside')
        src = f'`derived/accounts/{w[:10]}….json`'
        if s['join_date']:
            ev.append((utc(s['join_date']), f"{name} ({tag}) : création du compte", src))
        a = json.load(open(ROOT / f'derived/accounts/{w}.json'))
        for r in a['activity']:
            if r['type'] in ('DEPOSIT', 'WITHDRAWAL'):
                verb = 'dépôt' if r['type'] == 'DEPOSIT' else 'retrait'
                ev.append((utc(r['timestamp']), f"{name} : {verb} de {r['usdc_size']:,.2f} $".replace(',', ' '), f"tx `{r['transaction_hash'][:14]}…`"))
        if s['first_trade']:
            ev.append((utc(s['first_trade']), f"{name} : premier trade", src))
        if s['last_trade']:
            ev.append((utc(s['last_trade']), f"{name} : dernier trade", src))
    ev.sort(key=lambda x: x[0])
    with open(ROOT / 'TIMELINE.md', 'w') as f:
        f.write('# Chronologie UTC\n\nToutes les heures sont en UTC. Paris est à UTC+2 jusqu’au 25 octobre 01:00 UTC, puis UTC+1. Lignes de comptes tirées de l’API Data et vérifiées sur les mints et burns de pUSD (`derived/ledger.json`). Une ligne ne dit rien de la personne derrière un wallet.\n\n')
        f.write('| Date et heure | Événement | Source |\n|---|---|---|\n')
        for d, t, s in ev:
            f.write(f'| {d} | {t} | {s} |\n')
    print(len(ev), 'lines')


if __name__ == '__main__':
    main()
