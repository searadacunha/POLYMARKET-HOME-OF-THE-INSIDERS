# Audit des deux sources

Lecture du 13 novembre 2026. Le code de `poly_data` a été lu, pas exécuté. Les pages Pendulum et six Parquet ciblés ont été téléchargés. Aucun logiciel tiers n'a été lancé avec un jeton.

## poly_data

Dépôt lu au commit [`136e129735c73bce3a3d59f20354417b188e47fd`](https://github.com/warproxxx/poly_data/commit/136e129735c73bce3a3d59f20354417b188e47fd) (8 septembre 2026, message « gif formatting »). L'étiquette `v1-final` pointe sur [`23d9138d334a3c7c7ec549bb2adf33b833334611`](https://github.com/warproxxx/poly_data/tree/v1-final) (27 avril 2026).

Le fichier `LICENSE` à ce commit commence par « GNU GENERAL PUBLIC LICENSE, Version 3 ». Le badge du README dit GPL-3.0. Le `pyproject.toml` déclare `license = { text = "MIT" }`. Les deux textes ne donnent pas le même droit. Ce dépôt n'en copie donc aucun module.

Le README actuel décrit un pipeline v2 en trois étapes : marchés CLOB, journaux `OrderFilled` via Envio HyperSync, puis jointure. Le contrat indexé est un seul : `0xe111180000d2663c0091e4f400237545b87b996b`, à partir du bloc `84_902_353`. Le code de `update_utils/update_chain.py` le dit, et il rappelle une migration le 28 avril 2026. Le contrat neg-risk `0xe2222d279d744050d28e00520010520000310f59` n'est pas dans la requête. Les colonnes écrites sont `timestamp`, `maker`, `makerAssetId`, `makerAmountFilled`, `taker`, `takerAssetId`, `takerAmountFilled`, `transactionHash`. L'index de journal, le hash d'ordre, les frais, `builder` et `metadata` sont décodés puis écartés.

Conséquence : une ligne de ce CSV n'est pas un journal on-chain identifiable. Deux `OrderFilled` d'une même exécution, le côté maker et le côté taker, peuvent être additionnés deux fois si l'on somme les lignes. Le README dit lui-même de filtrer sur `maker`. Le contrat peut apparaître comme `taker` lors d'un appariement qui passe par l'échange : ce n'est pas un portefeuille.

La v1 du même dépôt, conservée à `v1-final`, s'appuyait sur le sous-graphe Goldsky. Le README v2 dit que cette voie ne renvoie plus un historique complet. Elle ne couvre pas, dans le code v2 lu, les échanges antérieurs au 28 avril 2026.

HyperSync exige `HYPERSYNC_API` depuis le 3 novembre 2025. Ce secret n'est pas dans l'environnement. Le collecteur n'a pas été lancé. Les quatre fichiers de tests du dépôt (`tests/test_process_live.py`, `test_update_chain.py`, `test_update_markets.py`, `test_utils.py`) n'ont pas été exécutés : les lancer aurait installé `hypersync` et le reste de la chaîne, ce qui n'a pas été audité comme un programme à faire tourner.

## Pendulum Flow

Index lu le 13 novembre 2026 sur [archive.pendulumflow.com](https://archive.pendulumflow.com/). Le fichier machine est [llms.txt](https://archive.pendulumflow.com/llms.txt). La citation demandée par l'archive : pendulumflow, Polymarket Orderbook Archive, consulté le 2026-11-13, CC BY-NC 4.0. Les ères miroir PMXT sont en CC BY 4.0. AG6 ne publie pas de licence sur la page [comment citer](https://archive.pendulumflow.com/cite).

Fenêtres annoncées ce jour-là :

| Ère | Collecteur | Heures annoncées | Grade annoncé |
|---|---|---|---|
| V1 | PMXT | 2026-02-21T18 à 2026-04-16T05 | instantané |
| V2 | PMXT | 2026-04-13T19 à 2026-08-09T23 | instantané |
| V2 | AG6 | 2026-08-01T13 à 2026-08-15T09 | instantané |
| V3 | pendulumflow | 2026-08-18T06 à 2026-10-30T18 | « military grade » |
| V3.1 bêta | pendulumflow | 2026-10-27T00 à 2026-11-13T13 | bêta |

La page d'accueil dit que la publication V3 a environ treize jours de retard, et que quatre heures manquent : `2026-04-04T18`, puis `2026-06-11T04` à `2026-06-11T06`. Ces phrases sont celles du site. Elles n'ont pas été recomptées fichier par fichier.

La page [format V1](https://archive.pendulumflow.com/formats/v1) dit, d'après ses propres mesures : dernière heure avec des lignes le 2026-04-15T08 ; 21 objets vides ensuite ; environ 65 % des marchés qui ont tradé ont un carnet sur six heures tirées à l'avance, avec une fourchette de 32 % à 99 % ; 46 % à 48 % d'impressions « fantômes » jusqu'au 19 juin 2026, attribuées au relais du venue et non à l'archive ; pas de `transaction_hash`. Un carnet V1 ne joint donc pas une impression à une transaction, encore moins à un portefeuille.

Un objet V3 complet, `2026-10-30T18`, répond `content-length: 1552647208` octets. Il n'a pas été téléchargé. Le site demande d'éviter les téléchargements massifs pendant le passage en V3.1.

## Ce qui a été téléchargé

Trois heures d'aperçu V3.1, le 11 octobre 2026, de 00:00 à 03:00 UTC, sont publiées sous [preview/v3.1](https://archive.pendulumflow.com/preview/v3.1/). Six fichiers, choisis parce qu'ils font moins de 5 Mo, ont été lus :

| Fichier | Octets | SHA-256 |
|---|---:|---|
| `2026-10-11T00.science.parquet` | 742145 | `6b88bc7445756222801a240b18ae279e93a7a6938e4fa9747248d845f68748a4` |
| `2026-10-11T00.economy.parquet` | 4663222 | `5c510b1114122f549388a3e89b7bf9e089aa87c75779f807a9bde0e74ba5fa82` |
| `2026-10-11T00.earnings.parquet` | 79234 | `c90c9cd76ff29406ae93af472db7a9058df66aac5d7ad415cf7b2294ad8c8c74` |
| `2026-10-11T01.science.parquet` | 753804 | `02ed5a807741a8dee1e91f26d03c967459aa303458bc368432cab40c71a9da33` |
| `2026-10-11T01.economy.parquet` | 4591051 | `444fc7930001307aaa984acbd30d42651380498ec4ee61fb803fb8b1c1b68235` |
| `2026-10-11T01.earnings.parquet` | 79245 | `3c2441de290bc4d816793fe4f0af5702e1d1b74602177192deb2096adb76a0ed` |

Le pied de `science00` a été décrit par DuckDB. Il contient 29 colonnes, dont `source_witness`, `lead_lag_ns` et `spread`. La page [format V3.1](https://archive.pendulumflow.com/formats/v3.1) décrit un fichier maigre de 27 colonnes, avec la provenance à part. L'aperçu n'est donc pas le schéma V3.1 publié. Les comptes d'événements lus :

| Fichier | price_change | best_bid_ask | book | last_trade_price |
|---|---:|---:|---:|---:|
| science 00 | 112649 | 6726 | 1250 | 25 |
| science 01 | 118403 | 7564 | 941 | 37 |
| earnings 00 | 5105 | 743 | 363 | 10 |
| earnings 01 | 4916 | 864 | 299 | 41 |
| economy 00 | 761411 | 64569 | 6227 | 128 |
| economy 01 | 792562 | 55846 | 4521 | 112 |

Chaque `last_trade_price` de ces six fichiers a un `transaction_hash`, et aucun hash ne se répète dans un fichier. Ce hash est celui envoyé par le venue. Aucun reçu Polygon n'a été relu pour le confirmer. Les témoins `source_witness` se mélangent (`o`, `m`, `h`, `i`). L'heure utilisée ensuite est l'horodatage du venue, pas la différence d'arrivée entre machines : [llms.txt](https://archive.pendulumflow.com/llms.txt) dit que soustraire des `timestamp_received` de machines différentes mesure aussi le décalage des horloges.

Un carnet (`book`) porte des niveaux prix/taille. Une impression (`last_trade_price`) porte un prix, une taille, un côté et un hash. Un changement de carnet n'a pas d'adresse. Ces trois objets restent séparés.
