# Capacité de détection de PolySentinel : résultats du 30 octobre 2026

## Réponse A

Cette étude de cas est **exploratoire et conditionnelle**. R0 est un profil structurel avant gel issu de code non gelé ; R3 est une comparaison exploratoire aux labels publics ajoutés après scellement. R1/R2/R3 suivent les choix fixés, sans constituer une validation confirmatoire externe.

**Le rejeu conditionnel aurait classé Thin-Disclaimer-Life prioritaire dès le 13 octobre. La capacité historique réelle reste NON_ESTIMABLE.** Les deux énoncés portent sur des objets différents.

Sous disponibilité immédiate des transactions et statut ouvert supposé, ce wallet franchit le seuil inchangé de 2 le **13 octobre à 18:50:49 UTC** sur l'événement 1105364, rang de compétition **1 parmi 74 paires wallet-événement** ayant un achat récent à ce tick. Son premier comportement apparaît le 13 octobre à 11:40:49. La concentration observée et le changement de taille des achats produisent deux familles distinctes. Avec les délais fixés de 60, 300, 900 secondes, la première priorité passe respectivement à 18:51:49, 18:55:49, 19:05:49, toujours le 13 octobre. Ce sont des heures de décision simulées, pas des heures d'émission observées en 2026.

Sur 11 étiquettes publiques, 6 correspondances exactes avec des alias actuels sont résolues ; ces 6 wallets sont présents et effectivement évalués dans le rejeu. Cinq ont au moins un comportement natif, un seul franchit le seuil conditionnel de priorité. Les 5 étiquettes non résolues restent inconnues, jamais absentes par défaut. Les 9 comptes de la liste initiale comprennent 5 résolus ; les 2 cas nommés ultérieurement comprennent 1 résolu. L’effectif indépendant externe de ce rapprochement est une affaire. La continuité des alias historiques n'est pas prouvée. **Ces comptes ne constituent pas une vérité terrain d'initiés.** Aucun taux de rappel, précision ou faux positifs n'est calculé.

Source de chaque cellule : [comparaison après scellement](derived/label_comparison.json), qui conserve tous les dossiers par paire et tous les délais. Le résumé wallet signifie « au moins un événement » ; la table primaire ci-dessous distingue les événements.

## Étendue et preuve d'aveuglement

Le noyau `exploratory-1.2` et la configuration sont copiés à l'identique, avec seuil de priorité 2 et paramètres natifs inchangés. Le constructeur du rejeu, lancé sans historique, n'a lu ni labels ni anciennes conclusions. Le coordinateur connaissait déjà l'affaire : cela ne constitue ni un aveuglement intégral de sa personne ni une nouvelle validation indépendante.

Le plan, le code, les données et contrôles ont été gelés le 30 octobre à 12:58:02 UTC (44 fichiers). Les sorties complètes R1/R2 ont été scellées le 30 octobre à 13:09:48.120290 UTC, avant importation des labels. Le sceau et les labels ont ensuite été ajoutés au gel prévu, sans changer code ni seuils : 47 fichiers, 1 ajout. Voir [verrou](PROTOCOL.lock), [sceau](derived/pre_label_seal.json), [contrôle d'import](controles/labels_import.md).

La strate contient 15 148 transactions et 1 301 wallets, sur 22 identités d'événements issues du catalogue ultérieur. Elle réutilise une collecte lexicale de famille d'événements, taker seulement, choisie après l'affaire. La fenêtre est [23 septembre 15:17:49, 23 octobre 15:17:49[ UTC. L'ancien rapport retenait 15 067 lignes avant le signalement avec une borne basse différente ; les 81 lignes supplémentaires sont antérieures à son ancienne borne, pas des résultats futurs ajoutés. Les 46 533 lignes sources se réconcilient en 15 148 retenues, 319 avant la fenêtre et 31 066 au cutoff ou après ; aucun doublon supprimé. Source : [manifeste](data/input_manifest.json).

Les entrées excluent noms de candidats, résultats, titres, alias, profils, liquidités actuelles et labels publics. Les IDs de marchés/événements reposent néanmoins sur une correspondance supposée stable du catalogue acquis ensuite. L'univers complet admissible au 23 octobre, ses statuts historiques et ses flux ne sont pas établis. Le schéma officiel et le probe global archivé montrent que les paramètres start/end ne bornent pas cette forme globale de l'API. Il n'a pas été fabriqué de catalogue exhaustif ni de curseur. Voir [acquisition](ACQUISITION_PLAN.md), [schéma](data/api_schema.json), [probe](data/global_probe_receipt.json).

Le contrôle strict conservant les vrais observed_at postérieurs au cutoff examine 0 paire et émet 0 dossier : cela prouve uniquement l'absence d'observations contemporaines dans ces entrées. Il ne mesure pas une sensibilité nulle. Aucun des délais simulés n'est un retard maximal garanti. M1 suppose ouverture et absence de publication bloquante ; cette hypothèse favorable n'est pas une borne supérieure démontrée. Source : `strict_actual_observation_replay` dans [R1](derived/replay.json.gz).

## Dénominateurs réellement évalués

Les rangs portent sur les achats récents effectivement examinés, avec égalités conservées. Un wallet seulement présent comme contexte n'obtient pas un score 0 ni un rang artificiel. Les premiers signaux proviennent des ticks réguliers de 60 secondes ; le snapshot final hors cadence est distinct.

| Délai hypothétique | Présents dans le fichier | Disponibles au cutoff | Wallets évalués au moins une fois | Avec comportement | Avec priorité conditionnelle |
|---:|---:|---:|---:|---:|---:|
| 0 | 1301 | 1301 | 1078 | 84 | 23 |
| 60 | 1301 | 1301 | 1078 | 84 | 23 |
| 300 | 1301 | 1301 | 1078 | 84 | 23 |
| 900 | 1301 | 1300 | 1077 | 84 | 23 |

Source : les compteurs de chaque scénario R1. Pour le délai 0, 23 wallets prioritaires conditionnels comprennent une correspondance avec les wallets publics résolus et 22 autres wallets non étiquetés. Ces 22 ne sont pas des faux positifs établis. L’effectif indépendant externe reste **une affaire**.

## Comparaison publique, par paire

| Alias actuel | Événement | Score maximal | Premier comportement UTC | Rang au premier comportement | Première priorité conditionnelle UTC | Rang à cette priorité | Raisons au score maximal |
|---|---|---:|---|---|---|---|---|
| Thin-Disclaimer-Life | 1105364 | 2 | 13/10 11:40:49 | 2 / 85 | 13/10 18:50:49 | 1 / 74 | event_concentration, wallet_size_shift |
| Thin-Disclaimer-Life | 1105213 | 0 | aucun dans ce scénario | aucun | aucun dans ce scénario | aucun | aucune famille pondérée |
| Thin-Disclaimer-Life | 1105369 | 0 | aucun dans ce scénario | aucun | aucun dans ce scénario | aucun | aucune famille pondérée |
| VidenteRibeira | 1105364 | 1 | 16/10 00:27:49 | 1 / 106 | aucun dans ce scénario | aucun | event_concentration, first_observed_large |
| cookedrice | identité non résolue | inconnu | inconnu | inconnu | inconnu | inconnu | aucun rapprochement supposé |
| WenZhuanBuPei | 1105364 | 1 | 18/10 20:16:49 | 1 / 126 | aucun dans ce scénario | aucun | event_concentration, first_observed_large |
| 0x86544e4dfde | identité non résolue | inconnu | inconnu | inconnu | inconnu | inconnu | aucun rapprochement supposé |
| brace227 | 1105364 | 1 | 16/10 19:27:49 | 1 / 134 | aucun dans ce scénario | aucun | event_concentration |
| brace227 | 1105185 | 0 | aucun dans ce scénario | aucun | aucun dans ce scénario | aucun | aucune famille pondérée |
| brace227 | 1105369 | 0 | aucun dans ce scénario | aucun | aucun dans ce scénario | aucun | aucune famille pondérée |
| brace227 | 1189431 | 0 | aucun dans ce scénario | aucun | aucun dans ce scénario | aucun | aucune famille pondérée |
| brace227 | 1218179 | 0 | aucun dans ce scénario | aucun | aucun dans ce scénario | aucun | aucune famille pondérée |
| walletwallet8424 | 1105364 | 0 | aucun dans ce scénario | aucun | aucun dans ce scénario | aucun | aucune famille pondérée |
| Zoomman17 | identité non résolue | inconnu | inconnu | inconnu | inconnu | inconnu | aucun rapprochement supposé |
| kraben006 | identité non résolue | inconnu | inconnu | inconnu | inconnu | inconnu | aucun rapprochement supposé |
| OuldLm3alem | 1218179 | 1 | 22/10 18:51:49 | 2 / 355 | aucun dans ce scénario | aucun | event_concentration |
| OuldLm3alem | 1105185 | 0 | aucun dans ce scénario | aucun | aucun dans ce scénario | aucun | aucune famille pondérée |
| OuldLm3alem | 1105364 | 0 | 23/10 10:53:49 | 16 / 387 | aucun dans ce scénario | aucun | aucune famille pondérée |
| OuldLm3alem | 1218178 | 0 | 23/10 10:53:49 | 16 / 387 | aucun dans ce scénario | aucun | aucune famille pondérée |
| OuldLm3alem | 1225367 | 0 | 23/10 10:54:49 | 16 / 390 | aucun dans ce scénario | aucun | aucune famille pondérée |
| OuldLm3alem | 1225368 | 0 | 23/10 10:53:49 | 16 / 387 | aucun dans ce scénario | aucun | aucune famille pondérée |
| 0xdd97e6 | identité non résolue | inconnu | inconnu | inconnu | inconnu | inconnu | aucun rapprochement supposé |

Table sans sélection du meilleur événement après coup : toutes les paires des wallets publics résolus sont conservées, délai 0. « Aucun » signifie aucun signal dans ce scénario et ce corpus, pas une absence d'activité ailleurs. Les dates des autres scénarios sont dans R3.

VidenteRibeira et WenZhuanBuPei cumulent premier gros achat observé et concentration, mais ces deux règles appartiennent à la même famille exposure : score 1, sous le seuil 2. brace227 reste également à 1 ; walletwallet8424 à 0. OuldLm3alem atteint 1 sur 1218179 ; certaines annotations de récurrence sur les autres événements ont un poids 0 parce que l'indépendance des événements n'est pas établie. Ni un premier trade retrouvé ni une concentration dans cette strate ne prouvent création récente ou information privée.

## Priorités de toute la strate, sans filtrage par les noms publics

La table suivante conserve toutes les paires ayant franchi le seuil dans le scénario délai 0. L'ordre reprend celui de R1 : score maximal décroissant puis identités stables, avec égalités non départagées statistiquement. Le score maximal et ses raisons peuvent être postérieurs à la première priorité ; ils ne sont pas attribués artificiellement à son instant. Les autres scénarios et toutes les unités sans signal sont conservés dans R1.

| Wallet | Événement | Score maximal de période | Première priorité UTC | Rang à ce tick | Raisons au score maximal |
|---|---|---:|---|---|---|
| 0x1ee9a5fc09665909c0cce297c581703bfbb9197f | 1200407 | 3 | 17/10 23:52:49 | 1 / 199 | event_concentration, linked_market_rotation, wallet_size_shift |
| 0x1387d145aaf01f6e33b66525dda6e1f51f6955f8 | 1218178 | 2 | 20/10 16:36:49 | 2 / 497 | event_concentration, linked_market_rotation |
| 0x1ca36d811f2928cd021992916f1a791df50fd80f | 1200407 | 2 | 18/10 02:34:49 | 1 / 179 | event_concentration, linked_market_rotation |
| 0x36901eb0f21519cc9055662a6d2483e96da1e16f | 1218178 | 2 | 22/10 19:24:49 | 1 / 374 | event_concentration, wallet_size_shift |
| 0x36901eb0f21519cc9055662a6d2483e96da1e16f | 811117 | 2 | 21/10 15:03:49 | 1 / 398 | linked_market_rotation, synchronized_entries |
| 0x43372356634781eea88d61bbdd7824cdce958882 | 1189431 | 2 | 18/10 02:02:49 | 1 / 185 | event_concentration, linked_market_rotation |
| 0x5061b324b41e1493c540b13ca78e915a579e1b03 | 1189431 | 2 | 16/10 23:36:49 | 1 / 174 | event_concentration, linked_market_rotation |
| 0x5a218c7ad04135830a45c41aaed7294df7809318 | 811117 | 2 | 21/10 14:06:49 | 1 / 389 | linked_market_rotation, synchronized_entries |
| 0x5cd5c8d7a17c78d7389d8b87b611aed83322ac33 | 1105185 | 2 | 20/10 16:06:49 | 2 / 520 | event_concentration, linked_market_rotation |
| 0x6a678ca367432d28cb6aa55bb6bc57d8f53bdf6f | 1105185 | 2 | 11/10 10:13:49 | 1 / 78 | event_concentration, linked_market_rotation |
| 0x6a678ca367432d28cb6aa55bb6bc57d8f53bdf6f | 811117 | 2 | 19/10 16:13:49 | 1 / 236 | event_concentration, wallet_size_shift |
| 0x7789957157a13aa3610e26d61ef8f99317b7a280 | 811117 | 2 | 23/10 02:58:49 | 1 / 372 | event_concentration, linked_market_rotation |
| 0x7cbefea2f57bf129ea3446d53397b9520747c4b7 | 1218179 | 2 | 20/10 21:30:49 | 1 / 398 | event_concentration, linked_market_rotation |
| 0x818cc53babe10f79c21e21d73eac20a6a447a500 | 811117 | 2 | 21/10 12:30:49 | 1 / 344 | event_concentration, linked_market_rotation |
| 0x8d3319c51520518ad01f6744486ceea29f376f5b | 1105364 | 2 | 13/10 18:50:49 | 1 / 74 | event_concentration, wallet_size_shift |
| 0xa278b41b5afda5d18da683eb7f851a7b2dc13369 | 811117 | 2 | 21/10 14:48:49 | 1 / 392 | linked_market_rotation, synchronized_entries |
| 0xb0c85813a7a4428f1139ff91d3118a92c391fe7f | 1218178 | 2 | 20/10 16:03:49 | 2 / 521 | event_concentration, linked_market_rotation |
| 0xb10047d6a254b2ebb306d7a7d13bf59171ab6461 | 1200407 | 2 | 23/10 04:50:49 | 1 / 378 | event_concentration, repeated_large_entries, synchronized_entries |
| 0xb10047d6a254b2ebb306d7a7d13bf59171ab6461 | 994444 | 2 | 08/10 15:30:49 | 1 / 52 | event_concentration, first_observed_large, synchronized_entries |
| 0xb1ca909e848cc24ec4e220ce1c453bc290c51705 | 1200407 | 2 | 18/10 01:10:49 | 1 / 187 | event_concentration, linked_market_rotation |
| 0xd218e474776403a330142299f7796e8ba32eb5c9 | 1105185 | 2 | 10/10 12:39:49 | 1 / 48 | event_concentration, linked_market_rotation |
| 0xd218e474776403a330142299f7796e8ba32eb5c9 | 811117 | 2 | 19/10 18:49:49 | 1 / 318 | event_concentration, linked_market_rotation |
| 0xd5a817163ea5acd551ee9201efbcf8b709bf9793 | 1105185 | 2 | 01/10 17:29:49 | 1 / 69 | event_concentration, linked_market_rotation |
| 0xd5a817163ea5acd551ee9201efbcf8b709bf9793 | 1105364 | 2 | 13/10 15:33:49 | 1 / 76 | event_concentration, wallet_size_shift |
| 0xd6b6f6924341b00626e603240f799644d4b6342b | 811117 | 2 | 23/10 05:34:49 | 1 / 376 | event_concentration, wallet_size_shift |
| 0xde44891c8d31b14701892ad932c36429b05f751f | 811117 | 2 | 21/10 10:48:49 | 1 / 348 | event_concentration, linked_market_rotation |
| 0xeed7c2e6c4e998fd50098b66144ee8dff01d16b2 | 1105185 | 2 | 01/10 23:19:49 | 1 / 59 | event_concentration, linked_market_rotation |
| 0xf797d4d1c038d1eb0593edae0e66bf8e4b2e0bf2 | 1105185 | 2 | 13/10 11:03:49 | 1 / 82 | event_concentration, linked_market_rotation |

## Huit dimensions et références internes

R2 décrit le snapshot 23 octobre 15:17:48 UTC, délai 0, fenêtre native récente de 24 heures : **413 paires, 253 wallets ; une affaire indépendante externe**. Ce n'est pas une réévaluation des seuls comptes nommés ni une description de leurs positions complètes. Les synthèses suivantes sont des sommes des booléens déjà enregistrés, sans nouveau seuil. Source : [R2](derived/features.json.gz).

| Dimension demandée | Ce qui est mesuré et ce qui reste inconnu |
|---|---|
| Création récente | Date réelle inconnue ; ancienneté depuis le premier trade du corpus seulement, borne inférieure de l'ancienneté réelle. |
| Premier pari après création | Inconnu : ni création fiable ni premier pari global démontré. |
| Concentration | 9 sur 413 paires satisfont la règle native de concentration des BUY nominaux observés, pas de l'ensemble du portefeuille. |
| Convergence | 3 sur 413 paires ont le signal natif d'achats synchronisés. Des achats ne prouvent pas une position nette commune. |
| Montant / liquidité | Inconnu sans instantané historique frais de liquidité. Taille×prix donne un nominal partiel, pas un coût complet incluant frais. |
| Issues précises cohérentes | Nombre de tokens/marchés achetés conservé ; cohérence logique et positions nettes inconnues sans règles datées et inventaires. |
| Financement partagé ou synchronisé | Inconnu à l'échelle de cet univers aveugle ; aucune information ciblée après labels injectée. |
| Opérations avant information publique | Toutes précèdent ce signalement précis ; première information publique pertinente et absence d'autres publications inconnues. |

La conjonction concentration ET synchronie concerne 1 sur 413 paires ; elle n'ajoute aucun point au score de production. Les 413 concentrations observées sont calculables. 384 paires ont au moins un pair interne et 29 n'en ont aucun : leurs fréquences de référence restent inconnues. L'appariement utilise même événement, même jour UTC du dernier BUY et tranche fixe 0,2 du prix moyen pondéré par les parts. Les effectifs, médianes/étendues et fréquences des pairs sont conservés pour chaque ligne. Ce ne sont pas des témoins innocents prouvés ; activité, réseau, liquidité et historique extérieur ne sont pas contrôlés. Aucun contraste causal ni test de supériorité n'est estimé.

Expertise, information sportive publique, chance, suivi d'autres traders, automatisation, arbitrage/couverture, service de financement commun et censure de collecte restent des explications concurrentes. Ces observations ne les départagent pas.

Le complément forensique de l'étude précédente reste **exploratoire, sélectionné après labels**, séparé du test aveugle. Il a réconcilié un trade et un dépôt par adresse et identifié une route USDC.e commune à brace227 et walletwallet8424, sans prouver un propriétaire commun. Il documente aussi la limite du parseur actuel, qui voit le mint pUSD sans remonter toute la route USDC.e. Aucun de ces éléments n'a modifié R1/R2. Les montants réconciliés concernent les seules opérations vérifiées ; inventaires, profit et financeurs ultimes restent inconnus. Voir [résultats forensiques antérieurs](../ballon_2026_20261030/results.md).

## Multiplicité, puissance et reproduction

Le registre final contient 4 calculs réels : R0 structurel 1, R1 chronologique 36 456 007, R2 dimensions 3 717, R3 labels 44 ; total 36 459 769 comparaisons comptables. Le seuil Bonferroni conservateur est 0,05 / 36 459 769, environ 1,37×10⁻⁹. **Aucune p-value n'est définie : ni significativité ni performance ne découlent de ce nombre.** La dépendance entre ticks, wallets, événements et scénarios ne crée pas de nouveaux cas indépendants. n effectif externe=1 affaire. Voir [registre](registre/tests.jsonl) et [audit](audit/PHASE5.md).

Les contrôles synthétiques comprennent trois fixtures déterministes nul/moyen/fort et des graines d'équivalence des implémentations. Ils ne mesurent ni puissance empirique, ni précision, ni rappel, ni taux de faux positifs. Les 256 contrôles ponctuels du noyau complet pendant le rejeu (64 par délai) vérifient le cache, pas une performance financière ou prédictive.

Après deux premières tentatives interrompues par le plancher disque, deux nouvelles invocations indépendantes du reproducteur officiel ont chacune créé une copie fraîche avec HOME isolé. R1, R2 et R3 sont **identiques octet pour octet dans les deux copies**, aucune clé ignorée, et l'étude d'origine n'a pas été écrite. Voir [reproduction 1](../../evidence/detection_prospective_20261030/repro_3.log), [reproduction 2](../../evidence/detection_prospective_20261030/repro_4.log).

## Réponse B et capacités restantes

**Émission et conservation prospectives locales démontrées sur de vraies nouvelles observations d'alertes.** Le sidecar activé exclut les observations historiques, tout en admettant de nouvelles observations de dossiers existants, conserve contenu/provenance/lacunes, heure de lecture puis émission après fsync et scellement local. Son premier lot conserve deux observations le 30 octobre à 12:34:37 UTC sur « Fed Decision in December? », avant la réunion annoncée pour les 8–9 décembre. La première publication effective future de la décision n'est pas encore documentée : aucune réussite prédictive n'est annoncée. Voir [preuve opérationnelle et limites](../../evidence/detection_prospective_20261030/OPERATIONAL_REPORT.md), [premier reçu](../../evidence/prospective_eval/00000001/receipt.json).

Le lancement périodique est actif toutes les 60 secondes. Un manque d'espace a effectivement provoqué un refus, puis les captures ont repris quand l'espace est revenu. Le service source et ses seuils restent inchangés. Budget 20 Mo, aucune purge, aucun accroissement massif de collecte. La chaîne locale et les fichiers uchg protègent contre des modifications accidentelles ; le propriétaire peut lever ces protections. Horloge locale, pas d'ancrage tiers ni protection contre rollback coordonné. La collecte peut s'interrompre au plancher disque ou au plafond ; la réception humaine n'est pas démontrée.

Pour transformer A en évaluation historique globale, il manque : catalogue d'admissibilité daté ; transactions maker et taker avec couverture et publication attestées ; historiques globaux et inventaires des wallets ; création des comptes ; statuts/liquidités/règles de résolution datés ; chronologie sourcée des informations publiques ; parcours des transformations et financements en amont. Leur ajout doit être évalué sous un nouveau protocole, sans régler des seuils sur cette affaire. Pour B, il faut maintenant documenter les annonces publiques futures et comparer leurs heures aux émissions conservées, ainsi qu'un budget de conservation durable ; les résultats de cette campagne ne sont pas encore connus.

Aucun intervalle empirique honnête n'est identifiable pour l'historique réel. Pour les 6 adresses résolues présentes, 0 à 6 wallets alertés au moins une fois est seulement un intervalle logique compatible avec les lacunes d'observabilité, d'admissibilité et d'entrées ; ce n'est pas un intervalle de confiance. Le résultat 1 sous M1 n'en est pas une borne garantie, et les cinq identités non résolues restent hors de ce comptage.

## Deviations and data notes

- L’ajout documentaire planifié de trois fichiers (labels, sceau, contrôle d’import) a eu lieu après R1/R2. Il conserve le code et la méthode gelés ; R3 reste exploratoire.
- R0 a mesuré la taille et le profil de charge avant gel. Il est enregistré comme tel. Aucun rejeu de détection n'a précédé le gel ; ne pas affirmer qu'aucun calcul réel préalable n'existe.
- L'implémenteur est aveugle aux labels ; le coordinateur connaissait le précédent rapport et la strate est choisie après l'affaire. A1 n'est donc pas une validation externe sur l'univers complet.
- Le libellé du plan « fixtures nul/moyen/fort plusieurs graines » est plus large que ce qui a été réalisé : trois fixtures déterministes et graines distinctes d'équivalence. La contrelecture indépendante le relève ; aucune puissance statistique n'est revendiquée et le plan gelé n'est pas réécrit.
- Deux reproductions en copies fraîches ont été interrompues par le plancher de 10,5 Go avant la comparaison finale : [premier arrêt](../../evidence/detection_prospective_20261030/repro_1.log), [second arrêt](../../evidence/detection_prospective_20261030/repro_2.log). Les journaux sont conservés. Il ne s’agit pas de divergences numériques constatées. Les deux nouvelles tentatives complètes ont ensuite reproduit les trois sorties exactement.
- Une tentative de contrôle synthétique a été refusée sous 10,5 Go ; elle est enregistrée, pas comptée comme PASS. Après retour spontané de l'espace, les contrôles finaux ont passé. Aucune suppression supplémentaire n'a été effectuée.
- Les résumés wallet R3 signifient au moins un événement ; toutes les paires et les scores 0 restent publiés. Les maximums de période ne sont pas des classements disponibles dès le début de la fenêtre.
- Les contrôles de code et le volume de transactions ne sont jamais utilisés comme preuve de performance. Aucun initié prouvé, aucun vrai négatif, aucune précision/rappel/FPR véritable n'est disponible.

