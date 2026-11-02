# Phase 13 : capture des wallets SIG_HIST à faible latence

Rapport du 01/10/2026, 10:25 UTC. Protocole : `PROTOCOLE_P13.md`, écrit avant toute mesure. W du second trade gelé sur TRAIN : `frozen_p13.json`.

**Cadre :**
- SIG_HIST V1 n'est pas modifié. Aucune variante V2 n'a été créée.
- Les phases 11 et 12 continuent, intactes : la phase 13 les lit seulement.
- Aucun ordre, aucun classement public. `wallet_watchlist.csv` reste local.

## Réponses

**Question 1.** Si l'on connaît déjà les wallets prédictifs, peut-on détecter leur entrée assez vite pour garder une espérance positive après frais, spread, glissement et latence réelle ?

**Pas avec ce qui est mesurable aujourd'hui, et la latence n'est pas la seule cause.**
- **La latence réelle est d'environ 1,3 à 2,1 s :**
  - meilleure source combinée, médiane 1,34 s ;
  - RTDS seul, 2,08 s ;
  - les achats de taille SIG_HIST sont les plus lents (2,5 s).
- **Sur l'alerte SIG_HIST live, l'observateur perd même avec une détection instantanée** (contrefactuel T_EXEC + 0 ms) : le trade du wallet a déjà consommé la profondeur, et le mid a pris 3 points avant que quiconque puisse réagir.
  - Le net est de −2,4 % de 0 à 2 s, et de −3,5 % au-delà.
  - Ce n'est donc pas d'abord WALLET IDENTIFICATION TOO SLOW, mais **MARKET MOVES TOO FAST**. Le mouvement exploitable est dans le trade lui-même.
  - Sur un autre achat de la watchlist, l'ask est à 0,10 mais 500 $ paient en moyenne 0,27 : **INSUFFICIENT LIQUIDITY**.
- **Réserve :** n = 1 alerte SIG_HIST et 3 achats de la watchlist en une heure de direct. Diagnostic **provisoire**. Le processus paper (`p13_paper.py`) tourne maintenant pour accumuler les cas.

**Question 2.** Cela reste-t-il vrai sur des wallets et des marchés qui n'ont pas servi à construire le signal ?

**INCONNU pour l'exécution** (trop peu de cas live). En revanche, la limite des nouveaux wallets est **établie** :
- un wallet ne se qualifie qu'après une médiane de **9 FAE** et **146 jours** ;
- 91 % des wallets jamais qualifiés disparaissent avant ;
- les wallets de Maduro et de l'Iran **n'étaient pas qualifiés** au moment de leurs achats.

**NEW_WALLET_DETECTION = NOT POSSIBLE WITH CURRENT SIGNAL.**

**Piste la plus intéressante, historique, sans exécution mesurée : le second achat.**
- 18 à 21 % des alertes SIG_HIST ont un 2e achat du même wallet sur le même jeton dans l'heure, en médiane **66 à 81 s** après le premier.
- Ce 2e achat reste prédictif : LEAD60 de 40 % (VALID) et 28 % (TEST), contre 12 % et 10 % pour les contrôles.
- Il laisse plus d'une minute après l'identification du 1er achat.
- À tester en direct.

---

## 1. Les sources d'identification (§3, §4, §5)

Comparaison sur 10 minutes, mêmes marchés, 158 trades de référence (`latency_sources.csv`, `latency_distribution.csv`). Latence mesurée par rapport à la réception du trade dans le carnet.

| Source | Vus | Pertes | P10 | P50 | P90 | P99 | Reconnexions | Inversions d'ordre |
|---|---|---|---|---|---|---|---|---|
| **RTDS** | 152 | **3,8 %** | 1,15 s | **2,08 s** | **3,54 s** | **3,94 s** | 1 | 32 |
| Nœuds Polygon publics (premier des 4 fournisseurs) | 146 | 7,6 % | **0,65 s** | 1,94 s | **144 s** | 174 s | **577** | 26 |
| data-api (interrogation en boucle) | 15 | 90,5 % | 60 s | 391 s | 432 s | 473 s | 0 | 11 |

**Notes :**
- Dans ce premier passage, les 4 fournisseurs RPC ont été fusionnés par une erreur d'étiquetage (corrigée).
- Les doublons de RTDS sont les lignes makers : une ligne par participant.

**Relance par fournisseur** (5 minutes, 10:18 à 10:23 UTC, 66 trades de référence ; `latency_sources_fournisseurs.csv`, `latency_distribution_fournisseurs.csv`) :

| Source | Vus | Pertes | P10 | P50 | P90 | P99 | Reconnexions |
|---|---|---|---|---|---|---|---|
| **publicnode** | 64 | 3 % | **0,43 s** | **1,19 s** | **1,63 s** | 3,20 s | 0 |
| drpc | 47 | 29 % | 1,10 s | 1,70 s | 2,56 s | 3,34 s | 2 |
| RTDS | 62 | 6 % | 1,02 s | 1,83 s | 2,67 s | 3,01 s | 1 |
| blastapi | 0 | 100 % | | | | | 145 (jamais connecté) |
| tenderly | 0 | 100 % | | | | | 141 (jamais connecté) |
| data-api | 2 | 97 % | 54 s | 58 s | 63 s | | 0 |
| **Meilleure voie** (premier arrivé) | 64 | 3 % | 0,43 s | **1,19 s** | **1,62 s** | 2,08 s | |

- publicnode arrive premier sur 61 trades sur 64.
- Achats de 100 à 1 000 $ : publicnode P50 1,05 s, RTDS 1,78 s.
- Le P90 de 144 s du premier passage vient d'un trou de publicnode (les deux autres fournisseurs ne compensent pas). **Le même nœud est excellent sur 5 minutes et absent sur d'autres** : c'est sa stabilité, pas sa vitesse, qui limite.

**Par catégorie (RTDS, P50) :**

| Catégorie | P50 |
|---|---|
| trades < 100 $ | 1,97 s |
| trades de 100 à 1 000 $ | **2,57 s** |
| achats | **2,47 s** |
| ventes | 1,59 s |
| bloc à 1 ou 2 trades | 1,86 s |
| bloc à 48 trades | **3,37 s** |

**Sur les données de la phase 11** (10 trades de wallets de la watchlist) : meilleure voie combinée P50 **1,34 s** (P10 0,79 ; P90 2,21). RTDS 2,09 s. Chaîne 1,42 s, mais P90 de 29 s.

**MESURÉ**
- Aucune source publique n'est à la fois rapide et stable sur la durée.
- **RTDS** est la plus fiable (P99 < 4 s, presque aucune perte).
- **La chaîne** est la plus rapide quand elle répond (P10 0,65 s), avec des trous de plusieurs minutes.
- **Le data-api** est inutilisable pour la vitesse.
- **Les trades qui ressemblent à SIG_HIST** (achats moyens dans des blocs chargés) sont identifiés le plus tard.

**INFÉRÉ**
- Une voie publique réaliste et robuste, c'est la chaîne (publicnode) quand elle répond, RTDS sinon : 1,2 à 1,3 s en médiane, 1,6 à 2,5 s en P90 selon l'état du nœud.

**INCONNU**
- Un nœud Polygon privé ou payant.
- Un accès au mempool de l'opérateur.

**PROCHAINE ÉTAPE**
- Mesurer un nœud dédié. C'est la seule voie qui pourrait descendre sous la seconde de façon stable.

## 2. La watchlist (§6, §7)

Fichier `wallet_watchlist.csv`, local, jamais publié.

| Classe | Wallets |
|---|---|
| KNOWN_HIGH_LEAD (qualifié, hist_n ≥ 10) | 73 |
| NEWLY_QUALIFIED (qualifié, hist_n de 5 à 9) | 34 |
| UNKNOWN : déclencheurs historiques non qualifiés au démarrage | 57 |

**Watchlist contre marché global :**
- Le calcul n'est pas le goulot : 7 ms entre la réception RTDS et l'alerte (phase 11).
- Les deux approches produisent les mêmes alertes SIG_HIST, puisque le signal exige un wallet qualifié.
- La watchlist permet surtout de **filtrer le flux de la chaîne** sur 107 wallets : environ 99 % de volume en moins.
- **Alertes attendues :** quelques-unes par jour. Une heure de direct a donné 1 alerte SIG_HIST et 10 trades de wallets de la watchlist sur les marchés enregistrés.

## 3. Courbe de latence et capacité (§8 à §12)

Tables : `latency_capture_curve.csv`, `capacity_curve.csv`, `execution_detail.csv`. Carnet réel enregistré, connu à l'instant de décision.

**Alerte SIG_HIST V1 live** : wallet `0x8f42ae0a`, 3 111 $ de NO, marché Likud ; 500 $, sortie à 300 s, frais inclus.

| Latence après T_EXEC | 0 ms | 100 ms | 250 ms | 500 ms | 1 s | 1,5 s | 2 s | 3 s | 5 s | 10 s |
|---|---|---|---|---|---|---|---|---|---|---|
| Net | −2,4 % | −2,4 % | −2,4 % | −2,4 % | −2,4 % | −2,4 % | −2,4 % | −3,5 % | −3,5 % | −3,5 % |
| Glissement vs mid | 2,0 pts | 1,5 | 1,5 | 1,5 | 1,5 | 0,5 | 0,5 | 1,0 | 1,0 | 1,0 |

- Entrée réaliste (T_DETECT = T_EXEC + 1,6 s, puis 0, 100 ou 250 ms d'envoi) : −2,4 %.
- Remplissage de 100 % à toutes les tailles testées (50 à 5 000 $), mais le net est négatif partout : −2,4 % à 500 $, −2,9 % à 1 000 $, −6,4 % à 5 000 $ (T_DETECT, 300 s). **Taille maximale positive : aucune.**

**Achats de 250 $ ou plus de la watchlist** (2 cas, élargi) :

| Cas | Entrée réaliste | Net, sortie 60 s | Net, sortie 300 s | Lecture |
|---|---|---|---|---|
| Marché liquide | T_EXEC + 0,9 s | −1,1 % | −1,1 % | perte modérée (ask 0,89) |
| Marché mince | T_EXEC + 1,3 s | **−71 %** | **−64 %** | ask 0,10, mid 0,085, mais 500 $ paient en moyenne 0,27 |

**INFÉRÉ (n = 1 et n = 2 : illustration)**
- Sur l'alerte, le contrefactuel à 0 ms est déjà négatif : **le mouvement est dans le trade du wallet**. Le carnet qui suit son balayage ne laisse rien à prendre.
- C'est une **LATENCY LIMIT inférieure à 0 ms**, autrement dit **MARKET MOVES TOO FAST**, et non une INFORMATION LIMIT.

**INCONNU**
- La distribution sur 100 alertes.

**PROCHAINE ÉTAPE**
- Le paper trading accumule les cas ; relancer `p13_execution.py` sur les données de la phase 11 chaque semaine.

## 4. Premier trade, second trade, continuation (§13, §14, §15)

Historique (trades ≥ 100 $), W = 3 600 s choisi et gelé sur TRAIN. Tables : `second_trade.csv`, `continuation.csv`.

| | VALID SIG_HIST | VALID contrôle | TEST SIG_HIST | TEST contrôle |
|---|---|---|---|---|
| Part avec un 2e achat dans l'heure | 21 % | 12 % | 18 % | 14 % |
| Délai médian entre 1er et 2e achat | **66 s** | 242 s | **81 s** | 92 s |
| 2e achat avant l'identification du 1er (< 1,75 s) | 0 % | 1,4 % | 0,8 % | 0 % |
| Dérive du prix entre les deux achats | +1,2 point | −0,2 | +0,4 | +0,3 |
| LEAD60 après le 2e achat | **39,8 %** | 11,6 % | **27,8 %** | 10,0 % |
| Mouvement après le prix du 2e achat (60 min), moyenne / médiane | +1,45 / +0,43 point | −0,21 / 0 | +1,92 / 0,00 | −0,86 / 0 |

**Continuation (LEAD60 par rang, SIG_HIST) :**

| Rang | VALID | TEST |
|---|---|---|
| 1 | 31 % | 30 % |
| 2 | 40 % | 28 % |
| 3 | 41 % | 41 % |
| 4 | 58 % (n = 12) | 36 % (n = 14) |

**MESURÉ**
- Le premier trade n'est pas toujours isolé : un sur cinq est le début d'une séquence.
- Le 2e achat arrive une minute plus tard en médiane et reste prédictif hors échantillon.
- Le mouvement moyen qui suit son prix est positif, mais la médiane est proche de 0 : quelques gros mouvements font la moyenne.

**INFÉRÉ**
- **SIG_HIST_SECOND est la seule configuration où la latence d'identification (1,3 à 2 s) est petite devant la fenêtre (environ 60 s).**
- Mais on ne sait **qu'a posteriori** qu'il y aura un 2e achat : 80 % des alertes n'en ont pas.

**INCONNU**
- Le prix disponible dans le carnet au moment du 2e achat.

**PROCHAINE ÉTAPE**
- Ajouter au paper trading la règle « entrer à l'identification du 2e achat d'un wallet SIG_HIST dans l'heure », gelée dès maintenant, et la mesurer en direct.

## 5. Wallet déjà actif et positions (§16, §17)

Tables : `wallet_actif.csv`, `positions.csv`.

| | VALID SIG_HIST | VALID contrôle | TEST SIG_HIST | TEST contrôle |
|---|---|---|---|---|
| Délai médian depuis le dernier trade du wallet | 19 h | 38 h | 13 h | 43 h |
| Wallet actif dans les 10 min précédentes | 16 % | 10 % | 20 % | 11 % |
| LEAD60 : nouvelle position / renforcement | 30 % / 32 % | 10 % / 9 % | 32 % / 27 % | 15 % / 11 % |

**INFÉRÉ**
- Les wallets SIG_HIST sont plus souvent actifs juste avant leur alerte, mais 80 % des alertes viennent sans activité dans les 10 min.
- Passer d'une position nulle à une position forte ne rend pas le signal plus fort.
- **Il n'y a pas de pré-signal exploitable du wallet lui-même.**

## 6. Nouveaux wallets (§21, §22)

Table : `new_wallet_limit.csv`.

| Mesure | Valeur |
|---|---|
| Wallets ayant au moins un FAE | 149 526 |
| Ceux qui atteignent 5 FAE résolus | 12 217 |
| **Ceux qui se qualifient un jour** | **139** (0,09 %) |
| FAE avant la qualification | médiane 9 (P25 8, P75 17) |
| Jours entre le premier trade et la qualification | médiane **146** (P25 56, P75 242, P90 357) |
| Wallets à 1-4 FAE disparus (inactifs plus de 30 jours) | 135 815, soit **91 %** des jamais qualifiés |

**Filtres de priorisation** (âge du wallet, MoonPay ; `priorisation.csv`) : **non testables**. L'échantillon de financement de la phase 8 (1 506 wallets) ne contient **aucun** wallet qualifié.

**NEW_WALLET_DETECTION = NOT POSSIBLE WITH CURRENT SIGNAL.**

## 7. Les 8 comptes (§18)

Table : `comptes_8.csv`.
- Aucun n'est dans la watchlist live.
- Aucun ne s'est jamais qualifié : hist_n maximal de 3 pour Chiwawas.
- Aucune alerte SIG_HIST.
- Continuation : Chiwawas a 2 achats du même jeton dans l'heure qui suit un FAE ; les autres, aucun.
- Financement : en feature séparée (MoonPay pour Chiwawas et 154x838hjd6). Ce n'est pas un signal.

**Verdict : NO SIGNAL wallet-aware possible pour ces comptes.**

## 8. Maduro (§19)

Table : `maduro_wallet_replay.csv`. T_DETECT est estimé avec la distribution live (P10 0,84 s, P50 1,75 s, P90 2,56 s). Le prix est celui du prochain trade observé, car le carnet d'époque n'existe pas.

| Wallet | T_EXEC | Statut V1 à l'instant | Prix payé | Prix observé après T_DETECT | +1 h | Au repricing (06:16) | 1er trade ≥ 0,5 (06:15:41) |
|---|---|---|---|---|---|---|---|
| `0x31a56e9e` | 01:38:35 | **non qualifié** (hist_n 3, score 0,025) | 0,073 | 0,06 | 0,06 | 0,25 | 0,51 |
| `0x31a56e9e` | 02:15:05 | non qualifié | 0,080 | 0,06 | 0,08 | 0,25 | 0,51 |
| `0x31a56e9e` | 02:58:25 | non qualifié | 0,082 | 0,08 | 0,09 | 0,25 | 0,51 |
| `0x6baf05d1` | 03:42:01 | **non qualifié** (hist_n 0) | 0,113 | 0,09 | 0,10 | 0,25 | 0,51 |

Événements publics : premières explosions ~06:00 (APPROXIMATE), annonce 09:21 (APPROXIMATE).

**MESURÉ**
- SIG_HIST V1 n'aurait signalé aucun de ces achats.
- Si on les avait suivis par un autre critère, le prix disponible après détection est resté à 0,06-0,10 pendant plus de 2 h.

**INFÉRÉ**
- Ici, la latence n'est pas en cause. Le seul obstacle est **la sélection du wallet**.
- Choisir ces wallets après coup (ce sont les « comptes forts » de juillet) utiliserait le futur.

## 9. Iran (§20)

Table : `iran_wallet_replay.csv`.

| Achat de `0x4dfd481c` | Statut V1 | Prix payé | Prix observé après T_DETECT | +5 min | +1 h |
|---|---|---|---|---|---|
| 05:15:53, 32 337 $ | **non qualifié** (hist_n 5, score 0,022 < seuil 0,222) | 0,170 | 0,16 | 0,19 | **0,90** |
| 05:21:55, 23 675 $ | non qualifié | 0,201 | 0,19 à 0,23 | 0,20 | 0,80 |
| 05:33:47, 29 503 $ | non qualifié | 0,223 | 0,20 | 0,21 | 0,68 |

**Repères :**
- début de l'anomalie : **05:15** (référence 12 h) et **06:10** (référence veille), avec un prix de 0,16 et 0,26 ;
- 1er trade ≥ 0,5 : 06:12:17 ;
- repricing CLOB : 06:13:22 (0,39) ;
- frappes ~06:15 (APPROXIMATE, prix 0,80) ;
- annonce israélienne 06:23 (VERIFIED, 0,72).

**INFÉRÉ**
- Ce wallet avait assez d'historique, mais un score **inférieur** au seuil : V1 le classe comme « ordinaire ».
- La fenêtre a duré environ 1 h. La latence n'est pas en cause ; **le signal ne le désigne pas**.

## 10. Paper trading (§23)

`scripts/p13_paper.py`, lancé par `p13_run.sh`, **PAPER ONLY** :
- il identifie les wallets de la watchlist par la chaîne et par RTDS (le premier arrivé compte) ;
- il calcule SIG_HIST V1 ;
- il prend l'entrée papier sur le carnet REST au moment de la détection (50 à 1 000 $), puis les sorties à +60 et +300 s.

Journaux : `donnees/brut_p13/paper_alerts.jsonl` et `paper_exits.jsonl`. Toutes les alertes y figurent, pertes comprises.
`scripts/p13_paper_export.py` les convertit en `paper_alerts.csv` (frais du marché appliqués à l'analyse).

**État au moment du rapport :**
- prêt à 10:24:34 UTC, 107 wallets surveillés, 430 s de démarrage ;
- connexions chaîne et RTDS ouvertes, aucune erreur ;
- **0 alerte papier** : `paper_alerts.csv` ne contient que l'en-tête. À relancer après quelques jours.

## 11. Critères (§24) et diagnostic (§25)

| # | Critère | État |
|---|---|---|
| 1 | wallet identifié avant le mouvement | **non** sur l'alerte live (mid +3 points avant T_DETECT) |
| 2 | latence réelle mesurée | **oui** (P50 1,34-2,08 s, P90 2,2-3,5 s) |
| 3 | entrée sur le carnet réel | oui |
| 4, 5 | positif en VALID et en TEST | non évaluable pour l'exécution (n = 1) ; historique : non (phases 9 et 10) |
| 6, 7 | frais et glissement intégrés | oui |
| 8 | capacité | non : aucune taille positive |
| 9 | pas quelques wallets | non évaluable |
| 10 | pas de sélection future | oui |

**Diagnostic, dans l'ordre :**
1. **MARKET MOVES TOO FAST.** Le mouvement est dans le trade du wallet : son balayage du carnet arrive avant toute identification, même à 0 ms.
2. **WALLET IDENTIFICATION TOO SLOW.** Pour ce qui reste, la meilleure voie publique stable met 1,3 à 2,5 s. C'est exactement le temps où le prochain acheteur arrive (2 à 4 s, phase 10).
3. **INSUFFICIENT LIQUIDITY** sur une partie des marchés.
4. **Limite de sélection.** Les nouveaux wallets ne sont pas qualifiables, et les wallets des cas Maduro et Iran ne l'étaient pas.

**Exception à suivre : le second achat** (fenêtre d'environ 60 s). Prédictif en VALID et en TEST, exécution non mesurée.

## 12. Écarts au protocole

- **Étiquetage des fournisseurs RPC** : au premier passage, les 4 fournisseurs étaient fusionnés. Corrigé, puis relancé 5 minutes (§1). Les deux passages sont conservés.
- **Taille de l'échantillon live** : 1 alerte SIG_HIST et 2 achats de la watchlist. Les courbes de latence et de capacité sont des illustrations, pas des estimations.
- **Paper trading** : entre la fin du rattrapage et l'ouverture des flux, quelques secondes de trades ne sont pas vues. Ce trou est accepté et non comblé.
- **Maduro et Iran** : le carnet d'époque n'existe pas. Le prix « après détection » est celui du prochain trade, et T_DETECT est tiré de la distribution live de 2026.

## 13. Fichiers

**`phase13/`**
- Protocole et rapport : `PROTOCOLE_P13.md`, `RAPPORT_PHASE13.md`, `frozen_p13.json`
- Latence : `latency_sources.csv`, `latency_sources_fournisseurs.csv`, `latency_distribution.csv`, `latency_detail.csv`
- Watchlist et live : `wallet_watchlist.csv` (local), `wallet_trades_live.csv`
- Exécution : `latency_capture_curve.csv`, `capacity_curve.csv`, `execution_detail.csv`
- Historique : `second_trade.csv`, `second_trade_detail.csv`, `continuation.csv`, `positions.csv`, `wallet_actif.csv`
- Nouveaux wallets : `new_wallet_limit.csv`, `new_wallet_detail.csv`, `priorisation.csv`
- Cas : `comptes_8.csv`, `maduro_wallet_replay.csv`, `iran_wallet_replay.csv`
- Paper : `paper_alerts.csv`

**Scripts**
- `p13_wallet_monitor.py`, `p13_latency_replay.py`, `p13_execution.py`, `p13_second_trade.py`
- `p13_paper.py`, `p13_run.sh`, `p13_paper_export.py`
