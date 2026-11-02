# Phase 12 : ce qui est observable avant le wallet, et quand

Mesuré le 01/10/2026 sur les données brutes de la phase 11, de 08:52 à 09:50 UTC, en lecture seule. Détail par transaction : `latence_detail.csv`. Statistiques : `latence_stats.csv`.

## 1. Cartographie (§4)

| Source | Variable | Statut |
|---|---|---|
| CLOB (websocket marché) | best bid, best ask, mid, spread | OBSERVABLE_BEFORE_WALLET |
| CLOB | profondeur, niveaux, taille par niveau | OBSERVABLE_BEFORE_WALLET |
| CLOB | changements de niveaux (`price_change`, ~20 ms avant le trade correspondant) | OBSERVABLE_BEFORE_WALLET |
| CLOB | prix, taille et horodatage du trade (`last_trade_price`) | OBSERVABLE_BEFORE_WALLET |
| CLOB | sens du trade (`side`, côté preneur) | OBSERVABLE_BEFORE_WALLET |
| CLOB | hash de transaction | OBSERVABLE_BEFORE_WALLET : il ne révèle pas le wallet tant que le bloc n'est pas lu |
| On-chain | hash, bloc, horodatage, `OrderFilled`, token, montant | OBSERVABLE_ONLY_AFTER_WALLET : ces données arrivent dans le même message que le maker et le preneur |
| On-chain | maker, preneur | OBSERVABLE_ONLY_AFTER_WALLET (c'est le wallet) |
| RTDS | horodatage, trade, wallet | OBSERVABLE_ONLY_AFTER_WALLET |

**Avant le wallet, seul le carnet est disponible**, avec les trades anonymes.

## 2. Latences réelles (§5)

| Délai | n | Moyenne | Médiane | P10 | P25 | P75 | P90 | Max |
|---|---|---|---|---|---|---|---|---|
| CLOB → ON-CHAIN | 59 | 4,92 s | 1,62 s | 0,55 s | 0,83 s | 4,82 s | 14,09 s | 25,81 s |
| CLOB → WALLET (RTDS) | 575 | 1,76 s | **1,80 s** | 0,92 s | 1,32 s | 2,24 s | 2,60 s | 3,26 s |
| ON-CHAIN → WALLET (RTDS) | 59 | −3,22 s | 0,50 s | −12,79 s | −3,61 s | 0,87 s | 1,07 s | 1,19 s |
| **CLOB → WALLET, voie la plus rapide** (chaîne ou RTDS) | 575 | 1,71 s | **1,75 s** | **0,84 s** | 1,24 s | 2,19 s | **2,56 s** | 3,26 s |

**Référence CLOB :** réception du `last_trade_price`. La mise à jour des niveaux arrive environ 20 ms avant.

**Points de mesure :**
- La chaîne n'est enregistrée sans filtre que de 09:10 à 09:17. Ensuite, seuls les fills des wallets SIG_HIST le sont : d'où n = 59 transactions avec les trois sources.
- Le 01/10, une mesure parallèle sur 763 transactions donnait la chaîne 0,81 s avant RTDS (médiane).

**MESURÉ**
- **La fenêtre avant l'identification du wallet est de 1,75 s en médiane** (P10 0,84 s, P90 2,56 s).
- Le nœud Polygon public est **irrégulier** : parfois plus rapide que RTDS (0,5 s en médiane), parfois 10 à 25 s plus lent. RTDS est plus régulier.

**INFÉRÉ**
- Un détecteur qui n'attend pas le wallet gagne au mieux 0,8 à 2,6 s.
- Pour en gagner davantage, il faudrait voir le flux **avant** le trade du wallet.

**INCONNU**
- La latence d'un nœud Polygon privé, et celle du mempool : les transactions de règlement sont envoyées par l'opérateur du CLOB.

**PROCHAINE ÉTAPE**
- Remesurer sur 2 semaines de données de la phase 11 (fills des wallets SIG_HIST).
