# Audits indépendants, phase5

Restitution par le coordinateur des rapports remis par les agents en lecture seule. Les agents ont déclaré n'avoir ouvert ni les résultats, ni les labels, ni l'ancienne étude. Les scripts analytiques n'ont pas été exécutés par eux.

## Conformité : blind_protocol_final

PASS final, après deux passes code seul puis plan. Les deux écarts pré-gel sont clos : description de la disponibilité hypothétique alignée sur l'adaptateur en mémoire ; fractions de pairs inconnues sans pair. Garde de sceau exact R1/R2, SHA avant labels, capacité avant calcul/périodique R1/avant écriture et création exclusive vérifiés. Gel officiel44/44 intact, SHA28350d58c4942cc6129ccddebb92b2a991e842d0590e41a64dc0ab2156912a8d. ContrôlesV4/V3 lus PASS7chacun, non relancés. Registre12lignes intact au contrôle, total provisoire3718 ; R1/R3 pas encore terminés. Ni achèvement ni reproduction ni conclusions validés par ce PASS.

## Fuites : blind_leakage_final

PASS, aucun bloquant/majeur ouvert. Vérification indépendante44/44 empreintes et index hors dépôt. Source observed_at et scénarios hypothétiques séparés ; entrées futures exclues ; pas de label injecté démontré. Garde de sceau complété avant gel, contrôles lus. MINEUR conservé : les booléens résumés R3 portent sur wallet « au moins un événement » ; rapport primaire doit fournir toutes les paires wallet-événement. A0 NON_ESTIMABLE ; A1 strate lexicale censurée choisie après affaire. Cinq lignes d'entrée ont été lues en projection sans identités/labels uniquement pour vérifier la chronologie d'observation, aucun test statistique ajouté. Aucun résultat ni registre lu ; intégrité du registre laissée au coordinateur.

## Échecs silencieux : cache_refutation

PASS statique, aucun bloquant/majeur. Gel44/44 indépendant, SHA identique. Garde capacité, écriture xb, manifeste commun R1/R2, erreurs JSON/gzip propagées, réconciliation de préparation, sceau exact R1/R2 et inconnus sans pairs vérifiés. Pas de certification nouvelle de la collecte antérieure interdite. Passe finale :44comparaisons d'intégrité, aucun test/donnée réelle analysée. Passe antérieure indépendante :256comparaisons synthétiques (240dépendances de synchronie,16calendriers), modèle indépendant sans import étude, toutesPASS ; six vérifications dehash. Résultat et script conservés dans controles/read_only_adverse.* et enregistrés.

## Statistiques : blind_stats_final

PASS pour méthode descriptive conditionnelle, pas performanceglobale. R1 compte unités wallet-événement-tick dense via pondération, deux métadonnées et diagnostics finaux ; strictobserved+1. R2=9N ; R3=4L. n effectif externe=1 affaire. Appariement même événement/jour/tranche fixe deprix ne contrôle ni activité, ni réseaux, ni historique hors corpus. Pas dep-value, pas de véritéterrain ; Bonferroni est un compteur conservateur et ne valide pas un test inexistant.

MAJEUR de portée retenu : nul/moyen/fort sont troisfixtures déterministes ; les graines vérifient équivalence du code, pas puissance ou calibration de fauxpositifs. La conclusion doit le dire et ne peut les transformer en validation statistique. Une contrelecture neuve de ce point a été demandée. MINEUR : R0structurel a été calculé avantgel, donc ne pas écrire «aucun calcul réel avantgel» ; aucunrejeu de détection n'a précédé le gel. Au contrôle,12lignes dont10synthétiques et2réelles,3718comparaisons ; complétude finale provisoire en attenteR1/R3.

## Porte restante

Terminer R1/R3, recompter le registre, vérifier les deux reproductions fraîches et soumettre les conclusions à deux audits indépendants. Aucun PASS ci-dessus n'est une démonstration de détection.

## Contre-examen neuf : power_refutation

Constat établi, non bloquant pour A1 descriptive explicitement sans performance. Trois fixtures fixes nul/moyen/fort ; graines exclusivement pour équivalence. MINEUR : le libellé gelé «fixtures nul/moyen/fort plusieurs graines» est plus large que les contrôles exécutés. Signaler cette déviation dans les conclusions, ne jamais affirmer une puissance mesurée. Seuls quatre fichiers de code/plan/contrôles lus, aucun résultat/label/registre ; aucune exécution ni écriture. Une lecture rg a été refusée par le verrou, aucun contournement. Le gel reste inchangé.

## Décompte final, blind_stats_final

Réserve de complétude levée : registre14lignes intact,10synthétiques et4réelles. R0=1, R1=36456007, R2=3717, R3=44 ; total36459769. Seuil seulement comptable0,05/N=1,37e-9, aucune p-value, n effectif externe1affaire. Résultats/labels non consultés par cet auditeur, aucune écriture dans étude.
