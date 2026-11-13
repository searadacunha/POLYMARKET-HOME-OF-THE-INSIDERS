# Compatibilité avec le dépôt

Le README public et `research_notes/relay-followup-2026-11-04/` ne sont pas modifiés. Le garde de publication les fige. Les enquêtes déjà notées, y compris [Maduro et Iran](../../investigations/maduro-iran/FINDINGS.md) et [Ballon d'Or](../../investigations/ballon-dor-wallets/README.md), ne sont pas réécrites.

L'adaptateur déjà présent dans [integrations/forensic-intelligence](../../integrations/forensic-intelligence/README.md) reste un contrôle de couverture et de grand livre, en bibliothèque standard. Le moteur nouveau est à côté, dans `integrations/quantitative_engine/`. Il ne remplace pas PolySentinel et ne change aucun seuil gelé.

## Ce que les sources ajoutent, et ce qu'elles ne peuvent pas faire

Le dépôt sait déjà rejouer des transferts, des reçus et des activités Data API sur les dossiers Maduro, Iran et Ballon d'Or. Il sait aussi que les contrats V1 vont jusqu'au 28 avril 2026 à 11:00 UTC et que les V2 commencent le 3 avril, d'après [l'audit CLOB de la phase 10](../../investigations/maduro-iran/sources/phase10/CLOB_DATA_AUDIT.md).

`poly_data` v2, tel que son code le décrit, n'ajoute pas ces historiques. Il commence au bloc 84 902 353, sur un seul contrat, sans index de journal. S'en servir pour une transaction de janvier, février ou octobre 2025 serait une affirmation fausse. La période du 3 au 28 avril 2026 est un chevauchement : les deux générations de contrats existent. Le moteur refuse de l'appeler une couverture V2 unique.

Pendulum ajoute le carnet, pas l'identité. V1 commence le 21 février 2026 à 18:00 UTC. Maduro (fin janvier 2026) et les flux Ballon d'Or / C7 d'octobre 2025 sont avant cette date. Iran (jusqu'au 28 février 2026) touche les derniers jours de V1 au calendrier. Ces heures n'ont pas été téléchargées. Même lues, elles n'ont pas de hash de transaction et manquent une partie des marchés, selon la page de format V1. Un mouvement de carnet ne désigne pas le portefeuille qui a posé l'ordre.

La Data API v2 du dépôt, documentée dans l'audit d'outillage du 6 novembre 2026, reste la voie des activités de portefeuille. Pendulum ne la remplace pas. `poly_data` ne la remplace pas non plus tant que le jeton HyperSync manque et que le schéma reste lossy.

## Pull requests récentes

[#42](https://github.com/searadacunha/POLYMARKET-HOME-OF-THE-INSIDERS/pull/42) est fusionnée. C'est un registre documentaire de signalements extérieurs, pas une nouvelle preuve RPC. [#43](https://github.com/searadacunha/POLYMARKET-HOME-OF-THE-INSIDERS/pull/43) est fusionnée. Elle enregistre KPMG, les midterms, XFM et l'incident d'octobre 2026, avec des contrôles qui refusent de promouvoir une p-value tierce. [#69](https://github.com/searadacunha/POLYMARKET-HOME-OF-THE-INSIDERS/pull/69) est ouverte le 13 novembre 2026 : une note de statut sur C7. Elle n'est pas fusionnée par ce travail.

## Base choisie

La base est `main` à `d8189e8040e7376e0e437272ed23252c8bd3fa90`.

`research/early-detection-20261113` et `investigation/followup-verification-20261104` n'ajoutent aucun commit à `origin/main` : le propriétaire l'a vérifié sur le Mac (0 commit d'avance). Le travail non publié est le dossier `monitoring/phi_monitor/`, maintenant dans cette branche, sans changement de seuil.

`fix-pr69-report` et `investigation/followup-verification-20261104` ne sont pas des refs distantes. La pull request #69 est la branche `audit/20261113-c7-superseded-status`. Elle n'est pas la base : elle ne fait qu'annoter deux notes. `investigation/followup-20261113` a les mêmes `STATUS.md` et `FINDINGS.md` que `main`.

Déjà contenues dans `main`, donc non refaites : `research/kpmg-iran-financial-links-20261107`, `research/x-leads-verification-20261106`, le rapport [Inca](../../research_notes/inca-crosscheck-2026-11-06/REPORT.md), les sorties pontées [Inca](../../research_notes/inca-bridged-exits-2026-11-06/REPORT.md) et le registre [TriAgent](../../research_notes/triagent-campaign/registry-2026-11-08/REPORT.md).

Pas prises comme base, parce qu'elles divergent et retardent `main` : `research/global-insider-forensics-20261102` (61 commits devant, 181 derrière), `research/forensic-intelligence-20261102`, et les trois branches TriAgent du 8 novembre. Leurs résultats écrits sont cités dans [le rejeu](REJOU_HISTORIQUE.md). Le dossier `integrations/forensic-intelligence/` de `main` reste le contrôle déjà en place. Il n'est pas recopié.
