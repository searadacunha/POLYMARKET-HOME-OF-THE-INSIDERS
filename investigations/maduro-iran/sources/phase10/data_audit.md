# Phase 10 : audit des données

Fait le 30/09/2026, avant tout calcul de résultat. Détail du carnet : `CLOB_DATA_AUDIT.md`.

## 1. Le signal préservé : SIG_HIST (phase 9, inchangé)

La définition vient de `phase9/PROTOCOLE_P9.md`, de `phase9/frozen_spec.json` et de `scripts/p9_detector.py`.

Une alerte SIG_HIST est émise sur un trade qui réunit ces quatre conditions :

1. **Le trade est un FAE** : un achat preneur ≥ 250 $, sans aucun trade du même wallet dans ce marché depuis 24 h. Il est vu dans le flux des trades ≥ 100 $ du data-api.
2. **Le trade n'est pas FOLLOW** : Δ 10 min avant < 1,5 point dans la direction achetée. Le prix de référence est le dernier trade ≥ 100 $ strictement antérieur à la seconde de T.
3. **Le prix de référence existe** (`p_before` non vide).
4. **Le wallet a un historique suffisant** : `hist_n` ≥ 5 et `hist_score` ≥ **0,22207409391469976**. Ces deux valeurs sont calculées ainsi :
   - `hist_score = (LEAD + 10 × 0,03298) / (n + 10)` ;
   - elles ne comptent que les FAE non-FOLLOW du wallet déjà résolus : T_e + 3 600 s ≤ T ;
   - LEAD60 = Δ ≥ 3 points à 60 min, mesuré sur les trades ≥ 100 $ des autres wallets.

**Alertes.** 1 985 au total : TRAIN 688, VALID 561, TEST 736, sur 522 marchés. Ce sont exactement celles de `events_final.pkl`, identiques à celles du détecteur en flux (concordance de 100 %). En phase 10, SIG_HIST n'est jamais recalculé avec les petits trades : **le signal reste celui de la phase 9**. Les petits trades ne servent qu'à mesurer ce qui se passe autour.

## 2. T0

**Définition.** T0 = horodatage (seconde, horodatage de bloc) du trade du wallet signalé, avec sa position exacte dans le bloc, donnée par l'ordre du data-api (identique au logIndex).

**Condition d'observabilité.** Le signal est calculable dès que le trade est visible avec l'adresse du wallet, c'est-à-dire au plus tôt à l'inclusion du bloc.

**Délai réel de l'observateur : INCONNU.** Il dépend de la voie choisie :
- un nœud Polygon donne le bloc environ 2 s après le match ;
- le data-api, par sondage, a un délai de publication non mesuré.

T0 est donc une **borne basse**. OBSERVER_0, placé immédiatement après le trade du wallet dans le même bloc, est **théorique** et non atteignable.

## 3. Sources utilisées

| Source | Contenu | Usage |
|---|---|---|
| `alltrades.pkl` (phase 8) | trades ≥ 100 $, 2 097 marchés | historique des wallets, graphe des suiveurs, SIG_HIST |
| data-api `/trades` avec `start`/`end`, toutes tailles, preneurs + makers | fenêtre [T0 − 900 s, T0 + 4 500 s] autour de chaque alerte SIG_HIST et de chaque contrôle apparié | prix avant, impact, niveaux consommés, latences, tailles, suiveurs, sorties |
| Reçus de transaction (Etherscan V2, `eth_getTransactionReceipt`) | frais réellement payés par le wallet signalé | taux de frais preneur du marché à T0 |
| CLOB `prices-history` (1 min) | contexte, Maduro et Iran | chronologies |
| Sources publiques horodatées | heures des événements | chronologies seulement, jamais dans un signal |

## 4. Données Iran avant 05:28 UTC le 28/02

| Point | Constat |
|---|---|
| Source | data-api `/trades?market=0x3488f31e…&start=&end=` (preneurs et makers), contrôlable par les logs on-chain v1 `0x4bfb41d5` |
| Disponibilité | testé : des trades existent jusqu'à 05:27:59 et avant |
| Couverture | la complétude du data-api est validée sur la fenêtre Maduro. Pour l'Iran, elle sera contrôlée par comptage contre les logs on-chain de la phase 2 (05:28-06:13) |
| Horodatage | seconde (bloc), ordre exact |
| Fenêtre collectée | 27/02 12:00 → 28/02 07:00 UTC. Pour Maduro : 02/01 12:00 → 03/01 10:00 |
| Série de prix à la minute | disponible (`prices-history`, 688 points du 27/02 18:00 au 28/02 05:28) |

## 5. Ce qui reste INCONNU

- Carnet d'ordres complet entre deux trades : best bid / best ask, profondeur restante.
- Placements et annulations d'ordres.
- Délai réel de publication pour un observateur.
- Position dans la file d'attente d'un ordre limite.

Conséquence pour les ordres limites : un remplissage n'est compté que si la preuve est dans les trades, avec une règle conservatrice et une règle optimiste, définies dans le protocole.
