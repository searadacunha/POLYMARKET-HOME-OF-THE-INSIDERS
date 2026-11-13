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

`--seconds` vaut 120 par défaut. Pour une session d'une heure, ajouter `--seconds 3600`.

Le fichier de marchés contient 20 marchés encore ouverts le 13 novembre 2026, avec le token Yes. Dix-neuf sont des marchés neg-risk. Le WebSocket `wss://ws-subscriptions-clob.polymarket.com/ws/market` fournit le carnet et les prix. Les portefeuilles viennent de `https://data-api.polymarket.com/v2/trades`, une source séparée. Cinq hashs de transaction au plus sont relus sur `https://polygon-bor-rpc.publicnode.com`.

## Reprise

```bash
scripts/livecollect_supervise.sh \
  research_notes/forensic-engine-2026-11-13/data/prospective_markets.json \
  /var/phi
```

Le script relance la commande après chaque sortie, avec une pause de deux secondes. Sans variable d'environnement, chaque passage dure 3600 secondes. `PHI_SECONDS` change cette durée. Ce n'est pas un service systemd. Pour l'arrêter : interrompre ce processus.

Une coupure brutale est reprise au relancement : `state.json` garde les clés déjà vues, les fichiers jsonl sont ajoutés en queue, et `restarts` augmente.

## État

```bash
python3 -m monitoring.livecollect status --out /var/phi
```

`permanent` reste `false`. Un battement est écrit toutes les 10 secondes. `uptime_ratio` additionne les écarts d'au plus 15 secondes et divise par le temps entre le premier et le dernier battement. `max_gap_s` est le plus grand trou. `uptime_s` est l'horloge murale depuis le premier démarrage, trou compris.
