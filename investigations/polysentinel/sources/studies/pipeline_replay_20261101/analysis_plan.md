# Rejeu du pipeline avec univers témoin : plan du 1er novembre 2026

Écrit avant tout téléchargement de trades et avant tout calcul du détecteur sur ces données. Les seuls appels déjà faits (10 requêtes) testent l'API ; ils sont dans `data/requests.jsonl` et `data/api_probe*.json`. L'auteur connaît l'affaire et le wallet de Thin-Disclaimer-Life : ce rejeu n'est pas une validation indépendante du détecteur, conçu le 27 octobre après l'article du 23 octobre. Le code n'a accès à aucun alias.

## Questions

Q1. Dans un univers qui n'a pas été choisi après l'affaire, le wallet de Thin émerge-t-il ? Heure de première priorité, score, rang au tick, dossiers à examiner avant lui.
Q2. Combien de dossiers le détecteur gelé produit-il par jour dans cet univers, et sur quels marchés témoins ?
Q3. Quelles limites du pipeline réel expliquent le résultat (filtre, rotation, plafond d'analyse, historique des wallets) ?

A0, la détection qu'aurait réellement faite PolySentinel le 13 octobre, reste **NON ESTIMABLE** : le service n'existait pas, et aucune latence, aucun carnet ni catalogue daté de cette période n'existe. Les scénarios ci-dessous sont conditionnels.

## Faits mesurés avant le plan

| Fait | Valeur | Source |
|---|---|---|
| Flux global `/v2/trades` | curseur signé, bornes ignorées, mois courant et précédent seulement | schéma officiel, `api_probe.json` |
| `/trades` ancien, avec `market=` | `start`/`end` respectés, `limit=10000` | `api_probe2.json` |
| `/trades` ancien, sans `market=` | bornes ignorées ; `offset=150000` refusé | `api_probe3.json`, `api_probe4.json` |
| Lignes ≥ 1 000 $ sur 24 h | 15 264, dont ≥ 2 500 $ : 40,4 %, ≥ 5 000 $ : 18,4 % | base de production |
| Plafond de 50 000 trades analysés | couvre 25,2 à 66,2 h, médiane 43,8 h | base de production, 102 relevés horaires |
| Cycle | médiane 60 s | table `cycles`, 48 h |
| File de marchés ciblés | 10 par cycle : 5 annonces sur 1 076 éligibles, 5 en exploration sur 71 071 | checkpoint `collect:queue` |
| Dossiers prioritaires nouveaux | 56 à 616 par jour selon le jour, 1 971 en tout | `history_refs`, kind `alert` |

Conséquence : le flux réel à 1 000 $ jusqu'au 13 octobre demanderait environ 320 pages, au-dessus du plafond de 300 requêtes. Le pilote prend un recensement au filtre **2 500 $** (F). C'est un sous-ensemble du flux de production. La file obtenue n'est **pas** une borne de la file réelle à 1 000 $, dans aucun sens : retirer des lignes en dessous de F peut supprimer une priorité, mais aussi en créer une (une ligne paraît « première », et la concentration monte quand le dénominateur baisse). Le taux réel de production, mesuré ci-dessus, reste la meilleure référence de charge.

## Fenêtres

- T_fin = 1792768669, 23 oct. 15:17:49 UTC, coupure de l'article (identique à `detection_20261030`).
- T_alertes = 1791849600, 13 oct. 00:00:00 UTC, début du décompte principal de la file.
- T_debut = 1791691200, 11 oct. 04:00:00 UTC : T_alertes moins 44 h, pour amorcer le plafond d'analyse.
- Grille de décision : toutes les 60 s de T_debut à T_fin. Rien n'est émis avant T_alertes dans le décompte principal. Le décompte depuis T_debut est aussi rapporté.

## Acquisition, 300 requêtes au total

Tout passe par `code/ledger.py`, qui compte chaque tentative et refuse la 301e.

| Phase | Plafond | Méthode |
|---|---|---|
| Sondes | 10 (faites) | |
| A1 Recensement global | 170 | `/v2/trades?limit=1000&taker_only=true&filter_type=CASH&filter_amount=2500`, curseur, reprise sur page, arrêt à T_debut |
| A2 Compléter la famille Ballon | 15 | `/trades` borné pour les 3 flux tronqués de l'étude antérieure (48361, 811116, 811117) |
| A3 Catalogue des témoins | 25 | Gamma `/events/slug/<slug>` |
| A4 Trades des témoins | 40 | `/trades?market=...&start=&end=&limit=10000&takerOnly=true`, de 30 jours avant T_fin à T_fin |
| A5 Historiques de wallets | 100 | `/trades?user=...&end=&limit=10000&takerOnly=true`, sans borne basse, après R1 et avant lecture des labels |

Règle de repli A1, fixée d'avance : après 20 pages, projeter le nombre de pages jusqu'à T_debut d'après le rythme observé. Au-delà de 170, recommencer à **5 000 $** et le signaler. Si T_debut n'est pas atteint à 170 pages, le recensement commence à la borne atteinte. Si cette borne est postérieure au 13 oct. 18:00 UTC, S_G et S_A deviennent NON ESTIMABLES.

Les champs `name`, `pseudonym`, `bio`, `icon`, `profile*` sont retirés avant toute écriture. Les réponses brutes ne sont pas conservées, seuls leur SHA-256 et leur taille le sont. Les lignes postérieures à T_fin sont mises à part dans `data/global_post.jsonl.gz`, jamais lues par le rejeu.

Contrôles de collecte, sans regarder le détecteur :
- rappel du recensement : les lignes de la famille Ballon à ≥ F dans la fenêtre doivent s'y retrouver, écart écrit ;
- rappel du recensement contre les lignes ≥ F de la base de production depuis le 27 oct., écart écrit ;
- `/trades` borné contre `/v2/trades` sur le marché de la sonde, écart écrit ;
- continuité des horodatages, doublons et lignes rejetées comptés.

## Base de sondage et tirage des témoins

Fait une seule fois, après A1, avant tout calcul de score.

- Base : tous les `event_slug` ayant au moins une ligne de recensement dans [T_alertes, T_fin[, hors famille Ballon (identifiants et slugs de `ballon_2026_20261030/data/catalog_*.json`). Un événement sans aucune ligne ≥ F n'est pas dans la base : limite écrite.
- Quatre strates :
  - D+ : titre sans motif `_PRICE` ni `_SPORT` de `priority.py`, au moins 20 lignes ;
  - D- : même titre, moins de 20 lignes ;
  - C+ : motif prix ou sport, au moins 20 lignes ;
  - C- : motif prix ou sport, moins de 20 lignes.
- Candidats : 8, 8, 5, 4. Tirage aléatoire simple dans chaque strate, graine = SHA-256 du fichier du recensement, slugs triés avant mélange.
- Inclusion en tourniquet D+, D-, C+, C-, jusqu'à 50 marchés au total. Au plus 4 marchés par événement ; au-delà, tirage simple de 4 marchés (π second degré = 4/M). Les événements qui feraient dépasser 50 ne sont pas pris et l'arrêt est écrit.
- Conservés pour chaque unité : effectif de strate N_h, tirés n_h, π_h = n_h/N_h, marchés retenus, M.
- Les probabilités servent à l'estimateur de Horvitz-Thompson du nombre de dossiers ajoutés par la visibilité des petites lignes, compté sur les marchés retenus seulement, sans et avec le poids M/m du second degré : les deux chiffres encadrent une quantité que ce tirage n'identifie pas exactement.
- Limite du tirage, déjà effectué et conservé : le motif prix/sport a été testé sur le titre de marché de la ligne la plus récente, pas sur celui de l'événement. 3 des 4 unités D+ sont des matchs. L'estimateur total reste valable, la lecture par strate non.

## Le pipeline rejoué

Mêmes modules que la production, importés depuis une copie gelée du paquet, dans une racine isolée :

1. Découverte : `collect.normalize_event`, `normalize_market` sur Gamma, pour la famille et les témoins seulement. Catalogue reconstitué : version ouverte à `createdAt` + 600 s (intervalle du catalogue), version fermée à `closedTime` ; une échéance passée déclenche une réévaluation ; `umaResolutionStatus` et la liquidité actuelle sont retirés. Tout événement du seul recensement est `unmapped:<slug>`, avec une clé de marché par condition, supposé ouvert (hypothèse M1). Le catalogue local n'est pas utilisé : il ne connaît que les marchés encore vivants après T_fin, ce qui donnerait des métadonnées selon le futur. M1 ne ferme jamais un événement alors que la production l'exclurait : chaque sortie porte un drapeau `m1`, chaque dossier le dit, et les files sont données **avec et sans M1**.
2. Ingestion chronologique : `collect.normalize_trade` et identifiants `signature:occurrence`.
3. Historique des wallets : `first_timestamp` sur les lignes observées avant le tick, comme `engine.wallet_history`.
4 et 5. Caractéristiques et score : `signals.evaluate`, noyau SHA `45d1a5c0…`, seuils inchangés, appelé sur les wallets touchés. Équivalence vérifiée à 64 ticks fixes contre l'appel complet sur toute la trame, refus en cas d'écart. Au-delà de 25 000 lignes (limite mémoire), la vérification porte sur un échantillon haché de wallets, fermé par la synchronie : elle est comptée comme partielle.
6. File : `material_fingerprint` de la production pour dédupliquer ; première priorité par paire wallet-événement.
7. Alertes : `prospective_bridge.publish_cases` sans allocation, horloge simulée, base SQLite isolée.
8. Dossiers : `reports.export_dossier` et `review.case_scope`. L'enquête réseau `investigate` n'est pas rejouée : aucune réponse contemporaine n'existe.

Différences avec `run_cycle`, assumées :
- le plafond de 50 000 lignes est imité par une durée ;
- la sélection `priority.select_markets` est remplacée par le modèle de rotation ci-dessous ;
- les réobservations sont comptées mais seules la première version et les hausses de score sont écrites sur disque ;
- pas de budget réseau simulé par cycle ;
- `liquidity_fraction` et `cohort_size` ne peuvent jamais se déclencher : aucune liquidité datée n'existe. La famille « size » perd donc 2 règles sur 3, dans tous les scénarios ;
- `specialization_shift` est impossible pour un wallet ayant une ligne sur un événement M1 (pas de tags) ;
- le filtre F relève de fait les seuils hors famille et témoins : synchronie à 2 500 $ au lieu de 250 $, rupture de taille à 12 500 $ au moins. La file est déformée dans les deux sens par rapport à la production ;
- `end_date` est la valeur actuelle : elle sert de barrière de priorité et, par exclusion, modifie le dénominateur de concentration. Date historique invérifiable. Aucun marché de la famille n'a d'échéance avant T_fin, contre 112 marchés témoins sur 188.

## Scénarios (fixés avant calcul)

| Id | Lignes visibles | Plafond d'analyse | Délai | Rôle |
|---|---|---|---|---|
| S_A | S_G + petites lignes de la famille et des témoins selon la rotation neutre | 44 h | 60 s | **Scénario de référence** |
| S_C | Famille Ballon + témoins, toutes tailles, depuis 30 jours | aucun | 60 s | Demande littérale : univers témoin complet |
| S_G | Recensement ≥ F, plus lignes ≥ F de la famille et des témoins | 44 h | 60 s | Flux global seul |
| S_B | S_A sans plafond | aucun | 60 s | Effet du plafond de 50 000 |
| S_L | S_A avec la règle de production, qui nomme « ballon d'or » | 44 h | 60 s | Le pipeline tel qu'il est écrit, biaisé par l'affaire |
| S_E | Appel du noyau à l'heure de la première priorité, sur l'historique taker que l'API rend pour le wallet (A5) ; synchronie reportée du scénario, non recalculée | aucun | 60 s | Fragilité aux trades hors univers |

Tous les scénarios sauf S_C partent de T_debut : le recensement ne remonte pas plus loin, et l'écart entre eux ne doit mesurer que ce que leur nom annonce. S_C garde 30 jours, uniformément sur son univers.

**Rotation neutre.** `priority.py` a été écrit après l'article et sa règle `awards` nomme « ballon d'or ». Avec ce mot, 93 marchés de la famille seraient visités toutes les 215 min et aucun témoin ; sans lui, aucun marché de la famille n'est éligible. Le scénario de référence retire donc ce seul mot de la règle. S_L le garde, pour mesurer ce qu'il change.

Rotation : `priority.announcement_scope` (fonction réelle) sur la version ouverte du marché. Éligible : visite toutes les 215 min (1 076 / 5 cycles). Sinon : visite toutes les 14 214 min (71 071 / 5 cycles). Phase par hachage de l'identifiant du marché. Une ligne < 1 000 $ devient visible à la visite suivante ; une ligne de plus de 3 780 s avant la première visite n'est jamais vue (`initial_lookback` + `overlap`). Une ligne ≥ 1 000 $ et < F, visible en production par le flux global, n'existe ici que pour la famille et les témoins, où elle est traitée comme visible à +60 s. La limite de 250 lignes par page n'est pas simulée.

## Mesures

Pour chaque scénario, sur des entrées sans alias :
- file chronologique des premières priorités, par paire et par wallet, depuis T_debut, depuis T_alertes, et sur les fenêtres glissantes de 24 h et 72 h avant une première priorité, avec et sans M1, ex æquo résolus par ordre lexical et signalés ; T_alertes est calé sur la date de l'affaire, les fenêtres glissantes et le taux par jour ne le sont pas ;
- score, règles, rang de compétition au tick, nombre de paires examinées ;
- dossiers nouveaux par jour, réobservations, part d'annonces sur les seuls dossiers catalogués (inconnue pour M1) ;
- pour les témoins : comportements (score ≥ 1, datés au premier score ≥ 1), priorités, pondérés par 1/π, IC bootstrap par grappes d'événements (2 000 tirages, graine fixe), rapportés comme descriptifs ;
- ressources : RSS maximal, delta de swap, disque, requêtes.

Pas de p-value : aucun modèle nul échangeable n'est défendable, et aucun label d'initié n'existe. Aucune précision, aucun rappel, aucun taux de faux positifs.

## Scellement, puis comparaison

Ordre obligatoire :
1. R1 : S_A, S_C, S_G, S_B, S_L ; écriture de `derived/R1_*.json.gz`.
2. A5 + S_E sur les wallets prioritaires pris dans l'ordre de la file S_A depuis T_alertes, puis S_C, sans lire de label, plafond 100 requêtes. R2 : `derived/R2_enrichment.json.gz`. Un wallet de la famille absent de S_A garde ainsi une seconde chance qu'un wallet du seul recensement n'a pas ; c'est une limite. Une réponse vide, tronquée à 10 000 lignes ou sans la transaction déclencheuse est non estimable, jamais un résultat.
3. `code/ana_suite.py sceller` écrit `derived/pre_label_seal.json` une seule fois : SHA-256 de toutes les sorties et de `data/wallet_histories.jsonl.gz`, heure de scellement. Ajout au gel.
4. R3 : `code/ana_suite.py labels` lit `../detection_20261030/data/labels_after.json` et compare. R3 est exploratoire.

Aveuglement : aucun code du rejeu ne lit les alias. Les fichiers `ballon_2026_20261030/data/raw/`, `trades_normalized.jsonl`, `labels_after.json` (deux copies) les contiennent et sont interdits avant R3. L'auteur connaît toutefois le wallet : les sorties de R1 contiennent des adresses, l'aveuglement porte sur le code et sur l'ordre de scellement, pas sur sa personne. Les auditeurs de la phase 5 restent aveugles aux résultats.

## Verdicts possibles (fixés d'avance)

Pour Thin, dans chaque scénario, parmi : `DETECTE_RANG_<n>` (prioritaire avant T_fin), `COMPORTEMENT_SANS_PRIORITE` (score 1), `NON_DETECTE` (évalué, score 0), `NON_EVALUE` (lignes absentes du scénario). `NON_ESTIMABLE` ne se décide pas ici : il vaut pour la détection historique réelle (A0), et pour un scénario dont le plan de repli aurait coupé la couverture avant la première heure utile. Le recensement a atteint T_debut, donc ce second cas ne s'applique pas.

Le résultat reste « conditionnel, non indépendant » quel qu'il soit. Le rejeu antérieur reste un objet distinct.

Lecture fixée d'avance :
- S_A est le scénario de référence pour « aurait émergé dans des conditions réalistes » ;
- une première priorité précédée de plus de 50 dossiers nouveaux dans les 72 h sera décrite comme « noyée dans une file chronologique », sans que cela invalide le signal ; la même mesure sans M1 est donnée à côté ;
- si le wallet n'atteint la priorité que dans S_C ou S_B, on écrit que le résultat dépend d'une visibilité que la production n'avait pas.

## Plafonds d'exécution

Garde-fou externe `code/guard.py` :
- RSS du groupe de processus > 400 Mo : arrêt ;
- swap > base + 100 Mo : arrêt ;
- écritures de l'étude et du bac à sable > 250 Mo : arrêt ;
- disque libre < 14 Go pendant l'exécution, ou < 15 Go avant une phase lourde : arrêt ou refus ;
- battement du collecteur vieux de plus de 180 s : arrêt.

Arrêt par SIGTERM, puis SIGKILL après 20 s. État et motif dans `data/guard_*.json`.

Le pilote est lancé sous `diskguard.py run --need 300M`, `nice -n 15`. Si un plafond saute deux fois, le périmètre est réduit (d'abord S_B, puis la grille passe à 300 s) et c'est écrit. La base de production n'est jamais ouverte qu'en `mode=ro`, et la collecte passe avant ce pilote.

## Tests multiples

Registre `registre/tests.jsonl`, une ligne par balayage réel avec `n_comparaisons` = paires × ticks évalués. Cumul avec les études antérieures reporté dans le rapport. Aucune significativité n'est revendiquée.

## Changements avant gel (aucun score calculé à ce moment)

- La famille Ballon comprend maintenant les 3 flux tronqués de l'étude antérieure, dont `48361`, « Ballon d'Or Winner 2026 », 83 203 lignes dans la fenêtre, absentes des rejeux précédents. S_C n'est donc pas comparable tel quel au rejeu du 30 octobre.
- 604 lignes du recensement sont rejetées par le vrai normaliseur (même quarantaine qu'en production) et comptées dans chaque sortie.
- A5 relevé à 100 requêtes : la collecte a coûté moins que prévu (147 sur 300 à ce stade).
- S_E devient un calcul ponctuel à l'heure de la première priorité : un rejeu complet avec historiques exigerait des lignes de tous les autres wallets, sans en changer la lecture pour le wallet interrogé.

## Corrections après les deux audits d'avant-gel (aucun score calculé)

Deux audits indépendants, sur le code et le plan, ont trouvé 4 BLOQUANTS et 13 MAJEURS (constats recoupés entre eux), sans lire aucun résultat :
- le statut de résolution actuel décidait la visibilité des petites lignes de la famille : retiré ;
- le mot « ballon d'or » de la règle de production décidait la rotation : scénario de référence neutre, S_L à part ;
- M1 ouvrait des événements sans jamais les fermer, et interdisait certaines règles : clé de marché par condition, drapeau et résultats avec et sans M1 ;
- le catalogue local sélectionnait selon le futur : retiré ;
- « borne basse » était faux : retiré ;
- échéances sans réévaluation, plancher d'historique inégal entre scénarios, premier score retenu au lieu du premier score ≥ 1, poids du second degré ignoré, reprise sous une autre grille, configuration lue en direct, oracle absent de S_C : corrigés et, sauf le poids, testés dans `code/ctl_replay.py`.

Les rapports d'audit sont résumés dans `audit/PRE_GEL.md`.
