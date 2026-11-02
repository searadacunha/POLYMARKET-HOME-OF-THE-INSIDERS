# Reprise prospective après refus du plafond

30octobre2026. La chaîne actuelle est conservée, mais la capture supplémentaire est arrêtée explicitement :19 914 752octets/20 000 000, curseur682094,64reçus vérifiés. Le moniteur séparé continue de signaler le refus. Aucun nouveau dossier d'époque n'a été ouvert pour contourner la limite.

La base principale continue à collecter. Au relevé `prospective_backlog.json`,29observations source après le curseur restent en attente de scellement. Ce nombre n'est ni29alertes indépendantes ni une perte définitive prouvée ; la rétention ultérieure pourrait toutefois rendre une reprise complète impossible. Un rattrapage ne recréerait pas rétroactivement une preuve scellée à l'heure d'origine.

La reprise durable nécessite une décision de conservation, distincte du modèle. Proposition à préparer dans une nouvelle version séparée :

1. Préserver l'époque actuelle et son manifeste ; deux copies vérifiées sur supports indépendants et restauration contrôlée avant tout accord distinct de retrait local. Aucun support/copie de ce type n'est validé par cette mission.
2. Pour la prochaine époque, stocker les contenus identiques une seule fois, compresser les entrées et conserver des références vérifiables dans chaque reçu. Une simple déduplication des empreintes de dossiers ne suffit pas : les275observations du snapshot initial ont275empreintes matérielles distinctes. Il faut dédupliquer les contenus partagés entre captures, conserver la provenance et rendre les références manquantes explicites.
3. Mesurer taille et restauration d'une copie candidate hors production ; tester panne, lot partiel, données manquantes, remplissage et reprise. Maintenir le plafond global20Mo et la marge disque, sans effacer de preuve existante. Tant qu'une capacité vérifiée n'est pas disponible dans ce plafond, ne pas déclarer la conservation future opérationnelle.
4. Conserver le noyau/configuration gelés le30octobre14:30:21UTC. Nouvelle époque ou nouveau format ne doit pas être confondu avec une modification du score. Les anciens événements/dossiers restent séparés des premières découvertes futures.
5. Avant adjudication des prochains résultats, figer la définition des événements admissibles et de la première publication publique, les sources à archiver, les états « inconnu », les délais effectifs et les métriques. Comparer observations réellement émises aux annonces réellement observées. Le fait de gagner un pari n'est pas un label d'initié.

Plan proposé seulement : aucun archivage, retrait, changement de format, nouveau plafond ou nouvelle époque déployé. La surveillance de capacité et son état durable, eux, sont actifs.
