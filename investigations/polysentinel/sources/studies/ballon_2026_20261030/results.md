# Le Ballon expose les limites de PolySentinel

Étude du 30 octobre 2026 ; verdict : `NOT_DEPLOYED_THEN_AND_COUNTERFACTUAL_NOT_ESTIMABLE`.

**PolySentinel n’a pas détecté cette affaire avant sa révélation : son premier cycle local date du 27 octobre 2026 à 17:07 UTC, après le signalement public et la cérémonie.** Le replay fidèle produit zéro alerte sur zéro donnée disponible à ces dates ; il ne mesure donc pas une défaillance de sensibilité. La reconstruction retrouve des transactions antérieures pour six adresses associées aujourd’hui à des comptes publiquement cités. Elle ne permet pas d’établir combien auraient déclenché une alerte, à quelle heure ou à quel rang. Le verdict contrefactuel reste **non estimable**, avec des lacunes identifiées et des mouvements économiques précis vérifiés sur chaîne. ([Résultats gelés T1](/Users/benjamindacunha/Projects/PolySentinel/studies/ballon_2026_20261030/derived/audit.json), [rapprochement T2](/Users/benjamindacunha/Projects/PolySentinel/studies/ballon_2026_20261030/derived/public_overlap.json))

## La coupure utile précède la cérémonie de trois jours

La première révélation primaire retrouvée est le post Upside du **23 octobre à 15:17:49 UTC**, corroboré par son identifiant et les métadonnées de l’article. C’est une borne attestée, pas la preuve qu’aucune rumeur ne circulait auparavant. La seconde coupure est le **26 octobre à 20:00 UTC**, début annoncé de la cérémonie ; elle ne représente pas l’heure exacte d’annonce des différents rangs. Une opération antérieure à la cérémonie peut donc suivre une information déjà publique. ([Post primaire](https://x.com/UpsideMediaoff/status/2113651111051596165), [horaire UEFA](https://www.uefa.com/ballondor/news/02aa-21dcfc743210-2786daba77d8-1000--2026-ballon-d-or-ceremony-when-and-where-all-the-nominees-/), [preuves archivées](</Users/benjamindacunha/Projects/PolySentinel/research_notes/PolySentinel et le Ballon 2026/public_case.md>))

Le plan a fixé les fenêtres, les calculs et le détecteur existant `exploratory-1.2`, sans ajuster ses seuils. La découverte des marchés était lexicale, indépendante des vainqueurs et des adresses publiées. Les sorties ont été fixées avant le rapprochement des labels. L’aveuglement personnel intégral n’est toutefois pas revendiqué : le coordinateur avait vu des titres révélant le gagnant et quelques noms de fichiers de profils lors d’une reprise. Cette étude reste un cas rétrospectif choisi après médiatisation. ([Plan gelé](/Users/benjamindacunha/Projects/PolySentinel/studies/ballon_2026_20261030/analysis_plan.md), [empreintes pré-labels](/Users/benjamindacunha/Projects/PolySentinel/studies/ballon_2026_20261030/derived/pre_label_output_sha256.json))

Le replay exige à la fois une date de transaction et une date d’observation antérieures à la coupure. Les transactions récupérées le 30 octobre ne deviennent pas des observations du 23. Aucun statut actuel de marché, liquidité actuelle ou résultat final n’a servi à fabriquer un classement historique. Aux deux coupures, la base locale contient zéro transaction, zéro marché et zéro alerte admissibles. **Nombre contrefactuel détecté, première alerte, rang, faux positifs, précision et rappel sont non mesurables.** ([Sortie T1](/Users/benjamindacunha/Projects/PolySentinel/studies/ballon_2026_20261030/derived/audit.json))

## Les 46 533 lignes récupérées laissent trois flux incomplets

La collecte a consommé les **100 requêtes prévues** : trois recherches, 31 actualisations et 66 pages de transactions. Le périmètre comprend **31 événements et 642 marchés**, y compris trophées féminins, autres récompenses et marchés connexes. Il ne représente pas seulement le classement masculin. Les 46 533 lignes ont été rapprochées des réponses brutes, sans ligne rejetée ni erreur de collecte constatée. Cette validation technique ne certifie pas l’exhaustivité du fournisseur. ([Couverture et sources](</Users/benjamindacunha/Projects/PolySentinel/research_notes/PolySentinel et le Ballon 2026/historical_coverage.md>), [validation](/Users/benjamindacunha/Projects/PolySentinel/studies/ballon_2026_20261030/data/collection_validation.json))

Dans la fenêtre commune commençant le **26 septembre à 20:00 UTC**, 15 067 lignes concernent 1 293 wallets avant le signalement ; 34 648 lignes concernent 2 357 wallets avant la cérémonie. Ce sont des effectifs de transactions retrouvées après coup ; l’effectif indépendant est une seule affaire. Le flux est limité aux takers : les participants uniquement makers ne sont pas couverts. ([T1](/Users/benjamindacunha/Projects/PolySentinel/studies/ballon_2026_20261030/derived/audit.json), [documentation Data API](https://data-api.polymarket.com/v2/docs))

La pagination est terminée pour 28 flux sur 31. Pour le vainqueur masculin, les 6 000 lignes récupérées ne remontent qu’au **26 octobre à 22:26:17**, donc après les deux coupures. Le top cinq s’arrête au 23 octobre à 12:28:24 et le top trois au 18 octobre à 18:49:48 ; leurs curseurs restent ouverts. Les marchés supprimés, renommés ou mal indexés demeurent également possibles. L’absence d’une adresse dans ce corpus ne constituerait pas un faux négatif établi. ([État par flux](/Users/benjamindacunha/Projects/PolySentinel/studies/ballon_2026_20261030/data/collection_summary.json))

## Six correspondances documentaires ne sont pas six détections

Le dossier public contient **11 étiquettes nominatives : six correspondances exactes avec des alias actuels, cinq non résolues**. Parmi les neuf comptes surlignés dans l’image initiale, cinq sont résolus et tous cinq apparaissent dans le corpus avant chacune des coupures. Parmi les deux comptes nommés ultérieurement, un est résolu et présent aux deux dates. La continuité historique des alias n’est pas prouvée. Les comptes non cités restent non étiquetés ; aucun groupe d’« initiés » ou de « non-initiés » vérifiés n’existe ici. ([Image primaire](https://pbs.twimg.com/media/HVUwQxmXQAAHlDQ.jpg), [suivi Upside](https://www.upside24.com/articles/ballon-d-or-2026-le-top-5-exact-avait-ete-mise-sur-polymarket-avant-la-ceremonie-723196), [labels archivés](</Users/benjamindacunha/Projects/PolySentinel/research_notes/PolySentinel et le Ballon 2026/labels_after/labels.json>))

Le tableau décrit uniquement les lignes disponibles avant le **23 octobre à 15:17:49 UTC**. Les montants sont les sommes API `taille × prix`, arrondies à deux décimales, hors frais. La première date est celle du premier trade retrouvé dans ce corpus : **ni création du wallet, ni première alerte**. ([Cellules T2](/Users/benjamindacunha/Projects/PolySentinel/studies/ballon_2026_20261030/derived/public_overlap.json))

| Alias actuel | Premier trade retrouvé, UTC | Lignes | Achats nominaux partiels | Ventes nominales partielles |
|---|---|---:|---:|---:|
| brace227 | 09/10 20:50:04 | 54 | 6 813,69 | 1 235,61 |
| Thin-Disclaimer-Life | 12/10 00:16:03 | 45 | 42 392,12 | 179,42 |
| walletwallet8424 | 15/10 19:43:25 | 7 | 879,92 | 0,00 |
| VidenteRibeira | 16/10 00:27:24 | 6 | 27 245,13 | 0,00 |
| WenZhuanBuPei | 18/10 20:16:17 | 3 | 15 564,48 | 0,00 |
| OuldLm3alem, nommé ultérieurement | 22/10 18:49:30 | 21 | 15 438,41 | 0,00 |

Ces sommes n’établissent pas le capital total engagé. L’affirmation médiatique de **264 000 dollars sur douze comptes** reste une affirmation de source non réconciliée ; l’image exprime des parts, pas des coûts d’achat. Les pages d’activité obtenues ultérieurement pour les six adresses n’avaient plus de continuation, mais cette fin de pagination ne prouve ni l’exhaustivité on-chain ni l’absence d’activité passée ailleurs. ([Article initial](https://www.upside24.com/articles/ballon-d-or-2024-264-000-mises-sur-polymarket-suggerent-une-fuite-du-top-5-avant-596165), [historique forensique](</Users/benjamindacunha/Projects/PolySentinel/research_notes/PolySentinel et le Ballon 2026/forensics.md>))

## Les reçus prouvent des débits et une route partagée

L’enquête complémentaire **exploratoire, sélectionnée après les labels**, contrôle un trade et un dépôt par adresse (six adresses, une seule affaire indépendante). Les six trades sont rapprochés de reçus réussis et de blocs canoniques ; les six dépôts sont également confirmés. Pour chaque trade retenu, nominal on-chain plus frais collateral égale exactement le débit pUSD. Les valeurs suivantes concernent ces seules opérations, sans gas ni remises ultérieures. Le dépôt n’est pas nécessairement entièrement investi sur les marchés étudiés. ([Réconciliations et hashes](</Users/benjamindacunha/Projects/PolySentinel/research_notes/PolySentinel et le Ballon 2026/forensics/funding_routes_and_amounts.json>), [reçus et dates](</Users/benjamindacunha/Projects/PolySentinel/research_notes/PolySentinel et le Ballon 2026/forensics/summary.json>))

| Alias | Nominal du trade, pUSD | Frais, pUSD | Débit vérifié, pUSD | Dépôt retenu, pUSD |
|---|---:|---:|---:|---:|
| brace227 | 120,000000 | 3,600000 | 123,600000 | 2 186,427015 |
| Thin-Disclaimer-Life | 871,295400 | 20,575100 | 891,870500 | 11 833,228666 |
| walletwallet8424 | 260,375000 | 6,509370 | 266,884370 | 3 906,988140 |
| VidenteRibeira | 3 379,405800 | 79,524780 | 3 458,930580 | 9 940,006803 |
| WenZhuanBuPei | 12 772,993300 | 285,196860 | 13 058,190160 | 15 926,884500 |
| OuldLm3alem | 581,093000 | 8,786150 | 589,879150 | 23 386,255984 |

Les dépôts de **brace227 et walletwallet8424** empruntent la même route intermédiaire USDC.e `0xf70d… → 0xb92f… → 0xc8a6… → contrat pUSD`, les 9 et 13 octobre. C’est un lien antérieur au signalement, dont la nature reste inconnue : service commun, bridge ou opérateur économique commun ne sont pas départagés. L’adresse zéro qui émet le pUSD n’est pas le financeur. Les quatre autres sources immédiates distinctes ne prouvent pas davantage leur indépendance en amont. ([Reçu brace227](https://polygonscan.com/tx/0x2a89597ebf1d83b5b76ceccab02924c28ca0ad8f6d208b2c42801a0925280a2c), [reçu walletwallet8424](https://polygonscan.com/tx/0xd6c102f7e3eed462f41e9d9eb96bee66d07b81ff0dec9ecd55e15f7aef83fa34), [mécanisme pUSD](https://docs.polymarket.com/concepts/pusd))

Les inventaires initiaux, transformations de tokens, ventes complètes, retraits, autres wallets et financeurs ultimes manquent. **Exposition nette, profit et contrôle commun restent inconnus.** Copie après publication, anticipation sportive publique, chance, automatisation, arbitrage ou couverture demeurent des explications concurrentes ; le corpus ne permet pas de les départager. ([Portée et limites](</Users/benjamindacunha/Projects/PolySentinel/research_notes/PolySentinel et le Ballon 2026/forensics.md>))

## Le prochain test exige des archives contemporaines complètes

Les capacités manquantes sont concrètes : pagination suivie jusqu’à une borne historique attestée, couverture maker et taker, conservation datée des statuts et liquidités, historique inter-marchés et inventaires, chronologie des informations publiques, puis rapprochement systématique des transferts et transformations. Le parseur de financement actuel ne retient que les transferts touchant le wallet cible : sur ces dépôts, il voit le mint pUSD mais masque la route USDC.e en amont. Cette limite a été démontrée par relecture hors ligne des mêmes reçus. Une route commune demande ensuite des preuves sur la fonction et le contrôle des intermédiaires. ([Collecte et lacunes](</Users/benjamindacunha/Projects/PolySentinel/research_notes/PolySentinel et le Ballon 2026/historical_coverage.md>), [complément hors ligne](</Users/benjamindacunha/Projects/PolySentinel/research_notes/PolySentinel et le Ballon 2026/forensics/ADDENDUM_OFFLINE.md>))

La renormalisation des bruts puis T1/T2 ont été **reproduits à l’identique dans deux copies fraîches**. Les lanceurs antérieurs ont refusé explicitement les opérations non permises ; leurs traces sont conservées. Les audits ont vérifié le périmètre descriptif et les protections contre les fuites ; le complément d’isolation des dépendances ne rend pas l’environnement entièrement hermétique, notamment pour `httpx`, et ne certifie aucune nouvelle acquisition réseau. ([Reproduction](/Users/benjamindacunha/Projects/PolySentinel/studies/ballon_2026_20261030/audit/REPRODUCTION.md), [audits](/Users/benjamindacunha/Projects/PolySentinel/studies/ballon_2026_20261030/audit/AUDIT_STATUS.md))

Le registre conserve **37 exécutions de fixtures synthétiques sur cinq passages** : 27 avant gel, puis un contrôle complémentaire exploratoire du candidat moyen et neuf fixtures après résultats. Ce ne sont pas 37 cas indépendants. Sur chaque graine 11, 29 et 47, les fixtures donnent zéro priorité sur trois wallets pour le nul, zéro sur un pour le moyen, trois sur trois pour le fort ; le contrôle moyen complémentaire vérifie aussi un candidat de score 1 sans priorité. [Contrôles](/Users/benjamindacunha/Projects/PolySentinel/studies/ballon_2026_20261030/controles/CONTROLES.md). Les données réelles comptent **29 comparaisons descriptives enregistrées** : six prévues T1/T2, dix-huit exploratoires T3/T3b et cinq diagnostics exploratoires de distributions ajoutés tardivement au registre après détection de leur omission par les audits. Ces derniers décrivent les regroupements par wallet, événement, marché, hash de transaction et identifiant ; ils n’ajoutent aucun test de détection. L’effectif indépendant reste **une affaire** ; aucune p-value, puissance empirique ou généralisation de performance n’en découle. ([Registre complet](/Users/benjamindacunha/Projects/PolySentinel/studies/ballon_2026_20261030/registre/tests.jsonl))

## Conclusion

Cette affaire fournit un cas documenté pour tester la conservation et la reconstruction des preuves. Elle ne permet pas de répondre « oui, PolySentinel les aurait trouvés ». Le dispositif installé était trop tardif ; sa capacité hypothétique antérieure demeure inconnue. Une validation utile devra mesurer prospectivement les alertes sur une population suivie indépendamment des comptes médiatisés, avec données contemporaines et adjudication explicite des inconnus.

Non établi : capital total, profits, bénéficiaires économiques, information privilégiée et performance de détection. La remise en service et le stockage font l’objet d’un bilan opérationnel séparé.

## Deviations and data notes

- L'aveuglement personnel complet n'a pas été atteint (titres de presse et noms de fichiers vus) ; sélection lexicale et seuils du détecteur inchangés, labels rapprochés après scellement de T1.
- Les 100 requêtes autorisées n'ont pas achevé trois flux : aucun remplacement par une métrique de performance sur le sous-échantillon.
- Après T1, des copies des dépendances et trois lanceurs successifs ont été ajoutés au gel sans modifier les versions initiales. Le troisième permet la renormalisation hors réseau ; l'environnement externe reste partiellement non hermétique.
- Le contrôle exploratoire explicite du candidat moyen et une répétition de neuf fixtures ont été ajoutés après résultats. Les 27 exécutions initiales restent distinctes ; aucun contrôle synthétique ne mesure la puissance empirique.
- Le premier lancement d'auditeurs avait hérité de résultats ; il a été abandonné et remplacé par des auditeurs neufs sans historique. Les audits aveugles revendiqués concernent uniquement ces remplaçants.
- Un auditeur avait calculé cinq diagnostics structurels exploratoires hors registre. Leur script et sortie sont désormais conservés, et leur enregistrement tardif est explicite ; cette régularisation ne les rend pas prévus au plan.
- T3 et T3b sont des analyses forensiques exploratoires après labels, inscrites séparément au registre ; elles n'ajoutent aucune détection au replay.

Chronologie et preuves : [audits](/Users/benjamindacunha/Projects/PolySentinel/studies/ballon_2026_20261030/audit/AUDIT_STATUS.md), [complément technique](/Users/benjamindacunha/Projects/PolySentinel/studies/ballon_2026_20261030/audit/DEPENDENCY_COMPLETION.md), [registre](/Users/benjamindacunha/Projects/PolySentinel/studies/ballon_2026_20261030/registre/tests.jsonl).
