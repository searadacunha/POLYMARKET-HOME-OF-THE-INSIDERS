# Phase 15 : protocole d'audit (couverture et détection en direct)

Rédigé le 01/10/2026 vers 11:45 UTC.

**Avant ce protocole, trois lectures seulement :**
- le code des processus ;
- les journaux de connexion ;
- la reconstruction du cas Oklahoma (§5).

Ces lectures ont déjà révélé deux défauts : le champ `conditionId` vide dans RTDS, et les silences RTDS. Ils sont rapportés tels quels. Les critères ci-dessous sont fixés avant la mesure de couverture.

**Cette phase est un audit :**
- SIG_HIST V1 n'est pas modifié, aucun seuil non plus ;
- aucun processus existant n'est arrêté ni modifié ;
- aucun signal n'est créé, aucun ordre n'est passé.

## 1. Sources de vérité (§4 de la mission)

| Champ | Vérité | Contrôle croisé |
|---|---|---|
| **A. Trade** | Logs Polygon `OrderFilled` v2 des deux contrats d'échange. Le fill de l'ordre preneur (topic 3 = contrat d'échange) identifie le trade. Clé : (hash de transaction, jeton). | data-api `/trades?takerOnly=true`, complet et ordonné (vérifié contre la chaîne en phase 10 : 103/103) |
| **B. Carnet** | Websocket `market` du CLOB (book + price_change) enregistré par le collecteur | instantanés REST `/books` (phase 11 : 133/134) |
| **C. Wallet** | Champ maker (topic 2) du fill de l'ordre preneur, c'est-à-dire le proxy qui agit | `proxyWallet` du data-api (takerOnly=true) |
| **D. Marché** | Gamma : `clobTokenIds` (l'ordre donne l'outcome), `conditionId`, `slug`, `question` | data-api (`conditionId`, `outcomeIndex`) |
| **Temps** | horodatage de bloc (en-têtes `newHeads`) | heure d'échange du websocket (ms) ; heure locale de réception (ns, horloge du Mac, contrôlée par SNTP dans `meta/clock.jsonl`) |

**Règles :**
- aucune source ne sert de référence pour tous les champs ;
- un champ sans vérité disponible est noté **UNKNOWN**.

## 2. Mesures

| Élément | Définition |
|---|---|
| **Classement du mapping** | **CORRECT** ; **MISSING** (champ vide) ; **DELAYED** (marché inconnu à la réception, connu ensuite) ; **WRONG** (différent de la vérité) |
| **Classement du prix** | **CORRECT** (écart < 1e-6) ; **ROUNDING** (écart < 0,005) ; **STALE** (prix d'un trade antérieur) ; **WRONG_TOKEN** ; **WRONG_SIDE** ; **UNKNOWN** |
| **Doublons** | **TRUE_DUPLICATE** (même ligne reçue deux fois) ; **SAME_TRADE_DIFFERENT_ID** ; **TIMESTAMP_ALIAS** (même trade, deux horodatages) ; **UNKNOWN** |
| **Couverture d'une source** | rappel = trades de la vérité vus par la source / trades de la vérité ; précision = trades de la source présents dans la vérité / trades de la source |
| **Latence** | réception locale moins horodatage de bloc. Ce n'est **pas** une latence pure, car les deux horloges diffèrent ; c'est signalé à chaque fois. Réception locale entre deux sources : même horloge, comparable. |

## 3. Enregistreur d'audit indépendant (`p15_audit.py --live`)

Processus séparé, **sans aucune décision**. Il enregistre, pendant au moins 3 heures :
- **deux connexions RTDS simultanées, A et B :**
  - A est continue ;
  - **B est coupée volontairement 30 s toutes les 20 min** (test de reconnexion, §19) ;
  - les deux ont le même chien de garde que la production (30 s de silence) ;
- **les logs `OrderFilled` v2 non filtrés et les en-têtes de blocs**, d'un nœud Polygon public :
  - un trou d'en-têtes est rattrapé par `eth_getLogs`, ce qui teste si la chaîne est récupérable ;
- **un journal d'état toutes les 60 s.**

Sortie : `donnees/brut_p15/`. Le carnet et les sources des phases 11 à 14 sont relus dans leurs propres fichiers, sans les toucher.

## 4. Critères de validation (§23 de la mission)

| # | Critère | Seuil |
|---|---|---|
| 1 | Couverture des marchés connue | table complète univers / P11 / P12 / P13 / P14 |
| 2 | Couverture des trades connue | rappel mesuré contre la vérité A pour chaque source, sur au moins 3 heures |
| 3 | Pertes mesurées | rappel ≥ 99 % pour la source d'identification des alertes (RTDS du listener), sinon défaut |
| 4 | Doublons mesurés | classés |
| 5 | Timestamps réconciliés | écart systématique expliqué entre chaque paire de sources |
| 6 | Prix validés | ≤ 0,1 % de prix WRONG_* sur les trades d'au moins 100 $ |
| 7 | Wallets validés | ≤ 0,1 % de wallets différents de la vérité C sur les trades preneurs d'au moins 100 $ |
| 8 | Reconnexions testées | perte d'un trou de 30 s mesurée ; « récupéré » seulement si une source le rattrape |
| 9 | Chiens de garde testés | pour chaque processus : vivant, flux vivant, âge du dernier événement |
| 10 | SIG_HIST rejouable | alertes historiques : part visible avec les pertes et défauts mesurés |
| 11 | Cas Oklahoma | expliqué par des données brutes, pas par hypothèse |
| 12 | Aucune divergence critique inexpliquée | |

**Verdicts :**
- **INFRASTRUCTURE VALIDATED :** les 12 critères sont tenus ;
- **INFRASTRUCTURE PARTIALLY VALIDATED :** certaines sources tiennent leurs critères, d'autres non, et les défauts sont mesurés ;
- **INFRASTRUCTURE NOT VALIDATED :** un défaut touche directement le chemin des alertes (identification du wallet, marché, prix de référence) assez pour fausser l'interprétation des résultats en direct.

Si un défaut critique est démontré avant la fin de l'enregistrement, la conclusion peut être posée sans attendre (§22 de la mission). L'enregistrement continue pour mesurer son ampleur.
