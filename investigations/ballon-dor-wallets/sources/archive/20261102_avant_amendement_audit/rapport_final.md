# Enquête Ballon d'Or 2026 : rapport final

Écrit le 02/11/2026 à 08:18 UTC depuis les fichiers de preuve. Espace : `~/Projects/PolySentinel-investigation`. Une adresse n'est pas une personne : aucune identité civile n'est établie ni recherchée.

## 1. Conclusion

**Aucune coordination et aucune information privilégiée ne sont démontrées.** Les onze comptes publics sont reliés à une adresse et leurs flux sont reconstruits, mais rien ne prouve qu'ils ont un propriétaire commun. Le signal collectif testé est visible au 13 octobre, sans être spécifique.

| Niveau | Verdict | Sur quoi il repose |
|---|---|---|
| Comportement atypique | **Observé, avec un biais de sélection** | 11 comptes sur 11 actifs depuis octobre seulement. 9 sur 11 ont déposé moins d'une heure avant leur premier achat sur cette famille. 11 sur 11 sont sur Mbappé devant Yamal. La presse en a surligné 9 sur ces traits. |
| Coordination | **Non démontrée** | 0 transfert direct de fonds, 0 adresse partagée discriminante sur 55 paires, 0 paire nommée dans E4 v2, pas de synchronie nette (centile 95,5 à 5 min non corrigé, 84,2 à 60 min). |
| Insider trading | **Non démontré** | Aucune preuve d'accès à l'information. Gagner un pari, même tôt, ne prouve pas sa source. Les chronologies publiques des 8 au 13 octobre restent incomplètes. |

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

Sur les 7 comptes soldés, retraits moins dépôts : **129 367,79 $**. Les 4 autres ne sont pas soldés ou gardent un résidu (0x86544e4dfde, brace227, Zoomman17, OuldLm3alem) : aucun gain n'y est affirmé. Ce total ne recoupe pas les chiffres de presse, dont le périmètre diffère.

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
- Lien discriminant : aucun. Transfert de fonds direct avec un autre dossier : aucun sur les chaînes et jetons lus.
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
- Combinaisons inhabituelles E4 v2 : 0 paire sur les trois graines et les deux dates.
- Autres nommés achetant le même token à moins de 5 min : 0x86544e4dfde ; à moins de 60 min : 1.
- Financement E6 : 532,5 min entre le dernier dépôt et le premier achat. 11 comparateurs sur 42 font aussi court ou plus court. Confondu avec l'âge du compte.
- Top 20 des décisions E7 : 2026-10-13 18:48:52, 14 935,70 $, prix 0,490 avant, 0,577 payé, 0,88 fois le volume de 24 h.
- Quatre rangs exacts détenus avant l'article : non. Combinaison cotée environ 0,28 à cette date, donc pas rare par rapport aux prix.

**Niveau de confiance et limites.**

- Lien étiquette vers adresse : **élevée** (nom exact et parts de la capture).
- Flux : **élevée** sur 13 relations lues sur la chaîne, **moyenne** sur 1 relations dépendant d'un service ou d'une étiquette.
- Coordination et information privilégiée : **non démontrées**, aucune preuve dans ce dossier ne les établit.
- La trace s'arrête à : `EMu2EAWjzP…Mqsd`. Seul le service connaît le compte d'origine.
- Mouvements natifs non lus hors enregistrement Relay. Soldes lus à la date indiquée, ils peuvent changer.

### VidenteRibeira

Wallet `0x5f8b30fde56bd2d2f3853769602330aeb9f1866a`, DEPOSIT_WALLET, clé propriétaire `0x3cb3f4f6b1a81bdf523e36b7f5fa5081113f0f5e`. Dossier complet : `cases/vidente.md`.

**Comportements suspects réellement observés.** Ce sont des faits, pas des preuves d'intention.

- Premier événement Polymarket le 2026-10-15 21:06 UTC, premier achat sur la famille le 2026-10-16 00:27 UTC.
- Concentration : 100,0 % de ses achats sur le Ballon masculin (27 884,23 $ sur 1 issues, 0,00 $ ailleurs).
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
- Relations à identifiant stable : ONCHAIN_CONFIRMED 4, PROTOCOL_CONFIRMED 3, SERVICE_INTERACTION 1.

**Liens éventuels avec les autres wallets.**

- SERVICE_ETIQUETE : `BmFdpraQhk…ymy6`, aussi 0xdd97e6, cookedrice, ouldlm3alem, thin.
- SERVICE_MESURE : `GxjcMTWWDc…nvBW`, aussi cookedrice.
- Lien discriminant : aucun. Transfert de fonds direct avec un autre dossier : aucun sur les chaînes et jetons lus.
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
- Combinaisons inhabituelles E4 v2 : 0 paire sur les trois graines et les deux dates.
- Autres nommés achetant le même token à moins de 5 min : brace227 ; à moins de 60 min : 2.
- Financement E6 : 200,5 min entre le dernier dépôt et le premier achat. 10 comparateurs sur 42 font aussi court ou plus court. Confondu avec l'âge du compte.
- Top 20 des décisions E7 : absent.
- Quatre rangs exacts détenus avant l'article : non. Combinaison cotée environ 0,28 à cette date, donc pas rare par rapport aux prix.

**Niveau de confiance et limites.**

- Lien étiquette vers adresse : **élevée** (nom exact et parts de la capture).
- Flux : **élevée** sur 7 relations lues sur la chaîne, **moyenne** sur 1 relations dépendant d'un service ou d'une étiquette.
- Coordination et information privilégiée : **non démontrées**, aucune preuve dans ce dossier ne les établit.
- La trace s'arrête à : `5xHWduZuzC…uz1a`, `5xHWduZuzC…uz1a`. Seul le service connaît le compte d'origine.
- Mouvements natifs non lus hors enregistrement Relay. Soldes lus à la date indiquée, ils peuvent changer.

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
- Relations à identifiant stable : ONCHAIN_CONFIRMED 3, PROTOCOL_CONFIRMED 2, SERVICE_INTERACTION 1.

**Liens éventuels avec les autres wallets.**

- SERVICE_ETIQUETE : `BmFdpraQhk…ymy6`, aussi 0xdd97e6, ouldlm3alem, thin, vidente.
- SERVICE_MESURE : `GxjcMTWWDc…nvBW`, aussi vidente.
- Lien discriminant : aucun. Transfert de fonds direct avec un autre dossier : aucun sur les chaînes et jetons lus.
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
- Combinaisons inhabituelles E4 v2 : 0 paire sur les trois graines et les deux dates.
- Autres nommés achetant le même token à moins de 5 min : aucun ; à moins de 60 min : 2.
- Financement E6 : 2,4 min entre le dernier dépôt et le premier achat. 3 comparateurs sur 42 font aussi court ou plus court. Confondu avec l'âge du compte.
- Top 20 des décisions E7 : absent.
- Quatre rangs exacts détenus avant l'article : non. Combinaison cotée environ 0,28 à cette date, donc pas rare par rapport aux prix.

**Niveau de confiance et limites.**

- Lien étiquette vers adresse : **élevée** (nom exact et parts de la capture).
- Flux : **élevée** sur 5 relations lues sur la chaîne, **moyenne** sur 1 relations dépendant d'un service ou d'une étiquette.
- Coordination et information privilégiée : **non démontrées**, aucune preuve dans ce dossier ne les établit.
- La trace s'arrête à : `BJcZxhXFt2…JxFU`. Seul le service connaît le compte d'origine.
- Mouvements natifs non lus hors enregistrement Relay. Soldes lus à la date indiquée, ils peuvent changer.

### WenZhuanBuPei

Wallet `0x8832319d9c25df311e37511f0aa5b214abc16500`, DEPOSIT_WALLET, clé propriétaire `0x6697f72fa32de93d8450830eb07f5b6724104405`. Dossier complet : `cases/wen.md`.

**Comportements suspects réellement observés.** Ce sont des faits, pas des preuves d'intention.

- Premier événement Polymarket le 2026-10-18 20:14 UTC, premier achat sur la famille le 2026-10-18 20:16 UTC.
- Concentration : 100,0 % de ses achats sur le Ballon masculin (15 904,76 $ sur 1 issues, 0,00 $ ailleurs).
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
- Lien discriminant : aucun. Transfert de fonds direct avec un autre dossier : aucun sur les chaînes et jetons lus.
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
- Combinaisons inhabituelles E4 v2 : 0 paire sur les trois graines et les deux dates.
- Autres nommés achetant le même token à moins de 5 min : aucun ; à moins de 60 min : 0.
- Financement E6 : 1,8 min entre le dernier dépôt et le premier achat. 1 comparateurs sur 42 font aussi court ou plus court. Confondu avec l'âge du compte.
- Top 20 des décisions E7 : 2026-10-18 20:16:17, 12 772,99 $, prix 0,550 avant, 0,553 payé, 0,68 fois le volume de 24 h.
- Quatre rangs exacts détenus avant l'article : non. Combinaison cotée environ 0,28 à cette date, donc pas rare par rapport aux prix.

**Niveau de confiance et limites.**

- Lien étiquette vers adresse : **élevée** (nom exact et parts de la capture).
- Flux : **élevée** sur 6 relations lues sur la chaîne, **moyenne** sur 0 relations dépendant d'un service ou d'une étiquette.
- Coordination et information privilégiée : **non démontrées**, aucune preuve dans ce dossier ne les établit.
- Mouvements natifs non lus hors enregistrement Relay. Soldes lus à la date indiquée, ils peuvent changer.

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
- Lien discriminant : aucun. Transfert de fonds direct avec un autre dossier : aucun sur les chaînes et jetons lus.
- Une exécution de carnet d'ordres entre OuldLm3alem et 0x86544e4dfde : 520,97 parts à 0,53, `0x870eaa6cb8298d7a02379b48093d4633af4f77ba58638bfc78ff9b0146f30b48`. Ordinaire sur un carnet.
- Issues aussi détenues par d'autres nommés : Kylian Mbappé or Lamine Yamal / Mbappé (10 autres); Harry Kane win / Yes (4 autres); Lamine Yamal finish 3rd in / Yes (4 autres); Rodri or Lionel Messi / Rodri (3 autres).

**Explications alternatives et faux positifs.**

- Parieur actif sur plusieurs issues dès le 9 octobre, Kane compris, au moment où ce marché montait déjà. Mouvement de Kane amorcé la veille sans wallet nommé.
- Faux positifs d'une règle de « financeur commun » : `0xc8a6871d…8d64`, `0x0ce9bdf3…f06d`. Ce sont des services, ils ne relient personne.
- Biais de sélection : ce compte est étudié parce que la presse l'a nommé après le résultat. Taille et âge ne sont donc pas des résultats indépendants.

**Résultats des contrôles statistiques.** Lecture individuelle descriptive : n effectif de l'affaire = 1, sans puissance par wallet.

- S_A scellé : vu, 2 paire(s) avec comportement, score maximal 1, **0 priorité**. Comparaison exploratoire, hors R3.
- Alerte A0 : 2026-10-11 14:00:00, Kylian Mbappé or Lamine Yamal / Mbappé, 3 wallets, avant le 13 oct. 18:51.
- Alerte du recensement E1G : membre d'aucune.
- Rafales E2, membre de : 0 à 5 min, 1 à 15 min, 5 à 60 min.
- Petits puis gros E3 : non.
- Combinaisons inhabituelles E4 v2 : 0 paire sur les trois graines et les deux dates.
- Autres nommés achetant le même token à moins de 5 min : brace227, thin, walletwallet8424 ; à moins de 60 min : 6.
- Financement E6 : 3,9 min entre le dernier dépôt et le premier achat. 4 comparateurs sur 42 font aussi court ou plus court. Confondu avec l'âge du compte.
- Top 20 des décisions E7 : absent.
- Quatre rangs exacts détenus avant l'article : non. Combinaison cotée environ 0,28 à cette date, donc pas rare par rapport aux prix.

**Niveau de confiance et limites.**

- Lien étiquette vers adresse : **moyenne à élevée** (parts de la capture).
- Flux : **élevée** sur 14 relations lues sur la chaîne, **moyenne** sur 0 relations dépendant d'un service ou d'une étiquette.
- Coordination et information privilégiée : **non démontrées**, aucune preuve dans ce dossier ne les établit.
- Mouvements natifs non lus hors enregistrement Relay. Soldes lus à la date indiquée, ils peuvent changer.

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
- Lien discriminant : aucun. Transfert de fonds direct avec un autre dossier : aucun sur les chaînes et jetons lus.
- Issues aussi détenues par d'autres nommés : Kylian Mbappé or Lamine Yamal / Mbappé (10 autres); Harry Kane win / Yes (4 autres); Lamine Yamal finish 3rd in / Yes (4 autres); Rodri or Lionel Messi / Rodri (3 autres).

**Explications alternatives et faux positifs.**

- Profil de petit parieur actif : nombreux tickets, 8 dépôts, 9 issues, et des retraits en cours de route. Aucune priorité ni comportement dans S_A.
- Faux positifs d'une règle de « financeur commun » : `0xc8a6871d…8d64`, `0x4cd00e38…bc31`, `0xc1d13492…a1b5`. Ce sont des services, ils ne relient personne.
- Biais de sélection : ce compte est étudié parce que la presse l'a nommé après le résultat. Taille et âge ne sont donc pas des résultats indépendants.

**Résultats des contrôles statistiques.** Lecture individuelle descriptive : n effectif de l'affaire = 1, sans puissance par wallet.

- S_A scellé : vu, 0 paire(s) avec comportement, score maximal 0, **0 priorité**. Comparaison exploratoire, hors R3.
- Alerte A0 : 2026-10-11 14:00:00, Kylian Mbappé or Lamine Yamal / Mbappé, 3 wallets, avant le 13 oct. 18:51.
- Alerte du recensement E1G : membre d'aucune.
- Rafales E2, membre de : 1 à 5 min, 1 à 15 min, 1 à 60 min.
- Petits puis gros E3 : non.
- Combinaisons inhabituelles E4 v2 : 0 paire sur les trois graines et les deux dates.
- Autres nommés achetant le même token à moins de 5 min : 0x86544e4dfde, vidente, zoomman17 ; à moins de 60 min : 5.
- Financement E6 : 1,0 min entre le dernier dépôt et le premier achat. 1 comparateurs sur 42 font aussi court ou plus court. Confondu avec l'âge du compte.
- Top 20 des décisions E7 : absent.
- Quatre rangs exacts détenus avant l'article : non. Combinaison cotée environ 0,28 à cette date, donc pas rare par rapport aux prix.

**Niveau de confiance et limites.**

- Lien étiquette vers adresse : **élevée** (nom exact et parts de la capture).
- Flux : **élevée** sur 25 relations lues sur la chaîne, **moyenne** sur 4 relations dépendant d'un service ou d'une étiquette.
- Coordination et information privilégiée : **non démontrées**, aucune preuve dans ce dossier ne les établit.
- Mouvements natifs non lus hors enregistrement Relay. Soldes lus à la date indiquée, ils peuvent changer.

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
- Lien discriminant : aucun. Transfert de fonds direct avec un autre dossier : aucun sur les chaînes et jetons lus.
- Issues aussi détenues par d'autres nommés : Kylian Mbappé or Lamine Yamal / Mbappé (10 autres); Harry Kane win / Yes (4 autres).

**Explications alternatives et faux positifs.**

- Deux paris cohérents entre eux, Kane et Mbappé devant Yamal, pris au moment où Kane montait déjà. Compatible avec une lecture du marché.
- Faux positifs d'une règle de « financeur commun » : `0xc8a6871d…8d64`, `0x0ce9bdf3…f06d`. Ce sont des services, ils ne relient personne.
- Biais de sélection : ce compte est étudié parce que la presse l'a nommé après le résultat. Taille et âge ne sont donc pas des résultats indépendants.

**Résultats des contrôles statistiques.** Lecture individuelle descriptive : n effectif de l'affaire = 1, sans puissance par wallet.

- S_A scellé : vu, 1 paire(s) avec comportement, score maximal 1, **0 priorité**. Comparaison exploratoire, hors R3.
- Alerte A0 : membre d'aucune.
- Alerte du recensement E1G : membre d'aucune.
- Rafales E2, membre de : 0 à 5 min, 1 à 15 min, 2 à 60 min.
- Petits puis gros E3 : non.
- Combinaisons inhabituelles E4 v2 : 0 paire sur les trois graines et les deux dates.
- Autres nommés achetant le même token à moins de 5 min : 0x86544e4dfde ; à moins de 60 min : 2.
- Financement E6 : 3,3 min entre le dernier dépôt et le premier achat. 4 comparateurs sur 42 font aussi court ou plus court. Confondu avec l'âge du compte.
- Top 20 des décisions E7 : absent.
- Quatre rangs exacts détenus avant l'article : non. Combinaison cotée environ 0,28 à cette date, donc pas rare par rapport aux prix.

**Niveau de confiance et limites.**

- Lien étiquette vers adresse : **élevée** (nom exact et parts de la capture).
- Flux : **élevée** sur 11 relations lues sur la chaîne, **moyenne** sur 0 relations dépendant d'un service ou d'une étiquette.
- Coordination et information privilégiée : **non démontrées**, aucune preuve dans ce dossier ne les établit.
- Mouvements natifs non lus hors enregistrement Relay. Soldes lus à la date indiquée, ils peuvent changer.

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
- Lien discriminant : aucun. Transfert de fonds direct avec un autre dossier : aucun sur les chaînes et jetons lus.
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
- Combinaisons inhabituelles E4 v2 : 0 paire sur les trois graines et les deux dates.
- Autres nommés achetant le même token à moins de 5 min : brace227 ; à moins de 60 min : 3.
- Financement E6 : 2,6 min entre le dernier dépôt et le premier achat. 4 comparateurs sur 42 font aussi court ou plus court. Confondu avec l'âge du compte.
- Top 20 des décisions E7 : absent.
- Quatre rangs exacts détenus avant l'article : non. Combinaison cotée environ 0,28 à cette date, donc pas rare par rapport aux prix.

**Niveau de confiance et limites.**

- Lien étiquette vers adresse : **moyenne à élevée** (parts de la capture).
- Flux : **élevée** sur 20 relations lues sur la chaîne, **moyenne** sur 1 relations dépendant d'un service ou d'une étiquette.
- Coordination et information privilégiée : **non démontrées**, aucune preuve dans ce dossier ne les établit.
- Mouvements natifs non lus hors enregistrement Relay. Soldes lus à la date indiquée, ils peuvent changer.

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
- Lien discriminant : aucun. Transfert de fonds direct avec un autre dossier : aucun sur les chaînes et jetons lus.
- Issues aussi détenues par d'autres nommés : Kylian Mbappé or Lamine Yamal / Mbappé (10 autres); Harry Kane win / Yes (4 autres); Lamine Yamal finish 3rd in / Yes (4 autres); Kylian Mbappé finish 2nd in / Yes (2 autres).

**Explications alternatives et faux positifs.**

- Le plus progressif : 14 petits dépôts depuis le 1er octobre, rotation visible de Kane vers les rangs exacts à mesure que ces marchés ouvrent, comme le note la capture. Compatible avec un parieur actif qui prend ses gains et se repositionne.
- Faux positifs d'une règle de « financeur commun » : `0xc8a6871d…8d64`, `0x4cd00e38…bc31`, `0xc1d13492…a1b5`, `0x58f298e3…0214`. Ce sont des services, ils ne relient personne.
- Biais de sélection : ce compte est étudié parce que la presse l'a nommé après le résultat. Taille et âge ne sont donc pas des résultats indépendants.

**Résultats des contrôles statistiques.** Lecture individuelle descriptive : n effectif de l'affaire = 1, sans puissance par wallet.

- S_A scellé : vu, 0 paire(s) avec comportement, score maximal 0, **0 priorité**. Comparaison exploratoire, hors R3.
- Alerte A0 : membre d'aucune.
- Alerte du recensement E1G : membre d'aucune.
- Rafales E2, membre de : 0 à 5 min, 0 à 15 min, 2 à 60 min.
- Petits puis gros E3 : non.
- Combinaisons inhabituelles E4 v2 : 0 paire sur les trois graines et les deux dates.
- Autres nommés achetant le même token à moins de 5 min : aucun ; à moins de 60 min : 4.
- Financement E6 : 2,2 min entre le dernier dépôt et le premier achat. 3 comparateurs sur 42 font aussi court ou plus court. Confondu avec l'âge du compte.
- Top 20 des décisions E7 : absent.
- Quatre rangs exacts détenus avant l'article : oui. Combinaison cotée environ 0,28 à cette date, donc pas rare par rapport aux prix.

**Niveau de confiance et limites.**

- Lien étiquette vers adresse : **élevée** (parts de la capture, et vente de Kane pour Yamal 3e conforme à la note de la capture).
- Flux : **élevée** sur 45 relations lues sur la chaîne, **moyenne** sur 7 relations dépendant d'un service ou d'une étiquette.
- Coordination et information privilégiée : **non démontrées**, aucune preuve dans ce dossier ne les établit.
- Mouvements natifs non lus hors enregistrement Relay. Soldes lus à la date indiquée, ils peuvent changer.

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
- Swap dans la transaction de retrait `0x909d9602d5ad975b2f30c66d4a058592306e2468a002dd0a691170b61677a6f1` : le reçu montre l'échange, le paiement natif ne laisse pas de log et le montant reçu repose sur l'enregistrement Relay. Solde natif actuel de `0x1B500B6c…5f2c` : 3,14. Ces fonds sont donc repartis, et leur destination n'a pas été lue : les mouvements natifs ne sont pas scannés.
- Relations à identifiant stable : ONCHAIN_CONFIRMED 6, PROTOCOL_CONFIRMED 5, SERVICE_INTERACTION 2.

**Liens éventuels avec les autres wallets.**

- SERVICE_ETIQUETE : `BmFdpraQhk…ymy6`, aussi 0xdd97e6, cookedrice, thin, vidente.
- SERVICE_MESURE : `0xee7ae85f…4055`, aussi wen.
- Lien discriminant : aucun. Transfert de fonds direct avec un autre dossier : aucun sur les chaînes et jetons lus.
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
- Combinaisons inhabituelles E4 v2 : 0 paire sur les trois graines et les deux dates.
- Autres nommés achetant le même token à moins de 5 min : aucun ; à moins de 60 min : 0.
- Financement E6 : 10,1 min entre le dernier dépôt et le premier achat. 7 comparateurs sur 42 font aussi court ou plus court. Confondu avec l'âge du compte.
- Top 20 des décisions E7 : absent.
- Quatre rangs exacts détenus avant l'article : oui. Combinaison cotée environ 0,28 à cette date, donc pas rare par rapport aux prix.

**Niveau de confiance et limites.**

- Lien étiquette vers adresse : **élevée** (nom exact).
- Flux : **élevée** sur 11 relations lues sur la chaîne, **moyenne** sur 2 relations dépendant d'un service ou d'une étiquette.
- Coordination et information privilégiée : **non démontrées**, aucune preuve dans ce dossier ne les établit.
- La trace s'arrête à : `5oXG1xh68W…paxJ`. Seul le service connaît le compte d'origine.
- Mouvements natifs non lus hors enregistrement Relay. Soldes lus à la date indiquée, ils peuvent changer.

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
- Relations à identifiant stable : ONCHAIN_CONFIRMED 4, PROTOCOL_CONFIRMED 3, SERVICE_INTERACTION 1.

**Liens éventuels avec les autres wallets.**

- SERVICE_ETIQUETE : `BmFdpraQhk…ymy6`, aussi cookedrice, ouldlm3alem, thin, vidente.
- Lien discriminant : aucun. Transfert de fonds direct avec un autre dossier : aucun sur les chaînes et jetons lus.
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
- Combinaisons inhabituelles E4 v2 : 0 paire sur les trois graines et les deux dates.
- Autres nommés achetant le même token à moins de 5 min : aucun ; à moins de 60 min : 3.
- Financement E6 : 1,5 min entre le dernier dépôt et le premier achat. 1 comparateurs sur 42 font aussi court ou plus court. Confondu avec l'âge du compte.
- Top 20 des décisions E7 : absent.
- Quatre rangs exacts détenus avant l'article : oui. Combinaison cotée environ 0,28 à cette date, donc pas rare par rapport aux prix.

**Niveau de confiance et limites.**

- Lien étiquette vers adresse : **moyenne** (préfixe de presse unique).
- Flux : **élevée** sur 7 relations lues sur la chaîne, **moyenne** sur 1 relations dépendant d'un service ou d'une étiquette.
- Coordination et information privilégiée : **non démontrées**, aucune preuve dans ce dossier ne les établit.
- La trace s'arrête à : `4MMHYz6K6z…zgE1`. Seul le service connaît le compte d'origine.
- Mouvements natifs non lus hors enregistrement Relay. Soldes lus à la date indiquée, ils peuvent changer.

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

Les liens Relay classés `PROTOCOL_CONFIRMED` portent le même identifiant dans le log d'escrow et dans le paiement, lus sur les deux chaînes. Cette preuve ne dépend pas de l'API de Relay. L'API reste utile pour trouver le paiement, et sa route publique disparaît le 24 novembre.

## 4. Liens de financement reclassés

Une règle naïve de « financeur commun » relierait **21 paires sur 55**. Après classement, **0 paire** repose sur une adresse discriminante.

| Adresse partagée | Classe | Dossiers | Aussi chez les témoins | Pourquoi |
|---|---|---|---|---|
| `BmFdpraQhk…ymy6` | SERVICE_ETIQUETE | 0xdd97e6, cookedrice, ouldlm3alem, thin, vidente | token_oppose 1 | KuCoin Hot Wallet 2, selon orbmarkets.io |
| `0xc8a6871d…8d64` | SERVICE_MESURE | 0x86544e4dfde, brace227, kraben006, walletwallet8424, zoomman17 | meme_token 1, token_oppose 3, fraiches_recensement 1 | 215 sorties et 211 entrées en 3,75 h, un seul payeur |
| `0x4cd00e38…bc31` | SERVICE_ETIQUETE | brace227, kraben006, zoomman17 | non | Relay Depository, selon api.relay.link |
| `GxjcMTWWDc…nvBW` | SERVICE_MESURE | cookedrice, vidente | non | Environ 1,2 transaction par minute. Sur 120 transactions lues : 18 entrées, 95 sorties, 67 destinataires. Sur 400 tirées : 73 entrées, médiane 270 $,  |
| `0xee7ae85f…4055` | SERVICE_MESURE | ouldlm3alem, wen | token_oppose 1 | Polygon : 1 173 sorties vers 824 destinataires en 12 h autour du 18 oct. Arbitrum : 890 sorties vers 743 destinataires en 12 h autour du 26 oct. Appel |
| `0x0ce9bdf3…f06d` | SERVICE_MESURE | 0x86544e4dfde, walletwallet8424 | non | 85 sorties vers 57 destinataires en 3,8 h |
| `0xc1d13492…a1b5` | SERVICE_MESURE | brace227, kraben006 | non | 549 sorties vers 454 destinataires en 10 h |
| `0x58f298e3…0214` | SERVICE_MESURE | kraben006, zoomman17 | non | Nonce de 114 468 |

**Transferts directs.** Scan de 33 adresses (wallets, clés, adresses de pont, destinations), Polygon et Ethereum, stablecoins, pUSD et positions, depuis le 25 sept. : **0 transfert de fonds entre dossiers**. Une seule exécution de carnet d'ordres entre deux dossiers : OuldLm3alem vend 520,97 parts à 0,53 à 0x86544e4dfde, le 26 oct. 13:29:02 UTC, `0x870eaa6cb8298d7a02379b48093d4633af4f77ba58638bfc78ff9b0146f30b48`. C'est ordinaire sur un carnet. `graphs/direct_transfers.json`.

**Montant et heure.** 0 candidat entre une sortie et une entrée à 6 h et 90 à 100,1 %, sur 25 sorties et 46 entrées. Placebo à dates décalées : 0 aussi. `graphs/links.json`.

### Taux de base et faux positifs

Même lecteur sur un dépôt par wallet, 11 nommés et 50 comparateurs : `controls/funding_baseline_detail.jsonl`. L'échantillon est partiel : 6 non surlignés sur 6, 7 même token sur 10, 25 token opposé sur 27, 12 comptes frais sur 40. Le garde-fou disque a arrêté la collecte au réveil du Mac et elle n'a pas été prolongée, sur ta consigne d'utiliser les données déjà collectées. L'ordre de lecture ne dépend pas du résultat : adresses triées, tirage à graine fixe.

| Trait | Nommés | Non surlignés | Même token | Token opposé | Comptes frais du recensement | Tous témoins | p unilatéral, non corrigé |
|---|---|---|---|---|---|---|---:|
| Passage par KuCoin Hot Wallet 2 | 3/11 | 0/6 | 0/7 | 1/25 | 0/12 | 1/50 | 0,016 |
| Origine Solana | 3/11 | 0/6 | 0/7 | 2/25 | 0/12 | 2/50 | 0,037 |
| Contrat `0xc8a6…` | 5/11 | 0/6 | 1/7 | 3/25 | 1/12 | 5/50 | 0,012 |
| Relay | 11/11 | 4/6 | 3/7 | 16/25 | 11/12 | 34/50 | 0,024 |
| Adresse de pont 7702 | 6/11 | 4/6 | 2/7 | 14/25 | 11/12 | 31/50 | 0,789 |

Sur tous leurs dépôts, 5 nommés sur 11 passent par cette étiquette : 0xdd97e6, cookedrice, ouldlm3alem, thin, vidente. Ce chiffre ne se compare pas à la ligne du tableau, qui lit un seul dépôt. **KuCoin ressort donc plus souvent chez les nommés (3/11 contre 1/50, p ≈ 0,016 avant correction).** Face aux seuls comptes frais, l'écart tombe à 3/11 contre 0/12, p ≈ 0,093. Avec cinq traits regardés après coup, un groupe choisi par la presse et une étiquette à source unique, c'est un indice faible, sans aucune valeur de propriété commune : un exchange sert de très nombreux clients.

**L'âge explique une partie de ces écarts.** Relay vaut 11/11 chez les nommés et 11/12 chez les comptes frais : les comptes récents passent simplement par ce chemin.

**Faux positifs identifiés et écartés :**

- `0xc8a6…`, `0xee7a…`, `GxjcMTWW…`, `0x0ce9…`, `0xc1d1…`, `0x58f2…` : chacun relie plusieurs dossiers, et chacun se révèle mutualisé à la mesure. Tableau ci-dessus.
- La route `0xf70d… → 0xb92f… → 0xc8a6…`, signalée le 30 octobre comme « nature inconnue » entre brace227 et walletwallet8424 : c'est Relay et un contrat de passage, donc pas un lien.
- `GxjcMTWW…` : VidenteRibeira et cookedrice y déposent à un jour d'écart (51 489,00 USDT, 39 158,00 USDC). Service à 1 % de frais, payant par morceaux. Sur 400 transactions tirées, 2 entrées à 10 000 $ ou plus sur 73, médiane 270,38 $ : ces gros dépôts sont plutôt rares, sans que cela relie leurs auteurs. Les sorties ne s'apparient pas sans le registre du service.
- Part de 29 353 $ sur 30 398 $ d'achats côté Mbappé le 13 octobre par des comptes nommés : mécanique, puisqu'ils sont nommés parce qu'ils détenaient ce token.
- Pièges de lecture évités : nœud Solana rendant 0 signature pour une adresse payée, hash du pont introuvable sur sa chaîne, sondage récent de `0xee7a…` à 0 trafic. Ces trois faux zéros ont été recoupés.

## 5. Détection collective

Plan gelé avant tout calcul de taux (`collective/analysis_plan.md`, `PROTOCOL.lock`), partie A scellée avant la lecture des noms et des résultats. **L'auteur connaissait l'affaire : aucune validation n'en découle.** Une seule affaire, donc n effectif = 1.

### A. Analyse prospective simulée

**Verdict fixé d'avance, au 13 oct. 18:51 UTC comme au 23 oct. 15:17 UTC : `VISIBLE_NON_SPECIFIQUE`.**

- **Alerte de cohorte fraîche A0** (au moins 3 wallets de 14 jours ou moins, 1 000 $ chacun, 10 000 $ en tout, sur 72 h) : 5 tokens de la famille en alerte au 13 octobre, 14 au 23 octobre sur 346. Témoins tirés : 4 sur 59. Femmes : 0 sur 148, sans puissance.
- **Recensement de tout Polymarket :** meilleur token de la famille au rang 41 au 13 octobre, et au rang 50 au 23 octobre. Le verdict exigeait le top 10. Charge : au plus 12 nouveaux tokens par jour hors famille.
- **Placebo des âges mélangés** (1 000 tirages) : maximum de 8 wallets frais au 13 octobre, p = 0,145 ; 10 au 23 octobre, p = 0,298. La fraîcheur ne se concentre pas plus qu'au hasard. Aucun p de cette étude n'approche le seuil de Bonferroni du registre, voir `collective/results.md`.
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

Rien de cette section n'utilise un nom, un résultat ou une donnée postérieure à la date simulée. Reproduction en copie fraîche : E1, E1G, E2, E3 et le placebo identiques au sceau (`collective/audit/REPRODUCTION.json`).

### B. Investigation rétrospective

Cette partie lit les noms et les résultats. Elle ne revient jamais dans A.

- **Wallets étudiés :** 11 wallets nommés lus en détail ; 50 comparateurs pour le financement, dont les 6 non surlignés ; 3 082 wallets dont l'âge a été lu, dont 388 avec des achats dans la famille.
- **Montant cumulé sur la même issue :** 168 888,64 $ sur Mbappé devant Yamal par les 11, dont 57 544,64 $ avant le 13 oct. 18:51 UTC et 155 188,28 $ avant l'article. Kane vainqueur : 80 389,22 $ par 5 d'entre eux, dont 51 141,79 $ avant le 13 octobre.
- **Première alerte de la famille contenant des comptes nommés :** 2026-10-11 14:00:00 UTC sur Mbappé devant Yamal, les 3 wallets sont 0x86544e4dfde, brace227, zoomman17. Biais : acheter gros tôt mène justement dans le top de la capture.
- **Achats synchrones :** 5 paires nommées à 5 min, 14 à 60 min sur 55. Contre groupes tirés sur le token opposé : centiles 95,5 à 5 min et 84,2 à 60 min, non corrigés. Part de leurs dollars sur les 24 h les plus actives : 15,3 %, centile 9,8. Ces achats sont étalés sur des semaines, pas groupés.
- **Combinaisons de paris (E4 v2, trois graines) :** 12 paires inhabituelles au 13 octobre, 37 au 23 octobre, dont **0 impliquant un compte nommé**. 23 paires stables sur les trois graines au 23 octobre. Le nombre change avec la graine (25 à 34), donc il ne faut pas lire ce chiffre au point près.
- **Classement exact :** avant l'article, une seule combinaison complète des rangs 2 à 5 est détenue parmi 42 wallets : la bonne, par 4 wallets (kraben006, 0xdd97e6, 0xeed8c2be…35f0, ouldlm3alem). **Ce n'est pas rare par rapport aux prix** : le produit des quatre prix valait environ 0,28 à cette date, et ces marchés ouvrent déjà vers 0,6 le 19 octobre.
- **Financement avant achat :** écart médian 2,6 min chez les nommés, 9/11 sous une heure. Non surlignés 2/6, même token 1/10, token opposé 7/27. Confondu avec l'âge : un compte neuf dépose puis mise.
- **Prix et liquidité :** aucun carnet daté n'existe. Parmi les 20 plus grosses décisions, 2 viennent de comptes nommés. Thin le 13 oct. : 14 935,70 $, 0,88 fois le volume des 24 h précédentes du token, prix de 0,490 avant à 0,577 payé en moyenne.

### Les questions posées

| Question | Réponse |
|---|---|
| Ont-ils misé au même moment ? | Non, pas de manière distincte : étalés du 1er au 26 octobre, peu de paires proches. |
| Ont-ils acheté les mêmes issues ? | Oui sur Mbappé devant Yamal (11/11), mais 9 ont été choisis sur ce critère. 5/11 sur Kane. |
| Combinaisons statistiquement rares ? | Non établi : aucune paire nommée dans E4 v2, combinaison exacte déjà cotée environ 28 %. |
| Mises anormales par rapport à la liquidité ? | Certaines sont grandes par rapport au volume récent. Sans carnet daté, la profondeur reste inconnue. |
| Financements similaires avant les achats ? | Oui en apparence, mais confondu avec l'âge des comptes. |
| Routes communes ? | Oui, uniquement des services. Aucune discriminante. |
| Conforme à des informations publiques ? | Non déterminable. Selon des extraits de recherche d'Oddschecker, Yamal est favori le 5 octobre, Mbappé à 22/1. Sur Polymarket, Kane passe de 0,49 le 7 octobre à 0,66 le 11, sans source datée trouvée pour ces jours. |
| Visible le 13 octobre ? | Oui au sens du plan, sans spécificité. Rang 41 sur tout Polymarket. PolySentinel n'existait pas à cette date. |

## 6. ChangeNOW, FixedFloat, XMR

Sur les sauts lus, **aucune interaction avec une adresse étiquetée ChangeNOW ou FixedFloat, et aucun échange XMR**. Le statut `XMR_VISIBILITY_BOUNDARY` n'est donc jamais posé. Cela n'exclut rien : ma liste ChangeNOW compte 8 adresses Polygon de seconde main (`tools/services.json`). Pour Solana, l'étude `cn_pm_sakana` n'a gardé que les préfixes de deux hubs : aucune adresse lue ne les porte, mais un préfixe reste un test faible. Je n'ai aucune adresse FixedFloat, et ces services paient depuis des adresses qui tournent.

`GxjcMTWW…` est le point le plus proche : un service non identifié qui prélève 1 % et paie par morceaux. Rien ne permet de dire ce qu'il est, ni de suivre ce qui en sort.

**Iris :** aucune clé trouvée, aucun crédit consommé, aucune adresse envoyée. Requêtes les plus utiles : `reports/iris_requetes.md`.

## 7. Limites

- Flux **taker seulement** pour les univers de l'étude collective : un compte par ordres limites n'y apparaît pas. Le dossier de chaque wallet lit, lui, son activité complète.
- Stablecoins lus dans les logs : les mouvements natifs (ETH, POL, BNB, SOL) ne le sont pas, sauf là où un enregistrement Relay les nomme. Exemple : 0xdd97e6 sort en ETH, OuldLm3alem en partie en jeton natif.
- Étiquettes de services incomplètes et datées. KuCoin : une seule source. BscScan et Polygonscan refusent la lecture automatique.
- `Non surlignés`, `Même token`, `Token opposé` et `Comptes frais` sont des échantillons partiels pour le taux de base (voir section 4).
- Comparateurs imparfaits : témoins surtout sportifs, famille féminine sans puissance, comptes nommés choisis après coup.
- Trois wallets non nommés détiennent la même combinaison complète de rangs (`0xeed8c2be…35f0`, `0x1583c5d3…cdde`, `0x14c32680…df68`). Seule cette similarité les rapproche : aucun dossier ouvert, aucun financement testé, aucune mise en cause. Aucun wallet supplémentaire n'est relié aux onze par une preuve de chaîne.
- Sorties natives non suivies : les 839 893,73 POL d'OuldLm3alem et les 26,97 ETH de 0xdd97e6. Destination des premiers non lue, solde des seconds non vérifié.
- Non lancés : les quatre audits indépendants à l'aveugle et les deux audits de conclusions du protocole d'étude gelée. Ce rapport n'a pas de relecture indépendante.
- Reproduction : E1, E1G, E2, E3 et placebo identiques. E4 d'origine non reproductible, corrigé par E4 v2 (amendement 002), son ancienne sortie est conservée.

## 8. Synthèse des hypothèses

**Confirmées :** H1, H2. **Réfutées, dans le périmètre indiqué :** H5, H6, H10. **Affaiblies :** H3, H4, H7, H8, H9, H11. **Non tranchées :** H12, H13, H14, H15.

Confirmée : les données la soutiennent directement. Affaiblie : testée, non soutenue, sans pouvoir l'exclure. Réfutée : contredite par les données, dans le périmètre indiqué. Non tranchée : indice faible, listes incomplètes, ou données publiques insuffisantes.

| # | Hypothèse | Statut | Sur quoi |
|---|---|---|---|
| H1 | Les onze étiquettes correspondent à des wallets identifiables | **CONFIRMÉE, niveaux inégaux** | Capture reproduite 15 lignes sur 15 ; 7 noms exacts, 3 par les parts, 1 par préfixe |
| H2 | Ces comptes ont réalisé des gains | **CONFIRMÉE pour 7 comptes soldés, non établie pour 4** | Comptabilité complète, résidu nul sur les soldés |
| H3 | Un même opérateur contrôle les onze | **AFFAIBLIE** | 11 clés distinctes, routes différentes, 0 transfert direct, 0 lien discriminant. Des comptes d'exchange restent invisibles : non exclue |
| H4 | Un financeur personnel commun relie certains comptes | **AFFAIBLIE** | 21 paires naïves, 0 après reclassement. Hors des sauts lus, inconnu |
| H5 | La route commune brace227 et walletwallet8424 du 30 octobre est un lien | **RÉFUTÉE comme lien** | Relay plus contrat de passage à fort trafic |
| H6 | Un signal collectif spécifique était visible le 13 octobre | **RÉFUTÉE pour la règle testée** | Verdict gelé VISIBLE_NON_SPECIFIQUE, rang 41 du recensement. Ne vaut pas pour toute autre règle |
| H7 | Des comptes frais se concentrent sur une issue plus que le hasard | **AFFAIBLIE** | Placebo p = 0,145 puis 0,298, 1 000 tirages |
| H8 | Les comptes nommés achètent de façon synchrone | **AFFAIBLIE** | 5 paires à 5 min sur 55, centile 95,5 non corrigé, mais centile 84,2 à 60 min et 9,8 sur la concentration en 24 h |
| H9 | Les nommés partagent des combinaisons inhabituelles | **AFFAIBLIE** | E4 v2 : 0 paire nommée sur 37 paires et trois graines |
| H10 | Détenir le classement exact était rare | **RÉFUTÉE par rapport aux prix** | Combinaison cotée environ 0,28 avant l'article, marchés de rangs ouverts vers 0,6 |
| H11 | Les comptes nommés ont eux-mêmes lancé la hausse de Kane | **AFFAIBLIE** | Hausse amorcée le 8 octobre : 24 444 $ d'achats, 0 $ de comptes nommés. Ils pèsent ensuite 25 à 53 % des achats du 9 au 11 |
| H12 | Une route KuCoin plus fréquente chez les nommés | **INDICE FAIBLE, non confirmée** | 3/11 contre 1/50, p ≈ 0,016 non corrigé, 0,093 face aux seuls comptes frais, étiquette à source unique |
| H13 | Les fonds passent par ChangeNOW, FixedFloat ou XMR | **NON SOUTENUE** | Aucune interaction sur les sauts lus, listes incomplètes, deux chaînes s'arrêtent à un service non identifié |
| H14 | Des retraits coordonnés | **NON DÉMONTRÉE** | Plusieurs retraits peu après la résolution, ce qu'impose le calendrier du marché. Aucun comparateur daté de cette fenêtre |
| H15 | Une information privilégiée | **NON TESTABLE ici** | Aucune preuve d'accès. Des données publiques seules ne peuvent pas trancher |

## 9. Conclusion

### FAITS DÉMONTRÉS

- La capture Upside correspond à 15 wallets du tape public, ligne par ligne.
- Les dépôts, positions et retraits des 11 wallets, avec 182 relations à identifiant stable dans `graphs/relations.jsonl`.
- 7 comptes soldés totalisent 129 367,79 $ de retraits moins dépôts.
- Des liens entre chaînes prouvés par le même identifiant Relay dans les deux sens.
- Aucun transfert de fonds direct entre ces dossiers, sur les chaînes et jetons lus.
- À la date de lecture, des sorties restent immobiles : Thin-Disclaimer-Life 39 999,85 USDC sur `CXVYMP5qxB…GrfJ`, Thin-Disclaimer-Life 39 537,78 USDC sur `EnHRjTP4pK…PZ8B`, 0x86544e4dfde 74 198,32 sur `0x69837228…0ded`, brace227 22 024,57 sur `0xc852b093…af26`, walletwallet8424 35 546,89 sur `0x82775eb8…a3a1`, kraben006 15 154,83 sur `0x101b5f4d…fb65`.
- Au 13 octobre, la règle A0 alerte sur 5 tokens, et le meilleur de la famille reste au rang 41 du recensement.

### HYPOTHÈSES PLAUSIBLES

- Des retraits d'exchange directs vers l'adresse de dépôt Polymarket, pour une partie des dépôts.
- Des comptes neufs convaincus, ou des suiveurs d'un mouvement de marché : la hausse de Kane du 8 au 11 octobre est large et ne dépend pas d'eux seuls.

### INDICES FAIBLES

- KuCoin plus fréquent chez les nommés (3/11 contre 1/50, non corrigé).
- Le même service à 1 % pour VidenteRibeira et cookedrice, à un jour d'écart.
- Peu d'acheteurs côté Mbappé pendant que le prix monte, avec un biais de sélection.
- 4 changements de nom dans la capture, dont un compte non surligné : leurs dates sont inconnues.

### NON DÉTERMINABLE

- Qui contrôle ces wallets, et si plusieurs ont le même propriétaire.
- L'origine de leur conviction, et s'ils ont eu accès au résultat.
- Ce que les exchanges et services savent de ces comptes : seule une demande légale y accède.
- Ce qui sort de `GxjcMTWW…`, et l'identité de ce service.
- La liquidité réelle au moment des achats.
- La détection réelle de PolySentinel le 13 octobre : le service n'existait pas.

## 10. Incidents et corrections pendant l'enquête

- **S_C arrêté deux fois par son garde-fou.** Le 1er nov. vers 22:48 UTC, battement du collecteur à plus de 180 s, charge à 27, avec le rendu vidéo, un benchmark d'une autre session et mes scripts : ma part n'est pas mesurée. Le 2 nov. vers 07:39 UTC, au moment du réveil du Mac, endormi depuis 01:13 : swap +6,8 Go, disque tombé à 11,2 Go. Mes scripts dépassaient alors au plus 180 Mo et ne sont pas en cause. S_C a repris seul. Aucun fichier du rejeu n'a été touché.
- **Erreurs de mon code, corrigées :** adresse zéro prise pour destination, swap dans la même transaction non géré, course d'écriture sur le cache entre deux processus, seuil « avant cérémonie » faux dans E6 (champ non cité, fichier gelé conservé), lot de comparaison `meme_token` dégénéré (centiles non cités).
- **Trois workers réseau pendant moins de 2 minutes,** au lieu de deux, corrigé tout de suite.
- **`rm -rf` bloqué par un contrôle de sécurité,** non contourné. Une copie de reproduction reste dans le scratchpad de session.

## 11. Fichiers

| Fichier | Contenu |
|---|---|
| `cases/<dossier>.md`, `.json` | Dossier complet par wallet, historique daté, hashes |
| `reports/inventaire_adresses.md` | Liens étiquette vers adresse |
| `reports/liens_entre_wallets.md` | Reclassement et faux positifs |
| `archive/20261102_avant_correction_burn/` | Dossiers et liens d'avant la correction, conservés |
| `reports/iris_requetes.md`, `reports/proposition_shadow.md` | Requêtes Iris, proposition d'intégration |
| `reports/sources_cinq_depots.md` | Les cinq dépôts de recherche |
| `graphs/relations.jsonl`, `graphs/links_classified.json`, `graphs/direct_transfers.json` | Relations et liens |
| `collective/` | Étude gelée : plan, code, sorties, amendements, registre |
| `controls/` | Taux de base |
| `evidence/` | Reçus, captures, mesures |
