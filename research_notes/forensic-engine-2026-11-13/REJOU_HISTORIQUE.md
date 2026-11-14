> **Erratum du 14 novembre 2026.** Les « conclusions inchangées » ci-dessous désignent uniquement cette revue limitée des sources `poly_data` et PendulumFlow. Elles ne reflètent pas les découvertes de la PR #71 : C7 Nobel 2025 comporte des transferts intra-groupe nouvellement recoupés, une correction des achats de 152 311,84 à 212 874,45 USD et un second groupe financier. Voir [AUDIT_20261113.md](../../AUDIT_20261113.md) et [NEW_LEADS.md](../../NEW_LEADS.md). Aucun accès à une information privée n'est démontré.

# Rejeu des dossiers

Question posée : les données nouvelles changent-elles une conclusion déjà écrite ? Réponse, dossier par dossier : non. Aucun nouveau lien de portefeuille n'a été démontré. Le détail machine est dans [data/results.json](data/results.json), clé `historical_cases`.

## Maduro

Conclusion déjà écrite dans [FINDINGS.md](../../investigations/maduro-iran/FINDINGS.md) : flux du réseau à huit comptes confirmés ; signal prédéclaré non exploitable hors échantillon ; l'adresse `0x73e237f9` n'a pas d'activité Maduro avant le 30 avril 2026. La fenêtre de décision retenue ici va jusqu'au 31 janvier 2026.

`poly_data` v2 ne couvre pas cette date. L'archive Pendulum commence le 21 février 2026 à 18:00 UTC. Aucun fichier de cette fenêtre n'a été lu. Conclusion inchangée. Code : `NO_NEW_DATA_ON_THIS_CASE`.

## Iran

Même fichier de conclusions. Le timing reste une hypothèse, et la phase 2 comptait 128 acheteurs YES dans la fenêtre. La fin retenue est le 28 février 2026, donc avant la coupure du 28 avril. `poly_data` v2 ne s'applique pas.

Le calendrier V1 de Pendulum commence le 21 février 2026 à 18:00 UTC, donc les derniers jours se chevauchent sur le papier. Ces heures n'ont pas été téléchargées. La page de format V1 dit qu'il n'y a pas de hash de transaction et qu'une part importante des marchés tradés n'a pas de carnet. Un chevauchement non lu ne change pas le graphe de financement. Conclusion inchangée.

## Ballon d'Or 2026

Le [README du dossier](../../investigations/ballon-dor-wallets/README.md) reconstruit onze comptes nommés par la presse et un test collectif gelé. Les flux datés dans le suivi du 13 novembre, notamment les dépôts des 9 et 10 octobre 2025, sont antérieurs à toute ère Pendulum et à `poly_data` v2. Les fichiers sports du 11 octobre 2026, qui pourraient contenir un marché encore ouvert, n'ont pas été téléchargés : ce sont les gros fichiers de l'heure. Aucune nouvelle relation n'est démontrée. Conclusion inchangée.

## C7, Nobel 2025

Le [suivi du 13 novembre](../../investigations/followup-20261113/README.md) documente un financeur commun et des retraits Relay, lus le 12 novembre 2026. La fenêtre des 9 et 10 octobre 2025 est hors des deux sources. La pull request [#69](https://github.com/searadacunha/POLYMARKET-HOME-OF-THE-INSIDERS/pull/69), encore ouverte, ne fait qu'annoter un statut. Elle n'est pas fusionnée ici et n'est pas un apport de carnet. Conclusion inchangée.

## KPMG et les autres registres

[#42](https://github.com/searadacunha/POLYMARKET-HOME-OF-THE-INSIDERS/pull/42) et [#43](https://github.com/searadacunha/POLYMARKET-HOME-OF-THE-INSIDERS/pull/43) sont des registres documentaires. Le rapport KPMG est [ici](../../research_notes/kpmg-election-integrity-2026-11-07/REPORT.md). Sa fenêtre traverse la coupure d'avril 2026. Le moteur marque `WINDOW_CROSSES_CUTOVER_NOT_CLAIMED` : on ne peut pas dire que `poly_data` v2 couvre l'ensemble, et rien n'a été téléchargé pour ce dossier. La p-value tierce n'est pas rejouée. Conclusion inchangée.

## Lecture de carnet déjà faite, non recommencée

La branche `research/global-insider-forensics-20261102`, commit `34ff2846884981bf4bf06a364794168f402dc72a`, n'est pas dans `main`. Son `investigations/global-forensics/FINDINGS.md` et son `results/ORDERBOOKS.md` du 3 novembre 2026 restent la lecture de carnet à citer. Elle n'a pas été rejouée : elle avait déjà tiré plusieurs gigaoctets par requêtes de plages HTTP sur `r2.pmxt.dev` et `r2v2.pmxt.dev`.

Ce qu'elle a mesuré, et que ce travail ne contredit pas :

- F-007 : aux heures testées, le carnet public couvre des fenêtres Iran et Khamenei de février 2026, et pas Maduro (3 janvier), le Nobel d'octobre 2025, ni les heures Ballon d'Or testées en octobre 2026. Le marché de cessez-le-feu du 7 avril 2026 a 0 ligne dans 18 heures lues.
- F-014 : le 26 février 2026, trois achats Yes du fichier de septembre (mrs-joker, planktonbets, neodbs) paient l'ask visible ou moins, avec 21 566 à 28 355 dollars de profondeur d'ask à 2 cents, et le mid bouge d'un cent ou moins sur cinq minutes. La fiche le dit : description, sans groupe de comparaison, sans conclusion sur ce que quelqu'un savait.
- F-005 : sur 2 091 marchés résolus, le verdict gelé des entrées synchronisées est `NOT_SUPPORTED` sur les six fenêtres. Ce n'est pas une détection d'information privilégiée.
- Le même commit de `poly_data`, `136e129`, y est déjà classé référence seule, GPL contre MIT, sans le contrat neg-risk. HyperSync n'y a pas été utilisé non plus.
- Pendulum Flow y est « non confirmé » le 3 novembre. La page du 13 novembre confirme le miroir et les ères V3. Cela ne réécrit pas les heures PMXT déjà lues.

Les heures sports d'octobre 2026 sur Pendulum V3 n'ont pas été téléchargées ici. L'absence mesurée le 3 novembre sur les hôtes PMXT reste l'état cité pour ces heures-là.

## Synthèse

| Dossier | poly_data v2 | Pendulum lu pour le dossier | Lien nouveau | Conclusion |
|---|---|---|---|---|
| Maduro | non | non | non | inchangée |
| Iran | non | non, chevauchement V1 non téléchargé | non | inchangée |
| Ballon d'Or 2026 | non | non | non | inchangée |
| C7 Nobel 2025 | non | non | non | inchangée |
| KPMG | fenêtre à cheval, non revendiquée | non | non | inchangée |
