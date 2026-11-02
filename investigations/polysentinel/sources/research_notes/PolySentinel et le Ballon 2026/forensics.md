# Ballon d’Or 2026 ; vérification forensique exploratoire de six comptes publics

## Que prouvent les montants reconstruits ?

### Takeaway
Six transactions choisies après connaissance des labels publics sont réconciliées avec leurs reçus Polygon : les débits pUSD comprennent des frais en plus du produit taille×prix. Ces six montants prouvent des mouvements précis ; ils ne mesurent ni l’investissement total, ni le capital net à risque, ni un profit. [Sortie T3](forensics/summary.json), [réconciliation économique T3b](forensics/funding_routes_and_amounts.json).

### Cited Findings
- La sélection retient le premier trade reconstructible par wallet dans le jeu historique gelé, strictement avant le 23/10/2026 à 15:17:49 UTC. Elle porte sur les six rapprochements exacts avec des alias actuellement exposés par l’API officielle, dont la continuité historique n’est pas démontrée. Il s’agit d’un échantillon conditionné par les signalements publics, constitué après T1/T2 ; aucune mesure de précision ou de rappel ne peut en être tirée. [Plan écrit avant collecte](forensics/PLAN.md), [sélection](forensics/selection.json), [labels et limites](labels_after/labels.json).
- Pour chacun des six trades : reçu réussi, bloc canonique, timestamp identique au trade API, confirmations supérieures à 128, réconciliation `matched` avec le code de production copié à l’identique. Le contrôle hors ligne rapproche les unités entières des frais collateral et du transfert ERC20 pUSD. Le produit API taille×prix peut porter une erreur d’arrondi du prix ; le nominal issu du log est exact à six décimales. [Bruts et contrôles](forensics/summary.json), [code hors ligne](forensics/inspect_saved_receipts.py), [ABI officielle](https://github.com/Polymarket/ctf-exchange-v2/blob/main/src/exchange/interfaces/ITrading.sol).

| Alias public | Trade retenu (UTC) | Parts | Nominal pUSD | Frais pUSD | Débit pUSD vérifié | Reçu |
|---|---|---:|---:|---:|---:|---|
| walletwallet8424 | 15/10/2026 19:43:25 | 520.75 | 260.375000 | 6.509370 | 266.884370 | [Polygon](https://polygonscan.com/tx/0xf40fcaa9c633bdee520ec2f02d442a1a6909c6c004addcfe935bc8ab54bc2e45) |
| VidenteRibeira | 16/10/2026 00:27:24 | 6383.99 | 3379.405800 | 79.524780 | 3458.930580 | [Polygon](https://polygonscan.com/tx/0x76b9f0c980716eadaef62144e3bfe598c34c3415b2384a020916c635a5178979) |
| OuldLm3alem | 22/10/2026 18:49:30 | 832.99 | 581.093000 | 8.786150 | 589.879150 | [Polygon](https://polygonscan.com/tx/0x011b6b966fd5fb174b528d3ef06e6542bb4f86c959f92c79d7add156a3577128) |
| brace227 | 09/10/2026 20:50:04 | 300.0 | 120.000000 | 3.600000 | 123.600000 | [Polygon](https://polygonscan.com/tx/0x4561cf17ea6112101ac40a3de412461ccc2a09d1ec25d4840e490b23f5da2e1e) |
| WenZhuanBuPei | 18/10/2026 20:16:17 | 23079.37 | 12772.993300 | 285.196860 | 13058.190160 | [Polygon](https://polygonscan.com/tx/0xbe6c81c1d9ea65e02508e90bc896b0a2e9592512b2b56394abc8686c53cfb5c7) |
| Thin-Disclaimer-Life | 12/10/2026 00:16:03 | 1651.08 | 871.295400 | 20.575100 | 891.870500 | [Polygon](https://polygonscan.com/tx/0xf5424b77e7c4413b16be5e4f4304938743c0d12edfafb06bf7cfa0d6a8167e99) |

Sources locales de chaque cellule : [six réconciliations économiques avec hashes et logIndex](forensics/funding_routes_and_amounts.json). Les liens Polygon rendent chaque transaction identifiable ; la preuve collectée est le reçu RPC brut archivé, pas une interprétation de l’explorateur.

### Inferences
- Pour ces six transactions seulement, le nominal onchain augmenté des frais collateral est exactement égal au débit pUSD du wallet vers l’exchange. Les éventuelles compensations/rebates ultérieurs et les frais de gas ne sont pas inclus. Le rôle de l’expéditeur de la transaction ou de l’exchange n’établit pas qui finance économiquement le wallet. [Réconciliation T3b](forensics/funding_routes_and_amounts.json), [limites du parseur conservées](forensics/chain_vendor.py).
- L’écart entre parts, nominal, débit et financement explique pourquoi une capture de positions en « shares » ne peut pas être lue directement comme des dollars engagés. Les totaux API issus de l’échantillon historique censuré de l’étude restent des sommes de lignes disponibles ; ce contrôle de six reçus ne les transforme pas en capital total. [Données de sélection](forensics/selection.json), [analyse de la capture publique](public_case.md).

### Gaps
- Les transformations SPLIT/MERGE/CONVERSION, toutes les entrées/sorties ERC1155 et collateral, les inventaires initiaux, toutes les ventes, redeem, remises et autres wallets éventuels ne sont pas reconstruits. Ni montant maximal à risque, ni position historique complète, ni PnL réalisés ne sont établis. Un dépôt n’est pas nécessairement entièrement investi sur ces marchés. [Portée fixée](forensics/PLAN.md), [champs explicitement inconnus](forensics/summary.json).

## Y a-t-il un financement commun ?

### Takeaway
Les six dépôts sélectionnés sont confirmés sur chaîne. Deux présentent la même route intermédiaire USDC.e avant émission de pUSD ; la nature de ces intermédiaires et le financeur économique restent inconnus. La route commune est un lien observé, pas une preuve de contrôle commun ou d’information privilégiée. [Transferts intégraux des reçus sélectionnés](forensics/funding_routes_and_amounts.json).

### Cited Findings
- Une requête historique DEPOSIT/WITHDRAWAL/TIP avant le premier trade sélectionné a fourni au moins un dépôt par wallet. Le dépôt le plus récent de chaque page a reçu un contrôle reçu+bloc canonique. Chacun contient un transfert pUSD depuis l’adresse zéro vers le wallet : c’est l’émission du token, et l’adresse zéro n’est pas un financeur. La documentation décrit le wrapping USDC.e→pUSD et permet un bénéficiaire différent de l’appelant. [Six reçus](forensics/summary.json), [documentation pUSD](https://docs.polymarket.com/concepts/pusd).

| Alias | Dépôt retenu (UTC) | pUSD reçus | Reçu |
|---|---|---:|---|
| walletwallet8424 | 13/10/2026 18:19:48 | 3906.988140 | [Polygon](https://polygonscan.com/tx/0xd6c102f7e3eed462f41e9d9eb96bee66d07b81ff0dec9ecd55e15f7aef83fa34) |
| VidenteRibeira | 15/10/2026 21:06:54 | 9940.006803 | [Polygon](https://polygonscan.com/tx/0xcb790208996b569b3671f4d5090acae8ca22eff2a3cec6029b8aeee2081aa2d1) |
| OuldLm3alem | 22/10/2026 18:39:23 | 23386.255984 | [Polygon](https://polygonscan.com/tx/0xaed3dd931c9bbc163818983c01b6ebc43cb3885f43dcb18359d3651e7f5fe4dd) |
| brace227 | 09/10/2026 20:49:05 | 2186.427015 | [Polygon](https://polygonscan.com/tx/0x2a89597ebf1d83b5b76ceccab02924c28ca0ad8f6d208b2c42801a0925280a2c) |
| WenZhuanBuPei | 18/10/2026 20:14:27 | 15926.884500 | [Polygon](https://polygonscan.com/tx/0x45c27719b34b5490a620b319911db190d6570bc1b0e2da3782d5bbb8c4cc2da3) |
| Thin-Disclaimer-Life | 11/10/2026 15:23:31 | 11833.228666 | [Polygon](https://polygonscan.com/tx/0x761f6058829482bc5fc66acd8b6d5bcc583e96a463ac75e52d666b31fd6f32d1) |

- Pour **walletwallet8424** et **brace227**, les reçus affichent la même chaîne USDC.e : `0xf70da97812cb96acdf810712aa562db8dfa3dbef` → `0xb92fe925dc43a0ecde6c8b1a2709c170ec4fff4f` → `0xc8a6871d4ec4dae64f605db0f8a0b3d9ef928d64` → contrat pUSD `0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb`. Un auto-transfert de b92… apparaît aussi. Les montants sont respectivement 3906,988140 et 2186,427015 USDC.e ; chaque bénéficiaire reçoit autant de pUSD. Les dépôts datent des 13 et 9 octobre, donc ce lien existait avant le premier signalement retenu. [Reçu walletwallet](https://polygonscan.com/tx/0xd6c102f7e3eed462f41e9d9eb96bee66d07b81ff0dec9ecd55e15f7aef83fa34), [reçu brace](https://polygonscan.com/tx/0x2a89597ebf1d83b5b76ceccab02924c28ca0ad8f6d208b2c42801a0925280a2c), [logs complets archivés](forensics/funding_routes_and_amounts.json).
- Dans les quatre autres reçus, les sources USDC.e immédiates vers le contrat pUSD sont distinctes : Vidente `0x6d24d9452f900f3307cd5b791ffaf1d1a7476df8`, Ould `0xb3afcdc711378d17ca1a1000770af5a0b78bb0ba`, Wen `0x315ac6e73410faafd02edac1b1a46da7b90814c5`, Thin `0x8e43af995577339436e071990e524ebfe6c09865`. Cela ne prouve pas leur indépendance plus en amont. Les six reçus montrent ensuite un flux USDC.e du contrat pUSD vers `0xc417fd8e9661c0d2120b64a04bb3278c17e99db1` ; cet endpoint commun appartient au mécanisme de ces dépôts observés, sans établir un donneur d’ordre commun. [Logs ERC20, hashes et indices](forensics/funding_routes_and_amounts.json).
- Le parseur de production `transfers(receipt,wallet,contracts)` filtre les transferts touchant le wallet cible. Sur ces dépôts, ce filtre ne montre que le mint pUSD et masque la route USDC.e amont. Le complément réutilise le parseur depuis toutes les extrémités présentes et déduplique par transaction/logIndex, sans changement du code de production et sans nouvelle requête. [Code de production copié](forensics/chain_vendor.py), [extension hors ligne](forensics/inspect_saved_receipts.py), [amendement exploratoire après observation](forensics/ADDENDUM_OFFLINE.md).

### Inferences
- Un même service d’acheminement, de bridge, de dépôt ou un même opérateur économique peut produire une route partagée. Aucune de ces explications n’est identifiée ici : les adresses n’ont pas reçu d’étiquette de service validée et leurs entrées antérieures n’ont pas été remontées. La qualification permise est « route intermédiaire partagée, nature inconnue ». [Portée et avertissements T3b](forensics/funding_routes_and_amounts.json), [architecture de wrapping permettant un bénéficiaire distinct](https://docs.polymarket.com/concepts/pusd).

### Gaps
- Financements en amont de la transaction retenue, contrôle des adresses intermédiaires, rapprochements inter-chaînes, tous les autres dépôts et transferts, bénéficiaire économique et identité réelle : inconnus. Une adresse de règlement, de bundler/relayer ou de garde partagée ne suffit pas à résoudre ces inconnues. [Plan borné](forensics/PLAN.md), [sortie avec contrôle commun null](forensics/funding_routes_and_amounts.json).

## Quelle couverture historique et quelle validité pour cette vérification ?

### Takeaway
La collecte a obtenu une page d’activité épuisée par wallet avant la coupure publique, mais l’exhaustivité de l’indexeur ne prouve pas celle de la chaîne. Aucun portefeuille actuel n’est assimilé à une position historique. Les résultats sont descriptifs et exploratoires ; le détecteur gelé et ses verdicts n’ont pas été recalculés par ce complément. [Journal des requêtes](forensics/requests.jsonl), [plan](forensics/PLAN.md).

### Cited Findings
- Requêtes d’activité `start=1`, `end=cutoff−1`, ordre ASC, limite 250 et dépôts/retraits inclus ; recherche de financement séparée, ordre DESC, avant le premier trade sélectionné. La documentation expose les paramètres temporels, les types d’activité et une pagination par curseur. Les pages retournées n’ont pas de continuation. Ce sont des réponses observées le 30 octobre, pas des captures disponibles en temps réel à la date des trades. [Requêtes exactes et heures de collecte](forensics/requests.jsonl), [documentation activité](https://docs.polymarket.com/api-reference/feeds/list-account-activity).

| Alias | Lignes API activité | Dont TRADE | Dont DEPOSIT | Pagination API |
|---|---:|---:|---:|---|
| walletwallet8424 | 35 | 27 | 3 | épuisée |
| VidenteRibeira | 11 | 6 | 2 | épuisée |
| OuldLm3alem | 62 | 59 | 1 | épuisée |
| brace227 | 110 | 96 | 8 | épuisée |
| WenZhuanBuPei | 6 | 3 | 1 | épuisée |
| Thin-Disclaimer-Life | 67 | 58 | 3 | épuisée |

Sources de ces dénominateurs : [résumé des pages](forensics/summary.json), réponses brutes référencées par [requests.jsonl](forensics/requests.jsonl). Les types autres que TRADE/DEPOSIT sont notamment récompenses, rebates et un retrait ; toutes ces lignes ne sont pas des transactions d’achat.

- La collecte automatisée totalise 38 requêtes et 38 réponses, 0 erreur et0 HTTP429, pour 695718 octets bruts ; les six reçus de trades et six reçus de dépôts sont disponibles. Les sept tests existants `tests.test_chain` ont passé avant la collecte ; les auto-contrôles du collecteur et de l’extension hors ligne ont passé. [Résumé et compteurs](forensics/summary.json), [validation locale](forensics/validation.json), [journal d’exécution](forensics/execution.log), [auto-contrôle hors ligne](forensics/funding_routes_and_amounts.json).
- T3 a été enregistré avec n=6, n_effectif=1, six comparaisons descriptives ; l’extension T3b avec n=6, n_effectif=1, douze comparaisons descriptives (six routes et six égalités économiques). Les deux sont déclarés hors plan, exploratoires et sans p-value. Les sorties enregistrées sont `summary.json` et `funding_routes_and_amounts.json`. [Registre officiel](../../studies/ballon_2026_20261030/registre/tests.jsonl), [addendum](forensics/ADDENDUM_OFFLINE.md).
- Les empreintes des sources de code, configuration, données gelées et labels sont conservées ; l’extension et les bruts sont indexés par le manifeste final. [Sources](forensics/sources.json), [manifeste](forensics/manifest.json).

### Inferences
- Les pages d’activité offrent des pistes pour enrichir une future reconstruction systématique incluant makers, dépôts et transformations. Les explorer uniquement pour les comptes déjà nommés ne permet pas d’améliorer rétroactivement une mesure de détection ni d’estimer les faux positifs. [Sélection conditionnée](forensics/PLAN.md), [documentation des types d’activité](https://docs.polymarket.com/api-reference/feeds/list-account-activity).

### Gaps
- Pas d’inventaire exact ni de graphe complet de financement, pas d’étiquetage établi des intermédiaires, pas d’échantillon indépendant représentatif et pas de recherche d’autres wallets. La continuité historique des alias demeure non prouvée. Cette dernière passe clôt la collecte dans les limites annoncées ; les éléments manquants restent explicitement non vérifiés. [Labels](labels_after/labels.json), [plan](forensics/PLAN.md), [sortie T3](forensics/summary.json).
