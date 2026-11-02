# Phase 9 : audit des données temporelles

Fait le 30/09/2026, avant toute mesure de mouvement de prix. Les tests d'endpoints ont été faits en direct.

| Donnée | Statut | Résolution réelle | Source / preuve |
|---|---|---|---|
| Horodatage des trades | **DISPONIBLE** | 1 seconde (entier Unix). 1,23 % des horodatages tombent sur une minute pleine, donc pas d'arrondi à la minute. | data-api `/trades`, 2 515 167 trades ≥ 100 $ (phase 8, `alltrades.pkl`) |
| Ordre d'exécution dans la même seconde | **PARTIEL** | 13,7 % des trades partagent (jeton, seconde) avec un autre trade ; data-api ne donne pas d'ordre. L'ordre exact n'existe que on-chain (bloc ≈ 2 s + `logIndex`). | fills OrderFilled phase 2 (14 290 lignes, fenêtres Maduro et Iran) ; ailleurs, uniquement via Etherscan `getLogs`, coûteux |
| Prix, taille, side, wallet (proxy), marché, jeton/outcome, hash | **DISPONIBLE** | par trade | data-api (`price`, `size`, `side` du preneur, `proxyWallet`, `conditionId`, `asset`, `outcomeIndex`, `transactionHash`) |
| Trades < 100 $ | **PARTIEL** | non collectés en phase 8 (filtre `CASH ≥ 100`) ; récupérables par data-api, avec plafond d'offset | — |
| Densité des trades ≥ 100 $ | mesurée | écart médian entre trades d'un marché : **602 s** (P25 194 s, P75 1 888 s) ; 386 trades par marché en médiane | calcul local |
| Série de prix CLOB | **PARTIEL** | **1 minute au minimum** (`fidelity=0.1` renvoie les mêmes points à la minute) ; 7 jours au plus par appel | `clob.polymarket.com/prices-history` ; déjà récupérée pour 30 108 événements de phase 8 (T − 65 min → T + 6 h) |
| Meilleur bid, meilleur ask, mid, spread, profondeur **historiques** | **ABSENT** | — | `/book`, `/midpoint`, `/spread` ne répondent que pour un carnet vivant (404 sur un marché fermé) |
| Proxy de bid/ask par trades | **PARTIEL (inféré)** | à la seconde, quand un trade existe | prix d'un achat preneur ≈ ask ; prix d'une vente preneuse ≈ bid |
| Historique des trades CLOB | **ABSENT** sans clé API | — | `/trades` renvoie 401 (clé exigée, non créée) |
| Pose et annulation d'ordres | **ABSENT** | — | aucun endpoint public ; le on-chain ne voit que les fills |
| Exécution on-chain (OrderFilled) | **PARTIEL** | bloc (~2 s) + `logIndex` | Etherscan `getLogs` ; fenêtres Maduro et Iran déjà disponibles localement |
| Heure d'annonce publique | **INCONNU** (non vérifié) | — | phase 2 : repricing mesuré à 06:16 (Maduro) et 06:13 (Iran) ; annonces « ~05:50-06:00 » et « ~06:35 » issues d'une chronologie non revérifiée |

## Conséquences pour la phase 9

1. **Résolution effective du mouvement de prix : la minute.** La série de trades est à la seconde mais dense seulement par moments. Les horizons +1, +5, +10 et +30 s ne sont mesurés que lorsqu'un trade existe dans la fenêtre ; sinon, ils sont notés « sans observation ».
2. **Exécution simulée :**
   - le prix d'entrée est celui des achats réellement exécutés par d'autres wallets après le signal (proxy de l'ask) ;
   - le prix de sortie est celui des ventes réellement exécutées (proxy du bid) ;
   - la taille est plafonnée par le volume réellement observé ;
   - sans profondeur historique, le glissement est **inféré**, jamais mesuré.
3. **Frais preneurs 2026 :**
   - modélisés à 0,02 × min(p, 1 − p) par action, soit 1 centime à p = 0,5, ce qui correspond à la catégorie « politique » ;
   - scénario avec frais et scénario sans frais, car le statut `feesEnabled` de chaque marché n'est pas historisé.
4. **Spoofing, pose et annulation d'ordres :** hors de portée. **INCONNU.**
