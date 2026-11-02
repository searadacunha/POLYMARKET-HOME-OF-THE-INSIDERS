# Financement et sorties des 11 comptes du Ballon d'Or 2026

Enquête historique, données lues le 2 novembre 2026. Niveaux : **démontré** (lu sur la chaîne), **protocole** (identifiant d'un pont lu sur les deux chaînes ou enregistrement du protocole), **attribution** (flux démontré, nom du service selon une étiquette ou une mesure), **hypothèse** (compatible, non démontré), **inaccessible** (registre privé).

Une adresse n'est pas une personne. Ces comptes sont des sujets d'investigation : rien ici ne démontre ni un propriétaire commun, ni un délit d'initié.

## 1. Résultat

**Relay est le seul service commun aux onze comptes.** Aucune source personnelle commune n'apparaît à l'échelle du groupe. L'argent sort presque partout de plateformes ou de services dépositaires, puis traverse Relay, qui met fin à la lecture directe entre chaînes mais laisse un identifiant vérifiable.

1. **D'où vient l'argent ?** Les 304 137,63 $ de dépôts remontent à des plateformes étiquetées pour plus de la moitié : KuCoin Hot Wallet 2 sur Solana pour 5 comptes et 102 833,93 $, des adresses étiquetées Binance pour 3 comptes et 65 755,73 $, plus Revolut et BloFin. Le reste vient de services non attribués, de SwftSwap et de Chainflip. Une seule branche remonte à un portefeuille personnel ancien : `0x408ce42a…c5b3`, pour 2 457,76 $.
2. **Exchange, pont, mixeur, Monero ?** Relay sur les 46 dépôts et sur 24 des 25 retraits, le 25e étant un échange Relay sur la même chaîne. **Aucune interaction lue avec Tornado Cash, Railgun ou un autre mixeur étiqueté. Aucun indice de Monero.** Cela ne l'exclut pas derrière les comptes de plateforme et les services non identifiés.
3. **Où est allé l'argent ?** Sur 493 094,76 $ retirés, **environ 74 % n'avaient pas quitté leur première adresse ou y étaient revenus le 2 novembre** : 299 565,17 $ en stablecoins et 26,97 ETH sur 7 comptes. Trois comptes ont déposé chez des services non identifiés, soit 118 371,00 $ ; Zoomman17 a envoyé 6 893,00 USDC vers une adresse de dépôt balayée par Revolut 5. **Aucune destination finale commune.**
4. **Financeurs ou destinations communs ?** **Un lien fort, et il est nouveau.** La clé de brace227 finance à 100 % une autre clé, qui possède un wallet Polymarket non nommé par la presse à ma connaissance, `0xa8e64a3c…74a5`. Ce wallet n'a acheté que du Kane Oui, et le partage se fait à parts presque égales avec brace227. La même clé envoie aussi 0,00205 ETH à la clé de kraben006. Aucune autre paire n'a de lien direct ni d'adresse personnelle partagée.

**Ce que cela ne démontre pas.** Ni propriétaire commun, ni coordination, ni information privilégiée. Une origine commune n'est pas un délit d'initié. La presse a choisi ces comptes après coup, ce qui biaise toute comparaison.

| Compte | Origine la plus proche | Service d'entrée | Destination des retraits | Sorti de la première adresse ? | XMR | Où la trace devient incertaine |
|---|---|---|---|---|---|---|
| Thin-Disclaimer-Life | KuCoin (Solana), Binance (BSC) | Relay, adresse de pont | 2 adresses Solana | Non : 79 537,63 USDC en place | Absente des données accessibles | Comptes de plateforme, en amont |
| VidenteRibeira | KuCoin (Solana) | Relay, adresse de pont | Dépôt chez `GxjcMTWW…nvBW` | Oui, balayé en 4 s | Absente des données accessibles | Service non identifié, en aval |
| cookedrice | KuCoin (Solana) | Relay, adresse de pont | Dépôt chez `GxjcMTWW…nvBW` | Oui, balayé en 2 s | Absente des données accessibles | Service non identifié, en aval |
| WenZhuanBuPei | Binance (Polygon) | Relay, adresse de pont | Intermédiaire à 1 %, puis service | Oui | Absente des données accessibles | `0x51cf2d9f…4999`, en aval |
| 0x86544e4dfde | Service Circle non attribué ; portefeuille ancien | Relay, interface et adresse de pont | Clé, Ethereum | Non : 74 198,32 USDC en place | Absente des données accessibles | Service non attribué, en amont |
| brace227 | SwftSwap, BloFin | Relay, interface | Clé, Ethereum | Non : 22 024,57 USDC en place | Absente des données accessibles | SwftSwap, en amont |
| walletwallet8424 | Adresse active non étiquetée ; service Circle | Relay, interface | Clé, Ethereum | Non : 35 546,89 USDC en place | Absente des données accessibles | `0xcc0f311e…23f7`, en amont |
| Zoomman17 | Revolut, Chainflip | Relay, interface | Adresse de dépôt, puis Revolut 5 | Oui | Absente des données accessibles | Revolut, en aval ; Chainflip, en amont |
| kraben006 | Portefeuilles de paiement non attribués | Relay, interface | Clé, Ethereum | Non : 15 154,83 USDC en place | Absente des données accessibles | Service non attribué, en amont |
| OuldLm3alem | KuCoin, Binance, contrat non attribué | Relay, adresse de pont | Clé, puis Hyperliquid, retour | Revenu : 73 001,19 USDC sur Arbitrum | Absente des données accessibles | En amont seulement |
| 0xdd97e6 | KuCoin ; service BSC non attribué | Relay, adresse de pont | `0xca8b1f1a…6165` | Non : 26,97 ETH en place | Absente des données accessibles | En amont seulement |

## 2. Matrice de liens entre les 11 comptes

D : transfert direct entre clés. h : hub non attribué partagé (pas un lien). s : seulement des services nommés partagés (pas un lien). Vide : aucune adresse partagée dans les historiques lus.

|  | thin | vidente | cookedric | wen | 0x86544e4 | brace227 | walletwal | zoomman17 | kraben006 | ouldlm3al | 0xdd97e6 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| thin | · | s | s | s | s |  |  |  |  | s | s |
| vidente | s | · | s | s | s |  |  |  |  | s | s |
| cookedric | s | s | · | s | s |  |  |  |  | s | s |
| wen | s | s | s | · | s |  | s |  |  | s | s |
| 0x86544e4 | s | s | s | s | · | s | s | s | s | s | s |
| brace227 |  |  |  |  | s | · | s | s | **D** | s | s |
| walletwal |  |  |  | s | s | s | · | s | s |  | s |
| zoomman17 |  |  |  |  | s | s | s | · | s | s | s |
| kraben006 |  |  |  |  | s | **D** | s | s | · | s | s |
| ouldlm3al | s | s | s | s | s | s |  | s | s | · | s |
| 0xdd97e6 | s | s | s | s | s | s | s | s | s | s | · |

**La seule paire avec un lien direct est brace227 et kraben006.** Les « s » sont des services communs (Relay, KuCoin, MetaMask, SwftSwap, ChangeNOW…) et ne relient personne. Le wallet `0xa8e64a3c…74a5` n'est pas dans cette matrice : il n'est pas un des onze, il est relié à brace227 seul.

### Le financement du wallet `0xa8e64a3c…74a5` par la clé de brace227

**Démontré par la chaîne :**

| UTC | Fait | Transaction |
|---|---|---|
| 10-08 10:13:20 | Wallet `0xa8e64a3c…74a5` créé par la fabrique Polymarket, propriétaire `0x48ec106c…b12d` (`owner()` lu, adresse recalculée) | `0xa6e22997…5d7b` |
| 10-09 20:03:47 et 20:06:35 | SwftSwap paie 4 337,52 et 83,89 USDC à la clé de brace227 | `0xead283d8…2f3f`, `0xb193c0e9…` |
| 10-09 20:28:35 | La clé envoie **2 210,00 USDC** à `0x48ec106c…b12d` : sa première entrée | `0x7e3aecb9…` |
| 10-09 20:36:28 | Dépôt de 2 200,00 $ sur `0xa8e64a3c…74a5` | `0x3cd7757a…` |
| 10-09 20:37:10 | Premier achat de ce wallet, sur Kane Oui | |
| 10-09 20:48:59 | La clé dépose 2 186,43 $ sur le wallet de brace227 | `0xdade8977…` |
| 10-10 00:26:47 | SwftSwap paie 5 925,84 USDC à la clé | `0x492e2f05…` |
| 10-10 00:51:11 | La clé envoie **2 960,00 USDC** à `0x48ec106c…b12d` | `0xb07c3c53…` |
| 10-10 10:48:04 | Dépôt de 2 965,00 $ sur `0xa8e64a3c…74a5` | `0xdcf9e178…` |
| 10-27 01:58:20 | Redemption de 8 061,89 $ sur `0xa8e64a3c…74a5`, marché Kane | `0xe33c61e7…` |
| 10-27 18:49:06 | Retrait de 8 061,90 $ vers `0x48ec106c…b12d`, qui détient encore 5 062,18 USDC et a échangé 3 000 USDC contre 2 969,57 mUSD le 29 oct. | `0x09d05d70…` |

- **Exclusif.** L'activité de `0xa8e64a3c…74a5` : 2 dépôts, 16 achats, tous sur « Will Harry Kane win the 2026 Ballon d'Or? », Oui, pour 5 164,99 $ et 8 061,89 parts, du 9 au 11 oct., 1 redemption, 1 retrait. Retraits moins dépôts : 2 896,90 $.
- **Parts égales** (relevé par la session parallèle de l'enquête, relu ici) : 2 210,00 sur 4 421,41 USDC, soit 49,98 %, le 9 oct. ; 2 960,00 sur 5 925,84 USDC, soit 49,95 %, le 10 oct. Total 5 170,00 $ vers `0x48ec106c…b12d`, contre 5 173,25 $ vers le wallet de brace227 sur ses 4 premiers dépôts.
- **Clé neuve.** Avant son premier dépôt, `0x48ec106c…b12d` ne reçoit que les 2 210,00 USDC de la clé de brace227, plus du gaz de MetaMask. Sur 50 adresses testées, 94 essais en tout, seule celle-ci possède un Deposit Wallet actif : 44 adresses touchées par les clés des onze ou par la marche, sous les 2 formes de wallet, et 6 clés de dossiers sous l'ancienne forme seulement, leur forme récente étant leur wallet déjà connu. Le calcul de l'adresse retrouve 11 wallets connus sur 11. Limite : 5 clés de dossiers sans flux lu, et les anciens proxys Safe et Magic, ne sont pas testés.
- **Création avant les fonds.** Le wallet est créé la veille du premier versement.

**Le lien avec kraben006.** `0xd07bea20…2b98`, 4 oct. 13:54:35 UTC, 0,00205 ETH de la clé de brace227 vers celle de kraben006, envoi simple. Il suit de 108 s un paiement Relay de 0,00169 ETH venu de `7XUJsJBN…JfrZc` sur Solana, pour 4,62 USDT, prouvé par le même identifiant sur les deux chaînes. La clé part ainsi de 0,00207 ETH et n'en garde presque rien. Sa dernière sortie avant cette date remonte au 28 avril 2025 sur Ethereum et au 17 mai 2025 sur BSC : « première sortie en 17 mois » de l'audit devient 16 mois et demi. Sur la continuité de la valeur, relevée par la même session : au moins 81 % de l'envoi vient forcément du paiement Relay.

**Autres points communs entre brace227 et kraben006, plus faibles :** SwftSwap (15 096,29 $ et 188,97 $) et ChangeNOW (`0xdd3d72c5…`, Hot Wallet 3), deux services. La clé de kraben006 envoie aussi, 10 h après le transfert, 0,00247 ETH vers une adresse de dépôt de ChangeNOW : le gaz reçu semble donc avoir été revendu, ce qui n'est pas démontré.

**Ce qui va contre un opérateur unique** (même source, relu) : brace227 vend son Kane à 0,999 le 26 oct. à 23:10, alors que `0xa8e64a3c…74a5` ne vend jamais, attend le lot de redemption et retire 16 h 51 plus tard. Deux clés distinctes, deux stratégies de sortie.

**Ce que cela établit :** un lien financier direct et important entre ces deux clés, dont l'une finance presque entièrement l'autre juste avant des paris sur le même marché.

**Ce que cela n'établit pas :** qu'une seule personne contrôle les deux clés. Deux proches, un prêteur et un emprunteur, ou une avance entre amis donnent la même image. Rien ne permet de dire si ce wallet est le 12e compte allégué par la presse. Aucune information privilégiée n'en découle.

## 3. Les 11 comptes

### Thin-Disclaimer-Life

Wallet `0x8d3319c51520518ad01f6744486ceea29f376f5b`. Clé propriétaire lue sur la chaîne : `0x1bf0b469f7f3612657e99bf785e470eee2a76028`. Lien étiquette vers adresse : ALIAS_EXACT_AND_SHARES. 3 dépôts pour 45 679,23 $, 4 retraits pour 80 037,93 $, soit 34 358,70 $ de retraits moins dépôts.

**En bref.** Trois dépôts, deux plateformes. Le premier sort de KuCoin Hot Wallet 2 sur Solana, les deux autres de Binance Hot Wallet 6 sur BSC. Tout passe par Relay. Les retraits partent vers deux adresses Solana qui n'ont plus bougé : 79 537,63 USDC et 4,93 SOL y restent. Rien n'est sorti.

| Question | Réponse | Niveau |
|---|---|---|
| Origine des financements | 45 679,23 $ en 3 dépôts : 11 833,23 $ par KuCoin Hot Wallet 2, 33 846,00 $ par Binance Hot Wallet 6 | démontré pour les flux, attribution pour les noms |
| Premier financeur identifiable | `BmFdpraQhk…ymy6` (KuCoin Hot Wallet 2, Solana) et `0x8894e0a0…2d4e3` (Binance Hot Wallet 6, BSC) | attribution |
| Dernier maillon avant dépôt | Adresse de pont `0x8e43af99…9865`, payée par le solveur Relay | démontré, protocole |
| Services | KuCoin, Binance, Relay | attribution, protocole |
| XMR | Absente des données accessibles | aucun indice |
| Retraits | 80 037,93 $ vers `CXVYMP5q…GrfJ` et `EnHRjTP4…PZ8B` (Solana) | protocole |
| Où la trace devient incertaine | En amont, dans les comptes des deux plateformes. Aucune sortie en aval. | inaccessible |

**Sources de l'argent, par dépôt** (répartition PEPS quand plusieurs entrées se mêlent, convention comptable) :

| Dernière source publique | Chaîne | Service | Catégorie | Dollars alloués | Tx |
|---|---|---|---|---|---|
| `0x8894e0a0…d4e3` | bsc | Binance: Hot Wallet | exchange | 33 846,00 | 2 |
| `BmFdpraQhk…ymy6` | solana | KuCoin Hot Wallet 2 | exchange | 11 833,23 | 1 |

**Soldes lus le 2 nov.** :

| Adresse du dossier | Chaîne | Solde lu | Lu à (UTC) |
|---|---|---|---|
| `CXVYMP5qxB…GrfJ` | solana | 2.468227 SOL ; 39 999.850544 USDC | 2026-11-02 14:02:38 |
| `EnHRjTP4pK…PZ8B` | solana | 2.465146 SOL ; 39 537.780037 USDC | 2026-11-02 14:02:38 |

**Rapprochement.** Solde pUSD calculé 0.000000, lu 0.000000. Dépôts 3/3 et retraits 4/4 rapprochés de l'API. Frappes hors dépôts : 2, toutes des remboursements (`REDEEM`) : oui. Transferts de positions hors transaction de marché : 0. Mouvements de pUSD absents de l'API : 0.

**Chemins non résolus** :

- Qui a approvisionné les comptes KuCoin et Binance : registres privés. La clé `0x1bf0b469…6028` n'a aucun flux lu sur Ethereum, Polygon, Arbitrum et Optimism, et un nonce de 0 sur les six chaînes testées.

**Confiance et explications alternatives.** Flux : haute. Noms : moyenne : KuCoin repose sur Orb seul, Binance sur deux sources publiques (liste de 2023 et Blockscout). Alternatives : deux personnes différentes derrière ces comptes de plateforme, ou un intermédiaire qui retire pour autrui.

**Transactions vérifiables, financement :**

| UTC | Chaîne | Actif | Montant | De | Vers | Événement | Service | Preuve | Transaction |
|---|---|---|---|---|---|---|---|---|---|
| 2026-10-11 15:23:10 | solana | USDC | 11 833,23 | `BmFdpraQhk…ymy6` | `EMu2EAWjzP…Mqsd` | transfer_in | KuCoin Hot Wallet 2 | CHAINE+ATTRIBUTION | `3bn5hJNsXAx814rxWrHrHUPqY5C53NF3sSH4CfH8uhk19ExDFUrNAcE6g73oj5Vmcwc6NTBcD7wpJ8pmdLHnJR2t` |
| 2026-10-11 15:23:31 | polygon | USDC.e→pUSD | 11 833,23 | `0x8e43af99…9865` | `0x8d3319c5…6f5b` | wrap_mint_pusd |  | CHAINE | `0x761f6058829482bc5fc66acd8b6d5bcc583e96a463ac75e52d666b31fd6f32d1` |
| 2026-10-11 15:23:31 | solana | USDC | 11 833,23 | `EMu2EAWjzP…Mqsd` | `0x8e43af99…9865` | relay_escrow_to_payout |  | PROTOCOLE | `3tqC6ccwrcS7a7Lfm4k3tkJZN9iTDsGSzY2gP4FY8T1g21tkLMto7DJnXEGhUpGDmqeaCb16VqJ5GkzKiHypwRyW` |
| 2026-10-13 13:46:53 | bsc | USDC | 11 946,00 | `0x8894e0a0…d4e3` | `0x8e43af99…9865` | transfer_into_bridge_address | Binance: Hot Wallet | CHAINE+ATTRIBUTION | `0x23e2219c3e902360004a3f893ac3560649617a0ac372ff9aa9d218f0ad442ff3` |
| 2026-10-13 13:47:23 | polygon | USDC.e→pUSD | 11 946,00 | `0x8e43af99…9865` | `0x8d3319c5…6f5b` | wrap_mint_pusd |  | CHAINE | `0x1e2c6576867d250de440e43b97bc01fd456952c30b1c6811fa0665cbf216a2f6` |
| 2026-10-13 13:47:23 | bsc | USDC | 11 946,00 | `0x8e43af99…9865` | `0x8e43af99…9865` | relay_bridge_deposit_address |  | PROTOCOLE | `0x92f86b5a04511bfe30aff0c7193aee4c1ea0247dad3740f7fd6669cac99593f2` |
| 2026-10-13 18:36:40 | bsc | USDC | 21 900,00 | `0x8894e0a0…d4e3` | `0x8e43af99…9865` | transfer_into_bridge_address | Binance: Hot Wallet | CHAINE+ATTRIBUTION | `0x3d90c0a34035a1efa225a2bf308f412e738e10eb4d1c9c2201e51bed202c37a7` |
| 2026-10-13 18:37:10 | polygon | USDC.e→pUSD | 21 900,00 | `0x8e43af99…9865` | `0x8d3319c5…6f5b` | wrap_mint_pusd |  | CHAINE | `0x975d526512ae2b0af5dc50b05af0b409b8686dfe9a522409483342bccc084aec` |
| 2026-10-13 18:37:10 | bsc | USDC | 21 900,00 | `0x8e43af99…9865` | `0x8e43af99…9865` | relay_bridge_deposit_address |  | PROTOCOLE | `0xaed0d982e0d0c9c907393cd2de73ed10319e95cb677fbcdae8475c44925c37c1` |

**Transactions vérifiables, sorties :**

| UTC | Chaîne | Actif | Montant | De | Vers | Événement | Service | Preuve | Transaction |
|---|---|---|---|---|---|---|---|---|---|
| 2026-10-27 01:24:26 | polygon | pUSD | 250,00 | `0x8d3319c5…6f5b` | `0x00000000…0000` | burn_pusd_unwrap |  | CHAINE | `0x6373a98fb86f82e1562448ccddf261d537a06a7112180f1d414e3f0968d9be7c` |
| 2026-10-27 01:24:26 | solana | SOL | 2,47 | `0x8d3319c5…6f5b` | `CXVYMP5qxB…GrfJ` | relay_payout_to_recipient |  | PROTOCOLE | `3hB2wsiT2GhpJ9k3wajsJTsxpS28HbSuZySnW61RJy5zeVtHqzSakELK66xzrzWGkZ87xZ6Xr8MKoG9SKfBTrY89` |
| 2026-10-27 01:27:32 | polygon | pUSD | 40 000,00 | `0x8d3319c5…6f5b` | `0x00000000…0000` | burn_pusd_unwrap |  | CHAINE | `0xa41a56f185a14d413f23839a94f0e92574dbf72a46b132dde1984f44d88b288e` |
| 2026-10-27 01:27:32 | solana | USDC | 39 999,85 | `0x8d3319c5…6f5b` | `CXVYMP5qxB…GrfJ` | relay_payout_to_recipient |  | PROTOCOLE | `rwiu1FRYMBHqQTiXVdqCssrSs8YQZY2my7fLdNXvrBWDG8V4QckoRoirN3WGeSM6sY3XxC7ERwg486zHmLZEsEd` |
| 2026-10-27 01:28:14 | polygon | pUSD | 250,00 | `0x8d3319c5…6f5b` | `0x00000000…0000` | burn_pusd_unwrap |  | CHAINE | `0xe35ea7f316355dc91347aa2f409aa030bb696035151a5ea5d8d72a69d11df989` |
| 2026-10-27 01:28:14 | solana | SOL | 2,47 | `0x8d3319c5…6f5b` | `EnHRjTP4pK…PZ8B` | relay_payout_to_recipient |  | PROTOCOLE | `2UzjMVyoNhLo2tpSeLqGsqBByBjr8Y74LMmvYyuaNbExtF25TCtU29xCKuk372H9SA2K9VLx12sfoqT1eFSgvGW3` |
| 2026-10-27 01:29:03 | polygon | pUSD | 39 537,93 | `0x8d3319c5…6f5b` | `0x00000000…0000` | burn_pusd_unwrap |  | CHAINE | `0x5c4d9506a42a1ecb190233847a7baea1f967766873218d042c714fb00bf31b90` |
| 2026-10-27 01:29:03 | solana | USDC | 39 537,78 | `0x8d3319c5…6f5b` | `EnHRjTP4pK…PZ8B` | relay_payout_to_recipient |  | PROTOCOLE | `4HRAyjtxWPQ4Dn4yGAr9Hr5uXp4hMyKmiHUonaLosSPjYpT1z2VAFkeyGLk4Es6urGkauByp6Cbs4RFU4opdhk5o` |

### VidenteRibeira

Wallet `0x5f8b30fde56bd2d2f3853769602330aeb9f1866a`. Clé propriétaire lue sur la chaîne : `0x3cb3f4f6b1a81bdf523e36b7f5fa5081113f0f5e`. Lien étiquette vers adresse : ALIAS_EXACT_AND_SHARES. 2 dépôts pour 28 029,96 $, 1 retraits pour 51 509,88 $, soit 23 479,92 $ de retraits moins dépôts.

**En bref.** Deux dépôts depuis KuCoin Hot Wallet 2, par une adresse Solana de passage, puis Relay. Le retrait de 51 509,88 $ arrive en USDT sur une adresse de dépôt d'un service dépositaire non identifié, qui le balaie 4 secondes plus tard avec sa propre signature. La trace s'arrête là.

| Question | Réponse | Niveau |
|---|---|---|
| Origine des financements | 28 029,96 $ en 2 dépôts, tous deux par KuCoin Hot Wallet 2 | démontré pour les flux, attribution pour le nom |
| Premier financeur identifiable | `BmFdpraQhk…ymy6` (KuCoin Hot Wallet 2) | attribution |
| Dernier maillon avant dépôt | `5xHWduZu…uz1a` (Solana) puis Relay, puis `0x6d24d945…6df8` | démontré, protocole |
| Services | KuCoin, Relay, `GxjcMTWW…nvBW` (service non identifié) | attribution, protocole, mesure |
| XMR | Absente des données accessibles : la trace s'arrête à un service non identifié, ce qui n'est pas un indice | aucun indice |
| Retraits | 51 509,88 $ devenus 51 489,09 USDT sur `DMmDPF9s…1wt5T`, puis 51 489,00 USDT vers `GxjcMTWW…nvBW` | protocole, démontré |
| Où la trace devient incertaine | À l'entrée de `GxjcMTWW…nvBW` : ce service mêle ses clients | inaccessible |

**Sources de l'argent, par dépôt** (répartition PEPS quand plusieurs entrées se mêlent, convention comptable) :

| Dernière source publique | Chaîne | Service | Catégorie | Dollars alloués | Tx |
|---|---|---|---|---|---|
| `BmFdpraQhk…ymy6` | solana | KuCoin Hot Wallet 2 | exchange | 28 029,96 | 2 |

**Soldes lus le 2 nov.** :

| Adresse du dossier | Chaîne | Solde lu | Lu à (UTC) |
|---|---|---|---|
| `DMmDPF9sFc…wt5T` | solana | 0.092043 USDT | 2026-11-02 14:02:38 |

**Rapprochement.** Solde pUSD calculé 0.000000, lu 0.000000. Dépôts 2/2 et retraits 1/1 rapprochés de l'API. Frappes hors dépôts : 1, toutes des remboursements (`REDEEM`) : oui. Transferts de positions hors transaction de marché : 0. Mouvements de pUSD absents de l'API : 0.

**Chemins non résolus** :

- Sortie de `GxjcMTWW…nvBW` : dans les 6 h suivant le balayage, 128 destinataires sur 260 transactions tirées, aucun ne reçoit un total proche de 99 à 101 % du montant. Il faudrait le registre du service.

**Confiance et explications alternatives.** Flux : haute. Le balayage cosigné désigne une adresse de dépôt tenue par le service. Alternatives : plateforme, service de paiement ou échange : aucune étiquette ne permet de choisir.

**Transactions vérifiables, financement :**

| UTC | Chaîne | Actif | Montant | De | Vers | Événement | Service | Preuve | Transaction |
|---|---|---|---|---|---|---|---|---|---|
| 2026-10-15 21:06:33 | solana | USDC | 9 940,01 | `BmFdpraQhk…ymy6` | `5xHWduZuzC…uz1a` | transfer_in | KuCoin Hot Wallet 2 | CHAINE+ATTRIBUTION | `622wDP15doVfkbQf8CG7LgFr7aihdS7L4vHb8NQKpmLruMkka7efttqRuhnh2TZ1bWPDPAaCjszS5Y6tdzsQFL28` |
| 2026-10-15 21:06:54 | polygon | USDC.e→pUSD | 9 940,01 | `0x6d24d945…6df8` | `0x5f8b30fd…866a` | wrap_mint_pusd |  | CHAINE | `0xcb790208996b569b3671f4d5090acae8ca22eff2a3cec6029b8aeee2081aa2d1` |
| 2026-10-15 21:06:54 | solana | USDC | 9 940,01 | `5xHWduZuzC…uz1a` | `0x6d24d945…6df8` | relay_escrow_to_payout |  | PROTOCOLE | `uqknnPyKXoxmBx9tce4HhJPmVR7onV6QsWaaWgNbP8QTS7qEzPGXNYdANSTn48ezukGsK6EBwsqMuVdJbgQrYrL` |
| 2026-10-16 20:32:43 | solana | USDC | 18 089,95 | `BmFdpraQhk…ymy6` | `5xHWduZuzC…uz1a` | transfer_in | KuCoin Hot Wallet 2 | CHAINE+ATTRIBUTION | `kfZ1ydAjy19WmzSpXGfgs7LfZ3mzcu5xFRZCWuhFHHpsD35F68GzYFWR2tsJ6evuY17yait2mbR5DUAT3q1YnsB` |
| 2026-10-16 20:33:05 | polygon | USDC.e→pUSD | 18 089,95 | `0x6d24d945…6df8` | `0x5f8b30fd…866a` | wrap_mint_pusd |  | CHAINE | `0xd2297a703dce632821afdf1ad1ab71ccc5f0b0113b64a429939a83777423b9a7` |
| 2026-10-16 20:33:05 | solana | USDC | 18 089,95 | `5xHWduZuzC…uz1a` | `0x6d24d945…6df8` | relay_escrow_to_payout |  | PROTOCOLE | `5v2gVH3xD6HE5fCuo7bb4zp65466guDNJSvVxiZie6D9b2CBWcAUgurcCp1mtXZrsQ7xAvLnfUYBMDrngtyMZHKq` |

**Transactions vérifiables, sorties :**

| UTC | Chaîne | Actif | Montant | De | Vers | Événement | Service | Preuve | Transaction |
|---|---|---|---|---|---|---|---|---|---|
| 2026-10-27 16:51:53 | polygon | pUSD | 51 509,88 | `0x5f8b30fd…866a` | `0x00000000…0000` | burn_pusd_unwrap |  | CHAINE | `0x650d76f3ef10b8e0001baf61693372fa8634ae29a29ae11f86589c064cf52e16` |
| 2026-10-27 16:51:53 | solana | USDT | 51 489,09 | `0x5f8b30fd…866a` | `DMmDPF9sFc…wt5T` | relay_payout_to_recipient |  | PROTOCOLE | `57XPE63Zvu53geF8C7saiFwDMjeZBimPBsyoD82kM72hPRMFBePmjcgSgz2vCsRmjLLUPe4u8RFTMdaCMzehQvTx` |
| 2026-10-27 16:51:56 | solana | USDT | 51 489,00 | `DMmDPF9sFc…wt5T` | `GxjcMTWWDc…nvBW` | onward_transfer | Unidentified Solana custodial service (cosig | CHAINE+ATTRIBUTION | `2UCgkFYwUKGceXb1VXABUFTUZiNrwUgUh6vDPDr9ae2MN9SEFB8GqLikvoHueeuavaoQ3AQspG72L8fiwd78LQRq` |

### cookedrice

Wallet `0x4060509c8c70cece529be4a089d6d66ad865b4d0`. Clé propriétaire lue sur la chaîne : `0x6ec290051ea167cf564a4282c153351ab3fd876f`. Lien étiquette vers adresse : ALIAS_EXACT_AND_SHARES. 1 dépôts pour 21 873,74 $, 1 retraits pour 39 158,78 $, soit 17 285,05 $ de retraits moins dépôts.

**En bref.** Un seul dépôt depuis KuCoin Hot Wallet 2, par une adresse Solana de passage. Le retrait de 39 158,78 $ part vers une adresse de dépôt du même service dépositaire non identifié que VidenteRibeira. Ce service est mutualisé, ce n'est pas un lien entre les deux comptes.

| Question | Réponse | Niveau |
|---|---|---|
| Origine des financements | 21 873,74 $, par KuCoin Hot Wallet 2 | démontré pour le flux, attribution pour le nom |
| Premier financeur identifiable | `BmFdpraQhk…ymy6` (KuCoin Hot Wallet 2) | attribution |
| Dernier maillon avant dépôt | `BJcZxhXF…JJxFU` (Solana) puis Relay, puis `0xd628c333…5c58` | démontré, protocole |
| Services | KuCoin, Relay, `GxjcMTWW…nvBW` | attribution, protocole, mesure |
| XMR | Absente des données accessibles : même remarque que VidenteRibeira | aucun indice |
| Retraits | 39 158,78 $ devenus 39 158,63 USDC sur `F7ew8r8X…Nh5Eh`, puis 39 158,00 USDC vers `GxjcMTWW…nvBW` | protocole, démontré |
| Où la trace devient incertaine | À l'entrée de `GxjcMTWW…nvBW` | inaccessible |

**Sources de l'argent, par dépôt** (répartition PEPS quand plusieurs entrées se mêlent, convention comptable) :

| Dernière source publique | Chaîne | Service | Catégorie | Dollars alloués | Tx |
|---|---|---|---|---|---|
| `BmFdpraQhk…ymy6` | solana | KuCoin Hot Wallet 2 | exchange | 21 873,74 | 1 |

**Soldes lus le 2 nov.** :

| Adresse du dossier | Chaîne | Solde lu | Lu à (UTC) |
|---|---|---|---|
| `F7ew8r8X5Y…h5Eh` | solana | 0.000891 SOL ; 0.631183 USDC | 2026-11-02 14:02:38 |

**Rapprochement.** Solde pUSD calculé 0.000000, lu 0.000000. Dépôts 1/1 et retraits 1/1 rapprochés de l'API. Frappes hors dépôts : 2, toutes des remboursements (`REDEEM`) : oui. Transferts de positions hors transaction de marché : 0. Mouvements de pUSD absents de l'API : 0.

**Chemins non résolus** :

- Sortie de `GxjcMTWW…nvBW` : 126 destinataires sur 260 transactions tirées dans les 6 h, aucun total proche du montant.

**Confiance et explications alternatives.** Flux : haute. Alternatives : voir VidenteRibeira. Les deux comptes passent par le même service à un jour d'écart : `GxjcMTWW…nvBW` traite environ 90 à 95 transactions par heure sur les fenêtres lues, ce rapprochement n'a pas de valeur de lien.

**Transactions vérifiables, financement :**

| UTC | Chaîne | Actif | Montant | De | Vers | Événement | Service | Preuve | Transaction |
|---|---|---|---|---|---|---|---|---|---|
| 2026-10-14 19:58:12 | solana | USDC | 21 873,74 | `BmFdpraQhk…ymy6` | `BJcZxhXFt2…JxFU` | transfer_in | KuCoin Hot Wallet 2 | CHAINE+ATTRIBUTION | `5dECJvXWiXgqWPoxUQCHEwPvozrArWL5uz6iPGFHHQj4HTBVZFs35iALL34rcgyvxUTUfrvedrzAbB9Fh4kSfjJX` |
| 2026-10-14 19:58:36 | polygon | USDC.e→pUSD | 21 873,74 | `0xd628c333…5c58` | `0x4060509c…b4d0` | wrap_mint_pusd |  | CHAINE | `0x9e1a809440c983f23ae834f92a6214198cfd15b65b4001e5739add05ea733012` |
| 2026-10-14 19:58:36 | solana | USDC | 21 873,74 | `BJcZxhXFt2…JxFU` | `0xd628c333…5c58` | relay_escrow_to_payout |  | PROTOCOLE | `4ZWgBQaKB4G6YAEh7Kn2fk9QPzpJTGsxfDA3XDWjCDZw6g6aFiNLDk9PFg9wSd4Ze9osbwFPgdPfwbKEsde9AkXb` |

**Transactions vérifiables, sorties :**

| UTC | Chaîne | Actif | Montant | De | Vers | Événement | Service | Preuve | Transaction |
|---|---|---|---|---|---|---|---|---|---|
| 2026-10-28 18:04:55 | polygon | pUSD | 39 158,78 | `0x4060509c…b4d0` | `0x00000000…0000` | burn_pusd_unwrap |  | CHAINE | `0x32c1285b13708b90937e6af48e956c07148630916649d021f9047af08767f1ae` |
| 2026-10-28 18:04:55 | solana | USDC | 39 158,63 | `0x4060509c…b4d0` | `F7ew8r8X5Y…h5Eh` | relay_payout_to_recipient |  | PROTOCOLE | `2wgkQdsKcoAKNPmCVt8JuKEXNwHJBvVLWVfXVKCfPkwn4nq69r2S5W1WG36XU3CcKKSETNwkidHcBUcC6unyGWa7` |
| 2026-10-28 18:04:56 | solana | USDC | 39 158,00 | `F7ew8r8X5Y…h5Eh` | `GxjcMTWWDc…nvBW` | onward_transfer | Unidentified Solana custodial service (cosig | CHAINE+ATTRIBUTION | `5jAnEGy7ZFNQCkWBWNXSVwU8K6FqvBLCtPyAA2Ls9NoTa85uj7WLAVdUQPrmkdbHD9mF4i1nfCcbLmd53WhrtVkJ` |

### WenZhuanBuPei

Wallet `0x8832319d9c25df311e37511f0aa5b214abc16500`. Clé propriétaire lue sur la chaîne : `0x6697f72fa32de93d8450830eb07f5b6724104405`. Lien étiquette vers adresse : ALIAS_EXACT_AND_SHARES. 1 dépôts pour 15 926,88 $, 1 retraits pour 27 724,79 $, soit 11 797,91 $ de retraits moins dépôts.

**En bref.** Un dépôt de 15 926,88 $, payé sur Polygon par `0xee7ae85f…4055`, étiqueté Binance: Hot Wallet 34 sur Blockscout, dans une transaction envoyée par une adresse étiquetée Binance dans deux sources. Le retrait va sur Arbitrum, puis vers un intermédiaire à commission de 1,00 %, qui répartit le reste en trois morceaux. Ces trois morceaux sont regroupés 18 h plus tard par une adresse de service à 62 528 transactions.

| Question | Réponse | Niveau |
|---|---|---|
| Origine des financements | 15 926,88 $ depuis `0xee7ae85f…4055` (Binance: Hot Wallet 34), transaction envoyée par `0xe7804c37…e245` (Binance 48, et Binance: Hot Wallet 2 dans une liste de 2023) | démontré pour le flux, attribution pour le nom |
| Premier financeur identifiable | Binance, sur le payeur et sur l'expéditeur de la transaction | attribution |
| Dernier maillon avant dépôt | `0x315ac6e7…14c5` (adresse de pont), Relay | démontré, protocole |
| Services | Binance, Relay, `0x3ab2206b…7d50` (intermédiaire), `0x51cf2d9f…4999` (service) | protocole, attribution, mesure |
| XMR | Absente des données accessibles : l'intermédiaire à 1 % est non identifié, aucun indice de conversion | aucun indice |
| Retraits | 27 724,79 $ vers `0xe820ecb3…87cd` (Arbitrum), 27 724,00 USDC vers `0x3ab2206b…7d50` | protocole, démontré |
| Où la trace devient incertaine | À `0x51cf2d9f…4999`, qui reçoit 3 037 expéditeurs et paie 1 630 destinataires | inaccessible |

**Sources de l'argent, par dépôt** (répartition PEPS quand plusieurs entrées se mêlent, convention comptable) :

| Dernière source publique | Chaîne | Service | Catégorie | Dollars alloués | Tx |
|---|---|---|---|---|---|
| `0xee7ae85f…4055` | polygon | Binance: Hot Wallet 34 | exchange | 15 926,88 | 1 |

**Soldes lus le 2 nov.** :

| Adresse du dossier | Chaîne | Solde lu | Lu à (UTC) |
|---|---|---|---|
| `0xe820ecb3…87cd` | arbitrum | 0.000001 ETH ; 0.789808 USDC | 2026-11-02 14:02:38 |

**Rapprochement.** Solde pUSD calculé 0.000000, lu 0.000000. Dépôts 1/1 et retraits 1/1 rapprochés de l'API. Frappes hors dépôts : 1, toutes des remboursements (`REDEEM`) : oui. Transferts de positions hors transaction de marché : 0. Mouvements de pUSD absents de l'API : 0.

**Chemins non résolus** :

- Après `0x51cf2d9f…4999` : le service mêle ses clients, et son historique lu est tronqué au milieu. Il faudrait son registre.

**Confiance et explications alternatives.** Flux : haute jusqu'à `0x51cf2d9f…4999`, y compris les trois morceaux regroupés dans une seule transaction (`0x6ef3a7e7…1547`), ce qui prouve un contrôle commun de ces trois adresses par le service. Le mot « commission » décrit une mesure, pas un contrat : 277,24 USDC vont à `0x435e3931…dd1d` dans la seconde qui suit, exactement 1,00 %. Alternatives : gestionnaire de paiement, courtier de gré à gré, service de sortie de fonds. Aucune étiquette.

**Transactions vérifiables, financement :**

| UTC | Chaîne | Actif | Montant | De | Vers | Événement | Service | Preuve | Transaction |
|---|---|---|---|---|---|---|---|---|---|
| 2026-10-18 20:14:03 | polygon | USDC | 15 926,88 | `0xee7ae85f…4055` | `0x315ac6e7…14c5` | transfer_into_bridge_address | Binance: Hot Wallet 34 | CHAINE+ATTRIBUTION | `0x2c0d0943a7874d99abbc28c4d4930407c8eaad006df45655f6e3ad0c2b808db3` |
| 2026-10-18 20:14:27 | polygon | USDC.e→pUSD | 15 926,88 | `0x315ac6e7…14c5` | `0x8832319d…6500` | wrap_mint_pusd |  | CHAINE | `0x45c27719b34b5490a620b319911db190d6570bc1b0e2da3782d5bbb8c4cc2da3` |
| 2026-10-18 20:14:27 | polygon | USDC | 15 926,88 | `0x315ac6e7…14c5` | `0x315ac6e7…14c5` | relay_bridge_deposit_address |  | PROTOCOLE | `0xbe1b3982deaba664c64bfa8f6568f3512e7a2a798d41d888f947d78b43e6d622` |

**Transactions vérifiables, sorties :**

| UTC | Chaîne | Actif | Montant | De | Vers | Événement | Service | Preuve | Transaction |
|---|---|---|---|---|---|---|---|---|---|
| 2026-10-27 22:58:06 | polygon | pUSD | 27 724,79 | `0x8832319d…6500` | `0x00000000…0000` | burn_pusd_unwrap |  | CHAINE | `0x094f60bf5bf3a015903748b150b621bfeb115dcccf5d81d35bd688d5cdbe9b91` |
| 2026-10-27 22:58:06 | arbitrum | USDC | 27 724,79 | `0x8832319d…6500` | `0xe820ecb3…87cd` | relay_payout_to_recipient |  | PROTOCOLE | `0x521dbd22f8e00ba8ac55737e2a3479c76ea1162984b97815b4ea4c53a4f8595c` |
| 2026-10-27 22:58:10 | arbitrum | USDC | 27 724,00 | `0xe820ecb3…87cd` | `0x3ab2206b…7d50` | onward_transfer |  | CHAINE | `0xa06fecae758b361f2acf0c2198c5f399c89326806e0906d58561c6eb338640da` |

### 0x86544e4dfde

Wallet `0x3ed2c452f141c291adecb97ddfc72b1650acff3d`. Clé propriétaire lue sur la chaîne : `0x69837228fa0bcbac53713d981161c929523c0ded`. Lien étiquette vers adresse : SHARES_ONLY. 4 dépôts pour 44 847,24 $, 1 retraits pour 74 198,32 $, soit 29 351,08 $ de retraits moins dépôts.

**En bref.** Plus gros compte du groupe : 44 847,24 $ déposés en 4 fois. Trois dépôts viennent d'un compte intelligent Circle d'un service dépositaire non attribué, sur Polygon. Le quatrième vient d'un vieux portefeuille personnel, `0x408ce42a…c5b3`, alimenté de 2023 à 2024 par Kraken et Binance. Les 74 198,32 $ retirés sont intacts sur la clé, qui n'a jamais signé une seule transaction sur Ethereum.

| Question | Réponse | Niveau |
|---|---|---|
| Origine des financements | 42 389,48 $ par `0x0ce9bdf3…f06d`, 2 457,76 $ par `0x408ce42a…c5b3` | démontré pour les flux |
| Premier financeur identifiable | Service non attribué `0x0ce9bdf3…f06d`. Pour la branche `0x408ce42a…c5b3` : Kraken 4 et Binance 14, 15 et 18, de 2023 à 2024 | mesure ; attribution |
| Dernier maillon avant dépôt | Clé `0x69837228…0ded` et `0x99a5baa3…22be` (adresse de pont), Relay | démontré, protocole |
| Services | Service Circle non attribué, Relay, Polygon PoS, MetaMask, UniswapX ; Kraken et Binance dans l'historique de `0x408ce42a…c5b3` | mesure, protocole, attribution |
| XMR | Absente des données accessibles | aucun indice |
| Retraits | 74 198,32 $ vers la clé sur Ethereum | protocole |
| Où la trace devient incertaine | En amont de `0x0ce9bdf3…f06d`, et rien en aval : 74 198,32 USDC encore en place | inaccessible |

**Sources de l'argent, par dépôt** (répartition PEPS quand plusieurs entrées se mêlent, convention comptable) :

| Dernière source publique | Chaîne | Service | Catégorie | Dollars alloués | Tx |
|---|---|---|---|---|---|
| `0x0ce9bdf3…f06d` | polygon | Circle SingleOwnerMSCA account of an unattributed custodial service | custodial_unattributed | 42 389,52 | 3 |
| — | polygon | Échange fait par l'adresse elle-même (voir le récit) | dex_or_router | 2 457,76 | 1 |

**Soldes lus le 2 nov.** :

| Adresse du dossier | Chaîne | Solde lu | Lu à (UTC) |
|---|---|---|---|
| `0x69837228…0ded` | ethereum | 74 198.317716 USDC | 2026-11-02 14:02:38 |
| `0x69837228…0ded` | polygon | 0.969341 USDC | 2026-11-02 14:02:38 |

**Rapprochement.** Solde pUSD calculé 0.000000, lu 0.000000. Dépôts 4/4 et retraits 1/1 rapprochés de l'API. Frappes hors dépôts : 9, toutes des remboursements (`REDEEM`) : oui. Transferts de positions hors transaction de marché : 0. Mouvements de pUSD absents de l'API : 0.

**Chemins non résolus** :

- Le service derrière `0x0ce9bdf3…f06d` : 1 001 destinataires sur 2 000 lignes en 84 h, expéditeur `0x0853ea40…4d0b` (nonce 407 684) sans étiquette.

**Confiance et explications alternatives.** Flux : haute. `0x408ce42a…c5b3` n'a envoyé que 2 457,76 $ : le lien entre lui et le titulaire de la clé reste une hypothèse. Alternatives : un proche ou un autre compte du même titulaire. Le compte a touché 15,86 $ de primes de parrainage, ce qui explique son résidu.

**Transactions vérifiables, financement :**

| UTC | Chaîne | Actif | Montant | De | Vers | Événement | Service | Preuve | Transaction |
|---|---|---|---|---|---|---|---|---|---|
| 2026-10-09 15:40:00 | polygon | USDC | 15 000,00 | `0x0ce9bdf3…f06d` | `0x69837228…0ded` | transfer_in | Circle SingleOwnerMSCA account of an unattri | CHAINE+ATTRIBUTION | `0x76465038ac8cd628232731259c2544ff4d6b2c61af02619e1be0a97b33b2e13b` |
| 2026-10-09 18:06:01 | polygon | USDC.e→pUSD | 14 999,00 | `0xc8a6871d…8d64` | `0x3ed2c452…ff3d` | wrap_mint_pusd | VaultDepositooor (fun.xyz deposit passage co | CHAINE | `0x40f84e77821ecf20773964ead4dba8868267f8efcb9f9d134d50c3a27dcc2f1e` |
| 2026-10-09 18:06:01 | polygon | USDC | 14 999,00 | `0x69837228…0ded` | `0xc8a6871d…8d64` | relay_escrow_to_payout | VaultDepositooor (fun.xyz deposit passage co | PROTOCOLE | `0xba5a0a5905f753ed509069527670eef0fb8b2bfdc3a27b569f3476ba4df8ab40` |
| 2026-10-09 18:49:22 | polygon | USDC | 25 686,12 | `0x0ce9bdf3…f06d` | `0x69837228…0ded` | transfer_in | Circle SingleOwnerMSCA account of an unattri | CHAINE+ATTRIBUTION | `0x83ed04db9fba270f025fd0f75f7a115253240a42bda33f17ccf4537bd5a738d9` |
| 2026-10-10 19:45:00 | polygon | USDC.e→pUSD | 25 686,09 | `0xc8a6871d…8d64` | `0x3ed2c452…ff3d` | wrap_mint_pusd | VaultDepositooor (fun.xyz deposit passage co | CHAINE | `0x3e36a0beb3147013446714e1a2eca952d09627c4177d582ab815e80660b4ef1d` |
| 2026-10-10 19:45:00 | polygon | USDC | 25 686,09 | `0x69837228…0ded` | `0xc8a6871d…8d64` | relay_escrow_to_payout | VaultDepositooor (fun.xyz deposit passage co | PROTOCOLE | `0x652561de9eb87689c9e52bb149cea2a8839104494841f2102ff110a1363a87cb` |
| 2026-10-13 17:38:28 | polygon | USDC | 1 704,42 | `0x0ce9bdf3…f06d` | `0x69837228…0ded` | transfer_in | Circle SingleOwnerMSCA account of an unattri | CHAINE+ATTRIBUTION | `0x4b07b47c57150828753d172e89df4f629bad4faecdec9f926b2742d6868c1bdc` |
| 2026-10-13 17:39:42 | polygon | USDC.e→pUSD | 1 704,39 | `0xc8a6871d…8d64` | `0x3ed2c452…ff3d` | wrap_mint_pusd | VaultDepositooor (fun.xyz deposit passage co | CHAINE | `0x3515f48f31ca27c67c690e0743e674b8ce03d8cbff5011b3ce71e56e5560eb17` |
| 2026-10-13 17:39:42 | polygon | USDC | 1 704,39 | `0x69837228…0ded` | `0xc8a6871d…8d64` | relay_escrow_to_payout | VaultDepositooor (fun.xyz deposit passage co | PROTOCOLE | `0xa3ccb569d79223afe7f0312bbbffa78a1c5be7abda10f771b7035c9fad0cc13b` |
| 2026-10-16 20:04:29 | polygon | USDC | 2 463,37 | `0xc590175e…c02b` | `0x408ce42a…c5b3` | return_of_own_swap | Swap contract used through MetaMask delegati | CHAINE | `0x6596b08f24090f8977c82e72fa7dab4db71343a3a30f57ec70b0918ef3f739f4` |
| 2026-10-17 21:09:21 | polygon | USDC | 2 457,76 | `0x408ce42a…c5b3` | `0x99a5baa3…22be` | transfer_into_bridge_address |  | CHAINE | `0x3efc385da95f96a3a86f06462ef651a4a89f3082086697fc4229c1913fea83f3` |
| 2026-10-17 21:09:47 | polygon | USDC.e→pUSD | 2 457,76 | `0x99a5baa3…22be` | `0x3ed2c452…ff3d` | wrap_mint_pusd |  | CHAINE | `0x8579f8fba65448840888623b49218adb9fbb0a39ef7821a997fb1ce6fd5243cf` |
| 2026-10-17 21:09:47 | polygon | USDC | 2 457,76 | `0x99a5baa3…22be` | `0x99a5baa3…22be` | relay_bridge_deposit_address |  | PROTOCOLE | `0x5d7a73815f6e2279baddc87f5b7591ce3716ccab7973822f34319f76b539784c` |

**Transactions vérifiables, sorties :**

| UTC | Chaîne | Actif | Montant | De | Vers | Événement | Service | Preuve | Transaction |
|---|---|---|---|---|---|---|---|---|---|
| 2026-10-27 01:59:51 | polygon | pUSD | 74 198,32 | `0x3ed2c452…ff3d` | `0x00000000…0000` | burn_pusd_unwrap |  | CHAINE | `0x592333616322f0718366c916984050edd5b23d8ce108c62f4aaecb62cfe03b83` |
| 2026-10-27 01:59:51 | ethereum | USDC | 74 198,32 | `0x3ed2c452…ff3d` | `0x69837228…0ded` | relay_payout_to_recipient |  | PROTOCOLE | `0xf157abfd294420ba1d35bf08a5c8725bb74a87437454fea3ead8da50dbeabb05` |

### brace227

Wallet `0x873848cd27784900e193611845fc3fd2c4716d03`. Clé propriétaire lue sur la chaîne : `0xc852b0938f5ad79b640d105ed11c14499454af26`. Lien étiquette vers adresse : ALIAS_EXACT_AND_SHARES. 8 dépôts pour 10 032,98 $, 4 retraits pour 22 036,76 $, soit 12 003,77 $ de retraits moins dépôts.

**En bref.** La clé reçoit 15 096,29 $ de SwftSwap, service d'échange instantané, et en partage la moitié avec une autre clé, `0x48ec106c…b12d`, qui possède un **autre wallet Polymarket**. Ce wallet n'a acheté que du Kane Oui. C'est le seul compte supplémentaire relié aux onze par la chaîne, et le fait le plus discriminant de cette enquête. La clé envoie aussi 0,00205 ETH à la clé de kraben006. Ses retraits restent sur la clé : 22 024,57 USDC.

| Question | Réponse | Niveau |
|---|---|---|
| Origine des financements | SwftSwap 15 096,29 $ en 4 versements du 9 au 16 oct., BloFin (Hot Wallet 1) 110,20 $. Gaz : `7XUJsJBN…JfrZc` (Solana) par Relay | démontré, attribution pour les noms |
| Premier financeur identifiable | SwftSwap pour la période des paris. Plus ancien : KuCoin 10 et Binance 20 en mars 2022. `0x3eaef6d5…`, financé entièrement par ChangeNOW (Hot Wallet 3 et 4), envoie 291,32 USDT en janv. 2025 | attribution |
| Dernier maillon avant dépôt | La clé `0xc852b093…af26`, Relay, `0xc8a6871d…8d64` | démontré, protocole |
| Services | SwftSwap, BloFin, Relay, THORChain (7 USDC), NEAR Intents (5 USDC contre du gaz), MetaMask ; ChangeNOW fin 2024 sur un financeur ancien | nom vérifié, attribution, protocole |
| XMR | Absente des données accessibles : SwftSwap ne liste pas XMR à la lecture ; ChangeNOW le liste, et finance fin 2024 l'adresse qui envoie 291,32 USDT à la clé : simple compatibilité, 21 mois avant les paris | aucun indice |
| Retraits | 22 036,76 $ vers la clé. 22 024,57 USDC y restent | protocole |
| Où la trace devient incertaine | Derrière SwftSwap : l'actif d'origine et le client de chaque ordre ne sont pas publics | inaccessible |

**Sources de l'argent, par dépôt** (répartition PEPS quand plusieurs entrées se mêlent, convention comptable) :

| Dernière source publique | Chaîne | Service | Catégorie | Dollars alloués | Tx |
|---|---|---|---|---|---|
| `0xc1d13492…a1b5` | ethereum | SwftSwap (SWFT Blockchain) | instant_exchange | 9 922,28 | 4 |
| `0x7ff8bbf9…cce5` | ethereum | BloFin: Hot Wallet 1 | exchange | 109,18 | 1 |
| `0xd37bbe57…7146` | ethereum | THORChain: THORChain Router v4.1.1 | bridge | 1,53 | 1 |

**Soldes lus le 2 nov.** :

| Adresse du dossier | Chaîne | Solde lu | Lu à (UTC) |
|---|---|---|---|
| `0x2c791cb8…118a` | ethereum | 0.000001 ETH | 2026-11-02 14:02:38 |
| `0xc852b093…af26` | ethereum | 0.001933 ETH ; 22 024.568917 USDC ; 0.021283 USDT | 2026-11-02 14:02:38 |
| `0xc852b093…af26` | bsc | 0.001631 BNB | 2026-11-02 14:02:38 |
| `0xcde23098…d1f1` | ethereum | 0.000014 ETH | 2026-11-02 14:02:38 |

**Rapprochement.** Solde pUSD calculé 3.390600, lu 3.390600. Dépôts 8/8 et retraits 4/4 rapprochés de l'API. Frappes hors dépôts : 0, toutes des remboursements (`REDEEM`) : oui. Transferts de positions hors transaction de marché : 0. Mouvements de pUSD absents de l'API : 0.

**Chemins non résolus** :

- Origine des 15 096,29 $ : SwftSwap paie par `withdraw` depuis son contrat. Sa route d'état d'ordre exige un identifiant d'ordre que la chaîne ne donne pas.
- BSC : 109 transactions signées, 104 avant le 30 juil. 2022 et non énumérées une à une, 5 lues : la dernière date du 17 mai 2025. Entrées BSC non lues.

**Confiance et explications alternatives.** Le partage et le second wallet : haute, voir `COMMON_FUNDERS.md`. Ils démontrent un lien financier, pas un propriétaire commun : don, prêt, ou ami à qui on avance les fonds restent possibles. Rien sur une information privilégiée.

**Transactions vérifiables, financement :**

| UTC | Chaîne | Actif | Montant | De | Vers | Événement | Service | Preuve | Transaction |
|---|---|---|---|---|---|---|---|---|---|
| 2026-10-09 20:03:47 | ethereum | USDC | 4 337,52 | `0xc1d13492…a1b5` | `0xc852b093…af26` | transfer_in | SwftSwap (SWFT Blockchain) | CHAINE+ATTRIBUTION | `0xead283d89c81ad82e63d7186d7b52a5d4279fe11bd3352fa0430d01b7f472f3f` |
| 2026-10-09 20:06:35 | ethereum | USDC | 83,89 | `0xc1d13492…a1b5` | `0xc852b093…af26` | transfer_in | SwftSwap (SWFT Blockchain) | CHAINE+ATTRIBUTION | `0xb193c0e941ce513b1e78d15b6bd337ac1e94013a20a54799146d10afb16fbdbe` |
| 2026-10-09 20:49:05 | polygon | USDC.e→pUSD | 2 186,43 | `0xc8a6871d…8d64` | `0x873848cd…6d03` | wrap_mint_pusd | VaultDepositooor (fun.xyz deposit passage co | CHAINE | `0x2a89597ebf1d83b5b76ceccab02924c28ca0ad8f6d208b2c42801a0925280a2c` |
| 2026-10-09 20:49:05 | ethereum | USDC | 2 186,43 | `0xc852b093…af26` | `0xc8a6871d…8d64` | relay_escrow_to_payout | VaultDepositooor (fun.xyz deposit passage co | PROTOCOLE | `0xdade897786d0929dcaf4c0c93513178069d81b0b946f17c375355a39079a9cf8` |
| 2026-10-10 00:26:47 | ethereum | USDC | 5 925,84 | `0xc1d13492…a1b5` | `0xc852b093…af26` | transfer_in | SwftSwap (SWFT Blockchain) | CHAINE+ATTRIBUTION | `0x492e2f055c2744be7eac558536cf6076c0b2baff84d0bc7b18f59704ad4e8d21` |
| 2026-10-10 03:08:27 | polygon | USDC.e→pUSD | 1 000,00 | `0xc8a6871d…8d64` | `0x873848cd…6d03` | wrap_mint_pusd | VaultDepositooor (fun.xyz deposit passage co | CHAINE | `0x0b8b69e72185664feeab3d997c16c72367c610d66788ea865d9fa0a64cbcc152` |
| 2026-10-10 03:08:27 | ethereum | USDC | 1 000,00 | `0xc852b093…af26` | `0xc8a6871d…8d64` | relay_escrow_to_payout | VaultDepositooor (fun.xyz deposit passage co | PROTOCOLE | `0xf7e421ed21a1d55912d3b138a32e83f5ddf1e0984817bac04f7960077e0c2945` |
| 2026-10-10 12:39:27 | polygon | USDC.e→pUSD | 993,41 | `0xc8a6871d…8d64` | `0x873848cd…6d03` | wrap_mint_pusd | VaultDepositooor (fun.xyz deposit passage co | CHAINE | `0x304530cd01ccb84aef9f7ffe48c218f15e3fcc5ff3842a1b10834db9f367370a` |
| 2026-10-10 12:39:27 | ethereum | USDC | 993,41 | `0xc852b093…af26` | `0xc8a6871d…8d64` | relay_escrow_to_payout | VaultDepositooor (fun.xyz deposit passage co | PROTOCOLE | `0xbe018c5d4e3ca833edaa672217de0ef73becafbac63fdbe63a9476c355bf758d` |
| 2026-10-10 14:40:51 | polygon | USDC.e→pUSD | 993,41 | `0xc8a6871d…8d64` | `0x873848cd…6d03` | wrap_mint_pusd | VaultDepositooor (fun.xyz deposit passage co | CHAINE | `0x7709ecb84b93e3a1deac094a05211d27df6c2248325cf22c8fbf5ef7d7a98f2b` |
| 2026-10-10 14:40:51 | ethereum | USDC | 993,41 | `0xc852b093…af26` | `0xc8a6871d…8d64` | relay_escrow_to_payout | VaultDepositooor (fun.xyz deposit passage co | PROTOCOLE | `0xa88f067d70cb26c18e13159c6ed82645ba1160ef7dbf857ec468952cb4e84a66` |
| 2026-10-12 18:45:59 | ethereum | USDT | 6,71 | `0xd37bbe57…7146` | `0xc852b093…af26` | transfer_in | THORChain: THORChain Router v4.1.1 | CHAINE+ATTRIBUTION | `0xfd1f2912b28873463db1c46178c684ea3018b20a24d0b8e923ea43f8eaa9ef89` |
| 2026-10-16 19:16:35 | ethereum | USDC | 4 749,03 | `0xc1d13492…a1b5` | `0xc852b093…af26` | transfer_in | SwftSwap (SWFT Blockchain) | CHAINE+ATTRIBUTION | `0xb67d5b6a2b46c6c50cc585c05e402247e359bad32146fb4d5219be65c1ae783d` |
| 2026-10-16 19:22:14 | polygon | USDC.e→pUSD | 1 000,00 | `0xc8a6871d…8d64` | `0x873848cd…6d03` | wrap_mint_pusd | VaultDepositooor (fun.xyz deposit passage co | CHAINE | `0xda28969d7733181d80caf5a0cdad60f099bf392514d0f5dc302f916f800b432d` |
| 2026-10-16 19:22:14 | ethereum | USDC | 1 000,00 | `0xc852b093…af26` | `0xc8a6871d…8d64` | relay_escrow_to_payout | VaultDepositooor (fun.xyz deposit passage co | PROTOCOLE | `0x638d4d0caa162a09618f4a98e1d0e26f7a24a34286948f777c19e45f7c472c34` |
| 2026-10-16 19:25:53 | polygon | USDC.e→pUSD | 1 900,00 | `0xc8a6871d…8d64` | `0x873848cd…6d03` | wrap_mint_pusd | VaultDepositooor (fun.xyz deposit passage co | CHAINE | `0x897023041c721497b60b56f6ef9ed5aa4ecb29a48b2741f93660b5041f7fcd7d` |
| 2026-10-16 19:25:53 | ethereum | USDC | 1 900,00 | `0xc852b093…af26` | `0xc8a6871d…8d64` | relay_escrow_to_payout | VaultDepositooor (fun.xyz deposit passage co | PROTOCOLE | `0xe18b970e5eb357c5ad2b4d5427373a661a8a8c5b6752ebb194f9dadc43e00c95` |
| 2026-10-16 21:28:27 | polygon | USDC.e→pUSD | 1 849,54 | `0xc8a6871d…8d64` | `0x873848cd…6d03` | wrap_mint_pusd | VaultDepositooor (fun.xyz deposit passage co | CHAINE | `0x38c1409f7aa3df420cc76de6b8f17649f7ad0dd2584eb673322790816ea9763a` |
| 2026-10-16 21:28:27 | ethereum | USDC | 1 849,54 | `0xc852b093…af26` | `0xc8a6871d…8d64` | relay_escrow_to_payout | VaultDepositooor (fun.xyz deposit passage co | PROTOCOLE | `0x96f21bc7fbb641dfe8d197e9abdb09058991b382b93d1a658a68ca2b6f870ec2` |
| 2026-10-20 16:44:11 | ethereum | USDC | 110,20 | `0x7ff8bbf9…cce5` | `0xc852b093…af26` | transfer_in | BloFin: Hot Wallet 1 | CHAINE+ATTRIBUTION | `0xebbc699a370b7796c6e13e52da28cbea08541b03e79551b30ed70a8b0002edd3` |
| 2026-10-20 17:20:53 | polygon | USDC.e→pUSD | 110,20 | `0xc8a6871d…8d64` | `0x873848cd…6d03` | wrap_mint_pusd | VaultDepositooor (fun.xyz deposit passage co | CHAINE | `0x061bec572955f3bcc16d129b8a39fc0ff21b364a49f26466045bf9379023f28b` |
| 2026-10-20 17:20:53 | ethereum | USDC | 110,20 | `0xc852b093…af26` | `0xc8a6871d…8d64` | relay_escrow_to_payout | VaultDepositooor (fun.xyz deposit passage co | PROTOCOLE | `0x8858ec044be85495794267d398c7b5adb0814a680c6b4991aadb18151d8183d8` |

**Transactions vérifiables, sorties :**

| UTC | Chaîne | Actif | Montant | De | Vers | Événement | Service | Preuve | Transaction |
|---|---|---|---|---|---|---|---|---|---|
| 2026-10-11 13:25:33 | polygon | pUSD | 13,19 | `0x873848cd…6d03` | `0x00000000…0000` | burn_pusd_unwrap |  | CHAINE | `0x93518e172a0daf71fa8610c411e0ec5b7e208773424a2898e889e39e0816c946` |
| 2026-10-11 13:25:33 | ethereum | USDC | 13,19 | `0x873848cd…6d03` | `0xc852b093…af26` | relay_payout_to_recipient |  | PROTOCOLE | `0x1f3bb89154029ee54984e44d8650fe88b2dddd22051aeb97c942ca31525454bf` |
| 2026-10-12 18:45:11 | ethereum | USDC | 7,00 | `0xc852b093…af26` | `0xd37bbe57…7146` | onward_transfer | THORChain: THORChain Router v4.1.1 | CHAINE+ATTRIBUTION | `0xac47d8f901b76bad8b1aa370945a8ac16039c3e57e538d48c7b72d5f10719951` |
| 2026-10-12 18:47:47 | ethereum | USDT | 6,69 | `0xc852b093…af26` | `0x2c791cb8…118a` | onward_transfer |  | CHAINE | `0xa6497b227fb39257f0107ad44d860182a585f9e860ca4e7725acc368da4867df` |
| 2026-10-16 19:20:11 | ethereum | USDC | 5,00 | `0xc852b093…af26` | `0xcde23098…d1f1` | onward_transfer |  | CHAINE | `0x1acaf51467d0686487dffacdb213edd1e4212105084fedce06ba9716ab953998` |
| 2026-10-16 19:22:11 | ethereum | USDC | 1 000,00 | `0xc852b093…af26` | `0x4cd00e38…bc31` | onward_relay_deposit | Relay Depository | CHAINE | `0x638d4d0caa162a09618f4a98e1d0e26f7a24a34286948f777c19e45f7c472c34` |
| 2026-10-16 19:25:47 | ethereum | USDC | 1 900,00 | `0xc852b093…af26` | `0x4cd00e38…bc31` | onward_relay_deposit | Relay Depository | CHAINE | `0xe18b970e5eb357c5ad2b4d5427373a661a8a8c5b6752ebb194f9dadc43e00c95` |
| 2026-10-16 21:28:23 | ethereum | USDC | 1 849,54 | `0xc852b093…af26` | `0x4cd00e38…bc31` | onward_relay_deposit | Relay Depository | CHAINE | `0x96f21bc7fbb641dfe8d197e9abdb09058991b382b93d1a658a68ca2b6f870ec2` |
| 2026-10-20 17:20:47 | ethereum | USDC | 110,20 | `0xc852b093…af26` | `0x4cd00e38…bc31` | onward_relay_deposit | Relay Depository | CHAINE | `0x8858ec044be85495794267d398c7b5adb0814a680c6b4991aadb18151d8183d8` |
| 2026-10-26 23:13:03 | polygon | pUSD | 19 842,33 | `0x873848cd…6d03` | `0x00000000…0000` | burn_pusd_unwrap |  | CHAINE | `0x6391df5cd4c4d177988c8473ac1b17fdd26569cc78e34c646306e11b3ce950fc` |
| 2026-10-26 23:13:03 | ethereum | USDC | 19 842,33 | `0x873848cd…6d03` | `0xc852b093…af26` | relay_payout_to_recipient |  | PROTOCOLE | `0x8669118e08e63b629ff54d78c9301ae1aa94f1d21b10d67d0c6a20837ff19a2c` |
| 2026-10-26 23:15:36 | polygon | pUSD | 2 175,73 | `0x873848cd…6d03` | `0x00000000…0000` | burn_pusd_unwrap |  | CHAINE | `0x770f97d1b820295c9045b520eb64175dbe32a0b9b4065f866634596cd027333e` |
| 2026-10-26 23:15:36 | ethereum | USDC | 2 175,73 | `0x873848cd…6d03` | `0xc852b093…af26` | relay_payout_to_recipient |  | PROTOCOLE | `0x78603ab216c7da4b00394583d28fd6cc918b428b6af11b9bf02a1b02d447eaf6` |
| 2026-10-27 00:14:00 | polygon | pUSD | 5,50 | `0x873848cd…6d03` | `0x00000000…0000` | burn_pusd_unwrap |  | CHAINE | `0x5575675d19ecd30f1cfce70f1d80adbb0e481b7a84c5ac2b718d3d651882732e` |
| 2026-10-27 00:14:00 | ethereum | USDC | 5,50 | `0x873848cd…6d03` | `0xc852b093…af26` | relay_payout_to_recipient |  | PROTOCOLE | `0x40bc8e9a05ac22b66cbf418e8b85ad1928c421656aa864c634985c7cabec5fef` |

### walletwallet8424

Wallet `0x1a1ef4c65583d5c71011d7fe51e9f544e2b1cc40`. Clé propriétaire lue sur la chaîne : `0x82775eb82fe33acffdf1b91a28c0fc19b4b6a3a1`. Lien étiquette vers adresse : ALIAS_EXACT_AND_SHARES. 3 dépôts pour 22 088,68 $, 1 retraits pour 35 546,89 $, soit 13 458,21 $ de retraits moins dépôts.

**En bref.** Trois dépôts. Deux viennent du même service Circle non attribué que 0x86544e4dfde. Le gros, 16 508,26 $, suit un chemin long mais démontré : 16 808,96 USDC d'une adresse très active, échangés en 6,63 ETH, passés sur Polygon par le pont officiel, puis ré-échangés en USDC. Les 35 546,89 $ retirés sont intacts sur la clé.

| Question | Réponse | Niveau |
|---|---|---|
| Origine des financements | `0xcc0f311e…23f7` 16 808,96 USDC ; `0x0ce9bdf3…f06d` 1 674,43 et 3 907,03 USDC | démontré pour les flux |
| Premier financeur identifiable | `0xcc0f311e…23f7`, sans étiquette, 672 contreparties, et parmi ses entrées Stake.com et CoinsPaid | mesure |
| Dernier maillon avant dépôt | La clé `0x82775eb8…a3a1`, Relay, `0xc8a6871d…8d64` | démontré, protocole |
| Services | Service Circle non attribué, MetaMask (échange et gaz), pont Polygon PoS, `0xc590175e…c02b`, Relay | mesure, attribution, protocole |
| XMR | Absente des données accessibles | aucun indice |
| Retraits | 35 546,89 $ vers la clé sur Ethereum | protocole |
| Où la trace devient incertaine | En amont de `0xcc0f311e…23f7`. Rien en aval : les fonds sont en place | inaccessible |

**Sources de l'argent, par dépôt** (répartition PEPS quand plusieurs entrées se mêlent, convention comptable) :

| Dernière source publique | Chaîne | Service | Catégorie | Dollars alloués | Tx |
|---|---|---|---|---|---|
| — | polygon | Échange fait par l'adresse elle-même (voir le récit) | dex_or_router | 16 508,27 | 1 |
| `0x0ce9bdf3…f06d` | polygon | Circle SingleOwnerMSCA account of an unattributed custodial service | custodial_unattributed | 5 580,45 | 2 |

**Soldes lus le 2 nov.** :

| Adresse du dossier | Chaîne | Solde lu | Lu à (UTC) |
|---|---|---|---|
| `0x82775eb8…a3a1` | ethereum | 0.000694 ETH ; 35 546.886550 USDC | 2026-11-02 14:02:38 |
| `0x82775eb8…a3a1` | polygon | 0.983929 USDC | 2026-11-02 14:02:38 |

**Rapprochement.** Solde pUSD calculé 0.000000, lu 0.000000. Dépôts 3/3 et retraits 1/1 rapprochés de l'API. Frappes hors dépôts : 2, toutes des remboursements (`REDEEM`) : oui. Transferts de positions hors transaction de marché : 0. Mouvements de pUSD absents de l'API : 0.

**Chemins non résolus** :

- `0xcc0f311e…23f7` : 672 contreparties, historique lu aux deux bouts seulement. Aucune entrée d'au moins 1 USDC dans les 36 h autour du paiement, sur les lignes lues : il paie sur son stock.

**Confiance et explications alternatives.** Flux : haute. Le passage en ETH puis retour en USDC ressemble à un chemin choisi par l'interface MetaMask, rien n'indique une volonté de brouiller. Alternatives pour `0xcc0f311e…23f7` : gré à gré, paiement, salaire, gain de jeu.

**Transactions vérifiables, financement :**

| UTC | Chaîne | Actif | Montant | De | Vers | Événement | Service | Preuve | Transaction |
|---|---|---|---|---|---|---|---|---|---|
| 2026-10-10 13:12:00 | polygon | USDC | 1 674,43 | `0x0ce9bdf3…f06d` | `0x82775eb8…a3a1` | transfer_in | Circle SingleOwnerMSCA account of an unattri | CHAINE+ATTRIBUTION | `0x1e19e0ae34d250fac1b26db226a98a6c06d41859245ccdaa1ba2dbc8041c319d` |
| 2026-10-10 13:19:01 | polygon | USDC.e→pUSD | 1 673,43 | `0xc8a6871d…8d64` | `0x1a1ef4c6…cc40` | wrap_mint_pusd | VaultDepositooor (fun.xyz deposit passage co | CHAINE | `0x71250186b46bcded0deb878fae935386f67adeb43ed59c64a6d1614d291594f4` |
| 2026-10-10 13:19:01 | polygon | USDC | 1 673,43 | `0x82775eb8…a3a1` | `0xc8a6871d…8d64` | relay_escrow_to_payout | VaultDepositooor (fun.xyz deposit passage co | PROTOCOLE | `0xa63cf849db8399ff7d626dadcc460e013665907cf6ae6f4c81fab577f9c17c17` |
| 2026-10-10 19:32:48 | polygon | USDC | 16 508,29 | `0xc590175e…c02b` | `0x82775eb8…a3a1` | return_of_own_swap | Swap contract used through MetaMask delegati | CHAINE | `0x0adf897130e4317e7cfc06fd08c4a6cb9b26b4810611fa8037f532930f9b261d` |
| 2026-10-10 19:36:46 | polygon | USDC.e→pUSD | 16 508,26 | `0xc8a6871d…8d64` | `0x1a1ef4c6…cc40` | wrap_mint_pusd | VaultDepositooor (fun.xyz deposit passage co | CHAINE | `0x65313863d1c3e0ba9f96429e0169954219efa83ab4cf9e90d5b5f8d4b7cb3352` |
| 2026-10-10 19:36:46 | polygon | USDC | 16 508,26 | `0x82775eb8…a3a1` | `0xc8a6871d…8d64` | relay_escrow_to_payout | VaultDepositooor (fun.xyz deposit passage co | PROTOCOLE | `0x9fdf811640b09f2acf1393e380f5036c90d4dc242508a37ecb3fb7d381761b9c` |
| 2026-10-13 14:02:58 | polygon | USDC | 3 907,03 | `0x0ce9bdf3…f06d` | `0x82775eb8…a3a1` | transfer_in | Circle SingleOwnerMSCA account of an unattri | CHAINE+ATTRIBUTION | `0x3e00f4baa2ac4456738db270fd46ad840b9d3b8bd3b637933fa05c5ebde6da67` |
| 2026-10-13 18:19:48 | polygon | USDC.e→pUSD | 3 906,99 | `0xc8a6871d…8d64` | `0x1a1ef4c6…cc40` | wrap_mint_pusd | VaultDepositooor (fun.xyz deposit passage co | CHAINE | `0xd6c102f7e3eed462f41e9d9eb96bee66d07b81ff0dec9ecd55e15f7aef83fa34` |
| 2026-10-13 18:19:48 | polygon | USDC | 3 906,99 | `0x82775eb8…a3a1` | `0xc8a6871d…8d64` | relay_escrow_to_payout | VaultDepositooor (fun.xyz deposit passage co | PROTOCOLE | `0x8cc54609fd99877895618ddbfe12386a2a95b13ccb991a7164156c53976776c4` |

**Transactions vérifiables, sorties :**

| UTC | Chaîne | Actif | Montant | De | Vers | Événement | Service | Preuve | Transaction |
|---|---|---|---|---|---|---|---|---|---|
| 2026-10-27 02:01:24 | polygon | pUSD | 35 546,89 | `0x1a1ef4c6…cc40` | `0x00000000…0000` | burn_pusd_unwrap |  | CHAINE | `0x27db9e0ad79e75020c1fcff6d22940313ab26808a853a5139db35c8823321a91` |
| 2026-10-27 02:01:24 | ethereum | USDC | 35 546,89 | `0x1a1ef4c6…cc40` | `0x82775eb8…a3a1` | relay_payout_to_recipient |  | PROTOCOLE | `0x1eb9ec280314e1c8e81753c286d53d4aee7c0e7e1eac4149e4de1f9409213b76` |

### Zoomman17

Wallet `0x92a8eec13a691af81a1a196b7594c1eccfa0eebc`. Clé propriétaire lue sur la chaîne : `0xd90d00130519086d412d2b9ffac2bb01f71ef444`. Lien étiquette vers adresse : SHARES_ONLY. 5 dépôts pour 9 743,19 $, 3 retraits pour 6 894,00 $, soit -2 849,19 $ de retraits moins dépôts.

**En bref.** Seul compte perdant du groupe. L'argent vient d'adresses étiquetées Revolut, de Chainflip et d'un service dépositaire non attribué. Les retraits repartent par `0x8c5dc729…10fe`, adresse à une seule sortie, vers `0xf7c8da79…d921`, étiquetée Revolut 5 : c'est le profil d'une adresse de dépôt chez Revolut. L'argent semble être revenu d'où il venait.

| Question | Réponse | Niveau |
|---|---|---|
| Origine des financements | Chainflip 1 5 439,33 $, Revolut 1 3 227,76 $ sur 7 versements, `0x58f298e3…0214` 867,98 $ ; 0,11 ETH par `0x09c30cdc…` (Revolut 6) | démontré pour les flux, attribution pour les noms |
| Premier financeur identifiable | Revolut 1 et Chainflip 1, chacune dans deux sources publiques | attribution |
| Dernier maillon avant dépôt | La clé `0xd90d0013…f444`, Relay, `0xc8a6871d…8d64` | démontré, protocole |
| Services | Revolut, Chainflip, `0x58f298e3…0214`, MetaMask, Relay | attribution, mesure, protocole |
| XMR | Absente des données accessibles | aucun indice |
| Retraits | 6 894,00 $ vers la clé, dont 6 893,00 USDC en 4 envois vers `0x8c5dc729…10fe`, balayés vers `0xf7c8da79…d921` (Revolut 5) | protocole, démontré, attribution |
| Où la trace devient incertaine | À `0xf7c8da79…d921` | inaccessible |

**Sources de l'argent, par dépôt** (répartition PEPS quand plusieurs entrées se mêlent, convention comptable) :

| Dernière source publique | Chaîne | Service | Catégorie | Dollars alloués | Tx |
|---|---|---|---|---|---|
| `0xf5e10380…2bcc` | ethereum | Chainflip 1 | bridge | 5 438,33 | 1 |
| `0xb23360cc…c460` | ethereum | Revolut: Hot Wallet | exchange | 3 181,85 | 5 |
| `0x58f298e3…0214` | ethereum | Payout wallet of an unattributed custodial service | custodial_unattributed | 862,59 | 1 |
| — | ethereum | Ses propres retraits, redéposés | bridge | 1,87 | 1 |

**Soldes lus le 2 nov.** :

| Adresse du dossier | Chaîne | Solde lu | Lu à (UTC) |
|---|---|---|---|
| `0xd90d0013…f444` | ethereum | 0.001040 ETH ; 0.000002 USDC | 2026-11-02 14:02:38 |

**Rapprochement.** Solde pUSD calculé 0.002333, lu 0.002333. Dépôts 5/5 et retraits 3/3 rapprochés de l'API. Frappes hors dépôts : 2, toutes des remboursements (`REDEEM`) : oui. Transferts de positions hors transaction de marché : 0. Mouvements de pUSD absents de l'API : 0.

**Chemins non résolus** :

- L'actif d'origine avant Chainflip : registre du protocole non lu. `0xf7c8da79…d921` : étiquette Revolut 5 sur Blockscout seule, confortée par 27 lignes avec Revolut 1.

**Confiance et explications alternatives.** Flux : haute. « Dépôt chez Revolut » repose sur le profil (adresse à nonce 1, un seul balayage) et sur une étiquette à source unique. Les retraits moins dépôts donnent une perte de 2 849,19 $.

**Transactions vérifiables, financement :**

| UTC | Chaîne | Actif | Montant | De | Vers | Événement | Service | Preuve | Transaction |
|---|---|---|---|---|---|---|---|---|---|
| 2026-10-06 00:32:11 | ethereum | USDC | 867,98 | `0x58f298e3…0214` | `0xd90d0013…f444` | transfer_in | Payout wallet of an unattributed custodial s | CHAINE+ATTRIBUTION | `0xa3214c31f7b3b3494293abbea89a40f059f2bb42b20cb04434970d2a2361a120` |
| 2026-10-06 00:45:05 | polygon | USDC.e→pUSD | 857,25 | `0xc8a6871d…8d64` | `0x92a8eec1…eebc` | wrap_mint_pusd | VaultDepositooor (fun.xyz deposit passage co | CHAINE | `0xc401f99aae37edbab349f5130cdf1db71d4c23539a741594aa8aa91b4dbc092e` |
| 2026-10-06 00:45:05 | ethereum | USDC | 857,25 | `0xd90d0013…f444` | `0xc8a6871d…8d64` | relay_escrow_to_payout | VaultDepositooor (fun.xyz deposit passage co | PROTOCOLE | `0xc57e5170b950615d23938e5fc57bed952f29927f7d838443b5c0b8f22b258643` |
| 2026-10-09 14:28:47 | ethereum | USDC | 217,77 | `0xb23360cc…c460` | `0xd90d0013…f444` | transfer_in | Revolut: Hot Wallet | CHAINE+ATTRIBUTION | `0x72a7ece2e2b99c4555d371704ff4a22d5ac890edbcb4129fd95b826444119d33` |
| 2026-10-09 16:13:59 | ethereum | USDC | 1 100,00 | `0xb23360cc…c460` | `0xd90d0013…f444` | transfer_in | Revolut: Hot Wallet | CHAINE+ATTRIBUTION | `0xd15f17aa01c3ca6a3f34f88a77896bdd232c247b24dcdd36a6cbacdd3a755caf` |
| 2026-10-09 16:20:35 | ethereum | USDC | 1 380,00 | `0xb23360cc…c460` | `0xd90d0013…f444` | transfer_in | Revolut: Hot Wallet | CHAINE+ATTRIBUTION | `0x31e87120bff89d35738310b07c72d21adff68f12065b2b677766d9f000ae997e` |
| 2026-10-09 16:27:04 | polygon | USDC.e→pUSD | 2 700,42 | `0xc8a6871d…8d64` | `0x92a8eec1…eebc` | wrap_mint_pusd | VaultDepositooor (fun.xyz deposit passage co | CHAINE | `0xebe54012d7f85a8b96b927389e7f8e0165a45cfd183c97920d43044ef9935227` |
| 2026-10-09 16:27:04 | ethereum | USDC | 2 700,42 | `0xd90d0013…f444` | `0xc8a6871d…8d64` | relay_escrow_to_payout | VaultDepositooor (fun.xyz deposit passage co | PROTOCOLE | `0x8463683e0e743d02ec00e81d2bf0f3a723e561e052c40d95326eec05a8f35805` |
| 2026-10-09 19:56:47 | ethereum | USDC | 18,18 | `0xb23360cc…c460` | `0xd90d0013…f444` | transfer_in | Revolut: Hot Wallet | CHAINE+ATTRIBUTION | `0x6abb64f75281a4e9d1b675f5abfff82b2723106421ec310af2b9f05b1d5e4e17` |
| 2026-10-09 20:03:47 | ethereum | USDC | 5 439,33 | `0xf5e10380…2bcc` | `0xd90d0013…f444` | transfer_in | Chainflip 1 | CHAINE+ATTRIBUTION | `0xa290b2af61506058dc65e362a1ef51896c86a6374f701d38b521f25044e975b7` |
| 2026-10-09 20:12:04 | polygon | USDC.e→pUSD | 5 438,42 | `0xc8a6871d…8d64` | `0x92a8eec1…eebc` | wrap_mint_pusd | VaultDepositooor (fun.xyz deposit passage co | CHAINE | `0x48fa0f7f390f9e4198fcad75edd672a0621cfb9f3102e269c5b37ca8e9e9bde5` |
| 2026-10-09 20:12:04 | ethereum | USDC | 5 438,42 | `0xd90d0013…f444` | `0xc8a6871d…8d64` | relay_escrow_to_payout | VaultDepositooor (fun.xyz deposit passage co | PROTOCOLE | `0x5cdaaf6dc1507a6031aaaa7c53bb39adebaaf253084a6c6ff005b71940fca4e3` |
| 2026-10-11 22:25:11 | ethereum | ETH | 0.000239 | `0xb42f812a…ead6` | `0xd90d0013…f444` | candidate_inflow | Relayer of MetaMask-delegated transactions | CHAINE | `0x03a5847d34cb913e473ed83f4ec77c31bac353664aff47319cb144f460b469bd` |
| 2026-10-12 17:04:35 | ethereum | USDC | 100,00 | `0xf70da978…dbef` | `0xd90d0013…f444` | own_withdrawal_returned | Relay EVM solver | CHAINE | `0x06fb9a3e9634ab9c66f7555fb3f4b4a82a0b9028380b3d918b5dead4fd01e5d6` |
| 2026-10-12 17:05:47 | ethereum | ETH | 0.000261 | `0xc066ac5d…8b8c` | `0xd90d0013…f444` | candidate_inflow | MetaMask: Gas Station | CHAINE+ATTRIBUTION | `0x15e4ae0f31c97421af589acbf9426564a1798eed948e17281a63578e88c29c40` |
| 2026-10-21 17:12:59 | ethereum | USDC | 487,69 | `0xb23360cc…c460` | `0xd90d0013…f444` | transfer_in | Revolut: Hot Wallet | CHAINE+ATTRIBUTION | `0xc61824ddee3940ee60df982102a28fe2c90e8a5bd7d5f1fe2416333a038cade6` |
| 2026-10-21 17:18:29 | polygon | USDC.e→pUSD | 488,56 | `0xc8a6871d…8d64` | `0x92a8eec1…eebc` | wrap_mint_pusd | VaultDepositooor (fun.xyz deposit passage co | CHAINE | `0x554a318df23454a06c0c128b8d37bf9fa65357dcc32fa2cb5753d148d40328b2` |
| 2026-10-21 17:18:29 | ethereum | USDC | 488,56 | `0xd90d0013…f444` | `0xc8a6871d…8d64` | relay_escrow_to_payout | VaultDepositooor (fun.xyz deposit passage co | PROTOCOLE | `0x30446d55890193a659e530e344c7b942919095f7e1e269050e316e90b1c690a2` |
| 2026-10-26 17:26:11 | ethereum | ETH | 0.113163 | `0x09c30cdc…d818` | `0xd90d0013…f444` | candidate_inflow | Revolut 6 | CHAINE+ATTRIBUTION | `0x1373d64937774e481aecc3d805ca0ce22c682de09625c56e323a49112ceac11a` |
| 2026-10-26 17:28:03 | polygon | USDC.e→pUSD | 258,54 | `0xc8a6871d…8d64` | `0x92a8eec1…eebc` | wrap_mint_pusd | VaultDepositooor (fun.xyz deposit passage co | CHAINE | `0xe71611559dcd72a58df7a1bbe93171cf606f773971a93c2e9c109ab75ea89c69` |
| 2026-10-26 17:28:03 | ethereum | ETH | 0.112061 | `0xd90d0013…f444` | `0xc8a6871d…8d64` | relay_escrow_to_payout | VaultDepositooor (fun.xyz deposit passage co | PROTOCOLE | `0xf399ec1d7e00462359566c5fb9f5e55205a6a5cc0b1a29f09a5dbd168b53653b` |

**Transactions vérifiables, sorties :**

| UTC | Chaîne | Actif | Montant | De | Vers | Événement | Service | Preuve | Transaction |
|---|---|---|---|---|---|---|---|---|---|
| 2026-10-11 22:23:39 | polygon | pUSD | 50,00 | `0x92a8eec1…eebc` | `0x00000000…0000` | burn_pusd_unwrap |  | CHAINE | `0x1bb4cf39845d19c62166ed1cb3e2b0f4c37a0c0298ce7cba062ff5e2217c33f8` |
| 2026-10-11 22:23:39 | ethereum | USDC | 50,00 | `0x92a8eec1…eebc` | `0xd90d0013…f444` | relay_payout_to_recipient |  | PROTOCOLE | `0xd65619db14590731fd8f81834bc692aa4ee22add918a8c70b898ba3e81c01899` |
| 2026-10-11 22:25:11 | ethereum | USDC | 50,00 | `0xd90d0013…f444` | `0x8c5dc729…10fe` | onward_transfer |  | CHAINE | `0x6e04aeb4c6c1a84ded7fa077c988edf2c5c95c00e8db7237a902e89d1863cf54` |
| 2026-10-12 17:04:35 | polygon | pUSD | 100,00 | `0x92a8eec1…eebc` | `0x00000000…0000` | burn_pusd_unwrap |  | CHAINE | `0x53d6a39bf44b025c21d3f2a071931cbaedd255bc7a7370cc402fcf378e74b67e` |
| 2026-10-12 17:04:35 | ethereum | USDC | 100,00 | `0x92a8eec1…eebc` | `0xd90d0013…f444` | relay_payout_to_recipient |  | PROTOCOLE | `0x06fb9a3e9634ab9c66f7555fb3f4b4a82a0b9028380b3d918b5dead4fd01e5d6` |
| 2026-10-12 17:05:47 | ethereum | USDC | 80,00 | `0xd90d0013…f444` | `0x8c5dc729…10fe` | onward_transfer |  | CHAINE | `0xf1774581f19e50f5e26cd2cfe08b1764256e3f1214a12ede562bc3a55451ae13` |
| 2026-10-12 17:05:47 | ethereum | USDC | 1,13 | `0xd90d0013…f444` | `0xe3478b0b…1964` | onward_transfer | MetaMask: Gas Station Swap | CHAINE+ATTRIBUTION | `0x33b450d1ee18857b54141b4f909d0ec0dccdfa0347f0a0f9ca2e60ce72ef7d9a` |
| 2026-10-13 05:11:23 | ethereum | USDC | 18,00 | `0xd90d0013…f444` | `0x8c5dc729…10fe` | onward_transfer |  | CHAINE | `0x03fe85a303e5ac330cbcd730098d92c35c6ec5e381daa77e86e87cbac4662033` |
| 2026-10-21 17:18:23 | ethereum | USDC | 488,56 | `0xd90d0013…f444` | `0x4cd00e38…bc31` | onward_relay_deposit | Relay Depository | CHAINE | `0x30446d55890193a659e530e344c7b942919095f7e1e269050e316e90b1c690a2` |
| 2026-10-26 17:27:59 | ethereum | ETH | 0.112061 | `0xd90d0013…f444` | `0x4cd00e38…bc31` | onward_relay_deposit | Relay Depository | CHAINE | `0xf399ec1d7e00462359566c5fb9f5e55205a6a5cc0b1a29f09a5dbd168b53653b` |
| 2026-10-27 02:08:27 | polygon | pUSD | 6 744,00 | `0x92a8eec1…eebc` | `0x00000000…0000` | burn_pusd_unwrap |  | CHAINE | `0x42bfdbb50dd6482190bd0e60fe9deeac157b1a6f6f1e5e1262b35c7bed66df97` |
| 2026-10-27 02:08:27 | ethereum | USDC | 6 744,00 | `0x92a8eec1…eebc` | `0xd90d0013…f444` | relay_payout_to_recipient |  | PROTOCOLE | `0x0f5ba8886f979909e2b5b54739641e860d8ed8cee449b60db1f5287f075ad8b0` |
| 2026-10-27 11:55:59 | ethereum | USDC | 6 745,00 | `0xd90d0013…f444` | `0x8c5dc729…10fe` | onward_transfer |  | CHAINE | `0x7a90713919396d421938d9fd885a4d11de93724f03cfadf7198cc8475203aef6` |

### kraben006

Wallet `0x84212ee459d1edaf35983bbec342b0806282d8ec`. Clé propriétaire lue sur la chaîne : `0x101b5f4dc0886c32e2b75972101aeaf9f338fb65`. Lien étiquette vers adresse : SHARES_ONLY. 14 dépôts pour 5 689,47 $, 5 retraits pour 15 593,54 $, soit 9 904,07 $ de retraits moins dépôts.

**En bref.** Beaucoup de petits dépôts, 14 pour 5 689,47 $, et une source principale : quatre portefeuilles de paiement à fort trafic, dont trois rechargés par la même trésorerie. S'y ajoutent 188,97 $ de SwftSwap. Plus tôt dans l'année, la clé a reçu de Deblock et de ChangeNOW. Le 4 octobre, elle reçoit 0,00205 ETH de la clé de brace227 et envoie 0,00247 ETH vers une adresse de dépôt de ChangeNOW. Les retraits restent sur la clé : 15 154,83 USDC.

| Question | Réponse | Niveau |
|---|---|---|
| Origine des financements | `0x58f298e3…0214`, `0xbd1f4462…eb3b`, `0x0c58909d…270d`, `0x7bef1627…5c24`, SwftSwap 188,97 $. Plus tôt en 2026, `0xdd3d72c5…` (ChangeNOW: Hot Wallet 3) et `0xb43c1981…` (Deblock: Wallet 1) : au PEPS, ces fonds sont sortis avant les dépôts de la période | démontré pour les flux, mesure |
| Premier financeur identifiable | Service dépositaire non attribué. Ces portefeuilles reçoivent de l'ETH de Kraken: Hot Wallet 2 pour leur gaz, ce qui ne suffit pas à en faire Kraken | mesure |
| Dernier maillon avant dépôt | La clé `0x101b5f4d…fb65`, Relay, `0xc8a6871d…8d64` | démontré, protocole |
| Services | Service non attribué, SwftSwap, ChangeNOW, Deblock, Across (49,18 USDC en fév. 2026), Relay | mesure, nom vérifié, attribution, protocole |
| XMR | Absente des données accessibles : la clé touche ChangeNOW, qui liste XMR, mais rien ne dit quel actif était en face. Simple compatibilité | aucun indice |
| Retraits | 15 593,54 $ vers la clé. 15 154,83 USDC y restent | protocole |
| Où la trace devient incertaine | En amont du service non attribué. En aval, seule sortie non Relay : 0,00247 ETH vers `0x7e67df45…6e23`, balayés vers `0x3f3ee0a9…207b` (ChangeNOW Dep) | inaccessible |

**Sources de l'argent, par dépôt** (répartition PEPS quand plusieurs entrées se mêlent, convention comptable) :

| Dernière source publique | Chaîne | Service | Catégorie | Dollars alloués | Tx |
|---|---|---|---|---|---|
| `0x7bef1627…5c24` | ethereum | Payout wallet of an unattributed custodial service | custodial_unattributed | 1 942,61 | 5 |
| `0xbd1f4462…eb3b` | ethereum | Payout wallet of an unattributed custodial service | custodial_unattributed | 1 752,46 | 2 |
| `0x58f298e3…0214` | ethereum | Payout wallet of an unattributed custodial service | custodial_unattributed | 1 046,82 | 2 |
| — | ethereum | Ses propres retraits, redéposés | bridge | 439,32 | 2 |
| `0x0c58909d…270d` | ethereum | Payout wallet of an unattributed custodial service | custodial_unattributed | 315,68 | 1 |
| `0xc1d13492…a1b5` | ethereum | SwftSwap (SWFT Blockchain) | instant_exchange | 188,97 | 1 |
| `0xcad97616…e850` | ethereum | non étiquetée (HIGH_VOLUME) | — | 3,61 | 1 |

**Soldes lus le 2 nov.** :

| Adresse du dossier | Chaîne | Solde lu | Lu à (UTC) |
|---|---|---|---|
| `0x101b5f4d…fb65` | ethereum | 0.001378 ETH ; 15 154.826661 USDC | 2026-11-02 14:02:38 |

**Rapprochement.** Solde pUSD calculé 0.000000, lu 0.000000. Dépôts 14/14 et retraits 5/5 rapprochés de l'API. Frappes hors dépôts : 0, toutes des remboursements (`REDEEM`) : oui. Transferts de positions hors transaction de marché : 0. Mouvements de pUSD absents de l'API : 0.

**Chemins non résolus** :

- `0x7e67df45…6e23` : 2 transactions, reçoit 0,00247 ETH et renvoie 0,00241 ETH 8 minutes plus tard vers `0x3f3ee0a9…207b`, étiqueté ChangeNOW Dep sur Blockscout : profil d'une adresse de dépôt ChangeNOW. Ce que la clé a reçu en échange, et où, n'est pas public.

**Confiance et explications alternatives.** Flux : haute. Le lien avec brace227 porte sur 0,00205 ETH, environ 5,5 $, soit moins de 0,1 % des dépôts : c'est un lien entre deux clés, pas un financement. Il est instruit dans `COMMON_FUNDERS.md`.

**Transactions vérifiables, financement :**

| UTC | Chaîne | Actif | Montant | De | Vers | Événement | Service | Preuve | Transaction |
|---|---|---|---|---|---|---|---|---|---|
| 2026-02-23 17:06:11 | ethereum | USDC | 49,18 | `0xcad97616…e850` | `0x101b5f4d…fb65` | transfer_in |  | CHAINE | `0x4f7bf1ca04123f5d7c0c7ee4ed54dcc6618b160f6b407edd8dfbf2b57e821fa9` |
| 2026-10-01 18:25:35 | ethereum | USDC | 188,97 | `0xc1d13492…a1b5` | `0x101b5f4d…fb65` | transfer_in | SwftSwap (SWFT Blockchain) | CHAINE+ATTRIBUTION | `0x7ba5697f8278d0558d58e97250d086128e76f18b730637072a44d2de0db6530f` |
| 2026-10-01 18:31:03 | polygon | USDC.e→pUSD | 191,58 | `0xc8a6871d…8d64` | `0x84212ee4…d8ec` | wrap_mint_pusd | VaultDepositooor (fun.xyz deposit passage co | CHAINE | `0x4431828712a924d5845de5f1779ad98eabf3563d55f299f46dde35700129a5a4` |
| 2026-10-01 18:31:03 | ethereum | USDC | 191,58 | `0x101b5f4d…fb65` | `0xc8a6871d…8d64` | relay_escrow_to_payout | VaultDepositooor (fun.xyz deposit passage co | PROTOCOLE | `0x08ac0743492cf551079d0623e366090dc55ddd32b2dbd302dc6614b70e5fc214` |
| 2026-10-01 18:37:23 | ethereum | USDC | 727,80 | `0x58f298e3…0214` | `0x101b5f4d…fb65` | transfer_in | Payout wallet of an unattributed custodial s | CHAINE+ATTRIBUTION | `0x8948ecd5edf1ab214c850641ca340fbbf7e6496f42b863c38f77f497417c6395` |
| 2026-10-01 18:40:05 | polygon | USDC.e→pUSD | 727,80 | `0xc8a6871d…8d64` | `0x84212ee4…d8ec` | wrap_mint_pusd | VaultDepositooor (fun.xyz deposit passage co | CHAINE | `0x9bd24bc8f5b3a2482c1d10c383ab09ed2cfaaf01881f1e061ca14db61de41ef2` |
| 2026-10-01 18:40:05 | ethereum | USDC | 727,80 | `0x101b5f4d…fb65` | `0xc8a6871d…8d64` | relay_escrow_to_payout | VaultDepositooor (fun.xyz deposit passage co | PROTOCOLE | `0x2352e5def174fc06c23cc4dda609ed59d6140b53cf96e3b4b278ff1f465f0c27` |
| 2026-10-01 21:48:11 | ethereum | USDC | 1 064,88 | `0xbd1f4462…eb3b` | `0x101b5f4d…fb65` | transfer_in | Payout wallet of an unattributed custodial s | CHAINE+ATTRIBUTION | `0x4106c63f93fffc8fd0b31ceb039a22c5e9dbf10d92167b7b523325dd7345f719` |
| 2026-10-01 22:14:06 | polygon | USDC.e→pUSD | 1 000,00 | `0xc8a6871d…8d64` | `0x84212ee4…d8ec` | wrap_mint_pusd | VaultDepositooor (fun.xyz deposit passage co | CHAINE | `0x134255bbdc7722246eb7f8cdd48aa159b11da845deb1fd6cf4533a7c54e26b0f` |
| 2026-10-01 22:14:06 | ethereum | USDC | 1 000,00 | `0x101b5f4d…fb65` | `0xc8a6871d…8d64` | relay_escrow_to_payout | VaultDepositooor (fun.xyz deposit passage co | PROTOCOLE | `0x557dc457f597753780d57903feaaef1faccbc868c0e51db75a199e0bf47be726` |
| 2026-10-01 22:34:30 | polygon | USDC.e→pUSD | 48,66 | `0xc8a6871d…8d64` | `0x84212ee4…d8ec` | wrap_mint_pusd | VaultDepositooor (fun.xyz deposit passage co | CHAINE | `0x9ab2d5a321f800a8e5927610fced63b41fd9e4a9fb2c2194acdd5171878f5ed5` |
| 2026-10-01 22:34:30 | ethereum | USDC | 48,66 | `0x101b5f4d…fb65` | `0xc8a6871d…8d64` | relay_escrow_to_payout | VaultDepositooor (fun.xyz deposit passage co | PROTOCOLE | `0x5683d212da17a9cb6492ff2cdfaa81462d121003255399b48b17535dd58c2ffe` |
| 2026-10-02 03:29:35 | ethereum | USDC | 319,02 | `0x58f298e3…0214` | `0x101b5f4d…fb65` | transfer_in | Payout wallet of an unattributed custodial s | CHAINE+ATTRIBUTION | `0xa07e9e381a84c7921734451f95e5aa95931a5b25265ca3071e832ed11dafc115` |
| 2026-10-02 03:34:15 | polygon | USDC.e→pUSD | 328,00 | `0xc8a6871d…8d64` | `0x84212ee4…d8ec` | wrap_mint_pusd | VaultDepositooor (fun.xyz deposit passage co | CHAINE | `0x1f9632314ef75fc7ff5db9dbad87b72dea7403e9567a79dd729428c22457f357` |
| 2026-10-02 03:34:15 | ethereum | USDC | 328,00 | `0x101b5f4d…fb65` | `0xc8a6871d…8d64` | relay_escrow_to_payout | VaultDepositooor (fun.xyz deposit passage co | PROTOCOLE | `0x3e43af73c52acf8d3867b1f275919c948906662af4e1a0e95dcd2b82c8d204a9` |
| 2026-10-02 03:51:23 | ethereum | USDC | 315,68 | `0x0c58909d…270d` | `0x101b5f4d…fb65` | transfer_in | Payout wallet of an unattributed custodial s | CHAINE+ATTRIBUTION | `0x26103b96cae8b5403fdd784b462f462e2ab81c2f9d51bbb11b337ebb443966b5` |
| 2026-10-02 03:53:17 | polygon | USDC.e→pUSD | 312,91 | `0xc8a6871d…8d64` | `0x84212ee4…d8ec` | wrap_mint_pusd | VaultDepositooor (fun.xyz deposit passage co | CHAINE | `0x6316e5f527c0d8686fa219d7dd21da71f3889949faeb891a50ce195f864a0e22` |
| 2026-10-02 03:53:17 | ethereum | USDC | 312,91 | `0x101b5f4d…fb65` | `0xc8a6871d…8d64` | relay_escrow_to_payout | VaultDepositooor (fun.xyz deposit passage co | PROTOCOLE | `0x16dfe57f78059c4096377e87029c9563c02ca9a79a425ba2752fd97b0cb23f68` |
| 2026-10-03 14:05:39 | polygon | USDC.e→pUSD | 10,00 | `0xc8a6871d…8d64` | `0x84212ee4…d8ec` | wrap_mint_pusd | VaultDepositooor (fun.xyz deposit passage co | CHAINE | `0x6ffa25cbccdab8a62d61e4227c5fa7198db101788e7da105268b52429db1d4bc` |
| 2026-10-03 14:05:39 | ethereum | USDC | 10,00 | `0x101b5f4d…fb65` | `0xc8a6871d…8d64` | relay_escrow_to_payout | VaultDepositooor (fun.xyz deposit passage co | PROTOCOLE | `0x73ed13aeda3ce6491eb426d441b40612467163410cc55bfa72de7d9891e44d5f` |
| 2026-10-07 00:18:59 | ethereum | USDC | 542,06 | `0x7bef1627…5c24` | `0x101b5f4d…fb65` | transfer_in | Payout wallet of an unattributed custodial s | CHAINE+ATTRIBUTION | `0x66a3b700ba3d9653b2a24f6a54f92fb9d772e52b408f11169fe552dee4c59acd` |
| 2026-10-07 00:23:15 | polygon | USDC.e→pUSD | 542,07 | `0xc8a6871d…8d64` | `0x84212ee4…d8ec` | wrap_mint_pusd | VaultDepositooor (fun.xyz deposit passage co | CHAINE | `0xbc0490b976c74db3d9294289bc1a161c2cedebdc0fe96882a77f9c266c70febd` |
| 2026-10-07 00:23:15 | ethereum | USDC | 542,07 | `0x101b5f4d…fb65` | `0xc8a6871d…8d64` | relay_escrow_to_payout | VaultDepositooor (fun.xyz deposit passage co | PROTOCOLE | `0x8854b76192e1bf3a2d821eae633c3b1dea2678277dc2a7d6f68ba1882c2c161d` |
| 2026-10-07 00:33:35 | ethereum | USDC | 438,28 | `0xf70da978…dbef` | `0x101b5f4d…fb65` | own_withdrawal_returned | Relay EVM solver | CHAINE | `0xb10a9439124aa29e783787d6a1399398cd1f2816b5d111c3c8cd60e19803d104` |
| 2026-10-07 00:34:38 | polygon | USDC.e→pUSD | 438,28 | `0xc8a6871d…8d64` | `0x84212ee4…d8ec` | wrap_mint_pusd | VaultDepositooor (fun.xyz deposit passage co | CHAINE | `0x2252ee0ab0d3dc7e71efc78278dc54232233778c22879ae41d201032d0e9079d` |
| 2026-10-07 00:34:38 | ethereum | USDC | 438,28 | `0x101b5f4d…fb65` | `0xc8a6871d…8d64` | relay_escrow_to_payout | VaultDepositooor (fun.xyz deposit passage co | PROTOCOLE | `0x49f71eeb7e709ed4c648df639364159c5b7d481ce4b439db3ecdeb546f121d81` |
| 2026-10-08 23:48:23 | ethereum | USDC | 323,76 | `0x7bef1627…5c24` | `0x101b5f4d…fb65` | transfer_in | Payout wallet of an unattributed custodial s | CHAINE+ATTRIBUTION | `0x02bbca7b4885423abaa6f04a0370fd03b30a9457e5678586409a531fb7455945` |
| 2026-10-08 23:52:15 | polygon | USDC.e→pUSD | 323,76 | `0xc8a6871d…8d64` | `0x84212ee4…d8ec` | wrap_mint_pusd | VaultDepositooor (fun.xyz deposit passage co | CHAINE | `0x6cdf49c109f7202a6c1825dfc7ee225d6dbb4a2d08ea3b1d0d961cdbfa1e7b05` |
| 2026-10-08 23:52:15 | ethereum | USDC | 323,76 | `0x101b5f4d…fb65` | `0xc8a6871d…8d64` | relay_escrow_to_payout | VaultDepositooor (fun.xyz deposit passage co | PROTOCOLE | `0x5943df9961b79c0f4093e9a23cb23471b5f806054f82815c4188332f4fb36a6d` |
| 2026-10-11 22:59:59 | ethereum | USDC | 1,04 | `0xf70da978…dbef` | `0x101b5f4d…fb65` | own_withdrawal_returned | Relay EVM solver | CHAINE | `0x78a14f612e551d846e49c906c906dbcbc56a4e2234b84f678d11eacb50b612f9` |
| 2026-10-14 19:41:59 | ethereum | USDC | 750,86 | `0x7bef1627…5c24` | `0x101b5f4d…fb65` | transfer_in | Payout wallet of an unattributed custodial s | CHAINE+ATTRIBUTION | `0x3b07198445c8f9790494caaa01cce5ff86b5746f43813b38fac8d6d634d4f513` |
| 2026-10-14 19:44:06 | polygon | USDC.e→pUSD | 751,90 | `0xc8a6871d…8d64` | `0x84212ee4…d8ec` | wrap_mint_pusd | VaultDepositooor (fun.xyz deposit passage co | CHAINE | `0xd26855d720351d96b6f93c524b89f80d79d9b15790ba536a150b0285edb4db8b` |
| 2026-10-14 19:44:06 | ethereum | USDC | 751,90 | `0x101b5f4d…fb65` | `0xc8a6871d…8d64` | relay_escrow_to_payout | VaultDepositooor (fun.xyz deposit passage co | PROTOCOLE | `0xcccd118f51a843c5f8f01b7e9a31f4435eb55fa97c290e38a45f418ca76a5538` |
| 2026-10-16 00:38:47 | ethereum | USDC | 183,37 | `0x7bef1627…5c24` | `0x101b5f4d…fb65` | transfer_in | Payout wallet of an unattributed custodial s | CHAINE+ATTRIBUTION | `0x31093011c3c696f513c31f2dcd40a5af5ccdcc4ca96a005e2a6b162a80f00968` |
| 2026-10-16 00:42:51 | polygon | USDC.e→pUSD | 183,37 | `0xc8a6871d…8d64` | `0x84212ee4…d8ec` | wrap_mint_pusd | VaultDepositooor (fun.xyz deposit passage co | CHAINE | `0xd45ecc0aceafeb9d69daf769e1abe18fe2f025c7c3a476952dede288c082e88e` |
| 2026-10-16 00:42:51 | ethereum | USDC | 183,37 | `0x101b5f4d…fb65` | `0xc8a6871d…8d64` | relay_escrow_to_payout | VaultDepositooor (fun.xyz deposit passage co | PROTOCOLE | `0x0c2d51c72fe26a2a9b7b800da3b1648e59848685e0ac3330053c0cc7ef41cf8d` |
| 2026-10-21 17:25:59 | ethereum | USDC | 687,58 | `0xbd1f4462…eb3b` | `0x101b5f4d…fb65` | transfer_in | Payout wallet of an unattributed custodial s | CHAINE+ATTRIBUTION | `0xb520245e080a9ac40962f90db4fda95829be88a91fe4a8ac1e07c7e6294c886f` |
| 2026-10-21 17:27:39 | polygon | USDC.e→pUSD | 687,58 | `0xc8a6871d…8d64` | `0x84212ee4…d8ec` | wrap_mint_pusd | VaultDepositooor (fun.xyz deposit passage co | CHAINE | `0xe118cd2cc411499646a056ab91b96edcfab83db74759b6503c560ced71c9b829` |
| 2026-10-21 17:27:39 | ethereum | USDC | 687,58 | `0x101b5f4d…fb65` | `0xc8a6871d…8d64` | relay_escrow_to_payout | VaultDepositooor (fun.xyz deposit passage co | PROTOCOLE | `0x91b38e708c25238008dda9f13d0f1f3edb01c9dce04f93710d29feed5f9c6d79` |
| 2026-10-21 18:09:23 | ethereum | USDC | 143,56 | `0x7bef1627…5c24` | `0x101b5f4d…fb65` | transfer_in | Payout wallet of an unattributed custodial s | CHAINE+ATTRIBUTION | `0x5393f4e9bf6a023fbe8d47bfca4f91678f2cac2952e19b4b212bef8a926f777b` |

2 autres lignes dans le CSV.

**Transactions vérifiables, sorties :**

| UTC | Chaîne | Actif | Montant | De | Vers | Événement | Service | Preuve | Transaction |
|---|---|---|---|---|---|---|---|---|---|
| 2026-10-07 00:33:34 | polygon | pUSD | 438,67 | `0x84212ee4…d8ec` | `0x00000000…0000` | burn_pusd_unwrap |  | CHAINE | `0x9e313ca47e181cfe4e0368653ed28a63826eded1ce4bbd50909db123ca99166e` |
| 2026-10-07 00:33:34 | ethereum | USDC | 438,28 | `0x84212ee4…d8ec` | `0x101b5f4d…fb65` | relay_payout_to_recipient |  | PROTOCOLE | `0xb10a9439124aa29e783787d6a1399398cd1f2816b5d111c3c8cd60e19803d104` |
| 2026-10-07 00:34:35 | ethereum | USDC | 438,28 | `0x101b5f4d…fb65` | `0x4cd00e38…bc31` | onward_relay_deposit | Relay Depository | CHAINE | `0x49f71eeb7e709ed4c648df639364159c5b7d481ce4b439db3ecdeb546f121d81` |
| 2026-10-08 23:52:11 | ethereum | USDC | 323,76 | `0x101b5f4d…fb65` | `0x4cd00e38…bc31` | onward_relay_deposit | Relay Depository | CHAINE | `0x5943df9961b79c0f4093e9a23cb23471b5f806054f82815c4188332f4fb36a6d` |
| 2026-10-11 23:00:00 | polygon | pUSD | 1,04 | `0x84212ee4…d8ec` | `0x00000000…0000` | burn_pusd_unwrap |  | CHAINE | `0xfe643b8d991f269ced5467f6d5d8d160b514f6465d55bb462f4f2ebeed232ed8` |
| 2026-10-11 23:00:00 | ethereum | USDC | 1,04 | `0x84212ee4…d8ec` | `0x101b5f4d…fb65` | relay_payout_to_recipient |  | PROTOCOLE | `0x78a14f612e551d846e49c906c906dbcbc56a4e2234b84f678d11eacb50b612f9` |
| 2026-10-14 19:43:59 | ethereum | USDC | 751,90 | `0x101b5f4d…fb65` | `0x4cd00e38…bc31` | onward_relay_deposit | Relay Depository | CHAINE | `0xcccd118f51a843c5f8f01b7e9a31f4435eb55fa97c290e38a45f418ca76a5538` |
| 2026-10-16 00:42:47 | ethereum | USDC | 183,37 | `0x101b5f4d…fb65` | `0x4cd00e38…bc31` | onward_relay_deposit | Relay Depository | CHAINE | `0x0c2d51c72fe26a2a9b7b800da3b1648e59848685e0ac3330053c0cc7ef41cf8d` |
| 2026-10-21 17:27:35 | ethereum | USDC | 687,58 | `0x101b5f4d…fb65` | `0x4cd00e38…bc31` | onward_relay_deposit | Relay Depository | CHAINE | `0x91b38e708c25238008dda9f13d0f1f3edb01c9dce04f93710d29feed5f9c6d79` |
| 2026-10-21 18:28:23 | ethereum | USDC | 143,56 | `0x101b5f4d…fb65` | `0x4cd00e38…bc31` | onward_relay_deposit | Relay Depository | CHAINE | `0x0a805d082656a4c775497039db8bba46d518aa0140bbaaff18661e056a822a41` |
| 2026-10-26 23:10:17 | polygon | pUSD | 11 078,88 | `0x84212ee4…d8ec` | `0x00000000…0000` | burn_pusd_unwrap |  | CHAINE | `0x95a3f9ded5c4e8e1a65fcaa53555ef4da06f9aba958f7476d4b8e99446453e98` |
| 2026-10-26 23:10:17 | ethereum | USDC | 11 078,88 | `0x84212ee4…d8ec` | `0x101b5f4d…fb65` | relay_payout_to_recipient |  | PROTOCOLE | `0x36e90fcd9e601dcc2ddab8f2a1bdda23074f63d63e751d89d1ce5d7941523b35` |
| 2026-10-26 23:30:08 | polygon | pUSD | 4 054,20 | `0x84212ee4…d8ec` | `0x00000000…0000` | burn_pusd_unwrap |  | CHAINE | `0x758a809484f6b8e5f3c72e135fdbdc950e105944921b06c192e03c3768564599` |
| 2026-10-26 23:30:08 | ethereum | USDC | 4 054,20 | `0x84212ee4…d8ec` | `0x101b5f4d…fb65` | relay_payout_to_recipient |  | PROTOCOLE | `0xaebdc4159eee3a84bc50b1be5ab6cefebb85c9150e9643ebbcdcd072e5f552b4` |
| 2026-10-26 23:39:21 | polygon | pUSD | 20,75 | `0x84212ee4…d8ec` | `0x00000000…0000` | burn_pusd_unwrap |  | CHAINE | `0x841f53dee5fce76b516ebf8e595606546d19c8dfd67a951d3ff8a0c5cdeba3a4` |
| 2026-10-26 23:39:21 | ethereum | USDC | 20,75 | `0x84212ee4…d8ec` | `0x101b5f4d…fb65` | relay_payout_to_recipient |  | PROTOCOLE | `0x301e162c42063edd7ef55c984bacee1b843d232835b8a0c11dcfbcb8cb79af59` |

### OuldLm3alem

Wallet `0x71ae923f12eb947c58365287691cf5a10bc3e5bf`. Clé propriétaire lue sur la chaîne : `0x1b500b6c40a2ff0930e540e8f53c559a32e75f2c`. Lien étiquette vers adresse : ALIAS_EXACT. 3 dépôts pour 56 167,11 $, 3 retraits pour 77 250,77 $, soit 21 083,66 $ de retraits moins dépôts.

**En bref.** Trois dépôts, chacun par une route différente : un contrat de paiement à fort trafic sur Ethereum, KuCoin Hot Wallet 2 sur Solana, une adresse étiquetée Binance sur Arbitrum. Le retrait principal, 77 050,77 $, a été converti en POL, puis en USDT, puis passé sur Arbitrum, puis sur Hyperliquid, où il a servi à trader. 73 001,19 USDC sont revenus sur la clé et y restent.

| Question | Réponse | Niveau |
|---|---|---|
| Origine des financements | `0xa3222357…59b3` 23 386,26 $, KuCoin Hot Wallet 2 16 798,01 $, `0xee7ae85f…4055` 15 982,84 $ | démontré pour les flux, attribution pour les noms |
| Premier financeur identifiable | KuCoin Hot Wallet 2 ; `0xee7ae85f…4055` (Binance: Hot Wallet 34) ; `0xa3222357…59b3` non attribué, 721 destinataires en 20 h, expéditeur `0x963737c5…ef9a` étiqueté Union Chain | attribution, mesure |
| Dernier maillon avant dépôt | `0xb3afcdc7…b0ba` (adresse de pont), Relay | démontré, protocole |
| Services | KuCoin, Binance, Relay, Uniswap, deBridge, CCTP, Hyperliquid | attribution, protocole |
| XMR | Absente des données accessibles | aucun indice |
| Retraits | 77 250,77 $ : 77 050,77 $ devenus 839 893,73 POL sur la clé ; 200,00 $ devenus 0,1333 BNB et 99,80 USDT sur `0xae232f78…c026` (BSC) | protocole |
| Où la trace devient incertaine | En amont seulement. Tout le reste est lu jusqu'au solde final | inaccessible |

**Sources de l'argent, par dépôt** (répartition PEPS quand plusieurs entrées se mêlent, convention comptable) :

| Dernière source publique | Chaîne | Service | Catégorie | Dollars alloués | Tx |
|---|---|---|---|---|---|
| `0xa3222357…59b3` | ethereum | non étiquetée (CONTRACT) | — | 23 386,26 | 1 |
| `BmFdpraQhk…ymy6` | solana | KuCoin Hot Wallet 2 | exchange | 16 798,01 | 1 |
| `0xee7ae85f…4055` | arbitrum | Binance: Hot Wallet 34 | exchange | 15 982,84 | 1 |

**Soldes lus le 2 nov.** :

| Adresse du dossier | Chaîne | Solde lu | Lu à (UTC) |
|---|---|---|---|
| `0x1b500b6c…5f2c` | polygon | 3.139130 POL | 2026-11-02 14:02:38 |
| `0x1b500b6c…5f2c` | arbitrum | 0.034316 ETH ; 73 001.186771 USDC | 2026-11-02 14:02:38 |
| `0xae232f78…c026` | bsc | 0.133330 BNB ; 99.796153 USDT | 2026-11-02 14:02:38 |

**Rapprochement.** Solde pUSD calculé 19.679800, lu 19.679800. Dépôts 3/3 et retraits 3/3 rapprochés de l'API. Frappes hors dépôts : 0, toutes des remboursements (`REDEEM`) : oui. Transferts de positions hors transaction de marché : 0. Mouvements de pUSD absents de l'API : 1.

**Chemins non résolus** :

- Le burn de pUSD du retrait `0x909d9602…a6f1` n'est pas une destination : la destination est la clé, payée en POL natif dans la même transaction.

**Confiance et explications alternatives.** Flux : haute, chaque saut est porté par un identifiant de protocole. Hyperliquid se réconcilie à 0,02 $ près : 75 724,54 $ reçus, 2 415,41 $ de pertes réalisées et 306,71 $ de frais sur 303 exécutions du contrat perpétuel HYPE, 73 002,40 $ repartis. Ce n'est pas une sortie déguisée. Un mouvement de 0,20 pUSD d'un autre wallet, absent de l'API, ressemble à un pourboire, non vérifié.

**Transactions vérifiables, financement :**

| UTC | Chaîne | Actif | Montant | De | Vers | Événement | Service | Preuve | Transaction |
|---|---|---|---|---|---|---|---|---|---|
| 2026-10-22 18:38:35 | ethereum | USDC | 23 386,26 | `0xa3222357…59b3` | `0xb3afcdc7…b0ba` | transfer_into_bridge_address |  | CHAINE | `0xe85dcab46ea592ba26e90b3c34deb1e804d7156dbd0b0a7627903394008c9950` |
| 2026-10-22 18:39:23 | polygon | USDC.e→pUSD | 23 386,26 | `0xb3afcdc7…b0ba` | `0x71ae923f…e5bf` | wrap_mint_pusd |  | CHAINE | `0xaed3dd931c9bbc163818983c01b6ebc43cb3885f43dcb18359d3651e7f5fe4dd` |
| 2026-10-22 18:39:23 | ethereum | USDC | 23 386,26 | `0xb3afcdc7…b0ba` | `0xb3afcdc7…b0ba` | relay_bridge_deposit_address |  | PROTOCOLE | `0xbf52b6aab3726466895dd1ebe5968895e0402dee8cc2163219126a8f491c3425` |
| 2026-10-26 01:22:14 | solana | USDC | 16 798,01 | `BmFdpraQhk…ymy6` | `5oXG1xh68W…paxJ` | transfer_in | KuCoin Hot Wallet 2 | CHAINE+ATTRIBUTION | `JCduE2q1Qd1hqs5NEu825y3NCJyydbetqNbRNF1nvESrqAvVnez9EpToiNBuYQcD7hHgpWFyRMnzdyi6senEy67` |
| 2026-10-26 01:22:32 | polygon | USDC.e→pUSD | 16 798,01 | `0xb3afcdc7…b0ba` | `0x71ae923f…e5bf` | wrap_mint_pusd |  | CHAINE | `0xfa1d9d8269559a21a64c18078d4df948cb203c04d9d8438d6ffe95af0693a585` |
| 2026-10-26 01:22:32 | solana | USDC | 16 798,01 | `5oXG1xh68W…paxJ` | `0xb3afcdc7…b0ba` | relay_escrow_to_payout |  | PROTOCOLE | `3rSQrmdXpUm5xekbR7FjmvtWGFLFAWZJRMNs2HPKtGs1f5re9JdYPpiCEpcgQexWbNGhtnnEFPy2VhXiHMRw2sRG` |
| 2026-10-26 09:40:40 | arbitrum | USDC | 15 982,84 | `0xee7ae85f…4055` | `0xb3afcdc7…b0ba` | transfer_into_bridge_address | Binance: Hot Wallet 34 | CHAINE+ATTRIBUTION | `0xc579ce36eea56ec37480b2d3c268f1a137af674c3cdc55c2d33f382a00840a32` |
| 2026-10-26 09:40:53 | polygon | USDC.e→pUSD | 15 982,84 | `0xb3afcdc7…b0ba` | `0x71ae923f…e5bf` | wrap_mint_pusd |  | CHAINE | `0x5989f1e5e5ca0b4bd298056077e0f07f0007dc78193cf576a6b7faa0366a45e9` |
| 2026-10-26 09:40:53 | arbitrum | USDC | 15 982,84 | `0xb3afcdc7…b0ba` | `0xb3afcdc7…b0ba` | relay_bridge_deposit_address |  | PROTOCOLE | `0x02a46fe71e8f8edf64c1e22f8b0a1b1d5e94c36c2736a0c840c45fafcf1825eb` |

**Transactions vérifiables, sorties :**

| UTC | Chaîne | Actif | Montant | De | Vers | Événement | Service | Preuve | Transaction |
|---|---|---|---|---|---|---|---|---|---|
| 2026-10-26 21:40:12 | polygon | pUSD | 100,00 | `0x71ae923f…e5bf` | `0x00000000…0000` | burn_pusd_unwrap |  | CHAINE | `0x8d84c3cf0d15c5e573b71b75c43182837a9d88b3d3ad1ed078c11ffef9c58a40` |
| 2026-10-26 21:40:12 | bsc | BNB | 0.133330 | `0x71ae923f…e5bf` | `0xae232f78…c026` | relay_payout_to_recipient |  | PROTOCOLE | `0xe9c0d3b85a632cf54ebdbdb10dd755b85797f82888e87496860f6ba16751bfb6` |
| 2026-10-26 21:41:59 | polygon | pUSD | 100,00 | `0x71ae923f…e5bf` | `0x00000000…0000` | burn_pusd_unwrap |  | CHAINE | `0x3e1349f5f6e9acd7450f9a7cdac622ca47d73811793f8cbef730063fdb441825` |
| 2026-10-26 21:41:59 | bsc | USDT | 99,80 | `0x71ae923f…e5bf` | `0xae232f78…c026` | relay_payout_to_recipient |  | PROTOCOLE | `0x966c40950de7e86379fa496c3cf2005f6e589c075fdea67b7ee021c0cf3a33ad` |
| 2026-10-26 23:50:53 | polygon | pUSD | 77 050,77 | `0x71ae923f…e5bf` | `0x00000000…0000` | burn_pusd_unwrap |  | CHAINE | `0x909d9602d5ad975b2f30c66d4a058592306e2468a002dd0a691170b61677a6f1` |
| 2026-10-26 23:50:53 | polygon | POL | 839 893,73 | `0x71ae923f…e5bf` | `0x1b500b6c…5f2c` | relay_same_tx_swap_native_log |  | PROTOCOLE | `0x909d9602d5ad975b2f30c66d4a058592306e2468a002dd0a691170b61677a6f1` |
| 2026-10-26 23:52:41 | polygon | POL | 839 000,00 | `0x1b500b6c…5f2c` | `0xdc264714…7c9f` | onward_transfer | UniversalRouter | CHAINE | `0x8c35829294c002aabcd2bd518e88f46f86e4c5a075c6e89938d4532cc62dd2c3` |
| 2026-10-29 20:54:51 | polygon | USDT | 75 946,74 | `0x1b500b6c…5f2c` | `0x663dc15d…c251` | onward_transfer | deBridge: Crosschain Forwarder Proxy | CHAINE+ATTRIBUTION | `0x70a1e0133b21f471c6e5bd556c54c5df982606ac8c45a47286edc0344c5d108f` |
| 2026-10-29 20:55:52 | arbitrum | USDC | 75 724,74 | `0x1b500b6c…5f2c` | `0xa95d9c1f…4fce` | onward_transfer | CctpExtension | CHAINE | `0x5c5e1650625c27fdc99cd69993a79132db223b899fef7b1b6b85911cf0fc223a` |
| 2026-10-29 22:11:57 | polygon | POL | 888,19 | `0x1b500b6c…5f2c` | `0x663dc15d…c251` | onward_transfer | deBridge: Crosschain Forwarder Proxy | CHAINE+ATTRIBUTION | `0xa2564ca04c4b7b9bfb74cc1d82a06193041fa66e560fe113c943826bc226d511` |

### 0xdd97e6

Wallet `0xdd97e6ad12ca4dd18a88804fb5ed7ed429849464`. Clé propriétaire lue sur la chaîne : `0xcf7b90deaf46d27b2b8f2f54a099d82879dd19ad`. Lien étiquette vers adresse : PREFIX_UNIQUE. 2 dépôts pour 44 059,16 $, 1 retraits pour 63 143,10 $, soit 19 083,95 $ de retraits moins dépôts.

**En bref.** Deux dépôts : 19 760,16 $ depuis un portefeuille BSC à fort trafic non étiqueté, 24 299,00 $ depuis KuCoin Hot Wallet 2. Le retrait de 63 143,10 $ a été converti en 26,97 ETH et n'a pas bougé. L'adresse de destination n'a signé aucune transaction.

| Question | Réponse | Niveau |
|---|---|---|
| Origine des financements | `0x6bf18baf…7e95` 19 760,16 $ (BSC), KuCoin Hot Wallet 2 24 299,00 $ (Solana) | démontré pour les flux |
| Premier financeur identifiable | KuCoin Hot Wallet 2. `0x6bf18baf…7e95` : nonce 966 093, sans étiquette | attribution, mesure |
| Dernier maillon avant dépôt | `0x22cec127…2e76` (adresse de pont), Relay | démontré, protocole |
| Services | KuCoin, service BSC non attribué, Relay | attribution, mesure, protocole |
| XMR | Absente des données accessibles | aucun indice |
| Retraits | 63 143,10 $ devenus 26,97 ETH sur `0xca8b1f1a…6165` | protocole |
| Où la trace devient incertaine | En amont seulement. Lien avec le wallet : préfixe de presse de six caractères, unique, non certifié | inaccessible |

**Sources de l'argent, par dépôt** (répartition PEPS quand plusieurs entrées se mêlent, convention comptable) :

| Dernière source publique | Chaîne | Service | Catégorie | Dollars alloués | Tx |
|---|---|---|---|---|---|
| `BmFdpraQhk…ymy6` | solana | KuCoin Hot Wallet 2 | exchange | 24 299,00 | 1 |
| `0x6bf18baf…7e95` | bsc | non étiquetée (HIGH_VOLUME) | — | 19 760,16 | 1 |

**Soldes lus le 2 nov.** :

| Adresse du dossier | Chaîne | Solde lu | Lu à (UTC) |
|---|---|---|---|
| `0xca8b1f1a…6165` | ethereum | 26.971594 ETH | 2026-11-02 14:02:38 |

**Rapprochement.** Solde pUSD calculé 0.000000, lu 0.000000. Dépôts 2/2 et retraits 1/1 rapprochés de l'API. Frappes hors dépôts : 2, toutes des remboursements (`REDEEM`) : oui. Transferts de positions hors transaction de marché : 0. Mouvements de pUSD absents de l'API : 0.

**Chemins non résolus** :

- Le lien entre l'étiquette de presse et ce wallet reste au niveau de l'inventaire de l'enquête d'origine.

**Confiance et explications alternatives.** Flux : haute. Alternatives : deux clients de plateforme distincts, ou le même : on ne peut pas trancher.

**Transactions vérifiables, financement :**

| UTC | Chaîne | Actif | Montant | De | Vers | Événement | Service | Preuve | Transaction |
|---|---|---|---|---|---|---|---|---|---|
| 2026-10-20 09:10:41 | bsc | USDC | 19 760,16 | `0x6bf18baf…7e95` | `0x22cec127…2e76` | transfer_into_bridge_address |  | CHAINE | `0x1a9bc0e19a8fe54df33a22b72e58e777aecd5adabb4717b0209f22d1f3b0b462` |
| 2026-10-20 09:11:08 | polygon | USDC.e→pUSD | 19 760,16 | `0x22cec127…2e76` | `0xdd97e6ad…9464` | wrap_mint_pusd |  | CHAINE | `0xf9ae2a36fcd4d92b72231b4bad40cca7fdc3a48f9620eace4cf9479bbbfb6f05` |
| 2026-10-20 09:11:08 | bsc | USDC | 19 760,16 | `0x22cec127…2e76` | `0x22cec127…2e76` | relay_bridge_deposit_address |  | PROTOCOLE | `0x46559f9c419241edec02846367c5340c43614407576d15631d2005c02d8df281` |
| 2026-10-21 11:58:31 | solana | USDC | 24 299,00 | `BmFdpraQhk…ymy6` | `4MMHYz6K6z…zgE1` | transfer_in | KuCoin Hot Wallet 2 | CHAINE+ATTRIBUTION | `2oSxXQQJktePVQVUCybxCsi28pQ4NBnVvkqmw7SnF2TcSLKT63R96LHubNdzdqLJs1UZPDWd3xbUKQjMoj1SvG3Z` |
| 2026-10-21 11:58:53 | polygon | USDC.e→pUSD | 24 299,00 | `0x22cec127…2e76` | `0xdd97e6ad…9464` | wrap_mint_pusd |  | CHAINE | `0x126d7ce56e0a9627b2ed4332e2b15071747d533dff7d3e735862067d6e249a68` |
| 2026-10-21 11:58:53 | solana | USDC | 24 299,00 | `4MMHYz6K6z…zgE1` | `0x22cec127…2e76` | relay_escrow_to_payout |  | PROTOCOLE | `3Jv2XZ96TRjTZisaYGosN4hQKYmAaBvCySWf9BoBf5i3UigtU1e8FYutH58GsZ9hA9r1MKp9jEfyHzpf5qTr6hwU` |

**Transactions vérifiables, sorties :**

| UTC | Chaîne | Actif | Montant | De | Vers | Événement | Service | Preuve | Transaction |
|---|---|---|---|---|---|---|---|---|---|
| 2026-10-27 00:49:30 | polygon | pUSD | 63 143,10 | `0xdd97e6ad…9464` | `0x00000000…0000` | burn_pusd_unwrap |  | CHAINE | `0x16ae2a26a481e38097d3b0cbcec9a704dc07d98e7de3b9d58935e6dc93f4b208` |
| 2026-10-27 00:49:30 | ethereum | ETH | 26,97 | `0xdd97e6ad…9464` | `0xca8b1f1a…6165` | relay_payout_to_recipient |  | PROTOCOLE | `0xf1ab0c279b35125a7101edf8092811b813e4a8566a82ad7d23e921d83b0d7718` |

## 4. Couverture et contrôles

| Mesure | Valeur |
|---|---|
| Dépôts lus | 46, 304 137,63 $ |
| Retraits lus | 25, 493 094,76 $ |
| Dépôts rapprochés d'une frappe de pUSD | 46 sur 46 |
| Retraits rapprochés d'une sortie de pUSD | 25 sur 25 |
| Soldes pUSD calculés égaux au solde lu | 11 sur 11 |
| Segments non résolus, en dollars d'entrée | 1 sur 46 dépôts, 258,54 $ (voir `UNKNOWN_PATHS.md`) |
| Tests sur cas connus | 77 sur 77 (`tests/test_forensics.py`) |
| Seconde source par saut (nœud public ou second RPC) | node_receipt_tx_exists : 130 ; node_receipt_log : 103 ; second_rpc_tx_exists : 12 ; second_rpc_parties_seen : 8 ; node_tx_value : 6 ; node_receipt_tx_exists_internal_or_unmatched : 1 |

## 5. Limites

- **Chaînes :** BSC et Base n'ont pas d'historique gratuit. Sur BSC : reçus connus, nonces et soldes ; pour la clé de brace227, 5 sorties récentes par dichotomie du nonce. Les entrées BSC et Base ne sont pas lues.
- **Natif :** lu sur Ethereum, Polygon, Arbitrum et Optimism. Solana : 60 transactions au plus par adresse.
- **Étiquettes :** trois sources publiques : deux listes, dont une datée de 2023, et les tags de Blockscout, lus sur Ethereum et Optimism pour les 73 adresses de services rencontrées. KuCoin Hot Wallet 2 : Orb seul. Une étiquette dit ce qu'une source a écrit, et aucune n'identifie un client.
- **Service absent des listes :** un exchange ou un mixeur récent peut ne pas y être. « Aucune interaction » veut dire aucune interaction avec une adresse connue, sur les historiques lus. Les adresses de dépôt de plateforme sont souvent éphémères et sans étiquette.
- **Budgets :** 4 sauts et 45 nœuds par sens et par dossier, au-dessus de 400 contreparties une adresse est traitée en hub. Aucun budget n'a été atteint ici, sauf le hub `0xcc0f311e…23f7`, dont l'historique est lu aux deux bouts.
- **PEPS :** la répartition entre entrées mêlées est une convention comptable.
- **Témoins :** échantillon partiel, traits choisis après coup, un seul témoin positif de lien direct.
- **Lien étiquette vers adresse :** niveaux inégaux, repris de l'inventaire de l'enquête d'origine.
- **Relecture :** faite par une session Claude parallèle, qui a relu le wallet `0xa8e64a3c…74a5` sur la chaîne. Même famille de modèle, pas un audit indépendant au sens fort.
