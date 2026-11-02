"""Format sealed outputs after two successful reproductions; no detector calculation."""
from pathlib import Path
import gzip,json,datetime,sys
ROOT=Path(__file__).resolve().parents[2]
S=ROOT/'studies/detection_20261030'
E=ROOT/'evidence/detection_prospective_20261030'
for i in (3,4):
    log=(E/f'repro_{i}.log').read_text()
    assert log.rstrip().endswith('REPRODUIT') and 'NON REPRODUIT' not in log
    assert log.count('IDENTIQUE')==3
sys.path.insert(0,str(S/'code'))
from budget import write_bytes
r=json.loads(gzip.decompress((S/'derived/replay.json.gz').read_bytes()))
f=json.loads(gzip.decompress((S/'derived/features.json.gz').read_bytes()))
l=json.loads((S/'derived/label_comparison.json').read_text())
x=r['scenarios'][0]
def dt(t):return datetime.datetime.fromtimestamp(t,datetime.timezone.utc).strftime('%d/%m %H:%M:%S') if t is not None else 'inconnu / aucun'
def rank(q):return f"{q['rank']} / {q['denominator']}" if q else 'aucun'
def flag(v):return 'oui' if v is True else 'non' if v is False else 'inconnu'
lines=['# Capacité de détection de PolySentinel : résultats du 30 octobre 2026','',
'''## Réponse A

**Le rejeu conditionnel aurait classé Thin-Disclaimer-Life prioritaire dès le 13 octobre. La capacité historique réelle reste NON_ESTIMABLE.** Les deux énoncés portent sur des objets différents.

Sous disponibilité immédiate des transactions et statut ouvert supposé, ce wallet franchit le seuil inchangé de 2 le **13 octobre à 18:50:49 UTC** sur l'événement1105364, rang de compétition **1 parmi74paires wallet-événement** ayant un achat récent à ce tick. Son premier comportement apparaît le13octobre à11:40:49. La concentration observée et le changement de taille des achats produisent deux familles distinctes. Avec les délais fixés de60,300,900secondes, la première priorité passe respectivement à18:51:49,18:55:49,19:05:49, toujours le13octobre. Ce sont des heures de décision simulées, pas des heures d'émission observées en2026.

Sur11étiquettes publiques,6correspondances exactes avec des alias actuels sont résolues ; ces6wallets sont présents et effectivement évalués dans le rejeu. Cinq ont au moins un comportement natif, un seul franchit le seuil conditionnel de priorité. Les5étiquettes non résolues restent inconnues, jamais absentes par défaut. Les9comptes de la liste initiale comprennent5résolus ; les2cas nommés ultérieurement comprennent1résolu. La continuité des alias historiques n'est pas prouvée. **Ces comptes ne constituent pas une vérité terrain d'initiés.** Aucun taux de rappel, précision ou faux positifs n'est calculé.

Source de chaque cellule : [comparaison après scellement](derived/label_comparison.json), qui conserve tous les dossiers par paire et tous les délais. Le résumé wallet signifie « au moins un événement » ; la table primaire ci-dessous distingue les événements.

## Étendue et preuve d'aveuglement

Le noyau `exploratory-1.2` et la configuration sont copiés à l'identique, avec seuil de priorité2 et paramètres natifs inchangés. Le constructeur du rejeu, lancé sans historique, n'a lu ni labels ni anciennes conclusions. Le coordinateur connaissait déjà l'affaire : cela ne constitue ni un aveuglement intégral de sa personne ni une nouvelle validation indépendante.

Le plan, le code, les données et contrôles ont été gelés le30octobre à12:58:02UTC (44fichiers). Les sorties complètes R1/R2 ont été scellées le30octobre à13:09:48.120290UTC, avant importation des labels. Le sceau et les labels ont ensuite été ajoutés au gel prévu, sans changer code ni seuils :47fichiers,1ajout. Voir [verrou](PROTOCOL.lock), [sceau](derived/pre_label_seal.json), [contrôle d'import](controles/labels_import.md).

La strate contient15148transactions et1301wallets, sur22identités d'événements issues du catalogue ultérieur. Elle réutilise une collecte lexicale de famille d'événements, taker seulement, choisie après l'affaire. La fenêtre est [23septembre15:17:49,23octobre15:17:49[UTC. L'ancien rapport retenait15067lignes avant le signalement avec une borne basse différente ; les81lignes supplémentaires sont antérieures à son ancienne borne, pas des résultats futurs ajoutés. Les46533lignes sources se réconcilient en15148retenues,319avant la fenêtre et31066au cutoff ou après ; aucun doublon supprimé. Source : [manifeste](data/input_manifest.json).

Les entrées excluent noms de candidats, résultats, titres, alias, profils, liquidités actuelles et labels publics. Les IDs de marchés/événements reposent néanmoins sur une correspondance supposée stable du catalogue acquis ensuite. L'univers complet admissible au23octobre, ses statuts historiques et ses flux ne sont pas établis. Le schéma officiel et le probe global archivé montrent que les paramètres start/end ne bornent pas cette forme globale de l'API. Il n'a pas été fabriqué de catalogue exhaustif ni de curseur. Voir [acquisition](ACQUISITION_PLAN.md), [schéma](data/api_schema.json), [probe](data/global_probe_receipt.json).

Le contrôle strict conservant les vrais observed_at postérieurs au cutoff examine0paire et émet0dossier : cela prouve uniquement l'absence d'observations contemporaines dans ces entrées. Il ne mesure pas une sensibilité nulle. Aucun des délais simulés n'est un retard maximal garanti. M1 suppose ouverture et absence de publication bloquante ; cette hypothèse favorable n'est pas une borne supérieure démontrée. Source : `strict_actual_observation_replay` dans [R1](derived/replay.json.gz).

## Dénominateurs réellement évalués

Les rangs portent sur les achats récents effectivement examinés, avec égalités conservées. Un wallet seulement présent comme contexte n'obtient pas un score0 ni un rang artificiel. Les premiers signaux proviennent des ticks réguliers de60secondes ; le snapshot final hors cadence est distinct.

| Délai hypothétique | Présents dans le fichier | Disponibles au cutoff | Wallets évalués au moins une fois | Avec comportement | Avec priorité conditionnelle |
|---:|---:|---:|---:|---:|---:|''']
for q in r['scenarios']:
 lines.append('| '+ ' | '.join(str(q[k]) for k in ('delay_seconds','n_wallets_present','n_wallets_available_by_final','n_wallets_recent_buy_evaluated','n_wallets_behavior_signal','n_wallets_conditional_priority'))+' |')
lines+=['', 'Source : les compteurs de chaque scénario R1. Pour le délai0,23wallets prioritaires conditionnels comprennent une correspondance avec les wallets publics résolus et22autres wallets non étiquetés. Ces22ne sont pas des faux positifs établis. L’effectif indépendant externe reste **une affaire**.', '', '## Comparaison publique, par paire', '', '| Alias actuel | Événement | Score maximal | Premier comportement UTC | Rang au premier comportement | Première priorité conditionnelle UTC | Rang à cette priorité | Raisons au score maximal |', '|---|---|---:|---|---|---|---|---|']
for a in l['rows']:
 q=a['scenarios'][0]
 if not a['wallet']:
  lines.append(f"| {a['public_label']} | identité non résolue | inconnu | inconnu | inconnu | inconnu | inconnu | aucun rapprochement supposé |")
 for p in q['wallet_event_records']:
  lines.append(f"| {a['public_label']} | {p['event_id']} | {p['best_score']} | {dt(p['first_signal_at'])} | {rank(p['rank_at_first_signal'])} | {dt(p['first_conditional_priority_at'])} | {rank(p['rank_at_first_conditional_priority'])} | {', '.join(p['best_score_reasons']) or 'aucune famille pondérée'} |")
lines+=['','''Table sans sélection du meilleur événement après coup : toutes les paires des wallets publics résolus sont conservées, délai0. « Aucun » signifie aucun signal dans ce scénario et ce corpus, pas une absence d'activité ailleurs. Les dates des autres scénarios sont dans R3.

VidenteRibeira et WenZhuanBuPei cumulent premier gros achat observé et concentration, mais ces deux règles appartiennent à la même famille exposure : score1, sous le seuil2. brace227 reste également à1 ; walletwallet8424 à0. OuldLm3alem atteint1 sur1218179 ; certaines annotations de récurrence sur les autres événements ont un poids0 parce que l'indépendance des événements n'est pas établie. Ni un premier trade retrouvé ni une concentration dans cette strate ne prouvent création récente ou information privée.

## Priorités de toute la strate, sans filtrage par les noms publics

La table suivante conserve toutes les paires ayant franchi le seuil dans le scénario délai0. L'ordre reprend celui de R1 : score maximal décroissant puis identités stables, avec égalités non départagées statistiquement. Le score maximal et ses raisons peuvent être postérieurs à la première priorité ; ils ne sont pas attribués artificiellement à son instant. Les autres scénarios et toutes les unités sans signal sont conservés dans R1.

| Wallet | Événement | Score maximal de période | Première priorité UTC | Rang à ce tick | Raisons au score maximal |
|---|---|---:|---|---|---|''']
for p in x['wallet_events']:
 if p['first_conditional_priority_at'] is not None:
  lines.append(f"| {p['wallet']} | {p['event_id']} | {p['best_score']} | {dt(p['first_conditional_priority_at'])} | {rank(p['rank_at_first_conditional_priority'])} | {', '.join(p['best_score_reasons'])} |")
lines+=['','''## Huit dimensions et références internes

R2 décrit le snapshot23octobre15:17:48UTC, délai0, fenêtre native récente de24heures : **413paires,253wallets**. Ce n'est pas une réévaluation des seuls comptes nommés ni une description de leurs positions complètes. Les synthèses suivantes sont des sommes des booléens déjà enregistrés, sans nouveau seuil. Source : [R2](derived/features.json.gz).

| Dimension demandée | Ce qui est mesuré et ce qui reste inconnu |
|---|---|
| Création récente | Date réelle inconnue ; ancienneté depuis le premier trade du corpus seulement, borne inférieure de l'ancienneté réelle. |
| Premier pari après création | Inconnu : ni création fiable ni premier pari global démontré. |
| Concentration | 9sur413paires satisfont la règle native de concentration des BUY nominaux observés, pas de l'ensemble du portefeuille. |
| Convergence | 3sur413paires ont le signal natif d'achats synchronisés. Des achats ne prouvent pas une position nette commune. |
| Montant / liquidité | Inconnu sans instantané historique frais de liquidité. Taille×prix donne un nominal partiel, pas un coût complet incluant frais. |
| Issues précises cohérentes | Nombre de tokens/marchés achetés conservé ; cohérence logique et positions nettes inconnues sans règles datées et inventaires. |
| Financement partagé ou synchronisé | Inconnu à l'échelle de cet univers aveugle ; aucune information ciblée après labels injectée. |
| Opérations avant information publique | Toutes précèdent ce signalement précis ; première information publique pertinente et absence d'autres publications inconnues. |

La conjonction concentration ET synchronie concerne1sur413paires ; elle n'ajoute aucun point au score de production. Les413concentrations observées sont calculables.384paires ont au moins un pair interne et29n'en ont aucun : leurs fréquences de référence restent inconnues. L'appariement utilise même événement, même jour UTC du dernier BUY et tranche fixe0,2 du prix moyen pondéré par les parts. Les effectifs, médianes/étendues et fréquences des pairs sont conservés pour chaque ligne. Ce ne sont pas des témoins innocents prouvés ; activité, réseau, liquidité et historique extérieur ne sont pas contrôlés. Aucun contraste causal ni test de supériorité n'est estimé.

Expertise, information sportive publique, chance, suivi d'autres traders, automatisation, arbitrage/couverture, service de financement commun et censure de collecte restent des explications concurrentes. Ces observations ne les départagent pas.

Le complément forensique de l'étude précédente reste **exploratoire, sélectionné après labels**, séparé du test aveugle. Il a réconcilié un trade et un dépôt par adresse et identifié une route USDC.e commune à brace227 et walletwallet8424, sans prouver un propriétaire commun. Il documente aussi la limite du parseur actuel, qui voit le mint pUSD sans remonter toute la route USDC.e. Aucun de ces éléments n'a modifié R1/R2. Les montants réconciliés concernent les seules opérations vérifiées ; inventaires, profit et financeurs ultimes restent inconnus. Voir [résultats forensiques antérieurs](../ballon_2026_20261030/results.md).

## Multiplicité, puissance et reproduction

Le registre final contient4calculs réels : R0structurel1, R1chronologique36456007, R2dimensions3717, R3labels44 ; total36459769comparaisons comptables. Le seuil Bonferroni conservateur est0,05/36459769, environ1,37×10⁻⁹. **Aucune p-value n'est définie : ni significativité ni performance ne découlent de ce nombre.** La dépendance entre ticks, wallets, événements et scénarios ne crée pas de nouveaux cas indépendants. n effectif externe=1affaire. Voir [registre](registre/tests.jsonl) et [audit](audit/PHASE5.md).

Les contrôles synthétiques comprennent trois fixtures déterministes nul/moyen/fort et des graines d'équivalence des implémentations. Ils ne mesurent ni puissance empirique, ni précision, ni rappel, ni taux de faux positifs. Les256contrôles ponctuels du noyau complet pendant le rejeu (64par délai) vérifient le cache, pas une performance financière ou prédictive.

Deux invocations indépendantes du reproducteur officiel ont chacune créé une copie fraîche avec HOME isolé. R1, R2 et R3 sont **identiques octet pour octet dans les deux copies**, aucune clé ignorée, et l'étude d'origine n'a pas été écrite. Voir [reproduction1](../../evidence/detection_prospective_20261030/repro_3.log), [reproduction2](../../evidence/detection_prospective_20261030/repro_4.log).

## Réponse B et capacités restantes

**Émission et conservation prospectives locales démontrées sur de vraies nouvelles observations d'alertes.** Le sidecar activé exclut les observations historiques, tout en admettant de nouvelles observations de dossiers existants, conserve contenu/provenance/lacunes, heure de lecture puis émission après fsync et scellement local. Son premier lot conserve deux observations le30octobre à12:34:37UTC sur « Fed Decision in December? », avant la réunion annoncée pour les8–9décembre. La première publication effective future de la décision n'est pas encore documentée : aucune réussite prédictive n'est annoncée. Voir [preuve opérationnelle et limites](../../evidence/detection_prospective_20261030/OPERATIONAL_REPORT.md), [premier reçu](../../evidence/prospective_eval/00000001/receipt.json).

Le lancement périodique est actif toutes les60secondes. Un manque d'espace a effectivement provoqué un refus, puis les captures ont repris quand l'espace est revenu. Le service source et ses seuils restent inchangés. Budget20Mo, aucune purge, aucun accroissement massif de collecte. La chaîne locale et les fichiers uchg protègent contre des modifications accidentelles ; le propriétaire peut lever ces protections. Horloge locale, pas d'ancrage tiers ni protection contre rollback coordonné. La collecte peut s'interrompre au plancher disque ou au plafond ; la réception humaine n'est pas démontrée.

Pour transformer A en évaluation historique globale, il manque : catalogue d'admissibilité daté ; transactions maker et taker avec couverture et publication attestées ; historiques globaux et inventaires des wallets ; création des comptes ; statuts/liquidités/règles de résolution datés ; chronologie sourcée des informations publiques ; parcours des transformations et financements en amont. Leur ajout doit être évalué sous un nouveau protocole, sans régler des seuils sur cette affaire. Pour B, il faut maintenant documenter les annonces publiques futures et comparer leurs heures aux émissions conservées, ainsi qu'un budget de conservation durable ; les résultats de cette campagne ne sont pas encore connus.

Aucun intervalle empirique honnête n'est identifiable pour l'historique réel. Pour les6adresses résolues présentes,0 à 6 wallets alertés au moins une fois est seulement un intervalle logique compatible avec les lacunes d'observabilité, d'admissibilité et d'entrées ; ce n'est pas un intervalle de confiance. Le résultat1sous M1 n'en est pas une borne garantie, et les cinq identités non résolues restent hors de ce comptage.

## Deviations and data notes

- R0a mesuré la taille et le profil de charge avant gel. Il est enregistré comme tel. Aucun rejeu de détection n'a précédé le gel ; ne pas affirmer qu'aucun calcul réel préalable n'existe.
- L'implémenteur est aveugle aux labels ; le coordinateur connaissait le précédent rapport et la strate est choisie après l'affaire. A1n'est donc pas une validation externe sur l'univers complet.
- Le libellé du plan « fixtures nul/moyen/fort plusieurs graines » est plus large que ce qui a été réalisé : troisfixtures déterministes et graines distinctes d'équivalence. La contrelecture indépendante le relève ; aucune puissance statistique n'est revendiquée et le plan gelé n'est pas réécrit.
- Une tentative de contrôle synthétique a été refusée sous10,5Go ; elle est enregistrée, pas comptée comme PASS. Après retour spontané de l'espace, les contrôles finaux ont passé. Aucune suppression supplémentaire n'a été effectuée.
- Les résumés wallet R3 signifient au moins un événement ; toutes les paires et les scores0restent publiés. Les maximums de période ne sont pas des classements disponibles dès le début de la fenêtre.
- Les contrôles de code et le volume de transactions ne sont jamais utilisés comme preuve de performance. Aucun initié prouvé, aucun vrai négatif, aucune précision/rappel/FPR véritable n'est disponible.
''']
body='\n'.join(lines)+'\n'
# Formatting only: separate prose counts, not hexadecimal IDs or machine artifacts.
for a,b in {'événement1105364':'événement 1105364','parmi74paires':'parmi 74 paires','le13octobre':'le 13 octobre','de60,300,900secondes':'de 60, 300, 900 secondes','à18:':'à 18:','à19:':'à 19:','à11:':'à 11:','en2026':'en 2026','Sur11étiquettes':'Sur 11 étiquettes','6correspondances':'6 correspondances','ces6wallets':'ces 6 wallets','Les5étiquettes':'Les 5 étiquettes','Les9comptes':'Les 9 comptes','comprennent5résolus':'comprennent 5 résolus','les2cas':'les 2 cas','comprennent1résolu':'comprennent 1 résolu','priorité2':'priorité 2','le30octobre':'le 30 octobre','44fichiers':'44 fichiers','47fichiers,1ajout':'47 fichiers, 1 ajout','15148transactions':'15 148 transactions','1301wallets':'1 301 wallets','22identités':'22 identités','15067lignes':'15 067 lignes','les81lignes':'les 81 lignes','46533lignes':'46 533 lignes','15148retenues':'15 148 retenues','319avant':'319 avant','31066au':'31 066 au','0paire':'0 paire','0dossier':'0 dossier','60secondes':'60 secondes','délai0':'délai 0','23wallets':'23 wallets','22autres':'22 autres','Ces22ne':'Ces 22 ne','score1':'score 1','seuil2':'seuil 2','à1':'à 1','à0':'à 0','atteint1':'atteint 1','sur1218179':'sur 1218179','poids0':'poids 0','413paires,253wallets':'413 paires, 253 wallets','9sur413paires':'9 sur 413 paires','3sur413paires':'3 sur 413 paires','1sur413paires':'1 sur 413 paires','Les413concentrations':'Les 413 concentrations','384paires':'384 paires','et29n’en':'et 29 n’en','et29n\'en':'et 29 n\'en','fixe0,2':'fixe 0,2','4calculs':'4 calculs','R0structurel1':'R0 structurel 1','R1chronologique36456007':'R1 chronologique 36 456 007','R2dimensions3717':'R2 dimensions 3 717','R3labels44':'R3 labels 44','total36459769comparaisons':'total 36 459 769 comparaisons','est0,05/36459769':'est 0,05 / 36 459 769','environ1,37':'environ 1,37','1affaire':'1 affaire','Les256contrôles':'Les 256 contrôles','64par':'64 par','reproduction1':'reproduction 1','reproduction2':'reproduction 2','les8–9décembre':'les 8–9 décembre','Budget20Mo':'Budget 20 Mo','les6adresses':'les 6 adresses','0à6alertes':'0 à 6 alertes','résultat1sous':'résultat 1 sous','R0a':'R0 a','A1n\'est':'A1 n\'est','troisfixtures':'trois fixtures','sous10,5Go':'sous 10,5 Go','scores0restent':'scores 0 restent','de24heures':'de 24 heures'}.items():body=body.replace(a,b)
write_bytes(S/'results.md',body.encode())
print(S/'results.md')
