# Audit indépendant de l'enquête Ballon d'Or 2026

Audit du 2 novembre 2026, de 08:22 à 09:05 UTC, sur `~/Projects/PolySentinel-investigation/reports/rapport_final.md` livré à 08:19. Aucun fichier de l'enquête, aucune étude gelée et aucun composant de production n'ont été modifiés : les scripts ont tourné sous un profil qui refuse ces écritures. Empreintes avant et après : 23 223 fichiers, 0 changé, 0 disparu, 1 nouveau, `collective/registre/refus_garde.jsonl`, écrit par le hook `protocol_guard` quand il a refusé une de mes commandes de lecture. Ce refus n'a pas été contourné : j'ai refait la lecture depuis ce dossier, comme il l'indique.

Méthode : relecture du rapport, recalculs depuis les fichiers de preuve, relecture de la chaîne par des nœuds publics sans le cache de l'enquête, trois audits à l'aveugle (fuites, plan contre code, échecs silencieux) vérifiés ensuite. Scripts et sorties : `code/`, `out/` de ce dossier.

Limite de cet audit : je suis aussi une instance de Claude, avec les mêmes angles morts possibles que l'auteur. Tout ce qui suit sur les personnes reste du niveau « adresse » : aucune identité n'est établie ni recherchée.

## 1. Verdict

**Le socle comptable est solide. La conclusion « non démontré » tient. Mais le rapport doit être corrigé avant toute diffusion, sur trois points de fond :**

1. **« 0 transfert direct, 0 lien discriminant sur 55 paires » est faux pour une paire.** La clé de brace227 a envoyé de l'ETH à la clé de kraben006.
2. **Le tableau du taux de base n'est pas valable tel que publié :** 20 lectures de comparateurs sur 50 sont invalides. L'« indice KuCoin » perd sa signification.
3. **Plusieurs « AFFAIBLIE » confondent absence de preuve et preuve d'absence** : H3, H4 et H9 n'ont aucun témoin positif, et 19 paires nommées sur 55 ne sont jamais testées par E4.

| Niveau demandé | Rapport | Après audit |
|---|---|---|
| Comportement atypique | Observé, biais de sélection | **Confirmé** |
| Coordination démontrée | Non démontrée | **Non démontrée, mais la formulation doit changer** : une paire a un lien direct entre clés, à instruire |
| Insider trading démontré | Non démontré | **Confirmé non démontré** : rien dans les données n'y répond |

## 2. Conclusions vérifiées

Recalculées ou relues par moi, indépendamment du code de l'enquête.

**Argent et chaîne** (`out/a1_relations.txt`, `out/a2_chain.txt`, `out/a3_activity.txt`)

- 25 retraits, tous réussis sur la chaîne. Chaque destruction de pUSD égale le montant de l'API, 25 sur 25, somme 493 094,76 $. Une seule destruction par transaction : **aucun double comptage**.
- 46 dépôts, 46 frappes exactes, somme 304 137,63 $.
- 129 367,79 $ est la somme exacte des 7 comptes soldés. Voir C9 pour ce que ce chiffre couvre.
- Aucune transaction en double entre dossiers, aucune à la fois dépôt et retrait.
- Les 11 historiques relus aujourd'hui sur l'API donnent le même nombre de lignes et les mêmes dépôts et retraits.
- 0x86544e4dfde : le résidu de -15,8647 $ est exactement la somme de ses 3 `REFERRAL_REWARD`. Le refus de le dire soldé est mécanique.

**Relations** (`out/a1_relations.txt`, `out/a18_misc.txt`)

- 182 relations, 182 identifiants uniques, mêmes contenus dans les dossiers et le graphe, aucune vers l'adresse zéro. 94 ONCHAIN, 70 PROTOCOL, 18 SERVICE.
- Chaque retrait a exactement une relation. Les 24 liens Relay d'un retrait ont le même identifiant dans le log Polygon et dans le paiement, 24 sur 24.
- Les 24 paiements viennent d'un solveur publié par Relay, 24 sur 24. Le code de l'enquête l'écrivait sans le vérifier : c'est maintenant vérifié.
- 55 paires, 21 paires naïves et 8 adresses partagées se recomposent à l'identique.

**Services mutualisés** (`out/a15_pairs.txt`, `out/a23_check.txt`)

- La nature de service tient, avec des données publiques que le rapport n'avait pas : `0xee7a…` (proxy, 1,85 M de transactions), `0x58f2…` (119 000), `0xc1d1…` (contrat vérifié nommé **SwftSwap**), `0xc8a6…` (aussi chez 5 comparateurs).
- Les deux adresses « non classées » signalées par l'audit des outils, `0xb42f…` et `0xb01c…`, partagées par 0x86544e4dfde et walletwallet8424, sont des relais à 850 000 transactions. Fausse alerte.
- Autres communs de mon scan, écartés : `0xc066…` (851 000 transactions) et `0xe347…` (1,8 M de transferts, reçoit des frais d'environ 1 $).
- KuCoin Hot Wallet 2 : une seule source reste trouvable (Orb), rien d'officiel, comme le dit le rapport.

**Étude gelée** (`out/a5_read.txt`, `out/a6_e4.txt`, `out/a10_verdict.txt`)

- Sceau de la partie A intact, 6 fichiers sur 6. Empreintes du gel intactes (audit protocole).
- **Amendement E4 :** v2 ne change que l'ordre et les graines, plus le plafond d'affichage. Statistique, univers, seuils et tirages inchangés. Sortie relancée de mon côté sous un autre `PYTHONHASHSEED`, identique sur les deux dates pour la graine 20261101. L'ancienne sortie reste en place. Décision de Benjamin vérifiée dans la transcription.
- Verdict recalculé par code, puisque l'étude l'applique à la main : A0 sur 5 tokens à D2 et 14 à T_FIN, meilleur rang 41 et 50, donc `VISIBLE_NON_SPECIFIQUE`. Il tient quoi qu'il arrive sur la charge (C8).
- Vérification sur le fond : les sommes par issue (168 888,64 $, 57 544,64 $, 155 188,28 $), les 5 et 14 paires synchrones, la médiane de 2,6 min se recomposent depuis les dossiers.

**Comportement** : 11 comptes actifs depuis octobre seulement, 9 sur 11 financés moins d'une heure avant le premier achat, tous sur Mbappé devant Yamal. Correct, et le biais de sélection est bien dit.

## 3. Conclusions contestées

Classées par conséquence.

### C1. Un transfert direct existe entre deux dossiers (BLOQUANT)

Le rapport écrit « 0 transfert direct de fonds » et « 0 lien discriminant ». Il précise ailleurs « sur les chaînes et jetons lus », et son scan ne lit ni l'ETH natif ni l'historique des clés.

- **Fait lu sur deux sources** (Blockscout, nœud public) : `0xd07bea20a22d9381e0ab364e7a7421776318c6f4aa7258799638472ad7092b98`, bloc 26119420, 4 oct. 13:54:35 UTC, de `0xc852b0…af26` (clé de brace227) à `0x101b5f…fb65` (clé de kraben006), **0,00205 ETH**, envoi simple, sans données.
- **Contexte :** la clé de brace227 n'avait rien fait depuis le 28 avril 2025. Elle reçoit 0,00169 ETH d'un solveur Relay à 13:52:47, puis envoie 108 secondes plus tard. C'est sa première sortie en 17 mois, 5 jours avant son premier achat Polymarket. kraben006 était déjà actif depuis le 1er octobre.
- **Autres éléments sur cette paire, plus faibles :** retraits principaux à 2,8 min d'écart, tous deux juste après la vente de Kane ; passage par SwftSwap ; 9 décisions d'achat à moins de 5 min sur un même token, surtout Kane le 24 oct., p ≈ 0,0012 contre des décalages temporels, exploratoire et **au-dessus du seuil de 0,00091 corrigé des 55 paires** (`out/a20_nearbuys.txt`).
- **Ce que cela établit :** un lien financier direct entre deux clés, sans service.
- **Ce que cela n'établit pas :** un propriétaire commun. Un montant de cet ordre ressemble à des frais de gas donnés à quelqu'un d'autre : deux personnes qui se connaissent suffisent. Une clé compromise reste possible, mais elle sert ensuite normalement. Rien ne dit non plus qu'ils ont parié ensemble.

**Correction demandée :** remplacer les deux « 0 » par « 1 transfert natif direct, paire brace227 et kraben006 », et passer H3 et H4 à « non tranchées » pour cette paire.

Reste du scan : aucun autre transfert direct entre dossiers. Ni sur 27 adresses EVM lues sur Ethereum, Arbitrum et Base, ni en POL natif sur 46 adresses. Un seul candidat POL (59 POL de `0xc590…` vers `0x408c…`) est **un faux positif que j'ai écarté** : c'est un échange fait par `0x408c…` à travers un contrat mutualisé (65 destinataires en 5 h) (`out/a24_c590.txt`). Aucun lien sur les 9 adresses Solana lues, payeurs de frais compris.

### C2. Le tableau du taux de base n'est pas valable (BLOQUANT)

- `tools/baseline.py` coupe l'historique à 12 pages sans le signaler. **17 comparateurs sur 50, 0 nommé sur 11**, sont lus sur un dépôt qui n'est pas celui d'avant le premier achat, par exemple un dépôt de 0,04 $ d'octobre 2024 pour un achat de 2026 (`out/a19_final.txt`).
- 14 lignes sans lecture de route comptent comme « pas KuCoin, pas Solana », plus 2 sans origine.
- **Les comparateurs utilisables sont 30 sur les 83 prévus.**

| Trait | Nommés | Publié | Origine lue | Plus historique complet | Comptes frais |
|---|---|---|---|---:|---:|
| KuCoin | 3/11 | 1/50, p = 0,016 | 1/34, p = 0,040 | 1/30, **p = 0,052** | 0/12, p = 0,093 |
| Solana | 3/11 | 2/50, p = 0,037 | 2/34, p = 0,085 | 2/30, **p = 0,110** | 0/12, p = 0,093 |
| `0xc8a6…` | 5/11 | 5/50, p = 0,012 | 5/34, p = 0,048 | 5/30, **p = 0,071** | 1/12, p = 0,060 |

- **KuCoin n'est pas un indice indépendant.** Son libellé n'est lu que sur une origine Solana : 3/3 contre 1/2. C'est donc la même observation que « origine Solana ».
- Le rapport met en avant KuCoin alors que `0xc8a6…` avait le plus petit p du tableau, sans le discuter : choix fait après coup.

**Les 33 wallets manquants** (3 même token, 2 token opposé, 28 comptes frais). Le manque ne dépend pas du résultat, ce qui est bien, mais il pèse sur le seul groupe comparable en âge :

- À données publiées, p passe au-dessus de 0,05 si 5 des 33 ont le trait.
- Face aux comptes frais, si **2 des 28** non lus ont le trait, p = 0,061. Un taux égal à celui des nommés en donnerait environ 8.
- 0/12 laisse un taux possible jusqu'à 26 %, alors que les nommés sont à 27 %.

**Correction demandée :** retirer « KuCoin plus fréquent » des indices, ou relire les 33 et les 17 avec une pagination complète.

### C3. Financement sous une heure : l'écart est surestimé

Même défaut dans E6 (`ana_31_funding.py`, `per_wallet_stats.py`) : 21 lignes sur 43 sont tronquées, `complete` est ignoré, et 38 wallets donnent 43 lignes.

- Publié : 9/11 contre 10/43, p = 0,0006.
- Sur lignes complètes : **9/11 contre 10/22, p = 0,05** (`out/a14_d2.txt`).
- Le vrai taux est entre les deux. Le rang « 3 comparateurs sur 42 » de cookedrice devient 3 sur 21.
- L'écart reste en partie confondu avec l'âge, comme le dit le rapport.

### C4. E4 v2 : « 0 paire nommée » ne veut pas dire ce qu'on lit

Vérifié dans `out/a6_e4.txt` :

- **VidenteRibeira et WenZhuanBuPei ne peuvent pas y figurer :** le code exige 2 tokens à 100 $, filtre absent du plan, qui écarte 260 wallets sur 621 à T_FIN. Leurs dossiers écrivent pourtant « 0 paire ».
- **19 paires nommées sur 55 ne sont jamais testées à T_FIN**, et 45 sur 55 à D2 (5 nommés dans l'univers).
- À D2, le seuil pour 1 ou 2 tokens communs égale le maximum possible : une telle paire ne peut pas le dépasser.
- Le seuil est un maximum sur toutes les paires : il ne voit qu'un extrême. Les meilleures paires nommées sont à 0,90 du seuil (OuldLm3alem et 0xdd97e6, centile 98,7 à nombre de tokens égal).
- Exploratoire, au niveau du groupe : les 9 nommés ont un chevauchement plus fort que des groupes tirés parmi les détenteurs du même token à T_FIN (part à ou au-dessus : 0,04), pas à D2 (0,27) (`out/a8_group.txt`). Non corrigé, et confondu avec la sélection par la presse : à ne pas surinterpréter.
- Le rapport écrit « 12 et 37 paires » : ce sont des unions sur trois graines. Par graine : 11, 11, 12 et 31, 25, 34.

**Correction demandée :** H9 passe à « non tranchée », et les lignes Vidente et Wen disent « hors univers ».

### C5. « Le paiement natif ne laisse pas de log » est faux sur Polygon

- Le reçu de `0x909d…a6f1` contient un `LogTransfer` de **839 893,73 POL vers la clé d'OuldLm3alem** (log 463). Cette relation peut passer de SERVICE_INTERACTION à lue sur la chaîne.
- La « destination non lue » se lit : 839 000 POL partent 108 secondes plus tard, à 23:52:41, dans un échange via Universal Router, `0x8c35829294c002aabcd2bd518e88f46f86e4c5a075c6e89938d4532cc62dd2c3`. Le saut suivant n'a pas été suivi. Pas d'adresse d'un autre dossier parmi celles vues.
- 0xdd97e6 : les 26,97 ETH sont toujours sur `0xca8B…6165`, aucune sortie au 2 nov. Le « solde non vérifié » peut être levé.

### C6. Les « AFFAIBLIE » sur la propriété commune sont trop forts

H3 et H4 reposent sur « 11 clés distinctes, routes différentes, 0 lien ». Or un même opérateur prudent aurait exactement cette empreinte, et **aucun témoin positif** ne montre que la méthode trouverait un lien réel. C1 montre qu'elle en a manqué un. Le terme juste est « non tranchée ». H13 devrait aussi citer SwftSwap, service d'échange de la même famille que ceux qu'elle examine, utilisé par brace227 et kraben006.

### C7. Dates et aveuglement

- « Partie A scellée avant la lecture des noms » est trompeur. Le sceau date du 1er nov. 23:28 UTC, alors que les noms sont dans la mission dès 22:26, que l'inventaire et le dossier Thin ont été faits avant. C'est le code de A qui ne lit pas les noms, pas l'auteur. Le rapport dit ailleurs que l'auteur connaissait l'affaire : garder cette seule phrase.
- **D2 = 18:51:00 tombe 60 secondes après un achat de 14 743 $ de Thin** (18:50:00). Le plan ne justifie pas cette date (`out/a14_d2.txt`). E1 s'arrête au tick de 18:00 et ne le voit pas, E4 et les sommes « avant le 13 octobre » l'incluent. Non dit dans le rapport.

### C8. Écarts de protocole non déclarés

Aucun ne renverse le verdict A, car le rang à lui seul l'emporte.

- La charge compte les **premières** alertes, au plus 12 par jour. Le plan parle de tokens en alerte : jusqu'à 34 par jour d'après le recomptage de l'audit, 8 jours sur 13 au-dessus de 20. Mon estimation sur 72 h donne le même ordre.
- Placebo : sur M, 10 à 13 % des dates mélangées tombent après l'achat et comptent comme fraîches. Refait avec un mélange réalisable, p = 0,15 à D2 et 0,87 à T_FIN sur M, 0,06 et 0,83 sur les témoins (`out/a13_placebo.txt`). La lecture reste la même. Mon mélange n'est pas uniforme : ordre de grandeur seulement.
- Bonferroni à 3,57e-07 est **inatteignable** : le plus petit p possible à 1 000 tirages est 0,001. « Aucun p n'approche ce seuil » n'apporte donc rien.
- Rapporté par l'audit, relu en partie : témoins X tirés sur des lignes postérieures à D2 (`col_echantillon.py`, vérifié), E2 et E3 non datés.
- E6 ajouté après résultats sans amendement. Il est dit dans `results.md`, mais le registre le marque déclaré.
- **Amendement 001 décidé par Claude**, alors que la règle réserve les amendements à Benjamin. Il attend toujours ta relecture.

### C9. 129 367,79 $ : exact, mais périmètre partiel

Sur les 11 comptes, retraits moins dépôts : **188 957,13 $**. Sur les 4 exclus, 3 sont soldés en pratique, pour 62 438,51 $ : 0x86544e4dfde (résidu = primes de parrainage), brace227 et OuldLm3alem (résidu ≈ solde restant). Zoomman17 est **perdant de 2 849,19 $**, avec 4 positions à valeur nulle, et 59 % de ses achats ailleurs. Le rapport ne le dit pas aussi nettement. Les deux lignes ouvertes de 0xdd97e6 sont bien à prix nul (Barcelone, Zidane) : son solde tient.

### C10. Corrections mineures

- **Gxjc :** les deux sorties sont cosignées par Gxjc, qui paie les frais, 4 et 2 secondes après réception. Ces adresses sont donc probablement des adresses de dépôt tenues par le service. Le « même comportement » de VidenteRibeira et cookedrice est son automatisme : **l'indice faible baisse encore**.
- **H11 :** « 0 $ de comptes nommés le 8 octobre » est exact pour ce jour. Mais kraben006 achète 2 500 $ de Kane les 1er et 2 octobre, Zoomman17 855 $ le 6, kraben006 243 $ le 7.
- **H14 :** 8 retraits principaux sur 11 suivent de moins de 10 min la dernière vente ou redemption. La proximité de 0x86544e4dfde et walletwallet8424 (1,6 min) s'explique par la redemption du marché Kane, qu'ils venaient de faire tous les deux. **Faux positif évité** : c'est le calendrier qui les rapproche.
- **H10 :** le produit des prix suppose l'indépendance, ce qui est faux pour des rangs. Le sens de la conclusion tient, mais « réfutée » est trop fort : « non soutenue ».
- `state/http_cache` garde `name`, `pseudonym`, `bio` : à ne jamais publier tel quel.

## 4. Indéterminé

- Si brace227 et kraben006 ont un même propriétaire, ou s'ils se connaissent seulement. Et s'ils ont parié ensemble.
- Propriété commune de tout autre compte : comptes d'exchange invisibles, méthode sans témoin positif.
- Accès à une information privée : les données publiques ne peuvent pas trancher.
- Ce qui sort de Gxjc, et l'identité de ce service.
- Le taux de base réel : 53 comparateurs sur 83 inutilisables à ce jour.
- La suite des 839 000 POL après l'échange.
- La profondeur de carnet au moment des achats.

**Non lu par cet audit :** BSC (nœuds archive refusés), Optimism (27 erreurs), Polygon via Blockscout (403, remplacé par les logs pour le POL natif), Base et Arbitrum au-delà de ce que listent les adresses. Historiques plafonnés à 3 pages sur 4 adresses (`0x3ab2…`, `0x7ff8…`, `0xa322…`, `0xf7c8…`). Statuts S_A des 5 wallets résolus tardivement : non recoupés. La capture Upside : relue via le fichier de reconstruction, sans refaire le calcul depuis le tape. Audit statistique complet et audit des conclusions du protocole : remplacés par ce rapport, sans en avoir la forme.

## 5. Corrections demandées, dans l'ordre

1. **C1 :** corriger la conclusion, le tableau et H3, H4 ; ajouter le fait au dossier de chaque wallet.
2. **C2, C3 :** relire les comparateurs avec pagination complète, retirer les lignes illisibles du dénominateur, puis republier le taux de base. Sans cela, retirer l'indice KuCoin.
3. **C4 :** dire ce qu'E4 ne peut pas voir, H9 « non tranchée », et déclarer le filtre.
4. **C5 :** reclasser le retrait de 77 050,77 $, dater la sortie des POL, lever le doute sur les ETH.
5. **C7, C8 :** dire pourquoi D2 est à 18:51:00, écrire le verdict en code, corriger la charge. Par amendement daté : c'est **ta décision**.
6. **C6 :** ajouter un scan natif et de l'historique des clés aux outils, avec un témoin positif sur des paires connues.

Le rapport de l'enquête ne doit pas sortir de ce Mac avant les points 1 et 2 : il affirme une absence que la chaîne contredit. Je n'ai rien corrigé moi-même dans ce dossier.
