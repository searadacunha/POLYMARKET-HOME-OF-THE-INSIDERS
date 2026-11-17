# Validation Mac de c218469

14 novembre 2026. Mesures prises par Benjamin sur son Mac, entre 09:25 et 09:41 WET, sur le commit `c218469618ac599247aedaed5d8aaf9ac69ff82c`. Aucune adresse n'est recopiée.

## Démontré

Avant la bascule, un essai hors production de 5 minutes, dans un répertoire séparé, a donné 40 carnets synchronisés sur 40 : 38 par WebSocket et 2 par `clob_rest`. Il y a eu 2 divergences. 1 251 éléments ont été reçus et 1 251 stockés, aucun rejeté. 2 422 `price_change` sur 2 422 étaient valorisés. 0 erreur. 80 sondages complets. Le plus grand écart entre battements était de 10 secondes.

La sauvegarde du répertoire de production est `~/phi-live-backup-20261114-pre-c218469`. L'ancien code est conservé dans `monitoring.old-249e70d` et `scripts.old-249e70d`.

Production, 16 minutes :

| Mesure | Valeur |
|---|---:|
| Actifs souscrits | 40, dont 20 tokens No |
| Éléments reçus / stockés / rejetés | 4 247 / 4 247 / 0 |
| Messages non décodés | aucun |
| Carnets synchronisés | 40 / 40 |
| Origine de ces carnets | 35 WebSocket, 5 `clob_rest` |
| Divergences | 10, sur 7 392 deltas, toutes resynchronisées |
| Lignes `book` | 90, couvrant les 40 actifs |
| `price_change` depuis le déploiement | 8 474 / 8 474, ratio 1,0 |
| Ratio global, anciennes lignes nulles comprises | 0,7875 |
| Sondages | 200, dont 0 incomplet |
| Erreurs depuis le déploiement | 0 |
| Attributions `confirmed` | 84, contre 61 avant |
| Attributions ambiguës | 50, les anciennes |
| Attributions `not_found` | 0 |
| Plus grand écart de battement | 10,17 s |
| `uptime_ratio` | 1,0 |
| Espace disque libre | 34 Go |

Un marché a un seul côté vide, à 0,999 / 0,001. Ce carnet est conforme au carnet officiel.

Les 5 erreurs et le sondage incomplet visibles dans les totaux datent d'avant ce déploiement : un `HTTPError` à 09:12 WET, sous l'ancien code.

## Hypothèses

Les 10 divergences de production ont le même profil que celles vues ailleurs : le meilleur bid et le meilleur ask coïncident, la profondeur non. Ce fichier ne contient pas le journal détaillé de ces 10 cas. Il ne tranche donc pas entre un décalage de séquence, un message manquant et une course entre le snapshot REST et le WebSocket.

## Limites

La fenêtre dure 16 minutes. Le Mac doit rester allumé, capot ouvert, pour que la collecte continue. Le ratio global 0,7875 compte les lignes nulles conservées de l'ancienne version. Le ratio depuis le déploiement ne les compte pas.
