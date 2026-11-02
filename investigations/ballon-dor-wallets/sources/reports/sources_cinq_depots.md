# Cinq dépôts publics : ce qui est réellement utilisable

Lecture du 01/11/2026. Lecture seule, par `gh api` et par Jina pour les pages publiques d'Iris. Aucun clone, aucune installation, aucun code de ces dépôts exécuté, aucune clé, aucun compte. Aucune adresse de l'enquête n'a été envoyée à un service.

Seul calcul local : un keccak256 écrit à part pour recalculer les topic0 cités (contrôle positif sur `Transfer(address,address,uint256)` et sur la chaîne vide).

## Synthèse

| Dépôt | Licence | Dernier commit | Verdict |
| --- | --- | --- | --- |
| iris-intel-app/sdk-js | MIT, SDK seulement. Le moteur est fermé. | 2026-10-30 13:04 UTC | Client mince. Valeur = API distante, non testée ici. |
| SnowBar0v0/crosschain-fund-flow | Aucune | 2026-07-17 16:34 UTC | Bonnes règles d'arrêt. Aucune adresse ChangeNOW ou FixedFloat. |
| codebuster22/polymarket-wallet-triangulation | Aucune (confirmé) | 2026-07-31 08:13 UTC | Meilleure source de faits Polymarket. Faits oui, code non. |
| graphsense/graphsense-lib | MIT | 2026-11-01 09:30 UTC | Polygon absent. Inutilisable sur le coeur de l'enquête. |
| vsbtc/polymarket-insider-detection | MIT | 2026-07-16 23:18 UTC | Idée utile, implémentation fragile, ne voit pas pUSD. |

Ce qui change l'enquête :

1. **Aucune adresse de service ChangeNOW ou FixedFloat dans les cinq dépôts.** Recherche de code GitHub à 0 résultat sur quatre dépôts. SnowBar nomme ces services, sans une seule adresse, et renvoie à une session Arkham connectée.
2. **« Premier financeur » n'a plus de sens seul à l'ère pUSD.** Un dépôt arrive comme un mint pUSD depuis `0x0` (codebuster). Une méthode limitée à USDC.e et USDC, comme celle de vsbtc, ne voit pas ces dépôts.
3. **Beaucoup de premiers financeurs sont sans doute un solveur de bridge.** `0xf70da978…` finance en premier 131 des 346 wallets du CSV de vsbtc, et SnowBar l'étiquette solveur Relay. L'API Relay décrite par SnowBar (`/requests/v2?hash=`) peut donner l'origine. Non testée.
4. **Iris documente ChangeNOW et FixedFloat, mais par rapprochement de valeur.** Monero n'est pas couvert. Sur Polygon, `/trace` ne passe que par les services de swap.
5. **Le CSV de vsbtc est public et joignable localement**, sans réseau, avec les adresses de l'enquête (`wallet_onchain.csv`, `wallet_rankings.csv`).
6. **Une piste de vsbtc reste à regarder :** `0xf5042e6f…`, écarté comme « service » avec 69 destinataires, dont 28 sont des suspects de leur liste.

Consignes destinées aux agents, vues dans les dépôts et ignorées : `SKILL.md` de SnowBar, `CLAUDE.md` de codebuster (Bun), `README` de GraphSense (`claude plugin install`), page `/mcp` d'Iris (commande de connexion). Rien de malveillant dans ce que j'ai lu.

---

## A. iris-intel-app/sdk-js

**Licence :** MIT (`LICENSE`, `package.json`). Elle couvre le client seul.
**Dernier commit :** `258421d`, 2026-10-30T13:04:02Z.
**Maturité :** organisation GitHub créée le 2026-10-30, soit deux jours avant cette lecture. Trois commits, version 0.1.0, 0 étoile. Polygon est entré dans le SDK par le deuxième commit (« Follow the API on master: Polygon... »).

### Méthodes demandées

Authentification : `Authorization: Bearer iris_live_…`, ou variable `IRIS_API_KEY`. Base : `https://iriscan.app/api`. Tout passe par POST.

| Méthode | Paramètres | Réponse | Chaînes | Coût annoncé |
| --- | --- | --- | --- | --- |
| `analyze(address)` | `chain`, `depth` 1 à 10 000 (défaut 1 000) | `identity`, `risk`, `labels[]` avec `source` et `source_url`, `evidence[]`, `known_counterparties[]`, `flows`, `connections[]`, `meta` | Les 11 | 1 analyse, 2 au-delà de 1 000 tx. Gratuit avec clé si 25 tx ou moins |
| `follow(address)` | `chain`, `asset`, `since`, `maxHops` 1 à 50 (défaut 25) | `asset`, `hops[]` (`share`, `to_label`), `end.reason` | solana, EVM, bitcoin, tron | 2 analyses ou 2 crédits |
| `trace(wallet)` | Requis : `counterparty`, `signature`, `direction`, `time`, `sol`, `usd`. Optionnels : `window`, `chain`, `hops`, `counterpartyKind` | `entity`, `kind`, `method`, `anchor`, `window`, `anonymity_set`, `candidates[]`, `warnings[]`, `swap` | solana, EVM, bitcoin, tron | 1 trace ou 3 crédits |
| `traceTransfer(wallet, tx)` | `chain`, `counterparty`, `direction` | Comme `trace` | Comme `trace` | Comme `trace`. Refus avant débit si wallet ou tx invalide |
| `tx(hash)` | `chain` | `transfers[]`, `parties[]` (`category`, `label`, `entity`, `role`), `programs[]`, `bridge`, `fee_payer`, `signers` | Les 11 | Gratuit avec clé : 60 par minute, 100 par jour en gratuit |
| `xchainResolve(tx)` | `chain` | `links[]` : `bridge`, `status`, `direction`, `source`, `destination`, `hops`, `evidence`, plus `warnings[]` | Les 11 | Gratuit avec clé, 30 par minute |
| `xchainWallet(address)` | `chain` | Comme `xchainResolve` | solana, EVM | Gratuit avec clé, partagé |

Chaînes : solana, ethereum, base, arbitrum, robinhood, bsc, polygon, dydx, noble, bitcoin, tron.

### Crédits et limites

- Après un appel payant : en-tête `x-iris-credits`, exposé par `iris.lastCredits`.
- Limite d'appels : `X-RateLimit-Limit`, `-Remaining`, `-Reset`, exposés par `iris.lastRateLimit`.
- `GET /billing/account` et `GET /billing/usage/{days}` : documentés, absents du SDK. MCP : `get_credits`.
- Compte gratuit : 10 analyses et 2 traces, puis 3 analyses par jour, et **10 appels API par jour, routes gratuites comprises**.
- Plan Individual : 20 $ par mois, 500 analyses, 50 traces, 50 appels par 10 minutes. 3 requêtes simultanées au plus. Coupure à 2 minutes (504).
- Paiement crypto sans renouvellement. Sans clé, x402 en USDC sur Solana ou Base : `analyze` 0,05 $, `trace` 0,25 $, `follow` 0,10 $.

### Local ou distant

- **Local :** `riskSummary`, `planTrace` (choix de la contrepartie par expression régulière, listes `NATIVE` et `STABLE` qui incluent POL, WPOL et PUSD), devinette de chaîne, relances, en-têtes.
- **Distant et propriétaire :** étiquettes, identité, risque, `follow`, rapprochement `trace`, résolution des bridges. Rien de ce moteur n'est dans le dépôt.

### ChangeNOW, FixedFloat, XMR

Le SDK ne contient ni « ChangeNOW » ni « FixedFloat ». Il dit seulement `swap_service`. Ces noms viennent de la documentation publique.

**Documenté :**

- Services nommés : SideShift, ChangeNOW, FixedFloat, SimpleSwap, StealthEX, Exolix, Changelly.
- SideShift : correspondance exacte (`exact_feed`) par son registre public, lu toutes les 2 minutes.
- Les autres : `value_match`. Paiements des 30 minutes suivantes valant 0,3 à 3 % de moins, aux prix du moment.
- Recherche des paiements sur Solana, Ethereum, Base, Arbitrum, BNB Chain, Polygon, Bitcoin, Tron, là où Iris connaît des wallets du service.
- FixedFloat : liste des derniers swaps de sa page d'accueil, qui restreint la pièce et la chaîne quand le swap y figure.
- Une adresse de dépôt à usage unique compte comme le service si elle a balayé vers lui dans l'heure.
- **Polygon :** hors Solana, `/trace` ne passe que par un service de swap. Exchanges seulement sur Tron. Railgun, Tornado Cash et Privacy Pools seulement sur Ethereum, Arbitrum et BNB Chain.
- Bridges (`Trace bridge`) : Relay, Across, deBridge, Li.Fi, Mayan, Wormhole, CCTP, LayerZero, Stargate, THORChain, Chainflip, NEAR Intents et d'autres, lus dans leurs propres registres.

**Seulement affirmé, sans validation publiée :**

- `value_match` « about 80% right », « right about 4 times in 5 ».
- Bridges : « It's free, and it's certain ».
- « 640,000+ labeled addresses from 57 sources ». `/api/status` renvoie 648 715 et 57, avec `refresh: "skipped"`. C'est une auto-déclaration.
- Les scores de `confidence` et le score de risque.

**XMR : aucune couverture annoncée.** Pas de chaîne Monero dans le type `Chain`. Le seul passage cite Houdini Swap, « with Monero (or another chain) between them », traité par `hops: 2`, piste faible.

Déduction de ma part, non documentée : un swap vers XMR n'a pas de paiement visible. `value_match` peut donc rendre des candidats d'autres clients, de valeur voisine. Le lire avec `anonymity_set` et `warnings`.

### Pièges

- Sans `chain`, une adresse 0x est lue sur Ethereum. **Passer `chain: "polygon"` partout.**
- `/analyze` lit les transactions **les plus récentes**. Le premier financement d'un wallet actif peut sortir de `depth`.
- Sur EVM, `behaviors` et `balance_history` sont vides. Le verdict vient des étiquettes.
- `/follow` va seulement vers l'avant et prend le plus gros transfert. La documentation dit « a lead, not a proof ». Il ne remonte pas au financeur. Une piste coupée par le temps imparti reste facturée.
- `meta.scope: "database"` signifie étiquettes seules, rien lu on-chain.
- Prise en compte de pUSD côté serveur inconnue. La liste `STABLE` du SDK est locale.
- Les jetons ERC-1155 de position : couverture non documentée.
- Contradictions : `/developers` dit « 10 chains » et « Four routes », la doc en liste 11 et 9, le README 13. Le README dit `kind` utilisable sans clé, la doc dit 401 hors `/status`.
- `/tx`, `/chains`, `/kind`, `/xchain/*`, `/trace/transfer` ne figurent pas dans le tableau des routes de `/docs/api`. Ils ne sont décrits que par le SDK. Tests à fetch simulé, pas de fixture de réponse pour `follow`, `trace`, `tx`, `xchain`.
- Toute requête montre à Iris les adresses de l'enquête. C'est une décision de Benjamin.

**Réutilisable :** le schéma de réponse comme modèle (`anonymity_set`, `window.truncated`, `window.fallback`, tiers de délai), `planTrace` (MIT).
**Pas réutilisable :** le moteur, absent. Rien ne fonctionne sans clé ni paiement, hors `/status`.
**Adresses et événements :** aucun.

---

## B. SnowBar0v0/crosschain-fund-flow

**Licence :** aucune. `/license` répond 404, pas de fichier dans l'arbre, pas de mention dans `README.md` ni `SKILL.md`. Tous droits réservés par défaut.
**Dernier commit :** `a76e1f6`, 2026-07-17T16:34:17Z.
**Forme :** skill Codex avec exécuteurs Python, 0 étoile. Lus : `README`, `SKILL`, les références, `expand_crosschain_cluster.py` par extraits, `trace_bridge_order.py`.

### Méthode, décrite avec mes mots

- **Ordre :** les faits de transaction d'abord, puis les étiquettes, puis l'interprétation. En cas de conflit : chaîne, puis réponses d'API, puis texte d'explorateur, puis étiquettes, puis hypothèses.
- **Solana :** signatures du propriétaire et des comptes de jetons, écarts de soldes avant et après, attribution au propriétaire du compte de jetons, instructions internes. L'intention de la transaction est classée avant de créer une arête.
- **EVM :** transactions normales, ERC-20, internes, puis reçus et logs. `approve` et `permit` ne sont pas des flux. `transferFrom` en est un.
- **Bridges :** consulter le registre du bridge avant de déduire une destination depuis des transferts bruts. Sans registre, marquer le manque, ne pas deviner.
- **Rôle économique :** seules les arêtes directes entre wallets ajoutent du score. Swaps, pools, dépôts et remplissages de bridge, services, contrats et `unknown_complex` restent des preuves sans score.
- **Après atterrissage :** une seule couche par défaut.

### Frontières où l'on s'arrête

Exchange, adresse de dépôt, hot wallet, compte Hyperliquid, wallet ChangeNOW ou FixedFloat, noeud de service à forte fréquence mélangé, activité seulement interne à une plateforme. Étiquettes de statut utiles : `closed_to_cex`, `closed_to_platform_wallet`, `not_closed_high_frequency_fanout`, `not_closed_insufficient_api_coverage`, `bridge_orderbook_missing`.

### Registres cités (non appelés ici)

- Relay : `https://api.relay.link/requests/v2?user=<adresse>` et `?hash=<tx>`. Champs : `user`, `recipient`, `data.inTxs[]`, `data.outTxs[]`.
- Mayan : `https://explorer-api.mayan.finance/v3/swaps`.
- Gas.zip : `https://backend.gas.zip/v2/search/<hash>`, `/deposit/`, `/outbound/`, `/user/<adresse>`.
- deBridge : `/api/Transaction/<tx>/orderIds`, `/liteModels`, `/api/Orders/<id>`.
- THORChain : `https://gateway.liquify.com/chain/thorchain_midgard/v2/actions?txid=<tx>`.
- NEAR Intents : `https://explorer.near-intents.org/`.
- Dans Relay : 792703809 = Solana, 1337 = Hyperliquid. Polygon 137 figure dans les chaînes EVM par défaut.

### ChangeNOW et FixedFloat

**Aucune adresse.** Seuls éléments : le statut d'arrêt, et les identifiants d'entité Arkham `changenow` et `fixedfloat` (`references/bridge-orderbooks.md`), à utiliser avec une session Arkham connectée. Le dépôt dit ne pas supposer d'API officielle pour ces services.

### Adresses citées

Source : `references/bridge-orderbooks.md` et `references/robinhood-chain.md`, sauf mention. **Vérifiable : non en l'état.** Le fichier écrit « from prior sampling », sans transaction ni preuve.

| Service | Rôle annoncé | Adresse |
| --- | --- | --- |
| Relay | Solveur EVM | `0xf70da97812cb96acdf810712aa562db8dfa3dbef` |
| Relay | Dépositaire EVM | `0x4cd00e387622c35bddb9b4c962c136462338bc31` |
| Relay | Routeur candidat | `0x4337084d9e255ff0702461cf8895ce9e3b5ff108` |
| Relay | Routeur candidat | `0xccc88a9d1b4ed6b0eaba998850414b24f1c315be` |
| Relay | RouterV3, Robinhood Chain | `0xb92fe925DC43a0ECdE6c8b1a2709c170Ec4fFf4f` |
| Relay | Solana | `7uTT8Xi5RWXzy7h9XL244GRgEycDYDhLjr3ZyNdXi8pZ` |
| Relay | Solveur Solana | `F7p3dFrjRTbtRp8FRF6qHLomXbKRBzpvBLjtQcfcgmNe` |
| Across | SpokePool, Robinhood Chain | `0xD29C85F15DF544bA632C9E25829fd29d767d7978` |
| deBridge | EVM | `0x555ce236c0220695b68341bc48c68d52210cc35b` |
| deBridge | EVM | `0xe547d2eed6dd60796013b485d284c17da1194c82` |
| deBridge | Solana | `2snHHreXbpJ7UwZxPe37gnUNf7Wx7wv6UKDSR2JckKuS` |
| Gas.zip | Programme Solana | `FzuVV5WeLyWHDuX6SPbeLgqkvePDTzMCRKYAhDbiP3z3` |
| Gas.zip | Destinataire Solana | `gasZT2bpe7mxu5wMgQbvry84vok5CuF2huCEokyC3qh` |
| THORChain | Vault | `0x382d6d83a31a41a569ca45e6ca093036c2137d29` |
| THORChain | Routeur ETH | `0xD37BbE5744D730a1d98d8DC97c42F0Ca46aD7146` |
| THORChain | Routeur BSC | `0xb30ec53f98ff5947ede720d32ac2da7e52a5f56b` |
| THORChain | Routeur AVAX et Base | `0x00dc6100103BC402d490aEE3F9a5560cBd91f1d4` |
| NEAR Intents | EVM | `0x2CfF890f0378a11913B6129B2E97417a2c302680` |
| NEAR Intents | EVM | `0x233c5370CCfb3cD7409d9A3fb98ab94dE94Cb4Cd` |
| NEAR Intents | EVM | `0xbb2f33f73ccc2c74e3fb9bb8eb75241ac15337e0` |

Recoupement partiel : dans le CSV de vsbtc, `0xf70da978…` paie 6 409 destinataires et `0xb92fe925…` 380. Cela colle avec une infrastructure, sans prouver l'identité. Le chiffre de `0xb92fe925…` porte sur Polygon, alors que SnowBar l'étiquette sur Robinhood Chain.

### Écarts entre le dit et le code

- **Adresse fausse :** dans `KNOWN_EVM_SERVICE_ADDRESSES`, le RouterV3 est écrit `0xb92fe925dc43a0ecde6c8b1a2709c170ec4ff4f`, soit 39 caractères hexadécimaux au lieu de 40. Il n'est donc jamais reconnu par cette liste. Ne pas copier cette liste.
- **Fanout non codé :** la référence annonce −4 pour les noeuds à forte fréquence. Le script ne contient aucune détection, seulement deux phrases de rapport.
- **Barème partiel :** seuls +8, +7, +7, +5, +6, −5 et +6 sont appelés. Les lignes +3, +2 et −3 de la référence n'apparaissent pas dans les `add_score`.
- **Bridges :** le README cite Mayan, deBridge, THORChain, NEAR, ChangeNOW, FixedFloat. `trace_bridge_order.py` n'accepte que `relay` et `gaszip`. Le reste est décrit comme « future coverage ».
- **Filtre par sous-chaîne :** `gate`, `bot`, `pool`, `program` sont cherchés dans le texte des étiquettes. « aggregator » contient « gate » : faux positif service possible.

**Réutilisable comme principe :** priorité des preuves, registre avant déduction, arêtes économiques seules, statuts d'arrêt explicites, pas d'identité à partir d'un score.
**Pas réutilisable :** le code (pas de licence), la liste d'adresses comme vérité, le barème comme s'il était implémenté, le recours à une session Arkham sans accord de Benjamin.

---

## C. codebuster22/polymarket-wallet-triangulation

**Licence : aucune, le commanditaire a raison.** `/license` répond 404, pas de fichier dans l'arbre, aucune mention dans le README. `"private": true` dans `package.json` est un drapeau npm, pas une licence.
**Dernier commit :** `8513892`, 2026-07-31T08:13:40Z.

Je décris les méthodes. Les adresses et topic0 sont des faits publics, recalculables. L'implémentation n'est pas recopiée. Les constantes d'init code sont dans `docs/vendor/wallet-derivation.md`.

Attention au vocabulaire : ici **funder** = l'adresse qui détient et déplace l'argent. Chez vsbtc, **funder** = l'expéditeur du premier USDC.

### Résolution d'identité

**Classement d'une adresse par état :**

- Pas de code : EOA, ou funder pas encore déployé.
- Préfixe de clone EIP-1167 : PolyProxy. Implémentation attendue `0x44e999d5c2f66ef0861317f9a4805ac2e90aeb4f`.
- Préfixe ERC-1967 : Deposit Wallet.
- Slot 0 égal au mastercopy `0xe51abdf814f8854941b9fe8e3a4f65cab4e7a4a8` : Safe.

Piège reconnu par l'auteur : le préfixe ne vérifie pas l'implémentation. Seul un test d'activité élimine les faux positifs, et il ne doit jamais valoir « actif » sur erreur.

**D'un EOA vers ses comptes (jusqu'à 4 candidats à tester) :**

- L'EOA lui-même.
- Safe : vue `getSafeWalletAddress(address)` de l'exchange V2.
- PolyProxy : vue `getProxyWalletAddress(address)` de l'exchange V2, recoupée par la formule CREATE2. La vue l'emporte.
- Deposit Wallet : `eth_getLogs` sur la factory, topic0 `WalletDeployed`, topic2 = EOA. Sinon formule CREATE2, sensible à l'époque du contrat.

**Du compte vers l'EOA :**

- Safe : `getOwners()` (`0xa0e67e2b`), un seul propriétaire attendu.
- Deposit Wallet : `owner()` (`0x8da5cb5b`), ou topic1 de l'événement.
- PolyProxy : **pas lisible dans l'état**, le slot contient la factory. Passer par la transaction de création (GSN `relayCall`, premier paramètre = signataire, RelayHub `0xD216153c06E857cD7f72665E0aF1d7D82172F494`, sélecteur `0x405cec67`), ou dériver depuis un EOA candidat et comparer.

Intérêt direct : regrouper par EOA propriétaire est plus solide que par financeur partagé. Limite : selon l'auteur, Polymarket valide ce lien côté serveur et ignore les transferts de propriété du compte.

### Contrats (Polygon)

| Rôle | Adresse |
| --- | --- |
| USDC.e | `0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174` |
| USDC natif | `0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359` |
| pUSD | `0xC011a7E12a19f7B1f670d46F03B03f3342E82DFB` |
| CTFExchange V1 | `0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E` |
| NegRiskCtfExchange V1 | `0xC5d563A36AE78145C45a50134d48A1215220f80a` |
| CTFExchange V2 (bloc 84 902 353, 2026-03-31) | `0xE111180000d2663C0091e4f400237545B87B996B` |
| NegRiskCtfExchange V2 (bloc 85 058 176) | `0xe2222d279d744050d28e00520010520000310F59` |
| ConditionalTokens (ERC-1155) | `0x4D97DCd97eC945f40cF65F87097ACe5EA0476045` |
| NegRiskAdapter | `0xd91E80cF2E7be2e162c6513ceD06f1dD0dA35296` |
| CollateralOnramp | `0x93070a847efEf7F70739046A929D47a521F5B8ee` |
| CollateralOfframp | `0x2957922Eb93258b93368531d39fAcCA3B4dC5854` |
| Receveur de frais V2 (Safe) | `0x115f48dc2a731aa16251c6d6e1befc42f92accc9` |
| WrappedCollateral | `0x3A3BD7bb9528E159577F7C2e685CC81A765002E2` |
| Factory Safe | `0xaacFeEa03eb1561C4e67d661e40682Bd20E3541b` |
| Factory PolyProxy | `0xaB45c5A4B0c941a2F231C04C3f49182e1A254052` |
| Factory Deposit Wallet | `0x00000000000Fb5C9ADea0298D729A0CB3823Cc07` |

### Événements

**Les 15 topic0 ci-dessous ont été recalculés localement depuis la signature : 15 sur 15 correspondent.** Les signatures de ConditionalTokens et NegRiskAdapter ne sont pas écrites dans les fichiers lus. Je les ai reconstituées, et la correspondance les confirme.

| Événement | Émetteur | Signature | topic0 |
| --- | --- | --- | --- |
| TransferSingle | ConditionalTokens | `TransferSingle(address,address,address,uint256,uint256)` | `0xc3d58168c5ae7397731d063d5bbf3d657854427343f4c083240f7aacaa2d0f62` |
| TransferBatch | ConditionalTokens | `TransferBatch(address,address,address,uint256[],uint256[])` | `0x4a39dc06d4c0dbc64b70af90fd698a233a518aa5d07e595d983b8c0526c8f7fb` |
| OrderFilled V1 | Exchanges V1 | `OrderFilled(bytes32,address,address,uint256,uint256,uint256,uint256,uint256)` | `0xd0a08e8c493f9c94f29311604c9de1b4e8c8d4c06bd0c789af57f2d65bfec0f6` |
| OrderFilled V2 | Exchanges V2 | `OrderFilled(bytes32,address,address,uint8,uint256,uint256,uint256,uint256,bytes32,bytes32)` | `0xd543adfd945773f1a62f74f0ee55a5e3b9b1a28262980ba90b1a89f2ea84d8ee` |
| PositionSplit | ConditionalTokens | `PositionSplit(address,address,bytes32,bytes32,uint256[],uint256)` | `0x2e6bb91f8cbcda0c93623c54d0403a43514fabc40084ec96b6d5379a74786298` |
| PositionsMerge | ConditionalTokens | `PositionsMerge(address,address,bytes32,bytes32,uint256[],uint256)` | `0x6f13ca62553fcc2bcd2372180a43949c1e4cebba603901ede2f4e14f36b282ca` |
| PayoutRedemption | ConditionalTokens | `PayoutRedemption(address,address,bytes32,bytes32,uint256[],uint256)` | `0x2682012a4a4f1973119f1c9b90745d1bd91fa2bab387344f044cb3586864d18d` |
| PositionSplit | NegRiskAdapter | `PositionSplit(address,bytes32,uint256)` | `0xbbed930dbfb7907ae2d60ddf78345610214f26419a0128df39b6cc3d9e5df9b0` |
| PositionsMerge | NegRiskAdapter | `PositionsMerge(address,bytes32,uint256)` | `0xba33ac50d8894676597e6e35dc09cff59854708b642cd069d21eb9c7ca072a04` |
| PayoutRedemption | NegRiskAdapter | `PayoutRedemption(address,bytes32,uint256[],uint256)` | `0x9140a6a270ef945260c03894b3c6b3b2695e9d5101feef0ff24fec960cfd3224` |
| PositionsConverted | NegRiskAdapter | `PositionsConverted(address,bytes32,uint256,uint256)` | `0xb03d19dddbc72a87e735ff0ea3b57bef133ebe44e1894284916a84044deb367e` |
| Wrapped | pUSD | `Wrapped(address,address,address,uint256)` | `0xc00a5c84859ae82a7f5e6a2773283fb525335d5b3195f61174aa1ecc7e15dd84` |
| Unwrapped | pUSD | `Unwrapped(address,address,address,uint256)` | `0x18b42b684d0b621cc609f4d888916e5ed9e934a476259ec1c11ec116f2b9aa7f` |
| WalletDeployed | Factory Deposit Wallet | `WalletDeployed(address,address,bytes32,address)` | `0x7441de0ad639fe5d2bf1c22447715a0528b682385736bb40ae8dd92555eb8276` |
| ProxyCreation | Factory Safe | `ProxyCreation(address,address)` | `0x4f51faf6c4561ff95f067657e43439f0f856d97c04d9ec9070a6199ad418e235` |

OrderFilled : topics 1 à 3 = `orderHash`, `maker`, `taker`. Le frais est le mot de données d'index 4 dans les deux versions. Le log dont `taker` est l'exchange désigne l'ordre taker, et son champ `maker` est le wallet taker.

**Règle à garder : émetteur ET topic0, jamais le topic seul.** N'importe quel contrat peut émettre un log de même forme.

### Dépôts, retraits et ledger

- Toutes les transactions touchant les 3 collatéraux sont lues, du bloc 0 au bloc figé. Une ligne est classée **par transaction**, pas par contrepartie.
- Après pUSD, tout dépôt arrive comme mint pUSD depuis `0x0`, avec `Wrapped` : la contrepartie ne dit rien.
- Pas de reçu : `unknown`.
- Événement de protocole impliquant le funder : trade, redeem, split, merge ou convert.
- Sinon, delta net sur les 3 collatéraux dans la transaction :
  - net nul avec plusieurs jetons : conversion ;
  - net nul sur un seul jeton : inconnu ;
  - rabais et récompenses : par jointure avec `/activity` ;
  - net positif et jetons de position sortants : trade ;
  - net négatif et jetons de position entrants : trade ;
  - sinon positif : dépôt, négatif : retrait.
- Merge et redeem exécutés par un opérateur n'indexent pas le funder. On les attribue par la jambe ERC-1155 sortante du funder. Seule la sortie compte : une entrée peut être semée par un tiers.

### Rapprochement positions et soldes

- Tout est figé sur **un seul bloc**. Pas de fenêtre : une analyse partielle ne peut pas boucler.
- Positions : parcours des `TransferSingle` et `TransferBatch` dans les deux sens, par tranches, puis `balanceOf` (`0x00fdd58e`) par token au bloc figé.
- `sanity_diff` = cash réel moins somme du ledger. Non nul : corriger le parcours avant toute lecture.
- `residual_flows` = flux de trade on-chain moins cash net vendeur : mesure des trous du fournisseur.
- **Angle mort :** la valeur des positions et les récompenses figurent des deux côtés et s'annulent. Un résidu nul prouve que les vues concordent, pas qu'elles ont raison.

### Pièges

- `/value` a mesuré environ 115 fois trop haut sur un wallet. `/positions` a renvoyé `[]` sur un wallet avec du dust. Ne pas s'en servir pour un montant.
- `/positions` : marchés entièrement vendus absents, seuil par défaut d'environ 1 part.
- `usdcSize` inclut déjà le frais taker. Ne pas le soustraire deux fois.
- USDC.e et USDC renvoient tous deux le symbole `USDC` : distinguer par adresse.
- Avant le 2026-03-31, frais nuls. Falcon (clé, tiers) n'a rien avant le 2024-02-23 et manque des transactions (48 % sur un wallet surtout maker, n=15, à titre d'hypothèse).
- Lignes par funder. Sommer par propriétaire compte double sans neutraliser les transferts internes.
- **Le dépôt ne remonte pas à l'origine des fonds.** Un dépôt payé par un tiers ressemble à un dépôt personnel. La jambe d'origine reste à lire dans la même transaction.
- Plusieurs faits reposent sur des dépôts voisins `titus-*`, non lus. Le fichier demande de revérifier avant abonnement.
- Dépendances à clé : Alchemy `alchemy_getAssetTransfers`, Falcon.

**Réutilisable comme principe :** tout ce qui précède, réécrit de zéro.
**Pas réutilisable :** le code et les fixtures.

---

## D. graphsense/graphsense-lib

**Licence :** MIT (`LICENSE`), y compris `rust/gs_clustering`.
**Dernier commit :** `1b9ffc3`, 2026-11-01T09:30:52Z, release 2.20.2, projet actif, 21 étoiles.

**Polygon : non pris en charge.** `src/graphsenselib/config/config.py` fixe `supported_base_currencies = ["btc", "eth", "ltc", "bch", "zec", "trx"]`. La couche Spark n'a de profil compte que pour `eth` et `trx`. La recherche de code ne trouve « polygon » que dans `tagpack/constants.py`, comme vocabulaire d'étiquettes. Les 158 résultats pour « matic » n'ont pas été passés en revue. Il reste `lookup_address(include_cross_chain_addresses=True)` côté services, par relation de clé publique, sur les réseaux indexés.

### Structure

- Keyspaces Cassandra `raw` et `transformed` par réseau.
- Job Spark : graphe d'adresses et vues dénormalisées.
- TagStore PostgreSQL pour les étiquettes.
- Clusters : heuristique multi-entrées UTXO par union-find en Rust. Pas d'équivalent décrit pour le modèle compte.
- Conversions : décodeurs THORChain, Symbiosis, swaps DEX et CoW.

### Méthodes d'investigation (skill `trace-funds`, lisible et sous MIT)

- Une étiquette dit qui contrôle probablement, pas où est allé l'argent. Chaque saut vient d'un transfert.
- Rester au niveau adresse. Un cluster reste une inférence. Écrire « cluster », jamais « entité ».
- Prochain saut : suivre le montant et le temps, pas le plus gros volume. Ignorer moins d'environ 1 %. Sur un split, suivre le plus gros et lister le reste.
- Fin légitime : adresse de dépôt d'exchange, wallet saisi ou sanctionné, sorties vérifiées vides en citant l'appel. **Tout le reste est « non résolu ».**
- Un résultat vide prouve peu : retirer les bornes et les filtres inutiles, changer de listing avant de conclure.
- Une date nue passée en `max_height` exclut la journée entière.
- `identifier-integrity` : jamais d'adresse ou de hash de mémoire, jamais compléter une adresse tronquée.

### MCP pour Claude Code

- Monté dans l'app FastAPI, sur `/mcp`. 18 outils, 19 avec `search_neighbors`, service externe **propriétaire**.
- Plugin : `claude plugin marketplace add graphsense/graphsense-lib`, puis `claude plugin install graphsense@graphsense`. URL par défaut `https://api.iknaio.com/mcp/`, avec clé. **Rien installé ici.**

### Backend exigé

Cassandra plus TagStore PostgreSQL pour l'API. Sans TagStore, repli sur un faux TagStore, donc étiquettes vides. Remplir Cassandra suppose nœuds, ingestion et Spark. Hors de portée sur ce Mac, vu les règles de disque.

### Endpoint public

**Aucun endpoint sans clé documenté.** L'hébergé `https://api.iknaio.com` est présenté avec clé API. Un GET anonyme sur `/stats`, via Jina, a renvoyé une erreur 4xx dont je n'ai pas lu le statut exact. `GSREST_DISABLE_AUTH` ne vaut que pour son propre serveur.

**Réutilisable :** les règles de `trace-funds`, le vocabulaire « non résolu », la discipline de provenance.
**Pas réutilisable :** le graphe, pour Polygon. Utile seulement sur des sorties ETH, TRX ou BTC, avec une clé Iknaio.
**Pièges :** l'absence de ChangeNOW et FixedFloat dans le code ne dit rien des étiquettes du TagStore hébergé. Adresses et événements cités : aucun d'utile ici.

---

## E. vsbtc/polymarket-insider-detection

**Licence :** MIT (`LICENSE`).
**Dernier commit :** `b2e0fe4`, 2026-07-16T23:18:51Z, commit unique.
**Fichiers lus en entier :** `src/onchain.py`, `src/ring_trace.py`, `src/config.py`, `ring_funding_edges.csv`. `report.md` par extraits. Statistiques du CSV recalculées.

### Méthode et seuils exacts

- **Source :** Etherscan V2, `tokentx`, chaîne 137, sur `proxyWallet`.
- **Jetons :** `0x2791bca1f2de4661ed88a30c99a7a9449aa84174` et `0x3c499c542cef5e3811e1192ce70d8cc03d5c3359`. Rien d'autre.
- **Entrées :** 300 lignes au plus par jeton, ordre croissant, première page. Le premier transfert entrant donne `first_funding_ts` et `first_funder`.
- **Population :** tiers High et Medium, `top_n` 120 par défaut, 400 dans le README. Résultat publié : 346 wallets.
- **Service :** 50 destinataires distincts ou plus (`SERVICE_RECIPIENTS = 50`), sur `offset=10000`, ordre décroissant, par jeton. Liste tronquée à 10 000 : service d'office. Erreur : `n = 9999`, service d'office.
- **Exclusion :** uniquement par ce comptage. Pas de liste d'étiquettes, pas de test de contrat.
- **Cluster :** deux suspects ou plus avec le même premier financeur non-service.
- **Fraîcheur :** `clip((30 - jours_financement_avant_pari) / 30, 0, 1)`. Pari approché par `jump_time`. 0 si pas de données.
- **Score chaîne :** `s_chain = clip(0,6 x fraîcheur + 0,4 x cluster, 0, 1)`.
- **Score final :** `clip(base x pénalité + 0,15 x s_chain + 0,08 x s_exit, 0, 1)`. `base = 0,45 base_m + 0,12 repeat + 0,22 s_calib + 0,09 s_conc + 0,12 s_fresh`. Pénalité 0,65 si PnL réalisé négatif.
- **Tiers :** Low jusqu'à 0,30, Medium jusqu'à 0,45, High au-delà.
- **`ring_trace.py` :** 2 financeurs × 4 wallets codés en dur. `test_then_send` si minimum 5 $ ou moins et maximum 1 000 $ ou plus.

### Faiblesses

1. **La découverte de l'anneau n'est pas dans ces fichiers.** Les six adresses sont en dur. `onchain.py` ne donne que le groupe de 2. Le script ne peut pas trouver un septième wallet. Le rapport le présente comme une marche du graphe.
2. **Aucun hash de transaction** dans `ring_funding_edges.csv`. Le contrôle exige de tout refaire.
3. **Seuil de 50 en état actuel, avec regard vers le futur.** Un opérateur de 50 wallets ou plus passe pour un service. Un service récent passe pour personnel.
4. **Exemple dans leur CSV :** `0xf5042e6ffac5a625d4e7848e0b01373d8eb9e222`, classé service à 69 destinataires, est premier financeur de 28 des 346 suspects, soit 40 % de ses destinataires. USDC entrant cumulé de ces 28 wallets : 2,81 M$. Premiers financements du 2025-08-15 au 2026-02-19. Écarté sans examen. Nature inconnue.
5. **Panne déguisée en service :** 12 financeurs et 14 wallets portent `n = 9999`. Si Etherscan renvoie une limite de débit en texte, le parcours lève une exception et le financeur devient service. Cela efface des clusters en silence.
6. **Trafic déguisé en service :** 6 wallets ont un financeur classé service sous 50 destinataires (4 à 46), à cause de la troncature.
7. **Panne déguisée en absence :** 17 wallets sans financeur. Une erreur et « pas d'USDC » se confondent, et la fraîcheur tombe à 0. Cause exacte non vérifiée. L'ère pUSD peut en expliquer une part.
8. **Sélection sur l'issue :** les clusters ne sont cherchés qu'entre suspects déjà classés. Un financeur et ses wallets ordinaires restent invisibles.
9. **Premier financeur seul :** le rapport admet que cela ne capte que 2 des 6 wallets. Pas de recharge avant pari, pas de sortie commune, pas d'EOA propriétaire.
10. **pUSD, POL, USDT et jetons de position ignorés.** « Âge du wallet » = premier USDC reçu, pas la création. Calculé contre `time.time()`, donc non reproductible.
11. **Financement après le saut de prix :** jours négatifs, donc fraîcheur 1 après `clip`.
12. **Pas de suite après un bridge :** `0xf70da978…` (131 wallets) s'arrête là. `0x000…000` compte 3 wallets et 2 814 destinataires, sans doute des mints, à vérifier.
13. **Fait non commenté :** les deux financeurs envoient parfois les mêmes totaux aux mêmes wallets le même jour (3 000 et 3 000 vers #20 ; 2 500 et 2 500 vers #376 ; 1 500 et 1 500 vers #60 ; 3 000 et 2 208,89 vers #384). Aucune vérification des liens entre les deux financeurs. Le script ne l'examine pas.

### Adresses et étiquettes

Source : `src/ring_trace.py`, étiquettes de l'auteur. Pas d'étiquette de service dans ce dépôt.

| Adresse | Étiquette |
| --- | --- |
| `0x0700cb9b2504c30c55273c323f67faaa23a3267b` | financeur, xores63838 (#3, High) |
| `0x798c424639a08c19fac8e214a9f0322b86b47bca` | financeur, Vorp (#399, Low) |
| `0x0ad7f1a66e6b6df6f5ea21852e0ff5d3ad878ad2` | frais, #20 (High) |
| `0x8517b980e32611ed689e64c131e841a094002ce5` | frais, #60 (High) |
| `0xe48b94f6e8a3445a1f20a70a7ce88df171278260` | frais, #376 (Low) |
| `0x075220a3c7ef18d4c2efd466fa5627c79adbf5e8` | frais, #384 (Low) |

Financeurs les plus fréquents du CSV (sans nom dans le dépôt, classement de l'auteur) :

| Adresse | Wallets | Destinataires |
| --- | --- | --- |
| `0xf70da97812cb96acdf810712aa562db8dfa3dbef` | 131 | 6 409 |
| `0xf5042e6ffac5a625d4e7848e0b01373d8eb9e222` | 28 | 69 |
| `0x1929347e025d4f5f8d6b2bd2261e2f4efcacd215` | 18 | 3 077 |
| `0xf0fc40a635a907ac93924f2d8c36b3e87afef52e` | 17 | 3 110 |
| `0x56c262027e0de4aea31d2489529cb25d23e58a8b` | 13 | 15 174 |

Clusters personnels du CSV : `0x0700…267b` (2 wallets, 9 destinataires) et `0x8640a770436b418149544b37f1e156a095b9ce48` (2 wallets, 10 destinataires).

**Réutilisable :** distinguer service et personnel en comptant sur tous les jetons, le motif « petit test puis mise », le CSV comme point de comparaison.
**Pas réutilisable :** la présence dans leur classement comme preuve, leur seuil tel quel, leur âge de wallet. Le README précise lui-même : indicateur, pas preuve. Le classifieur repose sur un modèle de langage.

---

## Requêtes Iris à poser si une clé existait

Classées par information par crédit. Une clé gratuite donne 10 appels par jour et 2 traces de départ, sans recharge annoncée : garder les traces pour la fin. Toujours `chain: "polygon"` sauf cas contraire. Noter à chaque appel `lastCredits`, et selon la route `meta.scope`, `meta.data_completeness`, `window.truncated`, `window.fallback`, `warnings`. Accord de Benjamin requis avant d'envoyer une adresse de l'enquête.

| Rang | Gabarit | Coût | Gain attendu |
| --- | --- | --- | --- |
| 1 | `xchainResolve("<tx de premier financement>", { chain: "polygon" })`, quand l'expéditeur est un solveur ou un bridge | Gratuit | Wallet et chaîne d'origine, avec la source du lien. Transforme un solveur en personne ou en wallet |
| 2 | `xchainWallet("<EOA ou compte>", { chain: "polygon" })` | Gratuit | Tous les transferts de bridge entrants et sortants. Peut relier deux comptes par une origine commune |
| 3 | `tx("<tx de financement ou de sortie>", { chain: "polygon" })` | Gratuit | `parties[]` avec `category`, `label`, `entity`. Moyen le plus sobre de voir si un wallet est étiqueté ChangeNOW ou FixedFloat. Vérifier aussi `fee_payer` et `signers` |
| 4 | `analyze("<premier financeur inconnu>", { chain: "polygon", depth: 1000 })` | Gratuit si 25 tx ou moins, sinon 1 | `labels[].source` et `source_url` à vérifier ailleurs, `known_counterparties[]`, `connections[]`. Peut donner des adresses de service avec leur source |
| 5 | `traceTransfer("<wallet>", "<tx reçue d'un service>", { chain: "polygon", direction: "in" })` | 1 trace | Dépôts candidats en amont, toutes chaînes. Lire `method`, `swap.matched`, `swap.deposit`, `anonymity_set`. Attendre `value_match` ou `exact_feed` selon le service |
| 6 | `traceTransfer("<wallet>", "<tx envoyée à un service>", { chain: "polygon", direction: "out" })` | 1 trace | Sorties candidates. `candidates[].chain`, `asset`, `delta_seconds`, `tier`. Résultat vide ou incohérent compatible avec une sortie en XMR, sans le prouver |
| 7 | `follow("<wallet>", { chain: "polygon", asset: "<contrat USDC.e, USDC ou pUSD>", since: <ts> })` | 2 analyses | Chaîne de sortie jusqu'à `end.reason`. Tester si pUSD est suivi |
| 8 | `chains("<EOA>")` | Gratuit | Autres chaînes EVM actives et `pick`. Une même clé peut y agir, mais le lien reste à prouver. Un contrat à la même adresse n'est pas le même wallet |
| 9 | `trace("<wallet>", { counterparty, signature, direction: "out", time, sol, usd, chain: "polygon", hops: 2 })` | 1 trace | Route via deux services (Houdini Swap). Piste faible, seul accès annoncé à un passage possible par Monero |

Tout résultat de `trace` reste une piste. Exiger une preuve indépendante avant de lier deux wallets : financeur commun, même propriétaire, mêmes contreparties.

---

## Non vérifié

**Iris**
- Aucun appel avec clé. Toutes les réponses viennent des types du SDK et de la doc, pas d'un essai.
- Comportement réel sur Polygon, traitement de pUSD et de l'ERC-1155.
- Nombre de wallets ChangeNOW et FixedFloat connus sur Polygon.
- Taux de 80 % et « certain » pour les bridges : aucune validation publiée trouvée.
- `/docs/api/xchain` et `/docs/api/tx` ont renvoyé une erreur 4xx via Jina. Ces routes reposent sur le SDK seul. Il peut exister d'autres chemins de doc.
- Dépôts `sdk-python` et `iris-guard` non lus.

**Adresses**
- Toutes les attributions de SnowBar (« prior sampling »).
- `0xf70da978…` = solveur Relay : une seule source, plus une cohérence de fanout.
- `0xb92fe925…` : routeur Relay sur Robinhood Chain selon SnowBar. Même rôle sur Polygon non vérifié.
- Adresses de contrats de codebuster : non contrôlées on-chain par moi. Seuls les topic0 l'ont été.
- Nature de `0xf5042e6f…`, et sens des montants identiques de l'anneau vsbtc.

**Méthodes**
- API Relay, Mayan, Gas.zip, deBridge, THORChain : aucune appelée.
- Date de début de pUSD : non donnée dans les fichiers lus. Seule la V2 est datée, le 2026-03-31.
- Résultats de vsbtc (rangs, p-valeurs, recoupements) : non reproduits. Seuls les comptages de `wallet_onchain.csv` sont recalculés.
- La cause exacte des 17 wallets sans financeur.

**Couverture de lecture**
- codebuster : `run.ts`, `fees.ts`, `positions/value.ts`, plans et sondes non lus. Sections de README lues par extraits.
- vsbtc : `score.py`, `enrich_wallets.py` non lus, ainsi la découverte de l'anneau pourrait être ailleurs dans le dépôt, sans que je l'aie vue.
- SnowBar : `expand_crosschain_cluster.py` lu par extraits et par recherche, pas intégralement.
- GraphSense : `CLAUDE.md`, `tools/consolidated.py` et le service `search_neighbors` non lus. Absence de Polygon établie par `config.py`, `NetworkDefaults.scala` et une recherche de code dont l'index peut retarder.
- Recherche de code « changenow » et « fixedfloat » : index GitHub, branche par défaut, pas une lecture de chaque fichier. Pour SnowBar, comptage sur les fichiers téléchargés.
- `api.iknaio.com/stats` : statut exact non lu. Offre commerciale d'Iknaio non lue.

**Sources web lues le 2026-11-01 via Jina (heure UTC, empreinte tronquée fournie par l'outil)**
- `iriscan.app/developers`, 22:31:32, `5335598a00c179f5`
- `iriscan.app/pricing`, 22:31:36, `a740f398fd2df85f`
- `iriscan.app/mcp`, 22:33:23, `d94942bdf1777be2`
- `iriscan.app/docs/api/trace`, 22:34:25, `1adaad9347b51469`
- `iriscan.app/docs/api/follow`, 22:34:28, `44324949ee3ccdbb`
- `iriscan.app/docs/api/errors`, 22:34:32, `1f6dd7d22dabc636`
- `iriscan.app/docs/api/x402`, 22:34:35, `490183feb7c3cbaf`
- `iriscan.app/docs/explorer/tracing`, 22:35:17, `a57aee0d3b821a65`
- `iriscan.app/docs/api/analyze`, 22:35:23, `aa1be76c15e5796a`
- `iriscan.app/docs`, 22:35:26, `f4e18f836e27536d`
- `iriscan.app/docs/chains`, 22:39:13, `0da89e36bbc149a1`
- `iriscan.app/docs/api/mcp`, 22:39:18, `a17b9c474c1bc18e`
- `iriscan.app/api/status`, 22:39:19, `f2f983e80db0d6bd`
- `iriscan.app/docs/api`, 22:33:20, `6940b87b40111979`
