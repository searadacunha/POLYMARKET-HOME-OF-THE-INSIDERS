# Phase 4 : attribution du service et séparation client / infrastructure

Date : 29/09/2026 (heures UTC).

**Annexes du dossier `phase4/`**
- `16_paiements_service.csv` : remplace `15_paiements_service.csv`.
- `0x44b6f8de_flux_reels.csv` : flux réels de `0x44b6f8de`, empoisonnement exclu.
- `3b6dcfde_entrees.csv`, `3b6dcfde_sorties.csv`.
- `famille_service.csv`.

**Couverture**
- Historiques complets, paginés par bloc, pour :
  - la trésorerie, sur Ethereum, Polygon et Arbitrum ;
  - les 4 payeurs stablecoin ;
  - les 2 payeurs ETH de 2e génération (465 529 et 471 426 transactions) ;
  - `0x44b6f8de`.
- Contrôle croisé sur 103 adresses EVM du réseau (listes de transactions natives, internes et de jetons) : recherche de tout paiement venant d'une des 12 adresses de la famille.
- Seuls les contrats officiels USDT, USDC, USDC.e et USDT0 sont comptés. Les faux jetons (USDС cyrillique, UЅDT, etc.) et les transferts de valeur nulle sont exclus, car ce sont des empoisonnements d'adresse.

---

## 0. Corrections apportées à la phase 3

1. **16 paiements du service vers le réseau, et non 15.** Le 16e est chronologiquement le premier.
   - Il s'agit de 0,01 ETH envoyé le **09/07/2025 à 06:04:35** par le payeur ETH `0x0e9e3919` à `0x420d62bf`, le wallet qui a alimenté `0x44b6f8de`.
   - Hash : `0x23d8c3c533029711723b1418f0184728905afaae0c5d2add1e4be108f4edbc20`.
   - Il n'avait pas été vu parce que les payeurs ETH n'étaient pas encore identifiés.
2. **La famille compte aussi des payeurs ETH.**
   - 2e génération : `0x974413b8` et `0x9bdbbd6f`.
   - 1re génération probable : `0x0e9e3919`.
3. **La trésorerie a 25 destinations stablecoin sur Ethereum, pas 156.** Les 156 comptaient des événements d'empoisonnement de valeur nulle.
4. **4 715,00 USDT revient 17 fois, vers 11 destinataires, dont 10 hors réseau** (et non 9 destinataires).
5. **Toute l'activité Polygon de `0x44b6f8de` est de l'empoisonnement** : faux USDT et faux USD Coin, adresses sosies. Aucun flux réel n'existe sur Polygon.
6. **Le rôle de `0xf4c0cfbc` n'est pas démontré** : il était présenté comme un « collecteur probable ». C'est un compte EIP-7702 alimenté surtout par deux adresses (138 transferts chacune). Rôle INCONNU.

---

## 1. Réponses directes (§1 de la mission)

**A. Qu'est réellement `0x3b6dcfde` ?**
- C'est la trésorerie centrale d'une plateforme custodiale grand public, identité INCONNUE. Voir la section A pour la classification et les preuves.
- Elle reçoit :
  - la liquidité institutionnelle : Coinbase Prime 1 et 2, Kraken HW5, Circle, OKX, FalconX, Bitstamp ;
  - les dépôts des clients, par l'intermédiaire de deux collecteurs.
- Elle alimente :
  - des hot wallets payeurs ;
  - ses propres comptes de dépôt chez ces plateformes.

**B. et C. Que sont `0x4a9a1675` et `0xb7152d59` ?**
- Ce sont les deux hot wallets payeurs **stablecoin** de 2e génération de cette plateforme.
- Ils sont jumeaux à tous points de vue mesurés : même financeur à 100 %, même date de départ, même volume, mêmes montants, mêmes heures.
- Ils ont été démarrés le **même jour (11/11/2025)** que les deux payeurs **ETH** de 2e génération, `0x974413b8` et `0x9bdbbd6f`.

**D. Pourquoi ces couches existent-elles ?** INFERÉ : c'est l'architecture standard d'une plateforme custodiale.
- **Dépôts** : adresses à usage unique → collecteur.
- **Trésorerie** : pivot de liquidité avec les plateformes institutionnelles et entre chaînes (via `0xba8c2284` → Stargate, Synapse).
- **Payeurs** :
  - séparés par actif (stablecoins d'un côté, ETH de l'autre) ;
  - doublés, pour répartir la charge : ~128 000 paiements stablecoin et ~455 000 paiements ETH par wallet ;
  - réapprovisionnés par petites tranches (~1 200 fois chacun), ce qui limite le solde exposé ;
  - remplacés par génération : la 1re génération s'éteint le 04/12/2025, 23 jours après le démarrage de la 2e.

**E. Les paiements vers les 8 comptes représentent-ils un même client, plusieurs clients, une même entreprise ou des clients indépendants ?**
- Ce n'est pas déterminable avec les données publiques. Les éléments sont présentés séparément en section D.
- Le fait mesuré le plus fort est le suivant : **les 5 adresses du réseau payées par le service ont toutes des transferts directs avec `0x44b6f8de`**, et la lignée de gas de `0x44b6f8de` part d'un payeur du service.
- Seuls 2 des 8 comptes (Chiwawas et 154x838hjd6) sont alimentés par le service.
- Formulation autorisée : **« Les données établissent un lien financier via le même service, mais ne permettent pas d'établir que les bénéficiaires ont le même propriétaire. »**

**F. Existe-t-il une preuve publique qui relie le service à une entité connue ?**
- **Non.** Les sources consultées sont :
  - les étiquettes Etherscan et Polygonscan des 12 adresses de la famille : aucune ;
  - le jeu d'étiquettes public brianleect (29 945 adresses) : aucune ;
  - une recherche web sur les adresses exactes : seulement des pages d'explorateurs, aucune mention, aucun GitHub, aucune documentation.
- Rappel : une absence de résultat n'est pas une preuve d'anonymat.

---

## 2. `0x3b6dcfde` : structure

### 2.1 Entrées (Ethereum, USDC et USDT officiels : 276 101 967 $, 257 expéditeurs après filtrage de 182 sosies)

| Source | Étiquette / rôle | Montant | Période | Actif | Fréquence | % |
|---|---|--:|---|---|--:|--:|
| `0xcd531ae9` | Coinbase Prime 1 | 104 097 269,85 | 2024-12-28 → 2026-09-26 | USDC/USDT | 714 | 37,70 |
| `0xceb69f63` | Coinbase Prime 2 | 63 426 500,00 | 2024-01-31 → 2025-06-05 | USDT | 624 | 22,97 |
| `0xaa8ba7d4` | Kraken: Hot Wallet 5 | 58 899 934,24 | 2025-11-07 → 2026-09-29 | USDT | 522 | 21,33 |
| `0x55fe002a` | Circle | 17 440 038,37 | 2024-05-16 → 2025-07-31 | USDC | 36 | 6,32 |
| `0xabe7931e` | collecteur de la famille (2e gén.) | 11 707 294,84 | 2025-04-18 → 2026-09-28 | USDC/USDT | 259 | 4,24 |
| `0xf4c0cfbc` | rôle INCONNU (EIP-7702) | 6 618 497,78 | 2026-06-10 → 2026-09-28 | USDT | 39 | 2,40 |
| `0x7f227df2` | collecteur de la famille (1re gén.) | 5 000 123,53 | 2024-07-05 → 2025-04-15 | USDC/USDT | 96 | 1,81 |
| `0x5041ed75` | OKX 7 | 4 374 404,16 | 2024-07-05 → 2024-12-19 | USDC/USDT | 16 | 1,58 |
| `0x959bd5bf` | client Circle non identifié | 2 000 000,00 | 2025-08-03 | USDC | 1 | 0,72 |
| `0x48ec5560` | Bitstamp: Wallet | 943 292,00 | 2024-10-20 → 2024-11-20 | USDC | 7 | 0,34 |
| `0xba8c2284` | rééquilibrage de la famille | 858 590,62 | 2024-08-26 → 2026-09-11 | USDC/USDT | 6 | 0,31 |
| `0x89e51fa8` | Kraken 7 | 400 258,73 | 2025-04-08 | USDT | 2 | 0,14 |
| `0x7eb6c83a` | OKX 20 | 135 540,55 | 2024-10-18 → 2025-01-18 | USDC | 2 | 0,05 |

- **Concentration des sources** : top 5 = 92,6 %, top 10 = 99,4 %, top 20 = 100,0 %.
- **Coinbase Prime 1 + 2** = 60,67 %.
- **Entrées ETH** : 74 227,78 ETH, venant de :
  - FalconX 1 : 38 314,68 ETH, 136 transferts ;
  - Coinbase Prime 1 : 12 298,67 ;
  - collecteur `0xabe7931e` : 11 453,20, 236 transferts ;
  - Coinbase Prime 2 : 11 168,68 ;
  - Bitstamp 61 : 263,0.
- **Polygon** : 19,75 M$, dont 91,4 % de `0x166716c2` (hot wallet non identifié, 724 287 tx, utilise CCTP) ; les collecteurs pèsent 3,2 %.
- **Arbitrum** : 0,28 M$ de `0x463f5d63`.

### 2.2 Sorties (Ethereum, 275 803 137 $, **25 destinations**)

| Destination | Rôle | Montant | Période | Actif | Fréquence | % |
|---|---|--:|---|---|--:|--:|
| `0xb7152d59` | payeur stablecoin 2e gén. | 44 253 053,65 | 2025-11-11 → 2026-09-29 | USDC/USDT | 1 232 | 16,05 |
| `0x4a9a1675` | payeur stablecoin 2e gén. | 44 040 200,00 | 2025-11-11 → 2026-09-29 | USDC/USDT | 1 221 | 15,97 |
| `0xb93e3d70` | payeur stablecoin 1re gén. | 34 005 444,21 | 2024-05-21 → 2025-12-04 | USDC/USDT | 809 | 12,33 |
| `0x26c50e67` | payeur stablecoin 1re gén. | 32 977 099,99 | 2024-05-21 → 2025-12-04 | USDC/USDT | 790 | 11,96 |
| `0x2313c810` | dépôt OKX (étiquette Etherscan) | 32 534 264,67 | 2024-05-21 → 2025-03-27 | USDT | 330 | 11,80 |
| `0x51481afd` | dépôt Coinbase Prime (INFERÉ : balayé vers Coinbase Prime 1) | 28 440 102,01 | 2024-05-22 → 2025-08-03 | USDC | 17 | 10,31 |
| `0x4ce15078` | dépôt OKX (INFERÉ : balayé vers OKX Hot Wallet 5) | 22 847 448,87 | 2025-03-30 → 2026-01-26 | USDT | 235 | 8,28 |
| `0xba8c2284` | rééquilibrage cross-chain (Stargate, Synapse) | 16 458 534,12 | 2024-06-13 → 2026-09-22 | USDC/USDT | 119 | 5,97 |
| `0xff3cf229` | dépôt Coinbase Prime (INFERÉ) | 5 780 858,00 | 2025-01-22 → 2025-01-31 | USDC | 3 | 2,10 |
| `0xeb1d71ae` | contrat de dépôt Bitstamp (INFERÉ : balayé vers Bitstamp 2) | 4 000 100,01 | 2024-08-08 → 2025-01-18 | USDC | 3 | 1,45 |
| `0x47ef369e` | dépôt Coinbase Prime (INFERÉ : balayé vers Coinbase Prime 2) | 3 799 465,00 | 2024-07-05 → 2025-01-18 | USDT | 10 | 1,38 |
| `0xd2f3b47f` | dépôt FalconX (INFERÉ : balayé vers FalconX 1) | 3 073 484,55 | 2025-12-11 → 2026-07-09 | USDC | 3 | 1,11 |
| `0x7afc12c8` | MoonPay 7 | 2 000 000,00 | 2025-08-29 | USDC | 1 | 0,73 |
| 12 autres | dont 4 petits destinataires récurrents de rôle INCONNU (`0x6bde4842` 50 ×, `0x7df079d2` 33 ×, `0x377428d0` 7 ×) | 1 592 632 | | | | 0,58 |

- **Concentration des sorties** : top 5 = 68,1 %, top 10 = 96,2 %, top 20 = 100,0 %.
- **Destinations** : 25 au total, dont 18 récurrentes (au moins 2 transferts) et 7 à paiement unique.
- **Répartition** :
  - les 4 payeurs stablecoin reçoivent 56,3 % ;
  - les comptes de dépôt chez des plateformes, 37,2 % ;
  - le rééquilibrage, 6,0 %.
- **Sorties ETH** : 73 832,96 ETH vers 15 destinations, dont 99,6 % vers les deux payeurs ETH :
  - `0x974413b8` : 36 792,58 ETH, 1 241 transferts ;
  - `0x9bdbbd6f` : 36 763,13 ETH, 1 229 transferts.
- **Polygon** : 100 % des sorties vont aux 4 payeurs stablecoin (à ~25 % chacun).

### 2.3 Classification (chaque catégorie testée)

| Catégorie | Pour | Contre | Verdict |
|---|---|---|---|
| Exchange hot wallet | volume ; plateformes institutionnelles | ne paie jamais d'utilisateur final : 25 destinations, top 10 = 96,2 % ; ses payeurs, eux, paient > 260 000 adresses | non |
| OTC | FalconX, Bitstamp, Coinbase Prime | aucune contrepartie de négoce identifiable ; flux entrants de dépôts clients (adresses à usage unique) ; sorties vers ses propres hot wallets | non démontré |
| Withdrawal processor | les 6 payeurs en sont (paiements médians 118 $ et 0,035 ETH) | la trésorerie elle-même ne paie pas les clients | rôle des payeurs, pas de la trésorerie |
| Payment processor / aggregator | dépôts clients agrégés par collecteurs (99 % d'adresses à usage unique, médiane ~200 $), paiements de masse | rien ne distingue « processeur pour marchands » de « plateforme avec comptes clients » ; aucune facture ni marchand visible | compatible, non démontré |
| Corporate treasury | pivot entre collecteurs, payeurs et comptes chez Coinbase Prime, Circle, OKX, Kraken, FalconX, Bitstamp, MoonPay ; aller-retours avec ces plateformes | aucun | **meilleur ajustement : trésorerie d'une plateforme custodiale grand public**, type exact (exchange, wallet, néobanque, jeu, processeur) INCONNU |

**Clients de la plateforme** : 107 626 bénéficiaires distincts pour les 4 payeurs stablecoin et 171 676 pour les 2 payeurs ETH de 2e génération, soit 261 508 au total. 6 274 bénéficiaires ont reçu au moins 4 paiements étalés sur plus de 3 mois : le retrait répété est un comportement courant chez ce service.

---

## 3. `0x4a9a1675` contre `0xb7152d59`

| Mesure | `0x4a9a1675` | `0xb7152d59` |
|---|---|---|
| Financeur | trésorerie 100 % (44 040 200 $ Ethereum, 4 948 070 $ Polygon) | trésorerie 100 % (44 253 054 $, 4 933 070 $) |
| Période | 2025-11-11 → 2026-09-29 | 2025-11-11 → 2026-09-29 |
| Réapprovisionnements | 1 221 | 1 232 |
| Paiements (≥ 1 $) | 128 076, soit 43,96 M$ | 127 608, soit 44,16 M$ |
| Bénéficiaires | 38 660 | 38 577 |
| Médiane | 118,25 $ | 117,12 $ |
| Montants les plus fréquents | 15,58 · 17,09 · 17,08 · 44,86 · 93,41 | 15,58 · 17,09 · 17,08 · 44,86 · 15,59 |
| Chaînes / actifs | Ethereum USDC+USDT ; Polygon USDC+USDT0 depuis le 08/01/2026 | identique |

**Similarités mesurées**
- Jaccard des bénéficiaires = **0,2746**, soit 16 642 communs sur 60 595.
- 47 des 50 montants les plus fréquents sont communs.
- Corrélation des profils horaires = **0,998**.
- Chevauchement temporel = 100 %.
- Financeurs : 100 % de chevauchement (trésorerie seule ; le reste est de la poussière).
- Réapprovisionnements alternés : 1 770 alternances sur 2 452 réapprovisionnements consécutifs ; 136 réapprovisionnements jumeaux à moins de 10 minutes l'un de l'autre ; écart médian de 123 min.

**Différences mesurées**
- Clients exclusifs : 22 018 pour `0x4a9a1675` et 21 935 pour `0xb7152d59`.
- Aucune différence de chaîne, d'actif, d'horaire ou de contrat.
- Un client du service peut être payé indifféremment par l'un ou l'autre.

**Comparaisons de référence**
- 1re génération (`0xb93e3d70` / `0x26c50e67`) : Jaccard 0,2563.
- Entre générations : Jaccard 0,036 à 0,038.
- Payeurs ETH `0x974413b8` / `0x9bdbbd6f` : Jaccard 0,2332.
- Seuls 9,5 % des bénéficiaires ETH sont aussi payés en stablecoins par 4a9a ou b715.
- **Conséquence pour l'enquête** : l'identité du payeur (4a9a ou b715) ne porte **aucune information sur le client**.

---

## SECTION A : identification des services

| Address | Role | Evidence | Confidence |
|---|---|---|---|
| `0x3b6dcfde` | trésorerie centrale d'une plateforme custodiale grand public | §2 : 276,1 M$ et 74 228 ETH entrés ; 25 destinations stablecoin ; collecteurs alimentés à 99 % par des adresses à usage unique ; comptes de dépôt chez Coinbase Prime, OKX, FalconX, Bitstamp ; Coinbase Prime et Circle Mint réservés aux entreprises | structure : haute ; identité : nulle |
| `0x4a9a1675`, `0xb7152d59` | payeurs stablecoin, 2e génération | §3 | haute |
| `0xb93e3d70`, `0x26c50e67` | payeurs stablecoin, 1re génération | 91 % financés par la trésorerie ; ~82 000 paiements chacun ; Jaccard 0,2563 ; s'éteignent le 04/12/2025 | haute |
| `0x974413b8`, `0x9bdbbd6f` | payeurs ETH, 2e génération | 100 % trésorerie ; démarrés le 11/11/2025 comme 4a9a et b715 ; ~455 000 paiements et ~106 000 bénéficiaires chacun ; médiane 0,035 ETH | haute |
| `0x0e9e3919` | payeur ETH, 1re génération (probable) | 689 298 tx ; médiane ~0,03 ETH, ~780 destinataires distincts par tranche de 1 000 paiements ; 6 transferts **dans les deux sens** avec la trésorerie (30 et 11 ETH reçus ; 0,1, 15, 12 et 7 ETH rendus) ; mêmes financeurs (Coinbase Prime 1, Bitstamp 61, `0xa7ceed38`) ; actif dès le 21/05/2024, jour de la 1re transaction de la trésorerie | moyenne à haute |
| `0x7f227df2`, `0xabe7931e` | collecteurs de dépôts clients | 867/871 et 763/764 expéditeurs à usage unique ; dépôt médian 200 $ ; remontent vers la trésorerie | haute |
| `0xba8c2284` | rééquilibrage cross-chain de la famille | financé par la trésorerie et les collecteurs ; sorties vers Stargate (10,38 M$) et Synapse (4,74 M$) | moyenne |
| `0xf4c0cfbc` | rôle INCONNU | EIP-7702 ; 6,62 M$ vers la trésorerie depuis le 10/06/2026 ; alimenté par `0xa7af2a15` et `0x8d601ef8` | appartenance non démontrée |
| `0xa3222357` | contrat de retrait par lots, INFERÉ HitBTC | phase 3 (réapprovisionné par « HitBTC 6 ») | moyenne |
| `0x1bac0800` | n.exchange (collecteur) | étiquette ; balayage vers Binance Deposit | haute |
| `0xed9c6843` (dépôts partagés `0x4e4da0e8`, `0xf1497b68`) | service à dépôts partagés, identité nulle | phase 3 | haute (service) |
| `0xfb19ffd1` + adresses de dépôt `0x1e9a4552`, `0xc2b1669e`, `0xb16b7a61` | Aeroswap 2 et ses adresses de dépôt par ordre | étiquette ; chaque adresse de dépôt reçoit de `0x44b6f8de` puis balaie vers Aeroswap 2 en 2 min | haute |
| `0x1231deb6` | LI.FI Diamond | étiquette | haute |
| `TA4chMzt` | **SERVICE / HUB TRON NON IDENTIFIÉ** | phase 3, inchangé | inchangé |
| `TDqSquXB` | service TRON non identifié | phase 3, inchangé | inchangé |

---

## SECTION B : famille de wallets

```text
Coinbase Prime 1/2 · Kraken HW5 · Circle · OKX 7/20 · FalconX 1 · Bitstamp          dépôts clients (adresses à usage unique)
                     │                                                                          │
                     ▼                                                                          ▼
              0x3b6dcfde  TRÉSORERIE  ◄────────────────────────────── collecteurs 0x7f227df2 (G1) · 0xabe7931e (G2)
        ┌────────────┬──────────────┼───────────────┬─────────────────────────┐
        ▼            ▼              ▼               ▼                         ▼
 stablecoin G1   stablecoin G2    ETH G2        ETH G1 (probable)      comptes de dépôt : Coinbase Prime ×3, OKX ×2,
 b93e · 26c5     4a9a · b715     9744 · 9bdb    0x0e9e3919             FalconX, Bitstamp, MoonPay 7 ; rééquilibrage 0xba8c2284
 05/24 → 12/25   11/25 →         11/25 →        05/24 → 08/26
```

| Address | Funder | Role | Common Clients | Evidence |
|---|---|---|---|---|
| `0x3b6dcfde` | Coinbase Prime 1 et 2 (60,7 %), Kraken HW5 (21,3 %), Circle (6,3 %), collecteurs (6,1 %) | trésorerie | sans objet | §2 |
| `0x7f227df2` | adresses de dépôt clients | collecteur, 1re génération | sans objet | 5,00 M$ vers la trésorerie ; 99 % d'expéditeurs à usage unique |
| `0xabe7931e` | adresses de dépôt clients | collecteur, 2e génération | sans objet | 11,71 M$ et 11 453 ETH vers la trésorerie ; 6,6 M$ directement aux payeurs de 1re génération |
| `0xb93e3d70` | trésorerie (91,1 %), `0xabe7931e` | payeur stablecoin G1 | 13 037 avec 26c5 | 82 129 paiements, 32 011 bénéficiaires |
| `0x26c50e67` | trésorerie (90,6 %), `0xabe7931e` | payeur stablecoin G1 | 13 037 avec b93e | 81 892 paiements, 31 891 bénéficiaires |
| `0x4a9a1675` | trésorerie (100 %) | payeur stablecoin G2 | 16 642 avec b715 ; ~2 500 avec chaque payeur G1 | §3 |
| `0xb7152d59` | trésorerie (100 %) | payeur stablecoin G2 | 16 642 avec 4a9a | §3 |
| `0x974413b8` | trésorerie (100 %) | payeur ETH G2 | 40 042 avec 9bdb | 455 791 paiements, 106 200 bénéficiaires |
| `0x9bdbbd6f` | trésorerie (100 %) | payeur ETH G2 | 40 042 avec 9744 | 453 240 paiements, 105 518 bénéficiaires |
| `0x0e9e3919` | Coinbase Prime 1, Bitstamp 61, trésorerie | payeur ETH G1 (probable) | non mesuré | aller-retours avec la trésorerie |
| `0xba8c2284` | trésorerie, collecteurs | rééquilibrage | sans objet | Stargate, Synapse |

**Réseau et famille**
- Aucun bénéficiaire de la famille (261 508 adresses) n'appartient aux groupes externes du §13 (35 adresses testées).
- Ces groupes restent hors analyse.

---

## SECTION C : paiements au réseau (16)

| # | Date (UTC) | Service | Recipient | Amount | PM Account | Hash |
|--:|---|---|---|--:|---|---|
| 16 | 2025-07-09 06:04:35 | `0x0e9e3919` (payeur ETH) | `0x420d62bf` (relais de `0x44b6f8de`) | 0,01 ETH | aucun directement : premier gas de la branche EVM | `0x23d8c3c533029711723b1418f0184728905afaae0c5d2add1e4be108f4edbc20` |
| 1 | 2025-09-02 12:10:23 | `0xb93e3d70` | dépôt MEXC `0x2c547073` | 1 884,92 USDT | aucun (MEXC) | `0xdac0a7b408458b753a1fa8c36ab4bcb45a5346fe7e9e4c7644e630660f8726fc` |
| 2 | 2025-09-02 12:17:35 | `0xb93e3d70` | dépôt MEXC `0x2c547073` | 1 884,94 USDT | aucun (MEXC) | `0x494617bb7827898db7cab4b308279a10b3d08dbd166499dc14633315cf9533b7` |
| 3 | 2025-09-02 13:16:11 | `0xb93e3d70` | dépôt MEXC `0x2c547073` | 1 884,69 USDT | aucun (MEXC) | `0x5682cce3ae80eacbfe0183347ecf2c5bcdadd224bba60d75bd765d89e074a158` |
| 4 | 2025-09-02 15:01:35 | `0x26c50e67` | dépôt MEXC `0x2c547073` | 1 884,78 USDT | aucun (MEXC) | `0x3a944513fb86dbcdee697e3eaa2df4dcd0158b663678db940b39c49fe071d7d8` |
| 5 | 2025-12-23 01:59:59 | `0x4a9a1675` | dépôt PM `0x572441fa` | 1 011,42 USDC | Chiwawas | `0x373c882e98bf3598597defc5460c3bbfcc0da61dc58a3aa8e9cd3ea2d0c91c07` |
| 6 | 2025-12-23 02:22:35 | `0xb7152d59` | dépôt PM `0x572441fa` | 1 011,42 USDC | Chiwawas | `0xb9784ec42a06bcc28ecc823d2ce09bb56df9e963c25ce57072a923c0929c89c9` |
| 7 | 2025-12-24 19:48:47 | `0xb7152d59` | dépôt PM `0x572441fa` | 1 011,42 USDC | Chiwawas | `0x36cc6a3f3d7fe043dd4873957e39faf63590f470bc60613fa10ab61f3696f5a1` |
| 8 | 2025-12-30 03:36:35 | `0x4a9a1675` | dépôt PM `0xd4f7d8ac` | 2 822,87 USDC | 154x838hjd6 | `0xbfd99289a894b9845f477db04302aa243d92ef486c25b559ff56860ea4e3c753` |
| 9 | 2025-12-30 22:03:35 | `0xb7152d59` | dépôt PM `0xd4f7d8ac` | 1 411,04 USDC | 154x838hjd6 | `0x40e6a861b4f8335720dd45d92947d14f10429f029ca86a3284e3d4f5330ae338` |
| 10 | 2025-12-31 02:10:35 | `0xb7152d59` | dépôt PM `0x572441fa` | 2 163,97 USDC | Chiwawas | `0x07e29a4f8bc4b85a30272f2ef5ffa5e93625c79e97cb83ce092098954e412832` |
| 11 | 2025-12-31 03:40:59 | `0x4a9a1675` | dépôt PM `0x572441fa` | 4 706,52 USDC | Chiwawas | `0x96a27a51a85e41d178002edd9310426a154652907c680d121cc197865044f83c` |
| 12 | 2026-01-03 04:59:47 | `0xb7152d59` | dépôt PM `0x572441fa` | 3 769,36 USDC | Chiwawas | `0xfcc94f042e52ecc26a3cda21e366aea52fbe6b57e574781aa2e75e404987007d` |
| 13 | 2026-01-03 05:42:59 | `0xb7152d59` | dépôt PM `0x572441fa` | 4 712,17 USDC | Chiwawas | `0x23e92344f4eb8d763c1493e26f642fe0461636490870d62b84a9ee072b73bd24` |
| 14 | 2026-02-28 05:50:59 | `0x4a9a1675` | `0x44b6f8de` → dépôt PM `0xd4f7d8ac` (05:57:23) | 4 715,00 USDT | 154x838hjd6 | `0xd9841323e6dff6d9b7d3e4611ab1b6198f17feeb5260eb07b4b768d086342eed` |
| 15 | 2026-02-28 06:01:35 | `0x4a9a1675` | `0x44b6f8de` → dépôt PM `0xd4f7d8ac` (06:02:35) | 4 715,00 USDT | 154x838hjd6 | `0x1a3ed8d2d18af4602e95161cd3894c59cf6480e3da1130a3b8b8aa932d6e0beb` |

**Totaux** : 39 589,52 $ en stablecoins et 0,01 ETH.

| Destination | Nombre | Montant |
|---|--:|--:|
| Chiwawas | 7 | 18 386,28 |
| 154x838hjd6 (direct) | 2 | 4 233,91 |
| 154x838hjd6 (via `0x44b6f8de`) | 2 | 9 430,00 |
| dépôt MEXC | 4 | 7 539,33 |
| `0x420d62bf` | 1 | 0,01 ETH |

Les ordres Relay de chaque dépôt (hash d'entrée et de sortie, montant) sont dans `16_paiements_service.csv`.

**Précisions**
- Le n°15 est reversé à 4 715,004715, soit 4 715 plus 0,004715 de poussière d'empoisonnement reçue à 05:58. `0x44b6f8de` vide donc son solde entier.
- Aucun autre paiement, sur 3 chaînes, des 12 adresses de la famille vers les 103 adresses EVM du réseau contrôlées.

```text
service ─► #16 0,01 ETH ─► 0x420d62bf ─(vidé)─► 0x44b6f8de ─(nonce 0)─► … ─► dépôts PM Chiwawas, TacticalInsiderNews, 154x838hjd6
service ─► #1-4 ─► dépôt MEXC 0x2c547073 ◄─ aussi alimenté par 0x44b6f8de (5 000 ; 14 002,65)
service ─► #5-7, #10-13 ─► dépôt PM 0x572441fa ─► Chiwawas   (ce dépôt reçoit aussi 29 350,68 de 0x44b6f8de)
service ─► #8-9 ─► dépôt PM 0xd4f7d8ac ─► 154x838hjd6          (ce dépôt reçoit aussi #14-15 via 0x44b6f8de)
service ─► #14-15 ─► 0x44b6f8de ─► dépôt PM 0xd4f7d8ac ─► 154x838hjd6
```

**Lignée de gas (MESURÉ)**
1. `0x420d62bf` reçoit 3 088,36 USDC de Robinhood 3 le 07/07/2025, puis 2 037,61 USDT de MEXC 16 le 09/07 à 05:47.
2. Son **premier ETH** est le paiement n°16 du service, à 06:04:35.
3. 84 s plus tard (nonce 0), il envoie l'USDT à `0x44b6f8de`, puis l'USDC (nonce 1), puis son ETH restant (nonce 2, 0,00993 ETH, 06:24:11). Il n'est plus jamais utilisé.
4. Ces 0,00993 ETH sont le **premier ETH de `0x44b6f8de`**, qui fait sa première transaction (nonce 0) 72 s plus tard.
5. `0x44b6f8de` paie ensuite le gas de la première transaction de `0xe9a7230f` (phase 1).

---

## SECTION D : client unique ou clients multiples (sans score)

| Evidence | Supports same client | Supports separate clients |
|---|---|---|
| Les 5 adresses du réseau payées par le service ont toutes des transferts directs avec `0x44b6f8de` (dépôt MEXC, dépôt Chiwawas, dépôt 154x838hjd6, `0x44b6f8de`, `0x420d62bf`) | oui : chaque destination du service est aussi une destination ou une source de `0x44b6f8de` | une adresse de dépôt (PM ou MEXC) peut être alimentée par quiconque la connaît |
| Même adresse de dépôt réutilisée : dépôt Chiwawas 7 fois en 12 jours ; dépôt MEXC 4 fois en 5 h ; dépôt 154x838hjd6 2 fois en direct et 2 fois via `0x44b6f8de` | oui, par destination | chez ce service, 6 274 bénéficiaires reçoivent au moins 4 paiements sur plus de 3 mois : la répétition est banale |
| Le payeur alterne entre les jumeaux (4a9a et b715 pour le même dépôt, b93e et 26c5 pour MEXC) | neutre | neutre : le choix du payeur est une répartition de charge (§3), pas un indice de client |
| Montants : 1 884,9 ×4 ; 1 011,42 ×3 ; 4 715 ×2 | répétition à l'identique vers une même adresse | ce sont des montants courants du service : ~1 884,9 = 255 paiements vers 190 destinataires ; 4 715 = 17 vers 11 (10 hors réseau) ; 1 011,42 = 5 vers 3 ; 1 411,04, 3 769,36 et 4 712,17 existent aussi hors réseau |
| Timing : n°12 et 13 (03/01, 04:59 et 05:42) et n°14 et 15 (28/02, 05:50 et 06:01) tombent dans les fenêtres des événements Maduro et Iran | cohérence avec une même intention | le service paie en continu (~400 paiements stablecoin par jour et par payeur) ; un autre paiement de 4 715 part à 06:09 le 28/02 vers `0x24278dcc`, sans lien avec le réseau |
| Lignée de gas service → `0x420d62bf` → `0x44b6f8de` → `0xe9a7230f` | le gas arrive 17 min après les fonds MEXC sur `0x420d62bf`, et ces fonds partent vers `0x44b6f8de` 84 s après le gas | un retrait de 0,01 ETH peut être demandé par un tiers au profit d'une adresse fournie |
| Réutilisation du capital : les retraits Relay de Chiwawas et de 154x838hjd6 reviennent à `0x44b6f8de`, qui refinance des dépôts PM | oui : un même wallet recycle le capital de plusieurs comptes | un wallet commun peut servir plusieurs personnes (hypothèse d'un intermédiaire, sans preuve) |
| Sources secondaires : `0x44b6f8de` reçoit aussi de MEXC 16, Kraken 7, Robinhood 3 (via `0x420d62bf`) et `0xa3222357` (INFERÉ HitBTC) | le même wallet opérationnel concentre plusieurs comptes CEX | plusieurs comptes CEX peuvent appartenir à plusieurs personnes |
| Cash-out : Chiwawas → `0x44b6f8de` → n.exchange ; 154x838hjd6 → Bridgers → TRON (`TSahUmP5`, `TJs1u6k8`) et via `0x44b6f8de` → `0x2e473c0a` → Bridgers | les deux passent par `0x44b6f8de` à un moment | chemins de sortie différents (n.exchange contre TRON) |
| Périodes : 07/2025 (gas), 09/2025 (MEXC), 12/2025 à 01/2026 (Chiwawas, 154x838hjd6), 02/2026 (`0x44b6f8de`) | toutes comprises dans la vie de `0x44b6f8de` (09/07/2025 → 28/02/2026) ; le dernier paiement coïncide avec sa dernière activité | salves séparées, sans chevauchement |
| Identifiant client | aucun on-chain | aucun on-chain |
| Portée : 2 comptes sur 8 (Chiwawas, 154x838hjd6) reçoivent des fonds du service | sans objet | les 6 autres comptes n'en reçoivent pas ; les 4 comptes Iran de la racine TRON n'ont aucun lien avec le service |

**Ce que les données permettent d'écrire**
- Les 16 paiements aboutissent tous à des adresses qui échangent directement avec un seul wallet opérationnel, `0x44b6f8de`.
- Le service a aussi fourni le premier gas de la chaîne qui mène à ce wallet.
- **Les données établissent un lien financier via le même service, mais ne permettent pas d'établir que les bénéficiaires ont le même propriétaire, ni que les 16 retraits proviennent d'un même compte client du service.**

---

## SECTION E : `0x44b6f8de`

**Chronologie**
- 1er ETH le 09/07/2025 à 06:24:11 (de `0x420d62bf`) ; 1re transaction (nonce 0) à 06:25:23.
- Dernier flux réel le 28/02/2026 à 10:05 ; 21 transactions envoyées (nonces 0 à 20) en 8 mois.
- Aucun flux réel sur Polygon (100 % d'empoisonnement).

**Bilan** : entrées 201 207,61 $ = sorties 201 207,63 $ (hors ETH de gas). C'est du **transit pur** : le solde est vidé à chaque fois, y compris la poussière d'empoisonnement.

### Contreparties réelles (21, sosies exclus)

| Contrepartie | Classe | Sens | Tx | Montant ($) |
|---|---|---|--:|--:|
| Relay solver `0xf70da978` (retraits de Chiwawas, chileno777, TacticalInsiderNews, 154x838hjd6) | POLYMARKET | entrée | 4 | 129 295,03 |
| n.exchange `0x1bac0800` | SERVICE | sortie | 3 | 83 220,71 |
| `0x2e473c0a` (→ Bridgers → TRON) | UNKNOWN (wallet du réseau) | sortie | 2 | 38 696,45 |
| `0xa3222357` (INFERÉ HitBTC) | SERVICE | entrée | 3 | 38 326,69 |
| dépôt PM Chiwawas `0x572441fa` | POLYMARKET | sortie | 1 | 29 350,68 |
| dépôt MEXC `0x2c547073` | CEX | sortie | 2 | 19 002,65 |
| dépôt PM 154x838hjd6 `0xd4f7d8ac` | POLYMARKET | sortie | 2 | 9 430,00 |
| payeur du service `0x4a9a1675` | SERVICE | entrée | 2 | 9 430,00 |
| Kraken 7 | CEX | entrée | 2 | 8 915,00 |
| dépôt partagé `0xf1497b68` (service `0xed9c6843`) | SERVICE | sortie | 1 | 6 495,32 |
| MEXC 16 | CEX | entrée | 1 | 6 468,40 |
| LI.FI (swaps ETH→USDC, USDC→USDT) | SERVICE | les deux | 5 | 6 160,16 |
| dépôt Aeroswap `0xc2b1669e` | SERVICE | sortie | 1 | 5 937,68 |
| `0x420d62bf` (← Robinhood 3, MEXC 16) | UNKNOWN (wallet relais) | entrée | 3 | 5 125,97 |
| dépôt PM TacticalInsiderNews `0x5b85645c` | POLYMARKET | sortie | 2 | 3 440,36 |
| dépôt partagé `0x4e4da0e8` (service `0xed9c6843`) | SERVICE | sortie | 1 | 2 082,56 |
| Aeroswap 2 | SERVICE | entrée | 2 | 574,73 |
| dépôt Aeroswap `0xb16b7a61` | SERVICE | sortie | 1 | 462,86 |
| contrat de règlement Aeroswap `0x4ee879f3` ; dépôt Aeroswap `0x1e9a4552` | SERVICE | entrée ; sortie | 2 | 0,196 ETH aller-retour |
| `0xe9a7230f` | UNKNOWN (wallet du réseau) | sortie | 1 | 0,00593 ETH de gas |

**Décompte des contreparties**
- 21 au total : 3 CEX (MEXC 16, Kraken 7, dépôt MEXC), 11 éléments de service, 4 éléments Polymarket, 3 wallets UNKNOWN du réseau.
- **0 client tiers identifié.** Aucune contrepartie n'a pu être classée WALLET PERSONNEL avec une preuve.

**Proportions des entrées**
- Réseau (retraits Polymarket) : **64,3 %**.
- Services : 25,5 %, dont HitBTC (INFERÉ) 19,0 % et service `0x3b6dcfde` 4,7 %.
- CEX en direct : 7,6 %.
- `0x420d62bf` : 2,5 %, soit en réalité Robinhood 3 et MEXC 16.

**Proportions des sorties**
- Services hors réseau : **50,3 %**, dont n.exchange 41,4 %.
- Dépôts PM du réseau : 21,0 %.
- Wallet du réseau `0x2e473c0a` : 19,2 %.
- Dépôt MEXC : 9,4 %.
- Au total, **40,2 % vont au réseau** et 59,8 % en sortent, vers des services et un CEX.

**Autres faits**
- `0x44b6f8de` **ne dépose jamais** chez le service `0x3b6dcfde` : il n'a aucun flux vers les collecteurs.
- Il est la cible d'empoisonnements d'adresse :
  - sosies `0xd4f0…`, `0x2e47e2…`, `0x2c54…`, `0x2e4515…`, `0xb16bf6…`, `0xc2b1f9…` ;
  - faux USDT, faux USD Coin, jetons d'hameçonnage.
- Il n'est jamais tombé dans le piège : tous ses envois vont aux vraies adresses.

### Thèse « wallet personnel » : preuves pour et contre (sans trancher)

**Comportements incompatibles avec un wallet personnel, cherchés un par un**
- **Dizaines de bénéficiaires** : non. 13 destinations réelles, toutes des services, un CEX ou des adresses du réseau.
- **Fréquence élevée** : non. 21 transactions envoyées en 8 mois.
- **Paiements à des tiers** : aucun identifié.
- **Nombreux services** : oui. LI.FI, Aeroswap, n.exchange, `0xed9c6843`, contrat HitBTC (INFERÉ), service `0x3b6dcfde`, Relay, plus MEXC, Kraken et Robinhood (via `0x420d62bf`). C'est compatible avec un particulier actif comme avec un opérateur.
- **Sweeping et routage** : oui. Transit pur, relais médian de 6 min depuis décembre 2025, soldes vidés au centime près.

**Éléments pour « wallet contrôlé directement par l'opérateur du réseau »**
- Genèse du gas par `0x420d62bf`, qui s'est vidé entièrement dans `0x44b6f8de`, ETH restant compris, puis n'a plus servi.
- `0x44b6f8de` paie le gas de `0xe9a7230f`, le wallet du côté Iran.
- Il finance 3 comptes PM et reçoit les retraits de 4.
- Aucun client tiers.

**Éléments contre**
- `0x44b6f8de` ne détient jamais rien. Ce profil convient aussi à un intermédiaire qui ferait transiter des fonds pour plusieurs personnes : un desk, un ami, un apporteur.
- Rien on-chain ne distingue « un opérateur » d'« un intermédiaire servant plusieurs titulaires ».

---

## SECTION F : sources CEX

**CEX → service (trésorerie)**

| CEX | Recipient | Amount | What is proven | What is unknown |
|---|---|--:|---|---|
| Coinbase Prime 1 | `0x3b6dcfde` | 104 097 269,85 $ + 12 298,67 ETH | retraits d'un compte Coinbase Prime vers la trésorerie ; la trésorerie redépose chez Coinbase Prime (`0x51481afd`, `0xff3cf229`) | l'entreprise titulaire du compte (connue de Coinbase par KYB) |
| Coinbase Prime 2 | `0x3b6dcfde` | 63 426 500,00 $ + 11 168,68 ETH | idem (redépôt via `0x47ef369e`) | idem |
| Kraken HW5 | `0x3b6dcfde` | 58 899 934,24 $ | retraits Kraken vers la trésorerie depuis le 07/11/2025 | le titulaire |
| Circle | `0x3b6dcfde` | 17 440 038,37 $ | émissions ou rachats USDC vers la trésorerie ; Circle Mint est réservé aux entreprises (INFERÉ) | le titulaire |
| OKX 7, OKX 20 | `0x3b6dcfde` | 4 509 944,71 $ | retraits OKX ; la trésorerie redépose chez OKX (`0x2313c810`, `0x4ce15078` : 55,4 M$) | le titulaire |
| FalconX 1 | `0x3b6dcfde` | 38 314,68 ETH | retraits FalconX ; redépôt via `0xd2f3b47f` (3,07 M$) | le titulaire |
| Bitstamp (Wallet, 61) | `0x3b6dcfde` | 943 292 $ + 263 ETH | idem ; redépôt via `0xeb1d71ae` | le titulaire |

**CEX → client du réseau**

| CEX | Recipient | Amount | What is proven | What is unknown |
|---|---|--:|---|---|
| MEXC 16 | `0x420d62bf` ; `0x44b6f8de` | 2 037,61 ; 6 468,40 USDT | retraits MEXC vers deux wallets du réseau | le ou les titulaires MEXC |
| MEXC (dépôt `0x2c547073`) | MEXC 16 / MEXC 3 | 19 002,65 (de `0x44b6f8de`) + 7 539,33 (du service) | une même adresse de dépôt MEXC reçoit de `0x44b6f8de` et du service | le compte MEXC ; si l'adresse de dépôt n'appartient qu'à un seul compte (usage normal, non démontré) |
| Robinhood 3 | `0x420d62bf` | 3 088,36 USDC | retrait Robinhood | le titulaire |
| Kraken 7 | `0x44b6f8de` | 8 915,00 USDT | retraits Kraken (Kraken 7 est un hot wallet général ; il paie aussi la trésorerie une fois, 400 258,73 le 08/04/2025, sans que cela relie quoi que ce soit) | le titulaire |
| Coinbase 10 | dépôt PM chileno777 | 4 996,55 USDC | 5 retraits Coinbase | le titulaire |
| « HitBTC 6 » (INFERÉ) → `0xa3222357` | `0x44b6f8de` | 38 326,69 | retraits d'une plateforme multi-actifs | la plateforme exacte et le titulaire |

**Point clé** : que la trésorerie soit cliente de Coinbase Prime ne dit rien des comptes CEX des bénéficiaires. Aucune adresse de dépôt ne permet ici d'identifier un client CEX.

---

## SECTION G : attribution

### PROUVÉ ON-CHAIN

1. 16 paiements de la famille `0x3b6dcfde` vers 5 adresses du réseau, du 09/07/2025 au 28/02/2026 (39 589,52 $ + 0,01 ETH). Hashes en section C.
2. Les 5 adresses destinataires ont des transferts directs avec `0x44b6f8de`.
3. La lignée de gas service `0x0e9e3919` → `0x420d62bf` → `0x44b6f8de` → `0xe9a7230f` : premier ETH de chaque adresse, nonces 0.
4. La structure de la famille : 1 trésorerie, 2 collecteurs, 4 payeurs stablecoin et 2 payeurs ETH financés par la trésorerie, 1 wallet de rééquilibrage. Les chiffres sont en sections 2, 3 et B.
5. `0x44b6f8de` est en transit pur (201 207,61 $ entrés = sortis), avec 21 contreparties réelles et aucun client tiers identifié.
6. Les montants des paiements au réseau sont des montants récurrents du service.
7. Aucun bénéficiaire de la famille parmi les adresses des groupes externes.

### ATTRIBUTION EXTERNE (étiquettes Etherscan, non vérifiées on-chain)

- Coinbase Prime 1/2, Kraken HW5, Kraken 7, Circle, OKX 7/20, OKX Deposit `0x2313c810`, FalconX 1, Bitstamp Wallet/2/61, MoonPay 7.
- MEXC 16/3, Robinhood 3, Coinbase 10, Aeroswap 2, LI.FI, n.exchange, Relay Solver, Stargate, Synapse, « HitBTC 6 ».
- Pour les 12 adresses de la famille : **aucune étiquette, aucune mention web** (recherches sur les adresses exactes : seulement des pages d'explorateurs).

### INFERÉ

- `0x3b6dcfde` est la trésorerie d'une **entreprise** qui exploite une plateforme custodiale grand public. Raison : accès à Coinbase Prime et à Circle Mint, dépôts clients par adresses uniques, plus de 260 000 bénéficiaires.
- Rôle des adresses de dépôt, déduit des balayages :
  - `0x51481afd`, `0xff3cf229`, `0x47ef369e` : dépôts Coinbase Prime ;
  - `0x4ce15078` : dépôt OKX ;
  - `0xd2f3b47f` : dépôt FalconX ;
  - `0xeb1d71ae` : dépôt Bitstamp.
- `0x0e9e3919` est le payeur ETH de 1re génération de la même famille.
- Le paiement n°16 est un retrait demandé depuis un compte du service, par le contrôleur de `0x420d62bf` ou pour lui.
- `0x420d62bf` et `0x44b6f8de` sont sous le même contrôle (vidage total, ETH restant compris). Ce n'est pas prouvé.
- `0xa3222357` appartient à HitBTC.

### INCONNU

- L'identité du service et le type exact de plateforme.
- Le ou les comptes clients du service derrière les 16 retraits.
- Qui contrôle `0x44b6f8de`, `0x420d62bf`, `0xe9a7230f`, `TA4chMzt`.
- Le rôle de `0xf4c0cfbc`.
- L'intérieur de n.exchange (aucune reconstruction XMR tentée).
- Les financeurs BSC.

---

## Critère de fin (§19)

1. **`0x3b6dcfde`** : trésorerie centrale d'une plateforme custodiale grand public. Structure : confiance haute. Identité : INCONNUE.
2. **Rôle des payeurs** : hot wallets de retrait jumeaux, par actif (stablecoins d'un côté, ETH de l'autre) et par génération. Le choix du payeur relève de la répartition de charge et ne porte aucune information sur le client. Confiance haute.
3. **`0x44b6f8de`** : wallet opérationnel de transit du réseau EVM, bénéficiaire du service et non composant du service. Aucun client tiers. Personnel ou intermédiaire : non départageable.
4. **Les 16 paiements, un ou plusieurs clients** : non déterminable publiquement. Tous aboutissent à des adresses reliées directement à `0x44b6f8de` (fait mesuré). Le service ne marque aucun client on-chain.
5. **Branches qui convergent réellement** :
   - service → Chiwawas et 154x838hjd6, en direct et via `0x44b6f8de` ;
   - `0x44b6f8de` → Chiwawas, TacticalInsiderNews, 154x838hjd6, et retraits de 4 comptes ;
   - liaison avec la racine TRON par le gas `0x44b6f8de` → `0xe9a7230f` et par `0x2e473c0a` → Bridgers → `TJs1u6k8` ;
   - la racine TRON (`TA4chMzt`, `TK7tg1gJ`) n'a aucun lien avec le service.
6. **Où la traçabilité s'arrête** :
   - au registre interne du service `0x3b6dcfde` ;
   - aux comptes MEXC, Kraken, Robinhood, Coinbase et HitBTC (INFERÉ) ;
   - à n.exchange, `0xed9c6843`, `TA4chMzt`, `TDqSquXB` ;
   - au BSC.
7. **Pourquoi** :
   - un service custodial paie depuis un pool, sans identifiant client on-chain ;
   - les CEX ne publient pas leurs titulaires ;
   - aucune attribution publique n'existe pour la famille ;
   - les étiquettes TRON (Tronscan) et Arkham sont derrière une protection anti-bot, non contournée ;
   - les RPC BSC publics sont élagués.

---

## Réponses à la question fondamentale (§17)

**« Quelle est aujourd'hui la meilleure description factuelle de l'architecture financière qui a alimenté les 8 comptes ? »**

Deux racines de capital, reliées par des transferts directs, alimentent les 8 comptes.

**Racine EVM**
- Un wallet de transit, `0x44b6f8de`, sans client tiers, reçoit :
  - des retraits d'un service custodial non identifié (famille `0x3b6dcfde`, refinancée par Coinbase Prime, Kraken, Circle, OKX, FalconX) ;
  - des retraits de MEXC, Kraken et Robinhood ;
  - des retraits d'un contrat de paiement multi-actifs (INFERÉ HitBTC) ;
  - puis, de façon croissante, les retraits Polymarket du réseau lui-même.
- Le premier gas de ce wallet vient du même service, via `0x420d62bf` (09/07/2025).
- Cette racine finance Chiwawas, 154x838hjd6 et TacticalInsiderNews. Le service paie aussi directement les dépôts de Chiwawas et de 154x838hjd6.
- chileno777 est financé à part, par Coinbase 10.

**Racine TRON**
- Le hub non identifié `TA4chMzt`, plus `TK7tg1gJ`, finance X34, Planktonbets, Mrs.Joker et Neodbs via `TTt3h6D2`, `TJs1u6k8`, Bridgers et `0xe9a7230f`.

**Lien entre les deux racines**
- Le gas de `0x44b6f8de` vers `0xe9a7230f`.
- Le chemin `0x44b6f8de` → `0x2e473c0a` → Bridgers → `TJs1u6k8`.

Les données établissent un lien financier via le même service, mais ne permettent pas d'établir que les bénéficiaires ont le même propriétaire.

**« Quelle est la dernière frontière que les données publiques permettent actuellement de franchir ? »**
- Les données publiques franchissent la **sortie** du service : elles prouvent quel hot wallet a payé quelle adresse, quand, et avec quel hash, y compris le gas du 09/07/2025.
- Elles ne franchissent pas l'**entrée dans son registre**, c'est-à-dire quel compte client a demandé chaque retrait.
- La même frontière s'applique :
  - aux comptes MEXC, Kraken, Robinhood, Coinbase et HitBTC (INFERÉ) ;
  - à n.exchange ;
  - aux hubs TRON `TA4chMzt` et `TDqSquXB`.

**« Quelle donnée supplémentaire aurait la plus grande valeur pour franchir cette frontière ? »**
- **L'identité du service**, puis son **registre des retraits** pour les 16 hashes : quel compte client a demandé chacun.
- Le pivot le plus précieux est le retrait n°16 : 0,01 ETH, 09/07/2025 à 06:04:35, `0x23d8c3c5…`. C'est la genèse de toute la branche EVM. Le compte qui l'a demandé contrôle ou finance `0x420d62bf` au moment précis où les fonds Robinhood et MEXC passent vers `0x44b6f8de`.
- Viennent ensuite les n°14 et 15 (28/02, fenêtre Iran) et les n°12 et 13 (03/01, fenêtre Maduro).
- L'identité du service est connue de Coinbase Prime et de Circle, par le KYB du titulaire qui retire vers `0x3b6dcfde`, ou d'une base d'attribution commerciale (Arkham, Nansen, TRM).
- En complément, un seul relevé MEXC suffirait à tester « un compte ou plusieurs » : celui du titulaire de l'adresse de dépôt `0x2c547073`, alimentée à la fois par le service et par `0x44b6f8de`.
