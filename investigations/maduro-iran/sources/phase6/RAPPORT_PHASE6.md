# Phase 6 : falsifier ou confirmer l'hypothèse MoonPay

29/09/2026, heures UTC.

**Fichiers**
- Annexe principale : `audit_attribution_moonpay.csv`, 52 observations avec hash, source, type de preuve, niveau et caractère contradictoire.
- Données de travail : `scratchpad/mad/p6_*.json`.
- Scripts : `scripts/p6_*.py`.

**Rapport de phase 5.** `RAPPORT_PHASE5.md` n'a jamais été écrit, la session s'étant arrêtée avant. Ses résultats sont repris et audités ici (§12). Seules les mesures nécessaires aux tests contradictoires ont été refaites.

---

## Verdict

**Issue B : IDENTIFICATION FORTE MAIS NON PROUVÉE.**

L'hypothèse MoonPay résiste à tous les tests de falsification tentés. Aucune observation ne la contredit. En plus de ceux de la phase 5, trois faisceaux nouveaux, indépendants entre eux, la renforcent :
1. **Un wallet d'administration commun.** `0xf691384d` a mis en service MoonPay 6 et 8 en 2021, puis a financé la trésorerie de la famille le 31/05/2024.
2. **Quatre bascules de génération synchrones**, toutes mesurées : payeurs stablecoin, payeurs ETH, collecteurs et distributeurs de gas.
3. **Un canal Ripple RLUSD dédié à la famille.** Les canaux d'Uphold, Bitso, B2C2 et Zero Hash sont séparés.

L'attribution reste non prouvée pour trois raisons :
- le nom « MoonPay » ne provient que des étiquettes Etherscan ;
- aucune source indépendante n'attribue une adresse de la famille à MoonPay ;
- une continuité d'opérateur n'établit pas l'entité juridique.

---

## 3. Audit des liens MoonPay

**Correction.** Le fichier `phase5/liens_famille_moonpay.csv` contient **21 liens, pas 23**. J'avais écrit « 23 » à tort dans le résumé de la phase 5.

| Classe | Nombre | Liens |
|---|--:|---|
| DIRECT, discriminant en contexte | 15 | MoonPay 8 → payeurs et trésorerie (6 : LINK ×2, BAT ×2, BAT 100 puis 8 656,4) ; échanges RLUSD entre `0xb93e3d70` et MoonPay 5 et 2 (7) ; PYUSD de `0xb93e3d70` vers MoonPay 5 (2, dont un en 2026 alors que ce payeur ne paie plus de clients depuis le 04/12/2025) |
| DIRECT, faiblement discriminant seul | 4 | MoonPay 7 → trésorerie 30,19 XAUt ; trésorerie → MoonPay 7 2 000 000 USDC ; MoonPay 7 → trésorerie DAI et WBTC |
| INDIRECT | 2 | MoonPay 7 → contrat de dépôt Bitstamp `0xeb1d71ae`, également utilisé par la famille |
| CORRÉLATION ou INCONNU | 0 | |

**Quelle proportion est réellement discriminante ?**
- **Aucun lien, pris seul, ne prouve l'identité.** Un règlement commercial entre deux sociétés produirait aussi un transfert direct.
- **15 sur 21 deviennent discriminants en contexte**, parce qu'ils ont la forme d'opérations de trésorerie interne :
  - transfert de stock deux jours après la mise en service ;
  - parts égales aux deux jumeaux, à 12 s d'intervalle ;
  - montant de test puis solde ;
  - actifs identiques à ceux que payait MoonPay 8 ;
  - vidage d'un payeur retiré vers MoonPay 5.
- Les 4 liens faiblement discriminants et les 2 liens indirects n'apportent rien de décisif seuls.

**Nouveaux liens trouvés en phase 6**, avec hashes dans le CSV :
- le wallet d'administration `0xf691384d` : 11 observations ;
- le canal Ripple ;
- les bascules.

---

## 4. Anciens payeurs MoonPay 6/8 et 1re génération

### Avant le 21/05/2024

MoonPay 6 et 8 (`0xd42f958e`, `0x22f6cc87`) :
- sont actifs depuis le 02-03/09/2021 et ont été mis en service par `0xf691384d` (100 000 USDC chacun) ;
- ont fait 74 300 et 74 324 paiements stablecoin au total, soit environ 82 par jour chacun sur les 12 derniers mois ;
- versent USDT et USDC, plus LINK, DAI, MATIC et BAT pour MoonPay 8 ;
- utilisent la limite de gas 84 000 pour 98,5 % des paiements des 12 derniers mois ;
- sont réapprovisionnés à 99 % par lots de 50 000, **directement depuis des hot wallets Binance** (Binance 14, 15, 16, 17, 18).

MoonPay 3 et 9 (payeurs ETH) :
- sont actifs depuis le 14/09/2021 ;
- font environ 2 000 paiements par jour à eux deux, avec une limite de gas de 21 000.

### Du 21 au 23/05/2024

| Jour | MoonPay 6 | MoonPay 8 | b93e | 26c5 | MoonPay 3 | MoonPay 9 | 0x0e9e3919 |
|---|--:|--:|--:|--:|--:|--:|--:|
| 20/05 | 76 | 94 | 0 | 0 | 991 | 977 | 0 |
| 21/05 | 77 | 83 | 7 | 6 | 677 | 657 | 455 |
| 22/05 | 44 | 26 | 64 | 54 | 0 | 0 | 1 002 |
| 23/05 | 0 | 0 | 90 | 84 | 0 | 0 | 1 170 |

Le détail horodaté de cette fenêtre :
- **21/05, 09:49 à 12:01 :** la trésorerie reçoit 451 000 USDT de Coinbase Prime 2 (3 transferts), puis envoie un test de 50 et 446 150 USDT vers le compte OKX `0x2313c810`. L'admin avait testé ce compte dès janvier 2024.
- **21/05, 14:56:35 et 14:56:47 :** premières transactions de `0x0e9e3919` et `0xa7ceed38`, à 12 s d'intervalle.
- **21/05, 15:55 à 16:12 :** tests de 50 USDC vers chaque payeur, puis 100 000 chacun.
- **21/05, 16:43 :** premier paiement de `0xb93e3d70` à un client.
- **23/05, 11:59 à 16:51 :** MoonPay 8 envoie 300 LINK et 203 BAT à chaque jumeau, puis 100 BAT de test et 8 656,4 BAT à la trésorerie.
- **31/05 :** les soldes de MoonPay 3 et 9 remontent vers l'admin, qui envoie 0,01 ETH de test puis 30 ETH à la trésorerie.

Aucun paiement client de MoonPay 6/8 n'a lieu après le 23/05/2024. Leurs soldes restants partent vers le dépôt Binance de MoonPay 7 (`0x0a4850be`) et vers l'admin.

### Après le 23/05/2024

La 1re génération tient environ 100 paiements par jour et par payeur, ce qui prolonge sans rupture le volume de MoonPay 6/8.

La continuité des bénéficiaires est forte :
- **côté stablecoins :** MoonPay 6 et 8 avaient déjà payé 58 % et 55 % de 160 bénéficiaires précoces tirés au hasard. Les autres rampes font beaucoup moins : Coinbase 10 16 %, Zero Hash 1 11 %, mercuryo 4 %.
- **côté ETH :** `0xa7ceed38` et `0x0e9e3919` paient ensuite 64 % et 60 % de 120 bénéficiaires tirés parmi ceux de MoonPay 3/9. Les autres rampes restent à Zero Hash 1 8 %, mercuryo 7 %, Transak 3 %.

### Migration interne ou nouveau service qui reprend une infrastructure semblable ?

**Un nouveau service indépendant n'explique pas les observations suivantes**, qui supposent le contrôle des clés des deux côtés :
- MoonPay 8 transfère son stock aux nouveaux payeurs deux jours après leur mise en service.
- L'admin qui a créé MoonPay 6/8 en 2021 finance la trésorerie en 2024, avec l'ETH récupéré sur MoonPay 3/9.
- L'admin teste en janvier 2024 le compte OKX que la trésorerie utilise dès son premier jour.
- Un payeur de la famille retiré du service, `0xb93e3d70`, vide encore du PYUSD vers MoonPay 5 en juillet 2026.
- Collecteurs et gas : même compte Bitstamp, passage de relais de collecteur en 2 jours, et lignée de distributeurs de gas partant d'un wallet financé par l'admin.

**Observations compatibles avec un tiers :**
- le financement change d'architecture : Binance d'un côté, trésorerie propre alimentée par Coinbase Prime, Kraken et Circle de l'autre ;
- le prix du gas diffère.

Aucune de ces deux observations n'exige un autre opérateur.

---

## 5. Test du « même opérateur » : mesures

Fenêtres de 12 mois :
- MoonPay 6/8 : 22/05/2023 → 20/05/2024 ;
- b93e/26c5 : 21/05/2024 → 20/05/2025 ;
- 4a9a/b715 : toute leur vie.

| Mesure | MoonPay 6 | MoonPay 8 | b93e | 26c5 | 4a9a | b715 |
|---|--:|--:|--:|--:|--:|--:|
| Paiements par jour | 82,4 | 82,5 | 101,4 | 102,0 | 405,4 | 403,8 |
| Limite de gas dominante | 84 000 (98,5 %) | 84 000 (98,3 %) | 84 000 (100 %) | 84 000 (100 %) | 100 000 (81 %) | 100 000 (81 %) |
| Prix du gas médian (même fenêtre, 21/05 16 h → 23/05) | 10,2 gwei | 11,3 gwei | 15,8 gwei | 15,6 gwei | | |
| Trous de nonce / tx échouées | 0 / 0 | 0 / 0 | 0 / 1 | 0 / 11 | 0 / 2 | 0 / 1 |
| Intervalle médian entre paiements | 636 s | 636 s | 492 s | 492 s | 132 s | 132 s |
| Paiements dans un bloc partagé | 1,0 % | 1,1 % | 2,1 % | 2,1 % | 7,9 % | 7,8 % |
| Part le week-end | 26,5 % | 26,4 % | 26,3 % | 26,0 % | 26,1 % | 26,3 % |
| Montant médian | 167,01 $ | 182,76 $ | 161,23 $ | 165,27 $ | 118,25 $ | 117,12 $ |
| Montants entiers | 5,7 % | 5,7 % | 2,0 % | 2,1 % | 1,7 % | 1,7 % |
| Lot de réappro dominant | 50 000 (99 %) | 50 000 (99 %) | 50 000 (73 %) | 50 000 (73 %) | 30 000 (52 %) | 30 000 (53 %) |
| Source du réappro | Binance 14-18 | Binance 14-18 | trésorerie | trésorerie | trésorerie | trésorerie |
| Délai médian réappro → paiement suivant | 648 s | 696 s | 528 s | 432 s | 120 s | 120 s |
| Durée de vie | 09/2021 → 05/2024 | 09/2021 → 05/2024 | 05/2024 → 12/2025 | 05/2024 → 12/2025 | 11/2025 → | 11/2025 → |

Autres mesures :
- **Jaccard des bénéficiaires :** MoonPay 6/8 0,247 ; b93e/26c5 0,238 ; entre générations 0,032.
- **Corrélation des profils horaires :** MoonPay 6/MoonPay 8 0,993 ; MoonPay 6/b93e 0,993 ; MoonPay 8/26c5 0,986 ; MoonPay 6/4a9a 0,990.

**Lecture.**
- Sont identiques : la limite de gas, la taille des lots de réapprovisionnement, le fonctionnement en paire (Jaccard intra-paire d'environ 0,24), la part du week-end, les heures et l'absence de trous de nonce.
- Diffèrent : la source du réapprovisionnement, le prix du gas dans la même fenêtre (environ +45 %) et la part des montants entiers (5,7 % contre 2,0 %).

Ces paramètres communs se retrouvent chez d'autres opérateurs. Ils corroborent mais ne prouvent rien.

---

## 6. Matrice des financeurs

| Source | MoonPay 6/8 (et 3/9) | Génération 1 | Génération 2 | Statut |
|---|---|---|---|---|
| Hot wallets Binance 14-18, 20 | stablecoins et ETH (direct) | aucun | aucun | différent |
| Admin `0xf691384d` | mise en service 2021, récupération 2023-2024 | trésorerie (30,01 ETH) | aucun | **commun** |
| Trésorerie `0x3b6dcfde` | aucun | 91 % des stablecoins | 100 % | différent (créée pour la famille) |
| Coinbase Prime 1 et 2 | aucun direct | trésorerie, altcoins, ETH G1 (84,7 %) | trésorerie | différent |
| Circle | via l'admin (2021) et MoonPay 7 | trésorerie (17,4 M$) | trésorerie | commun indirect (réservé aux entreprises, ne distingue pas) |
| Bitstamp 61, 53, Wallet | aucun direct | altcoins, gas, distributeur de gas | distributeur de gas | commun avec MoonPay 5 (Bitstamp 61) |
| Compte Bitstamp `0xeb1d71ae` | MoonPay 7 et admin (2023), ancien collecteur | collecteurs, trésorerie | aucun après 05/2025 | **commun** |
| Compte OKX `0x2313c810` | testé par l'admin (01-03/2024) | trésorerie (32,5 M$) | aucun | **commun** |
| Dépôt Binance de MoonPay 7 `0x0a4850be` | anciens payeurs et collecteur | aucun | aucun | différent |
| Kraken HW5, FalconX | aucun | aucun | trésorerie | différent |
| OKX 7, OKX 20 | MoonPay 7 (OKX HW5, 2026) | trésorerie | aucun | commun faible |

Bitstamp, Circle et OKX ne distinguent personne seuls. Les éléments communs discriminants sont trois comptes précis : l'admin, le compte Bitstamp et le compte OKX.

---

## 7. Test Bitstamp : `0xeb1d71ae`

**Nature du contrat (MESURÉ).**
- Proxy minimal EIP-1167 « Forwarder » (implémentation `0x059ffafd…`), créé le 25/02/2023 par **Bitstamp 1** via la fabrique `0xffa39728`.
- Bitstamp 1 le vide avec `flushForwarderTokens` et les fonds partent vers Bitstamp 2.
- C'est l'architecture standard d'une **adresse de dépôt attribuée à un compte client**, pas une adresse partagée.

**Expéditeurs (historique complet : 23 expéditeurs).**

| Expéditeur | Transferts | Période |
|---|--:|---|
| `0xfa7dddcf` (ancien collecteur) | 2 495 | 15/03/2023 → 30/06/2024 |
| `0x7f227df2` | 1 235 | 28/06/2024 → 16/04/2025 |
| `0xabe7931e` | 222 | 16/04/2025 → 27/05/2025 |
| Coinbase Prime 1 | 25 | 2024-2025 |
| Bitstamp: Wallet | 18 | |
| OKX (divers) | 21 | |
| Trésorerie | 4 | |
| MoonPay 7 | 2 | 10/2023 |
| Admin `0xf691384d` | 2 | 11-12/2023 |
| Binance 14, 15, 20 | 3 | |

**Individualisation.** Une adresse Forwarder correspond à un compte Bitstamp. On déduit (INFERÉ) que MoonPay 7, l'admin et la famille déposent sur le même compte Bitstamp. Le lien compte ↔ client n'est pas public, et il reste possible qu'un compte Bitstamp soit alimenté par des tiers : un dépôt n'exige pas d'être titulaire.

**Ce qui renforce l'inférence.** Il n'y a pas d'expéditeurs épars : les trois collecteurs se succèdent avec un recouvrement de 2 jours, et l'admin a récupéré les soldes de l'ancien collecteur en 2023.

**Conclusion.** C'est un compte individualisé, pas une infrastructure générique Bitstamp. Mais **« même dépôt Bitstamp = même entreprise » n'est pas démontré publiquement.**

---

## 8. Partenariats de jetons

| Jeton | Date on-chain (famille) | Date publique MoonPay | Source | Intervalle | Signification |
|---|---|---|---|---|---|
| USAT | 1er réappro 27/01/2026 16:45 (test 49,89) ; 1er paiement 17:12:23 | 27/01/2026, MoonPay parmi les plateformes de lancement (avec Kraken, OKX, Bybit, Crypto.com) | CoinDesk, Tether, The Block | même jour | cohérent ; aucun wallet MoonPay étiqueté ne manipule USAT ; la source de la famille (`0x17edcb15`) traite aussi avec Kraken |
| RLUSD | 1re réception 11/10/2024 21:39 depuis un multisig Ripple dédié ; 1er transfert sortant 16/10/2024 (vers MoonPay 5) | partenaires annoncés le 15/10/2024 (dont MoonPay) ; lancement public 17/12/2024 | Ripple (BusinessWire), moonpay.com | 5 jours avant l'annonce ; 2 mois avant le lancement | la famille est un **partenaire bêta avec son propre canal Ripple**, distinct de ceux d'Uphold, Bitso, B2C2 et Zero Hash ; aucun canal séparé ne mène à un wallet MoonPay |
| XAUt | 1er paiement 24/04/2025 20:08 ; la veille, MoonPay 7 envoie 30,19 XAUt à la trésorerie | annonce MoonPay le 29/04/2025 | moonpay.com, recherche | 5 jours avant | cohérent avec un lancement discret avant annonce |
| PYUSD | 1er paiement 01/10/2024 22:10 | 02-03/10/2024 | The Block, moonpay.com | 1 à 2 jours avant | idem ; même destinataire que l'un des tout premiers paiements RLUSD (`0xb7aec302`, 40 tx), compatible avec un wallet de test |
| USD1 | 20/05/2025 | inconnue | page moonpay.com sans date | | données insuffisantes |
| GODS | 04/06/2024 | inconnue | | | données insuffisantes |

Un jeton pris en charge par MoonPay ne prouve rien seul. L'intérêt est ailleurs : ces dates **ne dépendent pas des étiquettes Etherscan**. Parmi les listes publiées, MoonPay est la seule plateforme présente à la fois dans les partenaires de lancement RLUSD et USAT, et ces listes peuvent être incomplètes.

---

## 9. Test Polymarket

- **Les 16 paiements :**
  - 11 vont vers des adresses de dépôt Polymarket sur Ethereum (EIP-7702 délégué à `0xe6cae83b…`, gas payé par les sponsors fun.xyz, vidage vers Relay en moins d'une minute), en direct ou via `0x44b6f8de` ;
  - 4 vont vers un dépôt MEXC ;
  - 1 va vers un EOA (`0x420d62bf`) ;
  - leur mécanique d'envoi est identique à celle des autres paiements (`transfer` simple, limites de gas standard, aucun champ particulier).
- **Taux de base :**
  - 0 sur 250 paiements Ethereum échantillonnés vers une adresse de dépôt Polymarket ;
  - 1 sur 150 sur Polygon et 1 sur 150 sur Ethereum vers un compte Polymarket ;
  - la destination typique est un wallet en auto-garde : 17 % des paiements Ethereum vont à des comptes Trust Wallet EIP-7702.
- **Réponse :** les 16 paiements **n'ont pas de signature spécifique** d'un achat MoonPay × Polymarket. Ce sont des envois ordinaires du service vers une adresse fournie par l'acheteur ou le client. D'après la presse, l'intégration documentée livre des USDC sur Polygon à l'adresse Polymarket ; ce n'est pas la mécanique observée ici (Ethereum puis Relay).

---

## 10. Preuve de client

Les 5 adresses bénéficiaires ont été testées : dépôt MEXC, dépôts Polymarket de Chiwawas et de 154x838hjd6, `0x420d62bf` et `0x44b6f8de`.
- Aucune ne reçoit de fonds d'un wallet étiqueté MoonPay (2, 3, 5, 6, 7, 8, 9) ni de l'admin.
- Leurs seuls liens avec un service sont les payeurs de la famille.
- `0x420d62bf` n'apparaît qu'une seule fois dans toutes les données de la famille : le paiement n°16.

**Conclusion : aucun paiement ne peut être relié publiquement à un client ou à un service plus précis.** Le KYC de MoonPay n'est pas observable. Aucune tentative d'identification de personne n'a été faite.

---

## 11. Hypothèses concurrentes

| Hypothèse | Observations compatibles | Observations problématiques | Données manquantes |
|---|---|---|---|
| **H1 : migration interne MoonPay** | les 4 bascules synchrones ; admin commun ; stock ensemencé ; comptes Bitstamp et OKX communs ; RLUSD, USAT, XAUt et PYUSD calés sur les annonces MoonPay ; MoonPay 5 reprend les altcoins | le nom repose sur les étiquettes Etherscan ; famille non étiquetée ; financement et prix du gas changent | confirmation par MoonPay ou méthode d'étiquetage documentée |
| H2 : entité liée ou prestataire opérant pour MoonPay (filiale, entité régulée distincte, sous-traitant de paiement) | changement d'architecture de financement en 2024 ; comptes institutionnels propres (Coinbase Prime, Kraken, Circle Mint) | admin commun et comptes communs (OKX, Bitstamp) : un prestataire devrait partager les clés ou les comptes de MoonPay | organigramme, contrats, entités juridiques de MoonPay |
| H3 : une autre rampe (Transak, Banxa, Mercuryo, Ramp, Zero Hash, Coinbase Onramp) | activité et clientèle semblables | elles ont leurs propres wallets étiquetés ; Zero Hash a un canal RLUSD distinct ; chevauchement de bénéficiaires 3 à 11 % contre 55 à 64 % pour MoonPay ; aucun lien d'opérateur | aucune |
| H4 : un exchange (Uphold, Bitstamp, Kraken, OKX) | ils prennent en charge certains de ces jetons | Uphold a un canal RLUSD distinct ; la famille dépose **chez** Bitstamp, Kraken et OKX comme cliente ; 94,9 % d'adresses de dépôt à usage unique, typique d'une vente par commande, pas d'un compte d'exchange | aucune |
| H5 : un intégrateur (Trust Wallet, MetaMask) | 17 % des paiements vont à des comptes Trust Wallet | ces wallets ne gèrent ni trésorerie ni collecteurs ; ce sont des destinations, pas des émetteurs | aucune |
| H6 : les étiquettes « MoonPay N » sont fausses | Etherscan est la source unique du nom | les dates RLUSD, USAT, XAUt et PYUSD et le partenariat Polymarket concordent avec MoonPay indépendamment des étiquettes ; MoonPay 7 est reçu de Galaxy et Genesis OTC, cohérent avec une grande rampe | recoupement par un second fournisseur d'étiquettes (Arkham, Chainalysis, TRM) |

---

## 12. Audit des affirmations de la phase 5

| Affirmation | Source brute | Méthode | Résultat | Risque de biais |
|---|---|---|---|---|
| 431 056 bénéficiaires | historiques complets de 4 payeurs stablecoin et 3 payeurs ETH | union des destinataires : stablecoins ≥ 1 $, ETH > 0 | 431 056 ; recoupement stablecoin/ETH 29 446 | **borne basse** : exclut `0xa7ceed38` (identifié en phase 6), Polygon (57 064 paiements rien que sur les fenêtres tronquées de 4a9a et b715) et les altcoins ; ce sont des adresses, pas des personnes |
| 94,9 % d'usage unique (`0xabe7931e`) | historique complet : 148 671 tx et 43 432 transferts de jetons | expéditeurs de dépôts réels ; usage unique = un seul envoi | 155 571 sur 163 918 | inclut quelques sosies d'empoisonnement avec poussière (ex. 471 envois d'un sosie de la trésorerie) : effet négligeable |
| 72,1 % (`0x7f227df2`) | historique complet | idem | 29 487 sur 40 874 | idem |
| 21 transferts directs | `liens_famille_moonpay.csv` | lecture du fichier | **19 transferts directs** famille ↔ wallets étiquetés MoonPay + 2 indirects (MoonPay 7 → dépôt Bitstamp) = 21 lignes | nom MoonPay = étiquette Etherscan |
| 23 liens MoonPay | idem | idem | **faux, 21** (erreur de transcription) | |
| 2 000 000 USDC | tokentx de la trésorerie | transfert unique | 29/08/2025 16:41:23, `0xe373ac214f50b3362fee0d8b072cc0c0960c04612650d43981a49473b40b9ab7` | aucun |
| 58 % / 55 % | `p5_predecessor.json` | **échantillon** de 160 bénéficiaires tirés parmi 701 précoces répétés (au moins 3 paiements) ; 300 premiers transferts de chacun | 93 et 88 sur 160 (81 % et 77 % des 115 qui avaient reçu quoi que ce soit avant) | échantillon ; biais vers les bénéficiaires répétés ; historiques tronqués à 300 lignes |
| Arrêt de MoonPay 6/8 | historiques complets | paiements stablecoin par jour, hors comptes d'exploitation | dernier paiement client le 22/05/2024 ; zéro après le 23/05 ; balayages jusqu'au 12/07/2024 | aucun |
| Démarrage des nouveaux payeurs | historiques complets | premier paiement | b93e 21/05/2024 16:43:11 ; 26c5 18:22:11 ; 0x0e9e3919 14:56:35 ; 0xa7ceed38 14:56:47 | aucun |
| Limite de gas 84 000 | txlist | part des paiements | b93e et 26c5 : 100 % ; MoonPay 6 : **98,5 % sur les 12 derniers mois mais 45,7 % sur toute sa vie** (utilisée dès le 03/09/2021) | la formulation de phase 5 surestimait la constance chez MoonPay 6/8 |
| 42 332 adresses servies par `0x9d34c01d` | historique complet (44 800 tx) | destinataires distincts de valeur > 0 | 42 332 adresses, 43 889 envois | le rôle d'adresse de dépôt n'est vérifié que sur un **échantillon** de 25 sur 25 |

---

## 13. Le montant de 0,01 ETH

| Émetteur | Rôle | Part des envois à exactement 0,01 ETH | Contexte |
|---|---|--:|---|
| `0x0e9e3919` (payeur ETH) | paiement à un client | 0,32 % (2 193 sur 686 510) | le n°16 (0,01 ETH vers `0x420d62bf`) est un paiement ordinaire : gas 21 000, nonce 448 426, 18 autres paiements dans les ±10 min |
| `0x9d34c01d` (distributeur de gas) | gas des adresses de dépôt du service | 46 % (20 244 sur 43 889), puis 0,002 ETH | ses destinataires se vident vers un collecteur |
| `0x2ab9ac2b` et `0xa26ebecc` (anciens distributeurs) | même rôle | environ 75 % | mêmes variantes 0,0099, 0,0021, 0,0022 |
| Admin `0xf691384d` | test avant transfert de 30 ETH | 1 envoi | montant de test courant |

`0x420d62bf` n'a jamais rien envoyé à un collecteur : ce n'est **pas** une adresse de dépôt du service. **0,01 ETH n'est pas une signature**, et le n°16 n'est pas un envoi de gas du distributeur.

---

## 14. Réponses

**Q1. Les nouveaux payeurs sont-ils les successeurs fonctionnels de MoonPay 6/8 ?**
**Oui, c'est mesuré** :
- bascule en 48 h avec volume continu ;
- 55 à 58 % des bénéficiaires en commun ;
- mêmes paramètres ;
- stock transféré par MoonPay 8.

Il en va de même côté ETH (MoonPay 3/9 → `0x0e9e3919`/`0xa7ceed38`), côté collecteurs et côté gas.

**Q2. Peut-on attribuer les nouveaux payeurs à MoonPay ?**
FORTE MAIS NON PROUVÉE.

**Q3. Peut-on attribuer les collecteurs à MoonPay ?**
FORTE MAIS NON PROUVÉE :
- ils partagent le compte Bitstamp de MoonPay 7 et de l'admin ;
- ils prennent le relais de `0xfa7dddcf`, dont l'admin a récupéré les soldes ;
- la lignée de gas remonte à un wallet financé par l'admin.

Le lien est un peu moins direct que pour les payeurs : il n'y a aucun transfert direct entre un wallet MoonPay et `0x7f227df2` ou `0xabe7931e`.

**Q4. Peut-on attribuer la trésorerie à MoonPay ?**
FORTE MAIS NON PROUVÉE :
- l'admin lui envoie 0,01 puis 30 ETH ;
- MoonPay 8 lui envoie du BAT ;
- MoonPay 7 échange avec elle dans les deux sens ;
- l'admin avait testé son compte OKX avant elle.

**Q5. Les 16 paiements sont-ils des paiements MoonPay ?**
- « Émis par l'infrastructure attribuée à MoonPay » : FORTE MAIS NON PROUVÉE.
- « Achats de clients MoonPay » : COMPATIBLE seulement. C'est cohérent avec le modèle d'une rampe (montants calculés, 1,7 % de montants entiers), mais aucun paiement ne porte de marque qui le démontre, et il n'y a pas de signature Polymarket.

**Q6. Peut-on relier un seul des 16 paiements à un client ou un service identifiable publiquement ?**
Non.

**Q7. Existe-t-il une observation qui réfute MoonPay ?**
Aucune n'a été trouvée. Quatre observations l'affaiblissent sans la contredire :
- source unique du nom (Etherscan) ;
- architecture de financement différente ;
- prix du gas différent ;
- famille non étiquetée.

**Q8. Quelle donnée externe aurait le plus de valeur ?**
Une confirmation explicite que `0x4a9a1675`, `0xb7152d59`, `0x974413b8`, `0x9bdbbd6f`, `0x0e9e3919`, `0xa7ceed38` ou `0x3b6dcfde` appartiennent à MoonPay. Elle pourrait venir :
- de MoonPay (liste officielle d'adresses d'envoi, réponse à une réquisition, données Travel Rule) ;
- ou d'un fournisseur d'étiquettes à méthode documentée, indépendant d'Etherscan.

Viennent ensuite les registres de commandes de MoonPay pour les 16 hashes. Le n°16 (`0x23d8c3c5…`, 09/07/2025) est le premier maillon de la branche EVM du réseau.

---

## 15. Niveaux d'attribution finaux

| Objet | Niveau |
|---|---|
| **Identité du service** | **FORTE MAIS NON PROUVÉE** (MoonPay) |
| **Identité des wallets** (trésorerie, 6 payeurs, 2 collecteurs, distributeur de gas) | **FORTE MAIS NON PROUVÉE** |
| **Identité des 16 paiements** (émis par l'infrastructure MoonPay) | **FORTE MAIS NON PROUVÉE** ; nature « achat MoonPay » : **COMPATIBLE** |
| **Identité des clients** | **INCONNUE** |

---

## Conclusion : pourquoi l'identification reste non prouvée

1. **Aucune source indépendante n'attribue une adresse de la famille à MoonPay.** La famille n'a ni étiquette, ni mention publique, ni liste officielle d'adresses.
2. **Le mot « MoonPay » ne vient que des étiquettes Etherscan** (MoonPay 2, 3, 5, 6, 7, 8, 9). Ces étiquettes sont une attribution externe, sans méthode publique, reprise par les sites du même groupe et par un agrégateur. Elles se recoupent entre elles on-chain, mais ne sont pas indépendantes.
3. **Ce qui est démontré, c'est une continuité d'opérateur.** Un même contrôleur de clés (admin commun, transfert de stock, comptes communs) relie la famille au groupe de wallets étiqueté MoonPay. Cela ne désigne pas l'entité juridique : une filiale, une entité régulée distincte ou un prestataire ayant accès aux mêmes comptes restent possibles.
4. **Les indices qui ne reposent pas sur Etherscan** (dates RLUSD, USAT, XAUt et PYUSD, canal Ripple dédié, partenariat Polymarket) désignent MoonPay par recoupement de listes publiques. Ce sont des compatibilités, pas une attribution.

La conclusion est donc que **MoonPay est l'explication la plus cohérente et qu'elle survit à l'audit contradictoire**. Ce n'est pas une attribution certaine.
