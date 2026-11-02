# État final au 2026-10-30T13:59:35.957991+00:00

La note REPRISE_DETECTION.md décrivait le blocage intermédiaire. Il a été dépassé : deux nouvelles reproductions en copies fraîches ont terminé REPRODUIT, les trois sorties sont identiques octet pour octet dans chacune. Les échecs antérieurs sont conservés. Deux audits indépendants des conclusions A+B ont ensuite rendu PASS sur10critères chacun ; aucune correction ouverte.

Rapport courant : ../../studies/detection_20261030/results.md
SHA : 4005c46f9589e3c751e390a6a4415136700824f07991193397df6c1fe1265eb1
Preuve prospective : OPERATIONAL_REPORT.md
SHA : caba3c1823543ada35756e36eb290929d2bf76f48e85b2bc653314e8d313c15d
Audits : ../../studies/detection_20261030/audit/claims_a.json et claims_b.json.

Les limites scientifiques restent entières : étude exploratoire conditionnelle sur une strate censurée, observabilité historique globale NON_ESTIMABLE, pas de précision/rappel/FPR. Le seul franchissement de priorité parmi les6wallets publics résolus est conditionnel ; ce n'est pas une alerte historique prouvée.

Au relevé final_live_state.json (2026-10-30T13:56:36.908062+00:00) : 251518trades, mode normal, libre 10.610Go. La chaîne prospective est vérifiée ;26empreintes inchangées. Étude environ3,25Mo ; chaîne prospective12,813Mo sur20Mo. Le cap refuse toute écriture supplémentaire lorsqu'il est atteint, sans suppression. La marge de12Go n'est pas obtenue et la continuité reste exposée aux écritures concurrentes.

Aucune nouvelle suppression de données existantes. Le code et les seuils de production sont inchangés. Pour les événements futurs, rapprocher les annonces publiques sourcées de l'heure emitted_at des données conservées ; aucune conclusion d'information privilégiée à partir des seuls scores. L'étude n'est ni publiée ni clôturée ; clôture réservée à Benjamin.
