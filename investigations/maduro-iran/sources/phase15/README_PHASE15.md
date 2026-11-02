# Phase 15 : README

Audit de la couverture et de la détection en direct. **Aucun signal, aucun ordre, SIG_HIST V1 inchangé, aucun processus existant modifié.** Résultat : voir `RAPPORT_PHASE15.md`.

## Rejouer

**1. Audits sur les données déjà enregistrées** (phases 11 à 14), environ 2 min :

```bash
python3 ~/Documents/Crypto/enquete_maduro_iran/scripts/p15_historique.py
```

**2. Enregistreur d'audit indépendant** (4 h prévues ; 2 h 26 réalisées le 01/10, à cause de la veille du Mac) :

```bash
python3 ~/Documents/Crypto/enquete_maduro_iran/scripts/p15_audit.py --live --heures 4
```

- deux connexions RTDS (A continue, B coupée 30 s toutes les 20 min) ;
- logs de la chaîne non filtrés et en-têtes de blocs.

**3. Analyse de l'enregistrement contre la vérité chaîne,** puis fusion des tables :

```bash
python3 ~/Documents/Crypto/enquete_maduro_iran/scripts/p15_audit.py --analyse --fusion
```

## Données

| Emplacement | Contenu |
|---|---|
| `donnees/brut_p15/` | `rtds_*.jsonl.gz`, `chain_*.jsonl.gz`, `evenements_*.jsonl.gz` : une ligne par message, avec l'heure locale en ns |
| `donnees/brut_p15/cache/` | caches de relecture des données brutes de la phase 11 et du mapping jeton vers marché (Gamma) |

**Lecture seule :** `donnees/brut_p11/` à `brut_p14/`.

## Fichiers

| Fichier | Contenu |
|---|---|
| `PROTOCOLE_P15.md` | vérités par champ, classes, critères de validation |
| `phase15_market_coverage.csv` | univers live et phase 8 contre P11, P12, P13, P14 ; nom résolu, outcome valide |
| `phase15_trade_coverage.csv` | rappel et précision par source, contre la vérité chaîne (audit live) et le data-api (période P11) |
| `phase15_latency.csv` | paires d'horodatages, avec leur nature |
| `phase15_duplicates.csv` | lignes répétées classées (vrai doublon, alias d'horodatage, fills distincts) |
| `phase15_price_audit.csv` | prix retenu par la règle du listener contre le prix de la chaîne, par trade |
| `phase15_wallet_audit.csv` | wallet retenu par la règle du listener contre le preneur de la chaîne, par trade |
| `phase15_watchlist_audit.csv` | wallets surveillés par processus et leurs trades vus |
| `phase15_end_to_end.csv` | trades suivis de la chaîne jusqu'à P14 (période P11 et audit live) |
| `phase15_reconnect.csv` | trous, coupures volontaires, silences, rattrapage |
| `phase15_sig_hist_replay.csv` | alertes SIG_HIST historiques : visibilité en direct avec les défauts mesurés |
| `phase15_oklahoma_timeline.csv` | reconstruction du cas Oklahoma |
| `phase15_alertes_live_audit.csv` | les alertes live du 01/10 (6 du listener P11, 8 lignes P13) contre le data-api |
| `phase15_watchdog.csv` | chiens de garde, vivant contre aveugle |
| `phase15_regression_maduro_iran.csv` | régression Maduro et Iran |
| `phase15_comptes8.csv` | les 8 comptes en direct |
| `phase15_marches_sans_conditionId_top.csv` | les plus gros marchés que RTDS envoie sans `conditionId` |

**Scripts :** `scripts/p15_audit.py`, `p15_analyse.py`, `p15_historique.py`.
