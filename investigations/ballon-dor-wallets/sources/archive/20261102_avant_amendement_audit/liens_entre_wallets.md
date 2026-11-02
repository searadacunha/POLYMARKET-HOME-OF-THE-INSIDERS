# Liens entre les onze wallets

Extrait du rapport final. Un service commun ne relie personne, et aucune de ces lignes n'attribue deux wallets à un même propriétaire. Données : `graphs/links_classified.json`.


Une règle naïve de « financeur commun » relierait **21 paires sur 55**. Après classement, **0 paire** repose sur une adresse discriminante.

| Adresse partagée | Classe | Dossiers | Aussi chez les témoins | Pourquoi |
|---|---|---|---|---|
| `BmFdpraQhk…ymy6` | SERVICE_ETIQUETE | 0xdd97e6, cookedrice, ouldlm3alem, thin, vidente | token_oppose 1 | KuCoin Hot Wallet 2, selon orbmarkets.io |
| `0xc8a6871d…8d64` | SERVICE_MESURE | 0x86544e4dfde, brace227, kraben006, walletwallet8424, zoomman17 | meme_token 1, token_oppose 3, fraiches_recensement 1 | 215 sorties et 211 entrées en 3,75 h, un seul payeur |
| `0x4cd00e38…bc31` | SERVICE_ETIQUETE | brace227, kraben006, zoomman17 | non | Relay Depository, selon api.relay.link |
| `GxjcMTWWDc…nvBW` | SERVICE_MESURE | cookedrice, vidente | non | Environ 1,2 transaction par minute. Sur 120 transactions lues : 18 entrées, 95 sorties, 67 destinataires. Sur 400 tirées : 73 entrées, médiane 270 $,  |
| `0xee7ae85f…4055` | SERVICE_MESURE | ouldlm3alem, wen | token_oppose 1 | Polygon : 1 173 sorties vers 824 destinataires en 12 h autour du 18 oct. Arbitrum : 890 sorties vers 743 destinataires en 12 h autour du 26 oct. Appel |
| `0x0ce9bdf3…f06d` | SERVICE_MESURE | 0x86544e4dfde, walletwallet8424 | non | 85 sorties vers 57 destinataires en 3,8 h |
| `0xc1d13492…a1b5` | SERVICE_MESURE | brace227, kraben006 | non | 549 sorties vers 454 destinataires en 10 h |
| `0x58f298e3…0214` | SERVICE_MESURE | kraben006, zoomman17 | non | Nonce de 114 468 |

**Transferts directs.** Scan de 33 adresses (wallets, clés, adresses de pont, destinations), Polygon et Ethereum, stablecoins, pUSD et positions, depuis le 25 sept. : **0 transfert de fonds entre dossiers**. Une seule exécution de carnet d'ordres entre deux dossiers : OuldLm3alem vend 520,97 parts à 0,53 à 0x86544e4dfde, le 26 oct. 13:29:02 UTC, `0x870eaa6cb8298d7a02379b48093d4633af4f77ba58638bfc78ff9b0146f30b48`. C'est ordinaire sur un carnet. `graphs/direct_transfers.json`.

**Montant et heure.** 0 candidat entre une sortie et une entrée à 6 h et 90 à 100,1 %, sur 25 sorties et 46 entrées. Placebo à dates décalées : 0 aussi. `graphs/links.json`.

### Taux de base et faux positifs

Même lecteur sur un dépôt par wallet, 11 nommés et 50 comparateurs : `controls/funding_baseline_detail.jsonl`. L'échantillon est partiel : 6 non surlignés sur 6, 7 même token sur 10, 25 token opposé sur 27, 12 comptes frais sur 40. Le garde-fou disque a arrêté la collecte au réveil du Mac et elle n'a pas été prolongée, sur ta consigne d'utiliser les données déjà collectées. L'ordre de lecture ne dépend pas du résultat : adresses triées, tirage à graine fixe.

| Trait | Nommés | Non surlignés | Même token | Token opposé | Comptes frais du recensement | Tous témoins | p unilatéral, non corrigé |
|---|---|---|---|---|---|---|---:|
| Passage par KuCoin Hot Wallet 2 | 3/11 | 0/6 | 0/7 | 1/25 | 0/12 | 1/50 | 0,016 |
| Origine Solana | 3/11 | 0/6 | 0/7 | 2/25 | 0/12 | 2/50 | 0,037 |
| Contrat `0xc8a6…` | 5/11 | 0/6 | 1/7 | 3/25 | 1/12 | 5/50 | 0,012 |
| Relay | 11/11 | 4/6 | 3/7 | 16/25 | 11/12 | 34/50 | 0,024 |
| Adresse de pont 7702 | 6/11 | 4/6 | 2/7 | 14/25 | 11/12 | 31/50 | 0,789 |

Sur tous leurs dépôts, 5 nommés sur 11 passent par cette étiquette : 0xdd97e6, cookedrice, ouldlm3alem, thin, vidente. Ce chiffre ne se compare pas à la ligne du tableau, qui lit un seul dépôt. **KuCoin ressort donc plus souvent chez les nommés (3/11 contre 1/50, p ≈ 0,016 avant correction).** Face aux seuls comptes frais, l'écart tombe à 3/11 contre 0/12, p ≈ 0,093. Avec cinq traits regardés après coup, un groupe choisi par la presse et une étiquette à source unique, c'est un indice faible, sans aucune valeur de propriété commune : un exchange sert de très nombreux clients.

**L'âge explique une partie de ces écarts.** Relay vaut 11/11 chez les nommés et 11/12 chez les comptes frais : les comptes récents passent simplement par ce chemin.

**Faux positifs identifiés et écartés :**

- `0xc8a6…`, `0xee7a…`, `GxjcMTWW…`, `0x0ce9…`, `0xc1d1…`, `0x58f2…` : chacun relie plusieurs dossiers, et chacun se révèle mutualisé à la mesure. Tableau ci-dessus.
- La route `0xf70d… → 0xb92f… → 0xc8a6…`, signalée le 30 octobre comme « nature inconnue » entre brace227 et walletwallet8424 : c'est Relay et un contrat de passage, donc pas un lien.
- `GxjcMTWW…` : VidenteRibeira et cookedrice y déposent à un jour d'écart (51 489,00 USDT, 39 158,00 USDC). Service à 1 % de frais, payant par morceaux. Sur 400 transactions tirées, 2 entrées à 10 000 $ ou plus sur 73, médiane 270,38 $ : ces gros dépôts sont plutôt rares, sans que cela relie leurs auteurs. Les sorties ne s'apparient pas sans le registre du service.
- Part de 29 353 $ sur 30 398 $ d'achats côté Mbappé le 13 octobre par des comptes nommés : mécanique, puisqu'ils sont nommés parce qu'ils détenaient ce token.
- Pièges de lecture évités : nœud Solana rendant 0 signature pour une adresse payée, hash du pont introuvable sur sa chaîne, sondage récent de `0xee7a…` à 0 trafic. Ces trois faux zéros ont été recoupés.
