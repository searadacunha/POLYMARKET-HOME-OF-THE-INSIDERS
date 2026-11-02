# Dossier Thin-Disclaimer-Life

Généré depuis `cases/thin.json`. Une adresse n'est pas une personne : aucune identité civile n'est établie ni recherchée, et rien ici ne prouve une information privilégiée.

## 1. Adresse et type

- Wallet Polymarket : `0x8d3319c51520518ad01f6744486ceea29f376f5b`
- Type : DEPOSIT_WALLET. Propriétaire lu sur la chaîne : `0x1bf0b469f7f3612657e99bf785e470eee2a76028`. C'est une clé, pas une personne.
- Lien étiquette vers adresse : nom exact et parts de la capture.
- Première activité 2026-10-11 15:23:31 UTC, dernière 2026-10-27 01:29:03 UTC, 73 lignes d'activité, historique complet.
- Nonce du propriétaire sur six chaînes : {'polygon': 0, 'ethereum': 0, 'bsc': 0, 'arbitrum': 0, 'base': 0, 'optimism': 0}. Aucune transaction envoyée par cette clé sur ces chaînes : elle signe hors chaîne.

## 2 et 3. Premier financement et source directe

Premier dépôt : 2026-10-11 15:23:31 UTC, 11 833,23 pUSD, transaction `0x761f6058829482bc5fc66acd8b6d5bcc583e96a463ac75e52d666b31fd6f32d1`. Le pUSD est frappé depuis l'adresse zéro : celle-ci n'est pas un financeur.
Source immédiate du collatéral : `0x8e43af995577339436e071990e524ebfe6c09865`.
- Dépôt `0x761f60588294…` : `0x8e43af99…9865`, EIP7702_DELEGATED_EOA, nonce 1, 5 enregistrements au pont Polymarket.
- Dépôt `0x1e2c6576867d…` : `0x8e43af99…9865`, EIP7702_DELEGATED_EOA, nonce 1, 5 enregistrements au pont Polymarket.
- Dépôt `0x975d526512ae…` : `0x8e43af99…9865`, EIP7702_DELEGATED_EOA, nonce 1, 5 enregistrements au pont Polymarket.

## 4. Origines remontées, du plus ancien au dépôt

| Heure UTC | De | Vers | Chaîne | Montant | Niveau | Transaction |
|---|---|---|---|---:|---|---|
| 2026-10-11 15:23:10 | `BmFdpraQhk…ymy6` (KuCoin Hot Wallet 2) | `EMu2EAWjzP…Mqsd` | Solana | 11 833,23 USDC | SERVICE_INTERACTION | `3bn5hJNsXAx814rxWrHrHUPqY5C53NF3sSH4CfH8uhk19ExDFUrNAcE6g73oj5Vmcwc6NTBcD7wpJ8pmdLHnJR2t` |
| 2026-10-11 15:23:17 | `EMu2EAWjzP…Mqsd` | `0x8e43af99…9865` | Solana | 11 833,23 USDC | PROTOCOL_CONFIRMED | `3tqC6ccwrcS7a7Lfm4k3tkJZN9iTDsGSzY2gP4FY8T1g21tkLMto7DJnXEGhUpGDmqeaCb16VqJ5GkzKiHypwRyW` |
| 2026-10-11 15:23:31 | `0x8e43af99…9865` | `0x8d3319c5…6f5b` | Polygon | 11 833,23 USDC.e→pUSD | ONCHAIN_CONFIRMED | `0x761f6058829482bc5fc66acd8b6d5bcc583e96a463ac75e52d666b31fd6f32d1` |
| 2026-10-13 13:46:53 | `0x8894e0a0…d4e3` | `0x8e43af99…9865` | BSC | 11 946,00 USDC | ONCHAIN_CONFIRMED | `0x23e2219c3e902360004a3f893ac3560649617a0ac372ff9aa9d218f0ad442ff3` |
| 2026-10-13 13:47:06 | `0x8e43af99…9865` | `0x8e43af99…9865` | BSC | 11 946,00 USDC | PROTOCOL_CONFIRMED | `0x92f86b5a04511bfe30aff0c7193aee4c1ea0247dad3740f7fd6669cac99593f2` |
| 2026-10-13 13:47:23 | `0x8e43af99…9865` | `0x8d3319c5…6f5b` | Polygon | 11 946,00 USDC.e→pUSD | ONCHAIN_CONFIRMED | `0x1e2c6576867d250de440e43b97bc01fd456952c30b1c6811fa0665cbf216a2f6` |
| 2026-10-13 18:36:40 | `0x8894e0a0…d4e3` | `0x8e43af99…9865` | BSC | 21 900,00 USDC | ONCHAIN_CONFIRMED | `0x3d90c0a34035a1efa225a2bf308f412e738e10eb4d1c9c2201e51bed202c37a7` |
| 2026-10-13 18:36:55 | `0x8e43af99…9865` | `0x8e43af99…9865` | BSC | 21 900,00 USDC | PROTOCOL_CONFIRMED | `0xaed0d982e0d0c9c907393cd2de73ed10319e95cb677fbcdae8475c44925c37c1` |
| 2026-10-13 18:37:10 | `0x8e43af99…9865` | `0x8d3319c5…6f5b` | Polygon | 21 900,00 USDC.e→pUSD | ONCHAIN_CONFIRMED | `0x975d526512ae2b0af5dc50b05af0b409b8686dfe9a522409483342bccc084aec` |

**Où la trace s'arrête :**

- `EMu2EAWjzPB9UyarEiXFg9igRiBxpjDtB4omaPTDMqsd` : OFFCHAIN_RECORD_REQUIRED.  Financeur étiqueté : BmFdpraQhk…ymy6. Seul le service connaît le compte.
- `0x8894e0a0c962cb723c1976a4421c95949be2d4e3` (BSC) : nonce 58 893 846. Un tel volume désigne une adresse mutualisée, probablement un hot wallet de service, pas un portefeuille personnel. Aucune étiquette vérifiée.

## 5 et 6. Paris et positions

| Marché | Issue | Achats $ | Parts achetées | Ventes $ | Rachats $ | Net de parts avant l'article |
|---|---|---:|---:|---:|---:|---:|
| Ballon d'Or 2026: Kylian Mbappé or Lamine Yamal to finish higher? | Mbappé | 43 490,72 | 76 082,65 | n/d | 76 082,65 | 76 082,65 |
| Ballon d'Or 2026: Rodri or Lionel Messi to finish higher? | Rodri | 2 182,42 | 3 916,35 | n/d | 3 916,35 | 3 916,35 |
| Will Yui Hasegawa finish in the top 10 of the 2026 Women's Ballon d'Or? | No | 110,71 | 302,53 | 121,10 | n/d | 0,00 |
| Will Yui Hasegawa finish in the top 10 of the 2026 Women's Ballon d'Or? | Yes | 74,47 | 150,00 | 53,06 | n/d | 0,00 |

Premier achat : 2026-10-12 00:16:03 UTC, 891,87 $, « Ballon d'Or 2026: Kylian Mbappé or Lamine Yamal to finish higher? », Mbappé, `0xf5424b77e7c4413b16be5e4f4304938743c0d12edfafb06bf7cfa0d6a8167e99`.

**Historique daté** (73 lignes sur 73) :

| Heure UTC | Type | Marché | Issue | $ | Parts | Prix | Transaction |
|---|---|---|---|---:|---:|---:|---|
| 10-11 15:23:31 | DEPOSIT  |  |  | 11 833,23 | 11 833,23 |  | `0x761f6058829482bc5fc66acd8b6d5bcc583e96a463ac75e52d666b31fd6f32d1` |
| 10-12 00:16:03 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 891,87 | 1 651,08 | 0.5277124064 | `0xf5424b77e7c4413b16be5e4f4304938743c0d12edfafb06bf7cfa0d6a8167e99` |
| 10-12 00:23:51 | TRADE BUY | Will Yui Hasegawa finish in the top 10 of the  | No | 110,71 | 302,53 | 0.3544990579 | `0x24ac20da7b4e06b8db0a0242295a0bf3730ae16fc45084689b8f4bb638ad8a3a` |
| 10-12 00:24:59 | TRADE BUY | Ballon d'Or 2026: Rodri or Lionel Messi to fin | Rodri | 246,62 | 486,22 | 0.4947114475 | `0x6ab917075513fe46fb9f8f9ccdadcf6d1f35f3dd2aa15bed56016402b3ba1f21` |
| 10-12 00:51:05 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 540,10 | 982,00 | 0.55 | `0xdce857b1049230272cd578068c18d4ef96fecdb2cc777c323f120e94562a8302` |
| 10-12 01:14:41 | TRADE BUY | Ballon d'Or 2026: Rodri or Lionel Messi to fin | Rodri | 399,84 | 784,00 | 0.51 | `0xe00ed2b851e23eb933c314141e079dd3e1d4780e3dd03a57cca1f7583c95b2dc` |
| 10-12 08:09:49 | TRADE BUY | Ballon d'Or 2026: Rodri or Lionel Messi to fin | Rodri | 1,00 | 2,00 | 0.5 | `0x86905c9a879d6443a60148ef58d3c8b4e9510c8a46011b3c9de975cd1c72c9ad` |
| 10-12 08:14:11 | TRADE BUY | Ballon d'Or 2026: Rodri or Lionel Messi to fin | Rodri | 1,00 | 2,00 | 0.5 | `0x8bedc5eb8bd1d3b43a6beebe72f56cabc6e279759148430319c63c048762c69a` |
| 10-12 08:23:10 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 8,00 | 16,00 | 0.5 | `0x335fa2fca2f0fcf1aaad1287429838ad5baa5a956c54f673bc72919913978096` |
| 10-12 10:51:27 | TRADE BUY | Ballon d'Or 2026: Rodri or Lionel Messi to fin | Rodri | 25,00 | 50,00 | 0.5 | `0x579cf8f8e7dc2a897150d615c1754c729fa8baacb3e15a3b67288c91cde61774` |
| 10-12 11:32:47 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 50,00 | 100,00 | 0.5 | `0x9410c5c16c6bb20a98342a2e19274e054fad85afc3c45a9fc1b3579b7bf5d2b8` |
| 10-12 12:00:26 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 994,39 | 1 729,09 | 0.5627890972 | `0x547a3c40ba0eead22f697ce65a1eb9b11a2098211059e822e89e878c0b0d33d6` |
| 10-12 12:00:45 | TRADE BUY | Ballon d'Or 2026: Rodri or Lionel Messi to fin | Rodri | 628,59 | 1 173,63 | 0.5231227048 | `0x122ea102bc2934f155096e07b469d498453afe6d1c747b6d950b3a91da3b4283` |
| 10-12 12:10:18 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 639,81 | 1 120,00 | 0.5589285714 | `0x8c18b8103348bcd812e974d827328bf34e3d380af5438fd1537e4b25c1b5a5b4` |
| 10-12 15:19:51 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 424,50 | 849,00 | 0.5 | `0xbf7d43e5e69370c0aae71744670a67dc02b888217c9c2d4f4010d34a904ce540` |
| 10-12 18:13:47 | TRADE BUY | Ballon d'Or 2026: Rodri or Lionel Messi to fin | Rodri | 880,38 | 1 418,50 | 0.6087310539 | `0x7e76a5640e8d305e120db90df1b4bee210a5382c3de1a33bdb7375cc2b6d91f1` |
| 10-12 18:14:05 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 998,97 | 1 769,55 | 0.5521690825 | `0x90919b81d18bfc1ca1ba3ed64d7ee025498090729f68cd3e5adac078fffb37df` |
| 10-12 18:38:45 | TRADE BUY | Will Yui Hasegawa finish in the top 10 of the  | Yes | 74,47 | 150,00 | 0.484 | `0xde34bdce3309318ff0af444a0a986575b056da570d7842a0cf29f2d1f5f51acc` |
| 10-12 18:42:47 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 818,54 | 1 411,99 | 0.5674362425 | `0x15b4e30b4184f7430fa438e33001841c8c56e9ae744f8c6e56cf332531e8fd49` |
| 10-12 19:33:50 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 567,70 | 975,00 | 0.57 | `0x6a1d52766746f424993c94f410317ef119df3acb90deb192a56c68f92d608f14` |
| 10-12 21:29:41 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 330,00 | 600,00 | 0.55 | `0x6c2f72904111cc7a51d98d2069d06de9e572792110eedc4fa31f717759f3772c` |
| 10-12 21:30:53 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 9,35 | 17,00 | 0.55 | `0xdda31e7f1371b664b8cf93b56021c27e4327d3739464d3a43dee9c41cc2ce993` |
| 10-12 22:30:17 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 1 578,74 | 2 578,09 | 0.6003723687 | `0xf457e94c7cc604ea9762251297845d63beebe810dec819f1ca930ee99264df41` |
| 10-13 11:38:56 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 715,94 | 1 363,03 | 0.5127623016 | `0x22e92956c0917377e057f0ecb56bd06611c0eea467fbc52ca1a0ddfcafb6b44f` |
| 10-13 11:39:28 | TRADE SELL | Will Yui Hasegawa finish in the top 10 of the  | Yes | 40,34 | 85,40 | 0.4848477752 | `0xc63c43ccf91d4bb952c8f1a07f82faeeacde56b0d527e1639be646d45c52b717` |
| 10-13 11:39:53 | TRADE SELL | Will Yui Hasegawa finish in the top 10 of the  | Yes | 12,72 | 64,60 | 0.2050154799 | `0x894bd997558c6521b9a0ade46c05adacdd4cb24da4efa29ecdc62264bb4788c7` |
| 10-13 11:40:44 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 138,86 | 264,22 | 0.5130697903 | `0xf454b1e71741a18f370845f06718f97485665c81958aa80a604b83b21070aa4b` |
| 10-13 11:42:58 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 48,50 | 92,83 | 0.51 | `0x25e2c158a8f7bd23695c4ee56ae7d71e492f1057c8a47dff3d2d660c20cf6f4d` |
| 10-13 11:43:05 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 48,50 | 92,83 | 0.51 | `0xdb3b5245f9a8d08aaf96cbb5a5aca1f5b6b0a7ed3b5cd393557d6cc1984b8f92` |
| 10-13 11:43:16 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 203,78 | 390,01 | 0.51 | `0xbe15049e8640022e3c9a2290d66a037cf0f99a6e51ca1471aad5798d59ab4249` |
| 10-13 12:03:43 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 73,42 | 137,88 | 0.52 | `0xab85b7ea7355002fd7c00a715718ef402cd6907df75e33f758c174661e5ec9c3` |
| 10-13 13:47:23 | DEPOSIT  |  |  | 11 946,00 | 11 946,00 |  | `0x1e2c6576867d250de440e43b97bc01fd456952c30b1c6811fa0665cbf216a2f6` |
| 10-13 13:47:43 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 2 330,11 | 3 945,39 | 0.5783979277 | `0x0bbff55608bed318a09e904408d8cc1c1ced3813a951fe1fb2eb6c8578046d74` |
| 10-13 13:48:11 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 88,30 | 149,11 | 0.58 | `0x82bfc2682411b9f41182723f6ecfbbfb6a7ebdca522a38397a8d3cd1a0e4843c` |
| 10-13 13:48:35 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 1 135,47 | 1 797,25 | 0.62 | `0xf16b49841a740b5098f082384c603291a28c1a313739208433d35db68cf43b54` |
| 10-13 13:56:10 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 273,02 | 450,00 | 0.5946666667 | `0x9cba6b74844471dbcd0e1203e481b006fe8a6dbd929aad44471ba0a58a5602ce` |
| 10-13 14:26:14 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 176,20 | 291,00 | 0.5934364261 | `0x291eae3862e20220d379da347dd8bfb9092941f19c5b0c2a8598cbd82f9ac769` |
| 10-13 14:47:29 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 1 066,76 | 1 722,39 | 0.6074241606 | `0xb15b8d324ff38844634fc90fe813025f7684836be51f06d7a051718126ec99c4` |
| 10-13 14:47:37 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 18,36 | 30,00 | 0.6 | `0xe7cd5d6817cee40b3b6a2445102d47656d546cd350da4cf74a84e8009106c0cf` |
| 10-13 15:34:58 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 743,75 | 1 322,25 | 0.550116695 | `0x661019cd8882593d3d59ad2c20f37946788dc29b244676345b3539e30563ebb3` |
| 10-13 15:36:16 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 253,21 | 440,00 | 0.5631818182 | `0xd48412b9963850023a98316e2c3487f728ab08d1157a20a3bf41616750ba9013` |
| 10-13 16:55:33 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 33,89 | 63,64 | 0.52 | `0x50efa1d1db32bb66083acbf37ab97814d0494e4ef3416f52de063af55cbfb216` |
| 10-13 17:11:07 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 304,91 | 586,36 | 0.52 | `0x77249de2325be9c891726ee291cd9fbc8e703ee18e8425b7d989313a234e712b` |
| 10-13 17:18:37 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 442,00 | 850,00 | 0.52 | `0x3c4bc3584c436b4534e20419300b83bb3dc151f96bc3d332fa81df8f06fe76f8` |
| 10-13 17:33:22 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 2 835,00 | 5 043,29 | 0.5497560521 | `0xbfb68e8eda292574e2d945c6f58e3aba7dff8d9a9a25030b37f7745ef2f6b53f` |
| 10-13 17:33:39 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 53,26 | 106,00 | 0.49 | `0xb51281b12ffea307c0a1db7a49172e6ef77a36aa923ed6e2ea7d489b380d8ef7` |
| 10-13 17:37:58 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 3,28 | 7,12 | 0.4600000028 | `0x49542570f30e75335a350265e0ce11c986c204770c90b7ba92c793301a0d9513` |
| 10-13 17:47:52 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 2 592,07 | 4 662,29 | 0.5435596027 | `0xb1eeb8174af42ba533a073cfb7827f34b95cbec4765e268f260ea3f4bc1c063b` |
| 10-13 17:48:30 | TRADE SELL | Will Yui Hasegawa finish in the top 10 of the  | No | 121,10 | 302,53 | 0.4124192642 | `0xd6e48ef5ecfcc82b7980f60f88ab927b2119d8dc5ffef8d44ecb8ca5ff47d1b0` |
| 10-13 17:48:55 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 55,38 | 106,00 | 0.51 | `0x3a0cc0369159243ffe44467336bbd07749286647402d3c9708e97aee73d746e8` |
| 10-13 18:10:15 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 103,42 | 210,00 | 0.48 | `0x8d65fa5d989c12791d3ab521aa66ce56bf08595035326480a11312760f1ca815` |
| 10-13 18:37:10 | DEPOSIT  |  |  | 21 900,00 | 21 900,00 |  | `0x975d526512ae2b0af5dc50b05af0b409b8686dfe9a522409483342bccc084aec` |
| 10-13 18:48:52 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 197,16 | 392,36 | 0.49 | `0x19b06b9683593c8fdcfd8e364727ebc5de349c4233b398d1fb564e77a7064a03` |
| 10-13 18:50:00 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 15 053,97 | 25 474,05 | 0.5787631806 | `0x8dc10176ab3741ade3881689296c6ab459029bb176f5a18fe37cb4185b02c4a3` |
| 10-13 19:34:13 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 305,97 | 544,57 | 0.5494806912 | `0x543d4d16466324fa0716e61fe27f7fe8ba439b291732e4445193b0663335258d` |
| 10-13 20:03:43 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 276,20 | 499,99 | 0.54 | `0x7e8626862f01e9b83ed8ef557a5971dd221ab551fbf76360f07df9ffec74ee88` |
| 10-13 22:18:07 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 1 118,71 | 1 966,90 | 0.5564263562 | `0xc9190d6968635f170964db42b5f4f606245e86191430bc8efb4914cf39192211` |
| 10-14 14:21:45 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 243,25 | 511,71 | 0.4629313478 | `0x29658dc3bf67c07cc3ce6be83c85492723aac34f80d8de60f02eacafa8e73191` |
| 10-14 14:22:03 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 550,19 | 1 098,91 | 0.4881800147 | `0xa38250e3fdaa5fd9273080dbffcab7d12cc53267d05a87735041034708de3360` |
| 10-14 14:23:27 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 1 597,44 | 3 000,00 | 0.52 | `0x0f4ca85a732dcaeaa55fcb3ea72407e3d687f87e740c3f9571cc8a827c8c8c39` |
| 10-14 14:33:24 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 2 558,47 | 4 672,47 | 0.5351246771 | `0x43fbc51cfdaf9f09c72a673d13fa0b51ed3e98d2d29a589c8f028420090b658c` |
| 10-27 01:21:51 | REDEEM  | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 76 082,65 | 76 082,65 |  | `0xf4257fa4bf3572715912bd74b4b4cef60a6ba7a4c4f109dc43d3717a33df5c07` |
| 10-27 01:22:00 | REDEEM  | Ballon d'Or 2026: Rodri or Lionel Messi to fin | Rodri | 3 916,35 | 3 916,35 |  | `0x50499e6d60aca26cf158f512d9f04d11dc72e6d52e1e6bdd451a0286f6d64280` |
| 10-27 01:24:26 | WITHDRAWAL  |  |  | 250,00 | 250,00 |  | `0x6373a98fb86f82e1562448ccddf261d537a06a7112180f1d414e3f0968d9be7c` |
| 10-27 01:27:32 | WITHDRAWAL  |  |  | 40 000,00 | 40 000,00 |  | `0xa41a56f185a14d413f23839a94f0e92574dbf72a46b132dde1984f44d88b288e` |
| 10-27 01:28:14 | WITHDRAWAL  |  |  | 250,00 | 250,00 |  | `0xe35ea7f316355dc91347aa2f409aa030bb696035151a5ea5d8d72a69d11df989` |
| 10-27 01:29:03 | WITHDRAWAL  |  |  | 39 537,93 | 39 537,93 |  | `0x5c4d9506a42a1ecb190233847a7baea1f967766873218d042c714fb00bf31b90` |

**Compte (API d'activité) :**

| Poste | $ |
|---|---:|
| DEPOSIT | 45 679,23 |
| TRADE_BUY | -45 858,33 |
| REWARD | 2,25 |
| MAKER_REBATE | 9,05 |
| TRADE_SELL | 174,16 |
| TAKER_REBATE | 32,55 |
| REDEEM | 79 999,00 |
| WITHDRAWAL | -80 037,93 |

Résidu du calcul : 0.0. Compte soldé : oui. **Retraits moins dépôts sur ce wallet : 34 358,70 $**, frais de transaction inclus, gas et coûts hors de ce wallet exclus.

## 7. Sorties et destinations

| Heure UTC | De | Vers | Chaîne | Montant reçu | Niveau | Transaction |
|---|---|---|---|---:|---|---|
| 2026-10-27 01:24:25 | `0x8d3319c5…6f5b` | `CXVYMP5qxBENTNnqqmBAgvQB5wRLkcUBYPBDLFTeGrfJ` | Solana | 2,47 SOL | PROTOCOL_CONFIRMED | `3hB2wsiT2GhpJ9k3wajsJTsxpS28HbSuZySnW61RJy5zeVtHqzSakELK66xzrzWGkZ87xZ6Xr8MKoG9SKfBTrY89` |
| 2026-10-27 01:27:31 | `0x8d3319c5…6f5b` | `CXVYMP5qxBENTNnqqmBAgvQB5wRLkcUBYPBDLFTeGrfJ` | Solana | 39 999,85 USDC | PROTOCOL_CONFIRMED | `rwiu1FRYMBHqQTiXVdqCssrSs8YQZY2my7fLdNXvrBWDG8V4QckoRoirN3WGeSM6sY3XxC7ERwg486zHmLZEsEd` |
| 2026-10-27 01:28:13 | `0x8d3319c5…6f5b` | `EnHRjTP4pKGkA4BC1yfoCNyUJcU3wapK1Gj8Us35PZ8B` | Solana | 2,47 SOL | PROTOCOL_CONFIRMED | `2UzjMVyoNhLo2tpSeLqGsqBByBjr8Y74LMmvYyuaNbExtF25TCtU29xCKuk372H9SA2K9VLx12sfoqT1eFSgvGW3` |
| 2026-10-27 01:29:02 | `0x8d3319c5…6f5b` | `EnHRjTP4pKGkA4BC1yfoCNyUJcU3wapK1Gj8Us35PZ8B` | Solana | 39 537,78 USDC | PROTOCOL_CONFIRMED | `4HRAyjtxWPQ4Dn4yGAr9Hr5uXp4hMyKmiHUonaLosSPjYpT1z2VAFkeyGLk4Es6urGkauByp6Cbs4RFU4opdhk5o` |

**État des destinations à la lecture :**

- `CXVYMP5qxBENTNnqqmBAgvQB5wRLkcUBYPBDLFTeGrfJ` (Solana), lu le 2026-11-02 07:49:19 UTC : 2 transactions, historique complet, solde 2,47 SOL et 39 999,85 USDC. Sorties observées : 0.
- `EnHRjTP4pKGkA4BC1yfoCNyUJcU3wapK1Gj8Us35PZ8B` (Solana), lu le 2026-11-02 07:49:23 UTC : 2 transactions, historique complet, solde 2,47 SOL et 39 537,78 USDC. Sorties observées : 0.

## 8. ChangeNOW, FixedFloat, exchanges, XMR

- Services étiquetés touchés : KuCoin Hot Wallet 2.
- ChangeNOW ou FixedFloat : aucune interaction sur les sauts lus. Liste étiquetée incomplète : absence de preuve, pas preuve d absence.
- XMR : aucun échange XMR observé sur les sauts lus, donc aucun statut `XMR_VISIBILITY_BOUNDARY` à ce stade.

## 9. Liens avec les autres wallets

Lecture : un service commun ne relie personne. Détail et méthode : `reports/liens_entre_wallets.md`.

- Service étiqueté ou adresse à très fort nonce partagé : KuCoin Hot Wallet 2, aussi avec 0xdd97e6, cookedrice, ouldlm3alem, vidente.
- Transfert direct de fonds vers ou depuis un autre dossier : aucun sur Polygon et Ethereum, stablecoins et pUSD, du 25 sept. au 2 nov. (`graphs/direct_transfers.json`). Périmètre élargi après audit : voir l'addendum.

## 10. Niveau de preuve par relation

14 relations à identifiant stable dans `graphs/relations.jsonl`.
- PROTOCOL_CONFIRMED : 7
- ONCHAIN_CONFIRMED : 6
- SERVICE_INTERACTION : 1

## Addendum après audit, 02/11/2026

Ce dossier est celui du 2 nov. 08:18 UTC, conservé dans `archive/20261102_avant_amendement_audit/cases/`. Corrections : `reports/AMENDEMENT_AUDIT_2026-11-02.md`.

- Le 13 oct., 15 053,97 $ sont achetés à 18:50:00 UTC, dont 14 743,44 $ en flux taker, 60 s avant la date D2 du plan, qui ne justifie pas cette heure.
- E6 : le rang de financement publié sur 42 lignes contient des lignes coupées. Rang corrigé sur 20 comparateurs à historique complet : 10 font aussi court ou plus court. KuCoin n'est plus un indice : taux de base invalide, 53 comparateurs sur 83 inutilisables. Absence d'autre lien : sur un périmètre relu, non exhaustif, sans témoin positif de propriété commune.
