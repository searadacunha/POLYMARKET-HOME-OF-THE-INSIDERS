# Phase 7 : attribution externe indépendante de MoonPay

30/09/2026, heures UTC.

**Fichiers**
- `attribution_sources.csv` : 18 sources, avec URL, date, indépendance, niveau et contradiction.
- `timeline_0xf691384d.csv` : 107 mouvements réels, hashes complets.

**Scripts** : `scripts/p7_timeline.py` et `scripts/p7_ens_links.py`. Ce dernier vérifie par `eth_call` les enregistrements ENS et la chaîne de propriété de `moonpay.eth`.

**Pièces consultées** : plainte *Real v. Yuga Labs* (Doc. 114), plainte du DOJ 1:25-cv-02116, déclaration FEC Form 13 n° 1889684. Les copies téléchargées sont dans le scratchpad de session.

---

## Résultat en une phrase

**Aucune source indépendante n'attribue explicitement et de façon vérifiée une adresse de la famille à MoonPay.** En revanche, le cercle « tout repose sur Etherscan » est cassé pour **MoonPay 7 (`0x7afc12c8`)**. Une décision de justice, un document du DOJ et des noms ENS auto-déclarés, indépendants d'Etherscan, rattachent cette adresse à MoonPay ou à son PDG. Or MoonPay 7 échange directement avec la trésorerie de la famille et avec l'admin `0xf691384d`.

**Niveau final inchangé : FORT MAIS NON PROUVÉ.** La base est plus solide, parce qu'elle ne dépend plus d'Etherscan seul.

---

## 1. `0xf691384d` : recherche exhaustive

- **Requêtes testées :** adresse complète, adresse sans « 0x », fragment `0xf691384d`, combinaisons avec MoonPay, Bitstamp, Coinbase, OKX, « crypto » et « wallet ».
- **Résultat :** uniquement des pages d'explorateurs sans rapport. Une réponse de moteur de recherche a déduit un lien MoonPay à partir de pages Etherscan ; ce n'est pas retenu.
- **Etherscan :** pas d'étiquette. **ENS :** pas de nom inverse.
- **Aucune source**, dépendante ou non, ne nomme `0xf691384d`.

Chronologie minimale, avec tous les hashes dans `timeline_0xf691384d.csv` :

| Date | Événement | Hash |
|---|---|---|
| 02/09/2021 17:16 | admin → MoonPay 6, 100 000 USDC (mise en service) | `0xe7e132997278bfaffc761d94d62f986fa5083de12ab44cc543c64efcb8679ecd` |
| 02/09/2021 20:22 | admin → MoonPay 8, 100 000 USDC | `0x66588523c0ff1422968c3d1896c3cb4b88d390d7197cc8f6540a80321a9c2524` |
| 03/09/2021 → 19/12/2023 | 12 transferts dans les deux sens avec MoonPay 7 (6 entrants, 6 sortants) | voir CSV |
| 11/03/2023 08:42 | ancien collecteur `0xfa7dddcf` → admin, 133 306,85 USDC | `0x58a65ba876efc792f28a05879f819c736bf9ae1e4464da3ff63c3ea3b2551fcf` |
| 22-23/01/2024 | admin → dépôt OKX `0x2313c810`, 3 × 50 USDT (tests) | `0x2bbffdc1…`, `0x56430281…`, `0x748de23e…` |
| 31/05/2024 12:15 et 16:58 | admin → trésorerie `0x3b6dcfde` : 0,01 ETH puis 30 ETH | `0x2455a0062af29bd7b4a431dc6a3cdf444d5d28ba0859ee96015e8dad3a1779d1` ; `0xced5a4f2a5f40e0fdec3bb10aad92eb09b4d7d62ad73a8b817ea15d2fd00b5d7` |

Personne n'a documenté publiquement cette combinaison de transactions.

---

## 2. Adresses de la famille

Aucune mention publique ni étiquette pour :
- `0x3b6dcfde`, `0xb93e3d70`, `0x26c50e67`, `0x0e9e3919`, `0xa7ceed38` ;
- `0xabe7931e`, `0x7f227df2`, `0x9d34c01d`, `0xfa7dddcf` ;
- `0x4a9a1675`, `0xb7152d59`, `0x974413b8`, `0x9bdbbd6f`.

Sources vérifiées : recherche web, Etherscan, jeu Dune spellbook, jeu brianleect.

**Recherche de réfutation.** Aucune source n'attribue ces adresses à une autre entité ou à un prestataire.

---

## 3. Jeux de données publics

| Source | Contenu | Indépendance |
|---|---|---|
| **Dune spellbook**, `cex_evms_addresses.sql`, PR #4856 de `hildobby` (ajout 22/11/2023, fusion 27/11/2023) | 9 adresses « MoonPay » : MoonPay 1 à 8 et MoonPay Withdrawals 1 | **Faible.** Même nomenclature qu'Etherscan, aucune source citée. `0xb287eac4` s'y appelle « MoonPay 1 » contre « MoonPay 9 » chez Etherscan. Utile surtout comme **instantané daté, antérieur de 6 mois à la famille** : l'étiquetage des anciens wallets ne peut pas avoir été déduit de l'activité de la famille |
| brianleect/etherscan-labels (dernier scraping 10/2023) | aucune étiquette MoonPay | sans objet |
| dawsbot/eth-labels, ImMike | non exploités : ce sont des copies d'étiquettes Etherscan | aucune |
| Arkham, Nansen, Breadcrumbs, OKLink | **non vérifiés** : applications JavaScript ou protection anti-robot, non contournée | sans objet |

---

## 4. Origine des étiquettes Etherscan

- **Méthode publique** (Etherscan Information Center) : les « Public Name Tags » sont choisis par les curateurs d'Etherscan, avec « dans la plupart des cas » un lien vers la source.
- **Aucun lien de source** n'apparaît sur les pages de MoonPay 3, 6, 7, 8 et 9.
- L'API qui donnerait les métadonnées d'étiquette (`getaddresstag`) est réservée aux offres payantes.
- **Wayback Machine :**
  - MoonPay 6 **sans étiquette** au 28/11/2021 ;
  - MoonPay 7 étiqueté au 20/04/2025 ;
  - les captures de MoonPay 9 de 2023-2024 sont vides, probablement des pages anti-robot.
- **Conclusion :** on ne peut pas dire si l'étiquette est une attribution propre à Etherscan, une soumission de MoonPay ou une donnée importée. La méthode n'est pas publiée. Je ne spécule pas.

---

## 5. La source indépendante trouvée : MoonPay 7, `moonpay.eth` et le PDG

### 5.1 Décision de justice de 2023 (indépendante d'Etherscan pour MoonPay 7)

*Real v. Yuga Labs*, C.D. Cal. n° 2:22-cv-08909, First Amended Class Action Complaint, Doc. 114, déposée le 04/08/2023. Défendeurs : notamment **MoonPay USA LLC** et **Ivan Soto-Wright** (PDG de MoonPay).
- **§328 :** les achats de NFT de Soto-Wright passaient par son wallet « IvanHodl.eth », *« funded by the Moonpay.eth wallet as well as by the Ethereum wallet address 0x7AFC12C8DD2e6591581D95586eB2c2A4905a12a9 (the "Funding" Wallet) »*.
- **§329 :** *« The Moonpay.eth wallet was funded by the Funding Wallet »*.
- **§168 :** `0xd75233704795206de38cc58b77a1f660b5c60896`, « publicly labeled as MoonPay (the MoonPay Wallet) ». Cette qualification-là s'appuie sur l'étiquette publique et n'est donc pas indépendante.

**Nature de la preuve** : allégations de plaignants, non jugées. La plainte identifie `0x7afc12c8` par ses flux, pas par une étiquette.

### 5.2 ENS, vérifié on-chain par `eth_call`

- **`moonpay.eth`** :
  - propriétaire du registre et adresse résolue = `0xd7523370…` ;
  - **l'enregistrement inverse de `0xd7523370` est `moonpay.eth`**, ce qui ne peut être fixé que par le détenteur de la clé : c'est une **auto-déclaration**.
- **`ivanhodl.eth`** : même situation pour `0x695626a6…`.
- **Chaîne de propriété du nom `moonpay.eth`** (NFT) :
  - enregistré en 10/2019 par `0x1df65ede`, un tiers inconnu, puis migré par ENS le 07/02/2020 ;
  - passé le 30/08/2021 à `0x9319425d` (« firstofnations.eth »), qui a lui-même des transferts avec MoonPay 7 et moonpay.eth ;
  - puis le 08/09/2021 à `0xd7523370` ;
  - enfin le 10/10/2023 à `0x41485c75` (0 transaction).
- Le nom **n'a pas été attribué par une procédure de vérification de marque**, et MoonPay ne le publie pas : sa page ENS de 2023 n'en parle pas, et le site ne mentionne aucune adresse.

### 5.3 Vérification on-chain des affirmations de la plainte

- **MoonPay 7 → ivanhodl.eth :** 10 ETH (03/08/2021), 20 ETH (05/08/2021), 250 ETH (30/08/2021). Hashes : `0xcd86ab31…`, `0x409e97ab…`, `0x2a8d4d7a…`.
- **moonpay.eth → ivanhodl.eth :** 6 transferts en 2022 (30 ; 11,2 ; 16 ; 150 ; 30 ; 50 ETH).
- **MoonPay 7 ↔ moonpay.eth :** 11 entrants et 6 sortants entre 2021 et 2023, dont 100 ETH le 27/10/2021, et en retour 84 713 USDC (23/05/2023) et 60 945 USDT (21/09/2023).
- **Les affirmations de la plainte sont exactes on-chain.**

### 5.4 Dossier du DOJ de 2025 (indépendant, mais n'attribue pas l'adresse à MoonPay)

*United States v. Approximately 40,353 USDT.ETH*, D.D.C. n° 1:25-cv-02116, déposé le 02/07/2025, §26-27.
- « Victim-1 » a envoyé 250 300 USDT le 26/12/2024 à l'escroc qui se faisait passer pour Steve Witkoff.
- La transaction citée (`0x74ec438c…`) **part on-chain de MoonPay 7**.
- La plainte ne nomme ni MoonPay ni les victimes en clair. La presse (The Block, NOTUS) identifie les prénoms « Ivan » et « Mouna », présents dans les captures d'e-mails, au PDG et à la CFO de MoonPay. C'est une inférence journalistique.
- **FEC :** la déclaration Form 13 du comité d'investiture (943 donateurs) mentionne Coinbase, Ripple et Solana Labs, **mais pas MoonPay**. Cela ne corrobore rien et ne contredit rien : le don aurait été détourné.

### 5.5 Ce que cela établit

**Pour `0x7afc12c8` (MoonPay 7)**, trois sources publiques indépendantes d'Etherscan convergent : la plainte de 2023, les noms ENS auto-déclarés et le dossier du DOJ commenté par la presse. Elles le rattachent à **MoonPay ou à ses dirigeants**. Son profil va dans le même sens : 12 627 transactions, contreparties Circle, Galaxy et Genesis OTC, dépôts Binance à l'échelle de centaines de millions, soit une trésorerie d'entreprise.

**Limites :**
- aucune source ne dit explicitement « 0x7afc12c8 appartient à MoonPay (l'entreprise) » ;
- la plainte contient des allégations ;
- le DOJ anonymise ;
- ENS est déclaratif ;
- une partie des éléments désigne le PDG à titre personnel.

**Lien avec la famille, mesuré :**
- MoonPay 7 ↔ trésorerie : 2 000 000 USDC (29/08/2025), 30,19 XAUt, DAI et WBTC.
- MoonPay 7 ↔ admin `0xf691384d` : 12 transferts dans les deux sens (2021-2023).
- Payeurs de la famille → `moonpay.eth` : 7 petits paiements.
  - `0xa7ceed38` : 5 × 0,004 à 0,02 ETH, 2025 ;
  - `0x0e9e3919` : 0,0043 ETH, 18/01/2025 ;
  - `0xb93e3d70` : 49,05 USDC, 24/10/2025, hash `0x912c2bf6…`.
- Ces 7 paiements sont compatibles avec des achats de test de MoonPay sur son propre wallet. Un achat de test chez un concurrent produirait toutefois la même trace.

---

## 6. Autres sources institutionnelles

- **Bitstamp, Coinbase Prime, Circle, OKX, Ripple, Tether, Anchorage, Polymarket :** aucune publication ne donne d'adresse de wallet de MoonPay. Les partenariats publics (RLUSD, USAT, Polymarket, PYUSD) figuraient déjà dans les phases 5 et 6.
- **Documents juridiques et réglementaires :** hormis les deux plaintes ci-dessus, aucun document public avec adresse n'a été trouvé.
- **GitHub officiel de MoonPay** (4 dépôts), documentation développeur, centre d'aide : aucune adresse d'envoi publiée.

---

## 7. Réponses

**1. Existe-t-il maintenant une attribution indépendante d'au moins une adresse à MoonPay ?**
Oui, mais pas au niveau d'une preuve. `0x7afc12c8` (MoonPay 7) et `0xd7523370` (moonpay.eth) sont rattachés à MoonPay ou à son PDG par des sources indépendantes d'Etherscan. Aucune n'est une attribution explicite et vérifiée. **Niveau : FORT MAIS NON PROUVÉ.**

**2. Laquelle, et sur quelle preuve ?**
- `0x7afc12c8` : plainte *Real v. Yuga Labs* (Doc. 114, §328-329), transferts on-chain vers ivanhodl.eth et moonpay.eth, dossier DOJ 1:25-cv-02116 et presse.
- `0xd7523370` : enregistrement ENS inverse `moonpay.eth` (auto-déclaration) et plainte §168/§329.

**3. Cette attribution relie-t-elle `0xf691384d` à MoonPay ?**
Seulement par inférence d'opérateur :
- 12 transferts dans les deux sens avec MoonPay 7 ;
- relais MoonPay 7 → admin → compte Bitstamp en 3 minutes (2023) ;
- mise en service de MoonPay 6/8 et 3/9 (étiquettes Etherscan et Dune).

**FORT MAIS NON PROUVÉ.**

**4. Et `0x3b6dcfde` ?**
Par deux chemins mesurés : transferts directs avec MoonPay 7 (dont 2 000 000 USDC) et 30 ETH reçus de l'admin. **FORT MAIS NON PROUVÉ.**

**5. Les 16 paiements sont-ils des paiements émis par MoonPay ?**
Émis par l'infrastructure attribuée à MoonPay : **FORT MAIS NON PROUVÉ**. Nature « achat de client MoonPay » : **COMPATIBLE**.

**6. Peut-on identifier les clients ?**
**INCONNU.** Aucune tentative d'identification de personne n'a été faite, conformément au §12.

---

## 8. Niveau final

| Objet | Niveau |
|---|---|
| `0x7afc12c8` (MoonPay 7) → MoonPay ou ses dirigeants | FORT MAIS NON PROUVÉ (sources indépendantes d'Etherscan) |
| `0xd7523370` (moonpay.eth) → MoonPay | FORT MAIS NON PROUVÉ (auto-déclaration ENS non vérifiée) |
| `0xf691384d` → MoonPay | FORT MAIS NON PROUVÉ |
| Famille (trésorerie, payeurs, collecteurs, distributeur de gas) → MoonPay | FORT MAIS NON PROUVÉ |
| 16 paiements émis par MoonPay | FORT MAIS NON PROUVÉ |
| Clients | INCONNU |
| Réfutation | aucune trouvée |

**Pourquoi ce n'est toujours pas prouvé :**
- aucune source ne relie **explicitement** une adresse de la famille à MoonPay ;
- la source indépendante la plus proche porte sur MoonPay 7, et elle est allégative (plainte civile), anonymisée (DOJ) ou déclarative (ENS) ;
- le passage de MoonPay 7 à la famille repose sur des transferts on-chain, c'est-à-dire sur une continuité d'opérateur, pas sur une attribution.

**Ce qui franchirait le seuil :**
- une confirmation par MoonPay, par exemple par réquisition ou par une liste officielle d'adresses, que `0x7afc12c8`, `0xf691384d` ou `0x3b6dcfde` sont à elle ;
- ou une constatation judiciaire, et non une allégation, sur MoonPay 7.

La plainte *Yuga* et le dossier du DOJ sont les deux points d'entrée publics les plus directs pour une telle demande.
