# Constats de cette session

Chaque relation financière a un niveau. Un gain n'est pas une preuve d'information privée. `NO_EDGE_VALIDATED` reste le verdict prédictif.

## Confirmé

1. Le test T1 publié est reproductible au chiffre près sur les lignes engagées. n = 45, 13 gains, excès d'environ 3,5 points, p = 0,335. Le résultat n'est pas un avantage.

2. Les trois alertes `DISCOVERY` gagnantes ne font pas partie de ce test. Les compter produirait un échantillon choisi après coup.

3. Aucune des 45 alertes de validation n'a, dans la table analytique, un autre passage le même jour, sur le même marché et le même côté. Le contrôle de cellule n'est pas calculable ici.

4. Sur les sources et chemins enregistrés de la semaine close 2026-W47, aucun compte Polymarket n'a un financement ChangeNOW ou Tornado Cash au niveau vérifié.

5. Le transfert de 8,933289 USDC.e cité dans le rapport de reproduction est dans le journal Polygon archivé. C'est un transfert, pas une identité.

6. Les identifiants de position recalculés ici coïncident avec les `clobTokenIds` archivés de deux marchés Gamma : le marché binaire « Maduro out in 2025? » sous le collatéral USDC.e, et le marché neg-risk « Will Anthropic's public ticker be $ANTH? » sous le collatéral enveloppé `0x3a3bd7bb9528e159577f7c2e685cc81a765002e2`. L'USDC.e ne retrouve pas les jetons du second marché. Le code est dans `code/ctf_position.py`. Il n'est pas une copie des sources LGPL de Gnosis.

## Fortement soutenu, déjà publié, non rejoué ici

Le rapprochement du 6 novembre 2026 entre cinq comptes Inca et les encaissements du marché iranien de juin 2025 reste celui du rapport `research_notes/inca-crosscheck-2026-11-06/REPORT.md`. Deux des cinq adresses sont dans un réseau déjà tracé. Une adresse de dépôt ou de retrait partagée n'est pas une personne unique. Cette session ne relève pas ce niveau.

## Indéterminé

1. Le client qui a alimenté la route mélangée `0xf2020…c423` le 16 novembre 2026. Le collecteur laisse le reçu au niveau `POSSIBLE`.

2. Le lien entre ces 8,93 USDC.e et l'achat de tennis de 1,01 USD observé deux jours plus tard. L'ordre du temps est compatible avec un usage du reçu. Il ne localise pas les unités.

3. Les 39 portefeuilles d'Inca annoncés en juillet 2026, et les 152 portefeuilles militaires cités par Reuters le 20 août 2026. Les adresses ne sont pas dans les textes obtenus.

4. Le biais favori-outsider de Cardozo et Rivero-Wildemauwe sur 588 millions de transactions annoncées. Le chiffre et le signe selon le mode d'agrégation sont ceux des auteurs. Le seau 0,55–0,60 à sept jours, laissé ouvert par `EDGE_VERDICT.md`, n'est pas le leur. Leur exception « sport » concerne les queues de prix, pas ce seau. Elle ne valide pas une règle de trading et ne réfute pas, à elle seule, l'estimation externe que le dépôt n'a pas rejouée.

## Réfuté, pour le périmètre testé

1. L'hypothèse qu'un écart 48 contre 45 dans les lignes `lonely_thin` serait une erreur d'arithmétique du verdict. Les trois lignes sont l'ensemble de découverte.

2. L'hypothèse qu'un contrôle même marché, même jour et même côté serait déjà dans la table analytique.

3. L'hypothèse que la semaine W47, sur les chemins enregistrés, contiendrait un groupe vérifié de comptes financés par ChangeNOW ou Tornado Cash avant un pari informé. Le compte vérifié est zéro. Le seul reçu exact possible est de 8,93 USD, suivi d'un achat de 1,01 USD dont le PnL observé est de 0,27 USD.

4. L'hypothèse que les 63,9 millions USD bruts des retraits Tornado de la semaine seraient un financement Polymarket. La colonne de financement vérifié est 0,00 et le niveau est `UNKNOWN`.

## Probable

Aucun constat nouveau n'est classé probable. Les proximités de route mélangée restent indéterminées tant que le déposant n'est pas séparé des autres utilisateurs du même contrat.

## Ce qui n'est pas une découverte

Le partenariat Chainalysis annoncé par la presse, le score en direct de plusieurs dépôts GitHub, et les classements de portefeuilles déjà décrits le 20 novembre ne sont pas des résultats de cette session. Aucun code concurrent n'a été exécuté.
