# Dossier VidenteRibeira

Généré depuis `cases/vidente.json`. Une adresse n'est pas une personne : aucune identité civile n'est établie ni recherchée, et rien ici ne prouve une information privilégiée.

## 1. Adresse et type

- Wallet Polymarket : `0x5f8b30fde56bd2d2f3853769602330aeb9f1866a`
- Type : DEPOSIT_WALLET. Propriétaire lu sur la chaîne : `0x3cb3f4f6b1a81bdf523e36b7f5fa5081113f0f5e`. C'est une clé, pas une personne.
- Lien étiquette vers adresse : nom exact et parts de la capture.
- Première activité 2026-10-15 21:06:54 UTC, dernière 2026-10-27 16:51:53 UTC, 13 lignes d'activité, historique complet.
- Nonce du propriétaire sur six chaînes : {'polygon': 0, 'ethereum': 0, 'bsc': 0, 'arbitrum': 0, 'base': 0, 'optimism': 0}. Aucune transaction envoyée par cette clé sur ces chaînes : elle signe hors chaîne.

## 2 et 3. Premier financement et source directe

Premier dépôt : 2026-10-15 21:06:54 UTC, 9 940,01 pUSD, transaction `0xcb790208996b569b3671f4d5090acae8ca22eff2a3cec6029b8aeee2081aa2d1`. Le pUSD est frappé depuis l'adresse zéro : celle-ci n'est pas un financeur.
Source immédiate du collatéral : `0x6d24d9452f900f3307cd5b791ffaf1d1a7476df8`.
- Dépôt `0xcb790208996b…` : `0x6d24d945…6df8`, EIP7702_DELEGATED_EOA, nonce 1, 2 enregistrements au pont Polymarket.
- Dépôt `0xd2297a703dce…` : `0x6d24d945…6df8`, EIP7702_DELEGATED_EOA, nonce 1, 2 enregistrements au pont Polymarket.

## 4. Origines remontées, du plus ancien au dépôt

| Heure UTC | De | Vers | Chaîne | Montant | Niveau | Transaction |
|---|---|---|---|---:|---|---|
| 2026-10-15 21:06:33 | `BmFdpraQhk…ymy6` (KuCoin Hot Wallet 2) | `5xHWduZuzC…uz1a` | Solana | 9 940,01 USDC | SERVICE_INTERACTION | `622wDP15doVfkbQf8CG7LgFr7aihdS7L4vHb8NQKpmLruMkka7efttqRuhnh2TZ1bWPDPAaCjszS5Y6tdzsQFL28` |
| 2026-10-15 21:06:41 | `5xHWduZuzC…uz1a` | `0x6d24d945…6df8` | Solana | 9 940,01 USDC | PROTOCOL_CONFIRMED | `uqknnPyKXoxmBx9tce4HhJPmVR7onV6QsWaaWgNbP8QTS7qEzPGXNYdANSTn48ezukGsK6EBwsqMuVdJbgQrYrL` |
| 2026-10-15 21:06:54 | `0x6d24d945…6df8` | `0x5f8b30fd…866a` | Polygon | 9 940,01 USDC.e→pUSD | ONCHAIN_CONFIRMED | `0xcb790208996b569b3671f4d5090acae8ca22eff2a3cec6029b8aeee2081aa2d1` |
| 2026-10-16 20:32:51 | `5xHWduZuzC…uz1a` | `0x6d24d945…6df8` | Solana | 18 089,95 USDC | PROTOCOL_CONFIRMED | `5v2gVH3xD6HE5fCuo7bb4zp65466guDNJSvVxiZie6D9b2CBWcAUgurcCp1mtXZrsQ7xAvLnfUYBMDrngtyMZHKq` |
| 2026-10-16 20:33:05 | `0x6d24d945…6df8` | `0x5f8b30fd…866a` | Polygon | 18 089,95 USDC.e→pUSD | ONCHAIN_CONFIRMED | `0xd2297a703dce632821afdf1ad1ab71ccc5f0b0113b64a429939a83777423b9a7` |

**Où la trace s'arrête :**

- `5xHWduZuzCoKV91jeaEh8Et5txNim3aFR8jP4veQuz1a` : OFFCHAIN_RECORD_REQUIRED.  Financeur étiqueté : BmFdpraQhk…ymy6. Seul le service connaît le compte.
- `5xHWduZuzCoKV91jeaEh8Et5txNim3aFR8jP4veQuz1a` : OFFCHAIN_RECORD_REQUIRED.  Financeur étiqueté : BmFdpraQhk…ymy6. Seul le service connaît le compte.

## 5 et 6. Paris et positions

| Marché | Issue | Achats $ | Parts achetées | Ventes $ | Rachats $ | Net de parts avant l'article |
|---|---|---:|---:|---:|---:|---:|
| Ballon d'Or 2026: Kylian Mbappé or Lamine Yamal to finish higher? | Mbappé | 27 884,23 | 51 345,66 | n/d | 51 345,66 | 51 345,66 |

Premier achat : 2026-10-16 00:27:24 UTC, 3 458,93 $, « Ballon d'Or 2026: Kylian Mbappé or Lamine Yamal to finish higher? », Mbappé, `0x76b9f0c980716eadaef62144e3bfe598c34c3415b2384a020916c635a5178979`.

**Historique daté** (13 lignes sur 13) :

| Heure UTC | Type | Marché | Issue | $ | Parts | Prix | Transaction |
|---|---|---|---|---:|---:|---:|---|
| 10-15 21:06:54 | DEPOSIT  |  |  | 9 940,01 | 9 940,01 |  | `0xcb790208996b569b3671f4d5090acae8ca22eff2a3cec6029b8aeee2081aa2d1` |
| 10-16 00:27:24 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 3 458,93 | 6 383,99 | 0.5293563743 | `0x76b9f0c980716eadaef62144e3bfe598c34c3415b2384a020916c635a5178979` |
| 10-16 11:21:39 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 2 439,59 | 4 477,64 | 0.5323912597 | `0xf0bc933f56fd3fff7ff22c1c0d747d48e54a51b4b266176ecc40c433809c19a8` |
| 10-16 20:33:05 | DEPOSIT  |  |  | 18 089,95 | 18 089,95 |  | `0xd2297a703dce632821afdf1ad1ab71ccc5f0b0113b64a429939a83777423b9a7` |
| 10-16 20:38:47 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 9 697,20 | 17 762,31 | 0.533498447 | `0x87d0a485dd7d618271797fea1754472b5d018fb4bd03f59c6e1ba2400dc2d2fd` |
| 10-17 20:36:57 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 2 662,40 | 5 000,00 | 0.52 | `0x071846e1c7fb09cf7e67139e7c5bb63a57b80825ef8c64628306cd4b359f814d` |
| 10-17 20:44:23 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 2 253,87 | 4 397,79 | 0.5 | `0xdc1f1c09a8dda1c486a04b06171f2ddec87d14ad26066a3396494db5ee7a419b` |
| 10-18 10:34:44 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 7 372,24 | 13 323,93 | 0.5408917114 | `0x8311e0a0fb23b9b4f4d799f2833c90df14e0099304d6680ef8e7922850218bae` |
| 10-27 01:05:15 | REDEEM  | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 51 345,66 | 51 345,66 |  | `0x0b9768d113b099417a8504cdfb54f4ad2c4837923bde06677b5c28e4f3611f70` |
| 10-27 16:51:53 | WITHDRAWAL  |  |  | 51 509,88 | 51 509,88 |  | `0x650d76f3ef10b8e0001baf61693372fa8634ae29a29ae11f86589c064cf52e16` |

**Compte (API d'activité) :**

| Poste | $ |
|---|---:|
| DEPOSIT | 28 029,96 |
| TRADE_BUY | -27 884,23 |
| TAKER_REBATE | 18,48 |
| REDEEM | 51 345,66 |
| WITHDRAWAL | -51 509,88 |

Résidu du calcul : 0.0. Compte soldé : oui. **Retraits moins dépôts sur ce wallet : 23 479,92 $**, frais de transaction inclus, gas et coûts hors de ce wallet exclus.

## 7. Sorties et destinations

| Heure UTC | De | Vers | Chaîne | Montant reçu | Niveau | Transaction |
|---|---|---|---|---:|---|---|
| 2026-10-27 16:51:52 | `0x5f8b30fd…866a` | `DMmDPF9sFcNbq8dVKfxqZsKV4xKZBtsUZ4hXSwy1wt5T` | Solana | 51 489,09 USDT | PROTOCOL_CONFIRMED | `57XPE63Zvu53geF8C7saiFwDMjeZBimPBsyoD82kM72hPRMFBePmjcgSgz2vCsRmjLLUPe4u8RFTMdaCMzehQvTx` |
| 2026-10-27 16:51:56 | `DMmDPF9sFc…wt5T` | `GxjcMTWWDcKx5sxnHkNfPtuTSfV9cLgVkw3G7KvMnvBW` | Solana | 51 489,00 USDT | ONCHAIN_CONFIRMED | `2UCgkFYwUKGceXb1VXABUFTUZiNrwUgUh6vDPDr9ae2MN9SEFB8GqLikvoHueeuavaoQ3AQspG72L8fiwd78LQRq` |

**État des destinations à la lecture :**

- `DMmDPF9sFcNbq8dVKfxqZsKV4xKZBtsUZ4hXSwy1wt5T` (Solana), lu le 2026-11-02 07:49:58 UTC : 2 transactions, historique complet, solde 0,00 SOL et 0,09 USDT. Sorties observées : 1.

## 8. ChangeNOW, FixedFloat, exchanges, XMR

- Services étiquetés touchés : KuCoin Hot Wallet 2.
- ChangeNOW ou FixedFloat : aucune interaction sur les sauts lus. Liste étiquetée incomplète : absence de preuve, pas preuve d absence.
- XMR : aucun échange XMR observé sur les sauts lus, donc aucun statut `XMR_VISIBILITY_BOUNDARY` à ce stade.

## 9. Liens avec les autres wallets

Lecture : un service commun ne relie personne. Détail et méthode : `reports/liens_entre_wallets.md`.

- Service étiqueté ou adresse à très fort nonce partagé : KuCoin Hot Wallet 2, aussi avec 0xdd97e6, cookedrice, ouldlm3alem, thin.
- Service non identifié partagé : `GxjcMTWWDcKx5sxnHkNfPtuTSfV9cLgVkw3G7KvMnvBW`, aussi avec cookedrice. Mesure : About 1.2 transactions a minute; of 120 transactions read, 18 token inflows, 95 outflows, 67 receivers; of 400 sampled, 73 inflows, median 270 $, 2 at 10,000 $ or more.
- Transfert direct de fonds vers ou depuis un autre dossier : aucun sur Polygon et Ethereum, stablecoins et pUSD, du 25 sept. au 2 nov. (`graphs/direct_transfers.json`). Périmètre élargi après audit : voir l'addendum.

## 10. Niveau de preuve par relation

8 relations à identifiant stable dans `graphs/relations.jsonl`.
- ONCHAIN_CONFIRMED : 4
- PROTOCOL_CONFIRMED : 3
- SERVICE_INTERACTION : 1

## Addendum après audit, 02/11/2026

Ce dossier est celui du 2 nov. 08:18 UTC, conservé dans `archive/20261102_avant_amendement_audit/cases/`. Corrections : `reports/AMENDEMENT_AUDIT_2026-11-02.md`.

- La sortie vers `GxjcMTWW…` est cosignée par ce service, 4 s après réception : `DMmDPF9s…` est probablement une adresse de dépôt du service. Le balayage semblable à cookedrice tient à cet automatisme.
- E4 : hors univers, aucun achat au 13 oct., puis un seul token à 100 $ ou plus au 23 oct., écarté par un filtre absent du plan. Le « 0 paire » ne dit rien de ce compte.
- Redemption partagée avec WenZhuanBuPei : lot de 20 comptes, sans lien.
- E6 : le rang de financement publié sur 42 lignes contient des lignes coupées. Rang corrigé sur 20 comparateurs à historique complet : 9 font aussi court ou plus court. Le « KuCoin 3/11 contre 1/50 » est retiré : 48 comparateurs sur 78 étaient inutilisables. Relecture flow-trace : origine Solana 3/11 contre 6/68, p = 0,11, et financement sous 1 h 9/11 contre 32/39 comptes frais, rien de distinctif. Absence d'autre lien : sur un périmètre relu, non exhaustif, sans témoin positif de propriété commune.
