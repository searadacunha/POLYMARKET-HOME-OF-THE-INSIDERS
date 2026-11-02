# Capacité de détection, protocole distinct du 30 octobre 2026

## Question et statut

Mission de Benjamin : tester le détecteur inchangé avant le signalement du 23 octobre, comparer les classements scellés aux labels seulement ensuite, examiner huit dimensions et préparer une évaluation prospective. Cette nouvelle étude ne modifie aucun fichier ni verdict de l'étude ballon_2026_20261030. Le coordinateur connaît ses résultats et les comptes déjà publiés ; un implémenteur neuf sans historique écrit le rejeu sans lire ces labels, les résultats antérieurs ni les données avant contrôle de la méthode. Ce dispositif ne constitue pas un nouvel échantillon indépendant ni un aveuglement personnel intégral du coordinateur.

## Estimands et populations

A0 : capacité historique sur tout l'univers de marchés admissibles. Pour la mesurer il faudrait un catalogue et des statuts datés, la couverture de transactions et leurs délais de diffusion. La documentation Data API v2 et un probe global prévus dans ACQUISITION_PLAN.md montrent que start/end ne bornent pas le flux global. Ne pas fabriquer un curseur, un univers exhaustif ou un groupe de non-initiés. A0 reste NON_ESTIMABLE si ces informations ne sont pas établies.

A1 : étude de cas conditionnelle sur toutes les transactions de la collecte lexicale antérieure présentes dans la fenêtre, sans filtre d'adresse, de vainqueur, de montant ou de signal. Cette strate est censurée, taker seulement, sélectionnée par famille d'événements. Elle ne donne pas la concentration totale des wallets. Ne pas y mélanger le flux global filtré par taille du service. L'identité marché/événement issue du catalogue ultérieur est une hypothèse de correspondance stable, pas une preuve de référencement historique. Tous les zéros et inconnus restent dans les dénominateurs.

Fenêtre d'entrée : [1790176669,1792768669), soit 30 jours avant le 23 octobre 2026 15:17:49 UTC. Aucun résultat, titre, alias, profil, résolution ou liquidité actuels dans les entrées de détection. Prix = prix exécuté rapporté par l'API, jamais haut de graphique. Taille fois prix = achat nominal partiel, pas capital ou profit. Observed_at réel conservé.

Unité : wallet × événement, avec au moins un achat dans la fenêtre récente native. Rapporter aussi les wallets simplement présents, ceux effectivement examinés et ceux avec comportement retenu. L'effectif indépendant externe est une affaire ; événements du même trophée et wallets potentiellement dépendants ne sont pas des répétitions indépendantes.

## Détecteur et scénarios fixés avant calcul

Copie exacte de signals.py version exploratory-1.2 et de config.json. Seuils inchangés : large_nominal=1000, minimum_baseline=20, candidate_score=2, fenêtre de signal native 86400s, synchronie native 90s/3 wallets distincts/nominal minimal250, concentration native0,8. Aucun réglage après résultat. La sélection des 50000 trades les plus récents et l'historique wallet fourni suivent le caller existant, mais ne reconstituent pas le calendrier de collecte original.

Rejeu strict : le vrai observed_at postérieur au cutoff interdit de prétendre que ces lignes ont été observées alors. Un résultat vide n'est pas une mesure de sensibilité.

Simulations : disponibilité hypothétique timestamp + délai uniforme parmi {0,60,300,900}s. Disponibilité hypothétique calculée séparément ; l'adaptateur fournit cette valeur au paramètre observed_at en mémoire uniquement et n'altère jamais la source. Aucune de ces hypothèses n'est un délai maximal garanti. Le calendrier de décisions est toutes les60s depuis la borne basse ; une optimisation peut sauter seulement les ticks où ni arrivée ni expiration de la fenêtre ne modifie les règles, avec contrôle d'équivalence synthétique. Une seconde optimisation exacte peut conserver les cas des wallets non affectés par arrivée, expiration ou éviction de la limite. Elle réévalue via le noyau inchangé les wallets affectés et leur contexte de synchronie complet, anciens et nouveaux groupes compris. Sans métadonnées, la synchronie est le seul couplage entre wallets ; toute extension ultérieure des features invalide cette optimisation. Le noyau complet reste oracle : pour chacun des quatre délais, 64 ticks fixés par indices floor(i*43199/63), i=0..63, de la grille complète seront comparés (dossiers et diagnostics), avec refus en cas d'écart. Aucun échantillonnage du classement ; seuls les appels redondants sont évités. Les compteurs conceptuels restent ceux de la grille60s complète, pondérés sur les intervalles constants. Snapshot final cutoff-1 distinct des émissions sur cadence. Premier signal = premier tick où les données suffisantes sont disponibles, jamais timestamp minimal du groupe.

M0 : métadonnées historiques absentes, appeler le détecteur inchangé sans elles. Score comportemental calculable sur ce corpus, statut ouvert non prouvé, priorités mécaniques éventuellement bloquées. Le résultat réel demeure inconnu.

M1 : scénario favorable qui suppose les seuls événements/marchés présents ouverts et sans publication antérieure bloquante. Aucun chiffre de liquidité, date d'échéance, tag ou indépendance inventé. Le score est celui de M0 ; le passage du gate de priorité suit exactement bool(signals) et score>=2, équivalence contrôlée sur fixtures avec stubs active=True. Ce scénario n'est ni une borne supérieure garantie ni une preuve d'alerte réelle.

Conserver par scénario les unités évaluées, premiers signaux, premiers gates de priorité, rang au déclenchement, meilleur score/rang observés, classement au dernier tick et snapshot final. Rang de compétition sur score parmi les unités ayant un BUY récent effectivement examiné (égalité conservée), ID uniquement pour ordre stable. Les unités de contexte restent présentes sans score ni rang attribué par défaut. Distinguer rang wallet-événement et classement global des wallets par meilleur score ; les labels seront comparés au premier sans sélectionner le meilleur événement après coup sans le dire.

## Huit dimensions, témoins et combinaison

Évaluation descriptive séparée sous hypothèse de délai0 au snapshot final cutoff-1, sur toutes les unités wallet-événement ayant un BUY récent (24h). Rapport de couverture pour les autres wallets. Aucun label dans ces calculs.

1. Création récente : inconnue sans preuve de création de compte. Fournir seulement ancienneté depuis premier trade du corpus, borne inférieure d'ancienneté réelle, sans convertir en compte neuf.
2. Délai création→premier pari : inconnu ; aucun remplacement par premier achat retrouvé.
3. Concentration : somme des BUY nominaux récents sur événement / tous BUY nominaux récents observés du wallet, même strate. Famille native exposure, seuil0,8 et minimum1000. Inconnue pour la concentration de portefeuille complète.
4. Convergence : native synchronized_entries (même token/marché/événement,90s,3wallets,250 minimum). Achats convergents, pas positions prouvées ni propriété commune.
5. Montant/liquidité : inconnu sans liquide historique fraîche avant opération ; aucun proxy de volume présenté comme liquidité.
6. Issues précises cohérentes : inconnue sans règles de résolution datées et inventaire complet ; décrire seulement nombre de tokens/marchés distincts achetés. Ne pas assimiler plusieurs marchés Gamma à des issues logiquement cohérentes.
7. Financement commun/synchronisé : inconnu à l'échelle de l'univers évalué ; ne pas réutiliser l'enquête ciblée post-labels comme feature. Aucun propriétaire commun inféré.
8. Antériorité : tous les achats retenus précèdent le cutoff documenté ; cela ne prouve pas l'absence d'autres publications. Délai à cette publication précise peut être décrit, pas un signal discriminant interne ni l'annonce première de tous les événements.

Témoins internes non étiquetés : pour chaque unité au snapshot final, autres wallets du même événement, même jour UTC du dernier BUY, même tranche fixe de largeur0,2 du prix moyen pondéré par les parts BUY. Tous ont le même filtre de source et la même fenêtre ; ne pas apparier sur concentration, synchronie ou score. Rapport effectif des pairs et effectif à concentration calculable (prix nul conservé comme inconnu), médiane/étendue de concentration et fréquence descriptive de synchronie, inconnues si aucun pair. Liquidité, âge réel, réseau et historique hors corpus empêchent de qualifier ces groupes de parfaitement comparables. Conserver toutes les unités, pas seulement les dossiers émis. Pas de p-value ni d'inférence d'initiés à partir de ces témoins dépendants.

Combinaison : indicateur descriptif concentration ET synchronie, sans nouveau score ni seuil ; le score de production reste séparé. Aucun ajout des dimensions inconnues comme zéro ou comme preuve négative. Expertise, information publique, automatisation, copie, arbitrage/couverture et censure restent des explications concurrentes.

## Registre, multiplicité et contrôles

Chaque calcul réel est journalisé via registre.py après sortie : R1 scénario/chrono/classifications et un contrôle strict des observations réelles, R2 huit dimensions+combinaison sur toutes unités et comparateurs, R3 comparaison post-scellement labels. Le nombre de comparaisons R1 compte toutes les unités effectivement examinées à tous les ticks et scénarios, pas seulement huit scénarios nominaux ; R2=9 fois nombre d'unités, R3=nombre de labels fois quatre délais. Les contrôles synthétiques sont à part. Compteur officiel Bonferroni0,05/N conservateur sur toutes ces comparaisons ; aucune p-value n'est définie ici, donc aucune significativité, précision, rappel ou faux positif véritable annoncé. Si une inférence ultérieure est envisagée, elle exige nouveau protocole et modèle nul tenant compte des grappes. Toutes les reproductions identiques pour vérification ne sont pas des hypothèses nouvelles.

Avant gel : fixtures nul/moyen/fort plusieurs graines, exclusion future, doublon contradictoire, comptage des zéros, synchronie après dernière transaction, équivalence ticks sautés/ticks complets et M1/stubs, effets du délai, contrôle des comparateurs. Gel de plan/code/vendor/données exactes/config/contrôles puis audits aveugles séparés, reproduction deux copies, deux audits des conclusions. Aucun fichier de l'étude précédente modifié.

## Labels et bornes d'interprétation

Sceller SHA des classements et matrices avant d'ajouter la table de labels déjà publiée. Implémenteur du rejeu ne lit pas ces labels. Comparaison explicite par label résolu ou non : présent, réellement évalué, comportement, gate de priorité conditionnel, émission réelle inconnue, rang/date et raisons. Alias actuels ne garantissent pas identité historique ; absences dans corpus incomplet ne sont pas faux négatifs.

Si données manquantes empêchent un intervalle non trivial, déclarer NON_ESTIMABLE. Pour les adresses résolues présentes, intervalle logique0..N sous observabilité/éligibilité/inputs non identifiés, sans niveau de confiance. Ne pas présenter min/max des quatre délais comme intervalle de confiance ni comme borne de tous les retards possibles.

## Prospective et ressources

Un outil séparé observe en lecture seule les nouvelles alertes après activation, conserve véritable horodatage d'enregistrement/scellement, code/config et provenance, chaîne de hashes, fichiers protégés localement et erreurs explicites. Pas de backfill antidaté. L'heure de calcul et observed_at avant commit ne prouvent pas l'heure d'émission durable. Évaluation B distingue émission/scellement observés, ordre relatif à une publication vérifiée et capacité prédictive non validée. Un verrou local est réversible par le propriétaire, pas un horodatage tiers inviolable.

Collecte existante inchangée ; aucun accès privé ni transaction. Étude20Mo nouveaux fichiers maximum, sidecar20Mo maximum, aucune purge. Aucun gros téléchargement/copieur ni abaissement de seuil. Arrêter explicitement au plafond ; comptes et résultats incomplets restent marqués tels. Un plafonnement invalide toute prétention classement exhaustif même dans la strate.

## Entrées officielles et contrôle de ressources

Entrée R1 : code/ana_replay.py, validation obligatoire du manifeste et du SHA avant tout calcul ; la CLI directe du noyau est désactivée. R2 : code/ana_features.py. R3 : code/ana_labels.py après scellement. Une identité marché/événement/condition absente provoque un refus explicite de cette strate, jamais une catégorie artificielle None. Les versions partielles de préparation ne sont pas des entrées valides.

Capacité : chaque sortie analytique vérifie le cumul alloué/logique de20Mo et conserve10,5Go libres (mode normal) ; cette marge ne remplace pas la règle12Go pour travaux lourds. Les oracles identiques de vérification sont comptés séparément dans la sortie, sans duplication des hypothèses de classification.
