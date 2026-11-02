# Règles exploratoires — exploratory-1.1

Le score compte des **familles de phénomènes observés**. Ce n'est ni une probabilité, ni un résultat calibré, ni une qualification juridique. Les candidats ayant un seul phénomène sont conservés pendant l'apprentissage. `priority=true` nécessite un score au moins égal à `candidate_score` (2 par défaut), un marché/événement explicitement ouvert et aucune publication du résultat connue. La qualité documentaire reste « données insuffisantes » tant que la première disponibilité publique est inconnue, même pour un candidat prioritaire au sens du tri technique.

## Temporalité et unités d'observation

`evaluate(trades, markets, events, now=..., config=...)` est une fonction pure. Une transaction n'entre que si son heure **et** sa première observation sont au plus `now`. Les métadonnées observées après `now` sont exclues. On peut fournir plusieurs snapshots du même marché/événement : les comparaisons de liquidité utilisent le dernier snapshot observé **avant la transaction**, vieux de 30 minutes au maximum. Le dernier snapshot connu à `now` détermine seulement le statut actuel. Les références du portefeuille portent sur les groupes terminés avant le premier fill du groupe cible.

Un groupe est `(wallet, token, sens, order_hash)` si l'ordre est prouvé ; sinon `(wallet, token, sens, transaction_hash)`, puis l'identifiant de ligne si aucun hash n'existe. Un ordre contenant plusieurs transactions conserve toutes leurs références. Le montant et les parts sont additionnés, le prix est pondéré par les parts, les frais ne sont additionnés que si tous sont connus dans la même unité. Des ID dupliqués sont dédupliqués ; une contradiction économique sous le même ID fait échouer explicitement l'analyse. Le groupement ne déduit jamais le sens du taker à partir du maker et ne confond jamais deux tokens complémentaires.

Le flux global est filtré par taille, contrairement aux marchés suivis en détail. Les effectifs et concentrations concernent donc **l'union effectivement collectée**, pas tout le portefeuille ni toute la plateforme. L'âge d'une adresse et son inventaire initial restent inconnus. Les seuils de cohortes ne corrigent pas cette sélection.

## Conditions et références

| Règle | Condition exploratoire | Référence / effectif | Famille comptée |
|---|---|---|---|
| `first_observed_large` | Premier groupe observé sans groupe antérieur, achat ≥ `large_nominal` (1 000 par défaut) | 0 groupe antérieur accessible ; âge réel inconnu | exposition |
| `event_concentration` | Au moins 80 % des achats collectés sur les dernières 24 h sur cet événement, nominal ≥ 1 000 | Nominal événement / nominal portefeuille collecté ; nombre de groupes d'achat | exposition, une seule fois avec la règle précédente |
| `wallet_size_shift` | Achat ≥ max(1 000, 5 × médiane, médiane + 6 × 1,4826 × MAD) | Achats antérieurs du même portefeuille ; au moins `minimum_baseline` (20) groupes | taille |
| `liquidity_fraction` | Achat ≥ 10 % de la liquidité Gamma observée avant le trade, et ≥ 1 000 | Un snapshot ≤ 30 min ; liquidité Gamma, **pas** profondeur exécutable | taille, une seule fois |
| `cohort_size` | Même seuil robuste que ci-dessus | Au moins 20 groupes antérieurs d'autres wallets : catégorie, tranche de prix de 0,20, ordre de grandeur du délai à échéance, de la liquidité et de l'ancienneté observée | taille, une seule fois |
| `specialization_shift` | Achat ≥ 1 000 dans une catégorie absente des références connues | Au moins 20 groupes antérieurs et leurs catégories contemporaines toutes connues | rotation |
| `linked_market_rotation` | Achat ≥ 1 000 sur au moins deux marchés nouveaux du même événement en 24 h, avec des marchés antérieurs observés | Marchés précédents et nouveaux listés ; même événement Gamma seulement | rotation, une seule fois |
| `synchronized_entries` | ≥ 3 wallets, même événement/marché/token, achats ≥ 250, dans 90 s | Au moins une transaction distincte par wallet, qui n'est pas partagée avec un autre wallet du groupe | synchronisation |
| `repeated_large_entries` | Achats ≥ 1 000 sur ≥ 3 événements | Nombre d'événements et leur liste ; aucun résultat final utilisé | 0 point tant que l'indépendance n'est pas sourcée ; un point seulement si des `independence_group` explicites et distincts sont fournis |

Les groupes de fills ne sont pas déclarés indépendants statistiquement. La synchronisation reste un rapprochement probabiliste : copie, automatisation, arbitrage et nouvelle publique sont des explications concurrentes. Les liens financiers et les séquences financement → positions → retraits relèvent de l'enquête sourcée ; ils ne sont pas supposés ni ajoutés au score par ces règles. Les scénarios de vainqueur/classement/places conservent leurs issues observées, mais leur cohérence exige l'examen des règles de résolution : aucune multiplication de probabilités ou inférence d'indépendance.

## Statuts et immutabilité des alertes

- `public_at` et `public_observed_at` tous deux connus au plus à la date du calcul : **information publique retrouvée**, score préalable nul, score descriptif séparé dans `retrospective_score`.
- Événement explicitement fermé/inactif, ou tous ses marchés concernés explicitement fermés : **événement terminé**, aucune alerte préalable.
- Échéance passée sans statut de clôture confirmé : suspension de l'alerte préalable et limite explicite ; l'échéance ne prouve pas que le résultat est public.
- Statut ouvert non vérifié : candidat conservé, `priority=false`, `preliminary=false`.
- Sinon : candidat exploratoire, **données insuffisantes** lorsque la couverture publique est inconnue.

L'ID est stable par wallet, événement et version des règles. Le fingerprint matériel exclut la date du calcul et les seules bornes mobiles de la fenêtre. Le moteur doit archiver les calculs émis : un dossier réexaminé plus tard ne réécrit pas les connaissances de l'émission initiale. Les snapshots historiques de marché doivent être conservés et fournis à l'analyse pour ne pas remplacer une liquidité antérieure par une observation ultérieure.

## Comptabilité

`bookkeeping` distingue parts, volume brut, flux de trésorerie brut, frais, inventaire observé et gains réalisés. Le coût moyen n'est calculable que si l'appelant atteste un inventaire d'ouverture vide et un historique complet. Une vente sans coût documenté, une transformation SPLIT/MERGE/etc., ou un ordre BUY/SELL inconnu dans la même seconde rend le PnL **non calculable**. À seconde égale, un ordre vérifié exige bloc et logIndex. Les frais inconnus peuvent laisser le brut calculable mais jamais le net. Les gains latents, règlements et remboursements ne sont pas inventés. Le pipeline courant n'atteste pas un historique complet : le PnL réel reste donc non calculable.

## Vérification effectuée

`python -m unittest discover -s tests -p 'test_signals.py' -v` : 34 tests PASS au 27/10/2026. Fixtures entièrement synthétiques : atteignabilité technique, temps d'observation, liquidité pré-trade, publication connue tardivement, ordre fractionné, frais, coûts manquants, achat/vente à perte, synchronisation et sources dépendantes, déduplication et fingerprint. Cela ne valide aucune pertinence statistique ni aucun cas d'information privilégiée. Aucun entraînement, protocole d'évaluation ou résultat d'insider confirmé n'est revendiqué.

## Scénarios de vainqueur et de classement (text-scenarios-1)

`describe_scenarios(markets)` décrit sans bonus de score des contraintes conditionnelles de rang : vainqueur, top-N et place exacte. Seules des formulations explicites en anglais/français et des issues nommées sont reconnues. Les issues affirmatives/négatives sont appariées par leurs libellés Yes/No ou Oui/Non, jamais par leur indice. Un sujet identifié dans une issue nommée peut être rapproché du même sujet explicitement nommé dans une question binaire.

Le regroupement exige le même identifiant d'événement, le même sujet textuel et le même intitulé résiduel de compétition. Une formulation inconnue, une identité d'événement absente ou des libellés booléens ambigus restent dans `unclassified`. Deux compétitions de noms différents ne sont pas fusionnées, même dans un seul événement Gamma.

La sortie conserve les tokens/libellés et énumère des intervalles de rang avec les réponses conditionnelles correspondantes. Exemple, pour un même candidat : premier implique « vainqueur=oui, top-3=oui, deuxième=non » ; deuxième implique « vainqueur=non, top-3=oui, deuxième=oui ». Tous ces scénarios sont explicitement **conditionnels à la concordance des règles de résolution** ; égalités, ex aequo et annulations ne sont pas inférés. Le rapprochement est probabiliste, aucune équivalence de règlement n'est certifiée, aucune indépendance ni probabilité composée n'est calculée. L'appelant doit fournir les seuls snapshots accessibles à la date choisie.

## Correction du filtrage des marchés — exploratory-1.1

Un événement peut contenir à la fois des marchés ouverts et terminés. Le filtrage préalable s'applique désormais **à chaque opération selon son marché**, et au statut de l'événement : marché fermé, résolu, inactif, échéance passée ou résultat publiquement connu à la date de calcul → opération exclue des déclencheurs et des achats affichés dans `alerts`. Les agrégats de concentration, rotation et répétition préalables portent sur les seules opérations encore éligibles. Les transactions anciennes restent utilisables comme références historiques explicites de taille, sans utiliser leur résultat.

Les opérations exclues restent dans `retrospective_trades` avec leur motif, leurs signaux dans `retrospective_signals` et leur score descriptif dans `retrospective_score`. Une petite opération sur un marché ouvert ne réactive donc pas les grands achats d'un marché terminé du même événement. Sans signal éligible, `score=0`, `preliminary=false`, `priority=false`, `alerts=[]`. Le filtrage utilise uniquement les snapshots connus à `now` ; une clôture observée plus tard ne change pas un replay antérieur. La version change afin de distinguer les calculs corrigés des émissions antérieures archivées.

Régression reproduite et corrigée : trois wallets achetant chacun 5 000 de nominal sur un marché fermé, puis 1 sur un marché ouvert du même événement, produisent trois dossiers uniquement rétrospectifs, aucun prioritaire. Les cas de résolution explicite, publication connue et échéance passée sont testés, ainsi que la conservation d'un signal valide sur un marché ouvert.

## Correction datée du 27/10/2026 — exploratory-1.2

La revue des 40 priorités a retrouvé des activités plus anciennes, déjà connues au calcul, pour 5 des 14 dossiers portant `first_observed_large`. Ces lignes avaient été évincées par le plafond d'entrée. L'ancienneté connue consulte désormais toutes les transactions conservées, avec date d'observation et date économique antérieures au calcul. Une activité découverte après le calcul n'est pas antidatée. L'absence d'historique conserve le libellé « âge réel inconnu ».

L'entrée bornée de 50 000 lignes est désormais triée par date de transaction, puis identifiant stable. Ce changement de population est explicite : anciennes émissions, scores et données ne sont pas réécrits. Les seuils ne changent pas. Les résultats historiques v1.1 se reproduisent avec l'archive de livraison. Détails, témoins et réfutations : `evidence/review_20261027/dossiers/REPORT.md`.

## 27 octobre — priorité opérationnelle et audit comparatif

Les signaux et seuils v1.2 ne changent pas. La sélection d'enquêtes automatiques ajoute un périmètre d'annonce documentée (titre, URL de résolution, échéance future), distinct du score et de toute affirmation d'information non publique. Le marché peut rester surveillé dans la rotation générale même s'il n'est pas admissible à une enquête automatique.

Audit descriptif ponctuel : `evidence/continuous_20261027/dossiers/PLAN.md` et `REPORT.md`. Trois marchés corrélés d'une même décision FOMC, un témoin strict, aucun signal statistiquement validé et aucun résultat futur utilisé. L'absence de comparateur n'est pas une preuve de rareté.
