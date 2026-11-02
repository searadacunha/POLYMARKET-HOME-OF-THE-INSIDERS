# Requêtes Iris à envoyer si une clé autorisée existe

**Aucune requête n'a été envoyée.** Aucune clé `IRIS_API_KEY` trouvée dans l'environnement ni dans les fichiers vérifiés, aucun compte créé. Envoyer ces adresses à un tiers les lui communique : c'est ta décision. Le moteur d'Iris est propriétaire, donc une réponse reste un indice à recouper, jamais une preuve. Méthodes et limites : `reports/sources_cinq_depots.md`.

Classées par gain d'information. Vérifier d'abord crédits et coût.

| # | Méthode | Cible | Ce que ça trancherait |
|---|---|---|---|
| 1 | `tx`, `trace` | `2UCgkFYwUKGceXb1VXABUFTUZiNrwUgUh6vDPDr9ae2MN9SEFB8GqLikvoHueeuavaoQ3AQspG72L8fiwd78LQRq` (VidenteRibeira) et `5jAnEGy7ZFNQCkWBWNXSVwU8K6FqvBLCtPyAA2Ls9NoTa85uj7WLAVdUQPrmkdbHD9mF4i1nfCcbLmd53WhrtVkJ` (cookedrice) | Ce qu'est le service `GxjcMTWW…` et ce qui sort de ces dépôts |
| 2 | `analyze` | `GxjcMTWWDcKx5sxnHkNfPtuTSfV9cLgVkw3G7KvMnvBW` | Étiquette du service à 1 % |
| 3 | `tx` | `0x2c0d0943a7874d99abbc28c4d4930407c8eaad006df45655f6e3ad0c2b808db3` (Wen), `0xc579ce36eea56ec37480b2d3c268f1a137af674c3cdc55c2d33f382a00840a32` (OuldLm3alem) | Étiquette de `0xee7ae85f…`, le service payeur commun |
| 4 | `tx` | Dépôts passant par `0x8894e0a0…d4e3` et `0x6bf18baf…` | Exchange derrière ces adresses à très fort nonce |
| 5 | `analyze` | `0x0ce9bdf38714143043b1d36de9bd90f7335bf06d`, `0xc1d13492285eb664951e201bf7c80c7c6318a1b5`, `0x58f298e3bf930886ab7639f4d71f892d5f1f0214` | Étiquette de ces services amont |
| 6 | `follow` | `0x3ab2206b98b01ba256dbdd4c50208bf17ab27d50` (après Wen), `0x8c5dc729…` (après Zoomman17) | Destination suivante des fonds déjà partis |
| 7 | `xchainWallet` | `CXVYMP5qxBENTNnqqmBAgvQB5wRLkcUBYPBDLFTeGrfJ`, `EnHRjTP4pKGkA4BC1yfoCNyUJcU3wapK1Gj8Us35PZ8B` | Rien à attendre tant que les fonds n'ont pas bougé : à garder pour plus tard |

Rapprochement de valeur annoncé par Iris pour ChangeNOW et FixedFloat : lire son score comme un candidat, et mesurer d'abord le taux d'accidents sur des dates décalées.
