# Phase 10 : audit des données de carnet (CLOB)

Audit fait le 30/09/2026, avant tout calcul de résultat de la phase 10. Chaque statut a été testé en direct.

| DONNÉE | RÉSOLUTION | COUVERTURE | SOURCE | UTILISABLE POUR BACKTEST ? |
|---|---|---|---|---|
| Trades preneurs, toutes tailles | 1 s (horodatage de bloc) ; **ordre exact d'exécution** | complète sur toute fenêtre `start`/`end` : 103/103 trades et 323/323 fills contre les logs on-chain Maduro (03/01 05:00-06:11) ; ordre identique au (bloc, logIndex) sur 102/102 paires | data-api `/trades?market=&start=&end=&takerOnly=true` | **OUI** |
| Fills makers (ordres passifs consommés par chaque trade) | par fill, même transaction que le preneur | complète (même test) ; `takerOnly=false` ajoute une ligne par ordre maker touché, avec son prix et sa taille | data-api `/trades?...&takerOnly=false` | **OUI** : donne les **niveaux du carnet réellement consommés** par chaque trade |
| Ordre agressif / passif | par trade | complète | preneur = ligne présente avec `takerOnly=true` ; makers = lignes supplémentaires de la même transaction | **OUI** |
| Best ask **juste avant** un trade acheteur | au trade | uniquement aux instants où un achat-équivalent a lieu | prix du 1er niveau maker consommé par ce trade | **OUI**, seulement à ces instants |
| Best bid **juste avant** un trade vendeur | au trade | idem, pour les ventes-équivalentes | 1er niveau maker consommé | **OUI**, seulement à ces instants |
| Profondeur consommée (taille par niveau) | par niveau touché | seulement jusqu'à la taille du trade observé | fills makers | **PARTIEL** : on voit ce qui a été pris, jamais ce qui restait |
| Best bid / best ask **à un instant quelconque** | aucune | 0 | `/book`, `/midpoint`, `/spread` répondent 404 sur un marché fermé (testé sur le marché Iran) | **NON** : INCONNU entre deux trades |
| Mid, spread à un instant quelconque | aucune | 0 | idem | **NON** ; un spread ne peut être inféré qu'à partir d'un achat et d'une vente proches |
| Profondeur totale du carnet | aucune | 0 | aucun endpoint historique | **NON** |
| Placements, modifications, annulations d'ordres | aucune | 0 | carnet hors chaîne ; seules les exécutions sont réglées on-chain | **NON** : INCONNU |
| Série de prix | 1 min | 7 jours max par appel | CLOB `prices-history` | contexte seulement |
| Trades on-chain (OrderFilled, OrdersMatched) | bloc (~2 s) + logIndex | complète | Polygon ; v1 `0x4bfb41d5` (binaire) et `0xc5d563a3` (neg-risk), jusqu'au 28/04/2026 11:00 UTC ; v2 `0xe1111800` et `0xe2222d27`, à partir du 03/04/2026 | **OUI**, mais redondant avec le data-api (qui est complet et ordonné) ; sert de contrôle |
| Frais preneur payés | par trade | par reçu de transaction | v1 : champ `fee` de OrderFilled ; v2 : événement `0x55bb3cad` (FeeCharged, montant) | **OUI**, sur les transactions demandées (reçu par hash) |
| Heure à laquelle un observateur voit le trade | aucune | 0 | websocket CLOB (temps réel, sans adresse de wallet) ; data-api (délai de publication inconnu) ; nœud Polygon (bloc) | **INCONNU** : T0 = horodatage du bloc, c'est une borne basse |
| Identité du wallet au moment du trade | par trade | complète | data-api `proxyWallet`, on-chain `maker`/`taker` | **OUI** (nécessaire à SIG_HIST) |

## Conséquences

1. **B, le prix observable à T0 + L**, n'est mesurable que si un achat-équivalent d'un autre wallet s'exécute à ce moment-là. Son premier niveau maker donne alors le best ask. Sinon, B(T0 + L) est **INCONNU** : aucune interpolation n'est faite.
2. **C, le prix d'exécution simulé pour une taille S**, se lit sur les niveaux makers consommés par les trades observés. Au-delà de la profondeur consommée visible, la taille est déclarée **non observable**. On ne suppose jamais qu'elle aurait été exécutée.
3. **Résolution temporelle.**
   - Le bloc Polygon dure environ 2 s. T0 + 1 s et T0 + 2 s tombent dans le bloc suivant ou le même bloc ; T0 + 1 s est donc **indiscernable** de T0 + 2 s.
   - Les observateurs à 1 et 2 s sont calculés, mais aucune différence entre eux n'est interprétée.
4. **Migration des contrats (mesurée).**
   - Les marchés passent du contrat v1 au contrat v2 entre le 03/04 et le 28/04/2026, avec un nouveau collatéral `0xc011a7e1`, adossé à l'USDC.e, et un événement de frais séparé.
   - VALID chevauche la migration, TEST est entièrement en v2 : la microstructure n'est pas la même entre VALID et TEST.
5. **Clés d'API CLOB présentes dans `~/Downloads/.env`, non utilisées.**
   - L'historique `/data/trades` authentifié ne renvoie que les trades du titulaire du compte.
   - La mission interdit tout système d'exécution.
