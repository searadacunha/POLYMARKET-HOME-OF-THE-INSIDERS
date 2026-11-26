# Registre de la recherche du 25 novembre 2026

Ce registre fixe ce qui a été cherché, ouvert, compté et laissé de côté. Il ne prétend pas couvrir les bases privées des entreprises d'analyse de chaîne.

## Dépôts GitHub

- Catalogue : 56 noms dans `data/catalog.json`.
- Fichiers ouverts : 13 dépôts.
- Dont le source au-delà du README : 6.
- Code concurrent exécuté : la fonction `luck_pvalue` de vsbtc, sur les 45 lignes figées.
- Publications lues : 10, dont la page ACDC du 20 août 2026 et la carte du jeu `vgregoire/polymarket-users`.
- Fichiers parquet comptés : `markets.parquet` 729 133 lignes, `events.parquet` 316 429 lignes. Les transactions n'ont pas été téléchargées.

Les requêtes du 25 novembre ont été passées avec `gh search repos`, plafonnées à 30, 20 et 20 résultats. Ce n'est pas une énumération de GitHub. La saturation cherchée est celle des dépôts qui publient une méthode, un test ou un résultat négatif, pas celle des bots de copie sans code de mesure. Plusieurs dizaines de dépôts « insider » du premier listing n'ont qu'un README ou un robot. Ils sont nommés dans le catalogue et n'ont pas été ouverts un par un. Les ouvrir tous n'aurait pas changé une hypothèse.

## Publications

Huit documents, détaillés dans `data/publications.json`.

Lecture substantielle, cinq :

1. Cardozo et Rivero-Wildemauwe, arXiv 2609.12878, septembre 2026. 588 millions de transactions annoncées. Non recomptées.
2. Anatomie des marchés présidentiels Polymarket, arXiv 2603.03136. Un marché, pas un milliard de transactions. 958 contre 391 millions USD en octobre pour Trump, selon le mode de volume.
3. Sirolly, Ma, Kanoria et Sethi, PDF du 6 novembre 2025. Wash trading estimé, sans vérité de terrain.
4. Chen Wang et coauteurs, papier de débordement. Environ 1,6 million de transactions sur le seul contrat Trump-YES, du 5 janvier au 5 novembre 2024.
5. Chainalysis, billet du 7 mai 2026. Essai de vendeur, sans liste de portefeuilles.

Extraits seulement, trois : message Inca du 9 juillet 2026, Reuters du 20 août 2026 sur l'ACDC, CoinDesk du 30 avril 2026 sur le mandat Chainalysis.

La page Inca `polymarket-insider-report` a été téléchargée. Le HTML ne contient pas le rapport. Le corps reste inaccessible sans le document que la page ne livre pas.

## Investigations du dépôt relues, pas reconstruites

Le verdict de bord, le benchmark du 20 novembre, le rapprochement Inca du 6 novembre, l'index de cas du 7 novembre, et le statut de la série hebdomadaire ont été relus pour ne pas contredire un chiffre déjà tenu. Les dossiers Maduro, Iran et Ballon d'Or n'ont pas été recalculés. Leurs montants publiés dans le README restent ceux du README.

## Donnée primaire nouvelle

Une seule collecte : la semaine ISO 2026-W47, après sa clôture, avec le collecteur déjà versionné. Journaux Polygon et Ethereum des flux enregistrés, échantillon de 856 adresses actives, grand livre de portefeuilles, dix tests du protocole figé tous non testables. Empreinte du rapport précédent vérifiée égale au fichier déjà dans `investigations/weekly-funding-intelligence`.

## Langues et licences

Les pages demandées par le propriétaire sont en français. Le code et les JSON de contrôle sont en anglais. Aucun jeu de données tiers n'a été recopié. Le texte des papiers n'est pas redéposé. Les README concurrents ont été lus via l'API GitHub et laissés hors du dépôt.
