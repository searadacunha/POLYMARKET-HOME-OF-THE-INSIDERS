# Financeurs et destinations communs

Lu le 2 novembre 2026. Un service commun ne relie personne. Une origine commune, même démontrée, ne prouve ni un propriétaire commun ni une information privilégiée.

## 1. Réponse

**Un seul groupe de comptes est relié par la chaîne : brace227, le wallet non nommé `0xa8e64a3c…74a5`, et dans une moindre mesure kraben006.** Sur les 55 paires des onze comptes, 1 a un transfert direct. Les autres n'ont en commun que des services nommés ou des hubs mesurés.

Cela corrige « 0 lien discriminant » de l'enquête d'origine et complète l'audit, qui avait trouvé le transfert vers kraben006 mais pas le second wallet.

## 2. Transferts directs entre adresses de dossiers différents

1 sur les historiques bruts lus : natif, internes et tous les ERC-20, spam compris, sur Ethereum, Polygon, Arbitrum et Optimism, plus Solana. La seule exécution de carnet entre deux dossiers (OuldLm3alem vers 0x86544e4dfde, `0x870eaa6c…`) n'est pas un transfert : c'est une exécution sur le marché.

| UTC | Chaîne | De | Vers | Montant | Transaction |
|---|---|---|---|---|---|
| 2026-10-04 13:54:35 | ethereum | brace227 `0xc852b093…af26` | kraben006 `0x101b5f4d…fb65` | 0.002048943671205553 ETH | `0xd07bea20a22d9381e0ab364e7a7421776318c6f4aa7258799638472ad7092b98` |

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

## 3. Adresses partagées, par classe

| Adresse | Chaîne | Nom | Classe | Nonce | Dossiers |
|---|---|---|---|---|---|
| `0xc011a7e1…2dfb` | polygon | Polymarket pUSD — CollateralToken Poly v2 | contrat Polymarket | 1 | 0x86544e4dfde, 0xdd97e6, cookedrice, OuldLm3alem, Thin-Disclaimer-Life, VidenteRibeira, WenZhuanBuPei |
| `0xf70da978…dbef` | polygon | Relay EVM solver | pont | 3307349 | 0x86544e4dfde, 0xdd97e6, cookedrice, OuldLm3alem, Thin-Disclaimer-Life, VidenteRibeira, WenZhuanBuPei |
| `0xf70da978…dbef` | ethereum | Relay EVM solver | pont | 5002707 | 0x86544e4dfde, 0xdd97e6, brace227, kraben006, walletwallet8424, Zoomman17 |
| `7uTT8Xi5RW…i8pZ` | solana | Relay Solana depository vault | pont | — | 0xdd97e6, cookedrice, OuldLm3alem, Thin-Disclaimer-Life, VidenteRibeira |
| `BmFdpraQhk…ymy6` | solana | KuCoin Hot Wallet 2 | plateforme | — | 0xdd97e6, cookedrice, OuldLm3alem, Thin-Disclaimer-Life, VidenteRibeira |
| `0x4cd00e38…bc31` | ethereum | Relay Depository | pont | 1 | brace227, kraben006, OuldLm3alem, Zoomman17 |
| `0x4cd00e38…bc31` | polygon | Relay Depository | pont | 1 | 0x86544e4dfde, walletwallet8424, WenZhuanBuPei |
| `0x74de5d4f…6631` | ethereum | MetaMask: Swaps Spender | routeur ou infrastructure de portefeuille | 1 | brace227, walletwallet8424, Zoomman17 |
| `0xb42f812a…ead6` | ethereum | Relayer of MetaMask-delegated transactions | routeur ou infrastructure de portefeuille | 852035 | 0x86544e4dfde, brace227, Zoomman17 |
| `0xc066ac5d…8b8c` | ethereum | MetaMask: Gas Station | routeur ou infrastructure de portefeuille | 853351 | brace227, walletwallet8424, Zoomman17 |
| `0xe3478b0b…1964` | ethereum | MetaMask: Gas Station Swap | routeur ou infrastructure de portefeuille | 475 | 0x86544e4dfde, brace227, Zoomman17 |
| `F7p3dFrjRT…gmNe` | solana | Relay Solana solver | pont | — | cookedrice, Thin-Disclaimer-Life, VidenteRibeira |
| `0x0ce9bdf3…f06d` | polygon | Circle SingleOwnerMSCA account of an unattributed custodial  | service dépositaire non attribué | 1 | 0x86544e4dfde, walletwallet8424 |
| `0x2cff890f…2680` | ethereum | NEAR Intents | pont | 1309625 | 0x86544e4dfde, brace227 |
| `0x58f298e3…0214` | ethereum | Payout wallet of an unattributed custodial service | service dépositaire non attribué | 114537 | kraben006, Zoomman17 |
| `0xa0c68c63…7c77` | ethereum | Polygon (Matic): Bridge | pont | 1 | 0x86544e4dfde, walletwallet8424 |
| `0xb01caea8…9c2e` | ethereum | MetaMask: Gas Station 2 | routeur ou infrastructure de portefeuille | 853880 | brace227, Zoomman17 |
| `0xb23360cc…c460` | ethereum | Revolut: Hot Wallet | plateforme | 4247692 | brace227, Zoomman17 |
| `0xc1d13492…a1b5` | ethereum | SwftSwap (SWFT Blockchain) | échange instantané | 1 | brace227, kraben006 |
| `0xc590175e…c02b` | polygon | Swap contract used through MetaMask delegation | routeur ou infrastructure de portefeuille | 1 | 0x86544e4dfde, walletwallet8424 |
| `0xdd3d72c5…ceee` | ethereum | ChangeNOW: Hot Wallet 3 | échange instantané | 1651726 | brace227, kraben006 |
| `0xe3478b0b…1964` | polygon | MetaMask: Gas Station Swap | routeur ou infrastructure de portefeuille | 10 | 0x86544e4dfde, walletwallet8424 |
| `GxjcMTWWDc…nvBW` | solana | Unidentified Solana custodial service (cosigns sweeps of its | service dépositaire non attribué | — | cookedrice, VidenteRibeira |

Aucune de ces lignes n'est un lien entre personnes : chacune est un service nommé, ou un hub mesuré.

**Adresse de taille personnelle partagée entre deux dossiers : aucune**, en dehors des deux clés du transfert direct ci-dessus.

## 4. Taux de base

Même lecteur sur 78 wallets témoins distincts, 77 lus, tous les dépôts lus depuis l'API avec pagination complète, et lignes illisibles retirées du dénominateur : fraiches_recensement 39, meme_token 8, non_surlignes 3, token_oppose 27. Les étiquettes sont réduites aux listes publiques, pour les nommés comme pour les témoins. Les 11 nommés passent par le même lecteur. Tirage et groupes repris de l'enquête d'origine. Exploratoire, sans correction pour tests multiples.

| Trait | Nommés | Tous témoins | p | Comptes frais | p |
|---|---|---|---|---|---|
| dépôt via VaultDepositooor (fun.xyz) | 5/11 | 9/77 | 0.013 | 5/39 | 0.030 |
| dépôt via adresse de pont 7702 | 6/11 | 59/77 | 0.968 | 34/39 | 0.996 |
| Relay sur le dépôt lu | 11/11 | 68/77 | 0.282 | 39/39 | 1.000 |
| origine Solana (Relay) | 3/11 | 6/68 | 0.106 | 3/39 | 0.111 |
| KuCoin Hot Wallet 2 avant le pont Solana | 3/3 | 1/6 | 0.048 | 0/3 | 0.050 |
| financement moins d'1 h avant le premier achat | 9/11 | 41/76 | 0.074 | 32/39 | 0.692 |
| clé reçoit d'une plateforme étiquetée | 2/11 | 5/54 | 0.338 | 2/39 | 0.206 |
| clé touche SwftSwap | 2/11 | 0/54 | 0.026 | 0/39 | 0.045 |
| clé reçoit de MetaMask Gas Station | 3/11 | 2/54 | 0.031 | 1/39 | 0.029 |

p : test exact unilatéral, nommés plus fréquents que témoins, non corrigé.

**Liens clé à clé, même lecture (Ethereum, Polygon, Arbitrum) :**

| Groupe | Clés | Paires | Transferts directs | Contreparties personnelles partagées |
|---|---|---|---|---|
| Nommés | 11 | 55 | 1 | 0 |
| Tous témoins | 54 | 1431 | 0 | 0 |
| Comptes frais | 39 | 741 | 0 | 0 |

Liens directs entre une clé nommée et une clé témoin : 0. Le lien brace227 et kraben006 sert de témoin positif : le lecteur le retrouve. Un seul témoin positif ne mesure pas la sensibilité de la méthode.

**Lecture.** Ces rapports décrivent des routes, pas une intention. Aucun trait ne passe un seuil corrigé pour 9 tests (0,0056). Les traits ont été choisis après coup, et le groupe par la presse.

- **Financement moins d'une heure avant le premier achat : rien de distinctif.** 9/11 contre 32/39 comptes frais, p = 0,69. Le 9/11 contre 10/43, p = 0,0006, publié d'abord par l'enquête, venait d'historiques tronqués et d'âges mêlés : l'audit l'avait déjà ramené à 10/22, et cette lecture complète le confirme.
- **Origine Solana et KuCoin : indice faible.** 3/11 contre 6/68, p = 0,11. KuCoin Hot Wallet 2 : 3/3 contre 1/6, sur très peu de lignes. Ce tableau lit un seul dépôt par wallet ; sur tous les dépôts, 5 comptes nommés sur 11 passent par cette étiquette, sans comparaison possible avec cette ligne.
- **`VaultDepositooor` : l'écart le plus net.** 5/11 contre 9/77, p = 0,013, et 5/39 chez les comptes frais, p = 0,030. Cela désigne un outil de dépôt, pas un lien entre personnes.
- **SwftSwap :** 2/11 contre 0/54, p = 0,026. Ces deux comptes sont brace227 et kraben006 : ce n'est pas un trait indépendant du lien déjà lu.
- **MetaMask Gas Station :** 3/11 contre 2/54, p = 0,031. Un logiciel de portefeuille, pas un lien.
- **Liens directs entre clés :** 1 sur 55 paires nommées, 0 sur 1 431 paires de témoins, dont 0 sur 741 chez les comptes frais. Ce n'est pas un test, les paires n'étant pas indépendantes. Mais un transfert direct entre clés n'est pas banal dans ces témoins.
- **Clés lues :** 54 clés témoins sur 77 wallets, les autres n'ayant pas de propriétaire lisible par `owner()`, souvent d'anciens proxys.

## 5. Délais et montants

- **Premier achat après le premier dépôt :** de 59 s à 607 s pour 9 comptes sur 11, 3,34 h pour VidenteRibeira et 8,88 h pour Thin-Disclaimer-Life. Ce délai n'a rien de distinctif face à des comptes du même âge, voir la section 4.
- **Calendrier :** les retraits principaux suivent la résolution du marché Kane, le 27 oct. à 01:57:41 UTC (relevé par la session parallèle), ou la vente qui l'a précédée. C'est le calendrier qui les rapproche.
- **Montants :** Thin-Disclaimer-Life et OuldLm3alem font des retraits de petite taille avant les gros (250 $ en SOL, 100 $ en BNB et en USDT). Un retrait d'essai et l'achat de gaz l'expliquent simplement. Aucun schéma de répartition commun, sauf le partage à parts égales de brace227.
- **Regroupements et circuits :** aucune sortie d'un dossier ne revient dans un autre dossier. La seule boucle lue reste interne : 2 500 USDC envoyés de `0x48ec106c…b12d` à `0x6a2522df…7973` et rendus le lendemain.
