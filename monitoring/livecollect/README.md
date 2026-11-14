# Collecte prospective

Ce programme tourne tant que le processus tourne. Il ne survit pas à l'arrêt de la machine. La session cloud qui a produit la pull request s'arrête avec sa machine virtuelle. Le Mac du dépôt n'est pas un hôte fiable s'il dort. Lancer la collecte sur une machine Linux qui reste allumée.

Les flux restent sur la machine. Aucun secret n'est lu.

## Installation

Depuis la racine du dépôt :

```bash
python3 -m pip install -r monitoring/livecollect/requirements.txt
```

La dépendance épinglée est `websockets==15.0.1`. Le reste est la bibliothèque standard.

## Lancer

```bash
python3 -m monitoring.livecollect collect \
  --markets research_notes/forensic-engine-2026-11-13/data/prospective_markets.json \
  --out /var/phi
```

`--seconds` vaut 120 par défaut. Pour une session d'une heure, ajouter `--seconds 3600`. Le superviseur utilise déjà 3600 secondes. Cette durée est celle du processus WebSocket. Elle ne cadence plus les trades.

Le fichier de marchés contient 20 marchés encore ouverts le 13 novembre 2026, avec le token Yes. Dix-neuf sont des marchés neg-risk. Le WebSocket `wss://ws-subscriptions-clob.polymarket.com/ws/market` fournit le carnet et les prix.

Les trades viennent de `https://data-api.polymarket.com/v2/trades`, à part. Toutes les 90 secondes (`--trade-poll`), chaque marché est paginé depuis le plus récent jusqu'au dernier trade déjà couvert. Ce point est gardé dans `state.json`, clé `hwm`, avec l'horodatage et le hash. Un plafond de pages avant ce point écrit une ligne `kind=trade_page_cap` dans `gaps.jsonl` et une ligne `complete: false` dans `coverage.jsonl`. Ce n'est pas une absence de trades. Le plafond documenté de cette route est 300 requêtes / 10 s. Le client reste autour de 4 requêtes/s et respecte `Retry-After` sur 429 et 503.

Chaque nouveau hash est mis en file (`receipt_queue`) et relu sur `https://polygon-bor-rpc.publicnode.com`, sans plafond de cinq. La file reprend après une coupure. Un hash déjà présent dans `chain.jsonl` n'est pas redemandé.

## Reprise

```bash
scripts/livecollect_supervise.sh \
  research_notes/forensic-engine-2026-11-13/data/prospective_markets.json \
  /var/phi
```

Le script relance la commande après chaque sortie, avec une pause de deux secondes. Sans variable d'environnement, chaque passage dure 3600 secondes. `PHI_SECONDS` change cette durée. Ce n'est pas un service systemd. Pour l'arrêter : interrompre ce processus.

Une coupure brutale est reprise au relancement : `state.json` garde les clés déjà vues, la marque par marché et la file de reçus. Les fichiers jsonl sont ajoutés en queue. Les lignes déjà écrites restent valides, y compris celles qui n'ont pas de champ `condition`. `restarts` augmente. Un répertoire déjà rempli, par exemple `~/phi-live`, se reprend avec le même `--out` sans effacer les fichiers.

## État

```bash
python3 -m monitoring.livecollect status --out /var/phi
```

`permanent` reste `false`. Un battement est écrit toutes les 10 secondes. `uptime_ratio` additionne les écarts d'au plus 15 secondes et divise par le temps entre le premier et le dernier battement. `max_gap_s` est le plus grand trou. `uptime_s` est l'horloge murale depuis le premier démarrage, trou compris.

`status` indique aussi l'espace disque, la part de `price_change` remplis, les messages non décodés et les attributions `OrderFilled`. Le détail est dans [HEALTHCHECK.md](HEALTHCHECK.md). Les lignes déjà présentes dans le répertoire ne sont pas réécrites.
