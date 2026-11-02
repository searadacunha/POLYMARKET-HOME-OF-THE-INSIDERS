# Phase 3 : attribution financière du réseau Polymarket (8 comptes)

29/09/2026, heures UTC. Annexes : `paths_8_accounts.csv` (chemin de chaque compte avec hashes), `service_family_to_network.csv` (15 paiements du service vers le réseau), `ext_relay.json` (groupes externes), `an_3b6d.json` (flux de 0x3b6dcfde), `d3_pm.json`.

**Couverture** : graphe de profondeur 2 terminé (1 725 nœuds, 123 466 arêtes, 1 629/1 629 nœuds de profondeur 2 caractérisés). 244 adresses EVM de profondeur 3 testées. Aucune clé TronGrid n'existe dans l'environnement : les limites publiques ont été respectées.

**Correction de la phase 2** : le service a effectué **15 paiements** vers des adresses du réseau, pas 10 (7 vers le dépôt de Chiwawas, 2 vers celui de 154x838hjd6, 2 vers `0x44b6f8de`, 4 vers l'adresse de dépôt MEXC de `0x44b6f8de`).

---

## 1. GRAPHE FINANCIER

```text
RACINE EVM
Coinbase Prime 1/2 · Kraken HW5 · Circle · OKX 7 (+ 3 sources non étiquetées)
      ↓  (276,1 M$ poolés, 446 expéditeurs)
0x3b6dcfde  trésorerie d'un service non identifié
      ↓  (réapprovisionnements poolés, 1 200+ chacun)
0x4a9a1675 · 0xb7152d59 · 0xb93e3d70 · 0x26c50e67   (hot wallets payeurs jumeaux)
      ↓  15 paiements, 39 589,52 $, du 02/09/2025 au 28/02/2026
      ├──► dépôt MEXC 0x2c547073 (4 ×)            ← aussi alimenté par 0x44b6f8de
      ├──► dépôt PM Chiwawas 0x572441fa (7 ×)
      ├──► dépôt PM 154x838hjd6 0xd4f7d8ac (2 ×)
      └──► 0x44b6f8de (2 ×, 28/02 05:50 et 06:01) ──► dépôt PM 154x838hjd6

« HitBTC 6 » (INFERÉ) ──► 0xa3222357 (contrat de retrait par lots) ──► 0x44b6f8de (3 ×)
                                                           ──► dépôts PM Chiwawas, TacticalInsiderNews
MEXC 16 · Kraken 7 · Robinhood 3 (via 0x420d62bf) · Aeroswap 2 ──► 0x44b6f8de (2025)
Coinbase 10 ──► dépôt PM chileno777 (5 ×)

RACINE TRON
TCMLVCN1 · TCLo4KAu · TLMdMgMg … (35 expéditeurs, 1,17 M$)          TNXoiAJ3 (hot wallet CEX) → TK7tg1gJ
      ↓                                                                    ↓
TA4chMzt  hub TRON non identifié ──► TTt3h6D2 ──► X34 (via Bridgers → 0xe9a7230f), Planktonbets, Mrs.Joker
                                 └─► TJs1u6k8 ──► Neodbs

POLYMARKET (8 comptes) ── dépôts 191 791,16 $ (dont 151 084,40 $ de capital externe) ── PnL +509 993,25 $

CASH-OUT (retraits externes : 660 708,94 $)
Chiwawas            → 0x44b6f8de → n.exchange (82 020,71) → Binance Deposit (liquidité n.exchange)   [STOP]
chileno777, Tactical→ 0x44b6f8de → dépôts partagés de 0xed9c6843 (8 577,88)                          [STOP]
154x838hjd6, Neodbs → Bridgers → TRON TSahUmP5 / TJs1u6k8 → TChkscPd95 → TDqSquXB (127 424,60)          [STOP]
Planktonbets, Mrs.Joker, X34 → 0xe9a7230f → Bridgers → TTt3h6D2 ┐
154x838hjd6, Neodbs → TJs1u6k8 ─────────────────────────────────┴→ TA4chMzt (434 560,22)                 [STOP]
Liens entre racines : gas 0x44b6f8de → 0xe9a7230f (1re tx) ; 0x44b6f8de → 0x2e473c0a → Bridgers → TSah → TJs1u6k8.
```

## 2. TABLE DES 8 COMPTES

| Account | Funding (reçu sur Polymarket) | Funder (immédiat) | Source (dernière observable) | Outflow | Destination |
|---|--:|---|---|--:|---|
| Chiwawas | 47 718,95 | dépôt `0x572441fa` ← `0xb7152d59` ×5, `0x4a9a1675` ×2, `0x44b6f8de` ×1 | trésorerie `0x3b6dcfde` (pool) ; `0xa3222357` (INFERÉ HitBTC) | 82 070,14 | n.exchange → Binance Deposit |
| chileno777 | 4 994,04 | dépôt `0xc2be6a8c` ← Coinbase 10 ×5 | Coinbase | 4 161,83 | `0xed9c6843` (2 082,56) ; TacticalInsiderNews (2 077,54) |
| TacticalInsiderNews | 5 513,39 | dépôt `0x5b85645c` ← `0x44b6f8de` ×2, chileno777 ×1 | `0xa3222357` ; swap LI.FI signé par `0x44b6f8de` | 6 500,00 | `0xed9c6843` |
| 154x838hjd6 | 13 642,92 | dépôt `0xd4f7d8ac` ← `0x4a9a1675`, `0xb7152d59`, `0x44b6f8de` ×2 | 100 % trésorerie `0x3b6dcfde` (en direct ou via `0x44b6f8de`) | 72 897,51 | TRON : TDqSquXB, TA4chMzt |
| Neodbs | 9 883,75 | `TLREUZVR` ← `TJs1u6k8` | `TA4chMzt` | 98 837,50 | TRON : TJs1u6k8 → TDqSquXB / TA4chMzt |
| Planktonbets | 26 840,84 | `TEfE77Wk` ← `TTt3h6D2` ; `0x75db067e` ← Mrs.Joker | `TA4chMzt` ; bridge BSC (INFERÉ) | 200 747,08 | `0xe9a7230f` → Bridgers → `TTt3h6D2` → `TA4chMzt` |
| Mrs.Joker | 43 625,03 | `0xa460a588` ← `0xe9a7230f` ; `TFMhN2un` ← `TTt3h6D2` | gains de X34 ; `TA4chMzt` | 166 364,31 | Planktonbets (9 278) ; `0x2225a4fd` → `0xe9a7230f` → TRON |
| X34 | 39 572,24 | `0xefaa882c` ← `0xe9a7230f` ← Bridgers ← `TTt3h6D2` | `TA4chMzt` (23 750) + `TK7tg1gJ` (16 352,01) | 69 986,11 | Mrs.Joker (29 500) ; TRON (40 486,11) |

## 3. CONVERGENCES

| Node | Number of Accounts | Total Capital | Evidence |
|---|--:|--:|---|
| `0x44b6f8de` (financement) | 3 : Chiwawas, TacticalInsiderNews, 154x838hjd6 | 42 221,04 | `0xa539a68b…`, `0xf77c2856…`, `0xb6cef711…`, `0x8a8ae334…`, `0x2ea12eba…` |
| `0x44b6f8de` (retraits) | 4 : Chiwawas, chileno777, TacticalInsiderNews, 154x838hjd6 | 129 412,95 | ordres Relay (Table 1 de la phase 2) |
| Service `0x3b6dcfde` (hot wallets payeurs) | 2 comptes : Chiwawas, 154x838hjd6 ; + `0x44b6f8de` et son dépôt MEXC | 39 589,52 (15 paiements) | `service_family_to_network.csv` ; première convergence le **02/09/2025** |
| `0xa3222357` (via `0x44b6f8de`) | 2 : Chiwawas, TacticalInsiderNews | 32 776,19 | `0x130acd8f…` → `0xa539a68b…` ; `0xa39320fb…` → `0xb6cef711…` |
| `TA4chMzt` (hub TRON) | 4 : X34, Planktonbets, Mrs.Joker, Neodbs | 63 750 vers le réseau | `2a46b7ca…`, `21c60416…`, `218ca639…`, `d46dbecb…` |
| `TTt3h6D2` | 3 : X34, Planktonbets, Mrs.Joker (financement) ; 3 en retrait | 71 846,89 envoyés (39 899,20 + 17 637,69 + 14 310) | Table 1 de la phase 2 |
| `0xe9a7230f` | financement de 2 (X34, Mrs.Joker) ; retraits de 3 (X34, Planktonbets, Mrs.Joker) | 69 019,80 envoyés ; 427 318,28 reçus des 3 comptes | idem |
| Coinbase 10 | 1 (chileno777) | 4 996,55 | 5 hashes |

**Chemins indépendants vers une même source** : aucun nœud ne finance les 8 comptes. En financement, le maximum est de 4 comptes sur un même nœud non-infrastructure (`TA4chMzt`, qui est lui-même un hub dont 95 % des sorties vont hors réseau). En retrait, le maximum est de 4 comptes sur `0x44b6f8de`. Le réseau a **deux racines de capital** (EVM : `0x44b6f8de` et ses sources ; TRON : `TA4chMzt` et `TK7tg1gJ`), reliées par des transferts et du gas.

## 4. SERVICES

| Address | Classification | Evidence | Confidence |
|---|---|---|---|
| `0x3b6dcfde` | Trésorerie de service de paiement ou de retrait (entreprise), identité INCONNUE | 21/05/2024 → aujourd'hui ; 276,1 M$ reçus de 446 expéditeurs (Coinbase Prime 1 : 104,1 M$ ; Coinbase Prime 2 : 63,4 M$ ; Kraken HW5 : 58,9 M$ ; Circle : 17,4 M$ ; OKX 7 : 4,4 M$) ; 275,8 M$ vers 156 destinataires seulement (médiane 25 000 $) ; 4 hot wallets payeurs ≈ 155 M$ ; 32,5 M$ vers une adresse de dépôt OKX ; aussi actif sur Polygon (19,8 M$) et Arbitrum | structure : haute ; identité : nulle |
| `0x4a9a1675`, `0xb7152d59` | Hot wallets payeurs **jumeaux** du même service | même date de début (11/11/2025), même réapprovisionneur, ~128 000 paiements chacun, ~38 600 destinataires, médiane ~118 $, 43 % de bénéficiaires communs, même profil horaire | haute |
| `0xb93e3d70`, `0x26c50e67` | Autres hot wallets payeurs du même service | réapprovisionnés par `0x3b6dcfde` (34,0 M$ et 33,0 M$), ~93 000 tx chacun | haute |
| `0xa3222357` | Contrat de retrait par lots d'une plateforme multi-actifs, INFERÉ HitBTC | 141 808 appels, opérateur unique `0x963737c5`, fonction `0x0007e964`, 454 tokens, réapprovisionné par « HitBTC 6 » (686 fois) | moyenne |
| `0x1bac0800` n.exchange | Collecteur d'un service d'échange instantané | étiquette Etherscan ; balayage vers « Binance Deposit » `0xd0e83490` ; aucun paiement sortant vers un client | haute |
| `0xed9c6843` (→ `0xba4e328c`) | Service à adresses de dépôt partagées | `0xf1497b68` et `0x4e4da0e8` reçoivent de dizaines de payeurs et balaient en quelques secondes ; 71 666 tx ; 4 autres comptes Polymarket passent par là (profondeur 3) | haute (service) ; identité nulle |
| Bridgers `0xb685760e` / `TPwezUW` | Bridge de swap cross-chain | étiquette ; minReturn du calldata = montant reçu | haute |
| Relay (solver, router, depository ; TRON `TXtEs6t2`, `TYVWGh8X`) | Bridge | enregistrements Relay | haute |
| fun.xyz (referrer `funxyz\|su4gnoxz14` ; sponsors de gas `0x3f77a673`, `0xefce5b1c` ; TRX `TTdigaHy`) | Intégration de dépôt Polymarket | **identique pour tous les comptes, réseau ou non** | haute |
| Across SpokePool `0x5c7bcd6e` ; opérateur `0x3a54f61c` | Bridge ; opérateur de bridge (fonctions admin refund / withdrawFundsToSourceChain) | calldata du fill : origine BSC, dépôt 516709 | haute |
| `TA4chMzt` | **SERVICE / HUB TRON NON IDENTIFIÉ** | 05/12/2025 → 03/06/2026 ; 112 transferts ; 35 expéditeurs et 36 destinataires, dont 4 seulement dans les deux sens ; 1,17 M$ ; 30-40 % de montants ronds ; détention médiane ≈ 25 h ; le réseau pèse ~37 % de ses entrées et ~5 % de ses sorties | moyenne (hub) ; « OTC » non justifié |
| `TDqSquXB` | Service TRON non identifié | 733 expéditeurs en 6 h ; `TChkscPd95` lui balaie 20 transferts sur 20 | haute (service) |
| `TNXoiAJ3` | Hot wallet CEX TRON non étiqueté | 200 transferts vers 194 destinataires en 3 h | haute (service) |

## 5. CEX BOUNDARIES

| Address | CEX | Evidence | What remains unknown |
|---|---|---|---|
| `0xa9d1e08c` | Coinbase 10 | étiquette Etherscan ; 5 retraits vers le dépôt de chileno777 | le client Coinbase |
| `0x9642b23e`, `0x3cc936b7` ; dépôt `0x2c547073` | MEXC 16, MEXC 3 | retraits vers `0x44b6f8de` et `0x420d62bf` (2025) ; dépôts de `0x44b6f8de` balayés vers MEXC | le client MEXC ; si le dépôt `0x2c547073` n'appartient qu'à un compte (usage normal, non démontré ici) |
| `0x89e51fa8` | Kraken 7 | 3 915 et 5 000 USDT vers `0x44b6f8de` (2025) | le client Kraken |
| `0x60812586` | Robinhood 3 | 3 088,36 USDC vers `0x420d62bf` → `0x44b6f8de` | le client Robinhood |
| `0xceb69f63`, `0xcd531ae9`, `0xaa8ba7d4`, `0x55fe002a`, `0x5041ed75` | Coinbase Prime 2 et 1, Kraken HW5, Circle, OKX 7 | sources de la **trésorerie du service** `0x3b6dcfde`, pas du réseau | frontière réelle = le service lui-même (qui est client de ces plateformes) |
| `0xd0e83490` | Binance (dépôt de n.exchange) | balayage `0x085487a6…` | l'actif rendu par n.exchange |
| `0xa3222357` | HitBTC (INFERÉ) | réapprovisionnements par « HitBTC 6 » | l'identité exacte de la plateforme et du client |
| `TDqSquXB`, `TNXoiAJ3` | service ou CEX TRON non étiquetés | volume | tout (Tronscan est derrière anti-bot) |

## 6. MESURÉ

1. **N = 8, confirmé.** Profondeur 2 complète : 0 nouveau compte. En profondeur 3, 4 comptes Polymarket apparaissent, mais uniquement via les dépôts **partagés** de `0xed9c6843` (autres clients de ce service) ; Dhaman via un dépôt de service TRON.
2. **Un même service payeur (famille `0x3b6dcfde`) a versé 15 fois vers 4 adresses du réseau entre le 02/09/2025 et le 28/02/2026** (39 589,52 $), dont 2 comptes Polymarket, `0x44b6f8de` et l'adresse de dépôt MEXC de `0x44b6f8de`. Certains versements tombent dans les fenêtres des événements (03/01 04:59 et 05:42 ; 28/02 05:50 et 06:01).
3. **Les montants de ces paiements ne sont pas une signature.** 4 715,00 USDT est un montant récurrent du service (9 destinataires différents de décembre à septembre, dont `0x24278dcc` le 28/02 à 06:09, sans aucun lien avec le réseau) ; 1 011,42 revient aussi pour un autre client.
4. **Le `referrer` Relay `funxyz|su4gnoxz14` est identique pour tous les comptes**, réseau ou non : c'est l'intégration fun.xyz de Polymarket, pas un identifiant d'opérateur. La piste de juillet est **contredite**.
5. **`0x44b6f8de`** : 17 entrées (8 sources) et 16 sorties (11 destinations). En 2025, il agrège ; depuis décembre 2025, c'est un relais pur (délai médian 6 min). Toutes ses contreparties sont des CEX, des services, les 8 comptes ou `0xe9a7230f`/`0x2e473c0a`.
6. **Bilan économique** : capital externe 151 084,40 $, sorties externes 660 708,94 $, solde net 509 624,54 $ (PnL 509 993,25 $ ; écart 0,07 %).
7. **Groupes externes** : ils forment 2 grappes et non 3.
   - Grappe E (SemiconductorIT, yellowtop1, BlueElephant666, carltiosway, Momentumgod) : 5 comptes financés entre 05:27 et 06:06 le 28/02 ; sources Binance 2, KuCoin Hot Wallet, Kraken Hot Wallet, BSC (non traçable), service Arbitrum `0x03e6fa59` ; sorties vers un wallet Solana qui envoie ensuite à **« Privacy Cash Pool »**.
   - Grappe F (Pulser → dépôt de 0x0BB95597, lien direct) : source partagée avec E, `0x03e6fa59`, qui est un service (902 511 tx).
   - **Aucune convergence amont avec le réseau.**

## 7. INFERÉ

- `0x3b6dcfde` est la trésorerie d'une entreprise régulée ou institutionnelle : Coinbase Prime et Circle Mint sont réservés aux entreprises.
- Les 15 paiements du service vers 4 adresses du réseau sont compatibles avec **un seul compte client** qui retire vers ses propres adresses sur 6 mois. Ils sont aussi compatibles avec plusieurs clients d'un service qui paie ~40 000 bénéficiaires par wallet. Non départageable on-chain.
- `0x44b6f8de` est un **wallet opérationnel** du groupe : personnel ou partagé, pas un service ouvert au public, puisqu'il n'a aucun client tiers.
- Les 2 596,82 USDT reçus par `TTt3h6D2` le 18/02 viennent probablement du swap ETH de `0xe9a7230f` via Bridgers (3 min d'écart, valeur compatible). Non prouvé : ce swap natif n'émet pas l'événement décodé.

## 8. INCONNU

- **L'identité du service `0x3b6dcfde`**, et donc qui est son client.
- Qui contrôle `0x44b6f8de`, `0xe9a7230f` et `TA4chMzt`.
- La nature de `TA4chMzt` : trésorerie propre, contrepartie P2P ou OTC, ou service.
- La sortie de n.exchange ; les financeurs BSC (grappe E, et l'origine Across de `0xe9a7230f`).
- **Il n'existe pas de chemin unique** qui relierait les 8 comptes à une même source de capital : ce n'est pas observé.

## 9. ALTERNATIVES

| Lien | Hypothèses compatibles | Ce qui départagerait |
|---|---|---|
| Service `0x3b6dcfde` → 4 adresses du réseau | (a) un client du service ; (b) plusieurs clients liés entre eux ; (c) plusieurs clients sans lien, simple produit populaire | registres clients du service ; le seul indice on-chain, la répartition sur 4 adresses du même groupe pendant 6 mois, favorise (a) ou (b) sans exclure (c) |
| `0x44b6f8de` | wallet personnel ; wallet d'un desk dédié à ce groupe ; wallet partagé par un petit groupe | aucun client tiers observé, ce qui contredit « desk ouvert » ; les autres options restent indiscernables |
| `TA4chMzt` → 4 comptes Iran | trésorerie du groupe ; contrepartie P2P ou OTC utilisée dans les deux sens ; service | identifier ses 35 expéditeurs et 36 destinataires (étiquettes TRON inaccessibles ici) |
| `0xa3222357` → 2 comptes | un client de la plateforme (HitBTC INFERÉ) | registres de la plateforme |

## 10. TRACE STOPS

| Branche | Stop | Raison |
|---|---|---|
| Financement Chiwawas / 154x838hjd6 / `0x44b6f8de` | service `0x3b6dcfde` | service non identifié ; ses propres sources (Coinbase Prime, Kraken, Circle, OKX) financent son pool, pas un client identifiable |
| Financement `0x44b6f8de` (2025) | MEXC, Kraken, Robinhood, Aeroswap | CEX ou service |
| Financement Chiwawas / TacticalInsiderNews via `0xa3222357` | plateforme multi-actifs (INFERÉ HitBTC) | CEX |
| chileno777 | Coinbase 10 | CEX |
| Financement Iran (X34, Planktonbets, Mrs.Joker, Neodbs) | `TA4chMzt`, `TNXoiAJ3`, bridge BSC | hub ou service TRON non identifié ; CEX non étiqueté ; BSC inaccessible gratuitement (RPC élagués, BscScan derrière anti-bot) |
| Cash-out Chiwawas | n.exchange → Binance | échange instantané |
| Cash-out chileno777 / TacticalInsiderNews | `0xed9c6843` | service à dépôts partagés |
| Cash-out TRON | `TDqSquXB`, `TA4chMzt` | service ou hub non identifié |

---

## Réponses aux critères

**A. Chemin complet de chaque compte** : section 2 et `paths_8_accounts.csv`. Tous les chemins s'arrêtent à un CEX, à un service ou au hub `TA4chMzt`.

**B. Combien convergent vers une même source ?** Aucune source unique pour les 8.
- En financement : 4 sur `TA4chMzt` (hub ambigu) ; 3 sur `0x44b6f8de` ; 2 sur le service `0x3b6dcfde` ; 2 sur `0xa3222357`.
- En retrait : 4 sur `0x44b6f8de` ; les 8 aboutissent à 4 frontières (n.exchange, `0xed9c6843`, `TDqSquXB`, `TA4chMzt`).
- Le réseau a deux racines de capital, reliées par des transferts directs.

**C. Nature de `0x3b6dcfde`** : trésorerie d'un service de paiement ou de retrait financé par des canaux institutionnels, qui redistribue à au moins 4 hot wallets payeurs. Ce n'est ni un wallet personnel, ni un exchange qui paie directement ses clients. Identité INCONNUE.

**D. Relation entre `0x4a9a1675`, `0xb7152d59` et `0x44b6f8de`** : les deux premiers sont des hot wallets payeurs jumeaux du même service (même réapprovisionneur, même structure). `0x44b6f8de` est un **bénéficiaire** de ce service, pas un de ses éléments. Ce n'est pas un même flux économique au sens « même argent » : le service paie depuis un pool.

**E. Les groupes externes convergent-ils en amont ?** Non avec le réseau. Les grappes E et F partagent entre elles un nœud (`0x03e6fa59`), qui est une infrastructure (902 511 tx).

**F. Frontière exacte** : section 5 et section 10.

**G. Preuve publique au-delà ?** Non, avec les sources accessibles. Il faudrait :
- une base d'attribution commerciale (Arkham, Nansen, TRM) pour identifier le service `0x3b6dcfde` et les hubs TRON ;
- des réquisitions légales auprès du service `0x3b6dcfde`, de MEXC, Kraken, Robinhood, n.exchange et Coinbase.

Les points d'entrée les plus précis pour ces demandes sont :
- les **15 hashes** du service ;
- le dépôt MEXC `0x2c547073` ;
- l'ordre n.exchange du 03/01 à 16:55 (82 020,71 USDC, `0x40cbbfa8…`).
