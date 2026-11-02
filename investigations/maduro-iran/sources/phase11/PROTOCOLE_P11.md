# Phase 11 : protocole pré-enregistré

Rédigé le 01/10/2026 vers 09:00 UTC :
- après l'audit `CLOB_LIVE_AUDIT.md` ;
- après le démarrage du collecteur (08:51 UTC) ;
- **avant toute alerte SIG_HIST en direct et avant tout calcul de résultat**.

Toute déviation sera signalée dans le rapport.

## 0. Le signal

**SIG_HIST V1** est celui de la phase 9, identifié par son empreinte : `SIG_HIST_VERSION.json`, sha256 `bbb016d24f36c3e1…`. Toute modification créerait SIG_HIST_V2, sans jamais remplacer V1. **Aucune variante n'est prévue en phase 11.**

**En direct (SIG_HIST_LIVE).** Même règle, même code (`p9_detector.Detecteur`), mêmes modèles et seuils. L'état est construit dans cet ordre :
1. l'historique de la phase 9 (trades ≥ 100 $ jusqu'au 16/09/2026) ;
2. un rattrapage du 16/09 au démarrage (data-api, trades preneurs ≥ 100 $, marchés actifs ou fermés depuis le 16/09) ;
3. le flux RTDS en direct, où le preneur est identifié par le champ `fee`, ou à défaut comme la seule ligne de la transaction.

**Vérification a posteriori.** Chaque alerte live est recalculée a posteriori sur le data-api `takerOnly=true`, avec la définition exacte. Seules les alertes confirmées entrent dans l'évaluation. Les écarts sont publiés.

## 1. Les instants

| Instant | Définition |
|---|---|
| **T0** | heure de l'échange (ms) du `last_trade_price` portant le hash du trade du wallet, à défaut l'horodatage RTDS (seconde) |
| **T_obs** | heure locale de réception de la ligne RTDS du wallet signalé. C'est le premier instant où SIG_HIST est calculable (le wallet est connu). **Toutes les latences de l'observateur se comptent depuis T_obs.** T0 est publié à côté |
| Horloge | heure locale corrigée par le décalage sntp mesuré toutes les 30 min |

## 2. Le carnet connu à T (règle du §10)

**Reconstruction.** Le carnet d'un jeton à l'instant t est rebâti à partir de :
- son dernier `book` reçu avant t (heure locale de réception) ;
- puis tous les `price_change` reçus avant t, appliqués dans l'ordre. Chaque changement donne la nouvelle taille totale du niveau.

**Interdits :**
- aucune information reçue après t ne sert à décider à t ;
- aucune alerte n'est retirée parce qu'un ordre aurait ou n'aurait pas été rempli ensuite.

**Contrôle de cohérence.** Le `hash` des messages et les instantanés REST (toutes les 10 min, et en rafale après chaque alerte live) sont comparés au carnet reconstruit. Le taux d'accord est publié.

## 3. Exécution simulée (aucun ordre réel)

### Ordre au marché

- **Latences :** T_obs + L, avec L = 0, 100 ms, 250 ms, 500 ms, 1, 2, 3, 5, 10, 30 et 60 s. On ajoute T0 + L comme borne théorique (wallet connu instantanément).
- **Tailles :** S = 50, 100, 250, 500, 1 000, 2 500, 5 000 et 10 000 $.
- **Exécution :** on parcourt les asks du carnet connu à l'instant de décision.
- **Mesures publiées :**
  - VWAP_EXECUTION, quantité remplie, quantité restante, niveaux consommés ;
  - SLIPPAGE_VS_MID = VWAP − mid ;
  - spread ;
  - frais = taux du `feeSchedule` du marché × min(p, 1 − p) × actions, ou le taux mesuré dans RTDS si disponible.
- **Hypothèse :** notre ordre ne modifie pas le carnet des instants suivants. Cette hypothèse est signalée.

### Sortie

- **À l'horizon H** = 10, 30, 60, 120 ou 300 s après l'entrée, on vend sur les bids du carnet connu à ce moment.
- **À la résolution :** 1 ou 0 par action.

### Statistiques par case

Nombre de trades, taux de remplissage, VWAP, glissement, frais, rendement brut et net, MAE et MFE (mid, de l'entrée à la sortie).

### Ordres limites (§20)

- **Pose :** à T_obs, en achat.
- **Prix K, défini par le carnet à T_obs :** best ask, best ask − 0,5 point, − 1 point, − 2 points. K est arrondi au tick.
- **Durée de vie :** 10, 30, 60 et 300 s.
- **Remplissage conservateur :**
  - la file devant nous est la taille du niveau K côté bid à la pose ;
  - nous sommes remplis quand les ventes preneuses au prix K, après la pose, dépassent cette file plus notre taille ;
  - ou quand un trade s'imprime strictement sous K.
  - Les baisses de taille sans trade (annulations) ne nous font pas avancer.
- **Remplissage optimiste :** les annulations nous font avancer. Il est publié, mais ne sert jamais à conclure.
- **Publiés ensemble :** taux de remplissage et rendement conditionnel. Le K n'est **jamais** choisi après observation.

## 4. Délai d'avance (§13)

Mesuré depuis T0 et depuis T_obs, avec comme référence le carnet juste avant le trade du wallet :
- premier changement du best ask d'au moins 1 tick dans la direction ;
- premier changement du mid d'au moins 0,5 point ;
- premier mouvement du mid d'au moins 1 point ;
- premier mouvement du mid d'au moins 3 points.

Distribution publiée : médiane, P25, P75, P90, min, max.

**Fenêtres analysées séparément :** 0-250 ms, 250-500 ms, 500 ms-1 s, 1-2 s, 2-3 s et 3-5 s. Pour chacune : variation du best ask et du mid, et rendement de l'entrée au marché.

## 5. Impact propre et suiveurs (§14, §15, §16)

### Impact propre

| Classe | Condition |
|---|---|
| LOW_SELF_IMPACT | IMMEDIATE_IMPACT ≤ τ_I = 0,5 point (seuil phase 10, gelé) **et** taille du wallet ≤ 50 % de la profondeur ask à moins de 2 points dans le carnet d'avant |
| HIGH_SELF_IMPACT | sinon |

### Acheteurs après T0 (10 min, RTDS)

| Groupe | Définition |
|---|---|
| KNOWN_FOLLOWER | wallet ayant déjà suivi ce leader : graphe de la phase 10, plus le suivi en direct, uniquement avant T0 |
| UNKNOWN_FOLLOWER | tous les autres |

### Mécanisme

Variation du mid entre T0 et T0 + H, décomposée sans résidu en quatre parts :

| Part | Contenu |
|---|---|
| SELF_IMPACT | niveaux retirés par le trade du wallet |
| KNOWN_FOLLOWER_IMPACT | niveaux retirés par les trades des suiveurs connus |
| UNKNOWN_TRADER_IMPACT | niveaux retirés par les autres trades |
| QUOTES | changements de niveaux sans trade : placements et annulations |

La cause reste **UNKNOWN_CAUSE** tant qu'elle n'est pas démontrée.

## 6. Contrôle (§7)

**Événement de contrôle :** pour chaque alerte, un ou plusieurs FAE non SIG_HIST de la watchlist, sur la même période de collecte, appariés sur :
- le décile de prix ;
- la tranche de spread ;
- la profondeur ask à 2 points (tercile) ;
- le temps avant résolution ;
- la catégorie ;
- l'activité des 10 min précédentes.

**Traitement :** même pipeline, avec T_obs = réception RTDS du trade de contrôle.

## 7. Stratégie principale et critères (§23)

**Stratégie principale, fixée ici :**
- ordre au marché à **T_obs + 0** ;
- **500 $** ;
- sortie sur le carnet à **T_entrée + 300 s** ;
- frais du marché.

La grille complète est descriptive.

**Évaluation finale :** quand 100 alertes SIG_HIST confirmées ont un carnet enregistré, ou au bout de 6 semaines.

**La stratégie n'est démontrée que si les 10 critères du §23 sont réunis :**
- moyenne nette > 0 ;
- IC 95 % par bootstrap par marché, borne basse > 0 ;
- écart avec le contrôle > 0, IC excluant 0 ;
- moyenne sans les 5 % meilleurs trades > 0 ;
- aucun wallet ni marché au-dessus de 20 % des trades ;
- taux de remplissage à 500 $ ≥ 80 % ;
- mécanisme identifié par le §5.

Sinon : **NO ACTIONABLE EDGE DEMONSTRATED**.

**Rapports intermédiaires.** Ils sont descriptifs et n'entraînent aucun changement de règle.

## 8. Maduro et Iran (§17, §18)

Analyse séparée, uniquement sur les données historiques de la phase 10 : flux complet et niveaux consommés. Le carnet complet d'époque n'existe pas.
- **Maduro :** du 03/01 01:00 UTC à l'annonce.
- **Iran :** du 27/02 12:00 UTC à l'annonce.
- Les heures externes sont marquées **VERIFIED** ou **APPROXIMATE**.
