# Enquête Ballon d'Or 2026 : rapport final

**Version 2, corrigée après audit le 02/11/2026.** La version 1, écrite à 08:18 UTC, est conservée sans changement : `archive/20261102_avant_amendement_audit/rapport_final.md`, sha256 `de683ab687b293fca7d2ed9d09cda0aefe4341e0ee956510238022f76021c8c0`. Chaque correction : `reports/AMENDEMENT_AUDIT_2026-11-02.md`. Chaque vérification : `reports/CONTRE_VERIFICATION.md`. Espace : `~/Projects/PolySentinel-investigation`. Une adresse n'est pas une personne : aucune identité civile n'est établie ni recherchée.

## 1. Conclusion

**Ni contrôle commun, ni coordination, ni information privilégiée ne sont démontrés. Deux connexions financières directes existent pourtant.** La clé de brace227 envoie 0,00205 ETH, environ 5,53 $, à celle de kraben006 le 4 octobre. Surtout, elle finance les dépôts d'un wallet non nommé, 5 170 USDC les 9 et 10 octobre, à parts presque égales avec son propre wallet, et ce wallet ne parie que sur Kane. Ces faits ne disent pas qui contrôle ces clés, et ils ne disent rien d'une information privilégiée. Les onze comptes publics sont reliés à une adresse et leurs flux sont reconstruits. Le signal collectif testé est visible au 13 octobre, sans être spécifique.

| Niveau | Verdict | Sur quoi il repose |
|---|---|---|
| Comportement atypique | **Observé, avec un biais de sélection** | 11 comptes sur 11 actifs depuis octobre seulement. 9 sur 11 ont déposé moins d'une heure avant leur premier achat sur cette famille. 11 sur 11 sont sur Mbappé devant Yamal. La presse en a surligné 9 sur ces traits. |
| Connexion financière | **Établie : 1 paire sur 55 entre dossiers, et 1 wallet non nommé** | Transfert natif direct brace227 vers kraben006, lu sur deux nœuds. 5 170 USDC de la clé de brace227 vers la clé du wallet non nommé `0xa8e64a3c…f74a5`, lus sur la chaîne. Aucun autre lien entre dossiers trouvé sur le périmètre lu par l'audit (section 4). Ce périmètre n'est pas exhaustif : comptes d'exchange invisibles, BSC et autres wallets en cours de lecture, selon l'enquête flow-trace. |
| Contrôle commun de wallets | **Non déterminé** | Ni démontré, ni exclu, y compris pour brace227 et kraben006, et pour brace227 et `0xa8e64a3c…`, financé par elle. Financer un compte n'est pas le contrôler. La méthode n'a aucun témoin positif de propriété commune. |
| Coordination des paris | **Non démontrée** | 0 adresse partagée discriminante sur 55 paires, pas de synchronie nette (centile 95,5 à 5 min non corrigé, 84,2 à 60 min). E4 v2 ne trouve aucune paire nommée, mais 19 paires sur 55 n'y sont jamais testées. Indice le plus fort : brace227 et `0xa8e64a3c…`, même source de fonds les 9 et 10 oct., premiers achats à 13 min d'écart, Kane en commun, pour 954,04 $ chez brace227 ces deux jours contre 5 164,99 $ chez ce wallet jusqu'au 11 oct. Il fonde une hypothèse, pas une démonstration. |
| Insider trading | **Non démontré** | Aucune preuve d'accès à l'information. Gagner un pari, même tôt, ne prouve pas sa source, et une connexion financière entre deux comptes non plus. Les chronologies publiques des 8 au 13 octobre restent incomplètes. |

## 2. Les onze dossiers

| Étiquette | Wallet | Confiance sur le lien | Dépôts $ | Retraits $ | Retraits moins dépôts | Dernière destination lue |
|---|---|---|---:|---:|---:|---|
| Thin-Disclaimer-Life | `0x8d3319c5…6f5b` | élevée | 45 679,23 | 80 037,93 | 34 358,70 (soldé) | `EnHRjTP4pK…PZ8B (Solana)` |
| VidenteRibeira | `0x5f8b30fd…866a` | élevée | 28 029,96 | 51 509,88 | 23 479,92 (soldé) | `DMmDPF9sFc…wt5T (Solana)` |
| cookedrice | `0x4060509c…b4d0` | élevée | 21 873,74 | 39 158,78 | 17 285,05 (soldé) | `F7ew8r8X5Y…h5Eh (Solana)` |
| WenZhuanBuPei | `0x8832319d…6500` | élevée | 15 926,88 | 27 724,79 | 11 797,91 (soldé) | `0xE820eCB3…87cd (Arbitrum)` |
| 0x86544e4dfde | `0x3ed2c452…ff3d` | moyenne à élevée | 44 847,24 | 74 198,32 | non affirmé | `0x69837228…0DED (Ethereum)` |
| brace227 | `0x873848cd…6d03` | élevée | 10 032,98 | 22 036,76 | non affirmé | `0xc852b093…af26 (Ethereum)` |
| walletwallet8424 | `0x1a1ef4c6…cc40` | élevée | 22 088,68 | 35 546,89 | 13 458,21 (soldé) | `0x82775Eb8…A3a1 (Ethereum)` |
| Zoomman17 | `0x92a8eec1…eebc` | moyenne à élevée | 9 743,19 | 6 894,00 | non affirmé | `0xD90d0013…f444 (Ethereum)` |
| kraben006 | `0x84212ee4…d8ec` | élevée | 5 689,47 | 15 593,54 | 9 904,07 (soldé) | `0x101B5f4D…fb65 (Ethereum)` |
| OuldLm3alem | `0x71ae923f…e5bf` | élevée | 56 167,11 | 77 250,77 | non affirmé | `0x1B500B6c…5f2c (Polygon)` |
| 0xdd97e6 | `0xdd97e6ad…9464` | moyenne | 44 059,16 | 63 143,10 | 19 083,95 (soldé) | `0xca8B1f1a…6165 (Ethereum)` |

**Les deux montants à ne pas confondre.** 493 094,76 $ est un flux brut, 129 367,79 $ un net partiel. Arrondis au cent, d'où un écart d'un cent sur la somme des dépôts.

| Périmètre | Comptes | Dépôts $ | Retraits $ | Retraits moins dépôts $ |
|---|---:|---:|---:|---:|
| Soldés : Thin, VidenteRibeira, cookedrice, WenZhuanBuPei, walletwallet8424, kraben006, 0xdd97e6 | 7 | 183 347,12 | 312 714,91 | **129 367,79** |
| Résidu faible : 0x86544e4dfde, brace227, OuldLm3alem | 3 | 111 047,33 | 173 485,85 | 62 438,52 |
| Retraits inférieurs aux dépôts : Zoomman17 | 1 | 9 743,19 | 6 894,00 | -2 849,19 |
| **Les onze** | 11 | 304 137,63 | **493 094,76** | 188 957,12 |

- **493 094,76 $ n'est pas un gain.** Ce sont les 25 retraits des 11 comptes. Ils rendent d'abord les 304 137,63 $ déposés, et comptent un aller-retour de 438,67 $ de kraben006 (retiré puis redéposé 64 s plus tard).
- **129 367,79 $ ne couvre que 7 comptes.** C'est le seul périmètre où le compte est entièrement fermé. Les 4 autres gardent un résidu ou des positions : aucun gain n'y est affirmé. Ce chiffre ne dit rien de plus que retraits moins dépôts sur ces wallets : ni gas, ni frais hors du wallet, ni autre compte d'une même personne, inconnus ici.
- **Contrôle indépendant, sur la chaîne :** 25 destructions de pUSD sur 25 et 46 frappes sur 46 égales aux montants de l'API. Par ailleurs, dépôts plus activité (188 964,13 $ d'achats, ventes, redemptions, rebates, récompenses) moins retraits donnent 7,01 $, la somme des quatre résidus : c'est une identité du calcul, pas une preuve de plus.
- Ces totaux ne recoupent pas les chiffres de presse, dont le périmètre diffère. Montants reçus à destination : inférieurs aux retraits (frais de pont) et en jetons différents, donc non additionnés ici.

**Lecture des niveaux de confiance.** Élevée : lu sur la chaîne, ou même identifiant d'ordre sur deux chaînes. Moyenne : enregistrement d'un service, ou étiquette à source unique. Faible : comportement mesuré. La confiance du lien étiquette vers adresse est donnée à part.

**Comment les cinq comptes non résolus ont été reliés.** Le top 15 de la capture Upside est reproduit depuis le tape public, ligne par ligne, à moins d'une demi-part, à une seule fenêtre : 23 oct. 14:11:39 à 14:18:08 UTC (`evidence/screenshot_reconstruction.json`). kraben006 a en plus une confirmation indépendante : ce wallet vend bien du Kane pour acheter Yamal 3e, comme le note la capture. Détail : `reports/inventaire_adresses.md`.

### Thin-Disclaimer-Life

Wallet `0x8d3319c51520518ad01f6744486ceea29f376f5b`, DEPOSIT_WALLET, clé propriétaire `0x1bf0b469f7f3612657e99bf785e470eee2a76028`. Dossier complet : `cases/thin.md`.

**Comportements suspects réellement observés.** Ce sont des faits, pas des preuves d'intention.

- Premier événement Polymarket le 2026-10-11 15:23 UTC, premier achat sur la famille le 2026-10-12 00:16 UTC.
- Concentration : 99,6 % de ses achats sur le Ballon masculin (45 673,15 $ sur 2 issues, 185,18 $ ailleurs).
- Mbappé devant Yamal : 43 490,72 $ pour 76 082,65 parts, prix moyen 0,572 ; 36 840,48 $ avant le 13 oct. 18:51 UTC, 43 490,72 $ avant l'article. Part des achats taker du token avant l'article : 23,5 %.
- Autres issues : Rodri or Lionel Messi / Rodri (2 182 $).
- Plus grosse décision taker : 14 935,70 $ le 10-13 18:48 UTC, Kylian Mbappé or Lamine Yamal / Mbappé, 0,88 fois le volume du token sur les 24 h précédentes.
- Résultat : compte soldé, **retraits moins dépôts 34 358,70 $**, hors gas et coûts hors de ce wallet.

**Preuves on-chain vérifiables.**

- Premier financement : 2026-10-11 15:23:31 UTC, 11 833,23 $, `0x761f6058829482bc5fc66acd8b6d5bcc583e96a463ac75e52d666b31fd6f32d1`. Le pUSD est frappé depuis l'adresse zéro, qui n'est pas un financeur.
- Dépôts : 3, 45 679,23 $.
  - 11 833,23 $ : KuCoin Hot Wallet 2 → `EMu2EAWjzP…Mqsd` (Solana) → Relay
  - 11 946,00 $ : `0x8894e0a0…d4e3` (nonce 58 893 846) → adresse de pont, BSC → Relay
  - 21 900,00 $ : `0x8894e0a0…d4e3` (nonce 58 893 846) → adresse de pont, BSC → Relay
- Sorties : 4, 80 037,93 $.
  - 27/10 01:24 UTC, 250,00 $ → `CXVYMP5qxBENTNnqqmBAgvQB5wRLkcUBYPBDLFTeGrfJ` (Solana), reçu 2,4682 SOL, PROTOCOL_CONFIRMED. Retrait `0x6373a98fb86f82e1562448ccddf261d537a06a7112180f1d414e3f0968d9be7c`, paiement `3hB2wsiT2GhpJ9k3wajsJTsxpS28HbSuZySnW61RJy5zeVtHqzSakELK66xzrzWGkZ87xZ6Xr8MKoG9SKfBTrY89`.
  - 27/10 01:27 UTC, 40 000,00 $ → `CXVYMP5qxBENTNnqqmBAgvQB5wRLkcUBYPBDLFTeGrfJ` (Solana), reçu 39 999,8505 USDC, PROTOCOL_CONFIRMED. Retrait `0xa41a56f185a14d413f23839a94f0e92574dbf72a46b132dde1984f44d88b288e`, paiement `rwiu1FRYMBHqQTiXVdqCssrSs8YQZY2my7fLdNXvrBWDG8V4QckoRoirN3WGeSM6sY3XxC7ERwg486zHmLZEsEd`.
  - 27/10 01:28 UTC, 250,00 $ → `EnHRjTP4pKGkA4BC1yfoCNyUJcU3wapK1Gj8Us35PZ8B` (Solana), reçu 2,4651 SOL, PROTOCOL_CONFIRMED. Retrait `0xe35ea7f316355dc91347aa2f409aa030bb696035151a5ea5d8d72a69d11df989`, paiement `2UzjMVyoNhLo2tpSeLqGsqBByBjr8Y74LMmvYyuaNbExtF25TCtU29xCKuk372H9SA2K9VLx12sfoqT1eFSgvGW3`.
  - 27/10 01:29 UTC, 39 537,93 $ → `EnHRjTP4pKGkA4BC1yfoCNyUJcU3wapK1Gj8Us35PZ8B` (Solana), reçu 39 537,7800 USDC, PROTOCOL_CONFIRMED. Retrait `0x5c4d9506a42a1ecb190233847a7baea1f967766873218d042c714fb00bf31b90`, paiement `4HRAyjtxWPQ4Dn4yGAr9Hr5uXp4hMyKmiHUonaLosSPjYpT1z2VAFkeyGLk4Es6urGkauByp6Cbs4RFU4opdhk5o`.
- État de `CXVYMP5qxB…GrfJ`, lu le 2026-11-02 07:49:19 UTC : 39 999,85 USDC. Aucune sortie.
- État de `EnHRjTP4pK…PZ8B`, lu le 2026-11-02 07:49:23 UTC : 39 537,78 USDC. Aucune sortie.
- Relations à identifiant stable : PROTOCOL_CONFIRMED 7, ONCHAIN_CONFIRMED 6, SERVICE_INTERACTION 1.

**Liens éventuels avec les autres wallets.**

- SERVICE_ETIQUETE : `BmFdpraQhk…ymy6`, aussi 0xdd97e6, cookedrice, ouldlm3alem, vidente.
- Lien discriminant : aucun. Transfert direct avec un autre dossier : aucun trouvé sur le périmètre lu par l'audit (section 4), non exhaustif, revérifié ici seulement pour les clés de brace227 et kraben006 sur Ethereum.
- Issues aussi détenues par d'autres nommés : Kylian Mbappé or Lamine Yamal / Mbappé (10 autres); Rodri or Lionel Messi / Rodri (3 autres).

**Explications alternatives et faux positifs.**

- Pari de conviction renforcé sur plusieurs jours : achats étalés du 12 au 14 octobre, avec aussi deux petits paris sur Yui Hasegawa revendus à perte nette d'environ 11 $, ce qui ne ressemble pas à une connaissance de tous les résultats.
- Faux positifs d'une règle de « financeur commun » : `BmFdpraQhk…ymy6`. Ce sont des services, ils ne relient personne.
- Biais de sélection : ce compte est étudié parce que la presse l'a nommé après le résultat. Taille et âge ne sont donc pas des résultats indépendants.

**Résultats des contrôles statistiques.** Lecture individuelle descriptive : n effectif de l'affaire = 1, sans puissance par wallet.

- S_A scellé : vu, 1 paire(s) avec comportement, score maximal 1, **0 priorité**. Comparaison exploratoire, hors R3.
- Alerte A0 : membre d'aucune.
- Alerte du recensement E1G : 2026-10-16 01:00:00, Kylian Mbappé or Lamine Yamal / Mbappé.
- Rafales E2, membre de : 0 à 5 min, 0 à 15 min, 0 à 60 min.
- Petits puis gros E3 : 10-13 18:48, 14 935,70 $ après une médiane de 834,47 $.
- Combinaisons inhabituelles E4 v2 : 0 paire aux deux dates, sur les trois graines. E4 ne voit qu'un extrême, section 5.
- Autres nommés achetant le même token à moins de 5 min : 0x86544e4dfde ; à moins de 60 min : 1.
- Financement E6 : 532,5 min entre le dernier dépôt et le premier achat. 10 comparateurs sur 20 à historique complet font aussi court ou plus court. Publié en version 1 : 11 sur 42, lignes coupées comprises. Confondu avec l'âge du compte.
- Top 20 des décisions E7 : 2026-10-13 18:48:52, 14 935,70 $, prix 0,490 avant, 0,577 payé, 0,88 fois le volume de 24 h.
- Quatre rangs exacts détenus avant l'article : non. Combinaison cotée environ 0,28 à cette date, donc pas rare par rapport aux prix.

**Niveau de confiance et limites.**

- Lien étiquette vers adresse : **élevée** (nom exact et parts de la capture).
- Flux : **élevée** sur 13 relations lues sur la chaîne, **moyenne** sur 1 relation dépendant d'un service ou d'une étiquette.
- Coordination et information privilégiée : **non démontrées**, aucune preuve dans ce dossier ne les établit.
- La trace s'arrête à : `EMu2EAWjzP…Mqsd`. Seul le service connaît le compte d'origine.
- Mouvements natifs des clés : lus par l'audit sur le périmètre de la section 4, revérifiés ici seulement pour brace227 et kraben006 sur Ethereum. Soldes lus à la date indiquée, ils peuvent changer.

### VidenteRibeira

Wallet `0x5f8b30fde56bd2d2f3853769602330aeb9f1866a`, DEPOSIT_WALLET, clé propriétaire `0x3cb3f4f6b1a81bdf523e36b7f5fa5081113f0f5e`. Dossier complet : `cases/vidente.md`.

**Comportements suspects réellement observés.** Ce sont des faits, pas des preuves d'intention.

- Premier événement Polymarket le 2026-10-15 21:06 UTC, premier achat sur la famille le 2026-10-16 00:27 UTC.
- Concentration : 100,0 % de ses achats sur le Ballon masculin (27 884,23 $ sur 1 issue, 0,00 $ ailleurs).
- Mbappé devant Yamal : 27 884,23 $ pour 51 345,66 parts, prix moyen 0,543 ; 0,00 $ avant le 13 oct. 18:51 UTC, 27 884,23 $ avant l'article. Part des achats taker du token avant l'article : 15,8 %.
- Autres issues : aucune.
- Plus grosse décision taker : 9 476,16 $ le 10-16 20:38 UTC, Kylian Mbappé or Lamine Yamal / Mbappé, 0,61 fois le volume du token sur les 24 h précédentes.
- Résultat : compte soldé, **retraits moins dépôts 23 479,92 $**, hors gas et coûts hors de ce wallet.

**Preuves on-chain vérifiables.**

- Premier financement : 2026-10-15 21:06:54 UTC, 9 940,01 $, `0xcb790208996b569b3671f4d5090acae8ca22eff2a3cec6029b8aeee2081aa2d1`. Le pUSD est frappé depuis l'adresse zéro, qui n'est pas un financeur.
- Dépôts : 2, 28 029,96 $.
  - 9 940,01 $ : KuCoin Hot Wallet 2 → `5xHWduZuzC…uz1a` (Solana) → Relay
  - 18 089,95 $ : KuCoin Hot Wallet 2 → `5xHWduZuzC…uz1a` (Solana) → Relay
- Sorties : 1, 51 509,88 $.
  - 27/10 16:51 UTC, 51 509,88 $ → `DMmDPF9sFcNbq8dVKfxqZsKV4xKZBtsUZ4hXSwy1wt5T` (Solana), reçu 51 489,0920 USDT, PROTOCOL_CONFIRMED. Retrait `0x650d76f3ef10b8e0001baf61693372fa8634ae29a29ae11f86589c064cf52e16`, paiement `57XPE63Zvu53geF8C7saiFwDMjeZBimPBsyoD82kM72hPRMFBePmjcgSgz2vCsRmjLLUPe4u8RFTMdaCMzehQvTx`.
- État de `DMmDPF9sFc…wt5T`, lu le 2026-11-02 07:49:58 UTC : 0,09 USDT. Sortie : 27/10 16:51 UTC vers `GxjcMTWWDc…nvBW`, 51 489,00 USDT.
- Cette sortie est cosignée par `GxjcMTWW…`, qui en paie les frais, 4 s après la réception. `DMmDPF9s…` est donc probablement une adresse de dépôt tenue par ce service, pas une adresse personnelle.
- Relations à identifiant stable : ONCHAIN_CONFIRMED 4, PROTOCOL_CONFIRMED 3, SERVICE_INTERACTION 1.

**Liens éventuels avec les autres wallets.**

- SERVICE_ETIQUETE : `BmFdpraQhk…ymy6`, aussi 0xdd97e6, cookedrice, ouldlm3alem, thin.
- SERVICE_MESURE : `GxjcMTWWDc…nvBW`, aussi cookedrice.
- Lien discriminant : aucun. Transfert direct avec un autre dossier : aucun trouvé sur le périmètre lu par l'audit (section 4), non exhaustif, revérifié ici seulement pour les clés de brace227 et kraben006 sur Ethereum.
- Issues aussi détenues par d'autres nommés : Kylian Mbappé or Lamine Yamal / Mbappé (10 autres).

**Explications alternatives et faux positifs.**

- Achat tardif sur un seul marché, après la montée du prix de Mbappé depuis moins de 0,35 début octobre : compatible avec un pari de conviction ou le suivi du mouvement.
- Faux positifs d'une règle de « financeur commun » : `BmFdpraQhk…ymy6`, `GxjcMTWWDc…nvBW`. Ce sont des services, ils ne relient personne.
- Biais de sélection : ce compte est étudié parce que la presse l'a nommé après le résultat. Taille et âge ne sont donc pas des résultats indépendants.

**Résultats des contrôles statistiques.** Lecture individuelle descriptive : n effectif de l'affaire = 1, sans puissance par wallet.

- S_A scellé : vu, 1 paire(s) avec comportement, score maximal 1, **0 priorité**. Comparaison exploratoire, hors R3.
- Alerte A0 : membre d'aucune.
- Alerte du recensement E1G : 2026-10-16 01:00:00, Kylian Mbappé or Lamine Yamal / Mbappé.
- Rafales E2, membre de : 0 à 5 min, 0 à 15 min, 0 à 60 min.
- Petits puis gros E3 : non.
- Combinaisons inhabituelles E4 v2 : **hors univers** : aucun achat au 13 oct., puis un seul token à 100 $ ou plus au 23 oct., écarté par un filtre du code absent du plan. E4 ne dit rien de ce compte.
- Autres nommés achetant le même token à moins de 5 min : brace227 ; à moins de 60 min : 2.
- Financement E6 : 200,5 min entre le dernier dépôt et le premier achat. 9 comparateurs sur 20 à historique complet font aussi court ou plus court. Publié en version 1 : 10 sur 42, lignes coupées comprises. Confondu avec l'âge du compte.
- Top 20 des décisions E7 : absent.
- Quatre rangs exacts détenus avant l'article : non. Combinaison cotée environ 0,28 à cette date, donc pas rare par rapport aux prix.

**Niveau de confiance et limites.**

- Lien étiquette vers adresse : **élevée** (nom exact et parts de la capture).
- Flux : **élevée** sur 7 relations lues sur la chaîne, **moyenne** sur 1 relation dépendant d'un service ou d'une étiquette.
- Coordination et information privilégiée : **non démontrées**, aucune preuve dans ce dossier ne les établit.
- La trace s'arrête à : `5xHWduZuzC…uz1a`, `5xHWduZuzC…uz1a`. Seul le service connaît le compte d'origine.
- Mouvements natifs des clés : lus par l'audit sur le périmètre de la section 4, revérifiés ici seulement pour brace227 et kraben006 sur Ethereum. Soldes lus à la date indiquée, ils peuvent changer.

### cookedrice

Wallet `0x4060509c8c70cece529be4a089d6d66ad865b4d0`, DEPOSIT_WALLET, clé propriétaire `0x6ec290051ea167cf564a4282c153351ab3fd876f`. Dossier complet : `cases/cookedrice.md`.

**Comportements suspects réellement observés.** Ce sont des faits, pas des preuves d'intention.

- Premier événement Polymarket le 2026-10-14 19:58 UTC, premier achat sur la famille le 2026-10-14 20:01 UTC.
- Concentration : 100,0 % de ses achats sur le Ballon masculin (21 891,94 $ sur 2 issues, 0,00 $ ailleurs).
- Mbappé devant Yamal : 16 996,75 $ pour 32 001,91 parts, prix moyen 0,531 ; 0,00 $ avant le 13 oct. 18:51 UTC, 16 996,75 $ avant l'article. Part des achats taker du token avant l'article : 8,6 %.
- Autres issues : Rodri or Lionel Messi / Rodri (4 895 $).
- Plus grosse décision taker : 5 016,53 $ le 10-14 20:01 UTC, Kylian Mbappé or Lamine Yamal / Mbappé, 0,63 fois le volume du token sur les 24 h précédentes.
- Résultat : compte soldé, **retraits moins dépôts 17 285,05 $**, hors gas et coûts hors de ce wallet.

**Preuves on-chain vérifiables.**

- Premier financement : 2026-10-14 19:58:36 UTC, 21 873,74 $, `0x9e1a809440c983f23ae834f92a6214198cfd15b65b4001e5739add05ea733012`. Le pUSD est frappé depuis l'adresse zéro, qui n'est pas un financeur.
- Dépôts : 1, 21 873,74 $.
  - 21 873,74 $ : KuCoin Hot Wallet 2 → `BJcZxhXFt2…JxFU` (Solana) → Relay
- Sorties : 1, 39 158,78 $.
  - 28/10 18:04 UTC, 39 158,78 $ → `F7ew8r8X5YL3DPLtzg9Az3cPDKcVxXGjUpqgpskNh5Eh` (Solana), reçu 39 158,6312 USDC, PROTOCOL_CONFIRMED. Retrait `0x32c1285b13708b90937e6af48e956c07148630916649d021f9047af08767f1ae`, paiement `2wgkQdsKcoAKNPmCVt8JuKEXNwHJBvVLWVfXVKCfPkwn4nq69r2S5W1WG36XU3CcKKSETNwkidHcBUcC6unyGWa7`.
- État de `F7ew8r8X5Y…h5Eh`, lu le 2026-11-02 07:50:18 UTC : 0,63 USDC. Sortie : 28/10 18:04 UTC vers `GxjcMTWWDc…nvBW`, 39 158,00 USDC.
- Cette sortie est cosignée par `GxjcMTWW…`, qui en paie les frais, 2 s après la réception. `F7ew8r8X…` est donc probablement une adresse de dépôt tenue par ce service, pas une adresse personnelle.
- Relations à identifiant stable : ONCHAIN_CONFIRMED 3, PROTOCOL_CONFIRMED 2, SERVICE_INTERACTION 1.

**Liens éventuels avec les autres wallets.**

- SERVICE_ETIQUETE : `BmFdpraQhk…ymy6`, aussi 0xdd97e6, ouldlm3alem, thin, vidente.
- SERVICE_MESURE : `GxjcMTWWDc…nvBW`, aussi vidente.
- Lien discriminant : aucun. Transfert direct avec un autre dossier : aucun trouvé sur le périmètre lu par l'audit (section 4), non exhaustif, revérifié ici seulement pour les clés de brace227 et kraben006 sur Ethereum.
- Issues aussi détenues par d'autres nommés : Kylian Mbappé or Lamine Yamal / Mbappé (10 autres); Rodri or Lionel Messi / Rodri (3 autres).

**Explications alternatives et faux positifs.**

- Entrée le 14 octobre, à un prix déjà proche de 0,5, après la première montée : compatible avec le suivi du mouvement.
- Faux positifs d'une règle de « financeur commun » : `BmFdpraQhk…ymy6`, `GxjcMTWWDc…nvBW`. Ce sont des services, ils ne relient personne.
- Biais de sélection : ce compte est étudié parce que la presse l'a nommé après le résultat. Taille et âge ne sont donc pas des résultats indépendants.

**Résultats des contrôles statistiques.** Lecture individuelle descriptive : n effectif de l'affaire = 1, sans puissance par wallet.

- S_A scellé : vu, 2 paire(s) avec comportement, score maximal 1, **0 priorité**. Comparaison exploratoire, hors R3.
- Alerte A0 : membre d'aucune.
- Alerte du recensement E1G : 2026-10-16 01:00:00, Kylian Mbappé or Lamine Yamal / Mbappé.
- Rafales E2, membre de : 0 à 5 min, 0 à 15 min, 1 à 60 min.
- Petits puis gros E3 : 10-18 17:58, 4 065,57 $ après une médiane de 670,28 $.
- Combinaisons inhabituelles E4 v2 : hors univers au 13 oct., 0 paire au 23 oct. sur les trois graines. E4 ne voit qu'un extrême, section 5.
- Autres nommés achetant le même token à moins de 5 min : aucun ; à moins de 60 min : 2.
- Financement E6 : 2,4 min entre le dernier dépôt et le premier achat. 3 comparateurs sur 20 à historique complet font aussi court ou plus court. Publié en version 1 : 3 sur 42, lignes coupées comprises. Confondu avec l'âge du compte.
- Top 20 des décisions E7 : absent.
- Quatre rangs exacts détenus avant l'article : non. Combinaison cotée environ 0,28 à cette date, donc pas rare par rapport aux prix.

**Niveau de confiance et limites.**

- Lien étiquette vers adresse : **élevée** (nom exact et parts de la capture).
- Flux : **élevée** sur 5 relations lues sur la chaîne, **moyenne** sur 1 relation dépendant d'un service ou d'une étiquette.
- Coordination et information privilégiée : **non démontrées**, aucune preuve dans ce dossier ne les établit.
- La trace s'arrête à : `BJcZxhXFt2…JxFU`. Seul le service connaît le compte d'origine.
- Mouvements natifs des clés : lus par l'audit sur le périmètre de la section 4, revérifiés ici seulement pour brace227 et kraben006 sur Ethereum. Soldes lus à la date indiquée, ils peuvent changer.

### WenZhuanBuPei

Wallet `0x8832319d9c25df311e37511f0aa5b214abc16500`, DEPOSIT_WALLET, clé propriétaire `0x6697f72fa32de93d8450830eb07f5b6724104405`. Dossier complet : `cases/wen.md`.

**Comportements suspects réellement observés.** Ce sont des faits, pas des preuves d'intention.

- Premier événement Polymarket le 2026-10-18 20:14 UTC, premier achat sur la famille le 2026-10-18 20:16 UTC.
- Concentration : 100,0 % de ses achats sur le Ballon masculin (15 904,76 $ sur 1 issue, 0,00 $ ailleurs).
- Mbappé devant Yamal : 15 904,76 $ pour 27 691,01 parts, prix moyen 0,574 ; 0,00 $ avant le 13 oct. 18:51 UTC, 15 904,76 $ avant l'article. Part des achats taker du token avant l'article : 9,0 %.
- Autres issues : aucune.
- Plus grosse décision taker : 12 772,99 $ le 10-18 20:16 UTC, Kylian Mbappé or Lamine Yamal / Mbappé, 0,68 fois le volume du token sur les 24 h précédentes.
- Résultat : compte soldé, **retraits moins dépôts 11 797,91 $**, hors gas et coûts hors de ce wallet.

**Preuves on-chain vérifiables.**

- Premier financement : 2026-10-18 20:14:27 UTC, 15 926,88 $, `0x45c27719b34b5490a620b319911db190d6570bc1b0e2da3782d5bbb8c4cc2da3`. Le pUSD est frappé depuis l'adresse zéro, qui n'est pas un financeur.
- Dépôts : 1, 15 926,88 $.
  - 15 926,88 $ : `0xee7ae85f…4055` (nonce 1) → adresse de pont, Polygon → Relay
- Sorties : 1, 27 724,79 $.
  - 27/10 22:58 UTC, 27 724,79 $ → `0xE820eCB3C6F48A420a5538046caB73D2F40987cd` (Arbitrum), reçu 27 724,7897 USDC, PROTOCOL_CONFIRMED. Retrait `0x094f60bf5bf3a015903748b150b621bfeb115dcccf5d81d35bd688d5cdbe9b91`, paiement `0x521dbd22f8e00ba8ac55737e2a3479c76ea1162984b97815b4ea4c53a4f8595c`.
- `0xe820ecb3…87cd` (Arbitrum) : reçu 27 724,79, solde du même jeton 0,79, lu le 2026-11-02 08:07 UTC.
- Saut suivant de `0xe820ecb3…87cd` : 27 724,00 $ vers `0x3ab2206b…7d50`, EOA, nonce 1270, `0xa06fecae758b361f2acf0c2198c5f399c89326806e0906d58561c6eb338640da`.
- Relations à identifiant stable : ONCHAIN_CONFIRMED 4, PROTOCOL_CONFIRMED 2.

**Liens éventuels avec les autres wallets.**

- SERVICE_MESURE : `0xee7ae85f…4055`, aussi ouldlm3alem.
- Lien discriminant : aucun. Transfert direct avec un autre dossier : aucun trouvé sur le périmètre lu par l'audit (section 4), non exhaustif, revérifié ici seulement pour les clés de brace227 et kraben006 sur Ethereum.
- Issues aussi détenues par d'autres nommés : Kylian Mbappé or Lamine Yamal / Mbappé (10 autres).

**Explications alternatives et faux positifs.**

- Une seule grosse mise le 18 octobre à un prix déjà proche de 0,55 : compatible avec un pari de conviction tardif, et avec un compte neuf d'un parieur déjà actif ailleurs.
- Faux positifs d'une règle de « financeur commun » : `0xee7ae85f…4055`. Ce sont des services, ils ne relient personne.
- Biais de sélection : ce compte est étudié parce que la presse l'a nommé après le résultat. Taille et âge ne sont donc pas des résultats indépendants.

**Résultats des contrôles statistiques.** Lecture individuelle descriptive : n effectif de l'affaire = 1, sans puissance par wallet.

- S_A scellé : vu, 1 paire(s) avec comportement, score maximal 1, **0 priorité**. Comparaison exploratoire, hors R3.
- Alerte A0 : membre d'aucune.
- Alerte du recensement E1G : membre d'aucune.
- Rafales E2, membre de : 0 à 5 min, 0 à 15 min, 0 à 60 min.
- Petits puis gros E3 : non.
- Combinaisons inhabituelles E4 v2 : **hors univers** : aucun achat au 13 oct., puis un seul token à 100 $ ou plus au 23 oct., écarté par un filtre du code absent du plan. E4 ne dit rien de ce compte.
- Autres nommés achetant le même token à moins de 5 min : aucun ; à moins de 60 min : 0.
- Financement E6 : 1,8 min entre le dernier dépôt et le premier achat. 1 comparateur sur 20 à historique complet fait aussi court ou plus court. Publié en version 1 : 1 sur 42, lignes coupées comprises. Confondu avec l'âge du compte.
- Top 20 des décisions E7 : 2026-10-18 20:16:17, 12 772,99 $, prix 0,550 avant, 0,553 payé, 0,68 fois le volume de 24 h.
- Quatre rangs exacts détenus avant l'article : non. Combinaison cotée environ 0,28 à cette date, donc pas rare par rapport aux prix.

**Niveau de confiance et limites.**

- Lien étiquette vers adresse : **élevée** (nom exact et parts de la capture).
- Flux : **élevée** sur 6 relations lues sur la chaîne, **moyenne** sur 0 relations dépendant d'un service ou d'une étiquette.
- Coordination et information privilégiée : **non démontrées**, aucune preuve dans ce dossier ne les établit.
- Mouvements natifs des clés : lus par l'audit sur le périmètre de la section 4, revérifiés ici seulement pour brace227 et kraben006 sur Ethereum. Soldes lus à la date indiquée, ils peuvent changer.

### 0x86544e4dfde

Wallet `0x3ed2c452f141c291adecb97ddfc72b1650acff3d`, DEPOSIT_WALLET, clé propriétaire `0x69837228fa0bcbac53713d981161c929523c0ded`. Dossier complet : `cases/0x86544e4dfde.md`.

**Comportements suspects réellement observés.** Ce sont des faits, pas des preuves d'intention.

- Premier événement Polymarket le 2026-10-09 18:06 UTC, premier achat sur la famille le 2026-10-09 18:09 UTC.
- Concentration : 99,6 % de ses achats sur le Ballon masculin (48 209,30 $ sur 7 issues, 205,96 $ ailleurs).
- Mbappé devant Yamal : 10 576,40 $ pour 21 174,75 parts, prix moyen 0,499 ; 10 472,73 $ avant le 13 oct. 18:51 UTC, 10 576,40 $ avant l'article. Part des achats taker du token avant l'article : 2,8 %.
- Autres issues : Harry Kane win / Yes (30 709 $); Jude Bellingham finish in the top 10 of / No (4 567 $); Lionel Messi finish 5th in / Yes (1 191 $).
- Plus grosse décision taker : 6 167,19 $ le 10-11 13:55 UTC, Harry Kane win / Yes, 0,15 fois le volume du token sur les 24 h précédentes.
- Résultat : non affirmé. Compte non soldé ou non réconcilié : résidu de calcul -15,8647 $, solde pUSD 0,00 $, 0 positions ouvertes valant 0,00 $. Écart brut retraits moins dépôts : 29 351,08 $.

**Preuves on-chain vérifiables.**

- Premier financement : 2026-10-09 18:06:01 UTC, 14 999,00 $, `0x40f84e77821ecf20773964ead4dba8868267f8efcb9f9d134d50c3a27dcc2f1e`. Le pUSD est frappé depuis l'adresse zéro, qui n'est pas un financeur.
- Dépôts : 4, 44 847,24 $.
  - 14 999,00 $ : la clé propriétaire elle-même, Polygon → Relay
  - 25 686,09 $ : la clé propriétaire elle-même, Polygon → Relay
  - 1 704,39 $ : la clé propriétaire elle-même, Polygon → Relay
  - 2 457,76 $ : `0x408ce42a…c5b3` (nonce 2) → adresse de pont, Polygon → Relay
- Sorties : 1, 74 198,32 $.
  - 27/10 01:59 UTC, 74 198,32 $ → `0x69837228fa0bcBaC53713D981161C929523c0DED` (Ethereum), reçu 74 198,3177 USDC, PROTOCOL_CONFIRMED. Retrait `0x592333616322f0718366c916984050edd5b23d8ce108c62f4aaecb62cfe03b83`, paiement `0xf157abfd294420ba1d35bf08a5c8725bb74a87437454fea3ead8da50dbeabb05`.
- `0x69837228…0ded` (Ethereum) : reçu 74 198,32, solde du même jeton 74 198,32, lu le 2026-11-02 08:07 UTC.
- Relations à identifiant stable : ONCHAIN_CONFIRMED 9, PROTOCOL_CONFIRMED 5.

**Liens éventuels avec les autres wallets.**

- SERVICE_MESURE : `0xc8a6871d…8d64`, aussi brace227, kraben006, walletwallet8424, zoomman17.
- SERVICE_MESURE : `0x0ce9bdf3…f06d`, aussi walletwallet8424.
- Lien discriminant : aucun. Transfert direct avec un autre dossier : aucun trouvé sur le périmètre lu par l'audit (section 4), non exhaustif, revérifié ici seulement pour les clés de brace227 et kraben006 sur Ethereum.
- Une exécution de carnet d'ordres entre OuldLm3alem et 0x86544e4dfde : 520,97 parts à 0,53, `0x870eaa6cb8298d7a02379b48093d4633af4f77ba58638bfc78ff9b0146f30b48`. Ordinaire sur un carnet.
- Issues aussi détenues par d'autres nommés : Kylian Mbappé or Lamine Yamal / Mbappé (10 autres); Harry Kane win / Yes (4 autres); Lamine Yamal finish 3rd in / Yes (4 autres); Rodri or Lionel Messi / Rodri (3 autres).

**Explications alternatives et faux positifs.**

- Parieur actif sur plusieurs issues dès le 9 octobre, Kane compris, au moment où ce marché montait déjà. Mouvement de Kane amorcé la veille sans wallet nommé.
- Faux positifs d'une règle de « financeur commun » : `0xc8a6871d…8d64`, `0x0ce9bdf3…f06d`. Ce sont des services, ils ne relient personne.
- Redemption de Kane le 27 oct. à 01:58:15 UTC, en même temps que walletwallet8424 : faux positif comme lien, c'est un lot de 2 711 comptes en 136 transactions, le déclencheur n'est pas lu. Le retrait, 96 s plus tard, reste un geste propre et rapide face aux autres comptes du lot : indice faible, exploratoire, qui ne prouve aucun lien (section 4).
- Biais de sélection : ce compte est étudié parce que la presse l'a nommé après le résultat. Taille et âge ne sont donc pas des résultats indépendants.

**Résultats des contrôles statistiques.** Lecture individuelle descriptive : n effectif de l'affaire = 1, sans puissance par wallet.

- S_A scellé : vu, 2 paire(s) avec comportement, score maximal 1, **0 priorité**. Comparaison exploratoire, hors R3.
- Alerte A0 : 2026-10-11 14:00:00, Kylian Mbappé or Lamine Yamal / Mbappé, 3 wallets, avant le 13 oct. 18:51.
- Alerte du recensement E1G : membre d'aucune.
- Rafales E2, membre de : 0 à 5 min, 1 à 15 min, 5 à 60 min.
- Petits puis gros E3 : non.
- Combinaisons inhabituelles E4 v2 : 0 paire aux deux dates, sur les trois graines. E4 ne voit qu'un extrême, section 5.
- Autres nommés achetant le même token à moins de 5 min : brace227, thin, walletwallet8424 ; à moins de 60 min : 6.
- Financement E6 : 3,9 min entre le dernier dépôt et le premier achat. 4 comparateurs sur 20 à historique complet font aussi court ou plus court. Publié en version 1 : 4 sur 42, lignes coupées comprises. Confondu avec l'âge du compte.
- Top 20 des décisions E7 : absent.
- Quatre rangs exacts détenus avant l'article : non. Combinaison cotée environ 0,28 à cette date, donc pas rare par rapport aux prix.

**Niveau de confiance et limites.**

- Lien étiquette vers adresse : **moyenne à élevée** (parts de la capture).
- Flux : **élevée** sur 14 relations lues sur la chaîne, **moyenne** sur 0 relations dépendant d'un service ou d'une étiquette.
- Coordination et information privilégiée : **non démontrées**, aucune preuve dans ce dossier ne les établit.
- Mouvements natifs des clés : lus par l'audit sur le périmètre de la section 4, revérifiés ici seulement pour brace227 et kraben006 sur Ethereum. Soldes lus à la date indiquée, ils peuvent changer.

### brace227

Wallet `0x873848cd27784900e193611845fc3fd2c4716d03`, DEPOSIT_WALLET, clé propriétaire `0xc852b0938f5ad79b640d105ed11c14499454af26`. Dossier complet : `cases/brace227.md`.

**Comportements suspects réellement observés.** Ce sont des faits, pas des preuves d'intention.

- Premier événement Polymarket le 2026-10-09 20:49 UTC, premier achat sur la famille le 2026-10-09 20:50 UTC.
- Concentration : 100,0 % de ses achats sur le Ballon masculin (25 634,18 $ sur 9 issues, 0,00 $ ailleurs).
- Mbappé devant Yamal : 8 552,02 $ pour 17 106,64 parts, prix moyen 0,500 ; 3 320,77 $ avant le 13 oct. 18:51 UTC, 8 552,02 $ avant l'article. Part des achats taker du token avant l'article : 2,7 %.
- Autres issues : Harry Kane win / Yes (14 181 $); Lamine Yamal finish 3rd in / Yes (1 453 $); Lamine Yamal finish in the top 2 of / No (557 $).
- Plus grosse décision taker : 824,93 $ le 10-16 19:23 UTC, Kylian Mbappé or Lamine Yamal / Mbappé, 0,06 fois le volume du token sur les 24 h précédentes.
- Résultat : non affirmé. Compte non soldé ou non réconcilié : résidu de calcul 3,3906 $, solde pUSD 3,39 $, 0 positions ouvertes valant 0,00 $. Écart brut retraits moins dépôts : 12 003,77 $.

**Preuves on-chain vérifiables.**

- Premier financement : 2026-10-09 20:49:05 UTC, 2 186,43 $, `0x2a89597ebf1d83b5b76ceccab02924c28ca0ad8f6d208b2c42801a0925280a2c`. Le pUSD est frappé depuis l'adresse zéro, qui n'est pas un financeur.
- Dépôts : 8, 10 032,98 $.
  - 2 186,43 $ : la clé propriétaire elle-même, Ethereum → Relay
  - 1 000,00 $ : la clé propriétaire elle-même, Ethereum → Relay
  - 993,41 $ : la clé propriétaire elle-même, Ethereum → Relay
  - 993,41 $ : la clé propriétaire elle-même, Ethereum → Relay
  - 1 000,00 $ : la clé propriétaire elle-même, Ethereum → Relay
  - et 3 autres, dans le dossier complet.
- Sorties : 4, 22 036,76 $.
  - 11/10 13:25 UTC, 13,19 $ → `0xc852b0938f5ad79B640D105ED11c14499454af26` (Ethereum), reçu 13,1877 USDC, PROTOCOL_CONFIRMED. Retrait `0x93518e172a0daf71fa8610c411e0ec5b7e208773424a2898e889e39e0816c946`, paiement `0x1f3bb89154029ee54984e44d8650fe88b2dddd22051aeb97c942ca31525454bf`.
  - 26/10 23:13 UTC, 19 842,33 $ → `0xc852b0938f5ad79B640D105ED11c14499454af26` (Ethereum), reçu 19 842,3339 USDC, PROTOCOL_CONFIRMED. Retrait `0x6391df5cd4c4d177988c8473ac1b17fdd26569cc78e34c646306e11b3ce950fc`, paiement `0x8669118e08e63b629ff54d78c9301ae1aa94f1d21b10d67d0c6a20837ff19a2c`.
  - 26/10 23:15 UTC, 2 175,73 $ → `0xc852b0938f5ad79B640D105ED11c14499454af26` (Ethereum), reçu 2 175,7332 USDC, PROTOCOL_CONFIRMED. Retrait `0x770f97d1b820295c9045b520eb64175dbe32a0b9b4065f866634596cd027333e`, paiement `0x78603ab216c7da4b00394583d28fd6cc918b428b6af11b9bf02a1b02d447eaf6`.
  - 27/10 00:14 UTC, 5,50 $ → `0xc852b0938f5ad79B640D105ED11c14499454af26` (Ethereum), reçu 5,5018 USDC, PROTOCOL_CONFIRMED. Retrait `0x5575675d19ecd30f1cfce70f1d80adbb0e481b7a84c5ac2b718d3d651882732e`, paiement `0x40bc8e9a05ac22b66cbf418e8b85ad1928c421656aa864c634985c7cabec5fef`.
- `0xc852b093…af26` (Ethereum) : reçu 22 036,76, solde du même jeton 22 024,57, lu le 2026-11-02 08:07 UTC.
- Relations à identifiant stable : ONCHAIN_CONFIRMED 13, PROTOCOL_CONFIRMED 12, SERVICE_INTERACTION 4.

**Liens éventuels avec les autres wallets.**

- SERVICE_MESURE : `0xc8a6871d…8d64`, aussi 0x86544e4dfde, kraben006, walletwallet8424, zoomman17.
- SERVICE_ETIQUETE : `0x4cd00e38…bc31`, aussi kraben006, zoomman17.
- SERVICE_MESURE : `0xc1d13492…a1b5`, aussi kraben006.
- **Transfert direct vers le dossier kraben006 :** le 2026-10-04 13:54:35 UTC, la clé `0xc852b0938f5ad79b640d105ed11c14499454af26` envoie 0,002048943671205553 ETH, environ 5,53 $, à `0x101b5f4dc0886c32e2b75972101aeaf9f338fb65`, `0xd07bea20a22d9381e0ab364e7a7421776318c6f4aa7258799638472ad7092b98`. Détail et hypothèses : section 4. Aucun autre transfert direct trouvé sur le périmètre lu par l'audit, revérifié ici sur Ethereum pour cette clé. Aucune adresse partagée discriminante.
- **Hors des onze, wallet non nommé :** cette clé envoie 2 210 et 2 960 USDC à `0x48ec106cf690edd58fcd6df1e8b6abfc16dab12d`, propriétaire du wallet `0xa8e64a3c08d1e2a4e9f25a2dd33b8ac3458f74a5`, qui ne parie que sur Kane. Détail et hypothèses : section 4.
- Issues aussi détenues par d'autres nommés : Kylian Mbappé or Lamine Yamal / Mbappé (10 autres); Harry Kane win / Yes (4 autres); Lamine Yamal finish 3rd in / Yes (4 autres); Rodri or Lionel Messi / Rodri (3 autres).

**Explications alternatives et faux positifs.**

- Profil de petit parieur actif sur ce wallet : nombreux tickets, 8 dépôts, 9 issues, et des retraits en cours de route. Aucune priorité ni comportement dans S_A. Mais la même clé finance à parts presque égales un second wallet, tout sur Kane : ce profil ne décrit qu'une partie de ses fonds (section 4).
- Retrait principal 2,8 min après celui de kraben006 : aucun signal mesurable. Il suit de 136 s sa vente à 0,999, vitesse ordinaire, 10 vendeurs comparables sur 20 retirent aussi en moins de 5 min (section 4).
- Faux positifs d'une règle de « financeur commun » : `0xc8a6871d…8d64`, `0x4cd00e38…bc31`, `0xc1d13492…a1b5`. Ce sont des services, ils ne relient personne.
- Biais de sélection : ce compte est étudié parce que la presse l'a nommé après le résultat. Taille et âge ne sont donc pas des résultats indépendants.

**Résultats des contrôles statistiques.** Lecture individuelle descriptive : n effectif de l'affaire = 1, sans puissance par wallet.

- S_A scellé : vu, 0 paire(s) avec comportement, score maximal 0, **0 priorité**. Comparaison exploratoire, hors R3.
- Alerte A0 : 2026-10-11 14:00:00, Kylian Mbappé or Lamine Yamal / Mbappé, 3 wallets, avant le 13 oct. 18:51.
- Alerte du recensement E1G : membre d'aucune.
- Rafales E2, membre de : 1 à 5 min, 1 à 15 min, 1 à 60 min.
- Petits puis gros E3 : non.
- Combinaisons inhabituelles E4 v2 : 0 paire aux deux dates, sur les trois graines. E4 ne voit qu'un extrême, section 5.
- Autres nommés achetant le même token à moins de 5 min : 0x86544e4dfde, vidente, zoomman17 ; à moins de 60 min : 5.
- Financement E6 : 1,0 min entre le dernier dépôt et le premier achat. 1 comparateur sur 20 à historique complet fait aussi court ou plus court. Publié en version 1 : 1 sur 42, lignes coupées comprises. Confondu avec l'âge du compte.
- Top 20 des décisions E7 : absent.
- Quatre rangs exacts détenus avant l'article : non. Combinaison cotée environ 0,28 à cette date, donc pas rare par rapport aux prix.

**Niveau de confiance et limites.**

- Lien étiquette vers adresse : **élevée** (nom exact et parts de la capture).
- Flux : **élevée** sur 25 relations lues sur la chaîne, **moyenne** sur 4 relations dépendant d'un service ou d'une étiquette.
- Connexion financière directe avec kraben006 : **établie**, 1 transfert. Contrôle commun, coordination et information privilégiée : **non démontrés**. Le transfert n'en est pas la preuve.
- Mouvements natifs des clés : lus par l'audit sur le périmètre de la section 4, revérifiés ici seulement pour brace227 et kraben006 sur Ethereum. Soldes lus à la date indiquée, ils peuvent changer.

### walletwallet8424

Wallet `0x1a1ef4c65583d5c71011d7fe51e9f544e2b1cc40`, DEPOSIT_WALLET, clé propriétaire `0x82775eb82fe33acffdf1b91a28c0fc19b4b6a3a1`. Dossier complet : `cases/walletwallet8424.md`.

**Comportements suspects réellement observés.** Ce sont des faits, pas des preuves d'intention.

- Premier événement Polymarket le 2026-10-10 13:19 UTC, premier achat sur la famille le 2026-10-10 13:22 UTC.
- Concentration : 100,0 % de ses achats sur le Ballon masculin (20 777,85 $ sur 2 issues, 0,00 $ ailleurs).
- Mbappé devant Yamal : 5 827,10 $ pour 11 777,49 parts, prix moyen 0,495 ; 0,00 $ avant le 13 oct. 18:51 UTC, 5 827,10 $ avant l'article. Part des achats taker du token avant l'article : 0,5 %.
- Autres issues : Harry Kane win / Yes (14 951 $).
- Plus grosse décision taker : 5 000,00 $ le 10-10 19:48 UTC, Harry Kane win / Yes, 0,14 fois le volume du token sur les 24 h précédentes.
- Résultat : compte soldé, **retraits moins dépôts 13 458,21 $**, hors gas et coûts hors de ce wallet.

**Preuves on-chain vérifiables.**

- Premier financement : 2026-10-10 13:19:01 UTC, 1 673,43 $, `0x71250186b46bcded0deb878fae935386f67adeb43ed59c64a6d1614d291594f4`. Le pUSD est frappé depuis l'adresse zéro, qui n'est pas un financeur.
- Dépôts : 3, 22 088,68 $.
  - 1 673,43 $ : la clé propriétaire elle-même, Polygon → Relay
  - 16 508,26 $ : la clé propriétaire elle-même, Polygon → Relay
  - 3 906,99 $ : la clé propriétaire elle-même, Polygon → Relay
- Sorties : 1, 35 546,89 $.
  - 27/10 02:01 UTC, 35 546,89 $ → `0x82775Eb82Fe33AcfFDf1B91a28c0fc19B4b6A3a1` (Ethereum), reçu 35 546,8866 USDC, PROTOCOL_CONFIRMED. Retrait `0x27db9e0ad79e75020c1fcff6d22940313ab26808a853a5139db35c8823321a91`, paiement `0x1eb9ec280314e1c8e81753c286d53d4aee7c0e7e1eac4149e4de1f9409213b76`.
- `0x82775eb8…a3a1` (Ethereum) : reçu 35 546,89, solde du même jeton 35 546,89, lu le 2026-11-02 08:07 UTC.
- Relations à identifiant stable : ONCHAIN_CONFIRMED 7, PROTOCOL_CONFIRMED 4.

**Liens éventuels avec les autres wallets.**

- SERVICE_MESURE : `0xc8a6871d…8d64`, aussi 0x86544e4dfde, brace227, kraben006, zoomman17.
- SERVICE_MESURE : `0x0ce9bdf3…f06d`, aussi 0x86544e4dfde.
- Lien discriminant : aucun. Transfert direct avec un autre dossier : aucun trouvé sur le périmètre lu par l'audit (section 4), non exhaustif, revérifié ici seulement pour les clés de brace227 et kraben006 sur Ethereum.
- Issues aussi détenues par d'autres nommés : Kylian Mbappé or Lamine Yamal / Mbappé (10 autres); Harry Kane win / Yes (4 autres).

**Explications alternatives et faux positifs.**

- Deux paris cohérents entre eux, Kane et Mbappé devant Yamal, pris au moment où Kane montait déjà. Compatible avec une lecture du marché.
- Faux positifs d'une règle de « financeur commun » : `0xc8a6871d…8d64`, `0x0ce9bdf3…f06d`. Ce sont des services, ils ne relient personne.
- Redemption de Kane le 27 oct. à 01:58:15 UTC, en même temps que 0x86544e4dfde : faux positif comme lien, c'est un lot de 2 711 comptes en 136 transactions, le déclencheur n'est pas lu. Le retrait, 189 s plus tard, reste un geste propre et rapide face aux autres comptes du lot : indice faible, exploratoire, qui ne prouve aucun lien (section 4).
- Biais de sélection : ce compte est étudié parce que la presse l'a nommé après le résultat. Taille et âge ne sont donc pas des résultats indépendants.

**Résultats des contrôles statistiques.** Lecture individuelle descriptive : n effectif de l'affaire = 1, sans puissance par wallet.

- S_A scellé : vu, 1 paire(s) avec comportement, score maximal 1, **0 priorité**. Comparaison exploratoire, hors R3.
- Alerte A0 : membre d'aucune.
- Alerte du recensement E1G : membre d'aucune.
- Rafales E2, membre de : 0 à 5 min, 1 à 15 min, 2 à 60 min.
- Petits puis gros E3 : non.
- Combinaisons inhabituelles E4 v2 : hors univers au 13 oct., 0 paire au 23 oct. sur les trois graines. E4 ne voit qu'un extrême, section 5.
- Autres nommés achetant le même token à moins de 5 min : 0x86544e4dfde ; à moins de 60 min : 2.
- Financement E6 : 3,3 min entre le dernier dépôt et le premier achat. 4 comparateurs sur 20 à historique complet font aussi court ou plus court. Publié en version 1 : 4 sur 42, lignes coupées comprises. Confondu avec l'âge du compte.
- Top 20 des décisions E7 : absent.
- Quatre rangs exacts détenus avant l'article : non. Combinaison cotée environ 0,28 à cette date, donc pas rare par rapport aux prix.

**Niveau de confiance et limites.**

- Lien étiquette vers adresse : **élevée** (nom exact et parts de la capture).
- Flux : **élevée** sur 11 relations lues sur la chaîne, **moyenne** sur 0 relations dépendant d'un service ou d'une étiquette.
- Coordination et information privilégiée : **non démontrées**, aucune preuve dans ce dossier ne les établit.
- Mouvements natifs des clés : lus par l'audit sur le périmètre de la section 4, revérifiés ici seulement pour brace227 et kraben006 sur Ethereum. Soldes lus à la date indiquée, ils peuvent changer.

### Zoomman17

Wallet `0x92a8eec13a691af81a1a196b7594c1eccfa0eebc`, DEPOSIT_WALLET, clé propriétaire `0xd90d00130519086d412d2b9ffac2bb01f71ef444`. Dossier complet : `cases/zoomman17.md`.

**Comportements suspects réellement observés.** Ce sont des faits, pas des preuves d'intention.

- Premier événement Polymarket le 2026-10-06 00:45 UTC, premier achat sur la famille le 2026-10-06 00:47 UTC.
- Concentration : 41,0 % de ses achats sur le Ballon masculin (17 133,75 $ sur 3 issues, 24 618,40 $ ailleurs).
- Mbappé devant Yamal : 6 672,96 $ pour 13 357,82 parts, prix moyen 0,500 ; 6 182,05 $ avant le 13 oct. 18:51 UTC, 6 672,96 $ avant l'article. Part des achats taker du token avant l'article : 3,8 %.
- Autres issues : Harry Kane win / Yes (10 081 $); Rodri finish 4th in / Yes (380 $).
- Plus grosse décision taker : 1 500,00 $ le 10-09 20:13 UTC, Kylian Mbappé or Lamine Yamal / Mbappé, 0,74 fois le volume du token sur les 24 h précédentes.
- Résultat : non affirmé. Compte non soldé ou non réconcilié : résidu de calcul 0,0023 $, solde pUSD 0,00 $, 4 positions ouvertes valant 0,00 $. Écart brut retraits moins dépôts : -2 849,19 $.

**Preuves on-chain vérifiables.**

- Premier financement : 2026-10-06 00:45:05 UTC, 857,25 $, `0xc401f99aae37edbab349f5130cdf1db71d4c23539a741594aa8aa91b4dbc092e`. Le pUSD est frappé depuis l'adresse zéro, qui n'est pas un financeur.
- Dépôts : 5, 9 743,19 $.
  - 857,25 $ : la clé propriétaire elle-même, Ethereum → Relay
  - 2 700,42 $ : la clé propriétaire elle-même, Ethereum → Relay
  - 5 438,42 $ : la clé propriétaire elle-même, Ethereum → Relay
  - 488,56 $ : la clé propriétaire elle-même, Ethereum → Relay
  - 258,54 $ : la clé propriétaire elle-même, Ethereum → Relay
- Sorties : 3, 6 894,00 $.
  - 11/10 22:23 UTC, 50,00 $ → `0xD90d00130519086d412D2b9FFAC2Bb01f71ef444` (Ethereum), reçu 50,0000 USDC, PROTOCOL_CONFIRMED. Retrait `0x1bb4cf39845d19c62166ed1cb3e2b0f4c37a0c0298ce7cba062ff5e2217c33f8`, paiement `0xd65619db14590731fd8f81834bc692aa4ee22add918a8c70b898ba3e81c01899`.
  - 12/10 17:04 UTC, 100,00 $ → `0xD90d00130519086d412D2b9FFAC2Bb01f71ef444` (Ethereum), reçu 100,0000 USDC, PROTOCOL_CONFIRMED. Retrait `0x53d6a39bf44b025c21d3f2a071931cbaedd255bc7a7370cc402fcf378e74b67e`, paiement `0x06fb9a3e9634ab9c66f7555fb3f4b4a82a0b9028380b3d918b5dead4fd01e5d6`.
  - 27/10 02:08 UTC, 6 744,00 $ → `0xD90d00130519086d412D2b9FFAC2Bb01f71ef444` (Ethereum), reçu 6 744,0000 USDC, PROTOCOL_CONFIRMED. Retrait `0x42bfdbb50dd6482190bd0e60fe9deeac157b1a6f6f1e5e1262b35c7bed66df97`, paiement `0x0f5ba8886f979909e2b5b54739641e860d8ed8cee449b60db1f5287f075ad8b0`.
- `0xd90d0013…f444` (Ethereum) : reçu 6 894,00, solde du même jeton 0,00, lu le 2026-11-02 08:07 UTC.
- Saut suivant de `0xd90d0013…f444` : 6 745,00 $ vers `0x8c5dc729…10fe`, EOA, nonce 1, `0x7a90713919396d421938d9fd885a4d11de93724f03cfadf7198cc8475203aef6`.
- Relations à identifiant stable : ONCHAIN_CONFIRMED 12, PROTOCOL_CONFIRMED 8, SERVICE_INTERACTION 1.

**Liens éventuels avec les autres wallets.**

- SERVICE_MESURE : `0xc8a6871d…8d64`, aussi 0x86544e4dfde, brace227, kraben006, walletwallet8424.
- SERVICE_ETIQUETE : `0x4cd00e38…bc31`, aussi brace227, kraben006.
- SERVICE_MESURE : `0x58f298e3…0214`, aussi kraben006.
- Lien discriminant : aucun. Transfert direct avec un autre dossier : aucun trouvé sur le périmètre lu par l'audit (section 4), non exhaustif, revérifié ici seulement pour les clés de brace227 et kraben006 sur Ethereum.
- Issues aussi détenues par d'autres nommés : Kylian Mbappé or Lamine Yamal / Mbappé (10 autres); Harry Kane win / Yes (4 autres); Rodri finish 4th in / Yes (3 autres).

**Explications alternatives et faux positifs.**

- La famille ne pèse qu'environ 41 % de ses achats : ce compte parie largement ailleurs, ce qui rend moins probable un compte créé pour cette seule affaire.
- Faux positifs d'une règle de « financeur commun » : `0xc8a6871d…8d64`, `0x4cd00e38…bc31`, `0x58f298e3…0214`. Ce sont des services, ils ne relient personne.
- Biais de sélection : ce compte est étudié parce que la presse l'a nommé après le résultat. Taille et âge ne sont donc pas des résultats indépendants.

**Résultats des contrôles statistiques.** Lecture individuelle descriptive : n effectif de l'affaire = 1, sans puissance par wallet.

- S_A scellé : vu, 1 paire(s) avec comportement, score maximal 1, **0 priorité**. Comparaison exploratoire, hors R3.
- Alerte A0 : 2026-10-11 14:00:00, Kylian Mbappé or Lamine Yamal / Mbappé, 3 wallets, avant le 13 oct. 18:51.
- Alerte du recensement E1G : membre d'aucune.
- Rafales E2, membre de : 0 à 5 min, 1 à 15 min, 1 à 60 min.
- Petits puis gros E3 : non.
- Combinaisons inhabituelles E4 v2 : 0 paire aux deux dates, sur les trois graines. E4 ne voit qu'un extrême, section 5.
- Autres nommés achetant le même token à moins de 5 min : brace227 ; à moins de 60 min : 3.
- Financement E6 : 2,6 min entre le dernier dépôt et le premier achat. 4 comparateurs sur 20 à historique complet font aussi court ou plus court. Publié en version 1 : 4 sur 42, lignes coupées comprises. Confondu avec l'âge du compte.
- Top 20 des décisions E7 : absent.
- Quatre rangs exacts détenus avant l'article : non. Combinaison cotée environ 0,28 à cette date, donc pas rare par rapport aux prix.

**Niveau de confiance et limites.**

- Lien étiquette vers adresse : **moyenne à élevée** (parts de la capture).
- Flux : **élevée** sur 20 relations lues sur la chaîne, **moyenne** sur 1 relation dépendant d'un service ou d'une étiquette.
- Coordination et information privilégiée : **non démontrées**, aucune preuve dans ce dossier ne les établit.
- Mouvements natifs des clés : lus par l'audit sur le périmètre de la section 4, revérifiés ici seulement pour brace227 et kraben006 sur Ethereum. Soldes lus à la date indiquée, ils peuvent changer.

### kraben006

Wallet `0x84212ee459d1edaf35983bbec342b0806282d8ec`, DEPOSIT_WALLET, clé propriétaire `0x101b5f4dc0886c32e2b75972101aeaf9f338fb65`. Dossier complet : `cases/kraben006.md`.

**Comportements suspects réellement observés.** Ce sont des faits, pas des preuves d'intention.

- Premier événement Polymarket le 2026-10-01 18:31 UTC, premier achat sur la famille le 2026-10-01 18:33 UTC.
- Concentration : 99,5 % de ses achats sur le Ballon masculin (18 278,36 $ sur 6 issues, 91,15 $ ailleurs).
- Mbappé devant Yamal : 4 603,93 $ pour 9 279,59 parts, prix moyen 0,496 ; 728,61 $ avant le 13 oct. 18:51 UTC, 4 603,93 $ avant l'article. Part des achats taker du token avant l'article : 2,1 %.
- Autres issues : Harry Kane win / Yes (10 467 $); Lionel Messi finish 5th in / Yes (1 224 $); Rodri finish 4th in / Yes (765 $).
- Plus grosse décision taker : 980,81 $ le 10-01 22:29 UTC, Harry Kane win / Yes, 0,04 fois le volume du token sur les 24 h précédentes.
- Résultat : compte soldé, **retraits moins dépôts 9 904,07 $**, hors gas et coûts hors de ce wallet.

**Preuves on-chain vérifiables.**

- Premier financement : 2026-10-01 18:31:03 UTC, 191,58 $, `0x4431828712a924d5845de5f1779ad98eabf3563d55f299f46dde35700129a5a4`. Le pUSD est frappé depuis l'adresse zéro, qui n'est pas un financeur.
- Dépôts : 14, 5 689,47 $.
  - 191,58 $ : la clé propriétaire elle-même, Ethereum → Relay
  - 727,80 $ : la clé propriétaire elle-même, Ethereum → Relay
  - 1 000,00 $ : la clé propriétaire elle-même, Ethereum → Relay
  - 48,66 $ : la clé propriétaire elle-même, Ethereum → Relay
  - 328,00 $ : la clé propriétaire elle-même, Ethereum → Relay
  - et 9 autres, dans le dossier complet.
- Sorties : 5, 15 593,54 $.
  - 07/10 00:33 UTC, 438,67 $ → `0x101B5f4Dc0886c32E2b75972101AeAF9F338fb65` (Ethereum), reçu 438,2799 USDC, PROTOCOL_CONFIRMED. Retrait `0x9e313ca47e181cfe4e0368653ed28a63826eded1ce4bbd50909db123ca99166e`, paiement `0xb10a9439124aa29e783787d6a1399398cd1f2816b5d111c3c8cd60e19803d104`.
  - 11/10 23:00 UTC, 1,04 $ → `0x101B5f4Dc0886c32E2b75972101AeAF9F338fb65` (Ethereum), reçu 1,0420 USDC, PROTOCOL_CONFIRMED. Retrait `0xfe643b8d991f269ced5467f6d5d8d160b514f6465d55bb462f4f2ebeed232ed8`, paiement `0x78a14f612e551d846e49c906c906dbcbc56a4e2234b84f678d11eacb50b612f9`.
  - 26/10 23:10 UTC, 11 078,88 $ → `0x101B5f4Dc0886c32E2b75972101AeAF9F338fb65` (Ethereum), reçu 11 078,8792 USDC, PROTOCOL_CONFIRMED. Retrait `0x95a3f9ded5c4e8e1a65fcaa53555ef4da06f9aba958f7476d4b8e99446453e98`, paiement `0x36e90fcd9e601dcc2ddab8f2a1bdda23074f63d63e751d89d1ce5d7941523b35`.
  - 26/10 23:30 UTC, 4 054,20 $ → `0x101B5f4Dc0886c32E2b75972101AeAF9F338fb65` (Ethereum), reçu 4 054,1988 USDC, PROTOCOL_CONFIRMED. Retrait `0x758a809484f6b8e5f3c72e135fdbdc950e105944921b06c192e03c3768564599`, paiement `0xaebdc4159eee3a84bc50b1be5ab6cefebb85c9150e9643ebbcdcd072e5f552b4`.
  - 26/10 23:39 UTC, 20,75 $ → `0x101B5f4Dc0886c32E2b75972101AeAF9F338fb65` (Ethereum), reçu 20,7486 USDC, PROTOCOL_CONFIRMED. Retrait `0x841f53dee5fce76b516ebf8e595606546d19c8dfd67a951d3ff8a0c5cdeba3a4`, paiement `0x301e162c42063edd7ef55c984bacee1b843d232835b8a0c11dcfbcb8cb79af59`.
- `0x101b5f4d…fb65` (Ethereum) : reçu 15 593,15, solde du même jeton 15 154,83, lu le 2026-11-02 08:07 UTC.
- Relations à identifiant stable : ONCHAIN_CONFIRMED 26, PROTOCOL_CONFIRMED 19, SERVICE_INTERACTION 7.

**Liens éventuels avec les autres wallets.**

- SERVICE_MESURE : `0xc8a6871d…8d64`, aussi 0x86544e4dfde, brace227, walletwallet8424, zoomman17.
- SERVICE_ETIQUETE : `0x4cd00e38…bc31`, aussi brace227, zoomman17.
- SERVICE_MESURE : `0xc1d13492…a1b5`, aussi brace227.
- SERVICE_MESURE : `0x58f298e3…0214`, aussi zoomman17.
- **Transfert direct depuis le dossier brace227 :** le 2026-10-04 13:54:35 UTC, cette clé reçoit 0,002048943671205553 ETH, environ 5,53 $, de `0xc852b0938f5ad79b640d105ed11c14499454af26`, `0xd07bea20a22d9381e0ab364e7a7421776318c6f4aa7258799638472ad7092b98`. Détail et hypothèses : section 4. Aucun autre transfert direct trouvé sur le périmètre lu par l'audit, revérifié ici sur Ethereum pour cette clé. Aucune adresse partagée discriminante.
- Étiquettes ChangeNOW de Blockscout, source unique, sur cette clé : 834,85 USDC reçus le 23 fév. 2026, et 0,00247 ETH partis le 4 oct. vers `0x7e67…`, puis `0x3f3E…`. Section 6.
- Issues aussi détenues par d'autres nommés : Kylian Mbappé or Lamine Yamal / Mbappé (10 autres); Harry Kane win / Yes (4 autres); Lamine Yamal finish 3rd in / Yes (4 autres); Kylian Mbappé finish 2nd in / Yes (2 autres).

**Explications alternatives et faux positifs.**

- Retrait principal 2,8 min avant celui de brace227 : aucun signal mesurable. Il suit de 48 s sa vente à 0,999, vitesse ordinaire, 10 vendeurs comparables sur 20 retirent aussi en moins de 5 min (section 4).
- Le plus progressif : 14 petits dépôts depuis le 1er octobre, rotation visible de Kane vers les rangs exacts à mesure que ces marchés ouvrent, comme le note la capture. Compatible avec un parieur actif qui prend ses gains et se repositionne.
- Faux positifs d'une règle de « financeur commun » : `0xc8a6871d…8d64`, `0x4cd00e38…bc31`, `0xc1d13492…a1b5`, `0x58f298e3…0214`. Ce sont des services, ils ne relient personne.
- Biais de sélection : ce compte est étudié parce que la presse l'a nommé après le résultat. Taille et âge ne sont donc pas des résultats indépendants.

**Résultats des contrôles statistiques.** Lecture individuelle descriptive : n effectif de l'affaire = 1, sans puissance par wallet.

- S_A scellé : vu, 0 paire(s) avec comportement, score maximal 0, **0 priorité**. Comparaison exploratoire, hors R3.
- Alerte A0 : membre d'aucune.
- Alerte du recensement E1G : membre d'aucune.
- Rafales E2, membre de : 0 à 5 min, 0 à 15 min, 2 à 60 min.
- Petits puis gros E3 : non.
- Combinaisons inhabituelles E4 v2 : 0 paire aux deux dates, sur les trois graines. E4 ne voit qu'un extrême, section 5.
- Autres nommés achetant le même token à moins de 5 min : aucun ; à moins de 60 min : 4.
- Financement E6 : 2,2 min entre le dernier dépôt et le premier achat. 3 comparateurs sur 20 à historique complet font aussi court ou plus court. Publié en version 1 : 3 sur 42, lignes coupées comprises. Confondu avec l'âge du compte.
- Top 20 des décisions E7 : absent.
- Quatre rangs exacts détenus avant l'article : oui. Combinaison cotée environ 0,28 à cette date, donc pas rare par rapport aux prix.

**Niveau de confiance et limites.**

- Lien étiquette vers adresse : **élevée** (parts de la capture, et vente de Kane pour Yamal 3e conforme à la note de la capture).
- Flux : **élevée** sur 45 relations lues sur la chaîne, **moyenne** sur 7 relations dépendant d'un service ou d'une étiquette.
- Connexion financière directe avec brace227 : **établie**, 1 transfert. Contrôle commun, coordination et information privilégiée : **non démontrés**. Le transfert n'en est pas la preuve.
- Mouvements natifs des clés : lus par l'audit sur le périmètre de la section 4, revérifiés ici seulement pour brace227 et kraben006 sur Ethereum. Soldes lus à la date indiquée, ils peuvent changer.

### OuldLm3alem

Wallet `0x71ae923f12eb947c58365287691cf5a10bc3e5bf`, DEPOSIT_WALLET, clé propriétaire `0x1b500b6c40a2ff0930e540e8f53c559a32e75f2c`. Dossier complet : `cases/ouldlm3alem.md`.

**Comportements suspects réellement observés.** Ce sont des faits, pas des preuves d'intention.

- Premier événement Polymarket le 2026-10-22 18:39 UTC, premier achat sur la famille le 2026-10-22 18:49 UTC.
- Concentration : 100,0 % de ses achats sur le Ballon masculin (51 188,21 $ sur 6 issues, 0,00 $ ailleurs).
- Mbappé devant Yamal : 21 886,41 $ pour 30 045,94 parts, prix moyen 0,728 ; 0,00 $ avant le 13 oct. 18:51 UTC, 8 186,05 $ avant l'article. Part des achats taker du token avant l'article : 2,8 %.
- Autres issues : Kylian Mbappé finish 2nd in / Yes (15 454 $); Lamine Yamal finish 3rd in / Yes (8 287 $); Rodri finish 4th in / Yes (2 895 $).
- Plus grosse décision taker : 3 020,43 $ le 10-22 18:50 UTC, Lamine Yamal finish 3rd in / Yes, 2,52 fois le volume du token sur les 24 h précédentes.
- Résultat : non affirmé. Compte non soldé ou non réconcilié : résidu de calcul 19,4798 $, solde pUSD 19,68 $, 0 positions ouvertes valant 0,00 $. Écart brut retraits moins dépôts : 21 083,66 $.

**Preuves on-chain vérifiables.**

- Premier financement : 2026-10-22 18:39:23 UTC, 23 386,26 $, `0xaed3dd931c9bbc163818983c01b6ebc43cb3885f43dcb18359d3651e7f5fe4dd`. Le pUSD est frappé depuis l'adresse zéro, qui n'est pas un financeur.
- Dépôts : 3, 56 167,11 $.
  - 23 386,26 $ : `0xa3222357…59b3` (nonce 1) → adresse de pont, Ethereum → Relay
  - 16 798,01 $ : KuCoin Hot Wallet 2 → `5oXG1xh68W…paxJ` (Solana) → Relay
  - 15 982,84 $ : `0xee7ae85f…4055` (nonce 1) → adresse de pont, Arbitrum → Relay
- Sorties : 3, 77 250,77 $.
  - 26/10 21:40 UTC, 100,00 $ → `0xaE232f7885946Fda51B3F1DAC7e10FfAaE00C026` (BSC), reçu 0,1333 BNB, PROTOCOL_CONFIRMED. Retrait `0x8d84c3cf0d15c5e573b71b75c43182837a9d88b3d3ad1ed078c11ffef9c58a40`, paiement `0xe9c0d3b85a632cf54ebdbdb10dd755b85797f82888e87496860f6ba16751bfb6`.
  - 26/10 21:41 UTC, 100,00 $ → `0xaE232f7885946Fda51B3F1DAC7e10FfAaE00C026` (BSC), reçu 99,7962 USDT, PROTOCOL_CONFIRMED. Retrait `0x3e1349f5f6e9acd7450f9a7cdac622ca47d73811793f8cbef730063fdb441825`, paiement `0x966c40950de7e86379fa496c3cf2005f6e589c075fdea67b7ee021c0cf3a33ad`.
  - 26/10 23:50 UTC, 77 050,77 $ → `0x1B500B6c40a2Ff0930e540e8F53C559a32E75f2c` (Polygon), reçu 839 893,7315 POL, SERVICE_INTERACTION. Retrait `0x909d9602d5ad975b2f30c66d4a058592306e2468a002dd0a691170b61677a6f1`.
- `0xae232f78…c026` (BSC) : reçu 99,80, solde du même jeton 99,80, lu le 2026-11-02 08:07 UTC.
- Swap dans la transaction de retrait `0x909d9602d5ad975b2f30c66d4a058592306e2468a002dd0a691170b61677a6f1` : le paiement se lit sur la chaîne, `LogTransfer` de 839 893,73 POL vers la clé, log 463. La version 1 écrivait à tort qu'il ne laisse pas de log. La relation reste classée SERVICE_INTERACTION dans `graphs/relations.jsonl`, fichier non modifié.
- Sortie : 108 s plus tard, 23:52:41 UTC, la clé échange 839 000 POL contre 75 946,74 USDT par `0xdc264714…7c9f`, `0x8c35829294c002aabcd2bd518e88f46f86e4c5a075c6e89938d4532cc62dd2c3`, USDT reçus par la clé. Son solde USDT est de 0 le 2 nov. : ces fonds sont repartis, et la suite n'est pas lue ici, elle relève de l'enquête flow-trace.
- Relations à identifiant stable : ONCHAIN_CONFIRMED 6, PROTOCOL_CONFIRMED 5, SERVICE_INTERACTION 2.

**Liens éventuels avec les autres wallets.**

- SERVICE_ETIQUETE : `BmFdpraQhk…ymy6`, aussi 0xdd97e6, cookedrice, thin, vidente.
- SERVICE_MESURE : `0xee7ae85f…4055`, aussi wen.
- Lien discriminant : aucun. Transfert direct avec un autre dossier : aucun trouvé sur le périmètre lu par l'audit (section 4), non exhaustif, revérifié ici seulement pour les clés de brace227 et kraben006 sur Ethereum.
- Une exécution de carnet d'ordres entre OuldLm3alem et 0x86544e4dfde : 520,97 parts à 0,53, `0x870eaa6cb8298d7a02379b48093d4633af4f77ba58638bfc78ff9b0146f30b48`. Ordinaire sur un carnet.
- Issues aussi détenues par d'autres nommés : Kylian Mbappé or Lamine Yamal / Mbappé (10 autres); Lamine Yamal finish 3rd in / Yes (4 autres); Kylian Mbappé finish 2nd in / Yes (2 autres); Lionel Messi finish 5th in / Yes (3 autres).

**Explications alternatives et faux positifs.**

- Premier événement le 22 octobre, 20 heures avant l'article, à des prix déjà élevés sur des issues favorites. Journal du Coin et Numerama évoquent eux-mêmes la possibilité de suiveurs dans cette affaire.
- Faux positifs d'une règle de « financeur commun » : `BmFdpraQhk…ymy6`, `0xee7ae85f…4055`. Ce sont des services, ils ne relient personne.
- Biais de sélection : ce compte est étudié parce que la presse l'a nommé après le résultat. Taille et âge ne sont donc pas des résultats indépendants.

**Résultats des contrôles statistiques.** Lecture individuelle descriptive : n effectif de l'affaire = 1, sans puissance par wallet.

- S_A scellé : vu, 1 paire(s) avec comportement, score maximal 1, **0 priorité**. Comparaison exploratoire, hors R3.
- Alerte A0 : 2026-10-22 19:00:00, Lamine Yamal finish 3rd in / Yes, 3 wallets, après le 13 oct. 18:51.
- Alerte du recensement E1G : 2026-10-22 19:00:00, Lamine Yamal finish 3rd in / Yes.
- Rafales E2, membre de : 0 à 5 min, 0 à 15 min, 0 à 60 min.
- Petits puis gros E3 : 10-23 10:53, 2 882,51 $ après une médiane de 397,59 $.
- Combinaisons inhabituelles E4 v2 : hors univers au 13 oct., 0 paire au 23 oct. sur les trois graines. E4 ne voit qu'un extrême, section 5.
- Autres nommés achetant le même token à moins de 5 min : aucun ; à moins de 60 min : 0.
- Financement E6 : 10,1 min entre le dernier dépôt et le premier achat. 7 comparateurs sur 20 à historique complet font aussi court ou plus court. Publié en version 1 : 7 sur 42, lignes coupées comprises. Confondu avec l'âge du compte.
- Top 20 des décisions E7 : absent.
- Quatre rangs exacts détenus avant l'article : oui. Combinaison cotée environ 0,28 à cette date, donc pas rare par rapport aux prix.

**Niveau de confiance et limites.**

- Lien étiquette vers adresse : **élevée** (nom exact).
- Flux : **élevée** sur 11 relations lues sur la chaîne, **moyenne** sur 2 relations dépendant d'un service ou d'une étiquette.
- Coordination et information privilégiée : **non démontrées**, aucune preuve dans ce dossier ne les établit.
- La trace s'arrête à : `5oXG1xh68W…paxJ`. Seul le service connaît le compte d'origine.
- Mouvements natifs des clés : lus par l'audit sur le périmètre de la section 4, revérifiés ici seulement pour brace227 et kraben006 sur Ethereum. Soldes lus à la date indiquée, ils peuvent changer.

### 0xdd97e6

Wallet `0xdd97e6ad12ca4dd18a88804fb5ed7ed429849464`, DEPOSIT_WALLET, clé propriétaire `0xcf7b90deaf46d27b2b8f2f54a099d82879dd19ad`. Dossier complet : `cases/0xdd97e6.md`.

**Comportements suspects réellement observés.** Ce sont des faits, pas des preuves d'intention.

- Premier événement Polymarket le 2026-10-20 09:11 UTC, premier achat sur la famille le 2026-10-20 09:12 UTC.
- Concentration : 98,8 % de ses achats sur le Ballon masculin (43 592,18 $ sur 10 issues, 515,00 $ ailleurs).
- Mbappé devant Yamal : 6 493,36 $ pour 9 266,76 parts, prix moyen 0,701 ; 0,00 $ avant le 13 oct. 18:51 UTC, 6 493,36 $ avant l'article. Part des achats taker du token avant l'article : 3,6 %.
- Autres issues : Lamine Yamal finish 3rd in / Yes (15 968 $); Kylian Mbappé finish 2nd in / Yes (9 825 $); Lamine Yamal finish in the top 2 of / No (3 864 $).
- Plus grosse décision taker : 3 671,01 $ le 10-21 17:32 UTC, Kylian Mbappé or Lamine Yamal / Mbappé, 0,45 fois le volume du token sur les 24 h précédentes.
- Résultat : compte soldé, **retraits moins dépôts 19 083,95 $**, hors gas et coûts hors de ce wallet.

**Preuves on-chain vérifiables.**

- Premier financement : 2026-10-20 09:11:08 UTC, 19 760,16 $, `0xf9ae2a36fcd4d92b72231b4bad40cca7fdc3a48f9620eace4cf9479bbbfb6f05`. Le pUSD est frappé depuis l'adresse zéro, qui n'est pas un financeur.
- Dépôts : 2, 44 059,16 $.
  - 19 760,16 $ : `0x6bf18baf…7e95` (nonce 966 008) → adresse de pont, BSC → Relay
  - 24 299,00 $ : KuCoin Hot Wallet 2 → `4MMHYz6K6z…zgE1` (Solana) → Relay
- Sorties : 1, 63 143,10 $.
  - 27/10 00:49 UTC, 63 143,10 $ → `0xca8B1f1a56A0Fe8947D325BAAFA286F5bD4D6165` (Ethereum), reçu 26,9716 ETH, PROTOCOL_CONFIRMED. Retrait `0x16ae2a26a481e38097d3b0cbcec9a704dc07d98e7de3b9d58935e6dc93f4b208`, paiement `0xf1ab0c279b35125a7101edf8092811b813e4a8566a82ad7d23e921d83b0d7718`.
- `0xca8B1f1a…6165` détient 26,9716 ETH, nonce 0, lu le 2 nov. : aucune sortie depuis la réception.
- Relations à identifiant stable : ONCHAIN_CONFIRMED 4, PROTOCOL_CONFIRMED 3, SERVICE_INTERACTION 1.

**Liens éventuels avec les autres wallets.**

- SERVICE_ETIQUETE : `BmFdpraQhk…ymy6`, aussi cookedrice, ouldlm3alem, thin, vidente.
- Lien discriminant : aucun. Transfert direct avec un autre dossier : aucun trouvé sur le périmètre lu par l'audit (section 4), non exhaustif, revérifié ici seulement pour les clés de brace227 et kraben006 sur Ethereum.
- Issues aussi détenues par d'autres nommés : Kylian Mbappé or Lamine Yamal / Mbappé (10 autres); Lamine Yamal finish 3rd in / Yes (4 autres); Kylian Mbappé finish 2nd in / Yes (2 autres); Lionel Messi finish 5th in / Yes (3 autres).

**Explications alternatives et faux positifs.**

- Premier événement le 20 octobre, après l'ouverture des marchés de rangs, à des prix où ces issues étaient déjà favorites. Compatible avec le suivi du marché. Son lien avec l'étiquette n'est pas certifié.
- Faux positifs d'une règle de « financeur commun » : `BmFdpraQhk…ymy6`. Ce sont des services, ils ne relient personne.
- Biais de sélection : ce compte est étudié parce que la presse l'a nommé après le résultat. Taille et âge ne sont donc pas des résultats indépendants.

**Résultats des contrôles statistiques.** Lecture individuelle descriptive : n effectif de l'affaire = 1, sans puissance par wallet.

- S_A scellé : vu, 2 paire(s) avec comportement, score maximal 1, **0 priorité**. Comparaison exploratoire, hors R3.
- Alerte A0 : 2026-10-22 19:00:00, Lamine Yamal finish 3rd in / Yes, 3 wallets, après le 13 oct. 18:51.
- Alerte du recensement E1G : 2026-10-22 19:00:00, Lamine Yamal finish 3rd in / Yes.
- Rafales E2, membre de : 0 à 5 min, 0 à 15 min, 0 à 60 min.
- Petits puis gros E3 : non.
- Combinaisons inhabituelles E4 v2 : hors univers au 13 oct., 0 paire au 23 oct. sur les trois graines. E4 ne voit qu'un extrême, section 5.
- Autres nommés achetant le même token à moins de 5 min : aucun ; à moins de 60 min : 3.
- Financement E6 : 1,5 min entre le dernier dépôt et le premier achat. 1 comparateur sur 20 à historique complet fait aussi court ou plus court. Publié en version 1 : 1 sur 42, lignes coupées comprises. Confondu avec l'âge du compte.
- Top 20 des décisions E7 : absent.
- Quatre rangs exacts détenus avant l'article : oui. Combinaison cotée environ 0,28 à cette date, donc pas rare par rapport aux prix.

**Niveau de confiance et limites.**

- Lien étiquette vers adresse : **moyenne** (préfixe de presse unique).
- Flux : **élevée** sur 7 relations lues sur la chaîne, **moyenne** sur 1 relation dépendant d'un service ou d'une étiquette.
- Coordination et information privilégiée : **non démontrées**, aucune preuve dans ce dossier ne les établit.
- La trace s'arrête à : `4MMHYz6K6z…zgE1`. Seul le service connaît le compte d'origine.
- Mouvements natifs des clés : lus par l'audit sur le périmètre de la section 4, revérifiés ici seulement pour brace227 et kraben006 sur Ethereum. Soldes lus à la date indiquée, ils peuvent changer.

## 3. Réconciliation des retraits

L'erreur corrigée : pour le retrait de 77 050,77 $ d'OuldLm3alem, mon code avait pris l'adresse zéro pour destination, alors que c'est le burn de pUSD. La règle suit maintenant ce que le wallet envoie après ce burn, avec un test sur la forme réelle du reçu (`tools/test_case_chain.py`). Aucune relation ne vise plus l'adresse zéro.

| Dossier | Retraits API $ | Retraits suivis | Vers Relay avec paiement lu | Autres | Sans destination |
|---|---:|---:|---:|---:|---:|
| Thin-Disclaimer-Life | 80 037,93 | 4 | 4 | 0 | 0 |
| VidenteRibeira | 51 509,88 | 1 | 1 | 0 | 0 |
| cookedrice | 39 158,78 | 1 | 1 | 0 | 0 |
| WenZhuanBuPei | 27 724,79 | 1 | 1 | 0 | 0 |
| 0x86544e4dfde | 74 198,32 | 1 | 1 | 0 | 0 |
| brace227 | 22 036,76 | 4 | 4 | 0 | 0 |
| walletwallet8424 | 35 546,89 | 1 | 1 | 0 | 0 |
| Zoomman17 | 6 894,00 | 3 | 3 | 0 | 0 |
| kraben006 | 15 593,54 | 5 | 5 | 0 | 0 |
| OuldLm3alem | 77 250,77 | 3 | 2 | 1 | 0 |
| 0xdd97e6 | 63 143,10 | 1 | 1 | 0 | 0 |

Contre-vérification après audit, depuis les reçus en cache : chaque retrait a une sortie du wallet et une destruction de pUSD du même montant, 25 sur 25, 493 094,756177 $. Chaque dépôt a une frappe du même montant, 46 sur 46, 304 137,63473 $.

Les liens Relay classés `PROTOCOL_CONFIRMED` portent le même identifiant dans le log d'escrow et dans le paiement, lus sur les deux chaînes. Cette preuve ne dépend pas de l'API de Relay. L'API reste utile pour trouver le paiement, et sa route publique disparaît le 24 novembre.

## 4. Liens de financement reclassés

Une règle naïve de « financeur commun » relierait **21 paires sur 55**. Après classement, **0 paire** repose sur une adresse partagée discriminante. **Mais 1 paire sur 55, brace227 et kraben006, a un transfert direct entre clés**, que ce classement par adresses partagées ne pouvait pas voir.

| Adresse partagée | Classe | Dossiers | Aussi chez les témoins | Pourquoi |
|---|---|---|---|---|
| `BmFdpraQhk…ymy6` | SERVICE_ETIQUETE | 0xdd97e6, cookedrice, ouldlm3alem, thin, vidente | token_oppose 1 | KuCoin Hot Wallet 2, selon orbmarkets.io |
| `0xc8a6871d…8d64` | SERVICE_MESURE | 0x86544e4dfde, brace227, kraben006, walletwallet8424, zoomman17 | meme_token 1, token_oppose 3, fraiches_recensement 1 | 215 sorties et 211 entrées en 3,75 h, un seul payeur |
| `0x4cd00e38…bc31` | SERVICE_ETIQUETE | brace227, kraben006, zoomman17 | non | Relay Depository, selon api.relay.link |
| `GxjcMTWWDc…nvBW` | SERVICE_MESURE | cookedrice, vidente | non | Environ 1,2 transaction par minute. Sur 120 transactions lues : 18 entrées, 95 sorties, 67 destinataires. Sur 400 tirées : 73 entrées, médiane 270 $,  |
| `0xee7ae85f…4055` | SERVICE_MESURE | ouldlm3alem, wen | token_oppose 1 | Polygon : 1 173 sorties vers 824 destinataires en 12 h autour du 18 oct. Arbitrum : 890 sorties vers 743 destinataires en 12 h autour du 26 oct. Appel |
| `0x0ce9bdf3…f06d` | SERVICE_MESURE | 0x86544e4dfde, walletwallet8424 | non | 85 sorties vers 57 destinataires en 3,8 h |
| `0xc1d13492…a1b5` | SERVICE_MESURE | brace227, kraben006 | non | Contrat vérifié nommé SwftSwap. 549 sorties vers 454 destinataires en 10 h |
| `0x58f298e3…0214` | SERVICE_MESURE | kraben006, zoomman17 | non | Nonce de 114 468 |

**Transferts directs.** Le scan d'origine (33 adresses, Polygon et Ethereum, stablecoins, pUSD et positions, depuis le 25 sept., `graphs/direct_transfers.json`) rendait 0 transfert. Il ne lisait ni l'ETH natif ni l'historique ancien des clés : ce « 0 » de la version 1 était faux pour une paire. Après audit : **1 transfert natif direct, brace227 vers kraben006**, détaillé ci-dessous. Selon l'audit, aucun autre sur 27 adresses EVM lues sur Ethereum, Arbitrum et Base, ni en POL natif sur 46 adresses, ni sur les 9 adresses Solana lues. Ce scan n'est pas refait ici. Pour les deux clés de la paire, l'historique Ethereum complet ne montre que ce seul transfert, et leurs seules contreparties communes sont des services : USDC, Relay Depository, solveur Relay, SwftSwap.

**Exécutions et transactions communes.** Les onze historiques partagent 14 transactions, toutes décodées (`evidence/contre_verification_20261102/transactions_communes.json`). 8 sont des paiements en lot : 5 rebates ou récompenses, 3 redemptions de 20 comptes chacune. 5 sont des exécutions où deux dossiers sont makers face au même tiers, sans échange entre eux, dont une pour brace227 et kraben006 (24 oct. 16:41:44, ventes de Mbappé à 0,84). **1 seule est une exécution directe :** OuldLm3alem vend 520,97 parts à 0,53 à 0x86544e4dfde, le 26 oct. 13:29:02 UTC, `0x870eaa6cb8298d7a02379b48093d4633af4f77ba58638bfc78ff9b0146f30b48`. C'est ordinaire sur un carnet.

**Montant et heure.** 0 candidat entre une sortie et une entrée à 6 h et 90 à 100,1 %, sur 25 sorties et 46 entrées. Placebo à dates décalées : 0 aussi. `graphs/links.json`.

### Un wallet non nommé financé par la clé de brace227

Signalé par l'enquête flow-trace, relu ici sur la chaîne : `evidence/contre_verification_20261102/wallet_0xa8e6.json`. **La version 1 écrivait qu'aucun wallet supplémentaire n'était relié aux onze : c'est faux.** Ce financement pèse bien plus que les 5,53 $ du circuit décrit plus bas.

**Le lien.** Le wallet `0xa8e64a3c08d1e2a4e9f25a2dd33b8ac3458f74a5` a pour propriétaire, `owner()` lu sur Polygon, `0x48ec106cf690edd58fcd6df1e8b6abfc16dab12d`. La clé de brace227 envoie à cette clé 2 210 USDC le 9 oct. à 20:28:35 UTC, `0x7e3aecb9b41e6d3f92f25b8760228f15e9b55e798cd27977eb7170445cf64349`, et 2 960 USDC le 10 oct. à 00:51:11, `0xb07c3c53a713d98aea1d1bd5d6facf849b6edc675c0fe2cfd3df5b791db20add`. Sur Ethereum, ce sont ses seules entrées de jetons avant le retrait du 27 oct., et sa plus ancienne transaction listée date du 9 oct. à 20:32:11, page complète (nonce de 14 pour 13 envois listés, écart non expliqué). Ses deux envois à Relay Depository, 2 200 et 2 965 USDC, sont reliés à ces deux dépôts par l'enregistrement Relay, `user` et `recipient` compris (`wallet_0xa8e6_preuves.json`), sans recoupement ici par identifiant sur la chaîne. **Selon cette comptabilité, les dépôts de ce wallet viennent de la clé de brace227.** Autres chaînes non lues, hormis un nonce de 0 sur Polygon.

**Le partage.** Les arrivées de SwftSwap des 9 et 10 oct. sur la clé de brace227 sont coupées en deux, celle du 16 oct. va tout entière au wallet de brace227. Au total, 34,2 % des 15 096,29 USDC reçus de SwftSwap vont à `0x48ec…` :

| Arrivée sur la clé de brace227 | Vers `0x48ec…` | Part | Vers le wallet de brace227 |
|---|---:|---:|---:|
| 9 oct. 20:03 et 20:06, 4 421,41 USDC | 2 210,00 | 49,98 % | 2 186,43 |
| 10 oct. 00:26, 5 925,84 USDC | 2 960,00 | 49,95 % | 2 986,82, en trois dépôts |
| **Sous-total, 9 et 10 oct.** | **5 170,00** | | **5 173,25** |
| 16 oct. 19:16, 4 749,03 USDC | 0 | 0 % | 4 749,54, en trois dépôts |

**Les paris.** Le wallet dépose 2 200 $ à 20:36:28 et achète à 20:37:10. brace227 dépose 2 186,43 $ à 20:49:05 et achète à 20:50, dont du Kane dès 21:14. Le wallet fait 16 achats, tous sur Kane Yes, 5 164,99 $ pour 8 061,89 parts, du 9 oct. à 20:37 au 11 oct. à 17:54 UTC. Il ne vend jamais.

**La sortie.** Redemption de 8 061,89 $ à 01:58:20 le 27 oct., dans le lot Kane. Retrait de 8 061,90 $ vers `0x48ec…` 16 h 51 min plus tard, à 18:49:06. Retraits moins dépôts : 2 896,90 $, hors des totaux de la section 2. Aucun retour vers la clé de brace227 sur Ethereum. Le 2 nov., `0x48ec…` détient 5 062,18 USDC. Il envoie aussi 2 501 USDC à `0x6A2522Df…7973` le 28 oct., rendus le 29 oct., adresse non analysée. Le 29 oct., il échange 3 000 USDC contre 2 969,57 mUSD, envoyés à Relay Depository : suite non lue ici.

**Ce que cela établit :** selon cette comptabilité, une même clé a financé deux comptes Polymarket, à parts presque égales les 9 et 10 oct., et les deux ont acheté Kane le 9 oct. à moins d'une heure d'écart, 741,47 $ chez brace227. **Ce que cela n'établit pas :** un propriétaire commun, puisque financer un compte n'est pas le contrôler, ni une information privilégiée. Rien ne dit non plus que c'est le douzième compte allégué par la presse (`reports/inventaire_adresses.md`).

| Hypothèse, aucune n'est une conclusion | Pour | Contre ou limite |
|---|---|---|
| Un même opérateur, deux comptes | Aucune transaction listée avant le 9 oct. sur Ethereum, dépôts venus de l'autre clé, parts presque égales les 9 et 10 oct. | Deux clés. brace227 vend son Kane à 0,999 le 26 oct. à 23:10, ce wallet attend le lot puis 16 h. 9 issues d'un côté, 1 de l'autre. La tranche du 16 oct. va tout entière à brace227. Son Kane des 9 et 10 oct. ne pèse que 954,04 $ sur 4 917,62 $ d'achats |
| Deux personnes qui misent à parts égales | Parts égales les 9 et 10 oct., deux clés, sorties différentes | Aucune trace de cet accord, invérifiable |
| Prêt ou don | Compatible avec deux virements ponctuels | Aucun remboursement visible sur Ethereum à ce jour, invérifiable |

**Autre proximité.** Dans les sorties gelées, ce wallet figure aussi dans une rafale E2 de 60 min sur Kane, le 11 oct. à 13:34:42 UTC, 10 667,19 $, avec 0x86544e4dfde et walletwallet8424 (`collective/derived/A_E2.json`). Ni brace227 ni aucun transfert entre eux n'y figurent. C'est une proximité d'achat sur un marché actif, pas un lien.

**Pourquoi la version 1 ne l'a pas vu, et ce que cela implique.** Le dossier suit les dépôts et les sorties de Polymarket, pas ce que la clé envoie ailleurs. Ce wallet ne détient pas Mbappé, donc il n'est pas dans la capture Upside. Avec un seul token, il est aussi écarté d'E4. **D'autres wallets du même type peuvent exister sans être vus.** L'enquête flow-trace cherche si d'autres adresses personnelles autour des onze possèdent un wallet : résultat en attente.

### Le circuit 7XUJs, clé de brace227, clé de kraben006

Heures UTC, 4 octobre 2026. Données en wei : `evidence/contre_verification_20261102/circuit_7xujs_brace_kraben.json`.

| # | Heure | De | Vers | Montant | Preuve | Niveau |
|---|---|---|---|---|---|---|
| 1 | 13:52:35 | `7XUJsJBNp7…frZc` (Solana) | Relay | 4,62476 USDT, plus 0,0298 de frais | `3XaPp5kRsL5M…NfEL` | **Démontré** |
| 2 | 13:52:47 | solveur Relay `0xadA5bb90…F7CB` | clé de brace227 `0xc852b093…af26` | 0,001692408 ETH | Même identifiant `0x30484595…7867` à l'octet près dans l'instruction Solana et le calldata de `0xb17e1c46…ce3c`, sans dépendre de l'API | **Démontré** : même ordre, valeur équivalente, pas les mêmes jetons |
| 3 | 13:54:35 | clé de brace227 | clé de kraben006 `0x101b5f4d…fb65` | 0,002048944 ETH, environ 5,53 $ | `0xd07bea20…2b98`, bloc 26119420, 2 nœuds, envoi simple sans données, 21 000 gas, succès | **Démontré.** Au moins 81,4 % du montant vient forcément du maillon 2 |
| 4 | 23:48:47 | clé de kraben006 | `0x7e67dF45…6E23` | 0,00247406 ETH | `0x1a39308b…dd71`, Blockscout | Transaction démontrée. **Continuité limitée** : au moins 22,7 % de ce qui a été reçu, 23,9 % gas compris |
| 5 | 23:56:59 | `0x7e67dF45…6E23` | `0x3f3Ee0a9…207B` | 0,00241406 ETH | `0x22710b5e…9c26`, Blockscout | Continuité à l'adresse : 1 entrée, 1 sortie. **Destination étiquetée « ChangeNOW Dep » par Blockscout**, source unique, non recoupée, environ 321 000 transactions selon un compteur Blockscout qui rend 0 pour `0x7e67…`, donc peu fiable |

**Continuité démontrée, maillons 1 à 3.** Le maillon 2 est prouvé par la chaîne seule. Pour le maillon 3, la clé détenait 0,000380298 ETH et n'a rien reçu d'autre entre les deux transactions : au moins 0,001668646 ETH envoyés proviennent donc du paiement. Soldes des deux clés lus sur Blockscout et recoupés au wei près à ces blocs sur un nœud d'archive.

**Simple succession, maillon 4.** Il arrive 9 h 54 min plus tard, sur une clé qui détenait déjà 0,002007933 ETH. Seuls 0,000466127 ETH envoyés, 0,000489889 gas compris, sont imposés par la comptabilité. Attribuer le reste à ce transfert dépendrait d'une convention de traçage : l'ETH est fongible. Aucune lecture ne relie ces montants au capital d'un dépôt Polymarket, fait en USDC. L'ETH étant fongible, le solde de la clé a pu payer le gas de ses dépôts suivants, 0,00018 ETH consommés après l'envoi.

**Le payeur Solana.** `7XUJs…` compte 8 signatures en tout, depuis le 6 juin 2026 : il reçoit 304,70 USDT, en envoie 300, et le 4 octobre envoie presque tout le reste. Il garde 0,047 USDT. Une seule requête Relay à son nom. Aucune des 27 adresses qu'il touche n'apparaît dans les dossiers, hormis le jeton USDT lui-même.

**Portée du vidage de la clé de brace227.** Le transfert laisse 0,000000494 ETH : 98,85 % du solde envoyés, 1,12 % de gas, 0,02 % restant. Cela ressemble à un envoi du solde maximal, pas à un montant choisi.

- *Ce qui est vidé :* l'ETH seul, et la clé était déjà presque vide. Ses USDT étaient à 0 depuis le 28 avril 2025.
- *Ce n'est ni un abandon, ni un compte drainé :* la clé reçoit 4 337,52 USDC de SwftSwap le 9 octobre, et 22 024,57 USDC y dorment encore le 2 novembre.
- *Ensuite :* le 9 octobre, ses transactions passent par des relais de gas à fort trafic, étiquetés MetaMask par Blockscout, et le 16 octobre elle reçoit 0,00202 ETH de `0x2CfF890f…`, étiqueté NEAR Intents. Le lien de cause avec le vidage n'est pas établi.
- *En montant, ce n'est pas un financement significatif :* 5,53 $, soit 0,055 % des dépôts de brace227 et 0,097 % de ceux de kraben006.
- *La lecture « don de gas » de l'audit est peu soutenue :* la clé de kraben006 détenait déjà 0,0020 ETH et n'en a consommé que 0,00018 depuis. Un donateur peut toutefois ignorer le solde du destinataire.
- *« Première sortie en 17 mois » ne vaut que pour Ethereum.* La clé a un nonce de 109 sur BSC, visible dans son dossier mais jamais lu. Rapporté par l'enquête flow-trace, non revérifié ici : nonce 104 de 2022 à 2024, 109 au 20 mai 2025 et aujourd'hui, donc aucune sortie BSC pendant l'affaire. Les entrées BSC restent à lire.

**Ce que ce circuit établit :** une transaction signée par la clé de brace227 vise l'adresse de celle de kraben006, sans service entre elles. Qui l'a signée, et s'il connaissait le destinataire, reste inconnu. **Ce qu'il n'établit pas :** un propriétaire commun, un pari concerté, une information privilégiée.

| Hypothèse, aucune n'est une conclusion | Pour | Contre ou limite |
|---|---|---|
| Un même opérateur regroupe ses restes | Résidu d'USDT Solana et résidu d'ETH réunis en 2 min, envoi du solde maximal | Aucun autre transfert direct, aucune contrepartie personnelle commune sur Ethereum |
| Deux personnes qui se connaissent, petit paiement | Un seul envoi de 5,53 $ suffit à l'expliquer | Pas de mémo ni de contrepartie visible, invérifiable |
| Paiement sans rapport avec les paris | 5 jours avant le premier achat de brace227 | kraben006 était déjà actif, invérifiable |
| Clé compromise | Sortie 108 s après la réception | Peu probable : 22 024,57 USDC restent sur la clé, qui continue à financer des comptes ensuite |
| Erreur d'adresse | La clé de kraben006 reçoit des transactions de leurre à 0 valeur | Peu probable, et aucune trace d'une relation antérieure qui l'expliquerait |

Aucune donnée lue ici ne les départage : entrées BSC et sauts de la section 7 non lus. Un exchange ou un fournisseur de portefeuille pourrait le faire sur demande légale.

### Retraits rapprochés : ce que le calendrier explique, et ce qu'il n'explique pas

Tests exploratoires, écrits après avoir vu les données, non inscrits au registre gelé. Liste : `evidence/contre_verification_20261102/tests_exploratoires.jsonl`. Résultats : `stats_retraits_kane.json`.

**brace227 et kraben006, 2,8 min d'écart : aucun signal mesurable.** Kane atteint 0,99 à 22:50:24 UTC le 26 octobre. kraben006 retire 48 s après sa vente à 0,999, brace227 136 s après la sienne. Parmi 20 autres vendeurs comparables (5 000 $ ou plus, dans les 30 min après le premier 0,99), **10 retirent eux aussi en moins de 5 min**, p = 0,29 : la vitesse est ordinaire. Leurs ventes sont à 78 s d'écart, pour un écart médian de 45 s entre deux ventes consécutives de ces 22 vendeurs. Leurs retraits sont à 166 s : 8 paires sur 105 font aussi peu parmi les 15 vendeurs qui retirent sous 24 h, sans correction pour le choix de cette paire. Rien ici ne les distingue nettement.

**0x86544e4dfde et walletwallet8424, 1,6 min d'écart : deux faits distincts.**

- *La redemption simultanée est un faux positif.* Le marché Kane est résolu sur la chaîne à 01:57:41 UTC le 27 octobre, `0xf3684759…2430`. De 01:58:14 à 01:58:24, **2 711 comptes sont remboursés en 136 transactions**, 6 204 783,28 $. Les deux comptes y sont, à 01:58:15. Le déclencheur n'est pas lu, mais cette forme rend une décision individuelle synchrone très improbable.
- *La vitesse de retrait ne s'explique pas par le calendrier.* Ils retirent 96 s et 189 s après leur redemption (91 et 184 s après le repère de 01:58:20), et tout leur solde. L'audit classait ce point en faux positif : c'est trop fort.

Face aux autres comptes du lot à 5 000 $ ou plus. 178 lus, 175 retenus : 2 atteignent le plafond de lecture et ne sont pas comptés comme « sans retrait », 1 est le wallet financé par la clé de brace227, décrit plus haut, qui retire 16 h 51 min après. Le p teste 2 nommés sur 2 sous 5 min (Fisher unilatéral). La colonne x 55 corrige le choix de cette paire parmi 55. Sept strates sur treize, toutes dans `reports/CONTRE_VERIFICATION.md`.

| Comparateurs | n | Retrait en moins de 5 min | p brut | p x 55 |
|---|---:|---:|---:|---:|
| Tous | 175 | 1 | 0,0002 | 0,011 |
| Même taille, 20 000 à 50 000 $ | 40 | 0 | 0,0012 | 0,064 |
| Compte de 30 jours ou moins | 22 | 0 | 0,0036 | 0,20 |
| Aucun trade dans l'heure | 124 | 1 | 0,0004 | 0,021 |
| A retiré sous 24 h | 48 | 1 | 0,0024 | 0,13 |
| A retiré sous 24 h, Kane dernière clôture | 27 | 0 | 0,0025 | 0,14 |
| Compte de 60 jours ou moins, a retiré sous 24 h | 19 | 0 | 0,0048 | 0,26 |

Lecture :

- **Atypique à l'état brut, dans toutes les strates. Non significatif après correction dans les strates les plus comparables.**
- **L'écart de 93 s entre eux n'ajoute rien.** Une fois admis que les deux sont rapides, deux délais tirés au hasard sous 5 min sont aussi proches dans 52 % des cas.
- **C'est plutôt un trait du groupe que de la paire.** Entre la dernière clôture et le retrait principal, 8 nommés sur 11 mettent moins de 10 min, contre 9 sur 48 comparateurs qui retirent sous 24 h, p = 0,0011 non corrigé. Le taux des nommés sous 5 min, 4 sur 11, inclut ces deux comptes : appliqué à eux, 13 %. Sur les 9 autres nommés, 2 sur 9 donne 4,9 %. Sélection par la presse dans les deux cas.
- **Biais non contrôlés.** La presse a choisi les nommés après coup, parmi des comptes récents et concentrés. Les strates sont emboîtées, choisies après coup, sur un seul événement. Non mesurés : notifications, logiciel de portefeuille, fuseau horaire (02:00 UTC), autres positions au-delà de 24 h. Les deux clés ont le même contrat de délégation 7702 sur Polygon : le nombre d'adresses qui le partagent n'est pas mesuré ici, et rien n'en fait un lien.

Classement : indice faible, exploratoire. Compatible avec deux comptes dont Kane est la dernière position et qui guettent ce paiement, avec une consigne commune, ou avec un même opérateur. Le test ne les départage pas.

### Taux de base et faux positifs

**Le tableau publié en version 1 n'est pas valable.** Il comptait 50 comparateurs lus sur 83 prévus, comme s'ils étaient tous mesurés. **Seuls 30 sont utilisables, 53 ne le sont pas :**

| Cause | Comparateurs |
|---|---:|
| Jamais lus : 3 même token, 2 token opposé, 28 comptes frais | 33 |
| Lus, sans origine : la ligne comptait comme « pas KuCoin, pas Solana » | 16 |
| Origine lue, mais historique coupé avant le premier achat | 4 |
| **Total inutilisable** | **53** |

**Les 17 historiques coupés.** `tools/baseline.py` s'arrête à 12 pages, 6 000 lignes, sans le signaler. Rejoué depuis le cache : les 17 s'arrêtent avant leur premier achat de la famille, 17 sur 17, dont 13 sans origine lue. Le dépôt retenu précède cet achat de 61 à 736 jours, par exemple 0,04 $ en octobre 2024 pour un achat de 2026. Aucun nommé n'est touché : 11 historiques sur 11 sont complets, donc la comptabilité des dossiers ne bouge pas. Aucun compte frais non plus, mais 28 d'entre eux n'ont jamais été lus. Liste complète : `reports/CONTRE_VERIFICATION.md`.

| Trait | Nommés | Publié, 50 | Utilisables, 30 | Comptes frais utilisables, 11 | Bornes de p sur les 83 |
|---|---|---:|---:|---:|---:|
| Passage par KuCoin Hot Wallet 2 | 3/11 | 1, p = 0,016 | 1, **p = 0,052** | 0, p = 0,107 | 0,005 à 0,997 |
| Origine Solana | 3/11 | 2, p = 0,037 | 2, **p = 0,110** | 0, p = 0,107 | 0,011 à 0,998 |
| Contrat `0xc8a6…` | 5/11 | 5, p = 0,012 | 5, **p = 0,071** | 1, p = 0,074 | 0,002 à 0,972 |
| Adresse de pont 7702 | 6/11 | 31, p = 0,789 | 25, p = 0,987 | non calculé | 0,103 à 1,000 |

p unilatéraux de Fisher, non corrigés, avec cinq traits regardés après coup. Bornes de p : les 53 inutilisables n'ont aucun le trait, ou l'ont tous. Le trait Relay n'est plus testable : un comparateur utilisable a par construction une origine Relay.

- **« KuCoin plus fréquent chez les nommés » est retiré des indices.** À p = 0,052 sur 30, non corrigé, l'écart ne tient pas. Il n'est pas réfuté pour autant : les bornes vont de 0,005 à 0,997, donc **le taux de base réel reste inconnu**. Si 2 des 28 comptes frais non lus avaient ce trait, p = 0,064 face aux frais.
- **KuCoin n'est pas un indice indépendant de Solana :** son libellé n'est lu que sur une origine Solana, 3/3 chez les nommés, 1/2 chez les comparateurs.
- **Les 30 ne représentent pas les 83 :** les coupés sont les comptes les plus actifs et les plus anciens, les exclure déplace l'échantillon vers les comptes récents et peu actifs.
- **Taux de base corrigé :** en attente de l'enquête flow-trace, qui relit ces comparateurs. Aucun chiffre provisoire n'est repris ici.

**Faux positifs identifiés et écartés :**

- `0xc8a6…`, `0xee7a…`, `GxjcMTWW…`, `0x0ce9…`, `0xc1d1…`, `0x58f2…` : chacun relie plusieurs dossiers, et chacun se révèle mutualisé à la mesure. Tableau ci-dessus.
- La route `0xf70d… → 0xb92f… → 0xc8a6…`, signalée le 30 octobre comme « nature inconnue » entre brace227 et walletwallet8424 : c'est Relay et un contrat de passage, donc pas un lien.
- `GxjcMTWW…` : VidenteRibeira et cookedrice y déposent à un jour d'écart (51 489,00 USDT, 39 158,00 USDC). Les deux sorties sont cosignées par ce service, qui en paie les frais, 4 et 2 s après réception : le « même comportement » de sortie est donc son automatisme, seul le choix commun du service reste à expliquer. Service à 1 % de frais, payant par morceaux. Sur 400 transactions tirées, 2 entrées à 10 000 $ ou plus sur 73, médiane 270,38 $ : ces gros dépôts sont plutôt rares, sans que cela relie leurs auteurs. Les sorties ne s'apparient pas sans le registre du service.
- Part de 29 353 $ sur 30 398 $ d'achats côté Mbappé le 13 octobre par des comptes nommés : mécanique, puisqu'ils sont nommés parce qu'ils détenaient ce token.
- Le candidat de 59,09 POL de `0xc590175e…c02b` vers `0x408ce42a…c5b3`, repéré par l'audit, n'est pas un transfert entre dossiers : dans `0x4b89cf4f…5ac8`, `0x408c…` paie lui-même 5,62 USDC et reçoit ces POL. `0xc590…` est un contrat d'échange mutualisé qui a seulement servi aussi au dépôt de walletwallet8424.
- Relais `0xb42f…` et `0xb01c…` et adresses `0xc066…`, `0xe347…`, partagés par plusieurs dossiers : 160 000 à 850 000 transactions chacun selon l'audit, écartés.
- Redemptions dans une même transaction entre 0x86544e4dfde et cookedrice, VidenteRibeira et WenZhuanBuPei : lots de 20 comptes, sans lien.
- Pièges de lecture évités : nœud Solana rendant 0 signature pour une adresse payée, hash du pont introuvable sur sa chaîne, sondage récent de `0xee7a…` à 0 trafic. Ces trois faux zéros ont été recoupés.

## 5. Détection collective

Plan gelé avant tout calcul de taux (`collective/analysis_plan.md`, `PROTOCOL.lock`), partie A scellée le 1er nov. à 23:28 UTC, 6 fichiers sur 6 intacts. C'est le code de A qui ne lit pas les noms, pas l'auteur, qui les connaissait avant le gel. **L'auteur connaissait l'affaire : aucune validation n'en découle.** Une seule affaire, donc n effectif = 1.

### A. Analyse prospective simulée

**Verdict fixé d'avance, au 13 oct. 18:51 UTC comme au 23 oct. 15:17 UTC : `VISIBLE_NON_SPECIFIQUE`.** Il est appliqué à la main dans l'étude, recalculé par code par l'audit : il tient, car le rang l'emporte seul. La date de 18:51:00 tombe 60 s après un achat de Thin à 18:50:00 : 15 053,97 $ dans son activité, dont 14 743,44 $ en flux taker. Le plan ne justifie pas cette date. Selon l'audit, E1 s'arrête au tick de 18:00 et ne voit pas cet achat, E4 et les sommes « avant le 13 octobre » l'incluent.

- **Alerte de cohorte fraîche A0** (au moins 3 wallets de 14 jours ou moins, 1 000 $ chacun, 10 000 $ en tout, sur 72 h) : 5 tokens de la famille en alerte au 13 octobre, 14 au 23 octobre sur 346. Témoins tirés : 4 sur 59. Femmes : 0 sur 148, sans puissance. Portée : sur tables synthétiques, A0 détecte une cohorte d'au moins 3 wallets à 4 000 $ chacun en moins de 72 h, et ne détecte pas 2 wallets. Puissance sur données réelles inconnue : aucun cas vérifié n'existe (`collective/controles/CONTROLES.md`).
- **Recensement de tout Polymarket :** meilleur token de la famille au rang 41 au 13 octobre, et au rang 50 au 23 octobre. Le verdict exigeait le top 10. Charge : au plus 12 premières alertes par jour hors famille. Le plan parle de tokens en alerte : jusqu'à 37 par jour selon une estimation de l'audit, non recomptés exactement. Le verdict n'en dépend pas.
- **Placebo des âges mélangés** (1 000 tirages) : maximum de 8 wallets frais au 13 octobre, p = 0,145 ; 10 au 23 octobre, p = 0,298. Au tirage gelé, pas de concentration détectée. La lecture dépend du nul, selon l'audit : 0,174 et 0,318 en recalculant ce tirage, 0,15 et 0,87 avec un mélange réalisable, 0,008 et 0,077 en variante stricte, non retenue car elle abaisse le nul, et 0,012 sur les témoins au 13 oct. Le tirage gelé laisse 10 à 13 % des dates tomber après l'achat. Le seuil de Bonferroni du registre, 3,57e-07, est inatteignable à 1 000 tirages : ne pas l'atteindre ne prouve rien.
- **Rafales de 15 min :** 0,215 par token-jour dans la famille, 0,203 chez les témoins. Par million de dollars : 74,1 contre 10,6, car la famille compte beaucoup de petits tickets.
- **Petits achats puis gros :** 18,8 pour 100 couples wallet-token dans la famille, 11,6 chez les témoins. Écart descriptif, non testé.
- **Fills et décisions :** 75 072 fills pour 52 103 décisions dans la famille, pour ne pas compter plusieurs fois un même ordre.

Alertes A0 antérieures au 13 octobre 18:51 UTC :

| Première alerte UTC | Token | Wallets | Montant $ |
|---|---|---:|---:|
| 2026-09-30 08:00:00 | Will Harry Kane win the 2026 Ballon d'Or? / Yes | 3 | 17 947,01 |
| 2026-10-02 09:00:00 | Will Lamine Yamal win the 2026 Ballon d'Or? / Yes | 3 | 29 124,84 |
| 2026-10-04 17:00:00 | Will Lamine Yamal win the 2026 Ballon d'Or? / No | 3 | 10 821,71 |
| 2026-10-11 14:00:00 | Ballon d'Or 2026: Kylian Mbappé or Lamine Yamal to finish higher? / Mbappé | 3 | 11 971,15 |
| 2026-10-11 17:00:00 | Will Kylian Mbappé finish in the top 3 of the 2026 Ballon d'Or? / Yes | 3 | 23 160,62 |

Rien de cette section n'utilise un nom, un résultat ou une donnée postérieure à la date simulée. Reproduction en copie fraîche : E1, E1G, E2, E3 et le placebo identiques au sceau (`collective/audit/REPRODUCTION.json`). E4 v2 relancé après audit sur ses trois graines et deux dates, sous un autre hachage : identique, 6 sur 6.

### B. Investigation rétrospective

Cette partie lit les noms et les résultats. Elle ne revient jamais dans A.

- **Wallets étudiés :** 11 wallets nommés lus en détail ; 50 comparateurs lus sur 83 prévus pour le financement, dont 30 utilisables (section 4) ; 3 082 wallets dont l'âge a été lu, dont 388 avec des achats dans la famille.
- **Montant cumulé sur la même issue :** 168 888,64 $ sur Mbappé devant Yamal par les 11, dont 57 544,64 $ avant le 13 oct. 18:51 UTC, 15 053,97 $ de cette somme dans la dernière minute, et 155 188,28 $ avant l'article. Kane vainqueur : 80 389,22 $ par 5 d'entre eux, dont 51 141,79 $ avant le 13 octobre.
- **Première alerte de la famille contenant des comptes nommés :** 2026-10-11 14:00:00 UTC sur Mbappé devant Yamal, les 3 wallets sont 0x86544e4dfde, brace227, zoomman17. Biais : acheter gros tôt mène justement dans le top de la capture.
- **Achats synchrones :** 5 paires nommées à 5 min, 14 à 60 min sur 55. Contre groupes tirés sur le token opposé : centiles 95,5 à 5 min et 84,2 à 60 min, non corrigés. Part de leurs dollars sur les 24 h les plus actives : 15,3 %, centile 9,8. Ces achats sont étalés sur des semaines, pas groupés. Au-delà de ce flux, sur toute leur activité : brace227 et kraben006 ont 9 achats à moins de 5 min d'écart, dédoublonnés à 60 s, 0 avant le 13 oct., 1 le 17 oct., **8 sur Kane le 24 oct., le lendemain de l'article**. L'audit donne p = 0,0012 avec des décalages de plusieurs jours, au-dessus du seuil corrigé de 0,00091. Dans le seul créneau de 14:00 à 17:00 UTC, un décalage donne p = 0,40, sur 9 achats de brace227 sur 17, moyenne nulle 7,38 : ils achètent beaucoup au même moment de la journée, sans synchronie plus fine. Ce sont pourtant les deux plus gros acheteurs taker du créneau, 45 % des 21 753 $ achetés, et aucun des 14 autres acheteurs à 100 $ ou plus n'atteint leurs scores, maximum 7 contre 9 et 5 contre 7. Exploratoire, créneau choisi après coup. C'est un fait à instruire, pas une preuve.
- **Combinaisons de paris (E4 v2, trois graines) :** par graine, 11, 11 et 12 paires inhabituelles au 13 octobre, 31, 25 et 34 au 23 octobre, soit 12 et 37 en union. 23 paires stables sur les trois graines au 23 octobre. **0 paire nommée au-dessus du seuil, ce qui ne veut pas dire 0 paire nommée similaire.** Le code exige 2 tokens à 100 $, filtre absent du plan. Au 23 octobre, il écarte VidenteRibeira et WenZhuanBuPei : **19 paires nommées sur 55 ne sont jamais testées**. Au 13 octobre, **45 sur 55** : 40 parce qu'un des deux comptes n'avait encore rien acheté sur la famille, 5 par ce filtre, qui écarte walletwallet8424. À cette dernière date, le seuil pour 1 ou 2 tokens communs égale le maximum possible : une telle paire ne peut pas le dépasser. Le seuil est un maximum sur toutes les paires et ne voit qu'un extrême : la meilleure paire nommée, OuldLm3alem et 0xdd97e6, est à 0,90 du seuil, selon l'audit. L'audit relève aussi un chevauchement du groupe nommé plus fort que des groupes tirés sur le même token au 23 octobre (part à ou au-dessus : 0,04), pas au 13 (0,27) : exploratoire, non corrigé, confondu avec la sélection par la presse.
- **Classement exact :** avant l'article, une seule combinaison complète des rangs 2 à 5 est détenue parmi 42 wallets : la bonne, par 4 wallets (kraben006, 0xdd97e6, 0xeed8c2be…35f0, ouldlm3alem). **Ce n'est pas rare par rapport aux prix** : le produit des quatre prix valait environ 0,28 à cette date, et ces marchés ouvrent déjà vers 0,6 le 19 octobre.
- **Financement avant achat :** écart médian 2,6 min chez les nommés, 9/11 sous une heure. Le 10/43, p = 0,0006, publié dans l'étude est surestimé : 21 lignes sur 43 sont coupées, et 38 wallets y comptent pour 43 lignes. Sur les 20 comparateurs distincts à historique complet et écart mesurable : **9/20, p = 0,052**, non corrigé. En gardant `0x73ef4077…`, sans dépôt lu avant son achat : 9/21, p = 0,039. Ces p reflètent un choix de dénominateur, pas le vrai taux, qui reste inconnu. E6 est exploratoire : écrit après le sceau et après la lecture de E5. Confondu avec l'âge : un compte neuf dépose puis mise.
- **Prix et liquidité :** aucun carnet daté n'existe. Parmi les 20 plus grosses décisions, 2 viennent de comptes nommés. Thin le 13 oct. : 14 935,70 $, 0,88 fois le volume des 24 h précédentes du token, prix de 0,490 avant à 0,577 payé en moyenne.

### Les questions posées

| Question | Réponse |
|---|---|
| Ont-ils misé au même moment ? | Pas de manière distincte au niveau du groupe : étalés du 1er au 26 octobre, peu de paires proches. Deux cas à instruire : brace227 et kraben006 le 24 oct., brace227 et `0xa8e64a3c…` le 9 oct. |
| Ont-ils acheté les mêmes issues ? | Oui sur Mbappé devant Yamal (11/11), mais 9 ont été choisis sur ce critère. 5/11 sur Kane. |
| Combinaisons statistiquement rares ? | Non tranché : aucune paire nommée au-dessus du seuil d'E4 v2, mais 19 paires sur 55 non testées. Combinaison exacte déjà cotée environ 28 %. |
| Mises anormales par rapport à la liquidité ? | Certaines sont grandes par rapport au volume récent. Sans carnet daté, la profondeur reste inconnue. |
| Financements similaires avant les achats ? | Oui en apparence, écart surestimé en version 1, confondu avec l'âge des comptes. |
| Routes communes ? | Oui, uniquement des services, aucune adresse partagée discriminante. À part : un transfert direct brace227 vers kraben006, hors service. |
| Conforme à des informations publiques ? | Non déterminable. Selon des extraits de recherche d'Oddschecker, Yamal est favori le 5 octobre, Mbappé à 22/1. Sur Polymarket, Kane passe de 0,49 le 7 octobre à 0,66 le 11, sans source datée trouvée pour ces jours. |
| Visible le 13 octobre ? | Oui au sens du plan, sans spécificité. Rang 41 sur tout Polymarket. PolySentinel n'existait pas à cette date. |

## 6. ChangeNOW, FixedFloat, XMR

**La version 1 écrivait « aucune interaction avec une adresse étiquetée ChangeNOW » : c'est faux pour la clé de kraben006.** Les étiquettes publiques de Blockscout en portent deux, absentes de `tools/services.json`, source unique, non recoupée (`evidence/contre_verification_20261102/etiquettes_blockscout.json`) :

- `0xdd3d72C53Ff982ff59853da71158bf1538b3Ceee`, « ChangeNOW: Hot Wallet 3 », envoie 654,47 et 180,38 USDC à cette clé le 23 février 2026, `0x5e8b57210b722dbf0f7395cbe20c57a3e578d2897bb4ff8d4c5e853387789219` et `0x472c85a3cd9df3bbdf9b5fac9ee812326646b1b40c832278fb42107554c0cd80`, sept mois avant l'affaire.
- `0x3f3Ee0a9cAC2d01DB44001eca3E8382fbe40207B`, « ChangeNOW Dep », reçoit 0,00241406 ETH le 4 octobre, maillon 5 du circuit de la section 4.

Ces étiquettes ne disent ni qui a envoyé ces fonds, ni si un échange a eu lieu, ni ce qu'il aurait rendu, et elles ne relient pas ces fonds à un pari. **Aucun échange XMR n'est observé.** Le statut `XMR_VISIBILITY_BOUNDARY` n'est pas posé : ce qui sort de ChangeNOW n'est pas visible d'ici, et le poser ou non reste une décision de Benjamin. Autres étiquettes sur la clé de brace227, lues sans analyse : THORChain Router (7 USDC le 12 oct.), NEAR Intents (0,00202 ETH le 16 oct.), BloFin: Hot Wallet 1 (110,20 USDC le 20 oct., déposés ensuite), Bridgers (avril 2025), et en 2022 des adresses KuCoin et Binance.

**Cette relecture ne couvre que les clés de brace227 et kraben006 sur Ethereum et ce qu'elles touchent directement.** Les 9 autres clés, leurs destinations et les autres chaînes n'ont pas été relues : l'absence d'étiquette ailleurs n'est pas établie. Sur ce périmètre, aucune étiquette FixedFloat. Tout cela reste partiel : ma liste ChangeNOW compte 8 adresses Polygon de seconde main (`tools/services.json`). Pour Solana, l'étude `cn_pm_sakana` n'a gardé que les préfixes de deux hubs : aucune adresse lue ne les porte, mais un préfixe reste un test faible. Je n'ai aucune adresse FixedFloat, et ces services paient depuis des adresses qui tournent.

`GxjcMTWW…` est le point le plus proche : un service non identifié qui prélève 1 %, paie par morceaux et cosigne les sorties de ses adresses de dépôt probables. Rien ne permet de dire ce qu'il est, ni de suivre ce qui en sort. `0xc1d13492…a1b5`, utilisé par brace227 et kraben006, est un contrat vérifié nommé SwftSwap, service d'échange de la même famille, absent de ces listes.

**Iris :** aucune clé trouvée, aucun crédit consommé, aucune adresse envoyée. Requêtes les plus utiles : `reports/iris_requetes.md`.

## 7. Limites

- Flux **taker seulement** pour les univers de l'étude collective : un compte par ordres limites n'y apparaît pas. Le dossier de chaque wallet lit, lui, son activité complète.
- Le scan d'origine lit les stablecoins dans les logs, pas les mouvements natifs. Ajoutés par l'audit, non refaits ici sauf les deux clés sur Ethereum : Ethereum, Arbitrum et Base sur 27 adresses, POL natif sur 46 adresses. Non lus : BSC au-delà des nonces, Optimism au-delà des nonces des clés (0 sur les 11 clés), historiques plafonnés à 3 pages sur 4 adresses (`0x3ab2…`, `0x7ff8…`, `0xa322…`, `0xf7c8…`).
- **Aucun témoin positif de propriété commune :** la méthode n'a pas été éprouvée sur des paires connues, et elle a manqué deux liens réels en version 1. Son silence sur les 54 autres paires n'est pas une preuve d'absence.
- Étiquettes de services incomplètes et datées. KuCoin : une seule source. BscScan et Polygonscan refusent la lecture automatique.
- Taux de base : 53 comparateurs sur 83 inutilisables, résultat corrigé en attente (section 4).
- Comparateurs imparfaits : témoins surtout sportifs, famille féminine sans puissance, comptes nommés choisis après coup.
- Trois wallets non nommés détiennent la même combinaison complète de rangs (`0xeed8c2be…35f0`, `0x1583c5d3…cdde`, `0x14c32680…df68`). Seule cette similarité les rapproche : aucun dossier ouvert, aucun financement testé, aucune mise en cause. Pour ces trois wallets, aucun lien de chaîne n'a été cherché. Un wallet supplémentaire, lui, est relié aux onze par une preuve de chaîne : `0xa8e64a3c…f74a5`, section 4. D'autres adresses sont reliées aux clés, comme `7XUJs…` et `0x7e67…`, sans qu'on sache qui les tient.
- Sorties : les 26,97 ETH de 0xdd97e6 n'ont pas bougé (nonce 0). Les 839 000 POL d'OuldLm3alem sont devenus 75 946,74 USDT, repartis depuis : suite non lue ici.
- Relectures : un audit indépendant (`~/Projects/PolySentinel-audit-20261102/RAPPORT_AUDIT.md`) puis cette contre-vérification, puis un auditeur de conclusions, FAIL à ses deux passages, tous par des instances de Claude, avec les mêmes angles morts possibles. Sa dernière série de corrections n'a pas été relue une troisième fois. Aucune relecture humaine ni externe. Les audits du protocole d'étude gelée n'ont pas été faits sous leur forme prévue.
- Tests de cette version sur les retraits et les achats rapprochés : exploratoires, écrits après lecture des données, hors registre gelé.
- Amendement 001 de l'étude : décidé par Claude alors que la règle réserve les amendements à Benjamin, toujours à relire. Le fichier gelé n'est pas modifié.
- Reproduction : E1, E1G, E2, E3 et placebo identiques. E4 d'origine non reproductible, corrigé par E4 v2 (amendement 002), son ancienne sortie est conservée.

## 8. Synthèse des hypothèses

**Confirmées :** H1, H2, H16, H17. **Réfutées, dans le périmètre indiqué :** H5, H6. **Affaiblies :** H7, H8, H11. **Non soutenues :** H10, H12. **Non tranchées :** H3, H4, H9, H13, H14, H15.

Confirmée : les données la soutiennent directement. Affaiblie : testée, sans soutien, puissance non mesurée, sans pouvoir l'exclure. Non soutenue : rien de solide en sa faveur, sans preuve du contraire. Réfutée : contredite par les données, dans le périmètre indiqué. Non tranchée : la méthode ne pouvait pas répondre, listes incomplètes, ou données publiques insuffisantes. L'absence de preuve n'est jamais lue comme une preuve d'absence.

| # | Hypothèse | Statut | Sur quoi |
|---|---|---|---|
| H1 | Les onze étiquettes correspondent à des wallets identifiables | **CONFIRMÉE, niveaux inégaux** | Capture reproduite 15 lignes sur 15 ; 7 noms exacts, 3 par les parts, 1 par préfixe |
| H2 | Ces comptes ont réalisé des gains | **CONFIRMÉE pour 7 comptes soldés, non établie pour 4** | Comptabilité complète, résidu nul sur les soldés |
| H3 | Un même opérateur contrôle les onze | **NON TRANCHÉE** | 11 clés distinctes et routes différentes : un opérateur prudent laisserait la même empreinte. Aucun témoin positif, comptes d'exchange invisibles. Rien ne la soutient, rien ne l'exclut |
| H4 | Un financeur personnel commun relie certains comptes | **NON TRANCHÉE entre les onze** | 21 paires naïves, 0 après reclassement. Le transfert de 5,53 $ pèse 0,055 % et 0,097 % des dépôts des deux comptes. Hors des onze, voir H17. Hors des sauts lus, inconnu |
| H5 | La route commune brace227 et walletwallet8424 du 30 octobre est un lien | **RÉFUTÉE comme lien** | Relay plus contrat de passage à fort trafic |
| H6 | Un signal collectif spécifique était visible le 13 octobre | **RÉFUTÉE pour la règle testée** | Verdict gelé VISIBLE_NON_SPECIFIQUE, rang 41 du recensement. Ne vaut pas pour toute autre règle |
| H7 | Des comptes frais se concentrent sur une issue plus que le hasard | **AFFAIBLIE** | Placebo p = 0,145 puis 0,298, 1 000 tirages. Lecture sensible au choix du nul, section 5 |
| H8 | Les comptes nommés achètent de façon synchrone | **AFFAIBLIE** | 5 paires à 5 min sur 55, centile 95,5 non corrigé, mais centile 84,2 à 60 min et 9,8 sur la concentration en 24 h. Paire brace227 et kraben006 à instruire : 8 achats rapprochés le 24 oct., après l'article |
| H9 | Les nommés partagent des combinaisons inhabituelles | **NON TRANCHÉE** | E4 v2 : 0 paire nommée au-dessus du seuil, mais 19 paires sur 55 non testées et un seuil qui ne voit que l'extrême |
| H10 | Détenir le classement exact était rare | **NON SOUTENUE par rapport aux prix** | Combinaison cotée environ 0,28 avant l'article, marchés de rangs ouverts vers 0,6. Ce produit de prix suppose des rangs indépendants, ce qu'ils ne sont pas : le sens tient, « réfutée » était trop fort |
| H11 | Les comptes nommés ont eux-mêmes lancé la hausse de Kane | **AFFAIBLIE** | Hausse amorcée le 8 octobre : 24 444 $ d'achats, 0 $ de comptes nommés ce jour-là. Mais kraben006 achète 2 499 $ de Kane les 1er et 2 oct., Zoomman17 855 $ le 6, kraben006 243 $ le 7. Ils pèsent ensuite 25 à 53 % des achats du 9 au 11 |
| H12 | Une route KuCoin plus fréquente chez les nommés | **NON SOUTENUE, retirée des indices** | 3/11 contre 1/30 utilisables, p = 0,052 non corrigé, 53 comparateurs sur 83 inutilisables, même observation que l'origine Solana, étiquette à source unique. Taux réel inconnu |
| H13 | Les fonds passent par ChangeNOW, FixedFloat ou XMR | **NON TRANCHÉE** | Deux adresses étiquetées ChangeNOW sur la clé de kraben006, source unique, relecture limitée à deux clés, dont 0,0024 ETH le 4 oct. Aucun échange XMR observé, rien ne relie ces fonds à un pari. Listes incomplètes, deux chaînes s'arrêtent à un service non identifié. SwftSwap, service d'échange de la même famille, est utilisé par brace227 et kraben006 |
| H14 | Des retraits coordonnés | **NON TRANCHÉE, non démontrée** | brace227 et kraben006 : aucun signal mesurable, 10 vendeurs comparables sur 20 retirent aussi vite. 0x86544e4dfde et walletwallet8424 : redemption en lot, mais retrait rapide atypique face au lot, p brut de 0,0002 à 0,0069 selon les 13 strates, de 0,010 à 0,38 après correction, exploratoire. 8 retraits principaux sur 11 suivent de moins de 10 min la dernière clôture |
| H15 | Une information privilégiée | **NON TESTABLE ici** | Aucune preuve d'accès. Des données publiques seules ne peuvent pas trancher, et aucun lien financier entre comptes n'y répond |
| H16 | Un transfert direct relie deux dossiers | **CONFIRMÉE pour une paire** | 0,002048944 ETH de la clé de brace227 vers celle de kraben006. Lien entre clés, pas propriété commune |
| H17 | Un wallet non nommé est relié aux onze par une preuve de chaîne | **CONFIRMÉE pour un wallet** | La clé de brace227 envoie 5 170 USDC à la clé de `0xa8e64a3c…f74a5`, qui dépose 5 165 $ et ne parie que sur Kane. Lien financier, pas propriété commune. Douzième compte allégué : aucune preuve |

## 9. Conclusion

Trois niveaux à ne jamais confondre. **Connexion financière :** un transfert relie deux adresses. **Contrôle commun :** une même personne tient ces adresses. **Insider trading :** quelqu'un a parié en connaissant le résultat. Le premier est établi pour une paire des onze et entre brace227 et un wallet non nommé. Les deux autres ne sont établis pour personne, et le premier ne prouve pas les suivants.

### FAITS DÉMONTRÉS

- La capture Upside correspond à 15 wallets du tape public, ligne par ligne.
- Les dépôts, positions et retraits des 11 wallets, avec 182 relations à identifiant stable dans `graphs/relations.jsonl`.
- 25 retraits pour 493 094,76 $ et 46 dépôts pour 304 137,63 $ sur les onze comptes. 7 comptes soldés totalisent 129 367,79 $ de retraits moins dépôts. Le premier montant est brut, le second un net partiel.
- Des liens entre chaînes prouvés par le même identifiant Relay dans les deux sens.
- Un seul transfert direct trouvé entre deux dossiers : 0,002048944 ETH, environ 5,53 $, de la clé de brace227 à celle de kraben006, le 4 oct. 13:54:35 UTC, `0xd07bea20a22d9381e0ab364e7a7421776318c6f4aa7258799638472ad7092b98`.
- Ce transfert vide l'ETH de la clé de brace227, 108 s après un paiement Relay commandé depuis l'adresse Solana `7XUJs…frZc`, même identifiant sur les deux chaînes.
- La clé de brace227 envoie 5 170 USDC à `0x48ec106cf690edd58fcd6df1e8b6abfc16dab12d`, propriétaire du wallet non nommé `0xa8e64a3c08d1e2a4e9f25a2dd33b8ac3458f74a5`, et 5 173,25 $ à son propre wallet, les 9 et 10 oct. Ce wallet ne parie que sur Kane.
- Le 27 oct., les comptes détenteurs de Kane sont remboursés par un lot de 2 711 comptes en 136 transactions, moins d'une minute après la résolution. Le déclencheur n'est pas lu.
- À la date de lecture, des sorties restent immobiles : Thin-Disclaimer-Life 39 999,85 USDC sur `CXVYMP5qxB…GrfJ`, Thin-Disclaimer-Life 39 537,78 USDC sur `EnHRjTP4pK…PZ8B`, 0x86544e4dfde 74 198,32 sur `0x69837228…0ded`, brace227 22 024,57 sur `0xc852b093…af26`, walletwallet8424 35 546,89 sur `0x82775eb8…a3a1`, kraben006 15 154,83 sur `0x101b5f4d…fb65`.
- Au 13 octobre, la règle A0 alerte sur 5 tokens, et le meilleur de la famille reste au rang 41 du recensement.

### HYPOTHÈSES PLAUSIBLES

- Des retraits d'exchange directs vers l'adresse de dépôt Polymarket, pour une partie des dépôts.
- Des comptes neufs convaincus, ou des suiveurs d'un mouvement de marché : la hausse de Kane du 8 au 11 octobre est large et ne dépend pas d'eux seuls.
- Pour brace227 et kraben006 : un même opérateur, deux personnes qui se connaissent, ou un paiement sans rapport avec les paris. Aucune n'est établie (section 4).
- Pour brace227 et `0xa8e64a3c…` : un même opérateur avec deux comptes, deux personnes qui misent à parts égales, ou un prêt. Aucune n'est établie (section 4).

### INDICES FAIBLES

- Financement commun de brace227 et `0xa8e64a3c…` : connexion démontrée, coordination seulement possible, limites en section 4.
- brace227 et kraben006, plus gros acheteurs taker de Kane du créneau du 24 oct., après l'article, avec des achats rapprochés (p = 0,40 dans ce créneau).
- Retrait rapide après le lot Kane pour 0x86544e4dfde et walletwallet8424, et sortie rapide de la plupart des nommés : exploratoire, biais de sélection.
- Même service à 1 % pour VidenteRibeira et cookedrice, à un jour d'écart. Le balayage vient de son automatisme, le choix commun reste sans explication ni valeur de lien démontrée.
- Peu d'acheteurs côté Mbappé pendant que le prix monte, avec un biais de sélection.
- 4 changements de nom dans la capture, dont un compte non surligné : leurs dates sont inconnues.

### NON DÉTERMINABLE

- Qui contrôle ces wallets, et si plusieurs ont le même propriétaire, brace227 et kraben006 compris.
- Le taux de base réel des routes de financement : 53 comparateurs sur 83 inutilisables à ce jour.
- Qui tient `0x48ec…`, si `0xa8e64a3c…` est le douzième compte allégué, et si d'autres wallets du même type existent.
- L'origine de leur conviction, et s'ils ont eu accès au résultat.
- Ce que les exchanges et services savent de ces comptes : seule une demande légale y accède.
- Ce qui sort de `GxjcMTWW…`, et l'identité de ce service.
- La nature exacte de `0x3f3Ee0a9…207B`, étiquette ChangeNOW à source unique, si un échange a eu lieu et ce qu'il aurait rendu, et la suite des 75 946,74 USDT d'OuldLm3alem.
- La liquidité réelle au moment des achats.
- La détection réelle de PolySentinel le 13 octobre : le service n'existait pas.

## 10. Incidents et corrections pendant l'enquête

- **S_C arrêté deux fois par son garde-fou.** Le 1er nov. vers 22:48 UTC, battement du collecteur à plus de 180 s, charge à 27, avec le rendu vidéo, un benchmark d'une autre session et mes scripts : ma part n'est pas mesurée. Le 2 nov. vers 07:39 UTC, au moment du réveil du Mac, endormi depuis 01:13 : swap +6,8 Go, disque tombé à 11,2 Go. Mes scripts dépassaient alors au plus 180 Mo et ne sont pas en cause. S_C a repris seul. Aucun fichier du rejeu n'a été touché.
- **Erreurs de mon code, corrigées :** adresse zéro prise pour destination, swap dans la même transaction non géré, course d'écriture sur le cache entre deux processus, seuil « avant cérémonie » faux dans E6 (champ non cité, fichier gelé conservé), lot de comparaison `meme_token` dégénéré (centiles non cités).
- **Erreurs de la version 1, corrigées après audit :** « 0 transfert direct » sur un scan sans natif, « aucun wallet supplémentaire relié » sans suivre ce que les clés envoient ailleurs, taux de base avec historiques coupés et lignes illisibles comptées comme négatives, E6 sur lignes coupées et doublonnées, H3, H4 et H9 lues comme affaiblies sans témoin positif, phrase trompeuse sur le sceau de la partie A. Détail : `reports/AMENDEMENT_AUDIT_2026-11-02.md`.
- **Trois workers réseau pendant moins de 2 minutes,** au lieu de deux, corrigé tout de suite.
- **`rm -rf` bloqué par un contrôle de sécurité,** non contourné. Une copie de reproduction reste dans le scratchpad de session.

## 11. Fichiers

| Fichier | Contenu |
|---|---|
| `cases/<dossier>.md`, `.json` | Dossier complet par wallet, historique daté, hashes |
| `reports/inventaire_adresses.md` | Liens étiquette vers adresse |
| `reports/AMENDEMENT_AUDIT_2026-11-02.md` | Chaque correction : ancienne affirmation, preuves, nouvelle conclusion, raison |
| `reports/CONTRE_VERIFICATION.md` | Tableau des conclusions, vérification de l'audit, 17 historiques coupés |
| `reports/JOURNAL_MODIFICATIONS_2026-11-02.md` | Empreintes avant et après de chaque fichier modifié |
| `reports/POUR_FLOW_TRACE_2026-11-02.md` | Points transmis à l'enquête flow-trace |
| `evidence/contre_verification_20261102/`, `tools/cv_*.py` | Lectures et calculs de la contre-vérification |
| `archive/20261102_avant_amendement_audit/` | Rapport, liens et dossiers `.md` de la version 1, avec leurs empreintes |
| `reports/liens_entre_wallets.md` | Reclassement et faux positifs |
| `archive/20261102_avant_correction_burn/` | Dossiers et liens d'avant la correction, conservés |
| `reports/iris_requetes.md`, `reports/proposition_shadow.md` | Requêtes Iris, proposition d'intégration |
| `reports/sources_cinq_depots.md` | Les cinq dépôts de recherche |
| `graphs/relations.jsonl`, `graphs/links_classified.json`, `graphs/direct_transfers.json` | Relations et liens |
| `collective/` | Étude gelée : plan, code, sorties, amendements, registre |
| `controls/` | Taux de base |
| `evidence/` | Reçus, captures, mesures |
