# Sorties de ChangeNOW et rapprochements

Lu le 2 novembre 2026. Montants exacts et preuves : `data/verified_transfers.csv`.

## Résultat

| Type de correspondance | Nombre |
|---|---|
| **Documentée par un identifiant d'ordre** | **0** |
| Entrée et sortie d'une même opération reliées (niveau 4) | **0** |
| Paiement du service vers une adresse du dossier, prouvé sur la chaîne, sans ordre (niveau 2) | 12 |
| Rapprochement par montant et date retenu comme preuve | **0, volontairement** |

Les 12 sont : 2 vers la clé de kraben006, 9 vers `0x3eaef6d5…`, 1 vers `0xcc0f311e…`. `data/verified_transfers.csv` compte 18 lignes de niveau 2 : ces 12, plus les 5 paiements du service à d'autres destinataires de la clé (section dédiée et `0x66d582e5…`), plus le balayage entrant `0x22710b5e691160746fd4e054346daf18c91e98532999c1bd3bd9067340fe9c26`.

## kraben006 : les 834,85 USDC

| UTC | Montant | Transaction | Solde USDC après |
|---|---|---|---|
| 2026-02-23 15:56:23 | + 654,466304 | `0x5e8b57210b722dbf0f7395cbe20c57a3e578d2897bb4ff8d4c5e853387789219` | 775,543107 |
| 2026-02-23 16:04:35 | + 180,382489 | `0x472c85a3cd9df3bbdf9b5fac9ee812326646b1b40c832278fb42107554c0cd80` | 955,925596 |
| 2026-02-23 16:09:11 | **− 955** vers `0x66d582e5…` | `0x26808b939b7340e6e11ffc7c4a8ab3932b1bb01bb46c620edf6ffb26760aab61` | **0,925596** |
| 2026-02-23 17:06:11 | + 49,17571 de `0xcad97616…` | `0x4f7bf1ca04123f5d7c0c7ee4ed54dcc6618b160f6b407edd8dfbf2b57e821fa9` | 50,101306 |
| 2026-02-23 21:47:23 | **− 40** vers `0x66d582e5…` | `0xf0c56738c9280ff39aed8c6043d5d2409c3b4e8ffd140972eb5c518f79fe0516` | 10,101306 |
| 2026-03-07 03:38:35 | − 6,490649 | `0xf2a54e357a14db0737c9f73eae51e7f0e3826783a5e83f5570acb446b035c5b4` | 3,610657 |

Cette comptabilité ne garde que le vrai contrat USDC. Les lignes usurpant ce nom, 11 sur l'ensemble de la clé, ressemblent à de l'empoisonnement d'adresse. **Le solde recalculé à la fin, 15 154,826661 USDC, est exactement celui lu par flow-trace.**

**Conséquences :**

- **Actif source inconnu.** La clé n'avait que 121,076803 USDC avant ces paiements et n'a rien envoyé de comparable. L'entrée de l'ordre vient d'ailleurs, sur une chaîne inconnue.
- **Un ou deux ordres : inconnu.** 9 destinataires sur 57 dans la même fenêtre reçoivent deux paiements à moins de 10 minutes.
- **Aucun chemin documenté vers les paris.** 12 min 48 s après le premier paiement et 276 s après le second, 955 USDC repartent, 220 jours avant le premier dépôt du compte (2026-10-01). Il reste au plus 0,925596 USDC. Le dépôt du 1er octobre, 191,58343 USDC, puise 2,610648 USDC dans l'ancien solde : ce reliquat peut y passer, selon la convention.
- **Limite de ce raisonnement :** seuls les soldes de la clé sont établis. Les fonds entrent sur un compte de plateforme, où l'argent devient indistinct. Les dépôts d'octobre viennent de SwftSwap et de quatre adresses sans étiquette à fort trafic, `0x58f298e3…`, `0xbd1f4462…`, `0x0c58909d…` et `0x7bef1627…`, dont je n'ai pas analysé l'amont, et je n'ai pas lu les sorties de `0xa03400e0…`. **Un retour par ce compte, par un service ou par une chaîne non lue n'est ni observé ni exclu.**

## L'aval : `0x66d582e5e0670bd99153199f179733c6ee5d19be`

**Nouveau par rapport aux rapports existants. Aucune étiquette sur cette adresse.**

- **Comportement d'une adresse de dépôt de plateforme :** ses 44 sorties de stablecoins vont toutes à `0xa03400e098f4421b34a3a44a1b4e571419517687`, « HTX: Hot Wallet », « HTX 52 » sur Blockscout, HTX aussi dans la copie AMLBot. Sortie en 72 s pour les 955 USDC : `0x7ef5aa477f06fd17d17b21d395d0dccffef86c750b76a2ae0c58978817561853` à 16:10:23.
- **Plusieurs payeurs :** 26 expéditeurs de stablecoins sur 53 entrées. Parmi ses contreparties : Revolut 6, Binance 15 et Binance: Hot Wallet 34. Ne ressemble pas à un portefeuille personnel fermé.
- **Elle reçoit aussi du service :** 297,933091 USDC de `0xdd3d72c5…` le 2026-03-28 20:01:23, `0xc48360e906e9c1267c986ddc477b3c34f9af1d7b5df1aaa0119fa48f26091491`.
- **Active du 26 janvier au 28 mai 2026.** Les wallets Polymarket dérivés de cette adresse n'ont aucune activité, selon le test de flow-trace (fichier d'état, RAPPORTÉ).

**Lecture à ne pas dépasser :** cela suggère qu'un compte HTX reçoit des sorties de ChangeNOW. Rien ne dit que ce compte appartient à celui qui contrôle la clé. Une adresse de dépôt peut être payée par n'importe qui.

## Sortie de l'entrée du 4 octobre : non trouvée

| Vérification | Résultat |
|---|---|
| Entrée sur la clé dans les 48 h suivantes | Aucune. La suivante, 542,06 USDC de `0x7bef1627…` le 7 oct. 00:18:59, n'a rien de comparable |
| Paiement d'une adresse étiquetée ChangeNOW vers une des 108 adresses, après le 4 octobre | **0** sur les 4 chaînes lues, hors portefeuilles de service entre eux (`0x4778480c…` paie `0x3f3ee0a9…` le 31 octobre) |
| Actif et chaîne de sortie | Inconnus. Peut-être hors des chaînes lues, ou vers une adresse non étudiée |
| `0xdd3d72c5…` en octobre | Presque éteinte depuis le 10 août : aucune ligne USDC ou USDT dans les fenêtres autour de l'envoi |

**La trace s'arrête ici. Je ne propose aucun candidat par rapprochement.** Autour de l'envoi, 4 sorties de `0x3f3ee0a9…` sur 530 tombent à 5 % près du montant, et 10 à 10 % près : une correspondance par hasard est attendue environ une fois par heure.

## brace227 : un intermédiaire

Tous les paiements du service à `0x3eaef6d5e91ecf7b7623eb19978e145ebd417013`, et ce qui suit :

| UTC | Reçu du service | Transaction | Sortie suivante | Destinataire |
|---|---|---|---|---|
| 2024-12-12 01:55:59 | 113,10656 USDT | `0x9a689d98d5b8125b068122eab02a327c1909526ca9750fe2b5af282fc22fe14f` | 105,46567 USDT, 11 min après | `0x39d3e955…` |
| 2024-12-12 02:06:23 | 0,00230371 ETH | `0x005a4e48a74c4b088dd10166d900c11af55814db37284365bc04fd28621ff7fc` | | |
| 2024-12-16 23:41:59 | 20,512191 USDT | `0xb20bd2538db66c44d709174bdba6d29180673c5b20a4530737a3bcedb6fd29de` | 27,001929 USDT, 7 min après | `0xc7e1bb9f…` |
| 2024-12-17 01:35:59 | 26,86673 USDT | `0x3452693a1a6623b334cc548560ea66a214ce7c52770db2882c8ab717152696e0` | 26,985654 USDT, 40 min après | `0x36f779cf…` |
| 2024-12-17 02:14:47 | 0,0076965 ETH | `0x33b619fee777c198b71afda8822c149a3f0f5d5550be1466a2252119f690ca47` | | |
| **2025-01-04 02:01:47** | **290,286195 USDT** | `0xd0df7496375ecc9bb5dfb7e5aa8831053986a2a600734181afcf94f255ecd2d5` | **291,317423 USDT, 84 s après** | **Clé de brace227** |
| 2025-01-12 19:23:59 | 23,251534 USDT | `0x614729b208672ba1eceefa2cc6394f982667ca90b30e36bc54ddb5f075202cb7` | 23 USDT, 9 min après | `0xf79867de…` |
| 2025-04-28 12:28:47 | 31,286059 USDT | `0x608978a349223d6fd692e721d40cbbd371e05971cdaa5bed8cafd9ac95aec417` | 30,43 USDT, 1 min après | `0xb39e194c…` |
| 2025-04-28 15:32:11 | 5,185042 USDT | `0xfd0b34b7ff592c3f5d2da6fd3960bb8a4ffa43b04fc4875e7babf7c5e2d8cfc1` | 6 USDT, le 2 mai | `0xaecad942…` |

La transaction vers la clé est `0xf64e9d194769bdcad0682063984db82e7add22c752e28bbc1f597cdc02a7b3ff` (`data/verified_transfers.csv`). Total reçu : **510,494311 USDT et 0,01000021 ETH, uniquement de ce service.** Ses 9 sorties vont à 9 destinataires différents.

- **Lecture compatible :** portefeuille de paiement ou de gré à gré, qui se recharge chez ChangeNOW et paie des tiers, dont la clé de brace227 une fois. **Ce n'est pas démontré.**
- **Sort des fonds sur la clé :** 285 USDT repartent 3 minutes après vers `0x6b33c41c…` (`0x1a6beb1e35dff0ed1fd6a30bea5f7e31f5342fcd7a7e4bf175b323143e26cf5a`), une adresse que la clé avait déjà payée en décembre 2024. Elle les envoie 18 min 36 s plus tard à `0xebaba1d6…` (`0xfd2453398eabe36a86a8d47d000f72f8d904b3a3a68f7afab42242abf4540e86`), non suivie au-delà. Les 6,317423 USDT restants partent vers Bridgers le 28 avril 2025 (`0x5ed83ab3429fd89f767d05cc1f07ee3c17ac8f155dcb23f37d473c4f4b9eaaab`). **Solde USDT à 0 ce jour-là.**
- **Aucun lien financier documenté avec les paris :** premier dépôt Polymarket le 2026-10-09. Un retour par `0xebaba1d6…`, par Bridgers ou par BSC, où la clé a un nonce de 109, n'est ni observé ni exclu (`data/unresolved_paths.csv`, U5 et U6).

## Autres paiements du service à des adresses proches d'un dossier

Trouvés au second saut. **Aucun n'est un lien.** Ces adresses sont destinataires de la clé de kraben006 pour de petits montants, et elles sont aussi clientes du service, ou passent par un prestataire.

| UTC | De | Vers | Montant | Transaction | Reçu de la clé de kraben006 |
|---|---|---|---|---|---|
| 2025-12-05 22:14:47 | `0xdd3d72c5…` | `0x1086c953…` | 140,34 USDC | `0x71f08f49ae9755b5de8df1872de87344c0f09c1051b8644459580194f7e31f0f` | 10 USDC. Adresse qui reverse à Cryptomus |
| 2026-01-06 18:23:23 | `0xdd3d72c5…` | `0xe52b6693…` | 102,634647 USDC | `0x9f917782958ece42021dafc6af43c7bf24a737a2f8be8fdb8380569383d20412` | 25,591964 USDC |
| 2026-03-18 14:44:11 | `0xeba88149…` | `0xe52b6693…` | 0,0199247 ETH | `0x30d7b06ac6611cf29b831aaa6a1609c6fb1b77d8a749cd55d5dfe2b4057bee5a` | idem |
| 2026-08-10 05:54:11 | `0xeba88149…` | `0x50e3a360…` | 0,01848109 ETH | `0x2ef2fc2669c0cfbede1bd69ea652ba28a8e12e576f8c0e34d6dc315d14bee9c8` | 60,919122 USDC |

Sur les 8 destinataires de la clé de kraben006 jamais lus avant cette étude, 4 ont aussi reçu de ce service, en comptant `0x66d582e5…`. **Je n'ai pas mesuré si c'est inhabituel :** ce service a des centaines de milliers de clients probables. C'est une piste, pas une conclusion.

## Rapprochement avec Polymarket

| Compte | Fonds ChangeNOW reçus | Premier dépôt Polymarket | Chemin documenté vers un dépôt ? |
|---|---|---|---|
| kraben006 | 834,848793 USDC, 2026-02-23 | 2026-10-01 | **Aucun.** Partis 12 min 48 s et 276 s après les paiements, reste au plus 0,925596 USDC |
| brace227 | Indirect : 291,317423 USDT, 2025-01-04 | 2026-10-09 | **Aucun.** Solde USDT à 0 dès le 2025-04-28 |
| walletwallet8424 | Aucun : 0,00476548 ETH à un financeur mutualisé | 2026-10-10 | Aucun, ETH sur une adresse de 672 contreparties |
| Les 8 autres | Aucun lu | | |

**Aucun dépôt Polymarket n'est relié à un paiement ChangeNOW par un chemin documenté.**

<!-- adresses -->
## Adresses citées en forme courte

| Adresse complète | Étiquette publique lue |
|---|---|
| `0x0c58909d3bbca91c4a5c3acbe0a72b57312d270d` | Voir `data/changenow_candidates.csv` ou aucune |
| `0x1086c953cea1280c1afc87713a614dc464f7d7f7` | Voir `data/changenow_candidates.csv` ou aucune |
| `0x36f779cff510c39defa36c4f04cbd6f24d9b2582` | Voir `data/changenow_candidates.csv` ou aucune |
| `0x39d3e955eb77b19843ce25871976f28aef595aaf` | Voir `data/changenow_candidates.csv` ou aucune |
| `0x3eaef6d5e91ecf7b7623eb19978e145ebd417013` | Voir `data/changenow_candidates.csv` ou aucune |
| `0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b` | ChangeNOW Dep: 0x3f3...07B |
| `0x4778480c6c46521c41f7e4f2318f884b157cb1c9` | ChangeNow (0x4778) |
| `0x50e3a360ba9bc0accfbc216e0544bfe53d49ba12` | Voir `data/changenow_candidates.csv` ou aucune |
| `0x58f298e3bf930886ab7639f4d71f892d5f1f0214` | Voir `data/changenow_candidates.csv` ou aucune |
| `0x66d582e5e0670bd99153199f179733c6ee5d19be` | Voir `data/changenow_candidates.csv` ou aucune |
| `0x6b33c41cac7db6726dd1240bc8bbce5e6dbb2180` | Voir `data/changenow_candidates.csv` ou aucune |
| `0x7bef16275a88bd9c3004dbd0b85da65b08705c24` | Voir `data/changenow_candidates.csv` ou aucune |
| `0xa03400e098f4421b34a3a44a1b4e571419517687` | HTX: Hot Wallet, HTX 52 |
| `0xaecad9423549d3804d6fede0c17b089df9110d9d` | Voir `data/changenow_candidates.csv` ou aucune |
| `0xb39e194cb405854023a55e31c37ac5fcd1efac37` | Voir `data/changenow_candidates.csv` ou aucune |
| `0xbd1f44622d8a2480546e72afb90696ae4fc7eb3b` | Voir `data/changenow_candidates.csv` ou aucune |
| `0xc7e1bb9fda33dd39ea8cbd8e1eddfec4f74f5e8d` | Voir `data/changenow_candidates.csv` ou aucune |
| `0xcad97616f91872c02ba3553db315db4015cbe850` | Voir `data/changenow_candidates.csv` ou aucune |
| `0xcc0f311eb2c688f30bc9aadb42781e46899723f7` | Voir `data/changenow_candidates.csv` ou aucune |
| `0xdd3d72c53ff982ff59853da71158bf1538b3ceee` | ChangeNOW: Hot Wallet 3 |
| `0xe52b6693fa225adf73fd2a36b1799bc66f3327bb` | Voir `data/changenow_candidates.csv` ou aucune |
| `0xeba88149813bec1cccccfdb0dacefaaa5de94cb1` | ChangeNOW: Hot Wallet 4, ChangeNOW 16 |
| `0xebaba1d649be1e293a8a9e37b0f59f166b025d1f` | Voir `data/changenow_candidates.csv` ou aucune |
| `0xf79867de8fcc618eb3ad8eb35d79abd56153972e` | Voir `data/changenow_candidates.csv` ou aucune |
<!-- fin adresses -->
