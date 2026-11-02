# Phase 10 : protocole pré-enregistré

Rédigé le 30/09/2026 :
- après l'audit (`data_audit.md`, `CLOB_DATA_AUDIT.md`) ;
- pendant la collecte des flux ;
- **avant tout calcul de prix postérieur à T0 sur les nouvelles données**.

Toute déviation sera signalée dans le rapport. Seule la phase 9 a déjà observé les résultats de SIG_HIST, à partir des trades ≥ 100 $. Ceux des variantes ci-dessous ne sont connus de personne.

## 0. Le signal

**SIG_HIST est strictement celui de la phase 9** (`data_audit.md` §1) : 1 985 alertes (TRAIN 688, VALID 561, TEST 736). Rien n'y est modifié.

**Toute nouvelle règle porte un nom distinct** :
- SIG_HIST_LOW_IMPACT ;
- SIG_HIST_FOLLOW ;
- SIG_HIST_SOCIAL ;
- SIG_HIST_LOW_IMPACT_FOLLOW.

**Découpage inchangé** :
- TRAIN : T avant le 01/03/2026 ;
- VALID : du 01/03 au 31/05 ;
- TEST : à partir du 01/06.

**Contrôle.** Chaque alerte a un contrôle apparié : un FAE non-FOLLOW non SIG_HIST de la même strate (split × décile de prix × temps restant × activité), tiré avec la graine 10. Au total, 1 964 contrôles.

## 1. Flux et conventions

**Source.** Pour chaque fenêtre [T0 − 900 s, T0 + 4 500 s] :
- tous les trades preneurs du marché, toutes tailles, dans l'ordre exact d'exécution ;
- leurs fills makers, c'est-à-dire les niveaux consommés.

**Direction d = le jeton acheté par le wallet signalé.** Les prix sont exprimés en « prix de d » :
- prix x d'un trade sur d : x ;
- prix x d'un trade sur le jeton opposé : 1 − x.

**Sens des trades preneurs :**
- **achat-équivalent (AE)** : achat de d, ou vente du jeton opposé ;
- **vente-équivalente (VE)** : l'inverse.

**Niveaux d'un trade preneur.** Chacun de ses fills makers donne un niveau (prix en d, taille en actions) :
- pour un AE, ce sont des asks de d, triés par prix croissant ;
- pour un VE, ce sont des bids de d, triés par prix décroissant.

**Prix repères autour du trade du wallet :**

| Repère | Définition |
|---|---|
| `P_BEFORE` | prix du dernier trade preneur, tout wallet et toute taille, qui précède le trade du wallet dans l'ordre d'exécution |
| `ASK_BEFORE` | premier niveau consommé par le wallet (best ask juste avant son trade) |
| `A` | prix moyen payé par le wallet |
| `MARGINAL` | dernier niveau consommé par le wallet |
| `P_oth(t)` | prix du dernier trade preneur d'un **autre** wallet, postérieur au trade du wallet et d'heure ≤ t. S'il n'y en a aucun : pas de mouvement observé, marqué comme tel |

## 2. Décomposition du mouvement (§5, §6, §12)

**Mouvements (points de probabilité, direction d) :**
- Δ_pre = `P_BEFORE` − P(T0 − 600 s) ;
- IMMEDIATE_IMPACT = `MARGINAL` − `P_BEFORE` ;
- FOLLOW_THROUGH(H) = `P_oth`(T0 + H) − `MARGINAL`, pour H = 10, 60, 300, 600 et 3 600 s.

**Identité exacte (additive par construction) :**

Δ_total(H) = Δ_pre + IMMEDIATE_IMPACT + FOLLOW_THROUGH(H)

**Mesures complémentaires :**
- marche dans le carnet = `MARGINAL` − `ASK_BEFORE` ;
- impact à la phase 9 = `A` − `P_BEFORE`.

**follow_through_ratio** = FOLLOW_THROUGH(3 600) / max(IMMEDIATE_IMPACT ; 0,005).

**Seuil τ_I** = médiane de IMMEDIATE_IMPACT sur les alertes SIG_HIST de **TRAIN**.
- SELF_IMPACT_HIGH : impact > τ_I ;
- SELF_IMPACT_LOW : impact ≤ τ_I.

**Cas, sur les gagnants (LEAD60 = 1) et sur toutes les alertes :**

| Cas | Impact | FOLLOW_THROUGH(3 600) |
|---|---|---|
| A, INFORMATION | ≤ τ_I | ≥ 1,5 point |
| B, PRICE IMPACT | > τ_I | ≤ 0 |
| C, MIXTE | > τ_I | ≥ 1,5 point |
| AUTRE | tout le reste | |

## 3. Exécution simulée (§3, §7, §8, §9)

### Latences

Observateurs L = 0, 1, 2, 5, 10, 20, 30, 60, 120 et 300 s.

**OBSERVER_0 est théorique.** Il prend le premier AE d'un autre wallet qui suit le trade du wallet dans l'ordre d'exécution, même dans le même bloc. Personne ne peut l'atteindre.

### Prix d'entrée (ordre au marché)

Le premier AE d'un autre wallet d'heure ≥ T0 + L sert de repère :
- **B(L)** = son premier niveau, c'est-à-dire le best ask observé ;
- **C(L, S)** = prix moyen des S premiers dollars de ses niveaux.

Si ses niveaux ne suffisent pas pour S, on ajoute ceux des AE suivants dans les 10 s. On suppose alors que les niveaux déjà pris ne sont pas remplacés : c'est une approximation, signalée comme telle. Si la profondeur observée reste insuffisante, la taille est « non observable ». Elle n'est jamais supposée exécutée.

On calcule deux estimateurs :
- **STRICT (principal)** : le repère doit avoir lieu dans [T0 + L, T0 + L + 2 s]. Sinon, B(L) et C(L) sont INCONNUS pour cette alerte ;
- **SUIVANT (sensibilité)** : le repère peut avoir lieu jusqu'à T0 + L + 60 s. Le délai réel est enregistré.

### Tailles

S = 50, 100, 250, 500, 1 000, 2 500 et 5 000 $.

### Sortie

**Horizons :** H = 60, 300, 600 et 3 600 s (principal), plus la résolution.

**Sortie à l'horizon H :**
- on vend au bid, par les niveaux du premier VE d'un autre wallet d'heure ≥ T0 + H, en complétant par les VE suivants dans les 10 s ;
- le repère doit avoir lieu dans [T0 + H, T0 + H + 900 s] ;
- sinon, la sortie est « non observée » : l'alerte est exclue de ce calcul, et la part exclue est publiée.

**Sortie à la résolution :** 1 ou 0 par action (issue du marché, phase 8), sans frais de sortie.

### Frais

Ils sont **mesurés sur le reçu de la transaction du wallet signalé**, au même moment et dans le même marché :
- coefficient c = frais payés ($) / (actions × min(p, 1 − p)) ;
- frais de l'observateur = c × actions × min(p, 1 − p), à l'entrée et à la sortie (preneur) ;
- maker = 0.

Si le reçu est illisible, deux scénarios : c = 0 et c = 0,02 (hypothèse de la phase 9).

### Rendements et statistiques

- brut = (produit − coût) / coût ;
- net = brut − frais / coût.

Pour chaque case : n, couverture, moyenne, médiane, P10, P25, P75, P90, min, max, part > 0, MAE et MFE sur 60 min (prix des autres wallets).

## 4. Ordres limites (§10)

**Pose :** à T0 + 2 s, taille 500 $.

**Durées de vie :** D = 60 s et 300 s.

**Prix limite K :**

| Code | Prix |
|---|---|
| K1 | `ASK_BEFORE`, le prix d'avant l'impact |
| K2 | `A`, le prix du wallet |
| K3 | `P_BEFORE` + ½ (`A` − `P_BEFORE`) |

**Remplissage :**
- **immédiat (preneur)** : un AE d'un autre wallet dans la durée de vie montre un premier niveau ≤ K. Remplissage à ce niveau, avec frais ;
- **passif (maker, sans frais)** : des VE d'autres wallets consomment des niveaux de bid :
  - règle **conservatrice** : prix strictement < K, pour une quantité cumulée ≥ nos actions ;
  - règle **optimiste** : prix ≤ K.

La file d'attente est inconnue : seule la règle conservatrice compte pour la conclusion.

**Sortie :** comme l'ordre au marché, au bid à T0 + 3 600 s.

**Mesures :**
- probabilité de remplissage ;
- rendement conditionnel au remplissage ;
- espérance par alerte = probabilité × rendement conditionnel.

**Classement :** **NON CAPTURABLE** si la probabilité de remplissage est < 25 % ou si l'espérance par alerte est ≤ 0.

## 5. Reproduction du −2,3 % à 1 s (§7)

1. Rejouer **le même code** que la phase 9 (`p9_exec.sim`, L = 1 s, 500 $, trades ≥ 100 $), en enregistrant l'heure des trades utilisés pour l'entrée, la voie de sortie (observée ou repli) et les frais.
2. Publier la distribution : moyenne, médiane, P10, P25, P75, P90, min, max.
3. Séparer les alertes gagnantes (net > 0) et perdantes.
4. Décomposer la perte en quatre postes :
   - délai réel d'entrée ;
   - prix d'entrée − `A` ;
   - sortie au bid contre prix moyen ;
   - frais.

## 6. Suiveurs (§13, §14, §15)

**Par alerte, dans ]T0, T0 + 600 s] (flux complet) :**
- AE et VE d'autres wallets : nombre de wallets, volume, délais, prix ;
- **contribution au mouvement** : la variation `P_oth` entre T0 et T0 + 600 s est la somme exacte des pas de prix (prix du trade − prix du trade précédent). Ces pas sont attribués à trois groupes :
  - suiveurs liés (AE) ;
  - autres AE ;
  - VE.

**Graphe leader → suiveur (trades ≥ 100 $, tout l'historique, 2 097 marchés) :**
- **leaders** = wallets ayant déclenché SIG_HIST au moins une fois ;
- pour chaque FAE d'un leader :
  - **suiveurs** = autres wallets achetant le même jeton dans les 600 s qui suivent ;
  - **précurseurs** = ceux qui l'ont acheté dans les 600 s qui précèdent (contrôle temporel symétrique).
- **Mesures par couple** :
  - nombre de marchés distincts en aval et en amont ;
  - délai médian ;
  - rendement du suiveur et du leader : Δ à 60 min depuis leur propre prix, sur les trades des autres ;
  - part des cas où le prix avait déjà bougé d'au moins 1,5 point dans la direction entre le trade du leader et celui du suiveur (mouvement indépendant).

**Classement d'un couple (A, B) :**

| Classe | Condition |
|---|---|
| **FOLLOWER** (B suit A) | aval ≥ 3 marchés, aval ≥ 3 × max(amont, 1), et mouvement indépendant dans moins de 50 % des cas |
| **LEADER** (B précède A) | symétrique |
| **INDEPENDENT** | sinon |

**Chaînes A → B → C :** probabilité que C suive B sachant que B a suivi A, comparée à sa fréquence de base.

## 7. Variantes (§16, §17, §18, §19)

Elles sont définies ici, calculées d'abord sur TRAIN, puis leurs seuils sont gelés dans `frozen_p10.json` **avant** toute lecture de VALID. Ensuite VALID, puis TEST. **Aucun seuil n'est modifié après VALID.**

**SIG_HIST_LOW_IMPACT**
- Condition : SIG_HIST et IMMEDIATE_IMPACT ≤ τ_I (médiane TRAIN, §2).
- Observable à T0.

**SIG_HIST_FOLLOW**
- Condition : SIG_HIST et hist_follow(T0) ≥ τ_F.
- hist_follow(T0) = moyenne, sur les FAE non-FOLLOW du wallet résolus avant T0 (T_e + 3 600 ≤ T0), de la continuation après son propre prix. C'est le `move_after_exec` de la phase 9, calculé sur les trades ≥ 100 $.
- τ_F = médiane de hist_follow sur les alertes SIG_HIST de TRAIN.

**SIG_HIST_SOCIAL**
- Condition : SIG_HIST, puis, dans les 300 s qui suivent T0, un achat de d (toute taille) par un **suiveur lié**.
- Suiveur lié : il a acheté le même jeton dans les 600 s après un FAE de ce leader, dans au moins 2 marchés distincts, les deux fois avant T0 − 600 s (trades ≥ 100 $).
- L'heure du signal devient T1 = l'heure de ce premier achat. Les latences comptent depuis T1.
- Paramètres fixés a priori (k = 2, W = 300 s), non ajustés.

**SIG_HIST_LOW_IMPACT_FOLLOW**
- Condition : l'intersection des deux premières. Aucun paramètre nouveau.

**Stratégie principale de chaque variante (et de SIG_HIST)**
- ordre au marché, STRICT, L = 2 s, 500 $ ;
- sortie au bid à 60 min ;
- frais mesurés.

Le reste de la grille est descriptif. **Aucune case n'est choisie après lecture de VALID ou TEST.**

## 8. Critères de réussite (§22)

Une stratégie est positive seulement si **tous** les critères sont remplis :

1. **Information disponible à T.** Toute donnée d'entrée est horodatée ≤ heure de l'ordre (vérifié dans le code).
2. **Momentum contrôlé.** Moyenne nette > 0 dans les strates Δ_pre ≤ 0 et Δ_pre > 0 (VALID + TEST réunis).
3. **VALID.** Moyenne nette > 0, borne basse de l'IC 95 % (bootstrap par marché, 2 000 tirages, graine 10) > 0, n ≥ 30.
4. **TEST.** Mêmes conditions que VALID.
5. **Frais.** Frais mesurés inclus.
6. **Glissement.** Inclus : prix moyen sur les niveaux réellement consommés.
7. **Taille réaliste.** 500 $ ; la taille maximale positive est publiée.
8. **Liquidité.**
   - entrée et sortie observées pour au moins 30 % des alertes ;
   - profondeur de 500 $ observée pour au moins 50 % des entrées.
9. **Dispersion.**
   - la moyenne nette sans les 5 % meilleurs trades reste > 0 en VALID et en TEST ;
   - aucun wallet et aucun marché ne dépasse 20 % des trades.
10. **Mécanisme identifiable.** Il ressort de la décomposition (§2) ou des suiveurs (§6).

## 9. Maduro, Iran et les 8 comptes (§20, §21)

**Fenêtres collectées :**
- Iran : 27/02 12:00 → 28/02 07:00 UTC ;
- Maduro : 02/01 12:00 → 03/01 10:00 UTC.

**Chronologie :**
- activité des wallets ;
- prix ;
- signaux du détecteur (flux ≥ 100 $, état rejoué causalement) ;
- activité de tout le marché ;
- événements publics, chacun marqué **VÉRIFIÉ** (source horodatée) ou **APPROXIMATE**.

**Les 8 comptes** ne sont testés que sur les mécanismes ci-dessous. Un compte n'est « expliqué » que si l'un d'eux atteint le seuil fixé ici ; sinon, **NO SIGNAL**.

| Mécanisme | Seuil |
|---|---|
| Self-impact | IMMEDIATE_IMPACT > τ_I |
| Suiveurs | au moins 1 suiveur lié |
| Convergence | drapeau CONV |
| Accumulation | drapeau ACC |
| Financement | S_FRESH, S_FASTFUND ou S_MOONPAY de la phase 8 |
