# Sorties des 11 comptes

Lu le 2 novembre 2026. Le burn de pUSD n'est pas une destination : l'adresse zéro n'apparaît comme cible d'aucun retrait. La destination est technique : elle ne dit rien du bénéficiaire économique.

## 1. Réponse

**Sur 493 094,76 $ retirés, environ 74 % n'avaient pas bougé ou étaient revenus sur leur adresse le 2 novembre.** Sept comptes gardent 299 565,17 $ en stablecoins et 26,97 ETH. Trois comptes ont déposé chez des services non identifiés, soit 118 371,00 $, et Zoomman17 a envoyé 6 893,00 USDC vers une adresse de dépôt balayée par Revolut 5. **Aucune destination finale commune.** Le service `GxjcMTWW…nvBW` reçoit deux comptes : il est mutualisé.

## 2. Par compte

| Compte | Retraits $ | Destination technique | Suite vérifiable | Encore sur la première adresse le 2 nov. | Dernier point public |
|---|---|---|---|---|---|
| Thin-Disclaimer-Life | 80 037,93 | `CXVYMP5q…GrfJ`, `EnHRjTP4…PZ8B` (Solana) | Aucune | 79 537,63 USDC, 4,93 SOL | Ces deux adresses |
| VidenteRibeira | 51 509,88 | `DMmDPF9s…1wt5T` (Solana) | 51 489,00 USDT balayés vers `GxjcMTWW…nvBW`, cosigné | 0,09 USDT | `GxjcMTWW…nvBW` |
| cookedrice | 39 158,78 | `F7ew8r8X…Nh5Eh` (Solana) | 39 158,00 USDC balayés vers `GxjcMTWW…nvBW`, cosigné | 0,63 USDC | `GxjcMTWW…nvBW` |
| WenZhuanBuPei | 27 724,79 | `0xe820ecb3…87cd` (Arbitrum) | 27 724,00 USDC vers `0x3ab2206b…7d50`, 1 % de côté, 3 morceaux regroupés par `0x51cf2d9f…4999` | 0,79 USDC | `0x51cf2d9f…4999` |
| 0x86544e4dfde | 74 198,32 | Clé `0x69837228…0ded` (Ethereum) | Aucune | 74 198,32 USDC | La clé |
| brace227 | 22 036,76 | Clé `0xc852b093…af26` (Ethereum) | Petits échanges de gaz | 22 024,57 USDC | La clé |
| walletwallet8424 | 35 546,89 | Clé `0x82775eb8…a3a1` (Ethereum) | Aucune | 35 546,89 USDC | La clé |
| Zoomman17 | 6 894,00 | Clé `0xd90d0013…f444` (Ethereum) | 6 893,00 USDC vers `0x8c5dc729…10fe`, puis `0xf7c8da79…d921` (Revolut 5) | 0,00 USDC | Revolut 5, étiquette à source unique |
| kraben006 | 15 593,54 | Clé `0x101b5f4d…fb65` (Ethereum) | Dépôts Relay vers son propre wallet jusqu'au 21 oct. ; 0,00247 ETH vers ChangeNOW le 4 oct. | 15 154,83 USDC | La clé |
| OuldLm3alem | 77 250,77 | Clé `0x1b500b6c…5f2c` (Polygon) ; `0xae232f78…c026` (BSC) | POL, USDT, deBridge, CCTP, Hyperliquid, retour | 73 001,19 USDC (Arbitrum), 99,80 USDT et 0,13 BNB (BSC) | La clé, Arbitrum |
| 0xdd97e6 | 63 143,10 | `0xca8b1f1a…6165` (Ethereum) | Aucune, nonce 0 | 26,97 ETH | Cette adresse |

Total des retraits : 493 094,76 $, 25 retraits.

## 3. Ce que sont les mouvements

Le rapprochement (`state/reconcile.json`) classe tous les mouvements de pUSD et de positions des 11 wallets :

- **Dépôts :** chacune des 46 frappes de pUSD liées à un `DEPOSIT` de l'API est trouvée. Les autres frappes sont toutes des `REDEEM`.
- **Retraits :** les 25 sorties de pUSD sont trouvées. Elles passent par le contrat de sortie, qui détruit le pUSD et rend de l'USDC.e, envoyé à Relay. **Le burn n'est pas une destination.**
- **Marché :** achats, ventes et redemptions passent par les contrats Polymarket, ou par des contreparties directes dans la même transaction. Ce sont des exécutions, pas des transferts.
- **Primes :** toutes les autres lignes correspondent à `REWARD`, `MAKER_REBATE`, `TAKER_REBATE` ou `REFERRAL_REWARD`, à une exception près : 0,20 pUSD reçu par OuldLm3alem d'un autre wallet.
- **Transferts de positions hors marché :** 0 sur les 11 wallets.
- **Soldes :** le solde pUSD calculé égale le solde lu sur 11 wallets sur 11.

## 4. OuldLm3alem : le chemin complet

Chaque saut est lu, avec l'actif qui change. Rien ne repose sur une ressemblance de montant.

| UTC | Saut | Preuve |
|---|---|---|
| 10-26 23:50:53 | 77 050,77 $ de pUSD détruits, USDC.e vers Relay, 839 893,73 POL natifs vers la clé dans la même transaction | Reçu `0x909d9602…a6f1`, `LogTransfer` du POL |
| 10-26 23:52:41 | 839 000 POL échangés contre 75 946,74 USDT par la clé elle-même, Uniswap | `0x8c358292…c2d3` |
| 10-29 20:54:51 | 75 946,74 USDT vers le transfert deBridge, ordre donné et reçu par la clé | Ordre `0xb6a2ccbf…3f8e`, statut `ClaimedUnlock` |
| 10-29 20:54:55 | 75 724,74 USDC reçus sur Arbitrum, du solveur `0x555ce236…c35b` | `0x88a0d82f…66b7` |
| 10-29 20:55:52 | 75 724,74 USDC envoyés par CCTP vers Hyperliquid | Message Circle `0x5c5e1650…223a`, `cctp-forward` vers la clé |
| 10-29 21:18 à 21:35 | 303 exécutions sur le perpétuel HYPE, 1 384 778,39 $ de volume, -2 415,41 $ réalisés, 306,71 $ de frais | Registre public Hyperliquid |
| 10-29 22:11:18 | 73 001,19 USDC reviennent sur Arbitrum par CCTP depuis HyperEVM | `0x6edc469d…55a5`, domaine source 19 |
| 10-29 22:11:59 | 888,19 POL deviennent 0,0343 ETH par deBridge | Ordre `0x95a84eb2…df58` |
| 11-02 | La clé détient 73 001,19 USDC et 0,0343 ETH sur Arbitrum, 3,14 POL sur Polygon | Soldes lus |

Attribution de Hyperliquid : registre public de l'adresse, `api.hyperliquid.xyz/info`, lu le 2 nov.

## 5. WenZhuanBuPei : le chemin complet

| UTC | Saut | Transaction |
|---|---|---|
| 10-27 22:58:06 | 27 724,79 $ retirés, USDC reçus sur `0xe820ecb3…87cd` (Arbitrum) par Relay | `0x094f60bf…9b91` |
| 10-27 22:58:10 | 27 724,00 USDC vers `0x3ab2206b…7d50` | `0xa06fecae…40da` |
| 10-27 22:58:11 | 277,24 USDC vers `0x435e3931…dd1d`, soit 1,00 % | `0x8246f439…` |
| 10-27 22:58:14 | 9 943,96 USDC vers `0xbf8f747e…621c` | `0xcad77f71…` |
| 10-27 23:44:29 | 9 436,20 USDC vers `0x5012817a…6ed7` | `0xc73ea34d…` |
| 10-28 00:02:54 | 8 066,60 USDC vers `0x15ba4d74…e552` | `0xd2ced301…` |
| 10-28 17:23:07 | Les trois morceaux, 27 446,76 USDC, regroupés dans une seule transaction vers `0x51cf2d9f…4999` | `0x6ef3a7e7…1547` |

`0x3ab2206b…7d50` a d'autres flux au même rapport : 238 567 reçus pour 236 181,33 envoyés, 75 000 pour 74 250, 60 000 pour 59 400, 50 000 pour 49 500. Les trois adresses à morceaux sont neuves et déléguées (EIP-7702), et `0x51cf2d9f…4999` (nonce 62 528) reçoit de 3 037 expéditeurs : profil d'un service, qui n'a pas d'étiquette. **Ni plateforme ni mixeur n'est démontré.**

## 6. Toutes les lignes

`data/cashout_paths.csv` donne chaque saut, et `graphs/cashout_network.graphml` le graphe.
