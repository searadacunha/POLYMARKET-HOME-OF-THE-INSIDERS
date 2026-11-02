# Dossier WenZhuanBuPei

Généré depuis `cases/wen.json`. Une adresse n'est pas une personne : aucune identité civile n'est établie ni recherchée, et rien ici ne prouve une information privilégiée.

## 1. Adresse et type

- Wallet Polymarket : `0x8832319d9c25df311e37511f0aa5b214abc16500`
- Type : DEPOSIT_WALLET. Propriétaire lu sur la chaîne : `0x6697f72fa32de93d8450830eb07f5b6724104405`. C'est une clé, pas une personne.
- Lien étiquette vers adresse : nom exact et parts de la capture.
- Première activité 2026-10-18 20:14:27 UTC, dernière 2026-10-27 22:58:06 UTC, 8 lignes d'activité, historique complet.
- Nonce du propriétaire sur six chaînes : {'polygon': 0, 'ethereum': 0, 'bsc': 0, 'arbitrum': 0, 'base': 0, 'optimism': 0}. Aucune transaction envoyée par cette clé sur ces chaînes : elle signe hors chaîne.

## 2 et 3. Premier financement et source directe

Premier dépôt : 2026-10-18 20:14:27 UTC, 15 926,88 pUSD, transaction `0x45c27719b34b5490a620b319911db190d6570bc1b0e2da3782d5bbb8c4cc2da3`. Le pUSD est frappé depuis l'adresse zéro : celle-ci n'est pas un financeur.
Source immédiate du collatéral : `0x315ac6e73410faafd02edac1b1a46da7b90814c5`.
- Dépôt `0x45c27719b34b…` : `0x315ac6e7…14c5`, EIP7702_DELEGATED_EOA, nonce 1, 2 enregistrements au pont Polymarket.

## 4. Origines remontées, du plus ancien au dépôt

| Heure UTC | De | Vers | Chaîne | Montant | Niveau | Transaction |
|---|---|---|---|---:|---|---|
| 2026-10-18 20:14:03 | `0xee7ae85f…4055` | `0x315ac6e7…14c5` | Polygon | 15 926,88 USDC | ONCHAIN_CONFIRMED | `0x2c0d0943a7874d99abbc28c4d4930407c8eaad006df45655f6e3ad0c2b808db3` |
| 2026-10-18 20:14:15 | `0x315ac6e7…14c5` | `0x315ac6e7…14c5` | Polygon | 15 926,88 USDC | PROTOCOL_CONFIRMED | `0xbe1b3982deaba664c64bfa8f6568f3512e7a2a798d41d888f947d78b43e6d622` |
| 2026-10-18 20:14:27 | `0x315ac6e7…14c5` | `0x8832319d…6500` | Polygon | 15 926,88 USDC.e→pUSD | ONCHAIN_CONFIRMED | `0x45c27719b34b5490a620b319911db190d6570bc1b0e2da3782d5bbb8c4cc2da3` |

**Où la trace s'arrête :**


## 5 et 6. Paris et positions

| Marché | Issue | Achats $ | Parts achetées | Ventes $ | Rachats $ | Net de parts avant l'article |
|---|---|---:|---:|---:|---:|---:|
| Ballon d'Or 2026: Kylian Mbappé or Lamine Yamal to finish higher? | Mbappé | 15 904,76 | 27 691,01 | n/d | 27 691,01 | 27 691,01 |

Premier achat : 2026-10-18 20:16:17 UTC, 13 058,19 $, « Ballon d'Or 2026: Kylian Mbappé or Lamine Yamal to finish higher? », Mbappé, `0xbe6c81c1d9ea65e02508e90bc896b0a2e9592512b2b56394abc8686c53cfb5c7`.

**Historique daté** (8 lignes sur 8) :

| Heure UTC | Type | Marché | Issue | $ | Parts | Prix | Transaction |
|---|---|---|---|---:|---:|---:|---|
| 10-18 20:14:27 | DEPOSIT  |  |  | 15 926,88 | 15 926,88 |  | `0x45c27719b34b5490a620b319911db190d6570bc1b0e2da3782d5bbb8c4cc2da3` |
| 10-18 20:16:17 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 13 058,19 | 23 079,37 | 0.5534376935 | `0xbe6c81c1d9ea65e02508e90bc896b0a2e9592512b2b56394abc8686c53cfb5c7` |
| 10-19 13:28:17 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 1 243,36 | 2 031,64 | 0.6 | `0xf8db59f61340306ca9d0e66f2f149122da0388bd4ec4c3a8b01c55fc43076092` |
| 10-19 13:28:44 | TRADE BUY | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 1 603,20 | 2 580,00 | 0.609496124 | `0xa44a09fdd20c185cda13f057ab0945fed57fadee61faa291e8299fcdf7f499dc` |
| 10-27 01:05:15 | REDEEM  | Ballon d'Or 2026: Kylian Mbappé or Lamine Yama | Mbappé | 27 691,01 | 27 691,01 |  | `0x0b9768d113b099417a8504cdfb54f4ad2c4837923bde06677b5c28e4f3611f70` |
| 10-27 22:58:06 | WITHDRAWAL  |  |  | 27 724,79 | 27 724,79 |  | `0x094f60bf5bf3a015903748b150b621bfeb115dcccf5d81d35bd688d5cdbe9b91` |

**Compte (API d'activité) :**

| Poste | $ |
|---|---:|
| DEPOSIT | 15 926,88 |
| TRADE_BUY | -15 904,76 |
| TAKER_REBATE | 11,65 |
| REDEEM | 27 691,01 |
| WITHDRAWAL | -27 724,79 |

Résidu du calcul : -0.0. Compte soldé : oui. **Retraits moins dépôts sur ce wallet : 11 797,91 $**, frais de transaction inclus, gas et coûts hors de ce wallet exclus.

## 7. Sorties et destinations

| Heure UTC | De | Vers | Chaîne | Montant reçu | Niveau | Transaction |
|---|---|---|---|---:|---|---|
| 2026-10-27 22:58:05 | `0x8832319d…6500` | `0xE820eCB3C6F48A420a5538046caB73D2F40987cd` | Arbitrum | 27 724,79 USDC | PROTOCOL_CONFIRMED | `0x521dbd22f8e00ba8ac55737e2a3479c76ea1162984b97815b4ea4c53a4f8595c` |
| 2026-10-27 22:58:10 | `0xe820ecb3…87cd` | `0x3ab2206b98b01ba256dbdd4c50208bf17ab27d50` | Arbitrum | 27 724,00 0xaf88d065e77c8cc2239327c5edb3a432268e5831 | ONCHAIN_CONFIRMED | `0xa06fecae758b361f2acf0c2198c5f399c89326806e0906d58561c6eb338640da` |

**État des destinations à la lecture :**

- `0xE820eCB3C6F48A420a5538046caB73D2F40987cd` (Arbitrum), lu le 2026-11-02 07:51:01 UTC : n/d transactions, historique partiel, solde n/d SOL et aucun jeton. Sorties observées : 0.

## 8. ChangeNOW, FixedFloat, exchanges, XMR

- Services étiquetés touchés : aucun.
- ChangeNOW ou FixedFloat : aucune interaction sur les sauts lus. Liste étiquetée incomplète : absence de preuve, pas preuve d absence.
- XMR : aucun échange XMR observé sur les sauts lus, donc aucun statut `XMR_VISIBILITY_BOUNDARY` à ce stade.

## 9. Liens avec les autres wallets

Lecture : un service commun ne relie personne. Détail et méthode : `reports/liens_entre_wallets.md`.

- Service non identifié partagé : `0xee7ae85f2fe2239e27d9c1e23fffe168d63b4055`, aussi avec ouldlm3alem. Mesure : Polygon 1,173 outflows to 824 receivers in 12 h around 18 Oct; Arbitrum 890 outflows to 743 receivers in 12 h around 26 Oct; called by senders with nonces of 12.4 M and 8.6 M. No traffic in short samples on 1 and 2 Nov, unexplained.
- Transfert direct de fonds vers ou depuis un autre dossier : aucun sur Polygon et Ethereum, stablecoins et pUSD, du 25 sept. au 2 nov. (`graphs/direct_transfers.json`). Périmètre élargi après audit : voir l'addendum.

## 10. Niveau de preuve par relation

6 relations à identifiant stable dans `graphs/relations.jsonl`.
- ONCHAIN_CONFIRMED : 4
- PROTOCOL_CONFIRMED : 2

## Addendum après audit, 02/11/2026

Ce dossier est celui du 2 nov. 08:18 UTC, conservé dans `archive/20261102_avant_amendement_audit/cases/`. Corrections : `reports/AMENDEMENT_AUDIT_2026-11-02.md`.

- E4 : hors univers, aucun achat au 13 oct., puis un seul token à 100 $ ou plus au 23 oct., écarté par un filtre absent du plan. Le « 0 paire » ne dit rien de ce compte.
- Redemption partagée avec VidenteRibeira : lot de 20 comptes, sans lien.
- E6 : le rang de financement publié sur 42 lignes contient des lignes coupées. Rang corrigé sur 20 comparateurs à historique complet : 1 font aussi court ou plus court. KuCoin n'est plus un indice : taux de base invalide, 53 comparateurs sur 83 inutilisables. Absence d'autre lien : sur un périmètre relu, non exhaustif, sans témoin positif de propriété commune.
