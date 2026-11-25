# Méthodes intégrées

Deux méthodes sont maintenant du code testé dans cette note. Une troisième, déjà dans le dépôt, a été exécutée sur la semaine manquante. Aucune n'est copiée depuis un dépôt sans licence ou sous une licence qui interdirait la copie : le calcul de position est réécrit à partir de l'arithmétique publique de la courbe, et le règlement par rachat est une identité comptable sur des lots synthétiques étiquetés.

## Identifiants de position

`code/ctf_position.py` calcule l'identifiant ERC-1155 à partir du `conditionId`, de l'index set et du collatéral. Les constantes de champ sont celles de BN254. Keccak-256 est testé sur les vecteurs vides et `abc`. Les sources Solidity LGPL de Gnosis ne sont pas dans le dépôt.

Contrôles sur des marchés déjà archivés, sans nouvel appel réseau :

- `rail_markets.json`, marché binaire, `negRisk` faux. Les deux jetons Gamma égalent les positions USDC.e d'index 1 et 2. Le collatéral enveloppé ne les retrouve pas.
- `xfm_anth_market.json`, `negRisk` vrai. Les deux jetons égalent les positions du collatéral enveloppé. L'USDC.e ne les retrouve pas.

C'est le point que le benchmark du 20 novembre marquait comme absent. Le code ne couvre pas un parent de collection non nul, et il n'a été confronté qu'à ces deux marchés. Un troisième marché pourrait encore diverger. Les tests refusent le mauvais collatéral, donc un futur écart ne sera pas silencieux.

## Identité de rachat

`code/settlement.py` clôt un lot seulement si le rachat désigne son créneau. Le créneau gagnant paie une unité par part restante. L'autre créneau paie zéro et sa coût reste une perte réalisée. Un marché sans rachat reste ouvert, au coût non réalisé. Les tests utilisent des lots nommés `c`, avec le drapeau `synthetic`. Aucun portefeuille réel n'est passé dans cette fonction. Les ledgers de `bradca0/polymarket-pnl`, `DGHW/polymarket-trader-miner` et `1816x/Polymarket-PnL-AuditLog` décrivent des clôtures plus complètes, y compris split et merge. Leurs chiffres (92 % de positions rapprochées, 1,71 million de dollars sur quatre portefeuilles, 96,6 % de correspondance) sont des affirmations d'auteurs. Les intégrer sans relancer leur code aurait fait passer ces affirmations pour des nôtres. Le gap de split et merge sur les ledgers de cas du dépôt reste ouvert. Voir la grille, item R3, toujours non satisfait.

## Collecte W47

Le module `investigations/weekly-funding-intelligence/weekly_funding` n'a pas été modifié. Il a été lancé sur la semaine close. Le snapshot, les hachages d'entrées que le collecteur écrit dans son JSON, et les contrôles de `code/w47_check.py` sont le produit. La série W16–W46 du dossier d'investigation n'est pas régénérée. Promouvoir W47 dans cette série demanderait une relecture du vérificateur de ce dossier et une revue séparée. Cette note ne le fait pas à sa place.

## Seconde passe

`code/same_cell.py` compare, pour chaque alerte complète, le prix de l'alerte au prix moyen des autres achats du même résultat le même jour UTC, et séparément aux achats déjà passés à l'heure de l'alerte. Le bootstrap est à graine fixe. Le résultat est exploratoire. Il ne entre pas dans le protocole figé.

`code/activity_ledger.py` somme TRADE et REDEEM. SPLIT retire le collatéral indiqué par la ligne. MERGE le rend. Un type inconnu, ici REWARD, est compté et laissé hors de la somme. Sur les cinq historiques, ce choix retrouve la trésorerie déjà publiée. Le ledger ne fabrique pas les deux jambes d'un split que la ligne ne donne pas. Comme aucune ligne SPLIT n'est présente, cette limite n'a pas été rencontrée sur des données réelles.

`code/population_rank.py` calcule un p par portefeuille sur la table d'ignition et applique Benjamini-Hochberg. Zéro rejet. `code/f2020_cohort.py` recompte la cohorte sans importer `weekly_funding`. `code/ranking_formula.py` est la somme pondérée publiée par vsbtc, pas une copie de leur fichier.

## Ce qui a été lu et non intégré

- L'Isolation Forest de `rwondo/polymarket-insider` (`contamination=0.05`, points fixes 40, 30 et 30). Le README dit qu'un signal ne prouve pas une information privée. Le paramètre de contamination est un choix, pas une fréquence mesurée. Il n'est pas ajouté au moteur.
- Le null binomial à 0,5 et le générateur `demoData.js` de `suislanchez/polymarket-insider-detector`. Le générateur tire des adresses au hasard et des taux de gain fixés. Ce n'est pas une source.
- Les décodeurs à haut débit annoncés par `vikramT75/poly-pnl` (3,4 millions d'événements par seconde, 96,6 % de correspondance). Le README a été lu. Le banc n'a pas été rejoué. Aucun chiffre n'est repris comme mesure locale.
- Le filtre `incrementNonce` de `TheOneWhoBurns/polymarket-nonce-guard`. Le README dit que l'appel est aussi une annulation légitime. L'intégrer comme liste d'exploits créerait les faux positifs que l'auteur signale. Pas de nouvelle famille d'alerte.
- La pondération GDELT et le contrôle même cellule d'orcalayer. Le premier dépôt n'a pas été rouvert. Le second a des lignes privées. Copier le contrôle sans les transactions du même jour ne ferait qu'un test vide, et c'est exactement ce que la table analytique donne déjà.

## Licence

Le code de cette note est du dépôt. Les lectures externes restent chez leurs auteurs. Aucun fichier tiers n'est redistribué. `warproxxx/poly_data` est en GPL-3.0 : son pipeline n'a pas été copié. Le README a servi à noter que la collecte V2 lit les journaux du CTF Exchange après le 28 avril 2026, et que l'ancien subgraph ne couvre plus l'histoire récente.
