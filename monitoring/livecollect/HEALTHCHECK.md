# Contrôle du collecteur

`python3 -m monitoring.livecollect status --out <répertoire>` lit les fichiers déjà écrits. Il n'efface rien et n'envoie rien.

## Disque

Le seuil est 5 000 000 000 octets libres, ou 97 % d'occupation, le premier des deux atteint. `disk_alert` vaut `true` dans ce cas. Le collecteur, pas la commande `status`, ajoute alors une seule ligne `error=disk_space` dans `errors.jsonl`. Une nouvelle ligne n'est écrite qu'au passage sous le seuil, pas à chaque battement. À 94 % d'occupation et 13 Go libres, le seuil n'est pas franchi.

## Ce que status ajoute

- `undecoded_by_type` : messages WebSocket non décodés, par type. Une ligne vide n'est pas écrite dans `market.jsonl`.
- `price_change_value_ratio` : part des lignes `price_change` qui ont un `asset_id` et un `price`. Le fichier entier est compté, y compris les anciennes lignes nulles.
- `price_change_value_ratio_since_start` : la même part parmi les lignes reçues depuis `started`.
- `attribution_confirmed`, `attribution_ambiguous`, `attribution_not_found` : reçus décodés. `attribution_legacy` compte les anciennes lignes qui n'ont que `tx`, `t` et `families`.

## Fichiers

Aucune ligne existante n'est réécrite. `state.json` garde `hwm`, `receipt_queue` et `seen_trades`. Il peut gagner `disk_alert_open`, `disk_free_bytes` et `disk_used_ratio`.

Les nouveaux `price_change` ont une ligne par élément de `price_changes[]`. Les `book` gardent `bids` et `asks`. Les `last_trade_price` gardent prix, taille, côté, actif, marché, horodatage, et `fee_rate_bps` s'il est présent. Les anciennes lignes nulles restent lisibles.

Un reçu déjà décodé n'est pas redemandé. Une ligne ancienne sans champ `fills` est remise une fois en file : le reçu est relu et une nouvelle ligne, avec les fills et l'attribution, est ajoutée. L'ancienne ligne reste.

L'attribution `confirmed` exige le wallet, le token et le montant de parts sur le ou les `OrderFilled` de la transaction. Deux logs au même montant sont les deux faces du même fill. Sinon le statut est `ambiguous` ou `not_found`. Un identifiant d'actif dérivé du côté V2 est marqué `asset_ids_derived`.

`price_change_value_ratio_since_deploy` ne compte que les lignes dont le champ `collector` vaut la version en cours. `deployed_at` est écrit une fois dans `state.json` quand cette version prend le relais. Les lignes anciennes ne sont pas réécrites. `elements_received`, `elements_stored` et `elements_rejected` comptent chaque élément d'un message, y compris ceux d'un tableau. `books` donne un statut par actif. `synchronized` exige un snapshot de référence. Un snapshot officiel plus ancien que le dernier delta n'écrase pas le carnet. Un hash différent avec des niveaux identiques non plus.
