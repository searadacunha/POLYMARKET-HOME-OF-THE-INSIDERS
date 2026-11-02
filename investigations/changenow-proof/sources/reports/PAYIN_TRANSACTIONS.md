# Entrées vers ChangeNOW

Lu le 2 novembre 2026. Montants exacts et empreintes des preuves : `data/verified_transfers.csv`.

## Résultat

**Sur les 11 comptes, une seule entrée probable vers ChangeNOW : 0,00247406 ETH, depuis la clé de kraben006.** Chaque transfert est prouvé. Le fait que le relais soit une adresse de dépôt est une déduction.

Aucun wallet Polymarket et aucune clé n'envoie directement à une adresse étiquetée ChangeNOW.

## L'entrée de kraben006

| Étape | UTC | De | Vers | Valeur (wei) | Transaction | Bloc |
|---|---|---|---|---|---|---|
| Envoi | 2026-10-04 23:48:47 | `0x101b5f4dc0886c32e2b75972101aeaf9f338fb65` | `0x7e67df45e0a0bab092cbb2ff045f8aa8dfab6e23` | 2 474 060 000 000 000 | `0x1a39308b89cc7d9de6e38fbf0c62aa5d0bdd777863079cd151fe12a6b135dd71` | 26122383 |
| Balayage, 492 s après | 2026-10-04 23:56:59 | `0x7e67df45e0a0bab092cbb2ff045f8aa8dfab6e23` | `0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b` | 2 414 060 000 000 000 | `0x22710b5e691160746fd4e054346daf18c91e98532999c1bd3bd9067340fe9c26` | 26122424 |

- **Niveaux :** l'envoi de la clé au relais est au **niveau 0**, car `0x7e67df45…` n'est étiquetée nulle part : chemin indirect, inféré par empreinte (`reports/ATTRIBUTION_EVIDENCE.md`, section F). Le balayage vers `0x3f3ee0a9…` est au **niveau 2**, conditionné à l'attribution de cette adresse. Seuls 0,00241406 ETH l'atteignent.
- **Ce n'est pas un `payinAddress` documenté.** Seul un ordre le prouverait.
- **Valeur :** environ 6,7 $, à environ 2 700 $ l'ETH, d'après le rapport existant (5,53 $ pour 0,00205 ETH). Estimation, pas une mesure.

## D'où vient cet ETH

Soldes de la clé lus sur nœud :

| Moment | Solde (wei) |
|---|---|
| Avant le transfert de brace227, bloc 26119419 | 2 007 933 228 056 898 |
| Après, bloc 26119420 | 4 056 876 899 262 451 |
| Juste avant l'envoi, bloc 26122382 | 4 056 876 899 262 451 |
| Après l'envoi, bloc 26122383 | 1 559 054 917 606 451 |

- La clé de brace227 lui envoie 0,002048943671205553 ETH à 13:54:35 (`0xd07bea20a22d9381e0ab364e7a7421776318c6f4aa7258799638472ad7092b98`, lien déjà établi).
- **Aucune autre entrée entre les deux.** Les soldes le prouvent.
- L'envoi coûte 0,00247406 ETH et 0,000023761981656 ETH de gaz, soit plus que le solde d'avant : **au moins 0,000489888753599102 ETH, 19,8 % de l'envoi, viennent forcément de brace227**. Au plus 82,8 %. Le reste est une convention comptable. **« Le gaz reçu a été revendu » n'est donc pas démontré.**

## Comparaison avec Polymarket, kraben006

| Date UTC | Événement |
|---|---|
| 2026-10-01 18:31:03 | Premier dépôt |
| 2026-10-03 14:05:35 | 10 USDC envoyés à Relay, dernière opération avant l'envoi |
| **2026-10-04 23:48:47** | **Envoi de 0,00247406 ETH** |
| 2026-10-07 00:23:11 | Reprise des dépôts, 542,07 USDC |
| 2026-10-07 00:33:35 | Premier retour de fonds sur la clé |
| 2026-10-26 23:39:21 | Dernière activité |

Rien ne relie cet envoi à une opération Polymarket précise. Il n'y a ni retour d'ETH sur la clé, ni mouvement correspondant dans les 48 h.

## Recherche pour chaque compte

**Portée :** 122 859 lignes d'historique normalisées, 108 adresses étudiées dont 93 avec historique, chaînes 1, 137, 42161 et 10. Étiquettes interrogées en lot pour 1 349 contreparties. Les 15 adresses sans historique sont 14 adresses Solana et `0xae232f7885946fda51b3f1dac7e10ffaae00c026`.

| Compte | Nonces de la clé (lus par l'enquête) | Lignes d'historique dédoublonnées, y compris le bruit | Envoi direct à ChangeNOW | Envoi indirect | Gaz venant de ChangeNOW |
|---|---|---|---|---|---|
| kraben006 | ethereum 39 | 109 lignes | **0** | **1, ci-dessus** | Non |
| brace227 | ethereum 29, bsc 109 | 92 lignes | 0 | 0 lu | Sur l'intermédiaire seulement |
| zoomman17 | ethereum 38 | 128 lignes | 0 | 0 lu | Non |
| walletwallet8424 | ethereum 3, polygon 1 | 22 lignes | 0 | 0 lu | Sur un financeur mutualisé |
| ouldlm3alem | polygon 4, arbitrum 1 | 13 lignes | 0 | 0 lu | Non |
| 0x86544e4dfde | polygon 1 | 13 lignes | 0 | 0 lu | Non |
| thin | 0 sur 6 chaînes | 0 ligne | 0 | 0 lu | Non |
| vidente | 0 sur 6 chaînes | 0 ligne | 0 | 0 lu | Non |
| wen | 0 sur 6 chaînes | 0 ligne | 0 | 0 lu | Non |
| cookedrice | 0 sur 6 chaînes | 0 ligne | 0 | 0 lu | Non |
| 0xdd97e6 | 0 sur 6 chaînes | 0 ligne | 0 | 0 lu | Non |

## Second saut : clé, adresse intermédiaire, ChangeNOW

Sur les destinataires de valeur réelle jamais lus, 12 viennent directement d'une clé. Je les ai tous lus. **Aucun n'envoie à une adresse étiquetée ChangeNOW dans les lignes lues.** Deux ont été coupés à 1 000 lignes, ou plus : `0x4337ff05c84b9a80ea0a78dbe7b8e102f66d4c08` et `0xdc264714f68d84cf29bc605589405e78bdbe7c9f`. `0xe3478b0bb1a5084567c319096437924948be1964`, relais de gaz MetaMask, l'est aussi sur ses jetons.

Les destinataires qui reçoivent aussi du service sont listés dans `reports/PAYOUT_MATCHES.md`. Ils reçoivent, ils n'envoient pas : ce ne sont pas des entrées.

## Consolidation en aval

Le balayage arrive sur `0x3f3ee0a9…`, portefeuille de service. **Aucun envoi d'une clé ou d'un wallet étudié vers une adresse étiquetée ChangeNOW n'est donc observé directement.** À partir de là, plus rien n'est attribuable : dans les 10 heures autour, 826 entrées et 530 sorties. La première sortie après ce balayage, 24 s plus tard, va à `0x428407dd36b72156107fa91995d16acbb5790ea0` pour 0,0033112 ETH : **rien ne la relie à cet envoi**.

## Dépôts de gaz repérés

| De | Vers | Montant | UTC | Lecture |
|---|---|---|---|---|
| `0xeba88149…` | `0x3eaef6d5…` | 0,00230371 ETH | 2024-12-12 02:06:23 | 10 min après un paiement de 113,11 USDT |
| `0xeba88149…` | `0x3eaef6d5…` | 0,0076965 ETH | 2024-12-17 02:14:47 | Paiement du service |
| `0xeba88149…` | `0xcc0f311e…` | 0,00476548 ETH | 2025-09-30 18:32:47 | Adresse mutualisée |
| Clé de brace227 | Clé de kraben006 | 0,002048943671205553 ETH | 2026-10-04 13:54:35 | Hors service |

## Limites

- **BSC et Base :** pas d'historique gratuit. La clé de brace227 a un nonce de 109 sur BSC, ses envois n'y sont pas lus.
- **Solana et Tron :** aucune liste d'étiquettes ChangeNOW exploitable.
- **Adresse sans étiquette :** une entrée via une adresse relais que je n'ai pas lue échapperait à cette recherche.
- **Absence de preuve ≠ preuve d'absence.**

<!-- adresses -->
## Adresses citées en forme courte

| Adresse complète | Étiquette publique lue |
|---|---|
| `0x3eaef6d5e91ecf7b7623eb19978e145ebd417013` | Voir `data/changenow_candidates.csv` ou aucune |
| `0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b` | ChangeNOW Dep: 0x3f3...07B |
| `0x7e67df45e0a0bab092cbb2ff045f8aa8dfab6e23` | Aucune, relais |
| `0xcc0f311eb2c688f30bc9aadb42781e46899723f7` | Voir `data/changenow_candidates.csv` ou aucune |
| `0xeba88149813bec1cccccfdb0dacefaaa5de94cb1` | ChangeNOW: Hot Wallet 4, ChangeNOW 16 |
<!-- fin adresses -->
