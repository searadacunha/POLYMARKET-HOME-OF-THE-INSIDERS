# Étude chronologique descriptive — plan antérieur à la sélection

Écrit le 27 octobre 2026, après lecture du code et des schémas mais avant sélection
des événements terminés ou consultation de leurs issues. Les dossiers FOMC déjà
examinés sont connus et exclus. Cette étude cherche d'abord les raisons qui rendent
une évaluation historique impossible ; elle ne recherche pas des initiés.

## Question

Sur au plus huit événements terminés réellement présents dans les données du bot,
quelle part du chemin documentaire nécessaire à une évaluation strictement
chronologique existe ? Les alertes précèdent-elles une première information publique
vérifiée, avec une cible et une cohorte accessibles, ou seulement une clôture tardive ?

## Données et limites de lecture

Cutoff fixé : **2026-10-27T21:42:00Z**, dernière fin de cycle achevée avant ce cutoff.
Fenêtre d'échéance : les 24 heures précédant ce cutoff effectif. Source unique pour
les features et les labels : histoire SQLite locale effectivement observée avant le
cutoff, `mode=ro`, `query_only`; aucune lecture réseau dans cette étude. Transactions
de lecture courtes par requête, pas de backup de base, pas de décompression globale.
Chaque contenu décodé est vérifié par SHA-256. Maximum 10 000 dernières références
événement, 10 000 dernières références dossier, 1 000 jalons publics, 8 événements,
30 000 versions de dossiers pertinentes cumulées, 5 000 références de trades
d'alertes et 5 000 références d'activités par événement. Dépassement : arrêt explicite,
jamais troncature silencieuse. Au plus 25 MB de nouveaux fichiers de l'étude.

`code/col_extract.py` écrit une extraction compacte avec les références et dates
observées ; elle est gelée avant les calculs d'éligibilité, de comparaison ou de taux.
Le comptage d'extraction distingue demandé, reçu, absent et erreur. Une absence de
ligne historique signifie absence de preuve dans ce cache, pas absence d'activité.
Les modules de production sont **copiés** dans `code/vendor`, jamais gelés en place.

## Population et sélection, fixées avant labels

À chaque clé événement retenir la dernière version connue au cutoff. Est terminé
un événement dont `closed` est vrai, dont le brut porte `ended=true`, ou qui possède
un jalon officiel attestant toutes ses conditions connues résolues. `active=false`,
une échéance passée ou un prix proche de 0/1 seuls ne suffisent pas. Il faut une
échéance datée avec fuseau, dans la fenêtre de 24 h et au plus au cutoff. Exclure
l'événement FOMC 606422 et tout titre `Fed Decision` (les trois marchés déjà vus).
Trier **échéance croissante, identifiant** ; retenir les huit premiers sans remplacement.
Les événements hors fenêtre, sans date, non terminés et surnuméraires sont comptés.
Conditionnement explicite : catalogue collecté, événements terminés et fenêtre courte ;
aucune représentativité ni estimation sur les événements non observés.

## Instants, unité et n effectif

Pour chaque événement : premier constat terminal retrouvé dans ses versions historiques.
Ce constat est une **borne documentaire de clôture**, jamais la première annonce.
Sans première annonce vérifiée, l'instant descriptif proxy est la dernière fin de
cycle strictement antérieure au constat terminal. S'il n'existe pas, aucun instant
ni dossier ne sont fabriqués.
Pour chaque clé dossier, garder sa dernière version observée au plus à ce proxy et
dont `calculated_at` est au plus ce proxy. Les features proviennent des émissions
archivées : aucun score n'est recalculé sur un sous-univers réduit. Les anciennes
versions de règles restent identifiées ; seule exploratory-1.2 est admissible pour
une éventuelle comparaison de performance. Ce n'est **pas** un replay indépendant
intégral des 50 000 trades de chaque cycle.

Unité documentaire : événement. Unité des alertes : wallet-événement-version de règle,
un dossier par clé au proxy. Les marchés d'un événement et plusieurs wallets peuvent
être dépendants. n nominal = dossiers ; n effectif descriptif maximal = événements
distincts ; aucun contrôle commun d'adresses n'est inféré. Les comptes sans signal
persisté ne sont pas disponibles comme population négative exhaustive.

## Labels et porte d'estimabilité

Ne jamais assimiler `public_at` créé par `news.resolution_state` à la date de première
information : ce champ contient la première lecture du résultat officiel par le bot.
Un jalon accepté comme première information doit explicitement porter
`first_public_information_verified=true`, `public_at` UTC, `source_url` HTTPS,
`evidence_id`, `timestamp_basis`, `timing_uncertainty_seconds=0` et une preuve de
contemporanéité archivée. Un résultat officiel exige séparément une cible vérifiée
token/issue (`target_verified=true`, `winning_token_ids`, provenance), acquise après
la décision mais avant le cutoff. Les données de résultat ne sont jamais injectées
dans les features ni utilisées pour choisir les contrôles.

Une cohorte pré-information exige : décision < première information, couverture du
bot déjà commencée, observations/features toutes <= décision, version v1.2, preuve
de complétude du **périmètre de dossiers retenu avant information** (`cohort_complete`
documenté) et cible valide. Cette complétude n'est pas celle du marché mondial.
Si un maillon manque, précision et performance sont **non estimables** ; un zéro
observé n'est ni une absence de faux positifs ni une réussite. Une cible manque si
le résultat officiel ne précise pas les tokens gagnants, même si `resolved` est vrai.

Conditionnellement à cette porte seulement : part des BUY focaux de dossiers
prioritaires portant un token gagnant, dénominateur explicite ; ce n'est pas une
précision de détection d'initiés. Achat focal = nominal maximal, puis timestamp
croissant, puis transaction lexicographique. Aucune rentabilité réelle n'est calculée
dans cette étude : inventaire initial, conversions, ventes, frais et prix exécutables
de sortie doivent être complets pour cela. `economic_return=null` sans exception.

## Contrôles descriptifs et intégrité des observations

Pour chaque dossier prioritaire v1.2, contrôles parmi les dossiers archivés v1.2 non
prioritaires, encore courants et préalables, du même événement au proxy ; achat focal de même token et condition connue,
écart <= 60 min, prix <= 0,10, rapport des nominaux dans [1/3,3], rapport des
(groupes de trades du dossier +1) dans [1/3,3]. Cette dernière mesure est une
couverture partielle, pas une ancienneté du wallet. Trier par somme des distances
normalisées temps/prix et logs absolus des deux rapports, puis wallet/id ; trois
wallets distincts maximum ; aucune relaxation ni sélection sur l'issue.
Vérifier les trades sous-jacents des alertes et les métadonnées observables au calcul.
Des données arrivées après le calcul sont exclues même si leurs transactions sont
antérieures. Les cases avec preuve manquante sont comptées, pas réparées avec le futur.
Conserver regroupement de fills, liens transaction, censures d'historique, hypothèses
d'arbitrage/couverture/conversion/copie/automatisation et absence de preuve de propriété.

## Splits, tests et registre

Pas de TRAIN/VALIDATION/TEST statistique : unique audit documentaire exploratoire d'une
fenêtre déjà écoulée, et futur non touché. Pas d'optimisation de seuil ni de variante.
Un balayage réel déclaré, huit comparaisons événement au maximum, enregistré après
écriture de `derived/evaluation.json`, nombre exact de comparaisons = événements
sélectionnés. Toutes les exécutions synthétiques sont enregistrées séparément.
Aucun p, intervalle, alpha ou rejet statistique : la correction Bonferroni affichée
par l'outil registre est un inventaire standard, sans test d'hypothèse ici.

## Contrôles synthétiques avant gel

Trois graines (11, 29, 47), six wallets et un événement par scénario. Nul : achats
100, espacés ; moyen : achats 1 200, trois wallets synchrones et trois espacés ; fort :
six achats 1 200 synchrones. Le module v1.2 copié calcule les signaux sans changement
de seuil. Le pipeline documentaire et le verdict s'exécutent ensuite sur ces dossiers,
avec temps/publication/cible/cohorte synthétiques connus. Attendu : nul muet, trois
priorités sur six au moyen, six sur six au fort, verdict descriptif pour moyen/fort.
Ce tableau de sensibilité synthétique n'est pas une puissance statistique réelle.
Contrôles adverses : première lecture de résolution seule refusée ; feature tardive
refusée ; observation postérieure au cutoff refusée ; cible absente refusée ; cohorte
incomplète refusée ; duplicata de fill non doublé ; trade futur ignoré par group_fills.

## Verdict figé

Par événement, priorité des portes : `NON_ESTIMABLE_PUBLIC_TIMING`,
`NON_ESTIMABLE_COHORT`, `NON_ESTIMABLE_TARGET`, `NO_PRIORITY_SIGNAL`,
`DESCRIPTIVE_ONLY`. Tous les événements restent visibles même exclus. Verdict global :
`NON_ESTIMABLE` si aucun événement ne passe les portes ; sinon `DESCRIPTIVE_ONLY`.
Jamais `insider`, `validé`, `rentable` ou probabilité d'initié. Les causes secondaires
restent écrites même si une porte antérieure suffit à exclure.

## Reproduction, audit et modifications

Le parent organise la revue aveugle code/plan avant le gel. Après contrôles, geler
plan, code, données d'extraction et rapport synthétique par le script autorisé ;
aucune opération git dans le dépôt vide de ~. Calcul réel uniquement après gel intact.
Puis reproduction deux fois en copie fraîche sans réseau et sans base vivante.
Auditeurs aveugles : interdire results.md, derived/evaluation.json, audit/ et
registre/tests.jsonl ; fournir export aveugle et compte registre. Données gelées
lisibles, sans exécuter l'analyse. Le parent conduit les audits requis du skill.
Pas d'amendement au gel. Toute modification ultérieure exige un nouveau fichier
versionné/amendement ; aucune réécriture de preuve ou méthode gelée.
