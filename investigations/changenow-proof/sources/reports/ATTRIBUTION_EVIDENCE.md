# Preuves d'attribution

Lu le 2 novembre 2026. Une étiquette dit ce qu'une source a écrit, pas ce qu'est l'adresse. Aucune de ces adresses n'est confirmée par ChangeNOW.

## Résultat

| Adresse | Étiquette | Sources, avant dédoublonnage | Test sur la chaîne | Attribution |
|---|---|---|---|---|
| `0xdd3d72c53ff982ff59853da71158bf1538b3ceee` | ChangeNOW: Hot Wallet 3 | Blockscout ; copie Arkham ; copie AMLBot. **Pas de tag public Etherscan** | Reçoit 426 jetons de ChangeNOW 17, 343 181,85 USDT de Hot Wallet 4, même grappe d'adresses amont que Hot Wallet 4 | Corroborée, sans confirmation officielle |
| `0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b` | ChangeNOW Dep: 0x3f3...07B | Etherscan, repris à l'identique par Blockscout : **une seule source** | Reçoit 11,65 ETH de Hot Wallet 4 23 h après sa première transaction, échanges avec ChangeNOW 10, 21 et (0x4778), balayages à empreinte | Corroborée si hildobby ne dérive pas d'Etherscan. Le mot « Dep » trompe |
| `0x7e67df45e0a0bab092cbb2ff045f8aa8dfab6e23` | **Aucune** | Aucune | Empreinte de balayage identique | Déduite, jamais écrite par une source |

## A. Métadonnées exactes

Service : `GET https://metadata.services.blockscout.com/api/v1/metadata?addresses=<a>&chainId=1`.

### `0xdd3d72C53Ff982ff59853da71158bf1538b3Ceee`, chaîne 1

- **Emplacement :** `addresses["0xdd3d72C53Ff982ff59853da71158bf1538b3Ceee"].tags`
- **`tags[0]` :** `slug: changenow-hot-wallet-3`, `name: ChangeNOW: Hot Wallet 3`, `tagType: name`, `ordinal: 10`, `meta: {"tooltipUrl":"https://changenow.io/"}`
- **`tags[1]` :** `slug: changenow`, `name: ChangeNOW`, `tagType: protocol`, `meta: {"appActionButtonText":"ChangeNOW","appID":"changenow"}`
- **Fichier :** `evidence/api/blockscout_metadata_hot3_0xdd3d72c5.json`, collecté `2026-11-02T13:17:37Z`, SHA-256 `551433fb002c08e332069e2267dc6e2b89901d59591b367e329014c58e4ac601`
- **Autres routes :** `/api/v2/addresses/<a>` renvoie `metadata: null`, `public_tags: []` (`blockscout_address_hot3_0xdd3d72c5.json`, SHA-256 `d7a25ecfa1a4d94b8ebdd167430855a28077c6a20d3b1dd17394db8ba7f86da6`). Les listes `/transactions` portent le tag dans `items[].from|to.metadata.tags`, ce qu'avait relevé flow-trace.

### `0x3f3Ee0a9cAC2d01DB44001eca3E8382fbe40207B`, chaîne 1

- **Emplacement :** `addresses["0x3f3Ee0a9cAC2d01DB44001eca3E8382fbe40207B"].tags`
- **`tags[0]` :** `slug: changenow-dep-0x3f307b`, `name: ChangeNOW Dep: 0x3f3...07B`, `tagType: name`, `ordinal: 10`, `meta: {"tooltipUrl":"https://changenow.io/"}`
- **`tags[1]` :** `slug: deposit-address`, `name: DEPOSIT ADDRESS`, `tagType: generic`
- **`tags[2]` :** `slug: changenow-dep`, `name: ChangeNOW Dep`, `tagType: protocol`
- **Fichier :** `evidence/api/blockscout_metadata_dep_0x3f3ee0a9.json`, collecté `2026-11-02T13:17:42Z`, SHA-256 `a60f0e030466de9a0f4a62adf7223f5c8df94af9e4286094181792c74fa01e9c`

### `0x7e67df45e0a0bab092cbb2ff045f8aa8dfab6e23`, chaîne 1

- Réponse `{"addresses":{}}`, aucun tag. `evidence/api/blockscout_metadata_relay_0x7e67df45.json`, collecté `2026-11-02T13:17:46Z`, SHA-256 `1f8b89fdbfe5c49aa3691a1803b311ae86a3a70b159f2c04529f743019b14216`.

## B. Attribution publique, ou simple signalement ?

**Ni l'un ni l'autre n'est prouvé pour Hot Wallet 3, et ce n'est pas une déclaration de ChangeNOW.**

- `tooltipUrl: https://changenow.io/` est un lien vers le site du service. Ce n'est pas une attestation.
- Le service metadata n'indique pas qui a écrit ce tag. Un autre tag, « ChangeNOW 16 » sur `0xeba88149…`, porte lui une attribution explicite à l'Open Labels Initiative (`tooltipAttribution`). Hot Wallet 3 n'en porte aucune.
- **Aucune source officielle de ChangeNOW publiant ces adresses n'a été trouvée.** Recherche web sur les deux adresses : aucun résultat pertinent.

## C. Sources, et ce qui est vraiment indépendant

| Source | `0xdd3d72c5…` | `0x3f3ee0a9…` | Lecture | Indépendance |
|---|---|---|---|---|
| Etherscan, page d'adresse | **Pas de tag.** Titre : `Address: 0xdd3d72c5...538b3ceee` | **Public Name Tag** `ChangeNOW Dep: 0x3f3...07B`, lien changenow.io | Direct, 2026-11-02 13:17 UTC | Source primaire d'étiquette |
| Blockscout metadata | Oui | Oui, même texte qu'Etherscan | Direct | **Copie probable d'Etherscan pour `0x3f3ee0a9…`** : même nom, même lien. Ne compte pas double |
| Arkham | `changenow`, `ChangeNOW`, `cex`, `Hot Wallet` | Non vu | **Copie** : `Xaxrich/okx-ai-quant-lab@fc8b09aa7b`, CSV ligne 604, `source_channel: ARKHAM_CHANNEL`, transfert du 2026-05-05 | Autre fournisseur, non relu à la source |
| AMLBot (d'après le nom du dépôt) | `owner.name: ChangeNOW`, `type: exchange_licensed`, `global_id: 2360` | Non vu | **Copie** : `opun/amlbot-agent@15fc31e210`, `docs/examples/example-6.json` ligne 3771, transaction de fév. 2025 | Autre fournisseur, non relu à la source |
| `dawsbot/eth-labels` | Absente | Absente | Local, 82 lignes ChangeNOW | Résultat négatif |
| `brianleect/etherscan-labels` (2023) | Absente | Absente | Local | Résultat négatif, liste antérieure à ces adresses |
| `QuantumDev-CERN/.../swap_services.py` | Absente | Citée, source « Etherscan public label » | Dépôt tiers, 2026-09-27 | **Copie d'Etherscan, ne compte pas** |
| Compilation hildobby, via OLI et Blockscout | Absente | Absente | Note « tagged based on hildobby compilation » sur Hot Wallet 4, ChangeNOW 10, 17 et 21 (`evidence/api/bs_labels_direct.json`) | **À compter une fois.** Sert de référence aux tests de la section D. Indépendance vis-à-vis d'Etherscan non vérifiée |
| OKLink | Rien d'exploitable | Rien d'exploitable | Page générique | Aucune information |
| Arkham direct | Non lu | Non lu | `intel.arkm.com` : redirection 302 vers connexion, non contournée | Non lu |
| Blockchair | Non lu | Non lu | HTTP 401, non contourné | Non lu |

**Un point à garder en tête :** Hot Wallet 3 existe sur Blockscout mais pas sur la page Etherscan lue, alors que Hot Wallet 4 existe sur les deux. La raison est inconnue : tag retiré, source propre à Blockscout, ou restitution différente de la page. Le format de ce tag est le même que celui des tags repris d'Etherscan : il n'est donc pas sûr qu'il soit une source distincte.

## D. Test sur la chaîne : les mouvements

Ces tests ne dépendent pas du tag de l'adresse testée. **Ils dépendent des tags des autres adresses,** dont une bonne partie vient de la compilation hildobby : ce ne sont pas des tests indépendants de toute étiquette. Tableau complet : `data/attribution_links.csv`.

### `0xdd3d72c5…`

| Fait | Détail | Pourquoi c'est discriminant |
|---|---|---|
| **Reprise d'inventaire** | ChangeNOW 17 (`0xd72cd83afba0dcfeff95d463adcb2b8def6aa623`) lui envoie **432 lignes sur 426 jetons** du 8 au 16 oct. 2024, dont 3,2 ETH, 6 720,87 USDT et 2 347,43 USDC, cinq semaines après sa première entrée | Un client paie un actif. Une migration d'inventaire déplace des centaines de jetons |
| **Rééquilibrage direct** | Hot Wallet 4 lui envoie **343 181,853425 USDT** le 2026-07-06 06:00:47, `0x09c423f9d25a4b81bcc9a2c44d069bf82422f3b2818cd1b4422238c7bff336b5` | Montant de trésorerie entre deux portefeuilles |
| **Compte de plateforme** | Elle envoie à « ChangeNOW: HTX Deposit » (`0x6ba7fe01eec4c6a4308c8e2b35970e0488ce9a86`) **5 581 943,86 USDT et 1 709 560,30 USDC**, 486 lignes sur 17 jetons, de mars à mai 2026 | Liquidité envoyée à la plateforme. Sur 1 000 lignes seulement |
| **Soldes résiduels** | ChangeNOW 2 (`0x48c04ed5691981c42154c6167398f95e8f38a7ff`, déjà dans la liste Etherscan de 2023) lui envoie 34 jetons, surtout des poussières, pour l'essentiel le 3 oct. 2025 | Balayage de restes, pas un paiement |
| **Autre balayage** | `0x077d360f11d220e4d5d831430c81c26c9be7c4a4` lui envoie 5 jetons en 6 min 48 s le 10 mai 2026 | Idem |
| **Grappe d'adresses amont** | Voir ci-dessous | Compatible avec un même opérateur, indépendant de tout tag sur `0xdd3d72c5…` |

**Lignée de financement,** chaque transaction relue sur nœud :

```
0x077d360f… (étiqueté changenow par dawsbot)
   │ 0,24511322 ETH, 2022-05-17, 0x672963b7a84a4c6d1165c5017efff6307671ddb3db8de842b5bf7cd158e909c2
   ▼
0xa2768df0b1fb437d5d238d5d0e9b7ca584e84628 (sans étiquette)
   ├─ 0,001 ETH, 2024-08-29, 0x4ec43c5306b33ddb34ac942af565400e6a3579592692b2cee37eab46b2db2c6e
   │    → 0xeba88149… (Hot Wallet 4) : sa première entrée native
   └─ 0,003 ETH, 2022-10-20, 0x9c19808952d57cb97806793aa05ac8f8cb9e75f0c48511498a6550772e42c6c8
        → 0xb2c257557fd1c7a0738d7e9e2c953441f333b8fd (sans étiquette)
           └─ 0,0005 ETH, 2024-09-04, 0xa26effdead86d7181aa98f4d1f400203be70f6c022899a7c4474754e26cc0594
                → 0xdd3d72c5… : sa première entrée native
```

Hot Wallet 3 et Hot Wallet 4 reçoivent leur première entrée native à 6 jours d'écart, depuis `0xa2768df0…`, directement ou en un saut. Leurs financeurs immédiats diffèrent.

**Ce qui renforce :** `0xa2768df0…` fait des allers-retours de quelques minutes avec trois adresses étiquetées, chaque fois une partie du montant revient :

| Adresse | Envoi | Retour | Écart |
|---|---|---|---|
| ChangeNOW 17 | 0,005 ETH, 2024-07-31 13:58:59, `0xc76899d2d37ea401e840c931b7738c0b5177d6c551bef8ca9d61ff2ef9ce6c07` | 0,003 ETH, `0x37d3434e65505495a224b3ba721901043d93113dae701153e6e2d4ef7c8db500` | 11 min 24 s |
| Hot Wallet 4 | 0,001 ETH, 2024-08-29 10:07:35, `0x4ec43c5306b33ddb34ac942af565400e6a3579592692b2cee37eab46b2db2c6e` | 0,0005 ETH, `0x7326c64b3948894ebc8bfa851f0db41d711b360759f059ce8f44c2e0a9fae840` | 6 min 48 s |
| ChangeNOW: Deposit Funder 9 | 0,002 ETH, 2024-09-04 11:59:59, `0x5bcc3c5c8bb92df71f2ce7f92c95409d3483998a1935fec060a3eee022f749f2` | 0,001 ETH, `0x4f7e1da72218de821924fe7fbd0f960e34ff5dab1eef0c5bf82ea1f5c4949381` | 3 min 12 s |

`0xb2c25755…` reçoit aussi 4 fois de `0x077d360f…` et 1 fois de Hot Wallet 4 (`0x9596e42c5270f26adffeaa19b28fc55bacf6becce4cd291b194bbb94705f837f`).

**Ce qui limite :** `0xa2768df0…` a 22 expéditeurs et 173 destinataires. `0x077d360f…` n'y pèse que 5 entrées sur 31 et 0,32689326 ETH sur 2,152682 ETH. Un paiement depuis un portefeuille de service ne relie pas forcément ses clients.

**Lecture retenue :** grappe d'opérateur probable, compatible aussi avec un client. `0x077d360f…` est étiqueté par dawsbot, par un relevé Blockscout dans `scottonchain/layerzero_xgboost` (« ChangeNOW: hot wallet », 824 adresses financées) et par deux autres listes tierces, toutes de seconde main. `PeLegend` la note « (No Tag) ».

### `0x3f3ee0a9…`

| Fait | Détail |
|---|---|
| Virement de Hot Wallet 4, 23 h après sa première transaction | **11,65060825 ETH** le 2026-08-11 12:32:11, `0x3dff08df2aaf3e41cb1d5f998dbe411aa16ec38e55333917ca7bdd0eb78db606` |
| Échanges avec ChangeNOW 21 (`0x59855c07cdd4924609df4f5f175da3188699932f`) | Reçoit 809,229099 ETH (131 lignes), envoie 563,152178 ETH (44 lignes), 6 au 10 sept. 2026 |
| Envois à ChangeNOW 10 (`0xa12e1462d0ced572f396f58b6e2d03894cd7c8a4`) | 136,05123 ETH, 199 lignes, du 22 sept. au 1er nov. 2026 |
| Échanges avec ChangeNow (0x4778) (`0x4778480c6c46521c41f7e4f2318f884b157cb1c9`) | Reçoit 653,67608505 ETH (238 lignes), envoie 242,152206 ETH (76 lignes), 30 oct. au 2 nov. 2026 |
| Reçoit les balayages à empreinte | 30 témoins sur 30 dans les dernières lignes, 54 sur 60 autour du 4 octobre (voir F) |

### Passation du 10 août 2026

| Portefeuille | Observation |
|---|---|
| `0xdd3d72c5…` | Envois par heure : 140 à 12 h, 558 à 13 h, **4 à 14 h**. Ensuite 10 envois seulement après le 12 août |
| `0xeba88149…` | Au moins 428 envois le 10 août (les 1 000 lignes lues commencent à 07:39), 2 le 11 août, 0 ensuite |
| `0x3f3ee0a9…` | **Première transaction le 2026-08-10 13:35:23**, déjà 599 entrées et 379 sorties dans ses 4 premières heures |
| Adresses à usage unique étiquetées `ChangeNOW Dep` | 13 sur 13 balayent vers `0xeba88149…`, la dernière le 10 août |

C'est une coïncidence observée, compatible avec une rotation de portefeuilles par un même opérateur. La cause n'est pas connue. Première transaction : `0x721415a412cd0f7349d1512ec145923a3dcb05ca3331956ffe721f8ed9bb2e75`, venue de `0x262386755624eefd0c2d46ccf4a8ad35d480f1ee`, une adresse à 1 transaction.

## E. Ce qu'est vraiment `0x3f3ee0a9…`

**Le tag `DEPOSIT ADDRESS` est trompeur. Ce n'est pas l'adresse de dépôt d'un ordre.**

| Fenêtre | Lignes | Entrées | Sorties | Expéditeurs | Destinataires |
|---|---|---|---|---|---|
| 10 août 13:35 à 17:37 | 1 000 | 599 | 379 | 575 | 292 |
| 4 oct. 18:56 au 5 oct. 04:57 | 1 367 | 826 | 530 | 809 | 420 |
| 2 nov. 08:15 à 13:34 | 1 000 | 578 | 422 | 560 | 317 |

Elle reçoit des balayages et envoie vers des centaines d'adresses, ce qui ressemble à des paiements. Elle a 328 423 transactions sur Etherscan. Sur Blockscout, 321 022 à ma lecture et 321 237 à celle de l'enquête, un compteur qui n'est donc pas fiable. Sur les 16 adresses du tag `changenow-dep`, 13 ont exactement 2 transactions : ce sont elles qui ressemblent à de vrais dépôts.

**L'adresse de dépôt candidate est `0x7e67df45…`.**

## F. L'empreinte de balayage

**Définition, fixée après lecture de `0x3f3ee0a9…`, écrite dans `tools/p13_siblings.py`, sans fichier de gel :** 2 transactions, 1 entrée, 1 sortie vers le portefeuille du service, prix du gaz 1 gwei, limite de gaz 22 000, entrée moins sortie entre 6e13 et 6,01e13 wei, délai de 400 à 600 s.

**`0x7e67df45…` :** limite 22 000, 1 gwei, écart exact de 60 000 000 000 000 wei, délai de **492 s**. Le reste, 39 000 000 000 000 wei, est bien le solde lu.

| Groupe | Lu | Même forme | Empreinte complète |
|---|---|---|---|
| Témoins vers `0x3f3ee0a9…`, 4 oct. : **échantillon de définition, pas une validation** | 60 tirés sur 805 | 54 | 54 sur 54 de cette forme. Délai 492 s : 40 fois, 504 s : 11 fois |
| Témoins vers `0x3f3ee0a9…`, dernières lignes : **même portefeuille, autre date** | 30 | 30 | **30** |
| Adresses à 2 transactions portant le tag `changenow-dep`, balayées vers Hot Wallet 4 | 13 | 13 | **12**, la 13e à 3 gwei et écart triple |
| FixedFloat Dep, 3 adresses, le contrôle le plus comparable | 3 | 3 | **0** : limite 21 000, délais 96, 288 et 1 212 s |
| Expéditeurs vers FixedFloat: Hot Wallet 2 | 20 | 7 | **0** |
| Expéditeurs vers SwftSwap | 20 | 1 | **0** |
| Expéditeurs vers KuCoin 10 | 20 | 1 | **0** |
| Expéditeurs vers SimpleSwap 7 | 4 | 0 | **0** |
| Expéditeurs vers Binance 20 | 1 | 0 | **0** |

**Lecture :** `0x7e67df45…` se comporte comme les adresses portant ce tag. Hors de ce groupe, **0 sur 12 adresses de même forme**, soit une borne haute unilatérale exacte de 22 % à 95 %. Les 65 témoins tirés au total ne comptent pas : 53 n'ont pas la bonne forme.

**Ce que ce test ne prouve pas :**
- **Il est circulaire sur l'attribution.** Les 13 adresses viennent du tag Blockscout `changenow-dep`, de la même famille que le tag de `0x3f3ee0a9…`. Le test montre un logiciel commun aux adresses portant ce tag, pas que ce tag est juste.
- **Il n'est hors échantillon que partiellement.** Les 13 adresses n'ont pas servi à définir l'empreinte. Mais elles balayent vers Hot Wallet 4, pas vers `0x3f3ee0a9…`, ce que je n'ai vu qu'après un premier test sans résultat (`tools/p13_siblings.py`, remplacé par `tools/p14_final.py`).
- **Les contrôles sont peu nombreux.** Un partenaire utilisant le même logiciel présenterait la même empreinte.
- **Elle ne donne ni l'ordre, ni le client, ni la sortie.**

## G. Hypothèses alternatives

| Hypothèse | État | Raison |
|---|---|---|
| Exchange différent | **Peu soutenue** | Liens sur la chaîne et grappe d'adresses amont. Les 0 contact sur 10 contrôles ne pèsent pas : leurs fenêtres couvrent parfois quelques heures, et tombent souvent après l'arrêt d'août de `0xdd3d72c5…` |
| Partenaire en marque blanche | **Reste plausible** | Des portefeuilles et applications intègrent ChangeNOW. La chaîne ne distingue pas le canal |
| Hot wallet mutualisé | **Vrai, et important** | Ce sont des portefeuilles de service : un contact ne relie pas deux clients |
| Contrat | **Écartée** | `is_contract: false` sur les trois adresses |
| Adresse réutilisée | **Rare** | 3 témoins sur 60 ont plusieurs entrées. `0x7e67df45…` n'a servi qu'une fois |
| Remboursement | **Peu soutenue pour les 834,85 USDC** | La clé n'a jamais envoyé cet ordre de montant. Reste possible si une autre adresse a indiqué la clé en `refundAddress`. Pour les 0,00247 ETH : aucun retour d'ETH sur la clé ensuite |
| Facture d'un tiers | **Reste possible** | Celui qui paie l'adresse de dépôt n'est pas forcément celui qui a créé l'ordre |
| Mauvaise attribution | **Peu probable, non exclue** | Aucune confirmation officielle |

**Niveau d'attribution retenu : niveau 2 pour les transferts** touchant `0xdd3d72c5…` et `0xeba88149…`. **Niveau 2 conditionnel pour `0x3f3ee0a9…`,** tant que l'indépendance de hildobby et d'Etherscan n'est pas vérifiée. **`0x7e67df45…` n'a pas d'étiquette : niveau 0.** Un label isolé n'aurait pas suffi : c'est l'ensemble des preuves ci-dessus qui fonde ces niveaux. Ils ne prouvent ni le bénéficiaire, ni l'actif de sortie.

<!-- adresses -->
## Adresses citées en forme courte

| Adresse complète | Étiquette publique lue |
|---|---|
| `0x077d360f11d220e4d5d831430c81c26c9be7c4a4` | changenow (dawsbot), ChangeNOW: hot wallet |
| `0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b` | ChangeNOW Dep: 0x3f3...07B |
| `0x7e67df45e0a0bab092cbb2ff045f8aa8dfab6e23` | Aucune, relais |
| `0xa2768df0b1fb437d5d238d5d0e9b7ca584e84628` | Voir `data/changenow_candidates.csv` ou aucune |
| `0xb2c257557fd1c7a0738d7e9e2c953441f333b8fd` | Voir `data/changenow_candidates.csv` ou aucune |
| `0xdd3d72c53ff982ff59853da71158bf1538b3ceee` | ChangeNOW: Hot Wallet 3 |
| `0xeba88149813bec1cccccfdb0dacefaaa5de94cb1` | ChangeNOW: Hot Wallet 4, ChangeNOW 16 |
<!-- fin adresses -->
