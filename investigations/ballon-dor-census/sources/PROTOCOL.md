# Protocole de la contre-enquête Ballon d'Or 2026

Écrit le 2 novembre 2026, vers 14:35 UTC, **avant** tout calcul ChangeNOW direction 2, tout test statistique et tout détecteur. Déjà lus à ce moment : le post d'@irboz, les deux articles d'Upside, les comptes des 13 wallets (dépôts, retraits, positions), la reproduction de la capture Upside, le résumé des dépôts et retraits sur Polygon. Lus aussi avant cette rédaction, donc connus de l'auteur : les résumés de `PolySentinel-investigation`, l'audit, un extrait de `flow-trace`, le plan de `ChangeNOW-outflows`. Les conclusions de `ChangeNOW-proof` n'ont pas été lues. Tout écart s'ajoute à la fin, daté, sans réécriture.

## 0. Principes

- Aucune hypothèse n'est privilégiée (H0 à H4 de la mission). On cherche à détruire chaque rapprochement.
- Les résultats des autres enquêtes locales ne sont jamais une preuve ici. Ils servent de comparaison finale, dans `CONFRONTATION.md`.
- Une adresse n'est pas une personne. Aucune identité n'est cherchée.
- Une arrivée sur un exchange ou un service d'échange est une limite de traçabilité. Aucun lien n'est créé à travers un service.
- Absence de lien trouvé n'est pas preuve d'absence.

## 1. Échelle de preuve des liens entre wallets

| Niveau | Définition stricte |
|---|---|
| L1 `PROUVE_TX` | Transfert de valeur lu sur la chaîne entre deux adresses de taille personnelle, sans service intermédiaire, ou relié par un enregistrement de protocole vérifié sur les deux chaînes |
| L2 `ASSOCIATION_FORTE` | Au moins deux signaux indépendants parmi : financeur commun de taille personnelle, destination commune de taille personnelle, même clé ou CREATE2, gaz fourni par la même adresse personnelle. Le temps et le montant seuls ne comptent pas |
| L3 `SIMILITUDE` | Comportement proche, mesuré, sans transfert |
| L4 `MEME_PRESTATAIRE` | Même service, routeur ou contrat. N'autorise aucune fusion |
| L5 `FORTUIT_PLAUSIBLE` | Coïncidence compatible avec le taux de base ou le lot d'un service |

Seuls L1 et L2 fusionnent des wallets dans un cluster. Une adresse commune n'est « personnelle » que si elle n'a pas d'étiquette de service, pas de code de contrat, un nonce sous 1 000 et moins de 400 contreparties. Un relais de transactions (`tx.from` d'un retrait ou d'un dépôt sans gaz) n'est jamais un lien.

## 2. Verdicts des affirmations

`CONFIRMED` : relu sur la chaîne ou l'API, chiffre à ±2 %. `STRONGLY_SUPPORTED` : vrai à ±10 %, ou deux sources concordantes sans preuve directe. `PLAUSIBLE` : compatible, non démontré. `UNVERIFIED` : non testable avec les données accessibles. `CONTRADICTED` : les données disent autre chose.

## 3. Parcours des fonds

Paramètres fixés dans `code/col_60_walk.py` : 3 sauts, 45 nœuds par compte et par sens, 8 arêtes suivies par nœud, 20 $ minimum, sorties des clés lues depuis 30 jours avant le premier dépôt. Chaînes lues : Ethereum, Polygon, Arbitrum, Optimism, Solana, Bitcoin. Base et BSC : pas d'historique gratuit, seules les transactions citées par un enregistrement Relay y sont lues. Toute limite atteinte est écrite.

## 4. ChangeNOW direction 2

**Univers.** Toutes les adresses qu'une source publique attribue à ChangeNOW : tags Blockscout (`slug=changenow`, puis noms contenant « changenow »), listes dawsbot et brianleect. Chaînes 1, 137, 42161, 10.

**Fonction mesurée, distincte de l'étiquette**, sur octobre 2026 (du 1er octobre 00:00 UTC au 31 octobre 23:59 UTC) :
- `PAYOUT_HOT` : au moins 100 envois de valeur à au moins 50 destinataires distincts.
- `CONSOLIDATION` : au moins 20 envois et au plus 10 destinataires.
- `DEPOT_CLIENT` : moins de 20 envois, reçoit de peu d'expéditeurs.
- Autre : `INCONNUE`.

Seules les `PAYOUT_HOT` sont des sources de sortie. Une sortie vers une adresse étiquetée ChangeNOW est interne, vers un autre service, c'est un mouvement de service : ni l'une ni l'autre n'est un client.

**Destinataires.** Adresses sans étiquette de service, sans code de contrat (délégation EIP-7702 acceptée). Actifs reconnus seulement : natif, USDC, USDT, DAI, WETH, WBTC. Valeur en dollars au prix journalier DeFiLlama, approximative.

**Mesures :**
1. Wallets distincts financés. Total et par chaîne, avec la somme.
2. Nouveaux ou presque inactifs : au plus 3 transactions envoyées avant la réception, sur la chaîne de réception. Mesuré sur tous les destinataires si N ≤ 3 000, sinon sur un échantillon aléatoire de 3 000, graine 20261102, avec intervalle de Wilson.
3. Ont ensuite alimenté Polymarket : le Deposit Wallet calculé par CREATE2, ou l'adresse elle-même, a au moins un dépôt ou un trade après la réception, dans les 30 jours. Testé sur tous les destinataires.
4. Ont parié sur le Ballon d'Or : ce wallet est dans le recensement de la famille.
5. Montants identiques ou proches : groupes de destinataires à tolérance ±0,5 %, ±1 %, ±5 %.
6. Courte fenêtre : même tolérance et réception à moins de 10 min, 1 h, 6 h, 24 h. Soit 12 combinaisons.
7. Chemins comparables : `source → destinataire → Deposit Wallet` en moins de 24 h.
8. Sommes : total, vers Polymarket, vers les parieurs du Ballon d'Or, et part de chacun.

**Test des points 5 et 6.** Parmi les destinataires liés à Polymarket, nombre de paires proches en montant et en temps, comparé à une distribution nulle : on permute les couples (montant, date) sur tous les destinataires de la même chaîne et on retire au hasard un sous-ensemble de même taille, 10 000 tirages, graine 20261102. Correction de Holm sur les 12 combinaisons.

**Verdict figé.** `GROUPE_REVELE` seulement si **à la fois** : au moins 2 parieurs du Ballon d'Or dans les destinataires, et (un lien L1 ou L2 entre eux, ou un excès significatif après Holm au seuil 0,05 parmi les parieurs du Ballon d'Or). `INDICE_FAIBLE` : parieurs présents et excès parmi les destinataires Polymarket seulement. `NON_SOUTENU` : sinon. Dans tous les cas, on ne conclut qu'à l'intérieur de la couverture mesurée.

**Contrôles positifs avant lecture.** Le calcul CREATE2 doit retrouver 13 wallets sur 13. Un destinataire synthétique injecté doit être compté à chaque étape. Le recoupement doit retrouver un destinataire réel lié à Polymarket connu, s'il en existe sur la période, sinon le dire.

## 5. Statistiques

**Population.** Tous les wallets du recensement ayant acheté au moins 500 $ de notionnel dans la famille Ballon d'Or masculin (`48361`, `811116`, `811117`, `1105185`, `1189431`, `1105364`, `1105369`, `1105379`, `1218178`, `1218179`, `1225367`, `1225368`, `1226675`, `1226676`) avant la cérémonie. Sélection sur le fait d'avoir parié, pas d'avoir gagné.

**Dates de référence.** `T_VOTE` : 28 septembre, presse, non vérifié. `T_UPSIDE` : 23 octobre 15:17:49 UTC. `T_CEREMONIE` : 26 octobre 20:00 UTC. Les achats ultérieurs à `T_UPSIDE` ne servent jamais à mesurer une information antérieure à la publication.

**Frais.** Compte frais : créé au plus 30 jours avant son premier achat dans la famille, avec `join_date` de `/v2/user-stats`. Date absente : classé à part, jamais frais par défaut.

**Scénario gagnant.** Issues exactes réalisées : Kane 1er, Mbappé 2e, Yamal 3e, Rodri 4e, Messi 5e, Mbappé devant Yamal, Rodri devant Messi. Lues sur les résolutions de marché.

**Tests confirmatoires (T1 à T4), seuil de Holm à 0,05 sur les 4 :**
- **T1. Avantage des comptes frais.** ROI pondéré au dollar sur la famille, frais contre non frais, achats avant `T_UPSIDE`, bootstrap par wallet, 20 000 tirages. Le ROI inclut les perdants. Effet et intervalle à 95 %.
- **T2. Prix d'entrée.** Dans chaque marché du scénario gagnant, rang du prix d'entrée de chaque dollar parmi tous les achats du marché avant `T_UPSIDE`. Frais contre non frais, permutation stratifiée par marché et jour, 20 000 tirages. Mesure si les comptes frais achètent plus tôt que le prix, à date comparable.
- **T3. Concentration sur le scénario.** Part des frais dont au moins 80 % des achats de la famille portent sur le scénario gagnant, contre non frais appariés au montant (déciles). Permutation dans les déciles, 20 000 tirages.
- **T4. Excès de cohorte.** Part des achats de frais parmi tous les achats sur le scénario gagnant, comparée à leur part sur les autres issues au même prix (tranches de 10 centimes) et au même jour. Permutation stratifiée, 20 000 tirages.

**Dépendance.** Les marchés du scénario sont une seule réalisation. L'analyse Monte Carlo tire un classement unique par simulation, avec un Plackett-Luce calé sur les prix du marché du vainqueur à la date d'achat, 50 000 tirages par date retenue. Elle produit la probabilité implicite du scénario entier et, pour chaque wallet de la liste publique, la probabilité d'un P&L au moins égal. Elle est descriptive : le modèle est une approximation, et une p individuelle n'est pas une probabilité d'initié.

**Biais à chiffrer.** Survivance : combien de frais comparables ont perdu ou fini à zéro. Sélection après résultat : les listes publiques ont été faites en voyant les gagnants, leur performance ne prouve rien sans le dénominateur.

**Contrôles.** Tables synthétiques : nul (les frais ont la même distribution), moyen et fort. Le nul doit rester muet et le fort détecté. Population témoin hors événement : voir section 6.

**Interdit.** Aucune probabilité d'initié n'est produite.

## 6. Détecteurs prospectifs

Seuils fixés ici, jamais réglés ensuite. Toute variante après lecture est exploratoire.

Information autorisée à l'instant t : tape jusqu'à t, `join_date` du compte, catalogue Gamma tel que connu à t via `createdAt` des marchés. Résolutions, listes de presse et noms actuels interdits.

- **D1 `FRAIS_CONCENTRE`** : à l'instant t, compte de moins de 30 jours, au moins 5 000 $ de notionnel acheté dans une même famille d'événements en 72 h, et cette famille pèse au moins 80 % de ses achats vus.
- **D2 `COHORTE_FRAICHE`** : au moins 3 wallets D1 distincts sur la même issue en 7 jours glissants. Signal au niveau de l'issue.
- **D3 `SCENARIO_MULTI_MARCHES`** : compte de moins de 30 jours, acheteur dans au moins 3 marchés distincts d'une même famille en 72 h, au moins 1 000 $ chacun, prix d'achat entre 0,20 et 0,85.

**Temps.** Rejeu chronologique, pas d'une minute, sans regard en avant. Le signal n'est observable qu'à la seconde du trade qui franchit le seuil, plus la latence de collecte de l'API (mesurée, sinon notée inconnue).

**Échantillon de mise au point.** Aucun réglage. Le Ballon d'Or est l'échantillon d'origine et ne vaut pas test : les détecteurs sont inspirés de cette affaire.

**Hors échantillon.** Familles choisies selon une règle fixe avant lecture : tout événement Polymarket d'octobre 2026 à résultat révélé d'un coup, volume d'au moins 100 000 $ et catégorie `awards`, `science`, `culture` ou équivalent, plus 3 événements sportifs à volume comparable comme témoins sans vote secret. La liste exacte est écrite dans `study/oos_events.json` avant la collecte de leurs trades.

**Mesures.** Heure de première alerte, wallets signalés, part des alertes avant `T_UPSIDE`, nombre d'alertes par famille et par semaine, P&L et ROI des wallets signalés contre non signalés, nombre de comptes publics repérés avant `T_UPSIDE`. Aucun faux positif n'est certain, car il n'existe aucune vérité terrain : le taux d'alerte hors échantillon sert de borne de charge, pas de précision. Un détecteur qui ne distingue pas les familles témoins est déclaré non spécifique et n'est pas activé.

**Activation.** Aucune par cette enquête. Toute intégration reste une proposition à Benjamin.

## 7. Déviations

(ajout daté seulement)

- **02/11, 15:05 UTC, avant toute mesure ChangeNOW direction 2.** Blockscout étiquette ChangeNOW plus de 20 000 adresses sur la seule chaîne 1 (`slug=changenow`, type `protocol`, arrêt volontaire à 20 000), en grande majorité nommées « Deposit Address ». Elles sont une par client et ne peuvent pas être sources de sortie. L'univers mesuré est donc : tous les tags de nom sans « Dep: » ni « Deposit », le tag générique `changenow`, et les deux listes. Sont écartés avec leur motif, car ce ne sont pas des adresses du service : « Upbit Hacker …: ChangeNow », « Endaoment: Change Now Inc. », le contrat de jeton « ChangeNOW (NOW) ». Contrôle ajouté : 300 adresses de dépôt tirées au hasard (graine 20261102) passent par la même mesure de fonction, pour vérifier qu'aucune n'est une source de sortie. Conséquence pour la direction 1 : on interroge l'étiquette de chaque adresse rencontrée, ce qui ne dépend pas de l'énumération.

- **02/11, 15:10 UTC, avant lecture de T1 à T4.** Précision de T1 : le ROI valorise chaque dollar acheté avant `T_UPSIDE` à la résolution de son jeton, les ventes n'entrent pas. Motif : une sortie postérieure à `T_UPSIDE` mêlerait de l'information ultérieure, et cette mesure ne dépend pas des décisions de sortie. Les contrôles synthétiques (3 graines par scénario) ont donné une fausse alarme sur 12 tests dans le nul (T3, graine 3, en sens contraire) : le taux réel sous le nul est mesuré sur 30 graines supplémentaires et publié avec les résultats.

- **02/11, 15:35 UTC, après lecture de la cohorte, avant tout parcours de ces wallets. Exploratoire.** Comptes non nommés retenus pour un dossier : frais, au moins 2 000 $ avant `T_UPSIDE`, au moins 80 % sur le scénario gagnant, au plus 10 marchés lus (`derived/cohort.json`). Cette sélection a été faite en voyant les gagnants : elle sert à chercher des liens, pas à prouver un avantage. Budget réduit du parcours : 2 sauts, 15 nœuds par sens, 5 arêtes par nœud. La date de création `join_date` précède parfois le premier trade de façon incohérente (9 wallets à décalage négatif, classés frais par la règle du protocole) : la sensibilité de T1 et T4 sans ces wallets et sans les comptes publics est calculée à part, étiquetée exploratoire.

- **Correction des horodatages ci-dessus.** Les heures « 15:05 », « 15:10 » et « 15:35 » écrites dans les trois déviations précédentes sont des estimations fausses de ma part. Les heures vraies sont celles des commits : `6a5b98e` à 14:59:15 UTC, `7e92f4e` à 14:59:28 UTC, `037cdaa` à 15:04:56 UTC. L'en-tête « vers 14:35 » correspond au commit `9c9dd0a` à 14:34:21 UTC. L'ordre avant/après lecture reste celui décrit.
