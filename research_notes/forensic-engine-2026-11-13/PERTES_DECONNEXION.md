# Pertes pendant une coupure du flux WebSocket

14 novembre 2026, sur la machine d'essai. Ce n'est pas une mesure du Mac. Le Mac fait tourner `c218469` et n'a pas été relancé. Le journal des divergences de carnet reste dans [DIVERGENCES_PROFONDEUR.md](DIVERGENCES_PROFONDEUR.md).

## Démontré

Battements de 11:32:39 à 11:50:58 UTC, 79 lignes, étendue 1 099,6 s. Un seul intervalle dépasse 20 s : 11:44:19 à 11:49:48, soit 329,5 s.

`market.jsonl` contient 38 `price_change` entre 11:44:19 et 11:44:25, puis plus aucune ligne jusqu'à 11:49:48. Après la reprise, 12 lignes `book` portent `source` `clob_rest`, toutes à 11:50:02. Aucun `last_trade_price` n'est écrit après 11:44:25.

`gaps.jsonl` a 5 lignes, espacées de 15 s : 11:50:00 (334,5 s), 11:50:15 (349,5 s), 11:50:30 (364,5 s), 11:50:45 (379,5 s), 11:51:00 (394,5 s). Ce compteur est le temps depuis le dernier message WebSocket, pas le trou entre battements. `errors.jsonl` est absent.

`coverage.jsonl` a 180 sondages, tous `complete`. À partir de 11:50:42, 20 sondages, tous complets, 0 trade nouveau. `trades.jsonl` est absent sur toute la course. Les 40 carnets finissent `synchronized`.

## Ce que le code perd, détecte et rattrape

Le WebSocket écrit `price_change`, `book` et `last_trade_price`. Rien ne rejoue les messages absents de `market.jsonl`. Les deltas manqués, les `last_trade_price` manqués et le chemin intermédiaire du carnet ne sont pas reconstruits.

La détection a deux signaux distincts. Un silence de réception de 15 s ajoute une ligne dans `gaps.jsonl`. Un battement manquant se voit dans `heartbeats.jsonl` : au-delà de 15 s, l'intervalle n'entre plus dans `observed_online_s`. Au contrôle suivant, `POST /books` compare le carnet local au carnet officiel. Si le meilleur prix ou la profondeur diffère, `book_status.jsonl` reçoit la divergence, avec l'horodatage du dernier delta et celui du snapshot.

Le rattrapage du carnet est le snapshot `POST /books`, pas une reprise des deltas. Les 12 lignes `clob_rest` de 11:50:02 sont ce remplacement. Les trades passent par un autre fil : `GET /v2/trades` recule jusqu'à la marque haute (`hwm`). Un sondage qui s'arrête au plafond de 4 pages ne fait pas avancer cette marque et garde un curseur. Cette course n'a retourné aucun trade, donc le rattrapage d'un trade manqué n'y a pas été observé. Les 20 sondages d'après le trou étaient complets.

## Irrécupérable

Les `price_change` et `last_trade_price` non écrits après 11:44:25 ne peuvent pas être relus : le collecteur n'a pas de tampon de reprise. Le nombre de messages que le serveur a émis pendant ce silence n'est pas dans le journal. Un `last_trade_price` sans trade REST correspondant ne revient pas par le sondage. Un trade que l'API ne renvoie plus avant le sondage suivant ne revient pas non plus. La cause du trou de 329,5 s n'est pas identifiée : le journal montre l'absence de battement et de message, pas l'origine de la pause.
