# Contre-vérification : faux positifs et témoins

Lu le 2 novembre 2026. Tirages à graine fixe (`20261102`, `20261103`). Résultats dans `state/p10.json`, `state/p11.json`, `state/p13.json`, `state/p14.json`, `state/p16.json`.

**Tous ces tests sont exploratoires** : ils ont été conçus après la lecture des dossiers, et aucun seuil n'a été gelé. L'empreinte a seulement été écrite dans `tools/p13_siblings.py` avant ce script. Son premier test, sur les expéditeurs des adresses sœurs, n'a rien donné : je l'ai remplacé par une lecture des adresses elles-mêmes (`tools/p14_final.py`), après avoir vu ce résultat.

## Résumé

| Propriété | Chez le dossier | Chez les témoins | Verdict |
|---|---|---|---|
| Renvoi de 90 % en 5 min après un paiement | Oui | 18 sur 57 (31,6 %) | **Ordinaire** |
| Renvoi de 90 % en 15 min | Oui | 25 sur 57 (43,9 %) | **Ordinaire** |
| Deux paiements à moins de 10 min | Oui | 9 sur 57 (15,8 %) | **Fréquent** |
| Montant proche d'une sortie du service | Non retenu | 4 sorties à 5 %, 10 à 10 %, en 10 h | **Sans valeur de preuve** |
| Adresse à 2 transactions balayée en 492 s | Oui | 40 sur 60, et 54 sur 60 à forme égale | **Normal chez les adresses qui alimentent ce portefeuille** |
| Contact avec ChangeNOW au premier saut | 1 clé sur 11 | 0 sur 54 | **Non concluant, p = 0,17** |

Les 57 destinataires incluent la clé de kraben006 : sans elle, 17 sur 56, 24 sur 56 et 8 sur 56.

**Lecture :** aucun comportement de kraben006 autour de ChangeNOW ne le distingue d'un client ordinaire. Ce n'est pas une preuve d'innocence, seulement l'absence d'un signal.

## 1. Fausses correspondances de montants

| Fenêtre | Sorties | À 1 % | À 5 % | À 10 % |
|---|---|---|---|---|
| `0xdd3d72c5…`, USDC, 23 fév., 2,13 h, autour de 654,47 | 73 | 1 (la vraie) | | 2 |
| `0xdd3d72c5…`, USDC, 23 fév., 2,13 h, autour de 180,38 | 73 | 1 (la vraie) | | 1 |
| `0x3f3ee0a9…`, ETH natif, 4-5 oct., 10 h, autour de 0,00241406 ETH | 530 | | 4 | 10 |

**Environ un candidat à 10 % près par heure, sur un seul portefeuille et un seul actif.** En comptant les autres portefeuilles et les autres actifs, un rapprochement montant et date trouverait toujours quelque chose. **Je n'en retiens aucun.**

## 2. Effet des transferts automatisés

Le balayage de `0x7e67df45…` en 492 s n'est pas le geste d'une personne : 40 témoins sur 54 balayent au même délai exact, 11 autres à 504 s. Ces flux ne montrent aucune intention du client et ne doivent pas être lus comme une « exfiltration rapide ».

Même chose pour `0x66d582e5…` vers le portefeuille HTX en 72 s : c'est le comportement attendu d'une adresse de dépôt, HTX par comportement.

## 3. Adresses de dépôt réutilisées

Sur 60 témoins tirés parmi 805 expéditeurs vers `0x3f3ee0a9…` :

| Forme | Nombre | Lecture |
|---|---|---|
| 2 transactions, une entrée, une sortie vers le service | 54 | Usage unique |
| 1 transaction, aucune entrée native visible | 3 | Financement interne, non lu |
| Plusieurs entrées (4, 18 et 109 transactions) | 3 | Réutilisée, ou portefeuille d'un client habituel |

Donc environ 5 % de réutilisation visible, sur ce tirage. Une adresse réutilisée ne peut pas se lire comme un ordre unique.

## 4. Services mutualisés

| Rapprochement naïf | Pourquoi c'est faux |
|---|---|
| « ouldlm3alem et wen sont liés à ChangeNOW » | `0xee7ae85f…` (Binance: Hot Wallet 34) paie 10 000 USDC à `0x4958f6c3…` (ChangeNOW 22) le 2025-08-06. Flux entre deux services |
| « brace227 et kraben006 partagent un intermédiaire ChangeNOW » | `0xdd3d72c5…` : 1 656 021 transactions, 266 destinataires en 2,15 h |
| « walletwallet8424 est financé par ChangeNOW » | 0,00476548 ETH à une adresse mutualisée de 672 contreparties |
| « 4 destinataires de la clé de kraben006 sont liés à ChangeNOW » | Ils ont reçu du service. Dont une adresse de dépôt, HTX par comportement, et une adresse qui reverse à Cryptomus. Taux de base non mesuré |

## 5. Labels issus d'une même base

| Paire apparente | Réalité |
|---|---|
| Blockscout et Etherscan sur `0x3f3ee0a9…` | Même nom, même lien vers changenow.io : **à compter pour une seule source** |
| `QuantumDev-CERN` sur `0x3f3ee0a9…` | Cite Etherscan. **Une copie** |
| `PeLegend/BlockchainAnalysis` sur ChangeNOW n | Mêmes noms que dawsbot et OLI. **Une copie probable** |
| « ChangeNOW 16 » et « Hot Wallet 4 » sur `0xeba88149…` | Deux origines apparentes : OLI, compilation hildobby selon la note Blockscout, et Etherscan. Leur indépendance n'est pas vérifiée |
| Copies Arkham et AMLBot sur `0xdd3d72c5…` | Deux fournisseurs. **Indépendance réelle inconnue**, et lus de seconde main |
| Tag `changenow-dep` sur les 13 adresses à empreinte et sur `0x3f3ee0a9…` | Même famille de tags : **pas une corroboration de l'un par l'autre** |

**Exemples de mauvaise qualité d'étiquettes, écartés :**

- `amit-dev01/Chain-Sleuth-Backend` donne `0x077d360f11d220e4d5d831430c81c26c777e7340` à ChangeNOW. La vraie ligne de dawsbot est `0x077d360f11d220e4d5d831430c81c26c9be7c4a4` : début identique, fin différente. Le même fichier liste « 1ChangeNOW7kH9mN3L5vQ6rTSwXyZaK8gqY5 » et d'autres adresses qui semblent inventées.
- `Jam0k/Public-Feeds-IOCs` classe `0xdd3d72c5…` « high » pour « financial transactions related to malware deployment ». La source derrière ce flux montre 12,155745 USDT payés par ce portefeuille à une adresse de déploiement le 2025-08-26. **Un client malveillant ne rend pas le portefeuille malveillant.**
- `0xf2020cbf…` et `0x6976d802…`, « ChangeNOW candidate, unconfirmed » : non utilisés ici. Aucun contact avec les 11 comptes.

## 6. Taux d'erreur des heuristiques

| Heuristique | Mesure | Limite |
|---|---|---|
| Empreinte de balayage | 30 sur 30 sur le même portefeuille à une autre date, 12 sur 13 sur les adresses portant le tag, **0 sur 12 adresses de même forme** ailleurs, borne haute unilatérale de 22 % à 95 %. Les 54 sur 54 sont dans l'échantillon de définition et ne comptent pas | Circulaire sur l'attribution. Faux négatifs sur d'autres réglages de gaz non mesurés : la 13e adresse (3 gwei, écart triple) montre que le réglage varie |
| Tag `DEPOSIT ADDRESS` | Faux pour `0x3f3ee0a9…`, qui paie aussi | Tag à ne pas lire seul |
| Liens entre portefeuilles étiquetés | Contacts sur 9 adresses ChangeNOW sur 40 testées hors NOW Token, 10 n'ayant aucune ligne sur la chaîne 1. **Le contrôle ne vaut rien tel quel :** 0 sur 10, mais 3 adresses n'ont que 2 lignes et plusieurs fenêtres ne couvrent que quelques heures, souvent après l'arrêt d'août de `0xdd3d72c5…` | Ce test sert à décrire des liens, pas à mesurer une spécificité. C'est le contenu qui pèse : paniers de jetons et trésorerie |
| Page Blockscout `/addresses/` | Renvoie `metadata: null` même quand un tag existe | Déjà relevé par flow-trace |
| Compteur Blockscout | 0 transaction pour `0x7e67df45…`, qui en a 2 ; 321 022 contre 328 423 pour `0x3f3ee0a9…` | À ne pas utiliser pour une mesure |

## 7. Correspondances temporelles dues au hasard

- **Écart de 9 h 54 entre brace227 → kraben006 et l'envoi vers le dépôt :** l'envoi dépasse l'ancien solde, donc un lien comptable minimal existe (19,8 %). Le lien d'intention n'est pas démontré.
- **Passation du 10 août :** compatible avec une rotation de portefeuilles, sans cause connue. Elle n'est utilisée que pour l'attribution, jamais pour un compte.
- **Écart de 8 minutes entre les deux paiements :** fréquent (15,8 %).
- **Aucun rapprochement avec une date du marché du Ballon d'Or n'a été testé :** les fonds en cause partent 220 jours avant le premier dépôt.

## 8. Taux de base sur les comptes témoins

| Groupe | Lignes | Utilisables | Avec un historique | Avec un tag ChangeNOW |
|---|---|---|---|---|
| Comptes frais du recensement | 40 | 39 | 8 | 0 |
| Non surlignés | 6 | 2 | 0 | 0 |
| Même jeton | 10 | 1 | 0 | 0 |
| Jeton opposé | 27 | 12 | 6 | 0 |
| **Total comparateurs** | **83 lignes, 78 wallets distincts** | **54** | **14** | **0** |
| **11 comptes nommés** | **11** | **11** | **6** | **1 (kraben006)** |

- **Définition d'« utilisable » ici :** état READ, clé connue, historique de clé complet. Ce n'est pas le critère du taux de base de l'enquête, qui en compte 30 : ne pas confondre.
- **Fisher bilatéral :** p = 0,17 pour 1 sur 11 contre 0 sur 54. p = 0,30 pour 1 sur 6 contre 0 sur 14. Non corrigé, exploratoire. Une première copie à 62 lignes donnait 0 sur 44 et p = 0,20.
- **Puissance très faible.** Comparateurs choisis après lecture des dossiers, majoritairement frais, et clés souvent vides.
- **Premier saut seulement,** même lecture brute des deux côtés. `0x7e67df45…` n'aurait pas été vu par ce test.
- **Fichier final copié après la fin de flow-trace :** `evidence/comparators_final.jsonl`, SHA-256 `93031fd23ae3a7fbd399c999387c3dfd630cf8cde1866c4f96b822101f281155`. Première copie conservée : `evidence/comparators_snapshot.jsonl`. Résultats : `state/p16.json`.

**Contexte, population différente :** l'enquête `cn_pm_sakana` a recensé 158 parieurs Polymarket parmi les destinataires d'un portefeuille supposé ChangeNOW, en profil de clients perdants ordinaires (`NEGATIFS.md`, VÉRIFIÉ 16/10). Le contact avec ChangeNOW existe donc chez des parieurs ordinaires. Cette adresse n'a pas d'étiquette confirmée.

## 9. Chemins incomplets et historiques tronqués

| Élément | État |
|---|---|
| `0xdd3d72c5…`, `0x3f3ee0a9…`, `0xeba88149…` | Fenêtres seulement, jamais l'historique complet |
| Chaque adresse étiquetée, test des liens | 1 000 dernières lignes, par type |
| Adresses de services dans la marche de flow-trace | Coupées à 12 000 lignes au plus |
| `0x4337ff05…`, `0xdc264714…`, `0xe3478b0b…` | Coupées à 1 000 lignes |
| 5 clés | Aucune ligne : nonce 0, sur 6 chaînes |
| BSC, Base | Pas d'historique. Nonces seulement |
| Solana, Tron | Une seule adresse attribuée en source tierce sur Solana, aucune sur Tron |

## 10. Ce que ces tests ne disent pas

- Que kraben006 est innocent ou coupable.
- Que ChangeNOW a converti quoi que ce soit en XMR.
- Que les deux clés reliées appartiennent à une même personne.
- Que l'attribution vient de ChangeNOW : elle reste une déduction d'observateurs extérieurs.

<!-- adresses -->
## Adresses citées en forme courte

| Adresse complète | Étiquette publique lue |
|---|---|
| `0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b` | ChangeNOW Dep: 0x3f3...07B |
| `0x4337ff05c84b9a80ea0a78dbe7b8e102f66d4c08` | Voir `data/changenow_candidates.csv` ou aucune |
| `0x4958f6c329b61404b1cfd0ec8a44600a9486bd0a` | ChangeNOW 22 |
| `0x66d582e5e0670bd99153199f179733c6ee5d19be` | Voir `data/changenow_candidates.csv` ou aucune |
| `0x6976d8025229db5f54bc899dd3dbc9285423896b` | Voir `data/changenow_candidates.csv` ou aucune |
| `0x7e67df45e0a0bab092cbb2ff045f8aa8dfab6e23` | Aucune, relais |
| `0xdc264714f68d84cf29bc605589405e78bdbe7c9f` | Voir `data/changenow_candidates.csv` ou aucune |
| `0xdd3d72c53ff982ff59853da71158bf1538b3ceee` | ChangeNOW: Hot Wallet 3 |
| `0xe3478b0bb1a5084567c319096437924948be1964` | Voir `data/changenow_candidates.csv` ou aucune |
| `0xeba88149813bec1cccccfdb0dacefaaa5de94cb1` | ChangeNOW: Hot Wallet 4, ChangeNOW 16 |
| `0xee7ae85f2fe2239e27d9c1e23fffe168d63b4055` | Binance: Hot Wallet 34 |
| `0xf2020cbfc13fd5d4cb2da0ff8ae2d2c093c1c423` | Voir `data/changenow_candidates.csv` ou aucune |
<!-- fin adresses -->
