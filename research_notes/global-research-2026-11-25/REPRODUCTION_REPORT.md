# Rapport de reproduction

Date : 25 novembre 2026. Branche de travail distincte de `main`. Aucun chiffre accepté des semaines W16 à W46 n'est réécrit.

## Test figé du 13 novembre

Le test primaire T1 a été réécrit ici, sans importer `research_notes/early-detection-2026-11-13/study/code/stats.py`. La queue de Poisson-binomiale est recalculée sur les 45 lignes `VALIDATION` et `lonely_thin` de `analytic_table.jsonl`.

| Quantité | Publié | Recalculé |
|---|---:|---:|
| n | 45 | 45 |
| gains | 13 | 13 |
| prix moyen | 0,2538753111111111 | identique |
| excès | 0,03501357777777775 | identique |
| p unilatéral | 0,3345912628416912 | identique |
| événements | 44 | 44 |
| initiateurs | 45 | 45 |

Le verdict publié reste `NOT_SUPPORTED`. Le seuil corrigé pour 18 comparaisons est 0,002777…, très au-dessous de 0,33. `NO_EDGE_VALIDATED` ne change pas.

La table contient 48 lignes `lonely_thin`, pas 45. Les trois lignes supplémentaires sont dans `DISCOVERY` et ont toutes gagné. Les ajouter au test serait une erreur de sélection. Le protocole publié les laisse dehors. Cette note confirme cette exclusion. Ce n'est pas une correction d'un chiffre faux.

## Contrôle même marché, même jour, même côté

Sur 587 cellules (condition, jour UTC, côté), aucune n'a deux lignes. Les 45 alertes de validation n'ont donc aucun pair dans la table. Le contrôle demandé est `NOT_TESTABLE` à partir des données engagées. Aller chercher les autres acheteurs du même jour exigerait une bande d'ordres que cette session n'a pas reconstituée. Le résultat négatif déjà publié n'est pas transformé en contrôle apparié.

## Semaine 2026-W47

Le collecteur existant `weekly_funding.refresh` a tourné le 25 novembre 2026, après la clôture de la semaine (16 au 22 novembre). Le commit de départ est `9c27933`. Les journaux et le rapport sont sous `w47/`.

| Mesure | ChangeNOW | Tornado Cash |
|---|---:|---:|
| Comptes vérifiés (`CONFIRMED_DIRECT` ou `SUPPORTED_INDIRECT`) | 0 | 0 |
| USD de financement vérifié | 0,00 | 0,00 |
| Destinataires exacts Polymarket, niveau `POSSIBLE` | 1 | 0 |
| USD de ces reçus exacts | 8,93 | 0,00 |
| Échantillon actif de la semaine | 856 | 856 |

Les dix comparaisons du protocole figé sont `NOT_TESTABLE` (0 paire éligible, p nul). L'archive native Ethereum n'a pas de semaine capturée pour W47. Le dénominateur de toute la plateforme reste `UNKNOWN`.

Le reçu exact est un transfert de 8,933289 USDC.e, transaction `0x030557a6754871a8955cddb57a6312b04d27a4e7ab8377774236d62c96936311`, journal 2, bloc Polygon 97395179, 16 novembre 2026 à 03:03:58 UTC, de `0xf2020cbfc13fd5d4cb2da0ff8ae2d2c093c1c423` vers `0x74a7ff3574d91545a947bce48ef7b1c9452c56cb`. Le niveau du collecteur est `POSSIBLE`, parce que la route est mélangée. L'API a ensuite vu un achat de 1,010989 USD le 18 novembre à 03:00:25 UTC sur le marché « ATP World Tour Finals, Ivan Lendl Group: Carlos Alcaraz vs Daniil Medvedev », avec un PnL économique observé de 0,271061 USD à l'horodatage 24 novembre 2026. L'ordre temporel ne prouve pas que les 8,93 unités ont payé cet achat.

Deux autres adresses apparaissent dans le grand livre avec la relation `signer_only_no_final_transfer`. Elles ne sont pas des reçus exacts et ne sont pas comptées dans le 8,93.

Le brut Tornado de niveau `UNKNOWN` est 63 873 531,26 USD, avec un financement Polymarket de 0,00. Ce brut est l'activité des pools, pas un financement de comptes de marché. Le brut ChangeNOW de niveau `POSSIBLE` est 1 363 711,70 USD, dont 8,93 seulement arrivent sur une adresse de trading exacte dans les chemins contrôlés.

## Cohorte f2020

Le rapport machine de W47 reprend les comptes déjà produits par le collecteur : 3 408 bénéficiaires, 158 enregistrements de parieurs, 153 adresses de trading distinctes. Le fichier historique des bénéficiaires n'est pas dupliqué. Son rapport antérieur a l'empreinte SHA-256 `fed5e9193ffa7d9401f4d42d02fdefef6fc7b3c1752bdc8ed66339f3763a3c73`. Un tiers qui possède ce dépôt peut relancer `verify.py` sans réseau et retrouver ces contrôles. Il ne peut pas, à partir de cette seule note, réattribuer chaque bénéficiaire historique à un déposant.

## Seconde passe

Le contrôle de cellule et la trésorerie Inca sont dans `data/same_cell.json` et `data/inca_activity.json`. Les tests les relisent hors ligne. Le collecteur qui les a produits est `code/public_fetch.py`. Il a besoin du réseau. Il retire le nom, la biographie et l'image.

La cohorte f2020 se recompte par `code/f2020_cohort.py` depuis `investigations/changenow-polymarket/sources`. Les six comptes et l'empreinte SHA-256 collent au rapport hebdomadaire. Un tiers qui a ce dépôt n'a pas besoin de la machine d'origine pour ces comptes. Il ne réattribue pas pour autant chaque bénéficiaire à un déposant.

`luck_pvalue` de vsbtc, exécuté sur les 45 lignes, colle à notre p au bruit de virgule flottante près. Les 588 millions de transactions n'ont pas été comptées. Deux fichiers parquet publics l'ont été : 729 133 marchés et 316 429 événements.

## Ce qui n'a pas été reproduit

Le backtest de coût de pselamy, les tests de rwondo, le pipeline complet de vsbtc, les graphes de financement Inca, et les listes de 39 et de 152 adresses. Ces listes ne sont pas dans les pages lues.
