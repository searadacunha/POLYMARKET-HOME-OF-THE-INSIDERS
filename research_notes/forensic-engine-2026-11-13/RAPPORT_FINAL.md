# Rapport final

13 novembre 2026. Branche dédiée, sans fusion. Le README public n'est pas modifié.

## Exécuté

- Lecture du dépôt, des conclusions Maduro, Iran et Ballon d'Or, et des pull requests [#42](https://github.com/searadacunha/POLYMARKET-HOME-OF-THE-INSIDERS/pull/42), [#43](https://github.com/searadacunha/POLYMARKET-HOME-OF-THE-INSIDERS/pull/43) et [#69](https://github.com/searadacunha/POLYMARKET-HOME-OF-THE-INSIDERS/pull/69).
- Lecture du code `poly_data` au commit [`136e129`](https://github.com/warproxxx/poly_data/commit/136e129735c73bce3a3d59f20354417b188e47fd). La GPL-3.0 du fichier `LICENSE` contredit le MIT du `pyproject.toml`. Le programme n'a pas été installé ni lancé.
- Lecture de [archive.pendulumflow.com](https://archive.pendulumflow.com/), de [llms.txt](https://archive.pendulumflow.com/llms.txt), des pages de format V1 et V3.1, et de l'aperçu du 11 octobre 2026.
- Téléchargement de six Parquet, 10,9 Mo au total. Empreintes dans [l'audit](AUDIT_SOURCES.md).
- Score de 353 impressions avec DuckDB pour la lecture et le moteur pour le calcul. Heure 00 = découverte, heure 01 = validation.
- Treize tests unitaires hors ligne, plus `verify.py`, qui recalcule le résultat à partir de [data/scored_prints.jsonl](data/scored_prints.jsonl).

## Conçu, et pas branché sur un flux vivant

- Le promoteur d'alertes existe. Sur cet échantillon il retient 9 candidats et en émet 0. La classe de latence est `ARCHIVE_HOURLY` : une heure publiée avec du retard n'est pas une alerte instantanée.
- L'appariement maker/taker est testé sur des journaux synthétiques complets, avec index de journal. Il n'a pas été appliqué à un export `poly_data`, parce que cet export n'a pas d'index de journal et n'a pas été produit.
- Aucun collecteur en continu n'écoute le venue.

## Bloqué

- `HYPERSYNC_API` absent. Pas de backfill `OrderFilled`.
- Heures V1 de la fin février 2026 non téléchargées. Un objet V3 complet du 30 octobre 2026 fait 1 552 647 208 octets ; il n'a pas été pris.
- Fichiers sports de l'aperçu non pris.
- Aucun reçu Polygon n'a été rapproché des 353 hashs d'impression.
- Pas de clé d'API manquante autre que HyperSync. Rien n'a été payé.

## Passe complète

Le moniteur non publié est intégré sans changement de seuil. Sur les 102 000 trades des 13 portefeuilles et la seule bande de marché complète, il ne produit pas d'alerte : le plus gros acheteur des quinze minutes de l'ignition fait 18,9 % du flux, sous le seuil de 50 %. Aucun hash de trade n'est dans les 4 270 reçus, qui sont tous des transferts ERC-20. Février 2026 ne donne pas de population de contrôle. Le détail est dans [DONNEES_LOCALES.md](DONNEES_LOCALES.md).

## Données locales

Le correctif du 4 novembre a été lu hors branche. Il ne contient pas de montant absent de `main`, et son README n'est pas repris. `research/early-detection-20261113` reste absente du remote. Les archives Inca brutes sont sous `.local/`, ignorées par Git. Sur la bande de juin 2025, 12 portefeuilles autres que les cinq comptes nommés achètent aussi au moins 5 000 USDC de Yes avant le premier achat à 0,50. La décision est `NOT_DISCRIMINANT`. Le détail est dans [DONNEES_LOCALES.md](DONNEES_LOCALES.md). `poly_data` v2 et Pendulum ne couvrent pas juin 2025.

## Pattern

Aucun pattern nouveau ne passe la validation. Les trois hypothèses, consommation de profondeur, spread large et rafale d'impressions, sont `UNDERPOWERED` sur l'heure de validation. Les probabilités de Fisher sont 0,625, 0,857 et 0,333, au-dessus du seuil 0,05/3. Le détail est dans [PATTERNS.md](PATTERNS.md).

Ce n'est pas une probabilité d'information privilégiée. Les fichiers n'ont pas d'adresse. Un carnet ne nomme pas un portefeuille. Une impression gagnante après coup n'a pas été utilisée comme signal.

## Dossiers historiques

Aucune conclusion de `main` ne change. Maduro, Iran, Ballon d'Or 2026, C7 et le registre KPMG restent tels que les rapports cités les laissent. Iran a un chevauchement calendaire avec Pendulum V1 qui n'a pas été relu : la branche `research/global-insider-forensics-20261102` l'a déjà mesuré le 3 novembre sur PMXT (F-007, F-014), sans en faire une preuve d'information. Ce travail ne refait pas ce téléchargement. Le tableau est dans [REJOU_HISTORIQUE.md](REJOU_HISTORIQUE.md). Le choix de `main` comme base est dans [COMPATIBILITE.md](COMPATIBILITE.md).

## Limites qui restent

L'échantillon est trois petites catégories d'un aperçu de deux heures. Il ne représente pas le venue. Le schéma de l'aperçu n'est pas le fichier maigre V3.1 décrit par le site. Les miroirs exacts de carnet sont déjà retirés par l'archive : le volume n'a pas été sommé entre tokens complémentaires. Les témoins sont mélangés ; l'heure du venue a été utilisée, pas l'écart d'arrivée entre machines.
