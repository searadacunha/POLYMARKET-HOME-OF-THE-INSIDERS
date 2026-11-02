# Transactions utilisées au premier signal Thin

Projection documentaire de `derived/validation.json.gz`, scénario0. Montants/prix/temps rapportés par la Data API, reçus le30octobre ; les38 transactions ne sont pas toutes rapprochées ici de reçus blockchain. Les frais sont absents. Le regroupement du noyau donne38 groupes pour38 lignes. Aucun montant ne constitue un capital net, un profit ou une liquidité.

Les noms de marchés et des issues proviennent du catalogue collecté après événement, uniquement pour lire le tableau : ils n’entrent pas dans le score. Source `../ballon_2026_20261030/data/catalog_refreshed.json`, SHA256 fc7e7b11fb3e973a484b984387a91f962b06f96231635d8904b64572d1d1ccbe. Liquidité/profondeur observable au13octobre : **INCONNUE** pour tous ces marchés.

| Marché | Question | Issues (identités reconstruites) |
|---|---|---|
| 5140129 | Will Yui Hasegawa finish in the top 10 of the 2026 Women's Ballon d'Or? | ["Yes", "No"] |
| 5141816 | Ballon d'Or 2026: Kylian Mbappé or Lamine Yamal to finish higher? | ["Mbappé", "Yamal"] |
| 5141856 | Ballon d'Or 2026: Rodri or Lionel Messi to finish higher? | ["Rodri", "Messi"] |

Les tokens complets, condition_id, trade_id et observed_at réel sont conservés dans la sortie JSON et dans `data/replay_input.jsonl.gz`. Le tableau ci-dessous donne tous les hashes, sans arrondir les données source archivées.

| UTC transaction | Marché / issue | Sens | Quantité | Prix exécuté rapporté | Nominal brut | Rôle | Transaction |
|---|---|---|---:|---:|---:|---|---|
| 2026-10-12 00:16:03 | 5141816 / Mbappé | BUY | 1651.08000000 | 0.5277124064 | 871.295400 | baseline BUY | [0xf5424b77e7…](https://polygonscan.com/tx/0xf5424b77e7c4413b16be5e4f4304938743c0d12edfafb06bf7cfa0d6a8167e99) |
| 2026-10-12 00:23:51 | 5140129 / No | BUY | 302.53000000 | 0.3544990579 | 107.246600 | baseline BUY | [0x24ac20da7b…](https://polygonscan.com/tx/0x24ac20da7b4e06b8db0a0242295a0bf3730ae16fc45084689b8f4bb638ad8a3a) |
| 2026-10-12 00:24:59 | 5141856 / Rodri | BUY | 486.22000000 | 0.4947114475 | 240.538600 | baseline BUY | [0x6ab9170755…](https://polygonscan.com/tx/0x6ab917075513fe46fb9f8f9ccdadcf6d1f35f3dd2aa15bed56016402b3ba1f21) |
| 2026-10-12 12:00:26 | 5141816 / Mbappé | BUY | 1729.09000000 | 0.5627890972 | 973.113000 | baseline BUY | [0x547a3c40ba…](https://polygonscan.com/tx/0x547a3c40ba0eead22f697ce65a1eb9b11a2098211059e822e89e878c0b0d33d6) |
| 2026-10-12 12:00:45 | 5141856 / Rodri | BUY | 1173.63000000 | 0.5231227048 | 613.952500 | baseline BUY | [0x122ea102bc…](https://polygonscan.com/tx/0x122ea102bc2934f155096e07b469d498453afe6d1c747b6d950b3a91da3b4283) |
| 2026-10-12 12:10:18 | 5141816 / Mbappé | BUY | 1120.00000000 | 0.5589285714 | 626.000000 | baseline BUY | [0x8c18b81033…](https://polygonscan.com/tx/0x8c18b8103348bcd812e974d827328bf34e3d380af5438fd1537e4b25c1b5a5b4) |
| 2026-10-12 18:13:47 | 5141856 / Rodri | BUY | 1418.50000000 | 0.6087310539 | 863.485000 | baseline BUY | [0x7e76a5640e…](https://polygonscan.com/tx/0x7e76a5640e8d305e120db90df1b4bee210a5382c3de1a33bdb7375cc2b6d91f1) |
| 2026-10-12 18:14:05 | 5141816 / Mbappé | BUY | 1769.55000000 | 0.5521690825 | 977.090800 | baseline BUY | [0x90919b81d1…](https://polygonscan.com/tx/0x90919b81d18bfc1ca1ba3ed64d7ee025498090729f68cd3e5adac078fffb37df) |
| 2026-10-12 18:38:45 | 5140129 / Yes | BUY | 150.00000000 | 0.4840000000 | 72.600000 | baseline BUY | [0xde34bdce33…](https://polygonscan.com/tx/0xde34bdce3309318ff0af444a0a986575b056da570d7842a0cf29f2d1f5f51acc) |
| 2026-10-12 18:42:47 | 5141816 / Mbappé | BUY | 1411.99000000 | 0.5674362425 | 801.214300 | baseline BUY | [0x15b4e30b41…](https://polygonscan.com/tx/0x15b4e30b4184f7430fa438e33001841c8c56e9ae744f8c6e56cf332531e8fd49) |
| 2026-10-12 19:33:50 | 5141816 / Mbappé | BUY | 975.00000000 | 0.5700000000 | 555.750000 | baseline BUY ; concentration24h | [0x6a1d527667…](https://polygonscan.com/tx/0x6a1d52766746f424993c94f410317ef119df3acb90deb192a56c68f92d608f14) |
| 2026-10-12 22:30:17 | 5141816 / Mbappé | BUY | 2578.09000000 | 0.6003723687 | 1547.814000 | baseline BUY ; concentration24h | [0xf457e94c7c…](https://polygonscan.com/tx/0xf457e94c7cc604ea9762251297845d63beebe810dec819f1ca930ee99264df41) |
| 2026-10-13 11:38:56 | 5141816 / Mbappé | BUY | 1363.03000000 | 0.5127623016 | 698.910400 | baseline BUY ; concentration24h | [0x22e92956c0…](https://polygonscan.com/tx/0x22e92956c0917377e057f0ecb56bd06611c0eea467fbc52ca1a0ddfcafb6b44f) |
| 2026-10-13 11:39:28 | 5140129 / Yes | SELL | 85.40000000 | 0.4848477752 | 41.406000 | contexte SELL | [0xc63c43ccf9…](https://polygonscan.com/tx/0xc63c43ccf91d4bb952c8f1a07f82faeeacde56b0d527e1639be646d45c52b717) |
| 2026-10-13 11:39:53 | 5140129 / Yes | SELL | 64.60000000 | 0.2050154799 | 13.244000 | contexte SELL | [0x894bd99755…](https://polygonscan.com/tx/0x894bd997558c6521b9a0ade46c05adacdd4cb24da4efa29ecdc62264bb4788c7) |
| 2026-10-13 11:40:44 | 5141816 / Mbappé | BUY | 264.22000000 | 0.5130697903 | 135.563300 | baseline BUY ; concentration24h | [0xf454b1e717…](https://polygonscan.com/tx/0xf454b1e71741a18f370845f06718f97485665c81958aa80a604b83b21070aa4b) |
| 2026-10-13 11:42:58 | 5141816 / Mbappé | BUY | 92.83000000 | 0.5100000000 | 47.343300 | baseline BUY ; concentration24h | [0x25e2c158a8…](https://polygonscan.com/tx/0x25e2c158a8f7bd23695c4ee56ae7d71e492f1057c8a47dff3d2d660c20cf6f4d) |
| 2026-10-13 11:43:05 | 5141816 / Mbappé | BUY | 92.83000000 | 0.5100000000 | 47.343300 | baseline BUY ; concentration24h | [0xdb3b5245f9…](https://polygonscan.com/tx/0xdb3b5245f9a8d08aaf96cbb5a5aca1f5b6b0a7ed3b5cd393557d6cc1984b8f92) |
| 2026-10-13 11:43:16 | 5141816 / Mbappé | BUY | 390.01000000 | 0.5100000000 | 198.905100 | baseline BUY ; concentration24h | [0xbe15049e86…](https://polygonscan.com/tx/0xbe15049e8640022e3c9a2290d66a037cf0f99a6e51ca1471aad5798d59ab4249) |
| 2026-10-13 12:03:43 | 5141816 / Mbappé | BUY | 137.88000000 | 0.5200000000 | 71.697600 | baseline BUY ; concentration24h | [0xab85b7ea73…](https://polygonscan.com/tx/0xab85b7ea7355002fd7c00a715718ef402cd6907df75e33f758c174661e5ec9c3) |
| 2026-10-13 13:47:43 | 5141816 / Mbappé | BUY | 3945.39000000 | 0.5783979277 | 2282.005400 | baseline BUY ; concentration24h | [0x0bbff55608…](https://polygonscan.com/tx/0x0bbff55608bed318a09e904408d8cc1c1ced3813a951fe1fb2eb6c8578046d74) |
| 2026-10-13 13:48:11 | 5141816 / Mbappé | BUY | 149.11000000 | 0.5800000000 | 86.483800 | baseline BUY ; concentration24h | [0x82bfc26824…](https://polygonscan.com/tx/0x82bfc2682411b9f41182723f6ecfbbfb6a7ebdca522a38397a8d3cd1a0e4843c) |
| 2026-10-13 13:48:35 | 5141816 / Mbappé | BUY | 1797.25000000 | 0.6200000000 | 1114.295000 | baseline BUY ; concentration24h | [0xf16b49841a…](https://polygonscan.com/tx/0xf16b49841a740b5098f082384c603291a28c1a313739208433d35db68cf43b54) |
| 2026-10-13 13:56:10 | 5141816 / Mbappé | BUY | 450.00000000 | 0.5946666667 | 267.600000 | baseline BUY ; concentration24h | [0x9cba6b7484…](https://polygonscan.com/tx/0x9cba6b74844471dbcd0e1203e481b006fe8a6dbd929aad44471ba0a58a5602ce) |
| 2026-10-13 14:26:14 | 5141816 / Mbappé | BUY | 291.00000000 | 0.5934364261 | 172.690000 | baseline BUY ; concentration24h | [0x291eae3862…](https://polygonscan.com/tx/0x291eae3862e20220d379da347dd8bfb9092941f19c5b0c2a8598cbd82f9ac769) |
| 2026-10-13 14:47:29 | 5141816 / Mbappé | BUY | 1722.39000000 | 0.6074241606 | 1046.221300 | baseline BUY ; concentration24h | [0xb15b8d324f…](https://polygonscan.com/tx/0xb15b8d324ff38844634fc90fe813025f7684836be51f06d7a051718126ec99c4) |
| 2026-10-13 14:47:37 | 5141816 / Mbappé | BUY | 30.00000000 | 0.6000000000 | 18.000000 | baseline BUY ; concentration24h | [0xe7cd5d6817…](https://polygonscan.com/tx/0xe7cd5d6817cee40b3b6a2445102d47656d546cd350da4cf74a84e8009106c0cf) |
| 2026-10-13 15:34:58 | 5141816 / Mbappé | BUY | 1322.25000000 | 0.5501166950 | 727.391800 | baseline BUY ; concentration24h | [0x661019cd88…](https://polygonscan.com/tx/0x661019cd8882593d3d59ad2c20f37946788dc29b244676345b3539e30563ebb3) |
| 2026-10-13 15:36:16 | 5141816 / Mbappé | BUY | 440.00000000 | 0.5631818182 | 247.800000 | baseline BUY ; concentration24h | [0xd48412b996…](https://polygonscan.com/tx/0xd48412b9963850023a98316e2c3487f728ab08d1157a20a3bf41616750ba9013) |
| 2026-10-13 16:55:33 | 5141816 / Mbappé | BUY | 63.64000000 | 0.5200000000 | 33.092800 | baseline BUY ; concentration24h | [0x50efa1d1db…](https://polygonscan.com/tx/0x50efa1d1db32bb66083acbf37ab97814d0494e4ef3416f52de063af55cbfb216) |
| 2026-10-13 17:33:22 | 5141816 / Mbappé | BUY | 5043.29000000 | 0.5497560521 | 2772.579200 | baseline BUY ; concentration24h | [0xbfb68e8eda…](https://polygonscan.com/tx/0xbfb68e8eda292574e2d945c6f58e3aba7dff8d9a9a25030b37f7745ef2f6b53f) |
| 2026-10-13 17:33:39 | 5141816 / Mbappé | BUY | 106.00000000 | 0.4900000000 | 51.940000 | baseline BUY ; concentration24h | [0xb51281b12f…](https://polygonscan.com/tx/0xb51281b12ffea307c0a1db7a49172e6ef77a36aa923ed6e2ea7d489b380d8ef7) |
| 2026-10-13 17:47:52 | 5141816 / Mbappé | BUY | 4662.29000000 | 0.5435596027 | 2534.232500 | baseline BUY ; concentration24h | [0xb1eeb8174a…](https://polygonscan.com/tx/0xb1eeb8174af42ba533a073cfb7827f34b95cbec4765e268f260ea3f4bc1c063b) |
| 2026-10-13 17:48:30 | 5140129 / No | SELL | 302.53000000 | 0.4124192642 | 124.769200 | contexte SELL | [0xd6e48ef5ec…](https://polygonscan.com/tx/0xd6e48ef5ecfcc82b7980f60f88ab927b2119d8dc5ffef8d44ecb8ca5ff47d1b0) |
| 2026-10-13 17:48:55 | 5141816 / Mbappé | BUY | 106.00000000 | 0.5100000000 | 54.060000 | baseline BUY ; concentration24h | [0x3a0cc03691…](https://polygonscan.com/tx/0x3a0cc0369159243ffe44467336bbd07749286647402d3c9708e97aee73d746e8) |
| 2026-10-13 18:10:15 | 5141816 / Mbappé | BUY | 210.00000000 | 0.4800000000 | 100.800000 | baseline BUY ; concentration24h | [0x8d65fa5d98…](https://polygonscan.com/tx/0x8d65fa5d989c12791d3ab521aa66ce56bf08595035326480a11312760f1ca815) |
| 2026-10-13 18:48:52 | 5141816 / Mbappé | BUY | 392.36000000 | 0.4900000000 | 192.256400 | baseline BUY ; concentration24h | [0x19b06b9683…](https://polygonscan.com/tx/0x19b06b9683593c8fdcfd8e364727ebc5de349c4233b398d1fb564e77a7064a03) |
| 2026-10-13 18:50:00 | 5141816 / Mbappé | BUY | 25474.05000000 | 0.5787631806 | 14743.442201 | déclencheur taille ; concentration24h | [0x8dc10176ab…](https://polygonscan.com/tx/0x8dc10176ab3741ade3881689296c6ab459029bb176f5a18fe37cb4185b02c4a3) |

Dates effectives de collecte des lignes cible : 2026-10-30 10:45:38 à 2026-10-30 10:46:20 UTC. Leur date économique n'établit pas leur visibilité via API le13octobre.
