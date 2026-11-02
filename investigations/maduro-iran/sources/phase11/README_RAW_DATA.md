# Phase 11 : données brutes (`donnees/brut_p11/`)

Collecte démarrée le **01/10/2026 à 08:51 UTC**, par `scripts/p11_clob_collector.py` et `scripts/p11_signal_listener.py`. Chaque processus est lancé et relancé par `scripts/p11_run.sh`. Recherche uniquement : aucun ordre n'est passé.

## Format commun

- Fichiers horaires compressés en **zstd niveau 12**, une trame vidée toutes les 60 s. En cas d'arrêt brutal, on perd au plus 60 s de données. La dernière trame d'un fichier ouvert peut être incomplète.
- Une ligne JSON par message : **`[t_local_ns, connexion, message]`**
  - `t_local_ns` : heure locale de réception en nanosecondes ;
  - `connexion` : identifiant de la connexion (`c0`, `c1`… pour le carnet, `rtds`, ou une étiquette REST) ;
  - `message` : **chaîne brute telle que reçue**, sans aucune transformation, ou objet JSON pour les réponses REST.
- Correction d'horloge : `meta/clock.jsonl` (sntp toutes les 30 min). Heure vraie ≈ `t_local_ns` + décalage (+0,088 s au démarrage).

## Répertoires

| Chemin | Source | Résolution | Contenu |
|---|---|---|---|
| `ws_market/AAAA-MM-JJ/HH_cN.jsonl.zst` | `wss://ws-subscriptions-clob.polymarket.com/ws/market` | événement (horodatage d'échange en ms) | `book` (carnet complet), `price_change` (nouvelle taille par niveau, best bid / best ask, hash), `best_bid_ask`, `last_trade_price` (prix, taille, côté preneur, `fee_rate_bps`, hash de transaction) |
| `rtds/AAAA-MM-JJ/HH.jsonl.zst` | `wss://ws-live-data.polymarket.com`, topic `activity/trades` | trade (horodatage en s) | tous les trades de la plateforme, une ligne par participant : `proxyWallet`, côté, jeton, prix, taille, `fee` (preneur), `transactionHash`, slug |
| `chain/AAAA-MM-JJ/HH*.jsonl.zst` | nœud Polygon public `wss://polygon-bor-rpc.publicnode.com` (`eth_subscribe`) | bloc | logs OrderFilled v2 dont le maker est un wallet SIG_HIST (historique ou éligible) et en-têtes de blocs (`newHeads`). Du 01/10 09:10 à 09:17 UTC, tous les OrderFilled (sans filtre) |
| `rest_books/AAAA-MM-JJ/HH.jsonl.zst` | `POST https://clob.polymarket.com/books` | 10 min (`rest_10min`), et rafales après alerte (`burst:<alerte>:<décalage s>`) | instantanés complets, pour le contrôle de la reconstruction |
| `meta/watchlist_*.json` | Gamma + data-api | heure | marchés suivis : niveau A (wallets SIG_HIST), C (contrôle) ou D (dynamique), jetons, catégorie, `feeSchedule`, volume, liquidité |
| `meta/subscriptions.jsonl`, `meta/etat.jsonl`, `meta/etat_courant.json`, `meta/run_*.log` | collecteur | | abonnements, erreurs, reconnexions, état, journaux |
| `meta/dynamic_watch.jsonl`, `meta/burst_requests.jsonl` | listener → collecteur | | marchés ajoutés après une alerte, rafales REST demandées |
| `backfill/backfill_<de>_<à>.jsonl.gz` | data-api `takerOnly=true`, ≥ 100 $ | trade | rattrapage du 16/09/2026 au démarrage, réponses brutes par marché |
| `live/alerts.jsonl` | listener | ns | alertes SIG_HIST V1 en direct : `T_obs_ns` (réception RTDS), `T_alerte_ns`, wallet, marché, jeton, scores, empreinte de la définition |
| `live/verifications.jsonl` | data-api | 60 s, puis 10 min après l'alerte | confirmation que le wallet était bien le preneur |
| `live/fae_events.jsonl` | listener | ns | tous les FAE vus en direct (réservoir des contrôles) |
| `live/wallets_eligibles_au_demarrage.json`, `live/listener.log.jsonl` | listener | | état du détecteur |
| `travail/` | `p11_execution.py` | | résultats intermédiaires recalculables |

## Rejouer l'expérience

1. **Carnet à l'instant t :** `p11_replay.Timeline([jeton], t0, t1).book_at(jeton, t)`. Il se reconstruit avec le dernier `book` reçu avant t, puis les `price_change` reçus avant t. Contrôle contre les instantanés REST : `python3 scripts/p11_replay.py --check`.
2. **Simulations :** `python3 scripts/p11_execution.py`, puis `python3 scripts/p11_analysis.py --live`.
3. **Cas Maduro et Iran (historiques) :** `python3 scripts/p11_analysis.py --cases`. Il utilise les flux complets de la phase 10 (`donnees/brut_p10/`).

## Arrêt et redémarrage

- **Arrêt propre :** créer le fichier `donnees/brut_p11/meta/STOP`, puis `pkill -TERM -f p11_clob_collector.py` et `pkill -TERM -f p11_signal_listener.py`.
- **Redémarrage,** depuis `scripts/` (détaché de la session) :
  - `nohup ./p11_run.sh collector >/dev/null 2>&1 &`
  - `nohup ./p11_run.sh listener >/dev/null 2>&1 &`
- Les processus s'arrêtent si le Mac redémarre.
- **Garde de disque :** les marchés de contrôle sont suspendus sous 6 Go libres, et tout s'arrête sous 3 Go.
