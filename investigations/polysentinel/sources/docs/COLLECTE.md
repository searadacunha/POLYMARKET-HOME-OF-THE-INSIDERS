# Collecte PolySentinel — fonctionnement et preuve

Vérification le 27 octobre 2026. Le collecteur utilise les contrats officiels Gamma keyset et Data API v2, dont les copies OpenAPI sont dans `evidence/inspection/`. `net.py` et `collect.py` sont écrits pour ce projet ; aucun collecteur tiers n'a été exécuté ou copié.

## Périmètre réel

Le catalogue est progressivement découvert, pas exhaustif au démarrage. Chaque passage lit les nouvelles créations v1 **et** v2, avance un balayage ancien → récent avec curseur durable, visite une étiquette prioritaire tournante et rafraîchit deux événements anciennement observés. Les appels par identifiant/slug permettent la résolution à la demande. Les changements de libellés, échéances, règles et statuts sont conservés dans les versions SQLite. Les correspondances tokens/issues viennent des tableaux Gamma, jamais d'une hypothèse « index zéro = YES ».

Les marchés inactifs ou fermés ne sont pas suivis. Un marché dont les identifiants d'issues manquent reste au catalogue avec `mapping_quality=unavailable` et une raison. Les pages brutes préservent aussi les éléments que la normalisation ne sait pas exploiter. Les totaux d'une invocation de catalogue comptent les lignes reçues et peuvent inclure des événements revus : les effectifs uniques sont ceux de la table `objects`.

La surveillance globale filtre par **CASH ≥ 1 000** par défaut (`global_min_nominal`). Elle permet de repérer de nouveaux événements hors du catalogue déjà parcouru. Elle ne couvre donc pas les petites opérations globales. En complément, une file de marchés actifs est interrogée sans ce plancher monétaire ; environ la moitié des places va aux marchés prioritaires, le reste au marché le moins récemment interrogé, y compris hors catégories prioritaires. Le nombre de marchés par cycle est borné. L'heure de dernière réussite et les erreurs sont attachées à chaque marché, sans assimiler le catalogue à une surveillance complète.

`/v2/trades` sert uniquement les côtés taker (`taker_only=true`) pour éviter de compter automatiquement les deux côtés d'un échange. Les bornes temporelles de cette route sont honorées pour un portefeuille, **pas** pour les flux global/market : le bot n'envoie pas de faux filtre temporel et s'arrête localement après le chevauchement voulu. L'enquête d'un portefeuille peut ensuite consulter les deux côtés selon son propre périmètre explicite.

## Durabilité et limites d'identité

Une page normalisée, ses quarantaines et son curseur sont enregistrés dans une même transaction SQLite `BEGIN IMMEDIATE`, `synchronous=FULL`, WAL. La réponse HTTP brute est enregistrée avant cette transaction ; un arrêt peut laisser une preuve brute non encore normalisée, jamais un curseur avancé sans ses lignes. Les doublons ne modifient pas la première date d'observation des trades.

Chaque passage relit la tête récente, puis avance un arriéré. Les filtres de chaque parcours sont sauvegardés et conservés sur ses pages suivantes, même après modification de la configuration. Un changement de périmètre démarre une nouvelle fenêtre et crée une trace explicite. Un arrêt juste après le commit de la dernière page ne relance pas ce parcours terminé. Un curseur invalide donne lieu à une récupération depuis la tête avec trace `gap`. Les arriérés dépassant 24 parcours sont abandonnés avec leur curseur, leurs bornes et la raison conservés dans `gap` : la couverture n'est jamais qualifiée de complète pour ces intervalles.

La Data API n'expose ni sequence_id, ni logIndex, ni orderHash dans la forme publique examinée. L'identifiant local est donc une signature économique (wallet, transaction, token, sens, montant, prix, heure) et un rang d'occurrence. Les lignes économiques identiques de la même transaction sont conservées en multiplicité, y compris lorsqu'elles traversent deux pages. **Ce n'est pas une preuve d'identité individuelle du fill.** Les preuves brutes et le rapprochement on-chain restent nécessaires. Les montants, frais ou rôles on-chain ne sont pas inventés à partir de cette signature.

Une ligne malformée est conservée dans `rejected_trade` avec sa raison et la preuve de page. Elle est comptée en `rejected`, exclue des signaux et rend le passage `degraded`. Une enveloppe/pagination incohérente, une erreur réseau ou des trades désordonnés empêchent l'avancement du curseur. Un vide valide reste `empty`, une limite de pages `capped`, et une panne `error`.

## Réseau et ressources

HTTPS public uniquement ; redirections désactivées ; pas d'environnement proxy hérité. POST n'est autorisé que pour une liste de méthodes de lecture JSON-RPC. Pas de transaction, signature ou clé privée. Quatre requêtes simultanées au plus, tentatives bornées, backoff et jitter. `Retry-After` est respecté ; s'il impose plus de 30 secondes, la tentative est rendue en erreur pour reprise ultérieure plutôt que d'attendre moins longtemps.

Avant chaque requête, le bot réserve la taille maximale d'une réponse et vérifie l'espace libre ainsi que les octets de `data/`, `logs/` et `reports/`. L'épuisement du budget ou du disque suspend la collecte et reste visible ; aucune suppression automatique. Les compteurs par fournisseur distinguent requêtes, réponses, octets, vides valides, erreurs DNS/transport et HTTP 429, avec cumul persistant et dernière réussite préservée lors d'une panne.

Les en-têtes HTTP sont conservés. Une réponse réelle du 27/10 portait `Cache-Control: public, max-age=300` : une cadence de 60 secondes ne promet pas une fraîcheur de 60 secondes. `lag_seconds` mesure l'âge du dernier trade servi, qui peut aussi refléter l'absence de transactions, pas seulement la latence technique.

## Vérifications exécutées

`tests/test_collect.py` contient 19 tests synthétiques : filtres constants, multiplicités, interruption/reprise, crash après dernière page, changement de filtre, rollback, vide/plafond/erreur, quarantaine, curseur corrompu, v1/v2, rotation, libellés d'issues, conservation de la première observation, HTTP 429, budget, RSS, plafond octets et panne DNS conservant les compteurs. Tous sont passés avec `.venv/bin/python -m unittest discover -s tests -p test_collect.py -v`.

Une petite sonde réelle isolée après correction des schémas a effectué 12 requêtes : 10 événements uniques, 198 marchés uniques, 40 lignes de trades, zéro ligne rejetée, zéro erreur de source. Son flux global était volontairement plafonné (10 lignes/page, deux pages avec l'arriéré), donc `capped`. La fraîcheur de son dernier trade global était 4,8 secondes sur cette mesure unique. Ces chiffres décrivent la sonde, pas une couverture exhaustive ni les performances à long terme. La réception du service installé et ses effectifs sont consignés par l'intégration dans les rapports du projet.
