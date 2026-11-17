# Déploiement Mac du commit 249e70d

13 novembre 2026. Mesures prises par le propriétaire sur sa machine, après le commit `249e70da772bdf04b8a5030543cac17b62631b9e`. Aucune adresse de wallet n'est recopiée ici. Le code n'a pas été modifié pour écrire cette note.

## Démontré

Avant la bascule, le nouveau code a tourné 240 secondes dans un répertoire séparé. Les 3 006 `price_change` de cet essai ont un contenu. Les 60 sondages sont complets. Il n'y a ni erreur ni message non décodé.

La bascule a eu lieu à 23:10:08 WET. Le LaunchAgent a été arrêté. `~/phi-live` a été sauvegardé : le diff de cette copie est identique. L'ancien code est conservé dans `monitoring.old-f7ff734` et `scripts.old-f7ff734`. La collecte a été coupée environ 10 secondes, puis relancée. Le retour arrière consiste à recopier ces deux répertoires `.old-f7ff734`.

Contrôle de 23:10 à 23:26 WET, soit 16 minutes :

| Mesure | Valeur |
|---|---:|
| `price_change` avec `asset_id`, `price`, `side` et `size` | 14 062 / 14 062 |
| Actifs couverts par ces `price_change` | 40 |
| Marchés couverts | 20 |
| Snapshots `book` | 4, sur 4 actifs |
| Niveaux de ces carnets | 1 à 24 bids, 80 à 115 asks |
| `last_trade_price` | 0 |
| Nouveaux trades | 3 |
| `OrderFilled` V2 de ces trades, attribution `confirmed` | 3 |
| Anciennes lignes `chain` relues, attribution `ambiguous` (`trade_fields_missing`) | 50 |
| Sondages complets | 220 |
| Sondages incomplets | 0 |
| Trous | 0 |
| Erreurs | 0 |
| Intervalle médian entre sondages | 97,6 s |
| Intervalle maximal entre sondages | 98,2 s |
| Plus grand écart entre battements | 10,2 s |
| `uptime_ratio` depuis 18:04 | 1,0 |
| Disque | 80 % occupé, 40 Go libres, aucune alerte |

Les 50 lignes `ambiguous` viennent des trades écrits avant ce commit : il leur manque les champs qu'exige l'attribution. Ce résultat est celui attendu de la relecture. Ce n'est pas une régression du décodeur.

## Hypothèses

Le fait que le snapshot `book` n'arrive que pour environ 4 des 20 marchés a la même forme que l'essai en machine virtuelle. Rien dans ce contrôle n'en donne la cause.

## Limites

`price_change_value_ratio` et `price_change_value_ratio_since_start` valent 0,1095. `started` est le démarrage initial de 18:04. Les deux ratios comptent donc les anciennes lignes nulles avec les lignes nouvelles. Le meilleur bid et le meilleur ask restent présents sur les `price_change` des 20 marchés. La profondeur complète du carnet n'est reconstructible que pour les 4 actifs qui ont reçu un snapshot.

Proposition, non appliquée sur le Mac et non codée dans ce commit : garder dans `state.json` un horodatage `deployed_at`, écrit une seule fois au moment de la bascule, et faire compter à `status` les `price_change` dont `received` est postérieur à cette valeur. Pour cette bascule, cet instant est le 13 novembre 2026 à 23:10:08 WET. Ce compteur ne remplacerait pas `started`, qui doit rester le début réel de la collecte pour `uptime_ratio`.
