# ChangeNOW et les 11 comptes du Ballon d'Or 2026 : ce qui est prouvé

Lecture du 2 novembre 2026. Aucune demande envoyée à ChangeNOW ni à un tiers, aucune transaction émise, aucune clé privée, aucun logiciel installé. Rapport principal de l'enquête non modifié. Une adresse n'est pas une personne : aucune identité n'est recherchée.

## En bref

- **Un seul compte a un contact direct et corroboré avec ChangeNOW : kraben006.** Sa clé reçoit 834,848793 USDC en deux paiements le 23 février 2026, puis envoie 0,00247406 ETH le 4 octobre 2026 vers une adresse à usage unique sans étiquette, qui se comporte comme les adresses portant le tag `ChangeNOW Dep`.
- **Aucun chemin documenté ne relie cet argent aux paris.** Les 834,85 USDC quittent la clé 12 min 48 s après le premier paiement et 276 s après le second, vers une adresse de dépôt de plateforme (HTX par comportement), 220 jours avant le premier dépôt Polymarket du compte. Un retour par ce compte, par un service ou par une chaîne non lue n'est ni observé ni exclu.
- **Niveau de preuve atteint : 2,** pour les deux paiements reçus et pour le balayage vers le service. Le passage de la clé au relais est prouvé, mais son statut d'adresse de dépôt reste une déduction, donc niveau 0 sur ce saut. **Aucun ordre individuel n'est retrouvé** : ni niveau 3 ni niveau 4.
- **Monero : aucune preuve.** Zéro cas confirmé. Trois chemins restent « possibles » au sens strict, sans aucun élément propre à XMR.
- **L'attribution est plus solide qu'on ne le pensait, avec deux réserves.** `0xdd3d72c5…` n'a pas de tag public sur Etherscan, mais elle a reçu des centaines de jetons d'une autre adresse étiquetée ChangeNOW. Pour `0x3f3ee0a9…`, le niveau 2 suppose que la compilation hildobby ne dérive pas d'Etherscan, ce que je n'ai pas vérifié. `0x3f3ee0a9…` n'est pas l'adresse de dépôt d'un ordre : c'est un portefeuille de service, qui reçoit et envoie vers des centaines d'adresses.

## Réponses aux huit questions

### 1. Quels comptes ont une interaction réellement corroborée ?

**kraben006 seulement**, sur 11. Niveau 2.

| Compte | Clé | Contact direct | Contact indirect | Niveau pour le compte |
|---|---|---|---|---|
| kraben006 | `0x101b5f4dc0886c32e2b75972101aeaf9f338fb65` | Oui : 2 paiements reçus | 1 envoi via un relais à usage unique | **2** |
| brace227 | `0xc852b0938f5ad79b640d105ed11c14499454af26` | Non | Un intermédiaire, 21 mois avant les paris | 0 pour le compte. Le saut service vers intermédiaire est au niveau 2 |
| walletwallet8424 | `0x82775eb82fe33acffdf1b91a28c0fc19b4b6a3a1` | Non | Via une adresse mutualisée de 672 contreparties | 0 pour le compte. Le saut vers cette adresse est au niveau 2 |
| ouldlm3alem | `0x1b500b6c40a2ff0930e540e8f53c559a32e75f2c` | Non | Faux positif : Binance paie ChangeNOW 22 | 0 |
| wen | `0x6697f72fa32de93d8450830eb07f5b6724104405` | Non | Faux positif : même ligne | 0 |
| zoomman17 | `0xd90d00130519086d412d2b9ffac2bb01f71ef444` | Non | Aucun lu | 0 |
| 0x86544e4dfde | `0x69837228fa0bcbac53713d981161c929523c0ded` | Non | Aucun lu | 0 |
| thin | `0x1bf0b469f7f3612657e99bf785e470eee2a76028` | Non, nonce 0 sur 6 chaînes | Aucun lu | 0 |
| vidente | `0x3cb3f4f6b1a81bdf523e36b7f5fa5081113f0f5e` | Non, nonce 0 sur 6 chaînes | Aucun lu | 0 |
| cookedrice | `0x6ec290051ea167cf564a4282c153351ab3fd876f` | Non, nonce 0 sur 6 chaînes | Aucun lu | 0 |
| 0xdd97e6 | `0xcf7b90deaf46d27b2b8f2f54a099d82879dd19ad` | Non, nonce 0 sur 6 chaînes | Aucun lu | 0 |

Niveau 0 veut dire : aucune preuve dans ce qui est lisible. Cela ne prouve pas l'absence (voir « Où les preuves s'arrêtent »).

### 2. Quels montants et quelles transactions sont démontrés ?

Chaque ligne est relue sur un nœud public (transaction, reçu, bloc), avec empreinte dans `data/verified_transfers.csv`.

**kraben006, chaîne 1**

| UTC | Montant | De | Vers | Transaction |
|---|---|---|---|---|
| 2026-02-23 15:56:23 | 654,466304 USDC | `0xdd3d72c53ff982ff59853da71158bf1538b3ceee` | clé | `0x5e8b57210b722dbf0f7395cbe20c57a3e578d2897bb4ff8d4c5e853387789219` |
| 2026-02-23 16:04:35 | 180,382489 USDC | `0xdd3d72c53ff982ff59853da71158bf1538b3ceee` | clé | `0x472c85a3cd9df3bbdf9b5fac9ee812326646b1b40c832278fb42107554c0cd80` |
| 2026-10-04 23:48:47 | 0,00247406 ETH | clé | `0x7e67df45e0a0bab092cbb2ff045f8aa8dfab6e23` | `0x1a39308b89cc7d9de6e38fbf0c62aa5d0bdd777863079cd151fe12a6b135dd71` |
| 2026-10-04 23:56:59 | 0,00241406 ETH | `0x7e67df45e0a0bab092cbb2ff045f8aa8dfab6e23` | `0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b` | `0x22710b5e691160746fd4e054346daf18c91e98532999c1bd3bd9067340fe9c26` |

**Total démontré pour kraben006 : 834,848793 USDC reçus du service (niveau 2). 0,00247406 ETH envoyés au relais (niveau 0), dont 0,00241406 ETH balayés vers le service (niveau 2).**

**brace227 (indirect) :** `0xdd3d72c5…` paie 510,494311 USDT en 7 fois à `0x3eaef6d5e91ecf7b7623eb19978e145ebd417013`, et `0xeba88149…` lui envoie 0,01000021 ETH en 2 fois, de déc. 2024 à avril 2025. Cette adresse envoie 291,317423 USDT à la clé le 4 janvier 2025, 84 s après avoir reçu 290,286195 USDT du service. Détail dans `reports/PAYOUT_MATCHES.md`.

### 3. Quels comptes sont seulement reliés indirectement ?

- **brace227 :** par `0x3eaef6d5…`, qui verse à 9 destinataires différents, chacun une fois. La clé en est un parmi d'autres. Le solde USDT de la clé tombe à 0 le 28 avril 2025, plus de 17 mois avant son premier dépôt Polymarket : aucun chemin documenté vers les paris.
- **walletwallet8424 :** son financeur `0xcc0f311eb2c688f30bc9aadb42781e46899723f7`, 672 contreparties, reçoit 0,00476548 ETH de `0xeba88149…` le 30 sept. 2025. Sans portée : une adresse mutualisée de cette taille reçoit de tout le monde.
- **ouldlm3alem et wen : pas reliés.** Une règle naïve les relierait, parce que `0xee7ae85f…` (Binance: Hot Wallet 34), leur source à tous deux, envoie 10 000 USDC à `0x4958f6c3…` (« ChangeNOW 22 ») le 6 août 2025 sur Polygon. C'est un flux entre deux services.

### 4. Peut-on retrouver un ordre ChangeNOW individuel ?

**Non, pas avec des données publiques.**

- Aucun identifiant d'ordre, `payinHash`, `payoutHash`, `payinAddress` ou `payoutAddress` dans les dossiers locaux (`state/figures.json`), ni en clair sur la chaîne : les 49 transactions relues sur nœud ont une calldata standard, sans mémo ni identifiant ajouté.
- L'API officielle exige une clé partenaire et ne documente l'accès qu'aux transactions de ce partenaire (section « Documentation ChangeNOW »).
- Je n'ai énuméré aucun identifiant et n'ai appelé aucune route de `api.changenow.io`.

### 5. Peut-on identifier sa destination de sortie ?

**Non.** Pour les 0,00247406 ETH du 4 octobre, aucune entrée reçue par les adresses lues ne vient d'une adresse étiquetée ChangeNOW, hors portefeuilles de service entre eux. La trace s'arrête à l'entrée du service.

**Pour l'autre sens,** les 834,85 USDC, on connaît la sortie du service mais ni l'actif ni la chaîne d'entrée. La clé n'avait que 121,08 USDC juste avant : l'entrée vient d'ailleurs.

### 6. Existe-t-il une preuve d'utilisation de XMR ?

**Non.** CONFIRMÉ : 0. POSSIBLE : 3 chemins sur 2 comptes, plus 1 chemin lointain sans portée. NON ÉTABLI : tout le reste. Voir `reports/XMR_VISIBILITY.md`.

### 7. Les mêmes intermédiaires sont-ils utilisés par plusieurs comptes ?

**Aucun intermédiaire privé commun sur le chemin ChangeNOW.** Le seul point commun est le service lui-même : `0xdd3d72c5…` paie la clé de kraben006 en 2026 et l'intermédiaire de brace227 en 2024-2025. Cette adresse compte 1 656 021 transactions, ce n'est pas un lien.

Vérifié aussi : les contreparties de `0x66d582e5…` présentes dans l'étude sont la clé de kraben006 et quatre services (`0xdd3d72c5…`, Revolut 6, Binance 15, Binance: Hot Wallet 34). Celles de `0x3eaef6d5…` sont la clé de brace227 et les deux portefeuilles de service.

### 8. Ce qui pourrait renforcer une coordination, et ce qui l'explique autrement

Rien ici ne démontre une coordination ni une information privilégiée.

| Élément | Ce qu'il peut suggérer | Explication plus simple |
|---|---|---|
| La clé de brace227 envoie 0,00204894 ETH à celle de kraben006, qui envoie 0,00247406 ETH vers un relais à empreinte de dépôt 9 h 54 plus tard | Une chaîne entre deux dossiers | Un petit transfert de gaz. Entre 19,8 % et 82,8 % de l'envoi peut venir de brace227 selon la convention : pas de lien montant à montant |
| Deux comptes touchent le même portefeuille ChangeNOW | Rien de spécifique | 1 656 021 transactions, 266 destinataires en 2,15 h dans la fenêtre lue |
| Réception puis renvoi en moins de 5 minutes | Une exfiltration organisée | 18 destinataires sur 57 font pareil dans la même fenêtre |
| Deux paiements à 8 minutes d'écart | Un fractionnement | 9 destinataires sur 57 |
| kraben006 touche ChangeNOW, pas les comparateurs : 1 sur 11 contre 0 sur 54 | Un trait distinctif | p = 0,17, exploratoire. Seuls 14 comparateurs sur 54 ont un historique |

**Ce qui renforcerait vraiment :** un registre officiel montrant le même client derrière plusieurs ordres, ou une destination de sortie commune documentée.

## Où les preuves s'arrêtent

1. **À l'entrée du service.** Une fois les fonds arrivés sur `0x3f3ee0a9…`, ils se mêlent aux autres : 530 sorties natives en 10 heures autour de l'envoi.
2. **Au compte de plateforme** derrière `0x66d582e5…`, HTX par comportement, pour les 955 + 40 USDC.
3. **À `0x3eaef6d5…`** pour brace227 : propriétaire inconnu.
4. **Chaînes non lues :** historique de BSC et Base, payant ou derrière un contrôle anti-robot non contourné. Solana et Tron : une seule adresse Solana attribuée à ChangeNOW en source tierce, aucune sur Tron.

Liste complète : `data/unresolved_paths.csv` (11 lignes).

## Ce qu'il faudrait pour aller plus loin

Tout cela relève d'une décision de Benjamin. **Rien n'a été envoyé.**

| Élément officiel | Détenteur | Ce que cela lèverait |
|---|---|---|
| Ordre associé à `payinHash` `0x1a39308b89cc7d9de6e38fbf0c62aa5d0bdd777863079cd151fe12a6b135dd71` | ChangeNOW, sur réquisition, ou le client avec son identifiant d'ordre | Actif et adresse de sortie de l'envoi du 4 octobre |
| Ordres associés aux `payoutHash` `0x5e8b57210b722dbf0f7395cbe20c57a3e578d2897bb4ff8d4c5e853387789219` et `0x472c85a3cd9df3bbdf9b5fac9ee812326646b1b40c832278fb42107554c0cd80` | Idem | Actif et chaîne d'entrée, XMR ou non |
| Ordres payés à `0x3eaef6d5…` | Idem | Lien, ou absence de lien, avec brace227 |
| Titulaire de l'adresse de dépôt `0x66d582e5…` | HTX, sur réquisition | Destination finale des 995 USDC |
| Confirmation d'appartenance des adresses | ChangeNOW | Niveau d'attribution officiel |

Une API partenaire ne suffit pas : rien dans la documentation n'indique qu'elle donne accès aux ordres d'un tiers. L'identité d'un titulaire relève d'une autorité, pas de cette enquête.

## Ce que cela change par rapport aux rapports existants

Je n'ai touché à aucun de ces rapports. Points à reprendre si Benjamin le décide :

| Rapport | Écrit | Ce que je trouve |
|---|---|---|
| Amendement A5, investigation | Source unique, non recoupée | Le service est recoupé (Etherscan pour `0x3f3ee0a9…`, copies Arkham et AMLBot pour `0xdd3d72c5…`, liens sur la chaîne). L'ordre reste inconnu |
| Flow-trace, `COMMON_FUNDERS.md` | Le gaz reçu « semble » revendu | Part de l'ETH de brace227 entre 19,8 % et 82,8 % selon la convention, sortie inconnue. La lecture « revendu » reste non démontrée |
| Flow-trace, chemins non résolus | `0x3f3ee0a9…` profil d'adresse de dépôt | C'est `0x7e67df45…` qui a ce profil. `0x3f3ee0a9…` est un portefeuille de service, malgré son tag `DEPOSIT ADDRESS` |
| Flow-trace, kraben006 | Restes de `0xdd3d72c5…` parmi l'origine des financements | Au plus 0,925596 USDC de solde après la sortie du 23 février. Le dépôt du 1er octobre puise 2,610648 USDC dans l'ancien solde : au plus ce reliquat peut y passer, selon la convention |
| Hypothèse H13 | Non tranchée | Contact ChangeNOW au niveau 2 pour kraben006. XMR : non établi. Statut `XMR_VISIBILITY_BOUNDARY` à trancher par Benjamin |

**Nouveau dans ce rapport :** l'aval `0x66d582e5e0670bd99153199f179733c6ee5d19be`, absent des rapports précédents, et l'empreinte de balayage.

## Évaluation des cinq dépôts

Lus par `gh api` le 2 novembre (`evidence/repos/repos_metadata.json`). **Aucun n'est installé.** Fichiers tiers traités comme des données, jamais exécutés.

| Dépôt | État lu | Apport | Décision |
|---|---|---|---|
| `blockscout/swaggers` | Commit `d77e2ba` du jour, licence non standard | **Oui.** Spec du service metadata : tags par lot, tags par chaîne et liste d'adresses par tag. Capacité absente des scripts existants | Spec lue et archivée, appels directs |
| `dawsbot/eth-labels` | Branche `v1`, 2026-09-25, MIT, 304 étoiles | Déjà copié par flow-trace : 82 lignes ChangeNOW, mais ni `0xdd3d72c5…` ni `0x3f3ee0a9…` | Données réutilisées |
| `blockchain-etl/ethereum-etl` | 2026-01-25, MIT, 154 issues | **Non.** Export massif : le besoin est ciblé, et la RAM du Mac est limitée | Écarté |
| `blockscout/mcp-server` | v0.19.0 du 2026-09-08, licence non standard | **Non.** Enveloppe les mêmes routes par une clé PRO. Son SPEC a confirmé la route metadata | Écarté |
| `ChangeNow-io/ChangeNOW-api-python` | Dernier commit 2018-08-20, API v1 en dur sur `changenow.io/api/v1/` | Référence historique. `create_transaction` créerait un vrai ordre | Lu, jamais exécuté |

## Documentation ChangeNOW

Sources : `evidence/api/changenow_api_page.html` et `evidence/api/changenow_postman_collection_SVfTPnM8.json` (collection officielle, lue le 2 nov.).

| Information | Accès | Preuve dans la doc |
|---|---|---|
| Liste des devises, paires, adresse valide | Public ou clé simple | `GET /v2/exchange/currencies` |
| Statut d'un ordre : `payinAddress`, `payoutAddress`, `payinHash`, `payoutHash`, actifs, montants | **Clé partenaire + identifiant d'ordre** | `GET /v2/exchange/by-id?id=`, en-tête `x-changenow-api-key`, « (Required) Partner's api key », réponses 401 et 403 documentées |
| Ancienne route de statut | Clé dans l'URL | `GET /v1/transactions/:id/:api_key`. « The 'Get the transaction' method can be called only with your private API key » une fois une clé privée émise |
| Liste d'ordres | **Clé partenaire, ordres de ce partenaire** | `GET /v2/exchanges` : « returns a list of partner transactions » |
| Champs `userId` et `payload` | Partenaire, sur demande | Identifiant permanent côté partenaire, s'il existe |
| Page de suivi publique d'un ordre | **Non vérifié** | Absente de la documentation lue. Non testée, faute d'identifiant vérifiable |

**À noter :** la documentation décrit une route `private-transfer`, transfert d'un même actif par une adresse générée. L'envoi du 4 octobre pourrait donc être autre chose qu'un échange. Rien ne permet de trancher.

## Limites

- **Attribution :** aucune confirmation de ChangeNOW. Elle repose sur des étiquettes et des comportements. Un partenaire en marque blanche resterait compatible.
- **Compilation hildobby :** plusieurs adresses de référence (Hot Wallet 4, ChangeNOW 10, 17 et 21) portent la note « tagged based on hildobby compilation ». Son origine et son indépendance vis-à-vis d'Etherscan ne sont pas vérifiées. Pour `0x3f3ee0a9…`, le niveau 2 en dépend.
- **Copies Arkham et AMLBot :** lues dans des dépôts tiers, pas à la source. `intel.arkm.com` renvoie vers une connexion, non contournée. Leur indépendance entre elles n'est pas établie.
- **Empreinte de balayage :** définie après lecture de `0x3f3ee0a9…`, sans fichier de gel. Elle montre un logiciel commun aux adresses portant le tag, pas que ce tag est juste. Contrôles comparables : 0 sur 12 adresses de même forme, borne haute à 95 % de 22 %, donc un test faible. Détail : `reports/ATTRIBUTION_EVIDENCE.md`, section F.
- **Fenêtres partielles :** jamais l'historique entier de `0xdd3d72c5…` ni de `0x3f3ee0a9…`. Les liens comptent les 1 000 dernières lignes de chaque adresse étiquetée.
- **Taux de base faible :** 54 comparateurs utilisables sur 78 wallets distincts, dont 14 seulement avec un historique ; premier saut seulement. « Utilisable » veut dire ici : état READ, clé connue, historique de clé complet.
- **Second saut limité aux clés :** les 12 destinataires jamais lus. Les autres sorties des financeurs ne sont pas toutes suivies.
- **Relecture :** une passe d'audit des conclusions par un agent de la même famille de modèle, verdict FAIL sur les niveaux et certaines formulations. Défauts revérifiés sur pièces puis corrigés ici. Ces corrections n'ont pas été réauditées. Pas de relecture humaine.
- **Déviation de méthode :** le premier test des adresses sœurs (`tools/p13_siblings.py`) lisait leurs expéditeurs et n'a rien donné. Je l'ai remplacé par une lecture des adresses elles-mêmes (`tools/p14_final.py`), après avoir vu ce résultat.

## Reproduire

```bash
cd ~/Projects/PolySentinel-ChangeNOW-proof
export PYTHONDONTWRITEBYTECODE=1
python3 tools/p2_universe.py     # étiquettes publiques
python3 tools/p3_study.py        # adresses étudiées
python3 tools/p4_scan.py         # recherche dans tous les caches
python3 tools/p5_rows.py         # historiques en cache, lecture seule
python3 tools/p6_batch_labels.py # étiquettes en lot
python3 tools/p7_targets.py && python3 tools/p8_hops.py
python3 tools/p9_windows.py && python3 tools/p10_tests.py
python3 tools/p11_base_rate.py && python3 tools/p12_verify.py
python3 tools/p13_siblings.py && python3 tools/p14_final.py && python3 tools/p15_lineage.py
python3 tools/p16_base_rate_final.py && python3 tools/p17_figures.py
python3 tools/build.py && python3 tools/expand_refs.py && python3 tools/selfcheck.py
```

Le cache rejoue l'essentiel sans réseau, et les copies du fichier de comparateurs ne sont pas écrasées. Chiffres recalculés : `state/figures.json`. Recherches web : `evidence/docs/web_searches.md`, résumés seulement. Preuves : `evidence/api/MANIFEST.csv` (URL, date UTC, SHA-256), `evidence/onchain/`, `evidence/SHA256SUMS`, et `state/requests.jsonl` pour les réponses Etherscan.

<!-- adresses -->
## Adresses citées en forme courte

| Adresse complète | Étiquette publique lue |
|---|---|
| `0x3eaef6d5e91ecf7b7623eb19978e145ebd417013` | Voir `data/changenow_candidates.csv` ou aucune |
| `0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b` | ChangeNOW Dep: 0x3f3...07B |
| `0x4958f6c329b61404b1cfd0ec8a44600a9486bd0a` | ChangeNOW 22 |
| `0x66d582e5e0670bd99153199f179733c6ee5d19be` | Voir `data/changenow_candidates.csv` ou aucune |
| `0x7e67df45e0a0bab092cbb2ff045f8aa8dfab6e23` | Aucune, relais |
| `0xdd3d72c53ff982ff59853da71158bf1538b3ceee` | ChangeNOW: Hot Wallet 3 |
| `0xeba88149813bec1cccccfdb0dacefaaa5de94cb1` | ChangeNOW: Hot Wallet 4, ChangeNOW 16 |
| `0xee7ae85f2fe2239e27d9c1e23fffe168d63b4055` | Binance: Hot Wallet 34 |
<!-- fin adresses -->
