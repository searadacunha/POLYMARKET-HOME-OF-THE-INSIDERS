# Couverture historique indépendante des comptes cités

## Quelles données ont réellement été récupérées ?

### Takeaway
La collecte bornée a récupéré 46 533 lignes du flux taker sur 31 événements et 642 marchés trouvés par recherche lexicale. Elle s'est arrêtée au budget annoncé de 100 requêtes ; trois flux gardent un curseur de continuation. Ce n'est donc pas un historique exhaustif de l'affaire ni de Polymarket.

### Cited Findings
- Les recherches `Ballon`, `Ballon d'Or 2026` et `Ballon 2026`, avec marchés fermés conservés, ont chacune atteint `hasMore=false`. Leur union comprend 31 événements : vainqueur masculin, places exactes 2 à 5, top 2/3/5/10, duels, présence à la cérémonie, prix féminins et autres trophées. L'inclusion dépend uniquement du titre contenant « ballon » et « 2026 », jamais du résultat ni d'un compte publié. [Recherches conservées](/Users/benjamindacunha/Projects/PolySentinel/studies/ballon_2026_20261030/data/catalog_search.json), [catalogue actualisé](/Users/benjamindacunha/Projects/PolySentinel/studies/ballon_2026_20261030/data/catalog_refreshed.json).
- Acquisition : 3 requêtes de recherche, 31 actualisations d'événements, 66 pages de trades ; 100 réponses HTTP 200, 0 erreur de transport/HTTP, 0 erreur de flux constatée, 0 réponse trade vide, 0 HTTP 429 et 0 ligne rejetée. Les 46 533 lignes reçues ont été rapprochées une à une de leur réponse brute ; les SHA-256 des 100 réponses concordent. [Validation](/Users/benjamindacunha/Projects/PolySentinel/studies/ballon_2026_20261030/data/collection_validation.json), [journal des requêtes](/Users/benjamindacunha/Projects/PolySentinel/studies/ballon_2026_20261030/data/requests.jsonl).
- 28 flux ont atteint la fin de pagination exposée par l'API ; les 3 autres restent incomplets. Le flux `48361` (vainqueur masculin) contient 6 000 lignes mais ne remonte qu'au **26 octobre 22:26:17 UTC**, après la cérémonie ; le flux `811116` (top 5) contient 5 000 lignes, jusqu'au **23 octobre 12:28:24 UTC** ; `811117` (top 3), 5 000 lignes, jusqu'au **18 octobre 18:49:48 UTC**. [État par flux](/Users/benjamindacunha/Projects/PolySentinel/studies/ballon_2026_20261030/data/collection_summary.json).
- Les bruts occupent 48 672 131 octets. Le ledger économique minimal gzip occupe 5 149 061 octets, SHA-256 `958de0f0717ac100d9b502e64d878944ebefa17fe5cff6930b01a7962d1e3113`. Il exclut noms de profil, libellés d'issues, résultats et métadonnées actuelles ; les champs d'identité économique et les deux horloges sont conservés. [Ledger minimal](/Users/benjamindacunha/Projects/PolySentinel/studies/ballon_2026_20261030/data/trades_minimal.jsonl.gz), [sources exactes du normaliseur](/Users/benjamindacunha/Projects/PolySentinel/studies/ballon_2026_20261030/data/trade_normalizer_sources.json).

### Inferences
- Les recherches concordantes rendent le périmètre lexical vérifiable, sans démontrer qu'aucun marché supprimé, renommé ou mal indexé manque.
- Les événements connexes sont volontairement dans la collecte. Les effectifs agrégés ne doivent pas être présentés comme ceux des seuls paris sur le classement masculin.

### Gaps
- Aucune certification indépendante de l'exhaustivité des événements ou des transactions.
- Absence de continuation des trois curseurs après le plafond ; aucun nouvel appel n'a été ajouté lors de la reprise.
- Aucun reçu blockchain rapproché dans ce lot : ces lignes restent des affirmations de la Data API.

## Que permettent les horodatages sans fuite d'information ?

### Takeaway
Les transactions datées avant l'événement sont accessibles rétrospectivement, mais toutes les observations de ce lot ont été acquises le 30 octobre. Aucune n'était une observation enregistrée par cette collecte avant le premier signalement ou avant la cérémonie.

### Cited Findings
- Fenêtre économique : du 26 septembre 2026 à 20:00 UTC au 26 octobre à 20:00 UTC, borne droite exclue. Dans cette fenêtre, **15 067 lignes** précèdent le 23 octobre à 15:17:49 UTC ; **34 648 lignes** précèdent la cérémonie. Le lot comprend aussi 400 lignes antérieures à la borne basse et 11 485 lignes à partir de la cérémonie, conservées mais à exclure des calculs préalables. Ces effectifs sont un inventaire de lignes, pas une performance. [Validation des deux horloges](/Users/benjamindacunha/Projects/PolySentinel/studies/ballon_2026_20261030/data/collection_validation.json).
- `observed_at` et `actually_observed_at` sont la réception HTTP réelle. `timestamp` reste l'heure économique déclarée par l'API. Le compteur réellement observé avant chacune des deux bornes est **0** ; il ne faut pas remplacer la première horloge par la seconde pour simuler une preuve de détection passée. [Collecteur et contrôles](/Users/benjamindacunha/Projects/PolySentinel/studies/ballon_2026_20261030/code/col_historical.py).
- Les identifiants de marché et d'événement proviennent du catalogue courant. Leurs valeurs de liquidité, état ouvert/fermé, résultats et prix actuels ne sont pas transmises dans le ledger minimal. [Catalogue daté](/Users/benjamindacunha/Projects/PolySentinel/studies/ballon_2026_20261030/data/catalog_refreshed.json).

### Inferences
- On peut décrire les opérations historiques visibles et leur montant brut déclaré `size × price` ; cela n'établit ni l'inventaire initial, ni le capital net engagé, ni le PnL, ni une information privilégiée.
- Un classement de détection rétrospectif exigerait une hypothèse explicite de disponibilité historique et des métadonnées contemporaines vérifiées. Elles ne sont pas produites par ce lot.

### Gaps
- Pas d'archive contemporaine exhaustive des statuts ouverts, liquidités, catégories ou informations publiques à chaque instant.
- Pas d'historique complet inter-marchés par wallet, de positions d'ouverture ou de transformations de tokens.
- La borne du premier signalement a été transmise par l'équipe chargée des sources publiques ; aucun nom, wallet cité ou vainqueur n'a été lu pour choisir la population de collecte.

## Que garantissent les sources et les contrôles ?

### Takeaway
La provenance technique et les limites de pagination sont vérifiées. La fin d'une pagination taker n'est pas une preuve d'une histoire complète de tous les acteurs.

### Cited Findings
- La documentation officielle précise que le filtre événement/condition du flux `/v2/trades` dessert une fenêtre fixe de trois ans et ignore les bornes `start/end` ; le filtrage temporel est donc local. Les valeurs `size` sont des parts, les champs absents ne valent pas zéro. Le flux utilise des curseurs et n'exige pas de clé. [Documentation officielle Data API v2](https://data-api.polymarket.com/v2/docs).
- La collecte a demandé explicitement `taker_only=true`. Les participants uniquement maker ne sont pas couverts. La découverte Gamma et l'actualisation par identifiant suivent les endpoints publics ; l'événement regroupe plusieurs marchés. [Documentation de découverte](https://docs.polymarket.com/market-data/discover-markets), [paramètres exacts conservés](/Users/benjamindacunha/Projects/PolySentinel/studies/ballon_2026_20261030/data/requests.jsonl).
- Contrôles exécutés : dates UTC, séparation des deux horloges, montant, refus de nombres non finis/sens invalide/adresse invalide, refus de pagination manquante ; rapprochement de 31 catalogues et de chaque ligne normalisée aux bruts ; export final seulement après validation complète. Les données d'origine ont été préservées. [Code](/Users/benjamindacunha/Projects/PolySentinel/studies/ballon_2026_20261030/code/col_historical.py), [validation](/Users/benjamindacunha/Projects/PolySentinel/studies/ballon_2026_20261030/data/collection_validation.json).

### Inferences
- Le corpus permet un diagnostic documenté des données manquantes. Il ne fournit pas le dénominateur d'une précision/rappel ou d'un taux de faux positifs de la surveillance globale.

### Gaps
- Les fonctions de normalisation importent le code actif au moment d'une nouvelle exécution ; les sources exactes et leurs empreintes sont conservées pour provenance, tandis que le calcul doit lire la table minimale gelée. Aucun rejeu réseau ne doit être traité comme une reproduction du même instant.
- Aucune continuation, enquête de financement, acquisition d'identité civile ou analyse de performance n'a été effectuée par cet agent.
