# Amendement du rapport après audit, 2 novembre 2026

Corrige `reports/rapport_final.md`, version 1 du 02/11 08:18 UTC, sha256 `de683ab687b293fca7d2ed9d09cda0aefe4341e0ee956510238022f76021c8c0`, conservée dans `archive/20261102_avant_amendement_audit/`. Demandé par Benjamin le 2 novembre. La version 2 se rejoue : `python3 tools/appliquer_amendement_20261102.py`. Vérifications : `reports/CONTRE_VERIFICATION.md`. Empreintes : `reports/JOURNAL_MODIFICATIONS_2026-11-02.md`.

## Ce que cet amendement ne touche pas

- **Rien de gelé.** `collective/` reste tel quel : plan, code, sorties, registre, `results.md`. `PROTOCOL.lock` vérifié 27 fichiers sur 27.
- **Aucune preuve brute.** `graphs/`, `controls/`, `state/`, `cases/*.json` et `evidence/` existant sont intacts. Une relation classée SERVICE_INTERACTION reste ainsi classée dans `graphs/relations.jsonl`, et le rapport dit pourquoi.
- **Ce n'est pas un amendement de protocole.** Il corrige la lecture des résultats, pas une méthode gelée. Ses tests sont exploratoires et hors registre.
- **Aucune intervention** sur PolySentinel en production, PolySentinel-harness, PolySentinel-flow-trace, les rejeux S_C, les labels sous embargo.

## Le verdict, avant et après

| Niveau | Version 1 | Version 2 |
|---|---|---|
| Comportement atypique | Observé, biais de sélection | **Inchangé** |
| Connexion financière | 0 transfert direct, aucun wallet supplémentaire | **Établie : 1 paire sur 55 (5,53 $), et 5 170 USDC de la clé de brace227 vers un wallet non nommé** |
| Contrôle commun de wallets | Affaibli | **Non déterminé**, pour toutes les paires |
| Coordination des paris | Non démontrée | **Non démontrée.** Indice le plus fort : brace227 et le wallet non nommé |
| Insider trading | Non démontré | **Non démontré.** Aucun lien financier n'y répond |

## Les corrections

### A1. Transfert direct entre deux dossiers

- **Ancienne affirmation :** « 0 transfert direct de fonds », « Aucun transfert de fonds direct entre ces dossiers, sur les chaînes et jetons lus ».
- **Preuves examinées :** `0xd07bea20a22d9381e0ab364e7a7421776318c6f4aa7258799638472ad7092b98` relue sur `ethereum-rpc.publicnode.com` et `eth.drpc.org` : bloc 26119420, 2026-10-04 13:54:35 UTC, de `0xc852b0938f5ad79b640d105ed11c14499454af26` à `0x101b5f4dc0886c32e2b75972101aeaf9f338fb65`, 0,002048943671205553 ETH, 21 000 gas, sans données, succès. Historique Ethereum complet des deux clés.
- **Nouvelle conclusion :** 1 transfert natif direct, le seul entre ces deux clés sur Ethereum. Ni propriété commune, ni coordination, ni information privilégiée n'en découlent.
- **Raison :** le scan d'origine ne lisait ni l'ETH natif ni l'historique ancien des clés. Le « 0 » dépassait ce qu'il mesurait.

### A2. Wallet non nommé financé par la clé de brace227 (ajout)

- **Ancienne affirmation :** « Aucun wallet supplémentaire n'est relié aux onze par une preuve de chaîne. »
- **Preuves examinées :** signalé par l'enquête flow-trace, relu ici : `owner()` de `0xa8e64a3c08d1e2a4e9f25a2dd33b8ac3458f74a5` sur Polygon, 20 lignes d'activité complètes, transferts `0x7e3aecb9…4349` et `0xb07c3c53…0add`, jetons et transactions de `0x48ec106cf690edd58fcd6df1e8b6abfc16dab12d`, enregistrement Relay des deux dépôts.
- **Nouvelle conclusion :** la clé de brace227 envoie 5 170 USDC à la clé propriétaire de ce wallet, contre 5 173,25 $ à son propre wallet, les 9 et 10 oct. La tranche du 16 oct., 4 749,03 USDC, va tout entière à brace227. Ce wallet ne parie que sur Kane, 5 164,99 $, dès 20:37:10 le 9 oct. brace227 n'y met que 954,04 $ ces deux jours. **Connexion financière démontrée.** Propriétaire commun, entente et information privilégiée : non démontrés. Douzième compte allégué : aucune preuve.
- **Raison :** le dossier suivait les dépôts et les sorties de Polymarket, pas ce que la clé envoie ailleurs. Ce wallet ne détient pas Mbappé et n'a qu'un token : ni la capture ni E4 ne pouvaient le voir. Il figure pourtant dans une rafale E2 sur Kane, le 11 oct., avec 0x86544e4dfde et walletwallet8424 : une proximité d'achat, pas un lien. D'autres wallets de ce type peuvent exister.

### A3. Circuit autour du transfert (ajout)

- **Ancienne affirmation :** rien. L'audit signalait un paiement d'un solveur Relay.
- **Preuves examinées :** signature Solana `3XaPp5kRsL5MdAHFsTuKKvRJNyiDfkrhLQufjEsASUbKeYz2yhw5A2C2YECuLWHPZiKGXRP6bJznWsKh4s2VNfEL`, calldata de `0xb17e1c4627ad8914f98f48a4fa7f5916953d3286e60cf3d80c6508257f46ce3c`, enregistrement Relay, 8 signatures du payeur, soldes en wei recoupés sur un nœud d'archive.
- **Nouvelle conclusion :** continuité **démontrée** de `7XUJsJBNp7WykVXG4y76ntsSn3H7tFdLVcmehAgJfrZc` à la clé de brace227 (même identifiant `0x3048…7867` sur les deux chaînes) et jusqu'à la clé de kraben006 pour au moins 81,4 % du montant. **Simple succession** ensuite : au moins 22,7 % de ce qui a été reçu repart vers `0x7e67…`, 23,9 % gas compris, le reste dépend d'une convention de traçage.
- **Raison :** Benjamin demandait de séparer continuité et succession. La comptabilité du solde fixe la frontière.

### A4. Portée du vidage (ajout)

- **Ancienne affirmation :** l'audit : « un montant de cet ordre ressemble à des frais de gas donnés ».
- **Preuves examinées :** soldes de la clé de brace227 aux blocs 26119411 et 26119420, soldes USDT, activité ultérieure, solde de la clé de kraben006.
- **Nouvelle conclusion :** 98,85 % du solde ETH envoyés. L'ETH seul, 0,055 % et 0,097 % des dépôts des deux comptes : en montant, ce n'est pas un financement significatif. Ni abandon ni drainage : 22 024,57 USDC restent sur la clé. La lecture « don de gas » est peu soutenue.
- **Raison :** ce fait pèse sur la relation entre ces deux clés, pas sur le capital engagé. Le vrai financement est en A2.

### A5. ChangeNOW (ajout)

- **Ancienne affirmation :** « aucune interaction avec une adresse étiquetée ChangeNOW ou FixedFloat ». H13 non soutenue.
- **Preuves examinées :** étiquettes Blockscout dans les fichiers sauvés, `etiquettes_blockscout.json`.
- **Nouvelle conclusion :** `0xdd3d72C5…Ceee`, « ChangeNOW: Hot Wallet 3 », envoie 834,85 USDC à la clé de kraben006 le 23 fév. 2026. `0x3f3Ee0a9…207B`, « ChangeNOW Dep », reçoit 0,00241406 ETH le 4 oct. Source unique, non recoupée, relecture limitée aux clés de brace227 et kraben006 sur Ethereum. Rien ne dit qu'un échange a eu lieu. **Aucun échange XMR observé.** H13 **non tranchée**.
- **Raison :** `tools/services.json` n'avait pas ces adresses, et ma lecture de la page `/addresses/` rendait ces champs vides. Le premier brouillon écrivait « aucune étiquette » : l'auditeur de conclusions l'a relevé.

### A6. Hypothèses de propriété commune

- **Ancienne affirmation :** H3 et H4 « affaiblies » : « 11 clés distinctes, routes différentes, 0 transfert direct, 0 lien discriminant ».
- **Preuves examinées :** C6 de l'audit, A1, A2. Aucun témoin positif dans la méthode.
- **Nouvelle conclusion :** **non tranchées** entre les onze. H17 ajoutée, confirmée pour un wallet non nommé.
- **Raison :** un opérateur prudent laisserait la même empreinte, et la méthode a manqué deux liens réels. L'absence de preuve n'est pas une preuve d'absence.

### A7. Taux de base

- **Ancienne affirmation :** 50 comparateurs, KuCoin 3/11 contre 1/50, p ≈ 0,016, « KuCoin ressort donc plus souvent chez les nommés », indice faible.
- **Preuves examinées :** `controls/funding_baseline_detail.jsonl`, `collective/derived/B_E6.json`, 61 historiques rejoués depuis le cache.
- **Nouvelle conclusion :** 30 comparateurs utilisables sur 83 prévus, 53 inutilisables : 33 jamais lus, 16 sans origine, 4 coupés. KuCoin p = 0,052, Solana 0,110, `0xc8a6…` 0,071. **Indice KuCoin retiré.** Taux réel inconnu, bornes de 0,005 à 0,997. Résultat corrigé de flow-trace en attente, rien de provisoire n'est repris.
- **Raison :** 16 lignes sans origine, dont 14 sans lecture de route, comptaient comme des négatifs, 17 historiques s'arrêtent avant le premier achat, et le libellé KuCoin n'est lu que sur origine Solana.

### A8. Financement avant achat

- **Ancienne affirmation :** rangs « x comparateurs sur 42 », et dans l'étude 9/11 contre 10/43, p = 0,0006.
- **Preuves examinées :** `B_E6.json` : 43 lignes pour 38 wallets, 21 lignes coupées.
- **Nouvelle conclusion :** 9/11 contre 9/20 comparateurs distincts à écart mesurable, p = 0,052, ou 9/21, p = 0,039, en gardant un compte sans dépôt lu. Vrai taux inconnu. Exploratoire. Rangs recalculés dans chaque dossier.
- **Raison :** un même wallet comptait plusieurs fois et des historiques coupés fixaient l'écart. L'audit gardait 10/22, qui contient encore un doublon.

### A9. Combinaisons E4 et H9

- **Ancienne affirmation :** « 0 impliquant un compte nommé », « 12 et 37 paires », H9 affaiblie, « 0 paire » dans les dossiers VidenteRibeira et WenZhuanBuPei.
- **Preuves examinées :** `ana_overlap_core_v2.py`, filtre de 2 tokens à 100 $ absent du plan. Univers relus par `tools/cv_12_e4.py`. E4 v2 relancé : 6 sorties sur 6 identiques.
- **Nouvelle conclusion :** reproductible. Mais 19 paires sur 55 non testées au 23 oct., par ce filtre. 45 au 13 oct., dont 40 faute d'achat et 5 par ce filtre. H9 **non tranchée**. Chiffres par graine : 11, 11, 12 et 31, 25, 34.
- **Raison :** un test qui ne peut pas voir une paire ne dit rien d'elle.

### A10. Retraits brace227 et kraben006

- **Ancienne affirmation :** H14 « non démontrée », sans comparateur. L'audit les listait parmi les éléments de la paire.
- **Preuves examinées :** 22 vendeurs de Kane à 0,99 et plus, 5 000 $ ou plus, fenêtres complètes.
- **Nouvelle conclusion :** **aucun signal mesurable.** 10 vendeurs comparables sur 20 retirent aussi en moins de 5 min, p = 0,29. Ventes à 78 s d'écart, pour un écart médian de 45 s. Retraits à 166 s : 8 paires sur 105 font aussi peu.
- **Raison :** vendre à 0,999 puis retirer est courant dans cette fenêtre.

### A11. Retraits 0x86544e4dfde et walletwallet8424

- **Ancienne affirmation :** audit : proximité expliquée par la redemption « qu'ils venaient de faire tous les deux », « faux positif évité ».
- **Preuves examinées :** résolution `0xf3684759baebfdb2189871b80692f96ea8f7b7e4ecaafe26bd998c908fda2430`, 2 711 redemptions en 136 transactions, 178 comptes comparables lus, 175 retenus, 13 strates.
- **Nouvelle conclusion :** deux faits. La redemption simultanée est un **faux positif comme lien**, déclencheur du lot non lu. La vitesse de retrait reste **un indice faible** : 2 sur 2 sous 5 min contre 1 sur 175, 0 sur 27 dans la strate la plus proche, p brut de 0,0002 à 0,0069, de 0,010 à 0,38 après correction. L'écart de 93 s n'ajoute rien.
- **Raison :** le calendrier explique le paiement, pas le geste qui suit. Le trait touche la plupart des nommés et le test est post hoc : il ne prouve aucun lien.

### A12. Achats rapprochés de brace227 et kraben006

- **Ancienne affirmation :** audit : 9 décisions à moins de 5 min, p ≈ 0,0012.
- **Preuves examinées :** activité complète, marché Kane du 24 oct. de 14:00 à 17:00 UTC, décalage dans ce créneau, 14 autres acheteurs.
- **Nouvelle conclusion :** 0 avant le 13 oct., 1 le 17 oct., 8 le 24 oct., après l'article. Dans le créneau, p = 0,40. Plus gros acheteurs taker du créneau, 45 % des achats, et aucun autre n'atteint leurs scores. **À instruire, pas une preuve.**
- **Raison :** le p de l'audit mesure surtout deux comptes actifs le même après-midi.

### A13. Autres faux signaux

- **Ancienne affirmation :** liste de faux positifs de la version 1. L'audit ajoutait les 59 POL et Gxjc. Personne n'avait signalé les transactions communes.
- **Preuves examinées :** reçu `0x4b89cf4f04f9ce694b9dc26bc870fd873a5e00aa71ce1d3e99fd556a75005ac8`, sorties Solana des deux adresses Gxjc, 14 transactions décodées.
- **Nouvelle conclusion :** les 59,09 POL sont un échange payé par `0x408c…` lui-même. Gxjc cosigne et paie les frais : le balayage vient de son automatisme, le choix commun du service reste sans explication ni valeur de lien démontrée. Les 14 transactions : 8 lots, 5 co-makers, 1 seule exécution directe, déjà connue.
- **Raison :** une adresse ou une transaction partagée ne relie personne sans preuve de flux entre les deux.

### A14. Sorties d'OuldLm3alem et de 0xdd97e6

- **Ancienne affirmation :** « le paiement natif ne laisse pas de log », destination non lue, « solde non vérifié ».
- **Preuves examinées :** reçus `0x909d9602…a6f1` et `0x8c358292…c2d3`, nonces, soldes.
- **Nouvelle conclusion :** paiement lu au log 463. 839 000 POL échangés contre 75 946,74 USDT 108 s plus tard, solde USDT à 0 le 2 nov. 26,9716 ETH en place, nonce 0.
- **Raison :** sur Polygon, un `LogTransfer` trace le natif. La lecture était possible.

### A15. Montants

- **Ancienne affirmation :** 129 367,79 $ présenté sans le brut en regard. L'audit : 188 957,13 $, 62 438,51 $.
- **Preuves examinées :** 25 burns, 46 mints, comptes par dossier.
- **Nouvelle conclusion :** 493 094,76 $ est brut, 11 comptes, capital rendu compris. 129 367,79 $ est un net sur 7 comptes. Net des 11 : 188 957,12 $, dont 62 438,52 $ pour 3 comptes à résidu faible et -2 849,19 $ pour Zoomman17. Le wallet non nommé, 2 896,90 $ de retraits moins dépôts, est hors de ces totaux.
- **Raison :** ces chiffres n'ont pas le même périmètre et aucun ne mesure le gain d'une personne.

### A16. Date D2, sceau, protocole

- **Ancienne affirmation :** « partie A scellée avant la lecture des noms et des résultats », charge « au plus 12 », « Aucun p de cette étude n'approche le seuil », « La fraîcheur ne se concentre pas plus qu'au hasard ».
- **Preuves examinées :** activité de Thin, `derived/A_seal.json`, plan gelé, sorties de l'audit.
- **Nouvelle conclusion :** D2 tombe 60 s après 15 053,97 $ de Thin, dont 14 743,44 $ en flux taker, sans justification dans le plan. C'est le code de A qui ne lit pas les noms. Charge supérieure à 12 en tokens en alerte, selon l'audit. Seuil de 3,57e-07 inatteignable à 1 000 tirages. Placebo sensible au choix du nul. **Verdict inchangé**, le rang l'emporte seul.
- **Raison :** dire ce qu'on savait et ce qu'on ne pouvait pas mesurer.

### A17. Autres hypothèses

- **H10 :** « réfutée » devient **non soutenue** : le produit des prix suppose des rangs indépendants.
- **H11 :** précisée : 2 499 $, 855 $ et 243 $ de Kane avant le 8 oct.
- **H16 :** ajoutée, confirmée pour une paire.
- **Définition « affaiblie » :** « une certaine puissance » retiré, puissance non mesurée.

## Décisions qui reviennent à Benjamin

Aucune n'est prise ici.

1. Poser ou non `XMR_VISIBILITY_BOUNDARY` pour le passage par l'adresse étiquetée ChangeNOW.
2. Ouvrir ou non un dossier complet sur `0xa8e64a3c…`, et le traiter ou non comme un douzième compte. Le rapport ne le nomme pas ainsi.
3. Amendement 001 de l'étude, décidé par Claude alors que la règle les réserve à Benjamin : à relire.
4. Dire pourquoi D2 est à 18:51:00, écrire le verdict en code, corriger la charge, déclarer le filtre d'E4, E6 marqué déclaré au registre : amendements datés dans `collective/amendements/`.
5. Clore ou non `collective/`, faire entrer ou non les 5 adresses dans le R3 final.
6. Diffuser ou non. L'audit bloquait la diffusion sur C1 et C2 : C1 est corrigé. Pour C2, le tableau invalide est retiré et l'indice aussi, le taux corrigé reste en attente, et la recherche d'autres wallets aussi. `state/http_cache` garde `name`, `pseudonym`, `bio` : à ne jamais publier tel quel.
