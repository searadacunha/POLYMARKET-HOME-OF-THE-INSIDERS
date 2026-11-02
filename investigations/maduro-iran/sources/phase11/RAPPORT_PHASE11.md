# Phase 11 : capture du lead sur le carnet réel

**Rapport intermédiaire n°1 : 01/10/2026, 09:20 UTC.** Collecte en direct depuis 08:51 UTC, détection SIG_HIST en direct depuis 09:10 UTC.

Documents de référence :
- `CLOB_LIVE_AUDIT.md` : l'audit ;
- `PROTOCOLE_P11.md` : le protocole, écrit avant toute alerte ;
- `README_RAW_DATA.md` : les données brutes ;
- `SIG_HIST_VERSION.json` : l'empreinte du signal.

**Aucun ordre n'a été passé.** Les processus enregistrent et simulent seulement.

## Où on en est

L'évaluation finale du §23 suppose **100 alertes confirmées avec carnet enregistré** (ou 6 semaines). À cette heure, il y a **1 alerte**. Ce rapport livre donc quatre choses :
1. l'audit du CLOB en direct et ce qu'il change à la question ;
2. le dispositif de collecte, en marche, vérifié ;
3. une première alerte complète, traitée de bout en bout ;
4. les analyses séparées de Maduro et de l'Iran (§17, §18), qui ne dépendent pas de la collecte.

Verdict à ce stade : **NO ACTIONABLE EDGE DEMONSTRATED**. Ce n'est pas un résultat d'échec : l'évaluation n'a pas encore eu lieu.

### Le constat le plus important de l'audit

**SIG_HIST ne devient observable qu'environ 2 s après le trade du wallet.**
- Le carnet est visible en direct, avec environ 20 ms de latence.
- Mais le wallet n'y figure pas. Il faut l'attendre :
  - par RTDS : **2,1 s** en médiane après le trade ;
  - par les logs Polygon : **0,8 s plus tôt** (T0 + ~1,3 s).
- Or la phase 10 avait mesuré, sur l'historique, qu'à T0 + 2 s le meilleur ask est déjà +0,8 point au-dessus du prix du wallet.

Conséquence : **la fenêtre 0-1 s n'est accessible à aucun observateur qui attend l'identité du wallet.** L'expérience porte donc sur ce qui reste à partir de T_obs.

---

## 1. Ce que le CLOB permet réellement de voir (§3)

Détail : `CLOB_LIVE_AUDIT.md`.

**MESURÉ**

| Donnée | Statut |
|---|---|
| Carnet complet en direct (instantané + mises à jour par niveau, horodatage d'échange en ms) | DISPONIBLE |
| Trades (prix, taille, côté, frais, hash) | DISPONIBLE |
| Latence de réception | environ +20 ms après correction d'horloge (sntp ± 48 ms) |
| Wallet | PARTIEL : RTDS 2,1 s après le trade (0,9 à 3,3 s) ; logs Polygon 0,81 s plus tôt que RTDS (P10 0,44 s, P90 1,1 s ; 763 transactions sur 763) |
| Ordres individuels (placements, annulations) | ABSENT : seule la taille agrégée par niveau est visible |

- **Reconstruction du carnet** à partir des messages bruts, contre les instantanés REST : best ask identique 133 fois sur 134, best bid 133 sur 134, niveaux complets 106 sur 134 (écarts de taille dans les ~100 ms de la requête).
- **Les mises à jour de niveau d'un trade arrivent ~20 ms avant son `last_trade_price`** (horodatage d'échange, médiane −22 ms, de −289 à +46 ms). L'attribution d'un changement du carnet à un trade se fait donc sur une fenêtre de −300 à +50 ms.

**INFÉRÉ**
- La décision la plus précoce possible est T_obs, soit T0 + 1,3 à 2,1 s selon la voie.
- Tout ce qui se passe avant appartient au wallet et aux acteurs qui voient le carnet sans connaître le wallet.

**INCONNU**
- Si un nœud Polygon privé (ou le mempool) donnerait le wallet avant l'inclusion du bloc.

**PROCHAINE ÉTAPE**
- Mesurer T_obs par la chaîne sur toutes les alertes (enregistré depuis 09:10).

## 2. Le dispositif en marche (§4 à §8, §22)

### Les processus

| Processus | Rôle |
|---|---|
| `scripts/p11_clob_collector.py` | carnet de 651 marchés (3 websockets, 1 302 jetons), tous les trades de la plateforme (RTDS), logs Polygon des wallets SIG_HIST et en-têtes de blocs, instantanés REST toutes les 10 min, rafales REST après chaque alerte, horloge |
| `scripts/p11_signal_listener.py` | recalcule SIG_HIST V1 en direct sur chaque trade RTDS |
| `scripts/p11_run.sh` | relance automatique |

Les processus tournent détachés de la session (`caffeinate`). **Ils s'arrêtent si le Mac redémarre** : la commande de relance est dans `README_RAW_DATA.md`.

### Le listener

- **Historique rejoué :** les trades de la phase 9 jusqu'au 16/09.
- **Rattrapage :** du 16/09 au démarrage, 83 128 trades sur 5 434 marchés.
- **Wallets éligibles au démarrage :** 107.
- **Pour chaque alerte :**
  - demande de rafale REST (T+0, 100, 250, 500 ms, 1, 2, 3, 5, 10, 30, 60 s) ;
  - ajout du marché à la watchlist ;
  - vérification a posteriori par le data-api ;
- **Contrôles :** tous les FAE sont journalisés, ce qui constitue le réservoir de contrôles.

### La watchlist

| Niveau | Contenu |
|---|---|
| A | 500 marchés touchés par les wallets SIG_HIST dans les 30 derniers jours (98 des 139 wallets historiques sont actifs) |
| C | 150 marchés de contrôle tirés au hasard (graine 11) |
| D | ajouts dynamiques |

- Univers : 3 975 marchés actifs, avec les mêmes exclusions qu'aux phases 8-9.
- Hors watchlist, le carnet d'une alerte est quand même connu dès T_obs + ~0,1 s grâce à la rafale REST.

### SIG_HIST préservé

- V1, sha256 `bbb016d24f36c3e1…`. Aucune variante, aucun seuil touché.

### Volume et disque

- Environ 1,1 à 1,5 Go par jour compressé, pour 32,5 Go libres.
- **Autonomie d'environ 3 semaines.** Gardes à 6 Go (contrôles suspendus) et 3 Go (arrêt).

## 3. Première alerte en direct, de bout en bout (§8 à §16)

Alerte `A20261001T091257_1`.
- **Wallet :** `0x8f42ae0a`, 57 événements résolus, hist_score 0,244.
- **Trade :** achat de **NO** pour 3 111 $ à 0,852, marché « Will Likud win 30-34 seats ».
- **Confirmé preneur** par le data-api à +60 s.

| Instant (depuis T0) | Ask | Mid | Commentaire |
|---|---|---|---|
| juste avant le trade | 0,84 | 0,835 | profondeur ask à 2 points : 3 111 $ |
| T0 + 0,1 s | 0,87 | 0,850 | le wallet a consommé **100 %** de la profondeur à 2 points (dernier niveau 0,86) : HIGH_SELF_IMPACT |
| T0 + 1,67 s | | +3 points | mouvement de 3 points atteint |
| **T_obs = T0 + 2,12 s** | 0,87 | 0,865 | le wallet est connu (RTDS) |
| T_obs + 1 s | 0,88 | 0,870 | |
| T_obs + 60 s | 0,88 | 0,870 | |

**Exécution simulée**, ordre au marché à T_obs, sortie sur le carnet à +300 s, frais du marché inclus :

| Taille | Prix moyen | Glissement vs mid | Net |
|---|---|---|---|
| 500 $ | 0,870 (1 niveau) | +0,5 point | **−2,4 %** |
| 2 500 $ | 0,876 | +1,1 point | −4,0 % |
| 10 000 $ | rempli, 4,5 points au-dessus du mid | | −8,7 % |

Entrée à T_obs + 1 s : −3,5 %. MAE −0,5 point, MFE 0.

**Ordres limites** (best ask − 0,5, − 1 ou − 2 points, posés à T_obs) : **aucun rempli** en 10, 30, 60 ou 300 s.

**Mécanisme** (mid +3,5 points de T0 à T0 + 60 s) :

| Part | Contribution |
|---|---|
| Impact propre du wallet | +1,5 point |
| Acheteurs inconnus | +2,0 points (10 acheteurs, 1 392 $, délai médian 4,9 s, P25 2,9 s) |
| Suiveur connu | 0 (1 suiveur, 73 $) |
| Cotations | 0 |

**INFÉRÉ (une seule alerte : illustration, pas un résultat)**
- Le mouvement était fait à 86 % **avant** que le wallet soit identifiable (mid +3,0 points à T_obs, sur +3,5 à 60 s).
- L'observateur achète au sommet du premier saut et revend au bid.

**PROCHAINE ÉTAPE**
- Atteindre 100 alertes confirmées, puis appliquer le protocole (stratégie principale, contrôles, IC).

## 4. Maduro (§17), analyse séparée

Source : flux complet de la phase 10 (data-api, toutes tailles, ordre exact, niveaux consommés), de 01:00 UTC à l'annonce. Le carnet complet d'époque n'existe pas ; seuls les niveaux consommés sont connus. Tableau complet : `maduro_timeline.csv`, 3 584 trades, avec prix, wallet, taille, niveaux, impact propre, acheteurs suivants et signal.

| Heure UTC | Fait | Niveau |
|---|---|---|
| 01:00 → 06:00 | 241 trades : 57 376 $ d'achats YES-équivalents et 56 949 $ de ventes (flux **équilibré**) ; prix de 0,07 à 0,12 | MESURÉ |
| 01:38:35 → 02:58:25 | `0x31a56e9e` achète 3 fois (6 000, 7 000 et 7 215 $) à 0,07-0,08 ; 0 à 4 petits acheteurs derrière, prix inchangé à +10 min | MESURÉ |
| 03:42:01 | `0x6baf05d1` achète 10 000 $ et balaie 85 niveaux (0,09 → 0,13, impact propre +13 points) ; retour à 0,09 en 10 min | MESURÉ |
| 03:46 | ordre de lancement (non public à l'époque) | APPROXIMATE |
| 05:35:41 et 05:46:23 | Chiwawas : 5 188 $ puis 4 710 $ (financé 2,8 min avant) | MESURÉ |
| 05:51:25 | seule alerte SIG_HIST de la nuit : achat de **NO** | MESURÉ |
| ~06:00 | premières explosions signalées. NOTAM de la FAA en vigueur à 06:00 UTC, heure de publication non établie | APPROXIMATE |
| 06:15:41 / 06:16:11 | premier trade ≥ 0,5 / repricing (série CLOB) | MESURÉ |
| 09:21 | annonce de Trump | APPROXIMATE |

**Qui achète avant 06:00 :**
- 44 acheteurs, mais 5 wallets font **86 %** du volume :
  - `0x31a56e9e` : 20 215 $ ;
  - `0x6baf05d1` : 10 000 $ ;
  - Chiwawas : 9 898 $ ;
  - `0x858d551d` : 5 282 $ ;
  - `0x784feec3` : 3 791 $.
- Les petits montants (moins de 100 $) font 52 trades et **825 $ au total** : du bruit.
- Les 3 premiers gardent leur position.
- `0x31a56e9e` et `0x6baf05d1` sont deux « comptes forts » de juillet, sans lien avec le réseau des 8 (phases précédentes).

**Réponse au §17**

- **MESURÉ.**
  - Les premiers gros achats précèdent de 2 h 20 à 4 h 20 les explosions publiques (APPROXIMATE), et le premier précède l'ordre de lancement.
  - Les ventes ont absorbé ces achats : +5 points en 4 h.
  - Aucun signal public spécifique n'est identifié avant 06:00.
- **INFÉRÉ.** La fenêtre a duré plus de 4 h et était **ouverte à tous, au même prix**. C'est compatible avec une information sur l'imminence comme avec un pari sur la tension publique (renforcement militaire, avertissements FAA depuis novembre 2025).
- **INCONNU.** La cause : UNKNOWN_CAUSE.
- **PROCHAINE ÉTAPE.** Heure de publication du NOTAM ; posts X archivés de 01:00 à 06:00 UTC.

## 5. Iran (§18), analyse séparée

Source : flux complet du 27/02 12:00 au 28/02 07:00 (21 168 trades), complet contre la chaîne (807 transactions sur 807). Tableau : `iran_timeline.csv`.

| Heure UTC | Fait | Niveau |
|---|---|---|
| 27/02 12:00 → 23:59 | **activité normale** : prix 0,15-0,26 ; 50 à 260 k$ d'achats par heure | MESURÉ |
| 27/02 12:52 → 21:38 | 5 alertes SIG_HIST dans les deux sens | MESURÉ |
| 27/02 20:38 | autorisation des frappes (non publique) | APPROXIMATE |
| 28/02 00:00 → 05:10 | jour d'échéance : 192 k$ d'achats contre **1,17 M$ de ventes** ; prix de 0,20 à 0,15 | MESURÉ |
| **05:15** | **premier changement anormal** (référence glissante sur 12 h) : `0x4dfd481c` achète 32 337 $ (148 263 $ au total jusqu'à 06:13). Avec la référence « veille » de la phase 10 : 06:10 | MESURÉ, dépend de la référence |
| 05:15 → 06:12 | prix de 0,15 à 0,39 ; 191 acheteurs, les 5 premiers font 64 % | MESURÉ |
| 06:12:13 | `0x9d84ce03` (PERSISTENT_LEAD en phase 9) achète 27 157 $ ; pas de SIG_HIST (déjà actif sur ce marché dans les 24 h) | MESURÉ |
| 06:12:17 / 06:13:22 | premier trade ≥ 0,5 / repricing (série CLOB) | MESURÉ |
| ~06:15 | début des frappes | APPROXIMATE |
| 06:16:09 | alerte SIG_HIST : vente YES-équivalente | MESURÉ |
| 06:23 | annonce israélienne et sirènes | VERIFIED |

**SIG_HIST le jour J :** aucune alerte avant le repricing.

**INFÉRÉ**
- Le flux devient anormal environ 1 h avant les frappes si on le rapporte aux heures précédentes, mais pas si on le rapporte à la veille (plus active). Les deux références sont publiées.
- Le prix était déjà passé de 0,15 à 0,39 avant le repricing CLOB.

**INCONNU**
- Les signaux publics à la minute.
- La cause des achats de `0x4dfd481c` : UNKNOWN_CAUSE.

## 6. Critères du §23 (état à 09:20 UTC)

| Critère | État |
|---|---|
| 1 SIG_HIST observable avant l'entrée | oui, par construction (T_obs) |
| 2 le carnet réel permet de mesurer l'exécution | **oui** (reconstruction vérifiée, rafales REST) |
| 3 positif hors échantillon | non évalué (n = 1) |
| 4 à 6 après frais, glissement, taille réaliste | mesurés, non évalués |
| 7 pas dépendant de quelques événements | non évalué |
| 8 survit au contrôle | non évalué (1 contrôle) |
| 9 pas de sélection par le futur | **oui**, par construction |
| 10 mécanisme identifiable | décomposition en place |

**Verdict à ce stade : NO ACTIONABLE EDGE DEMONSTRATED.** Évaluation à 100 alertes confirmées.

## 7. Précisions de méthode ajoutées après le protocole, avant toute évaluation

1. **T_obs par la chaîne** (logs Polygon) : mesure ajoutée à 09:10. Elle est filtrée sur les wallets SIG_HIST depuis 09:17 pour limiter le disque.
2. **Carnet « juste avant » le trade :** dernier état antérieur à la rafale de mises à jour du trade (horodatage d'échange −300 ms).
3. **Instantanés REST intégrés** à la reconstruction du carnet, à leur heure de réception.
4. **Contrôles** pris dans les marchés dont le carnet est enregistré.

## 8. Fichiers

**`phase11/`**
- Rapports et protocole : `RAPPORT_PHASE11.md`, `PROTOCOLE_P11.md`, `CLOB_LIVE_AUDIT.md`, `README_RAW_DATA.md`, `SIG_HIST_VERSION.json`
- Tables live : `live_alerts.csv`, `orderbook_snapshots.csv`, `execution_simulation.csv`, `latency_curve.csv`, `capacity_curve.csv`, `lead_time_distribution.csv`, `follower_impact.csv`, `self_impact.csv`, `limit_orders.csv`
- Cas historiques : `maduro_timeline.csv`, `iran_timeline.csv`

**Scripts** : `scripts/p11_common.py`, `p11_clob_collector.py`, `p11_signal_listener.py`, `p11_replay.py`, `p11_execution.py`, `p11_analysis.py`, `p11_run.sh`.

**Données brutes** : `donnees/brut_p11/`.

**Pour mettre à jour ce rapport :**
```
cd ~/Documents/Crypto/enquete_maduro_iran/scripts && python3 p11_execution.py && python3 p11_analysis.py --live
```

**Sources publiques :**
- [Wikipedia, intervention de 2026 au Venezuela](https://en.wikipedia.org/wiki/2026_United_States_intervention_in_Venezuela)
- [Wikipedia, guerre d'Iran de 2026](https://en.wikipedia.org/wiki/2026_Iran_war)
- [Times of Israel, 28/02/2026](https://www.timesofisrael.com/liveblog_entry/israel-has-launched-a-preemptive-attack-on-iran-defense-minister-katz-says-sirens-sound-across-israel/)
- [CRS, fermetures d'espace aérien](https://www.everycrsreport.com/reports/IN12636.html)
- [Simple Flying, NOTAM de la FAA](https://simpleflying.com/faa-shuts-venezuelan-airspace-us-explosions-caracas/)
