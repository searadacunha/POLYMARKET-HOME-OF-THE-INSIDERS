# Reproduire la contre-enquête

Le dossier réel est `~/Projects/PolySentinel-ballon-dor-2026`, atteint aussi par le lien `~/Projects/PolySentinel/investigations/ballon_dor_2026`. Il est hors du dossier de PolySentinel pour une raison mesurée : le quota du projet compte chaque fichier sous sa racine, et le collecteur se met en pause vers 5,94 Go. Un lien symbolique n'y compte pas (`polysentinel/storage_budget.py`).

## Principe

Chaque réponse publique est gardée telle quelle dans `raw/http/` (gzip) et inscrite dans `evidence/requests.jsonl`, avec URL, date et SHA-256. Chaque ligne du registre porte l'empreinte de la précédente : modifier ou retirer une ligne casse toutes les suivantes. Une requête déjà archivée n'est jamais refaite : relancer un script rejoue l'instantané du 2 novembre 2026, sans réseau. Pour relire la chaîne à une autre date, travailler dans une copie sans `raw/http`.

La clé Etherscan vient de `~/Downloads/.env` et n'entre ni dans les archives ni dans le registre. La clé Helius, partagée avec un bot en service, n'est pas utilisée. Aucune transaction n'est émise, aucun service privé n'est touché.

## Dépendances

- Python 3 de la machine, bibliothèque standard, pour tout sauf les permutations.
- numpy pour `ana_50`, `ana_51`, `ana_54`, `ana_55` : `PY=~/.local/share/uv/tools/graphifyy/bin/python`. Aucun paquet n'a été installé pour cette enquête. Un Python avec numpy suffit.
- Listes d'étiquettes lues dans `~/Projects/PolySentinel-flow-trace/evidence/labels`, contrôlées par `SHA256SUMS` à chaque lecture. Lecture seule.

## Ordre des commandes

```bash
cd ~/Projects/PolySentinel-ballon-dor-2026/code
export PYTHONDONTWRITEBYTECODE=1
PY=~/.local/share/uv/tools/graphifyy/bin/python

# Tests sans réseau
python3 ../tests/test_addr.py
python3 ../tests/test_sol_loop.py
python3 ana_75_cn_recipients.py selfcheck

# A. Polymarket
python3 col_10_markets.py                 # catalogue, 33 événements
python3 col_20_accounts.py                # 13 comptes publics
python3 col_30_census.py                  # 866 023 lignes de la famille
python3 col_40_wallets.py                 # owner(), CREATE2, listes Polygon, reçus
python3 ana_10_upside_match.py            # capture Upside
python3 ana_20_ledger.py                  # comptes, TRADES.csv

# E. Statistiques
python3 ana_40_population.py
python3 col_45_joindates.py
$PY ana_50_stats.py controls              # avant toute lecture
$PY ana_51_null_rate.py
$PY ana_50_stats.py build
$PY ana_50_stats.py run                   # T1 à T4
$PY ana_55_sensitivity.py                 # exploratoire
python3 ana_52_context.py
python3 ana_53_cohort.py                  # comptes non nommés
$PY ana_54_mc.py                          # descriptif

# B et D. Flux et liens
python3 col_50_relay.py                   # une requête toutes les 15 s, route retirée le 24/11/2026
python3 ana_31_btc.py
python3 col_60_walk.py $(cat ../state/main13.txt)
WALK_HOPS=2 WALK_NODES=15 WALK_TOP=5 python3 col_60_walk.py $(cat ../state/lookalikes17.txt)
python3 ana_32_relay_table.py
python3 ana_30_flows.py                   # FUNDING_FLOWS.csv, WALLETS.csv, graph.html
python3 ana_35_clusters.py                # paires, contrôle positif bloquant
python3 ana_36_clusters_out.py            # CLUSTERS.json

# C. ChangeNOW
python3 col_70_cn_universe.py             # puis l'échantillon de dépôts, voir PROTOCOL.md
python3 col_75_cn_outflows.py
python3 ana_75_cn_recipients.py collect
python3 ana_75_cn_recipients.py analyse

# Détecteurs
python3 col_80_oos_select.py              # écrit avant la lecture des trades témoins
python3 col_85_oos_tapes.py
python3 ana_60_detectors.py ballon
python3 ana_60_detectors.py oos
python3 ana_65_detector_eval.py

# Livrables
python3 ana_90_claims.py                  # CLAIMS_AUDIT.csv
python3 ana_95_timeline.py                # TIMELINE.md
python3 ana_99_verify.py                  # chaîne du registre, archives, recoupements
```

## Vérifier l'intégrité

```bash
python3 -c "import sys; sys.path.insert(0,'code'); import net; print(net.verify_ledger()); print(net.verify_archive())"
git log --format='%h %ci %s'
```

`git log` date le protocole et ses déviations. Le dépôt est local, imbriqué dans ce dossier, sans remote, et n'a aucun lien avec `~/.git`.

## Limites de la reproduction

- Une réponse d'API décrit le 2 novembre 2026. Noms de profil, soldes et étiquettes peuvent changer.
- La route `requests/v2` de Relay doit être retirée le 24 novembre 2026. Les réponses sont conservées. Après cette date, seule la preuve par la chaîne reste rejouable sans archive.
- Le budget du parcours rend le résultat dépendant de ses paramètres, écrits dans `col_60_walk.py` et `PROTOCOL.md`.
