# Dossier cookedrice

Généré depuis `cases/cookedrice.json`. Une adresse n'est pas une personne : aucune identité civile n'est établie ni recherchée, et rien ici ne prouve une information privilégiée.

## 1. Adresse et type

- Wallet Polymarket : `0x4060509c8c70cece529be4a089d6d66ad865b4d0`
- Type : DEPOSIT_WALLET. Propriétaire lu sur la chaîne : `0x6ec290051ea167cf564a4282c153351ab3fd876f`. C'est une clé, pas une personne.
- Lien étiquette vers adresse : nom exact et parts de la capture.
- Première activité 2026-10-14 19:58:36 UTC, dernière 2026-10-28 18:04:55 UTC, 31 lignes d'activité, historique complet.
- Nonce du propriétaire sur six chaînes : {'polygon': 0, 'ethereum': 0, 'bsc': 0, 'arbitrum': 0, 'base': 0, 'optimism': 0}. Aucune transaction envoyée par cette clé sur ces chaînes : elle signe hors chaîne.

## 2 et 3. Premier financement et source directe

Premier dépôt : 2026-10-14 19:58:36 UTC, 21 873,74 pUSD, transaction `0x9e1a809440c983f23ae834f92a6214198cfd15b65b4001e5739add05ea733012`. Le pUSD est frappé depuis l'adresse zéro : celle-ci n'est pas un financeur.
Source immédiate du collatéral : `0xd628c333015848b9c4e8c519f51a22642a555c58`.
- Dépôt `0x9e1a809440c9…` : `0xd628c333…5c58`, EIP7702_DELEGATED_EOA, nonce 1, 1 enregistrements au pont Polymarket.

## 4. Origines remontées, du plus ancien au dépôt

| Heure UTC | De | Vers | Chaîne | Montant | Niveau | Transaction |
|---|---|---|---|---:|---|---|
| 2026-10-14 19:58:12 | `BmFdpraQhk…ymy6` (KuCoin Hot Wallet 2) | `BJcZxhXFt2…JxFU` | Solana | 21 873,74 USDC | SERVICE_INTERACTION | `5dECJvXWiXgqWPoxUQCHEwPvozrArWL5uz6iPGFHHQj4HTBVZFs35iALL34rcgyvxUTUfrvedrzAbB9Fh4kSfjJX` |
| 2026-10-14 19:58:20 | `BJcZxhXFt2…JxFU` | `0xd628c333…5c58` | Solana | 21 873,74 USDC | PROTOCOL_CONFIRMED | `4ZWgBQaKB4G6YAEh7Kn2fk9QPzpJTGsxfDA3XDWjCDZw6g6aFiNLDk9PFg9wSd4Ze9osbwFPgdPfwbKEsde9AkXb` |
| 2026-10-14 19:58:36 | `0xd628c333…5c58` | `0x4060509c…b4d0` | Polygon | 21 873,74 USDC.e→pUSD | ONCHAIN_CONFIRMED | `0x9e1a809440c983f23ae834f92a6214198cfd15b65b4001e5739add05ea733012` |

**Où la trace s'arrête :**

- `BJcZxhXFt2PTDnMicxkq4hUTpRXZmYK6hpzVaQoJJxFU` : OFFCHAIN_RECORD_REQUIRED.  Financeur étiqueté : BmFdpraQhk…ymy6. Seul le service connaît le compte.

## 5 et 6. Paris et positions

| Marché | Issue | Achats $ | Parts achetées | Ventes $ | Rachats $ | Net de parts avant l'article |
|---|---|---:|---:|---:|---:|---:|
| Ballon d'Or 2026: Kylian Mbappé or Lamine Yamal to finish higher? | Mbappé | 16 996,75 | 32 001,91 | n/d | 32 001,91 | 32 001,91 |
| Ballon d'Or 2026: Rodri or Lionel Messi to finish higher? | Rodri | 4 895,19 | 7 150,56 | n/d | 7 150,56 | 7 150,56 |

Premier achat : 2026-10-14 20:01:01 UTC, 5 140,54 $, « Ballon d'Or 2026: Kylian Mbappé or Lamine Yamal to finish higher? », Mbappé, `0x9e13320290a38413fa03e10699ec2d4947dbfdf814f7edaf99545ea2c902bd48`.

**Historique daté** (31 lignes sur 31) :

| Heure UTC | Type | Marché | Issue | $ | Parts | Prix | Transaction |
|---|---|---|---|---:|---:|---:|---|
| 10-14 19:58:36 | DEPOSIT  |  |  | 21 873,74 | 21 873,74 |  | `0x9e1a809440c983f23ae834f92a6214198cfd15b65b4001e5739add05ea733012` |
| 10-14 20:01:01 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 5 140,54 | 9 921,71 | 0.5056115226 | `0x9e13320290a38413fa03e10699ec2d4947dbfdf814f7edaf99545ea2c902bd48` |
| 10-14 22:06:39 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 686,07 | 1 267,73 | 0.5287221254 | `0x9fb8ef267940011e7790b46a57f4917943922d0d5342f9b0a7f0268e4e8e0518` |
| 10-15 11:09:42 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 98,74 | 209,00 | 0.46 | `0x9e728a316e19997bcbc2c8ed1cac6838c75349f4f20396c7a4150edaa47c12c6` |
| 10-15 15:06:05 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 407,60 | 801,83 | 0.4958432585 | `0xb9bdca48e82b9bc2d8a956b42b4b6e402f5781738d1a04142eb40f8b462b14d6` |
| 10-15 18:21:59 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 1 379,38 | 2 882,74 | 0.4660523668 | `0xbcd09fdd45e8a32598e89cf2ddba5add72cfc5b5b6572e932ff05f3a7ad1e3ef` |
| 10-15 18:44:04 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 1 814,45 | 3 606,69 | 0.4905822513 | `0x37477aa335d0f6c21a1584eceeba22e0174b4ac4e346fdfa99414371f1ffa3f5` |
| 10-15 18:51:53 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 325,46 | 648,88 | 0.4890753298 | `0xbd1eaddb28dbe513cce44e9758b203104fa3dc02e8b80e13ba6f0b1a7975071d` |
| 10-15 20:13:43 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 100,00 | 200,00 | 0.5 | `0x23564aa4438f61a588e39db60d11fdf50061d89bdddd1f8324713afe00b67dac` |
| 10-15 20:35:05 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 8,62 | 17,25 | 0.5 | `0xfe8b28dfe788d825d664b57e5905e5c0a7267ae2a3feacf83dc68b3f373bad1c` |
| 10-15 21:11:47 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 4,00 | 8,00 | 0.5 | `0xfd9c362de5a651db461493bebe7bfd1d125da399b4ecd286cd5d5cbdf30a406d` |
| 10-15 21:26:38 | TRADE BUY | Ballon d'Or 2026: Rodri or Lionel Messi to fin | Rodri | 2 162,30 | 3 363,03 | 0.6313250253 | `0x54619474d95769f8345380a28cb231b86b6c555982360cc24bf85f24b00bc20e` |
| 10-15 22:32:36 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 1,00 | 2,00 | 0.5 | `0x9d261f5f923eae7517353911ca51e18361a42a639824db193ffd63e8c08bb0bb` |
| 10-16 07:10:04 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 936,38 | 1 872,75 | 0.5 | `0x5ec6d178faf35f7c2e3ef99ba4aec9e892515460bed5c3138e53091d9f976fa3` |
| 10-18 17:58:47 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 4 157,98 | 7 454,15 | 0.5454101809 | `0xed5e12dfca8ec218c9294aab042aa2ae4584cd68c15d722cb77dc75539714e4c` |
| 10-19 15:53:18 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 664,50 | 1 103,64 | 0.59 | `0x6006d63d4e6ccbd9cd995b2b44643354093248b105902351ba6cac9d90b4c552` |
| 10-19 15:54:06 | TRADE BUY | Ballon d'Or 2026: Rodri or Lionel Messi to fin | Rodri | 1 736,67 | 2 423,00 | 0.7063722658 | `0xc73207ae0e9561955870b9fbf8c74e045ba5701e08fbeac50bef2ba69404300c` |
| 10-19 16:27:50 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 118,98 | 201,66 | 0.5900000008 | `0xabd01d448c2abed60b3266fc14facf25bf7dc13a70ac3a953899be65c26d7576` |
| 10-19 17:31:41 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 382,20 | 647,80 | 0.5900000006 | `0x1a8bc7f52c83ead0429f1934fc26e626ac1ed5a67ef4b32e3abe03593c1a64d2` |
| 10-19 17:32:32 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 206,81 | 350,53 | 0.59 | `0x2c01678717c1ecf29d04e2b1f2ebd2bda9b58fd60e6d650302c7a82b5bf8bc9f` |
| 10-19 19:39:42 | TRADE BUY | Ballon d'Or 2026: Rodri or Lionel Messi to fin | Rodri | 996,22 | 1 364,53 | 0.72 | `0xeaa35ad153f0f500035656a6aa4e15e0486badcf9476890cf70dbd164dc76e67` |
| 10-19 22:46:59 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 564,05 | 805,55 | 0.6895034449 | `0x01be12354ac52b5b89bc4a59068a768de0bca83a077b05150de566ca009f51f0` |
| 10-27 01:05:15 | REDEEM  | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 32 001,91 | 32 001,91 |  | `0x125aee8279c00137877e4139ea0b9d952467140ca4e232a437b04d1b720bc4fa` |
| 10-27 01:10:20 | REDEEM  | Ballon d'Or 2026: Rodri or Lionel Messi to fin | Rodri | 7 150,56 | 7 150,56 |  | `0xa224d967e60fbcc14e9ee5ffd5db1e0e3b7c8882d658349b77a579df2d9d1af9` |
| 10-28 18:04:55 | WITHDRAWAL  |  |  | 39 158,78 | 39 158,78 |  | `0x32c1285b13708b90937e6af48e956c07148630916649d021f9047af08767f1ae` |

**Compte (API d'activité) :**

| Poste | $ |
|---|---:|
| DEPOSIT | 21 873,74 |
| TRADE_BUY | -21 891,94 |
| TAKER_REBATE | 18,82 |
| MAKER_REBATE | 5,69 |
| REDEEM | 39 152,47 |
| WITHDRAWAL | -39 158,78 |

Résidu du calcul : 0.0. Compte soldé : oui. **Retraits moins dépôts sur ce wallet : 17 285,05 $**, frais de transaction inclus, gas et coûts hors de ce wallet exclus.

## 7. Sorties et destinations

| Heure UTC | De | Vers | Chaîne | Montant reçu | Niveau | Transaction |
|---|---|---|---|---:|---|---|
| 2026-10-28 18:04:54 | `0x4060509c…b4d0` | `F7ew8r8X5YL3DPLtzg9Az3cPDKcVxXGjUpqgpskNh5Eh` | Solana | 39 158,63 USDC | PROTOCOL_CONFIRMED | `2wgkQdsKcoAKNPmCVt8JuKEXNwHJBvVLWVfXVKCfPkwn4nq69r2S5W1WG36XU3CcKKSETNwkidHcBUcC6unyGWa7` |
| 2026-10-28 18:04:56 | `F7ew8r8X5Y…h5Eh` | `GxjcMTWWDcKx5sxnHkNfPtuTSfV9cLgVkw3G7KvMnvBW` | Solana | 39 158,00 USDC | ONCHAIN_CONFIRMED | `5jAnEGy7ZFNQCkWBWNXSVwU8K6FqvBLCtPyAA2Ls9NoTa85uj7WLAVdUQPrmkdbHD9mF4i1nfCcbLmd53WhrtVkJ` |

**État des destinations à la lecture :**

- `F7ew8r8X5YL3DPLtzg9Az3cPDKcVxXGjUpqgpskNh5Eh` (Solana), lu le 2026-11-02 07:50:18 UTC : 3 transactions, historique complet, solde 0,00 SOL et 0,63 USDC. Sorties observées : 1.

## 8. ChangeNOW, FixedFloat, exchanges, XMR

- Services étiquetés touchés : KuCoin Hot Wallet 2.
- ChangeNOW ou FixedFloat : aucune interaction sur les sauts lus. Liste étiquetée incomplète : absence de preuve, pas preuve d absence.
- XMR : aucun échange XMR observé sur les sauts lus, donc aucun statut `XMR_VISIBILITY_BOUNDARY` à ce stade.

## 9. Liens avec les autres wallets

Lecture : un service commun ne relie personne. Détail et méthode : `reports/liens_entre_wallets.md`.

- Service étiqueté ou adresse à très fort nonce partagé : KuCoin Hot Wallet 2, aussi avec 0xdd97e6, ouldlm3alem, thin, vidente.
- Service non identifié partagé : `GxjcMTWWDcKx5sxnHkNfPtuTSfV9cLgVkw3G7KvMnvBW`, aussi avec vidente. Mesure : About 1.2 transactions a minute; of 120 transactions read, 18 token inflows, 95 outflows, 67 receivers; of 400 sampled, 73 inflows, median 270 $, 2 at 10,000 $ or more.
- Transfert direct de fonds vers ou depuis un autre dossier : aucun sur Polygon et Ethereum, stablecoins et pUSD, du 25 sept. au 2 nov. (`graphs/direct_transfers.json`).

## 10. Niveau de preuve par relation

6 relations à identifiant stable dans `graphs/relations.jsonl`.
- ONCHAIN_CONFIRMED : 3
- PROTOCOL_CONFIRMED : 2
- SERVICE_INTERACTION : 1
