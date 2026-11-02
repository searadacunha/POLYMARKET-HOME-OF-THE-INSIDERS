# Exposition aux plateformes, ponts et services de confidentialité

Lu le 2 novembre 2026. Une interaction avec une plateforme dit où l'argent est passé, pas à qui il appartient.

## 1. Réponse

- **Plateformes :** oui, mais seulement à l'entrée pour l'essentiel. KuCoin Hot Wallet 2 sur Solana pour 5 comptes, des adresses étiquetées Binance pour 3 comptes, Revolut et BloFin pour 1 chacun. En sortie : Revolut 5 pour Zoomman17. Étiquettes publiques, pas des preuves d'identité.
- **Échange instantané :** SwftSwap, nom de contrat vérifié, pour brace227 et kraben006. **ChangeNOW**, deux tags Blockscout concordants : sur la clé de kraben006 (834,85 USDC reçus en fév. 2026, 0,00247 ETH envoyés le 4 oct. vers une adresse de dépôt), et sur `0x3eaef6d5…`, financeur de la clé de brace227 fin 2024. NEAR Intents pour un petit échange de gaz de brace227.
- **Ponts :** Relay partout. Aussi Polygon PoS, deBridge, CCTP, Chainflip, THORChain et Across, chacun sur un ou deux comptes.
- **Mixeurs et protocoles de confidentialité :** aucune interaction lue avec Tornado Cash, Railgun ou un contrat étiqueté comme tel, sur tous les historiques lus.
- **Monero :** aucun indice, sur aucun compte.

## 2. Par compte

| Compte | Plateformes | Échange instantané | Ponts | Service dépositaire non attribué | Mixeur ou confidentialité | XMR |
|---|---|---|---|---|---|---|
| Thin-Disclaimer-Life | KuCoin HW2, Binance HW6 | — | Relay | — | Aucune lue | Absente des données accessibles |
| VidenteRibeira | KuCoin HW2 | — | Relay | `GxjcMTWW…nvBW` | Aucune lue | Absente des données accessibles |
| cookedrice | KuCoin HW2 | — | Relay | `GxjcMTWW…nvBW` | Aucune lue | Absente des données accessibles |
| WenZhuanBuPei | Binance (Hot Wallet 34) | — | Relay | `0x3ab2206b…7d50`, `0x51cf2d9f…4999` | Aucune lue | Absente des données accessibles |
| 0x86544e4dfde | Kraken et Binance sur `0x408ce42a…c5b3`, 2023-24 | — | Relay, Polygon PoS | `0x0ce9bdf3…f06d` | Aucune lue | Absente des données accessibles |
| brace227 | BloFin ; KuCoin 10 et Binance 20 en 2022 | SwftSwap ; ChangeNOW en amont, fin 2024 | Relay, THORChain, NEAR Intents | — | Aucune lue | Absente des données accessibles |
| walletwallet8424 | — | — | Relay, Polygon PoS | `0x0ce9bdf3…f06d`, `0xcc0f311e…23f7` | Aucune lue | Absente des données accessibles |
| Zoomman17 | Revolut 1, 5 et 6 | — | Relay, Chainflip | `0x58f298e3…0214` | Aucune lue | Absente des données accessibles |
| kraben006 | Deblock | SwftSwap, ChangeNOW | Relay, Across | `0x58f298e3…0214`, `0xbd1f4462…eb3b`, `0x0c58909d…270d`, `0x7bef1627…5c24` | Aucune lue | Absente des données accessibles |
| OuldLm3alem | KuCoin HW2, Binance (Hot Wallet 34) | — | Relay, deBridge, CCTP | `0xa3222357…59b3` | Aucune lue | Absente des données accessibles |
| 0xdd97e6 | KuCoin HW2 | — | Relay | `0x6bf18baf…7e95` | Aucune lue | Absente des données accessibles |

## 3. Niveau de preuve par catégorie

| Niveau demandé | Ce qui y entre ici |
|---|---|
| Interaction directe confirmée | Relay (documents officiels et identifiant sur les deux chaînes), SwftSwap (nom vérifié), deBridge (ordre lu), CCTP (message lu), Hyperliquid (registre public), Polygon PoS, Uniswap, THORChain |
| Attribution probable, avec justification | Binance, Kraken, Revolut, Chainflip, BloFin, KuCoin 10, ChangeNOW, NEAR Intents, Deblock, MetaMask (listes publiques et tags Blockscout). KuCoin Hot Wallet 2 : une seule source, Orb |
| Simple compatibilité | ChangeNOW liste XMR, et touche la clé de kraben006 et un financeur ancien de la clé de brace227 : rien ne dit quel actif était en face. Un service qui proposerait XMR derrière `GxjcMTWW…nvBW`, `0x3ab2206b…7d50` ou `0x51cf2d9f…4999` : rien ne l'indique, rien ne l'exclut |
| Hypothèse non vérifiée | Dépôt chez Revolut pour `0x8c5dc729…10fe` ; plateforme de sortie pour `0x51cf2d9f…4999` ; Kraken derrière les portefeuilles rechargés en ETH par Kraken: Hot Wallet 2 |
| Aucune preuve observée | Tornado Cash, Railgun et tout contrat de confidentialité étiqueté ; toute conversion XMR ; FixedFloat et SimpleSwap |

## 4. Monero

**Statut pour les 11 comptes : absent des données accessibles.** Aucune transaction lue n'implique un service dont on peut montrer qu'il a converti ces fonds en XMR.

- **Ce qui a été cherché :** toute adresse étiquetée parmi les services proposant XMR, y compris ChangeNOW, FixedFloat, SimpleSwap, StealthEX et Exolix, dans les listes publiques, les tags Blockscout et sur tous les historiques lus. **Seul résultat : ChangeNOW.** Il paie 834,85 USDC à la clé de kraben006 en fév. 2026 et reçoit d'elle, par une adresse de dépôt, 0,00241 ETH le 4 oct. 2026. Il finance `0x3eaef6d5…`, qui envoie 291,32 USDT à la clé de brace227 en janv. 2025. Ces montants sont petits, et aucun de ces flux n'est lu comme une conversion XMR : ChangeNOW échange des centaines d'actifs.
- **Liste de coins :** ChangeNOW liste XMR aujourd'hui (`evidence/docs/changenow_currencies.json`). SWFT ne le liste pas aujourd'hui (`evidence/docs/swft_coinlist_all.json`). Ces listes datent de la lecture, pas des transactions.
- **Ce que cela ne dit pas :** les fonds entrent dans des comptes de plateforme et des services non identifiés. Ce qui s'y passe est invisible. Une conversion XMR avant le financement, ou après `GxjcMTWW…nvBW`, n'est ni démontrée ni exclue. Une rupture de trace n'est pas un indice de Monero.
- **Ce qu'il faudrait :** le registre des services, par voie légale.

## 5. Tous les services touchés

Montant : ordre de grandeur en dollars, natifs compris au cours approximatif, entrées et sorties additionnées, pour classer seulement. Une ligne par service, détail par dossier dans `data/service_attributions.csv`.

| Service | Catégorie | Chaînes | Dossiers | Transferts | Ordre de grandeur $ | Niveau |
|---|---|---|---|---|---|---|
| Relay EVM solver | pont | ethereum, polygon | 0x86544e4dfde, 0xdd97e6, OuldLm3alem, Thin-Disclaimer-Life, VidenteRibeira, WenZhuanBuPei, Zoomman17, brace227, cookedrice, kraben006, walletwallet8424 | 27 | 368 463 | named_source |
| KuCoin Hot Wallet 2 | plateforme | solana | 0xdd97e6, OuldLm3alem, Thin-Disclaimer-Life, VidenteRibeira, cookedrice | 6 | 102 834 | named_source |
| Relay Depository | pont | ethereum, polygon | 0x86544e4dfde, Zoomman17, brace227, kraben006, walletwallet8424 | 35 | 100 969 | named_source |
| Unidentified Solana custodial service (cosigns sweeps of i | service dépositaire non attribué | solana | VidenteRibeira, cookedrice | 2 | 90 647 | measured |
| Relay v3 Router | pont | polygon | OuldLm3alem | 1 | 83 989 | named_source |
| UniversalRouter | mesuré | polygon | OuldLm3alem | 1 | 83 900 | measured |
| deBridge: Crosschain Forwarder Proxy | pont | polygon | OuldLm3alem | 2 | 76 036 | blockscout_tag_chain_1 |
| 0x555ce236c0220695b68341bc48c68d52210cc35b | mesuré | arbitrum | OuldLm3alem | 1 | 75 725 | measured |
| CctpExtension | mesuré | arbitrum | OuldLm3alem | 1 | 75 725 | measured |
| Circle SingleOwnerMSCA account of an unattributed custodia | service dépositaire non attribué | polygon | 0x86544e4dfde, walletwallet8424 | 5 | 47 972 | measured |
| Binance: Hot Wallet 34 | plateforme | arbitrum, polygon | OuldLm3alem, WenZhuanBuPei | 2 | 31 910 | blockscout_tag_chain_1 |
| 0x3ab2206b98b01ba256dbdd4c50208bf17ab27d50 | mesuré | arbitrum | WenZhuanBuPei | 1 | 27 724 | measured |
| 0xa3222357a0eccf60c73606170be6c99adecb59b3 | mesuré | ethereum | OuldLm3alem | 1 | 23 386 | measured |
| MetaMask: Swaps Spender | routeur ou infrastructure de portefeuille | ethereum | Zoomman17, brace227, walletwallet8424 | 5 | 19 831 | blockscout_tag_chain_1 |
| SwftSwap (SWFT Blockchain) | échange instantané | ethereum | brace227, kraben006 | 5 | 15 285 | verified_contract_name |
| Polygon (Matic): Bridge | pont | ethereum | walletwallet8424 | 1 | 15 250 | blockscout_tag_chain_1 |
| Swap contract used through MetaMask delegation | routeur ou infrastructure de portefeuille | polygon | walletwallet8424 | 1 | 15 250 | measured |
| Kraken: Hot Wallet | plateforme | ethereum | 0x86544e4dfde | 4 | 11 867 | blockscout_tag_chain_1 |
| Revolut: Hot Wallet | plateforme | ethereum | Zoomman17 | 8 | 10 121 | blockscout_tag_chain_1 |
| Binance: Hot Wallet | plateforme | ethereum | 0x86544e4dfde, brace227 | 5 | 9 752 | blockscout_tag_chain_1 |
| Polymarket pUSD — CollateralToken Poly v2 | contrat Polymarket | polygon | brace227 | 1 | 8 062 | official_doc |
| Payout wallet of an unattributed custodial service | service dépositaire non attribué | ethereum | Zoomman17, kraben006 | 11 | 5 927 | measured |
| Chainflip 1 | pont | ethereum | Zoomman17 | 1 | 5 439 | blockscout_tag_chain_1 |
| Polymarket Neg Risk CTF Exchange | contrat Polymarket | polygon | brace227 | 5 | 2 251 | official_doc |
| ChangeNOW: Hot Wallet 3 | échange instantané | ethereum | brace227, kraben006 | 6 | 1 286 | blockscout_tag_chain_1 |
| ProxyWallet | mesuré | polygon | brace227 | 1 | 1 000 | measured |
| UniswapX: Dutch Order Reactor V2 | routeur ou infrastructure de portefeuille | ethereum | 0x86544e4dfde | 1 | 871 | blockscout_tag_chain_1 |
| 9byY2BBoUrQijZ5Xwe2KKgsmwtSCxjURLFTGZZNdrGdw | mesuré | solana | brace227 | 1 | 305 | measured |
| KuCoin: Hot Wallet | plateforme | ethereum | brace227 | 2 | 296 | blockscout_tag_chain_1 |
| Revolut 6 | plateforme | ethereum | Zoomman17 | 1 | 260 | blockscout_tag_chain_1 |
| Deblock: Wallet 1 | autre étiquette | ethereum | kraben006 | 3 | 253 | blockscout_tag_chain_1 |
| BloFin: Hot Wallet 1 | plateforme | ethereum | brace227 | 1 | 110 | blockscout_tag_chain_1 |
| deBridge: DlnDestination | pont | arbitrum | OuldLm3alem | 1 | 79 | blockscout_tag_chain_1 |
| 0xcad97616f91872c02ba3553db315db4015cbe850 | mesuré | ethereum | kraben006 | 1 | 49 | measured |
| B48kNVXs4YK4amkBCH2XokQiv1SeiVQGHDR17xDeKAAn | mesuré | solana | brace227 | 1 | 27 | measured |
| ChangeNOW 16 | plateforme | ethereum | brace227 | 2 | 23 | named_source |
| MetaMask: MetaBridge V2 Spender | pont | ethereum | Zoomman17 | 1 | 23 | blockscout_tag_chain_1 |
| THORChain: THORChain Router v4.1.1 | pont | ethereum | brace227 | 2 | 14 | blockscout_tag_chain_1 |
| MetaMask: Gas Station | routeur ou infrastructure de portefeuille | ethereum | Zoomman17, brace227, walletwallet8424 | 9 | 12 | blockscout_tag_chain_1 |
| Swap Router | routeur ou infrastructure de portefeuille | ethereum | Zoomman17 | 1 | 10 | blockscout_tag_chain_1 |
| MetaMask: Gas Station Swap | routeur ou infrastructure de portefeuille | ethereum | Zoomman17, brace227 | 7 | 8 | blockscout_tag_chain_1 |
| MetaMask: Meta Bridge | pont | ethereum | Zoomman17 | 1 | 8 | blockscout_tag_chain_1 |
| ChangeNOW Dep: 0x3f3...07B | échange instantané | ethereum | kraben006 | 1 | 6 | blockscout_tag_chain_1 |
| NEAR Intents | pont | ethereum | brace227 | 1 | 5 | blockscout_tag_chain_1 |
| Relay solver | pont | ethereum | brace227 | 1 | 4 | official_doc |
| MetaMask: Gas Station 2 | routeur ou infrastructure de portefeuille | ethereum | Zoomman17 | 3 | 4 | blockscout_tag_chain_1 |
| Relayer of MetaMask-delegated transactions | routeur ou infrastructure de portefeuille | ethereum | Zoomman17, brace227 | 3 | 2 | measured |
