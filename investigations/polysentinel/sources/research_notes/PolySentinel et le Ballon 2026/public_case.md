# Sources publiques du cas Ballon d’Or 2026

## Quand l’affaire était-elle déjà publique ?

### Takeaway
La borne attestée retrouvée est **2026-10-23 15:17:49 UTC**, et non le début de la cérémonie. Ce n’est pas une preuve qu’aucune rumeur antérieure n’existait.

### Cited Findings
- Le post primaire Upside porte cet horodatage dans le JSON public X ; l’identifiant snowflake donne indépendamment 15:17:49.270 UTC. Le champ `datePublished` de l’article initial donne aussi 15:17:49 UTC. Sources conservées : `labels_after/tweet_initial_full.json`, `upside_initial.html` et leurs métadonnées. [Post primaire](https://x.com/UpsideMediaoff/status/2113651111051596165), [article initial](https://www.upside24.com/articles/ballon-d-or-2024-264-000-mises-sur-polymarket-suggerent-une-fuite-du-top-5-avant-596165).
- L’UEFA annonçait une cérémonie à Londres le **26 octobre à 20:00 GMT / 21:00 CET**, dans une page datée du 19 octobre. [Horaire officiel](https://www.uefa.com/ballondor/news/02aa-21dcfc743210-2786daba77d8-1000--2026-ballon-d-or-ceremony-when-and-where-all-the-nominees-/).
- La publication officielle datée du 26 octobre confirme l’ordre Kane, Mbappé, Yamal, Rodri, Messi. Elle ne fournit pas ici une heure précise de première annonce. [Résultat officiel UEFA](https://www.uefa.com/uefachampionsleague/news/02aa-21ec47378e70-b29defb43769-1000--harry-kane-wins-2026-mens-ballon-d-or/).
- Avant la cérémonie, trois portraits présentant chacun un vainqueur différent ont été publiés par erreur ; Le Parisien rapporte l’explication de l’organisateur. Cela brouille le contexte informationnel du 26, sans expliquer mécaniquement des opérations du début octobre. [Article du 26 octobre](https://www.leparisien.fr/sports/football/kane-yamal-et-mbappe-annonces-vainqueurs-ces-articles-publies-sur-le-site-du-ballon-dor-qui-ont-seme-le-trouble-26-10-2026-ZEGPCXVUIJAXTMPAHL3PQXDKBM.php).

### Inferences
- Une alerte postérieure au 23 octobre 15:17:49 peut suivre une révélation publique. La borne « avant cérémonie » est un contrôle secondaire ; elle ne prouve pas l’antériorité à la révélation.
- La date éditoriale d’une page consultée le 30 n’est pas une capture contemporaine de tous ses champs. Seul l’horodatage précis du post est corroboré indépendamment ici.

### Gaps
L’heure exacte de l’annonce officielle du top cinq, la chronologie exhaustive des rumeurs et une capture historique complète des pages avant le 23 ne sont pas établies. Aucun résultat du détecteur n’a été consulté par ce chercheur.

## Quels comptes peuvent servir de comparaison documentaire ?

### Takeaway
`labels_after/labels.json` distingue **11 étiquettes publiques nominatives**, dont **6 correspondances exactes avec un alias actuel de l’API officielle** et **5 non résolues**. Ce n’est ni la liste complète des douze comptes allégués, ni un ensemble d’initiés prouvés. Le mot « exact » porte sur l’alias retourné aujourd’hui, pas sur une continuité historique démontrée.

### Cited Findings
- L’image originale présente neuf lignes surlignées : Thin-Disclaimer-Life, VidenteRibeira, cookedrice, WenZhuanBuPei, 0x86544e4dfde, brace227, walletwallet8424, Zoomman17, kraben006. La colonne est intitulée **SHARES**. Les autres détenteurs visibles non surlignés ne sont pas ajoutés aux suspects. [Image primaire](https://pbs.twimg.com/media/HVUwQxmXQAAHlDQ.jpg), liée dans le [post primaire](https://x.com/UpsideMediaoff/status/2113651111051596165).
- Les rapprochements exacts sont conservés avec leur URL, date de lecture et réponse officielle : [Thin-Disclaimer-Life, recherche adresse](https://gamma-api.polymarket.com/public-search?q=0x8d3319c51520518ad01f6744486ceea29f376f5b&search_profiles=true&limit_per_type=10), [VidenteRibeira](https://gamma-api.polymarket.com/public-search?q=VidenteRibeira&search_profiles=true&limit_per_type=10), [WenZhuanBuPei](https://gamma-api.polymarket.com/public-search?q=WenZhuanBuPei&search_profiles=true&limit_per_type=10), [brace227](https://gamma-api.polymarket.com/public-search?q=brace227&search_profiles=true&limit_per_type=10), [walletwallet8424](https://gamma-api.polymarket.com/public-search?q=walletwallet8424&search_profiles=true&limit_per_type=10), [OuldLm3alem](https://gamma-api.polymarket.com/public-search?q=OuldLm3alem&search_profiles=true&limit_per_type=10).
- Le suivi du 27 octobre nomme OuldLm3alem et 0xdd97e6 ; leur ajout est marqué **later_named_cases**, distinct de l’image du 23. [Suivi Upside](https://www.upside24.com/articles/ballon-d-or-2026-le-top-5-exact-avait-ete-mise-sur-polymarket-avant-la-ceremonie-723196).
- La recherche officielle pour kraben006 renvoie des noms proches différents ; Zoomman17 et cookedrice ne donnent pas non plus de correspondance exacte. Leurs pages directes retournent 404 le 30 octobre. La recherche du préfixe 0x86544e4dfde est vide. Le candidat 0xdd97e6… existe, mais la presse consultée ne donne ni adresse entière ni lien permettant de certifier l’association : `wallet=null`. [Recherche kraben006](https://gamma-api.polymarket.com/public-search?q=kraben006&search_profiles=true&limit_per_type=10), [Zoomman17](https://gamma-api.polymarket.com/public-search?q=Zoomman17&search_profiles=true&limit_per_type=10), [cookedrice](https://gamma-api.polymarket.com/public-search?q=cookedrice&search_profiles=true&limit_per_type=10), [préfixe 0x86544e4dfde](https://gamma-api.polymarket.com/public-search?q=0x86544e4dfde&search_profiles=true&limit_per_type=10).

### Inferences
- Comparaison autorisée sur `wallet` non nul et `mapping_status=exact_current_profile_alias` seulement. Les `candidate_wallet` ne sont pas des correspondances validées.
- Une adresse non mentionnée dans la presse reste non étiquetée. Elle n’est pas un faux positif par définition. Une absence dans une collecte tronquée n’est pas un faux négatif établi.
- Les labels ultérieurs ont été sélectionnés après le résultat : toute comparaison avec eux reste descriptive. Le coordinateur a signalé avoir vu quelques noms de fichiers au redémarrage ; on ne doit pas prétendre à son aveuglement personnel complet.

### Gaps
La liste exhaustive et adressée des douze comptes n’est pas publiée dans les pièces retrouvées. Les noms peuvent changer. Aucun contrôle civil ou propriétaire commun n’est établi. Les captures des profils consultés après la cérémonie ne prouvent pas leur état antérieur.

## Que prouvent les montants, les financements et les alternatives ?

### Takeaway
Les sources montrent un **signalement à examiner**, pas une preuve d’information privilégiée. Aucun financement commun n’est démontré dans les articles consultés. Les nombres médiatiques doivent rester des affirmations de source jusqu’au rapprochement des transactions et de l’inventaire.

### Cited Findings
- Upside allègue **264 000 dollars sur douze comptes**, dont sept sans autre activité observée, et une rotation du vainqueur vers les rangs exacts. Ce total n’est pas déduit des parts de l’image ; les coûts d’achat et les ventes doivent être reconstruits. [Article initial](https://www.upside24.com/articles/ballon-d-or-2024-264-000-mises-sur-polymarket-suggerent-une-fuite-du-top-5-avant-596165).
- Le suivi parle de près de **200 000 dollars de gains** et déclare lui-même qu’aucun lien entre comptes n’est prouvé. Il rapporte notamment des achats de 1 805 parts à 0,53 dollar : le produit vaut 956,65 dollars, pas 1 805 dollars investis. Ce calcul illustre une unité ; il ne valide pas la transaction ni le coût total de la position. [Suivi Upside](https://www.upside24.com/articles/ballon-d-or-2026-le-top-5-exact-avait-ete-mise-sur-polymarket-avant-la-ceremonie-723196).
- Journal du Coin utilise une autre sélection : **25 portefeuilles, près de 60 000 dollars**, jouant quatre rangs ; il décrit 16 entrées le jour de la cérémonie et envisage des suiveurs. Ces chiffres ne contredisent pas automatiquement les douze comptes et 264 000 dollars : périmètres différents. Son texte annonce environ 31 000 dollars pour OuldLm3alem alors que l’image affiche 21 663,54 dollars de PnL total ; pour 0x8d33, environ 31 500 dollars dans le texte contre 35 247,94 dans l’image. Une différence de périmètre ou d’instant est possible, mais non réconciliée. [Article JDC](https://journalducoin.com/actualites/mbappe-ballon-or-polymarket-paris-suspects/), [capture ventes](https://journalducoin-com.exactdn.com/app/uploads/2026/10/capture-compte-ouldlm3alem-encaissement.png?quality=90&strip=all&webp=90), [capture profil](https://journalducoin-com.exactdn.com/app/uploads/2026/10/capture-compte-0x8d33-pnl.png?quality=90&strip=all&webp=90).
- Numerama présente les deux comptes plus anciens comme des suiveurs possibles. Sa reprise emploie aussi « euros » pour un gain ailleurs exprimé en dollars ; aucune conversion n’est fournie. [Numerama](https://www.numerama.com/tech/2360575-polymarket-avait-raison-sur-le-ballon-dor-le-top-5-exact-avait-fuite-et-cest-un-gros-probleme.html).

### Inferences
- Les explications concurrentes à examiner sont copie après révélation, anticipation sportive publique, chance, diversification ou couverture, arbitrage entre issues et gestion de positions déjà gagnantes. Un classement exact ne fournit pas seul une probabilité de hasard : événements corrélés, sélection rétrospective et essais non publiés sont inconnus.
- Un funder commun éventuel pourrait être une plateforme, un bridge ou un relayer ; il ne prouverait pas à lui seul un opérateur commun. Il faut dater les transferts avant les prises de position, identifier les contrats et rapprocher les actifs réellement reçus.
- L’engagement économique demande achats moins ventes, frais, inventaire initial, conversions/splits/merges, dépôts et retraits. Les positions et PnL actuels ne peuvent être injectés dans le détecteur avant la cérémonie.

### Gaps
Aucun hash de transaction de financement commun fourni par les sources consultées ; aucun graphe on-chain exécuté dans cette sous-tâche. Les affirmations d’absence d’actualité, d’âge réel des wallets et de gains nets ne sont pas vérifiées indépendamment ici. Les résultats du détecteur et les métriques précision/rappel ne sont pas calculés dans ces notes.
