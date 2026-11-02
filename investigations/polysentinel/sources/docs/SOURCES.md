# Sources, enquêtes et limites — 27 octobre 2026

Le code des enquêtes est écrit pour ce projet. Aucun détecteur tiers ni code Solidity n'est copié. Les noms/signatures d'événements et leur ordre de champs proviennent des interfaces officielles ; les deux dépôts modernes portent BUSL-1.1, le dépôt historique MIT. Les liens précis se trouvent dans `config/contracts.json`. NetworkX sert seulement au graphe de transferts sourcés, jamais à une fusion d'identité.

## API et reprise

- `https://data-api.polymarket.com/v2/trades` : historique utilisateur, `start=1`, `end` fixé au début du parcours, `taker_only=false` afin d'observer les ordres de ce portefeuille. Ces lignes ne sont pas ajoutées au flux global ni à un score émis antérieurement.
- `/v2/activity` : mêmes bornes fixes, tri TIMESTAMP/DESC, `exclude_deposits_withdrawals=false`. Dépôts/retraits sont des actions de l'API ; le financeur direct éventuel provient exclusivement des événements Transfer du reçu.
- `/v2/positions` : état OPEN observé à présent, un parcours à curseur borné. Un reliquat de snapshot antérieur n'est pas présenté comme position courante. Coût de revient, PnL et valorisation restent des affirmations de source et ne servent pas aux signaux préalables.
- `/v2/resolutions` : état officiel de chaque condition. Une condition `resolved` est enregistrée séparément en `public_condition`, avec l'heure où le bot l'a vue. Toutes les conditions connues et toutes les lignes de la réponse doivent être résolues pour créer `public_milestone` au niveau événement. La date de première annonce n'est jamais déduite de la résolution.

Chaque reprise d’historique conserve son ancienne borne haute et son curseur. En parallèle, une page récente est réservée avant de poursuivre le passé : fenêtre jusqu’à l’heure actuelle, chevauchement de 180 secondes configurable. Une tête récente plafonnée conserve son propre curseur dans une fenêtre de rattrapage durable, enregistrée atomiquement avec les lignes et le checkpoint de tête. Les pages restantes alternent entre historique ancien et fenêtres de rattrapage, sans réinitialiser l’ancien curseur. Les bornes, la tête récente et le nombre de fenêtres récentes en attente restent visibles. Avec trois pages par défaut, tête, rattrapage et historique peuvent progresser dans la même enquête ; une configuration à une seule page privilégie le récent et laisse le passé explicitement incomplet.

Une page et son checkpoint sont enregistrés dans une transaction SQLite. Les filtres de la première page sont conservés sur toutes les reprises. `has_more` et `next_cursor` sont vérifiés ; la taille de page n'est pas une preuve de fin. Un curseur refusé produit une erreur explicite, puis une reprise à la première page aux mêmes bornes lors de l'enquête suivante. Les états `empty`, `complete`, `capped`, `error` restent distincts. Lignes brutes et identifiants de réponses sont conservés.

L'historique demeure censuré : atteindre le bout de l'API ne prouve pas la création récente de l'adresse ni la présence de tout son passé on-chain. L'API ne fournit pas de logIndex dans les lignes de trades : les répétitions exactement identiques sont une ambiguïté d'identité explicitement signalée, pas des observations indépendantes certaines.

## Blockchain

Registre Polygon 137 : CTF et NegRisk historiques, CTF et NegRisk V2, ExchangeV3 du Protocol V2. Intervalles de blocs de déploiement/retrait **non vérifiés** : bornes nulles, aucune couverture historique complète revendiquée.

Décodage d'OrderFilled par adresse ET topic, vérification des longueurs ABI, montants entiers bruts, maker/taker, token, sens de l'ordre, orderHash, blockHash, transactionHash, logIndex, frais et actif des frais. V1 : frais dans l'actif reçu ; V2/V3 : frais en collatéral. La dénomination exacte du collatéral CTF V2 reste non vérifiée ; aucune conversion artificielle n'est appliquée. Les unités d'exécution sont à six décimales ; le prix est le quotient collatéral/parts.

Le rapprochement exige l'ordre du portefeuille comme maker, son token, son sens et ses montants. Le taker d'un log complémentaire peut acheter l'autre issue : on ne lui invente jamais un SELL. Les exécutions d'un même orderHash sont regroupées ; tolérance d'arrondi nominal documentée dans chaque résultat (`max(0,00001 ; nominal × 0,000001)`).

Chaque reçu ciblé est vérifié contre le chainId, le head, le blockHash canonique et 128 confirmations par défaut. Résultat provisoire, transaction révoquée, décodage invalide et réorganisation ne deviennent pas des faits finaux. Une nouvelle lecture conserve l'ancienne observation et indique un ancien blockHash invalidé. Il ne s'agit pas d'une indexation générale des logs ; la revérification concerne les échantillons revisités.

Les transferts pUSD et USDC.e du reçu doivent porter les mêmes transactionHash et blockHash que ce reçu et ne pas être marqués removed. Une incohérence invalide l’extraction au lieu de produire une arête. Les transferts valides touchant le portefeuille créent des arêtes avec preuve/log/date. Les infrastructures connues ont un lien officiel ; une adresse sans étiquette peut également être un service. Aucun contrôle commun, financeur économique ultime ou personne civile n'est inféré. Le graphe est limité à un saut et huit adresses par défaut ; arêtes exclues comptées. Une séquence dépôt→trade→retrait est descriptive, sans attribution des mêmes fonds.

## Information publique

`config/sources.json` contient des flux officiels Federal Reserve, BLS et SEC, sélectionnés par sujet. Le texte ne constitue jamais une instruction. HTTPS, hôtes publics, redirections désactivées, XML sans entités, limites de taille et champs échappés par l'interface. Les résultats textuels sont des rapprochements documentaires ; au moins deux mots significatifs du titre d'événement doivent être présents (un si le titre n'en contient qu'un).

URL, titre, contenu utile, date de publication déclarée, modification éventuelle, première observation réelle et empreinte sont séparés. La reprise du même contenu porte la même clé d'indépendance. L'analyse de flux est plafonnée à 50 entrées : entrées totales, traitées, restantes, liens hors liste et contenus tronqués sont comptés. Les sources en erreur, non couvertes ou plafonnées dégradent explicitement l'enquête.

**Limite majeure :** une annonce connue publiquement mais non encore résolue n'est pas identifiée automatiquement de manière exhaustive. Une mention RSS seule ne démontre pas son résultat. Sans jalon documentaire vérifié séparé, le dossier affiche « première disponibilité publique inconnue ». L'absence de résultat de recherche n'établit aucune information secrète. Aucun accès de recherche payant ni LLM n'est configuré.

## Budgets et qualité

Par défaut : 18 requêtes logiques et 90 secondes par enquête, trois pages de 100 trades et d'activité au total par flux (tête récente, rattrapage et historique partagent ce budget), une page de 100 positions par invocation, au plus deux portefeuilles pour une cible événement. Les tentatives HTTP effectives sont aussi bornées par Net ; le plafond théorique de transport d'une enquête vaut requêtes logiques × tentatives. Les caches consultés ont des limites explicites et comptées, avec filtrage SQL par cible avant application du plafond. Les erreurs partielles ne sont jamais remplacées par des zéros.

Les dossiers préservent le score et les règles reçus en entrée, les temps de leur calcul, les preuves nouvelles et les explications concurrentes : expertise, hasard, information publique, arbitrage, couverture, copie et automatisation. Aucune précision/rappel d'initiés ni probabilité de culpabilité n'est calculée.

## Vérifications exécutées

- `tests/test_chain.py` : fixtures synthétiques des cinq exchanges, deux sens, frais, cas complémentaire maker/taker, fills fractionnés, ABI invalide, infrastructure, confirmations/réorganisation et conservation des anciennes observations.
- `tests/test_investigation.py` : pagination/reprise avec tête récente indépendante et rattrapage, rollback atomique tête/lignes/curseur de rattrapage, filtres constants, déduplication, états distincts, curseur refusé, mauvais wallet non enregistré, budget explicite, graphe borné, financeur partagé sans fusion et couverture documentaire dégradée.
- `tests/test_news.py` : dates séparées, liens refusés, XML à entités refusé, contenu traité en données, article qui ne devient pas un résultat, jalon futur exclu, frères de marché non tous résolus et plafonds visibles.
- Lecture réelle du reçu `0x9025d5fa8d137253720f90e9666bf23c64b3ab896a3ee69a8b4ee7a8fd08e8c8` : log 272, 15 956,727273 parts, nominal 8 776,2, rapprochement réussi, 6 782 confirmations à l'observation. `evidence/inspection/receipt_reconciliation_live.json`, réponses brutes en SQLite. Ce test technique ne démontre pas une anomalie ni une pertinence statistique.

Disponibilité réelle des trois flux RSS : non vérifiée dans cette passe. Leur panne reste un état visible ; aucune source inaccessible n'est contournée.

La CLI accepte une adresse complète, un identifiant Gamma positif ou un slug d’événement. Un slug est résolu par la route Gamma officielle avant les requêtes Data API ; chemins/URL et adresses tronquées sont refusés.

Les dossiers issus du flux global peuvent porter `event_id=unmapped:SLUG`. Ce marqueur interne est retiré avant résolution Gamma ; les trades déjà stockés avec le slug restent inclus après obtention de l'identifiant numérique. Si le marqueur contient un hash de condition ou un identifiant de token, aucune route de slug fictive n'est appelée : l'enquête porte sur le portefeuille et conserve la correspondance événement inconnue. Une panne de métadonnées Gamma ne bloque pas l'historique d'un portefeuille valide ; elle est enregistrée dans les erreurs et dans `event_mapping`, sans affecter un événement arbitraire au dossier.
