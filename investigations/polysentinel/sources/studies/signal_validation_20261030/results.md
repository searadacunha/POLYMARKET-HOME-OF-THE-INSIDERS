# Solidité du premier signal Thin-Disclaimer-Life

Étude exploratoire du30octobre2026, modèle et nouveaux calculs gelés à14:30:21UTC. Le signal conditionnel est reproductible. Sa rareté indépendante, son observabilité historique réelle et sa valeur prédictive restent **NON_ESTIMABLE**. Le Ballon d'Or a informé la conception du système : ce cas n'est pas une validation indépendante.

Toutes les valeurs analytiques ci-dessous proviennent de `derived/validation.json.gz`, SHA256 `aa5f48bb0a61c36750e83cd3fcf9d0206e51de942016505db35906eb8b46fc71`, scénarios0/60/300/900. Les pièces documentaires et opérationnelles sont référencées séparément. Unité externe indépendante : **une affaire** ; dépendances internes entre wallets et marchés non identifiées.

## 1. Pourquoi Thin ressort

Wallet : `0x8d3319c51520518ad01f6744486ceea29f376f5b`. Événement1105364, marché5141816, lu dans le catalogue ultérieur comme « Kylian Mbappé or Lamine Yamal to finish higher? », token associé à Mbappé. Ces noms et cette correspondance d'issue servent à expliquer les transactions après le calcul ; ils n'entraient pas dans le détecteur.

L'achat rapporté le **13octobre18:50:00UTC** est de **25474,05 parts à0,5787631806**, soit **14743,442201** unités de nominal brut, hors frais. Hash : [0x8dc10176ab3741ade3881689296c6ab459029bb176f5a18fe37cb4185b02c4a3](https://polygonscan.com/tx/0x8dc10176ab3741ade3881689296c6ab459029bb176f5a18fe37cb4185b02c4a3). La grille de décision minute, ancrée à la fenêtre du protocole antérieur, le prend en compte à18:50:49 avec délai0. Ces49secondes proviennent de la grille ; ce n'est pas une latence observée.

| Règle native au tick18:50:49 | Valeur reconstruite | Critère | Point |
|---|---|---|---:|
| Concentration événement | 29748,217401 /29748,217401 d'achats bruts sur24h,25 groupes BUY ; ratio1 | nominal événement≥1000 et part≥0,8 | 1, famille exposure |
| Rupture de taille | achat14743,442201 ;34 groupes BUY antérieurs ; médiane257,700000 ; MAD232,153600 | au moins20 achats antérieurs et nominal≥max(5×médiane,médiane+6×1,4826×MAD,1000)=2322,845564 | 1, famille size |

Score total **2**, seuil de priorité conditionnelle2. La taille et la concentration comptent comme deux familles, mais elles utilisent les mêmes achats et ne sont pas deux preuves statistiquement indépendantes. Aucun point pour la création récente, un financement commun, la liquidité ou la connaissance d'un gagnant. Au tick précédent, score1. À J−1, la paire cible est évaluable, sans signal retourné ; ce n'est pas une preuve d'innocuité ni un contrôle négatif garanti.

Le rang **1/74 est partagé avec un autre wallet**, `0xd5a817163ea5acd551ee9201efbcf8b709bf9793`, qui présente lui aussi concentration+rupture. « Premier » ne signifiait donc pas unique première place. À la première occurrence du signal de concentration, le13octobre11:40:49, sa valeur était6315,455800 /7865,493300 =0,8029319407 d'achats bruts24h ; au déclenchement de priorité18:50:49, elle vaut1 selon les montants du tableau. Les anciennes premières valeurs de chaque règle ne décrivent pas nécessairement le même instant.

Les [38 transactions et leurs prix/montants/horodatages](TRANSACTIONS.md) sont fournies intégralement, avec hashes et trois marchés. Le noyau compte38 groupes :35 BUY et3 SELL. Les34 BUY précédant l'achat déclencheur constituent sa baseline ; les ventes restent contexte et ne sont pas assimilées à des achats. Achats bruts, inventory delta et financement ne sont pas un capital net engagé ni un profit.

Le regroupement est transactionnel faute d'ordre parent prouvé. Un changement de fragmentation des ordres, une exécution en plusieurs fois ou un réapprovisionnement peuvent changer la distribution des tailles sans changement d'information. La baseline limitée au corpus ne reconstitue ni tous les ordres ni toute la stratégie du compte.

**Liquidité observable au13octobre : inconnue.** Aucun carnet daté, profondeur exécutable ou snapshot Gamma contemporain n'est présent. Le score n'utilise donc pas `liquidity_fraction` ni `cohort_size`. Prix de transaction et volume ultérieur ne remplacent pas cette liquidité.

## 2. Identité et observabilité

La réponse Gamma obtenue le30octobre10:44:31.842532UTC associe exactement ce proxyWallet au pseudonyme Thin-Disclaimer-Life. Pièce : `../../research_notes/PolySentinel et le Ballon 2026/labels_after/profile_search_0x8d3319c51520518ad01f6744486ceea29f376f5b.json`. Elle documente un alias actuel ; sa continuité au13octobre et l'identité civile ne sont pas prouvées. [Provenance détaillée](../../evidence/signal_validation_20261030/PROVENANCE.md).

Les38 lignes cible utilisées ont été effectivement recueillies le **30octobre10:45:38–10:46:20UTC**. Les dates économiques rapportées sont antérieures ; leur disponibilité API à ces dates et les délais de diffusion ne sont pas connus. Les transactions ne sont pas toutes rapprochées ici de reçus blockchain. Une vérification de bloc démontrerait leur inclusion, pas la disponibilité historique de toutes les API et métadonnées nécessaires.

Avec les observations réelles, PolySentinel n'avait aucune observation contemporaine de ce cas ; le service local n'a commencé que le27octobre. Dans les simulations, seule une copie en mémoire d'observed_at devient timestamp+délai. Les sources originales restent intactes. Les règles calculent un comportement ; **la priorité native reste fausse faute d'ouverture historique vérifiée**. Le franchissement annoncé suppose M1 : marché alors admissible et aucune première information publique antérieure. L'antériorité à Upside n'établit pas, à elle seule, l'antériorité à toute information publique.

## 3. Rareté et témoins

La combinaison examinée ici est concentration **ET** rupture de taille, choisie après résultat. L'étude précédente examinait séparément concentration+synchronie. Aucune permutation inférentielle n'a été exécutée : permuter identités, montants ou dates détruirait les dépendances mécaniques et ne reproduirait pas le mécanisme de sélection du compte/tick. Il n'existe pas de groupe de non-initiés vérifiés.

Scénario0 au tick18:50:49 :

| Ensemble descriptif | Combinaison / dénominateur, cible incluse | Témoins seuls |
|---|---:|---:|
| Toutes paires BUY24h évaluées | 2/74 | sans objet : plusieurs événements |
| Paires capables de baseline20 avant un achat récent | 2/9 | sans objet : plusieurs événements |
| C0 : même événement | 2/44 | 1/43 |
| C1 : même événement et baseline capable | 2/5 | 1/4 |
| C2 : C1 plus classes fixées d'âge observé, activité, montant récent, jour et prix | 1/1 | **0 témoin disponible** |

« 0 témoin » ne signifie pas que le comportement est infiniment rare : **l'appariement échoue à fournir un comparateur**. Pour les délais300/900, l'ensemble global devient2/73, C0 devient2/43 et ses témoins1/42 ; seuls les effectifs baseline capable, C1 et C2 restent identiques. Toutes les classes sont maintenues sans élargissement après lecture des effectifs. Les [quatre témoins C1 et la file complète](TEMOINS_ET_FILE.md), ainsi que les43 témoins C0 du délai0 et toutes covariables dans la sortie, permettent de vérifier ces dénominateurs.

Âge mesuré = durée depuis première observation dans le corpus (42,579444h pour Thin au tick0), pas création de compte. Activité/achats sont censurés à la famille collectée ; le montant récent conditionne sur une partie de l'anomalie. Positions nettes, âge réel et liquidité comparables manquent. Même événement ne garantit ni même liquidité de token ni même stratégie. **Une rareté statistique indépendante demeure NON_ESTIMABLE ; aucun p, IC binomial, précision, rappel ou FPR n'est fourni.**

Placebo J−1 :0 conjonction sur93 paires, dont11 capables de baseline. Au tick étudié,19 paires sont communes :18 restent sans conjonction,1 passe de0 à1 ;74 anciennes paires sortent et55 entrent (54 pour délais300/900). La transition de Thin appartient aux paires communes. Cette forte rotation interdit d'interpréter naïvement0/93 contre2/74 comme un effet statistique de l'information.

## 4. Charge de revue et quatre délais

Politique fixée avant ce calcul : examiner chronologiquement chaque première priorité, dédupliquée par wallet ou par paire ; départage lexical si égalité. Les observations répétées du même dossier ne sont pas de nouveaux dossiers. Aucune promesse de temps humain en minutes, faute de mesure de durée de revue.

| Délai hypothétique | Première priorité UTC13octobre | Paires au tick / rang partagé | Wallets évalués sur30jours | Paires évaluées sur30jours | Position chronologique wallet / paire |
|---:|---|---|---:|---:|---|
|0s|18:50:49|74 /1|1078|2013|7e /8e|
|60s|18:51:49|74 /1|1078|2013|7e /8e|
|300s|18:55:49|73 /1|1078|2013|7e /8e|
|900s|19:05:49|73 /1|1077|2011|7e /8e|

**Six autres wallets, représentant sept dossiers, auraient donc précédé Thin.** Il faut examiner7 wallets ou8 dossiers pour l'atteindre dans cette politique. Sur toute la fenêtre,23 wallets et28 paires atteignent le seuil dans chacun des scénarios :22 autres wallets restent à examiner au total, pas22 faux positifs. Le rang sur maximum ultérieur est2e ex æquo parmi1078wallets, avec positions possibles2–23 ; parmi2013paires,2–28. Ce classement rétrospectif n'est pas celui dont disposait l'analyste le13octobre. À délai900, dénominateurs1077/2011, mêmes intervalles d'ex aequo.

Distribution des maxima, délai0 :994wallets à0,61 à1,22 à2,1 à3 ;1899paires à0,86 à1,27 à2,1 à3. Les délais60/300 sont identiques. À900 :993/61/22/1wallets et1896/87/27/1paires. Le maximum3 concerne une autre unité, observée ultérieurement.

Ces charges portent sur **toute la strate effectivement évaluée**, pas sur tout Polymarket. Catalogue global admissible, couverture et politique de collecte historique restent inconnus ; la charge sur l'univers global ne peut être extrapolée.

## 5. Fragilité aux manquants

Pour chacun des quatre délais,38 retraits séparés de transaction ont été calculés avec le noyau complet et les autres wallets conservés :38 variantes évaluables, aucune perte d'éligibilité ;37 gardent le score2,1 tombe à1. Le seul retrait faisant perdre le seuil est celui de l'achat déclencheur de14743,44 ; la concentration subsiste. Il s'agit de38 scénarios déterministes par délai, **pas38 observations indépendantes ni une probabilité37/38 de réussir**. Les quatre délais réutilisent largement les mêmes données.

En conservant toutes les autres caractéristiques fixes, **plus de7437,054350 unités d'achats supplémentaires hors événement**, dans les mêmes24h et sans nouvel achat de cet événement, ramèneraient sa concentration sous0,8. L'égalité donne encore0,8. Cette borne est un calcul de dilution, pas une estimation des montants réellement absents ; ces achats pourraient aussi changer d'autres règles. Des achats antérieurs absents peuvent changer médiane/MAD, les34 comparateurs ou la taille apparente du saut. Des transactions absentes chez d'autres wallets changeraient également le classement et la charge de revue.

Aucune loi de manquants ni borne sur leur nombre n'étant connue, il n'existe pas d'intervalle de confiance informatif pour l'alerte réelle. Les deux états (alerte ou absence d'alerte) restent compatibles avec des compléments d'historique plausibles non quantifiés. Explications concurrentes : expertise, information déjà publique, pari convictionnel, copie, automatisation, arbitrage, couverture hors corpus, chance. Aucun de ces constats ne démontre une information privilégiée.

## 6. Indépendance et prospective

Les traces natives montrent une mission évoquant déjà le Ballon d'Or le27octobre14:09UTC, les seuils1000/20/2 écrits16:56, les règles de concentration/rupture créées17:02 ; versions1.1 puis1.2 le même jour, puis diagnostics. Toutes ces dates sont **postérieures au23octobre**. Les modifications documentées corrigent exclusions/ancienneté/diagnostics ; les seuils examinés restent stables dans les archives. Aucun ajustement spécifique à Thin n'a été trouvé dans cette revue ciblée, mais l'affaire a précédé le choix du modèle. [Pièces, lignes de sessions et empreintes](../../evidence/signal_validation_20261030/PROVENANCE.md).

Le noyau `exploratory-1.2` SHA256 `45d1a5c0c109c573c4057269fb1783f768fc41da3973bb73d7e17a29b78ded90` et la configuration SHA256 `5b7e8073bd345acc70c8a526edf37d132ad6af6963cd01c4acbab1ed52fb4b4b` sont gelés dans cette étude ; les empreintes font foi dans PROTOCOL.lock. Aucun seuil de production n'a changé. Les prochains événements dont première publication est postérieure au présent gel sont réservés à une observation future ; définir et geler l'adjudication avant de consulter leurs issues reste nécessaire.

Le [contrôle prospectif](../../evidence/signal_validation_20261030/prospective_capacity.md) vérifie à14:16:28UTC une chaîne intacte de56reçus :275observations de41dossiers wallet–événement,35wallets,21événements.234observations sont supplémentaires aux premières observations de ces dossiers ;265 concernent des dossiers créés avant l'activation. Les275empreintes matérielles distinctes ne font pas275alertes indépendantes. Les275observations ont des données manquantes et une première publication publique inconnue. Les captures conservent version/empreintes, scores, raisons, données ciblées disponibles, manquants et horodatages de lecture/persistance/émission/scellement.

La protection locale lecture seule/uchg et la chaîne de hashes sont vérifiées ; elles restent réversibles par le propriétaire et l'horloge n'a pas d'ancrage externe. Les sources sur disque ne prouvent pas exactement la version chargée en mémoire. Les données copiées à la capture ne constituent pas tous les comparateurs d'origine. Aucun succès prédictif n'est établi.

Un moniteur indépendant à60secondes est maintenant actif. Il conserve un état et un avertissement bornés hors spool, notifie les seuils80/90%, les refus et l'absence de place pour un lot, les pannes/stagnations du statut. Deux passages réels14:21:02/14:22:03 attestés ; occupation18,136448Mo au second. L'alerte90% a produit un retour macOS0, sans preuve de réception humaine. Le plafond20Mo reste strict : **un refus de nouvelle conservation est signalé, aucune purge ni extension automatique**. Voir l'état courant et les éventuels refus dans `../../evidence/prospective_monitor/status.json` et `ATTENTION.txt` ; cette mesure datée n'atteste pas de la capacité restante ultérieure.

Seules des observations futures pourront établir le délai réel entre alerte scellée et première annonce publique sourcée, la couverture de capture, la charge de revue durable et la reproductibilité sur d'autres événements. Précision/FPR exigent en plus une vérité terrain défendable ; un résultat gagnant n'en est pas une.

**Actualisation opérationnelle : refus réel au plafond.** Le relevé conservé dans `../../evidence/signal_validation_20261030/runtime_1435.json` contient l'état du moniteur à14:40:36UTC :19914752octets utilisés,85248restants, curseur682094,64reçus (activation incluse), statut `REFUSED`, motif `20 MB prospective cap reached; cursor unchanged, no pruning`. Le seuil n'a pas besoin d'être rempli au dernier octet : le prochain lot est refusé s'il ne tient pas. Le moniteur a notifié `SOURCE_NOT_CAPTURING` avec retour0 et avertissement persistant. Les nouvelles captures sont donc interrompues explicitement ; aucune continuité prospective n'est revendiquée après ce point. Collecte principale et conservation prospective sont deux états différents. Une capacité durable d'archivage vérifié ou un nouveau format prospectif moins redondant devra être préparé et validé avant de compter sur les prochains événements ; aucune purge ni hausse du plafond n'est faite ici.

## Reproductibilité, registre et limites de vérification

Gel initial12fichiers intact, quatre balayages réels enregistrés après gel :V1=960,V2=12361,V3=982,V4=156, total14459unités descriptives selon la convention écrite. Cumul de ces trois études :ballon29 +detection36459769 +présente14459 =36474257 ; ce n'est pas un recensement de toute la recherche de conception antérieure. Bonferroni formel0,05/N, **aucun p calculé ou revendiqué** ; ces compteurs ne sont ni des répétitions indépendantes ni une mesure de qualité. Les cinq passes de contrôles synthétiques restent séparées des analyses réelles. Six méthodes de tests passent ; contrôles déterministes, aucune puissance populationnelle.

Deux reproductions en copies fraîches, HOME isolé et sans réseau, donnent un fichier strictement identique. Log : `../../evidence/signal_validation_20261030/reproduction_with_output_directory.log`. La première tentative échouait parce que l'outil ne copie pas les dossiers vides : le répertoire derived manquait. Le second lancement crée ce seul dossier de sortie avant d'exécuter le même code gelé ; aucune entrée, règle ou sortie d'origine n'a été modifiée. Log d'échec conservé : `reproduction.log`.

Audits aveugles : fuites, conformité, échecs silencieux et statistiques ; correctifs avant gel détaillés dans `audit/PHASE5.md`. Les frontières exactes C2 et les transitions avec attrition n'ont pas de fixture synthétique dédiée ; elles ont une revue statique et peuvent être recomptées indépendamment à partir des sorties. La réussite des tests et des reproductions ne prouve pas la détection réelle au13octobre.

Contre-audit neuf : limite MAJEURE du helper de registre hors entrée officielle. Un appel direct au helper sans précontrôle, ou une variable ETUDE_REPRO_DIR mal ciblée, pourrait actualiser un témoin périmé avant de détecter son ancienneté. Le chemin `main()` normal vérifie strictement le témoin avant calcul, puis après chaque inscription ; les reproductions officielles n'inscrivent intentionnellement rien. Le contre-auditeur juge ce défaut non bloquant pour ces chemins, mais refuse une garantie globale du helper. Le lancement réel est terminé code0 et les quatre inscriptions sont présentes ; la présence seule du fichier de sortie n'aurait pas suffi. Aucun correctif n'a été appliqué au code gelé. Les appels futurs hors chemin validé exigent une version corrigée et un nouveau contrôle.

## Deviations and data notes

Étude nouvelle et explicitement post hoc, aucun ancien plan/rapport réécrit. Pas de permutation ni d'inférence faute d'échangeabilité/contrôles valides, comme fixé avant calcul. Compteurs synthétiques initiaux60/58 et n78 par niveau conservés ; dernière convention59 et n234 pour les neuf fixtures documentée, sans effet sur les résultats réels. Initialisation de dossier nécessaire en reproduction, code gelé inchangé. Aucun nouveau téléchargement historique, aucune modification de production ou baisse de garde-fou, aucune suppression. Les variations d'espace dues aux autres processus ne sont pas attribuées à ce travail.
