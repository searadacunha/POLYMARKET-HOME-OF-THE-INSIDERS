# Plan et définitions, écrits avant toute mesure sur les destinataires

2 novembre 2026. Enquête descriptive et exploratoire, non gelée : aucun verrou, aucun test confirmatoire. Tout écart à ce plan est ajouté en bas, daté, sans réécriture.

Avant ce plan, seuls ont été lus : les étiquettes et les 1 000 dernières lignes de chaque adresse étiquetée, depuis les caches de `PolySentinel-ChangeNOW-proof`. Aucun destinataire, aucun lien avec Polymarket ni avec les 11 dossiers n'a été calculé ici.

## Périmètre

- Chaînes lisibles sans payer : Ethereum (1), Polygon (137), Arbitrum (42161) par Etherscan v2 ; Optimism (10) par `explorer.optimism.io`. Base (8453) et BSC (56) : pas d'historique gratuit, à écrire comme non couvertes. Hors EVM (Solana, Tron, Bitcoin) : non couvert.
- Fin des données `T_fin` : dernier bloc lu. Fenêtres glissantes depuis `T_fin` : 24 h, 7 j, 30 j, 90 j.
- Fenêtres Ballon d'Or : du 2 au 19 octobre 2026, soit 7 jours avant le premier dépôt des 11 comptes (9 oct.) jusqu'au lendemain du dernier (18 oct.). Les dates de chaque compte viennent de `cases/*.json`.
- Collecte complète sur 90 jours. Avant, seulement la relecture des historiques déjà en cache des 11 dossiers.

## Une étiquette n'est pas une fonction

Chaque adresse reçoit une fonction mesurée sur son comportement, séparée de son étiquette :

| Fonction | Règle |
|---|---|
| `CONTRAT_ROUTEUR` | Code déployé, hors délégation EIP-7702 |
| `PAYOUT_HOT` | Au moins 100 envois de valeur vers au moins 50 destinataires, et au moins 50 % d'entre eux servis une seule fois dans l'échantillon, sur le natif ou sur les jetons reconnus |
| `CONSOLIDATION` | Au moins 20 envois, au plus 10 destinataires, ou un destinataire à au moins 50 % des envois |
| `GAS_FUNDER` | Étiquette « Deposit Funder », ou au moins 90 % d'envois natifs dont les destinataires renvoient ensuite surtout un jeton vers une adresse de ce registre (mesuré sur échantillon) |
| `DEPOT_CLIENT` | Reçoit de peu d'expéditeurs, renvoie presque tout vers une seule adresse, moins de 20 envois |
| `INCONNUE` | Tout le reste, ou activité trop faible |

Seules les adresses `PAYOUT_HOT` actives dans les 90 jours sont des **sources de sortie retenues**. Une adresse `CONSOLIDATION` est lue pour ce qu'elle est : un mouvement interne ou vers un service, jamais un payout.

Confiance d'attribution, par lignée de source et non par nombre de listes, car les listes se recopient :
- **Lignées :** `etherscan_tag` (Etherscan, dawsbot, brianleect, PeLegend, copies), `oli_hildobby` (Blockscout tag OLI, compilation hildobby), `blockscout_name` (tag de nom Blockscout sans mention OLI), `arkham_copie`, `amlbot_copie`, `osint_faible`.
- **Élevée :** au moins 2 lignées et un comportement cohérent. **Moyenne :** 1 lignée et un comportement cohérent. **Faible :** `osint_faible` seule, ou comportement incohérent. Aucune attribution ne vaut preuve qu'un échange ChangeNOW précis a eu lieu.

## Ce qui compte comme un payout économique

- Natif : transaction réussie, valeur > 0, envoyée par la source.
- Jeton : log `Transfer` depuis la source, sur un jeton **reconnu**. Reconnu veut dire : un prix DeFiLlama de confiance au moins 0,9 pour ce contrat. Les faux jetons qui usurpent ETH ou USDT (déjà vus dans les listes, avec des caractères trompeurs) en sont exclus et comptés à part.
- Exclus : destinataire zéro (burn), mints, échecs, transferts à valeur nulle.
- Interne : destinataire qui porte une étiquette ChangeNOW de n'importe quelle lignée, source ou non.
- Service : destinataire étiqueté exchange, pont, DEX ou autre service.
- Valeur USD : prix journalier DeFiLlama du contrat ou du natif. Stablecoins : même source, jamais fixés à 1 d'office. Sans prix : montant natif seul.

## Compteurs

- **A.** Adresses destinataires uniques, par (chaîne, adresse). Le total multi-chaînes est donné séparément en adresses distinctes.
- **B.** Parmi A : EOA, EOA déléguée (7702), contrat, exchange ou service étiqueté, ChangeNOW interne, statut inconnu.
- **C. `FIRST_FUNDED` :** lecture complète sur la chaîne (natif, internes, jetons reconnus), et aucune valeur reçue avant le premier transfert source dans ce bloc ni avant. Une entrée de jeton non reconnu ne compte pas.
- **D.** Adresse déjà active, premier financement observé depuis une source retenue.
- **E.** Historique illisible ou coupé : statut inconnu, jamais converti en C ou D.
- Mesure : recensement si le budget le permet, sinon échantillon aléatoire stratifié (graine 20261102), avec intervalle de Wilson à 95 % et effectif affiché.

## Polymarket

Trois niveaux, jamais confondus :
- **`P_DEMONTRE_DIRECT` :** même chaîne, chaque saut lu : source vers destinataire, puis destinataire vers son compte Polymarket, ou source directement vers le compte. Le dépôt suit le payout. Aucun service intermédiaire.
- **`P_DEMONTRE_PONT` :** un saut entre chaînes porté par l'enregistrement du protocole (Relay, deBridge, CCTP), jamais par un montant ou une date.
- **`P_HYPOTHESE` :** même adresse propriétaire ou compte existant, sans chemin de fonds lu. Compté à part, jamais additionné.

Compte Polymarket : adresse elle-même active dans la data-api, ou Deposit Wallet calculé (formes legacy et beacon, recalcul validé sur les 11 wallets connus), ou anciens proxys si leur événement de création est lisible.

## Rapprochement avec les 11 dossiers

Classes 1 à 5 de la mission : direct depuis une source corroborée, indirect sur chemin vérifié, simple exposition à un service commun, correspondance non prouvée, aucun lien observable. Les adresses comparées : wallets, clés, financeurs et voisins personnels des `cases/*.json`, `0xa8e64a3c…` et `0x48ec106c…`. Un service commun n'est jamais un lien entre deux comptes.

## Grappes temporelles

Fenêtres de 1, 5, 15 et 60 minutes sur les payouts vers adresses nouvellement financées lorsque le statut est connu, sinon sur tous les destinataires, en l'écrivant. Un service actif paie par construction beaucoup d'adresses en même temps : les tailles observées sont comparées à une permutation des heures à l'intérieur d'une même heure de semaine. Simultanéité n'égale pas coordination.

## Témoins

Comptes Polymarket témoins : wallets de même période de création, sans lien observé avec une source, lus par le même code. Comparaison descriptive, exploratoire, sans correction prétendant à la confirmation. Le biais de sélection de ChangeNOW et les différences de chaîne, de période, de montant et de mécanisme sont écrits avec chaque taux.

## Ressources

Un worker réseau, porté à zéro tant que deux autres enquêtes interrogent le réseau (`tools/net.py`). Clé Etherscan partagée : pause d'au moins 0,6 s. Traitement en flux, arrêt interne à 700 Mo de mémoire. Pause sous 14,5 Go libres, si le swap monte de 300 Mo, ou si le battement de PolySentinel dépasse 180 s.

## Écarts au plan

- **02/11, avant toute mesure sur les destinataires :** les dates écrites plus haut étaient fausses. Lues dans `cases/*.json`, les premiers dépôts vont du 1er oct. (kraben006) au 22 oct. (OuldLm3alem). La règle reste : 7 jours avant le premier, jusqu'au lendemain du dernier. La fenêtre Ballon d'Or est donc du 24 sept. au 23 oct. 2026, UTC.
- **02/11 14:30 UTC, pause du garde-fou :** swap passé de 2 190 à 2 585 Mo pendant `reg2_behave.py`, dont la mémoire reste de l'ordre de 20 Mo. Causes visibles : application ChatGPT et sessions Claude ouvertes au même moment. Swap stable ensuite. Relance, qui repart du niveau courant : une nouvelle hausse de 300 Mo remettra le script en pause.
- **02/11 14:40 UTC, garde-fou du swap :** nouvelle hausse (3 141 Mo), toujours sans lien avec ce worker de 12 Mo : 7 sessions Claude et l'application ChatGPT ouvertes. Règle ajustée : une hausse de 300 Mo met en pause 10 minutes, puis le niveau courant devient la référence. Le disque (14,5 Go) et le battement de PolySentinel (180 s) restent bloquants sans limite.
- **02/11 15:00 UTC, après lecture du comportement, avant toute mesure sur les destinataires :** deux ajouts et une correction.
  - **Palier ajouté, `CANDIDAT_COMPORTEMENTAL` :** adresse sans étiquette ChangeNOW, au profil `PAYOUT_HOT`, reliée par la chaîne à une adresse étiquetée. Ses chiffres sont rapportés à part, jamais additionnés aux sources étiquetées dans le compte principal. Motif : le Hot Wallet 3 cesse presque ses envois le 10 août 2026 et aucune adresse étiquetée active ne reprend son volume de jetons sur Ethereum. Sans ce palier, l'étude mesurerait une panne de couverture.
  - **Fonction par période :** la règle s'applique sur les données des 90 jours, par période, car une adresse peut changer de rôle. Exemple : le Hot Wallet 3 après le 10 août.
  - **Hubs réfutés :** `0xd91efec7…`, `0x58edf782…`, `0x83c41363…`, `0x45300136…` et `0x41e45771…` étaient suspectés d'après leurs flux avec `0x4778480c…`. Blockscout les étiquette KuCoin. Ils ne sont pas collectés.
- **02/11 14:55 UTC, défaut de collecte corrigé :** le plan gratuit d'Etherscan rend 1 000 lignes par appel, quel que soit `offset`. `outflows.py` en attendait 10 000 et prenait ces pages pour la fin de l'historique : 379 lignes au lieu de plusieurs dizaines de milliers pour `0x3f3ee0a9…`. Repéré à la lecture du journal, avant tout calcul. Lecture tronquée laissée dans `state/out/`, jamais utilisée ; collecte reprise dans `state/out_full/`, test `tests/test_outflows.py` ajouté.
- **02/11 15:00 UTC, collecte élargie :** les entrées des adresses lues sont gardées aussi. Une adresse qui reçoit du gas puis envoie un jeton vers une source est une adresse de dépôt du service, pas un client. Sans les entrées, ce test serait impossible. Essai partiel d'environ 1 minute déplacé dans `state/old_runs/`, non utilisé.
- **02/11 15:30 UTC, garde-fou réseau élargi :** deux autres sessions interrogent le réseau et n'étaient pas surveillées : `PolySentinel-hacks-parallel` et `PolySentinel-ballon-dor-2026`. Leurs journaux entrent dans la surveillance de `tools/net.py`. Le collecteur se met en pause tant que deux autres sessions ont écrit une requête dans les 120 dernières secondes. Une partie de la collecte a donc tourné en même temps qu'elles avant ce correctif.
- **02/11 15:45 UTC, décision de Benjamin sur le budget réseau :** question posée, réponse « Ballon d'Or seul ». `PolySentinel-hacks-parallel`, sur un autre sujet, sort du compte des 2 workers. Le collecteur reprend à côté de `PolySentinel-ballon-dor-2026`. Publication GitHub : à la fin, une seule pull request (réponse « À la fin »).
