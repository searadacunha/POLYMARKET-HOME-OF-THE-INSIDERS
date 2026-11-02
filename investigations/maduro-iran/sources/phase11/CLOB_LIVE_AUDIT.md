# Phase 11 : audit du CLOB en direct

Audit fait le 01/10/2026 vers 04:40 UTC, par tests directs sur des marchés vivants, avant d'écrire le collecteur.

**Horloge locale :** décalage de +0,088 s ± 0,048 s par rapport à `time.apple.com` (sntp). Le décalage est remesuré toutes les 30 min pendant la collecte.

## Sources

| Source | Point d'accès | Nature |
|---|---|---|
| **Websocket « market » du CLOB** | `wss://ws-subscriptions-clob.polymarket.com/ws/market`, abonnement `{"assets_ids": [...], "type": "market", "custom_feature_enabled": true}` | carnet en continu, événement par événement |
| **RTDS** (real-time data service) | `wss://ws-live-data.polymarket.com`, abonnement `{"action": "subscribe", "subscriptions": [{"topic": "activity", "type": "trades"}]}` | tous les trades de la plateforme, avec le wallet |
| REST CLOB | `/book`, `POST /books`, `/midpoint`, `/spread`, `/price`, `/tick-size`, `/fee-rate`, `/neg-risk` | instantanés à la demande (~100 ms par appel) |
| Gamma | `/markets?active=true&closed=false&end_date_min=&end_date_max=&limit=100&offset=` (offset ≤ 2 000) | métadonnées : `feesEnabled`, `feeSchedule`, `bestBid`, `bestAsk`, `liquidityClob`, `volume24hr` |
| data-api | `/trades?market=&start=&end=&takerOnly=` | trades avec wallet, a posteriori (complet, phase 10) |
| Polygon | logs OrderFilled v2 `0xe1111800` / `0xe2222d27` | bloc et logIndex, a posteriori |

## Données

| Donnée | Statut | Détail mesuré |
|---|---|---|
| Identifiant de marché (`market` = conditionId) | DISPONIBLE | dans chaque message du websocket |
| Identifiant de jeton (`asset_id`) | DISPONIBLE | dans chaque message |
| Carnet complet (tous les niveaux, prix et taille) | DISPONIBLE | événement `book` : instantané complet à l'abonnement (31 bids et 50 asks sur l'exemple), avec un `hash` |
| Mise à jour des niveaux | DISPONIBLE | `price_change` : prix, **nouvelle taille totale du niveau**, côté, `hash`, best bid et best ask après le changement. Les deux jetons d'un marché binaire sont mis à jour en miroir dans le même message (YES BUY 0,78 = NO SELL 0,22) |
| Best bid, best ask, spread | DISPONIBLE | événement `best_bid_ask` (fonctions avancées) et champs de `price_change` |
| Mid | DISPONIBLE (calculé) | (best bid + best ask) / 2 ; aussi par REST `/midpoint` |
| Profondeur par niveau | DISPONIBLE | taille par niveau, en actions |
| Trades | DISPONIBLE | `last_trade_price` : prix, taille, côté preneur, `fee_rate_bps`, `transaction_hash`, horodatage en ms |
| Wallet du trade | **PARTIEL** | absent du websocket du carnet ; présent dans RTDS (`proxyWallet`, plus les lignes makers) **2,1 s en médiane après** le `last_trade_price` du même hash (min 0,9 s, max 3,3 s, 58 transactions comparées) |
| Preneur ou maker dans RTDS | PARTIEL | RTDS donne une ligne par participant (2,6 par transaction). Le preneur est celle qui porte `fee` sur les marchés payants, ou celle qui correspond au `last_trade_price` |
| Frais payés | DISPONIBLE | RTDS `fee` (preneur) ; `fee_rate_bps` dans `last_trade_price` ; Gamma `feeSchedule` (ex. rate 0,04, exposant 1, preneur seulement, ristourne maker 0,25) |
| Hash de transaction | DISPONIBLE | `last_trade_price.transaction_hash`, RTDS `transactionHash` |
| Numéro de bloc, wallet par la chaîne | DISPONIBLE (ajouté le 01/10 à 09:10) | abonnement websocket `eth_subscribe logs` (OrderFilled v2) sur un nœud Polygon public : le log arrive **0,81 s avant RTDS en médiane** (P10 0,44 s, P90 1,1 s ; 763 transactions sur 763). Il donne le bloc, le logIndex, le maker et le preneur |
| Horodatage de l'échange | DISPONIBLE | ms dans `book`, `price_change`, `best_bid_ask` et `last_trade_price` ; seconde dans RTDS |
| Latence échange → réception | PARTIEL | réception locale − horodatage de l'échange = −66 ms en médiane avant correction d'horloge, soit **environ +20 ms** après correction (+88 ms). Fiabilité limitée par la précision sntp (± 48 ms) |
| Placements et annulations d'ordres individuels | **ABSENT** | le websocket ne donne que la taille agrégée par niveau. Une baisse sans trade correspondant = annulation (ou fill non vu), une hausse = placement ; aucun identifiant d'ordre |
| Fills par niveau d'un trade | PARTIEL | en direct : variation des niveaux entre deux `price_change`. A posteriori : data-api `takerOnly=false` (phase 10) |
| Fréquence | DISPONIBLE | par événement, sans échantillonnage |
| Granularité de prix | DISPONIBLE | `tick_size` (0,01 ou 0,001) |
| Capacité d'abonnement | mesurée | **environ 500 jetons par connexion** : à 1 000 et 1 600 jetons, seuls 46-48 instantanés `book` sont arrivés |
| Débit | mesuré | 500 jetons ≈ 190 ko/s au démarrage (instantanés compris) ; 1 600 jetons ≈ 345 ko/s ; compression zstd niveau 10 : 14,7× |

## Conséquences pour l'expérience

1. **T_obs n'est pas T0.**
   - Le trade du wallet est visible dans le carnet à T0, à environ 20 ms près.
   - Mais **SIG_HIST exige l'identité du wallet**, qui n'arrive par RTDS qu'environ 2 s plus tard.
   - L'heure de décision la plus précoce est donc T_obs = réception RTDS du trade du wallet. Toutes les latences de l'observateur se comptent depuis T_obs, avec T0 publié à côté.
   - La lecture directe des logs Polygon donne le wallet environ 0,8 s plus tôt : **T_obs_chaîne ≈ T0 + 1,3 s**. Ce flux est enregistré depuis 09:10 UTC, et les deux T_obs sont publiés.
2. **Le prix disponible à T est connu exactement** : carnet reconstruit à partir de l'instantané `book` et des `price_change` reçus avant T (heure locale). C'est la règle « carnet connu à T » du §10.
3. **Résolution réelle :** l'événement, au milliseconde côté échange. La réception locale est horodatée en ns.
4. **Annulations et placements :** seulement par niveau. On ne sait pas qui retire sa liquidité.
5. **Volume.** Un seul jeton par marché suffit, car le carnet est en miroir. Avec 700 marchés environ, on attend ~1 Go par jour compressé. Une garde de disque est prévue.
