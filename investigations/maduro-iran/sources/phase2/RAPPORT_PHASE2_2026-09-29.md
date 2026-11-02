# Phase 2 : expansion du réseau Maduro / Iran et dénominateur

29/09/2026. Heures en UTC (heure de bloc, sauf mention). Tables complètes en CSV dans ce dossier :
`TABLE1_graph.csv` (571 arêtes), `TABLE2_polymarket_accounts.csv`, `TABLE3_funding.csv`, `TABLE4_outflow.csv`,
`TABLE5_population_{maduro,iran,iranA}.csv`, `pnl_transactions.csv` (chaque BUY/SELL/REDEEM avec son hash), `stats_groups_*.json`.

## 0. Couverture réelle et corrections de méthode

| Élément | État |
|---|---|
| Balayage du graphe, plafond de 250 supprimé | 1 020 nœuds caractérisés, 89 072 arêtes. Profondeur 0 : 5/5. Profondeur 1 : 91/91. Profondeur 2 : 924/1 629 caractérisés (en cours, reprise automatique). |
| Nouvelles branches Polymarket, profondeur ≤ 2 | Ordres Relay de **1 709/1 709** nœuds (profondeurs 1 et 2) vérifiés. |
| Population Maduro, 05:00 → 06:12 | Complète : 136 495 événements `OrderFilled` scannés, **21** acheteurs YES. |
| Population Iran, 05:28 → 06:13 | Complète : 247 287 événements, **128** acheteurs YES. |
| Fenêtres de sensibilité | Iran 26/02 21:00 → 23:30 complète (114 acheteurs). Iran 27/02 14:30 → 17:45 et Maduro 02/01 16:00 → 03/01 05:00 en cours. |

Corrections faites en cours de route, qui changeaient les chiffres :
1. **TronGrid liste les `Approval` comme des transferts.** Démontré sur `TLREUZVR` : la tx `1e194527…` est un `approve` (sélecteur `095ea7b3`). Les sorties TRON de la phase 1 étaient gonflées ; elles sont refiltrées (`type == Transfer`) et désormais équilibrées (entrées = sorties).
2. **L'API Etherscan gratuite plafonne à 1 000 lignes par appel.** Les historiques complets sont repris par pagination sur les blocs.
3. **Le subgraph Goldsky est arrêté.** Les populations sont reconstruites depuis les logs `OrderFilled` du CTFExchange (`0x4bfb41d5`). Chaque ordre produit un événement vu depuis son propriétaire, ce qui a été validé sur l'achat de Chiwawas `0xac0eba63…`.
4. **Ordres maker ou taker.** 7 wallets remplis à la même seconde (05:46:37) au même prix sont des ordres limites passifs balayés par un même vendeur. Pour un maker, « l'heure d'entrée » n'est pas une décision ; le rôle est donc indiqué dans la table 5.
5. **TronGrid est limité à 1 requête/s sans clé.** C'est la seule cause de la profondeur 2 incomplète.

---

## TABLE 1 : GRAPH (extrait ; 571 arêtes dans `TABLE1_graph.csv`)

| Source | Destination | Chain | Asset | Amount | Timestamp | TX | Relation | Status |
|---|---|---|---|--:|---|---|---|---|
| Robinhood 3 `0x60812586` | `0x420d62bf` (relais, 4 tx) | ETH | USDC | 3 088,36 | 2025-07-07 13:43 | `0x79cd37a2…` | amont de 0x44b6f8de | PROVEN |
| MEXC 16 `0x9642b23e` | `0x420d62bf` | ETH | USDT | 2 037,61 | 2025-07-09 05:47 | `0x33983bff…` | amont | PROVEN |
| `0x420d62bf` | `0x44b6f8de` | ETH | USDT+USDC | 5 125,97 | 2025-07-09 06:05-06:17 | `0x50e76bd6…`, `0xcd8b51f8…` | 1er capital de 0x44b6f8de | PROVEN |
| MEXC 16 | `0x44b6f8de` | ETH | USDT | 6 468,40 | 2025-07-11 06:46 | `0x2c74dec7…` | retrait CEX | PROVEN |
| Kraken 7 `0x89e51fa8` | `0x44b6f8de` | ETH | USDT | 3 915 + 5 000 | 2025-07-29 / 08-05 | `0x0a64503a…`, `0x093c4685…` | retrait CEX | PROVEN |
| `0x44b6f8de` | `0x2c547073` → MEXC 16 | ETH | USDT | 5 000 + 14 002,65 | 2025-07-09 / 08-05 | `0x0ad5cf1e…`→`0x9efd19b5…` ; `0x4c79966a…`→`0x89cd6071…` | dépôt MEXC (balayé) | PROVEN |
| `0x44b6f8de` | `0xc2b1669e`, `0xb16b7a61` → Aeroswap 2 | ETH | USDT | 5 937,68 ; 462,86 | 2025-07-29 ; 10-16 | `0xaf1f0b3a…`→`0x575a47fa…` ; `0x54316173…`→`0xa8ceb961…` | swap Aeroswap (sortie INCONNUE) | PROVEN |
| batch `0xa3222357` (INFERÉ HitBTC) | `0x44b6f8de` | ETH | USDC | 29 350,68 | 2025-12-25 19:31 | `0x130acd8f…` | retrait plateforme | PROVEN |
| `0x44b6f8de` | `0x572441fa` (dépôt Chiwawas) → Relay → Chiwawas | ETH→Polygon | USDC | 29 350,68 | 2025-12-25 19:34 | `0xa539a68b…` / `0xa3cf6acd…` / `0xe6283e7a…` | financement | PROVEN |
| service `0xb7152d59` | `0x572441fa` → Chiwawas | ETH→Polygon | USDC | 3 769,36 ; 4 712,17 | 2026-01-03 04:59 ; 05:42 | `0xfcc94f04…`, `0x23e92344…` | financement le matin J | PROVEN |
| `0x44b6f8de` (swap LI.FI signé 05:16) | `0x5b85645c` → TacticalInsiderNews | ETH→Polygon | USDC | 14,85 | 2026-01-03 05:17 → 05:18 | `0xef193125…`, `0xf77c2856…` / `0x30cfdc25…` | financement | PROVEN |
| Chiwawas | `0x44b6f8de` | Polygon→ETH | USDC | 82 070,14 | 2026-01-03 16:49 | `0x9813a40e…` / `0xad8f683b…` | retrait | PROVEN |
| `0x44b6f8de` | n.exchange hot wallet | ETH | USDC | 82 020,71 | 2026-01-03 16:55 | `0x40cbbfa8…` | swap instantané | PROVEN |
| n.exchange hot wallet | « Binance Deposit » `0xd0e83490` | ETH | USDC | 91 045 (agrégé) | 2026-01-03 17:00 | `0x085487a6…` | balayage vers liquidité n.exchange | PROVEN |
| chileno777 | `0x44b6f8de` → `0x4e4da0e8` → `0xed9c6843` | Polygon→ETH | USDC | 2 082,56 | 2026-01-03 17:07 → 17:13 | `0x3cde2923…` / `0x90f2c3ea…` / `0x978d54af…` | retrait vers dépôt partagé d'un service | PROVEN |
| 154x838hjd6 | `0x2e473c0a` | Polygon→ETH | USDC | 34 138,99 | 2026-01-03 18:17 | `0xa817144b…` / `0x8b6a72f2…` | retrait | PROVEN |
| `0x44b6f8de` | `0x2e473c0a` | ETH | ETH | 0,0006 | 2026-01-03 18:26 | `0x36b9a311…` | gas | PROVEN |
| `0x2e473c0a` | Bridgers → TRON `TSahUmP5` | ETH→TRON | USDC→USDT | 34 118,22 → 33 840,607570 | 18:30 → 18:33 | `0xb6abc243…` / `8581f849…` | minReturn = reçu | PROVEN |
| `0x44b6f8de` | `0x5b85645c` → TacticalInsiderNews | ETH→Polygon | USDC | 3 425,51 | 2026-01-07 02:05 | `0xb6cef711…` / `0xb809d53e…` | financement | PROVEN |
| chileno777 | `0x5b85645c` (dépôt de TacticalInsiderNews) → TacticalInsiderNews | Polygon→ETH→Polygon | USDC | 2 077,54 | 2026-01-13 04:32-04:33 | `0x14289fbc…` / `0x3545c4cd…` / `0x908e648d…` | compte → compte | PROVEN |
| SBet365 | `0x8db6758f` (dépôt LINKCS) → LINKCS | Polygon | USDC | 25 100 | 2026-01-13 16:55-17:04 | `0x0368e7cb…` / `0xf295bd66…` | compte → compte | PROVEN |
| TacticalInsiderNews | `0x44b6f8de` → `0xf1497b68` → `0xed9c6843` | Polygon→ETH | USDC | 6 500 | 2026-01-14 20:18-20:22 | `0x2a1005f2…` / `0x5b2dc906…` / `0xa7ba24a3…` | retrait vers dépôt partagé | PROVEN |
| `0x44b6f8de` | `0xe9a7230f` | ETH | ETH | 0,0059 | 2026-01-14 20:50 | `0x80abce84…` | gas, **1re tx de 0xe9a7230f** | PROVEN |
| `TTt3h6D2` | Bridgers → `0xe9a7230f` | TRON→ETH | USDT | 39 899,20 → 39 619,803654 | 20:51:57 → 20:53 | `b7521eee…` / `0xbc2a2f52…` | calldata : destination 0xE9a7230f | PROVEN |
| `0xe9a7230f` | `0xefaa882c` → X34 | ETH→Polygon | USDT | 39 619,80 | 20:57 → 20:58 | `0x49028f2c…` / `0x591af2b2…` | financement | PROVEN |
| X34 | `0xe9a7230f` → `0xa460a588` → Mrs.Joker | Polygon→ETH→Polygon | USDT | 29 452,73 → 29 400 | 2026-01-15 → 01-20 | `0xd39eda38…` / `0xe51f99fc…`, `0xc8ba152c…` / `0x068ea83a…` | gains de X34 → Mrs.Joker (solde à source unique) | PROVEN |
| X34 | `0xe9a7230f` → Bridgers → `TTt3h6D2` | Polygon→ETH→TRON | USDC | 40 461,73 → 40 172,894745 | 2026-01-23 → 01-29 23:55 | `0x301936cd…` / `0xd7bcb53e…` / `e2474f1f…` | minReturn = reçu | PROVEN |
| `TTt3h6D2` | `TEfE77Wk` → Relay → Planktonbets | TRON→Polygon | USDT | 2 637,69 ; 15 000 | 02-18 04:41 ; 02-28 01:26 | `f2191321…`/`fbae1fba…` ; `478ee195…`/`735efa77…` | financement | PROVEN |
| `TTt3h6D2` | `TFMhN2un` → Relay → Mrs.Joker | TRON→Polygon | USDT | 9 310 ; 5 000 | 02-18 15:52 ; 02-26 18:00 | `ad53b9d1…`/`aa4a4d19…` ; `0a7931da…`/`ae322b15…` | financement | PROVEN |
| Mrs.Joker | `0x75db067e` → Planktonbets | Polygon→ETH→Polygon | USDC | 9 278 | 2026-02-18 15:59 → 16:00 | `0x93880459…` / `0x3697da74…` / `0x1f89497e…` | compte → compte | PROVEN |
| `TA4chMzt` | `TJs1u6k8` → `TLREUZVR` → Relay → Neodbs | TRON→Polygon | USDT | 10 000 | 2026-02-26 22:50 → 22:52:30 | `d46dbecb…` / `5ab36ea4…` / `c1bec320…` / `0xaf44ea53…` | financement | PROVEN |
| service `0x4a9a1675` | `0x44b6f8de` → `0xd4f7d8ac` → 154x838hjd6 | ETH→Polygon | USDT | 4 715 ×2 | 2026-02-28 05:50→05:57:53 ; 06:01→06:03:05 | `0xd9841323…`/`0x8a8ae334…`/`0x17039631…` ; `0x1a3ed8d2…`/`0x2ea12eba…`/`0x68e4863d…` | financement pendant la fenêtre | PROVEN |
| Planktonbets | `0xe9a7230f` | Polygon→ETH | USDT | 200 747,08 | 2026-02-28 09:43 | `0x96774c8c…` / `0x2865d714…` | retrait | PROVEN |
| Mrs.Joker | `0x2225a4fd` → `0xe9a7230f` | Polygon→ETH | USDT | 157 086,31 | 09:53 → 10:07 | `0x4a60fcc6…` / `0x935106d9…` / `0x12e4eb2d…` | retrait ; gas `0x89eceb11…` | PROVEN |
| `0xe9a7230f` | Bridgers → `TTt3h6D2` | ETH→TRON | USDT | 38 696,45 ; 159 373,47 ×2 | 10:00 ; 10:13 ; 10:21 | `0x2ba1113c…`, `0x28dbb955…`, `0xac894e83…` | minReturn = reçu | PROVEN |
| 154x838hjd6 | `0x44b6f8de` → `0x2e473c0a` → Bridgers → `TSahUmP5` | Polygon→ETH→TRON | USDT | 38 758,52 → 38 424,075149 | 09:36 → 10:28 | `0x6a3f37ed…` / `0x42419cdb…` / `0xe1c4e2b0…` / `4d9673c6…` | minReturn = reçu | PROVEN |
| Neodbs | `0x4e062726` → Bridgers → `TJs1u6k8` | Polygon→ETH→TRON | USDT | 98 837,50 → 97 987,080535 | 10:18 → 10:24 | `0x6182e185…` / `0xf6f4ae98…` / `b1c3b474…` | boucle fermée sur TJs1u6k8 | PROVEN |
| `TTt3h6D2` | `TA4chMzt` | TRON | USDT | 121 494,19 + 210 000 | 2026-02-28 16:13 ; 19:03 | `33888daf…`, `0c279760…` | vers hub TRON | PROVEN |
| `TJs1u6k8` | `TChkscPd95` → `TDqSquXB` | TRON | USDT | 93 603,60 | 2026-03-01 20:36 | `98673b93…` | dépôt de service (balayé 20/20 vers TDqSquXB) | PROVEN (flux) / INCONNU (entité) |

## TABLE 2 : POLYMARKET ACCOUNTS (marchés ≥ 500 $ ; 39 lignes dans le CSV)

| Account | Market | First Buy | Entry Price | Capital | Result | PnL | Network Link |
|---|---|---|--:|--:|---|--:|---|
| Chiwawas `0x168b100d` | Maduro out in 2025 (YES) | 2025-12-23 02:01 | 0,0521 | 39 241,66 | perdu | −37 821,28 | retrait → 0x44b6f8de ; dépôt financé par 0x44b6f8de |
| Chiwawas | Maduro out by Jan 31 (YES) | 2026-01-03 05:35:41 | 0,1206 | 9 897,67 | gagné | +72 172,47 | idem |
| chileno777 `0x834079f6` | Maduro out in 2025 (YES) | 2025-12-23 00:13 | 0,0357 | 3 840,01 | perdu | −3 624,79 | retrait → 0x44b6f8de ; paie le dépôt de TacticalInsiderNews |
| TacticalInsiderNews `0x5621116` | U.S. forces seize another Venezuela oil ship (YES) | 2026-01-07 01:58 | 0,526 | 1 469,78 | gagné | +1 226,45 | dépôt financé par 0x44b6f8de ; retrait → 0x44b6f8de |
| 154x838hjd6 `0xbf32f7a7` | Maduro out by Jan 31 (YES) | 2025-12-30 14:52 | 0,0817 | 2 776,95 | gagné | +31 216,17 | dépôt financé par 0x44b6f8de ; retraits → 0x44b6f8de et 0x2e473c0a |
| 154x838hjd6 | US strikes Iran by Feb 28 (YES) | 2026-02-28 05:59:05 | 0,2428 | 9 411,13 | gagné | +29 347,38 | idem |
| Neodbs `0x56efadc9` | US strikes Iran by Feb 28 (YES), seul trade | 2026-02-26 22:53:50 | 0,10 | 9 883,75 | gagné | +88 953,75 | financé depuis TJs1u6k8 ; retour sur TJs1u6k8 |
| Planktonbets `0x38745db2` | US strikes Iran by Feb 28 (YES) | 2026-02-26 21:44:48 | 0,1321 | 26 513,89 | gagné | +174 233,18 | financé par TTt3h6D2 et par Mrs.Joker ; retrait → 0xe9a7230f |
| Mrs.Joker `0xe9b80c38` | US strikes Iran by Feb 28 (YES) | 2026-02-06 18:11:09 | 0,172 | 27 008,93 | gagné | +130 046,12 | financé par 0xe9a7230f (gains de X34) et TTt3h6D2 ; retrait → 0xe9a7230f |
| Mrs.Joker | US strikes Iran by Feb 20 (YES) | 2026-02-06 18:10:35 | 0,1116 | 10 000 | perdu | −5 826,22 | idem |
| X34 `0x60280bef` | US strikes Iran by Jan 14 (YES) | 2026-01-14 20:59:34 | 0,196 | 10 770 | perdu (revendu) | +8 573,17 | financé par 0xe9a7230f (fonds TTt3h6D2) ; retraits → 0xe9a7230f |
| X34 | US strikes Iran by Jan 14 (NO) | 2026-01-14 22:44:10 | 0,5747 | 30 000 | gagné | +22 202,20 | idem |
| SBet365 `0x6baf05d1` | Maduro Jan 31 + Feb 28 (YES) | 2026-01-03 03:42:01 | 0,113 / 0,183 | 25 089,94 | gagné | +145 619,85 | hors réseau ; finance LINKCS |
| LINKCS `0x0e9310b9` | US strikes Iran by Feb 28 (**NO**) | 2026-02-27 17:21:21 | 0,82 | 20 080,87 | perdu | −20 080,87 | lié à SBet365 (dépôt direct + 2 adresses de dépôt Kraken communes) ; côté opposé au réseau |
| 0x31a56e9e | Maduro out by Jan 31 (YES) | 2025-12-31 00:20 | 0,0745 | 32 538,34 | gagné | +404 221,27 | hors réseau (Coinbase) |
| 0xa72db1749e | Maduro out by Jan 31 (YES) | 2026-01-02 21:44:21 | 0,0716 | 5 782,66 | gagné | +74 982,28 | hors réseau (Coinbase) |

PnL total par compte (formule SELL + REDEEM + MERGE + valeur − BUY − SPLIT ; composantes dans `pnl_summary.csv`, transactions dans `pnl_transactions.csv`) : Chiwawas +34 351,19 ; chileno777 −832,20 ; TacticalInsiderNews +1 035,08 ; 154x838hjd6 +59 254,58 ; Neodbs +88 953,75 ; Planktonbets +173 906,24 ; Mrs.Joker +122 910,74 ; X34 +30 413,87. **Réseau : +509 993,25 $.** Aucun SPLIT ni MERGE dans ces comptes.

## TABLE 3 : FUNDING (extrait ; 40 lignes dans le CSV)

| Account | Immediate Funder | Upstream Funder | Service | Evidence | Status |
|---|---|---|---|---|---|
| Chiwawas | `0x572441fa` (dépôt PM) | `0x4a9a1675` ×2, `0xb7152d59` ×4, `0x44b6f8de` ×1 | service de paiement non identifié (réapprovisionné par `0x3b6dcfde` ← Coinbase Prime 2, Circle, OKX 7) | `0x373c882e…`, `0x96a27a51…`, `0xfcc94f04…`, `0x23e92344…`, `0xa539a68b…` | PROVEN |
| chileno777 | `0xc2be6a8c` (dépôt PM) | Coinbase 10 ×5 | Coinbase | `0x22b42b0b…`, `0x93348ffd…` | PROVEN |
| TacticalInsiderNews | `0x5b85645c` (dépôt PM) | `0x44b6f8de` ×2, chileno777 ×1 | aucun | `0xf77c2856…`, `0xb6cef711…`, `0x3545c4cd…` | PROVEN |
| 154x838hjd6 | `0xd4f7d8ac` (dépôt PM) | `0x4a9a1675`, `0xb7152d59`, `0x44b6f8de` ×2 | service non identifié (même réapprovisionneur) | `0xbfd99289…`, `0x40e6a861…`, `0x8a8ae334…`, `0x2ea12eba…` | PROVEN |
| Neodbs | `TLREUZVR` (TRON, créée à la seconde) | `TJs1u6k8` ← `TA4chMzt` | Relay TRON ; TRX de frais par `TTdigaHy` (service, 418 destinataires en 14 j) | `5ab36ea4…`, `c1bec320…` | PROVEN |
| Planktonbets | `TEfE77Wk` ; `0x75db067e` | `TTt3h6D2` ; Mrs.Joker | Relay | `f2191321…`, `478ee195…`, `0x93880459…` | PROVEN |
| Mrs.Joker | `0xa460a588` ; `TFMhN2un` | `0xe9a7230f` (gains X34) ; `TTt3h6D2` | Relay | `0xe51f99fc…`, `0xc8ba152c…`, `ad53b9d1…` | PROVEN |
| X34 | `0xefaa882c` | `0xe9a7230f` ← Bridgers ← `TTt3h6D2` | Bridgers, Relay | `b7521eee…`, `0x49028f2c…` | PROVEN |
| `0x44b6f8de` (trésorerie) | ― | Robinhood 3 (via `0x420d62bf`), MEXC 16, Kraken 7, Aeroswap 2, `0xa3222357` ×3, `0x4a9a1675` ×2 | CEX + services | voir Table 1 | PROVEN (flux) ; entités = étiquettes publiques Etherscan |
| SBet365 | `0x72bf0886` (dépôt PM) | Coinbase 10 | Coinbase | `0x6988d26b…`, `0x91bbd397…` | PROVEN |
| 0x31a56e9e | `2i7HJJTs` (Solana, 10 sig.) | Coinbase Hot Wallet 5g7yN, Coinbase 1, Paxos Hot Wallet | Coinbase, Paxos | sig `5QFPj4bW…` | PROVEN |
| 0xa72db1749e | `0x1a714134` | Coinbase 10, Coinbase 14 (Base), Coinbase 6 | Coinbase | `0x50856280…`, `0x0018f6af…` | PROVEN |

## TABLE 4 : OUTFLOW (extrait ; 56 lignes dans le CSV)

| Account | Destination | Amount | Chain | Service | Evidence | Status |
|---|---|--:|---|---|---|---|
| Chiwawas | `0x44b6f8de` → n.exchange → Binance Deposit | 82 020,71 | Polygon→ETH | n.exchange | `0x40cbbfa8…`, `0x085487a6…` | PROVEN jusqu'à n.exchange ; sortie INCONNUE |
| chileno777 | `0x44b6f8de` → `0x4e4da0e8` → `0xed9c6843` | 2 082,56 | Polygon→ETH | service non identifié (71 666 tx) | `0x90f2c3ea…`, `0x978d54af…` | PROVEN / entité INCONNUE |
| TacticalInsiderNews | `0x44b6f8de` → `0xf1497b68` → `0xed9c6843` | 6 495,32 | Polygon→ETH | idem | `0x5b2dc906…`, `0xa7ba24a3…` | PROVEN / entité INCONNUE |
| 154x838hjd6 | `0x2e473c0a` et `0x44b6f8de` → Bridgers → `TSahUmP5` → `TJs1u6k8` / `TChkscPd95` → `TDqSquXB` | 34 138,99 + 38 758,52 | Polygon→ETH→TRON | Bridgers ; TRON service non identifié | Table 1 | PROVEN / entité INCONNUE |
| Neodbs | `0x4e062726` → Bridgers → `TJs1u6k8` | 98 837,50 | Polygon→ETH→TRON | Bridgers | `0xf6f4ae98…` | PROVEN |
| Planktonbets, Mrs.Joker | `0xe9a7230f` (+`0x2225a4fd`) → Bridgers → `TTt3h6D2` → `TA4chMzt` | 200 747,08 + 157 086,31 | Polygon→ETH→TRON | Bridgers ; hub TRON | Table 1 | PROVEN ; nature de TA4chMzt INCONNUE |
| X34 | `0xe9a7230f` → dépôt de Mrs.Joker ; → Bridgers → `TTt3h6D2` | 29 452,73 ; 40 461,73 | Polygon→ETH(→TRON) | Relay, Bridgers | Table 1 | PROVEN |
| SBet365 | Coinbase 10 (via `0x86b9bac9`) ; Kraken (ETH `0x13aad194`, Solana `EkDy99Z6`) ; LINKCS | 125 100 ; 100 + 16 409,80 ; 25 100 | Polygon→ETH/Solana | Coinbase, Kraken | `0x204eeba9…`, `0x7ab83b67…` | PROVEN |
| LINKCS | les **mêmes** adresses Kraken `0x13aad194` et `EkDy99Z6` | 429,44 en 24 retraits (4,31 à 169,98) | Polygon→ETH/Solana | Kraken | Table 4 CSV | PROVEN |
| 0x31a56e9e | `ERKEtTT` → Coinbase 4 | 437 639,43 | Polygon→Solana | Coinbase | sig `kxpeQ2r2…` | PROVEN |
| 0xa72db1749e | `0x9e53d1f6` → Coinbase 30 | 80 728,01 | Polygon | Coinbase | `0x787a001c…`, `0xea1beca0…` | PROVEN |

## TABLE 5 : EVENT POPULATION

### Maduro, 03/01 05:00 → 06:12 (repricing 06:16) : 21 acheteurs YES, population entière

| Wallet | Entry Time | Entry Price | Capital | Network? | Outcome (PnL marché) |
|---|---|--:|--:|---|--:|
| flipfloppity `0x858d551d` | 05:00:49 | 0,121 | 6 366,25 | non | +169 287 |
| diadjaid `0x784feec3` | 05:03:33 | 0,117 | 6 191,33 | non | +26 847 |
| simplystupid188 `0x682c9261` | 05:06:53 | 0,105 | 43,95 | non | +425 |
| thepolwinner `0x3078db4a` | 05:07:15 | 0,100 | 28,42 | non | +89 |
| spicyFrog `0xb2dc4eea` | 05:07:27 | 0,107 | 64,00 | non | −4 |
| Bska36 `0x9dc2e5f6` | 05:11:47 | 0,100 | 10,00 | non | +2 |
| lighterconfirm `0x0feffea2` | 05:13:19 | 0,115 | 4,60 | non | −21 |
| `0xf70ff98d` | 05:19:49 | 0,108 | 181,16 | non | +10 866 |
| **chileno777** | **05:35:27** | 0,103 | 215,23 | **oui** | +1 869 |
| Green55 `0xc854ac92` | 05:35:39 | 0,110 | 50,72 | non | +410 |
| **Chiwawas** | **05:35:41** | 0,121 | 9 897,67 | **oui** | +72 172 |
| Edje25 `0x6268011c` | 06:00:15 | 0,120 | 120,00 | non | +675 |
| Skepticc `0x573442a3` | 06:00:41 | 0,120 | 328,91 | non | +4 221 |
| A110 `0x77b0b896` | 06:02:41 | 0,120 | 200,00 | non | +1 211 |
| aurelius `0x3d94555a` | 06:03:33 | 0,120 | 250,00 | non | +4 945 |
| PressC `0x908dbf08` | 06:04:55 | 0,110 | 5,50 | non | +1 627 |
| gojomojo `0x6fe8867f` | 06:06:33 | 0,120 | 120,00 | non | +320 |
| HornyBibi `0x708dba57` | 06:07:01 | 0,120 | 450,00 | non | +1 035 |
| Faquarl `0x4ea67bdd` | 06:07:29 | 0,130 | 85,00 | non | +1 836 |
| balastair `0xe3295575` | 06:10:37 | 0,120 | 14,09 | non | +82 |
| slight- `0x090a0d3f` | 06:11:07 | 0,123 | 7 393,78 | non | +60 310 |

### Iran, 28/02 05:28 → 06:13 (repricing 06:13) : 128 acheteurs YES (liste entière dans le CSV), 10 plus gros

| Wallet | Entry Time | Entry Price | Capital | Network? | Outcome (PnL marché) |
|---|---|--:|--:|---|--:|
| Magamyman `0x4dfd481c` | 05:33:47 | 0,223 | 29 502,77 | non | +232 776 |
| luckyAugust1975 `0x0e00ce71` | 05:29:29 | 0,215 | 19 971,79 | non | +75 670 |
| rrrrgggbbbclat `0xe756468f` | 05:33:35 | 0,200 | 9 995,99 | non | +39 984 |
| **154x838hjd6** | **05:59:05** | 0,243 | 9 411,13 | **oui** | +29 347 |
| jamesjohnson176 `0x9c6bd2c9` | 05:29:31 | 0,225 | 8 500,00 | non | +29 337 |
| yellowtop1 `0x3e44cfbf` | 05:57:07 | 0,241 | 7 570,48 | non | +23 852 |
| Domariocarios `0x72630d49` | 05:38:27 | 0,209 | 7 219,32 | non | +27 377 |
| marketboy `0x128744a3` | 06:00:47 | 0,237 | 6 977,33 | non | +22 110 |
| `0xf5477b7f` | 05:55:31 | 0,241 | 6 000,00 | non | +18 894 |
| Levc505 `0x9e7d792c` | 05:48:55 | 0,225 | 5 707,65 | non | +19 645 |

### Comparaison réseau / population (métriques brutes)

| Fenêtre | Groupe | n | Capital (somme) | Médiane | Prix médian (IQR) | Délai achat → repricing, médiane (IQR) | Latence financement → achat, médiane | Part financée < 1 h |
|---|---|--:|--:|--:|---|---|--:|--:|
| Maduro | tous | 21 | 32 020,59 | 120,00 | 0,120 (0,108-0,120) | 40,5 min (11,3-64,4) | 5,09 h | 19 % |
| Maduro | réseau | 2 | 10 112,90 (31,6 %) | 5 056,45 | 0,112 | 40,6 min | 0,59 h (1 obs.) | 1/2 |
| Maduro | indépendants | 19 | 21 907,69 | 120,00 | 0,120 | 15,9 min (10,4-66,6) | 17,07 h | 16 % |
| Iran | tous | 128 | 187 401,00 | 167,50 | 0,220 (0,210-0,240) | 21,7 min (11,5-35,4) | 5,86 h | 20 % |
| Iran | réseau | 1 | 9 411,13 (5,0 %) | ― | 0,243 | 14,3 min | 0,02 h | 1/1 |
| Iran 26/02 21:00-23:30 | tous | 114 | 49 798,09 | 20,00 | 0,090 (0,080-0,100) | ~32 h | 16,9 h | 24 % |
| Iran 26/02 21:00-23:30 | réseau | 3 | 21 883,75 (43,9 %) | 6 000 | 0,100 | ~32 h | 1,86 h | 1/3 |

Rang des comptes du réseau dans leur fenêtre (part de la population, strictement) : Chiwawas : seuls 14 % des acheteurs ont payé plus cher que lui, et 48 % ont acheté après lui ; chileno777 : 86 % ont payé plus cher ; 154x838hjd6 : seuls 20 % ont payé plus cher, et **66 % des acheteurs Iran ont acheté avant lui ou en même temps** ; Neodbs, Mrs.Joker et Planktonbets sont les **3 plus gros acheteurs** de la fenêtre du 26/02, au prix médian.

Taux de gain : dans ces fenêtres, tout acheteur YES qui a conservé ses parts a gagné (les deux marchés ont résolu YES). Le taux de gain de la fenêtre (Maduro 90,5 %, Iran 89,8 %) ne mesure donc rien sur l'information des acheteurs.

---

## MESURÉ

1. **N = 8 comptes** dans le réseau, confirmés après expansion. Les ordres Relay des 1 709 nœuds de profondeur 1 et 2 ne font apparaître **aucun autre compte Polymarket**, hormis Dhaman (`0x7e9beb7d`, paris sportifs, −8 555,74 $), relié seulement par `TJD71gJZ`, adresse de dépôt d'un service (64 expéditeurs, 1 destinataire).
2. **Liens compte → compte directs** (fonds prouvés) : chileno777 → TacticalInsiderNews ; Mrs.Joker → Planktonbets ; X34 → Mrs.Joker (via `0xe9a7230f`, solde à source unique entre le 15/01 et le 20/01). Et, hors réseau, SBet365 → LINKCS.
3. **Trésoreries communes** : `0x44b6f8de` (4 comptes en retrait, 3 en financement), `0xe9a7230f` (3 comptes en retrait, 2 en financement), `TTt3h6D2` et `TJs1u6k8` sur TRON.
4. **Gas payé entre wallets du réseau** : `0x44b6f8de` → `0xe9a7230f` (sa première transaction) et → `0x2e473c0a` ; `0xe9a7230f` → `0x2225a4fd` ; `TTt3h6D2` → `TJs1u6k8` (244 TRX).
5. **Montant identique** : `0xe9a7230f` swappe **38 696,45** USDT vers TRON à 10:00:35 le 28/02, et `0x2e473c0a` swappe **38 696,4503** à 10:23:23. Ce sont deux sources différentes, le second montant étant le retrait de 154x838hjd6.
6. **Activité du contrôleur de `0x44b6f8de` pendant les fenêtres** : il signe un swap LI.FI à **05:16** et un transfert à 05:17 le 03/01 (repricing à 06:16), puis des transferts à **05:57 et 06:02** le 28/02 (repricing à 06:13).
7. **Capital amont de `0x44b6f8de`** : Robinhood 3, MEXC 16, Kraken 7 (retraits de CEX), Aeroswap 2 (swap), le contrat de retrait `0xa3222357`, et le service `0x4a9a1675`.
8. **`0x4a9a1675` / `0xb7152d59`** forment un même service de paiement (même réapprovisionneur `0x3b6dcfde`, lui-même alimenté par Coinbase Prime 2 : 22,5 M$, Circle : 8,8 M$, OKX 7 : 2,4 M$).
   - Actif depuis le 11/11/2025 : 132 997 paiements pour 43,96 M$, à 41 253 destinataires (67 % payés une seule fois).
   - Sur 80 bénéficiaires tirés au hasard, 1 seul envoie vers Relay : ce n'est pas une infrastructure Polymarket.
   - Il a payé **10 fois** dans le réseau : 6 fois dans le dépôt de Chiwawas, 2 fois dans celui de 154x838hjd6 et 2 fois dans `0x44b6f8de`.
9. **`0xa3222357`** est un contrat de retrait par lots :
   - 141 808 appels, dont 99,9 % par un seul opérateur `0x963737c5`, fonction `0x0007e964` (tableaux token / destinataire / montant, lots de 11 en médiane, jusqu'à 100) ;
   - 454 tokens distincts, plus de 143 000 destinataires ;
   - réapprovisionné notamment par « HitBTC 6 » (686 transferts).
10. **n.exchange** : la transaction `0x40cbbfa8…` prouve le dépôt de 82 020,71 USDC, balayé à 17:00 vers « Binance Deposit » `0xd0e83490`. Le hot wallet n'a fait **aucun** paiement sortant vers un client dans les 3 h.
11. **SBet365 et LINKCS** partagent deux adresses de dépôt Kraken (`0x13aad194` sur ETH, `EkDy99Z6` sur Solana). LINKCS a parié NO sur l'Iran, à l'opposé du réseau ; sa contrepartie (`0x52b74441`) est hors réseau.
12. **Dénominateur** : voir les tables de comparaison. Dans les deux fenêtres imposées, le réseau ne se distingue ni par le prix ni par le moment d'achat ; il se distingue par la taille.
13. **Autres grappes dans la population Iran** : SemiconductorIT, yellowtop1 et BlueElephant666 partagent des destinations de retrait (`0x519fa16e`, `4dLZQynk`) ; carltiosway et Momentumgod aussi (`0xa6c22144`) ; 0x0BB95597 et Pulser aussi (`0x6d77731e`). Dans la population Maduro, la seule adresse personnelle partagée est `0x44b6f8de`.

## INFERÉ

- **Contrôle commun des wallets du réseau** (`0x44b6f8de`, `0xe9a7230f`, `0x2e473c0a`, `0x2225a4fd`, `0x4e062726`, `TTt3h6D2`, `TJs1u6k8`). Cela repose sur plusieurs éléments indépendants : transferts directs, gas pour une première transaction, montant identique retapé, boucles fermées.
- **Les 8 comptes sont pilotés par une personne ou un petit groupe qui partage ses clés.** L'on-chain ne départage pas ces deux cas.
- **`0xa3222357` appartient à HitBTC** (ou à son groupe), ce qui repose sur ses réapprovisionnements. Non démontré.
- **`TA4chMzt`** appartient à un écosystème USDT de gré à gré ou P2P sur TRON : 35 expéditeurs, 36 destinataires, 1,17 M$ transités, montants ronds, contreparties elles-mêmes très connectées.
- **`0xed9c6843`** est un service (CEX ou processeur) dont `0xf1497b68` et `0x4e4da0e8` sont des adresses de dépôt partagées avec des dizaines d'autres payeurs.

## INCONNU

- **Qui contrôle les wallets.** Aucune donnée publique ne nomme une personne.
- **Ce qui est sorti de n.exchange** (actif, chaîne, destinataire) : INCONNU, frontière n.exchange. XMR-COMPATIBLE, pas XMR-SPECIFIC.
- **L'identité des services** `0x4a9a1675` / `0x3b6dcfde`, `0xed9c6843`, `TDqSquXB`, `TA4chMzt`.
- **Le premier signal public à la minute** sur les deux événements. Les heures d'annonce (Caracas ~05:50-06:00, CENTCOM ~06:35) viennent de la chronologie de juillet, non revérifiée à la minute.
- **La profondeur 2 hors Relay** : 705 nœuds n'ont pas encore leurs flux caractérisés.

## HYPOTHÈSES ALTERNATIVES

| Lien central | A. même opérateur | B. collecteur / service | C. dépôt partagé | D. infrastructure | E. autre | Ce que disent les données |
|---|---|---|---|---|---|---|
| `0x44b6f8de` ↔ 4 comptes | compatible | contredit : 26 tx, aucun payeur extérieur au groupe, il signe ses propres swaps | contredit : il initie des transferts et détient des soldes | contredit | petit groupe partageant la clé : compatible | A ou E, indiscernables |
| `0xe9a7230f` ↔ 3 comptes | compatible | contredit (21 tx) | contredit | contredit | groupe : compatible | A ou E ; sa 1re tx est du gas envoyé par `0x44b6f8de` |
| `TA4chMzt` ↔ TRON du réseau | possible | **compatible** (profil OTC/P2P) | possible | non | trésorerie propre : possible | indéterminé, donc non compté comme preuve |
| Ordres jumeaux Planktonbets / Mrs.Joker | compatible | ― | ― | ― | copie de signaux (même source d'information) : compatible | corroborant seulement, mais Mrs.Joker a aussi financé Planktonbets |
| « Le réseau savait » | ― | ― | ― | ― | trader OSINT rapide multi-comptes : compatible | prix et timing dans la moyenne de la population ; des paris perdants existent (Maduro 2025 : −37,8 k$ ; Iran Feb 20 : −5,8 k$) |

## TRACE STOPS

| Branche | Stop | Raison précise |
|---|---|---|
| Amont de `0x44b6f8de` | Robinhood, MEXC, Kraken | CEX : données client non publiques |
| Amont de Chiwawas / 154x838hjd6 | service `0x4a9a1675`/`0xb7152d59` | service de paiement institutionnel non étiqueté, 41 253 bénéficiaires |
| Amont de `0x44b6f8de` (déc.-janv.) | `0xa3222357` | contrat de retrait par lots (INFERÉ HitBTC) |
| Sortie de Chiwawas | n.exchange → Binance Deposit | échange instantané : pas d'association publique entrée → sortie |
| Sorties de chileno777 / TacticalInsiderNews | `0xed9c6843` | dépôts partagés d'un service non identifié |
| Sorties Iran (Planktonbets, Mrs.Joker, X34, Neodbs, 154x838hjd6) | `TA4chMzt`, `TDqSquXB` | hub OTC/P2P et service TRON non identifiés ; Tronscan et Arkham derrière anti-bot (non contournés) |
| SBet365, LINKCS, 0x31a56e9e, 0xa72db1749e | Coinbase, Kraken | CEX |

## PROCHAINE ÉTAPE

1. Laisser finir le graphe (705 nœuds, reprise automatique), puis rejouer la passe de recherche de comptes Polymarket.
2. Terminer les fenêtres de sensibilité (Iran 27/02 et Maduro 02/01 16:00 → 03/01 05:00, en cours) : elles placeront SBet365, 0x31a56e9e et 0xa72db1749e dans leur population.
3. Identifier `0x3b6dcfde` / `0x4a9a1675`. Un même client de ce service a demandé des retraits vers les dépôts de deux comptes différents et vers `0x44b6f8de` : c'est le point KYC le plus fort de l'affaire.
4. Obtenir une clé TronGrid (gratuite) : elle ferait passer TRON de 1 à ~15 requêtes/s.
5. Reconstruire la chronologie publique à la minute (flux horodatés) pour 05:16-06:16 le 03/01 et 05:28-06:13 le 28/02.
6. Recevoir la liste des ~80 wallets de la mission initiale (toujours absente).
