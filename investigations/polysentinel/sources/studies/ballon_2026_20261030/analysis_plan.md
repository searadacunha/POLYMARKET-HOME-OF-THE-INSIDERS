# PolySentinel et le Ballon d'Or 2026 : faisabilité rétrospective

Plan du 30 octobre 2026, écrit avant calcul des sorties du détecteur et rapprochement des comptes publiés. Question : le système existant aurait-il pu alerter avant la révélation publique, puis avant la cérémonie ? Il s'agit d'un audit descriptif d'un cas choisi après sa médiatisation, pas d'une validation statistique.

## Données et population

1. Disponibilité locale : requêtes courtes, en lecture seule et autocommit, dans les références historiques de la base vivante. Le premier cycle et les comptes de lignes avant les deux coupures sont conservés. Le code refuse de rejouer un jeu vide si des lignes historiques existent.
2. Reconstruction indépendante des comptes publiés : recherche lexicale des événements dont le titre contient Ballon et 2026, trois requêtes Gamma, puis rafraîchissement des événements et pagination tournante des trades Data API v2. Toutes les issues sont conservées, sans sélection des vainqueurs. Le périmètre inclut les autres récompenses de la cérémonie ; ce n'est pas uniquement le Ballon masculin.
3. Bornes d'acquisition : 100 requêtes, réponses de 8 Mo au plus, 150 Mo de réponses au plus ; acquisition de transactions vers les trente jours précédant la cérémonie, interruption explicite en cas de plafond. Une recherche épuisée n'établit pas l'exhaustivité des marchés. Flux taker seulement : pas un recensement de tous les makers.
4. Les réponses brutes, requêtes, horodatages d'acquisition, erreurs, pages vides, 429, continuations non terminées et lignes rejetées sont conservés. Aucun échec ne vaut zéro transaction.

## Unité, dénominateurs, dépendance

Transaction API identifiée par signature économique et occurrence, wallet public, paire wallet/événement. Les lignes identiques avec même ID sont dédupliquées ; une contradiction économique est une erreur. Les montants sont size × price, en décimal, séparés entre achats et ventes. Ce sont des affirmations API non rapprochées intégralement sur chaîne. Une même transaction peut comporter plusieurs fills. Un seul événement médiatique indépendant ; les wallets, marchés de placement et résultats sont dépendants. Aucune inférence de contrôle commun.

## Horloges et coupures

- Primaire : strictement avant 2026-10-23 15:17:49 UTC, horodatage du premier signalement primaire retrouvé par le chercheur séparé. C'est une borne attestée, pas une preuve d'absence de rumeur antérieure.
- Secondaire : strictement avant 2026-10-26 20:00:00 UTC, début annoncé de la cérémonie selon l'UEFA. Ce n'est pas l'heure exacte d'annonce de chaque rang.
- Le replay fidèle exige timestamp ET observed_at strictement avant la coupure. Jamais d'antidatage d'une acquisition du 30 octobre. Les statuts ouverts/résolus, liquidités, positions et résultats actuels ne deviennent pas des caractéristiques historiques.
- Le grand livre descriptif utilise seulement timestamp, avec une borne commune au 26 septembre 2026 à 20:00 UTC (trente jours avant la cérémonie) pour les deux coupures. Il décrit des transactions retrouvées ensuite et ne prouve pas qu'elles auraient été collectées à temps. Les lignes plus anciennes rapportées dans la dernière page sont conservées mais exclues du grand livre.

## Détecteur et features

Copie exacte du signals.py actif, version exploratory-1.2, et config.json. Aucun changement de seuil, famille, fenêtre ou groupement. Le détecteur est exécuté sur les seules entrées locales réellement disponibles aux coupures. Si cet ensemble est vide, zéro sortie décrit uniquement ce replay vide : ce n'est pas un score de performance.

La reconstruction API est évaluée pour sa faisabilité : sans snapshots historiques contemporains certifiés, couverture de collecte et histoires inter-marchés des wallets, aucun classement, première alerte ou taux contrefactuel ne sera fabriqué. Le code doit rendre NON ESTIMABLE. La présence de données historiques nouvelles n'autorise pas à forcer active=True, à antidater observed_at ni à remplacer les métadonnées par leur état final.

## Labels et connaissance des résultats

Un chercheur séparé établit les comptes expressément signalés dans les sources primaires et secondaires, leurs dates et leurs correspondances exactes vers des wallets publics. Liste incomplète et pseudonymes ambigus restent explicitement incomplets/ambigus. « Signalé publiquement » n'est pas « initié ». Les comptes non signalés ne sont pas des vrais négatifs.

Les sorties de détection et leur empreinte sont fixées avant lecture du tableau des labels. Limite de l'aveuglement : le coordinateur a vu des titres de recherche révélant le gagnant et, lors de la reprise après panne, des noms de fichiers de profils. Aucun aveuglement intégral de l'analyste n'est revendiqué. Le code et les seuils préexistent au cas ; sélection des marchés lexicale, données du détecteur séparées des labels.

## Calculs déclarés

T1 : un audit de faisabilité à deux coupures, replay fidèle et tableaux de flux descriptifs, tous enregistrés dans le registre. Deux comparaisons descriptives, aucun test de significativité. T2 : rapprochement documentaire des labels publics après fixation des sorties ; une comparaison par groupe de sources et par coupure, toutes comptées dans le registre. Pas de train/validation/test : un cas rétrospectif, aucune optimisation. Pas de p, correction multiple ou Monte-Carlo pertinente ; aucun résultat statistiquement validé.

Après gel des sorties, rapprochement exact des wallets du grand livre aux labels publics. Si aucune performance n'est estimable, nombre repéré, rang, première alerte, faux positifs, précision et rappel restent non mesurables. On peut rapporter la présence documentaire de wallets dans les transactions reconstituées, avec numérateur/dénominateur exact, sans l'appeler détection.

Financements, positions et capital réellement engagé : distinguer revendications publiques, flux API observés et preuves on-chain. Faute d'historique complet de transferts, splits/merges/conversions, inventaire initial, frais et recettes, aucune exposition nette réelle ni common ownership. Les explications publiques, copie, expertise, automatisation, arbitrage et couverture restent ouvertes.

## Contrôles avant gel

Trois graines (11,29,47), scénarios nul (petits achats), moyen (un gros achat : candidat sans priorité), fort (trois wallets synchronisés : priorités), exclusion des observations futures, doublons et contradictions, verdict final et métriques non estimables. C'est une table de sensibilité synthétique de neuf fixtures, pas une puissance empirique sur l'affaire. Rapport controles/CONTROLES.md et synthetic.json.

## Verdict et limites

NOT_DEPLOYED_THEN_AND_COUNTERFACTUAL_NOT_ESTIMABLE si premier cycle après les deux coupures, aucune ligne locale avant les coupures et aucune reconstruction point-in-time certifiée. Le code lève une erreur si les préconditions locales ne sont pas remplies. Aucun changement de méthode après résultat ; autre analyse seulement via nouvel ajout déclaré et amendement décidé par Benjamin.

Ce verdict ne démontre pas que les motifs économiques sont indétectables. Il constate l'absence de surveillance installée à l'époque et l'impossibilité d'évaluer honnêtement une performance historique avec les preuves réunies. Les capacités manquantes seront précisément reliées au code et aux lacunes de collecte.

## Amendements

Aucun au gel. Collecteur amélioré avant gel après audit de pagination et reprise ; première acquisition conservée. Aucun fichier d'une étude antérieure modifié.
