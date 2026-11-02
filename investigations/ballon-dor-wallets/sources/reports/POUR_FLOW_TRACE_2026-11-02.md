# Points transmis à l'enquête flow-trace, 2 novembre 2026

Échangés directement avec la session `polysentinel-flow-trace-c1`. Aucun fichier n'a été écrit dans son dossier. **Ses rapports sont finaux depuis le 2 novembre et sont intégrés au rapport : les points 1, 3, 5, 6 et 8 ci-dessous sont traités de son côté.** Reste ouvert : entrées BSC et Base. L'écart de 47 ou 50 adresses dans sa recherche de wallets est corrigé de son côté : 50.

## Répartition convenue

| Sujet | Qui |
|---|---|
| Historique BSC de `0xc852b0938f5ad79b640d105ed11c14499454af26` | flow-trace, `state/bsc_0xc852…json` en cours |
| Saut `0x7e67dF45…` puis `0x3f3Ee0a9…`, marche des clés élargie | flow-trace |
| Suite des 75 946,74 USDT de la clé d'OuldLm3alem | flow-trace |
| Ce qui sort de Gxjc | flow-trace |
| Taux de base corrigé, 83 comparateurs | flow-trace, `state/compare_rates.json`, pas encore écrit |
| Recherche d'autres wallets autour des onze | flow-trace |
| `data-api /trades` Kane et `/v2/activity` des comptes du lot | enquête, fait |
| Rapport corrigé et dossiers `.md` | enquête, fait |

## Fait transmis sur BSC

La clé de brace227 a un nonce de **109 sur BSC**. Les 10 autres clés propriétaires ont un nonce de 0. Réponse de flow-trace, RAPPORTÉ, non revérifié ici : nonce 104 de 2022 à 2024, 109 au 20/05/2025 et aujourd'hui, donc aucune sortie signée sur BSC après cette date. Limite : sorties seulement, pas les entrées.

## À vérifier par flow-trace

1. **Entrées et sorties BSC de 0xc852 :** dernière date exacte, destinataires, lien éventuel avec les 10 autres clés ou `7XUJs…`.
2. **Soldes BSC des clés à nonce 0 :** nonce 0 et solde 0 excluent une réception native. Non lu ici.
3. **Nature de `0x3f3Ee0a9cAC2d01DB44001eca3E8382fbe40207B` :** environ 321 000 transactions, étiquette Blockscout « ChangeNOW Dep », source unique. Recouper, et chercher ce que cet échange a rendu. Même chose pour `0xdd3d72C5…Ceee`, « ChangeNOW: Hot Wallet 3 ». Ces étiquettes sont dans les objets `from` et `to` des transactions Blockscout, pas sur la page `/addresses/`.
4. **Avant et après `7XUJs…` :** `9byY2BBoUr…` (304,70 USDT, juin), `AmvGsM9JKj…` (300 USDT), `AmHcVnxAt6…` (0,17 SOL, septembre). Autres étiquettes possibles ?
5. **Autres wallets :** `0x48ec106C…` a conduit au wallet non nommé `0xa8e64a3c…`, relu ici. Flow-trace cherche si d'autres adresses personnelles autour des onze possèdent un wallet : à reprendre dans le rapport dès que c'est fini.
6. **Taux de base corrigé :** à reprendre dans le rapport dès que `compare_rates.json` et son rapport sont finaux. Le rapport indique « en attente ».
7. **KuCoin :** deuxième source pour l'étiquette de `BmFdpraQhk…`.
8. **Étiquettes Blockscout sur les 9 autres clés et leurs destinations :** non relues ici, par le champ `metadata.tags` des objets de transaction. Une troisième étiquette y resterait invisible.

## Fichiers réutilisables, sans recollecte

Dans `evidence/contre_verification_20261102/` : `payeur_solana_7xujs.json`, `relay_par_utilisateur.json`, `identifiant_relay_7xujs.json`, `voisinage_transfert.json`, `circuit_7xujs_brace_kraben.json`, `calendrier_kane.json`, `transactions_communes.json`, `wallet_0xa8e6.json`, `etiquettes_blockscout.json`, `fenetre_lot_kane.jsonl`, `fenetre_vendeurs_kane.jsonl`, `trades_kane.json`.

## Fichiers de l'enquête que flow-trace lit

Non modifiés : `cases/*.json`, `graphs/*`, `tools/services.json`, `state/http_cache`, `controls/*`, `collective/*`. Modifiés après archivage : `reports/*.md`, `cases/*.md`.
