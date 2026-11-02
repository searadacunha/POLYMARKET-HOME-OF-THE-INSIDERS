# Contrat prospectif à relire — aucun déploiement

Cette étude n'installe rien. `ana_evaluate.evaluate_dataset` accepte des objets
documentaires à la même structure que l'extraction. Avant de l'utiliser sur un
échantillon prospectif, il faut un **nouveau protocole** qui fixe la population et
les instants, et un collecteur audité qui renseigne les champs ci-dessous. Il ne faut
ni compléter cette étude après connaissance des issues, ni réinterpréter les anciennes
résolutions du bot comme dates de première information.

1. Enregistrer l'événement et le périmètre de décision avant l'annonce ; conserver
   toutes les entrées admissibles, y compris celles sans score. Sceller l'instant,
   la version des règles, les références de contenu et les raisons d'exclusion.
2. Archiver à la décision le sous-univers complet effectivement analysé, ses limites
   (cap, pagination, historique censuré), les marchés et les observations de trades.
   Une erreur ou une pagination partielle interdit `cohort_complete=true`.
3. Sélectionner témoins et achat focal uniquement à partir de cette archive. Les
   données de résultat sont une entrée séparée, jamais accessibles aux features.
4. Vérifier une première information officielle précise, sa provenance et sa
   datation UTC ; archiver la preuve contemporaine. `public_at` produit aujourd'hui
   par `news.resolution_state` ne satisfait pas ce contrat : c'est une date de lecture.
5. Vérifier séparément les tokens gagnants et leur correspondance au marché. Une
   simple chaîne `resolved` n'établit pas une cible token/issue.
6. Pour une étude économique distincte, reconstruire inventaire initial, achats,
   ventes, conversions, splits, merges, redemption, frais et exécution disponible.
   Le présent pipeline renvoie toujours `economic_return=null`.

Champs de la porte de publication : `first_public_information_verified`,
`public_at`, `timing_uncertainty_seconds`, `timestamp_basis`, `source_url`,
`evidence_id`, `contemporaneous_archive`. Les heures incertaines doivent conduire à
une exclusion ou à un protocole futur explicitant des bornes conservatrices ; le
protocole actuel exige une horloge exacte et n'est pas élargi après les résultats.

Champs de cible : `target_verified`, `winning_token_ids`, `observed_at`,
`source_url`, `evidence_id`. Champ de cohorte : `cohort_complete` avec justification
et archive contrôlable. Ces booléens ne remplacent jamais l'audit des preuves.

Les neuf scénarios synthétiques exercent le module de score copié puis les portes
et leur verdict. Ils montrent seulement que le pipeline sait distinguer les
scénarios construits ; ni précision réelle ni détection d'initiés n'en découlent.
