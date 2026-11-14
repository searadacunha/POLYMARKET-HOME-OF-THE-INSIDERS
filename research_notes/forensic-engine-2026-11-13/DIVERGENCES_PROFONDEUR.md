# Divergences de profondeur

14 novembre 2026. Journal produit sur cette machine, pas sur le Mac. Le Mac fait tourner `c218469618ac599247aedaed5d8aaf9ac69ff82c`, qui n'a ni ce journal ni les deux gardes ajoutées ensuite.

## Démontré

Fenêtre de battements de 11:32:39 à 11:50:58 UTC, étendue 1 099,6 s. Un trou de 329,5 s n'est pas compté dans le temps en ligne : 770,2 s, ratio 0,7. 40 actifs souscrits, dont 20 tokens No. 3 130 éléments reçus, 3 130 stockés, 0 rejeté. 6 218 `price_change` sur 6 218 depuis ce déploiement. 22 divergences journalisées. Les 40 carnets étaient `synchronized` à la lecture finale, après remplacement par le snapshot officiel.

Les 22 lignes se répartissent ainsi.

Huit comparaisons n'avaient aucun delta appliqué depuis le snapshot local (`deltas_since_snapshot` 0, pas d'horodatage de delta). Deux d'entre elles n'ont aucune différence de niveau : seul le hash diffère. Six ont une taille différente sur un ou deux prix, le meilleur bid et le meilleur ask restant identiques. Ce sont deux snapshots, pas une application de delta dans le désordre.

Quatorze comparaisons suivent des deltas. Pour une paire de tokens complémentaires, le snapshot officiel est daté 531 ms avant le dernier delta, et un seul niveau de profondeur diffère. Le carnet officiel est plus ancien que ce que le collecteur a déjà appliqué. Pour les douze autres, le snapshot officiel est plus récent que le dernier delta d'environ 5 à 6 minutes, et plusieurs niveaux diffèrent. Ce retard coïncide avec le trou de battement de 329,5 s : pendant ce trou, les deltas n'étaient pas appliqués.

Dans tous les cas journalisés où le meilleur prix est présent, le meilleur bid et le meilleur ask coïncident.

## Hypothèses

Les six écarts de taille sans delta intermédiaire viennent d'une course : le snapshot WebSocket et le snapshot REST ne sont pas pris au même instant, et le message de changement n'est pas encore dans le journal, ou vient de partir. Rien ne montre un niveau tronqué ni une taille 0 opposée à une absence.

Les douze écarts après le trou sont des messages non lus pendant l'arrêt du fil, pas un format de carnet. La paire à 531 ms est une course dans l'autre sens : le REST est en retard sur le WebSocket.

## Indéterminé

Le journal ne prouve pas qu'un delta ait été appliqué dans le désordre à l'intérieur d'un même actif. Il ne prouve pas non plus que le serveur ait omis un message pendant que le collecteur lisait. Les 10 divergences du Mac, sur 7 392 deltas, n'ont pas ce journal : elles restent dans le même profil de meilleur prix, sans classement plus fin.

## Gardes ajoutées après cette mesure

Deux gardes ne sont pas dans `c218469`, et n'étaient pas actives pendant les 22 lignes ci-dessus. Si les niveaux sont identiques, un hash différent ne déclenche plus de resynchronisation. Si l'horodatage du snapshot officiel est antérieur au dernier delta déjà appliqué, le snapshot n'écrase pas le carnet local. Le Mac n'a pas ces gardes. Un redéploiement n'est pas nécessaire pour le fonctionnement déjà observé.
