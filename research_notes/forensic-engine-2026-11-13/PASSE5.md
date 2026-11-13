# Passe 5. Bandes de trades et collecte prospective

13 novembre 2026. Les seuils de `phi_monitor` ne sont pas modifiés. Aucune ligne de trade, aucun portefeuille et aucun flux brut ne sont dans Git. Les comptes ci-dessous viennent de [data/pass5_metrics.json](data/pass5_metrics.json). La borne de validation est le 14 novembre 2026 à 00:00 UTC : le score ignore tout horodatage à partir de cet instant. Le fichier le plus récent de ce téléchargement est du 13 novembre 2026.

Une hausse de prix prédite n'est pas une information privilégiée.

## API et couverture

`https://data-api.polymarket.com/v2/trades?condition=` pagine par `pagination.next_cursor`. `has_more: false` veut dire que le curseur est épuisé. Le 13 novembre 2026, la même requête sur le marché « Xi Jinping out before 2027? » avec `start=1700000000&end=1700003600` renvoie le même premier trade que la requête sans dates. Le filtre de période n'est pas utilisé. `taker_only` est laissé à sa valeur par défaut, vraie : une ligne est l'impression du preneur. Le côté `BUY` ou `SELL` est celui du preneur. Les makers ne sont pas dans la bande, et les deux faces d'une même exécution ne sont pas sommées. La clé de dédoublon est le hash, le portefeuille, le côté, l'issue, la taille, le prix et l'horodatage. Les 263 117 lignes téléchargées ont un portefeuille `0x` de 42 caractères. Elles se répartissent en 180 637 achats et 82 480 ventes.

Le plafond est de 3 pages de 1 000 lignes. Une bande qui a encore `has_more: true` est incomplète. Elle est comptée, puis elle sort du score.

| Ensemble | Complet | Incomplet, 3 000 lignes | Scoré |
|---|---:|---:|---:|
| Découverte | 33 | 27 | 33 |
| Validation nouvelle | 34 | 39 | 34 |

Les 67 bandes complètes vont de 126 à 2 663 impressions. Les 66 autres sont les marchés les plus longs : leur absence de score n'est pas un résultat négatif. `poly_data` v2 n'a pas été lancé. Le jeton HyperSync est absent, la licence du fichier `LICENSE` est GPL-3.0, et le backfill v2 ne couvre que le contrat `0xe111…996b` à partir du bloc 84 902 353. Il ne couvre ni les contrats V1 ni le contrat neg-risk `0xe222…0f59`. Les 4 270 reçus de l'archive Inca restent des transferts ERC-20, sans `OrderFilled` et sans hash commun avec les trades. Cette passe n'ajoute donc pas d'exécution on-chain aux 133 marchés.

Les 33 marchés de découverte scorés ont une série de prix de 29 points. Leur amplitude médiane est 0,0085, sous la cible de 0,15. Aucun n'a de hausse de 0,15 dans la fenêtre stockée. Quatre d'entre eux déclenchent la règle « nouveau portefeuille » à 24 h. Il n'y a pas de cible, donc pas de précision à estimer. Ce n'est pas une preuve d'absence de signal sur les 27 bandes incomplètes.

Les 34 marchés de validation scorés ont une série de 672 points, soit quatorze jours à 30 minutes. Vingt-neuf sont des courses de gouverneur 2026, les autres des endorsements pour le 2 novembre 2026. Ce sont des marchés liés. Ils comptent dans un seul bloc de validation, et ils n'ont pas servi à choisir les seuils. Ils ne font pas 34 essais indépendants.

## Quatre règles, seuils figés

Les seuils sont dans le code, pas ajustés sur la validation. Cible : hausse d'au moins 0,15 après l'instant du signal. Un prix déjà au-dessus de 0,85 n'est pas étiqueté.

1. Volume d'achat sur une heure d'au moins 1 000 USD et d'au moins trois fois la médiane des six heures précédentes, avec une bande qui commence au moins trois heures avant.
2. Portefeuille vu pour la première fois sur cette bande depuis moins de 24 h, achat d'au moins 1 000 USD, aucune vente entre-temps. « Nouveau » veut dire nouveau sur ce marché, pas nouveau sur le venue.
3. Au moins trois portefeuilles, au moins 200 USD chacun, même issue, dans une fenêtre de 600 secondes, sans vente de ces portefeuilles dans la fenêtre.
4. Le premier portefeuille fait au moins la moitié des achats de l'heure, le total vaut au moins 1 000 USD, et ce portefeuille ne vend pas dans l'heure.

La vente dans la fenêtre retire le portefeuille des règles 2, 3 et 4. C'est un contrôle partiel des teneurs de marché et de l'arbitrage en aller-retour. Il n'y a pas de liste de bots. Aucun horodatage d'information publique n'est joint. La comparaison est la règle de prix déjà figée : hausse d'au moins 0,05 sur une heure.

Le décompte retenu est un marché, une voix. Les points de grille, pris un point sur six, se recouvrent. Leur précision isolée gonfle les marchés qui restent en alerte pendant plusieurs heures. Elle est donnée ensuite, à part.

## Validation nouvelle, un marché une voix

Huit des 34 marchés ont au moins une fenêtre de 24 h qui monte de 0,15. Le taux de base est 8/34. Une règle qui alerte `A` marchés en a donc environ `A × 8/34` qui montent, si elle ne fait pas mieux que ce taux.

| Règle | Marchés en alerte | Hits | Précision (IC 95 %) | Rappel | Hits attendus au taux de base |
|---|---:|---:|---|---:|---:|
| Volume | 18 | 2 | 11 % (3,1–33) | 2/8 | 4,2 |
| Nouveau portefeuille sur le marché | 20 | 5 | 25 % (11–47) | 5/8 | 4,7 |
| Accumulation synchronisée | 1 | 0 | 0 % (0–79) | 0/8 | 0,2 |
| Concentration | 16 | 2 | 13 % (3,5–36) | 2/8 | 3,8 |
| Prix, hausse 1 h ≥ 0,05 | 5 | 0 | 0 % (0–43) | 0/8 | 1,2 |

À six heures, sept marchés bougent. Le nouveau portefeuille fait 4 hits sur 20 alertes, pour 4,1 attendus. Le volume en fait 1 sur 18, la concentration 1 sur 16, le prix 0 sur 5. À une heure, deux marchés bougent. Le nouveau portefeuille en touche 1 sur 20 alertes. Cet effectif ne porte pas de conclusion.

Sur la grille qui se recouvre, le nouveau portefeuille donne 225 alertes, 18 hits et 50 mouvements de 24 h : précision 8,0 % (5,1–12,3), rappel 36 % (24–50), 0,47 alerte par marché-jour, avance médiane 14,5 h. Le taux de mouvements sur ces points est 50/3524, soit 1,4 %. L'écart avec 8 % disparaît au décompte par marché : les mêmes marchés restent allumés sur de nombreux points. Le volume y fait 48 alertes et 2 hits. La synchronisation fait 1 alerte et 0 hit. La concentration fait 36 alertes et 2 hits. La règle de prix fait 0 hit.

La découverte n'a fourni aucun mouvement de 0,15 sur les bandes complètes. Le taux d'alerte y est nul pour le volume, la synchronisation et la concentration. Il ne sert donc pas de base aléatoire pour ces trois règles. Le taux du nouveau portefeuille en découverte est 5 points sur 165.

## Ce que cela ne démontre pas

Aucune relation financière nouvelle. La seule alerte synchronisée de la validation n'est pas suivie d'une hausse de 0,15. Aucune paire d'adresses n'est ajoutée aux liens déjà publiés. Maduro, les fenêtres Iran de février 2026 et Kane en octobre 2025 ne sont pas dans ces 67 bandes. Leurs séries de prix restent trop courtes pour cette cible, comme à la passe 4. Leurs montants publiés ne changent pas.

Les marchés liquides, ceux dont le curseur n'est pas épuisé à 3 000 lignes, ne sont pas dans ce score. Un résultat sur 34 courses électorales liées ne se transporte pas à un autre sujet.

## Collecte prospective

Le collecteur a tourné dans cette session. Il ne tourne plus. `permanent` vaut `false`. La machine virtuelle de la session ne conserve pas le processus, et ce dépôt ne prétend pas à une surveillance permanente.

Vingt marchés encore ouverts le 13 novembre 2026 sont dans [data/prospective_markets.json](data/prospective_markets.json). Dix-neuf sont neg-risk. Le WebSocket `wss://ws-subscriptions-clob.polymarket.com/ws/market` a fourni, sur l'essai conservé, 42 messages `book` et 190 messages `price_change`. Les portefeuilles viennent de `/v2/trades`, à part. Sur cet essai le décalage entre l'horloge de réception et l'horodatage du trade va de 103 secondes à 37,5 jours, médiane 5,9 jours : l'API renvoie un historique récent, le WebSocket porte le temps réel. Six reçus Polygon, lus sur `https://polygon-bor-rpc.publicnode.com`, contiennent chacun un `OrderFilled` v2 et un transfert ERC-20. Cinq reçus au plus sont lus par passage. Ce n'est pas un backfill.

Essai du 13 novembre 2026, répertoire `/tmp/phi-pass5b`, effacé avec la session :

| Passage | Issue | Lignes de marché | Trades | Reçus |
|---|---|---:|---:|---:|
| 1, 12 secondes | sortie normale | 91 | 4000 | 5 |
| 2, tué par SIGKILL à 12 secondes | reprise du répertoire | 155 | 4000 | 5 |
| 3, 12 secondes | sortie normale | 232 | 4001 | 6 |

Le troisième passage ajoute un trade apparu entre-temps. Il ne réécrit pas les 4 000 lignes. `status` après ces trois passages : `restarts` 3, `errors` 0, `gaps` 0, `permanent` false, 36,8 secondes entre le premier et le dernier battement, plus grand trou 10,0 secondes, ratio 1,0 sur cette fenêtre, horloge murale depuis le premier démarrage 41,1 secondes. Le trou du SIGKILL est resté sous 15 secondes parce que la reprise a été immédiate. Ce ratio n'est pas une disponibilité d'exploitation.

Le superviseur a aussi été lancé, tué, puis observé. Il a écrit `2026-11-13T17:12:27Z restart` et a relancé le processus. Ce processus a été arrêté ensuite.

Commandes, depuis la racine du dépôt, sur une machine Linux qui reste allumée :

```bash
python3 -m pip install -r monitoring/livecollect/requirements.txt
python3 -m monitoring.livecollect collect \
  --markets research_notes/forensic-engine-2026-11-13/data/prospective_markets.json \
  --out /var/phi
python3 -m monitoring.livecollect status --out /var/phi
scripts/livecollect_supervise.sh \
  research_notes/forensic-engine-2026-11-13/data/prospective_markets.json \
  /var/phi
```

`websockets` est épinglé à 15.0.1. Aucun secret n'est lu. Le détail d'exploitation est dans [le README du collecteur](../../monitoring/livecollect/README.md).

## Correctif de couverture

Le cycle horaire lisait 200 trades par marché, donc 4 000 lignes, et au plus cinq reçus. Sur le Mac, après 72 minutes, quatre de ces horodatages seulement étaient postérieurs au démarrage. Le correctif garde une marque par marché, horodatage plus hash, et pagine jusqu'à cette marque. Les trades sont relus toutes les 90 secondes, pendant que le WebSocket suit son propre cycle. Chaque hash nouveau entre dans une file de reçus, reprise après coupure. Un plafond de pages avant la marque est une ligne `trade_page_cap` dans `gaps.jsonl`, pas une absence de trades. Les lignes déjà écrites dans `~/phi-live` restent valides.

Essai du 13 novembre 2026 sur les 20 marchés, 960 secondes, sondage à 90 secondes. Le processus a été arrêté ensuite.

| Mesure | Valeur |
|---|---:|
| Sondages complets | 220 |
| Sondages incomplets | 0 |
| Trades dont l'horodatage suit le démarrage | 1 |
| Reçus Polygon | 1 |
| Erreurs | 0 |
| File de reçus en fin de course | 0 |
| Battements | 950,4 s |
| Ratio de battements | 1,0 |

Le trade nouveau a un décalage de réception de 220 secondes. Son reçu contient un `OrderFilled` v2 et un transfert ERC-20. Les 220 sondages tiennent en une page : la marque coupe l'historique ancien. Un silence WebSocket de 34,7 secondes est écrit dans `gaps.jsonl` ; ce n'est pas un plafond de pages. `permanent` reste `false`.

## Décodage du carnet et des reçus

Le correctif précédent écrivait `price_change` avec `asset_id`, `price`, `best_bid` et `best_ask` à null : ces champs sont dans `price_changes[]`, pas à la racine. Le topic V2 `0xd543adfd…` a été revérifié : il correspond à `OrderFilled(bytes32,address,address,uint8,uint256,uint256,uint256,uint256,bytes32,bytes32)`. Le contrat `0xe1111800…996b` et le contrat neg-risk `0xe2222d27…0f59` ont tous deux émis ce topic sur des reçus lus le 13 novembre 2026. Le V2 n'a pas deux identifiants d'actif dans le log. `maker_asset_id` et `taker_asset_id` sont dérivés de `side` et `tokenId`, et le champ `asset_ids_derived` le dit. Le V1, topic `0xd0a08e8c…`, porte ces deux identifiants directement.

Aucune ligne ancienne n'est réécrite. `hwm` reste en place. Une ligne `chain.jsonl` sans `fills` est relue une fois et une nouvelle ligne décodée est ajoutée. Le détail d'exploitation est dans [HEALTHCHECK.md](../../monitoring/livecollect/HEALTHCHECK.md).

### Démontré

Essai du 13 novembre 2026, 1 000 secondes, 20 marchés, processus arrêté ensuite. Battements de 22:45:44 à 23:02:14 UTC, soit 990,4 s, 100 battements, plus grand trou 10,0 s, ratio 1,0.

| Mesure | Valeur |
|---|---:|
| `price_change` avec `asset_id` et `price` | 12 122 / 12 122 |
| `last_trade_price`, dont `fee_rate_bps` | 3 |
| Sondages complets | 220 |
| Sondages incomplets | 0 |
| Intervalle médian entre sondages | 95,0 s |
| Trades écrits | 4, dont 3 après le démarrage |
| Attributions `confirmed` | 4 |
| Attributions `ambiguous` ou `not_found` | 0 |
| Erreurs | 0 |
| Messages non décodés | 0 |
| Occupation disque de la machine d'essai | 3,67 %, alerte non déclenchée |

Un actif a reçu deux snapshots `book`, séparés de 986,6 s, avec 771 `price_change` entre les deux. Rejouer ces changements sur le premier snapshot redonne les niveaux du second, prix et quantités. Les quatre reçus viennent du contrat neg-risk `0xe2222d27…0f59`. Chacun a deux logs `OrderFilled` et des transferts ERC-20. L'attribution `confirmed` compare le wallet, le token et le montant de parts. Deux logs au même montant comptent pour un seul fill.

### Hypothèses

Le serveur n'a envoyé un snapshot `book` que pour 4 des 20 tokens abonnés. La cause n'est pas établie. Les `maker_asset_id` V2 restent une lecture de `side` et `tokenId`, pas des mots du log.

### Limites

Un essai antérieur, avant de sortir le verrou du fil WebSocket, s'est bloqué : les battements se sont arrêtés au bout de 630 s et un silence de carnet de 375 s a été écrit. Ce n'est pas l'essai de 990 s. Le ratio de `price_change` sur le Mac compte encore les anciennes lignes nulles, y compris `price_change_value_ratio_since_start`, parce que `started` reste le démarrage de 18:04. Le contrôle après déploiement est dans [DEPLOIEMENT_MAC_249e70d.md](DEPLOIEMENT_MAC_249e70d.md). `permanent` reste `false`.
