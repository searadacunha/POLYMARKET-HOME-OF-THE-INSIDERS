# Contre-vérification de l'audit de l'enquête Ballon d'Or 2026

Écrit le 2 novembre 2026 par Claude Code (Opus 5.5). L'audit `~/Projects/PolySentinel-audit-20261102/RAPPORT_AUDIT.md` a été vérifié, pas adopté : relecture de la chaîne, recalculs sans son code, tests de ses explications. Le brouillon du rapport a ensuite été relu deux fois par un auditeur de conclusions indépendant : **FAIL les deux fois**, voir section 4. Les rapports finaux de l'enquête flow-trace ont ensuite été intégrés, section 8. Tous ces relecteurs sont des instances de Claude, avec les mêmes angles morts possibles. Aucune relecture humaine ou externe n'a eu lieu.

Une adresse n'est pas une personne. Trois niveaux ne se confondent jamais ici : **connexion financière** (un transfert relie deux adresses), **contrôle commun** (une même personne tient ces adresses), **insider trading** (quelqu'un a parié en connaissant le résultat).

Preuves : `evidence/contre_verification_20261102/`. Scripts : `tools/cv_*.py`. Niveaux : VÉRIFIÉ, relu ou recalculé ici le 02/11. RAPPORTÉ, écrit par un autre et non revérifié ici.

## 1. Tableau des conclusions

### Confirmées

| Conclusion | Vérification | Preuve |
|---|---|---|
| 25 retraits, 493 094,76 $ | Une sortie du wallet et une destruction de pUSD du même montant, 25 sur 25, depuis les reçus | `reconciliation_montants.json` |
| 46 dépôts, 304 137,63 $ | Une frappe du même montant, 46 sur 46 | `reconciliation_montants.json` |
| 129 367,79 $ sur 7 comptes soldés | Exact à 129 367,792914 $, périmètre précisé | `reconciliation_montants.json` |
| 182 relations, 94, 70 et 18 par catégorie | Recomptées, identifiants uniques | `compta_locale.json` |
| 11 historiques complets, 0 nommé coupé | Lignes, dépôts et retraits égaux à l'activité | `compta_locale.json`, `coupure_par_comparateur.json` |
| 55 paires, 21 par une règle naïve | Relu dans `graphs/links_classified.json`. Recomposition complète : RAPPORTÉ, audit | `compta_locale.json`, `out/a1_relations.txt` de l'audit |
| 1 seule exécution de carnet directe entre dossiers | Les 14 transactions communes décodées sur toute l'activité, sans limite de date | `transactions_communes.json` |
| Gel et sceau intacts | `PROTOCOL.lock` 27 fichiers sur 27, sceau de A 6 sur 6, à 23:28:27 UTC | `compta_locale.json` |
| E4 v2 reproductible | 3 graines, 2 dates, autre hachage (`PYTHONHASHSEED=7`) : identique, 6 sur 6 | `e4_reproduction.json` |
| Verdict gelé `VISIBLE_NON_SPECIFIQUE` | Rang 41 et 50 relus. Application par code : RAPPORTÉ, audit | `out/a10_verdict.txt` de l'audit |
| Services mutualisés | SwftSwap vérifié ici. Compteurs des autres relais : RAPPORTÉ, audit | `derniers_controles.json`, `out/a23_check.txt` |
| Comportement atypique, avec biais de sélection | Inchangé | rapport, section 1 |
| Information privilégiée non démontrée | Aucune donnée n'y répond, et aucun lien financier n'y répond | rapport, section 8 |

### Corrigées

| Version 1 | Maintenant | Preuve |
|---|---|---|
| E6 : 9/11 contre 10/43, p = 0,0006 | 9/20 comparateurs distincts à écart mesurable, p = 0,052. Relecture de flow-trace : 41/76, p = 0,074, et 32/39 comptes frais, p = 0,69, rien de distinctif. E6 est exploratoire | `complements.json`, `recoupe_flow_trace.json` |
| Rangs E6 sur 42 lignes | Rangs sur 20 comparateurs, par dossier | `complements.json` |
| H3, H4, H9 affaiblies | Non tranchées : aucun témoin positif, 19 paires sur 55 non testées par E4 | `e4_reproduction.json` |
| H13 non soutenue | Non tranchée : deux étiquettes ChangeNOW sur la clé de kraben006, source unique, relecture limitée à deux clés | `etiquettes_blockscout.json` |
| H10 réfutée | Non soutenue : le produit des prix suppose des rangs indépendants | audit, C10 |
| H11 : 0 $ de nommés au début de la hausse | Vrai le 8 oct., mais 2 499 $, 855 $ et 243 $ de Kane du 1er au 7 oct. | `compta_locale.json` |
| Retrait de 77 050,77 $ : « pas de log » | `LogTransfer` de 839 893,73 POL vers la clé, log 463 | `faux_signaux.json` |
| 839 893,73 POL : destination non lue | 839 000 POL échangés 108 s plus tard contre 75 946,74 USDT, solde USDT à 0 le 2 nov. | `faux_signaux.json` |
| 26,97 ETH : solde non vérifié | 26,9716 ETH, nonce 0 | `faux_signaux.json` |
| « Partie A scellée avant la lecture des noms » | Le code de A ne les lit pas, l'auteur les connaissait | plan gelé, en-tête |
| « 12 et 37 paires » dans E4 | Unions sur trois graines : 11, 11, 12 et 31, 25, 34 | `e4_reproduction.json` |
| Charge « au plus 12 par jour » | Premières alertes seulement. Tokens en alerte : jusqu'à 37 selon une estimation de l'audit | `out/a10_verdict.txt` de l'audit |

### Invalidées

| Affirmation | Pourquoi | Preuve |
|---|---|---|
| « 0 transfert direct » de la version 1 | 1 transfert natif, relu sur 2 nœuds | `transfert_brace_kraben_blockscout.json` |
| « Aucun wallet supplémentaire relié aux onze » de la version 1 | La clé de brace227 finance `0xa8e64a3c…`. Signalé par flow-trace, relu ici | `wallet_0xa8e6.json` |
| « Aucune interaction avec une adresse étiquetée ChangeNOW » de la version 1 | Deux étiquettes sur la clé de kraben006, source unique | `etiquettes_blockscout.json` |
| Tableau du taux de base de la version 1 | 48 wallets distincts sur 78 inutilisables | `taux_de_base.json`, section 5 ci-dessous |
| « 53 comparateurs sur 83 inutilisables », de l'audit et de ma version 2 | 5 wallets comptés comme jamais lus l'étaient sous un autre groupe : 48 sur 78 | `recoupe_flow_trace.json` |
| « KuCoin 3/11 contre 1/50 » comme indice | p = 0,052 sur les 30 utilisables. Relecture de flow-trace : origine Solana 3/11 contre 6/68, p = 0,11, et KuCoin 3/3 contre 1/6 sur 9 wallets. Reste un indice faible, sous aucun seuil corrigé | `complements.json`, `recoupe_flow_trace.json` |
| Écart de 2,8 min entre brace227 et kraben006 comme élément de lien (audit) | Vitesse ordinaire, 10 vendeurs sur 20. Ventes à 78 s, écart médian de 45 s entre ventes consécutives | `stats_retraits_kane.json`, `fenetre_vendeurs_kane.jsonl` |
| Redemption simultanée de 0x86544e4dfde et walletwallet8424 comme lien | Lot de 2 711 comptes en 136 transactions, déclencheur non lu | `calendrier_kane.json` |
| Candidat de 59,09 POL comme transfert entre dossiers | `0x408c…` paie lui-même 5,62 USDC, à travers un contrat mutualisé | `faux_signaux.json` |
| Même balayage de sortie de VidenteRibeira et cookedrice comme indice | Gxjc cosigne et paie les frais, 4 s et 2 s après réception. Le choix commun du service reste sans explication | `faux_signaux.json` |
| Transactions communes entre dossiers comme liens | 13 sur 14 sont des lots ou des co-makers | `transactions_communes.json` |
| Lecture « don de gas » du transfert (audit) | Peu soutenue : la clé de kraben006 avait déjà 0,0020 ETH et en a consommé 0,00018 depuis | `circuit_7xujs_brace_kraben.json` |
| « Faux positif » pour la vitesse de retrait de 0x86544e4dfde et walletwallet8424 (audit) | Le calendrier explique la redemption, pas le retrait | `stats_retraits_kane.json` |

### Indéterminées

| Question | Pourquoi |
|---|---|
| brace227 et `0xa8e64a3c…` : même opérateur, deux personnes à parts égales, ou prêt ? | Financement lu. Aucune donnée lue ici ne les départage |
| brace227 et kraben006 ont-ils un même propriétaire, ou se connaissent-ils seulement ? | Idem. Entrées BSC non lues |
| `0xa8e64a3c…` est-il le douzième compte allégué ? Existe-t-il d'autres wallets ? | Aucune preuve. Seul actif parmi les adresses testées par flow-trace, anciens proxys Safe et Magic non testés |
| Propriété commune de tout autre compte | Comptes d'exchange invisibles, aucun témoin positif |
| Ont-ils parié ensemble ? | Achats du 24 oct. postérieurs à l'article, p = 0,40 dans le créneau. Financement commun du 9 oct. : hypothèse, pas démonstration |
| Que signifie le retrait rapide après le lot Kane ? | Atypique à l'état brut, non significatif après correction dans les strates les plus comparables |
| Accès à une information privée | Les données publiques ne peuvent pas trancher |
| Taux de base au-delà de la relecture de flow-trace | 77 témoins, un dépôt par wallet, traits post hoc, exploratoire |
| Si un échange ChangeNOW a eu lieu, ce qu'il aurait rendu, statut `XMR_VISIBILITY_BOUNDARY` | Sortie invisible d'ici. Décision de Benjamin |
| Sortie de Gxjc et de `0x51cf2d9f…`, entrées BSC et Base | Registres privés ou chaînes sans historique gratuit, selon flow-trace |

## 2. L'audit vérifié, point par point

| Point | Verdict | Écart trouvé |
|---|---|---|
| C1, transfert direct | **Confirmé, à compléter** | Hash, bloc, adresses, montant, heure : exacts sur 2 nœuds. « Première sortie en 17 mois » ne vaut que pour Ethereum : nonce de 109 sur BSC, visible dans `cases/brace227.md`, jamais lu. Lu par flow-trace, relu dans son fichier : dernière sortie BSC le 17/05/2025 à 11:52:55, donc 16 mois et demi. La lecture « frais de gas » est peu soutenue. Le vidage et le payeur Solana manquaient. |
| C1, éléments plus faibles | **En partie invalidé** | L'écart de 2,8 min ne distingue pas la paire. Le p = 0,0012 mesure surtout deux comptes actifs le même après-midi : 8 achats sur 9 datent du 24 oct., après l'article, et le décalage dans ce créneau donne p = 0,40. Restent notables : deux plus gros acheteurs du créneau, et aucun autre acheteur n'atteint leurs scores. |
| C1, 59 POL | **Confirmé** | Reçu relu : 5,62 USDC sortis de `0x408c…`, 59,09 POL rendus. |
| C2, taux de base | **Confirmé et renforcé** | 17 coupés rejoués depuis le cache : aucun n'atteint le premier achat. **Mais son compte de 53 sur 83 est faux, et je l'avais « vérifié » :** 5 de ses 33 manquants sont déjà lus sous un autre groupe, c'est 48 wallets sur 78 distincts. Le « 0/12 frais » de l'audit devrait être 0/11 : un de ces comptes n'a pas d'origine lue, p = 0,107 et non 0,093. Si 2 des 28 non lus ont le trait, p = 0,064 et non 0,061. |
| C3, E6 | **Confirmé, à corriger** | L'audit dénonce les doublons puis garde 10/22, qui en contient un. Sur wallets distincts à écart mesurable : 9/20, p = 0,052. Le rang de cookedrice est 3 sur 20, pas 3 sur 21. |
| C4, E4 | **Confirmé, à préciser** | Filtre de 2 tokens lu dans le code, absent du plan. 45 et 19 paires non testées recalculées. Au 13 oct., le filtre n'explique que 5 des 45 : 40 viennent de comptes sans achat à cette date. Seuil de 1 ou 2 tokens égal au maximum : 2 × ln(190/2) = 9,1078. |
| C5, POL et ETH | **Confirmé** | Log 463 relu. L'échange rend 75 946,74 USDT à la clé, solde 0 ensuite. ETH : le nonce 0 est une meilleure preuve que le solde seul. |
| C6, « affaiblie » trop fort | **Confirmé** | Adopté pour H3, H4, H9. |
| C7, dates | **Confirmé, à préciser** | 18:50:00 lu dans l'activité de Thin : 15 053,97 $ dans l'activité, 14 743,44 $ en flux taker. Le rapport affiche 18:48 parce que la décision groupée commence à 18:48:52. Sceau à 23:28:27 UTC. |
| C8, protocole | **En partie vérifié** | La charge varie selon le comptage : 34 par jour sur 8 jours sur 13 dans le texte de l'audit, attribué à un recomptage que je n'ai pas refait ; 37 par jour sur 6 jours sur 16 dans son propre script, par approximation. Placebo : l'audit ne dit pas que son recalcul du tirage gelé donne 0,174 et non 0,145 stocké (sa reconstruction n'est pas le code gelé, reproduit à l'identique en copie fraîche), ni qu'une variante stricte donne 0,008 sur la famille et 0,012 sur les témoins. Non retenue car elle abaisse le nul, désormais dite dans le rapport. |
| C9, périmètre | **Confirmé, arrondis corrigés** | 188 957,12 $ et non ,13 ; 62 438,52 $ et non ,51. L'audit soustrayait des montants déjà arrondis. |
| C10, Gxjc | **Confirmé** | Cosignature et frais relus. Le choix commun de ce service reste sans explication. |
| C10, H14 | **Corrigé** | « Qu'ils venaient de faire tous les deux » est inexact : lot de 2 711 comptes. « Faux positif évité » est trop fort pour la vitesse de retrait. |
| C10, H10, H11 | **Confirmé** | Montants de Kane recalculés. |

## 3. Ce que l'audit n'avait pas vu

- **Le wallet non nommé `0xa8e64a3c…`,** financé par la clé de brace227. Trouvé par l'enquête flow-trace, relu ici : `owner()`, activité complète, transferts, enregistrement Relay des deux dépôts. Il figure aussi dans une rafale E2 sur Kane avec 0x86544e4dfde et walletwallet8424, relevée par l'auditeur de conclusions.
- **Deux étiquettes ChangeNOW sur la clé de kraben006.** Présentes dans mes propres fichiers, trouvées par l'auditeur de conclusions.
- Le transfert **vide** la clé de brace227 : 98,85 % envoyés, 0,02 % restant.
- L'ETH reçu juste avant vient d'un compte Solana, `7XUJs…frZc`, prouvé par le même identifiant sur les deux chaînes, à l'octet près. L'identifiant renvoyé par l'API Relay est différent de celui inscrit sur la chaîne.
- Le saut suivant de la clé de kraben006 : `0x7e67…`, adresse à 1 entrée et 1 sortie, puis `0x3f3E…`.
- Les 14 transactions communes à deux dossiers, décodées.
- Le lot Kane de 2 711 comptes en 136 transactions, 6 204 783,28 $.
- Le contrôle sur les vendeurs à 0,99 et sur les comptes du lot.

## 4. Mes erreurs, et le premier avis FAIL

**Relecture indépendante, deux passes, FAIL les deux fois.** Première passe : 31 défauts, vérifiés un à un avant correction. 1 écarté, D29, qui prenait le montant en dollars d'un compte pour son nombre de lignes : l'auditeur en convient. Seconde passe : D1 et D24 mal corrigés, la portée de D25 oubliée, et 14 nouveaux défauts de formulation, tous corrigés après vérification, dont la rafale E2 omise, un indice survendu et le périmètre limité des étiquettes. **Cette dernière série n'a pas été relue une troisième fois.** Principaux défauts de la première passe :

- **« Aucune étiquette » sur `0x3f3E…` : faux.** Ma lecture de la page `/addresses/` de Blockscout rendait des champs vides, alors que l'étiquette est dans les objets `from` et `to` des transactions déjà sauvées. C'est l'échec silencieux le plus grave de ce travail.
- **« Relu après audit » pour un scan que je n'ai pas refait.** Corrigé partout : il est attribué à l'audit, revérifié ici seulement pour deux clés sur Ethereum.
- **« Lot automatique » et « ce n'est pas leur décision » :** le déclencheur du lot n'est pas lu. Écrit maintenant comme une inférence.
- **Calcul circulaire de 13 %,** dont le taux incluait les deux comptes testés. Sur les 9 autres : 4,9 %.
- **« Comptes mono-pari » :** faux, 0x86544e4dfde a 7 issues.
- **« Le détenteur connaissait l'adresse » :** dépassait ce qu'établit une signature.
- **« Le vrai taux est entre les deux »,** sans fondement. Et 9/21, p = 0,039, était omis.
- **Filtre d'E4 tenu pour seule cause des 45 paires :** il n'en explique que 5.

**Erreur la plus visible : « 53 comparateurs inutilisables sur 83 ».** Repris de l'audit, recompté par moi en 33 + 16 + 4, relu par l'auditeur, envoyé à Benjamin dans mon message de fin de la version 2. Personne n'a vu que 5 wallets figurent dans deux groupes et sont déjà lus. Vu seulement en comparant avec les 78 témoins de flow-trace. Vrai compte : 28 + 16 + 4 = 48 sur 78.

**Autres erreurs trouvées en route :**

- `tools/cv_11_lot_kane.py` lisait 50 retraits au plus : 1 retrait à +1 230 s manqué. Aucun effet sous 10 min. Remplacé par des fenêtres complètes dans `tools/cv_13_ventes_kane.py`.
- 2 comptes du lot atteignent le plafond de 15 000 lignes : retirés du dénominateur, jamais comptés comme « sans retrait ».
- `0xa8e64a3c…` figurait parmi mes comparateurs, alors qu'il est financé par la clé de brace227 : retiré. D'où 175 comparateurs.
- Mon premier test du burn cherchait une destruction directe depuis le wallet : 25 faux écarts. Le burn part d'un contrat intermédiaire. Refait : 25 sur 25.
- Dans mon message à flow-trace, j'ai écrit 7 paiements en lot au lieu de 8. Corrigé par un second message.
- Piège constaté : dans `coin-balance-history` de Blockscout, `block_timestamp` est faux (07:16 pour une transaction de 13:54). Seuls les soldes et numéros de bloc sont utilisés ici, recoupés au wei près sur un nœud d'archive.

## 5. Les 17 historiques coupés

`tools/baseline.py` et `collective/code/ana_31_funding.py` arrêtent la lecture à 12 pages de 500 lignes, sans le signaler dans le taux de base. Tri croissant : ce sont les lignes les plus récentes qui manquent. Rejoué depuis le cache par `tools/cv_05_coupure.py`, sans réseau : **17 sur 17 s'arrêtent avant le premier achat de la famille.** Le dépôt retenu est donc le dernier de ce qui a été lu, pas celui d'avant l'achat. Détail : `coupure_par_comparateur.json`.

| Groupe | Wallet | Dépôt retenu | Montant $ | Premier achat de la famille | Écart, jours | Dernière ligne lue | Origine lue |
|---|---|---|---:|---|---:|---|---|
| meme_token | `0xb10047d6a254b2ebb306d7a7d13bf59171ab6461` | 2024-09-21 | 1 112,02 | 2026-09-26 | 735,6 | 2024-10-03 | non |
| non_surlignes | `0x614dc8d3542c12103d2c6a3553fd761e391d1546` | 2024-10-24 | 0,04 | 2026-09-29 | 705,0 | 2024-10-28 | non |
| token_oppose | `0x5cd5c8d7a17c78d7389d8b87b611aed83322ac33` | 2024-12-07 | 702,22 | 2026-10-02 | 663,2 | 2024-12-11 | non |
| token_oppose | `0xf797d4d1c038d1eb0593edae0e66bf8e4b2e0bf2` | 2025-02-20 | 48,49 | 2026-10-11 | 598,3 | 2025-05-28 | non |
| non_surlignes | `0x54b56146656e7eef9da02b3a030c18e06e924b31` | 2025-05-16 | 164,82 | 2026-09-30 | 501,7 | 2025-05-18 | non |
| token_oppose | `0x3de69fd6347a62a618656371e30a17b0c490e560` | 2025-10-18 | 1 905,00 | 2026-09-26 | 343,3 | 2025-10-21 | non |
| token_oppose | `0x5d636ffd7d0a613b8af6d481d14ddd96be562cbf` | 2025-11-18 | 4 078,17 | 2026-10-14 | 330,4 | 2026-04-23 | non |
| meme_token | `0x39aaed185b92e99a78249610cc14a589b764583c` | 2025-11-29 | 34 906,26 | 2026-10-19 | 324,5 | 2025-11-30 | non |
| meme_token | `0xe102b1da4367d827b48c47ea91fadf6997ff71df` | 2026-01-06 | 7 442,28 | 2026-10-03 | 269,8 | 2026-09-26 | non |
| meme_token | `0xf1ef8705e9f63c790c6fffd6329aea7011718cd6` | 2026-01-21 | 8 985,60 | 2026-10-09 | 260,9 | 2026-02-01 | non |
| token_oppose | `0x67ac9e1ad7d7e74ef0215d14fc8edb538e4fedf1` | 2026-02-22 | 7 777,00 | 2026-10-15 | 235,7 | 2026-02-22 | non |
| token_oppose | `0x80a0da00fbdc8440b0ef601341f14c3e24795708` | 2026-02-28 | 11 959,08 | 2026-10-09 | 223,4 | 2026-04-11 | non |
| token_oppose | `0x5b6331e7ff0831a3fe2ed12004747db1a9c911a4` | 2026-02-15 | 48 985,30 | 2026-09-26 | 222,9 | 2026-02-16 | non |
| non_surlignes | `0x970998da056e60c707d9b1fc55cfdf3d68c252ab` | 2026-07-09 | 149,44 | 2026-10-13 | 96,3 | 2026-07-09 | 728126428 |
| token_oppose | `0x9e3ed7b661a903fc97afcf49e0f014ebe869f882` | 2026-07-09 | 199 993,26 | 2026-09-27 | 79,8 | 2026-07-11 | 1 |
| token_oppose | `0x524db836890e08aceb3abcdee98d44240e324495` | 2026-07-22 | 2 838,00 | 2026-09-27 | 66,9 | 2026-09-17 | 1 |
| token_oppose | `0x2362ca97130b1aa518c8b1f4d52a0ab632c82ec5` | 2026-08-12 | 669,60 | 2026-10-12 | 61,5 | 2026-08-12 | 42161 |

Par groupe : 3 non surlignés, 4 même token, 10 token opposé, 0 compte frais, 0 nommé. 13 sur 17 n'ont aucune origine lue.

**Décomposition des 48 inutilisables, 78 wallets distincts moins 30 :** 28 jamais lus, tous des comptes frais, 16 lus sans origine (dont 14 sans lecture de route), 4 avec origine mais coupés. Les 83 lignes prévues comptent 5 wallets deux fois.

### Impact sur les conclusions négatives

| Conclusion négative | Dépend des 17 ? | Effet |
|---|---|---|
| « Pas d'écart établi sur KuCoin, Solana, `0xc8a6…` » | **Oui** | Indéterminé sur les seules données de l'enquête : p de 0,052, 0,110 et 0,071 sur 30, bornes de 0,005 à 0,995 selon les 48 absents. Levé en partie par la relecture de flow-trace : Solana p = 0,11, `0xc8a6…` p = 0,013, aucun sous le seuil corrigé de 0,0056. |
| Financement sous une heure | **Oui** | p de 0,0006 à 0,052 selon le dénominateur sur les données de l'enquête. Relecture de flow-trace : 41/76, p = 0,074, et 32/39 comptes frais, p = 0,69. Rien de distinctif. |
| Rangs E6 par dossier | **Oui** | Dénominateur de 42 lignes à 20 comptes. |
| « 0 premier retrait entre l'article et la cérémonie » dans `collective/results.md` | **En partie** | Le premier retrait d'un compte coupé n'est connu que s'il tombe dans les 6 000 premières lignes. Non revérifié pour ces 17. Fichier gelé non modifié. |
| « 0 lien discriminant », classement des services | **Non** | Le trafic de chaque service est mesuré à part. Seul `0xee7a…` a un témoin coupé, sans effet sur sa nature. |
| « Aucun autre transfert direct » | **Non** | Ne repose pas sur les comparateurs. Limité par son propre périmètre, section 4 du rapport. |
| Comptabilité des 11 dossiers | **Non** | 11 historiques sur 11 complets. |
| Verdict A, E1 à E4 | **Non** | Ne lisent pas ces historiques. Âges lus à part, `limit=1`. |

**Biais d'exclusion.** Les coupés sont les comptes les plus actifs et les plus anciens. Les retirer rend le groupe plus comparable en âge, mais moins représentatif de « tous les détenteurs ». Le sens de l'effet sur KuCoin est inconnu.

## 6. Retraits Kane : le test complet

**Question.** 0x86544e4dfde et walletwallet8424 retirent 96 s et 189 s après leur redemption, 91 s et 184 s après le repère de 01:58:20. Est-ce rare parmi les comptes du même lot ?

**Méthode.** Comptes du lot à 5 000 $ ou plus : 180, dont les 2 nommés. Sur 178 autres, 175 retenus : 2 lectures incomplètes, et `0xa8e64a3c…`, financé par la clé de brace227, qui retire 16 h 51 après. Fenêtre d'activité de 24 h avant et après, âge lu sur le premier événement, délai mesuré depuis la redemption de chaque compte. Fisher unilatéral sur « 2 nommés sur 2 ». Écrit après avoir vu les données. Non inscrit au registre gelé : liste dans `tests_exploratoires.jsonl`.

| Comparateurs | n | Moins de 5 min | p brut | p x 55 | Borne haute 95 % du taux | Moins de 10 min | p brut |
|---|---:|---:|---:|---:|---:|---:|---:|
| Tous | 175 | 1 | 0,0002 | 0,011 | 0,027 | 3 | 0,0006 |
| Taille 10 000 à 100 000 $ | 106 | 0 | 0,0002 | 0,010 | 0,028 | 1 | 0,0005 |
| Taille 20 000 à 50 000 $ | 40 | 0 | 0,0012 | 0,064 | 0,072 | 1 | 0,0035 |
| Compte de 30 jours ou moins | 22 | 0 | 0,0036 | 0,199 | 0,127 | 2 | 0,0217 |
| Compte de 60 jours ou moins | 28 | 0 | 0,0023 | 0,126 | 0,102 | 2 | 0,0138 |
| Aucun achat dans l'heure | 131 | 1 | 0,0003 | 0,019 | 0,036 | 1 | 0,0003 |
| Aucun trade dans l'heure | 124 | 1 | 0,0004 | 0,021 | 0,038 | 1 | 0,0004 |
| A retiré sous 24 h | 48 | 1 | 0,0024 | 0,135 | 0,095 | 3 | 0,0082 |
| Kane dernière clôture sous 24 h | 58 | 0 | 0,0006 | 0,031 | 0,050 | 1 | 0,0017 |
| A retiré sous 24 h, Kane dernière clôture | 27 | 0 | 0,0025 | 0,135 | 0,105 | 1 | 0,0074 |
| A retiré 50 % ou plus de Kane sous 24 h | 37 | 1 | 0,0040 | 0,223 | 0,122 | 3 | 0,0135 |
| 50 % ou plus, aucun trade dans l'heure | 28 | 1 | 0,0069 | 0,379 | 0,159 | 1 | 0,0069 |
| 60 jours ou moins, a retiré sous 24 h | 19 | 0 | 0,0048 | 0,262 | 0,146 | 2 | 0,0286 |

Dans la strate la plus proche, retrait sous 24 h et Kane dernière clôture, les délais vont de 327 s à plusieurs heures, médiane 24 030 s, soit 6 h 40.

**Biais de sélection traités :** taille, âge, intention de retirer, dernière position, réinvestissement (strates) ; choix de la paire parmi 55 (x 55).

**Biais non traités :**
- La presse a choisi les nommés après coup, parmi des comptes récents et concentrés. Aucune strate n'annule ce choix.
- La statistique elle-même, la vitesse, a été choisie après avoir vu l'écart. Les 26 tests sont emboîtés, leur minimum n'est pas une preuve de plus.
- Un seul événement, deux comptes.
- Non mesurés : notifications, logiciel de portefeuille, fuseau horaire, positions fermées au-delà de 24 h, comptes automatisés.
- Dépendance au taux supposé : à 10 %, la borne haute sur 27 comptes, voir 2 comptes sur 2 arrive une fois sur cent. À 4 sur 11, taux des nommés qui inclut ces deux comptes, 13 fois sur cent. Sur les 9 autres nommés, 2 sur 9, 4,9 fois sur cent.

**Comparaison utile.** Le même test sur 20 vendeurs de Kane à 0,99 donne l'inverse : 10 en moins de 5 min, p = 0,29. Retirer vite n'est donc pas rare chez un compte déjà actif à ce moment. Ce qui reste notable pour la paire du lot, c'est d'avoir retiré juste après un lot qu'ils n'ont pas déclenché eux-mêmes, selon toute apparence, à 02:00 UTC.

**Écart de 93 s entre eux.** 4 paires sur 1 128 parmi les comparateurs qui retirent sous 24 h font aussi peu, 0 où les deux sont sous 5 min. Mais une fois les deux rapides, deux délais tirés au hasard sous 5 min sont aussi proches dans 52 % des cas. L'écart n'ajoute rien à la vitesse.

**Conclusion.** Faux positif comme lien pour la redemption. Indice faible, exploratoire, pour la vitesse. Il ne prouve ni coordination ni propriété commune. Aucun transfert direct ne relie cette paire.

## 7. Non vérifié, et limites

- BSC, en dehors des nonces lus ici. Sorties de 0xc852 selon flow-trace, entrées non lues.
- Étiquettes Blockscout : source unique, non recoupée. Ma relecture se limite aux clés de brace227 et kraben006 sur Ethereum. Les 73 adresses de services de flow-trace ne sont pas relues ici.
- Wallet `0xa8e64a3c…` : lien entre l'envoi à Relay et le dépôt lu dans l'enregistrement Relay, pas par identifiant sur la chaîne. Nonce de 14 pour 13 envois listés, non expliqué.
- Compteurs de relais et de services : RAPPORTÉS par l'audit, sauf SwftSwap, `0x3f3E…`, `0xdd3d…` et les nonces lus ici.
- Scan des 27 adresses EVM, des 46 adresses en POL natif et des 9 adresses Solana : RAPPORTÉ par l'audit, historiques plafonnés sur 4 adresses. Vérifié ici pour les seules clés de brace227 et kraben006, sur Ethereum.
- Résultats de flow-trace : voir section 8, recoupés en partie seulement.
- Maillons 4 et 5 du circuit : Blockscout seul. Soldes des deux clés recoupés sur un nœud d'archive.
- Étiquette KuCoin : source unique.
- Placebo réalisable et charge : RAPPORTÉS par l'audit, non recalculés.
- La relecture indépendante n'a pas rejoué les numérateurs depuis les données brutes (charge de la machine), ni scanné les transcriptions.
- Rien ne remplace une demande légale auprès d'un exchange ou d'un fournisseur de portefeuille.

## 8. Rapports finaux de flow-trace : ce qui est recoupé et ce qui ne l'est pas

Reçus le 2 novembre, `~/Projects/PolySentinel-flow-trace/reports/`, avec accord de la session pour les citer. Recoupement : `recoupe_flow_trace.json`, `tools/cv_23_recoupe_flow_trace.py`, sans réseau.

| Élément | Recoupé ici | Résultat |
|---|---|---|
| p du taux de base | Oui, recalculés | 9 traits sur 9 égaux |
| Lecteur des comparateurs | En partie | Origine concordante 29 fois sur 30, source immédiate 27 sur 32, sur les wallets communs. Lecteur non refait |
| Compte des témoins | Oui | 78 distincts, ce qui a révélé mon erreur sur 53 |
| BSC de 0xc852 | Fichier relu | 5 sorties, dernière le 17/05/2025, aucune vers une adresse de `cases/*.json`. Lecture réseau non refaite |
| Autres wallets | Fichier relu | 1 seul actif, `0xa8e64a3c…`, sur 94 essais et 50 adresses : 44 sous 2 formes, 6 clés de dossiers sous l'ancienne seulement. Son rapport disait 47 : écart signalé, il l'a corrigé |
| Étiquettes `0xee7a…`, `0xf7c8…`, `0x8894…` | Fichier relu | Présentes. Source unique, non recoupée |
| `0xc8a6…` = VaultDepositooor | Fichier relu | Selon sa liste, nom de contrat vérifié. Non relu sur l'explorateur |
| Sorties, 74 %, Hyperliquid, Binance et KuCoin en amont | **Non** | RAPPORTÉ. Cité comme tel dans le rapport |
| Création du wallet le 8 oct. | **Non** | RAPPORTÉ |
| Absence de mixeur, Monero | **Non** | RAPPORTÉ, sur les adresses connues seulement |

Limite : flow-trace dit lui-même que sa relecture n'est pas un audit indépendant au sens fort. Cette intégration n'a pas été relue par l'auditeur de conclusions.

