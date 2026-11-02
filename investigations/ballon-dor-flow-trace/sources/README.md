# PolySentinel flow trace : financements et sorties des 11 comptes du Ballon d'Or 2026

Enquête historique indépendante, lue le 2 novembre 2026. Rien n'a été publié et aucune transaction n'a été émise. Une adresse n'est pas une personne : aucune identité civile n'est recherchée ni établie. Ces comptes sont des sujets d'investigation, pas des insiders démontrés.

Lire d'abord `reports/FUNDING_FORENSICS_FINAL.md`.

## Fichiers

| Fichier | Contenu |
|---|---|
| `reports/FUNDING_FORENSICS_FINAL.md` | Les 11 dossiers, la synthèse comparative et la matrice de liens |
| `reports/COMMON_FUNDERS.md` | Financeurs réellement partagés, 55 paires, comptes témoins |
| `reports/EXCHANGE_AND_PRIVACY_EXPOSURE.md` | Services touchés, niveau de preuve par service, XMR |
| `reports/CASHOUT_PATHS.md` | Destinations des retraits et soldes lus le 2 nov. |
| `reports/UNKNOWN_PATHS.md` | Ruptures de traçabilité et ce qu'il faudrait pour les lever |
| `data/funding_paths.csv`, `data/cashout_paths.csv` | Une ligne par saut : chaîne, actif, décimales, montant brut, source, cible, transaction, bloc, heure UTC, événement, service, niveau de preuve, seconde source |
| `data/service_attributions.csv` | Une ligne par service touché par dossier |
| `data/walk_edges.csv` | Tous les flux retenus par la marche, y compris hors chemin de dépôt |
| `data/service_labels_manual.csv` | Attributions mesurées à la main, avec leur justification |
| `graphs/funding_network.graphml`, `graphs/cashout_network.graphml` | Graphes séparés des entrées et des sorties |
| `evidence/` | Listes d'étiquettes publiques et documents officiels datés, avec empreintes ; enregistrements Relay extraits |
| `tests/test_forensics.py` | Contrôles sur les cas connus |
| `state/` | Cache HTTP (le point de reprise), journal des requêtes, résultats intermédiaires |

## Méthode

1. **Inventaire.** Les 11 dossiers, leurs clés et leurs adresses sont repris en lecture seule de `~/Projects/PolySentinel-investigation/cases/`.
2. **Historique complet.** Pour chaque clé, adresse de pont et destination : natif, transactions internes, tous les ERC-20. Etherscan v2 pour Ethereum, Polygon et Arbitrum, Blockscout pour Optimism, Solana RPC `api.mainnet-beta` pour Solana, en lisant aussi les comptes de jetons : une entrée sur un compte existant n'apparaît pas dans les signatures du propriétaire.
3. **Marche budgétée.** Vers l'amont et vers l'aval, seulement à travers des adresses de taille personnelle, avec 4 sauts au plus et 45 nœuds par sens et par dossier. Une adresse est arrêtée, avec la raison écrite, si elle porte une étiquette de service, un nonce d'au moins 1 000, ou au moins 400 contreparties réelles à la lecture.
4. **Ponts.** Un lien entre chaînes repose uniquement sur l'enregistrement du protocole : Relay `requests/v2` (route retirée le 24 nov. 2026, réponses conservées), deBridge DLN, Circle CCTP, et jamais sur une ressemblance de montant ou de date.
5. **Clés, y compris avant le premier retrait.** Les sorties des clés sont lues dès 30 jours avant le premier dépôt, et chaque adresse personnelle rencontrée est testée : possède-t-elle un Deposit Wallet Polymarket ? Le calcul CREATE2 retrouve les 11 wallets connus sur 11 (`tools/proxy_check.py`).
6. **Ce qu'on ne compte jamais comme un financement.** Une frappe depuis l'adresse zéro, le retour d'un échange fait par l'adresse elle-même, même relayé (EIP-7702, MetaMask), et les jetons hors liste, qui sont surtout du spam d'empoisonnement. Ces lignes restent lisibles dans les données brutes.
7. **Comptabilité.** Le découpage entre plusieurs entrées suit un PEPS (premier entré, premier sorti) en dollars de stablecoin. C'est une convention comptable, pas la preuve que ces dollars précis ont circulé : la colonne `alternatives` le signale.
8. **Rapprochement.** Chaque mouvement de pUSD et de position de chaque wallet est classé : dépôt, retrait, remboursement de marché, exécution de carnet, prime, transfert direct. Le solde calculé est comparé au solde lu sur la chaîne.
9. **Paires.** Toutes les paires sont testées sur l'historique brut des adresses propres : transfert direct, adresse de taille personnelle partagée, service partagé. Le même lecteur tourne sur des comptes témoins.

## Niveaux de preuve

| Niveau | Sens |
|---|---|
| `CHAINE` | Démontré par la chaîne : un transfert lu dans un reçu ou une trace |
| `PROTOCOLE` | Lien entre chaînes porté par l'enregistrement du protocole |
| `CHAINE+ATTRIBUTION` | Le flux est démontré, le nom du service repose sur une étiquette ou une mesure |
| Hypothèse | Compatible avec les faits, non démontré. Jamais écrite comme une conclusion |
| Inaccessible | Exigerait des données privées : registre d'un exchange ou d'un service |

## Reproduire

```bash
cd ~/Projects/PolySentinel-flow-trace
export PYTHONDONTWRITEBYTECODE=1   # n'écrit aucun .pyc dans les dossiers lus
python3 tools/labels.py            # contrôle des étiquettes
python3 tools/blockscout_tags.py   # tags de service (metadata.tags des listes de transactions)
python3 tools/walk.py              # rejoue le cache, ne réinterroge que le manquant
python3 tools/reconcile.py
python3 tools/bridges.py
python3 tools/pairs.py
python3 tools/proxy_check.py
python3 tools/gxjc.py
python3 tools/bsc_nonce.py 0xc852b0938f5ad79b640d105ed11c14499454af26
LABELS_PUBLIC_ONLY=1 python3 tools/comparators.py && LABELS_PUBLIC_ONLY=1 python3 tools/comparators.py named
LABELS_PUBLIC_ONLY=1 python3 tools/compare_rates.py
python3 tools/build_data.py && python3 tools/verify.py
python3 tools/build_reports.py
python3 tests/test_forensics.py
python3 tests/test_claims.py       # chaque chiffre et préfixe des récits doit exister dans les données
```

Une réponse lue est gardée en cache pour toute l'étude : l'ensemble est un instantané du 2 nov. 2026. Pour relire la chaîne à une autre date, vider `state/http_cache`. Lecture à travers `~/Projects/PolySentinel-investigation/state/http_cache`, sans y écrire.

La clé `ETHERSCAN_API_KEY` vient de `~/Downloads/.env`. Elle n'entre ni dans le cache, ni dans `state/requests.jsonl`, ni dans ces fichiers. Aucune autre clé n'est utilisée : la clé Helius, partagée avec un bot en service, n'a pas été touchée.

## Ressources

Un worker réseau au départ, deux au plus. Garde-fous dans `tools/net.py` : pause sous 14,5 Go libres, si le swap monte de 300 Mo, si le battement de PolySentinel a plus de 180 s, et si le cache dépasse 600 Mo. Aucune surveillance permanente n'a été lancée.

## Limites générales

- **BSC et Base :** pas d'historique gratuit. Etherscan v2 demande un plan payant pour ces chaînes et `base.blockscout.com` répond par un contrôle anti-robot, qui n'a pas été contourné. Seuls les reçus connus, les nonces et les soldes y sont lus.
- **Étiquettes :** elles disent ce qu'une source a écrit. Trois sources publiques : deux listes, dont une de 2023, et les tags Blockscout, lus pour les adresses rencontrées autour des dossiers seulement. Les comptes témoins n'utilisent que les listes, pour rester comparables (`LABELS_PUBLIC_ONLY`). KuCoin Hot Wallet 2 sur Solana repose sur la seule source Orb, et la liste officielle de KuCoin (2022) ne contient aucune adresse Solana.
- **Absence de preuve :** elle n'est jamais convertie en preuve d'absence. Une trace qui s'arrête à un service ne dit rien de ce qui se passe à l'intérieur.
- **Comptes témoins :** échantillon partiel et traits choisis après avoir lu les dossiers, donc exploratoires.
- **Relecture :** une session Claude parallèle, chargée de corriger le rapport d'origine, a relu sur la chaîne le wallet supplémentaire et signalé deux points (`0x48ec106c…`, tags Blockscout). Même famille de modèle : ce n'est pas un audit indépendant.
- **Incident :** un import de `tools/net.py` de l'enquête d'origine a écrit le 2 nov. à 09:26:59 UTC un fichier `tools/__pycache__/net.cpython-314.pyc` dans son dossier. Je l'ai retiré aussitôt. C'est la seule écriture dans ce dossier ; ensuite `PYTHONDONTWRITEBYTECODE=1`, et plus aucun import depuis ce dossier sauf `collective/code/rows.py`, sans bytecode.
